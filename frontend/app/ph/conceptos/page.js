'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { phService } from '../../../lib/phService';

import { FaFileInvoiceDollar, FaPlus, FaEdit, FaTrash, FaSave, FaTimes, FaLayerGroup } from 'react-icons/fa';
import BuscadorCuentas from '../../../components/BuscadorCuentas';
import { useRecaudos } from '../../../contexts/RecaudosContext'; // IMPORT
import ManualButton from '../../components/ManualButton';

function ConceptosContent() {
    const { labels } = useRecaudos(); // HOOK
    const [conceptos, setConceptos] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [availableModulos, setAvailableModulos] = useState([]);

    // Estado Formulario
    const [formData, setFormData] = useState({
        id: null,
        nombre: '',
        cuenta_ingreso_id: null,
        cuenta_ingreso_codigo: '',
        cuenta_ingreso_nombre: '',
        cuenta_cxc_id: null,
        cuenta_cxc_codigo: '',
        cuenta_cxc_nombre: '',
        cuenta_interes_id: null,
        cuenta_interes_codigo: '',
        cuenta_interes_nombre: '',
        cuenta_caja_id: null,
        cuenta_caja_codigo: '',
        cuenta_caja_nombre: '',
        es_fijo: true,
        es_interes: false,
        valor_defecto: 0,
        usa_coeficiente: false,
        modulos_ids: []
    });



    const searchParams = useSearchParams();

    useEffect(() => {
        loadData();

        const trigger = searchParams.get('trigger');
        if (trigger === 'new_ph_concept') {
            const newUrl = window.location.pathname;
            window.history.replaceState({}, '', newUrl);
            setTimeout(() => openNew(), 500);
        }
    }, [searchParams]);

    const loadData = async () => {
        try {
            setLoading(true);
            const [data, mods] = await Promise.all([
                phService.getConceptos(),
                phService.getModulos()
            ]);
            setConceptos(data);
            setAvailableModulos(mods);
        } catch (error) {
            console.error(error);
            alert("Error cargando datos");
        } finally {
            setLoading(false);
        }
    };

    const loadConceptos = async () => {
        // Reload only concepts list
        const data = await phService.getConceptos();
        setConceptos(data);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            if (formData.id) {
                await phService.updateConcepto(formData.id, formData);
            } else {
                await phService.createConcepto(formData);
            }
            setShowModal(false);
            loadConceptos();
        } catch (error) {
            console.error(error);
            alert("Error guardando concepto");
        }
    };

    const handleEdit = (c) => {
        setFormData({
            id: c.id,
            nombre: c.nombre,
            cuenta_ingreso_id: c.cuenta_ingreso_id,
            cuenta_ingreso_codigo: c.cuenta_ingreso ? c.cuenta_ingreso.codigo : '',
            cuenta_ingreso_nombre: c.cuenta_ingreso ? `${c.cuenta_ingreso.codigo} - ${c.cuenta_ingreso.nombre}` : '',
            cuenta_cxc_id: c.cuenta_cxc_id,
            cuenta_cxc_codigo: c.cuenta_cxc ? c.cuenta_cxc.codigo : '',
            cuenta_cxc_nombre: c.cuenta_cxc ? `${c.cuenta_cxc.codigo} - ${c.cuenta_cxc.nombre}` : '',
            cuenta_interes_id: c.cuenta_interes_id,
            cuenta_interes_codigo: c.cuenta_interes ? c.cuenta_interes.codigo : '',
            cuenta_interes_nombre: c.cuenta_interes ? `${c.cuenta_interes.codigo} - ${c.cuenta_interes.nombre}` : '',
            cuenta_caja_id: c.cuenta_caja_id,
            cuenta_caja_codigo: c.cuenta_caja ? c.cuenta_caja.codigo : '',
            cuenta_caja_nombre: c.cuenta_caja ? `${c.cuenta_caja.codigo} - ${c.cuenta_caja.nombre}` : '',
            es_fijo: c.es_fijo,
            es_interes: c.es_interes,
            valor_defecto: c.valor_defecto,
            usa_coeficiente: c.usa_coeficiente,
            modulos_ids: c.modulos ? c.modulos.map(m => m.id) : []
        });
        setShowModal(true);
    };

    const handleDelete = async (id) => {
        if (!confirm("¿Seguro de eliminar este concepto?")) return;
        try {
            await phService.deleteConcepto(id);
            loadConceptos();
        } catch (error) {
            alert("Error eliminando");
        }
    };

    const openNew = () => {
        setFormData({
            id: null,
            nombre: '',
            cuenta_ingreso_id: null,
            cuenta_ingreso_codigo: '',
            cuenta_ingreso_nombre: '',
            cuenta_cxc_id: null,
            cuenta_cxc_codigo: '',
            cuenta_cxc_nombre: '',
            cuenta_interes_id: null,
            cuenta_interes_codigo: '',
            cuenta_interes_nombre: '',
            cuenta_caja_id: null,
            cuenta_caja_codigo: '',
            cuenta_caja_nombre: '',
            es_fijo: true,
            es_interes: false,
            valor_defecto: 0,
            usa_coeficiente: false,
            modulos_ids: []
        });
        setShowModal(true);
    }

    const toggleModulo = (id) => {
        setFormData(prev => {
            const current = prev.modulos_ids || [];
            if (current.includes(id)) {
                return { ...prev, modulos_ids: current.filter(x => x !== id) };
            } else {
                return { ...prev, modulos_ids: [...current, id] };
            }
        });
    };

    return (
        <div className="min-h-screen bg-gray-50 p-6">
            <div className="max-w-6xl mx-auto">
                <div className="flex justify-between items-center mb-6">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2 mt-2">
                            <FaFileInvoiceDollar className="text-green-600" /> Conceptos de Facturación
                        </h1>
                    </div>
                    <div className="flex gap-3">
                        <ManualButton
                            manualPath="conceptos.html"
                            title="Manual de Conceptos de Cobro"
                            position="header"
                        />
                        <button onClick={openNew} className="btn-primary flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg">
                            <FaPlus /> Nuevo Concepto
                        </button>
                    </div>
                </div>

                <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Concepto</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cuenta Ingreso</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo Cobro</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Restricción</th>
                                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Valor Base</th>
                                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                            {conceptos.map(c => (
                                <tr key={c.id}>
                                    <td className="px-6 py-4 font-medium text-gray-900">{c.nombre}</td>
                                    <td className="px-6 py-4 text-gray-500 font-mono text-sm">
                                        {c.cuenta_ingreso ? `${c.cuenta_ingreso.codigo} - ${c.cuenta_ingreso.nombre}` : 'Sin Asignar'}
                                    </td>
                                    <td className="px-6 py-4">
                                        {c.usa_coeficiente ?
                                            <span className="badge bg-purple-100 text-purple-800 px-2 py-1 rounded text-xs">Por {labels.coeficiente}</span> :
                                            <span className="badge bg-green-100 text-green-800 px-2 py-1 rounded text-xs">Valor Fijo</span>
                                        }
                                    </td>
                                    <td className="px-6 py-4 text-xs">
                                        {c.modulos && c.modulos.length > 0 ? (
                                            <div className="flex flex-wrap gap-1">
                                                {c.modulos.map(m => (
                                                    <span key={m.id} className="bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full border border-indigo-200">
                                                        {m.nombre}
                                                    </span>
                                                ))}
                                            </div>
                                        ) : (
                                            <span className="text-gray-400 italic">Global (Todos)</span>
                                        )}
                                    </td>
                                    <td className="px-6 py-4 text-right font-mono">
                                        ${parseFloat(c.valor_defecto).toLocaleString()}
                                    </td>
                                    <td className="px-6 py-4 text-center flex justify-center gap-2">
                                        <button onClick={() => handleEdit(c)} className="text-blue-600 hover:text-blue-800"><FaEdit /></button>
                                        <button onClick={() => handleDelete(c.id)} className="text-red-600 hover:text-red-800"><FaTrash /></button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-xl shadow-xl w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
                        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                            {formData.id ? <FaEdit /> : <FaPlus />} {formData.id ? 'Editar' : 'Nuevo'} Concepto
                        </h2>

                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="label">Nombre del Concepto *</label>
                                <input
                                    className="input-field w-full border p-2 rounded"
                                    value={formData.nombre}
                                    onChange={e => setFormData({ ...formData, nombre: e.target.value })}
                                    required
                                />
                            </div>

                            {/* MÓDULOS */}
                            <div className="p-4 bg-indigo-50 border border-indigo-100 rounded-lg">
                                <label className="block text-xs font-bold text-indigo-700 uppercase mb-2 flex items-center gap-2">
                                    <FaLayerGroup /> Restricción por {labels.module}
                                </label>
                                <p className="text-xs text-gray-500 mb-3">
                                    Si seleccionas un módulo, este cobro <strong>SOLO</strong> se aplicará a las {labels.unidad.toLowerCase()}s que pertenezcan a él.
                                    Si no seleccionas nada, <strong>se cobrará a todos</strong>.
                                </p>

                                {availableModulos.length === 0 ? (
                                    <p className="text-xs text-gray-400 italic">No hay módulos configurados.</p>
                                ) : (
                                    <div className="grid grid-cols-2 gap-2">
                                        {availableModulos.map(mod => (
                                            <div
                                                key={mod.id}
                                                onClick={() => toggleModulo(mod.id)}
                                                className={`cursor-pointer px-3 py-2 text-sm rounded-md border flex items-center gap-2 transition-colors ${formData.modulos_ids.includes(mod.id)
                                                    ? 'bg-indigo-600 text-white border-indigo-600'
                                                    : 'bg-white text-gray-600 border-gray-200 hover:border-indigo-300'
                                                    }`}
                                            >
                                                <div className={`w-4 h-4 rounded-full border flex items-center justify-center ${formData.modulos_ids.includes(mod.id) ? 'bg-white/20' : 'border-gray-300'}`}>
                                                    {formData.modulos_ids.includes(mod.id) && <span className="text-[10px]">✓</span>}
                                                </div>
                                                {mod.nombre}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>

                            <div className="p-4 bg-gray-50 rounded-lg border border-gray-100">
                                <label className="label mb-2 block font-bold text-gray-700">1. Cuenta de Ingreso (Crédito) *</label>
                                <BuscadorCuentas
                                    onSelect={(cta) => setFormData({ ...formData, cuenta_ingreso_id: cta.id, cuenta_ingreso_codigo: cta.codigo, cuenta_ingreso_nombre: cta.nombre })}
                                    selectedCodigo={formData.cuenta_ingreso_codigo}
                                />
                                <p className="text-xs text-gray-500 mt-1">Cuenta donde se registra el ingreso (Ej: 4170 Cuotas de Administración).</p>
                            </div>

                            <div className="p-4 bg-blue-50 rounded-lg border border-blue-100">
                                <label className="label mb-2 block font-bold text-gray-700">2. Cuenta de Cartera (Débito) <span className="text-gray-400 font-normal">(Opcional)</span></label>
                                <BuscadorCuentas
                                    onSelect={(cta) => setFormData({ ...formData, cuenta_cxc_id: cta.id, cuenta_cxc_codigo: cta.codigo, cuenta_cxc_nombre: cta.nombre })}
                                    selectedCodigo={formData.cuenta_cxc_codigo}
                                />
                                <p className="text-xs text-gray-500 mt-1">Cuenta por cobrar. Si se deja vacía, se usa la cuenta global del {labels.propietario} o del Sistema (Ej: 1305).</p>
                            </div>

                            <div className="p-4 bg-orange-50 rounded-lg border border-orange-100">
                                <label className="label mb-2 block font-bold text-gray-700">3. Cuenta Mora / Interés <span className="text-gray-400 font-normal">(Opcional)</span></label>
                                <BuscadorCuentas
                                    onSelect={(cta) => setFormData({ ...formData, cuenta_interes_id: cta.id, cuenta_interes_codigo: cta.codigo, cuenta_interes_nombre: cta.nombre })}
                                    selectedCodigo={formData.cuenta_interes_codigo}
                                />
                                <p className="text-xs text-gray-500 mt-1">Cuenta para registrar intereses de mora específicos de este concepto.</p>
                            </div>

                            <div className="p-4 bg-green-50 rounded-lg border border-green-100">
                                <label className="label mb-2 block font-bold text-gray-700">4. Cuenta de Caja (Recaudo) <span className="text-indigo-500 font-bold">(Nueva)</span></label>
                                <BuscadorCuentas
                                    onSelect={(cta) => setFormData({ ...formData, cuenta_caja_id: cta.id, cuenta_caja_codigo: cta.codigo, cuenta_caja_nombre: cta.nombre })}
                                    selectedCodigo={formData.cuenta_caja_codigo}
                                    placeholder="Ej: 110505 - Caja General"
                                />
                                <p className="text-xs text-gray-500 mt-1">Cuenta Débito donde entra el dinero cuando se paga este concepto.</p>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="label block">Tipo de Cobro</label>
                                    <select
                                        className="input-field w-full border p-2 rounded"
                                        value={formData.usa_coeficiente}
                                        onChange={e => setFormData({ ...formData, usa_coeficiente: e.target.value === 'true' })}
                                    >
                                        <option value="false">Valor Fijo ($)</option>
                                        <option value="true">Por {labels.coeficiente} (%)</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="label block">Valor Base</label>
                                    <input
                                        type="number"
                                        className="input-field w-full border p-2 rounded"
                                        value={formData.valor_defecto}
                                        onChange={e => setFormData({ ...formData, valor_defecto: e.target.value })}
                                    />
                                </div>
                            </div>

                            {/* NUEVO: CHECKBOX DE COBRO FIJO/PERIODICO */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg flex items-start gap-3">
                                    <input
                                        type="checkbox"
                                        id="esFijoCheck"
                                        className="w-5 h-5 mt-1 text-indigo-600 rounded border-gray-300 focus:ring-indigo-500"
                                        checked={formData.es_fijo}
                                        onChange={e => setFormData({ ...formData, es_fijo: e.target.checked })}
                                    />
                                    <div>
                                        <label htmlFor="esFijoCheck" className="font-bold text-gray-800 cursor-pointer block">
                                            ¿Es un Cobro Fijo?
                                        </label>
                                        <p className="text-[10px] text-gray-500 leading-tight mt-1">
                                            Marcado: Se pre-selecciona siempre (Ej: Administración).
                                            <br />Desmarcado: Novedad ocasional.
                                        </p>
                                    </div>
                                </div>

                                <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
                                    <input
                                        type="checkbox"
                                        id="esInteresCheck"
                                        className="w-5 h-5 mt-1 text-red-600 rounded border-gray-300 focus:ring-red-500"
                                        checked={formData.es_interes}
                                        onChange={e => setFormData({ ...formData, es_interes: e.target.checked })}
                                    />
                                    <div>
                                        <label htmlFor="esInteresCheck" className="font-bold text-red-800 cursor-pointer block">
                                            ¿Es Interés de Mora?
                                        </label>
                                        <p className="text-[10px] text-red-600 leading-tight mt-1">
                                            Marcado: El sistema calcula el valor según días de mora (Smart).
                                            <br />Desmarcado: Cobra el valor fijo definido arriba.
                                        </p>
                                    </div>
                                </div>
                            </div>
                            {/* ------------------------------------- */}

                            <div className="flex justify-end gap-3 mt-6">
                                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded">Cancelar</button>
                                <button type="submit" className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 font-bold flex items-center gap-2">
                                    <FaSave /> Guardar
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}

export default function ConceptosPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-6 text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
                <p className="mt-4 text-gray-600 font-semibold">Cargando conceptos de facturación...</p>
            </div>
        }>
            <ConceptosContent />
        </Suspense>
    );
}

