from sqlalchemy import Column, Integer, String, DateTime, LargeBinary
from datetime import datetime
from app.core.database import Base

class CopiaSeguridad(Base):
    __tablename__ = "copia_seguridad"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, nullable=True, index=True)
    fecha = Column(DateTime, default=datetime.utcnow)
    nombre_archivo = Column(String, index=True)
    datos_json = Column(LargeBinary, nullable=False)
    tamanio_mb = Column(String)
