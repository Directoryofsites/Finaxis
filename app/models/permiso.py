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
    nombre = Column(String(100), unique=True, index=True, nullable=False)
    descripcion = Column(String(255))
    
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