# Manual de Usuario - Capítulo 19: Buscador por Llave Natural

## 1. Introducción
Esta herramienta técnica permite al equipo de soporte encontrar el **ID Interno (Primary Key)** de un registro en la base de datos utilizando su identificador público o "llave natural".

**Ubicación:** `Administración > Utilidades > Panel de Soporte > Pestaña "Buscador"`

---

## 2. ¿Para qué sirve?
En la base de datos, las relaciones se hacen por IDs numéricos (ej: `tercero_id = 452`), pero los usuarios conocen a los terceros por su NIT (ej: `900.123.456`). Esta herramienta traduce el lenguaje del usuario al lenguaje del sistema.

**Casos de Uso:**
*   Necesita usar el "Inspector Universal" (Capítulo 20) y le pide un ID numérico, pero usted solo tiene el NIT del cliente.
*   Necesita verificar en los logs del servidor qué pasó con la factura #500, pero los logs registran `documento_id`.

---

## 3. Tipos de Búsqueda
1.  **Tercero por NIT:** Ingrese el número de identificación (sin dígito de verificación si es posible, o completo).
2.  **Cuenta por Código:** Ingrese el código contable (ej: `110505`).
3.  **Centro de Costo por Código:** Ingrese el código corto del centro de costos.
4.  **Documento por Tipo y Número:** Requiere dos datos:
    *   **ID Tipo Doc:** El ID numérico del tipo de documento (ej: 1 para Factura de Venta).
    *   **Número:** El consecutivo del documento (ej: 1020).

## 4. Resultados
El sistema devolverá un mensaje verde con el **ID Encontrado**. Copie este número para usarlo en otras herramientas de diagnóstico.
