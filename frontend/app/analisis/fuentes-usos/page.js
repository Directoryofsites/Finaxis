'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
// Path check: frontend/app/analisis/fuentes-usos/page.js
// AuthContext: frontend/app/context/AuthContext.js
// Depth: 
// 1. fuentes-usos
// 2. analisis
// 3. app
// So ../../../context/AuthContext is correct.

import { FaPrint, FaFileCsv, FaSearch, FaChartBar, FaFilter, FaSpinner, FaBook } from 'react-icons/fa';
import { useRouter } from 'next/navigation';

export default function FuentesUsosPage() {
    const { user } = useAuth();
    const [fechaInicio, setFechaInicio] = useState('');
    const [fechaFin, setFechaFin] = useState('');

    // Data state
    const [reportData, setReportData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Initial dates
    useEffect(() => {
        const now = new Date();
        const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
        const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);

        const formatDate = (d) => {
            const offset = d.getTimezoneOffset();
            const local = new Date(d.getTime() - (offset * 60 * 1000));
            return local.toISOString().split('T')[0];
        };
        setFechaInicio(formatDate(firstDay));
        setFechaFin(formatDate(lastDay));
    }, []);

    const handleGenerate = async () => {
        setLoading(true);
        setError(null);
        setReportData(null);
        try {
            const token = localStorage.getItem('authToken');
            if (!token) throw new Error("Sesión no válida");

            const params = new URLSearchParams({
                fecha_inicio: fechaInicio,
                fecha_fin: fechaFin
            });

            // Endpoint: /api/reports/working-capital-analysis
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/reports/working-capital-analysis?${params}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!res.ok) throw new Error("Error obteniendo datos del reporte");

            const data = await res.json();
            setReportData(data);

        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleExportPDF = async () => {
        try {
            const token = localStorage.getItem('authToken');
            const params = new URLSearchParams({
                fecha_inicio: fechaInicio,
                fecha_fin: fechaFin
            });

            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/reports/working-capital-analysis/get-signed-url?${params}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!res.ok) throw new Error("No se pudo obtener URL firmada");
            const data = await res.json();

            const endpointPath = "/api/reports/working-capital-analysis/imprimir";
            const downloadUrl = `${process.env.NEXT_PUBLIC_API_URL}${endpointPath}?token=${data.signed_url_token}`;
            window.open(downloadUrl, '_blank');

        } catch (err) {
            alert("Error: " + err.message);
        }
    };

    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center bg-white p-4 rounded-xl shadow-sm border border-gray-100">
                <div>
                    <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                        <FaChartBar className="text-purple-600" />
                        Estado de Fuentes y Usos (Capital de Trabajo)
                    </h1>
                    <p className="text-gray-500 text-sm mt-1">
                        Analiza de dónde provienen los recursos (Fuentes) y en qué se utilizan (Usos) dentro del Capital de Trabajo.
                    </p>
                </div>
                <button
                    onClick={() => window.open('/manual/capitulo_64_fuentes_usos.html', '_blank', 'width=800,height=600')}
                    className="flex items-center gap-2 px-4 py-2 bg-purple-50 text-purple-600 rounded-lg hover:bg-purple-100 transition-colors text-sm font-medium"
                >
                    <FaBook /> Manual
                </button>
            </div>

            {/* Filters */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                <div className="space-y-1">
                    <label className="text-xs font-semibold text-gray-500 uppercase">Fecha Inicial</label>
                    <input type="date" value={fechaInicio} onChange={e => setFechaInicio(e.target.value)}
                        className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-purple-500 outline-none" />
                </div>
                <div className="space-y-1">
                    <label className="text-xs font-semibold text-gray-500 uppercase">Fecha Final</label>
                    <input type="date" value={fechaFin} onChange={e => setFechaFin(e.target.value)}
                        className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-purple-500 outline-none" />
                </div>
                <div className="md:col-span-2 flex items-end gap-2">
                    <button onClick={handleGenerate} disabled={loading}
                        className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition flex items-center gap-2 font-medium shadow-sm disabled:opacity-50">
                        {loading ? <FaSpinner className="animate-spin" /> : <FaFilter />} Generar Análisis
                    </button>
                    <button onClick={handleExportPDF} disabled={loading}
                        className="px-6 py-2 bg-white text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50 transition flex items-center gap-2 font-medium shadow-sm">
                        <FaPrint className="text-red-500" /> PDF
                    </button>
                </div>
            </div>

            {/* Results */}
            {reportData && (
                <div className="space-y-6">
                    {/* Tarjetas Resumen */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="bg-white p-4 rounded-xl shadow-sm border-l-4 border-green-500">
                            <h3 className="text-sm font-bold text-gray-500 uppercase">Total Fuentes</h3>
                            <p className="text-2xl font-bold text-green-600">${reportData.totales.total_fuentes.toLocaleString('es-CO', { maximumFractionDigits: 0 })}</p>
                            <p className="text-xs text-gray-400 mt-1">Orígenes (Sin Caja)</p>
                        </div>
                        <div className="bg-white p-4 rounded-xl shadow-sm border-l-4 border-red-500">
                            <h3 className="text-sm font-bold text-gray-500 uppercase">Total Usos</h3>
                            <p className="text-2xl font-bold text-red-600">${reportData.totales.total_usos.toLocaleString('es-CO', { maximumFractionDigits: 0 })}</p>
                            <p className="text-xs text-gray-400 mt-1">Aplicaciones (Sin Caja)</p>
                        </div>
                        <div className="bg-white p-4 rounded-xl shadow-sm border-l-4 border-gray-500">
                            <h3 className="text-sm font-bold text-gray-500 uppercase">Fuentes - Usos</h3>
                            <p className={`text-2xl font-bold ${reportData.totales.diferencia >= 0 ? 'text-gray-700' : 'text-red-600'}`}>
                                ${reportData.totales.diferencia.toLocaleString('es-CO', { maximumFractionDigits: 0 })}
                            </p>
                            <p className="text-xs text-gray-400 mt-1">Excedente/Déficit Neto</p>
                        </div>
                        <div className={`bg-white p-4 rounded-xl shadow-sm border-l-4 ${reportData.resumen_kt.variacion_kt >= 0 ? 'border-blue-500' : 'border-orange-500'}`}>
                            <h3 className="text-sm font-bold text-gray-500 uppercase">Variación K.T. Operativo</h3>
                            <p className={`text-2xl font-bold ${reportData.resumen_kt.variacion_kt >= 0 ? 'text-blue-600' : 'text-orange-600'}`}>
                                ${reportData.resumen_kt.variacion_kt.toLocaleString('es-CO', { maximumFractionDigits: 0 })}
                            </p>
                            <p className="text-xs text-gray-400 mt-1">Sin Efectivo</p>
                        </div>
                    </div>

                    {/* Tabla Detalle */}
                    <div className="bg-white rounded-xl shadow-sm overflow-hidden border border-gray-100">
                        <div className="p-4 border-b border-gray-100 bg-gray-50">
                            <h2 className="font-bold text-gray-700">Detalle por Cuenta</h2>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm text-left">
                                <thead className="bg-gray-50 text-gray-500 uppercase font-medium">
                                    <tr>
                                        <th className="px-4 py-3">Cuenta</th>
                                        <th className="px-4 py-3 text-right">Saldo Inicial</th>
                                        <th className="px-4 py-3 text-right">Saldo Final</th>
                                        <th className="px-4 py-3 text-right text-green-600 bg-green-50">Fuente</th>
                                        <th className="px-4 py-3 text-right text-red-600 bg-red-50">Uso</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100">
                                    {reportData.filas.map((row, idx) => (
                                        <tr key={idx} className="hover:bg-gray-50">
                                            <td className="px-4 py-3">
                                                <span className="font-mono text-xs bg-gray-100 px-1 rounded mr-2">{row.cuenta_codigo}</span>
                                                {row.cuenta_nombre}
                                            </td>
                                            <td className="px-4 py-3 text-right text-gray-600">${row.saldo_inicial.toLocaleString('es-CO', { maximumFractionDigits: 0 })}</td>
                                            <td className="px-4 py-3 text-right text-gray-600">${row.saldo_final.toLocaleString('es-CO', { maximumFractionDigits: 0 })}</td>
                                            <td className="px-4 py-3 text-right font-bold text-green-600 bg-green-50/30">
                                                {row.fuente > 0 ? `$${row.fuente.toLocaleString('es-CO', { maximumFractionDigits: 0 })}` : '-'}
                                            </td>
                                            <td className="px-4 py-3 text-right font-bold text-red-600 bg-red-50/30">
                                                {row.uso > 0 ? `$${row.uso.toLocaleString('es-CO', { maximumFractionDigits: 0 })}` : '-'}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
