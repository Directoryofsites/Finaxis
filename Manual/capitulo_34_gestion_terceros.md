# Gestión de Terceros: El Corazón de su Base de Datos

El módulo de **Gestión de Terceros** es el directorio maestro de su aplicación. Aquí se centraliza la información de todas las personas naturales o jurídicas con las que su empresa tiene relación: Clientes, Proveedores, Empleados y otros.

## 1. Creación y Edición de Terceros

Al crear o editar un tercero, encontrará un formulario detallado dividido en tres secciones críticas. La precisión aquí es vital para la facturación electrónica y los reportes contables.

### Sección 1: Identificación
-   **NIT / Cédula**: El identificador único. No se puede modificar una vez creado.
-   **DV (Dígito de Verificación)**: Calculado automáticamente o ingresado manualmente según el documento.
-   **Razón Social**: Nombre legal de la empresa o nombre completo de la persona.
-   **Nombre Comercial**: (Opcional) Como es conocido el negocio en el mercado (ej. "Panadería La 22" vs "Juan Pérez S.A.S.").

### Sección 2: Ubicación y Contacto
Datos esenciales para la facturación y notificaciones. Asegúrese de que el **Correo Electrónico** sea el destinado para la recepción de facturas electrónicas.

### Sección 3: Detalles Fiscales y Comerciales (¡MUY IMPORTANTE!)
Esta sección define cómo el sistema interactúa con este tercero.

-   **Responsabilidad Fiscal**: Código de responsabilidad (ej. R-99-PN). Consulte el RUT del tercero.
-   **Actividad Económica (CIIU)**: Código de la actividad principal.
-   **Régimen Simple**: Marque esta casilla si el tercero pertenece al Régimen Simple de Tributación.
-   **Lista de Precios**: Si maneja múltiples tarifas (ej. Mayorista, Detal), asigne la lista correspondiente aquí. El sistema cargará automáticamente estos precios al facturarle.

#### La Casilla "Cliente" y el Módulo de Cartera
> [!IMPORTANT]
> **¿Por qué es vital marcar la casilla "Cliente"?**
> Al marcar esta casilla, el sistema habilita inmediatamente el **Módulo de Cartera** para este tercero. Esto le permitirá:
> 1.  Generarle Facturas de Venta.
> 2.  Asignarle cupos de crédito.
> 3.  Hacer seguimiento a sus cuentas por cobrar.
> 4.  Ver su historial de pagos y morosidad.
>
> Si no marca esta casilla, el tercero existirá en la base de datos pero no aparecerá en los selectores de venta.

#### Proveedores y Empleados
-   **Proveedor**: Habilita el módulo de Cuentas por Pagar y Compras.
-   **Empleado**: Permite asignarlo a nómina y gastos de personal.
*Nota: Un mismo tercero puede ser Cliente, Proveedor y Empleado simultáneamente.*

## 2. Herramienta de Fusión (Fusionar Terceros)

¿Creó por error a "Juan Perez" y "Juan A. Perez" como dos registros diferentes? La herramienta **Fusionar** es la solución.

1.  Haga clic en el botón **"Fusionar"** en la pantalla principal.
2.  Seleccione el **Tercero Principal** (el que quedará).
3.  Seleccione el **Tercero Duplicado** (el que desaparecerá).
4.  El sistema moverá **todos** los movimientos (facturas, recibos, asientos) del duplicado al principal y luego eliminará el duplicado.

> [!WARNING]
> **Acción Irreversible**: Una vez fusionados, no se pueden separar. Verifique bien los NITs antes de confirmar.

## Preguntas Frecuentes (FAQ)

**P: ¿Puedo cambiar el NIT de un tercero?**
R: No directamente. El NIT es la llave maestra. Si se equivocó, debe crear uno nuevo y, si ya tiene movimientos, usar la herramienta "Fusionar" para mover todo al nuevo NIT correcto.

**P: ¿Por qué no me aparece un tercero al intentar hacer una factura?**
R: Seguramente no tiene marcada la casilla **"Cliente"** en su ficha. Edítelo y márquela.

**P: ¿Qué pasa si elimino un tercero?**
R: El sistema solo le permitirá eliminar terceros que **NO tengan movimientos contables**. Si ya tiene facturas o asientos, debe inactivarlo o fusionarlo, pero no podrá borrarlo para preservar la integridad contable.
