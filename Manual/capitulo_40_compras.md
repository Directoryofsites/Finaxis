# Capítulo 40: Gestión de Compras y Gastos

El módulo de **Nueva Compra** es la herramienta central para registrar todas las adquisiciones de la empresa, ya sean inventarios (mercancía para la venta) o gastos generales. Este proceso afecta simultáneamente:
1.  **Cuentas por Pagar**: Genera la deuda con el proveedor.
2.  **Inventario**: Aumenta las existencias en la bodega seleccionada (si se compran bienes).
3.  **Contabilidad**: Genera el asiento contable automático según la configuración del tipo de documento.

## 1. Requisitos Previos

Antes de registrar una compra, asegúrese de tener configurados:
*   **Proveedores**: El tercero debe existir y estar marcado como "Proveedor".
*   **Bodegas**: Debe existir al menos una bodega para recibir la mercancía.
*   **Tipos de Documento**: Debe existir un tipo de documento con función "CXP Proveedor" (ej: Factura de Compra).
*   **Productos/Servicios**: Los ítems a comprar deben estar creados en el sistema.

## 2. Paso a Paso: Registrar una Compra

La pantalla se divide en dos secciones principales: **Información del Proveedor** y **Productos a Comprar**.

### Paso 1: Datos Generales (Encabezado)

Complete los campos obligatorios marcados con asterisco (<span style="color:red">*</span>):

1.  **Fecha Emisión**: Fecha real de la factura del proveedor.
2.  **Tipo Documento**: Seleccione el comprobante a generar (ej: "Factura de Compra").
    *   *Nota*: Si el tipo de documento tiene **Numeración Manual**, aparecerá un campo adicional para digitar el número de la factura física del proveedor.
3.  **Bodega Destino**: Seleccione dónde ingresará la mercancía. Esto es vital para el control de inventario.
4.  **Proveedor**: Busque y seleccione la empresa o persona a quien se le compra.
5.  **# Factura Proveedor**: (Solo si aplica) Digite el número exacto de la factura recibida (ej: `FE-1099`) para evitar duplicados y facilitar auditorías.
6.  **Fecha Vencimiento**: (Opcional) Fecha límite de pago. Útil para reportes de proveedores y flujo de caja.
7.  **Centro de Costo**: (Opcional) Asigne la compra a un centro de costos específico si su empresa maneja contabilidad por centros.

### Paso 2: Agregar Productos o Servicios

1.  Haga clic en el botón verde **<i class="fa fa-plus"></i> Añadir Items**.
2.  Se abrirá una ventana modal con el catálogo de productos.
3.  **Buscar**: Use el buscador para encontrar ítems por nombre o código.
4.  **Seleccionar**: Marque la casilla de verificación a la izquierda de los productos que desea incluir.
5.  **Cantidad y Costo**: Puede pre-ingresar la cantidad y el costo unitario directamente en el modal, o hacerlo después en la tabla principal.
6.  Haga clic en **Agregar Seleccionados** para llevarlos a la pantalla de compra.

### Paso 3: Verificar y Ajustar Detalle

En la tabla de "Productos a Comprar":
*   **Cantidad**: Verifique que la cantidad coincida con la factura física.
*   **Costo Unit.**: Ingrese el costo unitario **antes de impuestos** (base). El sistema calculará el subtotal automáticamente.
*   **Eliminar**: Si se equivocó de ítem, use el botón rojo de "Papelera" para quitarlo de la lista.

> **Importante**: El sistema valida que las cantidades sean mayores a 0 y los costos no sean negativos.

### Paso 4: Guardar la Compra

1.  Verifique el **Total Compra** en la parte inferior de la tabla.
2.  Haga clic en el botón **<i class="fa fa-save"></i> Guardar Compra**.
3.  Si todo es correcto, verá un mensaje de éxito indicando el número de consecutivo interno generado (ej: "Compra #105 creada correctamente").

## 3. Preguntas Frecuentes (FAQ)

**¿Por qué no me aparece ninguna bodega?**
Debe crear al menos una bodega en *Administración > Inventario > Parámetros > Bodegas*. Sin bodega, no se puede ingresar inventario.

**¿Cómo registro un servicio (ej: Arriendo)?**
El proceso es idéntico. Asegúrese de que el ítem "Arriendo" esté creado en el inventario y marcado como "Es Servicio" (no maneja stock físico, pero sí afecta el gasto).

**¿Puedo registrar una compra a crédito?**
Sí. La forma de pago (crédito/contado) depende de cómo gestione la tesorería posteriormente. Al guardar la compra, se crea una cuenta por pagar (CXP). Luego, debe registrar el "Egreso" o "Pago" para saldar esa deuda.

**¿Qué hago si el proveedor no aparece?**
Debe ir a *Administración > Terceros* y crearlo, asegurándose de marcar la casilla "Es Proveedor".

**¿El sistema calcula IVA y Retención?**
Los impuestos se calculan automáticamente según la configuración del **Producto** (impuesto asociado) y del **Tercero** (si es Gran Contribuyente, Responsable de IVA, etc.), basándose en la parametrización contable interna.
