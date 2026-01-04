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
    links: [
        { name: 'Dashboard', href: '/analisis/dashboard', mnemonic: 'd', icon: FaChartPie },
        { name: 'Ratios', href: '/analisis/ratios', mnemonic: 'r', icon: FaPercentage },
        { name: 'Vertical', href: '/analisis/vertical', mnemonic: 'v', icon: FaArrowUp },
        { name: 'Horizontal', href: '/analisis/horizontal', mnemonic: 'h', icon: FaExchangeAlt },
        { name: 'Fuentes y Usos', href: '/analisis/fuentes-usos', mnemonic: 'f', icon: FaChartBar },
        { name: 'Flujos de Efectivo', href: '/analisis/flujos-efectivo', mnemonic: 'e', icon: FaChartLine },
    ]
};

const PH_MODULE = {
    id: 'ph',
    name: 'Propiedad Horizontal',
    icon: FaBuilding,
    links: [
        { name: 'Unidades', href: '/ph/unidades', mnemonic: 'u', icon: FaHome, description: 'Administrar apartamentos, casas y locales.' },
        { name: 'Propietarios', href: '/ph/propietarios', mnemonic: 'p', icon: FaUsers, description: 'Directorio de copropietarios y residentes.' },
        { name: 'Conceptos de Cobro', href: '/ph/conceptos', mnemonic: 'c', icon: FaListUl, description: 'Definir cuotas de administración y extras.' },
        { name: 'Generar Cuentas Cobro', href: '/ph/facturacion', mnemonic: 'g', icon: FaFileInvoiceDollar, description: 'Generar cuentas de cobro mensuales.' },
        { name: 'Recaudos (Pagos)', href: '/ph/pagos', mnemonic: 'r', icon: FaHandshake, description: 'Asentar recaudos de administración.' },
        { name: 'Estado de Cuenta', href: '/ph/estado-cuenta', mnemonic: 'e', icon: FaFileContract, description: 'Consultar saldos y descargar paz y salvos.' },
        { name: 'Reportes PH', href: '/ph/reportes', mnemonic: 'o', icon: FaChartBar, description: 'Informes financieros y de cartera.' },
        { name: 'Configuración PH', href: '/ph/configuracion', mnemonic: 'f', icon: FaCog, description: 'Parámetros generales del conjunto.' }
    ]
};
const NOMINA_MODULE = {
    id: 'nomina',
    name: 'Nómina',
    icon: FaUsers,
    links: [
        { name: 'Empleados', href: '/nomina/empleados', mnemonic: 'e', icon: FaUsers, description: 'Gestión de contratos y personal.' },
        { name: 'Liquidar Nómina', href: '/nomina/liquidar', mnemonic: 'l', icon: FaCalculator, description: 'Cálculo de devengados y deducciones.' },
        { name: 'Desprendibles', href: '/nomina/desprendibles', mnemonic: 'd', icon: FaFileAlt, description: 'Generación de comprobantes de pago.' },
        { name: 'Configuración (PUC)', href: '/nomina/configuracion', mnemonic: 'c', icon: FaCog, description: 'Parametrización contable de nómina.' },
    ]
};

// --- MODULO PRODUCCION (NUEVO) ---
const PRODUCCION_MODULE = {
    id: 'produccion',
    name: 'Producción',
    icon: FaIndustry,
    links: [
        { name: 'Gestión de Recetas', href: '/produccion/recetas', mnemonic: 'g', icon: FaListUl, description: 'Fórmulas y lista de materiales.' },
        { name: 'Órdenes Producción', href: '/produccion/ordenes', mnemonic: 'o', icon: FaClipboardList, description: 'Control de lotes y fabricación.' },
    ]
};

// --- MODULO CONCILIACION BANCARIA (NUEVO) ---
const CONCILIACION_BANCARIA_MODULE = {
    id: 'conciliacion_bancaria',
    name: 'Conciliación Bancaria',
    icon: FaExchangeAlt,
    links: [
        { name: 'Dashboard', href: '/conciliacion-bancaria', mnemonic: 'd', icon: FaChartBar },
        { name: 'Conciliación Manual', href: '/conciliacion-bancaria?tab=manual', mnemonic: 'm', icon: FaExchangeAlt },
        { name: 'Importar Extractos', href: '/conciliacion-bancaria?tab=import', mnemonic: 'i', icon: FaUpload },
        { name: 'Reportes', href: '/conciliacion-bancaria?tab=reports', mnemonic: 'r', icon: FaEye },
        { name: 'Configuración', href: '/conciliacion-bancaria?tab=config', mnemonic: 'c', icon: FaCog },
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
        links: [
            { name: 'Crear Documento', href: '/contabilidad/documentos', mnemonic: 'd', icon: FaFileAlt, description: 'Registro de asientos manuales y notas.' },
            { name: 'Captura Rápida', href: '/contabilidad/captura-rapida', mnemonic: 'r', icon: FaPlus, description: 'Ingreso ágil de facturas y gastos.' },
            { name: 'Explorador Doc.', href: '/contabilidad/explorador', mnemonic: 'e', icon: FaBook, description: 'Búsqueda avanzada de movimientos.' },
            { name: 'Libro Diario Detallado', href: '/contabilidad/reportes/libro-diario', mnemonic: 'l', icon: FaBook, description: 'Movimientos cronológicos por día.' },
            { name: 'Libro Diario Resumen', href: '/contabilidad/reportes/libro-diario-resumen', mnemonic: 'u', icon: FaBook, description: 'Resumen por tipo de documento.' },
            { name: 'Análisis de Cuenta por Documento', href: '/contabilidad/reportes/analisis-cuenta-documento', mnemonic: 'y', icon: FaBook, description: 'Desglose por fuente.' },
            { name: 'Balance General', href: '/contabilidad/reportes/balance-general', mnemonic: 'b', icon: FaBalanceScale, description: 'Estado de situación financiera (ESF).' },
            { name: 'Resultados (PYG)', href: '/contabilidad/reportes/estado-resultados', mnemonic: 'p', icon: FaChartBar, description: 'Pérdidas y Ganancias (PYG).' },
            { name: 'Balance Prueba', href: '/contabilidad/reportes/balance-de-prueba', mnemonic: 'a', icon: FaCheckCircle, description: 'Resumen de saldos débito y crédito.' },
            { name: 'Auxiliar Contable', href: '/contabilidad/reportes/auxiliar-cuenta', mnemonic: 'x', icon: FaFileAlt, description: 'Detalle de movimientos por cuenta.' },
            { name: 'Libros Oficiales', href: '/admin/utilidades/libros-oficiales', mnemonic: 'o', icon: FaUniversity, description: 'Generación de libros reglamentarios.' },
            { name: 'Auditoría Contable Avanzada', href: '/contabilidad/reportes/super-informe', mnemonic: '1', icon: FaClipboardList, description: 'Cruce de información y auditoría.' },
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
        links: [
            { name: 'Gestionar Centros', href: '/admin/centros-costo', mnemonic: 'g', icon: FaWrench, description: 'Administración de estructura de costos.' },
            { name: 'Auxiliar por C.C.', href: '/contabilidad/reportes/auxiliar-cc-cuenta', mnemonic: 'a', icon: FaFileAlt, description: 'Movimientos detallados por centro.' },
            { name: 'Balance por C.C.', href: '/contabilidad/reportes/balance-general-cc', mnemonic: 'b', icon: FaBalanceScale, description: 'Situación financiera segmentada.' },
            { name: 'Resultados por C.C.', href: '/contabilidad/reportes/estado-resultados-cc-detallado', mnemonic: 'r', icon: FaChartBar, description: 'Rentabilidad por centro de costo.' },
            { name: 'Balance Prueba C.C.', href: '/contabilidad/reportes/balance-de-prueba-cc', mnemonic: 'p', icon: FaCheckCircle, description: 'Saldos de prueba segmentados.' },
        ]
    },
    // 4. Terceros (T)
    {
        id: 'terceros',
        name: 'Terceros',
        mnemonic: 't',
        icon: FaUsers,
        links: [
            { name: 'Gestionar Terceros', href: '/admin/terceros', mnemonic: 'g', icon: FaHandshake, description: 'Directorio de clientes y proveedores.' },
            { name: 'Auxiliar Terceros', href: '/contabilidad/reportes/tercero-cuenta', mnemonic: 'a', icon: FaFileAlt, description: 'Movimientos por beneficiario.' },
            { name: 'Estado de Cuenta (Clientes)', href: '/contabilidad/reportes/estado-cuenta-cliente', mnemonic: 'c', icon: FaLock, description: 'Cuentas por cobrar a clientes.' },
            { name: 'Auxiliar de Cartera', href: '/contabilidad/reportes/auxiliar-cartera', mnemonic: 'v', icon: FaClipboardList, description: 'Detalle de vencimientos cartera.' },
            { name: 'Estado de Cuenta (Proveedores)', href: '/contabilidad/reportes/estado-cuenta-proveedor', mnemonic: 'p', icon: FaTruckMoving, description: 'Cuentas por pagar a proveedores.' },
            { name: 'Auxiliar de Proveedores', href: '/contabilidad/reportes/auxiliar-proveedores', mnemonic: 'r', icon: FaReceipt, description: 'Detalle de pasivos con terceros.' },
        ]
    },
    // 5. Impuestos (I)
    // 5. Impuestos (I)
    {
        id: 'impuestos',
        name: 'Impuestos',
        mnemonic: 'i',
        icon: FaFileInvoiceDollar,
        links: [
            { name: 'IVA', href: '/impuestos/iva', mnemonic: 'v', icon: FaPercentage, description: 'Impuesto al Valor Agregado.' },
            { name: 'Renta', href: '/impuestos/renta', mnemonic: 'r', icon: FaChartLine, description: 'Impuesto sobre la Renta.' },
            { name: 'Retefuente', href: '/impuestos/retefuente', mnemonic: 't', icon: FaFileContract, description: 'Retenciones en la fuente.' },
            { name: 'ReteICA', href: '/impuestos/reteica', mnemonic: 'i', icon: FaBuilding, description: 'Industria y Comercio.' },
            { name: 'Timbre', href: '/impuestos/timbre', mnemonic: 'b', icon: FaFileAlt, description: 'Impuesto de Timbre.' },
            { name: 'Consumo', href: '/impuestos/consumo', mnemonic: 'c', icon: FaDollarSign, description: 'Impuesto al Consumo.' },
            { name: 'Calendario', href: '/impuestos/calendario', mnemonic: 'a', icon: FaCalendarAlt, description: 'Vencimientos y obligaciones.' },
        ]
    },
    // 6. Inventarios (E - Inv[e]ntarios)
    {
        id: 'inventarios',
        name: 'Inventarios',
        mnemonic: 'e', // 'e' from Inv[e]ntarios
        icon: FaBoxes,
        links: [
            { name: 'Configuración', href: '/admin/inventario/parametros', mnemonic: 'c', icon: FaCog, description: 'Configuración de bodegas y grupos.' },
            { name: 'Gestión / Kardex', href: '/admin/inventario', mnemonic: 'k', icon: FaListUl, description: 'Kardex y control de existencias.' },
            { name: 'Estadísticas / Mov.', href: '/contabilidad/reportes/movimiento-analitico', mnemonic: 'e', icon: FaFileAlt, description: 'Análisis de rotación y costos.' },
            { name: 'Auditoría Docs.', href: '/contabilidad/reportes/super-informe-inventarios', mnemonic: 'a', icon: FaChartPie, description: 'Auditoría de docs de inventario.' },
            { name: 'Traslados', href: '/contabilidad/traslados', mnemonic: 't', icon: FaTruckMoving, description: 'Movimientos entre bodegas.' },
            { name: 'Ajustes Manuales', href: '/admin/inventario/ajuste-inventario', mnemonic: 'm', icon: FaWrench, description: 'Corrección manual de stock.' },
            { name: 'Gestión de Topes', href: '/contabilidad/reportes/gestion-topes', mnemonic: 'g', icon: FaPercentage, description: 'Control de mínimos y máximos.' },
        ]
    },
    // 7. Facturación (F)
    {
        id: 'facturacion',
        name: 'Facturación',
        mnemonic: 'f',
        icon: FaDollarSign,
        links: [
            { name: 'Nueva Factura', href: '/contabilidad/facturacion', mnemonic: 'n', icon: FaDollarSign, description: 'Emisión de facturas de venta.' },
            { name: 'Remisiones', href: '/remisiones', mnemonic: 'r', icon: FaClipboardList, description: 'Control de despachos sin factura.' },
            { name: 'Reportes Ventas', href: '/remisiones/reportes', mnemonic: 'v', icon: FaChartPie, description: 'Estadísticas de remisiones.' },
            { name: 'Cotizaciones', href: '/cotizaciones', mnemonic: 'c', icon: FaFileInvoiceDollar, description: 'Propuestas comerciales a clientes.' },
            { name: 'Compras', href: '/contabilidad/compras', mnemonic: 'm', icon: FaReceipt, description: 'Registro de facturas de compra.' },
            { name: 'Rentabilidad Prod.', href: '/contabilidad/reportes/rentabilidad-producto', mnemonic: 'p', icon: FaChartLine, description: 'Margen de ganancia por ítem.' },
            { name: 'Rentabilidad Doc.', href: '/contabilidad/reportes/gestion-ventas', mnemonic: 'd', icon: FaChartLine, description: 'Análisis de utilidad por venta.' },
        ]
    },
    // 8. Activos Fijos -> Activos (A)
    {
        id: 'activos',
        name: "Activos",
        mnemonic: 'a',
        icon: FaTractor,
        links: [
            { name: "Listado Activos", href: "/activos", mnemonic: 'l', icon: FaListUl, description: 'Inventario de propiedad, planta y equipo.' },
            { name: "Configuración", href: "/activos/categorias", mnemonic: 'c', icon: FaCogs, description: 'Configuración de depreciación.' },
        ]
    },
    // 9. Propiedad Horizontal -> PH (P)
    { ...PH_MODULE, name: 'PH', mnemonic: 'p' },
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
        subgroups: [
            {
                title: 'Parametrización',
                icon: FaFileContract,
                description: 'Configuración fundamental.',
                links: [
                    { name: 'PUC', href: '/admin/plan-de-cuentas', mnemonic: 'p', icon: FaBook },
                    { name: 'Tipos Doc.', href: '/admin/tipos-documento', mnemonic: 't', icon: FaClipboardList },
                    { name: 'Plantillas', href: '/admin/plantillas', mnemonic: 'l', icon: FaFileAlt },
                    { name: 'Conceptos', href: '/admin/utilidades/gestionar-conceptos', mnemonic: 'c', icon: FaListUl },
                    { name: 'Empresas', href: '/admin/empresas', mnemonic: 'e', icon: FaUniversity },
                ]
            },
            {
                title: 'Control',
                icon: FaBook,
                description: 'Procesos de cierre.',
                links: [
                    { name: 'Backups', href: '/admin/utilidades/migracion-datos', mnemonic: 'b', icon: FaRedoAlt },
                    { name: 'Cierre Periodos', href: '/admin/utilidades/periodos-contables', mnemonic: 'r', icon: FaCalendarAlt },
                    { name: 'Auditoría', href: '/admin/utilidades/auditoria-consecutivos', mnemonic: 'a', icon: FaCheckCircle },
                    { name: 'Conteo Registros', href: '/admin/utilidades/conteo-registros', mnemonic: 'c', icon: FaDatabase },
                ]
            },
            {
                title: 'Herramientas',
                icon: FaWrench,
                description: 'Mantenimiento.',
                links: [
                    { name: 'Scripts/Util', href: '/admin/utilidades/soporte-util', mnemonic: 's', icon: FaTools },
                    { name: 'Edición Masiva', href: '/admin/utilidades/eliminacion-masiva', mnemonic: 'm', icon: FaFileAlt },
                    { name: 'Recodificación', href: '/admin/utilidades/recodificacion-masiva', mnemonic: 'd', icon: FaRedoAlt },
                    { name: 'Papelera', href: '/admin/utilidades/papelera', mnemonic: 'x', icon: FaTimes },
                    { name: 'Configuración Correo', href: '/admin/utilidades/configuracion-correo', mnemonic: 'e', icon: FaEnvelope },
                ]
            },
        ]
    },
];
