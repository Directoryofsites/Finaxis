from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric, Float, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class PHConfiguracion(Base):
    __tablename__ = "ph_configuracion"
    
    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    
    # Intereses
    interes_mora_mensual = Column(Float, default=1.5) # Porcentaje mensual
    
    # Fechas Clave (Días del mes)
    dia_corte = Column(Integer, default=1) # Día que se genera la factura
    dia_limite_pago = Column(Integer, default=10) # Hasta cuándo se paga sin mora
    
    # Pronto Pago
    dia_limite_pronto_pago = Column(Integer, default=5)
    descuento_pronto_pago = Column(Float, default=0.0) # Porcentaje descuento
    
    # Mensajes
    mensaje_factura = Column(Text, nullable=True) # "Recuerde pagar antes del..."
    
    # Integración Contable
    # Integración Contable
    tipo_documento_factura_id = Column(Integer, ForeignKey("tipos_documento.id"), nullable=True)
    tipo_documento_recibo_id = Column(Integer, ForeignKey("tipos_documento.id"), nullable=True)
    tipo_documento_mora_id = Column(Integer, ForeignKey("tipos_documento.id"), nullable=True) # New Field
    
    # Cuentas Contables Centralizadas (Overrides)
    cuenta_cartera_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True) # Para CXC (13, 14, 16...)
    cuenta_caja_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True) # Para Caja/Bancos (11...)
    cuenta_ingreso_intereses_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True) # Para Ingreso por Intereses (42...)
    
    # Flags Logicos
    interes_mora_habilitado = Column(Boolean, default=True)

    empresa = relationship("app.models.empresa.Empresa", back_populates="ph_configuracion")
    tipo_documento_recibo = relationship("app.models.tipo_documento.TipoDocumento", foreign_keys=[tipo_documento_recibo_id])
    tipo_documento_mora = relationship("app.models.tipo_documento.TipoDocumento", foreign_keys=[tipo_documento_mora_id])
    cuenta_cartera = relationship("app.models.plan_cuenta.PlanCuenta", foreign_keys=[cuenta_cartera_id])
    cuenta_caja = relationship("app.models.plan_cuenta.PlanCuenta", foreign_keys=[cuenta_caja_id])
    cuenta_ingreso_intereses = relationship("app.models.plan_cuenta.PlanCuenta", foreign_keys=[cuenta_ingreso_intereses_id])

    # --- NUEVO CAMPO: TIPO DE NEGOCIO (SECTOR) ---
    # Valores: 'PH_RESIDENCIAL', 'PH_COMERCIAL', 'TRANSPORTE', 'EDUCATIVO', 'PARQUEADERO', 'GENERICO'
    tipo_negocio = Column(String(50), nullable=False, default='PH_RESIDENCIAL')


