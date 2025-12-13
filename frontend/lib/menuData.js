import {
    FaCalculator, FaChartBar, FaUsers, FaFileInvoiceDollar, FaBoxes, FaCog,
    FaFileAlt, FaPlus, FaBook, FaBalanceScale, FaCheckCircle, FaUniversity,
    FaClipboardList, FaWrench, FaHandshake, FaTruckMoving, FaReceipt, FaLock,
    FaListUl, FaDollarSign, FaChartLine, FaChartPie, FaPercentage, FaFileContract,
    FaRedoAlt, FaCalendarAlt, FaTools, FaTimes, FaChartArea, FaStar, FaBuilding,
    FaStamp, FaShoppingCart, FaMoneyBillWave, FaTractor, FaCogs, FaHome, FaIndustry
} from 'react-icons/fa';

// Módulos definidos externamente para claridad
const ANALISIS_FINANCIERO_MODULE = { id: 'analisis_financiero', name: 'Análisis Financiero', icon: FaChartArea };
const PH_MODULE = {
    id: 'ph',
    name: 'Propiedad Horizontal',
    icon: FaBuilding,
    links: [
        { name: 'Unidades', href: '/ph/unidades', icon: FaHome },
        { name: 'Propietarios', href: '/ph/propietarios', icon: FaUsers },
        { name: 'Conceptos de Cobro', href: '/ph/conceptos', icon: FaListUl },
        { name: 'Generar Cuentas Cobro', href: '/ph/facturacion', icon: FaFileInvoiceDollar },
        { name: 'Recaudos (Pagos)', href: '/ph/pagos', icon: FaHandshake },
        { name: 'Estado de Cuenta', href: '/ph/estado-cuenta', icon: FaFileContract },
        { name: 'Reportes PH', href: '/ph/reportes', icon: FaChartBar },
        { name: 'Configuración PH', href: '/ph/configuracion', icon: FaCog }
    ]
};
const NOMINA_MODULE = {
    id: 'nomina',
    name: 'Nómina',
    icon: FaUsers,
    links: [
        { name: 'Empleados', href: '/nomina/empleados', icon: FaUsers },
        { name: 'Liquidar Nómina', href: '/nomina/liquidar', icon: FaCalculator },
        { name: 'Desprendibles', href: '/nomina/desprendibles', icon: FaFileAlt },
        { name: 'Configuración (PUC)', href: '/nomina/configuracion', icon: FaCog },
    ]
};

// --- MODULO PRODUCCION (NUEVO) ---
const PRODUCCION_MODULE = {
    id: 'produccion',
    name: 'Producción',
    icon: FaIndustry,
    links: [
        { name: 'Gestión de Recetas', href: '/produccion/recetas', icon: FaListUl },
        { name: 'Órdenes Producción', href: '/produccion/ordenes', icon: FaClipboardList },
    ]
};

const FAVORITOS_MODULE = { id: 'favoritos', name: 'Favoritos', icon: FaStar };

export const menuStructure = [
    // 1. Contabilidad General
    {
        id: 'contabilidad',
        name: 'Contabilidad General',
        icon: FaCalculator,
        links: [
            { name: 'Crear Documento', href: '/contabilidad/documentos', icon: FaFileAlt },
            { name: 'Captura Rápida', href: '/contabilidad/captura-rapida', icon: FaPlus },
            { name: 'Explorador Doc', href: '/contabilidad/explorador', icon: FaBook },
            { name: 'Libro Diario', href: '/contabilidad/reportes/libro-diario', icon: FaBook },
            { name: 'Balance General', href: '/contabilidad/reportes/balance-general', icon: FaBalanceScale },
            { name: 'Estado de Resultados', href: '/contabilidad/reportes/estado-resultados', icon: FaChartBar },
            { name: 'Balance de Prueba', href: '/contabilidad/reportes/balance-de-prueba', icon: FaCheckCircle },
            { name: 'Reporte Auxiliar', href: '/contabilidad/reportes/auxiliar-cuenta', icon: FaFileAlt },
            { name: 'Libros Oficiales (PDF)', href: '/admin/utilidades/libros-oficiales', icon: FaUniversity },
            { name: 'Auditoría Avanzada (Super Informe)', href: '/contabilidad/reportes/super-informe', icon: FaClipboardList },
        ]
    },
    // 2. Análisis Financiero
    ANALISIS_FINANCIERO_MODULE,
    // 3. Centros de Costo
    {
        id: 'centros_costo',
        name: 'Centros de Costo',
        icon: FaChartBar,
        links: [
            { name: 'Gestionar C. de Costo', href: '/admin/centros-costo', icon: FaWrench },
            { name: 'Auxiliar por CC y Cuenta', href: '/contabilidad/reportes/auxiliar-cc-cuenta', icon: FaFileAlt },
            { name: 'Balance General por CC', href: '/contabilidad/reportes/balance-general-cc', icon: FaBalanceScale },
            { name: 'Estado Resultados por CC', href: '/contabilidad/reportes/estado-resultados-cc-detallado', icon: FaChartBar },
            { name: 'Balance de Prueba por CC', href: '/contabilidad/reportes/balance-de-prueba-cc', icon: FaCheckCircle },
        ]
    },
    // 4. Terceros
    {
        id: 'terceros',
        name: 'Terceros',
        icon: FaUsers,
        links: [
            { name: 'Gestionar Terceros', href: '/admin/terceros', icon: FaHandshake },
            { name: 'Auxiliar por Tercero', href: '/contabilidad/reportes/tercero-cuenta', icon: FaFileAlt },
            { name: 'Cartera', href: '/contabilidad/reportes/estado-cuenta-cliente', icon: FaLock },
            { name: 'Auxiliar de Cartera', href: '/contabilidad/reportes/auxiliar-cartera', icon: FaClipboardList },
            { name: 'Proveedores', href: '/contabilidad/reportes/estado-cuenta-proveedor', icon: FaTruckMoving },
            { name: 'Auxiliar Proveedores', href: '/contabilidad/reportes/auxiliar-proveedores', icon: FaReceipt },
        ]
    },
    // 5. Impuestos
    {
        id: 'impuestos',
        name: 'Impuestos',
        icon: FaFileInvoiceDollar,
        route: '/impuestos'
    },
    // 6. Inventarios
    {
        id: 'inventarios',
        name: 'Inventarios',
        icon: FaBoxes,
        links: [
            { name: 'Parámetros Inventario', href: '/admin/inventario/parametros', icon: FaCog },
            { name: 'Gestión de Inventarios', href: '/admin/inventario', icon: FaListUl },
            { name: 'Estado General y Movimientos', href: '/contabilidad/reportes/movimiento-analitico', icon: FaFileAlt },
            { name: 'Relación Documentos Inventarios', href: '/contabilidad/reportes/super-informe-inventarios', icon: FaChartPie },
            { name: 'Traslado Inventarios', href: '/contabilidad/traslados', icon: FaTruckMoving },
            { name: 'Ajuste Inventarios', href: '/admin/inventario/ajuste-inventario', icon: FaWrench },
            { name: '% Gestión de Topes', href: '/contabilidad/reportes/gestion-topes', icon: FaPercentage },
        ]
    },
    // 7. Facturación
    {
        id: 'facturacion',
        name: 'Facturación',
        icon: FaDollarSign,
        links: [
            { name: 'Facturación', href: '/contabilidad/facturacion', icon: FaDollarSign },
            { name: 'Gestión de Remisiones', href: '/remisiones', icon: FaClipboardList },
            { name: 'Reportes Remisiones', href: '/remisiones/reportes', icon: FaChartPie },
            { name: 'Gestión Cotizaciones', href: '/cotizaciones', icon: FaFileInvoiceDollar },
            { name: 'Gestión Compras', href: '/contabilidad/compras', icon: FaReceipt },
            { name: 'Rentabilidad Producto', href: '/contabilidad/reportes/rentabilidad-producto', icon: FaChartLine },
            { name: 'Rentabilidad por Documentos', href: '/contabilidad/reportes/gestion-ventas', icon: FaChartLine },
        ]
    },
    // 8. Activos Fijos
    {
        id: 'activos',
        name: "Activos Fijos (NIIF)",
        icon: FaTractor,
        links: [
            { name: "Listado de Activos", href: "/activos", icon: FaListUl },
            { name: "Categorías y Vidas Útiles", href: "/activos/categorias", icon: FaCogs },
        ]
    },
    // 9. Propiedad Horizontal
    PH_MODULE,
    // 10. Nómina
    NOMINA_MODULE,
    // 11. Producción
    PRODUCCION_MODULE,
    // 12. Administración y Configuración
    {
        id: 'administracion',
        name: 'Administración y Configuración',
        icon: FaCog,
        subgroups: [
            {
                title: 'Parametrización Maestra',
                icon: FaFileContract,
                links: [
                    { name: 'Gestionar PUC', href: '/admin/plan-de-cuentas', icon: FaBook },
                    { name: 'Gestionar Tipos de Doc.', href: '/admin/tipos-documento', icon: FaClipboardList },
                    { name: 'Gestionar Plantillas', href: '/admin/plantillas', icon: FaFileAlt },
                    { name: 'Gestionar Conceptos', href: '/admin/utilidades/gestionar-conceptos', icon: FaListUl },
                    { name: 'Gestionar Empresas', href: '/admin/empresas', icon: FaUniversity },
                ]
            },
            {
                title: 'Control y Cierre',
                icon: FaBook,
                links: [
                    { name: 'Copias y Restauración', href: '/admin/utilidades/migracion-datos', icon: FaRedoAlt },
                    { name: 'Cerrar Periodos Contables', href: '/admin/utilidades/periodos-contables', icon: FaCalendarAlt },
                    { name: 'Auditoría Consecutivos', href: '/admin/utilidades/auditoria-consecutivos', icon: FaCheckCircle },
                ]
            },
            {
                title: 'Herramientas Avanzadas',
                icon: FaWrench,
                links: [
                    { name: 'Gestión Avanzada y Utilitarios', href: '/admin/utilidades/soporte-util', icon: FaTools },
                    { name: 'Edición de Documentos', href: '/admin/utilidades/eliminacion-masiva', icon: FaFileAlt },
                    { name: 'Recodificación Masiva', href: '/admin/utilidades/recodificacion-masiva', icon: FaRedoAlt },
                    { name: 'Papelera de Reciclaje', href: '/admin/utilidades/papelera', icon: FaTimes },
                ]
            },
        ]
    },
    // 13. Favoritos
    FAVORITOS_MODULE,
];
