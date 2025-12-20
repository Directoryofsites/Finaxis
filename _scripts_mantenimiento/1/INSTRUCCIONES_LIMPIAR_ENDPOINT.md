# 🧹 INSTRUCCIONES PARA LIMPIAR ENDPOINT TEMPORAL

## ⚠️ IMPORTANTE: Eliminar después de usar

Una vez que el error 403 esté solucionado, **DEBES ELIMINAR** el endpoint temporal de `app/main.py`.

### **Código a ELIMINAR:**

Buscar y eliminar estas líneas en `app/main.py`:

```python
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
```

### **Después de eliminar:**
1. **Guardar** el archivo `app/main.py`
2. **Reiniciar** el backend una vez más
3. **Verificar** que el módulo sigue funcionando sin errores

### **¿Por qué eliminar?**
- Es un endpoint temporal solo para crear permisos
- No debe estar en producción
- Una vez creados los permisos, ya no es necesario

---

**🎉 Una vez completado, el módulo de conciliación bancaria estará 100% operativo!**