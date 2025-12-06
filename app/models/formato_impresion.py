from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP, text
from sqlalchemy import JSON
from sqlalchemy.orm import relationship # <--- Importar relationship
from ..core.database import Base

class FormatoImpresion(Base):
    __tablename__ = "formatos_documento_impresion"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    nombre = Column(String(255), nullable=False, unique=True)
    tipo_documento_id = Column(Integer, ForeignKey("tipos_documento.id"), nullable=True)
    contenido_html = Column(Text, nullable=False)
    variables_ejemplo_json = Column(JSON, nullable=True)
    creado_por_usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    fecha_creacion = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    ultima_modificacion = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'), onupdate=text('now()'))

    # --- AGREGA ESTA LÍNEA ---
    tipo_documento = relationship("TipoDocumento") 
    # -------------------------