# app/core/database.py

from sqlalchemy import create_engine, event, bindparam
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, ORMExecuteState, with_loader_criteria
from contextvars import ContextVar
from ..core.config import settings

import os
import sys

# Lógica para determinar la URL de la base de datos según el entorno
database_url = settings.DATABASE_URL

# Si estamos en modo empaquetado (.exe), redirigimos la BD a APPDATA para evitar problemas de permisos
if getattr(sys, 'frozen', False):
    appdata = os.getenv('APPDATA')
    if appdata:
        db_dir = os.path.join(appdata, "Finaxis")
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        # Si la URL original es SQLite relativa, la convertimos a absoluta en APPDATA
        if database_url.startswith("sqlite:///./"):
            db_path = os.path.join(db_dir, "contapy.db")
            database_url = f"sqlite:///{db_path}"

engine = create_engine(
    database_url, 
    echo=False,
    pool_size=20,
    max_overflow=40,
    connect_args={"check_same_thread": False} if database_url.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def sql_periodo_mes(field):
    """
    Retorna la expresión SQL adecuada para obtener el periodo YYYY-MM
    detectando si el motor es PostgreSQL o SQLite.
    """
    from sqlalchemy import func
    if engine.name == 'postgresql':
        return func.to_char(field, 'YYYY-MM')
    return func.strftime('%Y-%m', field)

# =========================================================================
# MIDDLEWARE MULTITENANCY (SEGURIDAD AISLAMIENTO POR EMPRESA)
# =========================================================================
# Variable de contexto que almacena el ID de la empresa de la request actual
current_empresa_id: ContextVar[int] = ContextVar("current_empresa_id", default=None)

@event.listens_for(SessionLocal, "do_orm_execute")
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