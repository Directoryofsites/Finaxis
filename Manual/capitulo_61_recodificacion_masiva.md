# Recodificación Masiva

La **Recodificación Masiva** es una de las herramientas más potentes de ContaPY, diseñada para corregir errores de asignación a gran escala sin tener que editar documento por documento.

## ¿Qué es la Recodificación?

Imagine que creó por error dos terceros para la misma persona: "Juan Perez" y "Juan A. Perez". Tiene 50 facturas con el primero y 30 con el segundo.
En lugar de entrar a 80 facturas para cambiar el tercero manualmente, la Recodificación le permite decir: *"Mueva TODOS los movimientos de Juan Perez a Juan A. Perez"*.

Esta herramienta funciona para:
1.  **Terceros:** Unificar clientes o proveedores duplicados.
2.  **Productos:** Corregir referencias creadas doblemente o migrar historia de un producto antiguo a uno nuevo.
3.  **Cuentas Contables:** Mover movimientos de una cuenta auxiliar a otra (ej: reclasificación de gastos).

## Proceso de Ejecución

1.  **Seleccione la Tabla:** Elija si va a recodificar Terceros, Productos o Cuentas.
2.  **Origen (Lo Incorrecto):** Busque el registro que tiene los movimientos que desea mover.
3.  **Destino (Lo Correcto):** Busque el registro que recibirá toda la historia.
    *   *Nota:* El destino debe existir previamente. Si no existe, créelo en el maestro correspondiente.
4.  **Filtros (Opcional):**
    *   **Rango de Fechas:** Puede limitar el cambio a un periodo específico (ej: "Solo corregir lo de Enero").
    *   **Tipo de Documento:** Puede aplicar el cambio solo a Facturas de Venta, ignorando Recibos, por ejemplo.
    *   **Números Específicos:** Puede ingresar una lista de números de documento (separados por coma) para una corrección quirúrgica.

## Advertencias Críticas

> [!WARNING]
> **Operación Irreversible**
> La recodificación modifica directamente las referencias en la base de datos. No existe un botón de "Deshacer". Si se equivoca (ej: mueve todo al tercero incorrecto), la única forma de arreglarlo es realizar una nueva recodificación inversa, lo cual puede ser complejo si mezcló datos de dos terceros reales.
>
> **Se recomienda hacer una Copia de Seguridad antes de realizar recodificaciones masivas.**

## Efectos en el Sistema

*   **Saldos:** El saldo del tercero/cuenta Origen quedará en cero (o disminuirá). El saldo del Destino aumentará.
*   **Reportes:** Todos los reportes históricos (incluso de años anteriores si no filtra por fecha) reflejarán el cambio como si siempre hubiera sido así.
*   **Integridad:** El sistema valida que no se rompa la integridad referencial. Por ejemplo, no le permitirá recodificar una cuenta de detalle a una cuenta mayor.
