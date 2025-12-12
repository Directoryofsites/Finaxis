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
    # --- FIN: RELACIÓN FALTANTE AÑADIDA ---

    # En app/models/empresa.py, dentro de la clase Empresa agrega:
    # ...
    cupos_adicionales = relationship("CupoAdicional", back_populates="empresa", cascade="all, delete-orphan")