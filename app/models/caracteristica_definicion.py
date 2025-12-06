# app/models/caracteristica_definicion.py

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint
from ..core.database import Base

class CaracteristicaDefinicion(Base):
    __tablename__ = 'caracteristica_definiciones'
    id = Column(Integer, primary_key=True, index=True)
    grupo_inventario_id = Column(Integer, ForeignKey('grupos_inventario.id'), nullable=False)
    nombre = Column(String(100), nullable=False) # Ej: "Color", "Talla", "Unidad Medida", "Material"
    # Podríamos añadir tipo_dato si quisiéramos validaciones más estrictas (ej: 'texto', 'numero', 'lista')
    # tipo_dato = Column(String(50), default='texto')
    es_unidad_medida = Column(Boolean, default=False) # Flag especial para identificar la unidad
    # Podríamos añadir es_obligatorio si fuera necesario
    # es_obligatorio = Column(Boolean, default=False)

    # Relación con GrupoInventario
    grupo_inventario = relationship('GrupoInventario', back_populates='caracteristicas_definidas')

    # Relación inversa con los valores asignados a productos
    valores_producto = relationship('CaracteristicaValorProducto', back_populates='definicion', cascade="all, delete-orphan")

    __table_args__ = (
        # Asegura que no se repita el nombre de característica dentro del mismo grupo
        UniqueConstraint('grupo_inventario_id', 'nombre', name='uq_caracteristica_definicion_grupo_nombre'),
    )