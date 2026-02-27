'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
    FaBalanceScale,
    FaCalendarAlt,
    FaSearch,
    FaFilePdf,
    FaBuilding,
    FaMoneyBillWave,
    FaLandmark,
    FaChartPie,
    FaExclamationTriangle,
    FaBook,
    FaChartBar,
    FaTable
} from 'react-icons/fa';

import { toast } from 'react-toastify';
import { useAuth } from '../../../context/AuthContext';
import { apiService } from '../../../../lib/apiService';
import { useAIAutomation } from '../../../hooks/useAIAutomation';
import dynamic from 'next/dynamic';

// Deshabilitamos el pre-renderizado del lado del servidor (SSR) para los gráficos
// ya que Recharts o librerías DOM lanzarán "Node is not defined" en Vercel Build.
const BalanceGraphics = dynamic(() => import('./BalanceGraphics'), { ssr: false });

// Estilos Reusables (Manual v2.0)
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none pl-10";

export default function BalanceGeneralPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
                <FaBalanceScale className="text-indigo-300 text-6xl mb-4 animate-pulse" />
                <p className="text-indigo-600 font-semibold text-lg animate-pulse">Iniciando Reporte...</p>
            </div>
        }>
            <BalanceGeneralContent />
        </Suspense>
    );
}

function BalanceGeneralContent() {
    const { user, authLoading } = useAuth();
    const router = useRouter();
    const searchParams = useSearchParams();

    const [reporte, setReporte] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [filtros, setFiltros] = useState({
        fecha_corte: new Date().toISOString().split('T')[0],
        nivel: 'clasificado' // Siempre consolidado (NIIF)
    });
    const [activeTab, setActiveTab] = useState('classic'); // 'classic', 'graphics'
    const [isPageReady, setPageReady] = useState(false);

    // Automation State
    const [autoPdfTrigger, setAutoPdfTrigger] = useState(false);
    const [wppNumber, setWppNumber] = useState(null);
    const [emailAddress, setEmailAddress] = useState(null);
    const [empresaInfo, setEmpresaInfo] = useState(null);
    const lastProcessedParams = React.useRef('');

    // Efecto de Autenticación y Carga de Empresa
    useEffect(() => {
        if (!authLoading) {
            if (user && user.empresaId) {
                // Fetch de información completa de la empresa
                apiService.get(`/empresas/${user.empresaId}`)
                    .then(response => {
                        setEmpresaInfo(response.data);
                        setPageReady(true);
                    })
                    .catch(err => {
                        console.error("Error al cargar datos de empresa:", err);
                        // Fallback para permitir ver la página aunque falle el nombre
                        setPageReady(true);
                    });
            } else {
                router.push('/login');
            }
        }
    }, [user, authLoading, router]);

    // Efecto para triggers especiales (WhatsApp / Email / PDF)
    useEffect(() => {
        if (!searchParams) return;
        const pAutoPdf = searchParams.get('auto_pdf');
        const pWpp = searchParams.get('wpp');
        const pEmail = searchParams.get('email');

        if (reporte && !isLoading) {
            if (pAutoPdf === 'true') handleExportPDF();

            if (pWpp) {
                const message = `Hola, adjunto el Balance General de ${user.nombre_empresa} con corte a ${filtros.fecha_corte}.`;
                const wppUrl = `https://wa.me/${pWpp}?text=${encodeURIComponent(message)}`;
                setTimeout(() => window.open(wppUrl, '_blank'), 1500);
            }

            if (pEmail) {
                handleSendEmail();
            }
        }
    }, [reporte, isLoading]);

    async function handleGenerateReport() {
        if (!filtros.fecha_corte) {
            setError("Por favor, seleccione una fecha de corte.");
            return;
        }
        setIsLoading(true);
        setError('');
        setReporte(null);
        try {
            const data = await apiService.get('/reports/balance-sheet', {
                params: { fecha_corte: filtros.fecha_corte, nivel: filtros.nivel }
            });
            setReporte(data.data);
        } catch (err) {
            setError(err.response?.data?.detail || "Error al generar el reporte.");
        } finally {
            setIsLoading(false);
        }
    }

    async function handleSendEmail() {
        if (!searchParams) return;
        const emailAddress = searchParams.get('email');
        if (!reporte || !emailAddress) return;
        toast.info(`📤 Enviando reporte a ${emailAddress}...`);
        try {
            await apiService.post('/reports/dispatch-email', {
                report_type: 'balance_general',
                email_to: emailAddress,
                filtros: { fecha_corte: filtros.fecha_corte }
            });
            toast.success(`✅ Correo enviado a ${emailAddress}`);
        } catch (err) {
            console.error("Error sending email:", err);
            toast.error("❌ Falló el envío del correo.");
        }
    }

    async function handleExportPDF() {
        if (!reporte) {
            setError("Primero debe generar un reporte para poder exportarlo.");
            return;
        }
        setIsLoading(true);
        setError('');
        try {
            const signedUrlResponse = await apiService.get('/reports/balance-sheet/get-signed-url', {
                params: { fecha_corte: filtros.fecha_corte, nivel: filtros.nivel }
            });

            const signedToken = signedUrlResponse.data.signed_url_token;
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const pdfDownloadUrl = `${baseUrl}/api/reports/balance-sheet/imprimir?signed_token=${signedToken}`;
            window.open(pdfDownloadUrl, '_blank');
        } catch (err) {
            setError(err.response?.data?.detail || "Error al generar el PDF del reporte.");
        } finally {
            setIsLoading(false);
        }
    }

    function formatCurrency(value) {
        const num = parseFloat(value);
        if (isNaN(num)) return '$ 0.00';
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }).format(num);
    }

    // --- AUTOMATIZACION UNIVERSAL (IA) ---
    // Se deja al FINAL de la lógica para evitar errores de inicialización (TDZ)
    useAIAutomation(isPageReady, filtros, setFiltros, handleGenerateReport);

    if (!isPageReady) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
                <FaBalanceScale className="text-indigo-300 text-6xl mb-4 animate-pulse" />
                <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando Balance General...</p>
            </div>
        );
    }

    // --- CÁLCULOS DINÁMICOS PARA EVITAR SECCIONES VACÍAS ---
    const activosCorrientes = (reporte?.clasificado_activo?.corriente || []).filter(item => item.codigo && item.codigo.length > 1);
    const activosNoCorrientes = (reporte?.clasificado_activo?.no_corriente || []).filter(item => item.codigo && item.codigo.length > 1);
    const pasivosCorrientes = (reporte?.clasificado_pasivo?.corriente || []).filter(item => item.codigo && item.codigo.length > 1);
    const pasivosNoCorrientes = (reporte?.clasificado_pasivo?.no_corriente || []).filter(item => item.codigo && item.codigo.length > 1);
    const patrimonioArr = (reporte?.patrimonio || []).filter(item => item.codigo && item.codigo.length > 1);

    const sumTotalActivoCorriente = activosCorrientes.reduce((acc, curr) => acc + curr.saldo, 0);
    const sumTotalActivoNoCorriente = activosNoCorrientes.reduce((acc, curr) => acc + curr.saldo, 0);
    const sumTotalPasivoCorriente = pasivosCorrientes.reduce((acc, curr) => acc + curr.saldo, 0);
    const sumTotalPasivoNoCorriente = pasivosNoCorrientes.reduce((acc, curr) => acc + curr.saldo, 0);
    const sumTotalPatrimonioBase = patrimonioArr.reduce((acc, curr) => acc + curr.saldo, 0);

    const utilidadCalc = reporte?.utilidad_ejercicio || 0;
    const totalActivosCalc = sumTotalActivoCorriente + sumTotalActivoNoCorriente;
    const totalPasivosCalc = sumTotalPasivoCorriente + sumTotalPasivoNoCorriente;
    const totalPatrimonioCalc = sumTotalPatrimonioBase + utilidadCalc;
    const totalPasivoPatrimonioCalc = totalPasivosCalc + totalPatrimonioCalc;
    const ecuacionCuadra = Math.abs(totalActivosCalc - totalPasivoPatrimonioCalc) < 1;
    // ----------------------------------------------------

    // Componente para una fila de cuenta
    const AccountRow = ({ codigo, nombre, saldo, colorClass = "text-gray-700" }) => (
        <div className="flex justify-between items-center py-2 border-b border-gray-50 hover:bg-gray-50 transition-colors px-2 rounded">
            <div className="flex flex-col md:flex-row md:items-center gap-1 md:gap-3">
                <span className={`font-mono text-xs font-bold px-2 py-0.5 rounded-md bg-gray-100 ${colorClass}`}>{codigo}</span>
                <span className="text-sm text-gray-700 font-medium">{nombre}</span>
            </div>
            <span className={`font-mono text-sm font-bold ${colorClass}`}>
                {formatCurrency(saldo)}
            </span>
        </div>
    );

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
            <div className="max-w-5xl mx-auto">

                {/* ENCABEZADO */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                    <div>
                        <div className="flex items-center gap-3 mt-3">
                            <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                                <FaBalanceScale className="text-2xl" />
                            </div>
                            <div>
                                <div className="flex items-center gap-4">
                                    <h1 className="text-3xl font-bold text-gray-800">Balance General</h1>
                                    <button
                                        onClick={() => window.open('/manual/capitulo_28_balance_general.html', '_blank')}
                                        className="text-indigo-600 hover:bg-indigo-50 px-2 py-1 rounded-md flex items-center gap-2 transition-colors"
                                        title="Ver Manual de Usuario"
                                    >
                                        <span className="text-lg">📖</span> <span className="font-bold text-sm hidden md:inline">Manual</span>
                                    </button>
                                </div>
                                <p className="text-gray-500 text-sm">Situación financiera: Activos, Pasivos y Patrimonio.</p>
                                {/* STATUS INDICATOR */}
                                {(wppNumber || autoPdfTrigger || emailAddress) && (
                                    <div className="mt-2 text-sm font-bold text-green-600 flex items-center gap-2 animate-bounce">
                                        <span>⚡ Procesando comando: Generando PDF {wppNumber ? 'para WhatsApp...' : emailAddress ? 'para Email...' : '...'}</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* CARD 1: FILTROS */}
                <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 animate-fadeIn mb-8">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-end">
                        <div className="md:col-span-1">
                            <label htmlFor="fechaCorte" className={labelClass}>Fecha de Corte</label>
                            <div className="relative">
                                <input
                                    type="date"
                                    id="fecha_corte"
                                    value={filtros.fecha_corte}
                                    onChange={(e) => setFiltros(prev => ({ ...prev, fecha_corte: e.target.value }))}
                                    className={inputClass}
                                />
                                <FaCalendarAlt className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                            </div>
                        </div>

                        <div className="md:col-span-1">
                            <label htmlFor="presentationMode" className={labelClass}>Formato de Presentación</label>
                            <div className="w-full px-4 py-2 border border-blue-100 bg-blue-50 text-blue-800 font-bold rounded-lg shadow-sm text-sm">
                                ESTÁNDAR NIIF (Corporativo)
                            </div>
                        </div>

                        <div className="md:col-span-2 flex flex-col md:flex-row justify-end gap-3">
                            <button
                                id="btn-generar-balance"
                                onClick={handleGenerateReport}
                                disabled={isLoading}
                                className={`
                                    px-6 py-2 rounded-lg shadow-md font-bold text-white transition-all transform hover:-translate-y-0.5 flex items-center justify-center gap-2 w-full md:w-auto
                                    ${isLoading ? 'bg-gray-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'}
                                `}
                            >
                                {isLoading ? <span className="loading loading-spinner loading-sm"></span> : <><FaSearch /> Generar Reporte</>}
                            </button>

                            <button
                                onClick={handleExportPDF}
                                disabled={!reporte || isLoading}
                                className={`
                                    px-6 py-2 rounded-lg shadow-md font-bold border transition-all transform hover:-translate-y-0.5 flex items-center justify-center gap-2 w-full md:w-auto
                                    ${!reporte || isLoading
                                        ? 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed'
                                        : 'bg-white text-red-600 border-red-100 hover:bg-red-50'}
                                `}
                            >
                                <FaFilePdf /> Exportar PDF
                            </button>
                        </div>
                    </div>

                    {error && (
                        <div className="mt-4 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded-r-lg flex items-center gap-3 animate-pulse">
                            <FaExclamationTriangle className="text-xl" />
                            <p className="font-bold">{error}</p>
                        </div>
                    )}
                </div>

                {reporte && (
                    <div className="mb-6 flex justify-center w-full print:hidden">
                        <div className="bg-white p-1 rounded-xl shadow-sm border border-gray-200 inline-flex transition-all">
                            <button
                                onClick={() => setActiveTab('classic')}
                                className={`
                                    px-6 py-2.5 text-sm font-bold flex items-center gap-2 rounded-lg transition-all
                                    ${activeTab === 'classic' ? 'bg-indigo-50 text-indigo-700 shadow-sm ring-1 ring-indigo-200' : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'}
                                `}
                            >
                                <FaTable className={activeTab === 'classic' ? 'text-indigo-600' : 'text-gray-400'} /> Vista Clásica
                            </button>
                            <button
                                onClick={() => setActiveTab('graphics')}
                                className={`
                                    px-6 py-2.5 text-sm font-bold flex items-center gap-2 rounded-lg transition-all
                                    ${activeTab === 'graphics' ? 'bg-indigo-50 text-indigo-700 shadow-sm ring-1 ring-indigo-200' : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'}
                                `}
                            >
                                <FaChartBar className={activeTab === 'graphics' ? 'text-indigo-600' : 'text-gray-400'} /> Dashboard Interactivo
                            </button>
                        </div>
                    </div>
                )}

                {/* AREA DE REPORTE O DASHBOARD */}
                {reporte && activeTab === 'graphics' ? (
                    <BalanceGraphics
                        reporte={reporte}
                        totalesCalculados={{ totalActivosCalc, totalPasivosCalc, totalPatrimonioCalc, totalPasivoPatrimonioCalc, ecuacionCuadra }}
                    />
                ) : reporte && activeTab === 'classic' ? (
                    <div className="bg-white rounded-none shadow-2xl border-t-8 border-indigo-900 animate-slideDown max-w-4xl mx-auto print:shadow-none print:border-none">

                        {/* CABECERA FORMAL CONTABLE */}
                        <div className="p-12 pb-6 text-center border-b border-gray-800 mx-12 mb-8">
                            <h2 className="text-3xl font-serif font-bold text-gray-900 tracking-wide uppercase mb-2">
                                {empresaInfo?.razon_social?.toUpperCase() || user?.nombre_empresa?.toUpperCase() || 'EMPRESA DEMO S.A.S.'}
                            </h2>
                            <p className="text-sm font-serif text-gray-600 mb-6">NIT: {empresaInfo?.nit || user?.nit || '800.000.000-1'}</p>

                            <h3 className="text-xl font-bold text-gray-800 uppercase tracking-widest mb-1 border-y-2 border-gray-800 py-1 inline-block px-8">
                                ESTADO DE SITUACIÓN FINANCIERA
                            </h3>

                            <p className="text-gray-600 font-serif italic mt-4">
                                Corte al {new Date(filtros.fecha_corte).toLocaleDateString('es-CO', { year: 'numeric', month: 'long', day: 'numeric' })}
                            </p>
                            <p className="text-xs text-gray-400 mt-1">(Cifras expresadas en Pesos Colombianos)</p>
                        </div>

                        <div className="p-6 space-y-8">

                            {/* ------------ VISTA CLASIFICADA (NIIF ESTANDAR) ------------ */}

                            {/* ACTIVOS */}
                            <section>
                                <div className="uppercase font-bold text-lg text-slate-800 border-b-2 border-slate-800 mb-4 pb-1 tracking-wider">ACTIVOS</div>

                                {/* Activo Corriente */}
                                {activosCorrientes.length > 0 && (
                                    <div className="mb-6 pl-2 md:pl-4">
                                        <h4 className="font-bold text-slate-700 mb-2 uppercase text-sm border-b border-slate-200 inline-block">ACTIVO CORRIENTE</h4>
                                        <div className="space-y-1 mt-2">
                                            {activosCorrientes.map((item, index) => (
                                                <div key={`act-curr-${index}`} className="flex justify-between items-end hover:bg-slate-50 transition-colors py-1.5 border-b border-dotted border-slate-200 pl-4">
                                                    <div className="flex gap-3 text-sm text-slate-600">
                                                        <span className="font-mono text-slate-500 text-xs w-10 text-right">{item.codigo}</span>
                                                        <span className="uppercase text-xs">{item.nombre}</span>
                                                    </div>
                                                    <span className="font-mono text-sm text-slate-700">{formatCurrency(item.saldo)}</span>
                                                </div>
                                            ))}
                                            <div className="flex justify-between items-center pt-2 mt-2 font-bold text-slate-800 tracking-wide">
                                                <span className="pl-16 text-xs uppercase">TOTAL ACTIVO CORRIENTE</span>
                                                <span className="font-mono border-t border-slate-800 w-36 text-right pt-1">{formatCurrency(sumTotalActivoCorriente)}</span>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Activo No Corriente */}
                                {activosNoCorrientes.length > 0 && (
                                    <div className="mb-6 pl-2 md:pl-4">
                                        <h4 className="font-bold text-slate-700 mb-2 uppercase text-sm border-b border-slate-200 inline-block">ACTIVO NO CORRIENTE</h4>
                                        <div className="space-y-1 mt-2">
                                            {activosNoCorrientes.map((item, index) => (
                                                <div key={`act-nocurr-${index}`} className="flex justify-between items-end hover:bg-slate-50 transition-colors py-1.5 border-b border-dotted border-slate-200 pl-4">
                                                    <div className="flex gap-3 text-sm text-slate-600">
                                                        <span className="font-mono text-slate-500 text-xs w-10 text-right">{item.codigo}</span>
                                                        <span className="uppercase text-xs">{item.nombre}</span>
                                                    </div>
                                                    <span className="font-mono text-sm text-slate-700">{formatCurrency(item.saldo)}</span>
                                                </div>
                                            ))}
                                            <div className="flex justify-between items-center pt-2 mt-2 font-bold text-slate-800 tracking-wide">
                                                <span className="pl-16 text-xs uppercase">TOTAL ACTIVO NO CORRIENTE</span>
                                                <span className="font-mono border-t border-slate-800 w-36 text-right pt-1">{formatCurrency(sumTotalActivoNoCorriente)}</span>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* GRAN TOTAL ACTIVOS */}
                                <div className="flex justify-end mt-6">
                                    <div className="flex justify-between items-center w-full bg-slate-100 p-3 border-y-2 border-slate-800 shadow-sm">
                                        <span className="font-black text-slate-900 uppercase tracking-widest pl-4 hover:pl-6 transition-all">TOTAL ACTIVOS</span>
                                        <span className="font-mono font-black text-xl text-slate-900">{formatCurrency(totalActivosCalc)}</span>
                                    </div>
                                </div>
                            </section>

                            {/* PASIVOS */}
                            <section className="mt-10">
                                <div className="uppercase font-bold text-lg text-slate-800 border-b-2 border-slate-800 mb-4 pb-1 tracking-wider">PASIVOS</div>

                                {/* Pasivo Corriente */}
                                {pasivosCorrientes.length > 0 && (
                                    <div className="mb-6 pl-2 md:pl-4">
                                        <h4 className="font-bold text-slate-700 mb-2 uppercase text-sm border-b border-slate-200 inline-block">PASIVO CORRIENTE</h4>
                                        <div className="space-y-1 mt-2">
                                            {pasivosCorrientes.map((item, index) => (
                                                <div key={`pas-curr-${index}`} className="flex justify-between items-end hover:bg-slate-50 transition-colors py-1.5 border-b border-dotted border-slate-200 pl-4">
                                                    <div className="flex gap-3 text-sm text-slate-600">
                                                        <span className="font-mono text-slate-500 text-xs w-10 text-right">{item.codigo}</span>
                                                        <span className="uppercase text-xs">{item.nombre}</span>
                                                    </div>
                                                    <span className="font-mono text-sm text-slate-700">{formatCurrency(item.saldo)}</span>
                                                </div>
                                            ))}
                                            <div className="flex justify-between items-center pt-2 mt-2 font-bold text-slate-800 tracking-wide">
                                                <span className="pl-16 text-xs uppercase">TOTAL PASIVO CORRIENTE</span>
                                                <span className="font-mono border-t border-slate-800 w-36 text-right pt-1">{formatCurrency(sumTotalPasivoCorriente)}</span>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Pasivo No Corriente */}
                                {pasivosNoCorrientes.length > 0 && (
                                    <div className="mb-6 pl-2 md:pl-4">
                                        <h4 className="font-bold text-slate-700 mb-2 uppercase text-sm border-b border-slate-200 inline-block">PASIVO NO CORRIENTE</h4>
                                        <div className="space-y-1 mt-2">
                                            {pasivosNoCorrientes.map((item, index) => (
                                                <div key={`pas-nocurr-${index}`} className="flex justify-between items-end hover:bg-slate-50 transition-colors py-1.5 border-b border-dotted border-slate-200 pl-4">
                                                    <div className="flex gap-3 text-sm text-slate-600">
                                                        <span className="font-mono text-slate-500 text-xs w-10 text-right">{item.codigo}</span>
                                                        <span className="uppercase text-xs">{item.nombre}</span>
                                                    </div>
                                                    <span className="font-mono text-sm text-slate-700">{formatCurrency(item.saldo)}</span>
                                                </div>
                                            ))}
                                            <div className="flex justify-between items-center pt-2 mt-2 font-bold text-slate-800 tracking-wide">
                                                <span className="pl-16 text-xs uppercase">TOTAL PASIVO NO CORRIENTE</span>
                                                <span className="font-mono border-t border-slate-800 w-36 text-right pt-1">{formatCurrency(sumTotalPasivoNoCorriente)}</span>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* GRAN TOTAL PASIVOS */}
                                <div className="flex justify-end mt-6">
                                    <div className="flex justify-between items-center w-full bg-slate-100 p-3 border-y-2 border-slate-800 shadow-sm">
                                        <span className="font-black text-slate-900 uppercase tracking-widest pl-4 hover:pl-6 transition-all">TOTAL PASIVOS</span>
                                        <span className="font-mono font-black text-xl text-slate-900">{formatCurrency(totalPasivosCalc)}</span>
                                    </div>
                                </div>
                            </section>

                            {/* SECCIÓN: PATRIMONIO (Común) */}
                            <section className="mt-10">
                                <div className="uppercase font-bold text-lg text-slate-800 border-b-2 border-slate-800 mb-4 pb-1 tracking-wider">PATRIMONIO</div>
                                <div className="space-y-1 pl-6">
                                    {patrimonioArr.map((item, index) => (
                                        <div key={`pat-${index}`} className="flex justify-between items-end hover:bg-slate-50 transition-colors py-1.5 border-b border-dotted border-slate-200">
                                            <div className="flex gap-3 text-sm text-slate-600">
                                                <span className="font-mono text-slate-500 text-xs w-10 text-right">{item.codigo}</span>
                                                <span className="uppercase text-xs">{item.nombre}</span>
                                            </div>
                                            <span className="font-mono text-sm text-slate-700">{formatCurrency(item.saldo)}</span>
                                        </div>
                                    ))}
                                    {/* Utilidad del Ejercicio */}
                                    <div className="flex justify-between items-end bg-blue-50/50 py-2 border-b border-blue-100">
                                        <div className="flex gap-3 text-sm font-bold text-indigo-900">
                                            <span className="font-mono text-xs w-10 text-right">3605</span>
                                            <span className="uppercase text-xs">{reporte.nombre_utilidad || 'UTILIDAD (PÉRDIDA) DEL EJERCICIO'}</span>
                                        </div>
                                        <span className={`font-mono text-sm font-bold pr-1 ${reporte.utilidad_ejercicio >= 0 ? 'text-indigo-900' : 'text-red-600'}`}>
                                            {formatCurrency(reporte.utilidad_ejercicio)}
                                        </span>
                                    </div>
                                </div>

                                <div className="flex justify-end mt-6">
                                    <div className="flex justify-between items-center w-full bg-slate-100 p-3 border-y-2 border-slate-800 shadow-sm">
                                        <span className="font-black text-slate-900 uppercase tracking-widest pl-4 hover:pl-6 transition-all">TOTAL PATRIMONIO</span>
                                        <span className="font-mono font-black text-xl text-slate-900">{formatCurrency(totalPatrimonioCalc)}</span>
                                    </div>
                                </div>
                            </section>

                            {/* ECUACIÓN CONTABLE FIN DE REPORTE */}
                            <div className="mt-16 pt-4 border-t-4 border-slate-900 bg-slate-50 rounded-b-lg">
                                <div className="flex justify-between items-center text-xl p-4">
                                    <span className="font-black text-slate-900 uppercase tracking-widest pl-2">TOTAL PASIVO + PATRIMONIO</span>
                                    <span className={`font-mono font-black border-b-4 border-double border-slate-900 pb-1 text-2xl ${ecuacionCuadra ? 'text-slate-900' : 'text-red-600'}`}>
                                        {formatCurrency(totalPasivoPatrimonioCalc)}
                                    </span>
                                </div>
                                {!ecuacionCuadra && (
                                    <div className="px-4 pb-4">
                                        <div className="bg-red-50 text-red-600 p-3 rounded border border-red-200 text-sm flex justify-between">
                                            <span><strong>Atención:</strong> Existe un descuadre en la ecuación patrimonial.</span>
                                            <span className="font-bold font-mono">Diferencia: {formatCurrency(Math.abs(totalActivosCalc - totalPasivoPatrimonioCalc))}</span>
                                        </div>
                                    </div>
                                )}
                                <p className="text-center text-xs text-slate-400 mt-8 mb-8 pb-4 tracking-widest uppercase">*** Fin del Informe Financiero ***</p>

                                {/* Firmas */}
                                <div className="flex justify-around mt-16 text-center">
                                    <div className="w-1/3 border-t border-gray-400 pt-2">
                                        <p className="font-bold text-sm">REPRESENTANTE LEGAL</p>
                                        <p className="text-xs text-gray-500 mt-1">C.C.</p>
                                    </div>
                                    <div className="w-1/3 border-t border-gray-400 pt-2">
                                        <p className="font-bold text-sm">CONTADOR PÚBLICO</p>
                                        <p className="text-xs text-gray-500 mt-1">T.P.</p>
                                    </div>
                                </div>
                            </div>

                        </div>
                    </div>
                ) : null}
            </div>
        </div>
    );
}