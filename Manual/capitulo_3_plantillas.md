# Manual de Usuario - Capítulo 3: Gestión de Plantillas Contables

## 1. Introducción
**¡Atención!** No confunda este módulo con el diseño de facturas PDF.
El módulo de **Plantillas Contables** es una herramienta de **Velocidad de Digitación**.

Su función es guardar "esqueletos" de asientos contables repetitivos (como la Nómina Mensual, el Arriendo o la Depreciación) para que usted no tenga que digitar cuenta por cuenta cada vez.

---

## 2. ¿Cómo acceder al módulo?
Siga esta ruta en el menú principal:

1.  Ubique la sección **Administración y Configuración**.
2.  Busque el grupo **Parametrización Maestra**.
3.  Haga clic en la opción **Administración de Plantillas**.

> **Ruta Rápida:** `Administración > Plantillas`

---

## 3. Lógica de Negocio (Reglas de Oro)

### 3.1. La Regla del Equilibrio (Balance)
El sistema **BLOQUEARÁ** el botón de guardar si la plantilla no está cuadrada.
*   **Suma de Débitos = Suma de Créditos.**
*   Si hay una diferencia de un solo centavo, el sistema asume que la plantilla es contablemente inválida y no permitirá crearla.

### 3.2. Datos "Sugeridos" vs. Fijos
Al crear una plantilla, verá campos como "Beneficiario Sugerido" o "Centro de Costo Sugerido".
*   **¿Qué significa "Sugerido"?** Que al usar la plantilla, el sistema llenará esos campos automáticamente, **PERO** usted podrá cambiarlos si lo desea.
*   *Ejemplo:* Puede crear una plantilla de "Pago de Arriendo" con la Inmobiliaria X como beneficiario sugerido. Si un mes cambia de inmobiliaria, podrá editarlo en el documento final sin dañar la plantilla original.

---

## 4. Guía Paso a Paso

### 4.1. Crear una Nueva Plantilla (Ej. Causación de Arriendo)
1.  Haga clic en el botón azul **Crear Nueva Plantilla**.
2.  **Datos Generales:**
    *   **Nombre:** `Causación Arriendo Oficina`.
    *   **Tipo Documento Sugerido:** Seleccione `Nota de Contabilidad` o `Comprobante de Egreso`.
    *   **Beneficiario:** Seleccione a su arrendador (opcional).
3.  **Movimientos (La "Receta" Contable):**
    *   **Fila 1:** Cuenta `5120 (Arrendamientos)` | Débito: `1.000.000` | Crédito: `0`.
    *   **Fila 2:** Cuenta `2408 (IVA Descontable)` | Débito: `190.000` | Crédito: `0`.
    *   **Fila 3:** Cuenta `2365 (Retención)` | Débito: `0` | Crédito: `35.000`.
    *   **Fila 4:** Cuenta `2335 (CxP Arrendamientos)` | Débito: `0` | Crédito: `1.155.000`.
4.  **Verificación:** Mire el total en la parte inferior. Si dice **BALANCEADO** en verde, el botón de guardar se activará.
5.  Haga clic en **Guardar Plantilla**.

### 4.2. Editar una Plantilla
1.  En la lista principal, haga clic en **Editar** (texto azul).
2.  Puede agregar nuevas cuentas o cambiar los valores base.
    > **Tip:** Use valores base (ej. 1.000) o déjelos en cero si los montos cambian cada mes. Lo importante es la estructura de cuentas.

---

## 5. Preguntas Frecuentes (FAQ)

*   **P: ¿Por qué el botón "Guardar" está gris y no funciona?**
    *   **R:** Mire el pie de página de la tabla. Seguramente dice **DESBALANCEADO** en rojo. Revise sus sumas; el Débito debe ser exactamente igual al Crédito.

*   **P: ¿Puedo usar una plantilla pero cambiarle el valor a una sola cuenta?**
    *   **R:** ¡Sí! La plantilla solo "pre-llena" el documento. Una vez cargada, usted tiene libertad total para editar montos, borrar filas o cambiar terceros antes de guardar el documento final.

*   **P: ¿Para qué sirve el "Concepto" en cada fila?**
    *   **R:** Ese texto aparecerá automáticamente en el movimiento contable. Sea genérico, por ejemplo: *"Canon de arrendamiento mes actual"*.

---

## 6. ¿Cómo usar las plantillas? (Conexión con Contabilidad)

Todo lo que usted cree en este módulo quedará disponible inmediatamente en el módulo de **Captura Rápida**.

1.  Vaya a **Contabilidad > Captura Rápida**.
2.  En el campo **"⚡ Plantilla (Requerido)"**, despliegue la lista.
3.  Seleccione la plantilla que acaba de crear (ej. `Causación Arriendo Oficina`).
4.  **¡Magia!** El sistema cargará automáticamente:
    *   El Tipo de Documento.
    *   El Beneficiario.
    *   Todas las cuentas contables con sus débitos y créditos.

Solo tendrá que ajustar la fecha y hacer clic en **Guardar Documento**. Así es como las plantillas le ahorran horas de trabajo manual.
