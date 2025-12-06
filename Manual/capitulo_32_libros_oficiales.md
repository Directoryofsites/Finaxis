# Libros Oficiales

El módulo de **Libros Oficiales** permite la generación y cierre de los libros contables requeridos por la normativa legal. Esta herramienta facilita tanto la revisión previa como la emisión definitiva de los documentos.

## 1. Tipos de Libros Disponibles

El sistema permite generar los tres libros principales:

1.  **📘 Libro Diario**: Registra cronológicamente todas las operaciones del periodo.
2.  **📗 Libro Mayor y Balances**: Resume los movimientos por cuenta mayor, mostrando saldos iniciales, movimientos y saldos finales.
3.  **📙 Libro de Inventarios y Balances**: Detalla los activos, pasivos y patrimonio al corte seleccionado.

## 2. Modos de Operación

Es crítico entender la diferencia entre los dos modos de generación:

### Modo Borrador (Recomendado para Revisión)
- **Icono**: <span style="color:indigo">🖨️</span>
- **Función**: Genera un PDF con marca de agua "BORRADOR".
- **Efecto**: **NO cierra el periodo**. Puede generar este reporte tantas veces como necesite para verificar que la información sea correcta antes del cierre definitivo.

### Modo Oficial (Zona de Peligro)
- **Icono**: <span style="color:red">🔒</span>
- **Función**: Genera el PDF oficial numerado y **CIERRA EL PERIODO CONTABLE**.
- **Efecto**:
    - Bloquea la creación, edición o anulación de documentos en el mes y año seleccionados.
    - Esta acción es **irreversible** desde el panel de usuario.
    - Se recomienda realizar una copia de seguridad antes de ejecutar esta acción.

## 3. Proceso de Generación

1.  Seleccione el **Tipo de Libro**.
2.  Indique el **Año Gravable** y el **Mes de Cierre**.
3.  Elija el **Modo de Operación** (Borrador u Oficial).
4.  Haga clic en el botón de generación.
    - Si eligió **Modo Oficial**, el sistema solicitará una confirmación adicional de seguridad.

## 4. Solución de Problemas

- **Error al generar**: Verifique que existan movimientos en el periodo seleccionado.
- **Periodo ya cerrado**: Si intenta cerrar un periodo previamente cerrado, el sistema le notificará que la operación no es permitida.
