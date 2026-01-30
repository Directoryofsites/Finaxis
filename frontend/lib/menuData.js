import {
    FaCalculator, FaChartBar, FaUsers, FaFileInvoiceDollar, FaBoxes, FaCog,
    FaFileAlt, FaPlus, FaBook, FaBalanceScale, FaCheckCircle, FaUniversity,
    FaClipboardList, FaWrench, FaHandshake, FaTruckMoving, FaReceipt, FaLock,
    FaListUl, FaDollarSign, FaChartLine, FaChartPie, FaPercentage, FaFileContract,
    FaRedoAlt, FaCalendarAlt, FaTools, FaTimes, FaChartArea, FaStar, FaBuilding,
    FaTractor, FaCogs, FaHome, FaIndustry, FaExchangeAlt, FaUpload, FaEye, FaArrowUp, FaDatabase, FaEnvelope
} from 'react-icons/fa';

// Módulos definidos externamente para claridad
const ANALISIS_FINANCIERO_MODULE = {
    id: 'analisis_financiero',
    name: 'Análisis Financiero',
    icon: FaChartArea,
    description: 'Indicadores financieros y KPIs.',
    permission: 'analisis_financiero:acceso',
    links: [
        { name: 'Dashboard', href: '/analisis/dashboard', mnemonic: 'd', icon: FaChartPie, permission: 'analisis_financiero:dashboard' },
        { name: 'Presupuestos', href: '/analisis/presupuesto', mnemonic: 'p', icon: FaCalculator, permission: 'analisis_financiero:dashboard' }, // Nueva herramienta
        { name: 'Ratios', href: '/analisis/ratios', mnemonic: 'r', icon: FaPercentage, permission: 'analisis_financiero:ratios' },
        { name: 'Vertical', href: '/analisis/vertical', mnemonic: 'v', icon: FaArrowUp, permission: 'analisis_financiero:vertical' },
        { name: 'Horizontal', href: '/analisis/horizontal', mnemonic: 'h', icon: FaExchangeAlt, permission: 'analisis_financiero:horizontal' },
        { name: 'Fuentes y Usos', href: '/analisis/fuentes-usos', mnemonic: 'f', icon: FaChartBar, permission: 'analisis_financiero:fuentes_usos' },
        { name: 'Flujos de Efectivo', href: '/analisis/flujos-efectivo', mnemonic: 'e', icon: FaChartLine, permission: 'analisis_financiero:flujos_efectivo' },
    ]
};

const PH_MODULE = {
    id: 'ph',
    name: 'Gestión de Recaudos', // RENAMED from 'Propiedad Horizontal'
    icon: FaBuilding,
    permission: 'ph:acceso',
    links: [
        { name: 'Unidades / Activos', href: '/ph/unidades', mnemonic: 'u', icon: FaHome, description: 'Administrar activos sujetos de cobro.', permission: 'ph:unidades' },
        { name: 'Terceros / Miembros', href: '/ph/propietarios', mnemonic: 'm', icon: FaUsers, description: 'Directorio de responsables de pago.', permission: 'ph:propietarios' },
        { name: 'Conceptos de Cobro', href: '/ph/conceptos', mnemonic: 'c', icon: FaListUl, description: 'Definir cuotas y servicios recurrentes.', permission: 'ph:conceptos' },
        { name: 'Generar Recaudos', href: '/ph/facturacion', mnemonic: 'g', icon: FaFileInvoiceDollar, description: 'Generar cobros masivos.', permission: 'ph:facturacion' },
        { name: 'Recaudos (Pagos)', href: '/ph/pagos', mnemonic: 'r', icon: FaHandshake, description: 'Asentar pagos recibidos.', permission: 'ph:pagos' },
        { name: 'Estado de Cuenta', href: '/ph/estado-cuenta', mnemonic: 'e', icon: FaFileContract, description: 'Consultar saldos y movimientos.', permission: 'ph:estado_cuenta' },
        { name: 'Reportes Recaudos', href: '/ph/reportes', mnemonic: 'o', icon: FaChartBar, description: 'Informes de cartera y financieros.', permission: 'ph:reportes' },
        { name: 'Cartera por Edades', href: '/ph/reportes/edades', mnemonic: 'd', icon: FaChartPie, description: 'Vencimientos 30-60-90 días.', permission: 'ph:reportes' },
        { name: 'Balance de Cartera', href: '/ph/reportes/saldos', mnemonic: 'b', icon: FaBalanceScale, description: 'Saldos detallados por unidad y concepto.', permission: 'ph:reportes' },
        { name: 'Presupuestos', href: '/ph/presupuestos/gestion', mnemonic: 'p', icon: FaCalculator, description: 'Matriz de proyección anual.', permission: 'ph:configuracion' },
        { name: 'Ejecución PPT (Junta)', href: '/ph/reportes/ejecucion', mnemonic: 't', icon: FaChartArea, description: 'Informe comparativo vs real.', permission: 'ph:reportes' },
        { name: 'Configuración', href: '/ph/configuracion', mnemonic: 'f', icon: FaCog, description: 'Parámetros del sistema de recaudos.', permission: 'ph:configuracion' }
    ]
};
const NOMINA_MODULE = {
    id: 'nomina',
    name: 'Nómina',
    icon: FaUsers,
    permission: 'nomina:acceso',
    links: [
        { name: 'Empleados', href: '/nomina/empleados', mnemonic: 'e', icon: FaUsers, description: 'Gestión de contratos y personal.', permission: 'nomina:empleados' },
        { name: 'Liquidar Nómina', href: '/nomina/liquidar', mnemonic: 'l', icon: FaCalculator, description: 'Cálculo de devengados y deducciones.', permission: 'nomina:liquidar' },
        { name: 'Desprendibles', href: '/nomina/desprendibles', mnemonic: 'd', icon: FaFileAlt, description: 'Generación de comprobantes de pago.', permission: 'nomina:desprendibles' },
        { name: 'Configuración (PUC)', href: '/nomina/configuracion', mnemonic: 'c', icon: FaCog, description: 'Parametrización contable de nómina.', permission: 'nomina:configuracion' },
    ]
};

// --- MODULO PRODUCCION (NUEVO) ---
const PRODUCCION_MODULE = {
    id: 'produccion',
    name: 'Producción',
    icon: FaIndustry,
    permission: 'produccion:acceso',
    links: [
        { name: 'Gestión de Recetas', href: '/produccion/recetas', mnemonic: 'g', icon: FaListUl, description: 'Fórmulas y lista de materiales.', permission: 'produccion:recetas' },
        { name: 'Órdenes Producción', href: '/produccion/ordenes', mnemonic: 'o', icon: FaClipboardList, description: 'Control de lotes y fabricación.', permission: 'produccion:ordenes' },
    ]
};

// --- MODULO CONCILIACION BANCARIA (NUEVO) ---
const CONCILIACION_BANCARIA_MODULE = {
    id: 'conciliacion_bancaria',
    name: 'Conciliación Bancaria',
    icon: FaExchangeAlt,
    permission: 'conciliacion_bancaria:acceso',
    links: [
        { name: 'Dashboard', href: '/conciliacion-bancaria', mnemonic: 'd', icon: FaChartBar, permission: 'conciliacion_bancaria:dashboard' },
        { name: 'Conciliación Manual', href: '/conciliacion-bancaria?tab=manual', mnemonic: 'm', icon: FaExchangeAlt, permission: 'conciliacion_bancaria:conciliar' },
        { name: 'Importar Extractos', href: '/conciliacion-bancaria?tab=import', mnemonic: 'i', icon: FaUpload, permission: 'conciliacion_bancaria:importar' },
        { name: 'Reportes', href: '/conciliacion-bancaria?tab=reports', mnemonic: 'r', icon: FaEye, permission: 'conciliacion_bancaria:reportes' },
        { name: 'Configuración', href: '/conciliacion-bancaria?tab=config', mnemonic: 'c', icon: FaCog, permission: 'conciliacion_bancaria:configurar' },
    ]
};

const FAVORITOS_MODULE = {
    id: 'favoritos',
    name: 'Favoritos',
    icon: FaStar,
    route: '/',
    description: 'Accesos directos y estadísticas.'
};

export const menuStructure = [
    // 1. Contabilidad General -> Contabilidad (C)
    {
        id: 'contabilidad',
        name: 'Contabilidad',
        mnemonic: 'c',
        icon: FaCalculator,
        permission: 'contabilidad:acceso',
        links: [
            { name: 'Crear Documento', href: '/contabilidad/documentos', mnemonic: 'd', icon: FaFileAlt, description: 'Registro de asientos manuales y notas.', permission: 'contabilidad:crear_documento' },
            { name: 'Captura Rápida', href: '/contabilidad/captura-rapida', mnemonic: 'r', icon: FaPlus, description: 'Ingreso ágil de facturas y gastos.', permission: 'contabilidad:captura_rapida' },
            { name: 'Explorador Doc.', href: '/contabilidad/explorador', mnemonic: 'e', icon: FaBook, description: 'Búsqueda avanzada de movimientos.', permission: 'contabilidad:explorador' },
            { name: 'Libro Diario Detallado', href: '/contabilidad/reportes/libro-diario', mnemonic: 'l', icon: FaBook, description: 'Movimientos cronológicos por día.', permission: 'contabilidad:libro_diario' },
            { name: 'Libro Diario Resumen', href: '/contabilidad/reportes/libro-diario-resumen', mnemonic: 'u', icon: FaBook, description: 'Resumen por tipo de documento.', permission: 'contabilidad:libro_diario' },
            { name: 'Análisis de Cuenta por Documento', href: '/contabilidad/reportes/analisis-cuenta-documento', mnemonic: 'n', icon: FaBook, description: 'Desglose por fuente.', permission: 'contabilidad:analisis_cuenta' },
            { name: 'Balance General', href: '/contabilidad/reportes/balance-general', mnemonic: 'b', icon: FaBalanceScale, description: 'Estado de situación financiera (ESF).', permission: 'contabilidad:balance_general' },
            { name: 'Resultados (PYG)', href: '/contabilidad/reportes/estado-resultados', mnemonic: 'p', icon: FaChartBar, description: 'Pérdidas y Ganancias (PYG).', permission: 'contabilidad:pyg' },
            { name: 'Balance Prueba', href: '/contabilidad/reportes/balance-de-prueba', mnemonic: 'a', icon: FaCheckCircle, description: 'Resumen de saldos débito y crédito.', permission: 'contabilidad:balance_prueba' },
            { name: 'Auxiliar Contable', href: '/contabilidad/reportes/auxiliar-cuenta', mnemonic: 'x', icon: FaFileAlt, description: 'Detalle de movimientos por cuenta.', permission: 'contabilidad:auxiliar' },
            { name: 'Libros Oficiales', href: '/admin/utilidades/libros-oficiales', mnemonic: 'o', icon: FaUniversity, description: 'Generación de libros reglamentarios.', permission: 'contabilidad:libros_oficiales' },
            { name: 'Auditoría Contable Avanzada', href: '/contabilidad/reportes/super-informe', mnemonic: 'v', icon: FaClipboardList, description: 'Cruce de información y auditoría.', permission: 'contabilidad:auditoria_avanzada' },
        ]
    },
    // 2. Análisis Financiero -> Análisis (L - "A" is taken by Activos)
    { ...ANALISIS_FINANCIERO_MODULE, name: 'Análisis', mnemonic: 'l' },
    // 3. Centros de Costo -> C Costos (S - CCo[s]tos)
    {
        id: 'centros_costo',
        name: 'CCostos',
        mnemonic: 's',
        icon: FaChartBar,
        permission: 'centros_costo:acceso',
        links: [
            { name: 'Gestionar Centros', href: '/admin/centros-costo', mnemonic: 'g', icon: FaWrench, description: 'Administración de estructura de costos.', permission: 'centros_costo:gestionar' },
            { name: 'Auxiliar por C.C.', href: '/contabilidad/reportes/auxiliar-cc-cuenta', mnemonic: 'a', icon: FaFileAlt, description: 'Movimientos detallados por centro.', permission: 'centros_costo:auxiliar' },
            { name: 'Balance por C.C.', href: '/contabilidad/reportes/balance-general-cc', mnemonic: 'b', icon: FaBalanceScale, description: 'Situación financiera segmentada.', permission: 'centros_costo:balance' },
            { name: 'Resultados por C.C.', href: '/contabilidad/reportes/estado-resultados-cc-detallado', mnemonic: 'r', icon: FaChartBar, description: 'Rentabilidad por centro de costo.', permission: 'centros_costo:pyg' },
            { name: 'Balance Prueba C.C.', href: '/contabilidad/reportes/balance-de-prueba-cc', mnemonic: 'p', icon: FaCheckCircle, description: 'Saldos de prueba segmentados.', permission: 'centros_costo:balance_prueba' },
        ]
    },
    // 4. Terceros (T)
    {
        id: 'terceros',
        name: 'Terceros',
        mnemonic: 't',
        icon: FaUsers,
        permission: 'terceros:acceso',
        links: [
            { name: 'Gestionar Terceros', href: '/admin/terceros', mnemonic: 'g', icon: FaHandshake, description: 'Directorio de clientes y proveedores.', permission: 'terceros:gestionar' },
            { name: 'Auxiliar Terceros', href: '/contabilidad/reportes/tercero-cuenta', mnemonic: 'a', icon: FaFileAlt, description: 'Movimientos por beneficiario.', permission: 'terceros:auxiliar' },
            { name: 'Estado de Cuenta (Clientes)', href: '/contabilidad/reportes/estado-cuenta-cliente', mnemonic: 'c', icon: FaLock, description: 'Cuentas por cobrar a clientes.', permission: 'terceros:estado_cuenta_cliente' },
            { name: 'Auxiliar de Cartera', href: '/contabilidad/reportes/auxiliar-cartera', mnemonic: 'x', icon: FaClipboardList, description: 'Detalle de vencimientos cartera.', permission: 'terceros:cartera' },
            { name: 'Estado de Cuenta (Proveedores)', href: '/contabilidad/reportes/estado-cuenta-proveedor', mnemonic: 'p', icon: FaTruckMoving, description: 'Cuentas por pagar a proveedores.', permission: 'terceros:estado_cuenta_proveedor' },
            { name: 'Auxiliar de Proveedores', href: '/contabilidad/reportes/auxiliar-proveedores', mnemonic: 'r', icon: FaReceipt, description: 'Detalle de pasivos con terceros.', permission: 'terceros:auxiliar_proveedores' },
            { name: 'Relación de Saldos', href: '/contabilidad/reportes/relacion-saldos', mnemonic: 's', icon: FaBalanceScale, description: 'Saldos netos por cuenta y tercero.', permission: 'terceros:auxiliar' },
        ]
    },
    // 5. Impuestos (I)
    // 5. Impuestos (I)
    {
        id: 'impuestos',
        name: 'Impuestos',
        mnemonic: 'i',
        icon: FaFileInvoiceDollar,
        permission: 'impuestos:acceso',
        links: [
            { name: 'IVA', href: '/impuestos/iva', mnemonic: 'v', icon: FaPercentage, description: 'Impuesto al Valor Agregado.', permission: 'impuestos:iva' },
            { name: 'Renta', href: '/impuestos/renta', mnemonic: 'r', icon: FaChartLine, description: 'Impuesto sobre la Renta.', permission: 'impuestos:renta' },
            { name: 'Retefuente', href: '/impuestos/retefuente', mnemonic: 't', icon: FaFileContract, description: 'Retenciones en la fuente.', permission: 'impuestos:retefuente' },
            { name: 'ReteICA', href: '/impuestos/reteica', mnemonic: 'i', icon: FaBuilding, description: 'Industria y Comercio.', permission: 'impuestos:reteica' },
            { name: 'Timbre', href: '/impuestos/timbre', mnemonic: 'b', icon: FaFileAlt, description: 'Impuesto de Timbre.', permission: 'impuestos:timbre' },
            { name: 'Consumo', href: '/impuestos/consumo', mnemonic: 'c', icon: FaDollarSign, description: 'Impuesto al Consumo.', permission: 'impuestos:consumo' },
            { name: 'Calendario', href: '/impuestos/calendario', mnemonic: 'a', icon: FaCalendarAlt, description: 'Vencimientos y obligaciones.', permission: 'impuestos:calendario' },
        ]
    },
    // 6. Inventarios (E - Inv[e]ntarios)
    {
        id: 'inventarios',
        name: 'Inventarios',
        mnemonic: 'e', // 'e' from Inv[e]ntarios
        icon: FaBoxes,
        permission: 'inventario:acceso',
        links: [
            { name: 'Configuración', href: '/admin/inventario/parametros', mnemonic: 'c', icon: FaCog, description: 'Configuración de bodegas y grupos.', permission: 'inventario:configuracion' },
            { name: 'Gestión / Kardex', href: '/admin/inventario', mnemonic: 'k', icon: FaListUl, description: 'Kardex y control de existencias.', permission: 'inventario:kardex' },
            { name: 'Estadísticas / Mov.', href: '/contabilidad/reportes/movimiento-analitico', mnemonic: 'e', icon: FaFileAlt, description: 'Análisis de rotación y costos.', permission: 'inventario:estadisticas' },
            { name: 'Auditoría Docs.', href: '/contabilidad/reportes/super-informe-inventarios', mnemonic: 'a', icon: FaChartPie, description: 'Auditoría de docs de inventario.', permission: 'inventario:auditoria' },
            { name: 'Traslados', href: '/contabilidad/traslados', mnemonic: 't', icon: FaTruckMoving, description: 'Movimientos entre bodegas.', permission: 'inventario:traslados' },
            { name: 'Ajustes Manuales', href: '/admin/inventario/ajuste-inventario', mnemonic: 'm', icon: FaWrench, description: 'Corrección manual de stock.', permission: 'inventario:ajustes' },
            { name: 'Gestión de Topes', href: '/contabilidad/reportes/gestion-topes', mnemonic: 'g', icon: FaPercentage, description: 'Control de mínimos y máximos.', permission: 'inventario:topes' },
        ]
    },
    // 7. Facturación (F)
    {
        id: 'facturacion',
        name: 'Facturación',
        mnemonic: 'f',
        icon: FaDollarSign,
        permission: 'facturacion:acceso',
        links: [
            { name: 'Nueva Factura', href: '/contabilidad/facturacion', mnemonic: 'n', icon: FaDollarSign, description: 'Emisión de facturas de venta.', permission: 'facturacion:nueva' },
            { name: 'Remisiones', href: '/remisiones', mnemonic: 'r', icon: FaClipboardList, description: 'Control de despachos sin factura.', permission: 'facturacion:remisiones' },
            { name: 'Remisionado vs Facturado', href: '/remisiones/reportes', mnemonic: 'v', icon: FaChartPie, description: 'Estadísticas de remisiones.', permission: 'facturacion:reporte_remisiones' },
            { name: 'Cotizaciones', href: '/cotizaciones', mnemonic: 'c', icon: FaFileInvoiceDollar, description: 'Propuestas comerciales a clientes.', permission: 'facturacion:cotizaciones' },
            { name: 'Compras', href: '/contabilidad/compras', mnemonic: 'm', icon: FaReceipt, description: 'Registro de facturas de compra.', permission: 'compras:acceso' },
            { name: 'Rentabilidad Prod.', href: '/contabilidad/reportes/rentabilidad-producto', mnemonic: 'p', icon: FaChartLine, description: 'Margen de ganancia por ítem.', permission: 'facturacion:rentabilidad_producto' },
            { name: 'Rentabilidad Doc.', href: '/contabilidad/reportes/gestion-ventas', mnemonic: 'd', icon: FaChartLine, description: 'Análisis de utilidad por venta.', permission: 'facturacion:rentabilidad_doc' },
            { name: 'Análisis Ventas Cliente', href: '/contabilidad/reportes/ventas-cliente', mnemonic: 'a', icon: FaChartPie, description: 'Reporte integral de ventas por cliente.', permission: 'facturacion:ventas_cliente' },
        ]
    },
    // 8. Activos Fijos -> Activos (A)
    {
        id: 'activos',
        name: "Activos",
        mnemonic: 'a',
        icon: FaTractor,
        permission: 'activos:acceso',
        links: [
            { name: "Listado Activos", href: "/activos", mnemonic: 'l', icon: FaListUl, description: 'Inventario de propiedad, planta y equipo.', permission: 'activos:listar' },
            { name: "Configuración", href: "/activos/categorias", mnemonic: 'c', icon: FaCogs, description: 'Configuración de depreciación.', permission: 'activos:configurar' },
        ]
    },
    // 9. Propiedad Horizontal -> PH (P)
    { ...PH_MODULE, mnemonic: 'g' },
    // 10. Nómina (N - [N]omina - Updated to avoid M conflict)
    { ...NOMINA_MODULE, mnemonic: 'n' },
    // 11. Producción (R - P[r]oduccion)
    { ...PRODUCCION_MODULE, mnemonic: 'r' },
    // 12. Conciliación Bancaria -> Conciliación (O - C[o]nciliacion)
    { ...CONCILIACION_BANCARIA_MODULE, name: 'Conciliación', mnemonic: 'o' },
    // 13. Administración -> Admin (D)
    {
        id: 'administracion',
        name: 'Admin',
        mnemonic: 'd',
        icon: FaCog,
        permission: 'administracion:acceso',
        subgroups: [
            {
                title: 'Parametrización',
                icon: FaFileContract,
                description: 'Configuración fundamental.',
                links: [
                    { name: 'PUC', href: '/admin/plan-de-cuentas', mnemonic: 'p', icon: FaBook, permission: 'contabilidad:gestionar_puc' },
                    { name: 'Tipos Doc.', href: '/admin/tipos-documento', mnemonic: 't', icon: FaClipboardList, permission: 'contabilidad:configuracion_tipos_doc' },
                    { name: 'Plantillas', href: '/admin/plantillas', mnemonic: 'i', icon: FaFileAlt, permission: 'contabilidad:configuracion_plantillas' },
                    { name: 'Conceptos', href: '/admin/utilidades/gestionar-conceptos', mnemonic: 'c', icon: FaListUl, permission: 'contabilidad:configuracion_conceptos' },
                    { name: 'Empresas', href: '/admin/empresas', mnemonic: 'e', icon: FaUniversity, permission: 'empresa:gestionar_empresas' },
                    { name: 'Usuarios y Roles', href: '/admin/configuracion/usuarios-roles', mnemonic: 'u', icon: FaUsers, permission: 'empresa:usuarios_roles' },
                ]
            },
            {
                title: 'Control',
                icon: FaBook,
                description: 'Procesos de cierre.',
                links: [
                    { name: 'Backups', href: '/admin/utilidades/migracion-datos', mnemonic: 'b', icon: FaRedoAlt, permission: 'utilidades:migracion' },
                    { name: 'Cierre Periodos', href: '/admin/utilidades/periodos-contables', mnemonic: 'r', icon: FaCalendarAlt, permission: 'utilidades:cierre_periodos' },
                    { name: 'Auditoría de Consecutivos', href: '/admin/utilidades/auditoria-consecutivos', mnemonic: 'a', icon: FaCheckCircle, permission: 'utilidades:auditoria_consecutivos' },
                    { name: 'Conteo Registros', href: '/admin/utilidades/conteo-registros', mnemonic: 'o', icon: FaDatabase, permission: 'utilidades:conteo_registros' },
                    { name: 'Mi Plan y Consumo', href: '/contabilidad/consumo', mnemonic: 'n', icon: FaChartPie, description: 'Estado de cupos y recargas.', permission: 'contabilidad:acceso' },
                ]
            },
            {
                title: 'Herramientas',
                icon: FaWrench,
                description: 'Mantenimiento.',
                links: [
                    { name: 'Scripts/Util', href: '/admin/utilidades/soporte-util', mnemonic: 's', icon: FaTools, permission: 'utilidades:scripts', onlySoporte: true },
                    { name: 'Edición Masiva', href: '/admin/utilidades/eliminacion-masiva', mnemonic: 'm', icon: FaFileAlt, permission: 'utilidades:edicion_masiva' },
                    { name: 'Recodificación', href: '/admin/utilidades/recodificacion-masiva', mnemonic: 'd', icon: FaRedoAlt, permission: 'utilidades:recodificacion' },
                    { name: 'Papelera', href: '/admin/utilidades/papelera', mnemonic: 'l', icon: FaTimes, permission: 'papelera:usar' },
                    { name: 'Configuración Correo', href: '/admin/utilidades/configuracion-correo', mnemonic: 'f', icon: FaEnvelope, permission: 'utilidades:config_correo' },
                ]
            },
        ]
    },
];
