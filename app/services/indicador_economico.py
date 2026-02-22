from sqlalchemy.orm import Session
from app.models import indicador_economico as model
from app.schemas import indicador_economico as schema
from datetime import datetime, date
import requests

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
        
    # Lazy Fetching de Valores Financieros Diarios
    if vigencia == datetime.now().year:
        if obj.fecha_sincronizacion != date.today():
            obj = sync_indicadores_api(obj)
            db.commit()
            db.refresh(obj)

    return obj

def sync_indicadores_api(obj: model.IndicadorEconomico) -> model.IndicadorEconomico:
    """Consulta APIs externas (Socrata para TRM, Frankfurter para Euro) y actualiza el objeto."""
    print("--- INICIANDO LAZY FETCHING DE INDICADORES (TRM/EURO) ---")
    
    # 1. Fetch TRM (Socrata API - Banco de la República / Superfinanciera)
    try:
        # endpoint api.datos.gov.co, dataset: 32sa-8pi3 (Tasa de Cambio Representativa del Mercado)
        # Nota estricta Socrata: El símbolo $ DEBE enviarse codificado como %24 para evitar el error "Unrecognized arguments []"
        url_trm = "https://www.datos.gov.co/resource/32sa-8pi3.json?%24limit=1&%24order=vigenciadesde%20DESC"
        resp = requests.get(url_trm, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data and len(data) > 0:
                trm_val = float(data[0]['valor'])
                obj.trm = trm_val
                print(f"TRM actualizada desde API Datos Abiertos: {trm_val}")
    except Exception as e:
        print(f"Error fetching TRM: {e}")

    # 2. Fetch Euro (ExchangeRate-API)
    try:
        url_euro = "https://open.er-api.com/v6/latest/EUR"
        resp2 = requests.get(url_euro, timeout=5)
        if resp2.status_code == 200:
            data2 = resp2.json()
            if "rates" in data2 and "COP" in data2["rates"]:
                euro_val = float(data2["rates"]["COP"])
                obj.euro = euro_val
                print(f"EURO actualizado desde ER-API: {euro_val}")
    except Exception as e:
        print(f"Error fetching EURO: {e}")

    # Se marca la fecha de sincronizacion
    obj.fecha_sincronizacion = date.today()
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
    if data.tasa_usura is not None: obj.tasa_usura = data.tasa_usura
    
    db.commit()
    db.refresh(obj)
    return obj
