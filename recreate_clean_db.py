#!/usr/bin/env python3
# Script para recrear completamente la base de datos kiro_clean_db

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from app.core.seeder import seed_database
import subprocess
import os

def recreate_kiro_database():
    """
    Recrear completamente la base de datos kiro_clean_db
    """
    print("🗑️  Recreando base de datos kiro_clean_db desde cero...")
    
    # Configuración de conexión (sin especificar base de datos)
    conn_params = {
        'host': 'localhost',
        'port': 5432,
        'user': 'postgres',
        'password': 'mysecretpassword'
    }
    
    try:
        # Conectar a PostgreSQL (base de datos por defecto)
        conn = psycopg2.connect(**conn_params, database='postgres')
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("📡 Conectado a PostgreSQL")
        
        # Terminar conexiones activas a kiro_clean_db
        print("🔌 Terminando conexiones activas...")
        cursor.execute("""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = 'kiro_clean_db' AND pid <> pg_backend_pid()
        """)
        
        # Eliminar la base de datos si existe
        print("🗑️  Eliminando base de datos existente...")
        cursor.execute("DROP DATABASE IF EXISTS kiro_clean_db")
        
        # Crear nueva base de datos
        print("🆕 Creando nueva base de datos...")
        cursor.execute("CREATE DATABASE kiro_clean_db")
        
        cursor.close()
        conn.close()
        
        print("✅ Base de datos recreada exitosamente")
        
        # Ejecutar migraciones de Alembic
        print("🔄 Ejecutando migraciones de Alembic...")
        result = subprocess.run(['alembic', 'upgrade', 'head'], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Error en migraciones: {result.stderr}")
            return False
        
        print("✅ Migraciones completadas")
        
        # Ejecutar seeder UNA SOLA VEZ
        print("🌱 Sembrando datos iniciales...")
        seed_database()
        
        print("\n🎉 ¡Base de datos kiro_clean_db recreada completamente!")
        print("📊 Estado final:")
        print("   - 1 Empresa de Demostración")
        print("   - 2 Usuarios: soporte@soporte.com y admin@empresa.com")
        print("   - Plan contable básico sembrado")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    recreate_kiro_database()