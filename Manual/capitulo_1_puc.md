# 📘 Manual de Usuario - Capítulo 1: El Plan de Cuentas (PUC)

## 1. Introducción
El **Plan de Cuentas (PUC)** es la columna vertebral de su sistema contable. Es el listado organizado de todas las cuentas necesarias para registrar los hechos económicos de la empresa (activos, pasivos, patrimonio, ingresos, gastos y costos).

En **PYsis**, el Plan de Cuentas es:
*   🏗️ **Jerárquico:** Las cuentas se organizan en niveles (Clase, Grupo, Cuenta, Subcuenta, Auxiliar).
*   🧩 **Flexible:** Puede crear tantos niveles y auxiliares como su empresa requiera.
*   🧠 **Inteligente:** El sistema valida automáticamente la estructura y calcula los niveles.

---

## 2. ¿Cómo acceder al módulo?

Para gestionar el Plan de Cuentas, siga esta ruta en el menú principal:

1.  Ubique la sección **⚙️ Administración y Configuración**.
2.  Busque el grupo **Parametrización Maestra**.
3.  Haga clic en la opción **📖 Gestionar PUC**.

> **Ruta:** `Administración > Parametrización Maestra > Gestionar PUC`

---

## 3. Conceptos Fundamentales

Antes de crear cuentas, es vital entender dos conceptos clave que el sistema le pedirá:

### A. Cuenta de Movimiento vs. Cuenta de Grupo
| Tipo de Cuenta | Descripción | Ejemplo |
| :--- | :--- | :--- |
| **📂 Cuenta de Grupo (Padre)** | Son cuentas que agrupan a otras. **NO** se pueden usar para hacer asientos contables. Su función es organizar y sumarizar. | `1105 - CAJA` |
| **📝 Cuenta de Movimiento (Auxiliar)** | Son las cuentas de último nivel donde **SÍ** se registran los valores. | `110505 - CAJA GENERAL` |

> *Nota:* En el sistema, esto se define con la casilla **"Permite Movimiento"**.

### B. Jerarquía y Código
El código define la jerarquía. Usted no necesita decirle al sistema el nivel, él lo calcula por la longitud del código y quién es su padre.

*   **Clase:** 1 dígito (Ej: `1`)
*   **Grupo:** 2 dígitos (Ej: `11`)
*   **Cuenta:** 4 dígitos (Ej: `1105`)
*   **Subcuenta:** 6 dígitos (Ej: `110505`)
*   **Auxiliar:** 8 o más dígitos.

---

## 4. Guía Paso a Paso

### 4.1. Crear una Nueva Cuenta

1.  En la pantalla del PUC, haga clic en el botón **"➕ Cuenta Raíz"** o en el botón **"Sub"** de una cuenta existente.
2.  Complete el formulario con los siguientes datos:
    *   **Código:** Escriba el código numérico único (Ej: `11050501`).
    *   **Nombre:** El nombre descriptivo de la cuenta (Ej: `Caja Menor Oficina Principal`).
    *   **Cuenta Padre:** Seleccione la cuenta superior a la que pertenece.
    *   **Permite Movimiento:**
        *   ✅ Marque esta casilla **SÍ** si es una cuenta auxiliar donde registrará dinero.
        *   ⬜ Déjela desmarcada **NO** si es una cuenta título o de agrupación.
3.  Haga clic en **Guardar**.

### 4.2. Editar una Cuenta Existente

1.  Busque la cuenta en el listado o use la barra de búsqueda por código o nombre.
2.  Haga clic en el icono de **✏️ Lápiz (Editar)** al lado de la cuenta.
3.  Modifique el nombre u otras propiedades.
    *   ⚠️ *Advertencia:* Cambiar el código o el padre de una cuenta que ya tiene movimientos puede afectar sus reportes. Hágalo con precaución.
4.  Haga clic en **Actualizar**.

### 4.3. Eliminar una Cuenta

1.  Ubique la cuenta que desea borrar.
2.  Haga clic en el icono de **🗑️ Basura (Eliminar)**.
3.  Confirme la acción.

> **⛔ Restricciones de Seguridad:** El sistema **NO** le permitirá borrar una cuenta si:
> *   Tiene cuentas hijas (primero debe borrar las hijas).
> *   Ya tiene movimientos contables registrados (para garantizar la integridad de la contabilidad).

---

## 5. Herramientas Avanzadas

### 🛡️ Depuración Jerárquica (Protección al Eliminar)
La herramienta de **Depuración** es un **asistente automático** que se activa cuando usted intenta **Eliminar** una cuenta con hijos.

**¿Cómo funciona?**
1.  Cuando usted hace clic en el icono de **🗑️ Eliminar** de una cuenta padre.
2.  El sistema ejecuta automáticamente un **Análisis de Depuración**.
3.  Se abrirá una ventana emergente mostrándole:
    *   Si la cuenta tiene subcuentas (hijos) que también se eliminarán.
    *   Si existen conflictos que impiden la eliminación.
4.  Usted podrá revisar esta información y confirmar la eliminación en cascada si está seguro.

> **Nota:** Esta es una medida de seguridad para evitar que queden "ramas sueltas" en su árbol contable.
