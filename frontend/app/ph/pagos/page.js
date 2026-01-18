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
    const [unidades, setUnidades] = useState([]);
    const [selectedUnidadId, setSelectedUnidadId] = useState('');
    const [estadoCuenta, setEstadoCuenta] = useState(null);
    const [loadingData, setLoadingData] = useState(false);

    const [pagoForm, setPagoForm] = useState({
        monto: '',
        fecha: new Date().toISOString().slice(0, 10)
    });
    const [processing, setProcessing] = useState(false);
    const [successMsg, setSuccessMsg] = useState('');
    const [errorMsg, setErrorMsg] = useState('');

    useEffect(() => {
        if (!authLoading) loadUnidades();
    }, [authLoading]);

    const loadUnidades = async () => {
        try {
            const data = await phService.getUnidades();
            setUnidades(data);
        } catch (err) {
            console.error(err);
        }
    };

    const handleUnidadChange = async (e) => {
        const uid = e.target.value;
        setSelectedUnidadId(uid);
        setEstadoCuenta(null);
        setSuccessMsg('');
        setErrorMsg('');
        setPagoForm(prev => ({ ...prev, monto: '' }));

        if (uid) {
            setLoadingData(true);
            try {
                const data = await phService.getEstadoCuenta(uid);
                setEstadoCuenta(data);
                if (data.saldo_total > 0) {
                    setPagoForm(prev => ({ ...prev, monto: data.saldo_total }));
                }
            } catch (err) {
                setErrorMsg('Error consultando estado de cuenta.');
            } finally {
                setLoadingData(false);
            }
        }
    };

    // --- MODAL RECALCULO ---
    const [showRecalculoModal, setShowRecalculoModal] = useState(false);
    const [recalculoData, setRecalculoData] = useState(null); // { unidad_id, fecha }
    const [recalculando, setRecalculando] = useState(false);
    const [recalculoResult, setRecalculoResult] = useState(null);

    const handlePagoSubmit = async (e) => {
        e.preventDefault();
        if (!selectedUnidadId) return;
        if (!confirm(`¿Confirmar pago de $${Number(pagoForm.monto).toLocaleString()} para la ${labels.unidad}?`)) return;

        setProcessing(true);
        setErrorMsg('');
        setSuccessMsg('');
        setRecalculoResult(null);

        try {
            const res = await phService.registrarPago({
                unidad_id: parseInt(selectedUnidadId),
                monto: parseFloat(pagoForm.monto),
                fecha: pagoForm.fecha
            });
            setSuccessMsg('Pago registrado exitosamente. El saldo se ha actualizado.');

            // Recargar estado
            const data = await phService.getEstadoCuenta(selectedUnidadId);
            setEstadoCuenta(data);
            setPagoForm(prev => ({ ...prev, monto: '' }));

            // --- DETECCION INTELIGENTE DE RECALCULO (Backend-Driven) ---
            if (false && res && res.sugerir_recalculo) { // DISABLED BY USER REQUEST
                console.log("Backend sugiere recálculo. Facturas afectadas:", res.facturas_futuras_count);
                setRecalculoData({ unidad_id: parseInt(selectedUnidadId), fecha: pagoForm.fecha });
                setShowRecalculoModal(true);
            } else {
                console.log("Backend NO sugiere recálculo.");
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
            setSuccessMsg(`Pago registrado y se actualizaron ${res.actualizadas} facturas posteriores con nuevo interés.`);
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

            <div className="max-w-5xl mx-auto">
                <div className="mb-6">
                    <div className="flex items-center gap-3 mt-3">
                        <div className="p-2 bg-green-100 rounded-lg text-green-600">
                            <FaMoneyBillWave className="text-2xl" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold text-gray-800">Recaudos y Pagos {labels.module}</h1>
                            <p className="text-gray-500 text-sm">Registro de pagos de administración y consulta de cartera por {labels.unidad}.</p>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* SELECCIÓN Y FORMULARIO */}
                    <div className="md:col-span-1 bg-white p-6 rounded-xl shadow-sm border border-gray-100 h-fit">
                        <label className="block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide">Seleccione {labels.unidad}</label>
                        <select
                            value={selectedUnidadId}
                            onChange={handleUnidadChange}
                            className="w-full px-4 py-2 mb-6 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-green-500 outline-none transition-all"
                        >
                            <option value="">-- Buscar {labels.unidad} --</option>
                            {unidades.map(u => (
                                <option key={u.id} value={u.id}>{u.codigo} - Torre {u.torre?.nombre}</option>
                            ))}
                        </select>

                        {estadoCuenta && (
                            <form onSubmit={handlePagoSubmit} className="space-y-4 pt-4 border-t border-dashed animate-fadeIn">
                                <h3 className="font-bold text-gray-700 flex items-center gap-2">
                                    <FaCheckCircle className="text-green-500" /> Registrar Nuevo Pago
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
                                    className={`w-full py-3 rounded-lg text-white font-bold shadow-md transition-all ${processing ? 'bg-gray-400' : 'bg-green-600 hover:bg-green-700 hover:scale-105'}`}
                                >
                                    {processing ? 'Procesando...' : 'REGISTRAR PAGO'}
                                </button>
                            </form>
                        )}

                        {successMsg && <div className="mt-4 p-3 bg-green-50 text-green-700 text-sm rounded-lg border border-green-200">{successMsg}</div>}
                        {errorMsg && <div className="mt-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg border border-red-200 flex items-center gap-2"><FaExclamationTriangle /> {errorMsg}</div>}
                    </div>

                    {/* ESTADO DE CUENTA */}
                    <div className="md:col-span-2 space-y-6">
                        {loadingData && <div className="text-center py-10 text-gray-400">Cargando información de cartera...</div>}

                        {!loadingData && !estadoCuenta && (
                            <div className="bg-gray-100 rounded-xl p-10 text-center text-gray-400 border-2 border-dashed border-gray-200">
                                <FaBuilding className="text-4xl mx-auto mb-2 opacity-50" />
                                <p>Seleccione una {labels.unidad.toLowerCase()} para ver su estado de cuenta.</p>
                            </div>
                        )}

                        {!loadingData && estadoCuenta && (
                            <>
                                {/* RESUMEN */}
                                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 animate-slideUp">
                                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                                        <div>
                                            <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">{labels.propietario.toUpperCase()}</p>
                                            <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                                                <FaUser className="text-indigo-500" /> {estadoCuenta.propietario_nombre}
                                            </h2>
                                            <p className="text-sm text-gray-500 mt-1">{labels.unidad} {estadoCuenta.unidad}</p>
                                        </div>
                                        <div className="text-right bg-red-50 p-4 rounded-lg border border-red-100 min-w-[200px]">
                                            <p className="text-xs font-bold text-red-400 uppercase tracking-wider">SALDO PENDIENTE</p>
                                            <p className="text-3xl font-bold text-red-600">${Number(estadoCuenta.saldo_total).toLocaleString()}</p>
                                        </div>
                                    </div>
                                </div>

                                {/* TABLA FACTURAS */}
                                <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden animate-slideUp">
                                    <div className="p-4 border-b bg-gray-50">
                                        <h3 className="font-bold text-gray-700 text-sm uppercase">Facturas Pendientes de Pago</h3>
                                    </div>
                                    <table className="w-full text-sm text-left">
                                        <thead className="text-xs text-gray-500 uppercase bg-gray-50 border-b">
                                            <tr>
                                                <th className="px-6 py-3"># Doc</th>
                                                <th className="px-6 py-3">Fecha</th>
                                                <th className="px-6 py-3 text-right">Valor Original</th>
                                                <th className="px-6 py-3 text-right">Saldo</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-100">
                                            {estadoCuenta.facturas_pendientes.length === 0 ? (
                                                <tr>
                                                    <td colSpan="4" className="px-6 py-8 text-center text-gray-500 italic">No hay facturas pendientes.</td>
                                                </tr>
                                            ) : (
                                                estadoCuenta.facturas_pendientes.map((f) => (
                                                    <tr key={f.id} className="hover:bg-gray-50 transition-colors">
                                                        <td className="px-6 py-4 font-bold text-indigo-600">#{f.numero}</td>
                                                        <td className="px-6 py-4 text-gray-600">{f.fecha}</td>
                                                        <td className="px-6 py-4 text-gray-600 text-right">${f.valor_total.toLocaleString()}</td>
                                                        <td className="px-6 py-4 font-bold text-red-600 text-right">${f.saldo_pendiente.toLocaleString()}</td>
                                                    </tr>
                                                ))
                                            )}
                                        </tbody>
                                        {estadoCuenta.facturas_pendientes.length > 0 && (
                                            <tfoot className="bg-gray-50 font-bold text-gray-700">
                                                <tr>
                                                    <td colSpan="3" className="px-6 py-3 text-right">TOTAL</td>
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
