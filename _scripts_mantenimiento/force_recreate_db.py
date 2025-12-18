#!/usr/bin/env python3
# Script para forzar recreación completa de la base de datos

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import subprocess

def force_recreate_database():
    """
    Forzar recreación completa eliminando y creando la base de datos
    """
    print("🔥 RECREACIÓN FORZADA de kiro_clean_db")
    
    # Configuración de conexión
    conn_params = {
        'host': 'localhost',
        'port': 5432,
        'user': 'postgres',
        'password': 'mysecretpassword'
    }
    
    try:
        # Conectar a PostgreSQL
        conn = psycopg2.connect(**conn_params, database='postgres')
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("📡 Conectado a PostgreSQL")
        
        # Terminar TODAS las conexiones a kiro_clean_db
        print("🔌 Terminando TODAS las conexiones...")
        cursor.execute("""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = 'kiro_clean_db' AND pid <> pg_backend_pid()
        """)
        
        # Eliminar la base de datos completamente
        print("💥 ELIMINANDO base de datos...")
        cursor.execute("DROP DATABASE IF EXISTS kiro_clean_db")
        
        # Crear nueva base de datos limpia
        print("🆕 Creando base de datos LIMPIA...")
        cursor.execute("CREATE DATABASE kiro_clean_db")
        
        cursor.close()
        conn.close()
        
        print("✅ Base de datos recreada")
        
        # Ahora ejecutar migraciones desde cero
        print("🔄 Ejecutando migraciones desde CERO...")
        
        # Primero marcar como base (sin migraciones)
        result1 = subprocess.run(['alembic', 'stamp', 'base'], 
                                capture_output=True, text=True)
        
        if result1.returncode != 0:
            print(f"⚠️  Advertencia en stamp base: {result1.stderr}")
        
        # Luego ejecutar todas las migraciones
        result2 = subprocess.run(['alembic', 'upgrade', 'head'], 
                                capture_output=True, text=True)
        
        if result2.returncode != 0:
            print(f"❌ Error en upgrade: {result2.stderr}")
            return False
        
        print("✅ Migraciones completadas")
        
        # Verificar que las tablas se crearon
        conn = psycopg2.connect(**conn_params, database='kiro_clean_db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tablas = cursor.fetchall()
        print(f"📊 Tablas creadas: {len(tablas)}")
        for tabla in tablas[:10]:  # Mostrar primeras 10
            print(f"   - {tabla[0]}")
        
        cursor.close()
        conn.close()
        
        # Ahora ejecutar el seeder
        print("🌱 Ejecutando seeder...")
        from app.core.seeder import seed_database
        seed_database()
        
        print("\n🎉 ¡BASE DE DATOS COMPLETAMENTE RECREADA!")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    force_recreate_database()