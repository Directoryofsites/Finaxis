# Manual de Usuario - Capítulo 16: Gestión de Empresas

## 1. Introducción
Este módulo permite administrar el ciclo de vida de las empresas (tenants) registradas en el sistema. Desde aquí se pueden actualizar datos fiscales, gestionar usuarios específicos de cada empresa o dar de baja un servicio.

**Ubicación:** `Administración > Utilidades > Panel de Soporte > Pestaña "Gestión Empresas"`

---

## 2. Listado de Empresas
El panel presenta una tabla con todas las compañías activas, mostrando su **NIT** y **Razón Social**.

## 3. Acciones Disponibles

### 3.1. Gestionar (Botón Azul)
Abre una ventana modal con dos pestañas internas:
1.  **Datos:** Permite corregir el nombre, NIT o fecha de inicio de la empresa.
2.  **Usuarios:** Permite ver, crear o eliminar usuarios *específicos* de esa empresa (sin afectar a otras).
    *   *Útil para:* Restablecer la contraseña del contador de un cliente específico.

### 3.2. Eliminar (Botón Rojo)
Esta es la acción más destructiva del sistema.
*   **Consecuencias:** Borra la empresa y **TODA** su información vinculada (documentos, terceros, cuentas, usuarios).
*   **Irreversible:** No hay papelera de reciclaje para empresas eliminadas.

> [!CAUTION]
> **Peligro de Pérdida de Datos:**
> Asegúrese de tener una copia de seguridad completa antes de eliminar una empresa. Esta acción no se puede deshacer.

---

## 4. Preguntas Frecuentes
*   **P: ¿Puedo fusionar dos empresas?**
    *   **R:** No automáticamente. Debe exportar datos de una e importarlos en la otra manualmente.
*   **P: ¿Por qué no puedo eliminar una empresa?**
    *   **R:** Es posible que el sistema tenga bloqueos de seguridad si la empresa tiene transacciones activas recientes. Contacte al desarrollador si el problema persiste.
