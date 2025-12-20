#!/usr/bin/env python3
"""
Script para añadir un endpoint temporal que cree los permisos
"""

# Contenido para añadir temporalmente a app/main.py

ENDPOINT_TEMPORAL = '''

# ============================================================================
# ENDPOINT TEMPORAL PARA CREAR PERMISOS - ELIMINAR DESPUÉS DE USAR
# ============================================================================

@app.get("/crear-permisos-conciliacion")
async def crear_permisos_conciliacion(db: Session = Depends(get_db)):
    """
    ENDPOINT TEMPORAL para crear permisos de conciliación bancaria
    ⚠️ ELIMINAR DESPUÉS DE USAR
    """
    try:
        from app.models.permiso import Permiso, Rol
        
        # Permisos a crear
        permisos_data = [
            {"nombre": "conciliacion_bancaria:ver", "descripcion": "Ver el módulo de conciliación bancaria y sus datos."},
            {"nombre": "conciliacion_bancaria:configurar", "descripcion": "Configurar importaciones y cuentas contables para conciliación."},
            {"nombre": "conciliacion_bancaria:importar", "descripcion": "Importar extractos bancarios y validar archivos."},
            {"nombre": "conciliacion_bancaria:conciliar", "descripcion": "Realizar conciliaciones manuales y automáticas."},
            {"nombre": "conciliacion_bancaria:ajustar", "descripcion": "Generar y aplicar ajustes automáticos."},
            {"nombre": "conciliacion_bancaria:reportes", "descripcion": "Ver y exportar reportes de conciliación."},
            {"nombre": "conciliacion_bancaria:auditoria", "descripcion": "Ver auditoría y actividad sospechosa en conciliaciones."},
        ]
        
        # Crear permisos
        permisos_creados = []
        for permiso_data in permisos_data:
            permiso = db.query(Permiso).filter_by(nombre=permiso_data["nombre"]).first()
            if not permiso:
                permiso = Permiso(**permiso_data)
                db.add(permiso)
                permisos_creados.append(permiso_data["nombre"])
        
        db.commit()
        
        # Obtener rol Administrador
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
        
        return {
            "success": True,
            "message": "Permisos creados exitosamente",
            "permisos_creados": len(permisos_creados),
            "permisos_asignados": permisos_asignados,
            "instrucciones": [
                "1. Recargar la página del módulo de conciliación bancaria",
                "2. Verificar que desaparece el error 403",
                "3. ELIMINAR este endpoint de app/main.py"
            ]
        }
        
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e),
            "message": "Error creando permisos"
        }

# ============================================================================
'''

print("📋 INSTRUCCIONES PARA CREAR PERMISOS VÍA ENDPOINT")
print("=" * 60)
print()
print("1. 📝 AÑADIR ENDPOINT TEMPORAL:")
print("   - Abrir el archivo: app/main.py")
print("   - Añadir al final (antes de la última línea) el código de arriba")
print()
print("2. 🔄 REINICIAR EL BACKEND:")
print("   - Detener el servidor backend (Ctrl+C)")
print("   - Volver a ejecutar: python run.py")
print()
print("3. 🌐 EJECUTAR ENDPOINT:")
print("   - Abrir navegador en: http://localhost:8000/crear-permisos-conciliacion")
print("   - Debe mostrar: {'success': True, 'message': 'Permisos creados exitosamente'}")
print()
print("4. ✅ VERIFICAR SOLUCIÓN:")
print("   - Recargar página del módulo de conciliación bancaria")
print("   - Verificar que desaparece el error 403")
print()
print("5. 🧹 LIMPIAR:")
print("   - ELIMINAR el endpoint temporal de app/main.py")
print("   - Reiniciar backend nuevamente")
print()
print("=" * 60)
print("🚀 Esta es la forma más segura de crear los permisos")
print("   sin problemas de políticas de Windows")