
from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from ..core.database import Base

class EmpresaConfigEmail(Base):
    __tablename__ = "empresa_config_email"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    smtp_user = Column(String, nullable=False)      # Email address
    smtp_password_enc = Column(Text, nullable=False) # Encrypted App Password
    smtp_host = Column(String, default="smtp.gmail.com")
    smtp_port = Column(Integer, default=587)
    
    empresa = relationship("Empresa", back_populates="config_email")
