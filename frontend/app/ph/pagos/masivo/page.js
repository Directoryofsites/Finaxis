'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { useRecaudos } from '../../../../contexts/RecaudosContext';
import { phService } from '../../../../lib/phService';
import ManualButton from '../../../components/ManualButton';
import { 
    FaMoneyBillWave, 
    FaBuilding, 
    FaCheckSquare, 
    FaRegSquare, 
    FaPlay, 
    FaHistory, 
    FaInfoCircle, 
    FaExclamationTriangle,
    FaArrowLeft,
    FaCheckCircle,
    FaArrowRight
} from 'react-icons/fa';
import Link from 'next/link';

// Estilos
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none";

export default function RecaudosMasivosPage() {
    const { user, loading: authLoading } = useAuth();
    const { labels } = useRecaudos();

    // ESTADOS
    const [loading, setLoading] = useState(true);
    const [processing, setProcessing] = useState(false);
    const [torres, setTorres] = useState([]);
    const [unidades, setUnidades] = useState([]);
    const [error, setError] = useState(null);
    const [resultado, setResultado] = useState(null);

    // FILTROS
    const [selectedTorreId, setSelectedTorreId] = useState('');
    const [selectedUnidades, setSelectedUnidades] = useState([]);

    // PARÁMETROS DE PAGO
    const [pagoParams, setPagoParams] = useState({
        fecha: new Date().toISOString().slice(0, 10),
        monto_tipo: 'SALDO_TOTAL', // 'SALDO_TOTAL' o 'MONTO_FIJO'
        monto_fijo: '',
        forma_pago_id: ''
    });

    useEffect(() => {
        if (!authLoading && user?.empresaId) {
            initData();
        }
    }, [authLoading, user]);

    const initData = async () => {
        try {
            setLoading(true);
            const [torresData] = await Promise.all([
                phService.getTorres()
            ]);
            setTorres(torresData);
        } catch (err) {
            setError("Error cargando torres.");
        } finally {
            setLoading(false);
        }
    };

    // Al cambiar la torre, cargar unidades y sus deudas
    useEffect(() => {
        if (selectedTorreId) {
            loadUnidades(selectedTorreId);
        } else {
            setUnidades([]);
            setSelectedUnidades([]);
        }
    }, [selectedTorreId]);

    const loadUnidades = async (torreId) => {
        try {
            setLoading(true);
            // Obtenemos unidades de la torre
            const data = await phService.getUnidades({ torre_id: torreId });
            
            // Para que se vea premium, cargamos dinámicamente el saldo de cada una?
            // NOTA: Como el usuario pidió "agilizar", esto debe ser rápido. 
            // Si el backend es rápido, podemos mapear deudas aquí.
            setUnidades(data);
            setSelectedUnidades(data.map(u => u.id)); // Por defecto todas seleccionadas
        } catch (err) {
            setError("Error cargando unidades.");
        } finally {
            setLoading(false);
        }
    };

    const toggleUnidad = (id) => {
        setSelectedUnidades(prev => 
            prev.includes(id) ? prev.filter(uid => uid !== id) : [...prev, id]
        );
    };

    const handleSelectAll = () => {
        if (selectedUnidades.length === unidades.length) {
            setSelectedUnidades([]);
        } else {
            setSelectedUnidades(unidades.map(u => u.id));
        }
    };

    const handleProcessPayments = async () => {
        if (selectedUnidades.length === 0) return alert("Seleccione al menos una unidad.");
        if (pagoParams.monto_tipo === 'MONTO_FIJO' && !pagoParams.monto_fijo) return alert("Ingrese el monto fijo.");

        if (!confirm(`¿Está seguro de procesar ${selectedUnidades.length} recaudos de forma masiva?`)) return;

        try {
            setProcessing(true);
            setError(null);
            
            const payload = {
                unidades_ids: selectedUnidades,
                fecha: pagoParams.fecha,
                pagar_saldo_total: pagoParams.monto_tipo === 'SALDO_TOTAL',
                monto_fijo: pagoParams.monto_tipo === 'MONTO_FIJO' ? parseFloat(pagoParams.monto_fijo) : null,
                observaciones: "Pago masivo procesado desde panel de gestión."
            };

            const res = await phService.registrarPagoMasivo(payload);
            setResultado(res);
            
            // Limpiar selección tras éxito
            if (res.procesados > 0) {
                // Opcional: Recargar deudas o volver al inicio
            }
        } catch (err) {
            setError("Error procesando pagos. Verifique la conexión.");
            console.error(err);
        } finally {
            setProcessing(false);
        }
    };

    if (authLoading) return null;

    return (
        <div className="min-h-screen bg-gray-50 p-6 pb-20">
            <div className="max-w-6xl mx-auto">
                
                {/* HEAD */}
                <div className="flex justify-between items-center mb-8">
                    <div className="flex items-center gap-4">
                        <Link href="/ph/facturacion" className="p-2 hover:bg-white rounded-full transition-colors text-gray-400 hover:text-indigo-600">
                            <FaArrowLeft />
                        </Link>
                        <div>
                            <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-3">
                                <FaMoneyBillWave className="text-indigo-600" /> Recaudos Masivos
                            </h1>
                            <p className="text-gray-500 text-sm">Procese múltiples recibos de caja en un solo bloque por torre o zona.</p>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    
                    {/* PANEL DE FILTROS Y PARÁMETROS */}
                    <div className="lg:col-span-1 space-y-6">
                        
                        {/* SECTOR 1: ORIGEN */}
                        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                            <h3 className="font-bold text-gray-700 flex items-center gap-2 mb-4">
                                <FaBuilding className="text-indigo-500" /> 1. Origen del Pago
                            </h3>
                            <div className="space-y-4">
                                <div>
                                    <label className={labelClass}>Seleccionar {labels?.torre || 'Torre/Bloque'}</label>
                                    <select 
                                        value={selectedTorreId} 
                                        onChange={(e) => setSelectedTorreId(e.target.value)}
                                        className={inputClass}
                                    >
                                        <option value="">-- Seleccionar --</option>
                                        {torres.map(t => (
                                            <option key={t.id} value={t.id}>{t.nombre}</option>
                                        ))}
                                    </select>
                                </div>
                                <div className="p-3 bg-blue-50 border border-blue-100 rounded-lg flex items-start gap-3">
                                    <FaInfoCircle className="text-blue-500 mt-1" />
                                    <p className="text-xs text-blue-700">El pago se distribuirá entre las unidades activas del sector seleccionado.</p>
                                </div>
                            </div>
                        </div>

                        {/* SECTOR 2: CONFIGURACIÓN PAGO */}
                        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                            <h3 className="font-bold text-gray-700 flex items-center gap-2 mb-4">
                                <FaCheckSquare className="text-indigo-500" /> 2. Reglas de Liquidación
                            </h3>
                            <div className="space-y-4">
                                <div>
                                    <label className={labelClass}>Fecha de los Recibos</label>
                                    <input 
                                        type="date" 
                                        value={pagoParams.fecha} 
                                        onChange={(e) => setPagoParams({...pagoParams, fecha: e.target.value})}
                                        className={inputClass}
                                    />
                                </div>
                                
                                <div className="pt-2">
                                    <label className={labelClass}>¿Cómo se liquida el monto?</label>
                                    <div className="space-y-2 mt-2">
                                        <button 
                                            onClick={() => setPagoParams({...pagoParams, monto_tipo: 'SALDO_TOTAL'})}
                                            className={`w-full text-left px-4 py-3 rounded-xl border-2 transition-all flex items-center justify-between group ${pagoParams.monto_tipo === 'SALDO_TOTAL' ? 'border-indigo-600 bg-indigo-50 text-indigo-700' : 'border-gray-100 hover:border-gray-200'}`}
                                        >
                                            <div className="flex items-center gap-3">
                                                <div className={`p-2 rounded-lg ${pagoParams.monto_tipo === 'SALDO_TOTAL' ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-400'}`}>
                                                    <FaCheckCircle className="text-xs" />
                                                </div>
                                                <span className="font-bold text-sm">Pagar Saldo Total</span>
                                            </div>
                                        </button>

                                        <button 
                                            onClick={() => setPagoParams({...pagoParams, monto_tipo: 'MONTO_FIJO'})}
                                            className={`w-full text-left px-4 py-3 rounded-xl border-2 transition-all group ${pagoParams.monto_tipo === 'MONTO_FIJO' ? 'border-indigo-600 bg-indigo-50 text-indigo-700' : 'border-gray-100 hover:border-gray-200'}`}
                                        >
                                            <div className="flex items-center gap-3 mb-2">
                                                <div className={`p-2 rounded-lg ${pagoParams.monto_tipo === 'MONTO_FIJO' ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-400'}`}>
                                                    <FaMoneyBillWave className="text-xs" />
                                                </div>
                                                <span className="font-bold text-sm">Valor Fijo para todos</span>
                                            </div>
                                            {pagoParams.monto_tipo === 'MONTO_FIJO' && (
                                                <input 
                                                    type="number" 
                                                    placeholder="Ej: 150000"
                                                    value={pagoParams.monto_fijo}
                                                    onChange={(e) => setPagoParams({...pagoParams, monto_fijo: e.target.value})}
                                                    className="w-full bg-white border border-indigo-200 rounded-lg px-3 py-2 text-sm outline-none shadow-inner"
                                                    onClick={(e) => e.stopPropagation()}
                                                />
                                            )}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* BTN ACCIÓN */}
                        <button 
                            disabled={processing || !selectedTorreId || selectedUnidades.length === 0}
                            onClick={handleProcessPayments}
                            className={`w-full py-4 rounded-2xl flex items-center justify-center gap-3 font-bold text-lg shadow-lg transition-all ${
                                processing || !selectedTorreId || selectedUnidades.length === 0 
                                ? 'bg-gray-300 text-gray-500 cursor-not-allowed shadow-none' 
                                : 'bg-indigo-600 text-white hover:bg-indigo-700 shadow-indigo-200'
                            }`}
                        >
                            {processing ? "Procesando ráfaga de pagos..." : `PROCESAR ${selectedUnidades.length} PAGOS`}
                        </button>
                    </div>

                    {/* PANEL DE LISTADO DE UNIDADES */}
                    <div className="lg:col-span-2">
                        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden h-full flex flex-col">
                            
                            <div className="p-6 bg-gray-50 border-b flex justify-between items-center">
                                <div>
                                    <h3 className="font-bold text-gray-700">Selección de Unidades</h3>
                                    <p className="text-xs text-gray-500">Marque las unidades que realizaron el pago.</p>
                                </div>
                                {unidades.length > 0 && (
                                    <button 
                                        onClick={handleSelectAll}
                                        className="text-xs font-bold text-indigo-600 hover:text-indigo-800 flex items-center gap-2 px-3 py-1 bg-indigo-50 rounded-full transition-colors"
                                    >
                                        {selectedUnidades.length === unidades.length ? <><FaCheckSquare /> Desmarcar Todo</> : <><FaRegSquare /> Seleccionar Todo</>}
                                    </button>
                                )}
                            </div>

                            <div className="flex-1 overflow-y-auto p-4 custom-scrollbar min-h-[400px]">
                                {!selectedTorreId ? (
                                    <div className="h-full flex flex-col items-center justify-center text-gray-400 opacity-60">
                                        <FaBuilding className="text-6xl mb-4" />
                                        <p className="font-bold">Seleccione un sector para cargar unidades.</p>
                                    </div>
                                ) : loading ? (
                                    <div className="h-full flex items-center justify-center">
                                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                                    </div>
                                ) : (
                                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                                        {unidades.map(u => (
                                            <div 
                                                key={u.id}
                                                onClick={() => toggleUnidad(u.id)}
                                                className={`p-4 rounded-xl border-2 cursor-pointer transition-all flex items-center gap-3 ${
                                                    selectedUnidades.includes(u.id) 
                                                    ? 'border-indigo-600 bg-indigo-50 shadow-sm' 
                                                    : 'border-gray-50 bg-white hover:border-gray-200 opacity-60'
                                                }`}
                                            >
                                                <div className={`text-xl ${selectedUnidades.includes(u.id) ? 'text-indigo-600' : 'text-gray-300'}`}>
                                                    {selectedUnidades.includes(u.id) ? <FaCheckSquare /> : <FaRegSquare />}
                                                </div>
                                                <div>
                                                    <p className="font-bold text-gray-800">{u.codigo}</p>
                                                    <p className="text-[10px] text-gray-400 uppercase truncate max-w-[120px]">
                                                        {u.propietario_nombre || 'Sin Propietario'}
                                                    </p>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* RESUMEN RESULTADO */}
                            {resultado && (
                                <div className="absolute inset-0 bg-white bg-opacity-95 flex items-center justify-center p-8 z-10 transition-all">
                                    <div className="bg-white p-8 rounded-3xl shadow-xl border border-gray-100 max-w-md w-full text-center">
                                        <div className="w-20 h-20 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-6 text-3xl">
                                            <FaCheckCircle />
                                        </div>
                                        <h2 className="text-2xl font-bold text-gray-800 mb-2">¡Lote Procesado!</h2>
                                        <div className="grid grid-cols-2 gap-4 my-6">
                                            <div className="bg-green-50 p-4 rounded-2xl">
                                                <p className="text-2xl font-bold text-green-600">{resultado.procesados}</p>
                                                <p className="text-[10px] font-bold text-green-700 uppercase">Éxitos</p>
                                            </div>
                                            <div className="bg-red-50 p-4 rounded-2xl">
                                                <p className="text-2xl font-bold text-red-600">{resultado.errores}</p>
                                                <p className="text-[10px] font-bold text-red-700 uppercase">Errores</p>
                                            </div>
                                        </div>
                                        <button 
                                            onClick={() => setResultado(null)}
                                            className="w-full bg-gray-800 text-white py-4 rounded-2xl font-bold hover:bg-black transition-colors"
                                        >
                                            Cerrar Resumen
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {error && (
                    <div className="mt-8 p-4 bg-red-50 border border-red-100 text-red-700 rounded-xl flex items-center gap-3">
                        <FaExclamationTriangle />
                        {error}
                    </div>
                )}
            </div>
        </div>
    );
}
