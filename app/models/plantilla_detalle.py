from sqlalchemy import Column, Integer, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship
from ..core.database import Base

class PlantillaDetalle(Base):
    __tablename__ = "plantillas_detalles"

    id = Column(Integer, primary_key=True, index=True)

    # --- CAMBIO CRÍTICO: Se añade ondelete="CASCADE" ---
    # Si se borra la PlantillaMaestra, este detalle se borrará automáticamente.
    plantilla_maestra_id = Column(Integer, ForeignKey("plantillas_maestras.id", ondelete="CASCADE"), nullable=False)

    # --- CAMBIO CRÍTICO: Se añade ondelete="CASCADE" ---
    # Si se borra una Cuenta del Plan de Cuentas, este detalle se borrará.
    # Esto previene que una plantilla quede con cuentas huérfanas.
    cuenta_id = Column(Integer, ForeignKey("plan_cuentas.id", ondelete="CASCADE"), nullable=False)

    # --- CAMBIO CRÍTICO: Se añade ondelete="SET NULL" ---
    # Si se borra un Centro de Costo, este campo se pondrá en NULL.
    # Usamos SET NULL porque el campo es nulable.
    centro_costo_id = Column(Integer, ForeignKey("centros_costo.id", ondelete="SET NULL"), nullable=True)

    concepto = Column(Text, nullable=True)
    debito = Column(Numeric(15, 2), default=0)
    credito = Column(Numeric(15, 2), default=0)

    # --- RELACIONES SINCRONIZADAS ---
    maestra = relationship("PlantillaMaestra", back_populates="detalles")
    centro_costo = relationship("CentroCosto", back_populates="plantillas_detalles")
    cuenta = relationship("PlanCuenta")
    # --- FIN RELACIONES ---