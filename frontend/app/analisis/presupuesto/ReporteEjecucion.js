"use client";

import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  Download, 
  Table as TableIcon, 
  Filter,
  CheckCircle2,
  AlertCircle,
  XCircle,
  ChevronRight,
  ChevronDown,
  Printer
} from 'lucide-react';
import { apiService } from '../../../lib/apiService';
import { toast } from 'react-toastify';

const ComparativeReport = ({ anio }) => {
    // ... items ...
    const [reportData, setReportData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [selectedMonths, setSelectedMonths] = useState([1, 2, 3]); // Default Q1
    const [viewMode, setViewMode] = useState('table'); // table or chart

    const mesesLabels = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"];

    useEffect(() => {
        fetchReport();
    }, [anio, selectedMonths]);

    const fetchReport = async () => {
        setLoading(true);
        try {
            const res = await apiService.get(`/presupuesto/comparativo`, {
                params: { anio, meses: selectedMonths }
            });
            setReportData(res.data);
        } catch (error) {
            toast.error("Error al cargar el reporte comparativo");
        } finally {
            setLoading(false);
        }
    };

    const toggleMonth = (mesIdx) => {
        const newMonths = [...selectedMonths];
        if (newMonths.includes(mesIdx + 1)) {
            if (newMonths.length > 1) {
                const filtered = newMonths.filter(m => m !== mesIdx + 1);
                setSelectedMonths(filtered);
            }
        } else {
            setSelectedMonths([...newMonths, mesIdx + 1].sort((a,b) => a-b));
        }
    };

    const getTrafficLight = (pct) => {
        if (pct > 100) return <div className="flex items-center text-red-600 font-bold"><XCircle size={14} className="mr-1"/> Sobreejecución</div>;
        if (pct >= 80) return <div className="flex items-center text-amber-600 font-bold"><AlertCircle size={14} className="mr-1"/> Límite</div>;
        return <div className="flex items-center text-green-600 font-bold"><CheckCircle2 size={14} className="mr-1"/> Normal</div>;
    };

    const getBgColor = (pct) => {
        if (pct > 100) return 'bg-red-50 text-red-700 border-red-100';
        if (pct >= 80) return 'bg-amber-50 text-amber-700 border-amber-100';
        return 'bg-green-50 text-green-700 border-green-100';
    };

    const handleExportCSV = async () => {
        try {
            const res = await apiService.get(`/presupuesto/comparativo/get-signed-url`, {
                params: { anio, meses: selectedMonths }
            });
            const token = res.data.signed_url_token;
            const url = `${apiService.defaults.baseURL}/presupuesto/comparativo/csv?signed_token=${token}`;
            window.open(url, '_blank');
        } catch (error) {
            console.error("Error al generar URL de exportación:", error);
            toast.error("No se pudo iniciar la descarga. Intente de nuevo.");
        }
    };

    const handleExportPDF = async () => {
        try {
            const res = await apiService.get(`/presupuesto/comparativo/get-signed-url`, {
                params: { anio, meses: selectedMonths }
            });
            const token = res.data.signed_url_token;
            const url = `${apiService.defaults.baseURL}/presupuesto/comparativo/pdf?signed_token=${token}`;
            window.open(url, '_blank');
        } catch (error) {
            console.error("Error al generar URL de exportación:", error);
            toast.error("No se pudo iniciar la descarga. Intente de nuevo.");
        }
    };

    const handleExportPDFGrafico = async () => {
        try {
            const res = await apiService.get(`/presupuesto/comparativo/get-signed-url`, {
                params: { anio, meses: selectedMonths }
            });
            const token = res.data.signed_url_token;
            const url = `${apiService.defaults.baseURL}/presupuesto/comparativo/pdf-grafico?signed_token=${token}`;
            window.open(url, '_blank');
        } catch (error) {
            console.error("Error al generar URL de exportación:", error);
            toast.error("No se pudo iniciar la descarga. Intente de nuevo.");
        }
    };

    return (
        <div className="flex flex-col space-y-6">
            {/* Filters Bar */}
            <div className="bg-white p-4 rounded-xl shadow-sm border flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center space-x-2 overflow-x-auto pb-2 md:pb-0">
                    <span className="text-xs font-bold text-gray-400 uppercase mr-2">Meses:</span>
                    {mesesLabels.map((m, i) => (
                        <button 
                            key={m}
                            onClick={() => toggleMonth(i)}
                            className={`px-3 py-1 rounded-full text-xs font-bold transition ${selectedMonths.includes(i+1) ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}
                        >
                            {m}
                        </button>
                    ))}
                </div>
                
                <div className="flex items-center space-x-2">
                    <button 
                        onClick={handleExportCSV}
                        title="Exportar Excel"
                        className="p-2 bg-gray-50 rounded-lg text-green-600 hover:bg-green-50 border border-transparent hover:border-green-200 transition"
                    >
                        <Download size={18} />
                    </button>
                    <button 
                        onClick={handleExportPDF}
                        title="Imprimir PDF Estándar"
                        className="p-2 bg-gray-50 rounded-lg text-red-600 hover:bg-red-50 border border-transparent hover:border-red-200 transition"
                    >
                        <Printer size={18} />
                    </button>
                    <button 
                        onClick={handleExportPDFGrafico}
                        title="PDF Gráfico con Barras"
                        className="p-2 bg-gray-50 rounded-lg text-blue-600 hover:bg-blue-50 border border-transparent hover:border-blue-200 transition"
                    >
                        <BarChart3 size={18} />
                    </button>
                    <div className="flex bg-gray-100 p-1 rounded-lg">
                        <button 
                            onClick={() => setViewMode('table')}
                            className={`p-1.5 rounded-md transition ${viewMode === 'table' ? 'bg-white shadow-sm text-blue-600' : 'text-gray-500'}`}
                        >
                            <TableIcon size={18} />
                        </button>
                        <button 
                            onClick={() => setViewMode('chart')}
                            className={`p-1.5 rounded-md transition ${viewMode === 'chart' ? 'bg-white shadow-sm text-blue-600' : 'text-gray-500'}`}
                        >
                            <BarChart3 size={18} />
                        </button>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
                {viewMode === 'table' ? (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead className="bg-slate-50 border-b">
                                <tr>
                                    <th className="p-4 text-xs font-bold text-gray-500 uppercase tracking-wider">Código / Cuenta</th>
                                    <th className="p-4 text-xs font-bold text-gray-500 uppercase tracking-wider text-right">Presupuestado</th>
                                    <th className="p-4 text-xs font-bold text-gray-500 uppercase tracking-wider text-right">Ejecutado</th>
                                    <th className="p-4 text-xs font-bold text-gray-500 uppercase tracking-wider text-right">Variación $</th>
                                    <th className="p-4 text-xs font-bold text-gray-500 uppercase tracking-wider text-center">Ejecución %</th>
                                    <th className="p-4 text-xs font-bold text-gray-500 uppercase tracking-wider text-center">Estado</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                                {loading ? (
                                    <tr>
                                        <td colSpan="6" className="p-12 text-center text-gray-400">
                                            <div className="flex flex-col items-center">
                                                <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-2"></div>
                                                Calculando variaciones...
                                            </div>
                                        </td>
                                    </tr>
                                ) : reportData.length === 0 ? (
                                    <tr>
                                        <td colSpan="6" className="p-12 text-center text-gray-400">
                                            No hay datos para los períodos seleccionados.
                                        </td>
                                    </tr>
                                ) : reportData.map((row) => (
                                    <tr key={row.codigo} className="hover:bg-slate-50 transition-colors">
                                        <td className="p-4">
                                            <div className="font-mono text-xs text-blue-600 mb-1">{row.codigo}</div>
                                            <div className="font-medium text-gray-800 text-sm">{row.nombre}</div>
                                        </td>
                                        <td className="p-4 text-right font-mono text-sm">${parseFloat(row.presupuestado).toLocaleString()}</td>
                                        <td className="p-4 text-right font-mono text-sm text-gray-900">${parseFloat(row.ejecutado).toLocaleString()}</td>
                                        <td className={`p-4 text-right font-mono text-sm ${row.variacion_abs < 0 ? 'text-green-600' : 'text-red-600'}`}>
                                            {row.variacion_abs > 0 ? '+' : ''}{parseFloat(row.variacion_abs).toLocaleString()}
                                        </td>
                                        <td className="p-4 text-center">
                                            <div className={`inline-block px-3 py-1 rounded-full text-xs font-bold border ${getBgColor(row.ejecucion_pct)}`}>
                                                {row.ejecucion_pct.toFixed(1)}%
                                            </div>
                                        </td>
                                        <td className="p-4 text-xs">
                                            {getTrafficLight(row.ejecucion_pct)}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="p-8">
                        <h3 className="text-lg font-bold text-gray-800 mb-6">Visualización de Ejecución Presupuestal</h3>
                        <div className="space-y-8">
                            {reportData.slice(0, 15).map(row => (
                                <div key={row.codigo} className="space-y-2">
                                    <div className="flex justify-between items-end">
                                        <div>
                                            <span className="text-xs font-mono text-blue-600">{row.codigo}</span>
                                            <h4 className="text-sm font-bold text-gray-700">{row.nombre}</h4>
                                        </div>
                                        <div className="text-right">
                                            <span className="text-xs text-gray-400 block uppercase font-bold">Ejecución: {row.ejecucion_pct.toFixed(1)}%</span>
                                        </div>
                                    </div>
                                    <div className="h-4 w-full bg-gray-100 rounded-full overflow-hidden flex shadow-inner border border-gray-200">
                                        <div 
                                            className={`h-full transition-all duration-1000 ${row.ejecucion_pct > 100 ? 'bg-gradient-to-r from-red-500 to-red-600' : 'bg-gradient-to-r from-blue-500 to-blue-600'}`}
                                            style={{ width: `${Math.min(row.ejecucion_pct, 100)}%` }}
                                        ></div>
                                        {row.ejecucion_pct > 100 && (
                                            <div 
                                                className="h-full bg-red-800 opacity-50 flex items-center justify-center text-[8px] text-white font-bold"
                                                style={{ width: `${row.ejecucion_pct - 100}%` }}
                                            >
                                                !
                                            </div>
                                        )}
                                    </div>
                                    <div className="flex justify-between text-[10px] font-bold">
                                        <span className="text-gray-400">Pres: ${parseFloat(row.presupuestado).toLocaleString()}</span>
                                        <span className="text-gray-800">Ejec: ${parseFloat(row.ejecutado).toLocaleString()}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
            
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="bg-white p-6 rounded-xl shadow-sm border-l-4 border-blue-500">
                    <h4 className="text-xs font-bold text-gray-400 uppercase mb-1">Total Presupuestado</h4>
                    <p className="text-2xl font-bold text-gray-800">${reportData.reduce((a, b) => a + parseFloat(b.presupuestado), 0).toLocaleString()}</p>
                </div>
                <div className="bg-white p-6 rounded-xl shadow-sm border-l-4 border-slate-800">
                    <h4 className="text-xs font-bold text-gray-400 uppercase mb-1">Total Ejecutado</h4>
                    <p className="text-2xl font-bold text-gray-800">${reportData.reduce((a, b) => a + parseFloat(b.ejecutado), 0).toLocaleString()}</p>
                </div>
                <div className="bg-white p-6 rounded-xl shadow-sm border-l-4 border-green-500">
                    <h4 className="text-xs font-bold text-gray-400 uppercase mb-1">Diferencia Neta</h4>
                    <p className="text-2xl font-bold text-gray-800">${(reportData.reduce((a, b) => a + parseFloat(b.presupuestado), 0) - reportData.reduce((a, b) => a + parseFloat(b.ejecutado), 0)).toLocaleString()}</p>
                </div>
                <div className={`bg-white p-6 rounded-xl shadow-sm border-l-4 ${
                    (reportData.reduce((a, b) => a + parseFloat(b.ejecutado), 0) / reportData.reduce((a, b) => a + parseFloat(b.presupuestado), 0) * 100) > 100 ? 'border-red-500' : 'border-blue-600'
                }`}>
                    <h4 className="text-xs font-bold text-gray-400 uppercase mb-1">Ejecución Total %</h4>
                    <p className="text-2xl font-bold text-gray-800">
                        {(reportData.reduce((a, b) => a + parseFloat(b.ejecutado), 0) / (reportData.reduce((a, b) => a + parseFloat(b.presupuestado), 0) || 1) * 100).toFixed(1)}%
                    </p>
                </div>
            </div>

            {/* Global Progress Bar (Graphical View) */}
            {viewMode === 'chart' && (
                <div className="mt-8 p-8 bg-slate-50 rounded-xl border-2 border-dashed border-slate-200">
                    <div className="flex justify-between items-end mb-4">
                        <h3 className="text-lg font-black text-slate-800 uppercase tracking-tight">TOTAL GENERAL DE EJECUCI&Oacute;N</h3>
                        <span className="text-xl font-black text-blue-700">
                            {(reportData.reduce((a, b) => a + parseFloat(b.ejecutado), 0) / (reportData.reduce((a, b) => a + parseFloat(b.presupuestado), 0) || 1) * 100).toFixed(1)}%
                        </span>
                    </div>
                    <div className="h-6 w-full bg-white rounded-full overflow-hidden flex shadow-inner border border-slate-300">
                        {(() => {
                            const totalPres = reportData.reduce((a, b) => a + parseFloat(b.presupuestado), 0);
                            const totalEjec = reportData.reduce((a, b) => a + parseFloat(b.ejecutado), 0);
                            const totalPct = (totalEjec / (totalPres || 1)) * 100;
                            
                            if (totalPct > 100) {
                                return (
                                    <>
                                        <div className="h-full bg-red-600" style={{ width: `${(100 / totalPct) * 100}%` }}></div>
                                        <div className="h-full bg-red-800 opacity-50 flex items-center justify-center text-xs text-white font-bold animate-pulse" style={{ width: `${((totalPct - 100) / totalPct) * 100}%` }}>
                                            SOBREEJECUCI&Oacute;N !
                                        </div>
                                    </>
                                );
                            } else {
                                return <div className="h-full bg-gradient-to-r from-blue-500 to-blue-700" style={{ width: `${totalPct}%` }}></div>;
                            }
                        })()}
                    </div>
                </div>
            )}
        </div>
    );
};

export default ComparativeReport;
