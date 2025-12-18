import {
    FaCalculator, FaChartBar, FaUsers, FaFileInvoiceDollar, FaBoxes, FaCog,
    FaFileAlt, FaPlus, FaBook, FaBalanceScale, FaCheckCircle, FaUniversity,
    FaClipboardList, FaWrench, FaHandshake, FaTruckMoving, FaReceipt, FaLock,
    FaListUl, FaDollarSign, FaChartLine, FaChartPie, FaPercentage, FaFileContract,
    FaRedoAlt, FaCalendarAlt, FaTools, FaTimes, FaChartArea, FaStar, FaBuilding,
    FaStamp, FaShoppingCart, FaMoneyBillWave, FaTractor, FaCogs, FaHome, FaIndustry
} from 'react-icons/fa';

// Módulos definidos externamente para claridad
const ANALISIS_FINANCIERO_MODULE = { id: 'analisis_financiero', name: 'Análisis Financiero', icon: FaChartArea, description: 'Indicadores financieros y KPIs.' };
const PH_MODULE = {
    id: 'ph',
    name: 'Propiedad Horizontal',
    icon: FaBuilding,
    links: [
        { name: 'Unidades', href: '/ph/unidades', icon: FaHome, description: 'Administrar apartamentos, casas y locales.' },
        { name: 'Propietarios', href: '/ph/propietarios', icon: FaUsers, description: 'Directorio de copropietarios y residentes.' },
        { name: 'Conceptos de Cobro', href: '/ph/conceptos', icon: FaListUl, description: 'Definir cuotas de administración y extras.' },
        { name: 'Generar Cuentas Cobro', href: '/ph/facturacion', icon: FaFileInvoiceDollar, description: 'Generar cuentas de cobro mensuales.' },
        { name: 'Recaudos (Pagos)', href: '/ph/pagos', icon: FaHandshake, description: 'Asentar recaudos de administración.' },
        { name: 'Estado de Cuenta', href: '/ph/estado-cuenta', icon: FaFileContract, description: 'Consultar saldos y descargar paz y salvos.' },
        { name: 'Reportes PH', href: '/ph/reportes', icon: FaChartBar, description: 'Informes financieros y de cartera.' },
        { name: 'Configuración PH', href: '/ph/configuracion', icon: FaCog, description: 'Parámetros generales del conjunto.' }
    ]
};
const NOMINA_MODULE = {
    id: 'nomina',
    name: 'Nómina',
    icon: FaUsers,
    links: [
        { name: 'Empleados', href: '/nomina/empleados', icon: FaUsers, description: 'Gestión de contratos y personal.' },
        { name: 'Liquidar Nómina', href: '/nomina/liquidar', icon: FaCalculator, description: 'Cálculo de devengados y deducciones.' },
        { name: 'Desprendibles', href: '/nomina/desprendibles', icon: FaFileAlt, description: 'Generación de comprobantes de pago.' },
        { name: 'Configuración (PUC)', href: '/nomina/configuracion', icon: FaCog, description: 'Parametrización contable de nómina.' },
    ]
};

// --- MODULO PRODUCCION (NUEVO) ---
const PRODUCCION_MODULE = {
    id: 'produccion',
    name: 'Producción',
    icon: FaIndustry,
    links: [
        { name: 'Gestión de Recetas', href: '/produccion/recetas', icon: FaListUl, description: 'Fórmulas y lista de materiales.' },
        { name: 'Órdenes Producción', href: '/produccion/ordenes', icon: FaClipboardList, description: 'Control de lotes y fabricación.' },
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
            { name: 'Crear Documento', href: '/contabilidad/documentos', icon: FaFileAlt, description: 'Registro de asientos manuales y notas.' },
            { name: 'Captura Rápida', href: '/contabilidad/captura-rapida', icon: FaPlus, description: 'Ingreso ágil de facturas y gastos.' },
            { name: 'Explorador Doc', href: '/contabilidad/explorador', icon: FaBook, description: 'Búsqueda avanzada de movimientos.' },
            { name: 'Libro Diario', href: '/contabilidad/reportes/libro-diario', icon: FaBook, description: 'Movimientos cronológicos por día.' },
            { name: 'Balance General', href: '/contabilidad/reportes/balance-general', icon: FaBalanceScale, description: 'Estado de situación financiera (ESF).' },
            { name: 'Estado de Resultados', href: '/contabilidad/reportes/estado-resultados', icon: FaChartBar, description: 'Pérdidas y Ganancias (PYG).' },
            { name: 'Balance de Prueba', href: '/contabilidad/reportes/balance-de-prueba', icon: FaCheckCircle, description: 'Resumen de saldos débito y crédito.' },
            { name: 'Reporte Auxiliar', href: '/contabilidad/reportes/auxiliar-cuenta', icon: FaFileAlt, description: 'Detalle de movimientos por cuenta.' },
            { name: 'Libros Oficiales (PDF)', href: '/admin/utilidades/libros-oficiales', icon: FaUniversity, description: 'Generación de libros reglamentarios.' },
            { name: 'Auditoría Avanzada (Super Informe)', href: '/contabilidad/reportes/super-informe', icon: FaClipboardList, description: 'Cruce de información y auditoría.' },
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
            { name: 'Gestionar C. de Costo', href: '/admin/centros-costo', icon: FaWrench, description: 'Administración de estructura de costos.' },
            { name: 'Auxiliar por CC y Cuenta', href: '/contabilidad/reportes/auxiliar-cc-cuenta', icon: FaFileAlt, description: 'Movimientos detallados por centro.' },
            { name: 'Balance General por CC', href: '/contabilidad/reportes/balance-general-cc', icon: FaBalanceScale, description: 'Situación financiera segmentada.' },
            { name: 'Estado Resultados por CC', href: '/contabilidad/reportes/estado-resultados-cc-detallado', icon: FaChartBar, description: 'Rentabilidad por centro de costo.' },
            { name: 'Balance de Prueba por CC', href: '/contabilidad/reportes/balance-de-prueba-cc', icon: FaCheckCircle, description: 'Saldos de prueba segmentados.' },
        ]
    },
    // 4. Terceros
    {
        id: 'terceros',
        name: 'Terceros',
        icon: FaUsers,
        links: [
            { name: 'Gestionar Terceros', href: '/admin/terceros', icon: FaHandshake, description: 'Directorio de clientes y proveedores.' },
            { name: 'Auxiliar por Tercero', href: '/contabilidad/reportes/tercero-cuenta', icon: FaFileAlt, description: 'Movimientos por beneficiario.' },
            { name: 'Cartera', href: '/contabilidad/reportes/estado-cuenta-cliente', icon: FaLock, description: 'Cuentas por cobrar a clientes.' },
            { name: 'Auxiliar de Cartera', href: '/contabilidad/reportes/auxiliar-cartera', icon: FaClipboardList, description: 'Detalle de vencimientos cartera.' },
            { name: 'Proveedores', href: '/contabilidad/reportes/estado-cuenta-proveedor', icon: FaTruckMoving, description: 'Cuentas por pagar a proveedores.' },
            { name: 'Auxiliar Proveedores', href: '/contabilidad/reportes/auxiliar-proveedores', icon: FaReceipt, description: 'Detalle de pasivos con terceros.' },
        ]
    },
    // 5. Impuestos
    {
        id: 'impuestos',
        name: 'Impuestos',
        icon: FaFileInvoiceDollar,
        route: '/impuestos',
        description: 'Gestión tributaria y calendario fiscal.'
    },
    // 6. Inventarios
    {
        id: 'inventarios',
        name: 'Inventarios',
        icon: FaBoxes,
        links: [
            { name: 'Parámetros Inventario', href: '/admin/inventario/parametros', icon: FaCog, description: 'Configuración de bodegas y grupos.' },
            { name: 'Gestión de Inventarios', href: '/admin/inventario', icon: FaListUl, description: 'Kardex y control de existencias.' },
            { name: 'Estado General y Movimientos', href: '/contabilidad/reportes/movimiento-analitico', icon: FaFileAlt, description: 'Análisis de rotación y costos.' },
            { name: 'Relación Documentos Inventarios', href: '/contabilidad/reportes/super-informe-inventarios', icon: FaChartPie, description: 'Auditoría de docs de inventario.' },
            { name: 'Traslado Inventarios', href: '/contabilidad/traslados', icon: FaTruckMoving, description: 'Movimientos entre bodegas.' },
            { name: 'Ajuste Inventarios', href: '/admin/inventario/ajuste-inventario', icon: FaWrench, description: 'Corrección manual de stock.' },
            { name: '% Gestión de Topes', href: '/contabilidad/reportes/gestion-topes', icon: FaPercentage, description: 'Control de mínimos y máximos.' },
        ]
    },
    // 7. Facturación
    {
        id: 'facturacion',
        name: 'Facturación',
        icon: FaDollarSign,
        links: [
            { name: 'Facturación', href: '/contabilidad/facturacion', icon: FaDollarSign, description: 'Emisión de facturas de venta.' },
            { name: 'Gestión de Remisiones', href: '/remisiones', icon: FaClipboardList, description: 'Control de despachos sin factura.' },
            { name: 'Reportes Remisiones', href: '/remisiones/reportes', icon: FaChartPie, description: 'Estadísticas de remisiones.' },
            { name: 'Gestión Cotizaciones', href: '/cotizaciones', icon: FaFileInvoiceDollar, description: 'Propuestas comerciales a clientes.' },
            { name: 'Gestión Compras', href: '/contabilidad/compras', icon: FaReceipt, description: 'Registro de facturas de compra.' },
            { name: 'Rentabilidad Producto', href: '/contabilidad/reportes/rentabilidad-producto', icon: FaChartLine, description: 'Margen de ganancia por ítem.' },
            { name: 'Rentabilidad por Documentos', href: '/contabilidad/reportes/gestion-ventas', icon: FaChartLine, description: 'Análisis de utilidad por venta.' },
        ]
    },
    // 8. Activos Fijos
    {
        id: 'activos',
        name: "Activos Fijos (NIIF)",
        icon: FaTractor,
        links: [
            { name: "Listado de Activos", href: "/activos", icon: FaListUl, description: 'Inventario de propiedad, planta y equipo.' },
            { name: "Categorías y Vidas Útiles", href: "/activos/categorias", icon: FaCogs, description: 'Configuración de depreciación.' },
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
                description: 'Configuración fundamental del sistema.',
                links: [
                    { name: 'Gestionar PUC', href: '/admin/plan-de-cuentas', icon: FaBook, description: 'Plan Único de Cuentas.' },
                    { name: 'Gestionar Tipos de Doc.', href: '/admin/tipos-documento', icon: FaClipboardList, description: 'Definición de documentos contables.' },
                    { name: 'Gestionar Plantillas', href: '/admin/plantillas', icon: FaFileAlt, description: 'Modelos de asientos recurrentes.' },
                    { name: 'Gestionar Conceptos', href: '/admin/utilidades/gestionar-conceptos', icon: FaListUl, description: 'Conceptos de facturación/gasto.' },
                    { name: 'Gestionar Empresas', href: '/admin/empresas', icon: FaUniversity, description: 'Datos de la compañía.' },
                ]
            },
            {
                title: 'Control y Cierre',
                icon: FaBook,
                description: 'Procesos de auditoría y cierre.',
                links: [
                    { name: 'Copias y Restauración', href: '/admin/utilidades/migracion-datos', icon: FaRedoAlt, description: 'Backups y migración de datos.' },
                    { name: 'Cerrar Periodos Contables', href: '/admin/utilidades/periodos-contables', icon: FaCalendarAlt, description: 'Bloqueo de meses procesados.' },
                    { name: 'Auditoría Consecutivos', href: '/admin/utilidades/auditoria-consecutivos', icon: FaCheckCircle, description: 'Verificación de secuencia numérica.' },
                ]
            },
            {
                title: 'Herramientas Avanzadas',
                icon: FaWrench,
                description: 'Utilitarios de mantenimiento.',
                links: [
                    { name: 'Gestión Avanzada y Utilitarios', href: '/admin/utilidades/soporte-util', icon: FaTools, description: 'Scripts de corrección de datos.' },
                    { name: 'Edición de Documentos', href: '/admin/utilidades/eliminacion-masiva', icon: FaFileAlt, description: 'Modificación/Eliminación masiva.' },
                    { name: 'Recodificación Masiva', href: '/admin/utilidades/recodificacion-masiva', icon: FaRedoAlt, description: 'Cambio de códigos contables.' },
                    { name: 'Papelera de Reciclaje', href: '/admin/utilidades/papelera', icon: FaTimes, description: 'Restauración de eliminados.' },
                ]
            },
        ]
    },
    // 13. Favoritos
    FAVORITOS_MODULE,
];
