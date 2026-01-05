# Bitácora Técnica: Optimización de Importación Universal Inteligente
**Fecha:** 03 de Enero de 2026
**Módulo:** Utilidad de Migración de Datos (Importación Universal)

---

## 1. Resumen Ejecutivo
Se realizó una reingeniería profunda del módulo de Importación Universal para solucionar problemas de **integridad de datos**, **colisión de tipos de documento** y **reportes incompletos**. La solución transformó un proceso lineal simple en un **Proceso Inteligente de Dos Fases**, garantizando que documentos con el mismo número pero diferente tipo (ej: Recibo #1 y Comprobante #1) sean tratados como entidades distintas.

## 2. Diagnóstico de Problemas
Durante las pruebas de importación masiva se detectaron los siguientes fallos críticos:

### A. Colisión de Tipos de Documento
El sistema generaba códigos de documento de forma simplista (ej: "Comprobante de Diario" -> "CD"). Si ya existía un "Comprobante de Depósito" con código "CD", el sistema mezclaba ambos conceptos, causando errores de numeración duplicada ("Ya existe el documento CD-1").

### B. Agrupamiento Incorrecto (El problema de "La Mezcla")
Al no tener códigos únicos, el sistema agrupaba movimientos de distintos orígenes bajo un solo "Documento Genérico #1". Esto resultaba en documentos "Frankenstein" con líneas de distintos tipos mezcladas.

### C. Pérdida de Información de Terceros
Aunque el encabezado del documento tenía un Beneficiario, los **movimientos individules** (débitos/créditos) perdían su asociación con el tercero (NIT) original de la línea del Excel. Esto hacía que el movimiento existiera contablemente pero fuera "anónimo" en los reportes detallados.

### D. Super Informe "Vacío"
Debido al punto C, el Super Informe (que busca detallar transacciones por tercero) no encontraba información en los movimientos y mostraba líneas en blanco o ceros, a pesar de que la importación había sido "exitosa".

---

## 3. Soluciones Técnicas Implementadas

### Solución 1: Algoritmo de Resolución de Colisiones (Inteligencia de Tipos)
Se mejoró la función `ImportUtils.ensure_tipo_documento_exists` para que, al encontrar un nombre nuevo, intente generar un código único usando estrategias escalonadas:
1.  **Acrónimo:** "Comprobante de Diario" -> **CDD**
2.  **Dos Letras:** "Comprobante de Diario" -> **CD**
3.  **Tres Letras:** "Comprobante de Diario" -> **COM**
4.  **Sufijo Numérico (Infalible):** Si todo falla -> **CDD1**, **CDD2**...

**Resultado:** Cada Tipo de Documento tiene garantizado un Código Único en el sistema.

### Solución 2: Motor de Importación de Dos Fases
Se reestructuró `UniversalImportService` para operar en dos tiempos:

*   **Fase 1 (Pre-Escaneo):** El sistema lee todo el archivo *sin importar nada*, solo para identificar los Nombres de Documentos. Va a la base de datos, aplica la Solución 1 y obtiene los códigos oficiales (ej: "RC", "CE", "CDD").
*   **Fase 2 (Agrupamiento y Proceso):** Con los códigos ya validados y cacheados, el sistema agrupa los movimientos. Ahora sabe con certeza que "Recibo #1" pertenece al grupo "RC-1" y "Comprobante #1" al grupo "CDD-1", manteniéndolos estrictamente separados.

### Solución 3: Trazabilidad de Tercero por Movimiento
1.  **Cambio en Base de Datos:** Se agregó la columna `tercero_id` a la tabla `movimientos_contables` (mediante migración Alembic).
2.  **Lógica de Importación:** Ahora, cada línea importada busca su NIT específico y lo guarda directamente en el movimiento, independientemente del encabezado del documento.

### Solución 4: Lógica de Fallback en Reportes
Se actualizó el `Super Informe` para usar una lógica de prioridad:
1.  Busca el Tercero del Movimiento (Dato preciso).
2.  Si no existe, usa el Beneficiario del Documento (Dato general).

---

## 4. Conclusión
El sistema ahora es capaz de importar archivos complejos con múltiples tipos de documentos simultáneos sin mezclarlos, preservando la integridad financiera y la detalle de los terceros línea por línea. La importación es robusta, auditable y genera reportes completos.
