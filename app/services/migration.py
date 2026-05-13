# app/services/migration.py
import os
import json
from sqlalchemy import create_engine, MetaData, select, insert, text, func
from app.core.database import Base, database_url as current_db_url
from app.core.config import settings

def run_sqlite_to_postgres_migration(sqlite_url: str, postgres_url: str):
    """
    Mueve datos de una base de datos SQLite a una PostgreSQL.
    """
    source_engine = create_engine(sqlite_url)
    target_engine = create_engine(postgres_url)

    # 1. Asegurar esquema en destino
    Base.metadata.create_all(target_engine)

    source_meta = MetaData()
    source_meta.reflect(bind=source_engine)

    tables_to_migrate = [
        'empresas',
        'usuarios',
        'roles',
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
        'indicadores_economicos',
        'ai_tutor_messages'
    ]

    results = []

    with source_engine.connect() as source_conn:
        with target_engine.connect() as target_conn:
            for table_name in tables_to_migrate:
                if table_name not in source_meta.tables:
                    continue
                
                table = source_meta.tables[table_name]
                rows = source_conn.execute(select(table)).fetchall()
                
                if not rows:
                    continue

                data = [dict(row._mapping) for row in rows]
                
                # Limpiar y Cargar
                target_conn.execute(table.delete())
                target_conn.execute(insert(table), data)
                target_conn.commit()
                results.append({"table": table_name, "count": len(data)})

    # 2. Sincronizar secuencias
    with target_engine.connect() as conn:
        for table_name in tables_to_migrate:
            try:
                conn.execute(text(f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), COALESCE(MAX(id), 1)) FROM {table_name}"))
                conn.commit()
            except:
                pass
    
    return results
