# Manual de Usuario - Capítulo 15: Crear Nueva Empresa

## 1. Introducción
Esta herramienta permite al equipo de soporte desplegar un nuevo entorno ("Tenant") para un cliente. El proceso crea tanto la entidad legal (Empresa) como los usuarios administradores iniciales en un solo paso.

**Ubicación:** `Administración > Utilidades > Panel de Soporte > Pestaña "Crear Empresa"`

---

## 2. Formulario de Registro

### 2.1. Datos de la Empresa
Estos son los datos fiscales obligatorios que definirán la identidad de la contabilidad:
*   **Razón Social:** El nombre legal de la compañía (ej: *Ferretería El Tornillo S.A.S.*).
*   **NIT:** El número de identificación tributaria sin dígito de verificación.
*   **Fecha Inicio de Operaciones:** La fecha contable desde la cual el sistema permitirá registrar movimientos.

### 2.2. Usuarios Administradores
Por defecto, el sistema exige crear al menos un usuario para que el cliente pueda acceder.
*   **Email:** Será el nombre de usuario para el inicio de sesión.
*   **Contraseña:** Debe tener mínimo 6 caracteres.

> [!TIP]
> **Múltiples Usuarios:** Puede hacer clic en "+ Añadir otro usuario" si necesita entregar la empresa con varios accesos configurados (ej: Gerente y Contador).

---

## 3. Proceso de Creación
1.  Diligencie todos los campos requeridos.
2.  Haga clic en el botón **"Crear Empresa y Usuarios"**.
3.  El sistema realizará las siguientes acciones automáticas:
    *   Creará el registro de la empresa en la base de datos maestra.
    *   Creará los usuarios vinculados a esa empresa.
    *   Asignará automáticamente el rol de **ADMINISTRADOR** a estos usuarios.
    *   Inicializará el Plan de Cuentas base (si está configurado así en el backend).

## 4. Solución de Problemas
*   **Error "El NIT ya existe":** Verifique en la pestaña "Gestión Empresas" si ya hay un registro con ese documento.
*   **Error "Email duplicado":** El correo electrónico ya está siendo usado por otro usuario en el sistema (incluso en otra empresa). Los emails deben ser únicos globalmente.
