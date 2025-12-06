# Manual de Usuario - Capítulo 5: Gestión de Empresas

## 1. Introducción
El módulo de **Gestión de Empresas** es su panel de control corporativo.

Aquí no se gestiona la contabilidad del día a día, sino la **Identidad** de su organización ante el mundo. Los datos que configure aquí (Dirección, Teléfono, Logo) son los que aparecerán en el encabezado de todas sus Facturas, Egresos y Certificados.

---

## 2. ¿Cómo acceder al módulo?
Siga esta ruta en el menú principal:

1.  Ubique la sección **Administración y Configuración**.
2.  Busque el grupo **Administración del Sistema**.
3.  Haga clic en la opción **Gestión de Empresas**.

> **Ruta Rápida:** `Administración > Empresas`

---

## 3. Lógica de Negocio (Identidad Corporativa)

### 3.1. El "Membrete" Automático
El sistema toma los datos de esta pantalla para generar dinámicamente los PDFs.
*   **Razón Social y NIT:** Son legales y obligatorios.
*   **Dirección y Teléfono:** Aparecen en el pie de página o encabezado de las facturas.
*   **Logo URL:** Si usted pega aquí el enlace de su logo, el sistema lo estampará en la esquina superior izquierda de todos sus documentos.

### 3.2. Seguridad de Usuarios (Modo Lectura)
En la parte inferior verá la lista de **Usuarios Asociados**.
*   **¿Por qué no puedo editar usuarios aquí?**
    Por seguridad, la gestión de usuarios (crear, borrar, cambiar claves) se hace en un módulo separado. Aquí solo tiene una vista de "Auditoría" para saber quién tiene acceso a esta empresa.

---

## 4. Guía Paso a Paso

### 4.1. Actualizar Datos de Contacto
1.  En la lista de empresas, haga clic en el botón **Gestionar** de la empresa deseada.
2.  Modifique los campos necesarios (Dirección, Email, Teléfono).
3.  Haga clic en **Guardar Datos**.
    *   *Efecto Inmediato:* La próxima factura que imprima ya saldrá con la nueva dirección.

### 4.2. Configurar el Logo
Para que su logo aparezca en los documentos:
1.  Suba su logo a internet (puede ser en su sitio web o un servicio de imágenes).
2.  Copie la dirección de la imagen (debe terminar en `.png` o `.jpg`).
3.  Péguela en el campo **URL del Logo**.
4.  Guarde los cambios.

### 4.3. Conexión con el Diseñador de Documentos
El campo **Logo URL** no actúa solo. Trabaja en conjunto con el **Diseñador de Formatos** (ubicado en *Tipos de Documento > Diseñar*).

*   **La Variable Mágica:** El sistema inyecta automáticamente la variable `{{empresa.logo_url}}` en sus plantillas HTML.
*   **Funcionamiento:**
    1.  Usted pega el enlace aquí (ej: `https://miweb.com/logos/empresa1.png`).
    2.  Al generar una factura, el sistema busca esta variable.
    3.  Si existe, reemplaza el espacio del logo con su imagen específica.
    
> **Tip para Multi-Empresa:** Si gestiona cientos de empresas, le recomendamos crear una carpeta pública en su servidor (ej: `/logos/`) y nombrar los archivos con el NIT (ej: `800123456.png`). Así podrá construir las URLs de forma lógica y rápida.

---

## 5. Preguntas Frecuentes (FAQ)

*   **P: ¿Dónde está el botón de "Crear Empresa"?**
    *   **R:** La creación de empresas es una función delicada que conlleva la creación automática de bases de datos y usuarios administradores. Por seguridad, esta opción suele estar reservada para el "Super Administrador" o el equipo de Soporte Técnico.

*   **P: ¿Cómo elimino una empresa?**
    *   **R:** **¡Cuidado!** Eliminar una empresa es una "Opción Nuclear". Borraría no solo el nombre, sino todos los terceros, cuentas, facturas y movimientos históricos. Por eso, no encontrará un botón de eliminar aquí. Si necesita dar de baja una empresa, contacte a Soporte para un borrado seguro.

*   **P: Me sale un aviso de "No tienes permisos para ver usuarios".**
    *   **R:** Esto es normal si usted es un usuario operativo (ej. Auxiliar Contable). Solo los usuarios con rol de "Administrador" o "Gerente" pueden ver la lista de accesos.
