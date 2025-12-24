from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base

class UsuarioBusqueda(Base):
    __tablename__ = 'usuarios_busquedas_guardadas'

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    
    # El título que el usuario le da (ej: "Reporte Mensual Jefe")
    titulo = Column(String(100), nullable=False)
    
    # El comando completo (ej: "Movimientos detallados de inventario...")
    comando = Column(Text, nullable=False)
    
    # Parámetros JSON opcionales para reconstruir estado exacto (futuro)
    parametros = Column(Text, nullable=True) 
    
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="busquedas_guardadas")
