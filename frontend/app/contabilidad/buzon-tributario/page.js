'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
    FaInbox, FaCog, FaCheckCircle, FaSpinner,
    FaEnvelope, FaLock, FaDatabase, FaListOl,
    FaFileInvoiceDollar, FaCheck, FaExclamationTriangle,
    FaSyncAlt
} from 'react-icons/fa';
import { apiService } from '../../../lib/apiService';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { useAuth } from '../../context/AuthContext';

export default function BuzonTributarioPage() {
    const router = useRouter();
    const { user, loading: authLoading } = useAuth();

    const [activeTab, setActiveTab] = useState('parametros'); // 'parametros' | 'escanear'

    // Parámetros State
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [tipoDocumentoId, setTipoDocumentoId] = useState('');
    const [cuentaGastoId, setCuentaGastoId] = useState('');
    const [cuentaCajaId, setCuentaCajaId] = useState('');
    const [configId, setConfigId] = useState(null); // Para saber si ya existe config

    // Catalogos
    const [tiposDocumentos, setTiposDocumentos] = useState([]);
    const [cuentasGasto, setCuentasGasto] = useState([]);
    const [cuentasCaja, setCuentasCaja] = useState([]);

    // UI States
    const [isLoadingData, setIsLoadingData] = useState(true);
    const [isSavingConfig, setIsSavingConfig] = useState(false);
    const [isScanning, setIsScanning] = useState(false);

    // Resultados del Escaneo
    const [scanResults, setScanResults] = useState(null);

    useEffect(() => {
        if (authLoading) return;
        if (!user) { router.push('/login'); return; }
        loadInitialData();
    }, [user, authLoading, router]);

    const loadInitialData = async () => {
        setIsLoadingData(true);
        try {
            // Cargar Catálogos
            const [tdRes, cRes] = await Promise.all([
                apiService.get('/tipos-documento'),
                apiService.get('/plan-cuentas/list-flat?permite_movimiento=true')
            ]);

            const filtrados = tdRes.data || [];
            setTiposDocumentos(filtrados);

            const fl = cRes.data || [];
            setCuentasGasto(fl.filter(c => c.codigo.startsWith('5') || c.codigo.startsWith('6') || c.codigo.startsWith('7')));
            setCuentasCaja(fl.filter(c => c.codigo.startsWith('11') || c.codigo.startsWith('23')));

            // Cargar Configuración Persistente
            try {
                const configRes = await apiService.get('/buzon-tributario/config');
                if (configRes.data && configRes.data.id) {
                    const cfg = configRes.data;
                    setConfigId(cfg.id);
                    setEmail(cfg.email_addr || '');
                    setPassword(cfg.password_app_masked || ''); // Viene enmascarada del backend
                    setTipoDocumentoId(cfg.tipo_documento_id ? String(cfg.tipo_documento_id) : '');
                    setCuentaGastoId(cfg.cuenta_gasto_id ? String(cfg.cuenta_gasto_id) : '');
                    setCuentaCajaId(cfg.cuenta_caja_id ? String(cfg.cuenta_caja_id) : '');
                }
            } catch (errConfig) {
                // Puede ser 404 si no hay config aún. No es un error crítico.
                console.log("No config found or error fetching config", errConfig);
            }

        } catch (error) {
            console.error(error);
            toast.error("Error al cargar configuración y catálogos.");
        } finally {
            setIsLoadingData(false);
        }
    };

    const handleSaveConfig = async (e) => {
        e.preventDefault();
        setIsSavingConfig(true);
        try {
            const payload = {
                email_addr: email,
                password_app: password,
                tipo_documento_id: tipoDocumentoId ? parseInt(tipoDocumentoId) : null,
                cuenta_gasto_id: cuentaGastoId ? parseInt(cuentaGastoId) : null,
                cuenta_caja_id: cuentaCajaId ? parseInt(cuentaCajaId) : null,
            };

            const res = await apiService.post('/buzon-tributario/config', payload);
            toast.success("Configuración guardada exitosamente.");

            if (res.data && res.data.id) {
                setConfigId(res.data.id);
                // Si guardamos, pasamos a la pestaña escanear automáticamente
                setActiveTab('escanear');
            }
        } catch (err) {
            console.error("Error saving config:", err);
            toast.error(err.response?.data?.detail || "No se pudo guardar la configuración.");
        } finally {
            setIsSavingConfig(false);
        }
    };

    const handleScan = async () => {
        // Enviar sincronización usando los parámetros persistidos en DB.
        // Solo mandamos un payload vacío para que el backend use los defaults de la BD.
        setIsScanning(true);
        setScanResults(null);
        try {
            // El backend fue adaptado para usar EmpresaConfigBuzon si no se pasan parámetros.
            const res = await apiService.post('/buzon-tributario/sincronizar', {});
            toast.success(`¡Escaneo finalizado! ${res.data.procesadas} nuevas facturas procesadas.`);
            setScanResults(res.data);
        } catch (err) {
            console.error("Error al sincronizar buzón:", err);
            const msg = err.response?.data?.detail || "Error en el servidor al leer el correo.";
            toast.error(msg);
        } finally {
            setIsScanning(false);
        }
    };

    if (authLoading || isLoadingData) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
                <FaInbox className="text-indigo-300 text-6xl mb-4 animate-pulse" />
                <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando Buzón Tributario...</p>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans">
            <ToastContainer position="top-right" autoClose={5000} />
            <div className="max-w-5xl mx-auto">
                {/* ENCABEZADO */}
                <div className="mb-8">
                    <div className="flex items-center gap-3 mt-3">
                        <div className="p-3 bg-indigo-100 rounded-xl text-indigo-600 shadow-sm">
                            <FaInbox className="text-3xl" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-extrabold text-gray-800 tracking-tight">
                                Buzón Tributario
                            </h1>
                            <p className="text-gray-500 text-sm mt-1">Automatización de registro de compras leyendo facturas electrónicas desde su correo.</p>
                        </div>
                    </div>
                </div>

                {/* TABS COMPONENT */}
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                    <div className="flex border-b border-gray-100 bg-gray-50/50">
                        <button
                            onClick={() => setActiveTab('parametros')}
                            className={`flex flex-1 items-center justify-center gap-2 py-4 px-6 text-sm font-bold uppercase tracking-wider transition-colors ${activeTab === 'parametros'
                                ? 'bg-white text-indigo-600 border-b-2 border-indigo-600 shadow-sm'
                                : 'text-gray-500 hover:text-indigo-500 hover:bg-white/60'
                                }`}
                        >
                            <FaCog className="text-lg" /> Parámetros
                        </button>
                        <button
                            onClick={() => setActiveTab('escanear')}
                            className={`flex flex-1 items-center justify-center gap-2 py-4 px-6 text-sm font-bold uppercase tracking-wider transition-colors ${activeTab === 'escanear'
                                ? 'bg-white text-emerald-600 border-b-2 border-emerald-600 shadow-sm'
                                : 'text-gray-500 hover:text-emerald-500 hover:bg-white/60'
                                }`}
                        >
                            <FaSyncAlt className={`${isScanning ? 'animate-spin' : ''} text-lg`} /> Escanear Buzón
                        </button>
                    </div>

                    <div className="p-6 md:p-8">
                        {/* CONTENIDO: PARÁMETROS */}
                        {activeTab === 'parametros' && (
                            <form onSubmit={handleSaveConfig} className="animate-fadeIn">
                                <div className="mb-6 bg-indigo-50 border border-indigo-100 p-4 rounded-xl flex gap-4">
                                    <div className="mt-1">
                                        <FaDatabase className="text-indigo-400 text-xl" />
                                    </div>
                                    <div className="text-sm text-indigo-900">
                                        <p className="font-bold mb-1">Configuración Persistente</p>
                                        <p>Guarde la cuenta de correo y la clave de aplicación IMAP (Ej. Gmail App Passwords). Estos datos quedarán almacenados de manera segura en el sistema para que no tenga que digitarlos en cada escaneo futuro. También fije las cuentas contables por defecto a afectar.</p>
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    {/* Credenciales */}
                                    <div className="space-y-4">
                                        <h3 className="font-bold text-gray-700 border-b pb-2 flex items-center gap-2">
                                            <span className="bg-indigo-100 text-indigo-600 w-6 h-6 flex items-center justify-center rounded-full text-xs">1</span>
                                            Credenciales de Acceso
                                        </h3>
                                        <div>
                                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Correo de Recepción DIAN</label>
                                            <div className="relative">
                                                <FaEnvelope className="absolute left-3 top-3 text-gray-400" />
                                                <input type="email" value={email} onChange={e => setEmail(e.target.value)} required className="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-colors" placeholder="facturacion@empresa.com" />
                                            </div>
                                        </div>
                                        <div>
                                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Clave de Aplicación (Gmail / IMAP)</label>
                                            <div className="relative">
                                                <FaLock className="absolute left-3 top-3 text-gray-400" />
                                                <input type="password" value={password} onChange={e => setPassword(e.target.value)} required placeholder={configId ? "******** (Clave guardada previamente)" : "ej: dscq zies jsrh oxiy"} className="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-colors" />
                                            </div>
                                            <p className="text-xs text-gray-400 mt-1 italic">Si ya fue guardada, no es necesario volver a digitarla a menos que cambie.</p>
                                        </div>
                                    </div>

                                    {/* Contabilidad Base */}
                                    <div className="space-y-4">
                                        <h3 className="font-bold text-gray-700 border-b pb-2 flex items-center gap-2">
                                            <span className="bg-indigo-100 text-indigo-600 w-6 h-6 flex items-center justify-center rounded-full text-xs">2</span>
                                            Parámetros Contables Base
                                        </h3>
                                        <div>
                                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Tipo de Documento (Para asentar la compra)</label>
                                            <select value={tipoDocumentoId} onChange={e => setTipoDocumentoId(e.target.value)} required className="w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-colors">
                                                <option value="">Seleccione tipo...</option>
                                                {tiposDocumentos.map(t => <option key={t.id} value={t.id}>{t.nombre}</option>)}
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Cuenta de Gasto (Débito Base)</label>
                                            <select value={cuentaGastoId} onChange={e => setCuentaGastoId(e.target.value)} required className="w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-colors">
                                                <option value="">Seleccione gasto general...</option>
                                                {cuentasGasto.map(c => <option key={c.id} value={c.id}>({c.codigo}) {c.nombre}</option>)}
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Cuenta de Contrapartida (Crédito - Caja/CXP)</label>
                                            <select value={cuentaCajaId} onChange={e => setCuentaCajaId(e.target.value)} required className="w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-colors">
                                                <option value="">Seleccione caja o pasivo...</option>
                                                {cuentasCaja.map(c => <option key={c.id} value={c.id}>({c.codigo}) {c.nombre}</option>)}
                                            </select>
                                        </div>
                                    </div>
                                </div>

                                <div className="mt-8 flex justify-end">
                                    <button
                                        type="submit"
                                        disabled={isSavingConfig}
                                        className="px-6 py-3 bg-indigo-600 text-white rounded-xl font-bold shadow-md hover:bg-indigo-700 hover:shadow-lg transition-all flex items-center gap-2 disabled:bg-indigo-300"
                                    >
                                        {isSavingConfig ? <FaSpinner className="animate-spin" /> : <FaCog />} Guardar Parámetros
                                    </button>
                                </div>
                            </form>
                        )}

                        {/* CONTENIDO: ESCANEAR */}
                        {activeTab === 'escanear' && (
                            <div className="animate-fadeIn space-y-8">
                                {!configId ? (
                                    <div className="text-center p-12 bg-amber-50 rounded-2xl border border-amber-200">
                                        <FaExclamationTriangle className="text-4xl text-amber-500 mx-auto mb-4" />
                                        <h3 className="text-xl font-bold text-amber-800 mb-2">Faltan Parámetros</h3>
                                        <p className="text-amber-700 mb-6">Primero debe configurar el correo y las cuentas contables en la pestaña "Parámetros" antes de escanear.</p>
                                        <button
                                            onClick={() => setActiveTab('parametros')}
                                            className="px-6 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors font-bold"
                                        >
                                            Ir a Parámetros
                                        </button>
                                    </div>
                                ) : (
                                    <div className="flex flex-col items-center justify-center p-8 bg-emerald-50/50 rounded-3xl border border-emerald-100">
                                        <div className="text-center max-w-lg mb-8">
                                            <div className="w-24 h-24 bg-white rounded-full shadow-md flex items-center justify-center mx-auto mb-6 text-emerald-500 border border-emerald-100">
                                                <FaInbox className="text-4xl" />
                                            </div>
                                            <h2 className="text-2xl font-black text-emerald-800 mb-3">Listo para Iniciar</h2>
                                            <p className="text-emerald-700/80">Al escanear, el asistente leerá todos los correos entrantes mediante IMAP filtrando adjuntos UBL 2.1 (.xml), identificará los proveedores y causará el gasto automáticamente sin afectar el inventario.</p>
                                        </div>

                                        <button
                                            onClick={handleScan}
                                            disabled={isScanning}
                                            className={`group relative overflow-hidden px-12 py-5 rounded-full font-black text-xl text-white shadow-xl transition-all duration-300 transform ${isScanning ? 'bg-emerald-400 cursor-wait scale-95' : 'bg-emerald-600 hover:bg-emerald-500 hover:scale-105 hover:shadow-emerald-500/30'}`}
                                        >
                                            {isScanning && (
                                                <div className="absolute inset-0 flex items-center justify-center bg-black/20 z-10">
                                                    <FaSpinner className="animate-spin text-3xl" />
                                                </div>
                                            )}
                                            <span className={`flex items-center gap-3 relative z-0 ${isScanning ? 'opacity-30' : ''}`}>
                                                <FaSyncAlt className={`${isScanning ? 'animate-spin' : 'group-hover:rotate-180 transition-transform duration-500'}`} />
                                                EJECUTAR ESCANEO AHORA
                                            </span>
                                        </button>
                                    </div>
                                )}

                                {/* ZONA DE RESULTADOS CON INTELIGENCIA */}
                                {scanResults && (
                                    <div className="mt-8 pt-8 border-t border-gray-100 animate-slideUp">
                                        <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                                            <FaListOl className="text-indigo-500" /> Resultados del Escaneo
                                        </h3>

                                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                                            <div className="bg-white p-5 border border-emerald-100 rounded-2xl shadow-sm border-l-4 border-l-emerald-500">
                                                <p className="text-sm font-bold text-gray-500 uppercase tracking-wide">Importadas</p>
                                                <p className="text-3xl font-black text-emerald-600 mt-1">{scanResults.procesadas}</p>
                                            </div>
                                            <div className="bg-white p-5 border border-indigo-100 rounded-2xl shadow-sm border-l-4 border-l-indigo-500">
                                                <p className="text-sm font-bold text-gray-500 uppercase tracking-wide">Total Correos Leídos</p>
                                                <p className="text-3xl font-black text-indigo-600 mt-1">{scanResults.total_correos}</p>
                                            </div>
                                        </div>

                                        <div className="bg-white border text-sm border-gray-200 rounded-xl overflow-hidden shadow-sm">
                                            <div className="px-5 py-3 bg-gray-50 border-b border-gray-200 font-bold text-gray-600 flex gap-2 items-center">
                                                <FaFileInvoiceDollar /> Detalle de Documentos Creados
                                            </div>
                                            {scanResults.detalle && scanResults.detalle.length > 0 ? (
                                                <table className="min-w-full divide-y divide-gray-200">
                                                    <thead className="bg-white">
                                                        <tr>
                                                            <th className="px-5 py-3 text-left font-bold text-gray-500 uppercase">Documento #</th>
                                                            <th className="px-5 py-3 text-left font-bold text-gray-500 uppercase">Proveedor</th>
                                                            <th className="px-5 py-3 text-right font-bold text-gray-500 uppercase">Total XML</th>
                                                            <th className="px-5 py-3 text-center font-bold text-gray-500 uppercase">Estado</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody className="bg-white divide-y divide-gray-100 font-medium text-gray-700">
                                                        {scanResults.detalle.map((comp, idx) => (
                                                            <tr key={idx} className="hover:bg-blue-50/50 transition-colors">
                                                                <td className="px-5 py-3">{comp.numero}</td>
                                                                <td className="px-5 py-3 flex flex-col">
                                                                    <span>{comp.proveedor}</span>
                                                                    <span className="text-xs text-gray-400 font-normal">NIT: {comp.nit}</span>
                                                                </td>
                                                                <td className="px-5 py-3 text-right text-emerald-600 font-bold">
                                                                    ${comp.total.toLocaleString()}
                                                                </td>
                                                                <td className="px-5 py-3 text-center">
                                                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold leading-5 bg-green-100 text-green-800 border border-green-200">
                                                                        <FaCheck className="mr-1" /> Importado
                                                                    </span>
                                                                </td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            ) : (
                                                <div className="p-8 flex flex-col items-center justify-center text-gray-400 bg-gray-50/50">
                                                    <FaInbox className="text-4xl mb-3 opacity-50" />
                                                    <p>No se encontraron nuevas facturas para procesar o todas las que estaban ya han sido contabilizadas previamente en base de datos.</p>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
