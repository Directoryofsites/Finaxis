from sqlalchemy import Column, Integer, ForeignKey, Text, Numeric
from sqlalchemy.orm import relationship
from ..core.database import Base
from sqlalchemy.schema import UniqueConstraint

# --- MODELO PARA MOVIMIENTOS ACTIVOS ---
class MovimientoContable(Base):
    __tablename__ = "movimientos_contables"

    id = Column(Integer, primary_key=True, index=True)
    documento_id = Column(Integer, ForeignKey("documentos.id"), nullable=False)
    cuenta_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=False)
    centro_costo_id = Column(Integer, ForeignKey("centros_costo.id"), nullable=True)

    # --- INICIO: NUEVAS COLUMNAS AÑADIDAS ---
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=True)
    cantidad = Column(Numeric(15, 2), nullable=True)
    # --- FIN: NUEVAS COLUMNAS ---

    concepto = Column(Text)
    debito = Column(Numeric(15, 2), default=0)
    credito = Column(Numeric(15, 2), default=0)

    # Relaciones
    cuenta = relationship("PlanCuenta")
    documento = relationship("Documento", back_populates="movimientos")
    centro_costo = relationship("CentroCosto", back_populates="movimientos")
    
    # --- INICIO: NUEVA RELACIÓN AÑADIDA ---

    producto = relationship("Producto", back_populates="movimientos_contables")
    # --- FIN: NUEVA RELACIÓN ---


# --- MODELO PARA MOVIMIENTOS ELIMINADOS ---
class MovimientoEliminado(Base):
    __tablename__ = "movimientos_eliminados"

    id = Column(Integer, primary_key=True, index=True)
    id_original = Column(Integer, nullable=False, index=True)

    # Foreign key al documento ELIMINADO
    documento_eliminado_id = Column(Integer, ForeignKey("documentos_eliminados.id"), nullable=False)
    documento_id_original = Column(Integer, nullable=False)

    cuenta_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=False)
    centro_costo_id = Column(Integer, ForeignKey("centros_costo.id"), nullable=True) # Columna que faltaba

    concepto = Column(Text)
    debito = Column(Numeric(15, 2), default=0)
    credito = Column(Numeric(15, 2), default=0)

    # Relación de vuelta al documento eliminado
    documento_eliminado = relationship("DocumentoEliminado", back_populates="movimientos")
    # Relaciones para poder navegar desde el movimiento eliminado a su cuenta y centro de costo
    cuenta = relationship("PlanCuenta")
    centro_costo = relationship("CentroCosto")