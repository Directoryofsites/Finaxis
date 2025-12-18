"use client";
import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { FaCog, FaSave, FaPlus, FaEdit, FaTrash, FaCheck, FaTimes, FaMoneyCheckAlt, FaArrowLeft, FaFileInvoiceDollar, FaCalculator } from 'react-icons/fa';
import Link from 'next/link';

// Services
import { getTiposNomina, createTipoNomina, updateTipoNomina, deleteTipoNomina, getConfig, saveConfig } from '../../../lib/nominaService';
import { getPlanCuentasFlat } from '../../../lib/planCuentasService';
import { apiService } from '../../../lib/apiService';

export default function NominaConfiguracion() {
    // State: Tipos
    const [tipos, setTipos] = useState([]);
    const [loading, setLoading] = useState(false);

    // State: Modal & Editing
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingTipo, setEditingTipo] = useState(null); // Full object
    const [activeTab, setActiveTab] = useState('general'); // 'general' | 'contabilidad'

    // State: Config Data
    const [cuentas, setCuentas] = useState([]);
    const [tiposDoc, setTiposDoc] = useState([]);
    const [currentConfig, setCurrentConfig] = useState({});

    // Forms
    const { register, handleSubmit, reset, setValue, formState: { errors } } = useForm();

    // -- INITIAL LOAD --
    useEffect(() => {
        loadInitialData();
    }, []);

    const loadInitialData = async () => {
        setLoading(true);
        try {
            await Promise.all([
                fetchTipos(),
                fetchMasterData()
            ]);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const fetchTipos = async () => {
        try {
            const data = await getTiposNomina();
            setTipos(data);
        } catch (error) {
            toast.error("Error al cargar tipos de nómina");
        }
    };

    const fetchMasterData = async () => {
        try {
            const resCuentas = await getPlanCuentasFlat();
            setCuentas(Array.isArray(resCuentas.data) ? resCuentas.data : []);

            const resTipos = await apiService.get('/tipos-documento');
            setTiposDoc(resTipos.data || []);
        } catch (e) {
            console.error("Error loading master data", e);
        }
    };

    // -- ACTIONS --

    const openNew = () => {
        setEditingTipo(null);
        reset();
        setValue('periodo_pago', 'Mensual');
        setCurrentConfig({}); // Reset config for new type (though config tab disabled until created? No, let's allow basic creation first)
        setActiveTab('general');
        setIsModalOpen(true);
    };

    const handleEdit = async (tipo) => {
        setEditingTipo(tipo);
        setActiveTab('general');

        // Fill General Form
        setValue('nombre', tipo.nombre);
        setValue('descripcion', tipo.descripcion);
        setValue('periodo_pago', tipo.periodo_pago);

        // Load Config for this Type
        try {
            const configData = await getConfig({ tipo_nomina_id: tipo.id });
            // Map nulls to '' for inputs
            const mapped = {};
            // Keys from backend schema
            const keys = [
                'tipo_documento_id', 'cuenta_sueldo_id', 'cuenta_auxilio_transporte_id',
                'cuenta_horas_extras_id', 'cuenta_comisiones_id', 'cuenta_salarios_por_pagar_id',
                'cuenta_aporte_salud_id', 'cuenta_aporte_pension_id', 'cuenta_fondo_solidaridad_id',
                'cuenta_otros_devengados_id', 'cuenta_otras_deducciones_id'
            ];
            keys.forEach(k => mapped[k] = configData[k] || '');
            setCurrentConfig(mapped);
        } catch (e) {
            toast.error("Error cargando configuración contable");
        }

        setIsModalOpen(true);
    };

    const handleDelete = async (id) => {
        if (!confirm("¿Seguro que deseas eliminar este tipo de nómina?")) return;
        try {
            await deleteTipoNomina(id);
            toast.success("Eliminado correctamente");
            fetchTipos();
        } catch (error) {
            toast.error(error.response?.data?.detail || "Error al eliminar");
        }
    };

    // -- SUBMIT HANDLERS --

    const onSubmitGeneral = async (data) => {
        try {
            let savedTipo;
            if (editingTipo) {
                savedTipo = await updateTipoNomina(editingTipo.id, data);
                toast.success("Datos básicos actualizados");
            } else {
                savedTipo = await createTipoNomina(data);
                toast.success("Tipo de nómina creado");
                // Switch to edit mode for the new type to allow config
                setEditingTipo(savedTipo);
            }
            fetchTipos();
            // Don't close modal, maybe user wants to edit config next
            // But if it was new, we might want to stay open. 
            if (!editingTipo) {
                // For UX, if new, maybe ask or just stay on general?
                // Let's stay and let them switch tabs
            }
        } catch (error) {
            toast.error("Error al guardar datos generales");
        }
    };

    const handleSaveConfig = async (e) => {
        e.preventDefault();
        if (!editingTipo) {
            toast.warn("Primero debes crear el Tipo de Nómina (Pestaña General)");
            return;
        }

        try {
            // Convert empty strings to null
            const payload = { ...currentConfig, tipo_nomina_id: editingTipo.id };
            Object.keys(payload).forEach(k => {
                if (payload[k] === '') payload[k] = null;
                else if (k !== 'tipo_nomina_id') payload[k] = parseInt(payload[k]);
            });

            await saveConfig(payload);
            toast.success("Configuración Contable Guardada");
        } catch (err) {
            toast.error("Error al guardar configuración");
        }
    };

    const handleConfigChange = (e) => {
        setCurrentConfig({ ...currentConfig, [e.target.name]: e.target.value });
    };

    // -- RENDER HELPERS --
    const renderConfigSelect = (label, name, help) => (
        <div className="mb-4">
            <label className="block text-sm font-bold text-gray-700 mb-1">{label}</label>
            <select name={name} value={currentConfig[name] || ''} onChange={handleConfigChange}
                className="w-full border p-2 rounded focus:ring-2 focus:ring-blue-500 bg-white text-sm">
                <option value="">-- Seleccionar Cuenta --</option>
                {cuentas.map(cta => (
                    <option key={cta.id} value={cta.id}>
                        {cta.codigo} - {cta.nombre}
                    </option>
                ))}
            </select>
            {help && <p className="text-xs text-gray-400 mt-1">{help}</p>}
        </div>
    );

    return (
        <div className="p-6 max-w-6xl mx-auto">
            <ToastContainer />

            {/* API HEADER */}
            <div className="flex justify-between items-center mb-8 border-b pb-4">
                <div>
                    <h1 className="text-2xl font-light text-gray-800 flex items-center gap-2">
                        <FaCog className="text-gray-500" /> Configuración de Nómina
                    </h1>
                    <p className="text-gray-500 text-sm mt-1">Define los Tipos de Nómina y su contabilización automática.</p>
                </div>
                <button onClick={openNew} className="bg-blue-600 text-white px-4 py-2 rounded shadow hover:bg-blue-700 flex items-center font-bold">
                    <FaPlus className="mr-2" /> Nuevo Tipo
                </button>
            </div>

            {/* TYPES GRID */}
            {loading ? (
                <div className="text-center py-10 text-gray-400">Cargando configuración...</div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {tipos.map(tipo => (
                        <div key={tipo.id} className="bg-white rounded-lg shadow border border-gray-100 p-6 hover:shadow-md transition relative group">
                            <div className="absolute top-4 right-4 flex space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button onClick={() => handleEdit(tipo)} className="text-blue-500 hover:text-blue-700 bg-blue-50 p-2 rounded-full">
                                    <FaEdit />
                                </button>
                                <button onClick={() => handleDelete(tipo.id)} className="text-red-400 hover:text-red-600 bg-red-50 p-2 rounded-full">
                                    <FaTrash />
                                </button>
                            </div>

                            <div className="flex items-center mb-4">
                                <div className={`p-3 rounded-full mr-4 ${tipo.periodo_pago === 'Mensual' ? 'bg-green-100 text-green-600' : 'bg-purple-100 text-purple-600'}`}>
                                    <FaMoneyCheckAlt size={24} />
                                </div>
                                <div>
                                    <h3 className="text-lg font-bold text-gray-800">{tipo.nombre}</h3>
                                    <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">{tipo.periodo_pago}</span>
                                </div>
                            </div>
                            <p className="text-gray-500 text-sm h-10 line-clamp-2 mb-4">{tipo.descripcion || 'Sin descripción'}</p>
                            <button onClick={() => handleEdit(tipo)} className="text-blue-600 text-sm font-bold hover:underline">
                                Configurar Cuentas &rarr;
                            </button>
                        </div>
                    ))}
                    {tipos.length === 0 && (
                        <div className="col-span-full text-center py-12 bg-gray-50 rounded-lg border border-dashed border-gray-300">
                            <p className="text-gray-400 mb-4">No hay tipos de nómina creados.</p>
                            <button onClick={openNew} className="text-blue-600 font-bold hover:underline">Crear el primero</button>
                        </div>
                    )}
                </div>
            )}

            {/* MODAL */}
            {isModalOpen && (
                <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
                    <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
                        {/* Modal Header */}
                        <div className="px-8 py-5 border-b border-gray-100 flex justify-between items-center bg-gray-50">
                            <h2 className="text-xl font-bold text-gray-800">
                                {editingTipo ? `Editar: ${editingTipo.nombre}` : 'Nuevo Tipo de Nómina'}
                            </h2>
                            <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                                <FaTimes size={20} />
                            </button>
                        </div>

                        {/* Tabs */}
                        <div className="flex border-b border-gray-200 px-8">
                            <button
                                onClick={() => setActiveTab('general')}
                                className={`py-4 px-6 font-bold text-sm border-b-2 transition ${activeTab === 'general' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
                            >
                                1. Datos Generales
                            </button>
                            <button
                                onClick={() => setActiveTab('contabilidad')}
                                disabled={!editingTipo}
                                className={`py-4 px-6 font-bold text-sm border-b-2 transition ${activeTab === 'contabilidad' ? 'border-purple-500 text-purple-600' : 'border-transparent text-gray-500 hover:text-gray-700'} ${!editingTipo ? 'opacity-50 cursor-not-allowed' : ''}`}
                            >
                                2. Contabilidad (PUC)
                            </button>
                        </div>

                        {/* Modal Content - Scrollable */}
                        <div className="flex-1 overflow-y-auto p-8 bg-gray-50/50">

                            {/* TAB: GENERAL */}
                            {activeTab === 'general' && (
                                <form onSubmit={handleSubmit(onSubmitGeneral)} className="space-y-6 max-w-lg mx-auto bg-white p-8 rounded shadow-sm border border-gray-100">
                                    <div>
                                        <label className="block text-sm font-bold text-gray-700 mb-1">Nombre <span className="text-red-500">*</span></label>
                                        <input
                                            {...register('nombre', { required: "El nombre es obligatorio" })}
                                            className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none"
                                            placeholder="Ej: Administrativa"
                                        />
                                        {errors.nombre && <span className="text-red-500 text-xs">{errors.nombre.message}</span>}
                                    </div>
                                    <div>
                                        <label className="block text-sm font-bold text-gray-700 mb-1">Descripción</label>
                                        <textarea
                                            {...register('descripcion')}
                                            className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none h-24 resize-none"
                                            placeholder="Descripción opcional..."
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-bold text-gray-700 mb-1">Periodo de Pago</label>
                                        <select
                                            {...register('periodo_pago')}
                                            className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none bg-white"
                                        >
                                            <option value="Mensual">Mensual</option>
                                            <option value="Quincenal">Quincenal</option>
                                        </select>
                                    </div>
                                    <div className="pt-4 flex justify-end">
                                        <button type="submit" className="bg-blue-600 text-white px-6 py-2 rounded font-bold shadow hover:bg-blue-700 transition">
                                            {editingTipo ? 'Actualizar Datos' : 'Crear y Continuar'}
                                        </button>
                                    </div>
                                </form>
                            )}

                            {/* TAB: CONTABILIDAD */}
                            {activeTab === 'contabilidad' && editingTipo && (
                                <form onSubmit={handleSaveConfig} className="space-y-6">
                                    <div className="bg-white p-6 rounded shadow border-l-4 border-gray-500 mb-6">
                                        <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center"><FaFileInvoiceDollar className="mr-2" /> Documento Contable</h3>
                                        <div>
                                            <label className="block text-sm font-bold text-gray-700 mb-1">Tipo de Documento</label>
                                            <select name="tipo_documento_id" value={currentConfig.tipo_documento_id || ''} onChange={handleConfigChange}
                                                className="w-full border p-2 rounded focus:ring-2 focus:ring-blue-500 bg-white">
                                                <option value="">-- Seleccionar Tipo --</option>
                                                {tiposDoc.map(td => (
                                                    <option key={td.id} value={td.id}>{td.codigo} - {td.nombre}</option>
                                                ))}
                                            </select>
                                            <p className="text-xs text-gray-400 mt-1">Se usará para generar los comprobantes de esta nómina.</p>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div className="bg-white p-6 rounded shadow border-l-4 border-blue-500">
                                            <h3 className="text-lg font-bold text-blue-800 mb-4 flex items-center"><FaCalculator className="mr-2" /> Gastos (Débito)</h3>
                                            {renderConfigSelect("Sueldos (Salario Base)", "cuenta_sueldo_id")}
                                            {renderConfigSelect("Auxilio de Transporte", "cuenta_auxilio_transporte_id")}
                                            {renderConfigSelect("Horas Extras y Recargos", "cuenta_horas_extras_id")}
                                            {renderConfigSelect("Comisiones", "cuenta_comisiones_id")}
                                            {renderConfigSelect("Otros Devengados", "cuenta_otros_devengados_id", "Bonificaciones no salariales, Auxilios extra, etc.")}
                                        </div>

                                        <div className="bg-white p-6 rounded shadow border-l-4 border-red-500">
                                            <h3 className="text-lg font-bold text-red-800 mb-4 flex items-center"><FaMoneyCheckAlt className="mr-2" /> Pasivos (Crédito)</h3>
                                            {renderConfigSelect("Saldos por Pagar (Neto)", "cuenta_salarios_por_pagar_id")}
                                            {renderConfigSelect("Aporte Salud (Total)", "cuenta_aporte_salud_id")}
                                            {renderConfigSelect("Aporte Pensión (Total)", "cuenta_aporte_pension_id")}
                                            {renderConfigSelect("Fondo Solidaridad", "cuenta_fondo_solidaridad_id")}
                                            {renderConfigSelect("Otras Deducciones", "cuenta_otras_deducciones_id", "Libranzas, Préstamos, etc.")}
                                        </div>
                                    </div>

                                    <div className="flex justify-end pt-4">
                                        <button type="submit" className="bg-green-600 text-white px-8 py-3 rounded font-bold shadow hover:bg-green-700 transition flex items-center">
                                            <FaSave className="mr-2" /> Guardar Configuración Contable
                                        </button>
                                    </div>
                                </form>
                            )}

                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
