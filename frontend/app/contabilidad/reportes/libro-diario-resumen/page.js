'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Script from 'next/script';
import {
    FaBook,
    FaSearch,
    FaFileCsv,
    FaFilePdf,
    FaCalendarAlt,
    FaFilter,
    FaExclamationTriangle,
    FaListAlt
} from 'react-icons/fa';

import { useAuth } from '../../../../app/context/AuthContext';
import { apiService } from '../../../../lib/apiService';

// Estilos reusables
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white";

export default function LibroDiarioResumenPage() {
    const { user, loading: authLoading } = useAuth();
    const router = useRouter();

    const [reportData, setReportData] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [tiposDocumento, setTiposDocumento] = useState([]);

    // Filtros
    const [filtros, setFiltros] = useState({
        inicio: new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0],
        fin: new Date().toISOString().split('T')[0],
        selectedTipos: [] // Array de IDs
    });

    // Cargar Tipos de Documento
    useEffect(() => {
        if (!authLoading && user) {
            const fetchTiposDocumento = async () => {
                try {
                    const res = await apiService.get('/tipos-documento/');
                    setTiposDocumento(res.data);
                } catch (err) {
                    setError("Fallo al cargar los filtros: " + (err.response?.data?.detail || err.message));
                }
            };
            fetchTiposDocumento();
        }
    }, [user, authLoading]);

    // Handle Multi-Select Change
    const handleTipoDocChange = (e) => {
        const options = e.target.options;
        const selectedValues = [];
        for (let i = 0; i < options.length; i++) {
            if (options[i].selected) {
                selectedValues.push(options[i].value);
            }
        }
        setFiltros(prev => ({ ...prev, selectedTipos: selectedValues }));
    };

    const handleGenerateReport = async () => {
        if (!filtros.inicio || !filtros.fin) {
            setError("Por favor, seleccione un rango de fechas.");
            return;
        }
        setIsLoading(true);
        setError(null);
        setReportData(null);

        const params = {
            fecha_inicio: filtros.inicio,
            fecha_fin: filtros.fin,
        };

        // Convertir array ['1', '2'] a string '1,2'
        if (filtros.selectedTipos.length > 0) {
            params.tipos_documento_ids = filtros.selectedTipos.join(',');
        }

        try {
            const res = await apiService.get('/reports/journal-summary', { params: params });
            setReportData(res.data);
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al cargar los datos del reporte.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleExportCSV = () => {
        if (!reportData) return alert("Primero debe generar un reporte.");
        if (typeof window.Papa === 'undefined') return alert("La librería CSV no está lista.");

        // Aplanar datos agrupados para CSV
        const dataToExport = [];

        reportData.forEach(grupo => {
            // Header de grupo
            dataToExport.push({
                'Sección': `--- ${grupo.tipo_documento} ---`,
                'Código': '', 'Cuenta': '', 'Débito': '', 'Crédito': ''
            });

            grupo.cuentas.forEach(cta => {
                dataToExport.push({
                    'Sección': grupo.tipo_documento,
                    'Código': cta.cuenta_codigo,
                    'Cuenta': cta.cuenta_nombre,
                    'Débito': parseFloat(cta.debito).toFixed(2),
                    'Crédito': parseFloat(cta.credito).toFixed(2)
                });
            });

            // Total de grupo
            dataToExport.push({
                'Sección': 'TOTAL ' + grupo.tipo_documento,
                'Código': '', 'Cuenta': '',
                'Débito': parseFloat(grupo.total_debito_grupo).toFixed(2),
                'Crédito': parseFloat(grupo.total_credito_grupo).toFixed(2)
            });

            dataToExport.push({}); // Línea vacía
        });

        // Gran Total
        const granTotalDebito = reportData.reduce((sum, g) => sum + g.total_debito_grupo, 0);
        const granTotalCredito = reportData.reduce((sum, g) => sum + g.total_credito_grupo, 0);

        dataToExport.push({
            'Sección': 'GRAN TOTAL', 'Código': '', 'Cuenta': '',
            'Débito': granTotalDebito.toFixed(2),
            'Crédito': granTotalCredito.toFixed(2)
        });

        const csv = window.Papa.unparse(dataToExport);
        const blob = new Blob(["\uFEFF" + csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.setAttribute('download', `Libro_Diario_Resumen_${filtros.inicio}_a_${filtros.fin}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const handleExportPDF = async () => {
        if (!reportData) return setError("Primero debe generar un reporte.");
        setIsLoading(true);
        setError(null);

        try {
            const params = {
                fecha_inicio: filtros.inicio,
                fecha_fin: filtros.fin,
            };
            if (filtros.selectedTipos.length > 0) {
                params.tipos_documento_ids = filtros.selectedTipos.join(',');
            }

            const signedUrlRes = await apiService.get('/reports/journal-summary/get-signed-url', { params });
            const signedToken = signedUrlRes.data.signed_url_token;
            const finalPdfUrl = `${process.env.NEXT_PUBLIC_API_URL}/api/reports/journal-summary/imprimir?signed_token=${signedToken}`;

            // ABRIR EN NUEVA PESTAÑA (FIX)
            window.open(finalPdfUrl, '_blank');

        } catch (err) {
            setError(err.response?.data?.detail || 'Error al obtener URL del PDF.');
        } finally {
            setIsLoading(false);
        }
    };

    if (authLoading) return <div className="p-10">Cargando...</div>;
    if (!user) return null;

    // Calcular Gran Total para renderizado
    const granTotalDebito = reportData ? reportData.reduce((sum, g) => sum + g.total_debito_grupo, 0) : 0;
    const granTotalCredito = reportData ? reportData.reduce((sum, g) => sum + g.total_credito_grupo, 0) : 0;

    // Handle Select All
    const handleSelectAll = () => {
        if (filtros.selectedTipos.length === tiposDocumento.length) {
            setFiltros(prev => ({ ...prev, selectedTipos: [] })); // Deselect All
        } else {
            setFiltros(prev => ({ ...prev, selectedTipos: tiposDocumento.map(t => t.id) })); // Select All
        }
    };

    // ... (rest of filtering logic)

    return (
        <>
            <Script src="https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js" />
            <div className="min-h-screen bg-gray-50 p-6 font-sans">
                <div className="max-w-7xl mx-auto">

                    {/* Header */}
                    <div className="flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-indigo-100 text-indigo-600 rounded-lg">
                                <FaListAlt className="text-2xl" />
                            </div>
                            <div>
                                <div className="flex items-center gap-4">
                                    <h1 className="text-3xl font-bold text-gray-800">Libro Diario Resumen</h1>
                                    <button
                                        onClick={() => window.open('/manual/capitulo_28_libro_diario_resumen.html', '_blank')}
                                        className="text-indigo-600 hover:bg-indigo-50 px-2 py-1 rounded-md flex items-center gap-2 transition-colors border border-transparent hover:border-indigo-200"
                                        title="Ver Manual de Usuario"
                                    >
                                        <span className="text-lg">📖</span> <span className="font-bold text-sm hidden md:inline">Manual</span>
                                    </button>
                                </div>
                                <p className="text-gray-500 text-sm">Agrupado por Tipos de Documento Contable</p>
                            </div>
                        </div>
                    </div>

                    {/* Filtros */}
                    <div className="bg-white rounded-xl shadow p-6 mb-8 border border-gray-100">
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 items-end">
                            <div className="md:col-span-2">
                                <div className="flex justify-between items-center mb-1">
                                    <label className={labelClass}>Tipos de Documento (Ctrl+Click)</label>
                                    <button
                                        onClick={handleSelectAll}
                                        className="text-xs text-indigo-600 hover:text-indigo-800 font-bold underline"
                                    >
                                        {filtros.selectedTipos.length === tiposDocumento.length ? 'Deseleccionar Todos' : 'Seleccionar Todos'}
                                    </button>
                                </div>
                                <select
                                    multiple
                                    className={`${inputClass} h-20`}
                                    value={filtros.selectedTipos}
                                    onChange={handleTipoDocChange}
                                >
                                    {tiposDocumento.map(t => (
                                        <option key={t.id} value={t.id}>{t.nombre}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className={labelClass}>Desde</label>
                                <input type="date" value={filtros.inicio} onChange={e => setFiltros(prev => ({ ...prev, inicio: e.target.value }))} className={inputClass} />
                            </div>
                            <div>
                                <label className={labelClass}>Hasta</label>
                                <input type="date" value={filtros.fin} onChange={e => setFiltros(prev => ({ ...prev, fin: e.target.value }))} className={inputClass} />
                            </div>
                        </div>
                        <div className="mt-4 flex justify-end">
                            <button onClick={handleGenerateReport} disabled={isLoading} className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-6 rounded-lg shadow transition-colors flex items-center gap-2">
                                {isLoading ? 'Generando...' : <><FaSearch /> Generar Resumen</>}
                            </button>
                        </div>
                    </div>

                    {error && (
                        <div className="mb-6 p-4 bg-red-100 border-l-4 border-red-500 text-red-700 flex items-center gap-2">
                            <FaExclamationTriangle /> {error}
                        </div>
                    )}

                    {/* Resultados */}
                    {reportData && (
                        <div className="bg-white rounded-xl shadow overflow-hidden border border-gray-100">
                            {/* Toolbar Exportación */}
                            <div className="bg-gray-50 p-4 border-b border-gray-200 flex justify-between items-center">
                                <span className="font-bold text-gray-700">Resultados</span>
                                <div className="flex gap-2">
                                    <button onClick={handleExportCSV} className="flex items-center gap-2 px-3 py-1 bg-white border border-green-500 text-green-600 rounded hover:bg-green-50">
                                        <FaFileCsv /> CSV
                                    </button>
                                    <button onClick={handleExportPDF} className="flex items-center gap-2 px-3 py-1 bg-white border border-red-500 text-red-600 rounded hover:bg-red-50">
                                        <FaFilePdf /> PDF
                                    </button>
                                </div>
                            </div>

                            <div className="p-6">
                                {reportData.length === 0 ? (
                                    <p className="text-center text-gray-400 italic">No se encontraron datos.</p>
                                ) : (
                                    <div className="space-y-8">
                                        {reportData.map((grupo, idx) => (
                                            <div key={idx} className="border rounded-lg overflow-hidden">
                                                <div className="bg-indigo-50 px-4 py-2 font-bold text-indigo-900 border-b border-indigo-100 flex justify-between">
                                                    <span>{grupo.tipo_documento}</span>
                                                </div>
                                                <table className="w-full text-sm">
                                                    <thead className="bg-gray-50 text-gray-500">
                                                        <tr>
                                                            <th className="px-4 py-2 text-left w-24">Código</th>
                                                            <th className="px-4 py-2 text-left">Cuenta</th>
                                                            <th className="px-4 py-2 text-right w-32">Débito</th>
                                                            <th className="px-4 py-2 text-right w-32">Crédito</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody className="divide-y divide-gray-100">
                                                        {grupo.cuentas.map((cta, i) => (
                                                            <tr key={i} className="hover:bg-gray-50">
                                                                <td className="px-4 py-1 font-mono text-gray-600">{cta.cuenta_codigo}</td>
                                                                <td className="px-4 py-1 text-gray-700">{cta.cuenta_nombre}</td>
                                                                <td className="px-4 py-1 text-right font-mono">{parseFloat(cta.debito).toLocaleString('es-CO', { minimumFractionDigits: 2 })}</td>
                                                                <td className="px-4 py-1 text-right font-mono">{parseFloat(cta.credito).toLocaleString('es-CO', { minimumFractionDigits: 2 })}</td>
                                                            </tr>
                                                        ))}
                                                        <tr className="bg-gray-50 font-bold text-gray-800">
                                                            <td colSpan="2" className="px-4 py-2 text-right uppercase text-xs">Total {grupo.tipo_documento}:</td>
                                                            <td className="px-4 py-2 text-right font-mono">{parseFloat(grupo.total_debito_grupo).toLocaleString('es-CO', { minimumFractionDigits: 2 })}</td>
                                                            <td className="px-4 py-2 text-right font-mono">{parseFloat(grupo.total_credito_grupo).toLocaleString('es-CO', { minimumFractionDigits: 2 })}</td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                            </div>
                                        ))}

                                        {/* GRAN TOTAL */}
                                        <div className="mt-8 p-4 bg-slate-800 text-white rounded-lg flex justify-between items-center shadow-lg">
                                            <span className="font-bold text-lg uppercase tracking-wide">Gran Total del Período</span>
                                            <div className="flex gap-8 text-xl font-mono font-bold">
                                                <div className="text-green-400">
                                                    <span className="text-xs text-slate-400 block text-right">DÉBITOS</span>
                                                    ${granTotalDebito.toLocaleString('es-CO', { minimumFractionDigits: 2 })}
                                                </div>
                                                <div className="text-green-400">
                                                    <span className="text-xs text-slate-400 block text-right">CRÉDITOS</span>
                                                    ${granTotalCredito.toLocaleString('es-CO', { minimumFractionDigits: 2 })}
                                                </div>
                                            </div>
                                        </div>

                                        {/* CHECK CUADRE */}
                                        <div className="text-center mt-2">
                                            {Math.abs(granTotalDebito - granTotalCredito) < 0.01 ? (
                                                <span className="text-green-600 font-bold text-sm">✅ Partida Doble Cuadrada</span>
                                            ) : (
                                                <span className="text-red-500 font-bold text-sm animate-pulse">❌ Descuadre Detectado: ${(granTotalDebito - granTotalCredito).toFixed(2)}</span>
                                            )}
                                        </div>

                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                </div>
            </div>
        </>
    );
}
