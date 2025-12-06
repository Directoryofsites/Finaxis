# app/models/lista_precio.py (Versión con relación inversa a Tercero)

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint
from ..core.database import Base

class ListaPrecio(Base):
    __tablename__ = 'listas_precio'
    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey('empresas.id'), nullable=False)
    nombre = Column(String(100), nullable=False)

    # Relación inversa con ReglaPrecioGrupo
    reglas_grupo = relationship('ReglaPrecioGrupo', back_populates='lista_precio', cascade="all, delete-orphan")

    # --- INICIO NUEVA RELACIÓN INVERSA ---
    terceros = relationship('Tercero', back_populates='lista_precio')
    # --- FIN NUEVA RELACIÓN INVERSA ---

    __table_args__ = (
        UniqueConstraint('empresa_id', 'nombre', name='uq_listas_precio_empresa_nombre'),
    )