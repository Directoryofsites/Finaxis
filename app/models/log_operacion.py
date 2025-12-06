from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, text
# --- CORRECCIÓN 1: Se cambia la importación de JSONB a JSON ---
from sqlalchemy import JSON 
from sqlalchemy.orm import relationship
from ..core.database import Base

class LogOperacion(Base):
    __tablename__ = "log_operaciones"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    documento_id_asociado = Column(Integer, ForeignKey("documentos.id"), nullable=True, index=True)
    # --- FIN: NUEVA COLUMNA ---

    email_usuario = Column(String(255))
    fecha_operacion = Column(TIMESTAMP(timezone=True)) # <-- LÍNEA MODIFICADA
    tipo_operacion = Column(String(50), nullable=False) # Ej: 'ANULACION', 'ELIMINACION', 'MODIFICACION'
    razon = Column(String(500))

    # --- CORRECCIÓN 2: Se cambia el tipo de la columna de JSONB a JSON ---
    detalle_documento_json = Column(JSON)

    # Relaciones existentes
    documentos_eliminados = relationship(
        "DocumentoEliminado",
        back_populates="log_eliminacion"
    )
    usuario = relationship(
        "Usuario",
        back_populates="logs_operacion"
    )

    documento_asociado = relationship("Documento", back_populates="logs_operacion")