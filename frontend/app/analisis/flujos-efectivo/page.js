'use client';

import React, { useState, useEffect } from 'react';
import { FaCalendarAlt, FaSearch, FaFilePdf, FaFileCsv, FaInfoCircle, FaCheckCircle, FaExclamationTriangle } from 'react-icons/fa';
import { formatCurrency } from '../../../utils/format';
import { useAuth } from '../../context/AuthContext';
import { apiService } from '../../../lib/apiService';
import { toast } from 'react-toastify';
import Link from 'next/link';

export default function FlujoEfectivoPage() {
    const { user, authLoading } = useAuth();
    const [fechaInicio, setFechaInicio] = useState('');
    const [fechaFin, setFechaFin] = useState('');
    const [reportData, setReportData] = useState(null);
    const [loading, setLoading] = useState(false);

    // Establecer fechas por defecto (mes actual)
    useEffect(() => {
        const today = new Date();
        const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
        setFechaInicio(firstDay.toISOString().split('T')[0]);
        setFechaFin(today.toISOString().split('T')[0]);
    }, []);

    const fetchReport = async () => {
        if (!user || !user.empresaId) {
            toast.error("Usuario no autenticado o sin empresa asignada.");
            return;
        }

        setLoading(true);
        try {
            const res = await apiService.get('/analisis/flujo-efectivo', {
                params: {
                    fecha_inicio: fechaInicio,
                    fecha_fin: fechaFin,
                    empresa_id: user.empresaId
                }
            });
            setReportData(res.data);
        } catch (error) {
            console.error(error);
            toast.error("No se pudo cargar el reporte.");
        } finally {
            setLoading(false);
        }
    };


    const handleExportPDF = async () => {
        if (!user || !user.empresaId || !fechaInicio || !fechaFin) {
            toast.warning("Faltan parámetros para generar el PDF.");
            return;
        }

        try {
            // 1. Obtener URL Firmada
            const signRes = await apiService.get('/analisis/flujo-efectivo/get-signed-url', {
                params: {
                    fecha_inicio: fechaInicio,
                    fecha_fin: fechaFin,
                    empresa_id: user.empresaId
                }
            });

            const token = signRes.data.signed_url_token;

            // 2. Abrir en nueva pestaña
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || '';
            const pdfUrl = `${baseUrl}/api/analisis/flujo-efectivo/imprimir?signed_token=${token}`;
            window.open(pdfUrl, '_blank');

        } catch (error) {
            console.error("Error Export PDF:", error);
            toast.error("No se pudo iniciar la descarga del PDF.");
        }
    };

    const handleExportCSV = () => {
        if (!reportData) {
            alert("Genere el reporte primero.");
            return;
        }

        let csvContent = "\uFEFF"; // BOM para Excel
        csvContent += "Concepto Financiero,Valor,Categoria\n";

        const processRows = (rows, category) => {
            rows.forEach(row => {
                const line = [
                    `"${row.concepto.replace(/"/g, '""')}"`,
                    row.valor,
                    category
                ].join(",");
                csvContent += line + "\n";
            });
        };

        if (reportData.flujos_operacion?.detalles) processRows(reportData.flujos_operacion.detalles, "Operacion");
        if (reportData.flujos_inversion?.detalles) processRows(reportData.flujos_inversion.detalles, "Inversion");
        if (reportData.flujos_financiacion?.detalles) processRows(reportData.flujos_financiacion.detalles, "Financiacion");

        // Totales al final
        csvContent += `\n,Flujo Neto Operacion,${reportData.flujos_operacion.total}\n`;
        csvContent += `,Flujo Neto Inversion,${reportData.flujos_inversion.total}\n`;
        csvContent += `,Flujo Neto Financiacion,${reportData.flujos_financiacion.total}\n`;
        csvContent += `,Flujo Neto Total,${reportData.flujos_netos_totales}\n`;

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.setAttribute("href", url);
        link.setAttribute("download", `Flujo_Efectivo_${fechaInicio}_${fechaFin}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    return (
        <div className="bg-white rounded-xl shadow-lg p-8 max-w-7xl mx-auto my-6">
            {/* Encabezado y Filtros */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-10 gap-6">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        <h1 className="text-3xl font-extrabold text-gray-800 tracking-tight">Estado de Flujos de Efectivo</h1>
                        <Link href="/manual?file=manual_flujo_efectivo.md" target="_blank" className="text-indigo-600 hover:text-indigo-800" title="Ver Manual de Ayuda">
                            <FaInfoCircle size={22} />
                        </Link>
                    </div>
                    <p className="text-gray-500 text-lg">Reporte Financiero de Variación del Efectivo.</p>
                </div>

                <div className="flex flex-col sm:flex-row gap-4 items-end">
                    <div className="flex gap-4 p-4 bg-gray-50 rounded-xl border border-gray-100 shadow-sm">
                        <div className="flex flex-col">
                            <label className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Desde</label>
                            <input
                                type="date"
                                value={fechaInicio}
                                onChange={(e) => setFechaInicio(e.target.value)}
                                className="input input-bordered input-sm w-40 font-medium text-gray-700 focus:ring-2 focus:ring-indigo-500"
                            />
                        </div>
                        <div className="flex flex-col">
                            <label className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Hasta</label>
                            <input
                                type="date"
                                value={fechaFin}
                                onChange={(e) => setFechaFin(e.target.value)}
                                className="input input-bordered input-sm w-40 font-medium text-gray-700 focus:ring-2 focus:ring-indigo-500"
                            />
                        </div>
                        <button
                            onClick={fetchReport}
                            className="bg-indigo-600 text-white px-6 py-2 rounded-lg shadow-sm hover:bg-indigo-700 font-semibold flex items-center gap-2 h-10 transition-colors"
                            disabled={loading}
                        >
                            {loading ? <span className="loading loading-spinner loading-xs"></span> : <FaSearch />}
                            Generar
                        </button>
                    </div>

                    <div className="flex gap-2">
                        <button onClick={handleExportCSV} className="text-emerald-600 border border-emerald-600 hover:bg-emerald-50 px-4 py-2 rounded-lg font-medium flex items-center gap-2 transition-colors" title="Descargar CSV">
                            <FaFileCsv /> CSV
                        </button>
                        <button onClick={handleExportPDF} className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 font-medium flex items-center gap-2 shadow-sm transition-colors" title="Ver PDF">
                            <FaFilePdf /> PDF
                        </button>
                    </div>
                </div>
            </div>

            {!reportData && !loading && (
                <div className="text-center py-20 bg-gray-50 rounded-2xl border-2 border-dashed border-gray-200">
                    <FaSearch className="text-gray-300 text-6xl mx-auto mb-4" />
                    <p className="text-gray-500 text-xl font-medium">Selecciona un rango de fechas y genera el estado financiero.</p>
                </div>
            )}

            {loading && (
                <div className="flex justify-center py-20">
                    <span className="loading loading-dots loading-lg text-indigo-600"></span>
                </div>
            )}

            {reportData && (
                <div className="space-y-8 animate-fade-in-up">
                    {/* Resumen Inicial */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <SummaryCard title="Saldo Inicial" amount={reportData.saldo_inicial} color="blue" />
                        <SummaryCard title="Flujos Netos del Período" amount={reportData.flujos_netos_totales} color={reportData.flujos_netos_totales >= 0 ? "green" : "red"} />
                        <SummaryCard title="Saldo Final" amount={reportData.saldo_final_calculado} color="indigo" isTotal />
                    </div>

                    {/* Alerta de Validación */}
                    {!reportData.validacion.es_valido && (
                        <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-4 rounded-r shadow-sm">
                            <div className="flex items-center">
                                <FaExclamationTriangle className="text-red-500 text-xl mr-3" />
                                <div>
                                    <p className="font-bold text-red-700">Advertencia de Integridad Financiera</p>
                                    <p className="text-sm text-red-600">
                                        El flujo de efectivo calculado no coincide con el saldo en libros.
                                        Diferencia: {formatCurrency(reportData.validacion.diferencia)}
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Bloques de Actividad */}
                    <div className="grid grid-cols-1 gap-8">
                        <ActivityBlock
                            title="Actividades de Operación"
                            data={reportData.flujos_operacion}
                            color="emerald"
                            description="Entradas y salidas relacionadas con el giro ordinario del negocio"
                        />
                        <ActivityBlock
                            title="Actividades de Inversión"
                            data={reportData.flujos_inversion}
                            color="amber"
                            description="Adquisición y venta de activos a largo plazo"
                        />
                        <ActivityBlock
                            title="Actividades de Financiación"
                            data={reportData.flujos_financiacion}
                            color="purple"
                            description="Movimientos de deuda y capital"
                        />
                    </div>

                    {/* Conciliación */}
                    <div className="bg-gray-900 text-white p-6 rounded-xl shadow-xl mt-8">
                        <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                            <FaCheckCircle className="text-green-400" /> Conciliación de Efectivo
                        </h3>
                        <div className="flex justify-between items-center text-lg border-b border-gray-700 pb-2 mb-2">
                            <span>Saldo Inicial</span>
                            <span className="font-mono">{formatCurrency(reportData.saldo_inicial)}</span>
                        </div>
                        <div className="flex justify-between items-center text-lg border-b border-gray-700 pb-2 mb-2">
                            <span>(+) Flujos Netos Totales</span>
                            <span className="font-mono">{formatCurrency(reportData.flujos_netos_totales)}</span>
                        </div>
                        <div className="flex justify-between items-center text-2xl font-bold pt-2">
                            <span>(=) Nuevo Saldo Disponible (Calculado)</span>
                            <span className={`font-mono ${reportData.validacion.es_valido ? 'text-green-400' : 'text-yellow-400'}`}>
                                {formatCurrency(reportData.saldo_final_calculado)}
                            </span>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

// Subcomponentes
function SummaryCard({ title, amount, color, isTotal }) {
    const formatColor = {
        blue: "bg-blue-50 text-blue-700 border-blue-100",
        green: "bg-green-50 text-green-700 border-green-100",
        red: "bg-red-50 text-red-700 border-red-100",
        indigo: "bg-indigo-50 text-indigo-700 border-indigo-100",
    }[color] || "bg-gray-50 text-gray-700";

    return (
        <div className={`p-6 rounded-xl border shadow-sm ${formatColor} ${isTotal ? 'ring-2 ring-indigo-500' : ''}`}>
            <p className="text-sm font-semibold opacity-80 uppercase tracking-wide mb-2">{title}</p>
            <p className="text-3xl font-extrabold tracking-tight">{formatCurrency(amount)}</p>
        </div>
    );
}

function ActivityBlock({ title, data, color, description }) {
    const config = {
        emerald: { border: "border-emerald-200", title: "text-emerald-800", bg: "bg-emerald-50", icon: "bg-emerald-100 text-emerald-600" },
        amber: { border: "border-amber-200", title: "text-amber-800", bg: "bg-amber-50", icon: "bg-amber-100 text-amber-600" },
        purple: { border: "border-purple-200", title: "text-purple-800", bg: "bg-purple-50", icon: "bg-purple-100 text-purple-600" },
    }[color];

    return (
        <div className={`border rounded-xl overflow-hidden shadow-sm ${config.border}`}>
            <div className={`px-6 py-4 flex justify-between items-center ${config.bg} border-b ${config.border}`}>
                <div>
                    <h3 className={`text-xl font-bold ${config.title}`}>{title}</h3>
                    <p className="text-sm text-gray-500 mt-1">{description}</p>
                </div>
                <div className="text-right">
                    <span className={`text-2xl font-bold ${data.total >= 0 ? "text-gray-800" : "text-red-600"}`}>
                        {formatCurrency(data.total)}
                    </span>
                </div>
            </div>
            <div className="p-0">
                <table className="w-full text-sm text-left">
                    <thead className="bg-gray-50 text-gray-500 font-semibold uppercase text-xs">
                        <tr>
                            <th className="px-6 py-3">Concepto Financiero</th>
                            <th className="px-6 py-3 text-right">Valor</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {data.detalles.length === 0 ? (
                            <tr>
                                <td colSpan="2" className="px-6 py-8 text-center text-gray-400 italic">No hay movimientos en este período.</td>
                            </tr>
                        ) : (
                            data.detalles.map((mov, idx) => (
                                <tr key={idx} className="hover:bg-gray-50 transition-colors">
                                    <td className="px-6 py-3 font-medium text-gray-800">{mov.concepto}</td>
                                    <td className={`px-6 py-3 text-right font-mono font-medium ${mov.valor >= 0 ? 'text-green-600' : 'text-red-500'}`}>
                                        {formatCurrency(mov.valor)}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

// Helper mock para formatCurrency si no existe en path relativo.
// En producción, borrar esto y usar import real.
// const formatCurrency = (val) => new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(val);
