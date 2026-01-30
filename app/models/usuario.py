from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Table, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
# Importamos la tabla de asociación que creamos en el otro archivo
from app.models.permiso import usuario_roles

# --- TABLA DE ASOCIACIÓN USUARIO-EMPRESA ---
usuario_empresas = Table('usuario_empresas', Base.metadata,
    Column('usuario_id', Integer, ForeignKey('usuarios.id'), primary_key=True),
    Column('empresa_id', Integer, ForeignKey('empresas.id'), primary_key=True),
    Column('is_owner', Boolean, default=False) # Para marcar quién es el creador/contador principal
)

class Usuario(Base):
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey('empresas.id'), nullable=True) # Contexto activo o Empresa Holding
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    
    nombre_completo = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Specify foreign_keys to resolve ambiguity with Empresa.owner_id
    empresa = relationship("Empresa", back_populates="usuarios", foreign_keys=[empresa_id])
    
    # --- RELACIONES DEL NUEVO SISTEMA DE PERMISOS ---
    roles = relationship("Rol",
                         secondary=usuario_roles,
                         back_populates="usuarios")
    
    # --- MULTITENANCY: EMPRESAS ASIGNADAS (N:M) ---
    empresas_asignadas = relationship("Empresa",
                                      secondary=usuario_empresas,
                                      backref="usuarios_asignados")

    excepciones = relationship("UsuarioPermisoExcepcion", back_populates="usuario")

    # --- OTRAS RELACIONES EXISTENTES --
    logs_operacion = relationship("LogOperacion", back_populates="usuario")
    periodos_cerrados_por_usuario = relationship("PeriodoContableCerrado", back_populates="usuario")
    
    # >>>>> CORRECCIÓN CRÍTICA: RELACIÓN DE FAVORITOS FALTANTE <<<<<
    # Esta relación es obligatoria para vincular al usuario con sus accesos rápidos
    favoritos = relationship(
        "UsuarioFavorito", 
        back_populates="usuario", 
        cascade="all, delete-orphan" 
    )
    
    # --- BUSQUEDAS GUARDADAS ---
    busquedas_guardadas = relationship(
        "UsuarioBusqueda",
        back_populates="usuario",
        cascade="all, delete-orphan"
    )
    # >>>>> FIN DE LA CORRECCIÓN <<<<<