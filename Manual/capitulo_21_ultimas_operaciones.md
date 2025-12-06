# Manual de Usuario - Capítulo 21: Últimas Operaciones

## 1. Introducción
Este módulo es el "ojo que todo lo ve" del sistema. Permite consultar una bitácora global de todas las operaciones críticas (Creación, Anulación, Eliminación) realizadas en **cualquier empresa**.

**Ubicación:** `Administración > Utilidades > Panel de Soporte > Pestaña "Últimas Operaciones"`

---

## 2. Filtros de Búsqueda
Para evitar sobrecargar el sistema, la consulta debe ser específica:

### 2.1. Límite y Orden
*   **Límite:** Cantidad máxima de registros a traer (por defecto 50).
*   **Ordenar Por:**
    *   *Fecha de Creación:* Cuándo se grabó el dato en el servidor (tiempo real).
    *   *Fecha del Documento:* La fecha contable asignada al documento.

### 2.2. Filtros de Tiempo
*   **Por Fecha de Creación:** Útil para saber "¿Qué hicieron los usuarios hoy entre las 2 PM y las 4 PM?".
*   **Por Fecha del Documento:** Útil para auditar periodos contables (ej: "¿Qué documentos se crearon con fecha de Enero 2023?").

### 2.3. Filtro por Empresa
Puede seleccionar una o varias empresas manteniendo presionada la tecla `Ctrl` (o `Cmd` en Mac). Si no selecciona ninguna, buscará en **todas**.

---

## 3. Interpretación de la Tabla
*   **Empresa:** El tenant donde ocurrió el evento.
*   **Usuario:** El correo electrónico de quien realizó la acción.
*   **Operación:**
    *   <span style="color:green">**CREACIÓN:**</span> Nuevo documento registrado.
    *   <span style="color:orange">**ANULACIÓN:**</span> Documento invalidado (reversión contable).
    *   <span style="color:red">**ELIMINACIÓN:**</span> Documento borrado físicamente (o enviado a papelera).
