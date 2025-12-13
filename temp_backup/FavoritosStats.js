import React from 'react';
import { FaStar, FaRocket, FaChartLine, FaCog } from 'react-icons/fa';

const FavoritosStats = ({ favoritos, onConfigure }) => {
    const usagePercentage = Math.round((favoritos.length / 24) * 100);
    
    const getUsageColor = () => {
        if (usagePercentage >= 80) return 'text-green-600 bg-green-100';
        if (usagePercentage >= 50) return 'text-yellow-600 bg-yellow-100';
        return 'text-blue-600 bg-blue-100';
    };

    const getUsageMessage = () => {
        if (usagePercentage >= 80) return '¡Excelente! Aprovechas al máximo tus accesos rápidos';
        if (usagePercentage >= 50) return 'Buen uso de tus accesos rápidos';
        if (usagePercentage > 0) return 'Puedes agregar más accesos para mayor productividad';
        return 'Configura tus primeros accesos rápidos';
    };

    return (
        <div className="bg-gradient-to-r from-indigo-50 to-purple-50 p-4 rounded-xl border border-indigo-200/50 mb-6">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${getUsageColor()}`}>
                        <FaChartLine className="text-lg" />
                    </div>
                    <div>
                        <p className="text-sm font-semibold text-gray-800">
                            {favoritos.length} de 24 configurados ({usagePercentage}%)
                        </p>
                        <p className="text-xs text-gray-600">
                            {getUsageMessage()}
                        </p>
                    </div>
                </div>
                
                {favoritos.length < 24 && (
                    <button
                        onClick={onConfigure}
                        className="flex items-center gap-2 px-3 py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-lg transition-colors text-xs font-medium"
                    >
                        <FaCog className="text-sm" />
                        Agregar más
                    </button>
                )}
            </div>
            
            {/* Barra de progreso */}
            <div className="mt-3 w-full bg-gray-200 rounded-full h-2">
                <div 
                    className="bg-gradient-to-r from-indigo-500 to-purple-600 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${usagePercentage}%` }}
                ></div>
            </div>
        </div>
    );
};

export default FavoritosStats;