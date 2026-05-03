# app/core/database.py

from sqlalchemy import create_engine, event, bindparam
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, ORMExecuteState, with_loader_criteria
from contextvars import ContextVar
from ..core.config import settings

# --- INICIO DE LA CORRECCIÓN ---
# Se cambia el parámetro echo=True por echo=False para desactivar
# el registro detallado de consultas SQL en la terminal.
# Esto resultará en un arranque del servidor mucho más limpio.
engine = create_engine(
    settings.DATABASE_URL, 
    echo=False,
    pool_size=20,
    max_overflow=40
)
# --- FIN DE LA CORRECCIÓN ---

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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