'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import BotonRegresar from '../../components/BotonRegresar';
import { phService } from '../../../lib/phService';
import BuscadorCuentas from '../../../components/BuscadorCuentas';
import { FaCogs, FaSave, FaPlus, FaTrash, FaEdit, FaExclamationTriangle, FaListUl, FaMoneyBillWave } from 'react-icons/fa';

// Estilos
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none";
const sectionTitleClass = "text-lg font-bold text-gray-700 flex items-center gap-2 border-b pb-2 mb-4";

export default function ConfiguracionPHPage() {
    const { user, loading: authLoading } = useAuth();

    // Estados Globales
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [saving, setSaving] = useState(false);

    // Estados Configuración
    const [config, setConfig] = useState({
        interes_mora_mensual: 1.5,
        dia_corte: 1,
        dia_limite_pago: 10,
        dia_limite_pronto_pago: 5,
        descuento_pronto_pago: 0,
        mensaje_factura: '',
        tipo_documento_factura_id: '',
        tipo_documento_recibo_id: ''
    });

    // Estados Conceptos (Faltaban)
    const [conceptos, setConceptos] = useState([]);
    const [tiposDoc, setTiposDoc] = useState([]);
    const [showConceptoForm, setShowConceptoForm] = useState(false);
    const [editingConcepto, setEditingConcepto] = useState(null);
    const [conceptoForm, setConceptoForm] = useState({
        nombre: '',
        codigo_contable: '',
        tipo_calculo: 'COEFICIENTE',
        valor_defecto: 0,
        activo: true
    });

    useEffect(() => {
        if (!authLoading && user?.empresaId) {
            fetchData();
        }
    }, [authLoading, user]);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [configData, conceptosData, tiposData] = await Promise.all([
                phService.getConfiguracion(),
                phService.getConceptos(),
                phService.getTiposDocumento()
            ]);
            setConfig(configData);
            setConceptos(conceptosData);
            setTiposDoc(tiposData);
        } catch (err) {
            setError('Error cargando configuración.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    // --- MANEJO DE CONFIGURACIÓN ---
    const handleSaveConfig = async (e) => {
        e.preventDefault();
        try {
            setSaving(true);
            await phService.updateConfiguracion(config);
            alert('Configuración guardada correctamente.');
        } catch (err) {
            alert('Error guardando configuración.');
        } finally {
            setSaving(false);
        }
    };

    const handleConfigChange = (e) => {
        const { name, value } = e.target;
        setConfig(prev => ({ ...prev, [name]: value }));
    };

    // --- MANEJO DE CONCEPTOS ---
    const handleConceptoSubmit = async (e) => {
        e.preventDefault();
        try {
            if (editingConcepto) {
                await phService.updateConcepto(editingConcepto.id, conceptoForm);
                alert('Concepto actualizado.');
            } else {
                await phService.createConcepto(conceptoForm);
                alert('Concepto creado.');
            }
            setShowConceptoForm(false);
            setEditingConcepto(null);
            setConceptoForm({
                nombre: '',
                codigo_contable: '',
                tipo_calculo: 'COEFICIENTE',
                valor_defecto: 0,
                activo: true,
                tipo_documento_id: null,
                cuenta_cartera_id: null,
                tipo_documento_recibo_id: null,
                cuenta_caja_id: null
            });
            fetchData(); // Recargar lista
        } catch (err) {
            alert('Error guardando concepto.');
        }
    };

    const handleEditConcepto = (c) => {
        setEditingConcepto(c);
        setConceptoForm({
            nombre: c.nombre,
            codigo_contable: c.codigo_contable || '',
            tipo_calculo: c.tipo_calculo,
            valor_defecto: c.valor_defecto,
            activo: c.activo,
            tipo_documento_id: c.tipo_documento_id,
            cuenta_cartera_id: c.cuenta_cartera_id,
            tipo_documento_recibo_id: c.tipo_documento_recibo_id,
            cuenta_caja_id: c.cuenta_caja_id,

            // UI Helpers
            cuenta_cartera_codigo: c.cuenta_cartera?.codigo || '',
            cuenta_caja_codigo: c.cuenta_caja?.codigo || ''
        });
        setShowConceptoForm(true);
    };

    const handleDeleteConcepto = async (id) => {
        if (!confirm('¿Eliminar este concepto?')) return;
        try {
            await phService.deleteConcepto(id);
            setConceptos(prev => prev.filter(c => c.id !== id));
        } catch (err) {
            alert('Error eliminando concepto.');
        }
    };

    if (authLoading || loading) return <p className="p-8 text-center text-gray-500">Cargando...</p>;

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
            <div className="max-w-6xl mx-auto">
                {/* HEAD */}
                <div className="mb-8">
                    <BotonRegresar />
                    <div className="flex items-center gap-3 mt-3">
                        <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                            <FaCogs className="text-2xl" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold text-gray-800">Configuración PH</h1>
                            <p className="text-gray-500 text-sm">Parámetros generales y conceptos de facturación.</p>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

                    {/* PANEL IZQUIERDO: CONFIGURACIÓN GENERAL */}
                    <div className="md:col-span-1">
                        <form onSubmit={handleSaveConfig} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                            <h2 className={sectionTitleClass}><FaCogs /> Parámetros Generales</h2>

                            <div className="space-y-4">
                                <div>
                                    <label className={labelClass}>Interés Mora Mensual (%)</label>
                                    <input type="number" step="0.01" name="interes_mora_mensual" value={config.interes_mora_mensual} onChange={handleConfigChange} className={inputClass} required />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className={labelClass}>Día Corte</label>
                                        <input type="number" min="1" max="31" name="dia_corte" value={config.dia_corte} onChange={handleConfigChange} className={inputClass} required />
                                    </div>
                                    <div>
                                        <label className={labelClass}>Límite Pago</label>
                                        <input type="number" min="1" max="31" name="dia_limite_pago" value={config.dia_limite_pago} onChange={handleConfigChange} className={inputClass} required />
                                    </div>
                                </div>

                                <div className="pt-4 border-t border-dashed">
                                    <p className="text-xs text-gray-400 mb-2 font-semibold">PRONTO PAGO</p>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className={labelClass}>Día Límite</label>
                                            <input type="number" min="1" max="31" name="dia_limite_pronto_pago" value={config.dia_limite_pronto_pago} onChange={handleConfigChange} className={inputClass} />
                                        </div>
                                        <div>
                                            <label className={labelClass}>Descuento (%)</label>
                                            <input type="number" step="0.01" name="descuento_pronto_pago" value={config.descuento_pronto_pago} onChange={handleConfigChange} className={inputClass} />
                                        </div>
                                    </div>
                                </div>

                                <div>
                                    <label className={labelClass}>Mensaje en Factura</label>
                                    <textarea name="mensaje_factura" value={config.mensaje_factura || ''} onChange={handleConfigChange} className={inputClass} rows="3"></textarea>
                                </div>

                                <div className="pt-4 border-t border-dashed">
                                    <p className="text-xs text-gray-400 mb-2 font-semibold">CONFIGURACIÓN CONTABLE</p>
                                    <div className="space-y-3">
                                        <div>
                                            <label className={labelClass}>Doc. Facturación (Cuentas de Cobro)</label>
                                            <select name="tipo_documento_factura_id" value={config.tipo_documento_factura_id || ''} onChange={handleConfigChange} className={inputClass}>
                                                <option value="">-- Seleccionar --</option>
                                                {tiposDoc.filter(t => t.funcion_especial !== 'PAGO_PROVEEDOR').map(t => (
                                                    <option key={t.id} value={t.id}>{t.codigo} - {t.nombre}</option>
                                                ))}
                                            </select>
                                        </div>
                                        <div>
                                            <label className={labelClass}>Doc. Recaudo (Recibos de Caja)</label>
                                            <select name="tipo_documento_recibo_id" value={config.tipo_documento_recibo_id || ''} onChange={handleConfigChange} className={inputClass}>
                                                <option value="">-- Seleccionar --</option>
                                                {tiposDoc.filter(t => t.funcion_especial !== 'FACTURA_VENTA').map(t => (
                                                    <option key={t.id} value={t.id}>{t.codigo} - {t.nombre}</option>
                                                ))}
                                            </select>
                                        </div>
                                    </div>
                                </div>


                                <button type="submit" disabled={saving} className="w-full flex justify-center items-center gap-2 bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-700 transition-colors shadow-sm font-medium mt-4">
                                    <FaSave /> {saving ? 'Guardando...' : 'Guardar Parámetros'}
                                </button>
                            </div>
                        </form>
                    </div>

                    {/* PANEL DERECHO: CONCEPTOS DE FACTURACIÓN */}
                    <div className="md:col-span-2">
                        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                            <div className="flex justify-between items-center bg-gray-50 p-3 rounded-lg mb-4 border border-gray-100">
                                <h2 className="text-lg font-bold text-gray-700 flex items-center gap-2"><FaMoneyBillWave /> Conceptos de Cobro</h2>
                                <button type="button" onClick={() => { setEditingConcepto(null); setConceptoForm({ nombre: '', codigo_contable: '', tipo_calculo: 'COEFICIENTE', valor_defecto: 0, activo: true }); setShowConceptoForm(!showConceptoForm); }} className="text-xs bg-green-600 text-white px-3 py-2 rounded-md hover:bg-green-700 transition font-bold flex items-center gap-1">
                                    <FaPlus /> NUEVO CONCEPTO
                                </button>
                            </div>

                            {/* FORMULARIO DE CONCEPTO (CONDICIONAL) */}
                            {showConceptoForm && (
                                <form onSubmit={handleConceptoSubmit} className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200 animate-fadeIn">
                                    <h3 className="text-sm font-bold text-gray-600 mb-3 border-b pb-1">{editingConcepto ? 'Editar Concepto' : 'Nuevo Concepto'}</h3>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                                        <div>
                                            <label className={labelClass}>Nombre Concepto</label>
                                            <input type="text" value={conceptoForm.nombre} onChange={e => setConceptoForm({ ...conceptoForm, nombre: e.target.value })} className={inputClass} required placeholder="Ej: Cuota Administración" />
                                        </div>
                                        <div>
                                            {/* BUSCADOR DE CUENTA CONTABLE INGRESO */}
                                            <BuscadorCuentas
                                                label="Cuenta de Ingreso (Crédito)"
                                                selectedCodigo={conceptoForm.codigo_contable}
                                                onSelect={(cuenta) => setConceptoForm({ ...conceptoForm, codigo_contable: cuenta ? cuenta.codigo : '' })}
                                            />
                                        </div>
                                        <div>
                                            <label className={labelClass}>Tipo de Cálculo</label>
                                            <select value={conceptoForm.tipo_calculo} onChange={e => setConceptoForm({ ...conceptoForm, tipo_calculo: e.target.value })} className={inputClass}>
                                                <option value="COEFICIENTE">Por Coeficiente (Presupuestal)</option>
                                                <option value="FIJO">Valor Fijo (Ej: Parqueadero)</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label className={labelClass}>Valor por Defecto / Base</label>
                                            <input type="number" step="0.01" value={conceptoForm.valor_defecto} onChange={e => setConceptoForm({ ...conceptoForm, valor_defecto: e.target.value })} className={inputClass} />
                                            <p className="text-[10px] text-gray-400 mt-1">Si es Coeficiente, deje en 0 (se usa presupuesto).</p>
                                        </div>

                                        {/* NUEVOS CAMPOS AVANZADOS */}
                                        {/* NUEVOS CAMPOS AVANZADOS */}
                                        <div className="col-span-1 md:col-span-2 border-t pt-2 mt-2">
                                            <p className="text-xs font-bold text-gray-400 mb-2 uppercase">Configuración de Facturación (Opcional)</p>
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                <div>
                                                    <label className={labelClass}>Tipo de Documento (Factura)</label>
                                                    <select value={conceptoForm.tipo_documento_id || ''} onChange={e => setConceptoForm({ ...conceptoForm, tipo_documento_id: e.target.value || null })} className={inputClass}>
                                                        <option value="">-- Usar Global --</option>
                                                        {tiposDoc.filter(t => t.funcion_especial !== 'PAGO_PROVEEDOR').map(t => (
                                                            <option key={t.id} value={t.id}>{t.codigo} - {t.nombre}</option>
                                                        ))}
                                                    </select>
                                                    <p className="text-[10px] text-gray-400 mt-1">Si se deja vacío, usa el configurado en Parámetros Generales.</p>
                                                </div>
                                                <div>
                                                    <BuscadorCuentas
                                                        label="Cuenta Cartera (Débito)"
                                                        selectedCodigo={conceptoForm.cuenta_cartera_codigo}
                                                        onSelect={(c) => setConceptoForm({ ...conceptoForm, cuenta_cartera_id: c ? c.id : null, cuenta_cartera_codigo: c ? c.codigo : '' })}
                                                    />
                                                    <p className="text-[10px] text-gray-400 mt-1">Ej: 1305 / 1605... (Sobrescribe la global).</p>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="col-span-1 md:col-span-2 border-t pt-2 mt-2">
                                            <p className="text-xs font-bold text-gray-400 mb-2 uppercase">Configuración de Recaudo / Abonos (Opcional)</p>
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                <div>
                                                    <label className={labelClass}>Tipo de Documento (Recibo)</label>
                                                    <select value={conceptoForm.tipo_documento_recibo_id || ''} onChange={e => setConceptoForm({ ...conceptoForm, tipo_documento_recibo_id: e.target.value || null })} className={inputClass}>
                                                        <option value="">-- Usar Global --</option>
                                                        {tiposDoc.filter(t => t.funcion_especial !== 'FACTURA_VENTA').map(t => (
                                                            <option key={t.id} value={t.id}>{t.codigo} - {t.nombre}</option>
                                                        ))}
                                                    </select>
                                                </div>
                                                <div>
                                                    <BuscadorCuentas
                                                        label="Cuenta Caja (Débito al Cobrar)"
                                                        selectedCodigo={conceptoForm.cuenta_caja_codigo}
                                                        onSelect={(c) => setConceptoForm({ ...conceptoForm, cuenta_caja_id: c ? c.id : null, cuenta_caja_codigo: c ? c.codigo : '' })}
                                                    />
                                                    <p className="text-[10px] text-gray-400 mt-1">Ej: 1105 Caja General...</p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex justify-end gap-2">
                                        <button type="button" onClick={() => setShowConceptoForm(false)} className="px-4 py-2 text-gray-500 hover:text-gray-700 text-xs font-bold uppercase">Cancelar</button>
                                        <button type="submit" className="px-5 py-2 bg-indigo-600 text-white rounded-md text-xs font-bold uppercase shadow hover:bg-indigo-700 transition">Guardar Concepto</button>
                                    </div>
                                </form>
                            )}

                            {/* LISTA DE CONCEPTOS */}
                            {/* LISTA DE CONCEPTOS */}
                            <div className="overflow-x-auto rounded-lg border border-gray-200">
                                <table className="min-w-full divide-y divide-gray-200">
                                    <thead className="bg-slate-100">
                                        <tr>
                                            <th className="py-2 px-3 text-left text-xs font-bold text-gray-600 uppercase">Activo</th>
                                            <th className="py-2 px-3 text-left text-xs font-bold text-gray-600 uppercase">Nombre</th>
                                            <th className="py-2 px-3 text-left text-xs font-bold text-gray-600 uppercase">Tipo</th>
                                            <th className="py-2 px-3 text-left text-xs font-bold text-gray-600 uppercase">Cod. Contable</th>
                                            <th className="py-2 px-3 text-center text-xs font-bold text-gray-600 uppercase">Acciones</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-100 bg-white">
                                        {conceptos.length > 0 ? (
                                            conceptos.map(c => (
                                                <tr key={c.id} className="hover:bg-indigo-50/30 transition">
                                                    <td className="py-2 px-3 text-center">
                                                        <input
                                                            type="checkbox"
                                                            checked={!!c.activo}
                                                            onChange={async (e) => {
                                                                const newValue = e.target.checked;
                                                                // Optimistic Update
                                                                setConceptos(prev => prev.map(oc => oc.id === c.id ? { ...oc, activo: newValue } : oc));

                                                                try {
                                                                    await phService.updateConcepto(c.id, { ...c, activo: newValue });
                                                                } catch (err) {
                                                                    // Revert if error
                                                                    setConceptos(prev => prev.map(oc => oc.id === c.id ? { ...oc, activo: !newValue } : oc));
                                                                    alert('Error actualizando concepto');
                                                                }
                                                            }}
                                                            className="rounded text-indigo-600 focus:ring-indigo-500 w-4 h-4 cursor-pointer"
                                                        />
                                                    </td>
                                                    <td className="py-2 px-3 text-sm font-medium text-gray-800">{c.nombre}</td>
                                                    <td className="py-2 px-3 text-xs">
                                                        <span className={`px-2 py-1 rounded-full font-bold ${c.tipo_calculo === 'COEFICIENTE' ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'}`}>
                                                            {c.tipo_calculo}
                                                        </span>
                                                    </td>
                                                    <td className="py-2 px-3 text-sm font-mono text-gray-500">{c.codigo_contable || 'N/A'}</td>
                                                    <td className="py-2 px-3 text-center flex justify-center gap-2">
                                                        <button onClick={() => handleEditConcepto(c)} className="text-blue-500 hover:text-blue-700"><FaEdit /></button>
                                                        <button onClick={() => handleDeleteConcepto(c.id)} className="text-red-500 hover:text-red-700"><FaTrash /></button>
                                                    </td>
                                                </tr>
                                            ))
                                        ) : (
                                            <tr><td colSpan="5" className="py-6 text-center text-gray-400 italic text-sm">No hay conceptos definidos.</td></tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>

                </div>
            </div >
        </div >
    );
}
