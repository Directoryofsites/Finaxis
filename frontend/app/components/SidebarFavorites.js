'use client';
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { getFavoritos } from '@/lib/favoritosService';
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
// POOL EXTENSO DE ÍCONOS
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

// LISTA MAESTRA DE ÍCONOS - Copia de la lógica para asegurar consistencia
const MASTER_ICON_MAP = {
    // --- CONTABILIDAD ---
    '/contabilidad/documentos/crear': FaFileAlt,
    '/contabilidad/documentos': FaFileInvoiceDollar,
    '/contabilidad/reportes/balance-prueba': FaBalanceScale,
    '/contabilidad/reportes/libro-diario': FaBook,
    '/contabilidad/reportes/estado-situacion': FaChartBar,
    '/contabilidad/reportes/estado-resultado': FaChartLine,
    '/contabilidad/reportes/movimiento-analitico': FaChartArea,
    '/contabilidad/reportes/estado-resultados-cc-detallado': FaChartPie,
    '/contabilidad/reportes/super-informe': FaRocket,

    // --- TERCEROS ---
    '/admin/terceros': FaUsers,
    '/admin/terceros/crear': FaUserPlus,
    '/cartera/informe-edades': FaClock,
    '/cartera/cuentas-por-cobrar': FaHandshake,

    // --- INVENTARIO ---
    '/admin/inventario/productos': FaBoxes,
    '/admin/inventario/bodegas': FaWarehouse,
    '/admin/inventario/grupos': FaLayerGroup,
    '/admin/inventario/parametros': FaCogs,
    '/admin/inventario': FaBoxes,
    '/inventario/ajuste': FaWrench,
    '/inventario/kardex': FaClipboardList,

    // --- FACTURACIÓN & VENTAS ---
    '/facturacion/crear': FaCashRegister,
    '/facturacion/pos': FaShoppingCart,
    '/facturacion/facturas': FaReceipt,
    '/cotizaciones/crear': FaFileContract,
    '/remisiones/crear': FaTruck,

    // --- PRODUCCIÓN ---
    '/produccion/recetas': FaListUl,
    '/produccion/ordenes': FaIndustry,

    // --- UTILIDADES & ADMIN ---
    '/admin/utilidades/configuracion-favoritos': FaStar,
    '/admin/utilidades/migracion-datos': FaDatabase,
    '/admin/empresas': FaBuilding,
    '/admin/usuarios': FaUserShield,
    '/admin/papelera': FaTimes
};

const getSmartIconForRoute = (route) => {
    if (!route) return ICON_POOL[0];
    const cleanRoute = route.endsWith('/') && route.length > 1 ? route.slice(0, -1) : route;
    if (MASTER_ICON_MAP[cleanRoute]) {
        return MASTER_ICON_MAP[cleanRoute];
    }
    const routeLower = route.toLowerCase();

    // Fallback logic simplificada pero efectiva
    if (routeLower.includes('factur')) return FaFileInvoiceDollar;
    if (routeLower.includes('venta')) return FaDollarSign;
    if (routeLower.includes('compras')) return FaReceipt;
    if (routeLower.includes('inventario')) return FaBoxes;
    if (routeLower.includes('contabil')) return FaCalculator;
    if (routeLower.includes('nomina')) return FaUsers;
    if (routeLower.includes('reporte')) return FaChartBar;

    // Hash fallback
    let hash = 0;
    for (let i = 0; i < route.length; i++) {
        const char = route.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash |= 0;
    }
    const index = Math.abs(hash) % ICON_POOL.length;
    return ICON_POOL[index];
};

export default function SidebarFavorites() {
    const router = useRouter();
    const [favoritos, setFavoritos] = useState([]);
    const [isOpen, setIsOpen] = useState(false);

    const fetchFavs = () => {
        getFavoritos().then(data => {
            if (Array.isArray(data)) {
                setFavoritos(data);
            } else {
                console.warn('Formato de favoritos inesperado:', data);
                setFavoritos([]);
            }
        }).catch(err => {
            console.error(err);
            setFavoritos([]);
        });
    };

    useEffect(() => {
        fetchFavs();

        const handleUpdate = () => fetchFavs();
        window.addEventListener('favoritesUpdated', handleUpdate);
        return () => window.removeEventListener('favoritesUpdated', handleUpdate);
    }, []);

    return (
        <div
            className={`fixed left-0 top-1/2 -translate-y-1/2 h-auto max-h-[80vh] bg-white shadow-2xl rounded-r-2xl border-y border-r border-gray-200 z-50 flex flex-col transition-all duration-300 ease-in-out overflow-hidden group ${isOpen ? 'w-16 opacity-100' : 'w-2 opacity-50 hover:w-16 hover:opacity-100'}`}
            onMouseEnter={() => setIsOpen(true)}
            onMouseLeave={() => setIsOpen(false)}
            style={{ minHeight: '100px' }}
        >
            {/* Banda decorativa cuando está cerrado */}
            {!isOpen && (
                <div className="absolute inset-y-0 left-0 w-1 bg-gradient-to-b from-blue-400 to-purple-500"></div>
            )}

            {/* Contenido del Sidebar */}
            <div className="flex flex-col items-center py-4 w-16 scrollbar-hide overflow-y-auto">

                {/* Botón Configurar (Siempre Primero) */}
                <button
                    onClick={() => router.push('/admin/utilidades/configuracion-favoritos')}
                    className="w-10 h-10 flex items-center justify-center rounded-xl bg-gray-100 text-gray-500 hover:bg-blue-50 hover:text-blue-600 transition-colors mb-2 shadow-sm tooltip tooltip-right"
                    title="Configurar Favoritos"
                >
                    <FaCog className="text-lg" />
                </button>

                <div className="w-8 h-[1px] bg-gray-200 my-2"></div>

                {/* Lista de Favoritos */}
                {Array.isArray(favoritos) && favoritos.map((item) => {
                    const IconComponent = getSmartIconForRoute(item.ruta_enlace);
                    return (
                        <Link
                            key={item.id}
                            href={item.ruta_enlace}
                            className="w-10 h-10 flex items-center justify-center mb-2 rounded-xl text-gray-400 hover:bg-gradient-to-br hover:from-blue-500 hover:to-purple-600 hover:text-white hover:shadow-lg transition-all transform hover:scale-110"
                            title={item.nombre_personalizado}
                        >
                            <IconComponent className="text-lg" />
                        </Link>
                    );
                })}


            </div>
        </div>
    );
}
