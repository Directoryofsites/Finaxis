# Manual de Usuario - Capítulo 20: Inspector Universal (ID)

## 1. Introducción
El Inspector Universal es una herramienta de diagnóstico profundo que permite localizar **cualquier registro** en la base de datos utilizando únicamente su **ID Interno**.

**Ubicación:** `Administración > Utilidades > Panel de Soporte > Pestaña "Inspector (ID)"`

---

## 2. ¿Cuándo usarlo?
A veces, los mensajes de error del sistema o los logs de auditoría solo muestran un número crudo (ej: `Error processing entity #4521`). Esta herramienta responde a la pregunta: **"¿Qué es el registro #4521?"**.

El sistema buscará ese número en **todas** las tablas principales:
*   Documentos
*   Terceros
*   Cuentas Contables
*   Centros de Costo
*   Tipos de Documento
*   Usuarios
*   Logs de Auditoría
*   Movimientos Contables

## 3. Interpretación de Resultados
El sistema mostrará una "tarjeta" por cada coincidencia encontrada.
*   **Encabezado:** Indica en qué tabla se encontró (ej: "Coincidencia encontrada en: **Tercero**").
*   **Cuerpo:** Muestra los datos crudos del registro (JSON) en formato de tabla clave-valor.

> [!NOTE]
> **IDs Duplicados:** Es normal que un mismo número (ej: 1) exista en varias tablas (el Tercero #1, el Documento #1, el Usuario #1). El inspector los mostrará todos.
