# app/models/caracteristica_valor_producto.py

from sqlalchemy import Column, Integer, String, Float, ForeignKey # Añadir Float si usamos valor_numero
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint
from ..core.database import Base

class CaracteristicaValorProducto(Base):
    __tablename__ = 'caracteristica_valores_producto'
    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey('productos.id'), nullable=False)
    definicion_id = Column(Integer, ForeignKey('caracteristica_definiciones.id'), nullable=False)
    # Almacenamos el valor como texto por simplicidad. Se podría expandir a valor_numero, etc.
    valor = Column(String(255), nullable=True) # El valor específico (ej: "Rojo", "L", "Unidad")

    # Relaciones
    producto = relationship('Producto', back_populates='valores_caracteristicas')
    definicion = relationship('CaracteristicaDefinicion', back_populates='valores_producto')

    __table_args__ = (
        # Asegura que un producto solo tenga un valor para cada característica definida
        UniqueConstraint('producto_id', 'definicion_id', name='uq_caracteristica_valor_producto_prod_def'),
    )