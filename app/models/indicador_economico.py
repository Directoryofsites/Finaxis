from sqlalchemy import Column, Integer, Float, Date, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class IndicadorEconomico(Base):
    __tablename__ = "indicadores_economicos"

    id = Column(Integer, primary_key=True, index=True)
    vigencia = Column(Integer, unique=True, nullable=False, index=True)  # Ej: 2025
    
    # --- LABORAL ---
    salario_minimo = Column(Float, default=0)
    auxilio_transporte = Column(Float, default=0)
    
    # --- TRIBUTARIO ---
    uvt = Column(Float, default=0)
    sancion_minima = Column(Float, default=0) # Opcional, o calculado 10*UVT en frontend
    
    # --- FINANCIERO (Valores del momento) ---
    trm = Column(Float, default=0) # Dólar Hoy
    euro = Column(Float, default=0) # Euro Hoy
    
    # --- METADATA ---
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), default=func.now())
