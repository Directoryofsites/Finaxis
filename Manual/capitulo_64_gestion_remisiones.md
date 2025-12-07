# Gestión de Remisiones (Despachos)

## 1. Introducción
La **Remisión** es un documento que permite entregar mercancía al cliente *antes* de generar la Factura de Venta definitiva. 
Es útil para entregas parciales, despachos de prueba o cuando el cliente exige recibir el producto antes de que se emita la factura fiscal.

### Ciclo de Vida
1.  **BORRADOR (📝):** El documento se crea pero **NO descuenta inventario**. Puede editarse libremente.
2.  **APROBADA (✅):** El inventario queda **COMPROMETIDO** (Reservado). Ya no se puede editar. Está lista para entregarse.
3.  **FACTURADA (💰):** La remisión se convierte en una Factura de Venta y se descuenta definitivamente del inventario.

---

## 2. ¿Cómo acceder?
Menú Principal > **Facturación** > **Gestión de Remisiones**.

---

## 3. Crear una Nueva Remisión

### Paso 1: Iniciar Documento
1.  Haga clic en el botón azul **+ Nueva Remisión**.
2.  Se abrirá el formulario de encabezado.

### Paso 2: Datos Generales
Complete la información obligatoria:
*   **Fecha de Emisión:** Por defecto hoy.
*   **Fecha de Vencimiento:** Plazo para facturar o devolver.
*   **Tercero (Cliente):** A quien se le entrega la mercancía.
*   **Bodega:** De qué bodega saldrá el inventario.

### Paso 3: Agregar Productos
1.  Busque el producto por código o nombre.
2.  Ingrese la cantidad a despachar.
3.  Haga clic en el botón **+** o presione Enter.
4.  *Repita para todos los ítems.*

### Paso 4: Guardar y Aprobar
*   **Guardar Borrador:** Permite seguir editando después. El inventario sigue libre.
*   **APROBAR:** El sistema verificará si hay existencias. Si todo está correcto, reservará las unidades y generará el consecutivo oficial.

> **Advertencia de Stock:** Si intenta aprobar una remisión y no hay suficiente mercancía libre en la bodega seleccionada, el sistema mostrará un error y no permitirá aprobarla hasta que ajuste el inventario.

---

## 4. Acciones Disponibles

### Editar (Solo Borrador)
Haga clic en el icono del lápiz (✏️) en la lista principal. 
*Solo permitido si el estado es BORRADOR.*

### Anular (Solo Aprobada)
Si la mercancía fue devuelta o no se entregó, puede **Anular** la remisión. Esto liberará el stock comprometido inmediatamente.

### Imprimir / PDF
En la lista de remisiones, haga clic en el icono de impresora para descargar el PDF oficial de entrega.
