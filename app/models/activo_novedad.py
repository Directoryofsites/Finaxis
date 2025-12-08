from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Numeric, Date, JSON
from sqlalchemy.orm import relationship
from ..core.database import Base
import enum

class TipoNovedadActivo(str, enum.Enum):
    ALTA = "ALTA" # Compra inicial
    DEPRECIACION = "DEPRECIACION" # Cierre de mes
    ADICION = "ADICION" # Mejora capitalizable
    DETERIORO = "DETERIORO" # Pérdida de valor extraordinaria
    TRASLADO = "TRASLADO" # Cambio de responsable o ubicación
    BAJA = "BAJA" # Venta o retiro

class ActivoNovedad(Base):
    __tablename__ = "activos_novedades"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    
    activo_id = Column(Integer, ForeignKey("activos_fijos.id"), nullable=False)
    fecha = Column(Date, nullable=False)
    
    tipo = Column(Enum(TipoNovedadActivo), nullable=False)
    
    valor = Column(Numeric(18, 2), default=0, doc="Valor monetario del movimiento (si aplica)")
    observacion = Column(String(500), nullable=True)
    
    # JSON para guardar detalles flexibles (Ej: {"ubicacion_anterior": "Bodega 1", "ubicacion_nueva": "Oficina"}
    detalles = Column(JSON, nullable=True)
    
    created_by = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    
    # Vínculo con Contabilidad
    documento_contable_id = Column(Integer, ForeignKey("documentos.id"), nullable=True, doc="Si generó un asiento, aquí se vincula")
    
    # Relaciones
    activo = relationship("ActivoFijo", back_populates="novedades")
    usuario = relationship("Usuario")
    documento = relationship("Documento")
