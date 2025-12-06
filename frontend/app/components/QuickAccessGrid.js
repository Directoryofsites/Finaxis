import React, { useMemo } from 'react';
import Link from 'next/link';
// Pool de 16+ iconos ÚNICOS y variados
import { 
    FaPlus, FaTools, FaFileAlt, FaLock, FaBoxes, FaChartLine, FaListUl, 
    FaUniversity, FaBook, FaReceipt, FaTruckMoving, FaMoneyBill, FaDollarSign, 
    FaStar, FaChartPie, FaRedoAlt, FaBalanceScale, FaPercentage, FaChartBar, 
    FaWrench, FaCog, FaMoneyCheckAlt, FaFileContract, FaCalendarAlt, FaCheckCircle, 
    FaSkullCrossbones, FaTags, FaSearch, FaCubes, FaHandHoldingUsd, FaArchive, 
    FaHistory, FaUsers, FaClipboardList, FaFileInvoiceDollar, FaGavel, FaDatabase, FaClipboardCheck,
    FaRegWindowMaximize, FaSortNumericUp
} from 'react-icons/fa';

// Límite ampliado a 16.
const MAX_FAVORITOS = 16; 

// POOL DE ÍCONOS ÚNICOS
const ICON_POOL = [
    FaFileInvoiceDollar, FaReceipt, FaHandHoldingUsd, FaTruckMoving, FaTags, 
    FaBook, FaBalanceScale, FaChartBar, FaSearch, FaWrench,
    FaCubes, FaArchive, FaCalendarAlt, FaDatabase, FaClipboardCheck,
    FaUsers, FaFileAlt, FaChartLine, FaMoneyBill, FaRedoAlt,
    FaGavel, FaRegWindowMaximize, FaSortNumericUp, FaChartPie
];

// FUNCIÓN RECTORA: Garantiza un ícono único para cada ruta usando un hash simple.
const getUniqueIconForRoute = (route) => {
    let hash = 0;
    if (route.length === 0) return ICON_POOL[0];
    for (let i = 0; i < route.length; i++) {
        const char = route.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash |= 0; 
    }
    const index = Math.abs(hash) % ICON_POOL.length;
    return ICON_POOL[index];
};

const QuickAccessGrid = ({ favoritos, router }) => {
    
    // Rellenar la lista de favoritos con placeholders
    const accessItems = useMemo(() => {
        const items = [...favoritos];
        while (items.length < MAX_FAVORITOS) {
            items.push(null); 
        }
        return items;
    }, [favoritos]);

    return (
        <div className="bg-white p-6 rounded-xl shadow-lg border border-gray-100 mb-8 animate-fadeIn">
            
            {/* ENCABEZADO */}
            <div className="flex justify-between items-center mb-6 pb-4 border-b border-gray-100">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-yellow-100 rounded-lg text-yellow-600">
                        <FaStar className="text-xl" />
                    </div>
                    <div>
                        <h3 className="text-lg font-bold text-gray-800">Accesos Rápidos</h3>
                        <p className="text-xs text-gray-500">Tus herramientas frecuentes.</p>
                    </div>
                </div>
                
                <button
                    onClick={() => router.push('/admin/utilidades/configuracion-favoritos')} 
                    className="flex items-center gap-2 px-4 py-2 bg-gray-50 hover:bg-gray-100 text-gray-600 rounded-lg transition-colors text-sm font-medium border border-gray-200 hover:border-gray-300"
                >
                    <FaCog /> <span className="hidden sm:inline">Configurar</span>
                </button>
            </div>
            
            {/* GRID */}
            <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-8 gap-4">
                {accessItems.map((item, index) => {
                    const isConfigured = item !== null;
                    
                    if (isConfigured) {
                        const IconComponent = getUniqueIconForRoute(item.ruta_enlace);
                        
                        return (
                            <Link 
                                key={item.id}
                                href={item.ruta_enlace} 
                                className="
                                    flex flex-col items-center justify-center p-3 h-28 
                                    bg-white border border-gray-200 rounded-xl shadow-sm 
                                    hover:shadow-md hover:border-indigo-300 hover:-translate-y-1 
                                    transition-all duration-200 group relative overflow-hidden
                                "
                                title={item.nombre_personalizado}
                            >
                                <div className="absolute top-0 left-0 w-full h-1 bg-indigo-500 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left"></div>
                                <div className="p-2 bg-indigo-50 text-indigo-600 rounded-full mb-2 group-hover:bg-indigo-100 transition-colors">
                                    <IconComponent size={20} />
                                </div>
                                <span className="text-xs font-bold text-gray-700 text-center leading-tight line-clamp-2 px-1 group-hover:text-indigo-700">
                                    {item.nombre_personalizado}
                                </span>
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
                                    bg-gray-50 border-2 border-dashed border-gray-200 rounded-xl 
                                    text-gray-400 hover:text-indigo-500 hover:border-indigo-300 hover:bg-indigo-50/30
                                    transition-all duration-200
                                "
                                title={`Añadir Acceso en posición ${index + 1}`}
                            >
                                <FaPlus className="mb-2 opacity-50" />
                                <span className="text-xs font-medium">Añadir</span>
                            </button>
                        );
                    }
                })}
            </div>
            
            {/* Mensaje Empty State */}
            {favoritos.length === 0 && (
                <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-100 text-center">
                    <p className="text-sm text-blue-800 font-medium">
                        🚀 ¡Personaliza tu tablero! Configura hasta 16 accesos directos para trabajar más rápido.
                    </p>
                </div>
            )}
        </div>
    );
};

export default QuickAccessGrid;