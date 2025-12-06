# Manual de Usuario - Capítulo 10: Edición de Documentos

## 1. Descripción General

La interfaz de **Edición de Documentos** es un entorno controlado diseñado para modificar transacciones contables ya guardadas. A diferencia de la creación inicial, este módulo impone restricciones estrictas para garantizar la integridad de la base de datos histórica.

**Acceso:** Desde el *Explorador de Documentos* o la *Gestión Masiva*, haciendo clic en el botón "Modificar" o el icono de lápiz.

---

## 2. Estructura de la Pantalla
Al ingresar al modo de edición, la pantalla se divide en tres secciones críticas, diseñadas para diferenciar claramente qué se puede cambiar y qué es inmutable.

### 2.1. Encabezado de Identificación (Zona Bloqueada)
En la parte superior derecha, verá campos con fondo grisáceo que **NO** son editables. Esto es una medida de seguridad:
*   **Tipo de Documento:** (Ej: *Comprobante de contabilidad*) Define la naturaleza legal del registro.
*   **Número:** (Ej: *111*) Es el identificador único (Consecutivo). Cambiarlo rompería la secuencia cronológica.

### 2.2. Datos de Encabezado (Zona Editable)
A la izquierda y centro, encontrará los campos que definen el contexto de la transacción. Estos **SÍ** pueden modificarse para corregir errores de imputación:
*   **Fecha:** Permite mover el documento en el tiempo (ej: cambiarlo del día 22 al 23).
    *   *Nota:* El sistema validará que la nueva fecha pertenezca a un periodo contable abierto.
*   **Beneficiario:** Desplegable para reasignar la transacción a otro Tercero (ej: cambiar *NVIDIA* por otro proveedor si la factura se cargó al NIT incorrecto).
*   **Centro de Costo:** Permite reclasificar el gasto o ingreso a otro departamento o proyecto (ej: mover de *Ninguno* a *Administración*).

### 2.3. Tabla de Movimientos Contables
El núcleo de la edición. Aquí se visualiza el asiento contable completo ("La Partida Doble").

*   **Columnas:**
    *   *CUENTA:* Código y nombre de la cuenta PUC (ej: *110505 - Caja General*).
    *   *CONCEPTO:* Descripción detallada del renglón (ej: *aseo*).
    *   *DÉBITO / CRÉDITO:* Valores numéricos de la transacción.
*   **Herramientas de Edición:**
    *   **Modificar Valores:** Puede hacer clic en cualquier celda de Débito o Crédito para ajustar montos.
    *   **Eliminar Filas (X Roja):** Ubicada a la derecha de cada renglón. Permite borrar movimientos erróneos.
    *   **Agregar Fila (Botón Blanco):** Inserta una nueva línea vacía al final para añadir cuentas olvidadas (ej: agregar una retención que faltó).

---

## 3. Validaciones y Guardado

### 3.1. La Regla de Oro: "Sumas Iguales"
En la parte inferior derecha, el sistema muestra en tiempo real los **Totales**:
*   *Total Débito*
*   *Total Crédito*

> [!IMPORTANT]
> **Bloqueo por Descuadre:** El botón verde **"Guardar Cambios"** solo funcionará si la diferencia entre Débitos y Créditos es exactamente **$0,00**. Si los montos no coinciden, el sistema impedirá guardar para proteger la contabilidad.

### 3.2. Finalizar Edición
Una vez realizados los ajustes y verificado el balance:
1.  Haga clic en el botón verde ancho **"Guardar Cambios"** al pie de página.
2.  El sistema confirmará la actualización y le redirigirá al panel anterior.
3.  Si decide no guardar, use el botón superior **"Regresar al Panel Principal"** para descartar los cambios.
