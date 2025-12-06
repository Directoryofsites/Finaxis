# Manual de Usuario - Capítulo 14: Gestión de Soporte (Interno)

## 1. Introducción
Este módulo es de uso exclusivo para el **Super-Administrador** del sistema. Permite gestionar las credenciales de los agentes de soporte técnico que tendrán acceso a las herramientas de diagnóstico y reparación de la base de datos.

**Ubicación:** `Administración > Utilidades > Panel de Soporte > Pestaña "Gestión Soporte"`

> [!IMPORTANT]
> **Acceso Restringido:** Los usuarios creados aquí tienen permisos elevados sobre todas las empresas del sistema. Solo debe otorgar acceso a personal de absoluta confianza.

---

## 2. Funcionalidades

### 2.1. Listado de Agentes
El panel muestra la lista de usuarios de soporte activos actualmente, con su correo electrónico y nombre completo.

### 2.2. Crear Nuevo Agente
Para dar de alta a un nuevo técnico:
1.  Complete el formulario inferior con **Email**, **Nombre Completo** y **Contraseña**.
2.  Haga clic en **"Crear Usuario"**.
3.  El nuevo agente podrá iniciar sesión inmediatamente en el panel de soporte.

### 2.3. Cambiar Contraseña
Si un agente olvida su clave o por seguridad se requiere rotarla:
1.  Busque al usuario en la lista.
2.  Haga clic en el botón **"Cambiar Contraseña"**.
3.  Ingrese la nueva clave en la ventana emergente.

### 2.4. Eliminar Agente
Para revocar el acceso a un técnico:
1.  Haga clic en el botón rojo **"Eliminar"**.
2.  Confirme la acción.
3.  El usuario perderá acceso inmediato al sistema.

---

## 3. Seguridad
*   **Auditoría:** Todas las acciones realizadas por los agentes de soporte quedan registradas en el log del sistema.
*   **Alcance:** Un usuario de soporte puede ver y modificar datos de *cualquier* empresa registrada en ContaPY2.
