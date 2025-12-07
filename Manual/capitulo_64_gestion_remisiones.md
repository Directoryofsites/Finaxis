# Manual de Usuario: Gestión de Remisiones (Despachos de Mercancía)

## 1. ¿Qué es y para qué sirve?
La **Remisión** es un documento oficial de transporte y entrega. Su función principal es respaldar la salida de mercancía de su bodega y la entrega al cliente, **sin generar todavía una cobro fiscal (Factura)**.

### ¿Cuándo debo usar una Remisión?
*   **Entregas Parciales:** El cliente compró 100 unidades, pero hoy solo se lleva 50. Hace una remisión por 50.
*   **Muestras Comerciales:** Envía productos para que el cliente los pruebe (luego se los factura o se los devuelven).
*   **Consignación:** Entrega mercancía para que el cliente la venda por su cuenta.
*   **Traslado a Obras:** Envía materiales a una obra o proyecto sin cobrar de inmediato.

---

## 2. Conceptos Clave (Antes de empezar)

Para evitar errores, es CRÍTICO entender los "Estados" del documento:

| Estado | Icono | Significado | ¿Afecta Inventario? | ¿Se puede Editar? |
| :--- | :---: | :--- | :---: | :---: |
| **BORRADOR** | 📝 | Es un papel de trabajo. Aún no es oficial. | **NO** (El stock sigue libre) | **SÍ** |
| **APROBADA** | ✅ | Ya es oficial. La mercancía está reservada o entregada. | **SÍ** (Stock Comprometido) | **NO** |
| **FACTURADA** | 💰 | Ya se convirtió en una venta real (Factura). | **SÍ** (Se descuenta definitivamente) | **NO** |
| **ANULADA** | 🚫 | Documento cancelado. No tiene validez. | **NO** (Libera el stock) | **NO** |

---

## 3. ¿Cómo crear una Remisión? (Paso a Paso)

**Ruta:** Menú Principal > **Facturación** > **Gestión de Remisiones**.

### Paso 1: Iniciar el Despacho
1.  Haga clic en el botón azul grande **[+ Nueva Remisión]** ubicado arriba a la derecha.
2.  El sistema cargará automáticamente el siguiente número consecutivo disponible.

### Paso 2: Datos del Encabezado (Quién y Cuándo)
Complete los siguientes campos con cuidado:
*   **Fecha de Emisión:** Generalmente es la fecha de hoy.
*   **Fecha de Vencimiento:** Es la fecha límite que usted le da al cliente para definir si compra o devuelve la mercancía.
*   **Tercero (Cliente):** Escriba el nombre o NIT de la persona que recibe la mercancía.
*   **Bodega de Salida:** **¡Muy Importante!** Seleccione de qué bodega física (Principal, Sede Norte, etc.) saldrá el producto. El sistema buscará las existencias en esa bodega específica.
*   **Observaciones:** Escriba detalles logísticos (ej: "Entregar en portería", "Transportadora XYZ").

### Paso 3: Listar los Productos
1.  En la caja de búsqueda "Agregar Producto", escriba el nombre o código.
2.  Presione `Enter` o seleccione el producto de la lista desplegable.
3.  **Cantidad:** Indique cuántas unidades va a entregar.
4.  **Precio (Opcional):** Si ya pactó un precio, escríbalo. Si es solo de traslado, puede dejarlo en 0 (aunque se recomienda poner valores para el seguro de transporte).
5.  Haga clic en el botón **[+] Agregar**. El producto aparecerá en la tabla inferior.
    *   *Repita este paso para todos los ítems.*

### Paso 4: Finalizar el Documento
Al terminar, tiene dos opciones en la parte inferior:

*   **Opción A: [Guardar Borrador]**
    Úselo si no está seguro de los datos o si va a terminar más tarde. La remisión se guarda pero **el inventario sigue disponible para otros**.

*   **Opción B: [APROBAR REMISIÓN]** 🚀
    Úselo cuando el camión ya va a salir.
    *   El sistema verificará si hay suficientes existencias en la bodega.
    *   Si todo está bien, **RESERVARÁ** esas unidades (nadie más podrá venderlas) y dejará el documento listo para imprimir.

---

## 4. Preguntas Frecuentes y Solución de Problemas (FAQ)

### 🔴 Problemas Comunes

**1. Hago clic en "Aprobar" y me sale un error rojo.**
*   **Causa:** Seguramente está intentando despachar más unidades de las que tiene en el sistema.
*   **Solución:** Revise el mensaje de error, le dirá exactamente cuánto stock ("Disponible Real") tiene en esa bodega. Debe ajustar la cantidad o hacer una entrada de almacén antes de aprobar.

**2. Me equivoqué en una remisión que ya está APROBADA. ¿Cómo la corrijo?**
*   **Respuesta:** Por seguridad contable, una remisión aprobada **NO se puede editar**.
*   **Solución:** Debe **ANULARLA** (botón de papelera roja en la lista) y crear una nueva. Al anularla, el sistema devuelve automáticamente el stock a la bodega.

**3. El cliente me devolvió la mercancía. ¿Qué hago?**
*   Si AÚN NO ha facturado: Simplemente ANULE la remisión.
*   Si YA facturó: Debe hacer una "Nota Crédito" o "Devolución en Ventas" (Módulo de Inventarios).

### 🔵 Dudas Generales

**4. ¿La remisión crea una Cuenta por Cobrar (Deuda del cliente)?**
**NO.** La remisión es un movimiento de inventario, no financiero. La deuda solo nace cuando usted convierte esa remisión en una **Factura de Venta**.

**5. ¿Puedo facturar solo una parte de la remisión?**
**SÍ.** Si envió 100 unidades y el cliente solo compró 80, al momento de facturar el sistema le preguntará qué cantidad desea procesar. Las otras 20 quedarán "Pendientes" o podrá pedir su devolución.

**6. ¿Qué pasa si dejo una remisión en BORRADOR por meses?**
Nada grave, pero esa información es "basura" en el sistema. Se recomienda revisar semanalmente los borradores y borrarlos si no se concretaron.

---
**¿Necesita más ayuda?** Contacte al administrador del sistema para temas de permisos o creación de nuevas bodegas.
