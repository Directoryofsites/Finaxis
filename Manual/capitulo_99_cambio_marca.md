# Manual Técnico: Cambio de Nombre de Marca y Razón Social

Este documento detalla los archivos exactos que deben modificarse para cambiar el nombre del programa (actualmente "Finaxis") o la Razón Social de la empresa en el sistema.

## 1. Cambio de Nombre del Programa (Rebranding)

Si desea cambiar el nombre del software (ej. de "Finaxis" a "OtroNombre"), debe editar los siguientes archivos:

### Frontend (Interfaz de Usuario)

1.  **Barra Lateral (Menú Principal):**
    *   **Archivo:** `c:\ContaPY2\frontend\components\Sidebar.js`
    *   **Ubicación:** Busca la etiqueta `<h2>` cerca de la línea 22.
    *   **Código a editar:**
        ```javascript
        <h2 className="text-xl font-bold text-white">
            Finaxis <span className="text-sm font-light text-blue-400">v1.0</span>
        </h2>
        ```

2.  **Título de la Pestaña del Navegador:**
    *   **Archivo:** `c:\ContaPY2\frontend\app\layout.js`
    *   **Ubicación:** Objeto `metadata` cerca de la línea 6.
    *   **Código a editar:**
        ```javascript
        export const metadata = {
          title: "Sistema Finaxis", // <--- Cambiar aquí
          description: "Sistema contable integral para Colombia",
        };
        ```

3.  **Pantalla de Bienvenida (Login):**
    *   **Archivo:** `c:\ContaPY2\frontend\app\page.js`
    *   **Ubicación:** Componente `HomePageContent` (al final del archivo), sección de no autenticado.
    *   **Código a editar:**
        ```javascript
        <h1 className="text-4xl font-extrabold text-blue-600 mb-4">Finaxis</h1>
        <p className="mt-4 text-lg text-gray-600">Tu Sistema Finaxis ERP...</p>
        ```

4.  **Logo de la Aplicación:**
    *   **Archivo:** `c:\ContaPY2\frontend\public\logo.png`
    *   **Acción:** Reemplazar este archivo de imagen con el nuevo logo. Asegúrese de mantener el nombre `logo.png` o actualizar las referencias en el código.

### Backend (API y Reportes)

1.  **Título de la API (Documentación):**
    *   **Archivo:** `c:\ContaPY2\app\main.py`
    *   **Ubicación:** Definición de `FastAPI` cerca de la línea 91.
    *   **Código a editar:**
        ```python
        app = FastAPI(
            title="API del Sistema Finaxis", # <--- Cambiar aquí
            // ...
        )
        ```

2.  **Pie de Página en Reportes PDF:**
    *   **Ubicación:** `c:\ContaPY2\app\templates\reports\`
    *   **Archivos:** Debe revisar los archivos `.html` en esta carpeta.
    *   **Ejemplo:** `rentabilidad_documento_report.html` (Línea ~88).
    *   **Código a editar:**
        ```html
        <div class="footer">
            <p>Sistema Contable Finaxis.</p> <!-- Cambiar aquí -->
        </div>
        ```
    *   *Nota:* Puede usar un editor de código para buscar y reemplazar "Finaxis" en todos los archivos de esta carpeta.

3.  **Formatos de Impresión (Base de Datos):**
    *   Si al imprimir un documento (Factura, Comprobante, etc.) ve el texto "Impreso por Sistema ContaPY", esto **NO está en el código**, sino en la configuración de la plantilla en la Base de Datos.
    *   **Solución:**
        1.  Ingrese al sistema como Administrador.
        2.  Vaya a **Configuración** -> **Formatos de Impresión**.
        3.  Seleccione el formato que está usando (ej. "Estándar").
        4.  Edite el contenido HTML y busque el texto en el pie de página.
        5.  Cámbielo por "Impreso por Sistema Finaxis" y guarde.

---

## 2. Cambio de Razón Social (Nombre de la Empresa)

El nombre de la empresa que aparece en los reportes y en la barra superior **NO está escrito en el código**, sino que se toma de la Base de Datos.

### Cómo cambiarlo:

1.  **Desde la Aplicación:**
    *   Ingrese al módulo **Administración** -> **Gestión de Empresas**.
    *   Seleccione su empresa y haga clic en **Editar**.
    *   Cambie el campo **Razón Social**.
    *   Guarde los cambios.

2.  **Efecto:**
    *   Este cambio se reflejará automáticamente en:
        *   Encabezados de todos los reportes PDF.
        *   Barra superior del Dashboard.
        *   Certificados y documentos generados.

### Excepción (Si se codificó manualmente en algún reporte específico):
Si por alguna razón ve un nombre de empresa fijo que no cambia al editar la base de datos, revise los archivos en `c:\ContaPY2\app\templates\reports\` y busque si el nombre fue escrito directamente en el HTML en lugar de usar la variable `{{ empresa.razon_social }}`.
