'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
    FaBalanceScale,
    FaCalendarAlt,
    FaSearch,
    FaFilePdf,
    FaFilter,
    FaLayerGroup,
    FaBuilding,
    FaExclamationTriangle
} from 'react-icons/fa';

import {
    FaBook,
} from 'react-icons/fa';


import { useAuth } from '../../../context/AuthContext';
import { getBalanceDePruebaCC, getSignedUrlForBalanceDePruebaCC } from '../../../../lib/reportesService';
import { apiService } from '../../../../lib/apiService';

// Estilos Reusables (Manual v2.0)
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none pl-10";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white pl-10";

export default function BalancePruebaCCPage() {
    const { user, loading: authLoading } = useAuth();
    const router = useRouter();

    const [filtros, setFiltros] = useState({
        fecha_inicio: new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0],
        fecha_fin: new Date().toISOString().split('T')[0],
        nivel_maximo: 4,
        filtro_centros_costo: 'CON_SALDO_O_MOVIMIENTO',
        cuenta_id: ''
    });

    const [reportData, setReportData] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [isPageReady, setPageReady] = useState(false);

    const [maestros, setMaestros] = useState({ cuentas: [] });

    // Verificación de sesión y carga inicial
    useEffect(() => {
        if (!authLoading) {
            if (user && user.empresaId) {
                setPageReady(true);
                const fetchMaestros = async () => {
                    try {
                        const cuentasRes = await apiService.get('/plan-cuentas/list-flat/?permite_movimiento=true');
                        setMaestros({ cuentas: cuentasRes.data || [] });
                    } catch (error) {
                        console.error("Error cargando maestros:", error);
                    }
                };
                fetchMaestros();
            } else {
                router.push('/login');
            }
        }
    }, [user, authLoading, router]);

    const handleFiltroChange = (e) => {
        const { name, value } = e.target;
        setFiltros(prev => ({ ...prev, [name]: value }));
    };

    const preparePayload = (filtrosActuales) => {
        const payload = { ...filtrosActuales };
        if (payload.cuenta_id === '') delete payload.cuenta_id;
        return payload;
    };

    const handleGenerateReport = async () => {
        if (!filtros.fecha_inicio || !filtros.fecha_fin) {
            setError("Por favor, seleccione una fecha de inicio y fin.");
            return;
        }
        setIsLoading(true);
        setError('');
        setReportData(null);
        try {
            const payloadLimpio = preparePayload(filtros);
            const { data } = await getBalanceDePruebaCC(payloadLimpio);
            setReportData(data);
        } catch (err) {
            const errorMsg = err.response?.data?.detail?.[0]?.msg || err.response?.data?.detail || 'Error al generar el reporte.';
            setError(errorMsg);
        } finally {
            setIsLoading(false);
        }
    };

    const handleExportPDF = async () => {
        if (!reportData) {
            setError("Primero debe generar un reporte para poder exportarlo.");
            return;
        }
        setIsLoading(true);
        setError('');
        try {
            const payloadLimpio = preparePayload(filtros);
            const { data } = await getSignedUrlForBalanceDePruebaCC(payloadLimpio);
            const token = data.signed_url_token;
            const pdfUrl = `${process.env.NEXT_PUBLIC_API_URL}/api/reports/balance-de-prueba-cc/imprimir?signed_token=${token}`;

            // Descarga directa
            const link = document.createElement('a');
            link.href = pdfUrl;
            link.setAttribute('download', `Balance_Prueba_CC_${filtros.fecha_inicio}_${filtros.fecha_fin}.pdf`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

        } catch (err) {
            const errorMsg = err.response?.data?.detail || 'Error al generar el PDF.';
            setError(errorMsg);
        } finally {
            setIsLoading(false);
        }
    };

    const formatCurrency = (value) => {
        return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 2 }).format(value || 0);
    };

    // Estilos jerárquicos visuales
    const getNivelClass = (nivel) => {
        switch (nivel) {
            case 1: return 'bg-indigo-50 font-bold text-indigo-900';
            case 2: return 'bg-slate-50 font-semibold text-slate-800';
            case 3: return 'text-gray-700 font-medium';
            default: return 'text-gray-600';
        }
    };

    const getPaddingClass = (nivel) => {
        switch (nivel) {
            case 1: return '';
            case 2: return 'pl-6';
            case 3: return 'pl-10';
            default: return 'pl-14 border-l-2 border-indigo-100';
        }
    };

    if (!isPageReady) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
                <FaBalanceScale className="text-indigo-300 text-6xl mb-4 animate-pulse" />
                <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando Balance por CC...</p>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
            <div className="max-w-7xl mx-auto">

                {/* ENCABEZADO */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                    <div>
                        <div className="flex items-center gap-3 mt-3">
                            <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                                <FaBuilding className="text-2xl" />
                            </div>
                            <div>
                                <div className="flex items-center gap-4">
                                    <h1 className="text-3xl font-bold text-gray-800">Balance de Prueba por CC</h1>
                                    <button
                                        onClick={() => window.open('/manual/capitulo_54_balance_prueba_cc.html', '_blank')}
                                        className="flex items-center gap-2 px-2 py-1 bg-white border border-indigo-200 text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors font-medium shadow-sm"
                                        type="button"
                                        title="Ver Manual de Usuario"
                                    >
                                        <span className="text-lg">📖</span> <span className="font-bold text-sm hidden md:inline">Manual</span>
                                    </button>
                                </div>
                                <p className="text-gray-500 text-sm">Análisis de saldos desagregado por centros de costo.</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* CARD 1: FILTROS */}
                <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 animate-fadeIn mb-8">
                    <div className="flex items-center gap-2 mb-6 border-b border-gray-100 pb-2">
                        <FaFilter className="text-indigo-500" />
                        <h2 className="text-lg font-bold text-gray-700">Criterios de Búsqueda</h2>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 items-end">

                        {/* Fechas */}
                        <div>
                            <label className={labelClass}>Desde</label>
                            <div className="relative">
                                <input type="date" name="fecha_inicio" value={filtros.fecha_inicio} onChange={handleFiltroChange} className={inputClass} />
                                <FaCalendarAlt className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                            </div>
                        </div>
                        <div>
                            <label className={labelClass}>Hasta</label>
                            <div className="relative">
                                <input type="date" name="fecha_fin" value={filtros.fecha_fin} onChange={handleFiltroChange} className={inputClass} />
                                <FaCalendarAlt className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                            </div>
                        </div>

                        {/* Cuenta (Opcional) */}
                        <div>
                            <label className={labelClass}>Cuenta Contable</label>
                            <div className="relative">
                                <select name="cuenta_id" value={filtros.cuenta_id} onChange={handleFiltroChange} className={selectClass}>
                                    <option value="">Todas las Cuentas</option>
                                    {maestros.cuentas.map(cuenta => (
                                        <option key={cuenta.id} value={cuenta.id}>{cuenta.codigo} - {cuenta.nombre}</option>
                                    ))}
                                </select>
                                <FaSearch className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                            </div>
                        </div>

                        {/* Nivel */}
                        <div>
                            <label className={labelClass}>Nivel de Detalle</label>
                            <div className="relative">
                                <select name="nivel_maximo" value={filtros.nivel_maximo} onChange={handleFiltroChange} className={selectClass}>
                                    <option value="1">1 (Nivel Principal)</option>
                                    <option value="2">2 (Intermedio)</option>
                                    <option value="3">3 (Detallado)</option>
                                    <option value="4">4 (Completo)</option>
                                </select>
                                <FaLayerGroup className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                            </div>
                        </div>

                        {/* Filtro CC */}
                        <div className="lg:col-span-2">
                            <label className={labelClass}>Mostrar Centros de Costo</label>
                            <div className="relative">
                                <select name="filtro_centros_costo" value={filtros.filtro_centros_costo} onChange={handleFiltroChange} className={selectClass}>
                                    <option value="CON_SALDO_O_MOVIMIENTO">Con Saldo o Movimiento</option>
                                    <option value="CON_MOVIMIENTO">Solo con Movimiento en el Periodo</option>
                                    <option value="TODAS">Todos (Incluso sin saldo)</option>
                                </select>
                                <FaFilter className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                            </div>
                        </div>

                        {/* Botones */}
                        <div className="lg:col-span-2 flex gap-3">
                            <button
                                onClick={handleGenerateReport}
                                disabled={isLoading}
                                className={`
                            flex-1 px-6 py-2 rounded-lg shadow-md font-bold text-white transition-all transform hover:-translate-y-0.5 flex items-center justify-center gap-2
                            ${isLoading ? 'bg-gray-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'}
                        `}
                            >
                                {isLoading ? <span className="loading loading-spinner loading-sm"></span> : <><FaSearch /> Generar Reporte</>}
                            </button>

                            <button
                                onClick={handleExportPDF}
                                disabled={!reportData || isLoading}
                                className={`
                            px-6 py-2 rounded-lg shadow-md font-bold border transition-all transform hover:-translate-y-0.5 flex items-center justify-center gap-2
                            ${!reportData || isLoading
                                        ? 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed'
                                        : 'bg-white text-red-600 border-red-100 hover:bg-red-50'}
                        `}
                            >
                                <FaFilePdf /> Exportar PDF
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

                {/* CARD 2: RESULTADOS */}
                {reportData ? (
                    <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden animate-slideDown">
                        <div className="p-6 bg-gray-50 border-b border-gray-200 flex flex-col md:flex-row justify-between items-center gap-4">
                            <div>
                                <h2 className="text-xl font-bold text-gray-800">{user?.nombre_empresa}</h2>
                                <p className="text-sm text-gray-600 font-medium mt-1">
                                    Balance de Prueba por CC: <span className="text-indigo-600">{filtros.fecha_inicio}</span> al <span className="text-indigo-600">{filtros.fecha_fin}</span>
                                </p>
                            </div>
                        </div>

                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-slate-100">
                                    <tr>
                                        <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider w-24">Código</th>
                                        <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">Centro de Costo</th>
                                        <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase tracking-wider w-32 bg-slate-50">Saldo Inicial</th>
                                        <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase tracking-wider w-32">Débitos</th>
                                        <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase tracking-wider w-32">Créditos</th>
                                        <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase tracking-wider w-32 bg-slate-50">Nuevo Saldo</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-100 text-sm">
                                    {reportData.filas.length === 0 ? (
                                        <tr><td colSpan="6" className="text-center py-8 text-gray-400 italic">No hay datos para mostrar.</td></tr>
                                    ) : (
                                        reportData.filas.map(fila => (
                                            <tr key={fila.codigo} className={`hover:bg-indigo-50/20 transition-colors ${getNivelClass(fila.nivel)}`}>
                                                <td className="px-4 py-2 font-mono text-sm whitespace-nowrap">{fila.codigo}</td>
                                                <td className={`px-4 py-2 text-sm ${getPaddingClass(fila.nivel)}`}>{fila.nombre}</td>
                                                <td className="px-4 py-2 text-right font-mono text-sm bg-slate-50/50">{formatCurrency(fila.saldo_inicial)}</td>
                                                <td className="px-4 py-2 text-right font-mono text-sm">{formatCurrency(fila.debito)}</td>
                                                <td className="px-4 py-2 text-right font-mono text-sm">{formatCurrency(fila.credito)}</td>
                                                <td className="px-4 py-2 text-right font-mono text-sm font-bold bg-slate-50/50">{formatCurrency(fila.nuevo_saldo)}</td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>

                                {/* Footer Totales */}
                                <tfoot className="bg-slate-800 text-white border-t-4 border-indigo-500">
                                    <tr>
                                        <td colSpan="2" className="px-4 py-4 text-right text-sm font-bold uppercase tracking-wider">Totales Generales:</td>
                                        <td className="px-4 py-4 text-right font-mono font-bold text-slate-300">{formatCurrency(reportData.totales.saldo_inicial)}</td>
                                        <td className="px-4 py-4 text-right font-mono font-bold text-green-400">{formatCurrency(reportData.totales.debito)}</td>
                                        <td className="px-4 py-4 text-right font-mono font-bold text-green-400">{formatCurrency(reportData.totales.credito)}</td>
                                        <td className="px-4 py-4 text-right font-mono font-bold text-white">{formatCurrency(reportData.totales.nuevo_saldo)}</td>
                                    </tr>
                                </tfoot>
                            </table>
                        </div>
                    </div>
                ) : (
                    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center text-gray-400 animate-fadeIn">
                        <FaBalanceScale className="text-6xl mx-auto mb-4 opacity-20" />
                        <p>Seleccione los criterios y genere el reporte para ver los resultados.</p>
                    </div>
                )}
            </div>
        </div>
    );
}