'use client';

import React, { useState, useEffect, Suspense } from 'react';
import Script from 'next/script';
import { useRouter } from 'next/navigation';
import {
    FaTruck, // Icono para Proveedor
    FaCalendarAlt,
    FaSearch,
    FaFileCsv,
    FaFilePdf,
    FaMoneyBillWave,
    FaExclamationTriangle,
    FaClock,
    FaCheckCircle
} from 'react-icons/fa';


import { useAuth } from '../../../context/AuthContext';
import { apiService } from '../../../../lib/apiService';

// --- ESTILOS REUSABLES (Manual v2.0) ---
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none pl-10";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white pl-10";

function EstadoCuentaProveedorContent() {
    const { user, authLoading } = useAuth();
    const router = useRouter();

    const [filtros, setFiltros] = useState({
        terceroId: '',
        fechaFin: new Date().toISOString().split('T')[0]
    });

    const [terceros, setTerceros] = useState([]);
    const [reportData, setReportData] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [isPageReady, setPageReady] = useState(false);

    // Autenticación
    useEffect(() => {
        if (!authLoading) {
            if (user && user.empresaId) {
                setPageReady(true);
            } else {
                router.push('/login');
            }
        }
    }, [user, authLoading, router]);

    // Carga de Proveedores
    useEffect(() => {
        if (user?.empresaId) {
            const fetchTerceros = async () => {
                try {
                    const response = await apiService.get('/terceros', { params: { es_proveedor: true } });
                    setTerceros(response.data || []);
                } catch (err) {
                    setError("Error al cargar la lista de proveedores: " + (err.response?.data?.detail || err.message));
                }
            };
            fetchTerceros();
        }
    }, [user]);

    const handleFiltroChange = (e) => {
        const { name, value } = e.target;
        setFiltros(prev => ({ ...prev, [name]: value }));
    };

    const handleGenerateReport = async () => {
        if (!filtros.terceroId || !filtros.fechaFin) {
            setError("Por favor, seleccione un proveedor y una fecha de corte.");
            return;
        }
        setIsLoading(true);
        setError(null);
        setReportData(null);
        try {
            const response = await apiService.get('/reports/estado-cuenta-proveedor', {
                params: {
                    tercero_id: filtros.terceroId,
                    fecha_fin: filtros.fechaFin
                }
            });
            setReportData(response.data);
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al generar el reporte.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleExportCSV = () => {
        if (!reportData || !reportData.facturas) return alert("No hay datos para exportar.");
        if (typeof window.Papa === 'undefined') return alert("La librería CSV no está lista.");

        const dataParaCSV = reportData.facturas.map(f => ({
            "Documento": `${f.tipo_documento}-${f.numero}`,
            "Fecha": new Date(f.fecha + 'T00:00:00').toLocaleDateString('es-CO'),
            "Valor Deuda": f.valor_original,
            "Pagos Realizados": f.abonos,
            "Saldo por Pagar": f.saldo_pendiente,
            "Dias Mora": f.dias_mora,
            "Estado": f.estado
        }));

        dataParaCSV.push({});
        dataParaCSV.push({ "Documento": "SALDO TOTAL POR PAGAR:", "Saldo por Pagar": reportData.saldoTotal });

        const csv = window.Papa.unparse(dataParaCSV);
        const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.setAttribute('download', `Estado_Cuenta_Prov_${reportData.proveedorInfo.razon_social}_${filtros.fechaFin}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const handleExportPDF = async () => {
        if (!reportData) return alert("Primero debe generar un reporte.");
        setIsLoading(true);
        setError('');
        try {
            const response = await apiService.get('/reports/estado-cuenta-proveedor/get-signed-url', {
                params: {
                    tercero_id: filtros.terceroId,
                    fecha_fin: filtros.fechaFin
                }
            });
            const signedToken = response.data.signed_url_token;
            const pdfUrl = `${process.env.NEXT_PUBLIC_API_URL}/api/reports/estado-cuenta-proveedor/imprimir?signed_token=${signedToken}`;

            // ABRIR EN NUEVA PESTAÑA (Request Usuario)
            window.open(pdfUrl, '_blank');

        } catch (err) {
            setError(err.response?.data?.detail || "Error al exportar PDF.");
        } finally {
            setIsLoading(false);
        }
    };

    const formatCurrency = (value) => {
        if (value === null || value === undefined) return '$ 0';
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(value);
    };

    if (!isPageReady) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
                <FaTruck className="text-indigo-300 text-6xl mb-4 animate-pulse" />
                <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando Cuentas por Pagar...</p>
            </div>
        );
    }

    return (
        <>
            <Script src="https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js" />

            <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
                <div className="max-w-5xl mx-auto">

                    {/* ENCABEZADO */}
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                        <div>
                            <div className="flex items-center gap-3 mt-3">
                                <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                                    <FaTruck className="text-2xl" />
                                </div>
                                <div>
                                    <h1 className="text-3xl font-bold text-gray-800">Estado de Cuenta (Proveedores)</h1>
                                    <p className="text-gray-500 text-sm">Análisis de cuentas por pagar y vencimientos.</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* CARD 1: FILTROS */}
                    <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 animate-fadeIn mb-8">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-end">

                            {/* Proveedor */}
                            <div className="md:col-span-1">
                                <label htmlFor="terceroId" className={labelClass}>Proveedor</label>
                                <div className="relative">
                                    <select
                                        id="terceroId"
                                        name="terceroId"
                                        value={filtros.terceroId}
                                        onChange={handleFiltroChange}
                                        className={selectClass}
                                    >
                                        <option value="">Seleccione un proveedor...</option>
                                        {terceros.map(t => (<option key={t.id} value={t.id}>{t.razon_social}</option>))}
                                    </select>
                                    <FaTruck className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                </div>
                            </div>

                            {/* Fecha Corte */}
                            <div className="md:col-span-1">
                                <label htmlFor="fechaFin" className={labelClass}>Fecha de Corte</label>
                                <div className="relative">
                                    <input
                                        type="date"
                                        name="fechaFin"
                                        value={filtros.fechaFin}
                                        onChange={handleFiltroChange}
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
                                    {isLoading ? <span className="loading loading-spinner loading-sm"></span> : <><FaSearch /> Generar Estado</>}
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
                    {reportData && (
                        <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden animate-slideDown">

                            {/* Cabecera Reporte */}
                            <div className="p-6 bg-gray-50 border-b border-gray-200 flex flex-col md:flex-row justify-between items-center gap-4">
                                <div>
                                    <h2 className="text-xl font-bold text-gray-800">{reportData.proveedorInfo?.razon_social}</h2>
                                    <p className="text-sm text-gray-600 font-mono mt-1">NIT: {reportData.proveedorInfo?.nit}</p>
                                </div>
                                <div className="flex gap-3">
                                    <button onClick={handleExportCSV} disabled={isLoading} className="flex items-center gap-2 px-4 py-2 bg-white border border-green-500 text-green-600 rounded-lg hover:bg-green-50 font-medium transition-colors shadow-sm disabled:opacity-50"><FaFileCsv /> CSV</button>
                                    <button onClick={handleExportPDF} disabled={isLoading} className="flex items-center gap-2 px-4 py-2 bg-white border border-red-500 text-red-600 rounded-lg hover:bg-red-50 font-medium transition-colors shadow-sm disabled:opacity-50"><FaFilePdf /> PDF</button>
                                </div>
                            </div>

                            {/* Tabla */}
                            <div className="overflow-x-auto">
                                <table className="min-w-full divide-y divide-gray-200">
                                    <thead className="bg-slate-100">
                                        <tr>
                                            <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">Documento</th>
                                            <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">Emisión</th>
                                            <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase tracking-wider">Valor Deuda</th>
                                            <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase tracking-wider">Pagos</th>
                                            <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase tracking-wider bg-slate-200/50">Saldo Pagar</th>
                                            <th className="px-4 py-3 text-center text-xs font-bold text-gray-600 uppercase tracking-wider">Estado</th>
                                        </tr>
                                    </thead>
                                    <tbody className="bg-white divide-y divide-gray-100">
                                        {(!reportData.facturas || reportData.facturas.length === 0) ? (
                                            <tr><td colSpan="6" className="text-center py-10 text-gray-400 italic">No hay deudas pendientes con este proveedor.</td></tr>
                                        ) : (
                                            reportData.facturas.map((factura) => (
                                                <tr key={factura.id} className="hover:bg-indigo-50/20 transition-colors">
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-800">
                                                        {factura.tipo_documento}-{factura.numero}
                                                    </td>
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600 font-mono">
                                                        {new Date(factura.fecha + 'T00:00:00').toLocaleDateString('es-CO')}
                                                    </td>
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-right font-mono text-gray-700">
                                                        {formatCurrency(factura.valor_original)}
                                                    </td>
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-right font-mono text-green-600">
                                                        ({formatCurrency(factura.abonos)})
                                                    </td>
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-right font-bold font-mono text-indigo-900 bg-slate-50">
                                                        {formatCurrency(factura.saldo_pendiente)}
                                                    </td>
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-center">
                                                        {factura.estado === 'VENCIDA' ? (
                                                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                                                <FaExclamationTriangle className="mr-1" /> {factura.dias_mora} días mora
                                                            </span>
                                                        ) : (
                                                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                                                <FaClock className="mr-1" /> Vence en {factura.dias_para_vencer} días
                                                            </span>
                                                        )}
                                                    </td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>

                                    {/* Footer Saldo Total */}
                                    <tfoot className="bg-slate-800 text-white border-t-4 border-indigo-500">
                                        <tr>
                                            <td colSpan="4" className="px-4 py-4 text-right text-sm font-bold uppercase tracking-wider">Total Deuda Proveedor:</td>
                                            <td className="px-4 py-4 text-right font-mono font-bold text-xl text-white bg-slate-700">
                                                {formatCurrency(reportData.saldoTotal)}
                                            </td>
                                            <td></td>
                                        </tr>
                                    </tfoot>
                                </table>
                            </div>

                            {/* DASHBOARD DE EDADES (AGING) */}
                            {reportData.edades && (
                                <div className="p-6 bg-gray-50 border-t border-gray-200">
                                    <h3 className="text-sm font-bold text-gray-500 uppercase mb-4">Análisis de Vencimientos (Aging)</h3>
                                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                                        <div className="bg-green-100 p-4 rounded-xl border border-green-200 text-center">
                                            <p className="text-xs font-bold text-green-700 uppercase">Por Vencer</p>
                                            <p className="text-lg font-bold text-green-900 font-mono mt-1">{formatCurrency(reportData.edades.por_vencer)}</p>
                                        </div>
                                        <div className="bg-yellow-50 p-4 rounded-xl border border-yellow-200 text-center">
                                            <p className="text-xs font-bold text-yellow-700 uppercase">1-30 Días</p>
                                            <p className="text-lg font-bold text-yellow-900 font-mono mt-1">{formatCurrency(reportData.edades.vencida_1_30)}</p>
                                        </div>
                                        <div className="bg-orange-50 p-4 rounded-xl border border-orange-200 text-center">
                                            <p className="text-xs font-bold text-orange-700 uppercase">31-60 Días</p>
                                            <p className="text-lg font-bold text-orange-900 font-mono mt-1">{formatCurrency(reportData.edades.vencida_31_60)}</p>
                                        </div>
                                        <div className="bg-red-50 p-4 rounded-xl border border-red-200 text-center">
                                            <p className="text-xs font-bold text-red-700 uppercase">61-90 Días</p>
                                            <p className="text-lg font-bold text-red-900 font-mono mt-1">{formatCurrency(reportData.edades.vencida_61_90)}</p>
                                        </div>
                                        <div className="bg-rose-100 p-4 rounded-xl border border-rose-200 text-center">
                                            <p className="text-xs font-bold text-rose-900 uppercase">+90 Días</p>
                                            <p className="text-lg font-bold text-rose-900 font-mono mt-1">{formatCurrency(reportData.edades.vencida_mas_90)}</p>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </>
    );
}