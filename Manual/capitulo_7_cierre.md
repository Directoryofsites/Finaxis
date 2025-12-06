# Manual de Usuario - Capítulo 7: Cierre de Periodos Contables

## 1. Introducción
El módulo de **Gestión de Periodos** es el candado de seguridad de su contabilidad.

Su función es simple pero crítica: **Bloquear el tiempo**.
Una vez usted cierra un mes (ej: Enero), el sistema prohíbe terminantemente crear, editar o borrar cualquier documento con fecha de ese mes. Esto garantiza que sus estados financieros presentados a la DIAN o a la Gerencia no cambien "mágicamente" después de ser reportados.

---

## 2. ¿Cómo acceder al módulo?
Siga esta ruta en el menú principal:

1.  Ubique la sección **Administración y Configuración**.
2.  Busque el grupo **Utilidades**.
3.  Haga clic en la opción **Periodos Contables**.

> **Ruta Rápida:** `Administración > Utilidades > Periodos`

---

## 3. Lógica de Negocio (El Mecanismo de Cremallera)

El sistema utiliza una lógica secuencial estricta, similar a subir o bajar una cremallera:

### 3.1. Para Cerrar (Subir Cremallera)
*   **Orden Obligatorio:** Usted no puede cerrar Marzo si Febrero sigue abierto. Debe ir en orden: Enero -> Febrero -> Marzo.
*   **Validación de Inicio:** No puede cerrar periodos anteriores a la fecha de fundación de su empresa.

### 3.2. Para Reabrir (Bajar Cremallera)
*   **Orden Inverso:** Si necesita corregir algo en Enero pero ya cerró hasta Marzo, el sistema le exigirá reabrir en orden inverso: Primero reabre Marzo, luego Febrero, y finalmente Enero.
*   **¿Por qué es tan estricto?** Porque los saldos de Febrero dependen de Enero. Si usted cambia Enero, automáticamente invalida los saldos iniciales de Febrero y Marzo. Esta restricción protege la integridad matemática de su contabilidad.

---

## 4. Guía Paso a Paso

### 4.1. Cerrar un Mes
1.  Ingrese al módulo. Verá una tabla con los meses del año actual.
2.  Busque el primer mes con estado **"Abierto"** (Color Verde).
3.  Haga clic en el botón azul **Cerrar Período**.
4.  Confirme la acción.
    *   *Resultado:* El estado cambiará a **"Cerrado"** (Rojo) y nadie podrá alterar datos de ese mes.

### 4.2. Reabrir un Mes (Correcciones)
1.  Busque el último mes con estado **"Cerrado"**.
2.  Haga clic en el botón amarillo **Reabrir Período**.
3.  Confirme la advertencia de seguridad.
    *   *Resultado:* El mes volverá a estar disponible para edición.

---

## 5. Preguntas Frecuentes (FAQ)

*   **P: ¿El cierre genera el asiento de "Cierre de Año" (Cancelación de cuentas de resultado)?**
    *   **R:** **No.** Este módulo es solo un bloqueo de seguridad (permisos). El asiento contable de cierre de año (Cuenta 59) es un proceso automático separado que se ejecuta en el módulo de "Comprobantes Automáticos".

*   **P: Soy el Gerente, ¿puedo editar un mes cerrado sin reabrirlo?**
    *   **R:** **No.** Ni siquiera el "Super Usuario" puede violar un periodo cerrado. La única forma es reabrirlo formalmente, hacer el cambio, y volver a cerrar. Esto deja una huella de auditoría clara.

*   **P: ¿Puedo cerrar el año 2024 si no he terminado el 2023?**
    *   **R:** No. El sistema exige continuidad cronológica absoluta. Debe cerrar Diciembre 2023 antes de poder cerrar Enero 2024.
