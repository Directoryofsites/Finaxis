# Papelera de Reciclaje

ContaPY implementa un sistema de **Eliminación Lógica (Soft Delete)**. Esto significa que cuando usted "elimina" un documento en cualquier módulo, este no desaparece físicamente de la base de datos, sino que es enviado a una **Papelera de Reciclaje** segura.

## Objetivos de la Papelera

1.  **Seguridad:** Evitar la pérdida accidental de información.
2.  **Auditoría:** Mantener un rastro de quién eliminó qué y cuándo.
3.  **Recuperación:** Permitir restaurar el trabajo realizado sin tener que digitar todo nuevamente.

## Acceso y Permisos

El módulo de Papelera de Reciclaje es una zona restringida. Generalmente, solo los usuarios con rol de **Administrador** o **Auditor** tienen acceso a ella. Un usuario operativo estándar puede eliminar documentos (si tiene permiso), pero no puede ver ni restaurar desde la papelera.

## Restauración de Documentos

Para recuperar un documento:
1.  Ingrese al módulo de Papelera.
2.  Use los filtros para buscar por Tipo, Número, Fecha de Eliminación o Usuario que eliminó.
3.  Seleccione el documento y haga clic en **Restaurar**.

### Validaciones de Restauración

El sistema aplicará dos validaciones críticas antes de permitir la restauración:

1.  **Periodo Contable:** Verifica la fecha original del documento. Si pertenece a un mes que ya fue **CERRADO**, el sistema bloqueará la restauración. Deberá reabrir el periodo primero.
2.  **Conflicto de Numeración:** Verifica si el número del documento ya fue reutilizado.
    *   *Ejemplo:* Eliminó la Factura #50. Luego creó una nueva Factura #50.
    *   Si intenta restaurar la #50 original, el sistema lo impedirá porque no pueden existir dos facturas activas con el mismo número. Deberá anular o cambiar la #50 nueva antes de restaurar la vieja.

## Auditoría de Eliminación

En la vista de la papelera, usted encontrará columnas clave para la auditoría forense:
*   **Usuario Eliminación:** El correo del usuario que ejecutó la acción.
*   **Fecha Eliminación:** La marca de tiempo exacta.
*   **Valor Original:** El valor total del documento al momento de ser borrado.

> **Nota Técnica:** Los documentos en la papelera **NO** suman en los reportes contables ni afectan el inventario. Están en un estado de "limbo" hasta que sean restaurados o purgados definitivamente (función de purga solo por base de datos).
