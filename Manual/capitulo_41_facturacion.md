# Capítulo 41: Facturación de Venta

El módulo de **Facturación** permite registrar las ventas de productos y servicios a clientes, generando el documento legal correspondiente y, si aplica, realizando la salida automática del inventario.

## 1. Conceptos Clave

Antes de facturar, asegúrese de tener configurados los siguientes maestros:
*   **Clientes (Terceros):** Deben estar creados y marcados como clientes. Si maneja listas de precios, asegúrese de asignarle una al cliente.
*   **Productos/Servicios:** Deben existir en el sistema.
*   **Bodegas:** Necesarias si va a facturar productos tangibles que mueven inventario.
*   **Tipos de Documento:** Debe existir un tipo de documento configurado para "Cartera Cliente" (ej. Factura de Venta).

## 2. Pasos para Crear una Factura

Para acceder, vaya al menú **Contabilidad > Facturación**.

### Paso 1: Información de la Venta (Encabezado)

En la primera sección, complete los datos generales:

1.  **Fecha Emisión:** Fecha contable de la factura. Por defecto es hoy.
2.  **Tipo Documento:** Seleccione el tipo de comprobante (ej. Factura de Venta).
    *   *Nota:* Si el tipo de documento afecta inventario, el campo "Bodega" se habilitará obligatoriamente.
3.  **Bodega:** Seleccione la bodega de donde saldrá la mercancía.
    *   Si el servicio no mueve inventario, este campo puede aparecer deshabilitado o como "(No aplica)".
4.  **Cliente:** Busque y seleccione el cliente.
    *   **Listas de Precio:** Si el cliente tiene asignada una lista de precios, aparecerá una etiqueta verde indicando el ID de la lista. El sistema usará estos precios automáticamente al agregar productos.
5.  **Condición Pago:**
    *   **Contado:** La factura se asume pagada de inmediato (o pendiente de cobro inmediato).
    *   **Crédito:** Habilita el campo "Fecha Vencimiento".
6.  **Fecha Vencimiento:** Obligatoria si la condición es Crédito. Indica el plazo máximo para el pago.
7.  **Centro de Costo:** Opcional. Útil para segmentar los ingresos por áreas o proyectos.

### Paso 2: Detalle de Productos

1.  Haga clic en el botón **"Añadir Items"**.
2.  Se abrirá una ventana modal para buscar productos.
    *   Puede buscar por nombre o código.
    *   Seleccione los productos deseados y haga clic en "Agregar".
3.  **Precios Automáticos:**
    *   Si el cliente tiene lista de precios, el sistema buscará el precio específico.
    *   Si no tiene lista o el producto no está en ella, traerá el precio base del producto.
4.  **Edición en Tabla:**
    *   Una vez agregados, puede modificar la **Cantidad** y el **Precio Unitario** directamente en la tabla.
    *   El subtotal y el total de la factura se recalcularán automáticamente.
5.  **Eliminar:** Use el icono de basura (rojo) para quitar una línea si se equivocó.

### Paso 3: Guardar

1.  Verifique que el **Total Factura** sea correcto.
2.  Haga clic en el botón **"Crear Factura"**.
3.  El sistema validará:
    *   Que haya stock suficiente (si la bodega controla stock y la configuración lo exige).
    *   Que las cantidades sean positivas.
    *   Que los campos obligatorios estén llenos.
4.  Si todo es correcto, verá un mensaje de éxito con el número de factura generado (consecutivo automático).

## 3. Preguntas Frecuentes (FAQ)

**¿Por qué no me deja seleccionar una Bodega?**
El campo Bodega solo se activa si el "Tipo de Documento" seleccionado está configurado para afectar inventario. Si está facturando solo servicios, es normal que esté deshabilitado.

**¿Cómo funcionan las Listas de Precios?**
Las listas de precios se asignan en la ficha del Cliente (Tercero). Al seleccionar el cliente en la factura, el sistema detecta su lista. Cuando agrega un producto, busca si ese producto tiene un precio especial en esa lista. Si lo encuentra, lo usa; si no, usa el precio estándar.

**¿Puedo cambiar el precio manualmente?**
Sí. Aunque el sistema sugiera un precio (base o de lista), usted puede editar la casilla "Precio Unit." en la tabla antes de guardar.

**¿Qué pasa si vendo a Crédito?**
El sistema generará una cuenta por cobrar (Cartera) al cliente. Podrá consultar esta deuda en los reportes de "Estado de Cuenta Cliente" o "Auxiliar de Cartera".
