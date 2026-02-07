import sys
import os
sys.path.append(os.getcwd())

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Explicit imports to resolve SQLAlchemy circular dependencies
import app.models.nomina
import app.models.propiedad_horizontal.unidad
from app.models.empresa import Empresa
from app.models.consumo_registros import HistorialConsumo, TipoOperacionConsumo
from app.models.documento import Documento
from datetime import datetime

# Setup DB
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def audit():
    print("--- AUDITORIA DE CONSUMO FANTASMA ---")
    
    # 1. Buscar Empresa Mejia
    empresa = db.query(Empresa).filter(Empresa.nit == '800300500-1').first()
    if not empresa:
        print("No se encontró la empresa Mejia y Mejia Tributos S.A.S.")
        return

    print(f"Empresa: {empresa.razon_social} (ID: {empresa.id})")
    
    # 2. Consultar Historial de Consumo Enero 2026
    start_date = datetime(2026, 1, 1)
    end_date = datetime(2026, 1, 31, 23, 59, 59)
    
    historial = db.query(HistorialConsumo).filter(
        HistorialConsumo.empresa_id == empresa.id,
        HistorialConsumo.fecha >= start_date,
        HistorialConsumo.fecha <= end_date
    ).all()
    
    print(f"\nRegistros en HistorialConsumo ({start_date.date()} - {end_date.date()}): {len(historial)}")
    
    orphaned_count = 0
    total_consumed = 0
    
    print(f"{'ID':<5} {'Fecha':<20} {'Tipo':<15} {'Cant':<5} {'DocID':<10} {'Fuente':<10} {'Estado Doc'}")
    print("-" * 90)
    
    for h in historial:
        doc_status = "N/A"
        if h.documento_id:
            doc = db.query(Documento).get(h.documento_id)
            if doc:
                doc_status = "EXISTE"
                if doc.anulado:
                    doc_status += " (ANULADO)"
            else:
                doc_status = "HUEFANO (BORRADO)"
                orphaned_count += 1
        
        if h.tipo_operacion == TipoOperacionConsumo.CONSUMO:
            total_consumed += h.cantidad
            
        print(f"{h.id:<5} {str(h.fecha):<20} {h.tipo_operacion.value:<15} {h.cantidad:<5} {str(h.documento_id):<10} {h.fuente_tipo.value:<10} {doc_status}")

    print(f"\nTotal Consumido (Sum of CONSUMO type): {total_consumed}")
    print(f"Total Huérfanos detectados: {orphaned_count}")

    if orphaned_count > 0:
        print("\nRECOMENDACIÓN: Se encontraron registros huérfanos. Se deben eliminar.")

audit()
