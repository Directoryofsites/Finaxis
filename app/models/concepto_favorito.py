from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, text
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class ConceptoFavorito(Base):
    __tablename__ = "conceptos_favoritos"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    descripcion = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    created_by = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    
    centro_costo_id = Column(Integer, ForeignKey("centros_costo.id"), nullable=True)
    # FIX CRÍTICO: Revertimos a relación simple para evitar el error de back_populates faltante en Empresa.
    empresa = relationship("Empresa") 
    creador = relationship("Usuario", foreign_keys=[created_by])
    actualizador = relationship("Usuario", foreign_keys=[updated_by])
    centro_costo = relationship("CentroCosto")
    
    __table_args__ = (
        UniqueConstraint('empresa_id', 'descripcion', name='uq_conceptos_favoritos_empresa_descripcion'),
    )