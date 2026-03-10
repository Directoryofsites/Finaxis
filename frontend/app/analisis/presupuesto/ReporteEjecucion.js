"use client";
import React, { useState, useEffect } from 'react';
import { apiService } from '../../../lib/apiService';
import { toast } from 'react-hot-toast';
import { FaArrowLeft, FaChartLine, FaExclamationTriangle, FaFilePdf } from 'react-icons/fa';

export default function ReporteEjecucion({ escenario, onBack }) {
    const [reporte, setReporte] = useState(null);
    const [loading, setLoading] = useState(true);
    const [mesDesde, setMesDesde] = useState(1);
    const [mesHasta, setMesHasta] = useState(12);

    const fetchReporte = async () => {
        setLoading(true);
        try {
            const res = await apiService.get(`/presupuesto/escenarios/${escenario.id}/ejecucion`, {
                params: { mes_desde: mesDesde, mes_hasta: mesHasta }
            });
            setReporte(res.data);
        } catch (error) {
            console.error(error);
            toast.error("Error cargando reporte de ejecución");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchReporte();
    }, [escenario.id, mesDesde, mesHasta]);

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
            const url = `${API_BASE}/api/presupuesto/escenarios/${escenario.id}/ejecucion/pdf?token=${token}&mes_desde=${mesDesde}&mes_hasta=${mesHasta}`;

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

            {/* Filtros de Rango */}
            <div className="flex gap-4 mb-6 bg-gray-50 p-4 rounded border items-end">
                <div>
                    <label className="block text-xs font-bold text-gray-700 mb-1">Mes Desde</label>
                    <select value={mesDesde} onChange={e => setMesDesde(Number(e.target.value))} className="border p-2 rounded">
                        <option value={1}>Enero</option><option value={2}>Febrero</option>
                        <option value={3}>Marzo</option><option value={4}>Abril</option>
                        <option value={5}>Mayo</option><option value={6}>Junio</option>
                        <option value={7}>Julio</option><option value={8}>Agosto</option>
                        <option value={9}>Septiembre</option><option value={10}>Octubre</option>
                        <option value={11}>Noviembre</option><option value={12}>Diciembre</option>
                    </select>
                </div>
                <div>
                    <label className="block text-xs font-bold text-gray-700 mb-1">Mes Hasta</label>
                    <select value={mesHasta} onChange={e => setMesHasta(Number(e.target.value))} className="border p-2 rounded">
                        <option value={1}>Enero</option><option value={2}>Febrero</option>
                        <option value={3}>Marzo</option><option value={4}>Abril</option>
                        <option value={5}>Mayo</option><option value={6}>Junio</option>
                        <option value={7}>Julio</option><option value={8}>Agosto</option>
                        <option value={9}>Septiembre</option><option value={10}>Octubre</option>
                        <option value={11}>Noviembre</option><option value={12}>Diciembre</option>
                    </select>
                </div>
                <div className="text-sm text-gray-500 italic pb-2">
                    Visualizando el acumulado de meses seleccionados.
                </div>
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
                            const isOverBudget = item.rango.variacion < 0; // Ojo, lógica simplificada
                            // Identificar si es cuenta mayor o hijo
                            const rowClass = item.nivel < 5 ? "font-bold bg-gray-50 uppercase text-xs" : "hover:bg-blue-50";

                            return (
                                <tr key={item.cuenta_id} className={`border-b ${rowClass}`}>
                                    <td className="p-2 border">
                                        <div style={{ paddingLeft: `${(item.nivel - 1) * 1.5}rem` }}>
                                            <span className="font-mono mr-2 text-gray-500">{item.codigo}</span>
                                            {item.nombre}
                                        </div>
                                    </td>
                                    <td className="p-2 border text-right">{item.rango.presupuestado.toLocaleString('es-CO', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                                    <td className="p-2 border text-right">{item.rango.ejecutado.toLocaleString('es-CO', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                                    <td className={`p-2 border text-right font-bold ${item.rango.variacion < 0 ? 'text-red-600' : 'text-green-600'}`}>
                                        {item.rango.variacion.toLocaleString('es-CO', {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                                    </td>
                                    <td className="p-2 border text-center">
                                        {item.rango.porcentaje_ejecucion.toFixed(1)}%
                                    </td>
                                    <td className="p-2 border text-center">
                                        {item.rango.variacion < 0 ? (
                                            <span className="bg-red-100 text-red-800 px-2 py-1 rounded text-xs font-bold">ALERTA</span>
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
                * Variación Negativa (Rojo) generalmente indica que el saldo ejecutado desfavorablemente superó el presupuesto (Sobrecosto en Gastos/Costos, Faltante en Ingresos).
            </p>
        </div>
    );
}
