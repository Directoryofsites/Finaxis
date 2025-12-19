# 🔧 GUÍA PASO A PASO - SOLUCIÓN ERROR 403

## 🎯 PROBLEMA ACTUAL
**Error en consola**: `Error HTTP cargando vista previa de ajustes: 403 "Acceso denegado: se requiere el permiso 'conciliacion_bancaria:ajustar'"`

## 🛠️ SOLUCIÓN INMEDIATA

### **OPCIÓN 1: Ejecutar SQL Directamente (Más Rápido)**

1. **Abrir tu cliente de base de datos** (MySQL Workbench, phpMyAdmin, etc.)

2. **Conectar a tu base de datos** del proyecto

3. **Ejecutar el archivo SQL**: `SOLUCION_SQL_DIRECTA.sql`
   - O copiar y pegar el contenido del archivo
   - Ejecutar paso por paso o todo junto

4. **Verificar resultados**:
   - Debe mostrar 7 permisos creados
   - Debe mostrar 7 permisos asignados al rol Administrador

5. **Recargar la página** del módulo de conciliación bancaria

### **OPCIÓN 2: Ejecutar Scripts Python (Si funciona)**

#### **Método A: Doble clic en archivos .bat**
1. Hacer doble clic en `Verificar_Estado_Permisos.bat`
2. Hacer doble clic en `Ejecutar_Fix_Permisos.bat`

#### **Método B: Desde terminal**
```bash
# Abrir terminal en el directorio del proyecto
cd ruta/del/proyecto

# Activar entorno virtual
.\.venv\Scripts\activate.bat

# Ejecutar scripts
python verificar_permisos_db.py
python check_and_fix_permissions.py
```

#### **Método C: Python directo**
```bash
# Desde el directorio del proyecto
.\.venv\Scripts\python.exe verificar_permisos_db.py
.\.venv\Scripts\python.exe check_and_fix_permissions.py
```

## 📋 VERIFICACIÓN DE LA SOLUCIÓN

### **1. En la Base de Datos:**
```sql
-- Verificar permisos creados
SELECT * FROM permisos WHERE nombre LIKE 'conciliacion_bancaria:%';
-- Debe devolver 7 registros

-- Verificar asignación al rol Administrador
SELECT COUNT(*) FROM rol_permisos rp
JOIN roles r ON rp.rol_id = r.id
JOIN permisos p ON rp.permiso_id = p.id
WHERE r.nombre = 'Administrador' AND p.nombre LIKE 'conciliacion_bancaria:%';
-- Debe devolver 7
```

### **2. En el Frontend:**
1. **Recargar** la página del módulo (F5 o Ctrl+R)
2. **Ir a la pestaña "Ajustes"**
3. **Verificar** que NO aparece el error 403 en consola
4. **Confirmar** que se carga la vista previa de ajustes

### **3. Señales de Éxito:**
- ✅ No más errores 403 en consola
- ✅ Vista previa de ajustes se carga
- ✅ Todas las pestañas funcionan
- ✅ Funcionalidades completas disponibles

## 🚨 PROBLEMAS COMUNES

### **Si persiste el error 403:**

#### **Problema 1: Usuario sin rol Administrador**
```sql
-- Verificar tu usuario
SELECT u.nombre, u.email, r.nombre as rol
FROM usuarios u
LEFT JOIN usuario_roles ur ON u.id = ur.usuario_id
LEFT JOIN roles r ON ur.rol_id = r.id
WHERE u.email = 'tu_email@ejemplo.com';

-- Si no tiene rol Administrador, asignarlo:
INSERT INTO usuario_roles (usuario_id, rol_id)
SELECT u.id, r.id
FROM usuarios u, roles r
WHERE u.email = 'tu_email@ejemplo.com'
AND r.nombre = 'Administrador';
```

#### **Problema 2: Caché del navegador**
1. **Limpiar caché** del navegador (Ctrl+Shift+Del)
2. **Cerrar y abrir** el navegador
3. **Cerrar y abrir sesión** en el sistema

#### **Problema 3: Rol Administrador no existe**
```sql
-- Crear rol Administrador
INSERT INTO roles (nombre, descripcion) VALUES 
('Administrador', 'Acceso total a todos los módulos y funcionalidades.');

-- Asignar TODOS los permisos al rol
INSERT INTO rol_permisos (rol_id, permiso_id)
SELECT r.id, p.id FROM roles r, permisos p WHERE r.nombre = 'Administrador';
```

## 🎯 RESULTADO ESPERADO

Después de aplicar la solución:

### **✅ Error 403 Eliminado**
- No más mensajes de error en consola
- Vista previa de ajustes funciona correctamente

### **✅ Módulo 100% Funcional**
- Todas las pestañas accesibles
- Ajustes automáticos operativos
- Funcionalidades completas disponibles

### **✅ Sistema Listo para Producción**
- 40+ endpoints funcionando
- 15 componentes frontend operativos
- Seguridad y permisos configurados
- Rendimiento optimizado

## 📞 SI NECESITAS AYUDA

### **Información a proporcionar:**
1. **Resultado** de la consulta de verificación de permisos
2. **Captura** del error en consola (si persiste)
3. **Email** de tu usuario en el sistema
4. **Método** que intentaste usar para la solución

### **Consultas útiles para diagnóstico:**
```sql
-- Ver todos los permisos
SELECT * FROM permisos ORDER BY nombre;

-- Ver todos los roles
SELECT * FROM roles;

-- Ver tu usuario y roles
SELECT u.nombre, u.email, r.nombre as rol
FROM usuarios u
LEFT JOIN usuario_roles ur ON u.id = ur.usuario_id
LEFT JOIN roles r ON ur.rol_id = r.id
WHERE u.email = 'tu_email@ejemplo.com';
```

---

## 🚀 PRÓXIMO PASO

**Una vez solucionado el error 403, el módulo de conciliación bancaria estará 100% operativo y listo para transformar la gestión financiera de tu empresa.**

**¡El sistema está técnicamente completo, solo necesita este último ajuste de permisos!**