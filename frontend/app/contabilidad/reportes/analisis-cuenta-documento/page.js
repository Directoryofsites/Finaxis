'use client';

import React, { useState, useEffect } from 'react';
import { FaPrint, FaFileCsv, FaSearch, FaBook, FaFilter, FaSpinner } from 'react-icons/fa';

import { useRouter } from 'next/navigation';
import { useAuth } from '../../../../app/context/AuthContext';

export default function AnalisisCuentaDocPage() {
    const router = useRouter();
    const { user } = useAuth();
    const [fechaInicio, setFechaInicio] = useState('');
    const [fechaFin, setFechaFin] = useState('');
    const [cuentaFiltro, setCuentaFiltro] = useState('');

    const [reportData, setReportData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Inicializar fechas
    useEffect(() => {
        const now = new Date();
        const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
        const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);

        // Ajuste zona horaria local
        const formatDate = (date) => {
            const offset = date.getTimezoneOffset();
            const local = new Date(date.getTime() - (offset * 60 * 1000));
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
            if (!token) throw new Error('No se encontró sesión activa');
            const params = new URLSearchParams({
                fecha_inicio: fechaInicio,
                fecha_fin: fechaFin
            });
            if (cuentaFiltro) params.append('cuenta_filtro', cuentaFiltro);

            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/reports/account-analysis-doc?${params}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!res.ok) throw new Error('Error al generar el reporte');
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
            if (!token) throw new Error('No se encontró sesión activa');

            const params = new URLSearchParams({
                fecha_inicio: fechaInicio,
                fecha_fin: fechaFin
            });
            if (cuentaFiltro) params.append('cuenta_filtro', cuentaFiltro);

            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/reports/account-analysis-doc/get-signed-url?${params}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!res.ok) throw new Error("No se pudo obtener URL firmada");
            const data = await res.json();

            // Abrir en nueva pestaña
            // El backend devuelve solo el token, y el endpoint base para imprimir es:
            const endpointPath = "/api/reports/account-analysis-doc/imprimir";
            const downloadUrl = `${process.env.NEXT_PUBLIC_API_URL}${endpointPath}?token=${data.signed_url_token}`;
            window.open(downloadUrl, '_blank');

        } catch (err) {
            alert("Error al exportar PDF: " + err.message);
        }
    };

    const handleExportCSV = () => {
        if (!reportData || !reportData.cuentas) return;

        let csvContent = "Cuenta Codigo,Cuenta Nombre,Saldo Inicial,Tipo Doc Codigo,Tipo Doc Nombre,Debito,Credito\n";

        reportData.cuentas.forEach(cuenta => {
            cuenta.movimientos_por_tipo.forEach(mov => {
                const row = [
                    cuenta.cuenta_codigo,
                    `"${cuenta.cuenta_nombre}"`,
                    cuenta.saldo_inicial,
                    mov.tipo_codigo,
                    `"${mov.tipo_nombre}"`,
                    mov.debito,
                    mov.credito
                ].join(",");
                csvContent += row + "\n";
            });
            // Fila de saldo final
            csvContent += `${cuenta.cuenta_codigo},"${cuenta.cuenta_nombre} (Saldo Final)",${cuenta.nuevo_saldo},,,, \n`;
        });

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.setAttribute("href", url);
        link.setAttribute("download", `analisis_cuenta_doc_${fechaInicio}_${fechaFin}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    return (
        <>
            <div className="p-6 max-w-7xl mx-auto space-y-6">
                {/* Header & Manual */}
                <div className="flex justify-between items-center bg-white p-4 rounded-xl shadow-sm border border-gray-100">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                            <FaBook className="text-blue-600" />
                            Análisis de Cuenta por Documento
                        </h1>
                        <p className="text-gray-500 text-sm mt-1">
                            Visualiza la composición del saldo por tipo de fuente (Facturas, Recibos, etc).
                        </p>
                    </div>
                    <button
                        onClick={() => window.open('/manual/capitulo_63_analisis_cuenta_doc.html', '_blank', 'width=800,height=600')}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors text-sm font-medium"
                    >
                        <FaBook /> Manual
                    </button>
                </div>

                {/* Filters */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                    <div className="space-y-1">
                        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Desde</label>
                        <input
                            type="date"
                            value={fechaInicio}
                            onChange={(e) => setFechaInicio(e.target.value)}
                            className="w-full p-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                        />
                    </div>
                    <div className="space-y-1">
                        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Hasta</label>
                        <input
                            type="date"
                            value={fechaFin}
                            onChange={(e) => setFechaFin(e.target.value)}
                            className="w-full p-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                        />
                    </div>
                    <div className="space-y-1 md:col-span-2">
                        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Filtrar Cuenta (Opcional)</label>
                        <div className="relative">
                            <FaSearch className="absolute left-3 top-3 text-gray-400" />
                            <input
                                type="text"
                                placeholder="Código o Nombre..."
                                value={cuentaFiltro}
                                onChange={(e) => setCuentaFiltro(e.target.value)}
                                className="w-full pl-10 p-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                            />
                        </div>
                    </div>
                </div>

                {/* Actions */}
                <div className="flex gap-3">
                    <button
                        onClick={handleGenerate}
                        disabled={loading}
                        className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 shadow-sm transition-all disabled:opacity-50 font-medium"
                    >
                        {loading ? <FaSpinner className="animate-spin" /> : <FaFilter />}
                        Generar Reporte
                    </button>
                    <button
                        onClick={handleExportPDF}
                        disabled={loading}
                        className="flex items-center gap-2 px-6 py-2.5 bg-white text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50 shadow-sm transition-all disabled:opacity-50 font-medium"
                    >
                        <FaPrint className="text-red-500" /> PDF
                    </button>
                    <button
                        onClick={handleExportCSV}
                        disabled={!reportData}
                        className="flex items-center gap-2 px-6 py-2.5 bg-white text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50 shadow-sm transition-all disabled:opacity-50 font-medium"
                    >
                        <FaFileCsv className="text-green-500" /> CSV
                    </button>
                </div>

                {/* Results */}
                {loading && (
                    <div className="text-center py-12">
                        <FaSpinner className="animate-spin text-4xl text-blue-500 mx-auto mb-4" />
                        <p className="text-gray-500 animate-pulse">Procesando información contable...</p>
                    </div>
                )}

                {error && (
                    <div className="bg-red-50 text-red-600 p-4 rounded-lg border border-red-100 flex items-center gap-3">
                        <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                        {error}
                    </div>
                )}

                {reportData && (
                    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                        <div className="p-4 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
                            <h2 className="font-semibold text-gray-700">Resultados</h2>
                            <div className="text-sm text-gray-500">
                                <strong>Total Débito:</strong> ${reportData.totales_generales.debito.toLocaleString()} |
                                <strong> Total Crédito:</strong> ${reportData.totales_generales.credito.toLocaleString()}
                            </div>
                        </div>

                        <div className="overflow-x-auto">
                            {reportData.cuentas.length === 0 ? (
                                <div className="p-8 text-center text-gray-400">No se encontraron movimientos.</div>
                            ) : (
                                <div className="divide-y divide-gray-100">
                                    {reportData.cuentas.map(cuenta => (
                                        <div key={cuenta.cuenta_id} className="p-4 hover:bg-gray-50 transition-colors">
                                            {/* Account Header */}
                                            <div className="flex justify-between items-center mb-3">
                                                <div className="font-bold text-gray-800 text-lg">
                                                    <span className="text-blue-600 mr-2">{cuenta.cuenta_codigo}</span>
                                                    {cuenta.cuenta_nombre}
                                                </div>
                                                <div className="text-sm font-medium bg-gray-100 px-3 py-1 rounded-full text-gray-600">
                                                    Saldo Inicial: ${cuenta.saldo_inicial.toLocaleString()}
                                                </div>
                                            </div>

                                            {/* Doc Types Table */}
                                            <table className="w-full text-sm">
                                                <thead className="text-gray-500 bg-gray-50/50">
                                                    <tr>
                                                        <th className="text-left font-medium py-2 pl-2">Tipo</th>
                                                        <th className="text-right font-medium py-2">Débitos</th>
                                                        <th className="text-right font-medium py-2 pr-2">Créditos</th>
                                                    </tr>
                                                </thead>
                                                <tbody className="divide-y divide-gray-100 border-t border-gray-100">
                                                    {cuenta.movimientos_por_tipo.map((mov, idx) => (
                                                        <tr key={idx}>
                                                            <td className="py-2 pl-2 text-gray-600">
                                                                <span className="font-mono text-xs mr-2 border border-gray-200 px-1 rounded">{mov.tipo_codigo}</span>
                                                                {mov.tipo_nombre}
                                                            </td>
                                                            <td className="text-right py-2 text-gray-800">${mov.debito.toLocaleString()}</td>
                                                            <td className="text-right py-2 pr-2 text-gray-800">${mov.credito.toLocaleString()}</td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                                <tfoot className="bg-gray-50 border-t border-gray-200">
                                                    <tr>
                                                        <td className="text-right font-bold py-2 pr-4 text-gray-600">Nuevo Saldo:</td>
                                                        <td colSpan="2" className="text-right font-bold py-2 pr-2 text-blue-700 text-lg">
                                                            ${cuenta.nuevo_saldo.toLocaleString()}
                                                        </td>
                                                    </tr>
                                                </tfoot>
                                            </table>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </>
    );
}
