# app/models/regla_precio_grupo.py

from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint
from ..core.database import Base

class ReglaPrecioGrupo(Base):
    __tablename__ = 'reglas_precio_grupo'
    id = Column(Integer, primary_key=True, index=True)
    grupo_inventario_id = Column(Integer, ForeignKey('grupos_inventario.id'), nullable=False)
    lista_precio_id = Column(Integer, ForeignKey('listas_precio.id'), nullable=False)
    # Porcentaje como decimal (ej: 0.30 para +30%, -0.10 para -10%)
    porcentaje_incremento = Column(Float, nullable=False, default=0.0)

    # Relaciones
    grupo_inventario = relationship('GrupoInventario', back_populates='reglas_precio')
    lista_precio = relationship('ListaPrecio') # Relación simple a ListaPrecio

    __table_args__ = (
        # Asegura que solo haya una regla por grupo y lista de precios
        UniqueConstraint('grupo_inventario_id', 'lista_precio_id', name='uq_regla_precio_grupo_grupo_lista'),
    )