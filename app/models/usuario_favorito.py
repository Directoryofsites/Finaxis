# app/models/usuario_favorito.py

from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from ..core.database import Base

class UsuarioFavorito(Base):
    __tablename__ = 'usuarios_favoritos'
    
    id = Column(Integer, primary_key=True, index=True)
    
    # FK al usuario que creó este favorito
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    
    # Nombre que el usuario le da al botón (Ej: "Factura Rápida")
    nombre_personalizado = Column(String(100), nullable=False)
    
    # Ruta de la aplicación (Ej: /contabilidad/facturacion)
    ruta_enlace = Column(String(255), nullable=False)
    
    # Posición en el dashboard (1 a 6)
    # Posición en el dashboard (1 a 12), reflejando la nueva regla de negocio.
    orden = Column(Integer, nullable=False) 

    # Relaciones
    usuario = relationship("Usuario", back_populates="favoritos")

    # Asegura que un usuario no tenga dos favoritos en la misma posición (orden)
    __table_args__ = (
        UniqueConstraint('usuario_id', 'orden', name='uq_usuario_favorito_orden'),
    )

# --- Se requiere actualizar models/usuario.py para añadir la relación inversa. ---
# (Lo haremos en el siguiente sub-paso).