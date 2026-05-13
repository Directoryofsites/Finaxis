# app/scripts/migrate_to_postgres.py
"""
SISTEMA DE MIGRACIÓN FINAXIS: SQLite -> PostgreSQL
Este script permite mover toda la información de una instalación local
a un servidor centralizado de red.
"""

import sys
import os
from sqlalchemy import create_engine, MetaData, Table, select, insert, func
from sqlalchemy.orm import sessionmaker

# Añadir el path base para importar modelos si es necesario
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.core.database import Base
from app.models import (
    Usuario, Empresa, Tercero, PlanCuenta, CentroCosto, 
    TipoDocumento, Documento, MovimientoContable, PHTorre, PHUnidad
)

# --- CONFIGURACIÓN ---
SQLITE_URL = "sqlite:///./contapy.db"
# Ajustar según las credenciales del servidor del cliente
POSTGRES_URL = "postgresql://postgres:postgres@localhost:5432/finaxis_network"

def migrate():
    print(f"🚀 Iniciando migración de datos...")
    print(f"Source: {SQLITE_URL}")
    print(f"Target: {POSTGRES_URL}")

    source_engine = create_engine(SQLITE_URL)
    target_engine = create_engine(POSTGRES_URL)

    # 1. Crear tablas en Postgres si no existen
    print("📦 Asegurando esquema en PostgreSQL...")
    Base.metadata.create_all(target_engine)

    source_meta = MetaData()
    source_meta.reflect(bind=source_engine)

    # Orden de migración para respetar Foreign Keys
    # (Ajustar según dependencias)
    tables_to_migrate = [
        'empresas',
        'usuarios',
        'plan_cuentas',
        'terceros',
        'centro_costos',
        'tipos_documento',
        'ph_torres',
        'ph_unidades',
        'documentos',
        'movimientos_contables',
        'configuracion_fe',
        'configuracion_reportes',
        'logs_operaciones',
        'consumo_registros',
        'control_planes_mensuales'
    ]

    with source_engine.connect() as source_conn:
        with target_engine.connect() as target_conn:
            for table_name in tables_to_migrate:
                if table_name not in source_meta.tables:
                    print(f"⚠️  Tabla {table_name} no encontrada en SQLite. Omitiendo.")
                    continue
                
                print(f"📤 Migrando tabla: {table_name}...")
                table = source_meta.tables[table_name]
                
                # Leer datos de SQLite
                rows = source_conn.execute(select(table)).fetchall()
                if not rows:
                    print(f"   (Tabla vacía)")
                    continue

                # Preparar inserción en Postgres
                # Convertimos filas a diccionarios
                data = [dict(row._mapping) for row in rows]
                
                # Limpiar tabla destino
                target_conn.execute(table.delete())
                
                # Inserción masiva
                target_conn.execute(insert(table), data)
                target_conn.commit()
                print(f"   ✅ {len(data)} registros migrados.")

    # 2. ACTUALIZAR SECUENCIAS EN POSTGRES (CRÍTICO)
    print("🔄 Sincronizando secuencias de PostgreSQL...")
    with target_engine.connect() as conn:
        for table_name in tables_to_migrate:
            # Solo tablas con columna 'id' que sea serial
            try:
                conn.execute(text(f"""
                    SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), 
                    COALESCE(MAX(id), 1)) FROM {table_name};
                """))
                conn.commit()
            except:
                pass # Algunas tablas podrían no tener secuencias seriales
    
    print("\n✨ MIGRACIÓN COMPLETADA CON ÉXITO.")
    print("Próximo paso: Configurar el .env del servidor con la nueva DATABASE_URL.")

from sqlalchemy import text

if __name__ == "__main__":
    # Si se pasan argumentos por consola, usarlos
    if len(sys.argv) > 2:
        SQLITE_URL = sys.argv[1]
        POSTGRES_URL = sys.argv[2]
    
    migrate()
