from sqlalchemy import Column, String
from app.core.database import Base

class ConfiguracionSistema(Base):
    __tablename__ = "configuracion_sistema"

    clave = Column(String, primary_key=True, index=True)
    valor = Column(String, nullable=False)
