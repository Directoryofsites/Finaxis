'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Script from 'next/script';
import {
    FaListOl,
    FaCalendarAlt,
    FaSearch,
    FaFilePdf,
    FaFileCsv,
    FaFilter,
    FaExclamationTriangle,
    FaBook
} from 'react-icons/fa';

import { useAuth } from '../../../context/AuthContext';
import { apiService } from '../../../../lib/apiService';

// Estilos Reusables (Manual v2.0)
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none pl-10";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white pl-10";

export default function AuxiliarPorCuentaPage() {
    const { user, loading: authLoading } = useAuth();
    const router = useRouter();
    const searchParams = useSearchParams(); // Hook para leer URL

    const [cuentas, setCuentas] = useState([]);
    const [selectedAccount, setSelectedAccount] = useState('');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');

    const [reportData, setReportData] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [isPageReady, setPageReady] = useState(false);
    const [autoRun, setAutoRun] = useState(false); // Flag para ejecución automática

    // Verificación de Sesión y Carga Inicial
    useEffect(() => {
        if (!authLoading) {
            if (user && user.empresaId) {
                setPageReady(true);
                fetchCuentas();
            } else {
                router.push('/login');
            }
        }
    }, [user, authLoading, router]);

    // EFECTO: Leer Parámetros URL y Auto-llenar
    useEffect(() => {
        if (cuentas.length > 0 && searchParams.size > 0 && !autoRun) {
            const pCuenta = searchParams.get('cuenta');
            const pInicio = searchParams.get('fecha_inicio');
            const pFin = searchParams.get('fecha_fin');

            if (pInicio) setStartDate(pInicio);
            if (pFin) setEndDate(pFin);

            if (pCuenta) {
                // Buscamos la cuenta por ID, Código o Nombre (Búsqueda inteligente)
                const term = pCuenta.toLowerCase();
                const matched = cuentas.find(c =>
                    c.id.toString() === pCuenta ||
                    c.codigo === pCuenta ||
                    c.nombre.toLowerCase().includes(term)
                );

                if (matched) {
                    setSelectedAccount(matched.id);
                    // Si tenemos todo, marcamos para ejecución automática
                    if (pInicio && pFin) {
                        setAutoRun(true);
                    }
                }
            }
        }
    }, [cuentas, searchParams, autoRun]);

    // EFECTO: Ejecución Automática una vez seteado el estado
    useEffect(() => {
        if (autoRun && selectedAccount && startDate && endDate) {
            fetchReport(selectedAccount, startDate, endDate);
            setAutoRun(false); // Reset flag para evitar loop
        }
    }, [autoRun, selectedAccount, startDate, endDate]);


    const fetchCuentas = async () => {
        try {
            const res = await apiService.get('/plan-cuentas/');
            const aplanarCuentas = (cuentasArray) => {
                let listaPlana = [];
                cuentasArray.forEach(cuenta => {
                    listaPlana.push({ id: cuenta.id, codigo: cuenta.codigo, nombre: cuenta.nombre });
                    if (cuenta.children && cuenta.children.length > 0) {
                        listaPlana = listaPlana.concat(aplanarCuentas(cuenta.children));
                    }
                });
                return listaPlana;
            };
            setCuentas(aplanarCuentas(res.data));
        } catch (err) {
            setError("Error al cargar el plan de cuentas: " + (err.response?.data?.detail || err.message));
        }
    };

    // Lógica Central de Consulta
    const fetchReport = async (accountId, start, end) => {
        setIsLoading(true);
        setError(null);
        setReportData(null);

        const params = {
            cuenta_id: accountId,
            fecha_inicio: start,
            fecha_fin: end,
        };

        try {
            const res = await apiService.get('/reports/account-ledger', { params: params });
            setReportData(res.data);
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al generar el reporte auxiliar.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleGenerateReport = () => {
        if (!selectedAccount || !startDate || !endDate) {
            setError('Por favor, selecciona una cuenta y un rango de fechas válido.');
            return;
        }
        fetchReport(selectedAccount, startDate, endDate);
    };

    const handleExportToCSV = () => {
        if (!reportData) return;
        if (typeof window.Papa === 'undefined') {
            alert("Librería CSV no cargada. Recargue la página.");
            return;
        }

        const dataToExport = [
            ['Fecha', 'Documento', 'Numero', 'Beneficiario', 'Concepto', 'Debito', 'Credito', 'Saldo Parcial'],
            ['', '', '', '', 'SALDO ANTERIOR', '', '', reportData.saldoAnterior.toFixed(2)],
            ...reportData.movimientos.map(mov => [
                new Date(mov.fecha).toLocaleDateString('es-CO', { timeZone: 'UTC' }),
                mov.tipo_documento,
                mov.numero_documento,
                mov.beneficiario || '',
                mov.concepto.replace(/,/g, ''),
                parseFloat(mov.debito).toFixed(2),
                parseFloat(mov.credito).toFixed(2),
                mov.saldo_parcial.toFixed(2)
            ])
        ];

        const csv = window.Papa.unparse(dataToExport);
        const blob = new Blob(["\uFEFF" + csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        const cuentaNombre = cuentas.find(c => c.id == selectedAccount)?.nombre || 'cuenta';
        link.setAttribute('download', `Auxiliar_${cuentaNombre}_${startDate}_${endDate}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const handleExportPDF = async () => {
        if (!reportData) return;
        setIsLoading(true);
        setError(null);

        try {
            const paramsForSignedUrl = {
                fecha_inicio: startDate,
                fecha_fin: endDate,
                cuenta_id: selectedAccount,
            };

            const signedUrlRes = await apiService.get('/reports/account-ledger/get-signed-url', { params: paramsForSignedUrl });
            const signedToken = signedUrlRes.data.signed_url_token;
            const finalPdfUrl = `${process.env.NEXT_PUBLIC_API_URL}/api/reports/account-ledger/imprimir?signed_token=${signedToken}`;

            // Abrir PDF en nueva pestaña (Solución Bug "Rompe Página")
            window.open(finalPdfUrl, '_blank');

        } catch (err) {
            setError(err.response?.data?.detail || 'Error al obtener el PDF.');
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
                <FaListOl className="text-indigo-300 text-6xl mb-4 animate-pulse" />
                <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando Auxiliar...</p>
            </div>
        );
    }

    return (
        <>
            <Script src="https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js" />

            <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
                <div className="max-w-6xl mx-auto">

                    {/* ENCABEZADO */}
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                        <div>
                            <div className="flex items-center gap-3 mt-3">
                                <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                                    <FaListOl className="text-2xl" />
                                </div>
                                <div>
                                    <div className="flex items-center gap-4">
                                        <h1 className="text-3xl font-bold text-gray-800">Auxiliar por Cuenta</h1>
                                        <button
                                            onClick={() => window.open('/manual/capitulo_31_auxiliar_cuenta.html', '_blank')}
                                            className="text-indigo-600 hover:bg-indigo-50 px-2 py-1 rounded-md flex items-center gap-2 transition-colors"
                                            title="Ver Manual de Usuario"
                                        >
                                            <span className="text-lg">📖</span> <span className="font-bold text-sm hidden md:inline">Manual</span>
                                        </button>
                                    </div>
                                    <p className="text-gray-500 text-sm">Detalle cronológico de movimientos para una cuenta específica.</p>
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

                        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 items-end">
                            {/* Selector de Cuenta */}
                            <div className="md:col-span-2">
                                <label htmlFor="cuenta" className={labelClass}>Cuenta Contable</label>
                                <div className="relative">
                                    <select
                                        id="cuenta"
                                        value={selectedAccount}
                                        onChange={e => setSelectedAccount(e.target.value)}
                                        className={selectClass}
                                    >
                                        <option value="">Seleccione una cuenta...</option>
                                        {cuentas.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
                                    </select>
                                    <FaListOl className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                </div>
                            </div>

                            {/* Fecha Inicio */}
                            <div>
                                <label htmlFor="fecha_inicio" className={labelClass}>Desde</label>
                                <div className="relative">
                                    <input
                                        type="date"
                                        id="fecha_inicio"
                                        value={startDate}
                                        onChange={e => setStartDate(e.target.value)}
                                        className={inputClass}
                                    />
                                    <FaCalendarAlt className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                </div>
                            </div>

                            {/* Fecha Fin */}
                            <div>
                                <label htmlFor="fecha_fin" className={labelClass}>Hasta</label>
                                <div className="relative">
                                    <input
                                        type="date"
                                        id="fecha_fin"
                                        value={endDate}
                                        onChange={e => setEndDate(e.target.value)}
                                        className={inputClass}
                                    />
                                    <FaCalendarAlt className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                </div>
                            </div>
                        </div>

                        <div className="flex justify-end mt-6 pt-4 border-t border-gray-100">
                            <button
                                onClick={handleGenerateReport}
                                disabled={isLoading}
                                className={`
                            px-8 py-2 rounded-lg shadow-md font-bold text-white transition-all transform hover:-translate-y-0.5 flex items-center gap-2
                            ${isLoading ? 'bg-gray-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'}
                        `}
                            >
                                {isLoading ? <span className="loading loading-spinner loading-sm"></span> : <><FaSearch /> Consultar Movimientos</>}
                            </button>
                        </div>
                    </div>

                    {/* MENSAJE ERROR */}
                    {error && (
                        <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded-r-lg flex items-center gap-3 animate-pulse">
                            <FaExclamationTriangle className="text-xl" />
                            <p className="font-bold">{error}</p>
                        </div>
                    )}

                    {/* CARD 2: RESULTADOS */}
                    {reportData && (
                        <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden animate-slideDown">
                            {/* Cabecera Reporte */}
                            <div className="p-6 bg-gray-50 border-b border-gray-200 flex flex-col md:flex-row justify-between items-center gap-4">
                                <div>
                                    <h2 className="text-xl font-bold text-gray-800">
                                        {cuentas.find(c => c.id == selectedAccount)?.codigo} - {cuentas.find(c => c.id == selectedAccount)?.nombre}
                                    </h2>
                                    <p className="text-sm text-gray-600 font-medium mt-1">
                                        Periodo: <span className="text-indigo-600">{startDate}</span> al <span className="text-indigo-600">{endDate}</span>
                                    </p>
                                </div>

                                <div className="flex gap-3">
                                    <button onClick={handleExportToCSV} disabled={isLoading} className="flex items-center gap-2 px-4 py-2 bg-white border border-green-500 text-green-600 rounded-lg hover:bg-green-50 font-medium transition-colors shadow-sm disabled:opacity-50"><FaFileCsv /> CSV</button>
                                    <button onClick={handleExportPDF} disabled={isLoading} className="flex items-center gap-2 px-4 py-2 bg-white border border-red-500 text-red-600 rounded-lg hover:bg-red-50 font-medium transition-colors shadow-sm disabled:opacity-50"><FaFilePdf /> PDF</button>
                                </div>
                            </div>

                            <div className="overflow-x-auto">
                                <table className="min-w-full divide-y divide-gray-200">
                                    <thead className="bg-slate-100">
                                        <tr>
                                            <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">Fecha</th>
                                            <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">Documento</th>
                                            <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">Beneficiario</th>
                                            <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider w-1/4">Concepto</th>
                                            <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase tracking-wider">Débito</th>
                                            <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase tracking-wider">Crédito</th>
                                            <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase tracking-wider bg-slate-200/50">Saldo</th>
                                        </tr>
                                    </thead>
                                    <tbody className="bg-white divide-y divide-gray-100">
                                        {/* Saldo Anterior */}
                                        <tr className="bg-yellow-50">
                                            <td colSpan={6} className="px-4 py-3 text-right text-sm font-bold text-yellow-700 uppercase tracking-wide">
                                                Saldo Anterior al {new Date(startDate + 'T00:00:00').toLocaleDateString('es-CO')}:
                                            </td>
                                            <td className="px-4 py-3 text-right text-sm font-mono font-bold text-yellow-800 bg-yellow-100/50">
                                                {formatCurrency(reportData.saldoAnterior)}
                                            </td>
                                        </tr>

                                        {/* Movimientos */}
                                        {reportData.movimientos.length === 0 ? (
                                            <tr><td colSpan="7" className="text-center py-8 text-gray-400 italic">No hay movimientos en este periodo.</td></tr>
                                        ) : (
                                            reportData.movimientos.map((mov, index) => (
                                                <tr key={index} className="hover:bg-indigo-50/20 transition-colors">
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600 font-mono">
                                                        {new Date(mov.fecha).toLocaleDateString('es-CO', { timeZone: 'UTC' })}
                                                    </td>
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-800">
                                                        {`${mov.tipo_documento} #${mov.numero_documento}`}
                                                    </td>
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600 truncate max-w-xs" title={mov.beneficiario}>
                                                        {mov.beneficiario}
                                                    </td>
                                                    <td className="px-4 py-3 text-sm text-gray-500 italic truncate max-w-xs" title={mov.concepto}>
                                                        {mov.concepto}
                                                    </td>
                                                    <td className="px-4 py-3 text-right text-sm font-mono text-gray-700">
                                                        {parseFloat(mov.debito) > 0 ? formatCurrency(mov.debito) : '-'}
                                                    </td>
                                                    <td className="px-4 py-3 text-right text-sm font-mono text-gray-700">
                                                        {parseFloat(mov.credito) > 0 ? formatCurrency(mov.credito) : '-'}
                                                    </td>
                                                    <td className="px-4 py-3 text-right text-sm font-mono font-bold text-indigo-900 bg-slate-50">
                                                        {formatCurrency(mov.saldo_parcial)}
                                                    </td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>

                                    {/* Saldo Final */}
                                    <tfoot className="bg-slate-800 text-white border-t-4 border-indigo-500">
                                        <tr>
                                            <td colSpan="6" className="px-4 py-4 text-right text-sm font-bold uppercase tracking-wider">Saldo Final a la Fecha:</td>
                                            <td className="px-4 py-4 text-right text-lg font-mono font-bold text-white bg-slate-700">
                                                {(reportData.movimientos.length > 0
                                                    ? formatCurrency(reportData.movimientos[reportData.movimientos.length - 1].saldo_parcial)
                                                    : formatCurrency(reportData.saldoAnterior)
                                                )}
                                            </td>
                                        </tr>
                                    </tfoot>
                                </table>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </>
    );
}