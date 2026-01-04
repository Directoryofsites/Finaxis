from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class ImportTemplate(Base):
    __tablename__ = "import_templates"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String(255), nullable=True)
    
    # Stores the mapping configuration
    # Example: {"fecha": 0, "tipo_doc": 1, "numero": 2, "tercero": 3, "cuenta": 4, "debito": 5, "credito": 6}
    mapping_config = Column(JSON, nullable=False)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    empresa = relationship("Empresa", backref="plantillas_importacion")

    def __repr__(self):
        return f"<ImportTemplate(nombre={self.nombre}, empresa_id={self.empresa_id})>"
