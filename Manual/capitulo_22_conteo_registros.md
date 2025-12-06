# Manual de Usuario - Capítulo 22: Control de Límites y Conteo

## 1. Introducción
Este módulo es el centro de control de facturación y consumo del sistema SaaS. Permite monitorear cuántos registros (documentos) está creando cada empresa y gestionar sus límites operativos.

**Ubicación:** `Administración > Utilidades > Panel de Soporte > Pestaña "Conteo"`

---

## 2. Panel Principal (Tabla)
Aquí verá el estado actual de todos los clientes:
*   **Consumo (Mes Actual):** Cantidad de documentos creados en el mes en curso.
*   **Plan Base:** El límite estándar contratado por el cliente (ej: 500 documentos/mes).
    *   *Edición Rápida:* Puede cambiar este número directamente en la tabla y al salir de la casilla (blur) se guardará automáticamente.

---

## 3. Gestión de Excepciones (Botón "Gestionar Meses")
A veces un cliente necesita más cupo solo por una temporada (ej: Navidad). No es necesario cambiar su contrato base; puede crear una **excepción mensual**.

### 3.1. Uso del Modal
1.  **Seleccione Mes y Año:** Por defecto aparece el mes actual.
2.  **Verifique Consumo Real:** El sistema le mostrará en tiempo real cuántos registros lleva la empresa y el porcentaje de uso del cupo.
    *   <span style="color:green">**Verde:**</span> Consumo normal.
    *   <span style="color:red">**Rojo (CRÍTICO):**</span> Cerca o excediendo el límite.
3.  **Definir Límite:**
    *   Ingrese el nuevo tope para ese mes específico.
    *   Ingrese `0` para borrar la excepción y que la empresa vuelva a usar su Plan Base.

### 3.2. Bloqueo de Servicio
Si una empresa supera su límite, el sistema **bloqueará la creación de nuevos documentos** automáticamente hasta el siguiente mes o hasta que soporte amplíe el cupo.
