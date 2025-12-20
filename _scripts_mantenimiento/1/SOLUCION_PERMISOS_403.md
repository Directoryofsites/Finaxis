# 🔧 SOLUCIÓN ERROR 403 - PERMISOS FALTANTES

## 🎯 Problema Identificado

**Error 403**: "Acceso denegado: se requiere el permiso 'conciliacion_bancaria:ajustar'"

## 🔍 Causa del Problema

Los **permisos del módulo de Conciliación Bancaria no están creados** en la base de datos. El sistema de seguridad está funcionando correctamente, pero faltan los permisos específicos del módulo.

## ✅ Solución Paso a Paso

### **Opción 1: Ejecutar Script de Permisos (Recomendado)**

1. **Ejecutar el script de permisos:**
   ```bash
   python seed_permissions.py
   ```

2. **Si hay problemas con el entorno, ejecutar:**
   ```bash
   python fix_permissions_issue.py
   ```

### **Opción 2: Crear Permisos Manualmente en Base de Datos**

Si los scripts no funcionan, ejecutar estas consultas SQL directamente:

```sql
-- 1. Crear permisos de conciliación bancaria
INSERT INTO permisos (nombre, descripcion) VALUES 
('conciliacion_bancaria:ver', 'Ver el módulo de conciliación bancaria y sus datos.'),
('conciliacion_bancaria:configurar', 'Configurar importaciones y cuentas contables para conciliación.'),
('conciliacion_bancaria:importar', 'Importar extractos bancarios y validar archivos.'),
('conciliacion_bancaria:conciliar', 'Realizar conciliaciones manuales y automáticas.'),
('conciliacion_bancaria:ajustar', 'Generar y aplicar ajustes automáticos.'),
('conciliacion_bancaria:reportes', 'Ver y exportar reportes de conciliación.'),
('conciliacion_bancaria:auditoria', 'Ver auditoría y actividad sospechosa en conciliaciones.');

-- 2. Obtener ID del rol Administrador
SELECT id FROM roles WHERE nombre = 'Administrador';

-- 3. Asignar permisos al rol Administrador (reemplazar {rol_id} con el ID obtenido)
INSERT INTO rol_permisos (rol_id, permiso_id)
SELECT {rol_id}, id FROM permisos WHERE nombre LIKE 'conciliacion_bancaria:%';
```

### **Opción 3: Crear Rol Específico para Conciliación Bancaria**

```sql
-- 1. Crear rol específico
INSERT INTO roles (nombre, descripcion) VALUES 
('Operador Bancario', 'Especializado en conciliación bancaria con acceso completo al módulo.');

-- 2. Obtener ID del nuevo rol
SELECT id FROM roles WHERE nombre = 'Operador Bancario';

-- 3. Asignar permisos al nuevo rol (reemplazar {rol_id} con el ID obtenido)
INSERT INTO rol_permisos (rol_id, permiso_id)
SELECT {rol_id}, id FROM permisos WHERE nombre IN (
    'conciliacion_bancaria:ver',
    'conciliacion_bancaria:configurar',
    'conciliacion_bancaria:importar',
    'conciliacion_bancaria:conciliar',
    'conciliacion_bancaria:ajustar',
    'conciliacion_bancaria:reportes',
    'contabilidad:ver_reportes'
);

-- 4. Asignar rol al usuario (reemplazar {usuario_id} y {rol_id})
INSERT INTO usuario_roles (usuario_id, rol_id) VALUES ({usuario_id}, {rol_id});
```

## 🔍 Verificación de la Solución

### **1. Verificar que los permisos existen:**
```sql
SELECT * FROM permisos WHERE nombre LIKE 'conciliacion_bancaria:%';
```

**Resultado esperado:** 7 permisos

### **2. Verificar que el usuario tiene los permisos:**
```sql
SELECT u.nombre, u.email, r.nombre as rol, p.nombre as permiso
FROM usuarios u
JOIN usuario_roles ur ON u.id = ur.usuario_id
JOIN roles r ON ur.rol_id = r.id
JOIN rol_permisos rp ON r.id = rp.rol_id
JOIN permisos p ON rp.permiso_id = p.id
WHERE u.email = 'tu_email@ejemplo.com'
AND p.nombre LIKE 'conciliacion_bancaria:%';
```

### **3. Probar en el Frontend:**
1. **Recargar** la página del módulo
2. **Ir a la pestaña** "Ajustes"
3. **Verificar** que ya no aparece el error 403
4. **Confirmar** que se cargan los ajustes automáticos

## 📋 Lista de Permisos Requeridos

| Permiso | Descripción | Funcionalidad |
|---------|-------------|---------------|
| `conciliacion_bancaria:ver` | Ver módulo y datos | Dashboard, consultas |
| `conciliacion_bancaria:configurar` | Configurar importaciones | Configuraciones |
| `conciliacion_bancaria:importar` | Importar extractos | Importación de archivos |
| `conciliacion_bancaria:conciliar` | Realizar conciliaciones | Conciliación manual/auto |
| `conciliacion_bancaria:ajustar` | **Generar ajustes** | **Ajustes automáticos** |
| `conciliacion_bancaria:reportes` | Ver reportes | Reportes y exportación |
| `conciliacion_bancaria:auditoria` | Ver auditoría | Monitoreo y auditoría |

## 🎯 Roles Recomendados

### **Administrador (Acceso Total):**
- ✅ Todos los permisos de conciliación bancaria
- ✅ Todos los permisos del sistema

### **Operador Bancario (Especializado):**
- ✅ `conciliacion_bancaria:ver`
- ✅ `conciliacion_bancaria:configurar`
- ✅ `conciliacion_bancaria:importar`
- ✅ `conciliacion_bancaria:conciliar`
- ✅ `conciliacion_bancaria:ajustar`
- ✅ `conciliacion_bancaria:reportes`
- ✅ `contabilidad:ver_reportes`

### **Consulta Bancaria (Solo Lectura):**
- ✅ `conciliacion_bancaria:ver`
- ✅ `conciliacion_bancaria:reportes`

## 🚨 Problemas Comunes

### **Error persiste después de crear permisos:**
1. **Limpiar caché** del navegador
2. **Cerrar y abrir** sesión
3. **Verificar** que el usuario tiene el rol correcto
4. **Confirmar** que el rol tiene los permisos asignados

### **Usuario no tiene rol Administrador:**
```sql
-- Asignar rol Administrador al usuario
INSERT INTO usuario_roles (usuario_id, rol_id) 
SELECT u.id, r.id 
FROM usuarios u, roles r 
WHERE u.email = 'tu_email@ejemplo.com' 
AND r.nombre = 'Administrador';
```

### **Rol Administrador no existe:**
```sql
-- Crear rol Administrador
INSERT INTO roles (nombre, descripcion) VALUES 
('Administrador', 'Acceso total a todos los módulos y funcionalidades.');

-- Asignar todos los permisos al rol Administrador
INSERT INTO rol_permisos (rol_id, permiso_id)
SELECT r.id, p.id FROM roles r, permisos p WHERE r.nombre = 'Administrador';
```

## ✅ Resultado Esperado

Después de aplicar la solución:

- ✅ **Error 403 eliminado**
- ✅ **Ajustes automáticos funcionando**
- ✅ **Todas las funcionalidades accesibles**
- ✅ **Sistema de permisos operativo**

## 🎉 Confirmación de Éxito

**Señales de que la solución funcionó:**

1. **No más errores 403** en la consola
2. **Vista previa de ajustes** se carga correctamente
3. **Todas las pestañas** del módulo son accesibles
4. **Funcionalidades completas** disponibles

---

**🚀 Una vez solucionado, el módulo de Conciliación Bancaria estará 100% operativo y listo para uso en producción.**