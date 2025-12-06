# Gestión de Inventario (Catálogo de Productos)

El módulo de **Gestión de Inventario** es el centro de administración para todos los bienes y servicios que su empresa comercializa. Desde aquí podrá crear, editar, eliminar y consultar el estado de su portafolio.

## Funcionalidades Principales

### 1. Búsqueda y Filtrado
Para facilitar la gestión de catálogos extensos, el sistema ofrece herramientas de búsqueda avanzada:
-   **Por Grupo**: Puede filtrar la lista para ver solo los productos de una o varias categorías específicas (ej. "Bebidas", "Servicios", "Materia Prima").
-   **Buscador Inteligente**: Escriba el código, nombre o referencia del producto en la barra de búsqueda. El sistema filtrará los resultados en tiempo real.

### 2. Listado de Productos
La tabla principal ofrece una vista rápida del estado de su inventario:
-   **Código**: Identificador único del producto.
-   **Nombre y Grupo**: Descripción y clasificación.
-   **Stock Total**: Cantidad actual disponible (calculada automáticamente según movimientos). *Nota: Los servicios no manejan stock.*
-   **Costo Promedio**: Valor de valoración del inventario.
-   **Precio Base**: Precio de venta sugerido antes de impuestos.
-   **Tipo**: Distintivo visual para diferenciar entre **Bien** (Producto físico) y **Servicio** (Intangible).

### 3. Creación y Edición de Productos
Al hacer clic en **"Nuevo Item"** o en el botón de **Editar (Lápiz)**, se abrirá una ventana con tres pestañas principales. A continuación se detalla cada una:

#### A. Pestaña: Datos Básicos
Aquí se define la identidad del producto.
-   **Código**: Identificador único (ej. `REF-001`). Campo obligatorio.
-   **Nombre**: Descripción comercial del producto. Campo obligatorio.
-   **Grupo**: Categoría a la que pertenece (ej. "Lácteos", "Servicios"). *Nota: Seleccionar un grupo es clave para habilitar las "Características" específicas.*
-   **Impuesto IVA**: Tasa impositiva aplicable al vender este producto.
-   **¿Es un Servicio?**: Casilla de verificación crítica.
    -   **Marcado (Sí)**: El sistema entiende que es un intangible (mano de obra, fletes). No gestionará stock físico ni costos de bodega.
    -   **Desmarcado (No)**: El sistema lo trata como un bien físico con control de inventario.

#### B. Pestaña: Inventario & Costos
Esta pestaña cambia su comportamiento dependiendo de si el item es un Bien o un Servicio.

**Para Servicios:**
-   Mostrará un mensaje indicando que no manejan inventario físico.

**Para Bienes Físicos:**
-   **Saldos Iniciales (Solo al crear):**
    -   *Stock Inicial*: Cantidad con la que arranca el producto.
    -   *Costo Unitario*: Valor de compra de ese stock inicial.
    -   *Bodega*: Ubicación física donde se almacenará ese saldo inicial.
-   **Límites de Stock:**
    -   *Stock Mínimo*: Cantidad por debajo de la cual el sistema generará alertas de reabastecimiento.
    -   *Stock Máximo*: Tope sugerido de inventario.
-   **Precio de Referencia:**
    -   *Precio Base Manual*: Precio de venta sugerido antes de impuestos. Si se deja vacío, el sistema podría sugerir el Costo Promedio como base (dependiendo de la configuración).
    -   *Costo Promedio Actual (Solo lectura)*: Visible al editar, muestra el valor contable actual del item.

#### C. Pestaña: Características
Este formulario es dinámico y depende del **Grupo** seleccionado en la primera pestaña.
-   Si el grupo tiene atributos definidos (ej. "Talla", "Color", "Marca", "Voltaje"), aparecerán aquí los campos correspondientes para diligenciar.
-   Si el grupo no tiene características, verá un mensaje indicándolo.

### 4. Eliminación de Items
En la columna de "Acciones" de cada fila encontrará el botón de **Eliminar (Basura)**.
> **Importante**: Por seguridad contable, el sistema **SOLO** permitirá eliminar productos que no tengan movimientos históricos (facturas, compras, ajustes). Si el producto ya ha sido usado, deberá inactivarlo en lugar de eliminarlo (funcionalidad futura).

### 5. Exportación
-   **PDF**: El botón rojo de "PDF" genera un reporte imprimible con la lista de productos filtrada en pantalla, ideal para tomas físicas de inventario o listas de precios.
