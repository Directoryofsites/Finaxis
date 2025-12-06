# Manual de Usuario - Capítulo 18: Inspector de Maestros

## 1. Introducción
El Inspector de Maestros es una herramienta de **super-administración** diseñada para consultar y limpiar bases de datos. Permite ver qué registros existen en las tablas maestras de una empresa y, si es necesario, eliminarlos forzosamente ("Erradicar").

**Ubicación:** `Administración > Utilidades > Panel de Soporte > Pestaña "Inspector Maestros"`

---

## 2. Funcionalidades de Inspección

### 2.1. Filtros de Búsqueda
1.  **Seleccione Empresa:** El tenant sobre el cual desea operar.
2.  **Seleccione Cartilla:** La tabla maestra a inspeccionar (Terceros, Plan de Cuentas, Centros de Costo, Usuarios, etc.).
3.  **Botón Inspeccionar:** Carga todos los registros de esa tabla en la empresa seleccionada.

### 2.2. Análisis de Dependencias
La tabla de resultados muestra una columna "Dependencias".
*   **Sin dependencias (Verde):** El registro está "limpio" y puede ser borrado sin afectar la integridad referencial inmediata (aunque siempre hay riesgos).
*   **Con dependencias (Amarillo):** El registro está siendo usado en documentos u otras tablas. El sistema le advertirá qué tablas dependen de él.

---

## 3. Acciones Críticas

### 3.1. Resetear Contraseña (Solo Usuarios/Terceros)
Si la cartilla inspeccionada es "Usuarios" o "Terceros" con acceso, aparecerá un botón gris **"Resetear Contraseña"**.
*   Genera un enlace de recuperación de contraseña.
*   Útil cuando el usuario no recibe los correos automáticos del sistema.

### 3.2. Erradicar (Botón Rojo)
Esta función permite **eliminar registros masivamente**.
1.  Seleccione los ítems usando las casillas de verificación (checkboxes).
2.  Haga clic en **"Erradicar Seleccionado(s)"**.

> [!DANGER]
> **Acción Destructiva e Irreversible:**
> "Erradicar" fuerza el borrado en la base de datos. Si borra un Tercero que tiene movimientos contables, dejará esos movimientos "huérfanos", corrompiendo la contabilidad. **Úselo solo para limpiar datos basura o errores de migración.**

---

## 4. Escenarios de Uso
*   **Limpieza de Pruebas:** Una empresa creó 50 terceros de prueba y quiere borrarlos antes de salir a producción.
*   **Corrección de Duplicados:** Se crearon dos cuentas contables idénticas por error y se desea eliminar la que no tiene saldo.
