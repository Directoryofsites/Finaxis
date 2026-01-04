'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRouter, useSearchParams, usePathname } from 'next/navigation';
import Script from 'next/script';
import {
    FaListOl,
    FaCalendarAlt,
    FaSearch,
    FaFilePdf,
    FaFileCsv,
    FaFilter,
    FaExclamationTriangle,
    FaBook
} from 'react-icons/fa';
import { toast } from 'react-toastify';

import { useAuth } from '../../../context/AuthContext';
import { apiService } from '../../../../lib/apiService';

// Estilos Reusables (Manual v2.0)
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none pl-10";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white pl-10";

export default function AuxiliarPorCuentaPage() {
    const { user, authLoading } = useAuth();
    const router = useRouter();
    const searchParams = useSearchParams(); // Hook para leer URL

    const [cuentas, setCuentas] = useState([]);
    const [selectedAccount, setSelectedAccount] = useState('');
    const [startDate, setStartDate] = useState(new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0]);
    const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);

    const [reportData, setReportData] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [isPageReady, setPageReady] = useState(false);
    const [autoPdfTrigger, setAutoPdfTrigger] = useState(false); // Trigger para PDF automático
    const [wppNumber, setWppNumber] = useState(null); // Número de WhatsApp destino
    const [emailAddress, setEmailAddress] = useState(null); // Correo destino (Fix: Agregando estado faltante)
    const pathname = usePathname();
    const lastProcessedParams = useRef(''); // Ref para evitar loops infinitos

    // Verificación de Sesión y Carga Inicial
    useEffect(() => {
        if (!authLoading) {
            if (user && user.empresaId) {
                setPageReady(true);
                fetchCuentas();
            } else {
                router.push('/login');
            }
        }
    }, [user, authLoading, router]);

    // EFECTO: Leer Parámetros URL y Ejecutar Reporte
    useEffect(() => {
        if (!authLoading && cuentas.length > 0 && searchParams.size > 0) {
            const pCuenta = searchParams.get('cuenta');
            const pInicio = searchParams.get('fecha_inicio');
            const pFin = searchParams.get('fecha_fin');
            const pAutoPdf = searchParams.get('auto_pdf');
            const pWpp = searchParams.get('wpp');
            const pEmail = searchParams.get('email');

            const currentParamsSignature = `${pCuenta}-${pInicio}-${pFin}-${pAutoPdf}-${pWpp}-${pEmail}`;

            if (lastProcessedParams.current === currentParamsSignature) return;

            if (pCuenta) {
                // --- BÚSQUEDA INTELIGENTE (NORMALIZACIÓN FONÉTICA + SCORING) ---
                const normalize = (str) => {
                    if (!str) return "";
                    return str.toLowerCase()
                        .normalize("NFD").replace(/[\u0300-\u036f]/g, "") // Sin tildes
                        .replace(/v/g, "b")  // Fonética V -> B
                        .replace(/z/g, "s")  // Fonética Z -> S
                        .replace(/c/g, "s")  // Fonética C -> S (Casa -> Sasa, Caza -> Sasa)
                        .replace(/g/g, "j")  // Fonética G -> J (Gente -> Jente)
                        .replace(/[^a-z0-9\s]/g, ""); // Solo letras y numeros
                };

                const searchNormalized = normalize(pCuenta);
                const searchWords = searchNormalized.split(" ").filter(w => w.length > 2); // Palabras clave > 2 letras

                const scoredCuentas = cuentas.map(c => {
                    let score = 0;
                    const nombreNorm = normalize(c.nombre);
                    const codigoNorm = normalize(c.codigo);

                    // 1. Coincidencia Exacta (High priority)
                    if (nombreNorm === searchNormalized) score += 100;
                    if (codigoNorm === searchNormalized) score += 100;

                    // 2. Contiene la frase completa
                    if (nombreNorm.includes(searchNormalized)) score += 50;

                    // 3. Coincidencia por palabras (Bag of words)
                    searchWords.forEach(word => {
                        // Match simple
                        if (nombreNorm.includes(word) || codigoNorm.includes(word)) {
                            score += 10;
                        } else {
                            // Match singular/plural (muy básico: quitar 's' final)
                            const wordNoS = word.endsWith('s') ? word.slice(0, -1) : word;
                            if (wordNoS.length > 3 && (nombreNorm.includes(wordNoS) || codigoNorm.includes(wordNoS))) {
                                score += 8; // Un poco menos que match exacto
                            }
                        }
                    });

                    // 4. Boost para Cuentas Auxiliares (Hojas) -> Priorizar el detalle sobre el grupo
                    if (c.es_auxiliar) score += 25;

                    return { ...c, score };
                });

                // Ordenar por score descendente, Y LUEGO POR LONGITUD DE NOMBRE (Más largo = Más específico)
                const bestMatches = scoredCuentas.filter(c => c.score > 0).sort((a, b) => {
                    if (b.score !== a.score) return b.score - a.score;
                    return b.nombre.length - a.nombre.length; // Tie-breaker: Preferir nombre más largo
                });
                const matched = bestMatches.length > 0 ? bestMatches[0] : null;

                // DEBUG VISUAL PARA EL USUARIO
                if (bestMatches.length > 0) {
                    const top3 = bestMatches.slice(0, 3).map(c => `${c.nombre} (${c.score})`).join(' | ');
                    toast.info(`IA Matches: ${top3}`, { autoClose: 5000 });
                }

                if (matched) {
                    setSelectedAccount(matched.id);
                    if (pInicio) setStartDate(pInicio);
                    if (pFin) setEndDate(pFin);

                    // Auto-Execute
                    if (pInicio && pFin) {
                        lastProcessedParams.current = currentParamsSignature;
                        if (pAutoPdf === 'true') setAutoPdfTrigger(true);
                        if (pWpp) setWppNumber(pWpp);
                        if (pEmail) setEmailAddress(pEmail);

                        // Delay para asegurar render
                        setTimeout(() => {
                            fetchReport(matched.id, pInicio, pFin);
                            window.history.replaceState(null, '', pathname); // Limpieza diferida
                        }, 500);
                    } else {
                        // Si faltan fechas, solo seleccionamos la cuenta pero NO ejecutamos
                        toast.info(`Cuenta encontrada: ${matched.codigo} - ${matched.nombre}`);
                    }
                } else {
                    toast.warning(`No se encontró cuenta similar a: "${pCuenta}"`);
                }
            }
        }
    }, [cuentas, searchParams, authLoading, pathname, router]);

    // EFECTO: Descarga Automática de PDF y WhatsApp cuando llegan los datos
    useEffect(() => {
        if (autoPdfTrigger && reportData && !isLoading) {
            handleExportPDF();

            // Si hay número de WhatsApp, abrimos el chat
            if (wppNumber) {
                const cuentaNombre = cuentas.find(c => c.id == selectedAccount)?.nombre || 'la cuenta';
                const message = `Hola, adjunto el reporte Auxiliar de *${cuentaNombre}* del periodo ${startDate} al ${endDate}.`;
                const wppUrl = `https://wa.me/${wppNumber}?text=${encodeURIComponent(message)}`;

                // Pequeño delay para que el navegador no bloquee el popup
                setTimeout(() => {
                    window.open(wppUrl, '_blank');
                }, 1000);
            }

            setAutoPdfTrigger(false); // Reset trigger
            setWppNumber(null);
        }
    }, [reportData, autoPdfTrigger, isLoading, wppNumber]);


    const fetchCuentas = async () => {
        try {
            const res = await apiService.get('/plan-cuentas/');
            const aplanarCuentas = (cuentasArray) => {
                let listaPlana = [];
                cuentasArray.forEach(cuenta => {
                    // Detectar si es auxiliar (hoja) si no tiene hijos o si hijos es vacío
                    const esAuxiliar = !cuenta.children || cuenta.children.length === 0;

                    listaPlana.push({
                        id: cuenta.id,
                        codigo: cuenta.codigo,
                        nombre: cuenta.nombre,
                        es_auxiliar: esAuxiliar
                    });

                    if (cuenta.children && cuenta.children.length > 0) {
                        listaPlana = listaPlana.concat(aplanarCuentas(cuenta.children));
                    }
                });
                return listaPlana;
            };
            setCuentas(aplanarCuentas(res.data));
        } catch (err) {
            setError("Error al cargar el plan de cuentas: " + (err.response?.data?.detail || err.message));
        }
    };

    // Lógica Central de Consulta
    const fetchReport = async (accountId, start, end) => {
        setIsLoading(true);
        setError(null);
        setReportData(null);

        const params = {
            cuenta_id: accountId,
            fecha_inicio: start,
            fecha_fin: end,
        };

        try {
            const res = await apiService.get('/reports/account-ledger', { params: params });
            setReportData(res.data);
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al generar el reporte auxiliar.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleGenerateReport = () => {
        if (!selectedAccount || !startDate || !endDate) {
            setError('Por favor, selecciona una cuenta y un rango de fechas válido.');
            return;
        }
        fetchReport(selectedAccount, startDate, endDate);
    };

    const handleExportToCSV = () => {
        if (!reportData) return;
        if (typeof window.Papa === 'undefined') {
            alert("Librería CSV no cargada. Recargue la página.");
            return;
        }

        const dataToExport = [
            ['Fecha', 'Tipo Doc', 'Número', 'Nit/CC', 'Beneficiario', 'Concepto', 'Debito', 'Credito', 'Saldo Parcial'],
            ['', '', '', '', '', 'SALDO ANTERIOR', '', '', reportData.saldoAnterior.toFixed(2)],
            ...reportData.movimientos.map(mov => [
                new Date(mov.fecha).toLocaleDateString('es-CO', { timeZone: 'UTC' }),
                mov.tipo_documento,
                mov.numero_documento,
                mov.beneficiario_nit || '',
                mov.beneficiario || '',
                mov.concepto.replace(/,/g, ''),
                parseFloat(mov.debito).toFixed(2),
                parseFloat(mov.credito).toFixed(2),
                mov.saldo_parcial.toFixed(2)
            ])
        ];

        const csv = window.Papa.unparse(dataToExport, { delimiter: ';' });
        const blob = new Blob(["\uFEFF" + csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        const cuentaNombre = cuentas.find(c => c.id == selectedAccount)?.nombre || 'cuenta';
        link.setAttribute('download', `Auxiliar_${cuentaNombre}_${startDate}_${endDate}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const handleExportPDF = async () => {
        if (!reportData) return;
        setIsLoading(true);
        setError(null);

        try {
            const paramsForSignedUrl = {
                fecha_inicio: startDate,
                fecha_fin: endDate,
                cuenta_id: selectedAccount,
            };

            const signedUrlRes = await apiService.get('/reports/account-ledger/get-signed-url', { params: paramsForSignedUrl });
            const signedToken = signedUrlRes.data.signed_url_token;
            const finalPdfUrl = `${process.env.NEXT_PUBLIC_API_URL}/api/reports/account-ledger/imprimir?signed_token=${signedToken}`;

            // MÉTODO BRUTO: Navegación directa
            // Al ser un attachment, el navegador no cambia de página, solo descarga.
            window.location.href = finalPdfUrl;

        } catch (err) {
            setError(err.response?.data?.detail || 'Error al obtener el PDF.');
        } finally {
            setIsLoading(false);
        }
    };

    const formatCurrency = (val) => {
        return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 2 }).format(val);
    };

    if (!isPageReady) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
                <FaListOl className="text-indigo-300 text-6xl mb-4 animate-pulse" />
                <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando Auxiliar...</p>
            </div>
        );
    }

    return (
        <>
            <Script src="https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js" />

            <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
                <div className="max-w-6xl mx-auto">



                    {/* ENCABEZADO */}
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                        <div>
                            <div className="flex items-center gap-3 mt-3">
                                <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                                    <FaListOl className="text-2xl" />
                                </div>
                                <div>
                                    <div className="flex items-center gap-4">
                                        <h1 className="text-3xl font-bold text-gray-800">Auxiliar por Cuenta</h1>
                                        <button
                                            onClick={() => window.open('/manual/capitulo_31_auxiliar_cuenta.html', '_blank')}
                                            className="text-indigo-600 hover:bg-indigo-50 px-2 py-1 rounded-md flex items-center gap-2 transition-colors"
                                            title="Ver Manual de Usuario"
                                        >
                                            <span className="text-lg">📖</span> <span className="font-bold text-sm hidden md:inline">Manual</span>
                                        </button>
                                    </div>
                                    <p className="text-gray-500 text-sm">Detalle cronológico de movimientos para una cuenta específica.</p>

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
                        <div className="flex items-center gap-2 mb-6 border-b border-gray-100 pb-2">
                            <FaFilter className="text-indigo-500" />
                            <h2 className="text-lg font-bold text-gray-700">Criterios de Búsqueda</h2>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 items-end">
                            {/* Selector de Cuenta */}
                            <div className="md:col-span-2">
                                <label htmlFor="cuenta" className={labelClass}>Cuenta Contable</label>
                                <div className="relative">
                                    <select
                                        id="cuenta"
                                        value={selectedAccount}
                                        onChange={e => setSelectedAccount(e.target.value)}
                                        className={selectClass}
                                    >
                                        <option value="">Seleccione una cuenta...</option>
                                        {cuentas.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
                                    </select>
                                    <FaListOl className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                </div>
                            </div>

                            {/* Fecha Inicio */}
                            <div>
                                <label htmlFor="fecha_inicio" className={labelClass}>Desde</label>
                                <div className="relative">
                                    <input
                                        type="date"
                                        id="fecha_inicio"
                                        value={startDate}
                                        onChange={e => setStartDate(e.target.value)}
                                        className={inputClass}
                                    />
                                    <FaCalendarAlt className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                </div>
                            </div>

                            {/* Fecha Fin */}
                            <div>
                                <label htmlFor="fecha_fin" className={labelClass}>Hasta</label>
                                <div className="relative">
                                    <input
                                        type="date"
                                        id="fecha_fin"
                                        value={endDate}
                                        onChange={e => setEndDate(e.target.value)}
                                        className={inputClass}
                                    />
                                    <FaCalendarAlt className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                </div>
                            </div>
                        </div>

                        <div className="flex justify-end mt-6 pt-4 border-t border-gray-100">
                            <button
                                onClick={handleGenerateReport}
                                disabled={isLoading}
                                className={`
                            px-8 py-2 rounded-lg shadow-md font-bold text-white transition-all transform hover:-translate-y-0.5 flex items-center gap-2
                            ${isLoading ? 'bg-gray-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'}
                        `}
                            >
                                {isLoading ? <span className="loading loading-spinner loading-sm"></span> : <><FaSearch /> Consultar Movimientos</>}
                            </button>
                        </div>
                    </div>

                    {/* MENSAJE ERROR */}
                    {error && (
                        <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded-r-lg flex items-center gap-3 animate-pulse">
                            <FaExclamationTriangle className="text-xl" />
                            <p className="font-bold">{error}</p>
                        </div>
                    )}

                    {/* CARD 2: RESULTADOS */}
                    {reportData && (
                        <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden animate-slideDown">
                            {/* Cabecera Reporte */}
                            <div className="p-6 bg-gray-50 border-b border-gray-200 flex flex-col md:flex-row justify-between items-center gap-4">
                                <div>
                                    <h2 className="text-xl font-bold text-gray-800">
                                        {cuentas.find(c => c.id == selectedAccount)?.codigo} - {cuentas.find(c => c.id == selectedAccount)?.nombre}
                                    </h2>
                                    <p className="text-sm text-gray-600 font-medium mt-1">
                                        Periodo: <span className="text-indigo-600">{startDate}</span> al <span className="text-indigo-600">{endDate}</span>
                                    </p>
                                </div>

                                <div className="flex gap-3">
                                    <button onClick={handleExportToCSV} disabled={isLoading} className="flex items-center gap-2 px-4 py-2 bg-white border border-green-500 text-green-600 rounded-lg hover:bg-green-50 font-medium transition-colors shadow-sm disabled:opacity-50"><FaFileCsv /> CSV</button>
                                    <button onClick={handleExportPDF} disabled={isLoading} className="flex items-center gap-2 px-4 py-2 bg-white border border-red-500 text-red-600 rounded-lg hover:bg-red-50 font-medium transition-colors shadow-sm disabled:opacity-50"><FaFilePdf /> PDF</button>
                                </div>
                            </div>

                            <div className="overflow-x-auto">
                                <table className="min-w-full divide-y divide-gray-200">
                                    <thead className="bg-slate-100">
                                        <tr>
                                            <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">Fecha</th>
                                            <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">Documento</th>
                                            <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">Beneficiario</th>
                                            <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider w-1/4">Concepto</th>
                                            <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase tracking-wider">Débito</th>
                                            <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase tracking-wider">Crédito</th>
                                            <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase tracking-wider bg-slate-200/50">Saldo</th>
                                        </tr>
                                    </thead>
                                    <tbody className="bg-white divide-y divide-gray-100">
                                        {/* Saldo Anterior */}
                                        <tr className="bg-yellow-50">
                                            <td colSpan={6} className="px-4 py-3 text-right text-sm font-bold text-yellow-700 uppercase tracking-wide">
                                                Saldo Anterior al {new Date(startDate + 'T00:00:00').toLocaleDateString('es-CO')}:
                                            </td>
                                            <td className="px-4 py-3 text-right text-sm font-mono font-bold text-yellow-800 bg-yellow-100/50">
                                                {formatCurrency(reportData.saldoAnterior)}
                                            </td>
                                        </tr>

                                        {/* Movimientos */}
                                        {reportData.movimientos.length === 0 ? (
                                            <tr><td colSpan="7" className="text-center py-8 text-gray-400 italic">No hay movimientos en este periodo.</td></tr>
                                        ) : (
                                            reportData.movimientos.map((mov, index) => (
                                                <tr key={index} className="hover:bg-indigo-50/20 transition-colors">
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600 font-mono">
                                                        {new Date(mov.fecha).toLocaleDateString('es-CO', { timeZone: 'UTC' })}
                                                    </td>
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-800">
                                                        {`${mov.tipo_documento} #${mov.numero_documento}`}
                                                    </td>
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600 truncate max-w-xs" title={mov.beneficiario}>
                                                        {mov.beneficiario}
                                                    </td>
                                                    <td className="px-4 py-3 text-sm text-gray-500 italic truncate max-w-xs" title={mov.concepto}>
                                                        {mov.concepto}
                                                    </td>
                                                    <td className="px-4 py-3 text-right text-sm font-mono text-gray-700">
                                                        {parseFloat(mov.debito) > 0 ? formatCurrency(mov.debito) : '-'}
                                                    </td>
                                                    <td className="px-4 py-3 text-right text-sm font-mono text-gray-700">
                                                        {parseFloat(mov.credito) > 0 ? formatCurrency(mov.credito) : '-'}
                                                    </td>
                                                    <td className="px-4 py-3 text-right text-sm font-mono font-bold text-indigo-900 bg-slate-50">
                                                        {formatCurrency(mov.saldo_parcial)}
                                                    </td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>

                                    {/* Saldo Final */}
                                    {/* Saldo Final y Totales */}
                                    <tfoot className="bg-slate-800 text-white border-t-4 border-indigo-500">
                                        <tr>
                                            <td colSpan="4" className="px-4 py-4 text-right text-sm font-bold uppercase tracking-wider">
                                                TOTALES PERIODO Y SALDO FINAL:
                                            </td>
                                            <td className="px-4 py-4 text-right text-sm font-mono font-bold text-green-300">
                                                {formatCurrency(reportData.movimientos.reduce((acc, m) => acc + parseFloat(m.debito || 0), 0))}
                                            </td>
                                            <td className="px-4 py-4 text-right text-sm font-mono font-bold text-red-300">
                                                {formatCurrency(reportData.movimientos.reduce((acc, m) => acc + parseFloat(m.credito || 0), 0))}
                                            </td>
                                            <td className="px-4 py-4 text-right text-lg font-mono font-bold text-white bg-slate-700 border-l border-slate-600">
                                                {(reportData.movimientos.length > 0
                                                    ? formatCurrency(reportData.movimientos[reportData.movimientos.length - 1].saldo_parcial)
                                                    : formatCurrency(reportData.saldoAnterior)
                                                )}
                                            </td>
                                        </tr>
                                    </tfoot>
                                </table>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </>
    );
}