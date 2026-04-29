'use client';
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter, usePathname, useSearchParams } from 'next/navigation';
import {
    FaHistory, FaTrashAlt, FaThumbtack, FaRegCircle, FaCheckCircle,
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
    FaColumns, FaClipboardList,
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
import { Reorder, AnimatePresence } from 'framer-motion';

import { menuStructure } from '@/lib/menuData';
import { useAuth } from '@/app/context/AuthContext';

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
// Este mapa se genera dinámicamente desde menuData para asegurar nombres exactos
const getFlattenedMenuMap = () => {
    const map = {};
    if (!menuStructure) return map;
    menuStructure.forEach(module => {
        if (module.links) {
            module.links.forEach(link => {
                map[link.href] = link.name;
            });
        }
        if (module.subgroups) {
            module.subgroups.forEach(sub => {
                if (sub.links) {
                    sub.links.forEach(link => {
                        map[link.href] = link.name;
                    });
                }
            });
        }
    });
    return map;
};

const MENU_NAME_MAP = getFlattenedMenuMap();

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

const formatPathName = (path) => {
    // 1. Prioridad: Nombre exacto del menú oficial
    if (MENU_NAME_MAP[path]) return MENU_NAME_MAP[path];
    
    // 2. Fallback: Formateo básico si no está en el menú
    if (path === '/') return 'Inicio';
    const parts = path.split('/').filter(Boolean);
    const lastPart = parts[parts.length - 1];
    return lastPart.charAt(0).toUpperCase() + lastPart.slice(1).replace(/-/g, ' ');
};

export default function SidebarFavorites() {
    const router = useRouter();
    const pathname = usePathname();
    const searchParams = useSearchParams();
    const { user } = useAuth();

    // Estado ZenMode
    const isZenMode = pathname === '/' && !searchParams.get('module');

    // Llave única por usuario para el almacenamiento local
    const historyKey = user ? `app_history_${user.id || user.username || 'default'}` : null;

    // Estado Historial
    const [history, setHistory] = useState([]);
    const [isOpen, setIsOpen] = useState(false);
    const [isLoaded, setIsLoaded] = useState(false); // Evita sobreescribir antes de cargar

    // Cargar historial inicial cuando cambia el usuario
    useEffect(() => {
        setIsLoaded(false);
        if (!historyKey) {
            setHistory([]);
            return;
        }

        const stored = localStorage.getItem(historyKey);
        if (stored) {
            try {
                setHistory(JSON.parse(stored));
            } catch (e) {
                console.error("Error parsing history", e);
                setHistory([]);
            }
        } else {
            setHistory([]);
        }
        setIsLoaded(true);
    }, [historyKey]);

    // Escuchar cambios de ruta y agregar al historial del usuario actual
    useEffect(() => {
        // Solo procedemos si el historial del usuario ya está cargado para evitar sobreescritura accidental
        if (!pathname || pathname === '/' || pathname.includes('login') || !historyKey || !isLoaded) return;

        setHistory(prev => {
            const itemExists = prev.find(item => item.path === pathname);
            
            // Si el item ya está pineado, no movemos su posición
            if (itemExists?.isPinned) return prev;

            const newItem = {
                path: pathname,
                label: formatPathName(pathname),
                timestamp: Date.now(),
                isPinned: false
            };

            const filtered = prev.filter(item => item.path !== pathname);
            const pinned = filtered.filter(i => i.isPinned);
            const unpinned = filtered.filter(i => !i.isPinned);

            // Las nuevas visitas van al principio de la sección NO pineada
            const updated = [...pinned, newItem, ...unpinned].slice(0, 21);

            localStorage.setItem(historyKey, JSON.stringify(updated));
            return updated;
        });
    }, [pathname, historyKey, isLoaded]);

    const togglePin = (e, path) => {
        e.preventDefault();
        e.stopPropagation();

        setHistory(prev => {
            const updated = prev.map(item =>
                item.path === path ? { ...item, isPinned: !item.isPinned } : item
            );

            // Re-ordenar: Pineados arriba, Recientes abajo (ordenados por timestamp)
            const pinned = updated.filter(i => i.isPinned);
            const unpinned = updated.filter(i => !i.isPinned).sort((a, b) => b.timestamp - a.timestamp);

            const final = [...pinned, ...unpinned];
            if (historyKey) localStorage.setItem(historyKey, JSON.stringify(final));
            return final;
        });
    };

    const handleReorder = (newOrder) => {
        // Solo permitimos reordenar si se respeta la lógica de pineados
        // Aunque framer-motion reordenará todo, nosotros guardamos el estado
        setHistory(newOrder);
        if (historyKey) localStorage.setItem(historyKey, JSON.stringify(newOrder));
    };

    const openAllPinned = () => {
        const pinned = history.filter(i => i.isPinned);
        pinned.forEach(item => {
            window.open(item.path, '_blank');
        });
    };

    const clearHistory = () => {
        // Mantener solo los pineados si el usuario borra el historial
        setHistory(prev => {
            const pinned = prev.filter(i => i.isPinned);
            if (historyKey) localStorage.setItem(historyKey, JSON.stringify(pinned));
            return pinned;
        });
    };

    // Clases CSS
    const containerClasses = isOpen
        ? 'min-w-[900px] w-max max-w-[98vw] opacity-100 shadow-2xl'
        : (isZenMode ? 'w-0 opacity-0 pointer-events-none' : 'w-3 opacity-60 hover:opacity-100 bg-gray-100 hover:bg-white');

    const pinnedCount = history.filter(i => i.isPinned).length;

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
                className={`fixed left-0 top-1/2 -translate-y-1/2 h-auto max-h-[92vh] bg-white rounded-r-2xl border-y border-r border-gray-200 z-50 flex flex-col transition-all duration-300 ease-in-out overflow-hidden group 
                    ${containerClasses}
                `}
                onClick={() => !isOpen && setIsOpen(true)}
                style={{ minHeight: '100px', cursor: !isOpen ? 'pointer' : 'default' }}
            >
                {/* Banda decorativa */}
                {(!isOpen && !isZenMode) && (
                    <div className="absolute inset-y-0 left-0 w-full bg-gradient-to-b from-green-400 to-blue-500"></div>
                )}

                <div className={`flex flex-col py-4 h-full overflow-y-auto scrollbar-hide ${isOpen ? 'items-start px-6' : 'items-center'}`}>

                    {/* Cabecera */}
                    <div className={`mb-4 flex items-center ${isOpen ? 'w-full justify-between' : 'justify-center'}`}>
                        {isOpen ? (
                            <>
                                <div className="flex items-center space-x-3">
                                    <div className="w-8 h-8 rounded-lg bg-blue-500 flex items-center justify-center text-white shadow-lg shadow-blue-200">
                                        <FaHistory className="text-sm" />
                                    </div>
                                    <div>
                                        <span className="text-gray-800 text-sm font-bold block leading-none">Mi Historial Personal</span>
                                        <span className="text-gray-400 text-[10px] font-medium uppercase tracking-tighter">Acceso Rápido Inteligente</span>
                                    </div>
                                </div>
                                <div className="flex items-center space-x-2">
                                    {pinnedCount > 0 && (
                                        <button
                                            onClick={openAllPinned}
                                            className="flex items-center px-3 py-1.5 bg-blue-600 text-white rounded-lg text-[11px] font-bold hover:bg-blue-700 transition-all shadow-sm hover:shadow-blue-200"
                                            title="Abrir todos los fijos en pestañas nuevas"
                                        >
                                            <FaRocket className="mr-2 text-[10px]" />
                                            LANZAR FIJOS
                                        </button>
                                    )}
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            setIsOpen(false);
                                        }}
                                        className="p-2 text-gray-400 hover:text-red-500 rounded-xl hover:bg-red-50 transition-all"
                                    >
                                        <FaTimes />
                                    </button>
                                </div>
                            </>
                        ) : (
                            <div className="text-gray-400 text-[10px] font-bold uppercase tracking-widest rotate-[-90deg] h-4 w-4 flex items-center justify-center whitespace-nowrap opacity-50">
                                H
                            </div>
                        )}
                    </div>

                    {isOpen && <div className="w-full h-[1px] bg-gray-100 mb-6"></div>}

                    {/* Lista de Historial con Reorder */}
                    {isOpen ? (
                        <Reorder.Group
                            axis="y"
                            values={history}
                            onReorder={handleReorder}
                            className="w-full grid grid-cols-3 gap-x-8 gap-y-3"
                        >
                            <AnimatePresence>
                                {history.map((item) => {
                                    const IconComponent = getSmartIconForRoute(item.path);
                                    const isActive = pathname === item.path;

                                    return (
                                        <Reorder.Item
                                            key={item.path}
                                            value={item}
                                            drag={item.isPinned} // Solo se pueden arrastrar los pineados
                                            className="relative"
                                        >
                                            <div
                                                className={`
                                                    group/item flex items-center transition-all duration-200 rounded-xl border relative
                                                    w-full px-4 py-2.5 text-[13px] justify-start space-x-3 cursor-pointer
                                                    ${isActive
                                                        ? 'bg-blue-50 text-blue-600 border-blue-200 shadow-sm'
                                                        : 'bg-white text-gray-600 border-gray-100 hover:border-blue-300 hover:shadow-md'
                                                    }
                                                    ${item.isPinned ? 'ring-1 ring-amber-100 bg-amber-50/30' : ''}
                                                `}
                                                onClick={() => {
                                                    router.push(item.path);
                                                    setIsOpen(false);
                                                }}
                                            >
                                                <IconComponent className={`text-lg flex-shrink-0 ${isActive ? 'text-blue-500' : 'text-gray-400 group-hover/item:text-blue-500'}`} />
                                                
                                                <span className={`font-semibold whitespace-nowrap flex-grow ${isActive ? 'text-blue-700' : 'text-gray-700'}`}>
                                                    {item.label}
                                                </span>

                                                {/* Botón de Fijar (Pin) */}
                                                <button
                                                    onClick={(e) => togglePin(e, item.path)}
                                                    className={`
                                                        p-1.5 rounded-lg transition-all
                                                        ${item.isPinned 
                                                            ? 'text-amber-500 bg-amber-100' 
                                                            : 'text-gray-300 opacity-0 group-hover/item:opacity-100 hover:bg-blue-50 hover:text-blue-500'
                                                        }
                                                    `}
                                                    title={item.isPinned ? "Desprender (Volver a recientes)" : "Inmovilizar en el historial"}
                                                >
                                                    <FaThumbtack className={`text-[10px] ${item.isPinned ? 'rotate-0' : 'rotate-45'}`} />
                                                </button>
                                            </div>
                                        </Reorder.Item>
                                    );
                                })}
                            </AnimatePresence>
                        </Reorder.Group>
                    ) : (
                        <div className="flex flex-col gap-2">
                            {history.map((item) => {
                                const IconComponent = getSmartIconForRoute(item.path);
                                return (
                                    <div
                                        key={item.path}
                                        className="w-10 h-10 flex items-center justify-center rounded-xl bg-white border border-gray-100 text-gray-400"
                                    >
                                        <IconComponent className="text-xl" />
                                    </div>
                                );
                            })}
                        </div>
                    )}

                    {history.length === 0 && (
                        <div className="w-full flex flex-col items-center justify-center py-10 text-gray-400 space-y-2">
                            <FaHistory className="text-3xl opacity-20" />
                            <span className="text-xs font-medium italic">No has visitado páginas aún</span>
                        </div>
                    )}

                    {isOpen && history.length > 0 && (
                        <>
                            <div className="w-full h-[1px] bg-gray-100 my-6"></div>
                            <div className="w-full flex items-center justify-between px-2">
                                <p className="text-[10px] text-gray-400 font-medium italic">
                                    {pinnedCount} fijados • {history.filter(i => !i.isPinned).length} recientes
                                </p>
                                <button
                                    onClick={clearHistory}
                                    className="flex items-center px-3 py-2 rounded-xl text-gray-400 hover:bg-red-50 hover:text-red-500 transition-all text-xs group/btn"
                                >
                                    <FaTrashAlt className="mr-2 group-hover/btn:animate-bounce" />
                                    <span>Limpiar Recientes</span>
                                </button>
                            </div>
                        </>
                    )}
                </div>
            </div>
        </>
    );
}

