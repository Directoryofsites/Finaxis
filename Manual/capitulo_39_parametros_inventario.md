# Configuración de Parámetros de Inventario

Este módulo es el "cerebro" de su sistema de inventarios. Aquí se definen las reglas de juego: dónde se guarda la mercancía, cómo se agrupa, qué impuestos aplican y cómo se calculan los precios.

> **Advertencia**: Una mala parametrización aquí puede causar errores contables. Se recomienda que esta sección sea gestionada por el Contador o el Administrador del sistema.

## 1. Gestión de Bodegas
Las bodegas representan las ubicaciones físicas o lógicas donde se almacena el inventario.
-   **Crear Bodega**: Simplemente ingrese el nombre (ej. "Bodega Principal", "Tienda Norte") y haga clic en **Crear**.
-   **Uso**: Al crear productos o realizar compras, el sistema le preguntará a qué bodega ingresa la mercancía.

## 2. Grupos de Inventario (Categorías)
Esta es la sección más crítica. Los grupos no solo organizan sus productos, sino que definen su comportamiento contable y sus características.

### A. Creación de Grupos y Contabilidad
Al crear un grupo (ej. "Electrodomésticos"), debe asociar las cuentas contables automáticas:
-   **Cta. Inventario (Activo)**: Donde se registra el valor de la mercancía al comprar.
-   **Cta. Ingresos (Ventas)**: Donde se registra la venta.
-   **Cta. Costo de Venta**: Donde se registra el costo al vender.
-   **Cta. Ajustes (Faltante/Sobrante)**: Para cuadres de inventario físico.

### B. Características (Atributos)
Una vez creado el grupo, use el botón de **Etiqueta (Tags)** para definir qué datos se pedirán al crear productos de este grupo.
*Ejemplo para el grupo "Ropa":*
1.  Haga clic en el icono de etiqueta del grupo "Ropa".
2.  Agregue la característica "Talla".
3.  Agregue la característica "Color".
4.  Agregue la característica "Material".
*Resultado*: Cuando cree una camisa en el grupo "Ropa", el sistema le exigirá Talla, Color y Material.

### C. Reglas de Precio
Use el botón de **Porcentaje (%)** para automatizar precios.
-   Puede definir que para la "Lista Mayorista", los productos de este grupo tengan un incremento del 20% sobre el costo.
-   Esto permite que al cambiar el costo de un producto, sus precios de venta se actualicen automáticamente si así lo desea.

## 3. Tasas de Impuesto
Defina los impuestos que aplican a sus productos (IVA, Impoconsumo, Exento).
-   **Tasa**: Ingrese el valor en decimal (ej. `0.19` para el 19%).
-   **Contabilidad**: Asocie las cuentas de IVA Generado (Ventas) e IVA Descontable (Compras) para que el sistema cause los impuestos automáticamente.

## 4. Listas de Precios
Cree tantas listas como necesite para segmentar a sus clientes (ej. "Público General", "Distribuidores", "Empleados").
-   Estas listas se usan luego en el módulo de Clientes para asignar una tarifa por defecto a cada tercero.

---

## Preguntas Frecuentes (FAQ)

**1. ¿Puedo borrar un grupo de inventario?**
Solo si no tiene productos asociados. Si ya creó productos bajo ese grupo, el sistema bloqueará la eliminación para proteger la integridad de los datos.

**2. ¿Qué pasa si me equivoco en una cuenta contable?**
Puede editar el grupo y corregir la cuenta. Los movimientos futuros usarán la nueva cuenta, pero los movimientos pasados **NO** se corregirán automáticamente (requerirá una nota contable manual).

**3. ¿Para qué sirve la casilla "U. Medida" en las características?**
Si marca una característica como "Unidad de Medida", el sistema la tratará de forma especial para reportes y conversiones futuras (ej. Litros, Kilos, Metros).

**4. ¿Puedo tener una bodega para mercancía averiada?**
Sí. Cree una bodega llamada "Averías" o "Cuarentena". Esto le permite separar el stock vendible del no vendible sin sacarlo de sus activos hasta que se decida su disposición final.

**5. ¿El sistema maneja impuestos compuestos?**
Actualmente se maneja un impuesto principal por producto. Para casos complejos, consulte con soporte técnico.
