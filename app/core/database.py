# app/core/database.py

from sqlalchemy import create_engine, event, bindparam
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, ORMExecuteState, with_loader_criteria
from contextvars import ContextVar
from ..core.config import settings

import os
import sys

# Lógica para determinar la URL de la base de datos según el entorno
_engine = None
_SessionLocal = None
_last_db_url = None

def get_engine():
    global _engine, _last_db_url, _SessionLocal
    
    # 1. Determinar URL actual (Prioridad: Config.json > Env)
    current_url = settings.DATABASE_URL
    appdata = os.getenv('APPDATA')
    if appdata:
        config_path = os.path.join(appdata, "Finaxis", "config.json")
        if os.path.exists(config_path):
            try:
                import json
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                    # Soportamos tanto DATABASE_URL (env) como database_url (json)
                    json_url = config_data.get("DATABASE_URL") or config_data.get("database_url")
                    if json_url:
                        current_url = json_url
            except:
                pass
        
        # Fallback para modo empaquetado si no hay override
        if getattr(sys, 'frozen', False) and current_url.startswith("sqlite:///./"):
            current_url = f"sqlite:///{os.path.join(appdata, 'Finaxis', 'contapy.db')}"

    # 2. Re-inicializar si la URL cambió
    if _engine is None or current_url != _last_db_url:
        if _engine:
            _engine.dispose()
        
        _last_db_url = current_url
        
        is_sqlite = current_url.startswith("sqlite")
        if is_sqlite:
            from sqlalchemy.pool import StaticPool
            _engine = create_engine(
                current_url,
                echo=False,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,  # SQLite: una sola conexión compartida
            )
        else:
            _engine = create_engine(
                current_url,
                echo=False,
                pool_size=20,
                max_overflow=40,
            )
        
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
        print(f"[DB] Motor listo: {current_url[:40]}...")

    return _engine

def get_session_local():
    get_engine()
    return _SessionLocal

# Objeto Proxy para mantener compatibilidad con el resto del sistema
class EngineProxy:
    @property
    def name(self): return get_engine().name
    def connect(self): return get_engine().connect()
    def begin(self): return get_engine().begin()
    def dispose(self): return get_engine().dispose()
    def execute(self, *args, **kwargs): return get_engine().execute(*args, **kwargs)

class SessionLocalProxy:
    def __call__(self, *args, **kwargs):
        factory = get_session_local()
        return factory(*args, **kwargs)
    
    # Para compatibilidad con decoradores o inspección que busquen atributos de sessionmaker
    def __getattr__(self, name):
        return getattr(get_session_local(), name)

engine = EngineProxy()
SessionLocal = SessionLocalProxy()
Base = declarative_base()

def get_db():
    session_factory = get_session_local()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()

def sql_periodo_mes(field):
    from sqlalchemy import func
    if engine.name == 'postgresql':
        return func.to_char(field, 'YYYY-MM')
    return func.strftime('%Y-%m', field)

# =========================================================================
# MIDDLEWARE MULTITENANCY (SEGURIDAD AISLAMIENTO POR EMPRESA)
# =========================================================================
# Variable de contexto que almacena el ID de la empresa de la request actual
current_empresa_id: ContextVar[int] = ContextVar("current_empresa_id", default=None)

# Nota: Para que el listener funcione con el factory dinámico, 
# escuchamos directamente a la clase Session de SQLAlchemy si es necesario, 
# o simplemente reinyectamos el evento al crear el factory.
from sqlalchemy.orm import Session
@event.listens_for(Session, "do_orm_execute")
def _add_tenant_filter(execute_state: ORMExecuteState):
    """
    Interceptor global de SQLAlchemy. Inyecta automáticamente la cláusula
    WHERE empresa_id = X en TODAS las consultas (SELECT, UPDATE, DELETE)
    si existe un usuario logueado en el contexto.
    """
    if current_empresa_id.get() is not None:
        # Permite bypass explícito con .execution_options(ignore_tenant=True)
        if execute_state.execution_options.get("ignore_tenant", False):
            return

        if execute_state.is_select or execute_state.is_update or execute_state.is_delete:
            execute_state.statement = execute_state.statement.options(
                with_loader_criteria(
                    Base,
                    lambda cls: cls.empresa_id == bindparam(
                        "ctx_empresa_id", callable_=lambda: current_empresa_id.get()
                    ) if hasattr(cls, 'empresa_id') else True,
                    include_aliases=True
                )
            )