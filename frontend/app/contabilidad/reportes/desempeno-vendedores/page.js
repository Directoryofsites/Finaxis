'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { FaUserTie, FaCalendarAlt, FaFileDownload, FaChartBar, FaTable, FaTrophy, FaArrowUp, FaPercent, FaMoneyBillWave } from 'react-icons/fa';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { apiService } from '../../../../lib/apiService';
import { 
    generarPdfDesempenoVendedores, 
    exportarCsvDesempenoVendedores 
} from '../../../../lib/reportesFacturacionService';
import { useAuth } from '../../../context/AuthContext';

const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm transition-all outline-none bg-white";

export default function DesempenoVendedoresPage() {
    const { user, loading: authLoading } = useAuth();
    const router = useRouter();

    const [fechaInicio, setFechaInicio] = useState(new Date(new Date().getFullYear(), new Date().getMonth(), 1));
    const [fechaFin, setFechaFin] = useState(new Date());
    const [loading, setLoading] = useState(false);
    const [data, setData] = useState(null);

    const fetchReportData = async () => {
        try {
            setLoading(true);
            const params = {
                fecha_inicio: fechaInicio.toISOString().split('T')[0],
                fecha_fin: fechaFin.toISOString().split('T')[0]
            };
            const response = await apiService.get('/reportes-facturacion/desempeno-vendedores', { params });
            setData(response.data);
        } catch (error) {
            console.error(error);
            toast.error("Error al cargar el reporte de desempeño.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (!authLoading && user) {
            fetchReportData();
        }
    }, [user, authLoading]);

    if (authLoading) return <div className="p-8 text-center">Verificando sesión...</div>;
    if (!user) return null;

    const formatCurr = (val) => new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(val);
    const formatPerc = (val) => `${parseFloat(val).toFixed(2)}%`;

    return (
        <div className="min-h-screen bg-gray-50 pb-12">
            <ToastContainer />
            
            {/* Header */}
            <div className="bg-white border-b border-gray-200 px-6 py-6 shadow-sm">
                <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-3">
                            <span className="bg-indigo-100 p-2 rounded-lg text-indigo-600">
                                <FaUserTie />
                            </span>
                            Desempeño de Vendedores
                        </h1>
                        <p className="text-gray-500 text-sm ml-11">Análisis de rentabilidad y utilidad real por fuerza de ventas.</p>
                    </div>

                    <div className="flex flex-wrap items-end gap-3">
                        <div>
                            <label className={labelClass}>Desde</label>
                            <div className="relative">
                                <DatePicker
                                    selected={fechaInicio}
                                    onChange={date => setFechaInicio(date)}
                                    className={inputClass}
                                    dateFormat="dd/MM/yyyy"
                                />
                                <FaCalendarAlt className="absolute right-3 top-3 text-gray-400 pointer-events-none" />
                            </div>
                        </div>
                        <div>
                            <label className={labelClass}>Hasta</label>
                            <div className="relative">
                                <DatePicker
                                    selected={fechaFin}
                                    onChange={date => setFechaFin(date)}
                                    className={inputClass}
                                    dateFormat="dd/MM/yyyy"
                                />
                                <FaCalendarAlt className="absolute right-3 top-3 text-gray-400 pointer-events-none" />
                            </div>
                        </div>
                        <button
                            onClick={fetchReportData}
                            disabled={loading}
                            className="bg-indigo-600 text-white px-6 py-2 rounded-lg font-bold hover:bg-indigo-700 transition-all shadow-md disabled:bg-gray-400 flex items-center gap-2"
                        >
                            {loading ? "Calculando..." : <><FaChartBar /> Refrescar</>}
                        </button>

                        <div className="flex gap-2">
                            <button
                                onClick={async () => {
                                    try {
                                        setLoading(true);
                                        const pdfBlob = await generarPdfDesempenoVendedores(
                                            fechaInicio.toISOString().split('T')[0],
                                            fechaFin.toISOString().split('T')[0]
                                        );
                                        const url = window.URL.createObjectURL(new Blob([pdfBlob]));
                                        const link = document.createElement('a');
                                        link.href = url;
                                        link.setAttribute('download', `Desempeno_Vendedores_${fechaInicio.toISOString().split('T')[0]}_a_${fechaFin.toISOString().split('T')[0]}.pdf`);
                                        document.body.appendChild(link);
                                        link.click();
                                        link.remove();
                                    } catch (err) {
                                        toast.error("Error al generar PDF");
                                    } finally {
                                        setLoading(false);
                                    }
                                }}
                                disabled={loading || !data}
                                className="bg-red-600 text-white px-4 py-2 rounded-lg font-bold hover:bg-red-700 transition-all shadow-md disabled:bg-gray-400 flex items-center gap-2"
                                title="Exportar Ranking a PDF"
                            >
                                <FaFileDownload /> PDF
                            </button>

                            <button
                                onClick={async () => {
                                    try {
                                        setLoading(true);
                                        await exportarCsvDesempenoVendedores(
                                            fechaInicio.toISOString().split('T')[0],
                                            fechaFin.toISOString().split('T')[0]
                                        );
                                    } catch (err) {
                                        toast.error("Error al exportar Excel");
                                    } finally {
                                        setLoading(false);
                                    }
                                }}
                                disabled={loading || !data}
                                className="bg-emerald-600 text-white px-4 py-2 rounded-lg font-bold hover:bg-emerald-700 transition-all shadow-md disabled:bg-gray-400 flex items-center gap-2"
                                title="Exportar Ranking a Excel/CSV"
                            >
                                <FaFileDownload /> EXCEL
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="max-w-7xl mx-auto px-6 py-8">
                {data && (
                    <>
                        {/* Summary Cards */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                            <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
                                <div className="flex items-center justify-between mb-4">
                                    <div className="bg-blue-50 p-3 rounded-lg text-blue-600"><FaMoneyBillWave size={24} /></div>
                                    <span className="text-xs font-bold text-gray-400 uppercase">Ventas Netas</span>
                                </div>
                                <h3 className="text-2xl font-black text-gray-800">{formatCurr(data.totales_globales.neto)}</h3>
                                <p className="text-xs text-blue-600 mt-2 font-bold flex items-center gap-1">
                                    IVA: {formatCurr(data.totales_globales.iva)}
                                </p>
                            </div>

                            <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
                                <div className="flex items-center justify-between mb-4">
                                    <div className="bg-orange-50 p-3 rounded-lg text-orange-600"><FaArrowUp size={24} /></div>
                                    <span className="text-xs font-bold text-gray-400 uppercase">Costo Mercancía</span>
                                </div>
                                <h3 className="text-2xl font-black text-gray-800">{formatCurr(data.totales_globales.costo)}</h3>
                                <p className="text-xs text-orange-600 mt-2 font-bold italic">Base de costo promedio</p>
                            </div>

                            <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
                                <div className="flex items-center justify-between mb-4">
                                    <div className="bg-green-50 p-3 rounded-lg text-green-600"><FaTrophy size={24} /></div>
                                    <span className="text-xs font-bold text-gray-400 uppercase">Utilidad Real</span>
                                </div>
                                <h3 className="text-2xl font-black text-gray-800">{formatCurr(data.totales_globales.utilidad)}</h3>
                                <p className="text-xs text-green-600 mt-2 font-bold italic">Lo que realmente queda</p>
                            </div>

                            <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
                                <div className="flex items-center justify-between mb-4">
                                    <div className="bg-purple-50 p-3 rounded-lg text-purple-600"><FaPercent size={24} /></div>
                                    <span className="text-xs font-bold text-gray-400 uppercase">Margen Global</span>
                                </div>
                                <h3 className="text-2xl font-black text-gray-800">
                                    {data.totales_globales.neto > 0 
                                      ? formatPerc((data.totales_globales.utilidad / data.totales_globales.neto) * 100)
                                      : '0%'
                                    }
                                </h3>
                                <p className="text-xs text-purple-600 mt-2 font-bold italic">Rendimiento promedio</p>
                            </div>
                        </div>

                        {/* Ranking Table */}
                        <div className="bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-200">
                            <div className="px-6 py-4 bg-gray-50 border-b border-gray-200 flex justify-between items-center">
                                <h3 className="font-bold text-gray-700 flex items-center gap-2">
                                    <FaTable className="text-indigo-500" /> Ranking por Ventas y Rentabilidad
                                </h3>
                                <div className="text-xs bg-indigo-100 text-indigo-700 px-3 py-1 rounded-full font-bold">
                                    {data.ranking.length} Vendedores con movimientos
                                </div>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="w-full text-left border-collapse">
                                    <thead>
                                        <tr className="bg-white text-gray-400 text-[10px] uppercase tracking-widest font-bold border-b border-gray-100">
                                            <th className="px-6 py-4">Puesto</th>
                                            <th className="px-6 py-4 text-gray-800">Vendedor</th>
                                            <th className="px-6 py-4 text-center">Facturas</th>
                                            <th className="px-6 py-4 text-right">Venta Bruta</th>
                                            <th className="px-6 py-4 text-right">Descuentos</th>
                                            <th className="px-6 py-4 text-right text-gray-800 bg-blue-50">Venta Neta</th>
                                            <th className="px-6 py-4 text-right">Costo</th>
                                            <th className="px-6 py-4 text-right text-green-700 bg-green-50">Utilidad</th>
                                            <th className="px-6 py-4 text-center">Margen</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-100">
                                        {data.ranking.map((v, idx) => (
                                            <tr key={v.vendedor_id} className="hover:bg-gray-50 transition-colors">
                                                <td className="px-6 py-4">
                                                    <span className={`
                                                        w-8 h-8 flex items-center justify-center rounded-lg font-bold text-sm
                                                        ${idx === 0 ? 'bg-yellow-100 text-yellow-700 shadow-sm border border-yellow-200' : 'bg-gray-100 text-gray-500'}
                                                    `}>
                                                        {idx + 1}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 font-bold text-gray-800">{v.vendedor_nombre}</td>
                                                <td className="px-6 py-4 text-center font-mono text-gray-500">{v.cantidad_facturas}</td>
                                                <td className="px-6 py-4 text-right font-mono text-xs">{formatCurr(v.total_ventas_brutas)}</td>
                                                <td className="px-6 py-4 text-right font-mono text-xs text-red-500">{formatCurr(v.total_descuentos)}</td>
                                                <td className="px-6 py-4 text-right font-black text-blue-700 bg-blue-50/50">{formatCurr(v.total_neto)}</td>
                                                <td className="px-6 py-4 text-right font-mono text-xs text-orange-600">{formatCurr(v.costo_total)}</td>
                                                <td className="px-6 py-4 text-right font-black text-green-700 bg-green-50/50">{formatCurr(v.utilidad_bruta)}</td>
                                                <td className="px-6 py-4 text-center">
                                                    <span className={`
                                                        px-3 py-1 rounded-full text-xs font-bold
                                                        ${v.margen_porcentaje > 30 ? 'bg-green-100 text-green-700' : 
                                                          v.margen_porcentaje > 15 ? 'bg-blue-100 text-blue-700' : 'bg-red-100 text-red-700'}
                                                    `}>
                                                        {formatPerc(v.margen_porcentaje)}
                                                    </span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
