#!/usr/bin/env python3
"""
Script para solucionar el problema de permisos del módulo de Conciliación Bancaria
"""

import sys
import os

# Añadir la ruta del proyecto al sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import permiso as models_permiso
from app.models import usuario as models_usuario

def fix_permissions():
    """Crear permisos faltantes y asignar al rol Administrador"""
    
    print("🔧 Solucionando problema de permisos...")
    
    db = SessionLocal()
    
    try:
        # Permisos del módulo de conciliación bancaria
        permisos_conciliacion = [
            {"nombre": "conciliacion_bancaria:ver", "descripcion": "Ver el módulo de conciliación bancaria y sus datos."},
            {"nombre": "conciliacion_bancaria:configurar", "descripcion": "Configurar importaciones y cuentas contables para conciliación."},
            {"nombre": "conciliacion_bancaria:importar", "descripcion": "Importar extractos bancarios y validar archivos."},
            {"nombre": "conciliacion_bancaria:conciliar", "descripcion": "Realizar conciliaciones manuales y automáticas."},
            {"nombre": "conciliacion_bancaria:ajustar", "descripcion": "Generar y aplicar ajustes automáticos."},
            {"nombre": "conciliacion_bancaria:reportes", "descripcion": "Ver y exportar reportes de conciliación."},
            {"nombre": "conciliacion_bancaria:auditoria", "descripcion": "Ver auditoría y actividad sospechosa en conciliaciones."},
        ]
        
        # 1. Crear permisos si no existen
        permisos_creados = []
        for permiso_data in permisos_conciliacion:
            permiso = db.query(models_permiso.Permiso).filter_by(nombre=permiso_data["nombre"]).first()
            if not permiso:
                permiso = models_permiso.Permiso(**permiso_data)
                db.add(permiso)
                permisos_creados.append(permiso_data["nombre"])
                print(f"  ✅ Creando permiso: {permiso.nombre}")
            else:
                print(f"  ℹ️  Permiso ya existe: {permiso.nombre}")
        
        db.commit()
        
        # 2. Obtener rol Administrador
        rol_admin = db.query(models_permiso.Rol).filter_by(nombre="Administrador").first()
        
        if not rol_admin:
            print("  ⚠️  Rol 'Administrador' no encontrado. Creándolo...")
            rol_admin = models_permiso.Rol(
                nombre="Administrador",
                descripcion="Acceso total a todos los módulos y funcionalidades."
            )
            db.add(rol_admin)
            db.commit()
        
        # 3. Asignar todos los permisos de conciliación al rol Administrador
        permisos_asignados = 0
        for permiso_data in permisos_conciliacion:
            permiso = db.query(models_permiso.Permiso).filter_by(nombre=permiso_data["nombre"]).first()
            if permiso and permiso not in rol_admin.permisos:
                rol_admin.permisos.append(permiso)
                permisos_asignados += 1
                print(f"  ✅ Asignando permiso '{permiso.nombre}' al rol Administrador")
        
        db.commit()
        
        # 4. Verificar usuarios con rol Administrador
        usuarios_admin = db.query(models_usuario.Usuario).join(
            models_usuario.Usuario.roles
        ).filter(
            models_permiso.Rol.nombre == "Administrador"
        ).all()
        
        print(f"\n📊 Resumen:")
        print(f"  • Permisos creados: {len(permisos_creados)}")
        print(f"  • Permisos asignados al rol Administrador: {permisos_asignados}")
        print(f"  • Usuarios con rol Administrador: {len(usuarios_admin)}")
        
        if usuarios_admin:
            print(f"\n👥 Usuarios que ahora tienen acceso:")
            for usuario in usuarios_admin:
                print(f"  • {usuario.nombre} ({usuario.email})")
        else:
            print(f"\n⚠️  ADVERTENCIA: No hay usuarios con rol 'Administrador'")
            print(f"     Asigna el rol 'Administrador' a tu usuario para acceder al módulo.")
        
        print(f"\n🎉 ¡Permisos configurados correctamente!")
        print(f"   Ahora puedes acceder al módulo de Conciliación Bancaria.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error configurando permisos: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()

def check_user_permissions(user_email: str = None):
    """Verificar permisos de un usuario específico"""
    
    db = SessionLocal()
    
    try:
        if user_email:
            usuario = db.query(models_usuario.Usuario).filter_by(email=user_email).first()
        else:
            # Obtener el primer usuario administrador
            usuario = db.query(models_usuario.Usuario).join(
                models_usuario.Usuario.roles
            ).filter(
                models_permiso.Rol.nombre == "Administrador"
            ).first()
        
        if not usuario:
            print(f"❌ Usuario no encontrado")
            return False
        
        print(f"\n🔍 Verificando permisos para: {usuario.nombre} ({usuario.email})")
        
        # Obtener todos los permisos del usuario a través de sus roles
        permisos_usuario = set()
        for rol in usuario.roles:
            for permiso in rol.permisos:
                permisos_usuario.add(permiso.nombre)
        
        # Verificar permisos de conciliación bancaria
        permisos_conciliacion = [
            "conciliacion_bancaria:ver",
            "conciliacion_bancaria:configurar", 
            "conciliacion_bancaria:importar",
            "conciliacion_bancaria:conciliar",
            "conciliacion_bancaria:ajustar",
            "conciliacion_bancaria:reportes",
            "conciliacion_bancaria:auditoria"
        ]
        
        print(f"\n📋 Permisos de Conciliación Bancaria:")
        for permiso in permisos_conciliacion:
            tiene_permiso = permiso in permisos_usuario
            status = "✅" if tiene_permiso else "❌"
            print(f"  {status} {permiso}")
        
        permisos_faltantes = [p for p in permisos_conciliacion if p not in permisos_usuario]
        
        if permisos_faltantes:
            print(f"\n⚠️  Permisos faltantes: {len(permisos_faltantes)}")
            return False
        else:
            print(f"\n🎉 ¡Todos los permisos están configurados correctamente!")
            return True
            
    except Exception as e:
        print(f"❌ Error verificando permisos: {str(e)}")
        return False
    finally:
        db.close()

def main():
    """Función principal"""
    
    print("="*60)
    print("  SOLUCIONADOR DE PERMISOS - CONCILIACIÓN BANCARIA")
    print("="*60)
    
    # 1. Crear y asignar permisos
    if fix_permissions():
        print("\n" + "="*60)
        
        # 2. Verificar permisos
        check_user_permissions()
        
        print("\n" + "="*60)
        print("✅ SOLUCIÓN COMPLETADA")
        print("="*60)
        print("🔧 Pasos realizados:")
        print("   1. ✅ Permisos de conciliación bancaria creados")
        print("   2. ✅ Permisos asignados al rol Administrador")
        print("   3. ✅ Verificación de permisos completada")
        print()
        print("🚀 Próximos pasos:")
        print("   1. Recargar la página del módulo de conciliación bancaria")
        print("   2. Verificar que ya no aparezca el error 403")
        print("   3. Probar la funcionalidad de ajustes automáticos")
        
        return True
    else:
        print("\n❌ FALLÓ LA CONFIGURACIÓN DE PERMISOS")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)