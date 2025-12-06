# Manual de Usuario - Capítulo 2: Tipos de Documento

## 1. Introducción
El módulo de **Tipos de Documento** es el "cerebro" que define cómo se comporta cada transacción en ContaPY. Aquí no solo se crean los nombres de sus comprobantes (Facturas, Recibos, Egresos), sino que se **programa la lógica** que el sistema ejecutará automáticamente.

Una configuración correcta garantiza que:
*   **Auditoría:** La numeración sea consecutiva y sin huecos.
*   **Automatización:** El sistema mueva inventarios y genere asientos contables por usted.
*   **Integración:** Los documentos alimenten correctamente los módulos de Cartera (CxC) y Proveedores (CxP).

---

## 2. ¿Cómo acceder al módulo?
Siga esta ruta en el menú principal:

1.  Ubique la sección **Administración y Configuración**.
2.  Busque el grupo **Parametrización Maestra**.
3.  Haga clic en la opción **Tipos de Documento**.

> **Ruta Rápida:** `Administración > Parametrización Maestra > Tipos de Documento`

---

## 3. Conceptos Fundamentales

### 3.1. Modos de Numeración
El sistema ofrece dos formas de controlar los consecutivos de sus documentos:

*   **Automática (Recomendado):** El sistema asigna el siguiente número disponible (1, 2, 3...) sin intervención humana. Es ideal para documentos internos como Facturas de Venta, Recibos de Caja o Notas Contables.
*   **Manual:** El usuario debe digitar el número al momento de crear el documento. Esto es obligatorio para documentos externos donde no controlamos el consecutivo, como las **Facturas de Compra** (usamos el número que nos da el proveedor).

### 3.2. Lógica de Negocio (El "Cerebro" del Sistema)
Aquí es donde usted define qué "superpoderes" tendrá el documento.

#### A. El Interruptor de Inventario (`Afecta Inventario`)
Esta casilla transforma el documento en una **Orden de Almacén**.
*   **Activado:** El sistema OBLIGARÁ a seleccionar una Bodega y descontará (ventas) o sumará (compras) unidades del Kardex físico.
*   **Desactivado:** El documento será puramente financiero (ej. una Nota Contable por ajuste de precio) y no tocará sus existencias.

#### B. La "Doble Llave" de Cartera y Proveedores
Para que un documento active los módulos especializados de cobro o pago, se requiere una **Sinergia** entre dos campos. Si falta uno, el módulo no funcionará.

| Módulo | Llave 1: Función Especial | Llave 2: Cuenta Configurada | Efecto |
| :--- | :--- | :--- | :--- |
| **Ventas (CxC)** | `VENTAS` | `Cuenta Débito CxC` (Ej. 1305) | Crea una deuda nueva al cliente. |
| **Recaudos (CxC)** | `RECIBO_CAJA` | `Cuenta Crédito CxC` (Ej. 1305) | Permite cruzar/abonar a facturas pendientes. |
| **Compras (CxP)** | `COMPRAS` | `Cuenta Crédito CxP` (Ej. 2205) | Crea una deuda nueva con el proveedor. |
| **Pagos (CxP)** | `PAGO_PROVEEDOR` | `Cuenta Débito CxP` (Ej. 2205) | Permite cruzar/abonar a facturas de compra. |

> **Ejemplo Crítico:** Si crea un "Recibo de Caja" pero olvida asignarle la cuenta 1305 en la configuración, el sistema **NO** le mostrará la opción de "Abonar a Facturas" cuando lo esté usando.

---

## 4. Diccionario de Campos (Referencia Detallada)

Al crear o editar un tipo de documento, encontrará los siguientes campos:

| Campo | Descripción | Recomendación |
| :--- | :--- | :--- |
| **Código** | Identificador corto de hasta 5 letras. | Use siglas lógicas: `FV` (Factura Venta), `RC` (Recibo Caja), `CE` (Comprobante Egreso). |
| **Nombre** | Nombre completo del documento. | Sea descriptivo: "Factura de Venta Electrónica". |
| **Numeración Manual** | Casilla de verificación. | Marcar SOLO para documentos de proveedores. |
| **Consecutivo Actual** | El último número usado. | Si inicia en 0, el primer documento será el 1. |
| **Función Especial** | Comportamiento pre-programado. | `VENTAS` para facturar, `COMPRAS` para gastos, `NINGUNA` para notas internas. |
| **Afecta Inventario** | Si mueve Kardex. | Marcar para Facturas y Remisiones. Desmarcar para Servicios. |
| **Cuenta Caja/Banco** | Cuenta por defecto para dinero. | Use la `1105` (Caja General) o `1110` (Bancos). |
| **Cuenta Débito CxC** | Cuenta de Cartera (Deuda Cliente). | Use la `1305` (Clientes Nacionales). |
| **Cuenta Crédito CxP** | Cuenta de Proveedores (Deuda Nuestra). | Use la `2205` (Proveedores Nacionales). |

---

## 5. Guía de Configuración Paso a Paso

### 5.1. Crear un Nuevo Tipo (Caso Práctico: Factura de Venta)
1.  Haga clic en el botón **Crear Nuevo Tipo** (color índigo) en la parte superior derecha.
2.  **Datos Básicos:**
    *   **Código:** `FV01`.
    *   **Nombre:** `Factura de Venta Principal`.
    *   **Numeración:** Automática.
    *   **Consecutivo:** 0 (para iniciar en 1).
3.  **Lógica de Negocio (¡Crucial!):**
    *   Marque **Afecta Inventario** (Si vende productos físicos).
    *   Seleccione Función Especial: **VENTAS**.
4.  **Cuentas Contables (El enrutamiento):**
    *   **Cuenta Caja:** Seleccione su cuenta de Caja General (1105). *Esto habilita ventas de contado.*
    *   **Cuenta Débito CxC:** Seleccione Clientes Nacionales (1305). *Esto habilita ventas a crédito y el módulo de cartera.*
5.  Haga clic en **Guardar**.

### 5.2. Diseñar Formato de Impresión
ContaPY permite personalizar cómo se ve el PDF de cada documento.
1.  En la tabla principal, ubique la columna **Diseño**.
2.  Haga clic en el botón **Diseñar** (icono de regla y lápiz).
3.  Se abrirá el editor visual donde podrá ajustar márgenes, logos y tamaños de letra.

### 5.3. Editar o Eliminar
*   **Editar:** Use el botón con el icono de lápiz para modificar nombres o cuentas asociadas.
*   **Eliminar:** Use el botón de papelera.
    > **Nota de Seguridad:** El sistema NO permitirá eliminar un tipo de documento si ya existen movimientos contables creados con él. Esto es un candado de seguridad para proteger la integridad histórica de su contabilidad.

---

## 6. Preguntas Frecuentes y Solución de Problemas

*   **P: Hice un Recibo de Caja pero no me deja cruzarlo con la Factura.**
    *   **R:** Verifique la configuración del Tipo de Documento "Recibo de Caja". Asegúrese de que tenga asignada la **MISMA** cuenta de Cartera (ej. 1305) que usó en la Factura de Venta. Sin esa coincidencia, el sistema no puede vincularlos.

*   **P: ¿Puedo cambiar la numeración de Automática a Manual después de crear documentos?**
    *   **R:** Técnicamente sí, pero **NO se recomienda**. Podría generar huecos o duplicados en sus consecutivos, lo cual es grave ante una auditoría fiscal.

*   **P: ¿Por qué el sistema me pide una Bodega obligatoriamente?**
    *   **R:** Porque activó la casilla "Afecta Inventario" en el tipo de documento. Si está haciendo una factura de solo servicios, debería usar un tipo de documento diferente que tenga esa casilla desactivada.
