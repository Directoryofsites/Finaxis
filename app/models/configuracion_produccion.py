from sqlalchemy import Column, Integer, ForeignKey
from app.core.database import Base

class ConfiguracionProduccion(Base):
    __tablename__ = 'produccion_configuracion'

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey('empresas.id'), unique=True, nullable=False)

    # Document Type for Standard Production Orders
    tipo_documento_orden_id = Column(Integer, ForeignKey('tipos_documento.id'), nullable=True)
    
    # Document Type for Annulment/Reversal (Devoluciones)
    tipo_documento_anulacion_id = Column(Integer, ForeignKey('tipos_documento.id'), nullable=True)

    # Puede haber más configs aquí (bodegas por defecto, etc.)
