from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
# --- 1. Importar el componente que faltaba ---
from sqlalchemy.schema import UniqueConstraint
from ..core.database import Base

class Bodega(Base):
    __tablename__ = 'bodegas'
    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey('empresas.id'), nullable=False)
    nombre = Column(String(100), nullable=False)

    # --- 2. Añadir la directiva para crear la restricción de unicidad ---
    __table_args__ = (
        UniqueConstraint('empresa_id', 'nombre', name='uq_bodegas_empresa_nombre'),
    )