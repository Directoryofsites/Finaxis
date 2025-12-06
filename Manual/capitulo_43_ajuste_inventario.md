# Capítulo 43: Toma Física y Ajuste de Inventario

El módulo de **Toma Física de Inventario** permite conciliar las existencias registradas en el sistema con lo que realmente hay en la bodega.

## 1. Pasos para Realizar un Ajuste

Para acceder, vaya al menú **Inventario > Ajuste de Inventario**.

### Paso 1: Cargar Inventario

1.  **Fecha del Ajuste:** Seleccione la fecha en la que se aplicará el movimiento contable.
2.  **Bodega:** Seleccione la bodega que va a auditar.
3.  **Filtros (Opcional):** Use "Filtrar por Grupo o Nombre" si desea hacer un conteo parcial (por ejemplo, solo contar "Bebidas").
4.  Haga clic en **"Cargar Inventario"**.
    *   El sistema mostrará una tabla con todos los productos de esa bodega y su **Saldo Sistema** actual.

### Paso 2: Digitar Conteo Físico

En la columna **"Conteo Físico"** (resaltada en amarillo), ingrese la cantidad real que contó en la bodega.
*   El sistema calculará automáticamente la **Diferencia** (Físico - Sistema).
*   Si hay diferencia, se mostrará en rojo (faltante) o verde (sobrante).

### Paso 3: Seleccionar Items a Ajustar

Marque la casilla **"Incluir"** (columna derecha) para los productos que desea ajustar.
*   **Nota:** Solo se procesarán los items seleccionados. Si deja un item sin marcar, el sistema ignorará su diferencia.

### Paso 4: Procesar

1.  Verifique el resumen en la parte inferior ("X items seleccionados para ajuste").
2.  Haga clic en **"Procesar Ajuste"**.
3.  El sistema generará automáticamente los movimientos de entrada o salida necesarios para igualar el stock del sistema al conteo físico.

## 2. Indicadores (KPIs)

En la parte superior verá tres tarjetas informativas:
*   **Valor en Sistema:** Cuánto vale el inventario teórico actual.
*   **Valor Físico:** Cuánto vale el inventario según lo que usted ha digitado.
*   **Diferencia Neta:** La pérdida o ganancia total valorizada que resultará de este ajuste.

## 3. Preguntas Frecuentes

**¿Qué pasa si dejo el conteo vacío?**
El sistema asume que el conteo es igual al saldo del sistema (diferencia cero) a menos que usted escriba explícitamente un número.

**¿Puedo hacer ajustes parciales?**
Sí. Puede filtrar por un grupo específico y ajustar solo esos productos. Los demás productos de la bodega no se verán afectados.

**¿Cómo corrijo un error?**
Una vez procesado, el ajuste crea movimientos definitivos. Si se equivocó, deberá realizar un nuevo ajuste con los valores correctos.
