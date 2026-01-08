from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.core.database import Base

# Tabla de Asociación: Usuario <-> Rol (Muchos a Muchos)
usuario_roles = Table('usuario_roles', Base.metadata,
    Column('usuario_id', Integer, ForeignKey('usuarios.id'), primary_key=True),
    Column('rol_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

# Tabla de Asociación: Rol <-> Permiso (Muchos a Muchos)
rol_permisos = Table('rol_permisos', Base.metadata,
    Column('rol_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permiso_id', Integer, ForeignKey('permisos.id'), primary_key=True)
)

class Rol(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False) # unique=True removido, se maneja con constraint compuesto
    descripcion = Column(String(255))
    empresa_id = Column(Integer, ForeignKey('empresas.id'), nullable=True)
    
    # Hacemos que el nombre sea único POR empresa.
    # Si empresa_id es NULL (rol global), la BD permite múltiples NULLs en teoría en Standard SQL, 
    # pero queremos solo 1 rol global con ese nombre.
    # En la práctica, validaremos en lógica de negocio o usaremos índice parcial si el motor lo soporta.
    # Para simplificar: UniqueConstraint(nombre, empresa_id)
    __table_args__ = (
        # UniqueConstraint('nombre', 'empresa_id', name='uq_rol_nombre_empresa'),
        # Nota: Dejamos esto comentado por ahora para evitar conflictos inmediatos sin migración.
        # La integridad se validará en código por el momento.
    )
    
    # Relación con Permisos   

    permisos = relationship("Permiso", secondary=rol_permisos, back_populates="roles")

    # Relación con Usuarios
    usuarios = relationship("Usuario", secondary=usuario_roles, back_populates="roles")

class Permiso(Base):
    __tablename__ = 'permisos'
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, index=True, nullable=False) # ej: "crear_documento"
    descripcion = Column(String(255))

    # Relación con Roles
    roles = relationship("Rol", secondary=rol_permisos, back_populates="permisos")

class UsuarioPermisoExcepcion(Base):
    __tablename__ = 'usuario_permisos_excepciones'
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), primary_key=True)
    permiso_id = Column(Integer, ForeignKey('permisos.id'), primary_key=True)
    
    # True para permitir, False para denegar explícitamente
    permitido = Column(Boolean, nullable=False)

    usuario = relationship("Usuario", back_populates="excepciones")
    permiso = relationship("Permiso")