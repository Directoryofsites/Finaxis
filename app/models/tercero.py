# app/models/tercero.py (Versión con lista_precio_id)

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint
from ..core.database import Base

class Tercero(Base):
    __tablename__ = "terceros"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    nit = Column(String(20), nullable=False, index=True)
    dv = Column(String(1), nullable=True)
    razon_social = Column(String(255), nullable=False, index=True)
    nombre_comercial = Column(String(255), nullable=True)
    es_cliente = Column(Boolean, default=False)
    es_proveedor = Column(Boolean, default=False)
    es_empleado = Column(Boolean, nullable=False, default=False)
    responsabilidad_fiscal = Column(String(100), nullable=True)
    direccion = Column(String(255), nullable=True)
    ciudad = Column(String(100), nullable=True)
    telefono = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    actividad_economica_ciiu = Column(String(10), nullable=True)
    es_regimen_simple = Column(Boolean, nullable=False, default=False)
    
    # --- FACTURACIÓN ELECTRÓNICA ---
    tipo_documento = Column(String(5), nullable=True, default='13', comment="13=Cedula, 31=NIT")
    tipo_persona = Column(String(1), nullable=True, default='2', comment="1=Juridica, 2=Natural")
    municipio_dane = Column(String(10), nullable=True)
    codigo_postal = Column(String(10), nullable=True)
    regimen_fiscal = Column(String(5), nullable=True)
    responsabilidad_fiscal = Column(String(20), nullable=True)
    # -------------------------------

    # --- INICIO NUEVA COLUMNA Y RELACIÓN ---
    lista_precio_id = Column(Integer, ForeignKey('listas_precio.id'), nullable=True)
    lista_precio = relationship('ListaPrecio', back_populates='terceros')
    # --- FIN NUEVA COLUMNA Y RELACIÓN ---

    created_by = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    # Relación para documentos ACTIVOS
    documentos = relationship("Documento", back_populates="beneficiario")

    # Relación separada para documentos ELIMINADOS
    documentos_eliminados = relationship("DocumentoEliminado", back_populates="beneficiario")

    # Relación para poder acceder a las plantillas que sugieren este tercero
    plantillas = relationship("PlantillaMaestra", back_populates="beneficiario")

    # Regla de unicidad
    __table_args__ = (
        UniqueConstraint('empresa_id', 'nit', name='uq_tercero_empresa_nit'),
    )