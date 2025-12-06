# Capítulo 42: Traslado de Inventario

El módulo de **Traslados** permite mover mercancía de una bodega a otra, manteniendo actualizado el inventario en ambas ubicaciones.

## 1. Conceptos Clave

*   **Bodega Origen (Salida):** Es la bodega de donde se descontarán los productos. Debe tener stock disponible.
*   **Bodega Destino (Entrada):** Es la bodega donde ingresarán los productos.
*   **Documento TR:** El sistema utiliza un tipo de documento interno (TR) para registrar estos movimientos.

## 2. Pasos para Realizar un Traslado

Para acceder, vaya al menú **Contabilidad > Traslados**.

### Paso 1: Logística (Encabezado)

1.  **Fecha Traslado:** Fecha en la que se hace efectivo el movimiento.
2.  **Selección de Bodegas:**
    *   **Origen:** Seleccione la bodega de donde sale la mercancía.
    *   **Destino:** Seleccione la bodega a donde llega.
    *   *Nota:* No puede seleccionar la misma bodega en ambos campos.
    *   **Botón de Intercambio:** Use el botón con flechas (↔) entre los selectores para invertir rápidamente el origen y el destino.
3.  **Observaciones:** Campo opcional para anotar detalles como "Envío por camión placa XXX" o "Reabastecimiento mensual".

### Paso 2: Selección de Mercancía

1.  Haga clic en **"Añadir Productos"**.
2.  Se abrirá el buscador de productos.
    *   **Importante:** El sistema solo le permitirá seleccionar productos que tengan stock disponible en la **Bodega de Origen** seleccionada.
3.  Una vez agregados, ajuste la **Cantidad** a trasladar en la tabla.
    *   Si intenta trasladar más de lo que hay en el origen, el sistema podría bloquear la operación o dejar el saldo en negativo (dependiendo de la configuración global).

### Paso 3: Confirmar

1.  Verifique el **Total Unidades** en la parte inferior de la tabla.
2.  Haga clic en **"Confirmar Traslado"**.
3.  El sistema generará un comprobante de traslado y ajustará los saldos automáticamente:
    *   Resta la cantidad en la Bodega Origen.
    *   Suma la cantidad en la Bodega Destino.

## 3. Preguntas Frecuentes (FAQ)

**¿Por qué no veo algunos productos en el buscador?**
El buscador filtra los productos según la **Bodega de Origen**. Si un producto no tiene existencias en esa bodega, no aparecerá para evitar errores de inventario negativo.

**¿Puedo anular un traslado?**
Los traslados confirmados afectan el kardex inmediatamente. Si cometió un error, lo más recomendable es realizar un nuevo traslado "inverso" (intercambiando origen y destino) por las mismas cantidades para revertir el efecto.

**¿Afecta la contabilidad?**
Depende de la configuración de las bodegas y los grupos de inventario. Generalmente, si ambas bodegas pertenecen a la misma empresa, es un movimiento interno que solo reclasifica el activo, pero no genera ingresos ni costos de venta.
