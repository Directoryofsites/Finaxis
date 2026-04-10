from sqlalchemy import Column, Integer, String, ForeignKey, Table, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

# Tabla de asociación (Muchos a Muchos) Unidades <-> Módulos
ph_unidad_modulo_association = Table(
    "ph_unidad_modulo_association",
    Base.metadata,
    Column("unidad_id", Integer, ForeignKey("ph_unidades.id"), primary_key=True),
    Column("modulo_id", Integer, ForeignKey("ph_modulos_contribucion.id"), primary_key=True)
)

# Tabla de asociación (Muchos a Muchos) Módulos <-> Torres
ph_modulo_torre_association = Table(
    "ph_modulo_torre_association",
    Base.metadata,
    Column("modulo_id", Integer, ForeignKey("ph_modulos_contribucion.id"), primary_key=True),
    Column("torre_id", Integer, ForeignKey("ph_torres.id"), primary_key=True)
)

class PHModuloContribucion(Base):
    """
    Representa un Módulo de Contribución para PH Mixta o por Sectores.
    Ej: "Módulo Residencial", "Módulo Comercial", "Torre A", "Torre B".
    
    Permite distribuir gastos específicos solo a un subconjunto de unidades.
    """
    __tablename__ = "ph_modulos_contribucion"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    
    nombre = Column(String(100), nullable=False) # Ej: "Sector Comercial"
    descripcion = Column(Text, nullable=True)
    
    # Tipo de Distribución por defecto para este módulo
    tipo_distribucion = Column(String(50), default="COEFICIENTE") 

    # Relaciones
    empresa = relationship("Empresa")
    
    # Relación inversa con Unidades
    unidades = relationship(
        "app.models.propiedad_horizontal.unidad.PHUnidad",
        secondary=ph_unidad_modulo_association,
        back_populates="modulos_contribucion"
    )

    # NUEVA RELACIÓN: Módulo -> Torres (Para filtrado de facturación)
    torres = relationship(
        "app.models.propiedad_horizontal.unidad.PHTorre",
        secondary=ph_modulo_torre_association,
        backref="modulos"
    )
