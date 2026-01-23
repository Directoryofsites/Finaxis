'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { phService } from '../../../../lib/phService';
import {
    FaChartBar,
    FaFileDownload,
    FaFileCsv,
    FaSearch,
    FaFilter,
    FaCalendarAlt,
    FaBuilding,
    FaPlay
} from 'react-icons/fa';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import { useRecaudos } from '../../../../contexts/RecaudosContext';

export default function ReporteSaldosPage() {
    const { user, loading: authLoading } = useAuth();
    const { labels } = useRecaudos();

    // Filtros
    const [fechaCorte, setFechaCorte] = useState('');
    const [selectedTorre, setSelectedTorre] = useState('');
    const [conceptoBusqueda, setConceptoBusqueda] = useState('');

    // Datos Auxiliares
    const [torres, setTorres] = useState([]);

    // Estado Reporte
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);

    // Carga Inicial
    useEffect(() => {
        if (!authLoading && user?.empresaId) {
            loadAuxData();
            loadReporte();
        }
    }, [authLoading, user]);

    const loadAuxData = async () => {
        try {
            const t = await phService.getTorres();
            setTorres(t);
        } catch (e) {
            console.error("Error cargando torres", e);
        }
    };

    const loadReporte = async () => {
        setLoading(true);
        try {
            const params = {};
            if (fechaCorte) params.fecha_corte = fechaCorte;
            if (selectedTorre) params.torre_id = selectedTorre;
            if (conceptoBusqueda) params.concepto_busqueda = conceptoBusqueda;

            const result = await phService.getReporteSaldos(params);
            setData(result);
        } catch (error) {
            console.error("Error loading report", error);
        } finally {
            setLoading(false);
        }
    };

    // Efecto para recargar al cambiar filtros (debounce opcional)
    useEffect(() => {
        // Carga inicial solo si no hay datos.
        // Si el usuario cambia filtros, debe dar click en el botón.
        if (!authLoading && user?.empresaId && !data && !loading) {
            loadReporte();
        }
    }, [authLoading, user]);

    // Exportar CSV
    const handleDownloadCSV = () => {
        if (!data || !data.items) return;

        const headers = ["Torre;Unidad;Propietario;Saldo;Detalle"];
        const rows = data.items.map(item =>
            `${item.torre_nombre};${item.unidad_codigo};${item.propietario_nombre};${item.saldo};${item.detalle}`
        );

        const csvContent = [headers, ...rows].join("\n");
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', `Reporte_Saldos_${fechaCorte || 'HOY'}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    // Exportar PDF
    const handleDownloadPDF = () => {
        if (!data) return;

        const doc = new jsPDF();
        const fechaImpresion = new Date().toLocaleDateString();

        // Header
        doc.setFontSize(18);
        doc.setTextColor(40, 40, 40);
        doc.text("Reporte de Saldos de Cartera", 14, 22);

        doc.setFontSize(10);
        doc.text(`Empresa: ${user?.empresaNombre || 'Consorcio'}`, 14, 28);
        doc.text(`Fecha de Corte: ${fechaCorte || new Date().toLocaleDateString()}`, 14, 34);
        if (conceptoBusqueda) doc.text(`Filtro Concepto: ${conceptoBusqueda}`, 14, 40);

        const tableColumn = ["Torre", "Unidad", "Propietario", "Saldo", "Detalle"];
        const tableRows = [];

        data.items.forEach(item => {
            const rowData = [
                item.torre_nombre,
                item.unidad_codigo,
                item.propietario_nombre,
                `$${item.saldo.toLocaleString()}`,
                item.detalle
            ];
            tableRows.push(rowData);
        });

        // Add Total Row
        tableRows.push(["", "", "TOTAL GENERAL", `$${data.total_general.toLocaleString()}`, ""]);

        autoTable(doc, {
            head: [tableColumn],
            body: tableRows,
            startY: 45,
            theme: 'striped',
            headStyles: { fillColor: [79, 70, 229] }, // Indigo
            styles: { fontSize: 8 },
            columnStyles: {
                3: { halign: 'right', fontStyle: 'bold' }
            }
        });

        doc.save(`Reporte_Saldos_${fechaCorte || 'HOY'}.pdf`);
    };

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8 flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-indigo-100 text-indigo-600 rounded-xl">
                            <FaChartBar className="text-3xl" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold text-gray-800">Balance General de Cartera</h1>
                            <p className="text-gray-500">Informe detallado de saldos por unidad, torre y concepto.</p>
                        </div>
                    </div>
                </div>

                {/* Filtros */}
                <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 mb-8">
                    <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
                        {/* Fecha Corte */}
                        <div>
                            <label className="block text-sm font-bold text-gray-700 mb-2 flex items-center gap-2">
                                <FaCalendarAlt className="text-indigo-500" /> Fecha de Corte
                            </label>
                            <input
                                type="date"
                                className="w-full px-4 py-2 border rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none"
                                value={fechaCorte}
                                onChange={(e) => setFechaCorte(e.target.value)}
                            />
                            <span className="text-xs text-gray-400 mt-1 block">Vacío = HOY</span>
                        </div>

                        {/* Torre */}
                        <div>
                            <label className="block text-sm font-bold text-gray-700 mb-2 flex items-center gap-2">
                                <FaBuilding className="text-indigo-500" /> Filtrar por Torre
                            </label>
                            <select
                                className="w-full px-4 py-2 border rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none bg-white"
                                value={selectedTorre}
                                onChange={(e) => setSelectedTorre(e.target.value)}
                            >
                                <option value="">Todas las Torres</option>
                                {torres.map(t => (
                                    <option key={t.id} value={t.id}>{t.nombre}</option>
                                ))}
                            </select>
                        </div>

                        {/* Concepto (Texto) */}
                        <div className="md:col-span-2">
                            <label className="block text-sm font-bold text-gray-700 mb-2 flex items-center gap-2">
                                <FaFilter className="text-indigo-500" /> Filtrar por Concepto
                            </label>
                            <div className="relative">
                                <FaSearch className="absolute left-3 top-3 text-gray-400" />
                                <input
                                    type="text"
                                    placeholder="Ej: Administración, Multa, Interés..."
                                    className="w-full pl-10 px-4 py-2 border rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none"
                                    value={conceptoBusqueda}
                                    onChange={(e) => setConceptoBusqueda(e.target.value)}
                                />
                            </div>
                            <span className="text-xs text-gray-400 mt-1 block">Busca coincidencia en el nombre del movimiento contable.</span>
                        </div>

                        {/* Botón Ejecutar */}
                        <div className="flex items-end">
                            <button
                                onClick={loadReporte}
                                disabled={loading}
                                className="w-full py-2.5 bg-indigo-600 text-white font-bold rounded-xl shadow-md hover:bg-indigo-700 transition-all flex justify-center items-center gap-2 disabled:opacity-50"
                            >
                                {loading ? <span className="loading loading-spinner loading-sm"></span> : <FaPlay />}
                                {loading ? 'Procesando...' : 'Generar Informe'}
                            </button>
                        </div>
                    </div>
                </div>

                {/* Resumen Totales */}
                {data && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                        <div className="bg-gradient-to-br from-indigo-600 to-indigo-800 text-white p-6 rounded-2xl shadow-lg">
                            <p className="text-indigo-200 text-sm font-bold uppercase tracking-wider mb-1">Total General Cartera</p>
                            <h2 className="text-4xl font-black">${data.total_general.toLocaleString()}</h2>
                            <p className="text-xs mt-2 opacity-80">Saldo Neto (Incluye anticipos restados)</p>
                        </div>
                        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-center justify-between">
                            <div>
                                <p className="text-gray-500 text-sm font-bold uppercase">Unidades con Deuda</p>
                                <h2 className="text-3xl font-bold text-gray-800">{data.items.length}</h2>
                            </div>
                            <div className="bg-indigo-50 p-3 rounded-full text-indigo-600">
                                <FaBuilding className="text-xl" />
                            </div>
                        </div>
                        <div className="flex flex-col gap-2 justify-center">
                            <button
                                onClick={handleDownloadPDF}
                                className="flex items-center justify-center gap-2 px-6 py-3 bg-red-600 text-white rounded-xl shadow-lg hover:bg-red-700 transition-all font-bold w-full"
                            >
                                <FaFileDownload className="text-xl" /> PDF
                            </button>
                            <button
                                onClick={handleDownloadCSV}
                                className="flex items-center justify-center gap-2 px-6 py-3 bg-green-600 text-white rounded-xl shadow-lg hover:bg-green-700 transition-all font-bold w-full"
                            >
                                <FaFileCsv className="text-xl" /> CSV / Excel
                            </button>
                        </div>
                    </div>
                )}

                {/* Tabla Resultados */}
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                    {loading ? (
                        <div className="p-12 flex flex-col items-center justify-center">
                            <span className="loading loading-spinner loading-lg text-indigo-600 mb-4"></span>
                            <p className="text-gray-500 font-bold animate-pulse">Analizando saldos históricos...</p>
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-left border-collapse">
                                <thead>
                                    <tr className="bg-gray-50 text-gray-500 uppercase text-xs tracking-wider font-bold">
                                        <th className="p-4 border-b">Torre</th>
                                        <th className="p-4 border-b">Unidad</th>
                                        <th className="p-4 border-b">Propietario</th>
                                        <th className="p-4 border-b">Detalle / Conceptos</th>
                                        <th className="p-4 border-b text-right">Saldo Total</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100">
                                    {data?.items.length === 0 ? (
                                        <tr>
                                            <td colSpan="5" className="p-8 text-center text-gray-400 italic">No se encontraron saldos con los filtros aplicados.</td>
                                        </tr>
                                    ) : (
                                        data?.items.map((item, idx) => (
                                            <tr key={idx} className="hover:bg-indigo-50 transition-colors group">
                                                <td className="p-4 text-sm text-gray-600">{item.torre_nombre}</td>
                                                <td className="p-4 text-sm font-bold text-indigo-600">{item.unidad_codigo}</td>
                                                <td className="p-4 text-sm text-gray-800">{item.propietario_nombre}</td>
                                                <td className="p-4 text-xs text-gray-500 max-w-xs truncate" title={item.detalle}>
                                                    {item.detalle}
                                                </td>
                                                <td className="p-4 text-sm font-bold text-right text-gray-800">
                                                    ${item.saldo.toLocaleString()}
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                                {data?.items.length > 0 && (
                                    <tfoot className="bg-gray-100">
                                        <tr>
                                            <td colSpan="4" className="p-4 text-right font-bold text-gray-700 uppercase">Total General:</td>
                                            <td className="p-4 text-right font-black text-indigo-700 text-lg">
                                                ${data.total_general.toLocaleString()}
                                            </td>
                                        </tr>
                                    </tfoot>
                                )}
                            </table>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
