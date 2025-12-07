from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base

class Cotizacion(Base):
    __tablename__ = 'cotizaciones'

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey('empresas.id'), nullable=False)
    
    # Consecutivo y Datos Básicos
    numero = Column(Integer, nullable=False)
    fecha = Column(Date, nullable=False)
    fecha_vencimiento = Column(Date, nullable=True) # Validez de la oferta
    
    # Relaciones Clave
    tercero_id = Column(Integer, ForeignKey('terceros.id'), nullable=True)
    # Bodega opcional en cotización, pero útil si se convierte a reserva
    bodega_id = Column(Integer, ForeignKey('bodegas.id'), nullable=True) 
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True)
    
    # Estado del Ciclo de Vida
    # BORRADOR -> APROBADA (Oferta Firme) -> FACTURADA -> ANULADA
    estado = Column(String(20), default='BORRADOR', nullable=False)
    
    observaciones = Column(Text, nullable=True)
    total_estimado = Column(Float, default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    tercero = relationship("Tercero")
    bodega = relationship("Bodega")
    usuario = relationship("Usuario")
    detalles = relationship("CotizacionDetalle", back_populates="cotizacion", cascade="all, delete-orphan")


class CotizacionDetalle(Base):
    __tablename__ = 'cotizaciones_detalles'

    id = Column(Integer, primary_key=True, index=True)
    cotizacion_id = Column(Integer, ForeignKey('cotizaciones.id'), nullable=False)
    producto_id = Column(Integer, ForeignKey('productos.id'), nullable=False)
    
    cantidad = Column(Float, nullable=False)
    precio_unitario = Column(Float, default=0.0)
    
    # Control para conversión parcial a factura (futuro)
    cantidad_facturada = Column(Float, default=0.0)    
    
    # Relaciones
    cotizacion = relationship("Cotizacion", back_populates="detalles")
    producto = relationship("Producto")
