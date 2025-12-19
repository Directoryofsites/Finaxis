-- ============================================================================
-- SOLUCIÓN SQL DIRECTA - CREAR PERMISOS DE CONCILIACIÓN BANCARIA
-- ============================================================================
-- Este script crea los permisos faltantes y los asigna al rol Administrador
-- Ejecutar en tu cliente SQL (MySQL Workbench, phpMyAdmin, etc.)
-- ============================================================================

-- PASO 1: Crear los 7 permisos de conciliación bancaria
-- ============================================================================

INSERT INTO permisos (nombre, descripcion) 
VALUES 
    ('conciliacion_bancaria:ver', 'Ver el módulo de conciliación bancaria y sus datos.'),
    ('conciliacion_bancaria:configurar', 'Configurar importaciones y cuentas contables para conciliación.'),
    ('conciliacion_bancaria:importar', 'Importar extractos bancarios y validar archivos.'),
    ('conciliacion_bancaria:conciliar', 'Realizar conciliaciones manuales y automáticas.'),
    ('conciliacion_bancaria:ajustar', 'Generar y aplicar ajustes automáticos.'),
    ('conciliacion_bancaria:reportes', 'Ver y exportar reportes de conciliación.'),
    ('conciliacion_bancaria:auditoria', 'Ver auditoría y actividad sospechosa en conciliaciones.')
ON DUPLICATE KEY UPDATE descripcion = VALUES(descripcion);

-- Verificar que se crearon correctamente
SELECT * FROM permisos WHERE nombre LIKE 'conciliacion_bancaria:%';

-- ============================================================================
-- PASO 2: Obtener el ID del rol Administrador
-- ============================================================================

SELECT id, nombre FROM roles WHERE nombre = 'Administrador';

-- ============================================================================
-- PASO 3: Asignar permisos al rol Administrador
-- ============================================================================
-- IMPORTANTE: Si el rol Administrador no existe, primero créalo con:
-- INSERT INTO roles (nombre, descripcion) VALUES ('Administrador', 'Acceso total a todos los módulos y funcionalidades.');

-- Asignar todos los permisos de conciliación bancaria al rol Administrador
INSERT INTO rol_permisos (rol_id, permiso_id)
SELECT r.id, p.id 
FROM roles r, permisos p 
WHERE r.nombre = 'Administrador' 
AND p.nombre LIKE 'conciliacion_bancaria:%'
AND NOT EXISTS (
    SELECT 1 FROM rol_permisos rp 
    WHERE rp.rol_id = r.id AND rp.permiso_id = p.id
);

-- Verificar que se asignaron correctamente
SELECT r.nombre as rol, p.nombre as permiso, p.descripcion
FROM roles r
JOIN rol_permisos rp ON r.id = rp.rol_id
JOIN permisos p ON rp.permiso_id = p.id
WHERE r.nombre = 'Administrador' 
AND p.nombre LIKE 'conciliacion_bancaria:%';

-- ============================================================================
-- PASO 4: Verificar usuarios con rol Administrador
-- ============================================================================

SELECT u.id, u.nombre, u.email, r.nombre as rol
FROM usuarios u
JOIN usuario_roles ur ON u.id = ur.usuario_id
JOIN roles r ON ur.rol_id = r.id
WHERE r.nombre = 'Administrador';

-- ============================================================================
-- PASO 5 (OPCIONAL): Asignar rol Administrador a un usuario específico
-- ============================================================================
-- Si tu usuario NO tiene el rol Administrador, ejecuta esto:
-- Reemplaza 'tu_email@ejemplo.com' con tu email real

-- INSERT INTO usuario_roles (usuario_id, rol_id)
-- SELECT u.id, r.id
-- FROM usuarios u, roles r
-- WHERE u.email = 'tu_email@ejemplo.com'
-- AND r.nombre = 'Administrador'
-- AND NOT EXISTS (
--     SELECT 1 FROM usuario_roles ur 
--     WHERE ur.usuario_id = u.id AND ur.rol_id = r.id
-- );

-- ============================================================================
-- VERIFICACIÓN FINAL
-- ============================================================================

-- Contar permisos de conciliación bancaria
SELECT COUNT(*) as total_permisos 
FROM permisos 
WHERE nombre LIKE 'conciliacion_bancaria:%';
-- Debe devolver: 7

-- Contar permisos asignados al Administrador
SELECT COUNT(*) as permisos_asignados
FROM rol_permisos rp
JOIN roles r ON rp.rol_id = r.id
JOIN permisos p ON rp.permiso_id = p.id
WHERE r.nombre = 'Administrador'
AND p.nombre LIKE 'conciliacion_bancaria:%';
-- Debe devolver: 7

-- Ver todos los permisos del rol Administrador
SELECT p.nombre, p.descripcion
FROM rol_permisos rp
JOIN roles r ON rp.rol_id = r.id
JOIN permisos p ON rp.permiso_id = p.id
WHERE r.nombre = 'Administrador'
ORDER BY p.nombre;

-- ============================================================================
-- ¡LISTO! Después de ejecutar este script:
-- 1. Recargar la página del módulo de conciliación bancaria
-- 2. El error 403 debe desaparecer
-- 3. La funcionalidad de ajustes automáticos debe funcionar
-- ============================================================================
