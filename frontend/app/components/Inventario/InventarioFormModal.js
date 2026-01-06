'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
    FaSave,
    FaTimes,
    FaBarcode,
    FaTag,
    FaLayerGroup,
    FaPercent,
    FaWarehouse,
    FaMoneyBillWave,
    FaCubes,
    FaSortAmountUp,
    FaSortAmountDown,
    FaInfoCircle
} from 'react-icons/fa';
import { toast } from 'react-toastify';
import { apiService } from '../../../lib/apiService';

// --- ESTILOS REUSABLES (Manual v2.0) ---
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none pl-10";
const inputClassSimple = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white pl-10";

export default function InventarioFormModal({ isOpen, onClose, onSaveSuccess, onSaveError, productoAEditar }) {
    // --- ESTADO INICIAL ---
    const estadoInicial = {
        codigo: '', nombre: '', es_servicio: false, grupo_id: '',
        impuesto_iva_id: '', costo_inicial: 0.0, stock_inicial: 0.0,
        bodega_id_inicial: '', precio_base_manual: '',
        stock_minimo: '', stock_maximo: '',
        valores_caracteristicas: []
    };
    const [formData, setFormData] = useState(estadoInicial);
    const [grupos, setGrupos] = useState([]);
    const [impuestos, setImpuestos] = useState([]);
    const [bodegas, setBodegas] = useState([]);
    const [definicionesGrupo, setDefinicionesGrupo] = useState([]);

    const [activeTab, setActiveTab] = useState('basico'); // Estado para Tabs
    const [isLoadingMaestros, setIsLoadingMaestros] = useState(false);
    const [isLoadingDefs, setIsLoadingDefs] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const modalContentRef = useRef(null);
    const isInitialLoadRef = useRef(true);

    // --- CARGA DE DATOS ---
    const fetchMaestros = useCallback(async () => {
        setIsLoadingMaestros(true);
        try {
            const [gruposRes, impuestosRes, bodegasRes] = await Promise.allSettled([
                apiService.get('/inventario/grupos/'),
                apiService.get('/inventario/tasas-impuesto/'),
                apiService.get('/bodegas/')
            ]);
            setGrupos(gruposRes.status === 'fulfilled' ? gruposRes.value.data : []);
            setImpuestos(impuestosRes.status === 'fulfilled' ? impuestosRes.value.data : []);
            setBodegas(bodegasRes.status === 'fulfilled' ? bodegasRes.value.data : []);
        } catch (err) {
            console.error("Error fetching maestros para modal:", err);
            toast.error("Error al cargar datos necesarios.");
        } finally {
            setIsLoadingMaestros(false);
        }
    }, []);

    const fetchDefiniciones = useCallback(async (grupoId) => {
        setDefinicionesGrupo([]);
        if (!grupoId) return;
        setIsLoadingDefs(true);
        try {
            const response = await apiService.get(`/grupos/${grupoId}/caracteristicas-definicion`);
            setDefinicionesGrupo(response.data || []);
        } catch (err) {
            console.error("Error fetching definiciones for group:", err);
            toast.error("Error al cargar características del grupo.");
        } finally {
            setIsLoadingDefs(false);
        }
    }, []);

    // --- EFECTOS ---
    useEffect(() => {
        if (isOpen) {
            setActiveTab('basico'); // Reset tab al abrir
            isInitialLoadRef.current = true;
            fetchMaestros();
            if (productoAEditar) {
                const dataToEdit = {
                    ...estadoInicial, ...productoAEditar,
                    grupo_id: productoAEditar.grupo_id ?? '',
                    impuesto_iva_id: productoAEditar.impuesto_iva_id ?? '',
                    precio_base_manual: productoAEditar.precio_base_manual ?? '',
                    stock_minimo: productoAEditar.stock_minimo ?? '',
                    stock_maximo: productoAEditar.stock_maximo ?? '',
                    valores_caracteristicas: productoAEditar.valores_caracteristicas?.map(vc => ({
                        definicion_id: parseInt(vc.definicion_id || vc.definicion?.id),
                        valor: vc.valor ?? ''
                    })) || []
                };
                delete dataToEdit.id; delete dataToEdit.empresa_id; delete dataToEdit.fecha_creacion;
                delete dataToEdit.costo_promedio; delete dataToEdit.stocks_bodega;
                delete dataToEdit.stock_total_calculado; delete dataToEdit.grupo_inventario;
                delete dataToEdit.impuesto_iva;
                setFormData(dataToEdit);
                if (dataToEdit.grupo_id) {
                    fetchDefiniciones(dataToEdit.grupo_id);
                } else {
                    setDefinicionesGrupo([]);
                }
            } else {
                setFormData(estadoInicial);
                setDefinicionesGrupo([]);
            }
            setTimeout(() => { modalContentRef.current?.scrollTo(0, 0); isInitialLoadRef.current = false; }, 100);
        }
    }, [isOpen, productoAEditar, fetchMaestros, fetchDefiniciones]);

    useEffect(() => {
        if (isOpen && !isInitialLoadRef.current && formData.grupo_id !== undefined) {
            fetchDefiniciones(formData.grupo_id);

            // --- LÓGICA DE ASIGNACIÓN AUTOMÁTICA DE IMPUESTO ---
            // Buscar el grupo seleccionado para ver si tiene impuesto predeterminado
            const selectedGroup = grupos.find(g => String(g.id) === String(formData.grupo_id));
            if (selectedGroup && selectedGroup.impuesto_predeterminado_id) {
                // Solo actualizamos si encontramos un default válido
                setFormData(prev => ({
                    ...prev,
                    impuesto_iva_id: selectedGroup.impuesto_predeterminado_id
                }));
                // Opcional: Mostrar toast informativo
                // toast.info("Impuesto asignado automáticamente según grupo.");
            }
            // ----------------------------------------------------

            if (String(formData.grupo_id) !== String(productoAEditar?.grupo_id)) {
                setFormData(prev => ({ ...prev, valores_caracteristicas: [] }));
            }
        } else if (isOpen && !isInitialLoadRef.current && !formData.grupo_id) {
            setDefinicionesGrupo([]);
            setFormData(prev => ({ ...prev, valores_caracteristicas: [] }));
        }
    }, [formData.grupo_id, fetchDefiniciones, isOpen, productoAEditar?.grupo_id, grupos]); // Agregué 'grupos' a deps


    // --- MANEJADORES ---
    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleCaracteristicaChange = (definicionId, valor) => {
        setFormData(prev => {
            const idNumerico = parseInt(definicionId);
            const valoresActuales = Array.isArray(prev.valores_caracteristicas) ? prev.valores_caracteristicas : [];
            const existingIndex = valoresActuales.findIndex(vc => vc.definicion_id === idNumerico);
            let newValores;
            if (existingIndex > -1) {
                newValores = [...valoresActuales];
                newValores[existingIndex] = { ...newValores[existingIndex], valor: valor };
            } else {
                newValores = [...valoresActuales, { definicion_id: idNumerico, valor: valor }];
            }
            return { ...prev, valores_caracteristicas: newValores };
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);
        try {
            const payload = { ...formData };
            payload.grupo_id = payload.grupo_id ? parseInt(payload.grupo_id) : null;
            payload.impuesto_iva_id = payload.impuesto_iva_id ? parseInt(payload.impuesto_iva_id) : null;
            payload.bodega_id_inicial = payload.bodega_id_inicial ? parseInt(payload.bodega_id_inicial) : null;
            payload.costo_inicial = parseFloat(payload.costo_inicial) || 0.0;
            payload.stock_inicial = parseFloat(payload.stock_inicial) || 0.0;
            const precioManualNum = parseFloat(payload.precio_base_manual);
            payload.precio_base_manual = payload.precio_base_manual !== '' && !isNaN(precioManualNum) ? precioManualNum : null;
            payload.stock_minimo = parseFloat(payload.stock_minimo) || 0.0;
            payload.stock_maximo = parseFloat(payload.stock_maximo) || 0.0;
            payload.valores_caracteristicas = (Array.isArray(payload.valores_caracteristicas)
                ? payload.valores_caracteristicas.filter(vc => vc.valor && String(vc.valor).trim() !== '')
                : [])
                .map(vc => ({
                    definicion_id: parseInt(vc.definicion_id),
                    valor: String(vc.valor).trim()
                }));

            let savedProducto;
            if (productoAEditar) {
                const updatePayload = { ...payload };
                delete updatePayload.costo_inicial; delete updatePayload.stock_inicial; delete updatePayload.bodega_id_inicial;
                const response = await apiService.put(`/inventario/productos/${productoAEditar.id}`, updatePayload);
                savedProducto = response.data;
            } else {
                const response = await apiService.post('/inventario/productos', payload);
                savedProducto = response.data;
            }
            onSaveSuccess(savedProducto);
        } catch (err) {
            const errorMsg = err.response?.data?.detail || 'Error al guardar el producto.';
            console.error("Error saving producto:", err.response || err);
            toast.error(`Error: ${errorMsg}`);
            if (onSaveError) onSaveError(err);
        } finally {
            setIsSubmitting(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex justify-center items-center z-50 animate-fadeIn p-4">
            <div ref={modalContentRef} className="bg-white rounded-xl shadow-2xl w-full max-w-2xl border border-gray-100 flex flex-col max-h-[90vh]">

                {/* HEADER */}
                <div className="flex justify-between items-center p-6 border-b border-gray-100">
                    <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                        {productoAEditar ? <FaTag className="text-indigo-500" /> : <FaCubes className="text-indigo-500" />}
                        {productoAEditar ? 'Editar Producto' : 'Crear Nuevo Producto'}
                    </h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors text-xl hover:rotate-90 transform duration-200">
                        <FaTimes />
                    </button>
                </div>

                {isLoadingMaestros ? (
                    <div className="p-12 text-center flex flex-col items-center justify-center">
                        <span className="loading loading-spinner loading-lg text-indigo-500 mb-4"></span>
                        <p className="text-gray-500 font-medium">Cargando datos maestros...</p>
                    </div>
                ) : (
                    <form onSubmit={handleSubmit} className="flex flex-col flex-1 overflow-hidden">

                        {/* TABS */}
                        <div className="flex border-b border-gray-200 px-6 pt-4 gap-6">
                            <button
                                type="button"
                                onClick={() => setActiveTab('basico')}
                                className={`pb-3 text-sm font-bold transition-all border-b-2 ${activeTab === 'basico' ? 'text-indigo-600 border-indigo-600' : 'text-gray-500 border-transparent hover:text-indigo-400'}`}
                            >
                                Datos Básicos
                            </button>
                            <button
                                type="button"
                                onClick={() => setActiveTab('inventario')}
                                className={`pb-3 text-sm font-bold transition-all border-b-2 ${activeTab === 'inventario' ? 'text-indigo-600 border-indigo-600' : 'text-gray-500 border-transparent hover:text-indigo-400'}`}
                            >
                                Inventario & Costos
                            </button>
                            <button
                                type="button"
                                onClick={() => setActiveTab('caracteristicas')}
                                className={`pb-3 text-sm font-bold transition-all border-b-2 ${activeTab === 'caracteristicas' ? 'text-indigo-600 border-indigo-600' : 'text-gray-500 border-transparent hover:text-indigo-400'}`}
                            >
                                Características {definicionesGrupo.length > 0 && <span className="ml-1 px-1.5 py-0.5 bg-indigo-100 text-indigo-600 rounded-full text-xs">{definicionesGrupo.length}</span>}
                            </button>
                        </div>

                        {/* CONTENIDO SCROLLABLE */}
                        <div className="p-6 overflow-y-auto flex-1 bg-gray-50">

                            {/* TAB 1: BÁSICO */}
                            {activeTab === 'basico' && (
                                <div className="space-y-6 animate-fadeIn">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div>
                                            <label className={labelClass}>Código <span className="text-red-500">*</span></label>
                                            <div className="relative">
                                                <input type="text" name="codigo" value={formData.codigo} onChange={handleChange} className={inputClass} required autoFocus placeholder="Ej: P-001" />
                                                <FaBarcode className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                            </div>
                                        </div>
                                        <div>
                                            <label className={labelClass}>Nombre <span className="text-red-500">*</span></label>
                                            <div className="relative">
                                                <input type="text" name="nombre" value={formData.nombre} onChange={handleChange} className={inputClass} required placeholder="Ej: Camisa Polo" />
                                                <FaTag className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                            </div>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div>
                                            <label className={labelClass}>Grupo</label>
                                            <div className="relative">
                                                <select name="grupo_id" value={formData.grupo_id || ''} onChange={handleChange} className={selectClass}>
                                                    <option value="">(Sin Grupo)</option>
                                                    {grupos.map(g => <option key={g.id} value={g.id}>{g.nombre}</option>)}
                                                </select>
                                                <FaLayerGroup className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                            </div>
                                        </div>
                                        <div>
                                            <label className={labelClass}>Impuesto IVA</label>
                                            <div className="relative">
                                                <select name="impuesto_iva_id" value={formData.impuesto_iva_id || ''} onChange={handleChange} className={selectClass}>
                                                    <option value="">(Exento / Sin Impuesto)</option>
                                                    {impuestos.map(t => <option key={t.id} value={t.id}>{t.nombre} ({(t.tasa * 100).toFixed(0)}%)</option>)}
                                                </select>
                                                <FaPercent className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                            </div>
                                        </div>
                                    </div>

                                    <div className="bg-indigo-50 p-4 rounded-lg border border-indigo-100 flex items-center">
                                        <input type="checkbox" name="es_servicio" checked={formData.es_servicio} onChange={handleChange} className="checkbox checkbox-primary" />
                                        <div className="ml-3">
                                            <span className="block text-sm font-bold text-indigo-900">¿Es un Servicio?</span>
                                            <span className="text-xs text-indigo-600">Marcar si no maneja stock físico (ej. Mano de obra, Fletes).</span>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* TAB 2: INVENTARIO */}
                            {activeTab === 'inventario' && (
                                <div className="space-y-6 animate-fadeIn">
                                    {formData.es_servicio ? (
                                        <div className="flex flex-col items-center justify-center h-48 text-gray-400">
                                            <FaInfoCircle className="text-4xl mb-2" />
                                            <p>Los servicios no manejan inventario físico.</p>
                                        </div>
                                    ) : (
                                        <>
                                            {/* Solo al crear */}
                                            {!productoAEditar && (
                                                <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm mb-4">
                                                    <h4 className="text-sm font-bold text-gray-700 mb-3 border-b border-gray-100 pb-2">Saldos Iniciales</h4>
                                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                                        <div>
                                                            <label className={labelClass}>Stock Inicial</label>
                                                            <div className="relative">
                                                                <input type="number" step="any" min="0" name="stock_inicial" value={formData.stock_inicial ?? ''} onChange={handleChange} className={inputClass} />
                                                                <FaCubes className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                                            </div>
                                                        </div>
                                                        <div>
                                                            <label className={labelClass}>Costo Unitario</label>
                                                            <div className="relative">
                                                                <input type="number" step="any" min="0" name="costo_inicial" value={formData.costo_inicial ?? ''} onChange={handleChange} className={inputClass} />
                                                                <FaMoneyBillWave className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                                            </div>
                                                        </div>
                                                        <div>
                                                            <label className={labelClass}>Bodega</label>
                                                            <div className="relative">
                                                                <select name="bodega_id_inicial" value={formData.bodega_id_inicial || ''} onChange={handleChange} className={selectClass} disabled={(parseFloat(formData.stock_inicial) || 0) <= 0}>
                                                                    <option value="">{(parseFloat(formData.stock_inicial) || 0) > 0 ? 'Seleccione...' : '(N/A)'}</option>
                                                                    {bodegas.map(b => <option key={b.id} value={b.id}>{b.nombre}</option>)}
                                                                </select>
                                                                <FaWarehouse className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            )}

                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                                <div>
                                                    <label className={labelClass}>Stock Mínimo (Alerta)</label>
                                                    <div className="relative">
                                                        <input type="number" step="any" min="0" name="stock_minimo" value={formData.stock_minimo ?? ''} onChange={handleChange} className={inputClass} />
                                                        <FaSortAmountDown className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                                    </div>
                                                </div>
                                                <div>
                                                    <label className={labelClass}>Stock Máximo</label>
                                                    <div className="relative">
                                                        <input type="number" step="any" min="0" name="stock_maximo" value={formData.stock_maximo ?? ''} onChange={handleChange} className={inputClass} />
                                                        <FaSortAmountUp className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                                    </div>
                                                </div>
                                            </div>
                                        </>
                                    )}

                                    {/* Precio Base (Siempre Visible) */}
                                    <div className="mt-6 pt-4 border-t border-gray-200">
                                        <h4 className="text-sm font-bold text-gray-700 mb-3">Precio de Referencia</h4>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                            <div>
                                                <label className={labelClass}>Precio Base Manual</label>
                                                <div className="relative">
                                                    <input type="number" step="any" min="0" name="precio_base_manual" value={formData.precio_base_manual ?? ''} onChange={handleChange} className={inputClass} placeholder="Opcional" />
                                                    <FaTag className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                                </div>
                                                <p className="text-xs text-gray-400 mt-1 ml-1">Si se deja vacío, se usará el Costo Promedio.</p>
                                            </div>
                                            {productoAEditar && !formData.es_servicio && (
                                                <div>
                                                    <label className={labelClass}>Costo Promedio Actual</label>
                                                    <div className="w-full px-4 py-2 bg-gray-100 border border-gray-200 rounded-lg text-sm font-mono font-bold text-gray-600">
                                                        {(productoAEditar.costo_promedio ?? 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP' })}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* TAB 3: CARACTERÍSTICAS */}
                            {activeTab === 'caracteristicas' && (
                                <div className="space-y-6 animate-fadeIn">
                                    {isLoadingDefs ? (
                                        <div className="text-center p-8 opacity-50"><span className="loading loading-spinner text-sm"></span> Cargando campos...</div>
                                    ) : definicionesGrupo.length > 0 ? (
                                        <div className="grid grid-cols-1 gap-4">
                                            {definicionesGrupo.map(def => (
                                                <div key={def.id}>
                                                    <label className={labelClass}>
                                                        {def.nombre} {def.es_unidad_medida && <span className="text-indigo-500 ml-1">(Unidad)</span>}
                                                    </label>
                                                    <input
                                                        type="text"
                                                        value={(Array.isArray(formData.valores_caracteristicas) ? formData.valores_caracteristicas.find(vc => vc.definicion_id === def.id)?.valor : '') || ''}
                                                        onChange={(e) => handleCaracteristicaChange(def.id, e.target.value)}
                                                        className={inputClassSimple}
                                                        placeholder={`Ingrese ${def.nombre}`}
                                                    />
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <div className="flex flex-col items-center justify-center h-40 text-gray-400 border-2 border-dashed border-gray-200 rounded-xl">
                                            <FaLayerGroup className="text-3xl mb-2 opacity-30" />
                                            <p>Seleccione un Grupo con características definidas para ver opciones aquí.</p>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>

                        {/* FOOTER ACCIONES */}
                        <div className="p-6 bg-white border-t border-gray-100 flex justify-end gap-3">
                            <button type="button" onClick={onClose} className="px-5 py-2 text-gray-600 hover:bg-gray-100 rounded-lg font-medium transition-colors" disabled={isSubmitting}>
                                Cancelar
                            </button>
                            <button type="submit" disabled={isSubmitting || isLoadingMaestros || isLoadingDefs} className="px-8 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg shadow-md font-bold flex items-center gap-2 transition-transform transform hover:-translate-y-0.5 disabled:bg-gray-400">
                                {isSubmitting ? <><span className="loading loading-spinner loading-xs"></span> Guardando...</> : <><FaSave /> Guardar</>}
                            </button>
                        </div>
                    </form>
                )}
            </div>
        </div>
    );
}