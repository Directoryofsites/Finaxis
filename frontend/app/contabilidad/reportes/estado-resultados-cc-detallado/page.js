'use client';

import React, { useState, useEffect } from 'react';
import Script from 'next/script';
import { useRouter } from 'next/navigation';
import { 
  FaChartPie, 
  FaCalendarAlt, 
  FaBuilding, 
  FaSearch, 
  FaFileCsv, 
  FaFilePdf, 
  FaExclamationTriangle 
} from 'react-icons/fa';

import { 
FaBook,
} from 'react-icons/fa';

import BotonRegresar from '../../../components/BotonRegresar';
import { useAuth } from '../../../context/AuthContext';
import { apiService } from '../../../../lib/apiService';

// --- ESTILOS REUSABLES (Manual v2.0) ---
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none pl-10";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white pl-10";

export default function EstadoResultadosCCPage() {
    const { user, loading: authLoading } = useAuth();
    const router = useRouter();

    // --- ESTADOS (Lógica Original) ---
    const [centrosCosto, setCentrosCosto] = useState([]);
    const [selectedCentroCostoId, setSelectedCentroCostoId] = useState('');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [reportData, setReportData] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [isPageReady, setPageReady] = useState(false);

    // --- EFECTOS (Lógica Original) ---
    
    // Redirección si no hay usuario
    useEffect(() => {
        if (!authLoading) {
            if (!user) {
                router.push('/login');
            } else {
                setPageReady(true); // Bandera para mostrar contenido
            }
        }
    }, [user, authLoading, router]);

    // Carga de Centros de Costo
    useEffect(() => {
        if (!authLoading && user) {
            const fetchCentrosCosto = async () => {
                try {
                    const res = await apiService.get('/centros-costo/get-flat');
                    setCentrosCosto(res.data);
                } catch (err) {
                    setError("Error al cargar la lista de centros de costo: " + (err.response?.data?.detail || err.message));
                }
            };
            fetchCentrosCosto();
        }
    }, [user, authLoading]);

    // --- HANDLERS (Lógica Original Intacta) ---

    const handleGenerateReport = async () => {
        if (!user || !user.empresaId) {
            setError('No se pudo identificar la empresa del usuario. Por favor, recargue la página.');
            return;
        }
        if (!startDate || !endDate) {
            setError('Por favor, seleccione un rango de fechas.');
            return;
        }

        setIsLoading(true);
        setError(null);
        setReportData(null);

        const params = {
            fecha_inicio: startDate,
            fecha_fin: endDate,
        };
        if (selectedCentroCostoId) {
            params.centro_costo_id = selectedCentroCostoId;
        }

        try {
            const res = await apiService.get('/reports/income-statement-cc', { params: params });
            setReportData(res.data);
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al generar el reporte de Estado de Resultados por Centro de Costo.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleExportCSV = () => {
        if (!reportData) return alert("Primero debe generar un reporte.");
        if (typeof window.Papa === 'undefined') {
            alert("La librería para exportar a CSV no está lista. Por favor, recargue la página.");
            return;
        }

        const formatCurrencyCSV = (value) => {
            return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(value);
        };

        const dataToExport = [];
        dataToExport.push(['Estado de Resultados por Centro de Costo']);
        const centroCostoName = selectedCentroCostoId ? 
            centrosCosto.find(cc => cc.id == selectedCentroCostoId)?.nombre || 'Desconocido' : 
            'Todos los Centros de Costo';
        dataToExport.push(['Centro de Costo:', centroCostoName]);
        dataToExport.push([`Del ${startDate} al ${endDate}`]);
        dataToExport.push([]);

        dataToExport.push(['INGRESOS OPERACIONALES']);
        reportData.ingresos.forEach(item => {
            dataToExport.push([item.codigo, item.nombre, formatCurrencyCSV(item.saldo)]);
        });
        dataToExport.push(['TOTAL INGRESOS', '', formatCurrencyCSV(reportData.totales.total_ingresos)]);
        dataToExport.push([]);

        if (reportData.costos.length > 0) {
            dataToExport.push(['COSTOS DE VENTA']);
            reportData.costos.forEach(item => {
                dataToExport.push([item.codigo, item.nombre, formatCurrencyCSV(-item.saldo)]);
            });
            dataToExport.push(['TOTAL COSTOS', '', formatCurrencyCSV(-reportData.totales.total_costos)]);
            dataToExport.push([]);
        }

        dataToExport.push(['UTILIDAD BRUTA EN VENTAS', '', formatCurrencyCSV(reportData.totales.utilidad_bruta)]);
        dataToExport.push([]);

        if (reportData.gastos.length > 0) {
            dataToExport.push(['GASTOS OPERACIONALES']);
            reportData.gastos.forEach(item => {
                dataToExport.push([item.codigo, item.nombre, formatCurrencyCSV(-item.saldo)]);
            });
            dataToExport.push(['TOTAL GASTOS', '', formatCurrencyCSV(-reportData.totales.total_gastos)]);
            dataToExport.push([]);
        }

        dataToExport.push(['UTILIDAD NETA DEL EJERCICIO', '', formatCurrencyCSV(reportData.totales.utilidad_neta)]);

        const csv = window.Papa.unparse(dataToExport);
        const blob = new Blob(["\uFEFF" + csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.setAttribute('download', `Estado_Resultados_CC_${startDate}_a_${endDate}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const handleExportPDF = async () => {
        if (!reportData) {
            setError("Primero debe generar un reporte.");
            return;
        }
        if (!user || !user.empresaId) {
            setError("No se pudo identificar el ID de la empresa del usuario.");
            return;
        }
        setIsLoading(true);
        setError(null);
        try {
            const paramsForSignedUrl = {
                fecha_inicio: startDate,
                fecha_fin: endDate,
            };
            if (selectedCentroCostoId) {
                paramsForSignedUrl.centro_costo_id = selectedCentroCostoId;
            }

            const signedUrlRes = await apiService.get('/reports/income-statement-cc/get-signed-url', { params: paramsForSignedUrl });
            const signedToken = signedUrlRes.data.signed_url_token;
            const finalPdfUrl = `${process.env.NEXT_PUBLIC_API_URL}/api/reports/income-statement-cc/imprimir?signed_token=${signedToken}`;

            const link = document.createElement('a');
            link.href = finalPdfUrl;
            link.setAttribute('download', `Estado_Resultados_CC_${startDate}_${endDate}.pdf`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

        } catch (err) {
            setError(err.response?.data?.detail || 'Error al obtener la URL firmada para el PDF.');
        } finally {
            setIsLoading(false);
        }
    };

    const formatNumber = (value) => {
        return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 2 }).format(value);
    };

    // --- RENDERIZADO ---

    if (authLoading || !isPageReady) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
                <FaChartPie className="text-indigo-300 text-6xl mb-4 animate-pulse" />
                <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando Reporte por Centro de Costo...</p>
            </div>
        );
    }

    if (!user) return null;

    return (
        <>
            <Script src="https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js" />
            
            <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
                <div className="max-w-5xl mx-auto">
                    
                    {/* ENCABEZADO */}
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                        <div>


                           <div className="flex items-center gap-3 mb-3">
                            
                            {/* 1. Botón Regresar (Izquierda) */}
                            <BotonRegresar />

                            {/* 2. Botón Manual (Derecha) */}
                            <button
                                onClick={() => window.open('/manual/capitulo_53_estado_resultados_cc_detallado.html', '_blank')}
                                className="text-indigo-600 hover:bg-indigo-50 px-3 py-1 rounded-md flex items-center gap-2 transition-colors font-bold text-sm"
                                type="button"
                            >
                                <FaBook className="text-lg" /> Manual
                            </button>

                        </div>


                            <div className="flex items-center gap-3 mt-3">
                                <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                                    <FaChartPie className="text-2xl" />
                                </div>
                                <div>
                                    <h1 className="text-3xl font-bold text-gray-800">Estado de Resultados (CC)</h1>
                                    <p className="text-gray-500 text-sm">Rentabilidad detallada por Centro de Costo.</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* CARD 1: FILTROS */}
                    <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 animate-fadeIn mb-8">
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 items-end">
                            
                            {/* Selector Centro Costo */}
                            <div className="md:col-span-1">
                                <label className={labelClass}>Centro de Costo</label>
                                <div className="relative">
                                    <select
                                        name="centroCostoId"
                                        value={selectedCentroCostoId}
                                        onChange={(e) => setSelectedCentroCostoId(e.target.value)}
                                        className={selectClass}
                                    >
                                        <option value="">Todos (Consolidado)</option>
                                        {centrosCosto.map(cc => (
                                            <option key={cc.id} value={cc.id}>{cc.codigo} - {cc.nombre}</option>
                                        ))}
                                    </select>
                                    <FaBuilding className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                </div>
                            </div>

                            {/* Fecha Inicio */}
                            <div className="md:col-span-1">
                                <label className={labelClass}>Desde</label>
                                <div className="relative">
                                    <input
                                        type="date"
                                        name="inicio"
                                        value={startDate}
                                        onChange={(e) => setStartDate(e.target.value)}
                                        className={inputClass}
                                    />
                                    <FaCalendarAlt className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                </div>
                            </div>

                            {/* Fecha Fin */}
                            <div className="md:col-span-1">
                                <label className={labelClass}>Hasta</label>
                                <div className="relative">
                                    <input
                                        type="date"
                                        name="fin"
                                        value={endDate}
                                        onChange={(e) => setEndDate(e.target.value)}
                                        className={inputClass}
                                    />
                                    <FaCalendarAlt className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                </div>
                            </div>

                            {/* Botón Generar */}
                            <div className="md:col-span-1">
                                <button
                                    onClick={handleGenerateReport}
                                    disabled={isLoading}
                                    className={`
                                        w-full px-6 py-2 rounded-lg shadow-md font-bold text-white transition-all transform hover:-translate-y-0.5 flex items-center justify-center gap-2
                                        ${isLoading ? 'bg-gray-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'}
                                    `}
                                >
                                    {isLoading ? <span className="loading loading-spinner loading-sm"></span> : <><FaSearch /> Generar</>}
                                </button>
                            </div>
                        </div>

                        {error && (
                            <div className="mt-4 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded-r-lg flex items-center gap-3 animate-pulse">
                                <FaExclamationTriangle className="text-xl" />
                                <p className="font-bold">{error}</p>
                            </div>
                        )}
                    </div>

                    {/* CARD 2: RESULTADOS (CONDICIONAL) */}
                    {reportData && (
                        <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden animate-slideDown">
                            
                            {/* Cabecera del Reporte */}
                            <div className="p-6 bg-gray-50 border-b border-gray-200 flex flex-col md:flex-row justify-between items-center gap-4">
                                <div>
                                    <h2 className="text-xl font-bold text-gray-800">{user?.nombre_empresa}</h2>
                                    <p className="text-sm text-gray-600 font-medium mt-1">
                                        {selectedCentroCostoId ? centrosCosto.find(cc => cc.id == selectedCentroCostoId)?.nombre : 'Todos los Centros de Costo'}
                                    </p>
                                    <p className="text-xs text-gray-500 mt-1">Periodo: {startDate} al {endDate}</p>
                                </div>
                                <div className="flex gap-3">
                                    <button onClick={handleExportCSV} disabled={isLoading} className="flex items-center gap-2 px-4 py-2 bg-white border border-green-500 text-green-600 rounded-lg hover:bg-green-50 font-medium transition-colors shadow-sm disabled:opacity-50"><FaFileCsv /> CSV</button>
                                    <button onClick={handleExportPDF} disabled={isLoading} className="flex items-center gap-2 px-4 py-2 bg-white border border-red-500 text-red-600 rounded-lg hover:bg-red-50 font-medium transition-colors shadow-sm disabled:opacity-50"><FaFilePdf /> PDF</button>
                                </div>
                            </div>

                            {/* Tabla de Resultados */}
                            <div className="overflow-x-auto">
                                <table className="min-w-full divide-y divide-gray-200">
                                    <tbody className="divide-y divide-gray-100">
                                        
                                        {/* SECCIÓN: INGRESOS */}
                                        <tr className="bg-emerald-50"><td colSpan="3" className="px-6 py-3 text-sm font-bold text-emerald-800 uppercase tracking-wider">Ingresos Operacionales</td></tr>
                                        {reportData.ingresos.map((item, index) => (
                                            <tr key={item.codigo || index} className="hover:bg-gray-50">
                                                <td className="px-6 py-2 whitespace-nowrap text-xs font-mono text-gray-500 w-32">{item.codigo}</td>
                                                <td className="px-6 py-2 text-sm text-gray-700">{item.nombre}</td>
                                                <td className="px-6 py-2 text-right text-sm font-mono font-medium text-emerald-700">{formatNumber(item.saldo)}</td>
                                            </tr>
                                        ))}
                                        <tr className="bg-emerald-100/50 font-bold">
                                            <td colSpan="2" className="px-6 py-3 text-right text-sm text-emerald-900">TOTAL INGRESOS</td>
                                            <td className="px-6 py-3 text-right text-sm font-mono text-emerald-900">{formatNumber(reportData.totales.total_ingresos)}</td>
                                        </tr>

                                        {/* SECCIÓN: COSTOS */}
                                        {reportData.costos.length > 0 && (
                                            <>
                                                <tr className="bg-rose-50"><td colSpan="3" className="px-6 py-3 text-sm font-bold text-rose-800 uppercase tracking-wider border-t-4 border-white">Costos de Venta</td></tr>
                                                {reportData.costos.map((item, index) => (
                                                    <tr key={item.codigo || index} className="hover:bg-gray-50">
                                                        <td className="px-6 py-2 whitespace-nowrap text-xs font-mono text-gray-500 w-32">{item.codigo}</td>
                                                        <td className="px-6 py-2 text-sm text-gray-700">{item.nombre}</td>
                                                        <td className="px-6 py-2 text-right text-sm font-mono font-medium text-rose-700">({formatNumber(Math.abs(item.saldo))})</td>
                                                    </tr>
                                                ))}
                                                <tr className="bg-rose-100/50 font-bold">
                                                    <td colSpan="2" className="px-6 py-3 text-right text-sm text-rose-900">TOTAL COSTOS</td>
                                                    <td className="px-6 py-3 text-right text-sm font-mono text-rose-900">({formatNumber(Math.abs(reportData.totales.total_costos))})</td>
                                                </tr>
                                            </>
                                        )}

                                        {/* UTILIDAD BRUTA */}
                                        <tr className="bg-gray-100 border-y-2 border-white">
                                            <td colSpan="2" className="px-6 py-4 text-right text-sm font-bold text-gray-800 uppercase">UTILIDAD BRUTA</td>
                                            <td className="px-6 py-4 text-right text-lg font-mono font-bold text-gray-900">{formatNumber(reportData.totales.utilidad_bruta)}</td>
                                        </tr>

                                        {/* SECCIÓN: GASTOS */}
                                        {reportData.gastos.length > 0 && (
                                            <>
                                                <tr className="bg-orange-50"><td colSpan="3" className="px-6 py-3 text-sm font-bold text-orange-800 uppercase tracking-wider border-t-4 border-white">Gastos Operacionales</td></tr>
                                                {reportData.gastos.map((item, index) => (
                                                    <tr key={item.codigo || index} className="hover:bg-gray-50">
                                                        <td className="px-6 py-2 whitespace-nowrap text-xs font-mono text-gray-500 w-32">{item.codigo}</td>
                                                        <td className="px-6 py-2 text-sm text-gray-700">{item.nombre}</td>
                                                        <td className="px-6 py-2 text-right text-sm font-mono font-medium text-orange-700">({formatNumber(Math.abs(item.saldo))})</td>
                                                    </tr>
                                                ))}
                                                <tr className="bg-orange-100/50 font-bold">
                                                    <td colSpan="2" className="px-6 py-3 text-right text-sm text-orange-900">TOTAL GASTOS</td>
                                                    <td className="px-6 py-3 text-right text-sm font-mono text-orange-900">({formatNumber(Math.abs(reportData.totales.total_gastos))})</td>
                                                </tr>
                                            </>
                                        )}

                                        {/* UTILIDAD NETA */}
                                        <tr className={`border-t-4 border-indigo-500 text-white ${reportData.totales.utilidad_neta >= 0 ? 'bg-slate-800' : 'bg-red-900'}`}>
                                            <td colSpan="2" className="px-6 py-6 text-right text-base font-bold uppercase tracking-wider">UTILIDAD NETA DEL EJERCICIO</td>
                                            <td className={`px-6 py-6 text-right text-2xl font-mono font-bold ${reportData.totales.utilidad_neta >= 0 ? 'text-green-400' : 'text-white'}`}>
                                                {formatNumber(reportData.totales.utilidad_neta)}
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </>
    );
}