'use client';

import React, { useState } from 'react';
import { getVerticalAnalysis } from '../../../lib/dashboardService';
import { FaFilePdf, FaSearch, FaSpinner, FaArrowLeft, FaCalendarAlt } from 'react-icons/fa';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import Link from 'next/link';

export default function VerticalAnalysisPage() {
    const [startDate, setStartDate] = useState(new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0]);
    const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);

    const handleGenerate = async () => {
        setLoading(true);
        try {
            const result = await getVerticalAnalysis(startDate, endDate);
            setData(result);
        } catch (error) {
            console.error(error);
            alert("Error al generar el análisis.");
        } finally {
            setLoading(false);
        }
    };

    const exportPDF = () => {
        if (!data) return;

        try {
            const doc = new jsPDF();

            // Header
            doc.setFontSize(18);
            doc.text("Análisis Vertical Financiero", 14, 15);

            doc.setFontSize(10);
            doc.text(`Periodo: ${data.periodo_texto}`, 14, 22);
            doc.text(`Generado: ${new Date().toLocaleDateString()}`, 14, 27);

            const tableBody = data.items.map(row => [
                row.codigo_cuenta,
                row.nombre_cuenta,
                `$ ${Number(row.saldo_periodo_1).toLocaleString('es-CO')}`,
                `${Number(row.porcentaje_participacion).toFixed(2)} %`
            ]);

            autoTable(doc, {
                startY: 35,
                head: [['Código', 'Cuenta', 'Saldo', '% Part.']],
                body: tableBody,
                theme: 'grid',
                headStyles: { fillColor: [41, 128, 185], textColor: 255 },
                styles: { fontSize: 8, cellPadding: 2 },
                columnStyles: {
                    0: { cellWidth: 30 },
                    1: { cellWidth: 'auto' },
                    2: { cellWidth: 40, halign: 'right' },
                    3: { cellWidth: 20, halign: 'center' }
                },
                didParseCell: (data) => {
                    // Bold simple logic for parents based on code length
                    if (data.section === 'body' && data.row.raw[0].length <= 4) {
                        data.cell.styles.fontStyle = 'bold';
                        data.cell.styles.fillColor = [240, 240, 240];
                    }
                }
            });

            doc.save(`Analisis_Vertical_${endDate}.pdf`);
        } catch (error) {
            console.error("Error generating PDF:", error);
            alert("Error al generar el PDF.");
        }
    };

    return (
        <div className="p-6 bg-gray-50 min-h-screen">
            <div className="max-w-7xl mx-auto">
                <div className="flex justify-between items-center mb-6">
                    <div>
                        <Link href="/" className="text-gray-500 hover:text-blue-600 flex items-center gap-2 mb-2">
                            <FaArrowLeft /> Volver al Inicio
                        </Link>
                        <h1 className="text-3xl font-bold text-gray-800">Análisis Vertical</h1>
                        <p className="text-gray-600">Evalúa la estructura y peso porcentual de cada cuenta.</p>
                    </div>
                    {data && (
                        <button onClick={exportPDF} className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 font-bold flex items-center gap-2 shadow-sm">
                            <FaFilePdf /> Exportar PDF
                        </button>
                    )}
                </div>

                {/* Filters */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-wrap gap-4 items-end mb-8">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Fecha Inicio</label>
                        <div className="relative">
                            <FaCalendarAlt className="absolute left-3 top-3 text-gray-400" />
                            <input
                                type="date"
                                value={startDate}
                                onChange={e => setStartDate(e.target.value)}
                                className="pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none w-48"
                            />
                        </div>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Fecha Fin</label>
                        <div className="relative">
                            <FaCalendarAlt className="absolute left-3 top-3 text-gray-400" />
                            <input
                                type="date"
                                value={endDate}
                                onChange={e => setEndDate(e.target.value)}
                                className="pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none w-48"
                            />
                        </div>
                    </div>
                    <button
                        onClick={handleGenerate}
                        disabled={loading}
                        className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 font-bold flex items-center gap-2 transition disabled:opacity-50 h-[42px]"
                    >
                        {loading ? <FaSpinner className="animate-spin" /> : <FaSearch />} Generar
                    </button>
                </div>

                {/* Results Table */}
                {data ? (
                    <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden animate-in fade-in slide-in-from-bottom-4">
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Código</th>
                                        <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Cuenta</th>
                                        <th className="px-6 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider">Saldo</th>
                                        <th className="px-6 py-3 text-center text-xs font-bold text-gray-500 uppercase tracking-wider">% Participación</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {data.items.map((row, idx) => {
                                        const isParent = row.codigo_cuenta.length <= 4;
                                        const isClass = row.codigo_cuenta.length === 1;
                                        return (
                                            <tr key={idx} className={`${isClass ? 'bg-gray-100' : (isParent ? 'bg-gray-50' : 'hover:bg-blue-50')} transition-colors`}>
                                                <td className={`px-6 py-3 whitespace-nowrap text-sm ${isParent ? 'font-bold text-gray-900' : 'text-gray-600 font-mono'}`}>
                                                    {row.codigo_cuenta}
                                                </td>
                                                <td className={`px-6 py-3 whitespace-nowrap text-sm ${isParent ? 'font-bold text-gray-900' : 'text-gray-700'}`}>
                                                    {row.nombre_cuenta}
                                                </td>
                                                <td className="px-6 py-3 whitespace-nowrap text-sm text-right font-mono text-gray-800">
                                                    $ {Number(row.saldo_periodo_1).toLocaleString('es-CO')}
                                                </td>
                                                <td className="px-6 py-3 whitespace-nowrap text-center">
                                                    <div className="flex items-center justify-center gap-2">
                                                        <span className="text-sm font-bold text-blue-600 w-16 text-right">
                                                            {Number(row.porcentaje_participacion).toFixed(2)} %
                                                        </span>
                                                        <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                                                            <div
                                                                className="h-full bg-blue-500"
                                                                style={{ width: `${Math.min(Math.abs(row.porcentaje_participacion), 100)}%` }}
                                                            ></div>
                                                        </div>
                                                    </div>
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </div>
                ) : (
                    !loading && (
                        <div className="text-center py-12 text-gray-400 bg-white rounded-xl border border-dashed border-gray-300">
                            <FaSearch className="mx-auto text-4xl mb-4 text-gray-200" />
                            <p>Selecciona un rango de fechas y genera el informe.</p>
                        </div>
                    )
                )}
            </div>
        </div>
    );
}
