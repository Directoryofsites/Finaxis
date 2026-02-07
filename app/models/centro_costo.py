from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint  # <-- 1. Importar UniqueConstraint
from app.core.database import Base

class CentroCosto(Base):
    __tablename__ = "centros_costo"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), nullable=False, index=True)
    nombre = Column(String(255), nullable=False)
    nivel = Column(Integer, nullable=False)
    permite_movimiento = Column(Boolean, default=True)
    
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    
    centro_costo_padre_id = Column(Integer, ForeignKey("centros_costo.id"), nullable=True)
    
    created_by = Column(Integer, ForeignKey("usuarios.id"))
    updated_by = Column(Integer, ForeignKey("usuarios.id"))

    empresa = relationship("Empresa")
    creador = relationship("Usuario", foreign_keys=[created_by])
    actualizador = relationship("Usuario", foreign_keys=[updated_by])
    
    padre = relationship("CentroCosto", remote_side=[id], back_populates="hijos")
    hijos = relationship("CentroCosto", back_populates="padre", cascade="all, delete-orphan")
    
    documentos = relationship("app.models.documento.Documento", back_populates="centro_costo") # <-- NUEVA
    movimientos = relationship("MovimientoContable", back_populates="centro_costo")
    plantillas_detalles = relationship("PlantillaDetalle", back_populates="centro_costo")
    plantillas_maestras_sugeridas = relationship("PlantillaMaestra", back_populates="centro_costo_sugerido")
    conceptos_favoritos = relationship("ConceptoFavorito", back_populates="centro_costo")

    # --- INICIO: CORRECCIÓN CRÍTICA ---
    # 2. Añadir la restricción de unicidad a nivel de tabla.
    __table_args__ = (
        UniqueConstraint('empresa_id', 'codigo', name='uq_centros_costo_empresa_codigo'),
    )
    # --- FIN: CORRECCIÓN CRÍTICA ---