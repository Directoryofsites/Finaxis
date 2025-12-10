from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Enum, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..core.database import Base

class EstadoOrdenProduccion(str, enum.Enum):
    PLANIFICADA = "PLANIFICADA"
    EN_PROCESO = "EN_PROCESO"
    CERRADA = "CERRADA"
    CANCELADA = "CANCELADA"

class TipoRecurso(str, enum.Enum):
    MOD = "MANO_OBRA_DIRECTA"
    CIF = "COSTO_INDIRECTO_FABRICACION"

class Receta(Base):
    __tablename__ = 'recetas'

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey('empresas.id'), nullable=False)
    producto_id = Column(Integer, ForeignKey('productos.id'), nullable=False) # El producto que se fabrica
    nombre = Column(String(255), nullable=False) # Ej: "Silla Estándar v1"
    descripcion = Column(String(500), nullable=True)
    cantidad_base = Column(Float, default=1.0) # Para cuánto alcanza esta receta (ej: 1 unidad, 100 litros)
    activa = Column(Boolean, default=True)
    
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    producto = relationship("Producto", backref="recetas") # backref para acceder desde Producto
    detalles = relationship("RecetaDetalle", back_populates="receta", cascade="all, delete-orphan")
    ordenes = relationship("OrdenProduccion", back_populates="receta")

class RecetaDetalle(Base):
    __tablename__ = 'receta_detalles'

    id = Column(Integer, primary_key=True, index=True)
    receta_id = Column(Integer, ForeignKey('recetas.id'), nullable=False)
    insumo_id = Column(Integer, ForeignKey('productos.id'), nullable=False) # Materia prima
    cantidad = Column(Float, nullable=False) # Cantidad requerida para la cantidad_base de la receta
    
    # Relaciones
    receta = relationship("Receta", back_populates="detalles")
    insumo = relationship("Producto")

class OrdenProduccion(Base):
    __tablename__ = 'ordenes_produccion'

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey('empresas.id'), nullable=False)
    numero_orden = Column(String(50), nullable=False) # Consecutivo OP-001
    
    producto_id = Column(Integer, ForeignKey('productos.id'), nullable=False)
    receta_id = Column(Integer, ForeignKey('recetas.id'), nullable=True) # Opcional, si se basó en una receta
    bodega_destino_id = Column(Integer, ForeignKey('bodegas.id'), nullable=False) # Dónde entrará el PT
    
    cantidad_planeada = Column(Float, nullable=False)
    cantidad_real = Column(Float, nullable=True, default=0.0) # Se llena al cierre
    
    estado = Column(String(50), default=EstadoOrdenProduccion.PLANIFICADA) # Usamos String para compatibilidad fácil, validado por Enum en código
    
    fecha_inicio = Column(Date, nullable=False, default=func.current_date())
    fecha_fin = Column(Date, nullable=True) # Fecha de cierre
    
    # Costos Acumulados (Snapshot al cierre)
    costo_total_mp = Column(Float, default=0.0)
    costo_total_mod = Column(Float, default=0.0)
    costo_total_cif = Column(Float, default=0.0)
    costo_unitario_final = Column(Float, default=0.0)
    
    observaciones = Column(String(1000), nullable=True)
    
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    producto = relationship("Producto")
    receta = relationship("Receta", back_populates="ordenes")
    bodega_destino = relationship("Bodega")
    
    insumos = relationship("OrdenProduccionInsumo", back_populates="orden", cascade="all, delete-orphan")
    recursos = relationship("OrdenProduccionRecurso", back_populates="orden", cascade="all, delete-orphan")

class OrdenProduccionInsumo(Base):
    """
    Registra el consumo REAL de materia prima. 
    Se llena automáticamente al despachar desde bodega.
    """
    __tablename__ = 'orden_produccion_insumos'

    id = Column(Integer, primary_key=True, index=True)
    orden_id = Column(Integer, ForeignKey('ordenes_produccion.id'), nullable=False)
    insumo_id = Column(Integer, ForeignKey('productos.id'), nullable=False)
    bodega_origen_id = Column(Integer, ForeignKey('bodegas.id'), nullable=False) # De dónde salió
    
    cantidad = Column(Float, nullable=False)
    costo_unitario_historico = Column(Float, nullable=False) # Costo promedio al momento del despacho
    costo_total = Column(Float, nullable=False) # cantidad * costo_unitario_historico
    
    fecha_despacho = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    orden = relationship("OrdenProduccion", back_populates="insumos")
    insumo = relationship("Producto")
    bodega_origen = relationship("Bodega")

class OrdenProduccionRecurso(Base):
    """
    Registra costos de MOD y CIF asignados a la orden.
    Ej: "Horas Tornero J.Perez", "Electricidad Estimada"
    """
    __tablename__ = 'orden_produccion_recursos'

    id = Column(Integer, primary_key=True, index=True)
    orden_id = Column(Integer, ForeignKey('ordenes_produccion.id'), nullable=False)
    
    descripcion = Column(String(255), nullable=False)
    tipo = Column(String(50), nullable=False) # Enum: MOD o CIF
    valor = Column(Float, nullable=False) # Valor monetario total
    
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    orden = relationship("OrdenProduccion", back_populates="recursos")
