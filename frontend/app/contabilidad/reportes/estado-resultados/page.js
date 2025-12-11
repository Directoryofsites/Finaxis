'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Script from 'next/script';
import {
    FaChartLine,
    FaCalendarAlt,
    FaSearch,
    FaFilePdf,
    FaFileCsv,
    FaMoneyBillWave,
    FaShoppingCart,
    FaCalculator,
    FaExclamationTriangle,
    FaBook
} from 'react-icons/fa';

import BotonRegresar from '../../../components/BotonRegresar';
import { useAuth } from '../../../context/AuthContext';
import { apiService } from '../../../../lib/apiService';

// Estilos Reusables (Manual v2.0)
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none pl-10";

export default function EstadoResultadosPage() {
    const { user, loading: authLoading } = useAuth();
    const router = useRouter();

    const [reporte, setReporte] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [fechaInicio, setFechaInicio] = useState('');
    const [fechaFin, setFechaFin] = useState('');
    const [isPageReady, setPageReady] = useState(false);

    useEffect(() => {
        if (!authLoading) {
            if (user && user.empresaId) {
                setPageReady(true);
            } else {
                router.push('/login');
            }
        }
    }, [user, authLoading, router]);

    const handleGenerateReport = async () => {
        if (!fechaInicio || !fechaFin) {
            setError("Por favor, seleccione una fecha de inicio y una fecha de fin.");
            return;
        }
        setIsLoading(true);
        setError(null);
        setReporte(null);

        const params = {
            fecha_inicio: fechaInicio,
            fecha_fin: fechaFin,
        };

        try {
            const res = await apiService.get('/reports/income-statement', { params: params });
            setReporte(res.data);
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al generar el reporte de Estado de Resultados.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleExportCSV = () => {
        if (!reporte) return;
        if (typeof window.Papa === 'undefined') {
            alert("La librería CSV no está lista. Por favor, recargue la página.");
            return;
        }

        const dataParaCSV = [];
        const formatNumber = (num) => (num || 0).toFixed(2);
        const totales = reporte.totales;

        dataParaCSV.push({ Seccion: 'INGRESOS', Codigo: '', Cuenta: '', Saldo: '' });
        reporte.ingresos.forEach(item => { dataParaCSV.push({ Seccion: '', Codigo: item.codigo, Cuenta: item.nombre, Saldo: formatNumber(item.saldo) }); });
        dataParaCSV.push({ Cuenta: 'TOTAL INGRESOS', Saldo: formatNumber(totales.total_ingresos) });
        dataParaCSV.push({});

        if (reporte.costos && reporte.costos.length > 0) {
            dataParaCSV.push({ Seccion: 'COSTOS DE VENTA' });
            reporte.costos.forEach(item => { dataParaCSV.push({ Seccion: '', Codigo: item.codigo, Cuenta: item.nombre, Saldo: formatNumber(item.saldo) }); });
            dataParaCSV.push({ Cuenta: 'TOTAL COSTOS', Saldo: formatNumber(totales.total_costos) });
            dataParaCSV.push({});
        }

        dataParaCSV.push({ Cuenta: 'UTILIDAD BRUTA', Saldo: formatNumber(totales.utilidad_bruta) });
        dataParaCSV.push({});

        if (reporte.gastos && reporte.gastos.length > 0) {
            dataParaCSV.push({ Seccion: 'GASTOS OPERACIONALES' });
            reporte.gastos.forEach(item => { dataParaCSV.push({ Seccion: '', Codigo: item.codigo, Cuenta: item.nombre, Saldo: formatNumber(item.saldo) }); });
            dataParaCSV.push({ Cuenta: 'TOTAL GASTOS', Saldo: formatNumber(totales.total_gastos) });
            dataParaCSV.push({});
        }

        dataParaCSV.push({ Cuenta: 'UTILIDAD NETA DEL EJERCICIO', Saldo: formatNumber(totales.utilidad_neta) });

        const csv = window.Papa.unparse(dataParaCSV);
        const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `estado-resultados-${fechaInicio}-al-${fechaFin}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const handleExportPDF = async () => {
        if (!reporte) return;
        setIsLoading(true);
        setError(null);
        try {
            const paramsForSignedUrl = {
                fecha_inicio: fechaInicio,
                fecha_fin: fechaFin,
            };
            const signedUrlRes = await apiService.get('/reports/income-statement/get-signed-url', { params: paramsForSignedUrl });
            const signedToken = signedUrlRes.data.signed_url_token;
            const finalPdfUrl = `${process.env.NEXT_PUBLIC_API_URL}/api/reports/income-statement/imprimir?signed_token=${signedToken}`;

            const link = document.createElement('a');
            link.href = finalPdfUrl;
            link.setAttribute('download', `Estado_Resultados_${fechaInicio}_${fechaFin}.pdf`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

        } catch (err) {
            setError(err.response?.data?.detail || 'Error al obtener la URL firmada para el PDF.');
        } finally {
            setIsLoading(false);
        }
    };

    const formatCurrency = (val) => {
        return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 2 }).format(val);
    };

    if (!isPageReady) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
                <FaChartLine className="text-indigo-300 text-6xl mb-4 animate-pulse" />
                <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando Estado de Resultados...</p>
            </div>
        );
    }

    const AccountRow = ({ codigo, nombre, saldo, isNegative = false }) => (
        <div className="flex justify-between items-center py-2 border-b border-gray-100 hover:bg-gray-50 transition-colors px-2 rounded">
            <div className="flex flex-col md:flex-row md:items-center gap-1 md:gap-3">
                <span className="font-mono text-xs font-bold px-2 py-0.5 rounded-md bg-gray-100 text-gray-600">{codigo}</span>
                <span className="text-sm text-gray-700 font-medium">{nombre}</span>
            </div>
            <span className={`font-mono text-sm font-bold ${isNegative ? 'text-red-600' : 'text-gray-800'}`}>
                {isNegative ? `(${formatCurrency(Math.abs(saldo))})` : formatCurrency(saldo)}
            </span>
        </div>
    );

    return (
        <>
            <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
                <div className="max-w-5xl mx-auto">

                    {/* ENCABEZADO */}
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                        <div>
                            <BotonRegresar />
                            <div className="flex items-center gap-3 mt-3">
                                <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                                    <FaChartLine className="text-2xl" />
                                </div>
                                <div>
                                    <h1 className="text-3xl font-bold text-gray-800">Estado de Resultados</h1>
                                    <p className="text-gray-500 text-sm">Análisis de rentabilidad: Ingresos, Costos y Gastos.</p>
                                </div>
                            </div>
                        </div>
                        <button
                            onClick={() => window.open('/manual/capitulo_29_estado_resultados.html', '_blank')}
                            className="text-indigo-600 hover:bg-indigo-50 px-3 py-1 rounded-md flex items-center gap-2 transition-colors"
                            title="Ver Manual de Usuario"
                        >
                            <FaBook className="text-lg" /> <span className="font-bold text-sm">Manual</span>
                        </button>
                    </div>

                    {/* CARD 1: FILTROS */}
                    <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 animate-fadeIn mb-8">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-end">
                            <div>
                                <label htmlFor="fechaInicio" className={labelClass}>Fecha Inicio</label>
                                <div className="relative">
                                    <input
                                        type="date"
                                        id="fechaInicio"
                                        value={fechaInicio}
                                        onChange={(e) => setFechaInicio(e.target.value)}
                                        className={inputClass}
                                    />
                                    <FaCalendarAlt className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                </div>
                            </div>
                            <div>
                                <label htmlFor="fechaFin" className={labelClass}>Fecha Fin</label>
                                <div className="relative">
                                    <input
                                        type="date"
                                        id="fechaFin"
                                        value={fechaFin}
                                        onChange={(e) => setFechaFin(e.target.value)}
                                        className={inputClass}
                                    />
                                    <FaCalendarAlt className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                </div>
                            </div>

                            <div className="flex flex-col md:flex-row justify-end gap-3">
                                <button
                                    onClick={handleGenerateReport}
                                    disabled={isLoading}
                                    className={`
                                w-full md:w-auto px-6 py-2 rounded-lg shadow-md font-bold text-white transition-all transform hover:-translate-y-0.5 flex items-center justify-center gap-2
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

                    {/* CARD 2: REPORTE */}
                    {reporte && (
                        <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden animate-slideDown">
                            {/* Cabecera Reporte */}
                            <div className="p-6 bg-gray-50 border-b border-gray-200 flex flex-col md:flex-row justify-between items-center gap-4">
                                <div>
                                    <h2 className="text-xl font-bold text-gray-800">{user?.nombre_empresa}</h2>
                                    <p className="text-sm text-gray-600 font-medium mt-1">
                                        Periodo: <span className="text-indigo-600">{fechaInicio}</span> al <span className="text-indigo-600">{fechaFin}</span>
                                    </p>
                                </div>
                                <div className="flex gap-3">
                                    <button onClick={handleExportCSV} disabled={isLoading} className="flex items-center gap-2 px-4 py-2 bg-white border border-green-500 text-green-600 rounded-lg hover:bg-green-50 font-medium transition-colors shadow-sm disabled:opacity-50"><FaFileCsv /> CSV</button>
                                    <button onClick={handleExportPDF} disabled={isLoading} className="flex items-center gap-2 px-4 py-2 bg-white border border-red-500 text-red-600 rounded-lg hover:bg-red-50 font-medium transition-colors shadow-sm disabled:opacity-50"><FaFilePdf /> PDF</button>
                                </div>
                            </div>

                            <div className="p-6 space-y-8">

                                {/* INGRESOS */}
                                <section>
                                    <div className="flex items-center gap-2 mb-4 pb-2 border-b-2 border-emerald-100">
                                        <div className="p-2 bg-emerald-100 text-emerald-600 rounded-lg"><FaMoneyBillWave /></div>
                                        <h3 className="text-xl font-bold text-gray-700">Ingresos Operacionales</h3>
                                    </div>
                                    <div className="pl-2 md:pl-4 space-y-1">
                                        {reporte.ingresos.map(item => <AccountRow key={item.codigo} {...item} />)}
                                    </div>
                                    <div className="flex justify-between items-center mt-3 pt-3 border-t border-gray-200 bg-emerald-50/50 p-3 rounded-lg">
                                        <span className="font-bold text-gray-700 uppercase text-sm">Total Ingresos</span>
                                        <span className="font-mono text-lg font-bold text-emerald-700">{formatCurrency(reporte.totales.total_ingresos)}</span>
                                    </div>
                                </section>

                                {/* COSTOS */}
                                {reporte.costos && reporte.costos.length > 0 && (
                                    <section>
                                        <div className="flex items-center gap-2 mb-4 pb-2 border-b-2 border-rose-100">
                                            <div className="p-2 bg-rose-100 text-rose-600 rounded-lg"><FaShoppingCart /></div>
                                            <h3 className="text-xl font-bold text-gray-700">Costos de Venta</h3>
                                        </div>
                                        <div className="pl-2 md:pl-4 space-y-1">
                                            {reporte.costos.map(item => <AccountRow key={item.codigo} {...item} isNegative={true} />)}
                                        </div>
                                        <div className="flex justify-between items-center mt-3 pt-3 border-t border-gray-200 bg-rose-50/50 p-3 rounded-lg">
                                            <span className="font-bold text-gray-700 uppercase text-sm">Total Costos</span>
                                            <span className="font-mono text-lg font-bold text-rose-700">({formatCurrency(Math.abs(reporte.totales.total_costos))})</span>
                                        </div>
                                    </section>
                                )}

                                {/* UTILIDAD BRUTA */}
                                <div className="bg-slate-100 p-4 rounded-lg border border-slate-200 flex justify-between items-center">
                                    <span className="font-bold text-gray-800 uppercase">Utilidad Bruta</span>
                                    <span className="font-mono text-xl font-bold text-gray-900">{formatCurrency(reporte.totales.utilidad_bruta)}</span>
                                </div>

                                {/* GASTOS */}
                                {reporte.gastos && reporte.gastos.length > 0 && (
                                    <section>
                                        <div className="flex items-center gap-2 mb-4 pb-2 border-b-2 border-orange-100">
                                            <div className="p-2 bg-orange-100 text-orange-600 rounded-lg"><FaCalculator /></div>
                                            <h3 className="text-xl font-bold text-gray-700">Gastos Operacionales</h3>
                                        </div>
                                        <div className="pl-2 md:pl-4 space-y-1">
                                            {reporte.gastos.map(item => <AccountRow key={item.codigo} {...item} isNegative={true} />)}
                                        </div>
                                        <div className="flex justify-between items-center mt-3 pt-3 border-t border-gray-200 bg-orange-50/50 p-3 rounded-lg">
                                            <span className="font-bold text-gray-700 uppercase text-sm">Total Gastos</span>
                                            <span className="font-mono text-lg font-bold text-orange-700">({formatCurrency(Math.abs(reporte.totales.total_gastos))})</span>
                                        </div>
                                    </section>
                                )}

                                {/* UTILIDAD NETA */}
                                <div className={`p-6 rounded-xl shadow-md border-l-8 flex justify-between items-center ${reporte.totales.utilidad_neta >= 0 ? 'bg-green-50 border-green-500 text-green-900' : 'bg-red-50 border-red-500 text-red-900'}`}>
                                    <div>
                                        <h3 className="text-2xl font-bold uppercase">Utilidad Neta del Ejercicio</h3>
                                        <p className="text-sm opacity-80">Ingresos - Costos - Gastos</p>
                                    </div>
                                    <span className="font-mono text-3xl font-bold">
                                        {formatCurrency(reporte.totales.utilidad_neta)}
                                    </span>
                                </div>

                            </div>
                        </div>
                    )}
                </div>
            </div>

            <Script src="https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js" />
        </>
    );
}