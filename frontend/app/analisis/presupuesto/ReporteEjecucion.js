"use client";
import React, { useState, useEffect } from 'react';
import { apiService } from '../../../lib/apiService';
import { toast } from 'react-hot-toast';
import { FaArrowLeft, FaChartLine, FaExclamationTriangle, FaFilePdf } from 'react-icons/fa';

export default function ReporteEjecucion({ escenario, onBack }) {
    const [reporte, setReporte] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchReporte = async () => {
            try {
                const res = await apiService.get(`/presupuesto/escenarios/${escenario.id}/ejecucion`);
                setReporte(res.data);
            } catch (error) {
                console.error(error);
                toast.error("Error cargando reporte de ejecución");
            } finally {
                setLoading(false);
            }
        };
        fetchReporte();
    }, [escenario.id]);

    if (loading) return <div className="p-8 text-center">Calculando variaciones (Presupuesto vs Real)...</div>;

    if (!reporte) return <div className="p-8 text-center text-red-500">No se pudo cargar el reporte.</div>;

    const handleDownloadPDF = async () => {
        const toastId = toast.loading("Generando PDF...");
        try {
            // 1. Obtener Token Seguro
            const res = await apiService.get(`/presupuesto/escenarios/${escenario.id}/pdf-token`);
            const token = res.data.token;

            // 2. Construir URL
            const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';
            const url = `${API_BASE}/api/presupuesto/escenarios/${escenario.id}/ejecucion/pdf?token=${token}`;

            // 3. Abrir
            window.open(url, '_blank');
            toast.dismiss(toastId);
        } catch (error) {
            console.error(error);
            toast.error("Error generando enlace de descarga", { id: toastId });
        }
    };

    return (
        <div className="bg-white p-4 rounded shadow h-full flex flex-col">
            {/* Header */}
            <div className="flex justify-between items-center mb-6 border-b pb-4">
                <div className="flex items-center gap-4">
                    <button onClick={onBack} className="text-gray-500 hover:text-gray-800">
                        <FaArrowLeft /> Atrás
                    </button>
                    <div>
                        <h2 className="text-xl font-bold flex items-center gap-2">
                            <FaChartLine className="text-purple-600" />
                            Ejecución Presupuestal: {escenario.nombre}
                        </h2>
                        <span className="text-sm text-gray-500">Comparativa Año Fiscal {escenario.anio}</span>
                    </div>
                </div>
                <button
                    onClick={handleDownloadPDF}
                    className="bg-gray-600 text-white px-4 py-2 rounded flex items-center gap-2 hover:bg-gray-700 shadow-sm"
                >
                    <FaFilePdf /> Exportar PDF
                </button>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                {/* TODO: Calcular totales globales en frontend o backend */}
            </div>

            {/* Grid Comparativo */}
            <div className="flex-1 overflow-auto">
                <table className="min-w-full text-sm border-collapse">
                    <thead className="bg-gray-100 sticky top-0">
                        <tr>
                            <th className="p-3 border text-left">Cuenta</th>
                            <th className="p-3 border text-right">Presupuestado (Anual)</th>
                            <th className="p-3 border text-right">Ejecutado (Anual)</th>
                            <th className="p-3 border text-right">Variación $</th>
                            <th className="p-3 border text-center">% Ejecución</th>
                            <th className="p-3 border text-center">Estado</th>
                        </tr>
                    </thead>
                    <tbody>
                        {reporte.items.map(item => {
                            const isOverBudget = item.total_anual.variacion < 0; // Gasté más de lo planeado (asumiendo gasto)
                            // Para ingresos sería al revés, pero por simplicidad asumiremos enfoque de Gasto por ahora
                            // Ojo: En contabilidad, Gasto es Debito. Ingreso es Credito. 
                            // Mi logica backend hizo Plan - Real. 
                            // Si Plan (Gasto) = 100, Real (Gasto) = 120 -> 100 - 120 = -20 (Variacion Negativa = Sobrecosto) -> ROJO

                            return (
                                <tr key={item.cuenta_id} className="hover:bg-gray-50">
                                    <td className="p-2 border">
                                        <span className="font-mono font-bold mr-2">{item.codigo}</span>
                                        {item.nombre}
                                    </td>
                                    <td className="p-2 border text-right">{item.total_anual.presupuestado.toLocaleString()}</td>
                                    <td className="p-2 border text-right">{item.total_anual.ejecutado.toLocaleString()}</td>
                                    <td className={`p-2 border text-right font-bold ${item.total_anual.variacion < 0 ? 'text-red-600' : 'text-green-600'}`}>
                                        {item.total_anual.variacion.toLocaleString()}
                                    </td>
                                    <td className="p-2 border text-center">
                                        {item.total_anual.porcentaje_ejecucion.toFixed(1)}%
                                    </td>
                                    <td className="p-2 border text-center">
                                        {item.total_anual.variacion < 0 ? (
                                            <span className="bg-red-100 text-red-800 px-2 py-1 rounded text-xs font-bold">EXCEDIDO</span>
                                        ) : (
                                            <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs font-bold">OK</span>
                                        )}
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
            <p className="text-xs text-gray-400 mt-2">
                * Variación Negativa (Rojo) indica que la ejecución (gasto real) superó el presupuesto.
            </p>
        </div>
    );
}
