from sqlalchemy import Column, Integer, String, TIMESTAMP, text, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship, backref
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
    # Specify foreign_keys to resolve ambiguity with owner_id
    usuarios = relationship("Usuario", back_populates="empresa", foreign_keys="[Usuario.empresa_id]")
    
    # Configuración de Correo (One-to-One)
    config_email = relationship("EmpresaConfigEmail", back_populates="empresa", uselist=False, cascade="all, delete-orphan")
    
    # Esto completa la relación con el modelo CupoAdicional
    # This completes the relationship with the CupoAdicional model
    cupos_adicionales = relationship("CupoAdicional", back_populates="empresa", cascade="all, delete-orphan")

    # --- CAMPOS MULTI-TENANCY Y CONTADOR ---
    # Jerarquía (Holding/Contador)
    padre_id = Column(Integer, ForeignKey('empresas.id'), nullable=True)
    hijas = relationship("Empresa", 
                        backref=backref('padre', remote_side=[id]),
                        foreign_keys=[padre_id])

    # Control de Cupos (Administrativo)
    limite_registros_mensual = Column(Integer, nullable=True, default=1000)

    # Plantillas (Standardization)
    is_template = Column(Boolean, default=False)
    template_category = Column(String(50), nullable=True) # 'RETAIL', 'SERVICIOS', 'PH'

    # Propiedad y Desacople
    owner_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True)
    owner = relationship("Usuario", foreign_keys=[owner_id], backref="empresas_propiedad")