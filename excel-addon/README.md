# Finaxis Excel Add-in (ContaExcel Premium)

Este directorio contiene el código fuente nativo de Microsoft Office Web Add-ins, que permite a Excel comunicarse directamente con la base de datos contable de Finaxis.

## ¿Cómo Probarlo Localmente (Sideloading)?

Dado que el Add-in consulta a la web, Microsoft requiere que los archivos JS y HTML estén alojados en un servidor **HTTPS**. Para pruebas locales:

### 1. Servir los archivos con HTTPS local (Recomendado)
Puedes usar Live Server de VSCode o un paquete de Node llamado `http-server` con certificados falsos.

```bash
# Requiere NodeJS
npx office-addin-dev-certs install
npx http-server -p 3000 --ssl --cert ~/.office-addin-dev-certs/localhost.crt --key ~/.office-addin-dev-certs/localhost.key
```

### 2. Cargar en Excel Desktop (Windows)
1. Abre Excel en blanco -> **Archivo** -> **Opciones** -> **Centro de confianza** -> **Configuración del Centro de confianza**.
2. Ve a **Catálogos de complementos de confianza**.
3. En el campo "URL del catálogo", pon la dirección física de la carpeta compartida donde guardaste el `manifest.xml` (debes compartir la carpeta `excel-addon` en red local, por ejemplo `\\TU-PC\excel-addon`).
4. Dale a **Agregar catálogo** y **Mostrar en el menú**.
5. Reinicia Excel.
6. Ve a **Insertar** -> **Mis complementos** -> Busca "Finaxis ContaExcel" en el panel "Carpeta compartida".

### 3. Cargar en Excel Web (Navegador) - ¡Mucho Más Fácil!
1. Abre Excel Online (Office.com).
2. Crea un libro nuevo.
3. Ve a **Insertar** -> **Complementos** -> **Mis Complementos**.
4. Haz clic en **Administrar mis complementos** -> **Cargar mi complemento**.
5. Selecciona el archivo `manifest.xml` de esta carpeta.

## Uso del Complemento
1. Te aparecerá una nueva pestaña (Finaxis) o un botón en el menú Inicio.
2. Ábrelo e Inicia sesión con tus credenciales de Finaxis.
3. En cualquier celda, escribe: `=FINAXIS.SALDO("110505", "2026-03")`.
4. La celda extraerá el dato en vivo de tu base de datos contable.
