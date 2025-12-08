from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from ..core.database import Base
import enum

class MetodoDepreciacion(str, enum.Enum):
    LINEA_RECTA = "LINEA_RECTA"
    REDUCCION_SALDOS = "REDUCCION_SALDOS"
    UNIDADES_PRODUCCION = "UNIDADES_PRODUCCION"
    NO_DEPRECIAR = "NO_DEPRECIAR"

class ActivoCategoria(Base):
    __tablename__ = "activos_categorias"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    
    nombre = Column(String(100), nullable=False)
    
    # Parametrización Contable
    vida_util_niif_meses = Column(Integer, default=0, nullable=False, doc="Vida útil para normas internacionales")
    vida_util_fiscal_meses = Column(Integer, default=0, nullable=False, doc="Vida útil para estatuto tributario")
    
    metodo_depreciacion = Column(Enum(MetodoDepreciacion), default=MetodoDepreciacion.LINEA_RECTA, nullable=False)
    
    # Cuentas Contables (PUC)
    cuenta_activo_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True, doc="Cuenta 15... (El bien en sí)")
    cuenta_gasto_depreciacion_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True, doc="Cuenta 51... (El gasto mensual)")
    cuenta_depreciacion_acumulada_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True, doc="Cuenta 1592... (El desgaste acumulado)")
    
    # Relaciones
    activos = relationship("ActivoFijo", back_populates="categoria")
    
    # Relaciones con Plan de Cuentas
    cuenta_activo = relationship("PlanCuenta", foreign_keys=[cuenta_activo_id])
    cuenta_gasto = relationship("PlanCuenta", foreign_keys=[cuenta_gasto_depreciacion_id])
    cuenta_depreciacion_acumulada = relationship("PlanCuenta", foreign_keys=[cuenta_depreciacion_acumulada_id])
