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
    const [isPageReady, setPageReady] = useState(false);

    // Automation State
    const [autoPdfTrigger, setAutoPdfTrigger] = useState(false);
    const [wppNumber, setWppNumber] = useState(null);
    const [emailAddress, setEmailAddress] = useState(null);
    const lastProcessedParams = React.useRef('');

    // Efecto de Autenticación
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
            const aiFechaCorte = urlParams.get('fecha_corte');

            const pAutoPdf = urlParams.get('auto_pdf');
            const pWpp = urlParams.get('wpp');
            const pEmail = urlParams.get('email');

            if (aiFechaCorte) {
                const currentSignature = `${aiFechaCorte}-${pAutoPdf}-${pWpp}-${pEmail}`;
                if (lastProcessedParams.current === currentSignature) return;
                lastProcessedParams.current = currentSignature;

                setFechaCorte(aiFechaCorte);

                if (pAutoPdf === 'true') setAutoPdfTrigger(true);
                if (pWpp) setWppNumber(pWpp);
                if (pEmail) setEmailAddress(pEmail);

                // Auto-ejecutar reporte si hay fecha
                setTimeout(() => {
                    document.getElementById('btn-generar-balance')?.click();
                    window.history.replaceState(null, '', window.location.pathname);
                }, 500);
            }
        }
    }, [isPageReady]);

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
                params: { fecha_corte: fechaCorte }
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
                params: { fecha_corte: fechaCorte }
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

                {/* CARD 2: REPORTE (RESULTADOS) */}
                {reporte && (
                    <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden animate-slideDown">
                        {/* Cabecera del Reporte */}
                        <div className="bg-slate-50 p-6 border-b border-gray-200 text-center">
                            <h2 className="text-2xl font-bold text-gray-800">{user?.nombre_empresa || 'Empresa'}</h2>
                            <p className="text-sm text-gray-500 font-medium uppercase tracking-wider mt-1">Estado de Situación Financiera</p>
                            <p className="text-indigo-600 font-bold mt-2 text-lg">
                                <FaCalendarAlt className="inline mr-2 mb-1" /> Corte a: {new Date(fechaCorte).toLocaleDateString('es-CO', { timeZone: 'UTC', year: 'numeric', month: 'long', day: 'numeric' })}
                            </p>
                        </div>

                        <div className="p-6 space-y-8">

                            {/* SECCIÓN: ACTIVOS */}
                            <section>
                                <div className="flex items-center gap-2 mb-4 pb-2 border-b-2 border-emerald-100">
                                    <div className="p-2 bg-emerald-100 text-emerald-600 rounded-lg"><FaMoneyBillWave /></div>
                                    <h3 className="text-xl font-bold text-gray-700">Activos</h3>
                                </div>
                                <div className="pl-2 md:pl-4 space-y-1">
                                    {reporte.activos.length === 0 ? <p className="text-gray-400 italic text-sm">Sin registros.</p> :
                                        reporte.activos.map((item, index) => (
                                            <AccountRow key={`act-${index}`} codigo={item.codigo} nombre={item.nombre} saldo={item.saldo} colorClass="text-emerald-700" />
                                        ))
                                    }
                                </div>
                                <div className="flex justify-between items-center mt-3 pt-3 border-t border-gray-200 bg-emerald-50/50 p-3 rounded-lg">
                                    <span className="font-bold text-gray-700 uppercase text-sm">Total Activos</span>
                                    <span className="font-mono text-lg font-bold text-emerald-700">{formatCurrency(reporte.total_activos)}</span>
                                </div>
                            </section>

                            {/* SECCIÓN: PASIVOS */}
                            <section>
                                <div className="flex items-center gap-2 mb-4 pb-2 border-b-2 border-rose-100">
                                    <div className="p-2 bg-rose-100 text-rose-600 rounded-lg"><FaBuilding /></div>
                                    <h3 className="text-xl font-bold text-gray-700">Pasivos</h3>
                                </div>
                                <div className="pl-2 md:pl-4 space-y-1">
                                    {reporte.pasivos.length === 0 ? <p className="text-gray-400 italic text-sm">Sin registros.</p> :
                                        reporte.pasivos.map((item, index) => (
                                            <AccountRow key={`pas-${index}`} codigo={item.codigo} nombre={item.nombre} saldo={item.saldo} colorClass="text-rose-700" />
                                        ))
                                    }
                                </div>
                                <div className="flex justify-between items-center mt-3 pt-3 border-t border-gray-200 bg-rose-50/50 p-3 rounded-lg">
                                    <span className="font-bold text-gray-700 uppercase text-sm">Total Pasivos</span>
                                    <span className="font-mono text-lg font-bold text-rose-700">{formatCurrency(reporte.total_pasivos)}</span>
                                </div>
                            </section>

                            {/* SECCIÓN: PATRIMONIO */}
                            <section>
                                <div className="flex items-center gap-2 mb-4 pb-2 border-b-2 border-blue-100">
                                    <div className="p-2 bg-blue-100 text-blue-600 rounded-lg"><FaLandmark /></div>
                                    <h3 className="text-xl font-bold text-gray-700">Patrimonio</h3>
                                </div>
                                <div className="pl-2 md:pl-4 space-y-1">
                                    {reporte.patrimonio.map((item, index) => (
                                        <AccountRow key={`pat-${index}`} codigo={item.codigo} nombre={item.nombre} saldo={item.saldo} colorClass="text-blue-700" />
                                    ))}

                                    {/* Utilidad del Ejercicio (Calculada dinámicamente) */}
                                    <div className="flex justify-between items-center py-2 px-2 bg-blue-50 rounded border border-blue-100 mt-2">
                                        <div className="flex gap-3 items-center">
                                            <span className="font-mono text-xs font-bold px-2 py-0.5 rounded-md bg-white text-blue-600 border border-blue-100">3605</span>
                                            <span className="text-sm text-blue-900 font-bold">Utilidad (Pérdida) del Ejercicio</span>
                                        </div>
                                        <span className={`font-mono text-sm font-bold ${reporte.utilidad_ejercicio >= 0 ? 'text-blue-700' : 'text-red-600'}`}>
                                            {formatCurrency(reporte.utilidad_ejercicio)}
                                        </span>
                                    </div>
                                </div>
                                <div className="flex justify-between items-center mt-3 pt-3 border-t border-gray-200 bg-blue-50/50 p-3 rounded-lg">
                                    <span className="font-bold text-gray-700 uppercase text-sm">Total Patrimonio</span>
                                    <span className="font-mono text-lg font-bold text-blue-700">{formatCurrency(reporte.total_patrimonio)}</span>
                                </div>
                            </section>

                            {/* ECUACIÓN CONTABLE */}
                            <div className="mt-8 pt-6 border-t-4 border-gray-200">
                                <div className="flex flex-col md:flex-row justify-between items-center bg-slate-800 text-white p-6 rounded-xl shadow-lg">
                                    <div className="flex items-center gap-3 mb-4 md:mb-0">
                                        <FaChartPie className="text-3xl text-yellow-400" />
                                        <div>
                                            <p className="text-sm text-slate-300 uppercase tracking-wider font-bold">Ecuación Patrimonial</p>
                                            <p className="text-xs text-slate-400">Total Pasivo + Total Patrimonio</p>
                                        </div>
                                    </div>
                                    <div className="text-3xl font-mono font-bold text-yellow-400">
                                        {formatCurrency(reporte.total_pasivo_patrimonio)}
                                    </div>
                                </div>

                                {/* Verificación Visual de Cuadre */}
                                {Math.abs(reporte.total_activos - reporte.total_pasivo_patrimonio) < 1 ? (
                                    <p className="text-center text-green-600 font-bold mt-3 flex justify-center items-center gap-2">
                                        <FaBalanceScale /> El balance está cuadrado correctamente.
                                    </p>
                                ) : (
                                    <p className="text-center text-red-500 font-bold mt-3 flex justify-center items-center gap-2 animate-pulse">
                                        <FaExclamationTriangle /> El balance presenta descuadres. Revise la contabilidad.
                                    </p>
                                )}
                            </div>

                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}