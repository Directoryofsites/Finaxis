# Super Informe: El Reporte Más Potente

El **Super Informe** es la herramienta de inteligencia de negocios central de la aplicación. A diferencia de los reportes estáticos, este módulo le permite "conversar" con sus datos mediante combinaciones de filtros.

## 1. Dimensiones de Búsqueda

Lo primero es definir **qué** desea consultar.

1.  **Movimientos Contables**: (Por defecto) Analiza cada transacción individual. Ideal para auditoría detallada.

## 2. La Lógica de los Filtros (Cómo Combinarlos)

El poder del Super Informe radica en la **combinación**. El sistema utiliza una lógica "Y" (AND), lo que significa que **entre más filtros aplique, más específicos serán los resultados**.

### Escenario A: Auditoría de un Tercero Específico
*Objetivo: Ver qué le hemos pagado a "Papelería El Éxito" este mes.*
1.  **Fecha Desde/Hasta**: Seleccione el mes actual.
2.  **Tercero**: Busque "Papelería El Éxito".
3.  **Resultado**: Solo verá los movimientos de ese tercero en ese rango de fechas.

### Escenario B: Rastreo de Gastos Altos
*Objetivo: Encontrar todos los gastos de viaje superiores a $500,000.*
1.  **Cuenta Contable**: Seleccione la cuenta de "Gastos de Viaje" (ej. 5155).
2.  **Filtros de Valor > Condición**: Seleccione "Mayor que".
3.  **Filtros de Valor > Monto**: Escriba "500000".
4.  **Resultado**: El sistema filtrará miles de registros y le mostrará solo aquellos que cumplan ambas condiciones.

### Escenario C: Búsqueda Forense (Palabras Clave)
*Objetivo: Encontrar una factura perdida de la que solo recuerda que era por "Mantenimiento".*
1.  **Filtros de Documento > Concepto**: Escriba "Mantenimiento".
2.  **Resultado**: El sistema buscará esa palabra dentro de las descripciones de todos los asientos contables.

## 3. Filtros Avanzados

Haga clic en **"Mostrar Filtros Avanzados"** para desplegar opciones quirúrgicas:

-   **Por Documento**: Filtre por tipo (ej. solo Egresos) o por un número específico (ej. Egreso #1540).
-   **Por Centro de Costo**: Aísle los movimientos de una sucursal o departamento específico.
-   **Por Estado**: Puede buscar incluso documentos **Anulados** o **Eliminados** para auditoría de seguridad.

## 4. Exportación Inteligente

Una vez haya filtrado la información y tenga en pantalla exactamente lo que necesita:

-   **Exportar PDF**: Genera un reporte impreso con los resultados actuales.
-   **Opción "Traer TODO"**: Por defecto, el PDF respeta la paginación. Si marca esta casilla, el sistema generará un PDF masivo con **todos** los registros que coincidan con su búsqueda (útil para reportes de miles de líneas).

> **Consejo de Experto**: No tenga miedo de experimentar. Si no encuentra resultados, intente limpiar algunos filtros con el botón **"Limpiar"** y sea menos específico.
