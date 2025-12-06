from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
# Importamos la tabla de asociación que creamos en el otro archivo
from app.models.permiso import usuario_roles

class Usuario(Base):
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey('empresas.id'))
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    
    nombre_completo = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    empresa = relationship("Empresa", back_populates="usuarios")
    
    # --- RELACIONES DEL NUEVO SISTEMA DE PERMISOS ---
    roles = relationship("Rol",
                         secondary=usuario_roles,
                         back_populates="usuarios")

    excepciones = relationship("UsuarioPermisoExcepcion", back_populates="usuario")

    # --- OTRAS RELACIONES EXISTENTES --
    logs_operacion = relationship("LogOperacion", back_populates="usuario")
    periodos_cerrados_por_usuario = relationship("PeriodoContableCerrado", back_populates="usuario")
    
    # >>>>> CORRECCIÓN CRÍTICA: RELACIÓN DE FAVORITOS FALTANTE <<<<<
    # Esta relación es obligatoria para vincular al usuario con sus accesos rápidos
    favoritos = relationship(
        "UsuarioFavorito", 
        back_populates="usuario", 
        cascade="all, delete-orphan" # Asegura que si el usuario se borra, sus favoritos también
    )
    # >>>>> FIN DE LA CORRECCIÓN <<<<<