'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';

import { phService } from '../../../lib/phService';
import { FaMoneyBillWave, FaUser, FaBuilding, FaCheckCircle, FaExclamationTriangle, FaCalendarAlt } from 'react-icons/fa';
import { useRecaudos } from '../../../contexts/RecaudosContext'; // IMPORT

export default function PagosPHPage() {
    const { user, loading: authLoading } = useAuth();
    const { labels } = useRecaudos(); // HOOK

    // Estados
    const [paymentMode, setPaymentMode] = useState('UNIT'); // 'UNIT' | 'OWNER'
    const [unidades, setUnidades] = useState([]);
    const [propietarios, setPropietarios] = useState([]); // Nuevo: Lista de Propietarios
    const [torres, setTorres] = useState([]);

    // Seleccion
    const [selectedUnidadId, setSelectedUnidadId] = useState('');
    const [selectedPropietarioId, setSelectedPropietarioId] = useState(null);

    const [estadoCuenta, setEstadoCuenta] = useState(null);
    const [loadingData, setLoadingData] = useState(false);

    // Filtros
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedTorreId, setSelectedTorreId] = useState(null);

    const [pagoForm, setPagoForm] = useState({
        monto: '',
        fecha: new Date().toISOString().slice(0, 10)
    });
    const [processing, setProcessing] = useState(false);
    const [successMsg, setSuccessMsg] = useState('');
    const [errorMsg, setErrorMsg] = useState('');

    useEffect(() => {
        if (!authLoading) loadInitialData();
    }, [authLoading]);

    const loadInitialData = async () => {
        try {
            const [uData, tData, pData] = await Promise.all([
                phService.getUnidades(),
                phService.getTorres(),
                phService.getPropietarios() // Fetch Owners
            ]);
            setUnidades(uData);
            setTorres(tData);
            setPropietarios(pData);
        } catch (err) {
            console.error(err);
        }
    };

    // Lógica de Filtrado Unidades
    const unidadesFiltered = unidades.filter(u => {
        const matchesSearch = searchTerm === '' ||
            (u.codigo || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
            (u.propietario?.razon_social || '').toLowerCase().includes(searchTerm.toLowerCase());
        const matchesTower = selectedTorreId === null || u.torre_id === selectedTorreId;
        return matchesSearch && matchesTower;
    });

    // Lógica de Filtrado Propietarios
    const propietariosFiltered = propietarios.filter(p => {
        return searchTerm === '' ||
            (p.nombre || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
            (p.documento || '').includes(searchTerm);
    });

    // HANDLERS
    const handleUnidadSelect = async (uid) => {
        setPaymentMode('UNIT');
        setSelectedUnidadId(uid);
        setSelectedPropietarioId(null);
        resetState();

        if (uid) fetchEstadoCuenta('UNIT', uid);
    };

    const handlePropietarioSelect = async (pid) => {
        setPaymentMode('OWNER');
        setSelectedPropietarioId(pid);
        setSelectedUnidadId(null);
        resetState();

        if (pid) fetchEstadoCuenta('OWNER', pid);
    };

    const resetState = () => {
        setEstadoCuenta(null);
        setSuccessMsg('');
        setErrorMsg('');
        setPagoForm(prev => ({ ...prev, monto: '' }));
    };

    const fetchEstadoCuenta = async (mode, id) => {
        setLoadingData(true);
        try {
            let data;
            if (mode === 'UNIT') {
                data = await phService.getEstadoCuenta(id);
                // Data: { saldo_total, facturas_pendientes... }
            } else {
                data = await phService.getEstadoCuentaPropietario(id);
                // Data: { saldo_total_consolidado, desglose_por_unidad... }
                // Mapeamos para que la UI lo entienda uniformemente
                data.saldo_total = data.saldo_total_consolidado; // Alias
                data.propietario_nombre = data.propietario.nombre;
                data.unidad = `(Todas las Unidades)`;
            }

            setEstadoCuenta(data);
            if (data.saldo_total > 0) {
                setPagoForm(prev => ({ ...prev, monto: data.saldo_total }));
            }
        } catch (err) {
            setErrorMsg('Error consultando estado de cuenta.');
        } finally {
            setLoadingData(false);
        }
    };

    // --- MODAL RECALCULO ---
    const [showRecalculoModal, setShowRecalculoModal] = useState(false);
    const [recalculoData, setRecalculoData] = useState(null);
    const [recalculando, setRecalculando] = useState(false);
    const [recalculoResult, setRecalculoResult] = useState(null);

    const handlePagoSubmit = async (e) => {
        e.preventDefault();
        const entityName = paymentMode === 'UNIT' ? labels.unidad : 'Propietario';
        const confirmMsg = `¿Confirmar pago de $${Number(pagoForm.monto).toLocaleString()} para ${entityName}?`;

        if (!confirm(confirmMsg)) return;

        setProcessing(true);
        setErrorMsg('');
        setSuccessMsg('');
        setRecalculoResult(null);

        try {
            let res;
            if (paymentMode === 'UNIT') {
                res = await phService.registrarPago({
                    unidad_id: parseInt(selectedUnidadId),
                    monto: parseFloat(pagoForm.monto),
                    fecha: pagoForm.fecha
                });
            } else {
                // PAGO CONSOLIDADO
                res = await phService.registrarPagoConsolidado({
                    propietario_id: parseInt(selectedPropietarioId),
                    monto_total: parseFloat(pagoForm.monto),
                    fecha: pagoForm.fecha,
                    observaciones: "Pago Consolidado Web"
                });
                // Res: { total_recibos, detalle_pagos ... }
            }

            const msg = paymentMode === 'UNIT'
                ? 'Pago registrado exitosamente.'
                : `Pago consolidado exitoso. Se generaron ${res.total_recibos} recibos.`;

            setSuccessMsg(msg);

            // Recargar estado
            if (paymentMode === 'UNIT') fetchEstadoCuenta('UNIT', selectedUnidadId);
            else fetchEstadoCuenta('OWNER', selectedPropietarioId);

            setPagoForm(prev => ({ ...prev, monto: '' }));

            // Deteccion recálculo (Solo Unit Mode por ahora)
            if (paymentMode === 'UNIT' && false && res && res.sugerir_recalculo) {
                setRecalculoData({ unidad_id: parseInt(selectedUnidadId), fecha: pagoForm.fecha });
                setShowRecalculoModal(true);
            }

        } catch (err) {
            setErrorMsg(err.response?.data?.detail || 'Error registrando pago.');
        } finally {
            setProcessing(false);
        }
    };

    const handleRecalcular = async () => {
        if (!recalculoData) return;
        setRecalculando(true);
        try {
            const res = await phService.recalcularIntereses(recalculoData.unidad_id, recalculoData.fecha);
            setRecalculoResult(res);
            setSuccessMsg(`Pago registrado y se actualizaron ${res.actualizadas} facturas posteriores.`);
            setTimeout(() => setShowRecalculoModal(false), 3000);
        } catch (err) {
            alert("Error recalculando: " + (err.response?.data?.detail || err.message));
        } finally {
            setRecalculando(false);
        }
    };

    if (authLoading) return <p className="p-8 text-center">Cargando...</p>;

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20 relative">
            {/* MODAL RECALCULO */}
            {showRecalculoModal && (
                <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 animate-scaleIn border-t-4 border-indigo-500">
                        <div className="flex items-center gap-3 mb-4 text-indigo-700">
                            <FaExclamationTriangle className="text-3xl" />
                            <h3 className="text-xl font-bold">¡Pago Retroactivo Detectado!</h3>
                        </div>
                        <p className="text-gray-600 mb-6">
                            El pago tiene fecha anterior a este mes. Es posible que existan facturas posteriores con intereses de mora calculados sobre el saldo antiguo.
                            <br /><br />
                            <strong>¿Deseas recalcular automáticamente los intereses de las facturas futuras?</strong>
                        </p>

                        {recalculoResult ? (
                            <div className="bg-green-100 text-green-700 p-3 rounded mb-4">
                                <strong>¡Listo!</strong> Se actualizaron {recalculoResult.actualizadas} facturas.
                            </div>
                        ) : (
                            <div className="flex gap-3 justify-end">
                                <button
                                    onClick={() => setShowRecalculoModal(false)}
                                    className="px-4 py-2 text-gray-500 hover:bg-gray-100 rounded-lg font-bold"
                                    disabled={recalculando}
                                >
                                    No, dejar así
                                </button>
                                <button
                                    onClick={handleRecalcular}
                                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg font-bold hover:bg-indigo-700 shadow-lg flex items-center gap-2"
                                    disabled={recalculando}
                                >
                                    {recalculando ? 'Procesando...' : 'SÍ, RECALCULAR INTERESES'}
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            )}

            <div className="max-w-6xl mx-auto">
                <div className="mb-6">
                    <div className="flex items-center gap-3 mt-3">
                        <div className="p-2 bg-green-100 rounded-lg text-green-600">
                            <FaMoneyBillWave className="text-2xl" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold text-gray-800">Recaudos y Pagos {labels.module}</h1>
                            <p className="text-gray-500 text-sm">Gestión de recaudos por {labels.unidad} o consolidado por Propietario.</p>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
                    {/* SELECCIÓN Y FORMULARIO */}
                    <div className="md:col-span-4 bg-white p-6 rounded-xl shadow-sm border border-gray-100 h-fit cursor-default">

                        {/* MODE TOGGLE */}
                        <div className="flex bg-gray-100 p-1 rounded-lg mb-4">
                            <button
                                onClick={() => { setPaymentMode('UNIT'); setSearchTerm(''); }}
                                className={`flex-1 py-2 rounded-md text-sm font-bold transition-all ${paymentMode === 'UNIT' ? 'bg-white shadow text-indigo-600' : 'text-gray-500 hover:text-gray-700'}`}
                            >
                                Por {labels.unidad}
                            </button>
                            <button
                                onClick={() => { setPaymentMode('OWNER'); setSearchTerm(''); }}
                                className={`flex-1 py-2 rounded-md text-sm font-bold transition-all ${paymentMode === 'OWNER' ? 'bg-white shadow text-indigo-600' : 'text-gray-500 hover:text-gray-700'}`}
                            >
                                Por Propietario
                            </button>
                        </div>

                        <label className="block text-xs font-bold text-gray-500 uppercase mb-3 tracking-wide">
                            {paymentMode === 'UNIT' ? `1. Seleccione ${labels.unidad}` : '1. Seleccione Propietario'}
                        </label>

                        {/* BUSCADOR */}
                        <div className="relative mb-4">
                            <input
                                type="text"
                                placeholder={`Buscar...`}
                                value={searchTerm || ''}
                                onChange={e => { setSearchTerm(e.target.value); setSelectedTorreId(null); }}
                                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-green-500 outline-none transition-all"
                            />
                            <FaBuilding className="absolute left-3 top-3 text-gray-400" />
                        </div>

                        {/* FILTRO TORRES (SOLO UNIT MODE) */}
                        {paymentMode === 'UNIT' && torres.length > 0 && (
                            <div className="mb-4 overflow-x-auto pb-2">
                                <div className="flex gap-2 min-w-max">
                                    <button
                                        onClick={() => setSelectedTorreId(null)}
                                        className={`px-3 py-1 rounded-full text-xs border font-bold transition-all ${!selectedTorreId ? 'bg-gray-800 text-white' : 'bg-white text-gray-600 hover:bg-gray-100'}`}
                                    >
                                        TODAS
                                    </button>
                                    {torres.map(t => (
                                        <button
                                            key={t.id}
                                            onClick={() => { setSelectedTorreId(t.id); setSearchTerm(''); }}
                                            className={`px-3 py-1 rounded-full text-xs border flex items-center gap-1 transition-all ${selectedTorreId === t.id ? 'bg-green-600 text-white border-green-600 shadow-md' : 'bg-white text-gray-600 hover:bg-green-50'}`}
                                        >
                                            {t.nombre}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* LISTA DE RESULTADOS */}
                        <div className="mb-6 max-h-[300px] overflow-y-auto pr-1 grid grid-cols-1 gap-2">
                            {paymentMode === 'UNIT' ? (
                                unidadesFiltered.length === 0 ? <p className="text-center text-gray-400 text-sm py-4">No se encontraron unidades.</p> :
                                    unidadesFiltered.map(u => (
                                        <div
                                            key={u.id}
                                            onClick={() => handleUnidadSelect(u.id)}
                                            className={`p-3 rounded-lg border cursor-pointer transition-all flex justify-between items-center hover:scale-[1.02] ${selectedUnidadId == u.id
                                                ? 'bg-green-50 border-green-500 ring-1 ring-green-500'
                                                : 'bg-white border-gray-200 hover:border-green-300 hover:shadow-sm'
                                                }`}
                                        >
                                            <div>
                                                <div className={`font-bold text-sm ${selectedUnidadId == u.id ? 'text-green-700' : 'text-gray-700'}`}>{u.codigo}</div>
                                                <div className="text-[10px] text-gray-500 truncate mt-0.5">{u.propietario?.razon_social || 'Sin Propietario'}</div>
                                            </div>
                                            {selectedUnidadId == u.id && <FaCheckCircle className="text-green-500" />}
                                        </div>
                                    ))
                            ) : (
                                propietariosFiltered.length === 0 ? <p className="text-center text-gray-400 text-sm py-4">No se encontraron propietarios.</p> :
                                    propietariosFiltered.map(p => (
                                        <div
                                            key={p.id}
                                            onClick={() => handlePropietarioSelect(p.id)}
                                            className={`p-3 rounded-lg border cursor-pointer transition-all flex justify-between items-center hover:scale-[1.02] ${selectedPropietarioId == p.id
                                                ? 'bg-indigo-50 border-indigo-500 ring-1 ring-indigo-500'
                                                : 'bg-white border-gray-200 hover:border-indigo-300 hover:shadow-sm'
                                                }`}
                                        >
                                            <div>
                                                <div className={`font-bold text-sm ${selectedPropietarioId == p.id ? 'text-indigo-700' : 'text-gray-700'}`}>{p.nombre}</div>
                                                <div className="text-[10px] text-gray-500 truncate mt-0.5">{p.documento || 'Sin Documento'}</div>
                                            </div>
                                            {selectedPropietarioId == p.id && <FaCheckCircle className="text-indigo-500" />}
                                        </div>
                                    ))
                            )}
                        </div>

                        {estadoCuenta && (
                            <form onSubmit={handlePagoSubmit} className="space-y-4 pt-4 border-t border-dashed animate-fadeIn">
                                <h3 className="font-bold text-gray-700 flex items-center gap-2 text-sm uppercase">
                                    <FaMoneyBillWave className={paymentMode === 'UNIT' ? "text-green-500" : "text-indigo-500"} />
                                    {paymentMode === 'UNIT' ? 'Registrar Pago Individual' : 'Pago Consolidado'}
                                </h3>

                                <div>
                                    <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Fecha Pago</label>
                                    <input
                                        type="date"
                                        value={pagoForm.fecha}
                                        onChange={e => setPagoForm({ ...pagoForm, fecha: e.target.value })}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-green-500"
                                        required
                                    />
                                </div>

                                <div>
                                    <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Monto a Pagar</label>
                                    <div className="relative">
                                        <span className="absolute left-3 top-2 text-gray-400">$</span>
                                        <input
                                            type="number"
                                            value={pagoForm.monto}
                                            onChange={e => setPagoForm({ ...pagoForm, monto: e.target.value })}
                                            className="w-full pl-8 pr-4 py-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-green-500 font-bold text-lg text-green-700"
                                            placeholder="0"
                                            min="1"
                                            required
                                        />
                                    </div>
                                </div>

                                <button
                                    type="submit"
                                    disabled={processing}
                                    className={`w-full py-3 rounded-lg text-white font-bold shadow-md transition-all ${processing ? 'bg-gray-400' :
                                        paymentMode === 'UNIT' ? 'bg-green-600 hover:bg-green-700' : 'bg-indigo-600 hover:bg-indigo-700'
                                        } hover:scale-105`}
                                >
                                    {processing ? 'Procesando...' : (paymentMode === 'UNIT' ? 'REGISTRAR PAGO UNIDAD' : 'DISTRIBUIR PAGO')}
                                </button>
                            </form>
                        )}

                        {successMsg && <div className="mt-4 p-3 bg-green-50 text-green-700 text-sm rounded-lg border border-green-200">{successMsg}</div>}
                        {errorMsg && <div className="mt-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg border border-red-200 flex items-center gap-2"><FaExclamationTriangle /> {errorMsg}</div>}
                    </div>

                    {/* ESTADO DE CUENTA */}
                    <div className="md:col-span-8 space-y-6">
                        {loadingData && <div className="text-center py-10 text-gray-400">Cargando información...</div>}

                        {!loadingData && !estadoCuenta && (
                            <div className="bg-gray-100 rounded-xl p-10 text-center text-gray-400 border-2 border-dashed border-gray-200 h-full flex flex-col items-center justify-center">
                                <FaBuilding className="text-4xl mx-auto mb-2 opacity-50" />
                                <p>Seleccione {paymentMode === 'UNIT' ? `una ${labels.unidad.toLowerCase()}` : 'un propietario'} para continuar.</p>
                            </div>
                        )}

                        {!loadingData && estadoCuenta && (
                            <>
                                {/* RESUMEN */}
                                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 animate-slideUp">
                                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                                        <div>
                                            <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">{labels.propietario.toUpperCase()}</p>
                                            <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                                                <FaUser className="text-indigo-500" /> {estadoCuenta.propietario_nombre}
                                            </h2>
                                            <p className="text-sm text-gray-500 mt-1">{labels.unidad}: <span className="font-mono bg-gray-100 px-2 py-0.5 rounded">{estadoCuenta.unidad}</span></p>
                                        </div>
                                        <div className="text-right bg-red-50 p-4 rounded-lg border border-red-100 min-w-[250px]">
                                            <p className="text-xs font-bold text-red-400 uppercase tracking-wider">
                                                {paymentMode === 'UNIT' ? 'SALDO PENDIENTE' : 'DEUDA CONSOLIDADA'}
                                            </p>
                                            <p className="text-4xl font-bold text-red-600">${Number(estadoCuenta.saldo_total).toLocaleString()}</p>
                                        </div>
                                    </div>
                                </div>

                                {/* TABLA ESPECÍFICA SEGÚN MODO */}
                                {paymentMode === 'OWNER' && estadoCuenta.desglose_por_unidad && (
                                    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden animate-slideUp mb-6">
                                        <div className="p-4 border-b bg-indigo-50 flex justify-between items-center">
                                            <h3 className="font-bold text-indigo-800 text-sm uppercase">Desglose por Inmueble</h3>
                                        </div>
                                        <table className="w-full text-sm text-left">
                                            <thead className="text-xs text-gray-500 uppercase bg-gray-50 border-b">
                                                <tr>
                                                    <th className="px-6 py-3">{labels.unidad}</th>
                                                    <th className="px-6 py-3 text-right">Saldo Actual</th>
                                                    <th className="px-6 py-3 text-center">Estado</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-gray-100">
                                                {estadoCuenta.desglose_por_unidad.map((u, idx) => (
                                                    <tr key={idx} className={u.saldo > 0 ? 'bg-white' : 'bg-green-50'}>
                                                        <td className="px-6 py-4 font-bold text-gray-700">{u.codigo}</td>
                                                        <td className="px-6 py-4 font-bold text-right text-gray-700">${u.saldo.toLocaleString()}</td>
                                                        <td className="px-6 py-4 text-center">
                                                            {u.saldo > 0 ? <span className="text-red-500 font-bold text-xs uppercase">Con Deuda</span> : <span className="text-green-600 font-bold text-xs uppercase bg-green-100 px-2 py-1 rounded-full">Al Día</span>}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                )}

                                {/* FACTURAS PENDIENTES (COMUN) */}
                                <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden animate-slideUp">
                                    <div className="p-4 border-b bg-gray-50">
                                        <h3 className="font-bold text-gray-700 text-sm uppercase">Detalle de Facturas Pendientes</h3>
                                    </div>
                                    <table className="w-full text-sm text-left">
                                        <thead className="text-xs text-gray-500 uppercase bg-gray-50 border-b">
                                            <tr>
                                                <th className="px-6 py-3"># Doc</th>
                                                <th className="px-6 py-3">Fecha</th>
                                                {paymentMode === 'OWNER' && <th className="px-6 py-3">{labels.unidad}</th>}
                                                <th className="px-6 py-3 text-right">Valor Original</th>
                                                <th className="px-6 py-3 text-right">Saldo</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-100">
                                            {estadoCuenta.facturas_pendientes.length === 0 ? (
                                                <tr>
                                                    <td colSpan={paymentMode === 'OWNER' ? 5 : 4} className="px-6 py-8 text-center text-gray-500 italic">No hay facturas pendientes.</td>
                                                </tr>
                                            ) : (
                                                estadoCuenta.facturas_pendientes.map((f, idx) => (
                                                    <tr key={f.id || idx} className="hover:bg-gray-50 transition-colors">
                                                        <td className="px-6 py-4 font-bold text-indigo-600">#{f.numero}</td>
                                                        <td className="px-6 py-4 text-gray-600">{f.fecha?.substring(0, 10)}</td>
                                                        {paymentMode === 'OWNER' && <td className="px-6 py-4 text-gray-800 font-bold">{f.unidad_codigo}</td>}
                                                        <td className="px-6 py-4 text-gray-600 text-right">${Number(f.valor_total).toLocaleString()}</td>
                                                        <td className="px-6 py-4 font-bold text-red-600 text-right">${Number(f.saldo_pendiente).toLocaleString()}</td>
                                                    </tr>
                                                ))
                                            )}
                                        </tbody>
                                        {estadoCuenta.facturas_pendientes.length > 0 && (
                                            <tfoot className="bg-gray-50 font-bold text-gray-700">
                                                <tr>
                                                    <td colSpan={paymentMode === 'OWNER' ? 4 : 3} className="px-6 py-3 text-right">TOTAL</td>
                                                    <td className="px-6 py-3 text-right text-red-600">${Number(estadoCuenta.saldo_total).toLocaleString()}</td>
                                                </tr>
                                            </tfoot>
                                        )}
                                    </table>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
