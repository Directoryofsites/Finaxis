'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';

import { apiService } from '../../../lib/apiService';
import { phService } from '../../../lib/phService';
import {
    FaMoneyBillWave, FaUser, FaBuilding, FaCheckCircle, FaExclamationTriangle, FaCalendarAlt,
    FaHistory, FaFileInvoiceDollar, FaPrint, FaFileAlt, FaListUl, FaLayerGroup
} from 'react-icons/fa';
import { useRecaudos } from '../../../contexts/RecaudosContext'; // IMPORT
import ManualButton from '../../components/ManualButton';
import Link from 'next/link';

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
    const [lastPaymentData, setLastPaymentData] = useState(null);
    const [downloading, setDownloading] = useState(null);
    const [successMsg, setSuccessMsg] = useState('');
    const [errorMsg, setErrorMsg] = useState('');

    const [detallesAbono, setDetallesAbono] = useState([]); // [{concepto_id, nombre, monto, saldo_pendiente}]
    const [isAbonoManual, setIsAbonoManual] = useState(false); // Modo Manual (Gobernanza) vs Automático (FIFO)

    useEffect(() => {
        if (!authLoading) loadInitialData();
    }, [authLoading]);

    const loadInitialData = async () => {
        try {
            const [uData, tData, pData] = await Promise.all([
                phService.getUnidades(),
                phService.getTorres(),
                phService.getPropietarios()
            ]);
            setUnidades(uData || []);
            setTorres(tData || []);
            setPropietarios(pData || []);
        } catch (err) {
            console.error(err);
        }
    };

    // Lógica de Filtrado Unidades
    const unidadesFiltered = (unidades || []).filter(u => {
        const matchesSearch = searchTerm === '' ||
            (u.codigo || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
            (u.propietario?.razon_social || '').toLowerCase().includes(searchTerm.toLowerCase());
        const matchesTower = selectedTorreId === null || u.torre_id === selectedTorreId;
        return matchesSearch && matchesTower;
    });

    // Lógica de Filtrado Propietarios
    const propietariosFiltered = (propietarios || []).filter(p => {
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
        setLastPaymentData(null);
        setPagoForm(prev => ({ ...prev, monto: '' }));
        setDetallesAbono([]);
        setIsAbonoManual(false); // Siempre resetear a automático
    };

    const fetchEstadoCuenta = async (mode, id) => {
        setLoadingData(true);
        try {
            let data;
            if (mode === 'UNIT') {
                data = await phService.getEstadoCuenta(id);
                
                // Mapear detalles para la UI
                if (data.detalles_por_concepto) {
                    setDetallesAbono(data.detalles_por_concepto.map(c => ({
                        concepto_id: c.id, 
                        nombre: c.nombre,
                        tipo: c.tipo,
                        saldo_pendiente: c.saldo || 0,
                        monto: 0,
                        selected: false // Iniciar desmarcado por defecto
                    })));
                }
            } else {
                data = await phService.getEstadoCuentaPropietario(id);
                data.saldo_total = data.saldo_total_consolidado; // Alias
                data.propietario_nombre = data.propietario.nombre;
                data.unidad = `(Todas las Unidades)`;
                setDetallesAbono([]); 
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

    // Al cambiar a manual, podemos sugerir el pago total distribuido
    const toggleAbonoManual = () => {
        const newValue = !isAbonoManual;
        setIsAbonoManual(newValue);
        if (newValue && detallesAbono.length > 0) {
             // Si activa manual, inicialmente todos desmarcados y monto 0
             setDetallesAbono(prev => prev.map(d => ({ ...d, selected: false, monto: 0 })));
             setPagoForm(prev => ({ ...prev, monto: 0 }));
        } else if (!newValue) {
             // Si desactiva manual, volver al saldo total en el campo general
             setPagoForm(prev => ({ ...prev, monto: estadoCuenta?.saldo_total || 0 }));
        }
    };

    const toggleConceptoSelection = (idx) => {
        const newDet = [...detallesAbono];
        const item = newDet[idx];
        item.selected = !item.selected;
        
        if (item.selected) {
            // Al marcar, sugerir el saldo pendiente
            item.monto = item.saldo_pendiente;
        } else {
            // Al desmarcar, limpiar monto
            item.monto = 0;
        }
        
        setDetallesAbono(newDet);
        const total = newDet.reduce((sum, d) => sum + d.monto, 0);
        setPagoForm(prev => ({ ...prev, monto: total }));
    };

    // Actualizar el monto total cuando cambian los detalles (solo en modo manual)
    const updateConceptoMonto = (idx, valor) => {
        const newDet = [...detallesAbono];
        newDet[idx].monto = parseFloat(valor) || 0;
        setDetallesAbono(newDet);
        
        const total = newDet.reduce((sum, d) => sum + d.monto, 0);
        setPagoForm(prev => ({ ...prev, monto: total }));
    };

    // --- MODAL RECALCULO ---
    const [showRecalculoModal, setShowRecalculoModal] = useState(false);
    const [recalculoData, setRecalculoData] = useState(null);
    const [recalculando, setRecalculando] = useState(false);
    const [recalculoResult, setRecalculoResult] = useState(null);

    const updateDetalleMonto = (index, val) => {
        const newDetalles = [...detallesAbono];
        newDetalles[index].monto = parseFloat(val) || 0;
        setDetallesAbono(newDetalles);

        // Actualizar monto total del form
        const newTotal = newDetalles.reduce((acc, curr) => acc + curr.monto, 0);
        setPagoForm(prev => ({ ...prev, monto: newTotal }));
    };

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
                    fecha: pagoForm.fecha,
                    detalles: isAbonoManual ? detallesAbono.filter(d => d.monto > 0) : null
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
            setLastPaymentData(res);

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
            console.error("Error en registrarPago:", err);
            let detail = err.response?.data?.detail || 'Error registrando pago.';
            // Si el detalle es un objeto (como en 422), convertirlo a string amigable
            if (typeof detail === 'object') {
                detail = JSON.stringify(detail);
            }
            setErrorMsg(String(detail));
        } finally {
            setProcessing(false);
        }
    };

    const handleDownloadPDF = async (type, id = null) => {
        // type: 'RECEIPT' | 'ACCOUNT_STATUS' | 'EXTRACT'
        setDownloading(type);
        try {
            let url = '';
            let filename = 'documento.pdf';

            if (type === 'RECEIPT') {
                if (!id) return;
                url = `/documentos/${id}/pdf`;
                filename = `Recibo_Caja_${id}.pdf`;
            } else if (type === 'ACCOUNT_STATUS') {
                const targetId = paymentMode === 'UNIT' ? selectedUnidadId : selectedPropietarioId;
                const mode = paymentMode === 'UNIT' ? 'UNIT' : 'OWNER';
                url = `/ph/pagos/estado-cuenta/${targetId}/pdf?mode=${mode}&view=PENDING`;
                filename = `Estado_Cuenta_${targetId}.pdf`;
            } else if (type === 'EXTRACT') {
                const targetId = paymentMode === 'UNIT' ? selectedUnidadId : selectedPropietarioId;
                const mode = paymentMode === 'UNIT' ? 'UNIT' : 'OWNER';
                url = `/ph/pagos/estado-cuenta/${targetId}/pdf?mode=${mode}&view=HISTORY`;
                filename = `Extracto_${targetId}.pdf`;
            }

            const response = await apiService.get(url, { responseType: 'blob' });
            const blob = new Blob([response.data], { type: 'application/pdf' });
            const blobUrl = URL.createObjectURL(blob);
            window.open(blobUrl, '_blank');
            setTimeout(() => URL.revokeObjectURL(blobUrl), 10000);
        } catch (error) {
            console.error(error);
            alert("Error al generar PDF.");
        } finally {
            setDownloading(null);
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
                    <div className="flex justify-between items-start">
                        <div className="flex items-center gap-3 mt-3">
                            <div className="p-2 bg-green-100 rounded-lg text-green-600">
                                <FaMoneyBillWave className="text-2xl" />
                            </div>
                            <div>
                                <h1 className="text-3xl font-bold text-gray-800">Recaudos y Pagos {labels.module}</h1>
                                <p className="text-gray-500 text-sm">Gestión de recaudos por {labels.unidad} o consolidado por Propietario.</p>
                            </div>
                        </div>
                        <div className="mt-3 flex items-center gap-2">
                            <ManualButton 
                                manualPath="pagos.html"
                                title="Manual de Registro de Pagos"
                                position="header"
                            />
                            <Link 
                                href="/ph/pagos/masivo" 
                                className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg font-bold text-xs shadow-lg hover:bg-indigo-700 transition-all hover:scale-105"
                            >
                                <FaLayerGroup /> RECAUDOS MASIVOS (POR TORRE)
                            </Link>
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
                                            readOnly={isAbonoManual}
                                            className={`w-full pl-8 pr-4 py-2 border rounded-lg outline-none focus:ring-2 font-bold text-lg ${
                                                isAbonoManual ? 'bg-gray-100 border-gray-200 text-gray-500' : 'border-gray-300 focus:ring-green-500 text-green-700'
                                            }`}
                                            placeholder="0"
                                            min="1"
                                            required
                                        />
                                        {isAbonoManual && <p className="text-[9px] text-gray-400 mt-1 italic">* Calculado desde abono por concepto</p>}
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

                        {successMsg && (
                            <div className="space-y-4">
                                <div className="mt-4 p-3 bg-green-50 text-green-700 text-sm rounded-lg border border-green-200 shadow-sm animate-fadeIn">
                                    <div className="flex items-center gap-2 font-bold mb-1">
                                        <FaCheckCircle /> Pago Exitoso
                                    </div>
                                    {successMsg}
                                </div>

                                {/* CENTRO DE ACCIÓN INMEDIATO */}
                                <div className="p-4 bg-indigo-50 rounded-xl border border-indigo-100 shadow-inner animate-slideUp">
                                    <p className="text-[10px] font-black text-indigo-400 uppercase tracking-widest mb-3 text-center">Acciones Rápidas</p>
                                    <div className="grid grid-cols-1 gap-2">
                                        {/* BOTON RECIBO(S) */}
                                        {paymentMode === 'UNIT' && lastPaymentData?.documento_id && (
                                            <button
                                                onClick={() => handleDownloadPDF('RECEIPT', lastPaymentData.documento_id)}
                                                className="flex items-center justify-between p-3 bg-white hover:bg-indigo-600 hover:text-white rounded-lg border border-indigo-200 transition-all font-bold text-sm text-indigo-700 group shadow-sm"
                                            >
                                                <div className="flex items-center gap-2">
                                                    <FaPrint className="group-hover:scale-110 transition-transform" /> Imprimir Recibo
                                                </div>
                                                <span className="text-[10px] opacity-60">PDF</span>
                                            </button>
                                        )}

                                        {paymentMode === 'OWNER' && lastPaymentData?.detalle_pagos && (
                                            <div className="space-y-1">
                                                <p className="text-[9px] font-bold text-indigo-300 uppercase mb-1">Recibos por Unidad:</p>
                                                <div className="max-h-32 overflow-y-auto pr-1">
                                                    {lastPaymentData.detalle_pagos.filter(p => p.estado === 'OK').map((p, i) => (
                                                        <button
                                                            key={i}
                                                            onClick={() => handleDownloadPDF('RECEIPT', p.documento_id)}
                                                            className="flex items-center justify-between w-full p-2 bg-white hover:bg-indigo-100 rounded border border-indigo-100 mb-1 text-xs text-indigo-600 transition-all"
                                                        >
                                                            <div className="flex items-center gap-1">
                                                                <FaListUl className="text-[10px]" /> {p.documento}
                                                            </div>
                                                            <FaPrint />
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        <button
                                            onClick={() => handleDownloadPDF('ACCOUNT_STATUS')}
                                            disabled={downloading === 'ACCOUNT_STATUS'}
                                            className="flex items-center justify-between p-3 bg-white hover:bg-indigo-600 hover:text-white rounded-lg border border-indigo-200 transition-all font-bold text-sm text-indigo-700 group shadow-sm"
                                        >
                                            <div className="flex items-center gap-2">
                                                <FaFileAlt className="group-hover:scale-110 transition-transform" /> Estado de Cuenta
                                            </div>
                                            <span className="text-[10px] opacity-60">VISTA ACTUAL</span>
                                        </button>

                                        <button
                                            onClick={() => handleDownloadPDF('EXTRACT')}
                                            disabled={downloading === 'EXTRACT'}
                                            className="flex items-center justify-between p-3 bg-white hover:bg-indigo-600 hover:text-white rounded-lg border border-indigo-200 transition-all font-bold text-sm text-indigo-700 group shadow-sm"
                                        >
                                            <div className="flex items-center gap-2">
                                                <FaHistory className="group-hover:scale-110 transition-transform" /> Descargar Extracto
                                            </div>
                                            <span className="text-[10px] opacity-60">HISTÓRICO</span>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}
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

                                {/* ABONO DIRIGIDO POR CONCEPTO */}
                                {paymentMode === 'UNIT' && detallesAbono.length > 0 && (
                                    <div className={`bg-white rounded-xl shadow-sm border-2 overflow-hidden animate-slideUp mb-6 transition-all ${isAbonoManual ? 'border-indigo-500' : 'border-gray-200'}`}>
                                        <div className={`p-4 border-b flex justify-between items-center transition-colors ${isAbonoManual ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-700'}`}>
                                            <div className="flex items-center gap-2">
                                                <FaListUl className={isAbonoManual ? "text-white" : "text-gray-500"} />
                                                <h3 className="font-bold text-sm uppercase">Detalle de Cobros</h3>
                                            </div>
                                            <div className="flex items-center gap-3">
                                                <span className={`text-[10px] font-bold uppercase transition-opacity ${isAbonoManual ? 'opacity-100' : 'opacity-50'}`}>
                                                    Abono Dirigido (Manual)
                                                </span>
                                                <button
                                                    onClick={toggleAbonoManual}
                                                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors outline-none ${isAbonoManual ? 'bg-green-400' : 'bg-gray-300'}`}
                                                >
                                                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${isAbonoManual ? 'translate-x-6' : 'translate-x-1'}`} />
                                                </button>
                                            </div>
                                        </div>
                                        
                                        <div className={`p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 transition-opacity ${isAbonoManual ? 'opacity-100' : 'opacity-40 pointer-events-none'}`}>
                                            {detallesAbono.map((d, idx) => (
                                                <div 
                                                    key={idx} 
                                                    onClick={() => isAbonoManual && toggleConceptoSelection(idx)}
                                                    className={`p-4 rounded-xl border flex flex-col justify-between transition-all shadow-sm cursor-pointer ${
                                                        isAbonoManual 
                                                            ? (d.selected ? 'bg-indigo-50 border-indigo-500 ring-1 ring-indigo-500' : 'bg-white border-gray-100 hover:border-indigo-200') 
                                                            : 'bg-gray-50 border-gray-100'
                                                    }`}
                                                >
                                                    <div className="mb-3">
                                                        <div className="flex justify-between items-start mb-1">
                                                            <p className={`text-[10px] font-bold uppercase tracking-tighter ${isAbonoManual ? 'text-indigo-500' : 'text-gray-400'}`}>{d.tipo}</p>
                                                            {isAbonoManual && (
                                                                <input 
                                                                    type="checkbox" 
                                                                    checked={d.selected} 
                                                                    onChange={() => {}} // Manejado por el onClick del div
                                                                    className="w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500"
                                                                />
                                                            )}
                                                        </div>
                                                        <p className="font-bold text-gray-800 text-xs truncate mb-1" title={d.nombre}>{d.nombre}</p>
                                                        <div className="flex justify-between items-center bg-red-50 px-2 py-1 rounded">
                                                            <span className="text-[10px] text-red-400 font-bold">DEUDA:</span>
                                                            <span className="text-[11px] text-red-600 font-black">${(d.saldo_pendiente || 0).toLocaleString()}</span>
                                                        </div>
                                                    </div>
                                                    <div className="relative group" onClick={(e) => e.stopPropagation()}>
                                                        <span className={`absolute left-3 top-2.5 text-xs font-bold ${isAbonoManual && d.selected ? 'text-indigo-600' : 'text-gray-300'}`}>$</span>
                                                        <input
                                                            type="number"
                                                            value={d.monto}
                                                            onChange={(e) => updateConceptoMonto(idx, e.target.value)}
                                                            disabled={!isAbonoManual || !d.selected}
                                                            className={`w-full pl-7 pr-3 py-2 border-2 rounded-lg text-right font-black text-md outline-none transition-all ${
                                                                isAbonoManual && d.selected 
                                                                    ? 'border-indigo-200 bg-white text-indigo-700 focus:border-indigo-500' 
                                                                    : 'border-gray-50 bg-gray-50 text-gray-300'
                                                            }`}
                                                        />
                                                        {isAbonoManual && d.selected && <p className="text-[9px] text-right mt-1 text-gray-400">¿Cuánto abonar?</p>}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                        
                                        {isAbonoManual && (
                                            <div className="bg-indigo-600 p-4 text-white flex justify-between items-center shadow-inner animate-fadeIn">
                                                <div>
                                                    <p className="text-[10px] font-bold uppercase opacity-80">Suma Total para Registrar</p>
                                                    <p className="text-xs italic opacity-60">(Se aplicará a estos conceptos específicos)</p>
                                                </div>
                                                <div className="text-right">
                                                    <p className="text-3xl font-black">${(Number(pagoForm.monto) || 0).toLocaleString()}</p>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}

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
