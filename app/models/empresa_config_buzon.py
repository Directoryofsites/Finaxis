from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from ..core.database import Base

class EmpresaConfigBuzon(Base):
    __tablename__ = "empresa_config_buzon"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), unique=True, nullable=False)
    
    # Credenciales del correo
    email_addr = Column(String(255), nullable=True)
    password_app = Column(String(255), nullable=True) # App password de Gmail

    # Parámetros contables (Factura de Compra - Mantener por compatibilidad)
    tipo_documento_id = Column(Integer, ForeignKey("tipos_documento.id"), nullable=True)
    cuenta_gasto_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True)
    cuenta_caja_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True)

    # Parámetros para Factura de Venta
    venta_tipo_documento_id = Column(Integer, ForeignKey("tipos_documento.id"), nullable=True)
    venta_cuenta_ingreso_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True)
    venta_cuenta_caja_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True)

    # Parámetros para Documento Soporte
    soporte_tipo_documento_id = Column(Integer, ForeignKey("tipos_documento.id"), nullable=True)
    soporte_cuenta_gasto_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True)
    soporte_cuenta_caja_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True)

    # Opciones adiciones (por si se ocupan a futuro)
    is_active = Column(Boolean, default=True)

    # Relaciones
    empresa = relationship("Empresa", back_populates="config_buzon")
    
    # Compras
    tipo_documento = relationship("TipoDocumento", foreign_keys=[tipo_documento_id])
    cuenta_gasto = relationship("PlanCuenta", foreign_keys=[cuenta_gasto_id])
    cuenta_caja = relationship("PlanCuenta", foreign_keys=[cuenta_caja_id])

    # Ventas
    venta_tipo_documento = relationship("TipoDocumento", foreign_keys=[venta_tipo_documento_id])
    venta_cuenta_ingreso = relationship("PlanCuenta", foreign_keys=[venta_cuenta_ingreso_id])
    venta_cuenta_caja = relationship("PlanCuenta", foreign_keys=[venta_cuenta_caja_id])

    # Soporte
    soporte_tipo_documento = relationship("TipoDocumento", foreign_keys=[soporte_tipo_documento_id])
    soporte_cuenta_gasto = relationship("PlanCuenta", foreign_keys=[soporte_cuenta_gasto_id])
    soporte_cuenta_caja = relationship("PlanCuenta", foreign_keys=[soporte_cuenta_caja_id])
