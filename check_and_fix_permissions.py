#!/usr/bin/env python3
"""
Script simple para verificar y crear permisos de conciliación bancaria
"""

import sys
import os

# Añadir la ruta del proyecto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.permiso import Permiso, Rol
from app.models.usuario import Usuario

def main():
    print("=" * 70)
    print("  VERIFICACIÓN Y CREACIÓN DE PERMISOS - CONCILIACIÓN BANCARIA")
    print("=" * 70)
    
    db = SessionLocal()
    
    try:
        # Permisos requeridos
        permisos_requeridos = [
            {"nombre": "conciliacion_bancaria:ver", "descripcion": "Ver el módulo de conciliación bancaria y sus datos."},
            {"nombre": "conciliacion_bancaria:configurar", "descripcion": "Configurar importaciones y cuentas contables para conciliación."},
            {"nombre": "conciliacion_bancaria:importar", "descripcion": "Importar extractos bancarios y validar archivos."},
            {"nombre": "conciliacion_bancaria:conciliar", "descripcion": "Realizar conciliaciones manuales y automáticas."},
            {"nombre": "conciliacion_bancaria:ajustar", "descripcion": "Generar y aplicar ajustes automáticos."},
            {"nombre": "conciliacion_bancaria:reportes", "descripcion": "Ver y exportar reportes de conciliación."},
            {"nombre": "conciliacion_bancaria:auditoria", "descripcion": "Ver auditoría y actividad sospechosa en conciliaciones."},
        ]
        
        print("\n1️⃣  VERIFICANDO PERMISOS EXISTENTES...")
        print("-" * 70)
        
        permisos_existentes = []
        permisos_faltantes = []
        
        for permiso_data in permisos_requeridos:
            permiso = db.query(Permiso).filter_by(nombre=permiso_data["nombre"]).first()
            if permiso:
                print(f"  ✅ {permiso_data['nombre']}")
                permisos_existentes.append(permiso_data["nombre"])
            else:
                print(f"  ❌ {permiso_data['nombre']} - FALTANTE")
                permisos_faltantes.append(permiso_data)
        
        # Crear permisos faltantes
        if permisos_faltantes:
            print(f"\n2️⃣  CREANDO {len(permisos_faltantes)} PERMISOS FALTANTES...")
            print("-" * 70)
            
            for permiso_data in permisos_faltantes:
                permiso = Permiso(**permiso_data)
                db.add(permiso)
                print(f"  ✅ Creado: {permiso_data['nombre']}")
            
            db.commit()
            print(f"\n  🎉 {len(permisos_faltantes)} permisos creados exitosamente!")
        else:
            print(f"\n  ✅ Todos los permisos ya existen en la base de datos")
        
        # Verificar rol Administrador
        print(f"\n3️⃣  VERIFICANDO ROL ADMINISTRADOR...")
        print("-" * 70)
        
        rol_admin = db.query(Rol).filter_by(nombre="Administrador").first()
        
        if not rol_admin:
            print(f"  ⚠️  Rol 'Administrador' no encontrado. Creándolo...")
            rol_admin = Rol(
                nombre="Administrador",
                descripcion="Acceso total a todos los módulos y funcionalidades."
            )
            db.add(rol_admin)
            db.commit()
            print(f"  ✅ Rol 'Administrador' creado")
        else:
            print(f"  ✅ Rol 'Administrador' existe")
        
        # Asignar permisos al rol Administrador
        print(f"\n4️⃣  ASIGNANDO PERMISOS AL ROL ADMINISTRADOR...")
        print("-" * 70)
        
        permisos_asignados = 0
        permisos_ya_asignados = 0
        
        for permiso_data in permisos_requeridos:
            permiso = db.query(Permiso).filter_by(nombre=permiso_data["nombre"]).first()
            if permiso:
                if permiso not in rol_admin.permisos:
                    rol_admin.permisos.append(permiso)
                    permisos_asignados += 1
                    print(f"  ✅ Asignado: {permiso_data['nombre']}")
                else:
                    permisos_ya_asignados += 1
                    print(f"  ℹ️  Ya asignado: {permiso_data['nombre']}")
        
        if permisos_asignados > 0:
            db.commit()
            print(f"\n  🎉 {permisos_asignados} permisos asignados al rol Administrador")
        
        if permisos_ya_asignados > 0:
            print(f"  ℹ️  {permisos_ya_asignados} permisos ya estaban asignados")
        
        # Verificar usuarios con rol Administrador
        print(f"\n5️⃣  VERIFICANDO USUARIOS CON ROL ADMINISTRADOR...")
        print("-" * 70)
        
        usuarios_admin = db.query(Usuario).join(Usuario.roles).filter(
            Rol.nombre == "Administrador"
        ).all()
        
        if usuarios_admin:
            print(f"  ✅ {len(usuarios_admin)} usuario(s) con rol Administrador:")
            for usuario in usuarios_admin:
                print(f"     • {usuario.nombre} ({usuario.email})")
        else:
            print(f"  ⚠️  NO HAY USUARIOS con rol 'Administrador'")
            print(f"     Debes asignar este rol a tu usuario desde la interfaz de administración")
        
        # Resumen final
        print("\n" + "=" * 70)
        print("  ✅ VERIFICACIÓN COMPLETADA")
        print("=" * 70)
        print(f"\n📊 RESUMEN:")
        print(f"  • Permisos existentes: {len(permisos_existentes)}")
        print(f"  • Permisos creados: {len(permisos_faltantes)}")
        print(f"  • Permisos asignados al Administrador: {permisos_asignados}")
        print(f"  • Usuarios con acceso: {len(usuarios_admin)}")
        
        if len(permisos_faltantes) > 0 or permisos_asignados > 0:
            print(f"\n🚀 PRÓXIMOS PASOS:")
            print(f"  1. Recargar la página del módulo de conciliación bancaria")
            print(f"  2. Verificar que ya no aparezca el error 403")
            print(f"  3. Probar la funcionalidad de ajustes automáticos")
        else:
            print(f"\n✅ Todo está configurado correctamente")
            print(f"   Si aún ves el error 403, verifica que tu usuario tenga el rol 'Administrador'")
        
        print("\n" + "=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
