'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import Script from 'next/script';
import {
    FaBook,
    FaSearch,
    FaFileCsv,
    FaFilePdf,
    FaCalendarAlt,
    FaFilter,
    FaExclamationTriangle
} from 'react-icons/fa';

import { useAuth } from '../../../../app/context/AuthContext'; // Ajusta la ruta si es necesario según tu estructura real
import { apiService } from '../../../../lib/apiService';

// Estilos reusables (Manual v2.0)
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white";

const getInitials = (name) => {
    if (!name) return '';
    return name.split(' ').map(word => word[0]).join('').toUpperCase();
};

export default function LibroDiarioPage() {
    const { user, loading: authLoading } = useAuth();
    const router = useRouter();

    const [reportData, setReportData] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [totals, setTotals] = useState({ debito: 0, credito: 0 });
    const [tiposDocumento, setTiposDocumento] = useState([]);
    const [filtros, setFiltros] = useState({
        inicio: new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0],
        fin: new Date().toISOString().split('T')[0],
        tipoDocId: ''
    });

    // Cargar filtros
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

    const handleGenerateReport = async () => {
        if (!filtros.inicio || !filtros.fin) {
            setError("Por favor, seleccione un rango de fechas.");
            return;
        }
        if (!user || !user.empresaId) {
            setError("No se pudo identificar el ID de la empresa del usuario.");
            return;
        }
        setIsLoading(true);
        setError(null);
        setReportData(null);

        const params = {
            fecha_inicio: filtros.inicio,
            fecha_fin: filtros.fin,
        };
        if (filtros.tipoDocId) {
            params.tipo_documento_id = filtros.tipoDocId;
        }

        try {
            const res = await apiService.get('/reports/journal', { params: params });

            setReportData(res.data);
            const newTotals = res.data.reduce((acc, mov) => {
                acc.debito += parseFloat(mov.debito);
                acc.credito += parseFloat(mov.credito);
                return acc;
            }, { debito: 0, credito: 0 });
            setTotals(newTotals);
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al cargar los datos del reporte.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleExportCSV = () => {
        if (!reportData) return alert("Primero debe generar un reporte.");
        if (typeof window.Papa === 'undefined') {
            console.warn("PapaParse no está cargado.");
            return alert("La librería CSV no está lista. Por favor, recargue la página.");
        }

        const dataToExport = reportData.map(row => ({
            'Fecha': new Date(row.fecha).toLocaleDateString('es-CO', { timeZone: 'UTC' }),
            'Documento': `${getInitials(row.tipo_documento)} #${row.numero_documento}`,
            'Beneficiario': row.beneficiario_nombre,
            'Código Cuenta': row.cuenta_codigo,
            'Nombre Cuenta': row.cuenta_nombre,
            'Concepto': row.concepto,
            'Débito': parseFloat(row.debito).toFixed(2),
            'Crédito': parseFloat(row.credito).toFixed(2)
        }));

        const csv = window.Papa.unparse(dataToExport);
        const blob = new Blob(["\uFEFF" + csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.setAttribute('download', `Libro_Diario_${filtros.inicio}_a_${filtros.fin}.csv`);
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
                fecha_inicio: filtros.inicio,
                fecha_fin: filtros.fin,
            };
            if (filtros.tipoDocId) {
                paramsForSignedUrl.tipo_documento_id = filtros.tipoDocId;
            }

            const signedUrlRes = await apiService.get('/reports/journal/get-signed-url', { params: paramsForSignedUrl });
            const signedToken = signedUrlRes.data.signed_url_token;
            const finalPdfUrl = `${process.env.NEXT_PUBLIC_API_URL}/api/reports/journal/imprimir?signed_token=${signedToken}`;

            window.open(finalPdfUrl, '_blank');

        } catch (err) {
            setError(err.response?.data?.detail || 'Error al obtener la URL firmada para el PDF.');
        } finally {
            setIsLoading(false);
        }
    };

    if (authLoading) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
                <FaBook className="text-indigo-300 text-6xl mb-4 animate-pulse" />
                <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando Libro Diario...</p>
            </div>
        );
    }

    if (!user) return null;

    return (
        <>
            <Script src="https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js" />

            <div className="min-h-screen bg-gray-50 p-6 font-sans">
                <div className="max-w-7xl mx-auto">

                    {/* ENCABEZADO */}
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                        <div>
                            <div className="flex items-center gap-3 mt-3">
                                <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                                    <FaBook className="text-2xl" />
                                </div>
                                <div>
                                    <div className="flex items-center gap-4">
                                        <h1 className="text-3xl font-bold text-gray-800">Libro Diario</h1>
                                        <button
                                            onClick={() => window.open('/manual/capitulo_27_libro_diario.html', '_blank')}
                                            className="text-indigo-600 hover:bg-indigo-50 px-2 py-1 rounded-md flex items-center gap-2 transition-colors"
                                            title="Ver Manual de Usuario"
                                        >
                                            <span className="text-lg">📖</span> <span className="font-bold text-sm hidden md:inline">Manual</span>
                                        </button>
                                    </div>
                                    <p className="text-gray-500 text-sm">Consulta cronológica de todos los movimientos contables.</p>
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
                            {/* Tipo Documento */}
                            <div className="md:col-span-2 lg:col-span-1">
                                <label className={labelClass}>Tipo de Documento</label>
                                <select
                                    value={filtros.tipoDocId}
                                    onChange={(e) => setFiltros(prev => ({ ...prev, tipoDocId: e.target.value }))}
                                    className={selectClass}
                                >
                                    <option value="">Todos</option>
                                    {tiposDocumento.map(tipo => (<option key={tipo.id} value={tipo.id}>{tipo.nombre}</option>))}
                                </select>
                            </div>

                            {/* Fecha Inicio */}
                            <div>
                                <label className={labelClass}>Fecha Inicio</label>
                                <div className="relative">
                                    <input
                                        type="date"
                                        value={filtros.inicio}
                                        onChange={(e) => setFiltros(prev => ({ ...prev, inicio: e.target.value }))}
                                        className={inputClass}
                                    />
                                    <FaCalendarAlt className="absolute right-3 top-3 text-gray-400 pointer-events-none" />
                                </div>
                            </div>

                            {/* Fecha Fin */}
                            <div>
                                <label className={labelClass}>Fecha Fin</label>
                                <div className="relative">
                                    <input
                                        type="date"
                                        value={filtros.fin}
                                        onChange={(e) => setFiltros(prev => ({ ...prev, fin: e.target.value }))}
                                        className={inputClass}
                                    />
                                    <FaCalendarAlt className="absolute right-3 top-3 text-gray-400 pointer-events-none" />
                                </div>
                            </div>

                            {/* Botón Generar */}
                            <div>
                                <button
                                    onClick={handleGenerateReport}
                                    disabled={isLoading}
                                    className={`
                                w-full px-6 py-2 rounded-lg shadow-md font-bold text-white transition-all transform hover:-translate-y-0.5 flex items-center justify-center gap-2
                                ${isLoading ? 'bg-gray-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'}
                            `}
                                >
                                    {isLoading ? <span className="loading loading-spinner loading-sm"></span> : <><FaSearch /> Generar Reporte</>}
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* MENSAJE DE ERROR */}
                    {error && (
                        <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded-r-lg flex items-center gap-3 animate-pulse">
                            <FaExclamationTriangle className="text-xl" />
                            <p className="font-bold">{error}</p>
                        </div>
                    )}

                    {/* CARD 2: RESULTADOS */}
                    {reportData && (
                        <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden animate-slideDown">
                            {/* Cabecera del Reporte */}
                            <div className="p-6 bg-gray-50 border-b border-gray-200 flex flex-col md:flex-row justify-between items-center gap-4">
                                <div>
                                    <h2 className="text-xl font-bold text-gray-800">{user?.nombre_empresa}</h2>
                                    <p className="text-sm text-gray-600 font-medium mt-1">
                                        Periodo: <span className="text-indigo-600">{filtros.inicio}</span> al <span className="text-indigo-600">{filtros.fin}</span>
                                    </p>
                                </div>

                                <div className="flex gap-3">
                                    <button
                                        onClick={handleExportCSV}
                                        disabled={isLoading}
                                        className="flex items-center gap-2 px-4 py-2 bg-white border border-green-500 text-green-600 rounded-lg hover:bg-green-50 font-medium transition-colors shadow-sm disabled:opacity-50"
                                    >
                                        <FaFileCsv className="text-lg" /> Exportar CSV
                                    </button>
                                    <button
                                        onClick={handleExportPDF}
                                        disabled={isLoading}
                                        className="flex items-center gap-2 px-4 py-2 bg-white border border-red-500 text-red-600 rounded-lg hover:bg-red-50 font-medium transition-colors shadow-sm disabled:opacity-50"
                                    >
                                        <FaFilePdf className="text-lg" /> Imprimir PDF
                                    </button>
                                </div>
                            </div>

                            {/* Tabla de Resultados */}
                            <div className="overflow-x-auto">
                                <table className="min-w-full divide-y divide-gray-200">
                                    <thead className="bg-slate-100">
                                        <tr>
                                            <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">Fecha</th>
                                            <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">Documento</th>
                                            <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">Beneficiario</th>
                                            <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">Cuenta</th>
                                            <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider w-1/4">Concepto</th>
                                            <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase tracking-wider">Débito</th>
                                            <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase tracking-wider">Crédito</th>
                                        </tr>
                                    </thead>
                                    <tbody className="bg-white divide-y divide-gray-100">
                                        {reportData.length === 0 ? (
                                            <tr><td colSpan="7" className="text-center py-8 text-gray-400 italic">No hay movimientos en este rango.</td></tr>
                                        ) : (
                                            reportData.map((row, index) => (
                                                <tr key={index} className="hover:bg-indigo-50/30 transition-colors">
                                                    <td className="px-4 py-3 text-sm font-mono text-gray-600 whitespace-nowrap">
                                                        {new Date(row.fecha).toLocaleDateString('es-CO', { timeZone: 'UTC' })}
                                                    </td>
                                                    <td className="px-4 py-3 text-sm font-medium text-gray-800">
                                                        <span className="text-xs text-gray-500 mr-1">{getInitials(row.tipo_documento)}</span>
                                                        <span className="font-mono">#{row.numero_documento}</span>
                                                    </td>
                                                    <td className="px-4 py-3 text-sm text-gray-700 truncate max-w-xs" title={row.beneficiario_nombre}>
                                                        {row.beneficiario_nombre}
                                                    </td>
                                                    <td className="px-4 py-3 text-sm text-gray-600">
                                                        <span className="font-mono font-bold text-indigo-700">{row.cuenta_codigo}</span>
                                                        <span className="block text-xs">{row.cuenta_nombre}</span>
                                                    </td>
                                                    <td className="px-4 py-3 text-sm text-gray-600 italic truncate max-w-xs" title={row.concepto}>
                                                        {row.concepto}
                                                    </td>
                                                    <td className="px-4 py-3 text-sm text-right font-mono text-gray-700">
                                                        {parseFloat(row.debito) > 0 ? parseFloat(row.debito).toLocaleString('es-CO', { minimumFractionDigits: 2 }) : '-'}
                                                    </td>
                                                    <td className="px-4 py-3 text-sm text-right font-mono text-gray-700">
                                                        {parseFloat(row.credito) > 0 ? parseFloat(row.credito).toLocaleString('es-CO', { minimumFractionDigits: 2 }) : '-'}
                                                    </td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                    {/* Footer Totales */}
                                    {reportData.length > 0 && (
                                        <tfoot className="bg-slate-50 border-t-2 border-slate-200">
                                            <tr>
                                                <td colSpan="5" className="px-4 py-4 text-right text-sm font-bold text-gray-600 uppercase">Totales Generales:</td>
                                                <td className="px-4 py-4 text-right text-sm font-bold font-mono text-green-600">
                                                    ${totals.debito.toLocaleString('es-CO', { minimumFractionDigits: 2 })}
                                                </td>
                                                <td className="px-4 py-4 text-right text-sm font-bold font-mono text-green-600">
                                                    ${totals.credito.toLocaleString('es-CO', { minimumFractionDigits: 2 })}
                                                </td>
                                            </tr>
                                        </tfoot>
                                    )}
                                </table>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </>
    );
}