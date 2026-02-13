'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
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
    FaBook
} from 'react-icons/fa';

import { toast } from 'react-toastify';
import { useAuth } from '../../../context/AuthContext';
import { apiService } from '../../../../lib/apiService';

// Estilos Reusables (Manual v2.0)
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none pl-10";

export default function BalanceGeneralPage() {
    const { user, authLoading } = useAuth();
    const router = useRouter();

    const [reporte, setReporte] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [fechaCorte, setFechaCorte] = useState(new Date().toISOString().split('T')[0]);
    const [presentationMode, setPresentationMode] = useState('auxiliar'); // 'auxiliar', 'mayor', 'clasificado'
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

    // --- AUTO-CONFIGURACION (IA) ---
    const [autoExecute, setAutoExecute] = useState(false);

    useEffect(() => {
        if (isPageReady) {
            const urlParams = new URLSearchParams(window.location.search);
            const aiFechaCorte = urlParams.get('fecha_corte');
            const aiPresentation = urlParams.get('nivel') || 'auxiliar'; // Support 'nivel' param if AI sends it

            const pAutoPdf = urlParams.get('auto_pdf');
            const pWpp = urlParams.get('wpp');
            const pEmail = urlParams.get('email');

            if (aiFechaCorte) {
                const currentSignature = `${aiFechaCorte}-${pAutoPdf}-${pWpp}-${pEmail}`;
                if (lastProcessedParams.current === currentSignature) return;
                lastProcessedParams.current = currentSignature;

                setFechaCorte(aiFechaCorte);
                setPresentationMode(aiPresentation); // Set presentation mode if provided

                if (pAutoPdf === 'true') setAutoPdfTrigger(true);
                if (pWpp) setWppNumber(pWpp);
                if (pEmail) setEmailAddress(pEmail);

                // Activar bandera de ejecución automática
                setAutoExecute(true);
            }
        }
    }, [isPageReady]);

    // EFECTO: Ejecutar reporte automáticamente cuando la bandera cambie
    useEffect(() => {
        if (autoExecute && fechaCorte) {
            handleGenerateReport();
            setAutoExecute(false); // Resetear bandera
            // Limpiar URL para no re-ejecutar al recargar
            window.history.replaceState(null, '', window.location.pathname);
        }
    }, [autoExecute, fechaCorte]);

    const handleGenerateReport = async () => {
        if (!fechaCorte) {
            setError("Por favor, seleccione una fecha de corte.");
            return;
        }
        setIsLoading(true);
        setError('');
        setReporte(null);
        try {
            const data = await apiService.get('/reports/balance-sheet', {
                params: { fecha_corte: fechaCorte, nivel: presentationMode }
            });
            setReporte(data.data);
        } catch (err) {
            setError(err.response?.data?.detail || "Error al generar el reporte.");
        } finally {
            setIsLoading(false);
        }
    };

    // HANDLE: Enviar por Correo
    const handleSendEmail = async () => {
        if (!reporte || !emailAddress) return;
        toast.info(`📤 Enviando reporte a ${emailAddress}...`);
        try {
            await apiService.post('/reports/dispatch-email', {
                report_type: 'balance_general',
                email_to: emailAddress,
                filtros: { fecha_corte: fechaCorte }
            });
            toast.success(`✅ Correo enviado a ${emailAddress}`);
        } catch (err) {
            console.error("Error sending email:", err);
            toast.error("❌ Falló el envío del correo.");
        }
    };

    // EFECTO: Automatización
    useEffect(() => {
        if (autoPdfTrigger && reporte && !isLoading) {
            handleExportPDF();

            if (wppNumber) {
                const message = `Hola, adjunto el Balance General de ${user.nombre_empresa} con corte a ${fechaCorte}.`;
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
        if (!reporte) {
            setError("Primero debe generar un reporte para poder exportarlo.");
            return;
        }
        setIsLoading(true);
        setError('');
        try {
            const signedUrlResponse = await apiService.get('/reports/balance-sheet/get-signed-url', {
                params: { fecha_corte: fechaCorte, nivel: presentationMode }
            });

            const signedToken = signedUrlResponse.data.signed_url_token;
            // Usamos la URL absoluta definida en el entorno o construida dinámicamente
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const pdfDownloadUrl = `${baseUrl}/api/reports/balance-sheet/imprimir?signed_token=${signedToken}`;

            // Técnica de descarga directa (Link Fantasma) para evitar bloqueo de popups
            // window.location.href = pdfDownloadUrl; // ANTES: Misma ventana
            window.open(pdfDownloadUrl, '_blank'); // AHORA: Nueva pestaña

        } catch (err) {
            setError(err.response?.data?.detail || "Error al generar el PDF del reporte.");
        } finally {
            setIsLoading(false);
        }
    };

    const formatCurrency = (value) => {
        const num = parseFloat(value);
        if (isNaN(num)) return '$ 0.00';
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }).format(num);
    };

    if (!isPageReady) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
                <FaBalanceScale className="text-indigo-300 text-6xl mb-4 animate-pulse" />
                <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando Balance General...</p>
            </div>
        );
    }

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
                                    id="fechaCorte"
                                    value={fechaCorte}
                                    onChange={(e) => setFechaCorte(e.target.value)}
                                    className={inputClass}
                                />
                                <FaCalendarAlt className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                            </div>
                        </div>

                        <div className="md:col-span-1">
                            <label htmlFor="presentationMode" className={labelClass}>Presentación</label>
                            <select
                                id="presentationMode"
                                value={presentationMode}
                                onChange={(e) => setPresentationMode(e.target.value)}
                                className={inputClass}
                            >
                                <option value="auxiliar">Detallado (Auxiliar)</option>
                                <option value="mayor">Resumen (Cuenta Mayor)</option>
                                <option value="clasificado">Clasificado (Corriente / No Corriente)</option>
                            </select>
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

                {/* CARD 2: REPORTE (RESULTADOS) - ESTILO PROFESIONAL "AUDITADO" */}
                {reporte && (
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
                                Corte al {new Date(fechaCorte).toLocaleDateString('es-CO', { year: 'numeric', month: 'long', day: 'numeric' })}
                            </p>
                            <p className="text-xs text-gray-400 mt-1">(Cifras expresadas en Pesos Colombianos)</p>
                        </div>

                        <div className="p-6 space-y-8">

                            {/* LOGICA DE RENDERIZADO SEGÚN NIVEL */}
                            {reporte.nivel === 'clasificado' ? (
                                <>
                                    {/* ------------ VISTA CLASIFICADA ------------ */}

                                    {/* ACTIVOS */}
                                    <section>
                                        <div className="uppercase font-bold text-lg text-gray-900 border-b-2 border-gray-900 mb-4 pb-1">Activos</div>

                                        {/* Activo Corriente */}
                                        <div className="mb-6 pl-4">
                                            <h4 className="font-bold text-gray-800 mb-2 uppercase text-sm border-b border-gray-300 inline-block">Activo Corriente</h4>
                                            <div className="space-y-1 mt-2">
                                                {reporte.clasificado_activo?.corriente.map((item, index) => (
                                                    <div key={`act-curr-${index}`} className="flex justify-between items-end hover:bg-gray-50 transition-colors py-1 border-b border-dotted border-gray-200">
                                                        <div className="flex gap-2 text-sm text-gray-700">
                                                            <span className="font-mono text-gray-500 text-xs w-12 text-right">{item.codigo}</span>
                                                            <span>{item.nombre}</span>
                                                        </div>
                                                        <span className="font-mono text-sm text-gray-800">{formatCurrency(item.saldo)}</span>
                                                    </div>
                                                ))}
                                                <div className="flex justify-between items-center pt-2 mt-2 font-bold text-gray-900">
                                                    <span className="pl-14 text-sm uppercase">Total Activo Corriente</span>
                                                    <span className="font-mono border-t border-gray-800 w-32 text-right">{formatCurrency(reporte.clasificado_activo?.total_corriente)}</span>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Activo No Corriente */}
                                        <div className="mb-6 pl-4">
                                            <h4 className="font-bold text-gray-800 mb-2 uppercase text-sm border-b border-gray-300 inline-block">Activo No Corriente</h4>
                                            <div className="space-y-1 mt-2">
                                                {reporte.clasificado_activo?.no_corriente.map((item, index) => (
                                                    <div key={`act-nocurr-${index}`} className="flex justify-between items-end hover:bg-gray-50 transition-colors py-1 border-b border-dotted border-gray-200">
                                                        <div className="flex gap-2 text-sm text-gray-700">
                                                            <span className="font-mono text-gray-500 text-xs w-12 text-right">{item.codigo}</span>
                                                            <span>{item.nombre}</span>
                                                        </div>
                                                        <span className="font-mono text-sm text-gray-800">{formatCurrency(item.saldo)}</span>
                                                    </div>
                                                ))}
                                                <div className="flex justify-between items-center pt-2 mt-2 font-bold text-gray-900">
                                                    <span className="pl-14 text-sm uppercase">Total Activo No Corriente</span>
                                                    <span className="font-mono border-t border-gray-800 w-32 text-right">{formatCurrency(reporte.clasificado_activo?.total_no_corriente)}</span>
                                                </div>
                                            </div>
                                        </div>

                                        {/* GRAN TOTAL ACTIVOS */}
                                        <div className="flex justify-end mt-4">
                                            <div className="flex justify-between items-center w-full md:w-1/2 bg-gray-100 p-2 border border-gray-300">
                                                <span className="font-bold text-gray-900 uppercase">Total Activos</span>
                                                <span className="font-mono font-bold text-lg text-gray-900">{formatCurrency(reporte.total_activos)}</span>
                                            </div>
                                        </div>
                                    </section>

                                    {/* PASIVOS */}
                                    <section>
                                        <div className="uppercase font-bold text-lg text-gray-900 border-b-2 border-gray-900 mb-4 pb-1">Pasivos</div>

                                        {/* Pasivo Corriente */}
                                        <div className="mb-6 pl-4">
                                            <h4 className="font-bold text-gray-800 mb-2 uppercase text-sm border-b border-gray-300 inline-block">Pasivo Corriente</h4>
                                            <div className="space-y-1 mt-2">
                                                {reporte.clasificado_pasivo?.corriente.map((item, index) => (
                                                    <div key={`pas-curr-${index}`} className="flex justify-between items-end hover:bg-gray-50 transition-colors py-1 border-b border-dotted border-gray-200">
                                                        <div className="flex gap-2 text-sm text-gray-700">
                                                            <span className="font-mono text-gray-500 text-xs w-12 text-right">{item.codigo}</span>
                                                            <span>{item.nombre}</span>
                                                        </div>
                                                        <span className="font-mono text-sm text-gray-800">{formatCurrency(item.saldo)}</span>
                                                    </div>
                                                ))}
                                                <div className="flex justify-between items-center pt-2 mt-2 font-bold text-gray-900">
                                                    <span className="pl-14 text-sm uppercase">Total Pasivo Corriente</span>
                                                    <span className="font-mono border-t border-gray-800 w-32 text-right">{formatCurrency(reporte.clasificado_pasivo?.total_corriente)}</span>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Pasivo No Corriente */}
                                        <div className="mb-6 pl-4">
                                            <h4 className="font-bold text-gray-800 mb-2 uppercase text-sm border-b border-gray-300 inline-block">Pasivo No Corriente</h4>
                                            <div className="space-y-1 mt-2">
                                                {reporte.clasificado_pasivo?.no_corriente.map((item, index) => (
                                                    <div key={`pas-nocurr-${index}`} className="flex justify-between items-end hover:bg-gray-50 transition-colors py-1 border-b border-dotted border-gray-200">
                                                        <div className="flex gap-2 text-sm text-gray-700">
                                                            <span className="font-mono text-gray-500 text-xs w-12 text-right">{item.codigo}</span>
                                                            <span>{item.nombre}</span>
                                                        </div>
                                                        <span className="font-mono text-sm text-gray-800">{formatCurrency(item.saldo)}</span>
                                                    </div>
                                                ))}
                                                <div className="flex justify-between items-center pt-2 mt-2 font-bold text-gray-900">
                                                    <span className="pl-14 text-sm uppercase">Total Pasivo No Corriente</span>
                                                    <span className="font-mono border-t border-gray-800 w-32 text-right">{formatCurrency(reporte.clasificado_pasivo?.total_no_corriente)}</span>
                                                </div>
                                            </div>
                                        </div>

                                        {/* GRAN TOTAL PASIVOS */}
                                        <div className="flex justify-end mt-4">
                                            <div className="flex justify-between items-center w-full md:w-1/2 bg-gray-100 p-2 border border-gray-300">
                                                <span className="font-bold text-gray-900 uppercase">Total Pasivos</span>
                                                <span className="font-mono font-bold text-lg text-gray-900">{formatCurrency(reporte.total_pasivos)}</span>
                                            </div>
                                        </div>
                                    </section>
                                </>
                            ) : (
                                <>
                                    <div className="space-y-8">
                                        {/* ------------ VISTA ESTANDAR (Auxiliar / Mayor) ------------ */}

                                        <section>
                                            <div className="uppercase font-bold text-lg text-gray-900 border-b-2 border-gray-900 mb-4 pb-1">Activos</div>
                                            <div className="space-y-1 pl-4">
                                                {reporte.activos.length === 0 ? <p className="text-gray-400 italic text-sm">Sin registros.</p> :
                                                    reporte.activos.map((item, index) => (
                                                        <div key={`act-${index}`} className="flex justify-between items-end hover:bg-gray-50 transition-colors py-1 border-b border-dotted border-gray-200">
                                                            <div className="flex gap-2 text-sm text-gray-700">
                                                                <span className="font-mono text-gray-500 text-xs w-12 text-right">{item.codigo}</span>
                                                                <span>{item.nombre}</span>
                                                            </div>
                                                            <span className="font-mono text-sm text-gray-800">{formatCurrency(item.saldo)}</span>
                                                        </div>
                                                    ))
                                                }
                                            </div>
                                            <div className="flex justify-end mt-4">
                                                <div className="flex justify-between items-center w-full md:w-1/2 bg-gray-100 p-2 border border-gray-300">
                                                    <span className="font-bold text-gray-900 uppercase">Total Activos</span>
                                                    <span className="font-mono font-bold text-lg text-gray-900">{formatCurrency(reporte.total_activos)}</span>
                                                </div>
                                            </div>
                                        </section>

                                        <section>
                                            <div className="uppercase font-bold text-lg text-gray-900 border-b-2 border-gray-900 mb-4 pb-1">Pasivos</div>
                                            <div className="space-y-1 pl-4">
                                                {reporte.pasivos.length === 0 ? <p className="text-gray-400 italic text-sm">Sin registros.</p> :
                                                    reporte.pasivos.map((item, index) => (
                                                        <div key={`pas-${index}`} className="flex justify-between items-end hover:bg-gray-50 transition-colors py-1 border-b border-dotted border-gray-200">
                                                            <div className="flex gap-2 text-sm text-gray-700">
                                                                <span className="font-mono text-gray-500 text-xs w-12 text-right">{item.codigo}</span>
                                                                <span>{item.nombre}</span>
                                                            </div>
                                                            <span className="font-mono text-sm text-gray-800">{formatCurrency(item.saldo)}</span>
                                                        </div>
                                                    ))
                                                }
                                            </div>
                                            <div className="flex justify-end mt-4">
                                                <div className="flex justify-between items-center w-full md:w-1/2 bg-gray-100 p-2 border border-gray-300">
                                                    <span className="font-bold text-gray-900 uppercase">Total Pasivos</span>
                                                    <span className="font-mono font-bold text-lg text-gray-900">{formatCurrency(reporte.total_pasivos)}</span>
                                                </div>
                                            </div>
                                        </section>
                                    </div>
                                </>
                            )}

                            {/* SECCIÓN: PATRIMONIO (Común) */}
                            <section className="mt-8">
                                <div className="uppercase font-bold text-lg text-gray-900 border-b-2 border-gray-900 mb-4 pb-1">Patrimonio</div>
                                <div className="space-y-1 pl-4">
                                    {reporte.patrimonio.map((item, index) => (
                                        <div key={`pat-${index}`} className="flex justify-between items-end hover:bg-gray-50 transition-colors py-1 border-b border-dotted border-gray-200">
                                            <div className="flex gap-2 text-sm text-gray-700">
                                                <span className="font-mono text-gray-500 text-xs w-12 text-right">{item.codigo}</span>
                                                <span>{item.nombre}</span>
                                            </div>
                                            <span className="font-mono text-sm text-gray-800">{formatCurrency(item.saldo)}</span>
                                        </div>
                                    ))}

                                    {/* Utilidad del Ejercicio */}
                                    <div className="flex justify-between items-end bg-blue-50 py-2 border-b border-blue-100">
                                        <div className="flex gap-2 text-sm font-bold text-blue-900 pl-14">
                                            <span className="font-mono text-xs w-12 text-right">3605</span>
                                            <span>UTILIDAD (PÉRDIDA) DEL EJERCICIO</span>
                                        </div>
                                        <span className={`font-mono text-sm font-bold pr-1 ${reporte.utilidad_ejercicio >= 0 ? 'text-blue-900' : 'text-red-600'}`}>
                                            {formatCurrency(reporte.utilidad_ejercicio)}
                                        </span>
                                    </div>
                                </div>

                                <div className="flex justify-end mt-4">
                                    <div className="flex justify-between items-center w-full md:w-1/2 bg-gray-100 p-2 border border-gray-300">
                                        <span className="font-bold text-gray-900 uppercase">Total Patrimonio</span>
                                        <span className="font-mono font-bold text-lg text-gray-900">{formatCurrency(reporte.total_patrimonio)}</span>
                                    </div>
                                </div>
                            </section>

                            {/* ECUACIÓN CONTABLE FIN DE REPORTE */}
                            <div className="mt-12 pt-4 border-t-4 border-gray-900">
                                <div className="flex justify-between items-center text-xl font-bold text-gray-900 px-4">
                                    <span>TOTAL PASIVO + PATRIMONIO</span>
                                    <span className="font-mono border-b-4 border-double border-gray-900 pb-1">{formatCurrency(reporte.total_pasivo_patrimonio)}</span>
                                </div>
                                <p className="text-center text-xs text-gray-400 mt-8 mb-8">*** Fin del Informe ***</p>

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
                )}
            </div>
        </div>
    );
}