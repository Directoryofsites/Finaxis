from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from ..core.database import Base

class SoporteTicket(Base):
    __tablename__ = "soporte_tickets"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    tercero_id = Column(Integer, ForeignKey("terceros.id"), nullable=False)
    asunto = Column(String(255), nullable=False)
    tipo = Column(String(50), nullable=False) # Reclamo, Consulta, Sugerencia, etc.
    mensaje = Column(Text, nullable=False)
    estado = Column(String(20), default="ABIERTO") # ABIERTO, PROCESO, CERRADO
    respuesta_soporte = Column(Text, nullable=True)
    
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now())

    # No agregamos relaciones explícitas aquí para evitar imports circulares pesados,
    # pero las definiremos en el seeder o donde se necesite.
