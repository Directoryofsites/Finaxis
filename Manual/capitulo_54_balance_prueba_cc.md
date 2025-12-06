# Manual de Usuario - Capítulo 54: Balance de Prueba por Centro de Costo

## 1. Introducción
El **Balance de Prueba por Centro de Costo** es una herramienta de auditoría que le permite verificar los saldos de sus cuentas contables, pero desagregados por cada unidad de negocio.

Es fundamental para detectar errores de imputación. Por ejemplo, si la cuenta de "Caja General" tiene saldo negativo en la "Sucursal Norte", este reporte se lo mostrará inmediatamente.

---

## 2. Criterios de Búsqueda (Filtros)

Para generar el reporte, configure los siguientes parámetros:

*   **Rango de Fechas:** Periodo a evaluar (Desde / Hasta).
*   **Cuenta Contable (Opcional):**
    *   Puede filtrar una cuenta específica (ej: `1105 - Caja`) para ver su comportamiento en todos los centros de costo.
    *   Si lo deja en `Todas las Cuentas`, el sistema traerá el plan de cuentas completo.
*   **Nivel de Detalle:**
    *   **1:** Solo Grupos (Activo, Pasivo, Patrimonio).
    *   **4:** Máximo detalle (Auxiliares).
*   **Filtro de Centros:**
    *   **Con Saldo o Movimiento:** Muestra centros activos (Recomendado).
    *   **Solo con Movimiento:** Oculta centros que tienen saldo pero no se movieron en este periodo.
    *   **Todos:** Muestra incluso los centros que están en cero.

Haga clic en **Generar Reporte** para ver la tabla.

---

## 3. Interpretación de Resultados

La tabla muestra la siguiente información para cada combinación de Cuenta y Centro de Costo:

*   **Código y Centro de Costo:** Identifica a quién pertenece el saldo.
*   **Saldo Inicial:** Con cuánto dinero empezó el periodo.
*   **Débitos:** Todo lo que entró (o gastos).
*   **Créditos:** Todo lo que salió (o ingresos).
*   **Nuevo Saldo:** El valor final al cierre del periodo.

### Totales Generales
Al final de la tabla (Footer), encontrará la sumatoria de todos los débitos y créditos.
> **Nota de Auditoría:** Si la contabilidad está correcta, la suma de Débitos debe ser igual a la suma de Créditos (Partida Doble).

---

## 4. Exportación

*   **Exportar PDF:** Genera un documento formal con los filtros aplicados, ideal para revisiones físicas o para enviar al contador.
