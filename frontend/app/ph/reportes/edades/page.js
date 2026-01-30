'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { phService } from '../../../../lib/phService';
import { FaChartPie, FaPrint, FaFileDownload, FaBuilding, FaExclamationTriangle } from 'react-icons/fa';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';

export default function CarteraEdadesPage() {
    const { user, loading: authLoading } = useAuth();
    const [loading, setLoading] = useState(true);
    const [data, setData] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [fechaCorte, setFechaCorte] = useState('');

    useEffect(() => {
        if (!authLoading && user?.empresaId) {
            loadReporte();
        }
    }, [authLoading, user, fechaCorte]);

    const loadReporte = async () => {
        setLoading(true);
        try {
            const params = {};
            if (fechaCorte) params.fecha_corte = fechaCorte;
            const result = await phService.getReporteEdades(params);
            setData(result);
        } catch (error) {
            console.error("Error loading report", error);
            alert("Error al cargar el reporte: " + error.message);
        } finally {
            setLoading(false);
        }
    };

    const handlePrintPDF = () => {
        if (!data) return;

        const doc = new jsPDF('l', 'mm', 'a4'); // Landscape

        // Header
        doc.setFontSize(18);
        doc.text("Reporte de Cartera por Edades (Vencimiento)", 14, 20);

        doc.setFontSize(10);
        doc.text(`Empresa: ${user?.empresaNombre || user?.empresa?.razon_social || user?.empresa?.nombre || 'Consorcio'}`, 14, 28);
        doc.text(`Fecha de Corte: ${fechaCorte || new Date().toLocaleDateString()}`, 14, 34);

        const tableColumn = ["Unidad", "Propietario", "Corriente", "1-30 Días", "31-60 Días", "61-90 Días", "> 90 Días", "TOTAL"];

        const tableRows = data.items.map(item => [
            { content: item.unidad_codigo, styles: { fontStyle: 'bold' } },
            item.propietario_nombre,
            `$${item.saldo_corriente.toLocaleString()}`,
            `$${item.edad_0_30.toLocaleString()}`,
            `$${item.edad_31_60.toLocaleString()}`,
            `$${item.edad_61_90.toLocaleString()}`,
            `$${item.edad_mas_90.toLocaleString()}`,
            { content: `$${item.saldo_total.toLocaleString()}`, styles: { fontStyle: 'bold', fillColor: [240, 240, 240] } }
        ]);

        // Footer Row with Totals
        tableRows.push([
            { content: "TOTALES", colSpan: 2, styles: { fontStyle: 'bold', halign: 'right' } },
            `$${data.total_corriente.toLocaleString()}`,
            `$${data.total_0_30.toLocaleString()}`,
            `$${data.total_31_60.toLocaleString()}`,
            `$${data.total_61_90.toLocaleString()}`,
            `$${data.total_mas_90.toLocaleString()}`,
            { content: `$${data.total_general.toLocaleString()}`, styles: { fontStyle: 'bold' } }
        ]);

        autoTable(doc, {
            head: [tableColumn],
            body: tableRows,
            startY: 40,
            theme: 'grid',
            headStyles: { fillColor: [41, 128, 185], textColor: 255 },
            styles: { fontSize: 8, cellPadding: 2 },
            columnStyles: {
                0: { cellWidth: 20 }, // Unidad
                1: { cellWidth: 70 }, // Propietario
                2: { halign: 'right' },
                3: { halign: 'right' },
                4: { halign: 'right' },
                5: { halign: 'right' },
                6: { halign: 'right' },
                7: { halign: 'right', fontStyle: 'bold' }
            }
        });

        doc.save(`Cartera_Edades_${new Date().toISOString().slice(0, 10)}.pdf`);
    };

    if (authLoading) return <div className="p-10 text-center">Cargando...</div>;

    const filteredItems = data?.items.filter(i =>
        searchTerm === '' ||
        i.unidad_codigo.toLowerCase().includes(searchTerm.toLowerCase()) ||
        i.propietario_nombre.toLowerCase().includes(searchTerm.toLowerCase())
    ) || [];

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans">
            <div className="max-w-7xl mx-auto">
                <div className="mb-8 flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-indigo-100 text-indigo-600 rounded-xl">
                            <FaChartPie className="text-3xl" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold text-gray-800">Cartera por Edades</h1>
                            <p className="text-gray-500">Análisis de vencimiento de cartera (Aging Report).</p>
                        </div>
                    </div>

                    <div className="flex gap-2">
                        <button
                            onClick={handlePrintPDF}
                            disabled={loading || !data}
                            className="flex items-center gap-2 px-5 py-2.5 bg-red-600 text-white rounded-lg shadow hover:bg-red-700 transition-colors disabled:opacity-50 font-bold"
                        >
                            <FaFileDownload /> Descargar PDF
                        </button>
                    </div>
                </div>

                <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 mb-6 flex items-center gap-4">
                    <label className="label-text font-bold">Fecha de Corte:</label>
                    <input
                        type="date"
                        className="input input-sm border-gray-300 focus:ring-indigo-500 focus:border-indigo-500"
                        value={fechaCorte}
                        onChange={(e) => setFechaCorte(e.target.value)}
                    />
                    <span className="text-xs text-gray-500">(Dejar vacío para HOY)</span>
                </div>

                {loading ? (
                    <div className="flex flex-col items-center justify-center h-64">
                        <span className="loading loading-spinner loading-lg text-indigo-600 mb-4"></span>
                        <p className="text-gray-500 animate-pulse">Calculando edades de cartera en tiempo real...</p>
                    </div>
                ) : data ? (
                    <div className="space-y-6">
                        {/* Tarjetas Resumen */}
                        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                            <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
                                <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Corriente</h3>
                                <p className="text-xl font-bold text-green-600">${data.total_corriente.toLocaleString()}</p>
                            </div>
                            <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
                                <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">1-30 Días</h3>
                                <p className="text-xl font-bold text-yellow-600">${data.total_0_30.toLocaleString()}</p>
                            </div>
                            <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
                                <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">31-60 Días</h3>
                                <p className="text-xl font-bold text-orange-500">${data.total_31_60.toLocaleString()}</p>
                            </div>
                            <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
                                <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">61-90 Días</h3>
                                <p className="text-xl font-bold text-orange-600">${data.total_61_90.toLocaleString()}</p>
                            </div>
                            <div className="bg-white p-4 rounded-xl shadow-sm border border-l-4 border-l-red-500">
                                <h3 className="text-xs font-bold text-red-500 uppercase tracking-wider mb-1 flex items-center gap-1">
                                    <FaExclamationTriangle /> &gt; 90 Días
                                </h3>
                                <p className="text-xl font-bold text-red-700">${data.total_mas_90.toLocaleString()}</p>
                            </div>
                        </div>

                        {/* Search */}
                        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex items-center gap-2">
                            <input
                                type="text"
                                placeholder="Filtrar por unidad o propietario..."
                                className="input input-sm border-gray-300 w-full max-w-md focus:ring-indigo-500 focus:border-indigo-500"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                            />
                        </div>

                        {/* Tabla */}
                        <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead className="bg-gray-100 text-gray-700 font-bold uppercase text-xs border-b">
                                        <tr>
                                            <th className="px-6 py-4 text-left">Unidad</th>
                                            <th className="px-6 py-4 text-left">Propietario</th>
                                            <th className="px-4 py-4 text-right">Corriente</th>
                                            <th className="px-4 py-4 text-right bg-yellow-50">1-30</th>
                                            <th className="px-4 py-4 text-right bg-orange-50">31-60</th>
                                            <th className="px-4 py-4 text-right bg-orange-100">61-90</th>
                                            <th className="px-4 py-4 text-right bg-red-50 text-red-700">&gt; 90</th>
                                            <th className="px-6 py-4 text-right bg-gray-50 border-l">Total</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-50">
                                        {filteredItems.map((item, idx) => (
                                            <tr key={idx} className="hover:bg-indigo-50/30 transition-colors">
                                                <td className="px-6 py-3 font-bold text-gray-800">{item.unidad_codigo}</td>
                                                <td className="px-6 py-3 text-gray-600 truncate max-w-xs" title={item.propietario_nombre}>
                                                    {item.propietario_nombre}
                                                </td>
                                                <td className="px-4 py-3 text-right text-gray-500 font-mono">
                                                    {item.saldo_corriente !== 0 ? item.saldo_corriente.toLocaleString() : '-'}
                                                </td>
                                                <td className="px-4 py-3 text-right text-gray-600 font-mono bg-yellow-50/30">
                                                    {item.edad_0_30 !== 0 ? item.edad_0_30.toLocaleString() : '-'}
                                                </td>
                                                <td className="px-4 py-3 text-right text-gray-600 font-mono bg-orange-50/30">
                                                    {item.edad_31_60 !== 0 ? item.edad_31_60.toLocaleString() : '-'}
                                                </td>
                                                <td className="px-4 py-3 text-right text-orange-700 font-mono bg-orange-100/30">
                                                    {item.edad_61_90 !== 0 ? item.edad_61_90.toLocaleString() : '-'}
                                                </td>
                                                <td className="px-4 py-3 text-right text-red-600 font-bold font-mono bg-red-50/30">
                                                    {item.edad_mas_90 !== 0 ? item.edad_mas_90.toLocaleString() : '-'}
                                                </td>
                                                <td className="px-6 py-3 text-right font-bold text-gray-900 border-l bg-gray-50/50">
                                                    ${item.saldo_total.toLocaleString()}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                    <tfoot className="bg-gray-800 text-white font-bold text-right border-t-2 border-indigo-500">
                                        <tr>
                                            <td colSpan="2" className="px-6 py-4 text-indigo-200">TOTAL GENERAL</td>
                                            <td className="px-4 py-4 font-mono">${data.total_corriente.toLocaleString()}</td>
                                            <td className="px-4 py-4 font-mono">${data.total_0_30.toLocaleString()}</td>
                                            <td className="px-4 py-4 font-mono">${data.total_31_60.toLocaleString()}</td>
                                            <td className="px-4 py-4 font-mono">${data.total_61_90.toLocaleString()}</td>
                                            <td className="px-4 py-4 font-mono text-red-300">${data.total_mas_90.toLocaleString()}</td>
                                            <td className="px-6 py-4 font-mono text-lg border-l border-gray-600">${data.total_general.toLocaleString()}</td>
                                        </tr>
                                    </tfoot>
                                </table>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="text-center py-20 bg-white rounded-xl border border-dashed">
                        Error cargando datos.
                    </div>
                )}
            </div>
        </div >
    );
}
