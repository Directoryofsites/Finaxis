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

    // Hash Fallback
    let hash = 0;
    for (let i = 0; i < route.length; i++) {
        hash = route.charCodeAt(i) + ((hash << 5) - hash);
    }
    return ICON_POOL[Math.abs(hash) % ICON_POOL.length];
};

const formatPathName = (path) => {
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
    const closedClass = isZenMode ? 'w-0 opacity-0 pointer-events-none' : 'w-2 opacity-50 hover:w-16 hover:opacity-100';

    return (
        <>
            {/* Trigger Zone para ZenMode */}
            {(isZenMode && !isOpen) && (
                <div
                    className="fixed left-0 top-0 bottom-0 w-4 z-[49] bg-transparent hover:bg-transparent cursor-pointer"
                    onMouseEnter={() => setIsOpen(true)}
                    title="Mostrar Historial"
                />
            )}

            <div
                className={`fixed left-0 top-1/2 -translate-y-1/2 h-auto max-h-[80vh] bg-white shadow-2xl rounded-r-2xl border-y border-r border-gray-200 z-50 flex flex-col transition-all duration-300 ease-in-out overflow-hidden group 
                    ${isOpen ? 'w-16 opacity-100' : closedClass}
                `}
                onMouseEnter={() => setIsOpen(true)}
                onMouseLeave={() => setIsOpen(false)}
                style={{ minHeight: '100px' }}
            >
                {/* Banda decorativa (Modo Historia = Verde/Azul) */}
                {(!isOpen && !isZenMode) && (
                    <div className="absolute inset-y-0 left-0 w-1 bg-gradient-to-b from-green-400 to-blue-500"></div>
                )}

                <div className="flex flex-col items-center py-4 w-16 scrollbar-hide overflow-y-auto">

                    {/* Título o Icono de Sección */}
                    <div className="mb-2 text-gray-400 text-xs font-bold uppercase tracking-widest rotate-[-90deg] h-4 w-4 flex items-center justify-center whitespace-nowrap opacity-50">
                        Historial
                    </div>

                    <div className="w-8 h-[1px] bg-gray-200 mb-2"></div>

                    {/* Lista de Historial */}
                    {history.map((item) => {
                        const IconComponent = getSmartIconForRoute(item.path);
                        return (
                            <Link
                                key={item.path}
                                href={item.path}
                                className={`w-10 h-10 flex items-center justify-center mb-2 rounded-xl transition-all transform hover:scale-110 shadow-sm
                                    ${pathname === item.path
                                        ? 'bg-blue-100 text-blue-600 ring-2 ring-blue-300'
                                        : 'bg-white text-gray-400 hover:bg-gradient-to-br hover:from-green-400 hover:to-blue-500 hover:text-white hover:shadow-lg'
                                    }
                                `}
                                title={`Ir a: ${item.label}`}
                            >
                                <IconComponent className="text-lg" />
                            </Link>
                        );
                    })}

                    {history.length === 0 && (
                        <div className="text-gray-300 text-xs text-center px-1">
                            Vacío
                        </div>
                    )}

                    <div className="w-8 h-[1px] bg-gray-200 my-2"></div>

                    {/* Botón Borrar Historial */}
                    {history.length > 0 && (
                        <button
                            onClick={clearHistory}
                            className="w-8 h-8 flex items-center justify-center rounded-full bg-gray-50 text-gray-400 hover:bg-red-50 hover:text-red-500 transition-colors"
                            title="Borrar Historial"
                        >
                            <FaTrashAlt className="text-xs" />
                        </button>
                    )}

                </div>
            </div>
        </>
    );
}
