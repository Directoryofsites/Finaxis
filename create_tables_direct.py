#!/usr/bin/env python3
# Script para crear tablas directamente usando SQLAlchemy ORM

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine
from app.core.database import Base
from app.core.config import settings
from app.core.seeder import seed_database

def create_tables_directly():
    """
    Crear tablas directamente usando SQLAlchemy sin Alembic
    """
    print("🔧 Creando tablas directamente con SQLAlchemy...")
    
    # Configuración de conexión para PostgreSQL admin
    conn_params = {
        'host': 'localhost',
        'port': 5432,
        'user': 'postgres',
        'password': 'mysecretpassword'
    }
    
    try:
        # 1. Recrear base de datos limpia
        print("🗑️  Recreando base de datos...")
        conn = psycopg2.connect(**conn_params, database='postgres')
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Terminar conexiones
        cursor.execute("""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = 'kiro_clean_db' AND pid <> pg_backend_pid()
        """)
        
        # Eliminar y crear base de datos
        cursor.execute("DROP DATABASE IF EXISTS kiro_clean_db")
        cursor.execute("CREATE DATABASE kiro_clean_db")
        
        cursor.close()
        conn.close()
        
        print("✅ Base de datos recreada")
        
        # 2. Crear todas las tablas usando SQLAlchemy
        print("🏗️  Creando tablas con SQLAlchemy...")
        
        # Importar todos los modelos para que estén registrados en Base.metadata
        from app.models import (
            Usuario, Empresa, Permiso, Rol, Tercero, Producto, 
            Documento, MovimientoContable, PlanCuenta,
            GrupoInventario, TasaImpuesto, Bodega
        )
        
        # Crear engine y tablas
        engine = create_engine(settings.DATABASE_URL)
        Base.metadata.create_all(bind=engine)
        
        print("✅ Tablas creadas exitosamente")
        
        # 3. Verificar tablas creadas
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tablas = inspector.get_table_names()
        
        print(f"📊 Tablas creadas: {len(tablas)}")
        for tabla in sorted(tablas):
            print(f"   - {tabla}")
        
        # 4. Ejecutar seeder
        print("\n🌱 Ejecutando seeder...")
        seed_database()
        
        print("\n🎉 ¡BASE DE DATOS CREADA EXITOSAMENTE!")
        print("📋 Estado final:")
        print("   - Base de datos: kiro_clean_db")
        print("   - Tablas: Todas creadas")
        print("   - Datos: Sembrados correctamente")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    create_tables_directly()