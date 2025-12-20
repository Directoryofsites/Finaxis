#!/usr/bin/env python3
"""
Script para verificar el estado actual de los permisos en la base de datos
"""

import sys
import os

# Añadir la ruta del proyecto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from sqlalchemy.orm import Session
    from app.core.database import SessionLocal
    from app.models.permiso import Permiso, Rol
    from app.models.usuario import Usuario
    
    print("✅ Importaciones exitosas")
    
    db = SessionLocal()
    
    print("\n🔍 VERIFICANDO ESTADO ACTUAL DE LA BASE DE DATOS...")
    print("=" * 60)
    
    # Verificar permisos de conciliación bancaria
    permisos_conciliacion = db.query(Permiso).filter(
        Permiso.nombre.like('conciliacion_bancaria:%')
    ).all()
    
    print(f"\n📋 PERMISOS DE CONCILIACIÓN BANCARIA ENCONTRADOS: {len(permisos_conciliacion)}")
    print("-" * 60)
    
    if permisos_conciliacion:
        for permiso in permisos_conciliacion:
            print(f"  ✅ {permiso.nombre}")
    else:
        print("  ❌ NO SE ENCONTRARON PERMISOS DE CONCILIACIÓN BANCARIA")
    
    # Verificar rol Administrador
    rol_admin = db.query(Rol).filter_by(nombre="Administrador").first()
    
    print(f"\n👑 ROL ADMINISTRADOR:")
    print("-" * 60)
    
    if rol_admin:
        print(f"  ✅ Rol 'Administrador' existe")
        print(f"  📊 Permisos asignados: {len(rol_admin.permisos)}")
        
        # Verificar permisos específicos de conciliación
        permisos_conciliacion_admin = [p for p in rol_admin.permisos if p.nombre.startswith('conciliacion_bancaria:')]
        print(f"  🏦 Permisos de conciliación bancaria: {len(permisos_conciliacion_admin)}")
        
        if permisos_conciliacion_admin:
            for permiso in permisos_conciliacion_admin:
                print(f"     • {permiso.nombre}")
        else:
            print("     ❌ NO TIENE PERMISOS DE CONCILIACIÓN BANCARIA")
    else:
        print("  ❌ Rol 'Administrador' NO EXISTE")
    
    # Verificar usuarios con rol Administrador
    usuarios_admin = db.query(Usuario).join(Usuario.roles).filter(
        Rol.nombre == "Administrador"
    ).all() if rol_admin else []
    
    print(f"\n👥 USUARIOS CON ROL ADMINISTRADOR: {len(usuarios_admin)}")
    print("-" * 60)
    
    if usuarios_admin:
        for usuario in usuarios_admin:
            print(f"  ✅ {usuario.nombre} ({usuario.email})")
    else:
        print("  ❌ NO HAY USUARIOS CON ROL ADMINISTRADOR")
    
    # Diagnóstico del problema
    print(f"\n🔧 DIAGNÓSTICO DEL PROBLEMA:")
    print("=" * 60)
    
    problema_encontrado = False
    
    if len(permisos_conciliacion) < 7:
        print(f"  ❌ FALTAN PERMISOS: Se encontraron {len(permisos_conciliacion)} de 7 requeridos")
        problema_encontrado = True
    
    if not rol_admin:
        print(f"  ❌ FALTA ROL: El rol 'Administrador' no existe")
        problema_encontrado = True
    elif len(permisos_conciliacion_admin) < 7:
        print(f"  ❌ PERMISOS NO ASIGNADOS: El rol Administrador tiene {len(permisos_conciliacion_admin)} de 7 permisos de conciliación")
        problema_encontrado = True
    
    if len(usuarios_admin) == 0:
        print(f"  ⚠️  SIN USUARIOS: No hay usuarios con rol Administrador")
        problema_encontrado = True
    
    if not problema_encontrado:
        print(f"  ✅ TODO PARECE ESTAR CORRECTO")
        print(f"     Si aún ves el error 403, verifica:")
        print(f"     1. Que hayas recargado la página")
        print(f"     2. Que tu usuario tenga el rol 'Administrador'")
        print(f"     3. Que hayas cerrado y abierto sesión")
    
    print(f"\n" + "=" * 60)
    
    db.close()
    
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()