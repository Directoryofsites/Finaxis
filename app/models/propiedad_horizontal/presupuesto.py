from sqlalchemy import Column, Integer, String, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from ...core.database import Base

class PHPresupuesto(Base):
    __tablename__ = "ph_presupuestos"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    anio = Column(Integer, nullable=False)
    cuenta_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=False)
    
    # Valores Mensuales
    mes_01 = Column(Float, default=0)
    mes_02 = Column(Float, default=0)
    mes_03 = Column(Float, default=0)
    mes_04 = Column(Float, default=0)
    mes_05 = Column(Float, default=0)
    mes_06 = Column(Float, default=0)
    mes_07 = Column(Float, default=0)
    mes_08 = Column(Float, default=0)
    mes_09 = Column(Float, default=0)
    mes_10 = Column(Float, default=0)
    mes_11 = Column(Float, default=0)
    mes_12 = Column(Float, default=0)
    
    # Valor Total (Calculado o Base)
    valor_anual = Column(Float, default=0)

    # Relaciones
    empresa = relationship("Empresa")
    cuenta = relationship("PlanCuenta")

    # Restricción: Un presupuesto por cuenta por año por empresa
    __table_args__ = (
        UniqueConstraint('empresa_id', 'anio', 'cuenta_id', name='uq_ph_presupuesto_empresa_anio_cuenta'),
    )
