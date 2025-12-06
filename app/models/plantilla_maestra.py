from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, text
from sqlalchemy.orm import relationship
# --- Se importa UniqueConstraint ---
from sqlalchemy.schema import UniqueConstraint
from ..core.database import Base

class PlantillaMaestra(Base):
    __tablename__ = "plantillas_maestras"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    nombre_plantilla = Column(String(255), nullable=False)
    tipo_documento_id_sugerido = Column(Integer, ForeignKey("tipos_documento.id"), nullable=True)
    beneficiario_id_sugerido = Column(Integer, ForeignKey("terceros.id"), nullable=True)
    centro_costo_id_sugerido = Column(Integer, ForeignKey("centros_costo.id"), nullable=True)

    created_at = Column(TIMESTAMP(timezone=True), nullable=False)

    created_by = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    # Relaciones
    detalles = relationship("PlantillaDetalle", back_populates="maestra", cascade="all, delete-orphan")
    beneficiario = relationship("Tercero", back_populates="plantillas")
    centro_costo_sugerido = relationship("CentroCosto", back_populates="plantillas_maestras_sugeridas")

    # --- INICIO DE LA CORRECCIÓN ARQUITECTÓNICA ---
    # Se añade la regla de unicidad que faltaba.
    # Ahora el nombre de la plantilla debe ser único para cada empresa.
    __table_args__ = (
        UniqueConstraint('empresa_id', 'nombre_plantilla', name='uq_plantillas_maestras_empresa_nombre'),
    )
    # --- FIN DE LA CORRECCIÓN ARQUITECTÓNICA ---