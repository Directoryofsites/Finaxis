from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint
from ..core.database import Base

class PlanCuenta(Base):
    __tablename__ = "plan_cuentas"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    codigo = Column(String(20), nullable=False)
    nombre = Column(String(255), nullable=False, index=True)
    nivel = Column(Integer, nullable=False)
    permite_movimiento = Column(Boolean, default=False)
    funcion_especial = Column(String(50), nullable=True)

    # La columna 'clase_cuenta' debe eliminarse y ser sustituida por 'clase' (Integer)
    # Si la columna existe en tu DB, Alembic la renombrará/reemplazará en el siguiente paso.
    clase = Column(Integer, nullable=True)

    # --- INICIO: NUEVA COLUMNA AÑADIDA ---
    # Esta es la "etiqueta" que le dirá a nuestro sistema qué cuentas son de ingresos.
    es_cuenta_de_ingresos = Column(Boolean, nullable=False, server_default='f', default=False, index=True)
    # --- FIN: NUEVA COLUMNA AÑADIDA ---
    
    cuenta_padre_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True)

    created_by = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    hijos = relationship("PlanCuenta", back_populates="padre", cascade="all, delete-orphan")
    padre = relationship("PlanCuenta", remote_side=[id], back_populates="hijos")

    __table_args__ = (
        UniqueConstraint('empresa_id', 'codigo', name='uq_plan_cuentas_empresa_codigo'),
    )