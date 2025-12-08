from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Numeric, Date, Text
from sqlalchemy.orm import relationship
from ..core.database import Base
import enum

class EstadoActivo(str, enum.Enum):
    ACTIVO = "ACTIVO"
    EN_MANTENIMIENTO = "EN_MANTENIMIENTO"
    BAJA_PENDIENTE = "BAJA_PENDIENTE" # Dado de baja pero aun en bodega
    BAJA_DEFINITIVA = "BAJA_DEFINITIVA" # Vendido, robado, chatarrízado
    TOT_DEPRECIADO = "TOT_DEPRECIADO" # Sigue en uso pero vale 0 (o residual)

class ActivoFijo(Base):
    __tablename__ = "activos_fijos"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    
    # Identificación
    codigo = Column(String(50), nullable=False,  doc="Placa de inventario o código interno")
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    serial = Column(String(100), nullable=True)
    modelo = Column(String(100), nullable=True)
    marca = Column(String(100), nullable=True)
    
    categoria_id = Column(Integer, ForeignKey("activos_categorias.id"), nullable=False)
    
    # Ubicación y Responsabilidad
    ubicacion = Column(String(200), nullable=True, doc="Texto libre: Sede Administrativa, Bodega 1, etc.")
    responsable_id = Column(Integer, ForeignKey("terceros.id"), nullable=True, doc="Empleado a cargo del bien")
    centro_costo_id = Column(Integer, ForeignKey("centros_costo.id"), nullable=True)
    
    # Adquisición
    fecha_compra = Column(Date, nullable=False)
    fecha_inicio_uso = Column(Date, nullable=True, doc="Fecha desde la cual inicia depreciación")
    proveedor_id = Column(Integer, ForeignKey("terceros.id"), nullable=True)
    numero_factura = Column(String(50), nullable=True)
    
    # Valores Históricos
    costo_adquisicion = Column(Numeric(18, 2), default=0, nullable=False)
    valor_residual = Column(Numeric(18, 2), default=0, nullable=False, doc="Valor de salvamento estimado al final de la vida útil")
    
    # Valores Actuales (Calculados)
    depreciacion_acumulada_niif = Column(Numeric(18, 2), default=0)
    depreciacion_acumulada_fiscal = Column(Numeric(18, 2), default=0)
    
    estado = Column(Enum(EstadoActivo), default=EstadoActivo.ACTIVO, nullable=False)
    
    # Relaciones
    categoria = relationship("ActivoCategoria", back_populates="activos")
    responsable = relationship("Tercero", foreign_keys=[responsable_id])
    proveedor = relationship("Tercero", foreign_keys=[proveedor_id])
    centro_costo = relationship("CentroCosto")
    
    novedades = relationship("ActivoNovedad", back_populates="activo", cascade="all, delete-orphan")
