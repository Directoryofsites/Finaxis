'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Script from 'next/script';
import {
    FaChartLine,
    FaCalendarAlt,
    FaSearch,
    FaFilePdf,
    FaFileCsv,
    FaMoneyBillWave,
    FaShoppingCart,
    FaCalculator,
    FaExclamationTriangle,
    FaBook,
    FaArrowUp,
    FaArrowDown,
    FaPercent
} from 'react-icons/fa';
import { LucideTrendingUp, LucideTrendingDown, LucideDollarSign, LucideBarChart3 } from 'lucide-react';

import { toast } from 'react-toastify';
import { useAuth } from '../../../context/AuthContext';
import { apiService } from '../../../../lib/apiService';

// Estilos Reusables (Manual v2.0 con estética Premium)
const labelClass = "block text-[10px] font-bold text-slate-400 uppercase mb-1.5 tracking-widest";
const inputClass = "w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none pl-10 hover:border-indigo-300";

// Componentes Internos Especializados
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
        <div className="absolute -right-2 -bottom-2 opacity-[0.03] text-6xl transform rotate-12 group-hover:rotate-0 transition-transform">
            {Icon}
        </div>
    </div>
);

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

export default function EstadoResultadosPage() {
    const { user, loading: authLoading } = useAuth();
    const router = useRouter();

    const [reporte, setReporte] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [fechaInicio, setFechaInicio] = useState(new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0]);
    const [fechaFin, setFechaFin] = useState(new Date().toISOString().split('T')[0]);
    const [isPageReady, setPageReady] = useState(false);

    // Automation State
    const [autoPdfTrigger, setAutoPdfTrigger] = useState(false);
    const [wppNumber, setWppNumber] = useState(null);
    const [emailAddress, setEmailAddress] = useState(null);
    const lastProcessedParams = React.useRef('');

    useEffect(() => {
        if (!authLoading) {
            if (user && user.empresaId) {
                setPageReady(true);
            } else {
                router.push('/login');
            }
        }
    }, [user, authLoading, router]);

    // --- AUTO-CONFIGURACION (IA) ---
    useEffect(() => {
        if (isPageReady) {
            const urlParams = new URLSearchParams(window.location.search);
            const aiInicio = urlParams.get('fecha_inicio');
            const aiFin = urlParams.get('fecha_fin');
            const pAutoPdf = urlParams.get('auto_pdf');
            const pWpp = urlParams.get('wpp');
            const pEmail = urlParams.get('email');

            if (aiInicio && aiFin) {
                const currentSignature = `${aiInicio}-${aiFin}-${pAutoPdf}-${pWpp}-${pEmail}`;
                if (lastProcessedParams.current === currentSignature) return;
                lastProcessedParams.current = currentSignature;

                setFechaInicio(aiInicio);
                setFechaFin(aiFin);

                if (pAutoPdf === 'true') setAutoPdfTrigger(true);
                if (pWpp) setWppNumber(pWpp);
                if (pEmail) setEmailAddress(pEmail);

                // Auto-ejecutar
                setTimeout(() => {
                    document.getElementById('btn-generar-er')?.click();
                    window.history.replaceState(null, '', window.location.pathname);
                }, 800);
            }
        }
    }, [isPageReady]);

    const handleGenerateReport = async () => {
        if (!fechaInicio || !fechaFin) {
            setError("Por favor, seleccione una fecha de inicio y una fecha de fin.");
            return;
        }
        setIsLoading(true);
        setError(null);
        setReporte(null);

        const params = {
            fecha_inicio: fechaInicio,
            fecha_fin: fechaFin,
        };

        try {
            const res = await apiService.get('/reports/income-statement', { params: params });
            setReporte(res.data);
            toast.success("✨ Inteligencia financiera cargada");
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al generar el reporte de Estado de Resultados.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleExportCSV = () => {
        if (!reporte) return;
        if (typeof window.Papa === 'undefined') {
            alert("La librería CSV no está lista. Por favor, recargue la página.");
            return;
        }

        const dataParaCSV = [];
        const formatNumber = (num) => (num || 0).toFixed(2);
        const totales = reporte.totales;

        dataParaCSV.push({ Seccion: 'INGRESOS', Codigo: '', Cuenta: '', Saldo: '', Porcentaje: '100%' });
        reporte.ingresos.forEach(item => { dataParaCSV.push({ Seccion: '', Codigo: item.codigo, Cuenta: item.nombre, Saldo: formatNumber(item.saldo), Porcentaje: formatNumber(item.porcentaje) + '%' }); });
        dataParaCSV.push({ Cuenta: 'TOTAL INGRESOS', Saldo: formatNumber(totales.total_ingresos) });
        dataParaCSV.push({});

        if (reporte.costos && reporte.costos.length > 0) {
            dataParaCSV.push({ Seccion: 'COSTOS DE VENTA' });
            reporte.costos.forEach(item => { dataParaCSV.push({ Seccion: '', Codigo: item.codigo, Cuenta: item.nombre, Saldo: formatNumber(item.saldo), Porcentaje: formatNumber(item.porcentaje) + '%' }); });
            dataParaCSV.push({ Cuenta: 'TOTAL COSTOS', Saldo: formatNumber(totales.total_costos) });
            dataParaCSV.push({});
        }

        dataParaCSV.push({ Cuenta: 'UTILIDAD BRUTA', Saldo: formatNumber(totales.utilidad_bruta), Porcentaje: formatNumber(totales.porcentaje_utilidad_bruta) + '%' });
        dataParaCSV.push({});

        if (reporte.gastos && reporte.gastos.length > 0) {
            dataParaCSV.push({ Seccion: 'GASTOS OPERACIONALES' });
            reporte.gastos.forEach(item => { dataParaCSV.push({ Seccion: '', Codigo: item.codigo, Cuenta: item.nombre, Saldo: formatNumber(item.saldo), Porcentaje: formatNumber(item.porcentaje) + '%' }); });
            dataParaCSV.push({ Cuenta: 'TOTAL GASTOS', Saldo: formatNumber(totales.total_gastos) });
            dataParaCSV.push({});
        }

        dataParaCSV.push({ Cuenta: 'UTILIDAD NETA DEL EJERCICIO', Saldo: formatNumber(totales.utilidad_neta), Porcentaje: formatNumber(totales.porcentaje_utilidad_neta) + '%' });

        const csv = window.Papa.unparse(dataParaCSV);
        const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `estado-resultados-premium-${fechaInicio}-al-${fechaFin}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const handleSendEmail = async () => {
        if (!reporte || !emailAddress) return;
        toast.info(`📤 Enviando reporte a ${emailAddress}...`);
        try {
            await apiService.post('/reports/dispatch-email', {
                report_type: 'estado_resultados',
                email_to: emailAddress,
                filtros: {
                    fecha_inicio: fechaInicio,
                    fecha_fin: fechaFin
                }
            });
            toast.success(`✅ Correo enviado a ${emailAddress}`);
        } catch (err) {
            console.error("Error sending email:", err);
            toast.error("❌ Falló el envío del correo.");
        }
    };

    useEffect(() => {
        if (autoPdfTrigger && reporte && !isLoading) {
            handleExportPDF();
            if (wppNumber) {
                const message = `Hola, adjunto el Estado de Resultados Premium de ${user.nombre_empresa} del ${fechaInicio} al ${fechaFin}.`;
                const wppUrl = `https://wa.me/${wppNumber}?text=${encodeURIComponent(message)}`;
                setTimeout(() => window.open(wppUrl, '_blank'), 1500);
            }
            if (emailAddress) handleSendEmail();
            setAutoPdfTrigger(false);
            setWppNumber(null);
            setEmailAddress(null);
        }
    }, [reporte, autoPdfTrigger, isLoading, wppNumber, emailAddress]);

    const handleExportPDF = async () => {
        if (!reporte) return;
        setIsLoading(true);
        setError(null);
        try {
            const paramsForSignedUrl = { fecha_inicio: fechaInicio, fecha_fin: fechaFin };
            const signedUrlRes = await apiService.get('/reports/income-statement/get-signed-url', { params: paramsForSignedUrl });
            const signedToken = signedUrlRes.data.signed_url_token;
            const finalPdfUrl = `${process.env.NEXT_PUBLIC_API_URL}/api/reports/income-statement/imprimir?signed_token=${signedToken}`;
            window.open(finalPdfUrl, '_blank');
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al obtener la URL firmada para el PDF.');
        } finally {
            setIsLoading(false);
        }
    };

    const formatCurrency = (val) => {
        return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(val);
    };

    if (!isPageReady) {
        return (
            <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center">
                <div className="relative">
                    <div className="w-20 h-20 border-4 border-indigo-100 border-t-indigo-600 rounded-full animate-spin"></div>
                    <LucideTrendingUp className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-indigo-600 w-8 h-8" />
                </div>
                <p className="text-slate-600 font-bold mt-6 tracking-tight animate-pulse">Iniciando motor financiero...</p>
            </div>
        );
    }

    const AccountRow = ({ codigo, nombre, saldo, porcentaje, isNegative = false, isBold = false }) => (
        <div className={`flex justify-between items-center py-2.5 border-b border-slate-50 hover:bg-slate-50/50 transition-colors px-3 rounded-lg ${isBold ? 'bg-slate-50/30' : ''}`}>
            <div className="flex flex-col md:flex-row md:items-center gap-2 md:gap-4 flex-1 mr-4">
                <span className="font-mono text-[10px] font-black px-2 py-0.5 rounded bg-slate-100 text-slate-500 min-w-[50px] text-center border border-slate-200">{codigo}</span>
                <span className={`text-sm ${isBold ? 'font-black text-slate-800' : 'font-medium text-slate-600'}`}>{nombre}</span>
            </div>

            <div className="flex items-center gap-6 md:gap-12 min-w-[120px] md:min-w-[200px] justify-end">
                <div className="flex items-center gap-1.5 min-w-[60px] justify-end">
                    <span className={`text-[11px] font-black ${isNegative ? 'text-rose-500' : 'text-slate-400'}`}>
                        {porcentaje?.toFixed(1)}
                    </span>
                    <FaPercent className="text-[8px] text-slate-300" />
                </div>
                <span className={`font-mono text-sm tracking-tighter w-24 md:w-32 text-right ${isBold ? 'font-black text-slate-900' : isNegative ? 'text-rose-600 font-bold' : 'text-slate-700 font-bold'}`}>
                    {isNegative ? `(${formatCurrency(Math.abs(saldo))})` : formatCurrency(saldo)}
                </span>
            </div>
        </div>
    );

    return (
        <>
            <div className="min-h-screen bg-slate-50/50 p-4 md:p-8 font-sans pb-32">
                <div className="max-w-6xl mx-auto">

                    {/* BARRA SUPERIOR ELEGANTE */}
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-10 gap-6">
                        <div className="flex items-center gap-5">
                            <div className="p-4 bg-white rounded-2xl shadow-sm border border-slate-100 text-indigo-600 ring-4 ring-indigo-50">
                                <LucideBarChart3 size={32} />
                            </div>
                            <div>
                                <div className="flex items-center gap-3">
                                    <h1 className="text-3xl font-black text-slate-850 tracking-tighter">Estado de Resultados Analítico</h1>
                                    <span className="bg-indigo-600 text-white text-[10px] font-black px-2 py-0.5 rounded-full tracking-widest uppercase">Premium</span>
                                </div>
                                <p className="text-slate-500 text-sm font-medium mt-1">Análisis detallado de rentabilidad y eficiencia de <span className="text-indigo-600 font-bold">{user.nombre_empresa}</span></p>
                            </div>
                        </div>

                        <div className="flex gap-2 w-full md:w-auto">
                            <button onClick={() => router.push('/contabilidad/reportes/estado-resultados-clasificado')} className="flex-1 md:flex-none px-4 py-2 bg-indigo-50 text-indigo-600 rounded-xl hover:bg-indigo-100 font-bold text-xs transition-all shadow-sm flex items-center justify-center gap-2">
                                Ver Clasificado →
                            </button>
                            <button onClick={() => window.open('/manual/capitulo_29_reportes_avanzados.html', '_blank')} className="flex-1 md:flex-none px-4 py-2 bg-white border border-slate-200 text-slate-600 rounded-xl hover:bg-slate-50 font-bold text-xs transition-all shadow-sm flex items-center justify-center gap-2">
                                <FaBook /> Manual
                            </button>
                        </div>
                    </div>

                    {/* PANEL DE CONTROL (FILTROS) */}
                    <div className="bg-white rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-100 p-8 mb-10 animate-fadeIn overflow-hidden relative group">
                        <div className="absolute top-0 right-0 p-8 opacity-5 pointer-events-none transform translate-x-1/4 -translate-y-1/4 group-hover:scale-110 transition-transform duration-700">
                            <LucideDollarSign size={200} />
                        </div>

                        <div className="relative z-10">
                            <h5 className="text-xs font-black text-indigo-600 mb-6 uppercase tracking-[0.2em]">Configuración del Análisis</h5>
                            <div className="grid grid-cols-1 md:grid-cols-4 gap-8 items-end">
                                <div className="md:col-span-1">
                                    <label htmlFor="fechaInicio" className={labelClass}>Periodo Desde</label>
                                    <div className="relative">
                                        <input type="date" id="fechaInicio" value={fechaInicio} onChange={(e) => setFechaInicio(e.target.value)} className={inputClass} />
                                        <FaCalendarAlt className="absolute left-3.5 top-3.5 text-indigo-400 pointer-events-none" />
                                    </div>
                                </div>
                                <div className="md:col-span-1">
                                    <label htmlFor="fechaFin" className={labelClass}>Periodo Hasta</label>
                                    <div className="relative">
                                        <input type="date" id="fechaFin" value={fechaFin} onChange={(e) => setFechaFin(e.target.value)} className={inputClass} />
                                        <FaCalendarAlt className="absolute left-3.5 top-3.5 text-indigo-400 pointer-events-none" />
                                    </div>
                                </div>
                                <div className="md:col-span-2 flex gap-4">
                                    <button
                                        id="btn-generar-er"
                                        onClick={handleGenerateReport}
                                        disabled={isLoading}
                                        className={`flex-1 h-[46px] rounded-xl shadow-lg font-black text-sm text-white transition-all transform active:scale-95 flex items-center justify-center gap-3
                                            ${isLoading ? 'bg-slate-400 cursor-not-allowed' : 'bg-gradient-to-r from-indigo-600 to-indigo-700 hover:shadow-indigo-200 hover:tracking-wider'}`}
                                    >
                                        {isLoading ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <><FaSearch /> Generar Reporte</>}
                                    </button>
                                </div>
                            </div>
                        </div>
                        {error && (
                            <div className="mt-8 p-4 bg-rose-50 border border-rose-100 text-rose-700 rounded-2xl flex items-center gap-3 animate-headShake">
                                <div className="bg-rose-500 p-2 rounded-lg text-white shadow-sm"><FaExclamationTriangle /></div>
                                <p className="font-bold text-sm tracking-tight">{error}</p>
                            </div>
                        )}
                    </div>

                    {/* VISTA DE RESULTADOS */}
                    {reporte ? (
                        <div className="space-y-10">

                            {/* KPI CARDS GRID */}
                            {/* El usuario solicitó quitar los KPIs horizontales y dejar solo el análisis vertical */}

                            {/* DASHBOARD CENTRAL */}
                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                                {/* CASCADA VISUAL (Waterfall) */}
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
                                        <p className="text-[10px] font-black text-indigo-600 uppercase tracking-widest mb-1">Rendimiento Actual</p>
                                        <p className="text-xs text-slate-600 leading-relaxed font-medium">
                                            Su <span className="text-indigo-600 font-black tracking-tight">utilidad neta</span> actual es del <span className="font-black text-indigo-700">{reporte.totales.porcentaje_utilidad_neta?.toFixed(2)}%</span>. Por cada peso vendido, la empresa retiene {formatCurrency(reporte.totales.total_ingresos > 0 ? (reporte.totales.utilidad_neta / reporte.totales.total_ingresos) : 0)} centavos tras cubrir todos los costos y gastos.
                                        </p>
                                    </div>
                                </div>

                                {/* TABLA ANALÍTICA PRINCIPAL */}
                                <div className="lg:col-span-2 bg-white rounded-3xl border border-slate-100 shadow-sm overflow-hidden flex flex-col">
                                    <div className="p-6 bg-slate-50/50 border-b border-slate-100 flex justify-between items-center">
                                        <div className="flex items-center gap-4">
                                            <h4 className="text-base font-black text-slate-800 tracking-tight uppercase">Cuentas del Periodo</h4>
                                            <div className="flex gap-2">
                                                <button onClick={handleExportCSV} className="p-2 bg-white border border-slate-200 text-emerald-600 rounded-lg hover:shadow-sm transition-all shadow-indigo-100"><FaFileCsv /></button>
                                                <button onClick={handleExportPDF} className="p-2 bg-white border border-slate-200 text-rose-600 rounded-lg hover:shadow-sm transition-all"><FaFilePdf /></button>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex-1 overflow-auto p-2">
                                        <div className="min-w-full">
                                            {/* HEADER TABLA */}
                                            <div className="flex justify-between items-center px-4 py-3 bg-slate-50 rounded-xl mb-4 border border-slate-100">
                                                <span className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Detalle de Operación</span>
                                                <div className="flex items-center gap-12 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] md:min-w-[200px] justify-end">
                                                    <span>% Ventas</span>
                                                    <span>Valor</span>
                                                </div>
                                            </div>

                                            {/* CUERPO - SECCIONADO */}
                                            <div className="space-y-8 px-2 max-h-[600px] overflow-auto custom-scrollbar">
                                                {/* INGRESOS */}
                                                <div>
                                                    <div className="flex items-center gap-2 mb-3 text-emerald-600 opacity-80">
                                                        <FaArrowUp size={10} />
                                                        <span className="text-[10px] font-black uppercase tracking-widest">Flujos de Entrada</span>
                                                    </div>
                                                    <div className="space-y-0.5">
                                                        {reporte.ingresos.map(item => <AccountRow key={item.codigo} {...item} />)}
                                                        <AccountRow codigo="4" nombre="TOTAL INGRESOS OPERACIONALES" saldo={reporte.totales.total_ingresos} porcentaje={100} isBold={true} />
                                                    </div>
                                                </div>

                                                {/* COSTOS */}
                                                {reporte.costos?.length > 0 && (
                                                    <div>
                                                        <div className="flex items-center gap-2 mb-3 text-rose-500 opacity-80">
                                                            <FaArrowDown size={10} />
                                                            <span className="text-[10px] font-black uppercase tracking-widest">Consumos Directos</span>
                                                        </div>
                                                        <div className="space-y-0.5">
                                                            {reporte.costos.map(item => <AccountRow key={item.codigo} {...item} isNegative={true} />)}
                                                            <AccountRow codigo="6/7" nombre="TOTAL COSTOS DE VENTA" saldo={reporte.totales.total_costos} porcentaje={reporte.totales.total_ingresos > 0 ? (Math.abs(reporte.totales.total_costos) / reporte.totales.total_ingresos * 100) : 0} isBold={true} isNegative={true} />
                                                        </div>
                                                    </div>
                                                )}

                                                <div className="bg-emerald-50/50 p-4 rounded-2xl border border-emerald-100 flex justify-between items-center mx-2 group">
                                                    <span className="font-black text-emerald-800 text-xs tracking-widest uppercase group-hover:tracking-[0.2em] transition-all">UTILIDAD BRUTA</span>
                                                    <div className="text-right">
                                                        <p className="text-xs text-emerald-600 font-bold mb-0.5">{reporte.totales.porcentaje_utilidad_bruta?.toFixed(2)}%</p>
                                                        <p className="font-black text-emerald-900 text-lg tracking-tight">{formatCurrency(reporte.totales.utilidad_bruta)}</p>
                                                    </div>
                                                </div>

                                                {/* GASTOS */}
                                                {reporte.gastos?.length > 0 && (
                                                    <div>
                                                        <div className="flex items-center gap-2 mb-3 text-orange-500 opacity-80">
                                                            <FaCalculator size={10} />
                                                            <span className="text-[10px] font-black uppercase tracking-widest">Gastos de Operación</span>
                                                        </div>
                                                        <div className="space-y-0.5">
                                                            {reporte.gastos.map(item => <AccountRow key={item.codigo} {...item} isNegative={true} />)}
                                                            <AccountRow codigo="5" nombre="TOTAL GASTOS OPERACIONALES" saldo={reporte.totales.total_gastos} porcentaje={reporte.totales.total_ingresos > 0 ? (Math.abs(reporte.totales.total_gastos) / reporte.totales.total_ingresos * 100) : 0} isBold={true} isNegative={true} />
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>

                                    {/* FOOTER TOTAL - UTILIDAD NETA */}
                                    <div className={`p-8 ${reporte.totales.utilidad_neta >= 0 ? 'bg-slate-900 text-white' : 'bg-rose-900 text-white'} border-t border-slate-100 flex justify-between items-center`}>
                                        <div className="flex-1">
                                            <div className="flex items-center gap-3 mb-1">
                                                <h3 className="text-2xl font-black uppercase tracking-tighter">Utilidad Neta</h3>
                                                <div className={`px-2 py-0.5 rounded-full text-[10px] font-black tracking-widest ${reporte.totales.utilidad_neta >= 0 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-300'}`}>
                                                    MARGEN: {reporte.totales.porcentaje_utilidad_neta?.toFixed(2)}%
                                                </div>
                                            </div>
                                            <p className="text-xs opacity-50 font-medium">Resultado final tras deducir costos de venta y gastos administrativos.</p>
                                        </div>
                                        <span className="text-4xl font-black tracking-tighter">
                                            {formatCurrency(reporte.totales.utilidad_neta)}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="bg-white rounded-3xl p-20 border border-slate-100 shadow-sm flex flex-col items-center justify-center text-center animate-fadeIn">
                            <div className="w-24 h-24 bg-indigo-50 text-indigo-200 rounded-full flex items-center justify-center mb-6">
                                <LucideBarChart3 size={48} />
                            </div>
                            <h4 className="text-xl font-bold text-slate-800 mb-2 tracking-tight">Análisis Desconectado</h4>
                            <p className="text-slate-500 max-w-sm mx-auto text-sm leading-relaxed">Defina el periodo de análisis arriba y haga clic en **Generar Reporte** para iniciar el motor de inteligencia financiera.</p>
                        </div>
                    )}
                </div>
            </div>

            <Script src="https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js" />

            <style jsx>{`
                .custom-scrollbar::-webkit-scrollbar {
                    width: 4px;
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: transparent;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: #e2e8f0;
                    border-radius: 10px;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: #cbd5e1;
                }
                
                @keyframes slideUp {
                    from { transform: translateY(20px); opacity: 0; }
                    to { transform: translateY(0); opacity: 1; }
                }
                .animate-slideUp {
                    animation: slideUp 0.6s ease-out forwards;
                }
            `}</style>
        </>
    );
}