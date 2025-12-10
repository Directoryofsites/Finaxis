# Guía de Configuración de Pagos en Propiedad Horizontal (PH)

Esta guía explica paso a paso cómo configurar el sistema para recibir pagos de administración sin errores.

## ¿Por qué ocurre el error "No se encontró cuenta"?

Cuando usted registra un pago de administración, el sistema intenta hacer automáticamente el siguiente asiento contable (respetando la partida doble):

1.  **ENTRADA DE DINERO (DÉBITO):** Aumenta su Caja o Banco.
2.  **DISMINUCIÓN DE DEUDA (CRÉDITO):** Disminuye la cuenta por cobrar del propietario.

Si el sistema no sabe qué cuenta usar para alguna de las dos partes, bloquea el pago para evitar desastres contables.

---

## Configuración Correcta (Paso a Paso)

Para que funcione, se requieren dos configuraciones obligatorias:

### Paso 1: Configurar el Tipo de Documento (Contabilidad)
El documento que usted use (ej. "RC", "A11", "Recibo de Caja") debe tener claras las reglas del juego contable.

1.  Vaya al menú **Administración** > **Tipos de Documento**.
2.  Busque su documento (ej. `A11`) y haga clic en **Editar**.
3.  Verifique la sección de **MAPEO CONTABLE AUTOMÁTICO**:
    *   **TESORERÍA / CAJA (Cuenta Débito):** Aquí debe ir la cuenta donde entra el dinero (Ej: `110505 - Caja General`).
    *   **CUENTAS POR COBRAR (Cuenta Crédito):** Aquí debe ir la cuenta de la deuda que se está pagando (Ej: `130505 - Clientes Nacionales` o la cuenta de Cartera PH).

> **IMPORTANTE:** Nunca ponga la misma cuenta en ambos lados (Caja vs Caja). Eso confunde al sistema porque no hay contrapartida. Debe ser **Caja** (Entra) vs **Cartera** (Sale/Baja).

### Paso 2: Seleccionar el Documento en PH (Operativo)
El módulo de Propiedad Horizontal necesita saber cuál de todos sus documentos es el "oficial" para los recibos.

1.  Vaya al menú **Propiedad Horizontal** > **Configuración / Parámetros**.
2.  En el panel izquierdo ("Parámetros Generales"), busque el selector:
    *   **Doc. Recaudo (Recibos de Caja)**
3.  Seleccione el documento que configuró en el Paso 1.
4.  **HAGA CLIC EN "GUARDAR PARÁMETROS"**.

> **NOTA:** Si no guarda, el sistema no sabrá qué usar, aunque usted lo vea seleccionado en la pantalla.

---

## Preguntas Frecuentes

**¿Por qué en el otro PC funcionó de una?**
Probablemente en ese computador, el documento que seleccionaron ya tenía configurada correctamente la cuenta `1305` (Cartera) en su definición contable desde antes. El error en su equipo se debía a que el documento tenía la `1105` en ambos lados (Débito y Crédito), lo que dejaba al sistema sin saber cuál era la cuenta de Cartera real.

**¿Puedo usar cualquier cuenta de Cartera?**
Sí, puede usar la `130505`, `130595` o la que su contador prefiera, siempre y cuando sea una cuenta de naturaleza "Cobrar" (Activo).
