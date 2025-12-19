#!/usr/bin/env python3
"""
Migración automática de permisos de conciliación bancaria
Este script se ejecuta automáticamente al iniciar la aplicación
"""

import os
import sys
from sqlalchemy.orm import Session
from sqlalchemy import text

# Añadir la ruta del proyecto
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def migrate_conciliacion_permissions():
    """Migrar permisos de conciliación bancaria automáticamente"""
    
    try:
        from app.core.database import SessionLocal
        from app.models.permiso import Permiso, Rol
        
        db = SessionLocal()
        
        print("🔧 Migrando permisos de conciliación bancaria...")
        
        # Permisos requeridos
        permisos_data = [
            {"nombre": "conciliacion_bancaria:ver", "descripcion": "Ver el módulo de conciliación bancaria y sus datos."},
            {"nombre": "conciliacion_bancaria:configurar", "descripcion": "Configurar importaciones y cuentas contables para conciliación."},
            {"nombre": "conciliacion_bancaria:importar", "descripcion": "Importar extractos bancarios y validar archivos."},
            {"nombre": "conciliacion_bancaria:conciliar", "descripcion": "Realizar conciliaciones manuales y automáticas."},
            {"nombre": "conciliacion_bancaria:ajustar", "descripcion": "Generar y aplicar ajustes automáticos."},
            {"nombre": "conciliacion_bancaria:reportes", "descripcion": "Ver y exportar reportes de conciliación."},
            {"nombre": "conciliacion_bancaria:auditoria", "descripcion": "Ver auditoría y actividad sospechosa en conciliaciones."},
        ]
        
        # Verificar si ya existen
        existing_count = db.query(Permiso).filter(
            Permiso.nombre.like('conciliacion_bancaria:%')
        ).count()
        
        if existing_count >= 7:
            print("✅ Permisos de conciliación bancaria ya existen")
            db.close()
            return True
        
        # Crear permisos faltantes
        permisos_creados = 0
        for permiso_data in permisos_data:
            existing = db.query(Permiso).filter_by(nombre=permiso_data["nombre"]).first()
            if not existing:
                permiso = Permiso(**permiso_data)
                db.add(permiso)
                permisos_creados += 1
        
        db.commit()
        
        # Obtener o crear rol Administrador
        rol_admin = db.query(Rol).filter_by(nombre="Administrador").first()
        if not rol_admin:
            rol_admin = Rol(
                nombre="Administrador",
                descripcion="Acceso total a todos los módulos y funcionalidades."
            )
            db.add(rol_admin)
            db.commit()
        
        # Asignar permisos al rol Administrador
        permisos_asignados = 0
        for permiso_data in permisos_data:
            permiso = db.query(Permiso).filter_by(nombre=permiso_data["nombre"]).first()
            if permiso and permiso not in rol_admin.permisos:
                rol_admin.permisos.append(permiso)
                permisos_asignados += 1
        
        db.commit()
        db.close()
        
        print(f"✅ Migración completada: {permisos_creados} permisos creados, {permisos_asignados} asignados")
        return True
        
    except Exception as e:
        print(f"❌ Error en migración de permisos: {str(e)}")
        try:
            db.rollback()
            db.close()
        except:
            pass
        return False

if __name__ == "__main__":
    migrate_conciliacion_permissions()