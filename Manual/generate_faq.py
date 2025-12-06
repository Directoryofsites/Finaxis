import os
import re
import base64

# Configuration
MANUAL_DIR = r"c:\ContaPY2\Manual"
OUTPUT_FILE = os.path.join(MANUAL_DIR, "manual_preguntas_frecuentes.html")

# Thematic Groups (Same as original)
GROUPS = {
    "Configuración y Maestros": [
        "capitulo_5_empresas.md",
        "capitulo_1_puc.md", "capitulo_2_tipos_documento.md", "capitulo_3_plantillas.md",
        "capitulo_4_conceptos.md", "capitulo_34_gestion_terceros.md", "capitulo_50_centros_de_costo.md"
    ],
    "Operación Diaria": [
        "capitulo_24_nuevo_documento.md", "capitulo_25_captura_rapida.md",
        "capitulo_26_explorador.md", "capitulo_40_compras.md", "capitulo_41_facturacion.md"
    ],
    "Reportes Contables": [
        "capitulo_27_libro_diario.md", "capitulo_28_balance_general.md", "capitulo_29_estado_resultados.md",
        "capitulo_30_balance_prueba.md", "capitulo_31_auxiliar_cuenta.md", "capitulo_32_libros_oficiales.md",
        "capitulo_33_super_informe.md", "capitulo_51_auxiliar_cc_cuenta.md", "capitulo_52_balance_general_cc.md",
        "capitulo_53_estado_resultados_cc_detallado.md", "capitulo_54_balance_prueba_cc.md", "capitulo_55_analisis_financiero.md"
    ],
    "Terceros y Cartera": [
        "capitulo_35_tercero_cuenta.md", "capitulo_36_estado_cuenta_cliente.md", "capitulo_37_auxiliar_cartera.md",
        "virtual_estado_cuenta_proveedor.md", "virtual_auxiliar_proveedor.md"
    ],
    "Inventario y Logística": [
        "capitulo_38_gestion_inventario.md", "capitulo_39_parametros_inventario.md",
        "capitulo_42_traslados.md", "capitulo_43_ajuste_inventario.md",
        "capitulo_44_rentabilidad_producto.md", "capitulo_45_movimiento_analitico.md", "capitulo_46_kardex_detallado.md",
        "capitulo_47_super_informe_inventarios.md", "capitulo_48_gestion_topes.md", "capitulo_49_gestion_ventas.md"
    ],
    "Utilidades": [
        "capitulo_60_edicion_documentos.md",
        "capitulo_61_recodificacion_masiva.md",
        "capitulo_62_papelera_reciclaje.md",
        "capitulo_63_control_cierre.md"
    ]
}

# FAQ Content Dictionary
FAQ_DATA = {
    # --- Configuración y Maestros ---
    "capitulo_5_empresas.md": [
        ("¿Cómo cambio el logo de mi empresa?", "Puede subir un nuevo logo en la pestaña 'Configuración General' dentro de la edición de empresa. Se recomiendan imágenes cuadradas en formato PNG para una mejor visualización en los reportes."),
        ("¿Es posible modificar el NIT de una empresa ya creada?", "No, el NIT es el identificador único e inmutable en el sistema. Si cometió un error al crearlo, debe crear una nueva empresa con el NIT correcto y solicitar a soporte la migración de datos si ya había ingresado información."),
        ("¿Puedo gestionar múltiples empresas con el mismo usuario?", "Sí, ContaPY es multi-empresa. Puede cambiar entre ellas desde el menú superior derecho sin necesidad de cerrar sesión, siempre que su usuario tenga permisos asignados en ambas."),
        ("¿Qué hago si supero el límite de registros mensuales?", "El sistema bloqueará la creación de nuevos documentos. Debe contactar al administrador del sistema para solicitar un 'Cupo Adicional' para el mes en curso o actualizar su plan base."),
        ("¿Cómo elimino una empresa definitivamente?", "La eliminación de una empresa es una operación crítica que borra en cascada: PUC, Terceros, Centros de Costo, Usuarios y Logs. Sin embargo, el sistema PROHÍBE eliminar empresas que tengan documentos contables (activos o anulados) por seguridad. En ese caso, se requiere una intervención técnica especial."),
        ("¿Para qué sirve la 'Fecha de Inicio de Operaciones'?", "Es una fecha de corte de seguridad. El sistema no permitirá crear documentos con fecha anterior a la establecida, protegiendo así la integridad de periodos contables previos o saldos iniciales."),
        ("¿Puedo cambiar el correo electrónico de la empresa?", "Sí, en la sección de edición. Este correo se utiliza para el envío automático de notificaciones y facturas, así que asegúrese de que sea válido y monitoreado."),
        ("¿Qué roles se crean automáticamente con una nueva empresa?", "Al crear una empresa, se asigna automáticamente un rol de 'Administrador' al usuario creador, otorgándole control total sobre la nueva entidad."),
        ("¿El sistema valida el dígito de verificación del NIT?", "Sí, el sistema calcula internamente el dígito de verificación para asegurar que el NIT ingresado sea válido según el algoritmo de la DIAN."),
        ("¿Puedo tener la misma empresa con dos razones sociales diferentes?", "No bajo el mismo NIT. Si la empresa cambió de razón social, simplemente actualice el campo 'Razón Social' en la configuración. El historial se mantendrá bajo el mismo NIT."),
        ("¿Cómo configuro el pie de página de los documentos?", "Aunque no está en la ficha de la empresa, esta información suele tomarse de la configuración de 'Formatos de Impresión' o datos de la empresa (Dirección, Teléfono, Email) que aparecen en el encabezado.")
    ],
    "capitulo_1_puc.md": [
        ("¿Puedo eliminar una cuenta contable?", "Solo puede eliminar cuentas que NO tengan movimientos (ni activos ni anulados) y que NO tengan subcuentas (hijos). Si la cuenta tiene historia, debe inactivarla en su lugar."),
        ("¿Cómo creo una cuenta auxiliar?", "Seleccione la cuenta padre (nivel 4 o 6) y haga clic en 'Crear Subcuenta'. El sistema calculará automáticamente el nivel. Asegúrese de marcarla como 'Auxiliar' para permitir movimientos."),
        ("¿Qué hago si el código de cuenta ya existe?", "Verifique en el filtro de 'Inactivas'. Es posible que la cuenta exista pero esté oculta. Si es así, reactívela en lugar de intentar crearla de nuevo."),
        ("¿Puedo cambiar el código de una cuenta ya creada?", "No, el código es la llave principal de la estructura jerárquica. Si necesita cambiarlo y la cuenta no tiene movimientos, elimínela y créela de nuevo. Si tiene movimientos, deberá realizar un traslado de saldos y luego inactivar la anterior."),
        ("¿Por qué no puedo marcar una cuenta padre como 'Auxiliar'?", "Las cuentas padre (Mayores) son agrupadoras y por definición contable no pueden recibir movimientos directos. Solo las cuentas de último nivel pueden ser auxiliares."),
        ("¿Para qué sirve la opción 'Depuración Jerárquica'?", "Es una herramienta avanzada que analiza todo el PUC y detecta cuentas que no tienen movimientos ni subcuentas útiles, permitiendo eliminarlas masivamente para limpiar su contabilidad."),
        ("¿Cómo sé si una cuenta exige Centro de Costo?", "En la configuración de la cuenta, verifique si tiene marcada la opción 'Requiere Centro de Costo'. Si es así, el sistema no dejará guardar documentos sin este dato."),
        ("¿Puedo crear cuentas de nivel 1, 2 o 3?", "Generalmente el sistema viene con las clases, grupos y cuentas (niveles 1-4) pre-cargados según norma. Se recomienda crear auxiliares a partir del nivel 4 o 6 para mantener la estructura legal."),
        ("¿Qué significa 'Naturaleza' de la cuenta?", "Define si la cuenta aumenta por el Débito o por el Crédito. Esto es vital para los reportes financieros y validaciones de saldo en rojo."),
        ("¿Puedo exportar mi PUC a Excel?", "Sí, en la vista principal del PUC hay un botón de exportación que genera un archivo plano con toda la estructura actual."),
        ("¿El sistema valida que la cuenta padre exista?", "Sí, no puede crear una cuenta 'huerfana'. Debe existir obligatoriamente el nivel superior inmediato.")
    ],
    "capitulo_2_tipos_documento.md": [
        ("¿Cómo reinicio la numeración de un documento?", "En la edición del Tipo de Documento, puede ajustar el 'Consecutivo Actual'. Tenga EXTREMO CUIDADO: si baja el número y ya existen documentos posteriores, el sistema bloqueará la creación por duplicidad."),
        ("¿Puedo tener prefijos en mis facturas?", "Sí, configure el campo 'Prefijo' (ej: FAC, FE, NC) en la configuración. Este prefijo aparecerá en todos los reportes e impresiones."),
        ("¿Qué significa 'Afecta Inventario'?", "Si marca esta opción, los documentos de este tipo moverán cantidades en el Kardex (ej: Facturas Venta, Compras). Si no la marca, solo moverán valores contables (ej: Notas Contables)."),
        ("¿Puedo eliminar un Tipo de Documento?", "No si ya ha sido usado en algún documento (activo o anulado) o si está asociado a una Plantilla Contable. Inactívelo si ya no lo va a usar."),
        ("¿Para qué sirven las cuentas 'Débito/Crédito Sugeridas'?", "Son las cuentas por defecto para Cartera (CXC) o Proveedores (CXP). El sistema las usa para automatizar los asientos de causación y pago."),
        ("¿Cómo configuro un documento para Facturación Electrónica?", "Debe asociarlo a la resolución de facturación correspondiente en el módulo de integración (si está activo) y asegurarse de que el tipo sea 'Factura de Venta'."),
        ("¿Puedo tener dos tipos de documento con el mismo prefijo?", "Sí, pero no es recomendable para evitar confusiones. Lo ideal es que cada tipo sea identificable por su código o prefijo único."),
        ("¿Qué es la 'Función Especial'?", "Es una etiqueta interna (ej: 'PAGO_PROVEEDOR', 'RC_CLIENTE') que activa lógicas automáticas, como el recálculo de saldos de cartera o la interfaz de cruce de facturas."),
        ("¿Puedo cambiar la 'Función Especial' de un documento ya usado?", "No se recomienda. Cambiar la lógica de negocio de documentos históricos puede causar inconsistencias graves en los reportes de cartera e inventario."),
        ("¿El sistema permite numeración manual?", "Sí, existe un check 'Numeración Manual'. Útil para documentos como Facturas de Compra donde el número lo da el proveedor, no el sistema.")
    ],
    "capitulo_3_plantillas.md": [
        ("¿Para qué sirven las plantillas?", "Permiten predefinir asientos contables repetitivos (ej: Nómina, Arriendos, Causaciones recurrentes) para agilizar la digitación y evitar errores de imputación."),
        ("¿Puedo editar una plantilla existente?", "Sí, puede agregar o quitar cuentas, modificar porcentajes o valores fijos en cualquier momento. Los cambios aplicarán a los documentos futuros, no a los pasados."),
        ("¿Cómo creo una plantilla desde un documento existente?", "Esta es la forma más rápida: abra un documento que ya digitó, y busque la opción 'Guardar como Plantilla'. El sistema copiará todas las cuentas y conceptos."),
        ("¿Las plantillas guardan los valores o solo las cuentas?", "Pueden guardar ambos. Si deja los valores en cero, la plantilla solo traerá la estructura de cuentas. Si pone valores, traerá las cifras sugeridas."),
        ("¿El sistema valida que la plantilla esté cuadrada?", "Sí, al igual que un documento, no puede guardar una plantilla si la suma de débitos y créditos no es igual."),
        ("¿Puedo asignar una plantilla a un tercero específico?", "Sí, puede sugerir un tercero. Al usar la plantilla, el sistema cargará automáticamente ese tercero en el encabezado."),
        ("¿Puedo usar porcentajes en las plantillas?", "Sí, puede configurar renglones que se calculen como porcentaje de una base, útil para impuestos o retenciones."),
        ("¿Cómo elimino una plantilla?", "Puede eliminarla desde el listado de plantillas. Esto no afecta los documentos que se crearon usando esa plantilla en el pasado."),
        ("¿Puedo tener plantillas privadas?", "Por defecto las plantillas son visibles para la empresa. No existe actualmente un sistema de plantillas privadas por usuario."),
        ("¿Qué pasa si una cuenta de la plantilla se inactiva?", "Al intentar usar la plantilla, el sistema le mostrará un error indicando que la cuenta no es válida y deberá actualizar la plantilla.")
    ],
    "capitulo_4_conceptos.md": [
        ("¿Cómo configuro el IVA automático?", "Cree un concepto de tipo 'Impuesto', asigne el porcentaje (ej: 19%) y la cuenta contable (2408...). Al usarlo en un documento, el sistema calculará el valor base automáticamente."),
        ("¿Los conceptos son obligatorios?", "No estrictamente, pero son altamente recomendados. Simplifican la captura al evitar que el usuario tenga que memorizar códigos contables complejos."),
        ("¿Puedo tener conceptos favoritos?", "Sí, cada usuario puede marcar conceptos como 'Favoritos' para que aparezcan al principio de las listas de selección, acelerando su trabajo diario."),
        ("¿Qué es un concepto de tipo 'Descuento'?", "Es un concepto que resta del valor total. Se usa para descuentos comerciales o financieros y se contabiliza en la cuenta asignada (generalmente un gasto o menor valor del ingreso)."),
        ("¿Puedo editar la cuenta de un concepto?", "Sí. Tenga en cuenta que esto solo afectará los documentos nuevos. Los documentos anteriores conservan la cuenta con la que fueron guardados."),
        ("¿Cómo manejo las Retenciones en la Fuente?", "Cree conceptos de tipo 'Retención', asigne la tasa y la cuenta pasiva (2365...). El sistema las calculará automáticamente sobre la base."),
        ("¿Puedo usar el mismo concepto para compras y ventas?", "Depende de la cuenta contable. Generalmente el IVA en ventas (Generado) y en compras (Descontable) usan cuentas diferentes, por lo que debería tener dos conceptos distintos."),
        ("¿El nombre del concepto sale en la impresión?", "Sí, generalmente el 'Concepto' o 'Detalle' del movimiento en la impresión toma el nombre que usted defina aquí, o la descripción manual que escriba al digitar."),
        ("¿Hay límite de conceptos?", "No, puede crear tantos como necesite para cubrir todas sus operaciones comerciales.")
    ],
    "capitulo_34_gestion_terceros.md": [
        ("¿Cómo importo terceros masivamente?", "Utilice la opción 'Importar desde Excel'. Descargue primero la plantilla de ejemplo, llénela respetando las columnas y súbala. El sistema validará NITs duplicados."),
        ("¿Un tercero puede ser cliente y proveedor a la vez?", "Sí, absolutamente. Solo asegúrese de marcar ambas casillas en su perfil o simplemente úselo en documentos de venta y compra según necesite."),
        ("¿Qué es la función 'Fusionar Terceros'?", "Es una herramienta poderosa para corregir duplicados (ej: creó 'Juan Perez' y 'Juan A. Perez'). Permite unificar toda la historia (facturas, recibos) en uno solo y eliminar el duplicado."),
        ("¿Puedo eliminar un tercero?", "El sistema es muy estricto: NO puede eliminar un tercero si tiene documentos (activos, anulados o en papelera) o si está asociado a plantillas. Si tiene historia, debe inactivarlo."),
        ("¿Cómo asigno una lista de precios a un cliente?", "En la edición del tercero, campo 'Lista de Precios'. Al facturarle, el sistema traerá automáticamente los precios de esa lista."),
        ("¿El sistema valida el dígito de verificación?", "Sí, para NITs, el sistema calcula y valida el dígito de verificación automáticamente."),
        ("¿Puedo buscar por nombre comercial?", "Sí, el buscador inteligente localiza por Razón Social, Nombre Comercial o NIT/Cédula."),
        ("¿Qué hago si el tercero cambió de dirección?", "Actualice el campo dirección en su ficha. Los documentos nuevos saldrán con la nueva dirección; los históricos conservan la integridad del momento en que se hicieron (si se reimprimen, podrían mostrar la nueva dependiendo del formato)."),
        ("¿Es obligatorio el correo electrónico?", "No, pero es vital para la facturación electrónica y el envío automático de notificaciones de cobro."),
        ("¿Cómo diferencio personas naturales de jurídicas?", "Mediante el 'Tipo de Identificación' (NIT vs Cédula) y los campos de nombres (Nombre/Apellido vs Razón Social).")
    ],
    "capitulo_50_centros_de_costo.md": [
        ("¿Es obligatorio usar centros de costo?", "Depende de la configuración de cada CUENTA CONTABLE. Si la cuenta (ej: 5105 Gasto Personal) está marcada como 'Requiere Centro de Costo', el sistema NO dejará guardar sin este dato."),
        ("¿Cómo veo la rentabilidad por centro de costo?", "Utilice el reporte 'Estado de Resultados por Centro de Costo' o el 'Estado de Resultados Detallado' para ver la utilidad neta de cada unidad de negocio."),
        ("¿Puedo crear una jerarquía de centros de costo?", "Sí, puede crear centros 'Padre' y 'Hijos'. Recuerde: Un centro de costo Padre NO puede recibir movimientos directos, solo sus hijos (similar al PUC)."),
        ("¿Cómo elimino un centro de costo?", "Solo puede eliminarlo si: 1) No tiene hijos, 2) No tiene movimientos contables, 3) No está asociado a encabezados de documentos, 4) No está en plantillas. De lo contrario, debe inactivarlo."),
        ("¿Puedo mover un centro de costo de un padre a otro?", "Sí, editando el campo 'Centro de Costo Padre'. Tenga cuidado de que esto tenga sentido para sus reportes históricos."),
        ("¿El centro de costo aplica al balance general?", "Sí, ContaPY permite imputar centros de costo a cuentas de balance (Activo/Pasivo) si así lo configura, permitiendo sacar un Balance General por unidad de negocio."),
        ("¿Puedo tener centros de costo 'Administrativos' y 'Operativos'?", "Sí, esa es la estructura recomendada. Cree dos grandes padres y desglose debajo de ellos."),
        ("¿Puedo numerar las páginas?", "Sí, puede indicar el número de página inicial al momento de imprimir.")
    ],
    "capitulo_33_super_informe.md": [
        ("¿Qué es el Super Informe?", "Es una herramienta de inteligencia de negocios (BI) que le permite crear reportes dinámicos arrastrando y soltando campos."),
        ("¿Puedo guardar mis reportes personalizados?", "Sí, use el botón 'Guardar Vista' para acceder a su configuración posteriormente.")
    ],
    "capitulo_51_auxiliar_cc_cuenta.md": [
        ("¿Cómo veo los gastos de un proyecto específico?", "Filtre por el Centro de Costo asociado a ese proyecto."),
        ("¿Puedo ver múltiples centros de costo a la vez?", "Sí, el filtro permite selección múltiple.")
    ],
    "capitulo_52_balance_general_cc.md": [
        ("¿El patrimonio se divide por centro de costo?", "Generalmente no, a menos que haya realizado asientos manuales imputando centros de costo a cuentas de patrimonio."),
        ("¿Cómo sé qué porcentaje representa cada área?", "Exporte a Excel para realizar análisis verticales por centro de costo.")
    ],
    "capitulo_53_estado_resultados_cc_detallado.md": [
        ("¿Puedo ver el detalle mes a mes?", "Sí, cambie la vista a 'Mensual' para ver la evolución de cada centro de costo en el tiempo."),
        ("¿Cómo identifico centros de costo no rentables?", "Busque columnas con Utilidad Neta negativa o márgenes inferiores al promedio.")
    ],
    "capitulo_54_balance_prueba_cc.md": [
        ("¿Para qué sirve este reporte?", "Para verificar que los débitos y créditos estén cuadrados dentro de cada centro de costo, asegurando la integridad de la contabilidad analítica.")
    ],
    "capitulo_55_analisis_financiero.md": [
        ("¿Qué hago si mi liquidez está en rojo?", "Revise sus cuentas por cobrar y plazos de pago a proveedores. El sistema sugiere mejorar la rotación de cartera."),
    ],
    # --- Terceros y Cartera ---
    # --- Terceros y Cartera ---
    "capitulo_35_tercero_cuenta.md": [
        ("¿Cómo se cruzan los pagos con las facturas?", "El sistema utiliza un método automático basado en antigüedad (FIFO) o asignación manual si se especifica en el recibo de caja. El reporte 'Auxiliar de Cartera' le muestra exactamente cómo se aplicó cada pago."),
        ("¿Qué pasa si un cliente paga más de lo que debe?", "El excedente queda como un saldo a favor (anticipo) en la cuenta de cartera. Verá un saldo negativo en el 'Estado de Cuenta', indicando que la empresa le debe ese valor al cliente (o que debe cruzarse con futuras facturas)."),
        ("¿Cómo corrijo un recibo mal aplicado?", "Debe anular el Recibo de Caja y volverlo a crear. Al hacerlo, el sistema libera el saldo de las facturas que habían sido 'pagadas' por ese recibo incorrecto."),
        ("¿El sistema calcula intereses de mora?", "No automáticamente en la contabilidad. Sin embargo, el reporte de 'Estado de Cuenta' le muestra los días de mora para que usted pueda calcular y cobrar los intereses manualmente si es su política."),
        ("¿Por qué una factura aparece pagada si no he hecho recibo?", "Revise si hubo una Nota Crédito aplicada a esa factura. Las devoluciones también disminuyen el saldo de la cartera."),
        ("¿Puedo ver la cartera por vendedor?", "Sí, si asignó un vendedor a cada factura. En el 'Super Informe' puede filtrar por vendedor para ver qué facturas generó, aunque el control de saldo neto es por cliente."),
        ("¿Qué es el 'Recálculo de Saldos'?", "Es un proceso interno que corre el sistema para asegurar que la suma de débitos y créditos coincida con el saldo pendiente de cada factura. Útil si detecta inconsistencias tras editar documentos antiguos.")
    ],

    "capitulo_36_estado_cuenta_cliente.md": [
        ("¿Qué indica la columna 'Días Mora'?", "Muestra cuántos días han pasado desde la fecha de vencimiento de la factura hasta hoy. Si es negativo o dice 'Vence en...', la factura aún está vigente."),
        ("¿Cómo interpreto el bloque de colores (Aging)?", "Es un resumen visual de la cartera: Verde (Al día), Amarillo (1-30 días vencido), Naranja (31-60), Rojo (61-90) y Vinotinto (>90). Ideal para priorizar la gestión de cobro."),
        ("¿Puedo enviar este reporte al cliente?", "Sí, use el botón 'Exportar PDF'. Genera un extracto formal con el logo de su empresa, perfecto para enviarlo por correo electrónico como cobro persuasivo."),
        ("¿Por qué el saldo total no coincide con la suma de las facturas?", "Verifique si hay 'Anticipos' o notas crédito sin cruzar que estén restando al saldo total pero no se han aplicado a una factura específica."),
        ("¿Incluye las facturas anuladas?", "No, el Estado de Cuenta solo muestra documentos con saldo pendiente real. Las anuladas se consideran inexistentes para efectos de deuda."),
        ("¿Puedo sacar el estado de cuenta a una fecha pasada?", "Sí, cambie la 'Fecha de Corte'. El sistema reconstruirá la deuda tal como estaba ese día (ignorando pagos posteriores a esa fecha)."),
        ("¿Qué hago si un cliente dice que ya pagó?", "Genere el reporte y compárelo con los soportes del cliente. Si falta el pago, debe ingresarlo en 'Recibo de Caja'."),
        ("¿Cómo veo solo lo vencido?", "Exporte a Excel (CSV) y filtre la columna 'Estado' o 'Días Mora' para depurar la lista.")
    ],
    "capitulo_37_auxiliar_cartera.md": [
        ("¿Cuál es la diferencia con el Estado de Cuenta?", "El Estado de Cuenta es una 'foto' del saldo actual. El Auxiliar es la 'película' completa: muestra la historia de cada factura y con qué recibos específicos se fue pagando."),
        ("¿Para qué sirve la vista 'Por Facturas'?", "Para auditar una factura específica: ver cuándo se creó, su valor original, y una lista detallada de todos los abonos que ha recibido hasta quedar en cero (o su saldo actual)."),
        ("¿Para qué sirve la vista 'Por Recibos'?", "Para auditar un pago: ver por qué valor entró el dinero y a qué facturas mató o abonó. Útil cuando un cliente paga $10.000.000 y quiere saber cómo se distribuyó ese dinero."),
        ("¿Por qué un recibo aparece en múltiples facturas?", "Porque un solo pago puede cubrir varias deudas. El sistema distribuye el valor del recibo para cubrir las facturas más antiguas primero (o según se haya indicado)."),
        ("¿Puedo ver los anticipos aquí?", "Sí. Si un recibo no tiene facturas cruzadas (o sobra dinero), aparecerá con el saldo a favor disponible."),
        ("¿Cómo detecto pagos duplicados?", "Revise la vista 'Por Recibos'. Si ve dos recibos con la misma fecha y valor, o aplicados a las mismas facturas, es una señal de alerta."),
        ("¿Este reporte sirve para conciliación bancaria?", "Ayuda, pero para bancos use el Libro Auxiliar de Bancos. Este reporte es específico para la relación Deuda-Pago con el tercero.")
    ],
    "virtual_estado_cuenta_proveedor.md": [
        ("¿Es igual al de Clientes?", "La lógica es idéntica, pero enfocado en 'Cuentas por Pagar'. Le muestra cuánto debe su empresa a los proveedores."),
        ("¿Me avisa qué facturas debo pagar hoy?", "Sí, revise la columna 'Estado'. Las que dicen 'Vence en 0 días' o tienen pocos días de vencidas son su prioridad de pago inmediata."),
        ("¿Cómo sé si tengo saldo a favor con un proveedor?", "El saldo total aparecerá negativo, o verá notas crédito/anticipos sin cruzar en el listado. Puede pedir devolución o cruzarlo con nuevas compras."),
        ("¿Incluye las retenciones practicadas?", "El saldo que se muestra es el 'Neto a Pagar' (Total Factura - Retenciones). Es lo que realmente debe girar al proveedor."),
        ("¿Puedo filtrar por sucursal?", "Si maneja centros de costo, este reporte es global por tercero. Para ver deudas por proyecto, use el 'Balance de Prueba por Centro de Costo' filtrando la cuenta de proveedores."),
        ("¿Por qué aparece una factura de hace años?", "Probablemente es un residuo o error antiguo no depurado. Se recomienda hacer un ajuste contable o anularla si no es real, para limpiar la cartera."),
        ("¿Sirve para programar flujo de caja?", "Totalmente. El análisis de vencimientos (Aging) le dice cuánto efectivo necesita para cubrir deudas de 30, 60 y 90 días.")
    ],
    "virtual_auxiliar_proveedor.md": [
        ("¿Cómo sé qué facturas pagué con un Egreso específico?", "Use la vista 'Por Comprobantes (Egresos)'. Busque el número de su Comprobante de Egreso y verá desplegadas todas las facturas de compra que ese dinero cubrió."),
        ("¿Puedo ver el historial de pagos a un proveedor?", "Sí, genere el reporte con un rango de fechas amplio (ej: todo el año). Verá todas las compras y todos los pagos realizados."),
        ("¿Qué significa 'Saldo x Pagar' en la vista de facturas?", "Es el valor que aún debe de esa factura específica después de restar todos los egresos y notas débito aplicados."),
        ("¿Por qué el total pagado no coincide con mis egresos del banco?", "Recuerde que este reporte muestra pagos aplicados a facturas. Si hizo un anticipo que no cruzó, o si pagó gastos diversos (no proveedores), no aparecerán aquí de la misma forma."),
        ("¿Cómo imprimo el soporte de pago de varias facturas?", "La vista 'Por Comprobantes' es ideal. Exporte a PDF y tendrá el detalle de qué facturas se cancelaron con ese giro, perfecto para adjuntar al comprobante de transferencia."),
        ("¿Muestra las devoluciones a proveedores?", "Sí, las Notas Débito (devoluciones) actúan como un 'pago' (disminuyen la deuda) y aparecerán restando al saldo de la factura.")
    ],
    # --- Reportes Contables ---
    "capitulo_27_libro_diario.md": [
        ("¿Por qué no veo movimientos de hoy?", "Asegúrese de que el filtro de 'Fecha Fin' incluya el día de hoy. Por defecto, algunos reportes pueden cargar hasta el día anterior dependiendo de su configuración."),
        ("¿Puedo exportar a Excel?", "Sí, utilice el botón 'Exportar CSV'. Este formato es compatible con Excel y le permite realizar tablas dinámicas fácilmente."),
        ("¿Qué significa la columna 'Documento'?", "Muestra las iniciales del Tipo de Documento (ej: FC para Factura de Compra) seguido del número consecutivo."),
        ("¿El reporte incluye documentos anulados?", "No, el Libro Diario solo muestra movimientos contables válidos (estado ACTIVO). Los documentos anulados no generan movimiento contable."),
        ("¿Cómo ordeno los datos?", "El reporte se ordena cronológicamente por defecto. Si exporta a CSV, puede reordenar por cualquier columna en su hoja de cálculo."),
        ("¿Qué hago si veo un movimiento duplicado?", "Verifique el número de documento. Si es el mismo, es posible que el documento tenga múltiples líneas imputando a la misma cuenta (ej: varios productos con la misma cuenta de ingreso)."),
        ("¿Puedo filtrar por usuario creador?", "No en este reporte estándar. Para esa búsqueda específica, utilice el 'Super Informe'."),
        ("¿Por qué el débito y crédito no cuadran en una línea?", "El Libro Diario muestra el detalle por movimiento. El cuadre (partida doble) se garantiza a nivel de Documento, no necesariamente línea por línea si hay múltiples cuentas involucradas.")
    ],
    "capitulo_28_balance_general.md": [
        ("¿Por qué no me cuadra el Balance?", "Revise la sección 'Ecuación Patrimonial' al final del reporte. Si hay diferencia, suele ser por movimientos directos a cuentas de patrimonio o errores en cierres anteriores. El sistema le alertará con un icono rojo."),
        ("¿La utilidad se calcula automáticamente?", "Sí. ContaPY calcula la 'Utilidad del Ejercicio' en tiempo real (Ingresos - Gastos - Costos) y la suma al Patrimonio para cuadrar el balance, sin necesidad de hacer un asiento de cierre manual cada mes."),
        ("¿Puedo ver el balance de meses anteriores?", "Sí, simplemente cambie la 'Fecha de Corte'. El sistema reconstruirá los saldos acumulados hasta esa fecha exacta."),
        ("¿Qué cuentas componen el Activo?", "Todas las cuentas que empiezan por el código '1'. Se ordenan por liquidez (Disponible, Inversiones, Deudores, etc.)."),
        ("¿Cómo imprimo este reporte para el banco?", "Use el botón 'Exportar PDF'. Este genera un documento oficial con el encabezado de la empresa, listo para firmar y entregar."),
        ("¿Por qué aparecen saldos negativos en el Activo?", "Generalmente son cuentas de naturaleza crédito dentro del activo, como la 'Depreciación Acumulada' o 'Provisiones'. Es el comportamiento contable correcto."),
        ("¿Incluye los impuestos?", "Sí, las cuentas de impuestos por pagar (Pasivo, grupo 24) o a favor (Activo, grupo 13) se reflejan según su saldo a la fecha de corte.")
    ],
    "capitulo_29_estado_resultados.md": [
        ("¿Este reporte incluye el IVA?", "No. El Estado de Resultados muestra Ingresos, Costos y Gastos antes de impuestos. El IVA se maneja en el Balance General (Pasivo/Activo)."),
        ("¿Cómo veo la utilidad bruta?", "El reporte estructura la información restando a los Ingresos (4) los Costos (6 y 7), mostrando el subtotal de Utilidad Bruta antes de restar los Gastos (5)."),
        ("¿Puedo ver el detalle de cada cuenta?", "Sí, al exportar o visualizar en pantalla, verá el desglose cuenta por cuenta. Para un análisis más profundo de una cuenta específica, use el 'Auxiliar de Cuenta'."),
        ("¿Por qué tengo utilidad negativa?", "Significa que sus Gastos y Costos superaron a sus Ingresos en el periodo consultado (Pérdida del Ejercicio)."),
        ("¿El reporte es acumulado o del mes?", "Depende del rango de fechas que seleccione. Puede sacar un P&G de un solo mes o acumulado del año (Enero a la fecha)."),
        ("¿Incluye ingresos no operacionales?", "Sí, se muestran en la sección de 'Otros Ingresos' (cuentas 42) después de la utilidad operacional."),
        ("¿Cómo analizo la rentabilidad?", "Divida la Utilidad Neta sobre los Ingresos Totales para obtener el margen neto. El reporte le entrega los valores absolutos para este cálculo.")
    ],
    "capitulo_30_balance_prueba.md": [
        ("¿Para qué sirve el 'Nivel' de cuenta?", "Le permite resumir o detallar el reporte. Nivel 1 muestra solo Grupos (Activo, Pasivo...), mientras que Nivel 4 o 5 muestra hasta las subcuentas específicas."),
        ("¿Puedo ver cuentas con saldo cero?", "Sí, use el filtro 'Mostrar cuentas con saldo cero' si desea ver todo el plan de cuentas, aunque no tengan movimiento."),
        ("¿Qué significa 'Saldo Inicial'?", "Es el valor acumulado de la cuenta justo antes de la 'Fecha Inicio' seleccionada. Es vital para verificar la continuidad de los saldos."),
        ("¿Cómo detecto errores de digitación?", "Revise las columnas Débito y Crédito del periodo. Si ve valores inusualmente altos o en cuentas que no corresponden, investigue con el Auxiliar."),
        ("¿Este reporte sirve para declaraciones tributarias?", "Es la base principal. Exporte a Excel y use los saldos finales para diligenciar sus formularios de impuestos."),
        ("¿Por qué el saldo inicial no coincide con el final del mes pasado?", "Verifique que no haya documentos con fecha posterior que se hayan anulado o modificado. El sistema es en tiempo real."),
        ("¿Puedo filtrar por un solo grupo de cuentas?", "Sí, puede escribir '1' en el filtro de cuenta para ver solo Activos, o '4' para Ingresos, etc.")
    ],
    "capitulo_31_auxiliar_cuenta.md": [
        ("¿Cómo busco un movimiento específico?", "Seleccione la cuenta contable y el rango de fechas. Verá cada débito y crédito detallado con su fecha, tercero y concepto."),
        ("¿Puedo ver todos los movimientos de un tercero en una cuenta?", "Sí, el reporte muestra la columna 'Beneficiario'. Al exportar a Excel, puede filtrar por el NIT del tercero."),
        ("¿Qué es el saldo arrastre?", "Es el saldo que traía la cuenta antes de la fecha de inicio de su consulta. Se suma a los movimientos para dar el nuevo saldo."),
        ("¿Cómo corrijo un movimiento incorrecto?", "Identifique el 'Tipo' y 'Número' de documento en el auxiliar. Vaya al módulo correspondiente (ej: Facturación), busque ese documento y anúlelo o cree una nota crédito/débito."),
        ("¿Por qué aparece 'Saldo Inicial' en cero?", "Si es una cuenta de resultado (Ingresos/Gastos) y está consultando un año nuevo, el saldo inicia en cero. Si es de Balance, verifique que la empresa tenga saldos anteriores."),
        ("¿Puedo imprimir el auxiliar de una sola cuenta?", "Sí, seleccione la cuenta específica en el filtro y genere el PDF. Es muy útil para anexar a soportes contables.")
    ],
    "capitulo_32_libros_oficiales.md": [
        ("¿Estos libros cumplen con la norma legal?", "Sí, generan la estructura estándar requerida: Encabezado de la empresa, fechas, y columnas reglamentarias (Saldo Anterior, Movimientos, Saldo Nuevo)."),
        ("¿Cómo numero las páginas?", "Al imprimir el PDF, puede configurar la numeración en las opciones de impresión de su navegador o lector de PDF si lo requiere físicamente."),
        ("¿Debo imprimir esto todos los días?", "No, generalmente se imprimen y archivan mensualmente o anualmente según las políticas de su empresa y la normativa local."),
        ("¿Qué diferencia hay entre el Libro Mayor y el Balance de Prueba?", "El Libro Mayor es más resumido (generalmente a 4 dígitos) y muestra el movimiento mensual acumulado, ideal para la visión macro de los libros oficiales."),
        ("¿El Libro de Inventarios y Balances es lo mismo que el de Inventario de Mercancía?", "No. El 'Libro de Inventarios y Balances' es un estado financiero general (Activos, Pasivos, Patrimonio). Para ver el detalle de productos, use los reportes de 'Inventario y Logística'."),
        ("¿Puedo generar libros de años pasados?", "Sí, siempre que la información histórica esté cargada en el sistema, puede generar libros de cualquier periodo.")
    ],
    "capitulo_33_super_informe.md": [
        ("¿Qué es el Super Informe?", "Es una herramienta de inteligencia de negocios (BI) y auditoría. Le permite cruzar casi cualquier dato del sistema: quién creó un documento, cuándo, por qué valor, etc."),
        ("¿Cómo encuentro documentos borrados?", "En el filtro 'Estado del Documento', seleccione 'Eliminados'. Podrá ver quién eliminó el documento y la justificación (si se configuró obligatoria)."),
        ("¿Puedo buscar por valor exacto?", "Sí. Use el filtro de 'Monto' y el operador 'Igual' (o Mayor/Menor) para encontrar esa transacción de $150.000 que no recuerda a qué corresponde."),
        ("¿Cómo audito el trabajo de un usuario?", "Filtre por 'Usuario Creador' o 'Usuario Operación' para ver todas las transacciones realizadas por una persona específica en un rango de fechas."),
        ("¿Puedo guardar mis reportes personalizados?", "Actualmente debe configurar los filtros cada vez, pero puede guardar la URL de la búsqueda en sus favoritos del navegador para acceso rápido."),
        ("¿Sirve para buscar en el detalle de los conceptos?", "Sí, el campo 'Palabra clave en concepto' busca texto dentro de las descripciones de cada movimiento. Ideal para encontrar 'compra de papelería' si no recuerda la cuenta."),
        ("¿Puedo ver documentos anulados?", "Sí, seleccione 'Anulados' en el estado. Verá también la fecha y usuario que realizó la anulación.")
    ],
    "capitulo_51_auxiliar_cc_cuenta.md": [
        ("¿Cómo veo los gastos de un proyecto específico?", "Filtre por el Centro de Costo asociado a ese proyecto. Verá solo los movimientos imputados a esa unidad de negocio."),
        ("¿Puedo ver múltiples centros de costo a la vez?", "Sí, el reporte permite agrupar o filtrar. Si exporta a Excel, tendrá la columna 'Centro de Costo' para tablas dinámicas."),
        ("¿Qué pasa si un movimiento no tiene centro de costo?", "No aparecerá en este reporte si filtra por un centro específico. Para ver esos casos, use el Auxiliar de Cuenta normal o el Super Informe."),
        ("¿Es útil para control presupuestal?", "Totalmente. Puede comparar lo ejecutado en cada cuenta de gasto por centro de costo contra su presupuesto externo."),
        ("¿Muestra ingresos por centro de costo?", "Sí, si al facturar imputó los ingresos a centros de costo (ej: Ventas Zona Norte), aquí verá el detalle de facturación por zona.")
    ],
    "capitulo_52_balance_general_cc.md": [
        ("¿El patrimonio se divide por centro de costo?", "Generalmente no, a menos que haya realizado asientos manuales imputando centros de costo a cuentas de patrimonio. Lo usual es ver Activos y Resultados."),
        ("¿Cómo sé qué porcentaje representa cada área?", "Exporte a Excel para realizar un análisis vertical. El sistema le da los valores absolutos por centro."),
        ("¿Puedo ver un balance consolidado de dos centros?", "El sistema muestra el detalle. Para consolidar (sumar) específicos, se recomienda la exportación a hoja de cálculo."),
        ("¿Por qué no me cuadra el balance de un centro de costo?", "Es normal. Los centros de costo no siempre manejan partida doble estricta (ej: solo registran gastos sin contrapartida de banco en el mismo centro). No es un error, es la naturaleza de la contabilidad analítica."),
        ("¿Sirve para evaluar gerentes de área?", "Sí, permite ver los activos bajo su responsabilidad y los pasivos específicos de su gestión.")
    ],
    "capitulo_53_estado_resultados_cc_detallado.md": [
        ("¿Puedo ver el detalle mes a mes?", "Sí, cambie la vista o el rango de fechas. Es ideal para ver la estacionalidad de los gastos por departamento."),
        ("¿Cómo identifico centros de costo no rentables?", "Busque columnas con Utilidad Neta negativa. Este reporte cruza Ingresos vs Gastos directos de cada centro."),
        ("¿Incluye gastos generales prorrateados?", "Solo si usted realizó asientos de distribución de costos (prorrateo) en la contabilidad. El sistema reporta lo que se imputó directamente."),
        ("¿Puedo comparar dos centros de costo?", "Sí, genere el reporte y compare las columnas o secciones de cada uno. Ideal para comparar sucursales o puntos de venta."),
        ("¿Muestra el margen bruto por proyecto?", "Sí, al separar los Costos de Ventas por centro de costo, puede ver la utilidad bruta real de cada proyecto.")
    ],
    "capitulo_54_balance_prueba_cc.md": [
        ("¿Para qué sirve este reporte?", "Para verificar la integridad de la data por centro de costo. Le ayuda a auditar que no falten imputaciones en cuentas clave."),
        ("¿Puedo ver solo las cuentas de gasto?", "Sí, filtre por el rango de cuentas del grupo 5. Así verá rápidamente cuánto ha gastado cada área."),
        ("¿Es igual al Balance de Prueba normal?", "En estructura sí, pero desglosado. La suma de todos los centros de costo (más lo sin centro) debe igualar al Balance de Prueba general."),
        ("¿Detecta errores de imputación?", "Sí, si ve una cuenta administrativa (ej: Sueldos Gerencia) en un centro de costo operativo (ej: Planta Producción), sabrá que hubo un error de digitación.")
    ],
    "capitulo_55_analisis_financiero.md": [
        ("¿Cómo se calcula el EBITDA?", "Utilidad Operacional + Depreciaciones + Amortizaciones. Es un indicador aproximado de la caja operativa."),
        ("¿Cada cuánto se actualizan los indicadores?", "En tiempo real. Cada factura o gasto que registre actualiza inmediatamente la liquidez y rentabilidad."),
        ("¿Qué es la Prueba Ácida?", "Es el Activo Corriente menos los Inventarios, dividido por el Pasivo Corriente. Muestra su capacidad de pago inmediata sin depender de vender mercancía."),
        ("¿Puedo personalizar los indicadores?", "El dashboard muestra los estándares (Liquidez, Solvencia, Rentabilidad). Para indicadores propios, use el Super Informe y Excel."),
        ("¿Por qué mi rentabilidad es cero?", "Si no ha registrado ventas o costos en el periodo, o si son exactamente iguales, el margen será cero. Revise el Estado de Resultados."),
        ("¿Sirve para solicitar créditos?", "Sí, los bancos suelen pedir estos indicadores clave. Puede tomar una captura o imprimir el reporte para sustentar su solicitud.")
    ],
    "capitulo_24_nuevo_documento.md": [
        ("¿Existe la opción de guardar como borrador?", "No, en ContaPY los documentos afectan la contabilidad inmediatamente al guardarse (estado ACTIVO). Si necesita corregir un error, debe anular el documento o crear una nota contable correctiva."),
        ("¿Hay atajos de teclado para agilizar la digitación de valores?", "Sí. En los campos de Débito/Crédito, puede usar la tecla '+' para multiplicar el valor actual por 1.000 y '-' para multiplicarlo por 100. Ejemplo: Escriba '50' y presione '+' para obtener '50.000'."),
        ("¿Cómo cuadro el documento automáticamente?", "Si tiene una diferencia en el asiento, presione la tecla 'Tab' en el último campo de valor (Débito o Crédito). El sistema calculará automáticamente la diferencia para cuadrar el asiento y lo asignará a ese campo."),
        ("¿Puedo cambiar la fecha del documento?", "Sí, pero el sistema validará que no sea inferior a la 'Fecha de Inicio de Operaciones' de la empresa ni pertenezca a un periodo cerrado."),
        ("¿Qué hago si el tercero no existe?", "Debe crearlo previamente en el módulo de Terceros o usar la opción de creación rápida si está habilitada en su perfil.")
    ],
    "capitulo_25_captura_rapida.md": [
        ("¿Para qué sirve el 'Valor Único'?", "Es una herramienta de productividad. Si ingresa un valor en este campo, se distribuirá automáticamente a todos los renglones de la plantilla, ideal para causaciones donde todos los débitos/créditos son iguales."),
        ("¿Cómo creo un tercero sin salir de la pantalla?", "Presione la tecla 'Insert' en su teclado. Se abrirá una ventana modal para la creación rápida del tercero sin perder el progreso de su documento."),
        ("¿Por qué se copia el concepto automáticamente?", "El sistema usa un 'Efecto Espejo': lo que escribe en el concepto del primer renglón se replica en el segundo. Esto agiliza la digitación de asientos simples de dos líneas."),
        ("¿Puedo modificar las cuentas de la plantilla aquí?", "No, la Captura Rápida usa la estructura fija de la plantilla. Si necesita cambiar cuentas, debe usar 'Nuevo Documento' o editar la plantilla en Configuración.")
    ],
    "capitulo_26_explorador.md": [
        ("¿Cómo reimprimo una factura o documento?", "Ubique el documento en la lista usando los filtros y haga clic en el icono de impresora en la columna de 'Acciones'. Se generará un PDF en una nueva pestaña."),
        ("¿Puedo ver documentos anulados?", "Sí, el explorador muestra todos los documentos. Los anulados se identifican claramente con una etiqueta roja 'ANULADO' en la columna de estado."),
        ("¿Cómo filtro por un cliente específico?", "Use el filtro 'Tercero' en la barra superior. Puede combinarlo con rangos de fecha para ser más específico."),
        ("¿Puedo exportar este listado?", "Actualmente la vista es de consulta en pantalla y reimpresión. Para exportaciones masivas, se recomienda usar el 'Libro Diario' o los reportes auxiliares."),
        ("¿Cómo anulo un documento desde aquí?", "Por seguridad, la anulación no se hace directamente en el explorador de consulta rápida. Debe ir a la opción de anulación específica o entrar al detalle del documento si su rol lo permite.")
    ],
    "capitulo_40_compras.md": [
        ("¿Es obligatorio el número de factura del proveedor?", "Sí, si el Tipo de Documento tiene marcada la opción 'Numeración Manual'. Esto es vital para evitar registrar dos veces la misma factura de un proveedor."),
        ("¿Qué pasa si no selecciono bodega?", "Si el documento afecta inventario (ej: Compra de Mercancía), el campo Bodega es OBLIGATORIO. El sistema no le dejará guardar sin definir dónde entrará la mercancía."),
        ("¿Puedo cambiar el costo unitario sugerido?", "Sí. El sistema puede sugerir el último costo, pero usted debe ingresar el valor real de la factura. Este nuevo costo actualizará el Promedio Ponderado del producto automáticamente."),
        ("¿Cómo registro una compra a crédito?", "Ingrese la 'Fecha de Vencimiento' en el campo correspondiente. Esto generará la cuenta por pagar en el módulo de proveedores con esa fecha de corte."),
        ("¿Puedo crear productos desde esta pantalla?", "Sí, use el botón '+' o la opción de creación rápida en el buscador de productos si el ítem no existe en su maestro de inventarios.")
    ],
    "capitulo_41_facturacion.md": [
        ("¿Cómo se asigna el precio de venta?", "El sistema busca automáticamente la 'Lista de Precios' asignada al Cliente seleccionado. Si no tiene lista, traerá el precio base del producto."),
        ("¿Qué pasa si la venta es a Crédito?", "Debe seleccionar 'Crédito' en la condición de pago y OBLIGATORIAMENTE establecer una 'Fecha de Vencimiento' válida (mayor o igual a la fecha de factura)."),
        ("¿Puedo facturar sin stock?", "Depende de la configuración de 'Topes' de la empresa. Generalmente, el sistema validará existencias y bloqueará la venta si no hay suficiente inventario en la bodega seleccionada."),
        ("¿Cómo cambio la bodega de salida?", "Seleccione la bodega en el encabezado ANTES de agregar los productos. Si cambia la bodega después, deberá verificar la disponibilidad nuevamente."),
        ("¿El sistema calcula impuestos automáticamente?", "Sí, basado en la configuración fiscal del Producto (IVA, Impoconsumo) y del Tercero (Retenciones). Verifique los totales antes de guardar.")
    ],


    # --- Inventario y Logística ---
    "capitulo_38_gestion_inventario.md": [
        ("¿Qué método de valoración utiliza el sistema?", "ContaPY utiliza el método de Promedio Ponderado. Cada vez que ingresa mercancía (compra o ajuste de entrada), el sistema recalcula el costo unitario dividiendo el nuevo valor total sobre la nueva cantidad total."),
        ("¿Cómo creo un producto compuesto (kit)?", "En la ficha del producto, marque la opción 'Es Kit'. Luego, en la pestaña 'Componentes', agregue los productos hijos y sus cantidades. Al facturar el Kit, el sistema descontará automáticamente el inventario de los componentes."),
        ("¿Puedo usar códigos de barras?", "Sí, el campo 'Código de Barras' es compatible con lectores estándar USB/Bluetooth. En la facturación, puede escanear el producto para agregarlo rápidamente."),
        ("¿Qué pasa si tengo stock negativo?", "El sistema permite facturar en negativo si la configuración de 'Bloquear sin Stock' está desactivada, pero esto distorsiona gravemente el Costo Promedio. Se recomienda realizar ajustes de entrada con fecha anterior a la venta para corregirlo."),
        ("¿Puedo inactivar un producto?", "Sí, si ya no lo vende. Esto lo oculta de las búsquedas pero mantiene su historia en los reportes. No se recomienda eliminar productos con movimientos."),
        ("¿Cómo manejo productos de servicio?", "Marque la casilla 'Es Servicio' al crear el producto. Estos ítems no controlan existencias (Kardex) y no requieren bodega para ser facturados."),
        ("¿Puedo cambiar el código de un producto?", "No es recomendable si ya tiene movimientos, ya que afecta la trazabilidad. Si es estrictamente necesario, use la herramienta de 'Recodificación' en utilidades (si está disponible para su rol)."),
        ("¿El sistema maneja lotes y fechas de vencimiento?", "Depende de su versión. La versión estándar maneja control de cantidades y costos globales por bodega. El control de lotes es un módulo avanzado.")
    ],
    "capitulo_39_parametros_inventario.md": [
        ("¿Qué son las bodegas?", "Son ubicaciones físicas (ej: Almacén Principal, Sucursal Norte) o lógicas (ej: Bodega Averías, Tránsito) donde se almacena el stock. Cada bodega maneja sus propias cantidades."),
        ("¿Cómo configuro las cuentas contables del inventario?", "En 'Grupos de Inventario', defina las cuentas de Inventario (Activo), Costo de Venta (Gasto), Ingreso (Venta) y Devolución. El sistema usará estas cuentas automáticamente en todas las transacciones."),
        ("¿Puedo tener diferentes cuentas para diferentes productos?", "Sí, cree múltiples 'Grupos de Inventario' (ej: Grupo Medicamentos, Grupo Aseo) y asigne cada producto a su grupo correspondiente."),
        ("¿Qué es una 'Característica' de producto?", "Son atributos adicionales como Talla, Color o Marca. Puede definirlos aquí y luego asignarlos a los productos para filtrar reportes más detallados."),
        ("¿Es obligatorio asignar una bodega al usuario?", "Sí, en la configuración de usuario se define una 'Bodega Predeterminada'. Esto agiliza la facturación, aunque el usuario puede cambiarla si tiene permisos.")
    ],
    "capitulo_42_traslados.md": [
        ("¿El traslado genera asiento contable?", "Solo si las bodegas pertenecen a Centros de Costo diferentes y tiene configurada la contabilidad por ubicación. De lo contrario, es un movimiento interno de cantidades (Salida Origen -> Entrada Destino) que no afecta el valor total del inventario."),
        ("¿Cómo muevo mercancía entre sucursales?", "Use el documento 'Traslado de Inventario'. Seleccione la Bodega Origen (debe tener saldo) y la Bodega Destino. El sistema valida que haya disponibilidad antes de guardar."),
        ("¿Puedo anular un traslado?", "Sí. Al anularlo, el sistema revierte la operación: devuelve los productos a la bodega de origen y los retira de la de destino."),
        ("¿Qué costo se usa en el traslado?", "El traslado se realiza al Costo Promedio que tenga el producto en el momento de la operación. No se puede modificar manualmente para evitar inconsistencias de valoración."),
        ("¿Puedo hacer traslados masivos?", "Sí, puede cargar los ítems desde un archivo plano o usar la función de 'Cargar desde Pedido' si el traslado responde a una solicitud interna.")
    ],
    "capitulo_43_ajuste_inventario.md": [
        ("¿Cuándo debo usar un ajuste?", "Use 'Ajuste de Entrada' para sobrantes, obsequios o carga inicial de saldos. Use 'Ajuste de Salida' para mermas, daños, robos o consumo interno."),
        ("¿El ajuste recalcula el costo promedio?", "Sí. Un ajuste de entrada (Sobrante) entra al costo que usted digite, lo cual promediará con el stock existente. Un ajuste de salida sale al costo promedio actual."),
        ("¿A qué cuenta va la contrapartida del ajuste?", "Depende de la configuración del 'Tipo de Documento' de ajuste. Generalmente se configura para que vaya a una cuenta de Gasto (Pérdida por Inventario) o Ingreso (Aprovechamientos)."),
        ("¿Puedo hacer ajustes con valor cero?", "Sí, para correcciones de solo cantidad. Tenga cuidado: entrar mercancía a costo cero bajará su promedio ponderado."),
        ("¿Cómo cargo el inventario inicial?", "Cree un documento de 'Ajuste de Entrada' (o Saldo Inicial), seleccione la bodega y cargue todos los productos con sus cantidades y costos reales de adquisición.")
    ],
    "capitulo_44_rentabilidad_producto.md": [
        ("¿Cómo se calcula la rentabilidad?", "Se toma el Precio de Venta (sin IVA) menos el Costo Promedio del producto al momento de la venta. El margen se expresa en porcentaje: (Utilidad / Precio Venta) * 100."),
        ("¿Por qué tengo rentabilidad del 100%?", "Esto ocurre cuando el Costo Promedio del producto es cero. Verifique si ingresó la mercancía mediante una compra o ajuste valorizado antes de venderla."),
        ("¿Puedo ver la rentabilidad por cliente?", "Sí, el reporte permite agrupar las ventas por Cliente para ver quién le deja mayor margen, no solo quién le compra más."),
        ("¿Incluye las notas crédito?", "Sí, las devoluciones de ventas restan de la rentabilidad, ajustando tanto el ingreso como el costo (la mercancía regresa al inventario)."),
        ("¿Qué hago si la rentabilidad es negativa?", "Significa que está vendiendo por debajo del costo. Revise su lista de precios o verifique si hubo un error en el costo de la última compra.")
    ],
    "capitulo_45_movimiento_analitico.md": [
        ("¿Puedo rastrear quién modificó el stock?", "Sí, este reporte es su herramienta de auditoría principal. Muestra el usuario, fecha, hora exacta y tipo de documento de cada transacción."),
        ("¿Sirve para auditoría?", "Es el mejor reporte para auditar, ya que muestra el 'antes' y 'después' de cada movimiento, permitiendo detectar saltos injustificados."),
        ("¿Puedo filtrar por un lote de documentos?", "Sí, puede filtrar por tipo de documento (ej: solo Ajustes) para revisar todas las correcciones manuales hechas en el mes."),
        ("¿Muestra los traslados?", "Sí, verá la salida de una bodega y la entrada a la otra como dos renglones separados pero vinculados por el mismo número de documento.")
    ],
    "capitulo_46_kardex_detallado.md": [
        ("¿Qué hago si tengo saldos negativos?", "Los negativos son matemáticamente posibles (vendió más de lo que tenía registrado) pero financieramente erróneos. Debe realizar un ajuste de entrada con fecha retroactiva (anterior a la venta) para sanear el Kardex."),
        ("¿Puedo ver el Kardex a una fecha pasada?", "Sí, el sistema reconstruye los saldos basándose en los movimientos históricos hasta la fecha de corte seleccionada. Ideal para cierres de mes."),
        ("¿Por qué el saldo en valores no cuadra con Cantidad * Costo?", "Por el redondeo de decimales en el Promedio Ponderado a lo largo de miles de movimientos. El sistema ajusta estas diferencias menores automáticamente, pero el valor real es el saldo contable acumulado."),
        ("¿Puedo exportar el Kardex de todos los productos?", "Sí, aunque puede ser un archivo muy pesado. Se recomienda filtrar por Grupo de Inventario o Bodega para exportaciones más manejables."),
        ("¿El Kardex incluye pedidos pendientes?", "No, el Kardex es un reporte de movimientos REALES (facturados/remisionados). Los pedidos son documentos informativos que no mueven inventario.")
    ],
    "capitulo_47_super_informe_inventarios.md": [
        ("¿Puedo ver rotación de inventario aquí?", "Sí, puede configurar columnas para ver Entradas y Salidas totales en un periodo y calcular índices de rotación en Excel."),
        ("¿Se puede filtrar por marca o categoría?", "Sí, todos los atributos extendidos (Marca, Talla, Color) están disponibles como filtros dinámicos en este informe."),
        ("¿Puedo ver el stock de todas las bodegas en columnas?", "Sí, use la vista de 'Matriz por Bodega' (si está disponible en su versión) o exporte a Excel y use una tabla dinámica para cruzar Producto vs Bodega.")
    ],
    "capitulo_48_gestion_topes.md": [
        ("¿El sistema me avisa si bajo del mínimo?", "Sí, en el dashboard principal y al momento de facturar puede salir una alerta visual si configuró el bloqueo o advertencia por stock mínimo."),
        ("¿Cómo calculo el máximo ideal?", "El sistema no lo calcula solo, pero le provee los datos de ventas promedio. Usted debe definir el máximo basándose en su capacidad de almacenamiento y tiempo de reposición."),
        ("¿Puedo actualizar los topes masivamente?", "Sí, mediante la importación de productos desde Excel puede actualizar las columnas 'Stock Mínimo' y 'Stock Máximo' rápidamente."),
        ("¿Para qué sirve el punto de reorden?", "Es el nivel de stock donde debería generar una nueva orden de compra para que la mercancía llegue antes de tocar el stock mínimo.")
    ],
    "capitulo_49_gestion_ventas.md": [
        ("¿Cuál es mi producto más vendido?", "Genere el reporte ordenando por la columna 'Cantidad Vendida' de mayor a menor. Puede ver también cuál es el más rentable ordenando por 'Utilidad'."),
        ("¿Puedo ver ventas por vendedor?", "Sí, agrupe el informe por el campo 'Vendedor'. Es la base para liquidar comisiones por ventas cobradas o facturadas."),
        ("¿Muestra las ventas por hora?", "El reporte detallado incluye la hora. Al exportar a Excel, puede analizar sus 'horas pico' de atención."),
        ("¿Cómo veo la venta perdida?", "El sistema registra cotizaciones no cerradas. Si filtra por cotizaciones anuladas o vencidas, puede estimar la venta potencial no realizada.")
    ],

    # --- Utilidades ---
    "capitulo_60_edicion_documentos.md": [
        ("¿Puedo editar un documento ya guardado?", "Sí, siempre y cuando el documento no esté anulado y el periodo contable esté abierto. Tenga en cuenta que editar valores o cuentas afectará inmediatamente la contabilidad."),
        ("¿Qué campos NO puedo editar?", "Por integridad de datos, no puede cambiar el 'Tipo de Documento' ni el 'Número' una vez creado. Si cometió un error en estos campos, debe anular y crear uno nuevo."),
        ("¿Puedo cambiar el tercero de una factura?", "Sí, puede editar el encabezado para asignar otro tercero. Sin embargo, si necesita hacer esto masivamente, se recomienda usar la herramienta de 'Recodificación Masiva'."),
        ("¿Queda rastro de mis ediciones?", "Sí, el sistema guarda un log de auditoría interno con la fecha y usuario que realizó la modificación."),
        ("¿Puedo editar documentos de meses anteriores?", "Solo si el periodo contable de ese mes no ha sido cerrado. Si está cerrado, el sistema bloqueará cualquier intento de edición."),
        ("¿Cómo agrego más ítems a una factura guardada?", "Ingrese al modo de edición, agregue las nuevas líneas y guarde. El sistema recalculará automáticamente los totales e impuestos.")
    ],
    "capitulo_61_recodificacion_masiva.md": [
        ("¿Para qué sirve la recodificación?", "Es una herramienta potente para corregir errores de asignación. Le permite mover todos los movimientos de un Tercero A a un Tercero B, o de un Producto A a un Producto B, sin tener que editar documento por documento."),
        ("¿Es reversible?", "No hay un botón de 'deshacer'. Si se equivoca, tendría que realizar una nueva recodificación inversa. Úsela con precaución."),
        ("¿Puedo recodificar solo un rango de fechas?", "Sí, puede especificar 'Fecha Inicio' y 'Fecha Fin' para que el cambio solo afecte los documentos de ese periodo."),
        ("¿Afecta la contabilidad?", "Sí, actualiza las referencias en todos los asientos contables (tabla movimientos_contables) y encabezados de documentos. Los saldos de los terceros/productos se actualizarán acorde al cambio."),
        ("¿Puedo recodificar por número de documento?", "Sí, puede ingresar una lista de números separados por coma (ej: 101, 102, 105) para aplicar el cambio solo a esos documentos específicos."),
        ("¿Qué pasa si el tercero destino no existe?", "Debe crearlo primero en el maestro de Terceros antes de intentar la recodificación.")
    ],
    "capitulo_62_papelera_reciclaje.md": [
        ("¿Cómo restauro un documento eliminado?", "Busque el documento en la papelera, selecciónelo y haga clic en 'Restaurar'. El documento volverá a estar ACTIVO en su módulo original."),
        ("¿Puedo restaurar si el periodo está cerrado?", "No. El sistema valida el periodo contable de la fecha del documento. Si el mes está cerrado, deberá reabrir el periodo primero."),
        ("¿Qué pasa si ya usé el número del documento eliminado?", "El sistema le impedirá restaurar si detecta que ya existe otro documento activo con el mismo Tipo y Número. Deberá anular o cambiar el número del documento nuevo."),
        ("¿Cuánto tiempo permanecen los documentos aquí?", "Depende de la política de depuración de su empresa. Por defecto, permanecen indefinidamente hasta que un administrador vacíe la papelera."),
        ("¿Quién puede ver la papelera?", "Solo los usuarios con permisos de 'Administrador' o 'Auditor' tienen acceso a este módulo de seguridad."),
        ("¿Se recuperan los asientos contables?", "Sí, al restaurar, el sistema reconstruye tanto el encabezado como todos los movimientos contables asociados.")
    ],
    "capitulo_63_control_cierre.md": [
        ("¿Para qué sirve cerrar un periodo?", "Para 'congelar' la contabilidad de un mes. Esto impide que cualquier usuario cree, edite, anule o elimine documentos en ese rango de fechas, garantizando que los estados financieros no cambien."),
        ("¿Puedo cerrar el año completo?", "El cierre es mensual. Debe cerrar Enero, luego Febrero, y así sucesivamente. Esto asegura un control secuencial estricto."),
        ("¿Cómo reabro un periodo?", "Si tiene permisos de Administrador, puede usar la opción 'Reabrir'. Tenga en cuenta que solo puede reabrir el último periodo cerrado (reversa secuencial)."),
        ("¿Qué es la Auditoría de Consecutivos?", "Es un reporte que busca 'huecos' en su numeración. Ej: Si tiene la factura 1, 2 y 4, el sistema le alertará que falta la 3. Vital para control fiscal."),
        ("¿Cómo veo quién eliminó un documento?", "En el 'Log de Operaciones' o directamente en la Papelera de Reciclaje, verá la columna 'Usuario Eliminación' y la fecha exacta del evento."),
        ("¿El sistema guarda log de las anulaciones?", "Sí, cada vez que se anula un documento, se exige una 'Razón de Anulación' que queda registrada en el historial del documento y en el reporte de auditoría."),
        ("¿Puedo ver qué usuario creó un documento?", "Sí, en el detalle de cualquier documento o en el Super Informe, el campo 'Usuario Creador' es visible y filtrable.")
    ]
}

def generate_faq_html():
    css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        
        :root {
            --primary: #2563eb;
            --secondary: #1e40af;
            --bg: #f1f5f9;
            --text: #334155;
            --sidebar-width: 320px;
            --sidebar-bg: #1e293b;
            --sidebar-text: #e2e8f0;
        }
        body {
            font-family: 'Inter', 'Segoe UI', sans-serif;
            margin: 0;
            padding: 0;
            background-color: var(--bg);
            color: var(--text);
            display: flex;
            height: 100vh;
            overflow: hidden;
        }
        /* Sidebar */
        .sidebar {
            width: var(--sidebar-width);
            background: var(--sidebar-bg);
            color: var(--sidebar-text);
            overflow-y: auto;
            padding: 2rem 1.5rem;
            flex-shrink: 0;
            box-shadow: 4px 0 10px rgba(0,0,0,0.1);
        }
        .sidebar h1 {
            font-size: 1.8rem;
            color: white;
            margin-bottom: 2.5rem;
            padding-left: 0.5rem;
            border-bottom: 1px solid #334155;
            padding-bottom: 1rem;
            font-weight: 700;
            letter-spacing: -0.02em;
        }
        .nav-group {
            margin-bottom: 2rem;
        }
        .nav-group-title {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #94a3b8;
            font-weight: 700;
            margin-bottom: 0.75rem;
            padding-left: 0.75rem;
        }
        .nav-link {
            display: flex;
            align-items: center;
            padding: 0.6rem 0.75rem;
            color: #cbd5e1;
            text-decoration: none;
            border-radius: 0.5rem;
            transition: all 0.2s ease;
            font-size: 0.95rem;
            font-weight: 400;
            margin-bottom: 0.25rem;
        }
        .nav-link::before {
            content: "•";
            margin-right: 0.75rem;
            color: #64748b;
            font-size: 1.2rem;
            line-height: 0;
        }
        .nav-link:hover {
            background-color: #334155;
            color: white;
            transform: translateX(4px);
        }
        .nav-link:hover::before {
            color: var(--primary);
        }
        .nav-link.active {
            background-color: var(--primary);
            color: white;
            font-weight: 600;
        }
        .nav-link.active::before {
            color: white;
        }
        
        /* Main Content */
        .main {
            flex: 1;
            overflow-y: auto;
            padding: 4rem 6rem;
            scroll-behavior: smooth;
        }
        .content-container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 5rem;
            border-radius: 1.5rem;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
        }
        
        /* Typography */
        h1.chapter-title {
            font-size: 2.5rem;
            color: #0f172a;
            margin-top: 5rem;
            margin-bottom: 2rem;
            border-bottom: 3px solid #e2e8f0;
            padding-bottom: 1rem;
            font-weight: 800;
            letter-spacing: -0.03em;
        }
        
        /* FAQ Styles */
        .faq-item {
            margin-bottom: 2rem;
            border-bottom: 1px solid #f1f5f9;
            padding-bottom: 2rem;
        }
        .faq-question {
            font-size: 1.25rem;
            color: var(--primary);
            font-weight: 700;
            margin-bottom: 0.75rem;
            display: flex;
            align-items: start;
        }
        .faq-question::before {
            content: "P.";
            margin-right: 0.75rem;
            color: #94a3b8;
            font-weight: 900;
        }
        .faq-answer {
            font-size: 1.05rem;
            color: #475569;
            line-height: 1.7;
            padding-left: 2rem;
        }
        
        /* Note Badge */
        .system-note {
            display: inline-block;
            background: #eff6ff;
            color: var(--primary);
            padding: 0.35rem 1rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 700;
            margin-bottom: 1.5rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border: 1px solid #bfdbfe;
        }
        
        hr {
            border: 0;
            height: 1px;
            background: #e2e8f0;
            margin: 4rem 0;
        }
    </style>
    """
    
    html_content = [f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Preguntas Frecuentes - ContaPY</title>
        {css}
    </head>
    <body>
        <nav class="sidebar">
            <h1>ContaPY FAQs</h1>
    """]
    
    # Build Sidebar
    for group_name, files in GROUPS.items():
        html_content.append(f'<div class="nav-group"><div class="nav-group-title">{group_name}</div>')
        for filename in files:
            file_id = filename.replace('.md', '')
            
            # Title Generation
            if filename == "virtual_estado_cuenta_proveedor.md":
                title = "Estado Cuenta Proveedor"
            elif filename == "virtual_auxiliar_proveedor.md":
                title = "Auxiliar Proveedores"
            else:
                title = filename.replace('capitulo_', '').replace('.md', '').replace('_', ' ')
                title = re.sub(r'^\d+\s*', '', title).title()
                
            html_content.append(f'<a href="#{file_id}" class="nav-link">{title}</a>')
        html_content.append('</div>')
    
    html_content.append("""
        </nav>
        <main class="main">
            <div class="content-container">
                <div style="text-align: center; margin-bottom: 8rem;">
                    <h1 style="font-size: 5rem; color: var(--primary); margin-bottom: 1.5rem; letter-spacing: -0.05em;">Preguntas Frecuentes</h1>
                    <p style="font-size: 1.8rem; color: #64748b; font-weight: 300;">Base de Conocimiento ContaPY</p>
                    <div style="margin-top: 4rem; display: inline-block; padding: 1rem 2rem; background: #f1f5f9; border-radius: 2rem; color: #475569; font-weight: 600;">
                        Respuestas Rápidas para el Usuario Final
                    </div>
                </div>
    """)
    
    # Build Content
    for group_name, files in GROUPS.items():
        html_content.append(f'<div class="group-section"><h1 style="font-size: 3.5rem; color: #0f172a; margin: 8rem 0 4rem 0; border-bottom: 5px solid var(--primary); display: inline-block; letter-spacing: -0.03em;">{group_name}</h1></div>')
        
        for filename in files:
            file_id = filename.replace('.md', '')
            
            # Title
            if filename == "virtual_estado_cuenta_proveedor.md":
                title = "Estado Cuenta Proveedor"
            elif filename == "virtual_auxiliar_proveedor.md":
                title = "Auxiliar Proveedores"
            else:
                title = filename.replace('capitulo_', '').replace('.md', '').replace('_', ' ')
                title = re.sub(r'^\d+\s*', '', title).title()
            
            html_content.append(f'<div id="{file_id}" class="chapter-container">')
            html_content.append(f'<div class="system-note">Módulo: {group_name}</div>')
            html_content.append(f'<h1 class="chapter-title">{title}</h1>')
            
            # Get FAQs
            faqs = FAQ_DATA.get(filename, [])
            
            if faqs:
                for question, answer in faqs:
                    html_content.append(f"""
                    <div class="faq-item">
                        <div class="faq-question">{question}</div>
                        <div class="faq-answer">{answer}</div>
                    </div>
                    """)
            else:
                html_content.append('<p style="color: #94a3b8; font-style: italic;">No hay preguntas frecuentes registradas para esta sección.</p>')
                
            html_content.append('</div><hr>')
                
    html_content.append("""
            </div>
        </main>
    </body>
    </html>
    """)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(''.join(html_content))
        
    print(f"Successfully generated {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_faq_html()
