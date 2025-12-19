#!/usr/bin/env python3
"""
Script para crear las tablas del módulo de conciliación bancaria directamente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.models.conciliacion_bancaria import *
from app.core.database import Base

def create_tables():
    """Crear todas las tablas del módulo de conciliación bancaria"""
    try:
        # Crear engine
        engine = create_engine(settings.DATABASE_URL, echo=True)
        
        print("Conectando a la base de datos...")
        
        # Crear todas las tablas definidas en los modelos
        print("Creando tablas del módulo de conciliación bancaria...")
        Base.metadata.create_all(bind=engine, tables=[
            ImportConfig.__table__,
            ImportSession.__table__,
            BankMovement.__table__,
            Reconciliation.__table__,
            ReconciliationMovement.__table__,
            AccountingConfig.__table__,
            ReconciliationAudit.__table__
        ])
        
        # Agregar las columnas a las tablas existentes
        print("Agregando columnas a tablas existentes...")
        with engine.connect() as conn:
            # Agregar columna a plan_cuentas
            try:
                conn.execute(text("""
                    ALTER TABLE plan_cuentas 
                    ADD COLUMN IF NOT EXISTS is_bank_reconciliation_account BOOLEAN DEFAULT FALSE
                """))
                conn.commit()
                print("✓ Columna is_bank_reconciliation_account agregada a plan_cuentas")
            except Exception as e:
                print(f"⚠ Error agregando columna a plan_cuentas: {e}")
            
            # Agregar columna a documentos
            try:
                conn.execute(text("""
                    ALTER TABLE documentos 
                    ADD COLUMN IF NOT EXISTS reconciliation_reference VARCHAR(255)
                """))
                conn.commit()
                print("✓ Columna reconciliation_reference agregada a documentos")
            except Exception as e:
                print(f"⚠ Error agregando columna a documentos: {e}")
            
            # Agregar columna a movimientos_contables
            try:
                conn.execute(text("""
                    ALTER TABLE movimientos_contables 
                    ADD COLUMN IF NOT EXISTS reconciliation_status VARCHAR(50) DEFAULT 'UNRECONCILED'
                """))
                conn.commit()
                print("✓ Columna reconciliation_status agregada a movimientos_contables")
            except Exception as e:
                print(f"⚠ Error agregando columna a movimientos_contables: {e}")
        
        print("\n🎉 ¡Tablas del módulo de conciliación bancaria creadas exitosamente!")
        
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("=== Creación de Tablas - Módulo Conciliación Bancaria ===\n")
    success = create_tables()
    if success:
        print("\n✅ Proceso completado exitosamente")
    else:
        print("\n❌ Proceso falló")
        sys.exit(1)