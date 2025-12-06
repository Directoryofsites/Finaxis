# Capítulo 44: Reporte de Rentabilidad por Producto

El **Reporte de Rentabilidad** es una herramienta estratégica ("la joya de la corona") diseñada para analizar en profundidad el desempeño financiero de sus ventas. Permite identificar qué productos, clientes o documentos generan ganancias reales y cuáles podrían estar ocasionando pérdidas.

## 1. Modos de Análisis

El reporte ofrece dos enfoques principales, seleccionables en la parte superior:

### A. Por Producto (Visión General)
Agrupa las ventas por referencia de producto. Ideal para responder preguntas como:
*   ¿Cuál es mi producto estrella?
*   ¿Qué productos estoy vendiendo con margen negativo?
*   ¿Cuánto gané en total por la venta de "Camisas Talla L"?

### B. Por Documento (Auditoría Puntual)
Permite buscar una factura específica (por ejemplo, `FV-1050`) para analizar la rentabilidad exacta de esa transacción. Muestra el desglose línea por línea de esa factura.

---

## 2. Filtros y Configuración

El panel de filtros es robusto y flexible. Puede combinar múltiples criterios para refinar su búsqueda.

### Filtros Básicos
*   **Rango de Fechas:** Defina el periodo a analizar (Desde / Hasta).
*   **Grupos de Inventario:** Seleccione uno o varios grupos (ej. "Bebidas", "Electrónica") o use la opción "Seleccionar Todo" para un reporte global.

### Filtros Avanzados
Haga clic en el botón **"Más Filtros"** para desplegar opciones adicionales:
1.  **Producto Específico:** Busque y seleccione uno o más productos puntuales para un análisis quirúrgico.
2.  **Cliente:** Filtre las ventas realizadas a un tercero específico. Útil para analizar la rentabilidad de un cliente clave.
3.  **Lista de Precios:** Vea el desempeño de una lista de precios concreta (ej. "Mayorista" vs "Detal").
4.  **Margen Mínimo %:** Ingrese un porcentaje (ej. `20`). El reporte filtrará y mostrará solo aquellos productos cuyo margen sea inferior a ese valor.
5.  **Solo Pérdidas:** Una casilla de verificación crítica. Al activarla, el sistema mostrará **exclusivamente** los items donde el costo superó al precio de venta (utilidad negativa).

---

## 3. Interpretación de Resultados

Una vez generado el reporte, verá una tarjeta de **Resultados del Análisis**.

### Indicadores Clave (KPIs)
En la esquina superior derecha, verá la **Utilidad Total** del periodo consultado.
*   **Verde:** Ganancia neta positiva.
*   **Rojo:** Pérdida neta.

### Tabla de Datos
La tabla detalla la información financiera columna por columna:
*   **Venta Total:** Ingresos brutos por ese producto (Cantidad x Precio Venta).
*   **Costo Total:** Costo de la mercancía vendida (Cantidad x Costo Promedio).
*   **Utilidad:** La ganancia neta en dinero (`Venta - Costo`).
*   **Margen %:** El porcentaje de rentabilidad sobre la venta.
    *   <span style="color:green; background-color:#dcfce7; padding:2px 5px; border-radius:4px; font-weight:bold;">Verde</span>: Margen saludable (> 15%).
    *   <span style="color:#854d0e; background-color:#fef9c3; padding:2px 5px; border-radius:4px; font-weight:bold;">Amarillo</span>: Margen bajo (< 15%).
    *   <span style="color:red; background-color:#fee2e2; padding:2px 5px; border-radius:4px; font-weight:bold;">Rojo</span>: Pérdida (Margen negativo).

### Trazabilidad (Drill-Down)
En el modo "Por Producto", verá un icono de **ojo** (<i class="fas fa-eye"></i>) en la columna "Ver Detalle".
*   Al hacer clic, se despliega una sub-tabla que muestra **todas las facturas** donde se vendió ese producto en el periodo seleccionado.
*   Esto le permite rastrear exactamente qué venta causó una baja rentabilidad (por ejemplo, un descuento excesivo autorizado en una factura específica).

---

## 4. Exportación e Impresión

*   **Exportar PDF Global:** El botón rojo "Exportar PDF" en el encabezado de resultados genera un documento formal con todo el análisis en pantalla, ideal para presentar a gerencia.
*   **Impresión Individual:** Dentro del detalle de trazabilidad, cada factura tiene un icono de impresora (<i class="fas fa-print"></i>) que le permite abrir el PDF original de esa venta específica para su revisión.
