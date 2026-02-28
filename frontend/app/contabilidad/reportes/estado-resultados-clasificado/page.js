'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Script from 'next/script';
import {
    FaCalendarAlt,
    FaSearch,
    FaFilePdf,
    FaFileCsv,
    FaMoneyBillWave,
    FaShoppingCart,
    FaExclamationTriangle,
    FaBook,
    FaArrowUp,
    FaArrowDown,
    FaPercent,
    FaBalanceScale
} from 'react-icons/fa';
import { LucideBarChart3, LucideTrendingUp, LucideGlobe } from 'lucide-react';

import { toast } from 'react-toastify';
import { useAuth } from '../../../context/AuthContext';
import { apiService } from '../../../../lib/apiService';

// Estilos Reusables Premium
const labelClass = "block text-[10px] font-bold text-slate-400 uppercase mb-1.5 tracking-widest";
const inputClass = "w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none pl-10 hover:border-indigo-300";

const WaterfallBar = ({ label, value, max, color, subLabel }) => {
    const widthPercentage = max > 0 ? (Math.abs(value) / max) * 100 : 0;
    return (
        <div className="group">
            <div className="flex justify-between items-end mb-1 px-1">
                <div className="flex flex-col">
                    <span className="text-[11px] font-bold text-slate-500 uppercase tracking-tight">{label}</span>
                    {subLabel && <span className="text-[9px] font-black text-indigo-400 -mt-0.5">{subLabel}</span>}
                </div>
                <span className="text-xs font-black text-slate-700">{new Intl.NumberFormat('es-CO').format(value)}</span>
            </div>
            <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden">
                <div
                    className={`h-full transition-all duration-1000 ease-out rounded-full ${color}`}
                    style={{ width: `${widthPercentage}%` }}
                />
            </div>
        </div>
    );
};

const KpiCard = ({ title, value, percentage, icon: Icon, colorClass, trend }) => (
    <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 flex items-start justify-between hover:shadow-md transition-all group overflow-hidden relative">
        <div className="flex-1">
            <p className="text-slate-500 text-xs font-bold uppercase tracking-wider mb-1">{title}</p>
            <h4 className="text-2xl font-black text-slate-800 tracking-tight">{value}</h4>
            <div className="flex items-center gap-1.5 mt-2">
                <div className={`flex items-center gap-0.5 px-2 py-0.5 rounded-full text-[10px] font-bold ${trend === 'up' ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'}`}>
                    {trend === 'up' ? <FaArrowUp size={8} /> : <FaArrowDown size={8} />}
                    {percentage}%
                </div>
            </div>
        </div>
        <div className={`p-3 rounded-xl ${colorClass} text-white shadow-lg transform group-hover:scale-110 transition-transform`}>
            {Icon}
        </div>
    </div>
);

export default function EstadoResultadosClasificadoPage() {
    const { user, loading: authLoading } = useAuth();
    const router = useRouter();

    const [reporte, setReporte] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [fechaInicio, setFechaInicio] = useState(new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0]);
    const [fechaFin, setFechaFin] = useState(new Date().toISOString().split('T')[0]);
    const [isPageReady, setPageReady] = useState(false);

    useEffect(() => {
        if (!authLoading) {
            if (user && user.empresaId) {
                setPageReady(true);
            } else {
                router.push('/login');
            }
        }
    }, [user, authLoading, router]);

    const handleGenerateReport = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const res = await apiService.get('/reports/income-statement', {
                params: { fecha_inicio: fechaInicio, fecha_fin: fechaFin, nivel: 4 }
            });
            setReporte(res.data);
            toast.success("✨ Reporte consolidado generado");
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al generar el reporte.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleExportPDF = async () => {
        if (!reporte) return;
        setIsLoading(true);
        try {
            const signedUrlRes = await apiService.get('/reports/income-statement/get-signed-url', {
                params: { fecha_inicio: fechaInicio, fecha_fin: fechaFin, nivel: 4 }
            });
            const signedToken = signedUrlRes.data.signed_url_token;
            const finalPdfUrl = `${process.env.NEXT_PUBLIC_API_URL}/api/reports/income-statement/imprimir?signed_token=${signedToken}`;
            window.open(finalPdfUrl, '_blank');
        } catch (err) {
            setError('Error al obtener el PDF.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleExportCSV = () => {
        if (!reporte || typeof window.Papa === 'undefined') return;
        const dataParaCSV = [];
        const formatNum = (n) => (n || 0).toFixed(2);

        const pushSection = (label, items, total) => {
            dataParaCSV.push({ Cuenta: label, Valor: '', Participacion: '' });
            items.forEach(i => dataParaCSV.push({ Cuenta: `${i.codigo} - ${i.nombre}`, Valor: formatNum(i.saldo), Participacion: formatNum(i.porcentaje) + '%' }));
            dataParaCSV.push({ Cuenta: `TOTAL ${label}`, Valor: formatNum(total), Participacion: '---' });
            dataParaCSV.push({});
        };

        pushSection('INGRESOS', reporte.ingresos, reporte.totales.total_ingresos);
        pushSection('COSTOS', reporte.costos, reporte.totales.total_costos);
        dataParaCSV.push({ Cuenta: 'UTILIDAD BRUTA', Valor: formatNum(reporte.totales.utilidad_bruta), Participacion: formatNum(reporte.totales.porcentaje_utilidad_bruta) + '%' });
        dataParaCSV.push({});
        pushSection('GASTOS', reporte.gastos, reporte.totales.total_gastos);
        dataParaCSV.push({ Cuenta: 'UTILIDAD NETA', Valor: formatNum(reporte.totales.utilidad_neta), Participacion: formatNum(reporte.totales.porcentaje_utilidad_neta) + '%' });

        const csv = window.Papa.unparse(dataParaCSV);
        const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `ER-Clasificado-${fechaInicio}.csv`;
        link.click();
    };

    const formatCurrency = (val) => new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(val);

    const AccountRowSimple = ({ codigo, nombre, saldo, porcentaje, isNegative }) => (
        <div className="flex justify-between items-center py-3 border-b border-slate-50 hover:bg-slate-50 transition-colors px-4 rounded-xl">
            <div className="flex items-center gap-4">
                <span className="font-mono text-[10px] font-black px-2 py-0.5 rounded bg-slate-100 text-slate-500 border border-slate-200">{codigo}</span>
                <span className="text-sm font-semibold text-slate-700">{nombre}</span>
            </div>
            <div className="flex items-center gap-8">
                <span className="text-[11px] font-bold text-slate-400 w-12 text-right">{porcentaje?.toFixed(1)}%</span>
                <span className={`font-mono text-sm w-32 text-right font-black ${isNegative ? 'text-rose-600' : 'text-slate-800'}`}>
                    {isNegative ? `(${formatCurrency(Math.abs(saldo))})` : formatCurrency(saldo)}
                </span>
            </div>
        </div>
    );

    if (!isPageReady) return <div className="min-h-screen flex items-center justify-center bg-slate-50"><LucideTrendingUp className="animate-spin text-indigo-600" size={48} /></div>;

    return (
        <div className="min-h-screen bg-slate-50/50 p-6 md:p-12 pb-32">
            <div className="max-w-6xl mx-auto">
                <div className="flex justify-between items-center mb-10">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-indigo-600 text-white rounded-2xl shadow-lg ring-4 ring-indigo-50">
                            <FaBalanceScale size={24} />
                        </div>
                        <div>
                            <h1 className="text-2xl font-black text-slate-800 tracking-tight">Estado de Resultados Clasificado</h1>
                            <p className="text-slate-500 text-xs font-bold uppercase tracking-widest mt-0.5">Visión Ejecutiva (Cuentas Mayores)</p>
                        </div>
                    </div>
                    <button onClick={() => router.push('/contabilidad/reportes/estado-resultados')} className="text-xs font-black text-indigo-600 hover:text-indigo-800 bg-indigo-50 px-4 py-2 rounded-xl transition-all">Ver Analítico →</button>
                </div>

                {/* Filtros Simplificados */}
                <div className="bg-white rounded-3xl shadow-sm border border-slate-100 p-8 mb-8">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-end">
                        <div>
                            <label className={labelClass}>Periodo Desde</label>
                            <div className="relative">
                                <input type="date" value={fechaInicio} onChange={e => setFechaInicio(e.target.value)} className={inputClass} />
                                <FaCalendarAlt size={12} className="absolute left-3.5 top-3.5 text-indigo-400" />
                            </div>
                        </div>
                        <div>
                            <label className={labelClass}>Hasta</label>
                            <div className="relative">
                                <input type="date" value={fechaFin} onChange={e => setFechaFin(e.target.value)} className={inputClass} />
                                <FaCalendarAlt size={12} className="absolute left-3.5 top-3.5 text-indigo-400" />
                            </div>
                        </div>
                        <button onClick={handleGenerateReport} disabled={isLoading} className="bg-slate-900 text-white h-[46px] rounded-xl font-black text-xs uppercase tracking-widest hover:bg-indigo-600 transition-all shadow-lg flex items-center justify-center gap-2">
                            {isLoading ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <><FaSearch /> Generar</>}
                        </button>
                    </div>
                </div>

                {reporte && (
                    <div className="space-y-10 animate-fadeIn">
                        {/* El usuario solicitó quitar los KPIs horizontales y dejar solo el análisis vertical */}
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                            {/* Panel Visual Izquierdo */}
                            <div className="lg:col-span-1 bg-white rounded-3xl p-8 border border-slate-100 shadow-sm flex flex-col">
                                <div className="flex items-center gap-3 mb-8">
                                    <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg"><LucideBarChart3 size={18} /></div>
                                    <h4 className="text-base font-black text-slate-800 tracking-tight">Estructura de Margen</h4>
                                </div>
                                <div className="space-y-8 flex-1">
                                    <WaterfallBar label="Ingresos" value={reporte.totales.total_ingresos} max={reporte.totales.total_ingresos} color="bg-indigo-600" />
                                    <WaterfallBar label="(-) Costos de Venta" value={Math.abs(reporte.totales.total_costos)} max={reporte.totales.total_ingresos} color="bg-rose-400" />
                                    <div className="pt-2 border-t border-slate-100">
                                        <WaterfallBar
                                            label="(=) Utilidad Bruta"
                                            value={reporte.totales.utilidad_bruta}
                                            max={reporte.totales.total_ingresos}
                                            color="bg-emerald-400 opacity-60"
                                            subLabel={`${reporte.totales.porcentaje_utilidad_bruta?.toFixed(1)}% Margen Bruto`}
                                        />
                                    </div>
                                    <WaterfallBar label="(-) Gastos Operativos" value={Math.abs(reporte.totales.total_gastos)} max={reporte.totales.total_ingresos} color="bg-orange-400" />
                                    <div className="pt-4 mt-4 border-t-2 border-slate-200">
                                        <WaterfallBar
                                            label="(=) Utilidad Neta"
                                            value={reporte.totales.utilidad_neta}
                                            max={reporte.totales.total_ingresos}
                                            color="bg-emerald-600 shadow-lg shadow-emerald-50"
                                            subLabel={`${reporte.totales.porcentaje_utilidad_neta?.toFixed(1)}% Margen Neto`}
                                        />
                                    </div>
                                </div>
                                <div className="mt-10 p-4 bg-indigo-50/50 rounded-2xl border border-indigo-100">
                                    <p className="text-[10px] font-black text-indigo-600 uppercase tracking-widest mb-1">Análisis Ejecutivo</p>
                                    <p className="text-xs text-slate-600 leading-relaxed font-medium">
                                        A nivel consolidado, la <span className="text-indigo-600 font-bold">utilidad neta</span> representa el <span className="font-black text-indigo-700">{reporte.totales.porcentaje_utilidad_neta?.toFixed(2)}%</span> de la operación.
                                    </p>
                                </div>
                            </div>

                            <div className="lg:col-span-2 bg-white rounded-3xl border border-slate-100 shadow-sm overflow-hidden flex flex-col">
                                <div className="p-4 bg-slate-50 border-b border-slate-100 flex justify-between items-center">
                                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest px-2">Consolidado Contable</span>
                                    <div className="flex gap-2">
                                        <button onClick={handleExportCSV} className="p-2 text-emerald-600 hover:bg-white rounded-lg transition-all"><FaFileCsv size={16} /></button>
                                        <button onClick={handleExportPDF} className="p-2 text-rose-600 hover:bg-white rounded-lg transition-all"><FaFilePdf size={16} /></button>
                                    </div>
                                </div>

                                <div className="p-4 space-y-8 flex-1 overflow-auto max-h-[600px] custom-scrollbar">
                                    <div>
                                        <p className="text-[10px] font-black text-indigo-400 uppercase mb-4 px-2">Estructura de Ingresos</p>
                                        <div className="space-y-1">
                                            {reporte.ingresos.map(i => <AccountRowSimple key={i.codigo} {...i} />)}
                                        </div>
                                    </div>

                                    {reporte.costos?.length > 0 && (
                                        <div>
                                            <p className="text-[10px] font-black text-rose-400 uppercase mb-4 px-2">Costos Consolidados</p>
                                            <div className="space-y-1">
                                                {reporte.costos.map(i => <AccountRowSimple key={i.codigo} {...i} isNegative={true} />)}
                                            </div>
                                        </div>
                                    )}

                                    <div>
                                        <p className="text-[10px] font-black text-slate-400 uppercase mb-4 px-2">Gastos Administrativos y Operativos</p>
                                        <div className="space-y-1">
                                            {reporte.gastos.map(i => <AccountRowSimple key={i.codigo} {...i} isNegative={true} />)}
                                        </div>
                                    </div>
                                </div>

                                <div className={`p-8 ${reporte.totales.utilidad_neta >= 0 ? 'bg-slate-900' : 'bg-rose-900'} text-white flex justify-between items-center rounded-b-3xl`}>
                                    <div>
                                        <h3 className="text-xl font-black uppercase tracking-tighter">Utilidad del Ejercicio</h3>
                                        <p className="text-[10px] opacity-60 font-bold uppercase tracking-widest">Nivel 4 Cuatro Dígitos</p>
                                    </div>
                                    <span className="text-3xl font-black tracking-tighter">{formatCurrency(reporte.totales.utilidad_neta)}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
            <Script src="https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js" />
        </div>
    );
}
