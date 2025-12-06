from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base

class Remision(Base):
    __tablename__ = 'remisiones'

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey('empresas.id'), nullable=False)
    
    # Consecutivo y Datos Básicos
    numero = Column(Integer, nullable=False)
    fecha = Column(Date, nullable=False)
    fecha_vencimiento = Column(Date, nullable=True) # Para expirar la reserva
    
    # Relaciones Clave
    tercero_id = Column(Integer, ForeignKey('terceros.id'), nullable=True)
    bodega_id = Column(Integer, ForeignKey('bodegas.id'), nullable=False) # Bodega de donde se reserva
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True)
    
    # Estado del Ciclo de Vida
    # BORRADOR -> APROBADA (Reserva) -> FACTURADA_PARCIAL -> FACTURADA_TOTAL -> ANULADA -> VENCIDA
    estado = Column(String(20), default='BORRADOR', nullable=False)
    
    observaciones = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    tercero = relationship("Tercero")
    bodega = relationship("Bodega")
    usuario = relationship("Usuario")
    detalles = relationship("RemisionDetalle", back_populates="remision", cascade="all, delete-orphan")


class RemisionDetalle(Base):
    __tablename__ = 'remisiones_detalles'

    id = Column(Integer, primary_key=True, index=True)
    remision_id = Column(Integer, ForeignKey('remisiones.id'), nullable=False)
    producto_id = Column(Integer, ForeignKey('productos.id'), nullable=False)
    
    # Cantidades para control de Backorder
    cantidad_solicitada = Column(Float, nullable=False) # La cantidad original
    cantidad_facturada = Column(Float, default=0.0)    # Lo que ya se convirtió en factura
    cantidad_pendiente = Column(Float, nullable=False) # Lo que falta (Reserva activa)
    
    # Precio pactado (Congelamiento de precio)
    precio_unitario = Column(Float, default=0.0)
    
    # Relaciones
    remision = relationship("Remision", back_populates="detalles")
    producto = relationship("Producto")
