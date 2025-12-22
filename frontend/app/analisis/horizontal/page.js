'use client';

import React, { useState } from 'react';
import { getHorizontalAnalysis } from '../../../lib/dashboardService';
import { FaFilePdf, FaSearch, FaSpinner, FaArrowLeft, FaCalendarAlt, FaExchangeAlt, FaArrowUp, FaArrowDown } from 'react-icons/fa';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import Link from 'next/link';

export default function HorizontalAnalysisPage() {
    // Default: Compare Current Year vs Last Year
    const currentYear = new Date().getFullYear();
    const [p1Start, setP1Start] = useState(`${currentYear - 1}-01-01`);
    const [p1End, setP1End] = useState(`${currentYear - 1}-12-31`);
    const [p2Start, setP2Start] = useState(`${currentYear}-01-01`);
    const [p2End, setP2End] = useState(new Date().toISOString().split('T')[0]);

    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);

    const handleGenerate = async () => {
        setLoading(true);
        try {
            const result = await getHorizontalAnalysis(p1Start, p1End, p2Start, p2End);
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
            const doc = new jsPDF('l'); // Landscape for more columns

            doc.setFontSize(18);
            doc.text("Análisis Horizontal Financiero", 14, 15);

            doc.setFontSize(10);
            doc.text(`Comparativo: [${data.periodo_1_texto}] vs [${data.periodo_2_texto}]`, 14, 22);
            doc.text(`Generado: ${new Date().toLocaleDateString()}`, 14, 27);

            const tableBody = data.items.map(row => [
                row.codigo_cuenta,
                row.nombre_cuenta,
                `$ ${Number(row.saldo_periodo_1).toLocaleString('es-CO')}`,
                `$ ${Number(row.saldo_periodo_2).toLocaleString('es-CO')}`,
                `$ ${Number(row.variacion_absoluta).toLocaleString('es-CO')}`,
                `${Number(row.variacion_relativa).toFixed(2)} %`
            ]);

            autoTable(doc, {
                startY: 35,
                head: [['Código', 'Cuenta', 'Periodo 1', 'Periodo 2', 'Var. Abs ($)', 'Var. Rel (%)']],
                body: tableBody,
                theme: 'grid',
                headStyles: { fillColor: [44, 62, 80], textColor: 255 },
                styles: { fontSize: 8, cellPadding: 2 },
                columnStyles: {
                    0: { cellWidth: 25 },
                    1: { cellWidth: 'auto' },
                    2: { cellWidth: 35, halign: 'right' },
                    3: { cellWidth: 35, halign: 'right' },
                    4: { cellWidth: 35, halign: 'right', fontStyle: 'bold' },
                    5: { cellWidth: 25, halign: 'center' }
                },
                didParseCell: (data) => {
                    if (data.section === 'body') {
                        // Highlight rows
                        if (data.row.raw[0].length <= 4) {
                            data.cell.styles.fillColor = [240, 240, 240];
                            data.cell.styles.fontStyle = 'bold';
                        }
                        // Colorize Variation
                        if (data.column.index === 5) {
                            const val = parseFloat(data.cell.raw);
                            if (val < 0) data.cell.styles.textColor = [192, 57, 43];
                            else if (val > 0) data.cell.styles.textColor = [39, 174, 96];
                        }
                    }
                }
            });

            doc.save(`Analisis_Horizontal_Comparativo.pdf`);
        } catch (error) {
            console.error(error);
            alert("Error al generar PDF.");
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
                        <h1 className="text-3xl font-bold text-gray-800">Análisis Horizontal</h1>
                        <p className="text-gray-600">Compara la variación y tendencia entre dos periodos.</p>
                    </div>
                    {data && (
                        <button onClick={exportPDF} className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 font-bold flex items-center gap-2 shadow-sm">
                            <FaFilePdf /> Exportar PDF
                        </button>
                    )}
                </div>

                {/* Filters */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 mb-8">
                    <div className="flex flex-col lg:flex-row items-center gap-6">

                        {/* Period 1 */}
                        <div className="flex-1 w-full bg-blue-50 p-4 rounded-lg border border-blue-100">
                            <h3 className="font-bold text-blue-800 mb-2 border-b border-blue-200 pb-1">Periodo 1 (Base)</h3>
                            <div className="flex gap-2">
                                <div className="flex-1">
                                    <label className="text-xs text-blue-600 font-bold">Inicio</label>
                                    <input type="date" value={p1Start} onChange={e => setP1Start(e.target.value)} className="w-full text-sm border rounded p-1" />
                                </div>
                                <div className="flex-1">
                                    <label className="text-xs text-blue-600 font-bold">Fin</label>
                                    <input type="date" value={p1End} onChange={e => setP1End(e.target.value)} className="w-full text-sm border rounded p-1" />
                                </div>
                            </div>
                        </div>

                        <div className="text-gray-400">
                            <FaExchangeAlt className="text-2xl" />
                        </div>

                        {/* Period 2 */}
                        <div className="flex-1 w-full bg-green-50 p-4 rounded-lg border border-green-100">
                            <h3 className="font-bold text-green-800 mb-2 border-b border-green-200 pb-1">Periodo 2 (Actual)</h3>
                            <div className="flex gap-2">
                                <div className="flex-1">
                                    <label className="text-xs text-green-600 font-bold">Inicio</label>
                                    <input type="date" value={p2Start} onChange={e => setP2Start(e.target.value)} className="w-full text-sm border rounded p-1" />
                                </div>
                                <div className="flex-1">
                                    <label className="text-xs text-green-600 font-bold">Fin</label>
                                    <input type="date" value={p2End} onChange={e => setP2End(e.target.value)} className="w-full text-sm border rounded p-1" />
                                </div>
                            </div>
                        </div>

                        <button
                            onClick={handleGenerate}
                            disabled={loading}
                            className="bg-indigo-600 text-white px-8 py-4 rounded-xl hover:bg-indigo-700 font-bold flex flex-col items-center justify-center gap-1 transition shadow-lg disabled:opacity-50 min-w-[120px]"
                        >
                            {loading ? <FaSpinner className="animate-spin text-xl" /> : <FaSearch className="text-xl" />}
                            <span className="text-sm">Comparar</span>
                        </button>
                    </div>
                </div>

                {/* Results Table */}
                {data ? (
                    <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden animate-in fade-in zoom-in duration-300">
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-[#2c3e50] text-white">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider">Código</th>
                                        <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider">Cuenta</th>
                                        <th className="px-6 py-3 text-right text-xs font-bold uppercase tracking-wider bg-blue-900/30">Saldo P1</th>
                                        <th className="px-6 py-3 text-right text-xs font-bold uppercase tracking-wider bg-green-900/30">Saldo P2</th>
                                        <th className="px-6 py-3 text-right text-xs font-bold uppercase tracking-wider">Var. Abs ($)</th>
                                        <th className="px-6 py-3 text-center text-xs font-bold uppercase tracking-wider">Var. Rel (%)</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {data.items.map((row, idx) => {
                                        const isParent = row.codigo_cuenta.length <= 4;
                                        const isClass = row.codigo_cuenta.length === 1;
                                        const varRel = parseFloat(row.variacion_relativa);
                                        const isNegative = varRel < 0;
                                        const isPositive = varRel > 0;

                                        return (
                                            <tr key={idx} className={`${isClass ? 'bg-gray-100' : (isParent ? 'bg-gray-50' : 'hover:bg-gray-50')} transition-colors`}>
                                                <td className={`px-6 py-3 whitespace-nowrap text-sm ${isParent ? 'font-bold text-gray-900' : 'text-gray-600 font-mono'}`}>
                                                    {row.codigo_cuenta}
                                                </td>
                                                <td className={`px-6 py-3 whitespace-nowrap text-sm ${isParent ? 'font-bold text-gray-900' : 'text-gray-700'}`}>
                                                    {row.nombre_cuenta}
                                                </td>
                                                <td className="px-6 py-3 whitespace-nowrap text-sm text-right font-mono text-gray-600 bg-blue-50/30">
                                                    $ {Number(row.saldo_periodo_1).toLocaleString('es-CO')}
                                                </td>
                                                <td className="px-6 py-3 whitespace-nowrap text-sm text-right font-mono text-gray-900 font-medium bg-green-50/30">
                                                    $ {Number(row.saldo_periodo_2).toLocaleString('es-CO')}
                                                </td>
                                                <td className={`px-6 py-3 whitespace-nowrap text-sm text-right font-mono font-bold ${(row.variacion_absoluta < 0) ? 'text-red-500' : 'text-green-600'}`}>
                                                    {row.variacion_absoluta < 0 ? '-' : '+'} $ {Math.abs(row.variacion_absoluta).toLocaleString('es-CO')}
                                                </td>
                                                <td className="px-6 py-3 whitespace-nowrap text-center">
                                                    <span className={`px-2 py-1 rounded text-xs font-bold flex items-center justify-center gap-1
                                                        ${isNegative ? 'bg-red-100 text-red-700' : (isPositive ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500')}
                                                    `}>
                                                        {isNegative && <FaArrowDown />}
                                                        {isPositive && <FaArrowUp />}
                                                        {Math.abs(varRel).toFixed(2)} %
                                                    </span>
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
                            <FaExchangeAlt className="mx-auto text-4xl mb-4 text-gray-200" />
                            <p>Define los dos periodos a comparar y pulsa "Comparar".</p>
                        </div>
                    )
                )}
            </div>
        </div>
    );
}
