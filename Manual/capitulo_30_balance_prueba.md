# Balance de Prueba

El **Balance de Prueba** es una herramienta de auditoría fundamental que permite verificar la exactitud de los registros contables. Muestra el resumen de todas las cuentas (Activo, Pasivo, Patrimonio, Ingresos, Gastos y Costos) asegurando que la contabilidad cumple con el principio de partida doble.

## 1. Configuración del Reporte

Este reporte es altamente personalizable para facilitar el análisis a diferentes niveles.

1.  **Rango de Fechas**: Defina el periodo a auditar (Desde - Hasta).
2.  **Nivel de Detalle**:
    - **1 (Clase)**: Resumen general (Activo, Pasivo, etc.).
    - **2 (Grupo)**: Disponible, Inversiones, Deudores.
    - **3 (Cuenta)**: Caja, Bancos, Clientes.
    - **4 (Subcuenta/Auxiliar)**: Detalle máximo cuenta por cuenta.
3.  **Filtro de Cuentas**:
    - **Con Saldo o Movimiento**: Muestra cuentas activas en el periodo (Recomendado).
    - **Solo con Movimiento**: Oculta cuentas estáticas aunque tengan saldo.
    - **Todas las Cuentas**: Muestra todo el plan de cuentas (puede ser muy extenso).

## 2. Interpretación de Columnas

El reporte presenta la evolución de cada cuenta en cuatro momentos:

- **Saldo Inicial**: Valor de la cuenta antes de iniciar el rango de fechas seleccionado.
- **Débitos**: Suma de todos los movimientos débito del periodo.
- **Créditos**: Suma de todos los movimientos crédito del periodo.
- **Nuevo Saldo**: Valor final de la cuenta.

> **Nuevo Saldo** = Saldo Inicial + Débitos - Créditos

## 3. Verificación de "Sumas Iguales"

Al final del reporte, el sistema totaliza las columnas de Débitos y Créditos.

- **Cuadre Correcto**: Si la suma de Débitos es idéntica a la suma de Créditos, aparecerá un mensaje en <span style="color:green">verde</span> confirmando que el balance está cuadrado.
- **Descuadre**: Si hay diferencias, el sistema mostrará una alerta en <span style="color:red">rojo</span> indicando el monto del error. Esto requiere revisión inmediata de los comprobantes.

## 4. Exportación

Puede generar un archivo PDF oficial haciendo clic en **📄 Exportar PDF**. Este documento es ideal para revisiones de revisoría fiscal o auditoría externa.
