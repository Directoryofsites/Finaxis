from sqlalchemy import Column, Integer, Numeric, ForeignKey, TIMESTAMP, text
from sqlalchemy.orm import relationship # <-- IMPORTACIÓN CORREGIDA
from ..core.database import Base

class AplicacionPago(Base):
    __tablename__ = "aplicacion_pagos"

    id = Column(Integer, primary_key=True)
    documento_factura_id = Column(Integer, ForeignKey("documentos.id", ondelete="CASCADE"), nullable=False)
    documento_pago_id = Column(Integer, ForeignKey("documentos.id", ondelete="CASCADE"), nullable=False)
    valor_aplicado = Column(Numeric(18, 2), nullable=False)
    fecha_aplicacion = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    empresa_id = Column(Integer, ForeignKey("empresas.id", ondelete="CASCADE"))

    # --- RELACIONES BIDIRECCIONALES ---
    documento_factura = relationship(
        "Documento",
        foreign_keys=[documento_factura_id],
        back_populates="aplicaciones_recibidas"
    )

    documento_pago = relationship(
        "Documento",
        foreign_keys=[documento_pago_id],
        back_populates="aplicaciones_realizadas"
    )