# Manual de Usuario - Capítulo 24: Nuevo Documento Contable

## 1. Introducción
Este es el módulo central del sistema. Aquí se registran todos los hechos económicos (Asientos, Facturas, Recibos, Notas) de forma manual.

**Ubicación:** `Contabilidad > Documentos > Nuevo`

---

## 2. Cabecera del Documento
Antes de ingresar los movimientos, debe definir los datos generales:

1.  **Fecha Contable:** Por defecto es hoy. Afecta el periodo contable.
2.  **Tipo de Documento:** Clasifica la operación (ej: `CC - Comprobante de Contabilidad`).
    *   *Nota:* Al seleccionar el tipo, el sistema cargará automáticamente el **siguiente número consecutivo** disponible.
3.  **Beneficiario (Tercero):** Quién está involucrado en la transacción.
4.  **Centro de Costo:** (Opcional) Para imputación de costos.

### 2.1. Funciones Especiales (Cartera y Proveedores)
Si selecciona un tipo de documento configurado para **Recaudo (RC)** o **Pago (CE/EG)**:
*   Aparecerá el campo **Valor Total a Abonar**.
*   Se desplegará la tabla de **Facturas Pendientes** de ese tercero.
*   Podrá distribuir el pago entre las facturas pendientes. El sistema generará los asientos de cruce automáticamente.

---

## 3. Detalle Contable (La Grilla)
Aquí se ingresan las cuentas.
*   **Cuenta Contable:** Puede buscar por código (ej: `1105`) o nombre (ej: `Caja`).
*   **Concepto:** Descripción del movimiento.
    *   *Tip:* Puede guardar conceptos frecuentes usando el botón `+`.
*   **Débito / Crédito:** Ingrese los valores.
    *   *Atajo:* Use las teclas `+` (miles) y `-` (centenas) para agregar ceros rápidamente.
    *   *Balance:* El sistema no dejará guardar si la diferencia no es cero.

---

## 4. Plantillas
Para ahorrar tiempo en asientos repetitivos (ej: Nómina, Arriendos):
*   **Cargar:** Seleccione una plantilla del menú desplegable "Cargar Plantilla".
*   **Guardar:** Si acaba de hacer un asiento que usará después, haga clic en "Guardar Plantilla".

## 5. Finalización
*   **Guardar Documento:** Registra la operación y genera el asiento.
*   **Imprimir:** Genera un PDF oficial del documento.
