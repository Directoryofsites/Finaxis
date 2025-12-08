from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from ..core.database import Base

class ConfiguracionReporte(Base):
    __tablename__ = 'configuraciones_reportes'

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey('empresas.id'), nullable=False)
    
    # Tipo de reporte: 'IVA', 'RENTA', 'ICA', etc.
    tipo_reporte = Column(String(20), nullable=False, index=True)
    
    # Identificador del renglón en el formulario (ej: "27", "58")
    renglon = Column(String(10), nullable=False)
    
    # Descripción del concepto (ej: "Ingresos por operaciones gravadas 5%")
    concepto = Column(String(255), nullable=True)
    
    # Lista de códigos de cuenta (Strings) o IDs. 
    # Usaremos códigos de cuenta (ej: ["413505", "413510"]) ser más portable si el ID cambia.
    # O IDs si queremos integridad referencial estricta.
    # El plan mencionaba "cuentas_ids = Column(JSON)". 
    # Pero para import/export es mejor códigos. 
    # Sin embargo, el Plan decia IDs. Me atendré al plan pero con flexibilidad (Array de ints).
    cuentas_ids = Column(JSON, default=[]) 
    
    # Relaciones
    empresa = relationship("Empresa")
