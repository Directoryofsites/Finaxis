from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class PHCampoPersonalizado(Base):
    __tablename__ = "ph_campos_personalizados"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    
    entidad = Column(String(50), nullable=False) # ej: "unidades", "terceros"
    etiqueta = Column(String(100), nullable=False) # ej: "Placa del Vehículo"
    llave_json = Column(String(100), nullable=False) # ej: "placa_vehiculo"
    tipo = Column(String(50), default="text") # text, number, date, boolean
    obligatorio = Column(Boolean, default=False)
    activo = Column(Boolean, default=True)

    empresa = relationship("Empresa")
