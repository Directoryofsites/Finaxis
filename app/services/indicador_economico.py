from sqlalchemy.orm import Session
from app.models import indicador_economico as model
from app.schemas import indicador_economico as schema
from datetime import datetime

def get_by_vigencia(db: Session, vigencia: int) -> model.IndicadorEconomico:
    """Busca indicadores por año. Si no existe, lo crea con defaults."""
    obj = db.query(model.IndicadorEconomico).filter(model.IndicadorEconomico.vigencia == vigencia).first()
    if not obj:
        # Defaults
        current_year = datetime.now().year
        # Si es el año actual, podriamos intentar heredar del anterior (TODO), por ahora defaults base 2024
        defaults = {
            "salario_minimo": 1300000 if vigencia >= 2024 else 1160000,
            "auxilio_transporte": 162000 if vigencia >= 2024 else 140606,
            "uvt": 47065 if vigencia >= 2024 else 42412,
            "sancion_minima": 470650, # 10 UVT
            "trm": 3900,
            "euro": 4200
        }
        obj = model.IndicadorEconomico(vigencia=vigencia, **defaults)
        db.add(obj)
        db.commit()
        db.refresh(obj)
    
    # Calcular sancion minima dinamica si no esta guardada (o actualizarla)
    # Aunque la guardamos en DB, podriamos recalcularla aqui para asegurar consistencia
    if obj.uvt:
        obj.sancion_minima = obj.uvt * 10
        
    return obj

def update_indicadores(db: Session, vigencia: int, data: schema.IndicadorUpdate) -> model.IndicadorEconomico:
    obj = get_by_vigencia(db, vigencia)
    
    if data.salario_minimo is not None: obj.salario_minimo = data.salario_minimo
    if data.auxilio_transporte is not None: obj.auxilio_transporte = data.auxilio_transporte
    if data.uvt is not None: 
        obj.uvt = data.uvt
        obj.sancion_minima = data.uvt * 10 # Auto-calc
    if data.trm is not None: obj.trm = data.trm
    if data.euro is not None: obj.euro = data.euro
    
    db.commit()
    db.refresh(obj)
    return obj
