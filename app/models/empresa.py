from sqlalchemy import Column, Integer, String, TIMESTAMP, text, Date
from sqlalchemy.orm import relationship
from ..core.database import Base

class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True)
    razon_social = Column(String(255), nullable=False)
    nit = Column(String(20), unique=True, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    fecha_inicio_operaciones = Column(Date, nullable=True)
    limite_registros = Column(Integer, nullable=True, default=None)
    precio_por_registro = Column(Integer, nullable=True, default=None) # Precio personalizado por registro (NULL = Usa Global)
    modo_operacion = Column(String(50), nullable=False, default='STANDARD') # STANDARD, AUDITORIA_READONLY

    # --- AGREGAR ESTAS LÍNEAS ---
    direccion = Column(String, nullable=True)
    telefono = Column(String, nullable=True)
    email = Column(String, nullable=True)
    logo_url = Column(String, nullable=True)
    
    # Configuración Contable
    prefijo_cxc = Column(String(10), nullable=False, default='13')
    prefijo_cxp = Column(String(10), nullable=False, default='2')
    # ----------------------------

    periodos_cerrados = relationship("PeriodoContableCerrado", back_populates="empresa")

    # --- INICIO: RELACIÓN FALTANTE AÑADIDA ---
    # Esta línea completa la relación con el modelo Usuario, resolviendo el error.
    usuarios = relationship("Usuario", back_populates="empresa")
    
    # Configuración de Correo (One-to-One)
    config_email = relationship("EmpresaConfigEmail", back_populates="empresa", uselist=False, cascade="all, delete-orphan")
    
    # Esto completa la relación con el modelo CupoAdicional
    # ...
    cupos_adicionales = relationship("CupoAdicional", back_populates="empresa", cascade="all, delete-orphan")