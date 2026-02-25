'use client';

import React, { useMemo } from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { FaChartPie, FaChartBar, FaInfoCircle, FaFilePdf } from 'react-icons/fa';
import domtoimage from 'dom-to-image-more';
import { jsPDF } from 'jspdf';
import { useRef, useState } from 'react';

// Registrar componentes de Chart.js
ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend
);

// Utilidad para formatear a pesos(COP) en los Tooltips
const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-CO', {
        style: 'currency',
        currency: 'COP',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
    }).format(value);
};

export default function BalanceGraphics({ reporte, empresaInfo, totalesCalculados }) {
    const activosRef = useRef();
    const pasivosRef = useRef();
    const [isExporting, setIsExporting] = useState(false);

    // --- PREPARACIÓN DE DATOS ---

    // 1. Gráfico de Barras: Distribución de Activos (Top 5)
    const barActivosData = useMemo(() => {
        if (!reporte) return null;

        const activosCombined = [
            ...(reporte.clasificado_activo?.corriente || []),
            ...(reporte.clasificado_activo?.no_corriente || [])
        ].filter(a => a.codigo && a.codigo.length > 1).sort((a, b) => b.saldo - a.saldo).slice(0, 5);

        return {
            labels: activosCombined.map(a => a.nombre.substring(0, 20) + (a.nombre.length > 20 ? '...' : '')),
            datasets: [
                {
                    label: 'Saldo ($)',
                    data: activosCombined.map(a => a.saldo),
                    backgroundColor: 'rgba(79, 70, 229, 0.7)', // Indigo
                    borderRadius: 6,
                },
            ],
        };
    }, [reporte]);

    // 2. Gráfico de Barras: Distribución de Pasivos (Top 5)
    const barPasivosData = useMemo(() => {
        if (!reporte) return null;

        const pasivosCombined = [
            ...(reporte.clasificado_pasivo?.corriente || []),
            ...(reporte.clasificado_pasivo?.no_corriente || [])
        ].filter(a => a.codigo && a.codigo.length > 1).sort((a, b) => b.saldo - a.saldo).slice(0, 5);

        return {
            labels: pasivosCombined.map(a => a.nombre.substring(0, 20) + (a.nombre.length > 20 ? '...' : '')),
            datasets: [
                {
                    label: 'Saldo ($)',
                    data: pasivosCombined.map(a => a.saldo),
                    backgroundColor: 'rgba(239, 68, 68, 0.7)', // Red
                    borderRadius: 6,
                },
            ],
        };
    }, [reporte]);

    // Configuraciones comunes de ChartJS

    const barOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false,
            },
            tooltip: {
                callbacks: {
                    label: function (context) {
                        let label = context.dataset.label || '';
                        if (label) {
                            label += ': ';
                        }
                        if (context.parsed.y !== null) {
                            label += formatCurrency(context.parsed.y);
                        }
                        return label;
                    }
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(0,0,0,0.05)',
                },
                ticks: {
                    callback: function (value) {
                        if (value >= 1000000) return '$' + (value / 1000000) + 'M';
                        if (value >= 1000) return '$' + (value / 1000) + 'k';
                        return '$' + value;
                    }
                }
            },
            x: {
                grid: { display: false }
            }
        }
    };

    const handleExportPDF = async () => {
        if (!activosRef.current || !pasivosRef.current) return;
        setIsExporting(true);

        try {
            // Capturar ambas tarjetas individualmente en máxima calidad
            const opts = {
                quality: 1,
                bgcolor: '#ffffff',
                style: { transform: 'scale(1)', transformOrigin: 'top left' }
            };

            const activosImgData = await domtoimage.toPng(activosRef.current, opts);
            const pasivosImgData = await domtoimage.toPng(pasivosRef.current, opts);

            const pdf = new jsPDF('p', 'mm', 'a4');
            const pdfWidth = pdf.internal.pageSize.getWidth();
            const pdfHeight = pdf.internal.pageSize.getHeight();

            // Cabecera Formal
            const titulo = empresaInfo?.razon_social?.toUpperCase() || 'EMPRESA DEMO S.A.S.';
            const nit = empresaInfo?.nit || '800.000.000-1';

            pdf.setFontSize(16);
            pdf.setFont("helvetica", "bold");
            pdf.text(titulo, pdfWidth / 2, 20, { align: 'center' });
            pdf.setFontSize(10);
            pdf.setFont("helvetica", "normal");
            pdf.text(`NIT: ${nit}`, pdfWidth / 2, 26, { align: 'center' });

            pdf.setFontSize(14);
            pdf.setFont("helvetica", "bold");
            pdf.text("REPORTES GRÁFICOS: BALANCE GENERAL", pdfWidth / 2, 35, { align: 'center' });

            // Cálculos de márgenes y tamaños maximizados
            const margin = 15;
            const contentWidth = pdfWidth - (margin * 2);

            const activosProps = pdf.getImageProperties(activosImgData);
            const pasivosProps = pdf.getImageProperties(pasivosImgData);

            // Ajustando a ancho máximo de la hoja
            const activosTargetHeight = (activosProps.height * contentWidth) / activosProps.width;
            const pasivosTargetHeight = (pasivosProps.height * contentWidth) / pasivosProps.width;

            // Verificar si caben en la página sin pasarse, si no, escalamos proporcionalmente
            const totalH = 45 + activosTargetHeight + 10 + pasivosTargetHeight + 20;

            if (totalH > pdfHeight) {
                // Escalar ambas para encajar en el límite vertical
                const available = pdfHeight - 45 - 20 - 10;
                const scale = available / (activosTargetHeight + pasivosTargetHeight);
                const fdW = contentWidth * scale;
                const fdH = activosTargetHeight * scale;
                const fbW = contentWidth * scale;
                const fbH = pasivosTargetHeight * scale;

                pdf.addImage(activosImgData, 'PNG', margin + (contentWidth - fdW) / 2, 45, fdW, fdH);
                pdf.addImage(pasivosImgData, 'PNG', margin + (contentWidth - fbW) / 2, 45 + fdH + 10, fbW, fbH);
            } else {
                pdf.addImage(activosImgData, 'PNG', margin, 45, contentWidth, activosTargetHeight);
                pdf.addImage(pasivosImgData, 'PNG', margin, 45 + activosTargetHeight + 10, contentWidth, pasivosTargetHeight);
            }

            // Footer
            pdf.setFontSize(8);
            pdf.setTextColor(150);
            pdf.text(`Generado por ContaPY2 IA - ${new Date().toLocaleDateString()}`, pdfWidth / 2, pdfHeight - 10, { align: 'center' });

            pdf.save(`Balance_Graficos_${new Date().getTime()}.pdf`);

        } catch (error) {
            console.error("Error generating PDF", error);
        } finally {
            setIsExporting(false);
        }
    };

    if (!reporte) return null;

    const { ecuacionCuadra, totalActivosCalc, totalPasivoPatrimonioCalc } = totalesCalculados || {};
    const diferenciaCalculada = Math.abs((totalActivosCalc || 0) - (totalPasivoPatrimonioCalc || 0));

    return (
        <div className="space-y-6 animate-fadeIn">
            {/* HEADER DE ALERTA/RESUMEN Y BOTÓN PDF */}
            <div className={`border rounded-2xl p-6 flex flex-col md:flex-row items-center justify-between shadow-sm ${ecuacionCuadra !== false ? 'bg-gradient-to-r from-indigo-50 to-blue-50 border-indigo-100' : 'bg-gradient-to-r from-red-50 to-orange-50 border-red-200'}`}>
                <div className="flex items-center gap-4">
                    <div className={`p-3 bg-white rounded-full shadow-sm ${ecuacionCuadra !== false ? 'text-indigo-600' : 'text-red-500'}`}>
                        <FaInfoCircle className="text-2xl" />
                    </div>
                    <div>
                        <h3 className={`text-lg font-bold ${ecuacionCuadra !== false ? 'text-slate-800' : 'text-red-700'}`}>
                            {ecuacionCuadra !== false ? 'Ecuación Contable Verificada' : 'Descuadre en Ecuación Contable'}
                        </h3>
                        <p className={`text-sm ${ecuacionCuadra !== false ? 'text-slate-500' : 'text-red-600 font-medium'}`}>
                            {ecuacionCuadra !== false
                                ? 'Los Activos totales cuadran con la suma del Pasivo y Patrimonio.'
                                : `Existe una diferencia matemática de ${formatCurrency(diferenciaCalculada)}.`}
                        </p>
                    </div>
                </div>
                <div className="mt-4 md:mt-0 flex flex-col items-end gap-3">
                    <div className="text-right">
                        <p className={`text-sm font-bold ${ecuacionCuadra !== false ? 'text-indigo-900' : 'text-red-900'}`}>Total Balance</p>
                        <p className={`text-3xl font-black tracking-tight ${ecuacionCuadra !== false ? 'text-indigo-700' : 'text-red-700'}`}>
                            {formatCurrency(totalActivosCalc || reporte.total_activos)}
                        </p>
                    </div>
                    <button
                        onClick={handleExportPDF}
                        disabled={isExporting}
                        className="bg-red-50 text-red-600 border border-red-200 hover:bg-red-100 px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2 transition-all shadow-sm"
                    >
                        {isExporting ? <span className="loading loading-spinner loading-xs"></span> : <FaFilePdf />}
                        Exportar Gráficos PDF
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-2 bg-white rounded-xl">

                {/* TARJETA BARRAS ACTIVOS */}
                <div ref={activosRef} className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col hover:shadow-md transition-shadow">
                    <div className="flex items-center gap-2 mb-6 border-b border-slate-100 pb-4">
                        <div className="bg-indigo-100 p-2 rounded-lg text-indigo-600"><FaChartBar /></div>
                        <h3 className="font-bold text-slate-800 text-lg">Distribución de Activos (Top 5)</h3>
                    </div>
                    <div className="relative h-72 w-full flex-grow">
                        <Bar data={barActivosData} options={barOptions} />
                    </div>
                </div>

                {/* TARJETA BARRAS PASIVOS */}
                <div ref={pasivosRef} className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col hover:shadow-md transition-shadow">
                    <div className="flex items-center gap-2 mb-6 border-b border-slate-100 pb-4">
                        <div className="bg-red-100 p-2 rounded-lg text-red-600"><FaChartBar /></div>
                        <h3 className="font-bold text-slate-800 text-lg">Distribución de Pasivos (Top 5)</h3>
                    </div>
                    <div className="relative h-72 w-full flex-grow">
                        <Bar data={barPasivosData} options={barOptions} />
                    </div>
                </div>

            </div>

        </div>
    );
}
