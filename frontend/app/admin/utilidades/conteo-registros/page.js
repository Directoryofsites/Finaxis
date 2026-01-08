'use client';
import React, { useEffect, useState } from 'react';
import { apiService } from '@/lib/apiService';
import { FaExclamationTriangle, FaCheckCircle, FaCalendarAlt, FaDatabase, FaBolt } from 'react-icons/fa';
import ModalComprarPaquete from '@/components/consumo/ModalComprarPaquete';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

export default function ConteoRegistrosPage() {
    const today = new Date();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [showRecargaModal, setShowRecargaModal] = useState(false);

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

    const handleRecargaSuccess = () => {
        fetchData(selectedMonth, selectedYear);
    };

    // Generar lista de años (Dinámico desde 2020 hasta actual + futuro)
    const currentYear = today.getFullYear();
    const startYear = 2020; // Año base seguro para legacy
    const years = [];
    for (let y = currentYear + 1; y >= startYear; y--) {
        years.push(y);
    }
    const months = [
        { id: 1, name: 'Ene' }, { id: 2, name: 'Feb' }, { id: 3, name: 'Mar' },
        { id: 4, name: 'Abr' }, { id: 5, name: 'May' }, { id: 6, name: 'Jun' },
        { id: 7, name: 'Jul' }, { id: 8, name: 'Ago' }, { id: 9, name: 'Sep' },
        { id: 10, name: 'Oct' }, { id: 11, name: 'Nov' }, { id: 12, name: 'Dic' }
    ];

    if (!data && loading) return <div className="p-8"><div className="animate-pulse h-40 bg-gray-100 rounded-xl border border-gray-200"></div></div>;
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
        <div className="p-6 max-w-4xl mx-auto">
            <h1 className="text-2xl font-light text-slate-800 mb-6 flex items-center">
                <FaDatabase className="mr-3 text-cyan-600" /> Control de Conteo de Registros
            </h1>
            <ToastContainer />

            <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-8 relative overflow-visible">

                {/* Cabecera con Filtros */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                    <div>
                        <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wide flex items-center gap-2 mb-2">
                            <FaCalendarAlt /> Periodo de Facturación
                        </h3>

                        {/* Selectores de Fecha */}
                        <div className="flex gap-2">
                            <select
                                value={selectedMonth}
                                onChange={(e) => setSelectedMonth(parseInt(e.target.value))}
                                className="text-base font-medium text-gray-700 bg-gray-50 border border-gray-200 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 cursor-pointer shadow-sm"
                            >
                                {months.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                            </select>
                            <select
                                value={selectedYear}
                                onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                                className="text-base font-medium text-gray-700 bg-gray-50 border border-gray-200 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 cursor-pointer shadow-sm"
                            >
                                {years.map(y => <option key={y} value={y}>{y}</option>)}
                            </select>
                        </div>
                    </div>

                    <div className={`flex items-center gap-3 px-4 py-2 rounded-lg bg-gray-50 ${textoEstado} shadow-sm border border-gray-100`}>
                        <span className="font-semibold">{loading ? "Actualizando..." : "Estado del Periodo"}</span>
                        {loading ? <span className="loading loading-spinner loading-sm"></span> : <Icono className="text-2xl" />}
                    </div>
                </div>

                {/* Botón de Recarga Visible */}
                <div className="flex justify-end mb-4">
                    <button
                        onClick={() => setShowRecargaModal(true)}
                        className="btn btn-sm bg-gray-100 hover:bg-gray-200 text-gray-700 border-none rounded-full shadow-sm gap-2 px-4 transition-all"
                    >
                        <FaBolt className="text-amber-500" /> Recargar Cupo Adicional
                    </button>
                </div>

                {/* Datos Grandes */}
                <div className="mb-6 text-center md:text-left">
                    <p className="text-5xl font-mono font-bold text-gray-800 mb-2">
                        {new Intl.NumberFormat('es-CO').format(total_registros)}
                        <span className="text-lg text-gray-400 font-sans font-normal ml-2">registros consumidos</span>
                    </p>
                    <p className="text-sm text-gray-500">
                        Total acumulado durante <span className="font-semibold">{periodo_texto}</span>
                    </p>
                </div>

                {/* Barra de Progreso */}
                <div className="w-full bg-gray-200 rounded-full h-4 mb-4 shadow-inner">
                    <div
                        className={`h-4 rounded-full transition-all duration-1000 ease-out ${colorBarra} relative`}
                        style={{ width: `${Math.min(porcentaje, 100)}%` }}
                    >
                        <span className="absolute right-0 -top-8 bg-gray-800 text-white text-xs font-bold px-2 py-1 rounded opacity-0 hover:opacity-100 transition-opacity">
                            {porcentaje}%
                        </span>
                    </div>
                </div>

                {/* Pie de Tarjeta */}
                <div className="flex justify-between text-sm font-semibold items-center bg-gray-50 p-4 rounded-lg border border-gray-100">
                    <span className={textoEstado}>
                        {porcentaje}% del plan utilizado
                    </span>
                    <span className="text-gray-600">
                        Límite contratado: <span className="font-bold text-gray-900">{limite_registros > 0 ? new Intl.NumberFormat('es-CO').format(limite_registros) : 'Ilimitado'}</span>
                    </span>
                </div>

                <div className="mt-8 p-4 bg-blue-50 text-blue-800 rounded-lg text-sm border border-blue-100">
                    <p className="flex items-center gap-2">
                        <FaCheckCircle />
                        <strong>Información:</strong> El conteo de registros incluye todos los documentos contables, facturas, recibos y asientos generados en el sistema durante el mes seleccionado.
                    </p>
                </div>
            </div>

            <ModalComprarPaquete
                isOpen={showRecargaModal}
                onClose={() => setShowRecargaModal(false)}
                onSuccess={handleRecargaSuccess}
            />
        </div >
    );
}
