import React, { useMemo } from 'react';
import Link from 'next/link';
// BIBLIOTECA EXTENSA DE ÍCONOS ESPECÍFICOS - IGUAL QUE EN MENUDATA.JS
import {
    FaPlus, FaCog, FaRocket, FaGem, FaBolt, FaMagic,
    // ÍCONOS ESPECÍFICOS DE TU APLICACIÓN
    FaCalculator, FaChartBar, FaUsers, FaFileInvoiceDollar, FaBoxes,
    FaFileAlt, FaBook, FaBalanceScale, FaCheckCircle, FaUniversity,
    FaClipboardList, FaWrench, FaHandshake, FaTruckMoving, FaReceipt, FaLock,
    FaListUl, FaDollarSign, FaChartLine, FaChartPie, FaPercentage, FaFileContract,
    FaRedoAlt, FaCalendarAlt, FaTools, FaTimes, FaChartArea, FaStar, FaBuilding,
    FaStamp, FaShoppingCart, FaMoneyBillWave, FaTractor, FaCogs, FaHome, FaIndustry,
    // ÍCONOS ADICIONALES ESPECÍFICOS
    FaMoneyBill, FaCoins, FaCreditCard, FaWallet, FaCashRegister,
    FaLandmark, FaPiggyBank, FaCubes, FaWarehouse, FaTags, FaBarcode, FaLayerGroup,
    FaClipboardCheck, FaListAlt, FaSort, FaUserTie, FaUserFriends, FaUserCheck,
    FaUserPlus, FaUserEdit, FaIdCard, FaAddressCard, FaUserClock, FaUserShield, FaUserTag,
    FaFilePdf, FaPrint, FaSearch, FaFilter, FaDatabase, FaTable, FaColumns,
    FaKey, FaShieldAlt, FaServer, FaPlug, FaToggleOn, FaToggleOff, FaAdjust,
    FaTruck, FaExchangeAlt, FaSync, FaHistory, FaTasks, FaProjectDiagram, FaRoute, FaMapMarkerAlt,
    FaEnvelope, FaPhone, FaFax, FaComments, FaBell, FaNewspaper, FaAward, FaMedal,
    FaClock, FaEye, FaEyeSlash, FaStore, FaCity, FaGlobe, FaFlag,
    FaLaptop, FaDesktop, FaMobile, FaTablet, FaWifi, FaCloud,
    FaCar, FaMotorcycle, FaBicycle, FaPlane, FaShip, FaTrain
} from 'react-icons/fa';

// Límite expandido a 24 botones
const MAX_FAVORITOS = 24;

// POOL EXTENSO DE ÍCONOS - Mantenido igual
const ICON_POOL = [
    // ... (Mismo pool que antes, no lo repetiré todo para ahorrar espacio si no cambió la lógica, pero lo incluyo para integridad)
    FaFileInvoiceDollar, FaDollarSign, FaReceipt, FaMoneyBillWave, FaCoins, FaCreditCard,
    FaShoppingCart, FaCashRegister, FaWallet, FaFileContract,
    FaCalculator, FaBalanceScale, FaChartLine, FaChartPie, FaChartBar, FaChartArea,
    FaUniversity, FaLandmark, FaPiggyBank, FaMoneyBill, FaPercentage, FaBook,
    FaBoxes, FaCubes, FaWarehouse, FaTags, FaBarcode, FaLayerGroup,
    FaIndustry, FaClipboardCheck, FaListUl, FaSort, FaTruckMoving,
    FaUsers, FaUserTie, FaUserFriends, FaUserCheck, FaUserPlus, FaUserEdit,
    FaIdCard, FaAddressCard, FaUserClock, FaUserShield, FaUserTag,
    FaFileAlt, FaFilePdf, FaPrint, FaSearch, FaFilter, FaDatabase, FaTable,
    FaColumns, FaClipboardList, FaCheckCircle,
    FaCog, FaCogs, FaTools, FaWrench, FaKey, FaShieldAlt, FaLock,
    FaServer, FaPlug, FaToggleOn, FaToggleOff, FaAdjust,
    FaTruck, FaHandshake, FaExchangeAlt, FaSync, FaHistory, FaCalendarAlt,
    FaTasks, FaProjectDiagram, FaRoute, FaMapMarkerAlt, FaRedoAlt,
    FaEnvelope, FaPhone, FaFax, FaComments, FaBell, FaNewspaper,
    FaStamp, FaAward, FaMedal, FaTimes,
    FaClock, FaCalendarAlt,
    FaEye, FaEyeSlash, FaLock,
    FaBuilding, FaStore, FaHome, FaCity, FaGlobe, FaFlag,
    FaLaptop, FaDesktop, FaMobile, FaTablet, FaWifi, FaCloud,
    FaCar, FaMotorcycle, FaBicycle, FaPlane, FaShip, FaTrain,
    FaTractor,
    FaStar, FaPlus, FaRocket, FaGem, FaBolt, FaMagic
];

// FUNCIÓN INTELIGENTE: Mapeo específico por funcionalidad real
const getSmartIconForRoute = (route) => {
    if (!route) return ICON_POOL[0];
    const routeLower = route.toLowerCase();

    // Lógica de mapeo de íconos (Idéntica a la anterior - abreviada donde posible)
    if (routeLower.includes('factur') || routeLower.includes('invoice')) return FaFileInvoiceDollar;
    if (routeLower.includes('venta') || routeLower.includes('sale')) return FaDollarSign;
    if (routeLower.includes('cotiz') || routeLower.includes('quote')) return FaFileInvoiceDollar;
    if (routeLower.includes('pos') || routeLower.includes('caja')) return FaCashRegister;
    if (routeLower.includes('recibo') || routeLower.includes('receipt')) return FaReceipt;
    if (routeLower.includes('devolucion') || routeLower.includes('return')) return FaExchangeAlt;

    if (routeLower.includes('compra') || routeLower.includes('purchase')) return FaReceipt;
    if (routeLower.includes('proveedor') || routeLower.includes('supplier')) return FaTruckMoving;
    if (routeLower.includes('orden') && routeLower.includes('compra')) return FaClipboardList;
    if (routeLower.includes('solicitud')) return FaFileContract;

    if (routeLower.includes('inventario') || routeLower.includes('inventory')) return FaBoxes;
    if (routeLower.includes('producto') || routeLower.includes('product')) return FaCubes;
    if (routeLower.includes('bodega') || routeLower.includes('warehouse')) return FaWarehouse;
    if (routeLower.includes('stock') || routeLower.includes('existencia')) return FaLayerGroup;
    if (routeLower.includes('codigo') && routeLower.includes('barra')) return FaBarcode;
    if (routeLower.includes('categoria')) return FaTags;
    if (routeLower.includes('ajuste') && routeLower.includes('inventario')) return FaWrench;
    if (routeLower.includes('traslado') || routeLower.includes('transfer')) return FaTruckMoving;
    if (routeLower.includes('conteo') || routeLower.includes('count')) return FaSort;

    if (routeLower.includes('contabil') || routeLower.includes('account')) return FaCalculator;
    if (routeLower.includes('balance') && routeLower.includes('general')) return FaBalanceScale;
    if (routeLower.includes('estado') && routeLower.includes('resultado')) return FaChartBar;
    if (routeLower.includes('libro') && routeLower.includes('diario')) return FaBook;
    if (routeLower.includes('plan') && routeLower.includes('cuenta')) return FaBook;
    if (routeLower.includes('asiento') || routeLower.includes('entry')) return FaFileAlt;
    if (routeLower.includes('auxiliar')) return FaFileAlt;
    if (routeLower.includes('mayor')) return FaDatabase;
    if (routeLower.includes('cierre') || routeLower.includes('close')) return FaCalendarAlt;

    if (routeLower.includes('nomina') || routeLower.includes('payroll')) return FaUsers;
    if (routeLower.includes('empleado') || routeLower.includes('employee')) return FaUsers;
    if (routeLower.includes('liquidacion') || routeLower.includes('settlement')) return FaCalculator;
    if (routeLower.includes('vacacion') || routeLower.includes('vacation')) return FaCalendarAlt;
    if (routeLower.includes('incapacidad') || routeLower.includes('disability')) return FaUserClock;
    if (routeLower.includes('cesantia') || routeLower.includes('severance')) return FaPiggyBank;
    if (routeLower.includes('prestacion') || routeLower.includes('benefit')) return FaAward;

    if (routeLower.includes('cliente') || routeLower.includes('customer')) return FaUsers;
    if (routeLower.includes('cartera') || routeLower.includes('portfolio')) return FaLock;
    if (routeLower.includes('credito') || routeLower.includes('credit')) return FaCreditCard;
    if (routeLower.includes('cobro') || routeLower.includes('collection')) return FaDollarSign;
    if (routeLower.includes('mora') || routeLower.includes('overdue')) return FaClock;

    if (routeLower.includes('pago') || routeLower.includes('payment')) return FaCreditCard;
    if (routeLower.includes('banco') || routeLower.includes('bank')) return FaUniversity;
    if (routeLower.includes('cheque') || routeLower.includes('check')) return FaDollarSign;
    if (routeLower.includes('transferencia') || routeLower.includes('wire')) return FaExchangeAlt;
    if (routeLower.includes('efectivo') || routeLower.includes('cash')) return FaMoneyBillWave;
    if (routeLower.includes('conciliacion') || routeLower.includes('reconciliation')) return FaBalanceScale;

    if (routeLower.includes('impuesto') || routeLower.includes('tax')) return FaFileInvoiceDollar;
    if (routeLower.includes('iva') || routeLower.includes('vat')) return FaChartPie;
    if (routeLower.includes('renta') || routeLower.includes('income')) return FaMoneyBillWave;
    if (routeLower.includes('retencion') || routeLower.includes('withholding')) return FaDollarSign;
    if (routeLower.includes('industria') && routeLower.includes('comercio')) return FaIndustry;
    if (routeLower.includes('timbre') || routeLower.includes('stamp')) return FaStamp;
    if (routeLower.includes('consumo') || routeLower.includes('consumption')) return FaShoppingCart;
    if (routeLower.includes('calendario') && routeLower.includes('obligacion')) return FaCalendarAlt;
    if (routeLower.includes('declaracion') || routeLower.includes('declaration')) return FaFileContract;
    if (routeLower.includes('dian') || routeLower.includes('tax-authority')) return FaLandmark;

    if (routeLower.includes('reporte') || routeLower.includes('report')) return FaChartBar;
    if (routeLower.includes('grafico') || routeLower.includes('chart')) return FaChartLine;
    if (routeLower.includes('dashboard') || routeLower.includes('inicio')) return FaChartPie;
    if (routeLower.includes('excel') || routeLower.includes('xlsx')) return FaTable;
    if (routeLower.includes('pdf')) return FaFilePdf;
    if (routeLower.includes('imprimir') || routeLower.includes('print')) return FaPrint;
    if (routeLower.includes('exportar') || routeLower.includes('export')) return FaFileAlt;
    if (routeLower.includes('estadistica') || routeLower.includes('statistics')) return FaChartBar;
    if (routeLower.includes('super') && routeLower.includes('informe')) return FaClipboardList;

    if (routeLower.includes('config') || routeLower.includes('setting')) return FaCog;
    if (routeLower.includes('usuario') || routeLower.includes('user')) return FaUserEdit;
    if (routeLower.includes('permiso') || routeLower.includes('permission')) return FaKey;
    if (routeLower.includes('rol') || routeLower.includes('role')) return FaUserShield;
    if (routeLower.includes('empresa') || routeLower.includes('company')) return FaUniversity;
    if (routeLower.includes('sucursal') || routeLower.includes('branch')) return FaStore;
    if (routeLower.includes('backup') || routeLower.includes('respaldo')) return FaRedoAlt;
    if (routeLower.includes('log') || routeLower.includes('auditoria')) return FaCheckCircle;
    if (routeLower.includes('seguridad') || routeLower.includes('security')) return FaShieldAlt;
    if (routeLower.includes('papelera') || routeLower.includes('elimina')) return FaTimes;
    if (routeLower.includes('utilidades') || routeLower.includes('herramientas')) return FaTools;

    if (routeLower.includes('activo') && routeLower.includes('fijo')) return FaTractor;
    if (routeLower.includes('depreciacion') || routeLower.includes('depreciation')) return FaChartLine;
    if (routeLower.includes('mantenimiento') || routeLower.includes('maintenance')) return FaWrench;
    if (routeLower.includes('vehiculo') || routeLower.includes('vehicle')) return FaCar;
    if (routeLower.includes('maquinaria') || routeLower.includes('machinery')) return FaIndustry;
    if (routeLower.includes('equipo') || routeLower.includes('equipment')) return FaLaptop;

    if (routeLower.includes('propiedad') && routeLower.includes('horizontal')) return FaBuilding;
    if (routeLower.includes('administracion') && routeLower.includes('conjunto')) return FaBuilding;
    if (routeLower.includes('cuota') && routeLower.includes('administracion')) return FaMoneyBill;
    if (routeLower.includes('propietario') || routeLower.includes('owner')) return FaUsers;
    if (routeLower.includes('unidades') || routeLower.includes('unidad')) return FaHome;

    if (routeLower.includes('remision') || routeLower.includes('delivery')) return FaClipboardList;
    if (routeLower.includes('transporte') || routeLower.includes('transport')) return FaTruck;
    if (routeLower.includes('ruta') || routeLower.includes('route')) return FaRoute;
    if (routeLower.includes('conductor') || routeLower.includes('driver')) return FaUserTie;

    if (routeLower.includes('produccion') || routeLower.includes('production')) return FaIndustry;
    if (routeLower.includes('receta') || routeLower.includes('recipe')) return FaListUl;
    if (routeLower.includes('orden') && routeLower.includes('produccion')) return FaClipboardList;

    let hash = 0;
    for (let i = 0; i < route.length; i++) {
        const char = route.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash |= 0;
    }
    const index = Math.abs(hash) % ICON_POOL.length;
    return ICON_POOL[index];
};



const QuickAccessGrid = ({ favoritos, router }) => {

    // Rellenar la lista de favoritos con placeholders hasta 24
    const accessItems = useMemo(() => {
        const items = [...favoritos];
        while (items.length < MAX_FAVORITOS) {
            items.push(null);
        }
        return items;
    }, [favoritos]);

    return (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 mb-8">

            {/* ENCABEZADO - Estilo Plataforma (Limpio) */}
            <div className="flex justify-between items-center mb-6 pb-4 border-b border-gray-100">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-50 rounded-lg text-blue-600">
                        <FaRocket className="text-xl" />
                    </div>
                    <div>
                        <h3 className="text-xl font-bold text-gray-800">
                            Accesos Rápidos
                        </h3>
                        <p className="text-xs text-gray-500">
                            Organiza tus herramientas frecuentes
                        </p>
                    </div>
                </div>

                <button
                    onClick={() => router.push('/admin/utilidades/configuracion-favoritos')}
                    className="flex items-center gap-2 px-4 py-2 bg-gray-50 hover:bg-gray-100 text-gray-600 rounded-lg transition-colors text-sm font-medium border border-gray-200"
                >
                    <FaCog />
                    <span className="hidden sm:inline">Personalizar</span>
                </button>
            </div>

            {/* GRID FIJO - 8 COLUMNAS */}
            <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 gap-3">
                {accessItems.map((item, index) => {
                    const isConfigured = item !== null;

                    if (isConfigured) {
                        const IconComponent = getSmartIconForRoute(item.ruta_enlace);
                        return (
                            <Link
                                key={item.id}
                                href={item.ruta_enlace}
                                className="group block h-full"
                                title={item.nombre_personalizado}
                            >
                                <div className="
                                    flex flex-col items-center justify-center p-3 h-28
                                    bg-white border border-gray-200 rounded-lg
                                    hover:border-blue-300 hover:shadow-md hover:bg-blue-50/10
                                    transition-all duration-200 w-full cursor-pointer
                                ">
                                    {/* Ícono Sólido (Estilo Plataforma: Fondo Blanco, Icono Verde -> Azul en Hover) */}
                                    <div className="w-10 h-10 flex items-center justify-center bg-white border border-gray-100 shadow-sm text-green-600 group-hover:text-blue-600 rounded-lg mb-2 transition-all duration-300 group-hover:scale-110 group-hover:shadow-md">
                                        <IconComponent size={20} />
                                    </div>

                                    {/* Nombre (Fuente Inter/Sans estándar) */}
                                    <span className="text-xs font-semibold text-gray-600 text-center leading-tight line-clamp-2 group-hover:text-gray-900 px-1">
                                        {item.nombre_personalizado}
                                    </span>
                                </div>
                            </Link>
                        );
                    } else {
                        // Placeholder
                        return (
                            <button
                                key={`placeholder-${index}`}
                                onClick={() => router.push('/admin/utilidades/configuracion-favoritos')}
                                className="
                                    flex flex-col items-center justify-center p-3 h-28
                                    bg-gray-50/50 border-2 border-dashed border-gray-200 rounded-lg
                                    text-gray-300 hover:text-gray-400 hover:border-gray-300 hover:bg-gray-50
                                    transition-all duration-200 w-full
                                "
                                title="Añadir acceso rápido"
                            >
                                <div className="w-10 h-10 flex items-center justify-center bg-gray-100 rounded-lg mb-2">
                                    <FaPlus size={14} />
                                </div>
                                <span className="text-xs font-medium text-gray-400">
                                    Añadir
                                </span>
                            </button>
                        );
                    }
                })}
            </div>

            {/* Empty State Simplificado */}
            {favoritos.length === 0 && (
                <div className="mt-4 text-center text-xs text-gray-400 py-4 bg-gray-50 rounded border border-dashed border-gray-200">
                    Configura tus accesos favoritos para verlos aquí.
                </div>
            )}
        </div>
    );
};

export default QuickAccessGrid;