# Manual de Usuario - Capítulo 52: Balance General por Centro de Costo

## 1. Introducción
El **Balance General por Centro de Costo** es un estado financiero especializado que le permite visualizar la situación patrimonial (Activos, Pasivos y Patrimonio) de una unidad de negocio específica.

Aunque contablemente el Balance General suele ser uno solo para toda la empresa, este reporte es vital para la **Contabilidad Administrativa**, ya que le permite tratar a cada sucursal, proyecto o departamento como si fuera una "mini-empresa" independiente, evaluando sus propios recursos y obligaciones.

---

## 2. Criterios de Búsqueda (Filtros)

Para generar el reporte, configure los siguientes campos:

*   **Centro de Costo:**
    *   Seleccione un centro específico para ver solo las cifras de esa área.
    *   Seleccione `-- Todos (Consolidado) --` para ver el Balance General total de la compañía.
*   **Fecha de Corte:** El balance es una "foto" en un momento del tiempo. Seleccione la fecha hasta la cual desea calcular los saldos acumulados (ej: 31 de Diciembre).

Haga clic en **Generar** para procesar la información.

---

## 3. Interpretación de Resultados

El reporte se divide en tres grandes secciones, siguiendo la ecuación contable fundamental:

### 3.1. Activos (Lo que se tiene)
Muestra los bienes y derechos asignados al centro de costo.
*   *Ejemplo:* Muebles y enseres de la Sucursal Norte, Caja Menor del Proyecto X.

### 3.2. Pasivos (Lo que se debe)
Muestra las obligaciones financieras imputadas al centro de costo.
*   *Ejemplo:* Cuentas por pagar a proveedores de materiales para la obra.

### 3.3. Patrimonio (Lo que realmente pertenece)
Muestra el capital y resultados.
*   **Utilidad del Ejercicio:** El sistema calcula automáticamente la ganancia o pérdida neta del centro de costo a la fecha de corte y la incluye en esta sección para cuadrar el balance.

### 3.4. Verificación de Cuadre (Ecuación Patrimonial)
Al final del reporte encontrará un panel de verificación:
*   **Activo = Pasivo + Patrimonio**
*   Si el balance está cuadrado, verá un mensaje en **Verde** con un check ✅.
*   Si existe algún descuadre, aparecerá una alerta en **Rojo** ⚠️. Esto puede ocurrir si se han realizado movimientos manuales que rompen la partida doble por centro de costo.

---

## 4. Exportación

*   **Botón PDF:** Genera un archivo PDF oficial, listo para imprimir y firmar. Incluye el encabezado de la empresa, la fecha de corte y la firma del sistema.
