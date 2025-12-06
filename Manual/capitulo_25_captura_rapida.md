# Capítulo 25: Captura Rápida

La herramienta de **Captura Rápida** está diseñada para acelerar drásticamente el proceso de digitación contable mediante el uso de **Plantillas Predefinidas**. A diferencia del formulario estándar de "Nuevo Documento", esta interfaz asume que la estructura del asiento (cuentas y naturaleza) ya está definida, permitiendo al usuario enfocarse únicamente en los valores y terceros.

## 1. Concepto General

El flujo de trabajo se basa en **Plantillas**. Una plantilla define qué cuentas se van a mover y en qué naturaleza (Débito/Crédito). Al usar esta herramienta, el sistema:
1.  Carga las cuentas automáticamente.
2.  Solicita un **Valor Único Total**.
3.  Distribuye ese valor automáticamente en las columnas correspondientes (partida doble automática).

## 2. Configuración Inicial

Al ingresar, encontrará el panel de configuración del asiento:

*   **Fecha:** Fecha contable del registro.
*   **⚡ Plantilla (Requerido):** Seleccione el tipo de operación (ej. "Gasto de Cafetería", "Pago de Servicio Público"). **Es el campo más importante**, ya que define toda la estructura del asiento.
*   **Beneficiario:** Tercero asociado al movimiento.
    *   **Botón (+):** Permite crear un nuevo tercero rápidamente (NIT y Nombre) sin salir de la pantalla.
*   **Centro de Costo:** Opcional. Asigna un centro de costo a todas las líneas del asiento.

## 3. Valores y Conceptos

Una vez seleccionada una plantilla, se despliega la sección de detalles:

### Valor Total del Asiento
Un campo grande y destacado donde debe ingresar el valor total de la operación.
*   **Automatización:** Al escribir el valor, el sistema lo asigna automáticamente al Débito de una cuenta y al Crédito de la otra, garantizando que el asiento siempre esté cuadrado (sumas iguales).

### Detalle de Movimientos
Muestra las cuentas contables cargadas por la plantilla.
*   **Concepto / Detalle:** Campo de texto libre para describir la operación.
    *   **Botón (Libro):** Si escribe una descripción que usará frecuentemente, haga clic en el icono de libro para guardarla en su librería de conceptos favoritos.
*   **Débito / Crédito:** Calculados automáticamente basados en el "Valor Total".

## 4. Validaciones y Guardado

*   **Balanceo:** El sistema verifica en tiempo real que Débitos = Créditos. Si hay diferencias, verá una alerta parpadeante.
*   **Guardar Documento:** Solo se habilita si el asiento está cuadrado y la información completa. Al guardar, se genera el consecutivo y se limpia el formulario para el siguiente registro inmediato.

---
**Tip de Eficiencia:** Use la tecla `TAB` para navegar rápidamente entre campos. Esta pantalla está optimizada para digitación veloz sin necesidad de usar el mouse constantemente.
