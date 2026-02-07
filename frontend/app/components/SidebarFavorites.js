'use client';
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter, usePathname, useSearchParams } from 'next/navigation';
import {
    FaHistory, FaTrashAlt,
    // Íconos generales importantes
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
    FaTruck, FaHandshake, FaExchangeAlt, FaSync, FaCalendarAlt,
    FaTasks, FaProjectDiagram, FaRoute, FaMapMarkerAlt, FaRedoAlt,
    FaEnvelope, FaPhone, FaFax, FaComments, FaBell, FaNewspaper,
    FaStamp, FaAward, FaMedal, FaTimes, FaClock,
    FaEye, FaEyeSlash,
    FaBuilding, FaStore, FaHome, FaCity, FaGlobe, FaFlag,
    FaLaptop, FaDesktop, FaMobile, FaTablet, FaWifi, FaCloud,
    FaCar, FaMotorcycle, FaBicycle, FaPlane, FaShip, FaTrain,
    FaTractor, FaStar, FaPlus, FaRocket, FaGem, FaBolt, FaMagic
} from 'react-icons/fa';

// --- ICON POOL PARA HASHING ---
const ICON_POOL = [
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

// --- MAPA DE RUTAS CONOCIDAS ---
const MASTER_ICON_MAP = {
    '/contabilidad/documentos': FaFileInvoiceDollar,
    '/contabilidad': FaCalculator,
    '/admin/terceros': FaUsers,
    '/admin/inventario': FaBoxes,
    '/facturacion/crear': FaCashRegister,
    '/facturacion': FaReceipt,
    '/analisis': FaChartBar,
    '/dashboard': FaChartLine,
    '/activos': FaLaptop,
    '/conciliacion-bancaria': FaUniversity,
    '/cotizaciones': FaFileInvoiceDollar,
    '/impuestos': FaPercentage,
    '/nomina': FaUserTie,
    '/ph': FaBuilding,
    '/produccion': FaIndustry,
    '/remisiones': FaTruck,
    '/admin/utilidades/configuracion-correo': FaEnvelope,
};

const getSmartIconForRoute = (route) => {
    if (!route) return FaHistory;

    // Check exact match
    if (MASTER_ICON_MAP[route]) return MASTER_ICON_MAP[route];

    // Check partial match
    const lowerRoute = route.toLowerCase();
    if (lowerRoute.includes('factura')) return FaFileInvoiceDollar;
    if (lowerRoute.includes('inventario')) return FaBoxes;
    if (lowerRoute.includes('terceros')) return FaUsers;
    if (lowerRoute.includes('analisis')) return FaChartBar;
    if (lowerRoute.includes('reporte')) return FaFileAlt;
    if (lowerRoute.includes('config')) return FaCog;
    if (lowerRoute.includes('utilidades')) return FaTools;
    if (lowerRoute.includes('nomina')) return FaUserTie;
    if (lowerRoute.includes('ph')) return FaBuilding;
    if (lowerRoute.includes('activos')) return FaLaptop;
    if (lowerRoute.includes('remision')) return FaTruck;

    // Hash Fallback
    let hash = 0;
    for (let i = 0; i < route.length; i++) {
        hash = route.charCodeAt(i) + ((hash << 5) - hash);
    }
    return ICON_POOL[Math.abs(hash) % ICON_POOL.length];
};

const PATH_NAME_OVERRIDES = {
    '/contabilidad/reportes/super-informe': 'Auditoría Contable Avanzada',
    '/contabilidad/reportes/libro-diario-resumen': 'Libro Diario Oficial',
    '/contabilidad/reportes/libro-diario': 'Libro Diario Detallado',
};

const formatPathName = (path) => {
    if (PATH_NAME_OVERRIDES[path]) return PATH_NAME_OVERRIDES[path];
    if (path === '/') return 'Inicio';
    const parts = path.split('/').filter(Boolean);
    const lastPart = parts[parts.length - 1];
    return lastPart.charAt(0).toUpperCase() + lastPart.slice(1).replace(/-/g, ' ');
};

export default function SidebarFavorites() {
    const router = useRouter();
    const pathname = usePathname();
    const searchParams = useSearchParams();

    // Estado ZenMode
    const isZenMode = pathname === '/' && !searchParams.get('module');

    // Estado Historial
    const [history, setHistory] = useState([]);
    const [isOpen, setIsOpen] = useState(false);

    // Cargar historial inicial
    useEffect(() => {
        const stored = localStorage.getItem('app_history');
        if (stored) {
            try {
                setHistory(JSON.parse(stored));
            } catch (e) {
                console.error("Error parsing history", e);
            }
        }
    }, []);

    // Escuchar cambios de ruta y agregar al historial
    useEffect(() => {
        if (!pathname || pathname === '/' || pathname.includes('login')) return;

        const newItem = {
            path: pathname,
            label: formatPathName(pathname),
            timestamp: Date.now()
        };

        setHistory(prev => {
            // Filtrar si ya existe (para moverlo al principio)
            const filtered = prev.filter(item => item.path !== pathname);
            // Agregar al principio
            const updated = [newItem, ...filtered].slice(0, 8); // Max 8 items

            // Guardar en Storage
            localStorage.setItem('app_history', JSON.stringify(updated));
            return updated;
        });
    }, [pathname]);

    const clearHistory = () => {
        setHistory([]);
        localStorage.removeItem('app_history');
    };

    // Clases CSS
    // Cuando está cerrado en modo normal: w-3 para que sea sutil pero visible
    // Cuando está expandido (isOpen): w-64 para mostrar texto
    const containerClasses = isOpen
        ? 'w-64 opacity-100 shadow-2xl'
        : (isZenMode ? 'w-0 opacity-0 pointer-events-none' : 'w-3 opacity-60 hover:opacity-100 bg-gray-100 hover:bg-white');

    return (
        <>
            {/* Trigger Zone para ZenMode */}
            {(isZenMode && !isOpen) && (
                <div
                    className="fixed left-0 top-0 bottom-0 w-4 z-[49] bg-transparent hover:bg-blue-500/10 cursor-pointer transition-colors"
                    onClick={() => setIsOpen(true)}
                    title="Clic para mostrar Historial"
                />
            )}

            <div
                className={`fixed left-0 top-1/2 -translate-y-1/2 h-auto max-h-[85vh] bg-white rounded-r-2xl border-y border-r border-gray-200 z-50 flex flex-col transition-all duration-300 ease-in-out overflow-hidden group 
                    ${containerClasses}
                `}
                // FIX: Allow clicking the collapsed bar to open it (since hover handlers were removed)
                onClick={() => !isOpen && setIsOpen(true)}
                style={{ minHeight: '100px', cursor: !isOpen ? 'pointer' : 'default' }}
            >
                {/* Banda decorativa (Modo Historia = Verde/Azul) */}
                {(!isOpen && !isZenMode) && (
                    <div className="absolute inset-y-0 left-0 w-full bg-gradient-to-b from-green-400 to-blue-500"></div>
                )}

                <div className={`flex flex-col py-4 h-full overflow-y-auto scrollbar-hide ${isOpen ? 'items-start px-2' : 'items-center'}`}>

                    {/* Título o Icono de Sección */}
                    <div className={`mb-4 flex items-center ${isOpen ? 'w-full justify-between' : 'justify-center'}`}>
                        {isOpen ? (
                            <>
                                <span className="text-gray-500 text-xs font-bold uppercase tracking-widest ml-2">
                                    Historial Reciente
                                </span>
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation(); // Evitar que el click en cerrar reabra el contenedor
                                        setIsOpen(false);
                                    }}
                                    className="p-1 text-gray-400 hover:text-red-500 rounded-full hover:bg-gray-100 transition-colors"
                                    title="Cerrar Barra Lateral"
                                >
                                    <FaTimes />
                                </button>
                            </>
                        ) : (
                            // Texto vertical cuando está cerrado (si cabe) o icono
                            <div className="text-gray-400 text-[10px] font-bold uppercase tracking-widest rotate-[-90deg] h-4 w-4 flex items-center justify-center whitespace-nowrap opacity-50">
                                H
                            </div>
                        )}
                    </div>

                    {isOpen && <div className="w-full h-[1px] bg-gray-100 mb-2"></div>}

                    {/* Lista de Historial */}
                    <div className="w-full flex flex-col gap-2">
                        {history.map((item) => {
                            const IconComponent = getSmartIconForRoute(item.path);
                            // Highlight check
                            const isActive = pathname === item.path;

                            return (
                                <Link
                                    key={item.path}
                                    href={item.path}
                                    onClick={() => setIsOpen(false)}
                                    className={`
                                        flex items-center transition-all duration-200 rounded-xl
                                        ${isOpen
                                            ? 'w-full px-3 py-2 text-sm justify-start space-x-3'
                                            : 'w-10 h-10 justify-center'
                                        }
                                        ${isActive
                                            ? 'bg-blue-50 text-blue-600 ring-1 ring-blue-200 shadow-sm'
                                            : 'bg-transparent text-gray-500 hover:bg-gray-50 hover:text-blue-500' // Estilo más limpio, menos arcoiris
                                        }
                                    `}
                                    title={!isOpen ? item.label : ''}
                                >
                                    <IconComponent className={`${isOpen ? 'text-lg' : 'text-xl'}`} />

                                    {/* Texto Solo Visible si Open */}
                                    {isOpen && (
                                        <span className="font-medium truncate max-w-[160px]">
                                            {PATH_NAME_OVERRIDES[item.path] || item.label}
                                        </span>
                                    )}
                                </Link>
                            );
                        })}
                    </div>

                    {history.length === 0 && (
                        <div className="text-gray-300 text-xs text-center px-1 mt-4">
                            {isOpen ? "No hay historial reciente" : "Vacío"}
                        </div>
                    )}

                    {isOpen && history.length > 0 && (
                        <>
                            <div className="w-full h-[1px] bg-gray-100 my-4"></div>
                            {/* Botón Borrar Historial con Texto */}
                            <button
                                onClick={clearHistory}
                                className="w-full flex items-center px-3 py-2 rounded-xl text-red-400 hover:bg-red-50 hover:text-red-500 transition-colors text-sm group/btn"
                            >
                                <FaTrashAlt className="text-sm mr-3 group-hover/btn:animate-pulse" />
                                <span>Borrar Historial</span>
                            </button>
                        </>
                    )}
                </div>
            </div>
        </>
    );
}

