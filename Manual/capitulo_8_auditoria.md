# Manual de Usuario - Capítulo 8: Auditoría de Consecutivos

## 1. Introducción
El módulo de **Auditoría de Consecutivos** es su herramienta de control fiscal y administrativo.

Su objetivo es responder una sola pregunta: **¿Falta algún documento?**
En contabilidad, la numeración consecutiva es sagrada. Si usted tiene la factura #100 y la #102, la DIAN (o su auditor) le preguntará: *"¿Dónde está la #101?"*. Este módulo escanea su base de datos en busca de esos "huecos" o saltos injustificados.

---

## 2. ¿Cómo acceder al módulo?
Siga esta ruta en el menú principal:

1.  Ubique la sección **Administración y Configuración**.
2.  Busque el grupo **Utilidades**.
3.  Haga clic en la opción **Auditoría de Consecutivos**.

> **Ruta Rápida:** `Administración > Utilidades > Auditoría`

---

## 3. Lógica de Negocio (Estados del Documento)

El sistema clasifica cada número en uno de estos estados:

### 3.1. ACTIVO (Normal)
El documento existe, tiene valores y es válido contablemente.

### 3.2. ANULADO (Legal)
El documento existe pero sus valores son CERO.
*   **Significado:** Se cometió un error, se anuló formalmente, y queda la evidencia (el "papel tachado").
*   **Impacto:** Correcto. No genera huecos fiscales.

### 3.3. ELIMINADO (Riesgo)
El documento existió alguna vez, pero fue borrado físicamente de la base de datos (probablemente por un administrador).
*   **Impacto:** Deja una huella de auditoría ("Aquí hubo algo"), pero no se puede recuperar el contenido.

### 3.4. HUECO (Alerta Máxima)
El sistema detecta un salto numérico sin explicación.
*   *Ejemplo:* Existe la factura #50 y la #52, pero la #51 nunca se creó ni se anuló. Simplemente no está.
*   **Causa Común:** Errores de red durante el guardado o manipulación indebida de la base de datos.

---

## 4. Guía Paso a Paso

### 4.1. Ejecutar una Auditoría
1.  Seleccione el **Tipo de Documento** que desea revisar (ej: Factura de Venta).
2.  Haga clic en el botón azul **Auditar**.
3.  El sistema escaneará miles de registros en segundos.

### 4.2. Interpretar los Resultados
Verá una tabla con colores:
*   **Blanco:** Documentos normales.
*   **Verde:** Documentos anulados (Correcto).
*   **Rojo:** Documentos eliminados (Atención).
*   **Amarillo (HUECO):** Saltos numéricos. El sistema le dirá: *"¡Alerta! Faltan 3 consecutivos desde el #105 hasta el #107"*.

---

## 5. Preguntas Frecuentes (FAQ)

*   **P: ¿El sistema puede "rellenar" los huecos automáticamente?**
    *   **R:** **No.** Por seguridad, el sistema nunca crea documentos fantasma. Si tiene un hueco, debe justificarlo manualmente ante su auditor o crear un documento con ese número (si el sistema se lo permite y la fecha corresponde).

*   **P: ¿Por qué tengo tantos "Huecos" en mis Cotizaciones?**
    *   **R:** Es normal. Las cotizaciones a menudo se borran o no se formalizan. La auditoría estricta es vital para **Facturas** y **Comprobantes de Egreso**, pero menos crítica para documentos internos.
