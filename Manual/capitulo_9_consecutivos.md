# Manual de Usuario - Capítulo 9: Gestión de Consecutivos

## 1. Introducción
El módulo de **Gestión de Consecutivos** no es una pantalla separada, sino una función de seguridad integrada dentro de la configuración de cada documento.

Su objetivo es permitirle definir **dónde inicia** su facturación (ej: iniciar en la #500) o **corregir** saltos numéricos en casos de emergencia técnica.

---

## 2. ¿Cómo acceder?
La numeración vive dentro de cada Tipo de Documento:

1.  Vaya a `Administración > Maestros > Tipos de Documento`.
2.  Busque el documento que desea configurar (ej: Factura de Venta).
3.  Haga clic en el botón **Editar** (Lápiz).
4.  Busque la tarjeta **"Información General"**.

---

## 3. Lógica de Negocio (El Candado de Seguridad)

Por defecto, el campo **"Último Consecutivo"** aparece bloqueado (gris). Esto es intencional para evitar que un clic accidental reinicie su facturación a cero.

### 3.1. ¿Cómo funciona el contador?
El número que usted ve ahí es el **último utilizado**.
*   Si dice `100`, la próxima factura que haga el sistema será la `101`.
*   Si usted lo cambia manualmente a `500`, la próxima factura será la `501`.

### 3.2. El Botón "Forzar Edición"
Para cambiar este número, debe hacer clic en el pequeño enlace **"Forzar Edición"** (Icono de Candado Abierto).
*   **Advertencia:** Al hacer esto, usted asume la responsabilidad de la continuidad fiscal. Si baja el número (ej: de 100 a 90), el sistema intentará crear la 91, y si ya existe, **generará un error** al guardar.

---

## 4. Casos de Uso Comunes

### 4.1. Iniciar una Nueva Resolución DIAN
Si su empresa es nueva en el software pero ya lleva facturando años en papel hasta la #4500:
1.  Entre a editar la "Factura de Venta".
2.  Desbloquee el campo.
3.  Escriba `4500`.
4.  Guarde.
5.  *Resultado:* La primera factura que haga en el sistema será la #4501.

### 4.2. Corregir un Salto Técnico
Si por un error de luz se perdió la factura #50 y el sistema saltó a la #51:
1.  (Solo si es estrictamente necesario y bajo asesoría contable).
2.  Puede regresar el contador a `49` para intentar reutilizar la #50.
3.  **Riesgo:** Esto es peligroso si hay múltiples usuarios facturando al tiempo. Úselo solo en horarios no laborales.

---

## 5. Preguntas Frecuentes (FAQ)

*   **P: ¿Puedo tener dos tipos de factura con la misma numeración?**
    *   **R:** No. Cada Tipo de Documento (FV, RC, CE) maneja su propio contador independiente.

*   **P: ¿Qué pasa si pongo un número que ya existe?**
    *   **R:** El sistema bloqueará la creación de nuevos documentos con un error: *"El consecutivo ya existe"*. Tendrá que volver aquí y subir el número hasta uno libre.
