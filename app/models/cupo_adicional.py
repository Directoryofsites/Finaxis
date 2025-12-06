from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class CupoAdicional(Base):
    __tablename__ = "cupos_adicionales"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    anio = Column(Integer, nullable=False) # Ej: 2025
    mes = Column(Integer, nullable=False)  # Ej: 11
    cantidad_adicional = Column(Integer, nullable=False) # Ej: 100

    # Relación
    empresa = relationship("Empresa", back_populates="cupos_adicionales")

    # Regla: Solo un registro de adicional por empresa/mes/año para evitar desorden
    __table_args__ = (
        UniqueConstraint('empresa_id', 'anio', 'mes', name='unique_cupo_mes_empresa'),
    )