// frontend/app/admin/inventario/parametros/page.js (REPARADO: BOTONES DE GRUPOS ACTIVOS)

'use client';

// 🎨 COMPONENTES DE DISEÑO V2.0
// =============================================================================

import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { apiService } from '../../../../lib/apiService';

import {
    FaTrashAlt, FaPencilAlt, FaTags, FaPercentage,
    FaWarehouse, FaLayerGroup, FaHandHoldingUsd, FaListOl, FaPlus, FaBook
} from 'react-icons/fa';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const TabButton = ({ active, onClick, icon: Icon, label }) => (
    <button
        onClick={onClick}
        className={`flex items-center w-full px-4 py-3 mb-2 text-sm font-medium transition-all duration-200 rounded-lg ${active
            ? 'bg-indigo-600 text-white shadow-md'
            : 'text-gray-600 hover:bg-indigo-50 hover:text-indigo-700'
            }`}
    >
        <Icon className={`mr-3 text-lg ${active ? 'text-indigo-200' : 'text-gray-400'}`} />
        {label}
    </button>
);

const ItemRow = ({ item, extraInfo, actions }) => (
    <div className="flex items-center justify-between p-4 bg-white border border-gray-100 rounded-lg shadow-sm mb-3 hover:shadow-md transition-shadow duration-200">
        <div>
            <h3 className="text-sm font-bold text-gray-800">{item.nombre}</h3>
            {extraInfo && <p className="text-xs text-gray-500 mt-1 font-mono">{extraInfo}</p>}
        </div>
        <div className="flex items-center gap-2">
            {actions}
        </div>
    </div>
);

// =============================================================================
// 🛠️ MODALES SECUNDARIOS (RESTAURADOS)
// =============================================================================

// --- 1. Modal Características ---
const CaracteristicasModal = ({ grupo, onClose }) => {
    const [definiciones, setDefiniciones] = useState([]);
    const [loading, setLoading] = useState(true);
    const [newDefName, setNewDefName] = useState('');
    const [isUnidadMedida, setIsUnidadMedida] = useState(false);
    const [submitting, setSubmitting] = useState(false);

    const fetchDefiniciones = useCallback(async () => {
        if (!grupo?.id) return;
        setLoading(true);
        try {
            const response = await apiService.get(`/grupos/${grupo.id}/caracteristicas-definicion`);
            setDefiniciones(response.data);
        } catch (err) {
            toast.error("Error al cargar características.");
        } finally {
            setLoading(false);
        }
    }, [grupo?.id]);

    useEffect(() => { fetchDefiniciones(); }, [fetchDefiniciones]);

    const handleAdd = async (e) => {
        e.preventDefault();
        if (!newDefName.trim()) return;
        setSubmitting(true);
        try {
            await apiService.post(`/grupos/${grupo.id}/caracteristicas-definicion`, {
                nombre: newDefName.trim(), es_unidad_medida: isUnidadMedida
            });
            toast.success("Característica añadida");
            setNewDefName('');
            setIsUnidadMedida(false);
            fetchDefiniciones();
        } catch (err) {
            toast.error(err.response?.data?.detail || "Error al crear");
        } finally {
            setSubmitting(false);
        }
    };

    const handleDelete = async (id) => {
        if (!confirm("¿Eliminar característica?")) return;
        try {
            await apiService.delete(`/caracteristicas-definicion/${id}`);
            fetchDefiniciones();
            toast.success("Eliminada");
        } catch (err) {
            toast.error("No se puede eliminar (posiblemente en uso).");
        }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex justify-center items-center p-4 backdrop-blur-sm">
            <div className="bg-white rounded-xl shadow-2xl p-6 w-full max-w-lg animate-fadeIn">
                <h2 className="text-lg font-bold text-gray-800 mb-4">Características: {grupo.nombre}</h2>

                <form onSubmit={handleAdd} className="flex gap-2 mb-4 items-end">
                    <div className="flex-grow">
                        <label className="text-xs font-bold text-gray-500 uppercase">Nueva Característica</label>
                        <input type="text" value={newDefName} onChange={e => setNewDefName(e.target.value)} className="input input-bordered input-sm w-full mt-1" placeholder="Ej: Color, Talla" required />
                    </div>
                    <div className="flex flex-col items-center pb-2">
                        <span className="text-[10px] text-gray-500 font-bold mb-1">U. Medida?</span>
                        <input type="checkbox" checked={isUnidadMedida} onChange={e => setIsUnidadMedida(e.target.checked)} className="checkbox checkbox-xs checkbox-primary" />
                    </div>
                    <button type="submit" disabled={submitting} className="btn btn-primary btn-sm"><FaPlus /></button>
                </form>

                <div className="max-h-60 overflow-y-auto border rounded-lg divide-y">
                    {loading ? <div className="p-4 text-center text-sm">Cargando...</div> :
                        definiciones.length === 0 ? <div className="p-4 text-center text-sm text-gray-400">Sin características</div> :
                            definiciones.map(def => (
                                <div key={def.id} className="flex justify-between items-center p-3 hover:bg-gray-50">
                                    <span className="text-sm">
                                        {def.nombre}
                                        {def.es_unidad_medida && <span className="ml-2 badge badge-xs badge-accent">U. Medida</span>}
                                    </span>
                                    <button onClick={() => handleDelete(def.id)} className="text-red-500 hover:text-red-700"><FaTrashAlt /></button>
                                </div>
                            ))}
                </div>
                <div className="mt-4 text-right">
                    <button onClick={onClose} className="btn btn-ghost btn-sm">Cerrar</button>
                </div>
            </div>
        </div>
    );
};

// --- 2. Modal Reglas de Precio ---
const ReglasPrecioModal = ({ grupo, listasPrecio, onClose }) => {
    const [reglas, setReglas] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedLista, setSelectedLista] = useState('');
    const [porcentaje, setPorcentaje] = useState(0);
    const [submitting, setSubmitting] = useState(false);

    const fetchReglas = useCallback(async () => {
        if (!grupo?.id) return;
        setLoading(true);
        try {
            const response = await apiService.get(`/grupos/${grupo.id}/reglas-precio`);
            setReglas(response.data);
        } catch (err) {
            toast.error("Error al cargar reglas.");
        } finally {
            setLoading(false);
        }
    }, [grupo?.id]);

    useEffect(() => { fetchReglas(); }, [fetchReglas]);

    const handleSave = async (e) => {
        e.preventDefault();
        if (!selectedLista) return;
        setSubmitting(true);
        try {
            await apiService.post(`/grupos/${grupo.id}/reglas-precio`, {
                lista_precio_id: parseInt(selectedLista),
                porcentaje_incremento: parseFloat(porcentaje) / 100
            });
            toast.success("Regla guardada");
            fetchReglas();
        } catch (err) {
            toast.error("Error al guardar regla.");
        } finally {
            setSubmitting(false);
        }
    };

    const handleDelete = async (id) => {
        if (!confirm("¿Eliminar regla?")) return;
        try {
            await apiService.delete(`/reglas-precio/${id}`);
            fetchReglas();
            toast.success("Eliminada");
        } catch (err) { toast.error("Error al eliminar"); }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex justify-center items-center p-4 backdrop-blur-sm">
            <div className="bg-white rounded-xl shadow-2xl p-6 w-full max-w-lg animate-fadeIn">
                <h2 className="text-lg font-bold text-gray-800 mb-4">Precios: {grupo.nombre}</h2>

                <form onSubmit={handleSave} className="bg-blue-50 p-3 rounded-lg mb-4 flex gap-2 items-end border border-blue-100">
                    <div className="flex-grow">
                        <label className="text-xs font-bold text-blue-800 uppercase">Lista</label>
                        <select value={selectedLista} onChange={e => setSelectedLista(e.target.value)} className="select select-bordered select-sm w-full mt-1" required>
                            <option value="">Seleccione...</option>
                            {listasPrecio.map(l => <option key={l.id} value={l.id}>{l.nombre}</option>)}
                        </select>
                    </div>
                    <div className="w-24">
                        <label className="text-xs font-bold text-blue-800 uppercase">% Incr.</label>
                        <input type="number" step="0.01" value={porcentaje} onChange={e => setPorcentaje(e.target.value)} className="input input-bordered input-sm w-full mt-1" required />
                    </div>
                    <button type="submit" disabled={submitting} className="btn btn-primary btn-sm">Guardar</button>
                </form>

                <div className="max-h-60 overflow-y-auto border rounded-lg divide-y bg-white">
                    {loading ? <div className="p-4 text-center text-sm">Cargando...</div> :
                        reglas.length === 0 ? <div className="p-4 text-center text-sm text-gray-400">Sin reglas definidas</div> :
                            reglas.map(r => (
                                <div key={r.id} className="flex justify-between items-center p-3 hover:bg-gray-50">
                                    <span className="text-sm font-medium text-gray-700">{r.lista_precio.nombre}</span>
                                    <div className="flex items-center gap-4">
                                        <span className={`font-mono font-bold ${r.porcentaje_incremento >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                            {(r.porcentaje_incremento * 100).toFixed(2)}%
                                        </span>
                                        <button onClick={() => handleDelete(r.id)} className="text-red-400 hover:text-red-600"><FaTrashAlt /></button>
                                    </div>
                                </div>
                            ))}
                </div>
                <div className="mt-4 text-right">
                    <button onClick={onClose} className="btn btn-ghost btn-sm">Cerrar</button>
                </div>
            </div>
        </div>
    );
};


// --- 3. Modal Edición General (Bodegas, Grupos, Impuestos) ---
const EditModal = ({ item, onSave, onClose, titulo, cuentas }) => {
    const [formData, setFormData] = useState({});
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        const initialData = item ? { ...item } : {};
        // Limpieza de datos
        Object.keys(initialData).forEach(key => {
            if (initialData[key] === null && key.includes('_id')) initialData[key] = '';
        });
        if (typeof initialData.tasa === 'number') initialData.tasa = String(initialData.tasa);
        ['impuesto_predeterminado_id', 'caracteristicas_definidas', 'reglas_precio', 'lista_precio'].forEach(k => delete initialData[k]);
        setFormData(initialData);
    }, [item]);

    const handleChange = (e) => setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);
        try {
            const payload = { ...formData };
            Object.keys(payload).forEach(key => {
                if (key.includes('_id') && payload[key] === '') payload[key] = null;
                if (key === 'tasa' && payload[key] !== '') payload[key] = parseFloat(payload[key]);
                else if (key === 'tasa') payload[key] = null;
            });
            ['id', 'empresa_id', 'caracteristicas_definidas', 'reglas_precio'].forEach(k => delete payload[k]);
            await onSave(item.id, payload);
            toast.success('Actualizado correctamente');
            onClose();
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Error al guardar');
        } finally {
            setIsSubmitting(false);
        }
    };

    if (!item) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex justify-center items-center p-4 backdrop-blur-sm">
            <div className="bg-white rounded-xl shadow-2xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto animate-fadeIn">
                <div className="flex justify-between items-center mb-6 border-b pb-4">
                    <h2 className="text-xl font-bold text-gray-800">Editar {titulo.slice(0, -1)}</h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><FaPlus className="rotate-45" /></button>
                </div>
                <form onSubmit={handleSubmit} className="space-y-5">
                    <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-1">Nombre</label>
                        <input type="text" name="nombre" value={formData.nombre || ''} onChange={handleChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none" required />
                    </div>

                    {titulo === 'Grupos de Inventario' && (
                        <>
                            <div className="grid grid-cols-1 gap-4">
                                <div className="bg-gray-50 p-3 rounded-lg border border-gray-200">
                                    <p className="text-xs font-bold text-gray-500 uppercase mb-2">Cuentas Principales</p>
                                    <div className="space-y-3">
                                        <div>
                                            <label className="text-xs text-gray-600">Inventario (Activo)</label>
                                            <select name="cuenta_inventario_id" value={formData.cuenta_inventario_id || ''} onChange={handleChange} className="w-full mt-1 px-3 py-2 border border-gray-300 rounded text-sm bg-white">
                                                <option value="">Seleccione...</option>
                                                {cuentas?.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
                                            </select>
                                        </div>
                                        <div>
                                            <label className="text-xs text-gray-600">Ingresos (Ventas)</label>
                                            <select name="cuenta_ingreso_id" value={formData.cuenta_ingreso_id || ''} onChange={handleChange} className="w-full mt-1 px-3 py-2 border border-gray-300 rounded text-sm bg-white">
                                                <option value="">Seleccione...</option>
                                                {cuentas?.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
                                            </select>
                                        </div>
                                        <div>
                                            <label className="text-xs text-gray-600">Costo de Venta</label>
                                            <select name="cuenta_costo_venta_id" value={formData.cuenta_costo_venta_id || ''} onChange={handleChange} className="w-full mt-1 px-3 py-2 border border-gray-300 rounded text-sm bg-white">
                                                <option value="">Seleccione...</option>
                                                {cuentas?.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
                                            </select>
                                        </div>
                                    </div>
                                </div>
                                <div className="bg-gray-50 p-3 rounded-lg border border-gray-200">
                                    <p className="text-xs font-bold text-gray-500 uppercase mb-2">Ajustes de Inventario</p>
                                    <div className="grid grid-cols-2 gap-3">
                                        <div>
                                            <label className="text-xs text-gray-600">Faltante (Gasto)</label>
                                            <select name="cuenta_ajuste_faltante_id" value={formData.cuenta_ajuste_faltante_id || ''} onChange={handleChange} className="w-full mt-1 px-3 py-2 border border-gray-300 rounded text-sm bg-white">
                                                <option value="">Seleccione...</option>
                                                {cuentas?.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
                                            </select>
                                        </div>
                                        <div>
                                            <label className="text-xs text-gray-600">Sobrante (Ingreso)</label>
                                            <select name="cuenta_ajuste_sobrante_id" value={formData.cuenta_ajuste_sobrante_id || ''} onChange={handleChange} className="w-full mt-1 px-3 py-2 border border-gray-300 rounded text-sm bg-white">
                                                <option value="">Seleccione...</option>
                                                {cuentas?.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
                                            </select>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div className="bg-gray-50 p-3 rounded-lg border border-gray-200 mt-2">
                                <p className="text-xs font-bold text-gray-500 uppercase mb-2">Producción</p>
                                <div>
                                    <label className="text-xs text-gray-600">Cta. Costo Producción (Clase 7)</label>
                                    <select name="cuenta_costo_produccion_id" value={formData.cuenta_costo_produccion_id || ''} onChange={handleChange} className="w-full mt-1 px-3 py-2 border border-gray-300 rounded text-sm bg-white">
                                        <option value="">Seleccione...</option>
                                        {cuentas?.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
                                    </select>
                                </div>
                            </div>
                        </>
                    )}

                    {titulo === 'Tasas de Impuesto' && (
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium">Tasa (Decimal)</label>
                                <input type="number" step="0.01" name="tasa" value={formData.tasa ?? ''} onChange={handleChange} placeholder="Ej: 0.19" className="w-full px-4 py-2 border border-gray-300 rounded-lg" required />
                            </div>
                            <div className="bg-gray-50 p-3 rounded-lg border border-gray-200">
                                <p className="text-xs font-bold text-gray-500 uppercase mb-2">Contabilidad</p>
                                <div className="space-y-3">
                                    <div>
                                        <label className="text-xs text-gray-600">Cta. IVA Generado</label>
                                        <select name="cuenta_id" value={formData.cuenta_id || ''} onChange={handleChange} className="w-full mt-1 px-3 py-2 border border-gray-300 rounded text-sm bg-white">
                                            <option value="">Seleccione...</option>
                                            {cuentas?.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
                                        </select>
                                    </div>
                                    <div>
                                        <label className="text-xs text-gray-600">Cta. IVA Descontable</label>
                                        <select name="cuenta_iva_descontable_id" value={formData.cuenta_iva_descontable_id || ''} onChange={handleChange} className="w-full mt-1 px-3 py-2 border border-gray-300 rounded text-sm bg-white">
                                            <option value="">Seleccione...</option>
                                            {cuentas?.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
                                        </select>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    <div className="flex justify-end gap-3 pt-4 border-t">
                        <button type="button" onClick={onClose} className="px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded-lg">Cancelar</button>
                        <button type="submit" disabled={isSubmitting} className="px-6 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-md disabled:opacity-50">
                            {isSubmitting ? 'Guardando...' : 'Guardar Cambios'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};


// =============================================================================
// 🧠 PÁGINA PRINCIPAL
// =============================================================================

export default function ParametrosInventarioPage() {
    const { user } = useAuth();

    const [activeTab, setActiveTab] = useState('bodegas');
    const [maestros, setMaestros] = useState({ bodegas: [], grupos: [], impuestos: [], cuentas: [], listasPrecio: [] });
    const [loading, setLoading] = useState(true);

    const [inputs, setInputs] = useState({
        bodegas: { nombre: '' },
        grupos: { nombre: '', cuenta_inventario_id: '', cuenta_ingreso_id: '', cuenta_costo_venta_id: '', cuenta_ajuste_faltante_id: '', cuenta_ajuste_sobrante_id: '', cuenta_costo_produccion_id: '' },
        impuestos: { nombre: '', tasa: '', cuenta_id: '', cuenta_iva_descontable_id: '' },
        listasPrecio: { nombre: '' }
    });

    // Estados Modales Principales
    const [itemAEditar, setItemAEditar] = useState(null);
    const [modalTitle, setModalTitle] = useState('');

    // Estados Modales Secundarios
    const [grupoCaracteristicas, setGrupoCaracteristicas] = useState(null);
    const [grupoReglas, setGrupoReglas] = useState(null);

    // Lógica de Carga
    const fetchData = useCallback(async () => {
        setLoading(true);
        try {
            const [bodegasRes, gruposRes, impuestosRes, cuentasRes, listasRes] = await Promise.all([
                apiService.get('/bodegas/'),
                apiService.get('/inventario/grupos/'),
                apiService.get('/inventario/tasas-impuesto/'),
                apiService.get('/plan-cuentas/list-flat/'),
                apiService.get('/listas-precio/')
            ]);
            setMaestros({
                bodegas: bodegasRes.data,
                grupos: gruposRes.data,
                impuestos: impuestosRes.data,
                cuentas: cuentasRes.data,
                listasPrecio: listasRes.data
            });
        } catch (err) {
            console.error(err);
            toast.error("Error cargando parámetros.");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { if (user) fetchData(); }, [user, fetchData]);

    // --- HANDLERS DE APERTURA MODALES SECUNDARIOS (FIX) ---
    const handleOpenCaracteristicas = (grupo) => setGrupoCaracteristicas(grupo);
    const handleOpenReglasPrecio = (grupo) => setGrupoReglas(grupo);

    // --- HANDLERS CRUD ---
    const handleInputChange = (category, field, value) => {
        setInputs(prev => ({ ...prev, [category]: { ...prev[category], [field]: value } }));
    };

    const handleCrear = async (category) => {
        let endpoint = '';
        let payload = { ...inputs[category] };
        let resetState = {};

        if (category === 'bodegas') { endpoint = '/bodegas/'; resetState = { nombre: '' }; }
        else if (category === 'grupos') { endpoint = '/inventario/grupos/'; resetState = { nombre: '', cuenta_inventario_id: '', cuenta_ingreso_id: '', cuenta_costo_venta_id: '', cuenta_ajuste_faltante_id: '', cuenta_ajuste_sobrante_id: '', cuenta_costo_produccion_id: '' }; }
        else if (category === 'impuestos') { endpoint = '/inventario/tasas-impuesto/'; resetState = { nombre: '', tasa: '', cuenta_id: '', cuenta_iva_descontable_id: '' }; }
        else if (category === 'listasPrecio') { endpoint = '/listas-precio/'; resetState = { nombre: '' }; }

        Object.keys(payload).forEach(k => {
            if (k.includes('_id') && payload[k] === '') payload[k] = null;
            if (k === 'tasa' && payload[k]) payload[k] = parseFloat(payload[k]);
        });

        try {
            const res = await apiService.post(endpoint, payload);
            setMaestros(prev => ({ ...prev, [category]: [...prev[category], res.data] }));
            setInputs(prev => ({ ...prev, [category]: resetState }));
            toast.success("Creado exitosamente");
        } catch (err) {
            toast.error(err.response?.data?.detail || "Error al crear");
        }
    };

    const handleDelete = async (id, category, endpointBase) => {
        if (!window.confirm("¿Eliminar este elemento?")) return;
        try {
            await apiService.delete(`${endpointBase}/${id}`);
            setMaestros(prev => ({ ...prev, [category]: prev[category].filter(i => i.id !== id) }));
            toast.success("Eliminado");
        } catch (err) {
            toast.error(err.response?.data?.detail || "Error al eliminar");
        }
    };

    const handleSaveEdit = async (id, payload) => {
        let endpoint = '';
        let category = '';

        if (modalTitle === 'Bodegas') { endpoint = `/bodegas/${id}`; category = 'bodegas'; }
        else if (modalTitle === 'Grupos de Inventario') { endpoint = `/inventario/grupos/${id}`; category = 'grupos'; }
        else if (modalTitle === 'Tasas de Impuesto') { endpoint = `/inventario/tasas-impuesto/${id}`; category = 'impuestos'; }
        else if (modalTitle === 'Listas de Precios') { endpoint = `/listas-precio/${id}`; category = 'listasPrecio'; }

        try {
            const res = await apiService.put(endpoint, payload);
            setMaestros(prev => ({
                ...prev,
                [category]: prev[category].map(i => i.id === id ? res.data : i)
            }));
        } catch (err) { throw err; }
    };

    const renderContent = () => {
        switch (activeTab) {
            case 'bodegas':
                return (
                    <div className="animate-fadeIn">
                        <h2 className="text-xl font-bold text-gray-800 mb-4">Gestión de Bodegas</h2>
                        <div className="flex gap-2 mb-6">
                            <input type="text" placeholder="Nombre de nueva bodega" className="input input-bordered w-full max-w-md" value={inputs.bodegas.nombre} onChange={e => handleInputChange('bodegas', 'nombre', e.target.value)} />
                            <button onClick={() => handleCrear('bodegas')} className="btn btn-primary"><FaPlus /> Crear</button>
                        </div>
                        <div className="grid gap-3">
                            {maestros.bodegas.map(b => (
                                <ItemRow
                                    key={b.id} item={b}
                                    actions={
                                        <>
                                            <button onClick={() => { setItemAEditar(b); setModalTitle('Bodegas'); }} className="btn btn-ghost btn-sm text-indigo-600"><FaPencilAlt /></button>
                                            <button onClick={() => handleDelete(b.id, 'bodegas', '/bodegas')} className="btn btn-ghost btn-sm text-red-600"><FaTrashAlt /></button>
                                        </>
                                    }
                                />
                            ))}
                        </div>
                    </div>
                );

            case 'grupos':
                return (
                    <div className="animate-fadeIn">
                        <h2 className="text-xl font-bold text-gray-800 mb-4">Grupos de Inventario</h2>
                        <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 mb-6">
                            <h3 className="text-sm font-bold text-gray-600 mb-3 uppercase">Nuevo Grupo</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
                                <input type="text" placeholder="Nombre del Grupo" className="input input-bordered w-full" value={inputs.grupos.nombre} onChange={e => handleInputChange('grupos', 'nombre', e.target.value)} />
                                <select className="select select-bordered w-full" value={inputs.grupos.cuenta_ingreso_id} onChange={e => handleInputChange('grupos', 'cuenta_ingreso_id', e.target.value)}>
                                    <option value="">Cta. Ingresos (Venta)...</option>
                                    {maestros.cuentas.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
                                </select>
                            </div>
                            <button onClick={() => handleCrear('grupos')} className="btn btn-primary w-full md:w-auto"><FaPlus /> Crear Grupo</button>
                        </div>
                        <div className="grid gap-3">
                            {maestros.grupos.map(g => (
                                <ItemRow
                                    key={g.id} item={g}
                                    extraInfo="Configuración contable y características"
                                    actions={
                                        <>
                                            {/* BOTONES REPARADOS CON ONCLICK */}
                                            <button onClick={() => handleOpenCaracteristicas(g)} className="btn btn-ghost btn-xs text-gray-500 tooltip" data-tip="Características"><FaTags /></button>
                                            <button onClick={() => handleOpenReglasPrecio(g)} className="btn btn-ghost btn-xs text-gray-500 tooltip" data-tip="Reglas Precio"><FaPercentage /></button>
                                            <div className="divider divider-horizontal m-0"></div>
                                            <button onClick={() => { setItemAEditar(g); setModalTitle('Grupos de Inventario'); }} className="btn btn-ghost btn-sm text-indigo-600"><FaPencilAlt /></button>
                                            <button onClick={() => handleDelete(g.id, 'grupos', '/inventario/grupos')} className="btn btn-ghost btn-sm text-red-600"><FaTrashAlt /></button>
                                        </>
                                    }
                                />
                            ))}
                        </div>
                    </div>
                );

            case 'impuestos':
                return (
                    <div className="animate-fadeIn">
                        <h2 className="text-xl font-bold text-gray-800 mb-4">Tasas de Impuesto</h2>
                        <div className="flex gap-2 mb-6 items-end">
                            <div className="flex-grow">
                                <label className="text-xs font-bold ml-1">Nombre</label>
                                <input type="text" placeholder="Ej: IVA 19%" className="input input-bordered w-full" value={inputs.impuestos.nombre} onChange={e => handleInputChange('impuestos', 'nombre', e.target.value)} />
                            </div>
                            <div className="w-32">
                                <label className="text-xs font-bold ml-1">Tasa (0-1)</label>
                                <input type="number" step="0.01" placeholder="0.19" className="input input-bordered w-full" value={inputs.impuestos.tasa} onChange={e => handleInputChange('impuestos', 'tasa', e.target.value)} />
                            </div>
                            <button onClick={() => handleCrear('impuestos')} className="btn btn-primary"><FaPlus /> Agregar</button>
                        </div>
                        <div className="grid gap-3">
                            {maestros.impuestos.map(t => (
                                <ItemRow
                                    key={t.id} item={t}
                                    extraInfo={`Tasa: ${(t.tasa * 100).toFixed(0)}%`}
                                    actions={
                                        <>
                                            <button onClick={() => { setItemAEditar(t); setModalTitle('Tasas de Impuesto'); }} className="btn btn-ghost btn-sm text-indigo-600"><FaPencilAlt /></button>
                                            <button onClick={() => handleDelete(t.id, 'impuestos', '/inventario/tasas-impuesto')} className="btn btn-ghost btn-sm text-red-600"><FaTrashAlt /></button>
                                        </>
                                    }
                                />
                            ))}
                        </div>
                    </div>
                );

            case 'listas':
                return (
                    <div className="animate-fadeIn">
                        <h2 className="text-xl font-bold text-gray-800 mb-4">Listas de Precios</h2>
                        <div className="flex gap-2 mb-6">
                            <input type="text" placeholder="Nombre de la lista (Ej: Mayorista)" className="input input-bordered w-full max-w-md" value={inputs.listasPrecio.nombre} onChange={e => handleInputChange('listasPrecio', 'nombre', e.target.value)} />
                            <button onClick={() => handleCrear('listasPrecio')} className="btn btn-primary"><FaPlus /> Crear</button>
                        </div>
                        <div className="grid gap-3">
                            {maestros.listasPrecio.map(l => (
                                <ItemRow
                                    key={l.id} item={l}
                                    actions={
                                        <>
                                            <button onClick={() => { setItemAEditar(l); setModalTitle('Listas de Precios'); }} className="btn btn-ghost btn-sm text-indigo-600"><FaPencilAlt /></button>
                                            <button onClick={() => handleDelete(l.id, 'listasPrecio', '/listas-precio')} className="btn btn-ghost btn-sm text-red-600"><FaTrashAlt /></button>
                                        </>
                                    }
                                />
                            ))}
                        </div>
                    </div>
                );
            default: return null;
        }
    };

    if (loading) return <div className="text-center mt-20"><span className="loading loading-spinner loading-lg text-primary"></span></div>;

    return (
        <div className="container mx-auto p-4 md:p-8 bg-gray-50 min-h-screen font-sans">
            <ToastContainer position="top-right" autoClose={3000} />

            <div className="flex justify-between items-center mb-8">
                <div>
                    <div className="flex items-center gap-3">
                        <h1 className="text-3xl font-bold text-gray-800">Configuración de Inventario</h1>
                        <button
                            onClick={() => window.open('/manual/capitulo_39_parametros_inventario.html', '_blank')}
                            className="flex items-center gap-2 px-2 py-1 bg-white border border-indigo-200 text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors font-medium shadow-sm"
                        >
                            <FaBook /> <span className="hidden md:inline">Manual</span>
                        </button>
                    </div>
                    <p className="text-gray-500 mt-1">Administra los parámetros maestros del sistema.</p>
                </div>
                <div className="flex gap-2">
                    {/* Actions consolidated */}
                </div>
            </div>

            <div className="flex flex-col lg:flex-row gap-8 items-start">
                <div className="w-full lg:w-64 flex-shrink-0">
                    <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-4 sticky top-4">
                        <h3 className="text-xs font-bold text-gray-400 uppercase mb-3 px-2 tracking-wider">Menú</h3>
                        <TabButton active={activeTab === 'bodegas'} onClick={() => setActiveTab('bodegas')} icon={FaWarehouse} label="Bodegas" />
                        <TabButton active={activeTab === 'grupos'} onClick={() => setActiveTab('grupos')} icon={FaLayerGroup} label="Grupos" />
                        <TabButton active={activeTab === 'impuestos'} onClick={() => setActiveTab('impuestos')} icon={FaHandHoldingUsd} label="Impuestos" />
                        <TabButton active={activeTab === 'listas'} onClick={() => setActiveTab('listas')} icon={FaListOl} label="Listas de Precio" />
                    </div>
                </div>

                <div className="flex-grow w-full">
                    <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 md:p-8 min-h-[500px]">
                        {renderContent()}
                    </div>
                </div>
            </div>

            {/* MODALES */}
            {itemAEditar && <EditModal item={itemAEditar} onSave={handleSaveEdit} onClose={() => setItemAEditar(null)} titulo={modalTitle} cuentas={maestros.cuentas} />}
            {/* RENDERIZADO DE MODALES SECUNDARIOS (ANTES FALTABAN) */}
            {grupoCaracteristicas && <CaracteristicasModal grupo={grupoCaracteristicas} onClose={() => setGrupoCaracteristicas(null)} />}
            {grupoReglas && <ReglasPrecioModal grupo={grupoReglas} listasPrecio={maestros.listasPrecio} onClose={() => setGrupoReglas(null)} />}
        </div>
    );
}