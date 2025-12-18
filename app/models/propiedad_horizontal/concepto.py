from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.core.database import Base

class PHConcepto(Base):
    """
    Define los conceptos facturables en la Propiedad Horizontal.
    Conecta la operación (Cobro) con la Contabilidad (Cuenta PUC).
    """
    __tablename__ = "ph_conceptos"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    
    nombre = Column(String(100), nullable=False)
    
    # Conexión Contable
    # CORRECCIÓN: Apuntando a 'plan_cuentas' en lugar de 'puc_cuentas'
    cuenta_ingreso_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=False)
    cuenta_cxc_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True) # Por defecto 1305
    cuenta_interes_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True) # Para mora
    cuenta_caja_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True) # Para Recaudos specificos

    # Configuración de Cobro
    usa_coeficiente = Column(Boolean, default=False)
    es_fijo = Column(Boolean, default=True) # True: Se cobra todos los meses. False: Novedad ocasional.
    valor_defecto = Column(Numeric(14, 2), default=0)
    
    activo = Column(Boolean, default=True)

    # Relaciones
    empresa = relationship("Empresa")
    # CORRECCIÓN: Relaciones apuntando a app.models.plan_cuenta.PlanCuenta
    cuenta_ingreso = relationship("app.models.plan_cuenta.PlanCuenta", foreign_keys=[cuenta_ingreso_id])
    cuenta_cxc = relationship("app.models.plan_cuenta.PlanCuenta", foreign_keys=[cuenta_cxc_id])
    cuenta_interes = relationship("app.models.plan_cuenta.PlanCuenta", foreign_keys=[cuenta_interes_id])
    cuenta_caja = relationship("app.models.plan_cuenta.PlanCuenta", foreign_keys=[cuenta_caja_id])

    # Relación M:M con Módulos (Filtrado de Cobro)
    modulos = relationship(
        "app.models.propiedad_horizontal.modulo_contribucion.PHModuloContribucion",
        secondary="ph_concepto_modulo_association",
        backref="conceptos" # Para saber qué conceptos afectan a un módulo
    )

from sqlalchemy import Table

ph_concepto_modulo_association = Table(
    "ph_concepto_modulo_association",
    Base.metadata,
    Column("concepto_id", Integer, ForeignKey("ph_conceptos.id"), primary_key=True),
    Column("modulo_id", Integer, ForeignKey("ph_modulos_contribucion.id"), primary_key=True)
)
