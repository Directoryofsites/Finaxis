# Manual de Usuario - Capítulo 50: Gestión de Centros de Costo

## 1. Introducción
El módulo de **Centros de Costo** permite definir la estructura organizativa de la empresa para la imputación detallada de gastos e ingresos.

A diferencia del Plan Único de Cuentas (PUC) que es obligatorio y legal, los Centros de Costo son una herramienta de **Contabilidad Administrativa** que le permite saber *en qué* o *quién* se gasta el dinero (ej: "Departamento de Ventas", "Proyecto Edificio Norte", "Sucursal Centro").

---

## 2. ¿Cómo acceder al módulo?
Siga esta ruta en el menú principal:

1.  Ubique la sección **Administración y Configuración**.
2.  Busque el grupo **Administración del Sistema**.
3.  Haga clic en la opción **Centros de Costo**.

> **Ruta Rápida:** `Administración > Centros de Costo`

---

## 3. Lógica de Negocio (Estructura Jerárquica)

El sistema maneja una estructura de árbol (padres e hijos) para organizar sus centros de costo.

### 3.1. Tipos de Centro de Costo
Existen dos tipos fundamentales que debe conocer:

*   **📂 Título (Carpeta):**
    *   Sirve solo para agrupar otros centros de costo.
    *   **NO** recibe movimientos contables.
    *   Ejemplo: "10 - DEPARTAMENTO ADMINISTRATIVO".
    *   Se identifica con un icono de carpeta amarilla.

*   **📄 Auxiliar (Movimiento):**
    *   Es el nivel último donde se registran los gastos.
    *   **SÍ** recibe movimientos contables.
    *   Ejemplo: "10.01 - Gerencia General".
    *   Se identifica con un icono de documento azul y la etiqueta "Auxiliar".

---

## 4. Guía Paso a Paso

### 4.1. Crear un Nivel Principal (Raíz)
Si está empezando desde cero, lo primero es crear las grandes divisiones de su empresa.

1.  Haga clic en el botón **+ Crear Nivel Principal** ubicado en la parte superior derecha.
2.  **Código:** Ingrese un código numérico (ej: `10`, `20`, `30`).
3.  **Nombre:** Escriba el nombre del área (ej: `ADMINISTRACIÓN`).
4.  **¿Es Auxiliar?:**
    *   Marque la casilla si este centro recibirá gastos directamente.
    *   **Desmarque** la casilla si planea crear sub-divisiones dentro de él (recomendado para niveles principales).
5.  Haga clic en **Guardar**.

### 4.2. Crear un Sub-nivel (Hijo)
Para crear una subdivisión dentro de una carpeta existente:

1.  Ubique el centro de costo "Padre" en la lista.
2.  Haga clic en el botón verde con el signo más **(+)** en la columna de acciones.
    *   *Nota: Este botón solo aparece en los centros tipo "Título".*
3.  El sistema abrirá el formulario y pre-seleccionará automáticamente la ubicación correcta.
4.  Complete el código (ej: si el padre es `10`, el hijo podría ser `10.01`).
5.  Defina el nombre y si es auxiliar o título.
6.  Guarde los cambios.

### 4.3. Editar un Centro de Costo
1.  Haga clic en el botón azul con el lápiz **(Editar)**.
2.  Modifique el nombre o corrija el código si es necesario.
3.  Guarde los cambios.

### 4.4. Eliminar un Centro de Costo
1.  Haga clic en el botón rojo con la papelera **(Eliminar)**.
2.  Confirme la acción en la ventana emergente.

> **Restricción de Seguridad:** No podrá eliminar un centro de costo si este ya tiene movimientos contables asociados o si tiene hijos (sub-niveles) dentro de él. Primero debe reasignar los movimientos o eliminar los hijos.

---

## 5. Preguntas Frecuentes (FAQ)

*   **P: ¿Puedo cambiar un centro de "Título" a "Auxiliar" después de crearlo?**
    *   **R:** Sí, puede editarlo y cambiar la casilla "Es Auxiliar". Sin embargo, tenga cuidado: si lo convierte en "Auxiliar", ya no podrá crearle hijos. Y si lo convierte en "Título", asegúrese de que no tenga movimientos contables directos, pues quedarían "huérfanos" de nivel.

*   **P: ¿Qué código debo usar?**
    *   **R:** El sistema es flexible, pero recomendamos usar una estructura escalonada con puntos para mayor orden visual:
        *   Nivel 1: `10`, `20`, `30`
        *   Nivel 2: `10.01`, `10.02`
        *   Nivel 3: `10.01.001`

*   **P: ¿Cuántos niveles de profundidad puedo tener?**
    *   **R:** No hay un límite técnico estricto, pero por usabilidad recomendamos no exceder 4 o 5 niveles de profundidad.
