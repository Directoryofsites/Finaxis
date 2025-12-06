# Control y Cierre

El módulo de **Control y Cierre** es el panel de mando para el Contador y el Auditor. Aquí se gestionan los procesos que garantizan la inmutabilidad de la información financiera y la calidad de los datos.

## 1. Cierre de Periodos

El cierre contable es el mecanismo para "congelar" la información. Una vez se han presentado impuestos o informes a gerencia, es vital asegurar que nadie modifique las cifras.

### Proceso de Cierre
*   El cierre es **Mensual**.
*   Debe realizarse de forma **Secuencial**: No puede cerrar Marzo si no ha cerrado Febrero.
*   El sistema valida la **Fecha de Inicio de Operaciones**: No puede cerrar periodos anteriores al nacimiento de la empresa.

### Efectos del Cierre
Cuando un mes está cerrado (ej: Enero 2024):
*   Nadie puede **Crear** documentos con fecha de Enero.
*   Nadie puede **Editar** documentos de Enero.
*   Nadie puede **Anular** ni **Eliminar** documentos de Enero.
*   Nadie puede **Restaurar** documentos de Enero desde la papelera.

### Reapertura
Si es estrictamente necesario hacer una corrección, un Administrador puede **Reabrir** el periodo.
*   La reapertura también es secuencial inversa (del último hacia atrás).
*   Al reabrir, el periodo queda expuesto nuevamente a modificaciones. Se recomienda cerrar inmediatamente después de realizar el ajuste.

## 2. Auditoría de Consecutivos

Este reporte es una herramienta de control fiscal indispensable. Su función es escanear la numeración de todos los documentos y detectar **saltos o huecos**.

*   **¿Por qué es importante?** La DIAN y normas de control interno exigen que la facturación sea consecutiva. Un salto (ej: Factura 1, 2, 4... falta la 3) es una alerta grave de posible evasión o pérdida de información.

### Análisis del Reporte
El sistema le mostrará:
*   **Total Documentos Encontrados.**
*   **Último Consecutivo Registrado.**
*   **Huecos Detectados:** Una lista detallada de los números faltantes (ej: "Faltan del 105 al 109").

## 3. Log de Operaciones

Es la "caja negra" del sistema. Registra eventos transversales de seguridad.

*   **Filtros:** Puede buscar por rango de fechas, usuario o tipo de evento.
*   **Eventos Registrados:**
    *   Inicios de Sesión (Login).
    *   Creación de Terceros/Usuarios.
    *   Anulación de Documentos (incluyendo la razón obligatoria digitada).
    *   Eliminación de registros.
    *   Cambios de configuración sensible.

Use este módulo periódicamente para monitorear la actividad inusual o verificar el cumplimiento de los procedimientos internos por parte de los usuarios.
