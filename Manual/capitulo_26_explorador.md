# Explorador de Movimientos

El **Explorador de Movimientos** es la herramienta central para la consulta histórica, auditoría y reimpresión de documentos contables. Permite buscar comprobantes específicos utilizando múltiples criterios de filtrado.

## 1. Panel de Filtros

Antes de visualizar información, debe utilizar los filtros superiores para delimitar su búsqueda. El sistema no carga datos automáticamente para optimizar el rendimiento.

| Campo | Descripción |
| :--- | :--- |
| **Desde / Hasta** | Rango de fechas para la búsqueda. |
| **Tipo Documento** | Filtra por una fuente específica (ej. Factura de Venta, Egreso). |
| **Tercero** | Muestra documentos asociados a un beneficiario específico (NIT/Nombre). |
| **Número** | Busca un consecutivo exacto (ej. `1025`). |

### Botones de Acción
- **<span style="color:blue">🔍 Buscar</span>**: Ejecuta la consulta con los filtros aplicados.
- **<span style="color:gray">🧹 Limpiar</span>**: Restablece todos los filtros y limpia la tabla de resultados.

## 2. Resultados y Acciones

La tabla de resultados muestra los documentos ordenados cronológicamente (más recientes primero).

### Columnas
- **Fecha**: Fecha contable del documento.
- **Tipo**: Código y nombre del documento (ej. `FV - Factura de Venta`).
- **Número**: Consecutivo único.
- **Beneficiario**: Tercero asociado a la transacción.
- **Valor Total**: Suma de débitos/créditos del asiento.
- **Estado**:
    - <span style="color:green; border:1px solid green; padding:2px; border-radius:4px;">ACTIVO</span>: Documento válido y contabilizado.
    - <span style="color:red; border:1px solid red; padding:2px; border-radius:4px;">ANULADO</span>: Documento revertido (sin efecto contable).

### Reimpresión de Comprobantes
Para obtener una copia física o digital de un documento:
1. Localice el documento en la tabla.
2. Haga clic en el botón **🖨️ Imprimir** en la columna de acciones.
3. El sistema generará un PDF oficial en una nueva pestaña, listo para descargar o imprimir.

> [!NOTE]
> **Paginación**: Si la búsqueda arroja muchos resultados, utilice los botones **« Anterior** y **Siguiente »** al final de la tabla para navegar entre páginas.
