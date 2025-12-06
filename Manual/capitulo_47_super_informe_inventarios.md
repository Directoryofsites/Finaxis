# Capítulo 47: Super Informe de Inventarios

El **Super Informe de Inventarios** es la herramienta de inteligencia de negocios más potente del módulo de inventarios. Está diseñado para responder preguntas complejas sobre el movimiento de mercancía, cruzando múltiples variables como terceros, bodegas, grupos y fechas.

A diferencia de los reportes estándar que muestran saldos estáticos, este informe permite "interrogar" a la base de datos para obtener respuestas específicas sobre la operación logística y comercial.

## 1. Panel de Preguntas y Respuestas (Casos de Uso)

A continuación, presentamos una guía práctica basada en preguntas frecuentes que este reporte puede resolver:

### P1: "¿Qué productos se movieron con un Tercero (Cliente/Proveedor) específico?"
**Situación:** Necesita auditar todas las transacciones (compras o ventas) realizadas con el proveedor "Distribuidora X" o el cliente "Empresa Y" para verificar volúmenes o precios pactados.
**Configuración:**
1.  Despliegue los **Filtros Avanzados**.
2.  En el campo **"Tercero"**, busque y seleccione el nombre o NIT de la empresa.
3.  Defina el rango de fechas.
4.  Presione **"Generar Reporte"**.
**Resultado:** Obtendrá una lista cronológica de todos los ítems comprados o vendidos a ese tercero, con sus costos unitarios y cantidades exactas.

### P2: "¿Cómo ver el movimiento de una familia de productos en una bodega puntual?"
**Situación:** El jefe de bodega de la "Sucursal Norte" quiere revisar solo el movimiento de "Lácteos" para controlar mermas.
**Configuración:**
1.  En **"Bodegas"**, seleccione "Sucursal Norte".
2.  En **"Grupos"**, seleccione "Lácteos".
3.  Presione **"Generar Reporte"**.
**Resultado:** El sistema filtrará el ruido y mostrará exclusivamente los movimientos que cumplen ambas condiciones simultáneamente.

### P3: "¿A qué precio compramos el producto 'X' el mes pasado?"
**Situación:** Compras necesita verificar la fluctuación de costos de un insumo clave.
**Configuración:**
1.  En **"Búsqueda Producto"**, escriba el nombre o código del insumo.
2.  Ajuste las fechas al mes pasado.
3.  Genere el reporte.
**Resultado:** Verá todas las entradas de ese producto. La columna **"COSTO UNIT"** le revelará el precio exacto registrado en cada factura de compra.

### P4: "¿Qué pasó con la Factura #12345?"
**Situación:** Contabilidad tiene una duda sobre una factura específica y quiere saber qué productos movió.
**Configuración:**
1.  En **"Ref. Documento"**, escriba "12345".
2.  Presione **"Generar Reporte"**.
**Resultado:** El informe aislará todas las líneas de detalle asociadas a ese número de documento, permitiéndole ver exactamente qué ítems y cantidades se afectaron.

## 2. Herramientas de Análisis

### Filtros Multi-Selección
Una característica única de este reporte es la capacidad de seleccionar **múltiples opciones** a la vez. Por ejemplo, puede analizar el movimiento conjunto de las Bodegas A y B, excluyendo la Bodega C.

### Exportación Masiva a PDF
El sistema permite exportar grandes volúmenes de datos a PDF.
*   **Casilla "Todo para PDF":** Si marca esta opción antes de exportar, el sistema ignorará la paginación de la pantalla y generará un documento completo con **todos** los registros encontrados (ideal para archivos físicos o auditorías fiscales).

## 3. Interpretación de Columnas Clave

*   **DOC / REF:** Tipo y número del documento soporte.
*   **MOV (Movimiento):** Indica la naturaleza de la operación (Venta, Compra, Traslado, Ajuste).
*   **COSTO UNIT:** El valor unitario real de la transacción. En ventas es el costo de mercancía vendida (CMV), en compras es el costo de adquisición.
*   **COSTO TOTAL:** El impacto económico total de esa línea (Cantidad * Costo Unitario).

---
> **Consejo de Experto:** Utilice este reporte para detectar "fugas" de inventario cruzando filtros. Por ejemplo, filtre por un grupo de productos de alto valor y revise si existen "Salidas por Ajuste" (mermas) inusualmente altas en el periodo.
