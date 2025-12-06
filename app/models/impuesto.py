from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
# --- 1. Importar el componente que faltaba ---
from sqlalchemy.schema import UniqueConstraint
from ..core.database import Base

class TasaImpuesto(Base):
    __tablename__ = 'tasas_impuesto'
    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey('empresas.id'), nullable=False)
    nombre = Column(String(50), nullable=False) # ej: "IVA 19%", "IVA 5%", "Exento"
    tasa = Column(Float, nullable=False) # ej: 0.19, 0.05, 0.0

    # Cuenta para IVA Generado (Ventas)
    cuenta_id = Column(Integer, ForeignKey('plan_cuentas.id'), nullable=True)
    # Cuenta para IVA Descontable (Compras)
    cuenta_iva_descontable_id = Column(Integer, ForeignKey('plan_cuentas.id'), nullable=True)

    # Relaciones con PlanCuenta
    cuenta = relationship("PlanCuenta", foreign_keys=[cuenta_id])
    cuenta_iva_descontable = relationship("PlanCuenta", foreign_keys=[cuenta_iva_descontable_id])

    # Relación inversa con Producto
    productos = relationship('Producto', back_populates='impuesto_iva')

    # --- 2. Añadir la directiva para crear la restricción de unicidad ---
    __table_args__ = (
        UniqueConstraint('empresa_id', 'nombre', name='uq_tasas_impuesto_empresa_nombre'),
    )