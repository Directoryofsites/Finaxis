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

    # Parámetros contables
    tipo_documento_id = Column(Integer, ForeignKey("tipos_documento.id"), nullable=True)
    cuenta_gasto_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True)
    cuenta_caja_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True)

    # Opciones adiciones (por si se ocupan a futuro)
    is_active = Column(Boolean, default=True)

    # Relaciones
    empresa = relationship("Empresa", back_populates="config_buzon")
    tipo_documento = relationship("TipoDocumento")
    cuenta_gasto = relationship("PlanCuenta", foreign_keys=[cuenta_gasto_id])
    cuenta_caja = relationship("PlanCuenta", foreign_keys=[cuenta_caja_id])
