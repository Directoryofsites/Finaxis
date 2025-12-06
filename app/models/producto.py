# app/models/producto.py (Versión con Precio Base Manual y Valores de Características)

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, func
# Quitar JSONB si ya no se usa directamente aquí
# from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint
from ..core.database import Base

class Producto(Base):
    __tablename__ = 'productos'
    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey('empresas.id'), nullable=False)
    grupo_id = Column(Integer, ForeignKey('grupos_inventario.id'), nullable=True)
    impuesto_iva_id = Column(Integer, ForeignKey('tasas_impuesto.id'), nullable=True) # Mantenemos impuesto a nivel de producto
    codigo = Column(String(50), nullable=False, index=True)
    nombre = Column(String(255), nullable=False, index=True)
    es_servicio = Column(Boolean, nullable=False, default=False)
    metodo_costeo = Column(String(50), nullable=False, default='promedio_ponderado') # Se mantiene
    costo_promedio = Column(Float, nullable=False, default=0.0) # Se mantiene como base
    # --- CAMBIO: Precio venta base se elimina, usamos precio_base_manual ---
    # precio_venta = Column(Float, nullable=False, default=0.0)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    # --- CAMBIO: Eliminados campos que van a características ---
    # unidad_medida = Column(String(50), nullable=True, default='Unidad')
    # caracteristicas = Column(JSONB, nullable=True)

    # --- CAMBIO: Mantenemos topes ---
    stock_minimo = Column(Float, nullable=True, default=0.0) # Se mantiene
    stock_maximo = Column(Float, nullable=True, default=0.0) # Se mantiene

    # --- INICIO NUEVO CAMPO PRECIO BASE MANUAL ---
    precio_base_manual = Column(Float, nullable=True) # Si tiene valor, anula costo_promedio para cálculo de precios
    # --- FIN NUEVO CAMPO PRECIO BASE MANUAL ---

    # Relaciones (Modificadas)
    grupo_inventario = relationship('GrupoInventario', back_populates='productos')
    impuesto_iva = relationship('TasaImpuesto', foreign_keys=[impuesto_iva_id])
    stocks_bodega = relationship('StockBodega', back_populates='producto', cascade="all, delete-orphan") # Se mantiene
    movimientos = relationship('MovimientoInventario', back_populates='producto', cascade="all, delete-orphan") # Se mantiene
    movimientos_contables = relationship('MovimientoContable', back_populates='producto') # Se mantiene

    # --- CAMBIO: Eliminada relación precios (a precio_producto) ---
    # precios = relationship('PrecioProducto', back_populates='producto', cascade="all, delete-orphan")

    # --- INICIO NUEVA RELACIÓN VALORES CARACTERÍSTICAS ---
    valores_caracteristicas = relationship(
        'CaracteristicaValorProducto',
        back_populates='producto',
        cascade="all, delete-orphan" # Si se borra el producto, se borran sus valores
    )
    # --- FIN NUEVA RELACIÓN VALORES CARACTERÍSTICAS ---

    __table_args__ = (
        UniqueConstraint('empresa_id', 'codigo', name='uq_productos_empresa_codigo'),
    )

# --- Modelo StockBodega (sin cambios) ---
class StockBodega(Base):
    __tablename__ = 'stock_bodegas'
    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey('productos.id'), nullable=False)
    bodega_id = Column(Integer, ForeignKey('bodegas.id'), nullable=False)
    stock_actual = Column(Float, nullable=False, default=0.0)
    # --- CAMBIO: Nuevo campo para manejar reservas de remisiones ---
    stock_comprometido = Column(Float, nullable=False, default=0.0) 
    # Formula: Stock Disponible = stock_actual - stock_comprometido
    # ---------------------------------------------------------------
    producto = relationship('Producto', back_populates='stocks_bodega')
    bodega = relationship('Bodega')
    __table_args__ = ( UniqueConstraint('producto_id', 'bodega_id', name='uq_stock_bodegas_producto_bodega'), )

# --- Modelo MovimientoInventario (sin cambios) ---
class MovimientoInventario(Base):
    __tablename__ = 'movimientos_inventario'
    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey('productos.id'), nullable=False)
    bodega_id = Column(Integer, ForeignKey('bodegas.id'), nullable=False)
    documento_id = Column(Integer, ForeignKey('documentos.id'), nullable=True)
    fecha = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    tipo_movimiento = Column(String(50), nullable=False)
    cantidad = Column(Float, nullable=False)
    costo_unitario = Column(Float, nullable=False)
    costo_total = Column(Float, nullable=False)
    producto = relationship('Producto', back_populates='movimientos')
    bodega = relationship('Bodega')
    documento = relationship('Documento')