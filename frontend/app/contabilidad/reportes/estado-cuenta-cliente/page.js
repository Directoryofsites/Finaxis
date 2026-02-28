'use client';

import React, { useState, useEffect, useRef, Suspense } from 'react';
import Script from 'next/script';
import { useRouter, useSearchParams } from 'next/navigation';
import {
    FaUserTag,
    FaCalendarAlt,
    FaSearch,
    FaFileCsv,
    FaFilePdf,
    FaMoneyBillWave,
    FaExclamationTriangle,
    FaClock,
    FaCheckCircle,
    FaBook
} from 'react-icons/fa';
import { toast } from 'react-toastify';

import { useAuth } from '../../../context/AuthContext';
import { apiService } from '../../../../lib/apiService';

// --- ESTILOS REUSABLES (Manual v2.0) ---
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none pl-10";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white pl-10";

// NUEVO: Select Inteligente con Búsqueda Integrada para un solo elemento
const SingleSearchSelect = ({ options, value, onChange, placeholder = "Seleccionar...", icon }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [searchTerm, setSearchTerm] = useState("");
    const dropdownRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const filteredOptions = options.filter(opt =>
        (opt.label || opt.nombre || opt.razon_social || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
        (opt.codigo || opt.numero_identificacion || opt.nit || "").toLowerCase().includes(searchTerm.toLowerCase())
    );

    const selectedOption = options.find(opt => opt.id === value);
    const displayLabel = selectedOption ? (selectedOption.label || selectedOption.nombre || selectedOption.razon_social) : placeholder;

    return (
        <div className="relative" ref={dropdownRef}>
            <div
                className="w-full px-4 py-2 pl-10 border border-gray-300 rounded-lg shadow-sm bg-white text-sm cursor-pointer flex justify-between items-center focus-within:ring-2 focus-within:ring-indigo-500 focus-within:border-indigo-500 transition-all"
                onClick={() => { setIsOpen(!isOpen); setSearchTerm(''); }}
            >
                {icon && <div className="absolute left-3 top-3 text-gray-400 pointer-events-none">{icon}</div>}
                <span className={`truncate font-medium ${selectedOption ? 'text-gray-900' : 'text-gray-500'}`}>
                    {displayLabel}
                </span>
                <span className="text-gray-400 text-xs">▼</span>
            </div>

            {isOpen && (
                <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-xl max-h-60 flex flex-col">
                    <div className="p-2 border-b border-gray-100">
                        <input
                            type="text"
                            className="w-full px-3 py-2 border border-gray-200 rounded text-sm focus:outline-none focus:border-indigo-500 bg-gray-50"
                            placeholder="Escribe para buscar (ej: JIM)..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            autoFocus
                            onClick={(e) => e.stopPropagation()}
                        />
                    </div>
                    <div className="overflow-y-auto flex-1 p-1 space-y-1 bg-white drop-shadow-xl">
                        <div
                            className={`px-3 py-2 text-sm rounded cursor-pointer transition-colors ${!value ? 'bg-indigo-50 text-indigo-700 font-bold' : 'hover:bg-gray-100 text-gray-700'}`}
                            onClick={() => { onChange(""); setIsOpen(false); }}
                        >
                            -- Borrar Selección --
                        </div>
                        {filteredOptions.map(option => (
                            <div
                                key={option.id}
                                className={`flex flex-col px-3 py-2 rounded cursor-pointer transition-colors ${value === option.id ? 'bg-indigo-50 border-l-2 border-indigo-500' : 'hover:bg-gray-50 border-l-2 border-transparent'}`}
                                onClick={() => { onChange(option.id); setIsOpen(false); }}
                            >
                                <span className={`text-sm ${value === option.id ? 'text-indigo-700 font-bold' : 'text-gray-800 font-medium'}`}>
                                    {option.label || option.nombre || option.razon_social}
                                </span>
                                {(option.numero_identificacion || option.nit || option.codigo) && (
                                    <span className="text-xs text-gray-400 mt-0.5 font-mono">
                                        ID: {option.numero_identificacion || option.nit || option.codigo}
                                    </span>
                                )}
                            </div>
                        ))}
                        {filteredOptions.length === 0 && (
                            <div className="text-center text-xs text-gray-500 py-4 italic">No se encontraron resultados para "{searchTerm}"</div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

function EstadoCuentaClienteContent() {
    const { user, authLoading } = useAuth();
    const router = useRouter();

    const [filtros, setFiltros] = useState({
        terceroId: '',
        fechaFin: new Date().toISOString().split('T')[0]
    });

    const [terceros, setTerceros] = useState([]);
    const [reportData, setReportData] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [isPageReady, setPageReady] = useState(false);

    // Estados para Automatización (Voz/IA)
    const [autoPdfTrigger, setAutoPdfTrigger] = useState(false);
    const [wppNumber, setWppNumber] = useState(null);
    const [emailAddress, setEmailAddress] = useState(null);
    const [shouldAutoRun, setShouldAutoRun] = useState(false); // Flag para ejecución automática robusta
    const lastProcessedParams = useRef('');

    // Autenticación
    useEffect(() => {
        if (!authLoading) {
            if (user && user.empresaId) {
                setPageReady(true);
            } else {
                router.push('/login');
            }
        }
    }, [user, authLoading, router]);

    const searchParams = useSearchParams();

    // Carga de Clientes
    useEffect(() => {
        if (user?.empresaId) {
            const fetchTerceros = async () => {
                try {
                    const response = await apiService.get('/terceros', { params: { es_cliente: true } });
                    setTerceros(response.data || []);
                } catch (err) {
                    setError("Error al cargar la lista de clientes: " + (err.response?.data?.detail || err.message));
                }
            };
            fetchTerceros();
        }
    }, [user]);

    // AUTO-CONFIGURACIÓN (IA)
    useEffect(() => {
        if (!authLoading && user && terceros.length > 0 && searchParams.size > 0) {
            const aiTercero = searchParams.get('tercero');
            const aiFechaCorte = searchParams.get('fecha_corte');

            // Automation Params
            const pAutoPdf = searchParams.get('auto_pdf');
            const pWpp = searchParams.get('wpp');
            const pEmail = searchParams.get('email');

            const currentSignature = `${aiTercero}-${aiFechaCorte}-${pAutoPdf}-${pWpp}-${pEmail}`;
            if (lastProcessedParams.current === currentSignature) return;

            if (aiTercero) {
                // Normalización para búsqueda
                const normalize = (str) => str ? str.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "") : "";
                const searchNorm = normalize(aiTercero);

                // Buscar mejor coincidencia
                const found = terceros.find(t => {
                    const name = normalize(t.razon_social || '');
                    const nit = normalize(t.numero_identificacion || '');
                    return name.includes(searchNorm) || nit.includes(searchNorm);
                });

                if (found) {
                    setFiltros(prev => ({
                        ...prev,
                        terceroId: found.id,
                        fechaFin: aiFechaCorte || prev.fechaFin
                    }));

                    // Configurar triggers
                    if (pAutoPdf === 'true') setAutoPdfTrigger(true);
                    if (pWpp) setWppNumber(pWpp);
                    if (pEmail) setEmailAddress(pEmail);

                    // Activar Auto-Ejecución (State-based, más robusto que click())
                    setShouldAutoRun(true);
                    toast.info(`⚡ IA: Generando Estado de Cuenta para ${found.razon_social}...`);

                    lastProcessedParams.current = currentSignature;

                    // Limpieza URL diferida
                    setTimeout(() => window.history.replaceState(null, '', window.location.pathname), 2000);
                } else {
                    toast.warning(`No encontré al cliente "${aiTercero}".`);
                }
            }
        }
    }, [terceros, searchParams, user, authLoading]);

    // EFECTO: Ejecución Robusta (Reactiva)
    // Se dispara solo cuando shouldAutoRun es true Y el filtro de tercero ya se actualizó
    useEffect(() => {
        if (shouldAutoRun && filtros.terceroId) {
            handleGenerateReport();
            setShouldAutoRun(false); // Apagar flag para evitar loop
        }
    }, [shouldAutoRun, filtros.terceroId]);

    const handleFiltroChange = (e) => {
        const { name, value } = e.target;
        setFiltros(prev => ({ ...prev, [name]: value }));
    };

    const handleGenerateReport = async () => {
        if (!filtros.terceroId || !filtros.fechaFin) {
            setError("Por favor, seleccione un cliente y una fecha de corte.");
            return;
        }
        setIsLoading(true);
        setError(null);
        setReportData(null);
        try {
            const response = await apiService.get('/reports/estado-cuenta-cliente', {
                params: {
                    tercero_id: filtros.terceroId,
                    fecha_fin: filtros.fechaFin
                }
            });
            setReportData(response.data);
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al generar el reporte.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleExportCSV = () => {
        if (!reportData || !reportData.facturas) return alert("No hay datos para exportar.");
        if (typeof window.Papa === 'undefined') return alert("La librería CSV no está lista.");

        const dataParaCSV = reportData.facturas.map(f => ({
            "Documento": `${f.tipo_documento}-${f.numero}`,
            "Fecha": new Date(f.fecha + 'T00:00:00').toLocaleDateString('es-CO'),
            "Valor Original": f.valor_original,
            "Abonos": f.abonos,
            "Saldo Pendiente": f.saldo_pendiente,
            "Dias Mora": f.dias_mora,
            "Estado": f.estado
        }));

        dataParaCSV.push({});
        dataParaCSV.push({ "Documento": "SALDO TOTAL CLIENTE:", "Saldo Pendiente": reportData.saldoTotal });

        const csv = window.Papa.unparse(dataParaCSV);
        const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.setAttribute('download', `Estado_Cuenta_${reportData.clienteInfo.razon_social}_${filtros.fechaFin}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const handleExportPDF = async () => {
        if (!reportData) return alert("Primero debe generar un reporte.");
        setIsLoading(true);
        setError('');
        try {
            const response = await apiService.get('/reports/estado-cuenta-cliente/get-signed-url', {
                params: {
                    tercero_id: filtros.terceroId,
                    fecha_fin: filtros.fechaFin
                }
            });
            const signedToken = response.data.signed_url_token;
            const pdfUrl = `${process.env.NEXT_PUBLIC_API_URL}/api/reports/estado-cuenta-cliente/imprimir?signed_token=${signedToken}`;

            // ABRIR EN NUEVA PESTAÑA (Request Usuario)
            window.open(pdfUrl, '_blank');

        } catch (err) {
            setError(err.response?.data?.detail || "Error al exportar PDF.");
        } finally {
            setIsLoading(false);
        }
    };

    // HANDLE: Enviar por Correo
    const handleSendEmail = async () => {
        if (!reportData || !emailAddress) return;
        toast.info(`📤 Enviando Estado de Cuenta a ${emailAddress}...`);
        try {
            await apiService.post('/reports/dispatch-email', {
                report_type: 'estado_cuenta_cliente',
                email_to: emailAddress,
                filtros: {
                    tercero_id: filtros.terceroId,
                    fecha_fin: filtros.fechaFin
                }
            });
            toast.success(`✅ Correo enviado a ${emailAddress}`);
        } catch (err) {
            console.error("Error sending email:", err);
            toast.error("❌ Falló el envío del correo.");
        }
    };

    // EFECTO: Automatización Post-Reporte (PDF -> WhatsApp -> Email)
    useEffect(() => {
        if (autoPdfTrigger && reportData && !isLoading) {
            // 1. PDF
            handleExportPDF();

            // 2. WhatsApp
            if (wppNumber) {
                const cliente = reportData.clienteInfo?.razon_social || 'el cliente';
                const total = formatCurrency(reportData.saldoTotal);
                const message = `Hola, adjunto el Estado de Cuenta de *${cliente}* con corte a ${filtros.fechaFin}. Saldo Total: *${total}*.`;
                const wppUrl = `https://wa.me/${wppNumber}?text=${encodeURIComponent(message)}`;
                setTimeout(() => window.open(wppUrl, '_blank'), 1500);
            }

            // 3. Email
            if (emailAddress) {
                handleSendEmail();
            }

            // Reset
            setAutoPdfTrigger(false);
            setWppNumber(null);
            setEmailAddress(null);
        }
    }, [reportData, autoPdfTrigger, isLoading, wppNumber, emailAddress]);

    const formatCurrency = (value) => {
        if (value === null || value === undefined) return '$ 0';
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(value);
    };

    if (!isPageReady) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
                <FaUserTag className="text-indigo-300 text-6xl mb-4 animate-pulse" />
                <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando Cartera...</p>
            </div>
        );
    }

    return (
        <>
            <Script src="https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js" />

            <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
                <div className="max-w-5xl mx-auto">

                    {/* ENCABEZADO */}
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                        <div>
                            <div className="flex items-center gap-3 mt-3">
                                <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                                    <FaUserTag className="text-2xl" />
                                </div>
                                <div>
                                    <div className="flex items-center gap-4">
                                        <h1 className="text-3xl font-bold text-gray-800">Estado de Cuenta (Clientes)</h1>
                                        <button
                                            onClick={() => window.open('/manual/capitulo_36_estado_cuenta_cliente.html', '_blank')}
                                            className="flex items-center gap-2 px-2 py-1 bg-white border border-indigo-200 text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors font-medium shadow-sm"
                                            title="Ver Manual de Usuario"
                                        >
                                            <span className="text-lg">📖</span> <span className="font-bold text-sm hidden md:inline">Manual</span>
                                        </button>
                                    </div>
                                    <p className="text-gray-500 text-sm">Análisis detallado de facturas pendientes y vencimientos.</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* CARD 1: FILTROS */}
                    <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 animate-fadeIn mb-8">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-end">

                            {/* Cliente */}
                            <div className="md:col-span-1">
                                <label htmlFor="terceroId" className={labelClass}>Cliente</label>
                                <SingleSearchSelect
                                    options={terceros}
                                    value={filtros.terceroId}
                                    onChange={(val) => handleFiltroChange({ target: { name: 'terceroId', value: val } })}
                                    placeholder="Seleccione un cliente..."
                                    icon={<FaUserTag />}
                                />
                            </div>

                            {/* Fecha Corte */}
                            <div className="md:col-span-1">
                                <label htmlFor="fechaFin" className={labelClass}>Fecha de Corte</label>
                                <div className="relative">
                                    <input
                                        type="date"
                                        name="fechaFin"
                                        value={filtros.fechaFin}
                                        onChange={handleFiltroChange}
                                        className={inputClass}
                                    />
                                    <FaCalendarAlt className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                </div>
                            </div>

                            {/* Botón Generar */}
                            <div className="md:col-span-1">
                                <button
                                    id="btn-generar-estado"
                                    onClick={handleGenerateReport}
                                    disabled={isLoading}
                                    className={`
                                w-full px-6 py-2 rounded-lg shadow-md font-bold text-white transition-all transform hover:-translate-y-0.5 flex items-center justify-center gap-2
                                ${isLoading ? 'bg-gray-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'}
                            `}
                                >
                                    {isLoading ? <span className="loading loading-spinner loading-sm"></span> : <><FaSearch /> Generar Estado</>}
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

                    {/* CARD 2: RESULTADOS */}
                    {reportData && (
                        <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden animate-slideDown">

                            {/* Cabecera Reporte */}
                            <div className="p-6 bg-gray-50 border-b border-gray-200 flex flex-col md:flex-row justify-between items-center gap-4">
                                <div>
                                    <h2 className="text-xl font-bold text-gray-800">{reportData.clienteInfo?.razon_social}</h2>
                                    <p className="text-sm text-gray-600 font-mono mt-1">NIT: {reportData.clienteInfo?.nit}</p>
                                </div>
                                <div className="flex gap-3">
                                    <button onClick={handleExportCSV} disabled={isLoading} className="flex items-center gap-2 px-4 py-2 bg-white border border-green-500 text-green-600 rounded-lg hover:bg-green-50 font-medium transition-colors shadow-sm disabled:opacity-50"><FaFileCsv /> CSV</button>
                                    <button onClick={handleExportPDF} disabled={isLoading} className="flex items-center gap-2 px-4 py-2 bg-white border border-red-500 text-red-600 rounded-lg hover:bg-red-50 font-medium transition-colors shadow-sm disabled:opacity-50"><FaFilePdf /> PDF</button>
                                </div>
                            </div>

                            {/* Tabla */}
                            <div className="overflow-x-auto">
                                <table className="min-w-full divide-y divide-gray-200">
                                    <thead className="bg-slate-100">
                                        <tr>
                                            <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">Documento</th>
                                            <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">Emisión</th>
                                            <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase tracking-wider">Valor Original</th>
                                            <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase tracking-wider">Abonos</th>
                                            <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase tracking-wider bg-slate-200/50">Saldo</th>
                                            <th className="px-4 py-3 text-center text-xs font-bold text-gray-600 uppercase tracking-wider">Estado</th>
                                        </tr>
                                    </thead>
                                    <tbody className="bg-white divide-y divide-gray-100">
                                        {(!reportData.facturas || reportData.facturas.length === 0) ? (
                                            <tr><td colSpan="6" className="text-center py-10 text-gray-400 italic">Este cliente está a paz y salvo. No tiene facturas pendientes.</td></tr>
                                        ) : (
                                            reportData.facturas.map((factura) => (
                                                <tr key={factura.id} className="hover:bg-indigo-50/20 transition-colors">
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-800">
                                                        {factura.tipo_documento}-{factura.numero}
                                                    </td>
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600 font-mono">
                                                        {new Date(factura.fecha + 'T00:00:00').toLocaleDateString('es-CO')}
                                                    </td>
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-right font-mono text-gray-700">
                                                        {formatCurrency(factura.valor_original)}
                                                    </td>
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-right font-mono text-green-600">
                                                        ({formatCurrency(factura.abonos)})
                                                    </td>
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-right font-bold font-mono text-indigo-900 bg-slate-50">
                                                        {formatCurrency(factura.saldo_pendiente)}
                                                    </td>
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-center">
                                                        {factura.estado === 'VENCIDA' ? (
                                                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                                                <FaExclamationTriangle className="mr-1" /> {factura.dias_mora} días mora
                                                            </span>
                                                        ) : (
                                                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                                                <FaClock className="mr-1" /> Vence en {factura.dias_para_vencer} días
                                                            </span>
                                                        )}
                                                    </td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>

                                    {/* Footer Saldo Total */}
                                    <tfoot className="bg-slate-800 text-white border-t-4 border-indigo-500">
                                        <tr>
                                            <td colSpan="4" className="px-4 py-4 text-right text-sm font-bold uppercase tracking-wider">Saldo Total Cliente:</td>
                                            <td className="px-4 py-4 text-right font-mono font-bold text-xl text-white bg-slate-700">
                                                {formatCurrency(reportData.saldoTotal)}
                                            </td>
                                            <td></td>
                                        </tr>
                                    </tfoot>
                                </table>
                            </div>

                            {/* DASHBOARD DE EDADES (AGING) */}
                            {reportData.edades && (
                                <div className="p-6 bg-gray-50 border-t border-gray-200">
                                    <h3 className="text-sm font-bold text-gray-500 uppercase mb-4">Análisis de Vencimientos (Aging)</h3>
                                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                                        <div className="bg-green-100 p-4 rounded-xl border border-green-200 text-center">
                                            <p className="text-xs font-bold text-green-700 uppercase">Por Vencer</p>
                                            <p className="text-lg font-bold text-green-900 font-mono mt-1">{formatCurrency(reportData.edades.por_vencer)}</p>
                                        </div>
                                        <div className="bg-yellow-50 p-4 rounded-xl border border-yellow-200 text-center">
                                            <p className="text-xs font-bold text-yellow-700 uppercase">1-30 Días</p>
                                            <p className="text-lg font-bold text-yellow-900 font-mono mt-1">{formatCurrency(reportData.edades.vencida_1_30)}</p>
                                        </div>
                                        <div className="bg-orange-50 p-4 rounded-xl border border-orange-200 text-center">
                                            <p className="text-xs font-bold text-orange-700 uppercase">31-60 Días</p>
                                            <p className="text-lg font-bold text-orange-900 font-mono mt-1">{formatCurrency(reportData.edades.vencida_31_60)}</p>
                                        </div>
                                        <div className="bg-red-50 p-4 rounded-xl border border-red-200 text-center">
                                            <p className="text-xs font-bold text-red-700 uppercase">61-90 Días</p>
                                            <p className="text-lg font-bold text-red-900 font-mono mt-1">{formatCurrency(reportData.edades.vencida_61_90)}</p>
                                        </div>
                                        <div className="bg-rose-100 p-4 rounded-xl border border-rose-200 text-center">
                                            <p className="text-xs font-bold text-rose-900 uppercase">+90 Días</p>
                                            <p className="text-lg font-bold text-rose-900 font-mono mt-1">{formatCurrency(reportData.edades.vencida_mas_90)}</p>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </>
    );
}

export default function EstadoCuentaClientePage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-6 text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
                <p className="mt-4 text-gray-600 font-semibold">Cargando estado de cuenta...</p>
            </div>
        }>
            <EstadoCuentaClienteContent />
        </Suspense>
    );
}