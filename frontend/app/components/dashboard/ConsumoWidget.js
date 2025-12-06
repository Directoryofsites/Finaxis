'use client';
import React, { useEffect, useState } from 'react';
import { apiService } from '@/lib/apiService'; 
import { FaExclamationTriangle, FaCheckCircle, FaCalendarAlt, FaSearch } from 'react-icons/fa';

export default function ConsumoWidget() {
    const today = new Date();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    
    // Estados para el filtro
    const [selectedMonth, setSelectedMonth] = useState(today.getMonth() + 1); // JS es 0-11, Backend es 1-12
    const [selectedYear, setSelectedYear] = useState(today.getFullYear());

    const fetchData = async (mes, anio) => {
        setLoading(true);
        try {
            // Enviamos los parámetros al backend
            const res = await apiService.get(`/dashboard/consumo?mes=${mes}&anio=${anio}`);
            setData(res.data);
        } catch (error) {
            console.error("Error cargando consumo", error);
        } finally {
            setLoading(false);
        }
    };

    // Carga inicial y cuando cambian los filtros
    useEffect(() => {
        fetchData(selectedMonth, selectedYear);
    }, [selectedMonth, selectedYear]);

    // Generar lista de años (Actual y anterior)
    const years = [today.getFullYear(), today.getFullYear() - 1];
    const months = [
        { id: 1, name: 'Ene' }, { id: 2, name: 'Feb' }, { id: 3, name: 'Mar' }, 
        { id: 4, name: 'Abr' }, { id: 5, name: 'May' }, { id: 6, name: 'Jun' },
        { id: 7, name: 'Jul' }, { id: 8, name: 'Ago' }, { id: 9, name: 'Sep' }, 
        { id: 10, name: 'Oct' }, { id: 11, name: 'Nov' }, { id: 12, name: 'Dic' }
    ];

    if (!data && loading) return <div className="animate-pulse h-40 bg-gray-100 rounded-xl border border-gray-200"></div>;
    if (!data) return null;

    const { total_registros, limite_registros, porcentaje, periodo_texto } = data;
    
    // Lógica visual
    let colorBarra = "bg-indigo-600";
    let textoEstado = "text-indigo-700";
    let Icono = FaCheckCircle;

    if (porcentaje >= 90) {
        colorBarra = "bg-red-600";
        textoEstado = "text-red-700";
        Icono = FaExclamationTriangle;
    } else if (porcentaje >= 75) {
        colorBarra = "bg-yellow-500";
        textoEstado = "text-yellow-700";
    }

    return (
        <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-5 relative overflow-visible">
            
            {/* Cabecera con Filtros */}
            <div className="flex justify-between items-start mb-4">
                <div>
                    <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wide flex items-center gap-2 mb-1">
                        <FaCalendarAlt /> Consumo Mensual
                    </h3>
                    
                    {/* Selectores de Fecha */}
                    <div className="flex gap-2">
                        <select 
                            value={selectedMonth}
                            onChange={(e) => setSelectedMonth(parseInt(e.target.value))}
                            className="text-sm font-bold text-gray-700 bg-gray-50 border border-gray-200 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-indigo-500 cursor-pointer"
                        >
                            {months.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                        </select>
                        <select 
                            value={selectedYear}
                            onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                            className="text-sm font-bold text-gray-700 bg-gray-50 border border-gray-200 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-indigo-500 cursor-pointer"
                        >
                            {years.map(y => <option key={y} value={y}>{y}</option>)}
                        </select>
                    </div>
                </div>

                <div className={`p-3 rounded-lg bg-gray-50 ${textoEstado} shadow-sm`}>
                    {loading ? <span className="loading loading-spinner loading-sm"></span> : <Icono className="text-xl" />}
                </div>
            </div>

            {/* Datos Grandes */}
            <div className="mb-3">
                <p className="text-3xl font-mono font-bold text-gray-800">
                    {new Intl.NumberFormat('es-CO').format(total_registros)}
                    <span className="text-sm text-gray-400 font-sans font-normal ml-1">registros</span>
                </p>
            </div>

            {/* Barra de Progreso */}
            <div className="w-full bg-gray-200 rounded-full h-2.5 mb-2">
                <div 
                    className={`h-2.5 rounded-full transition-all duration-500 ${colorBarra}`} 
                    style={{ width: `${Math.min(porcentaje, 100)}%` }}
                ></div>
            </div>

            {/* Pie de Tarjeta */}
            <div className="flex justify-between text-xs font-semibold items-center">
                <span className={textoEstado}>
                    {porcentaje}% utilizado en {periodo_texto}
                </span>
                <span className="text-gray-400 bg-gray-100 px-2 py-0.5 rounded">
                    Límite: {limite_registros > 0 ? new Intl.NumberFormat('es-CO').format(limite_registros) : '∞'}
                </span>
            </div>
        </div>
    );
}