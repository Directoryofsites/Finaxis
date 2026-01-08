'use client';
import React, { useState, useEffect } from 'react';
import {
    getPaquetesRecarga,
    createPaqueteRecarga,
    updatePaqueteRecarga,
    deletePaqueteRecarga
} from '../../../../../lib/soporteApiService';
import { FaPlus, FaEdit, FaTrash, FaCheck, FaTimes, FaSave } from 'react-icons/fa';

export default function GestionPaquetes({ isOpen, onClose }) {
    const [paquetes, setPaquetes] = useState([]);
    const [loading, setLoading] = useState(false);
    const [editingId, setEditingId] = useState(null);
    const [formData, setFormData] = useState({ nombre: '', cantidad_registros: '', precio: '', activo: true });

    // Estado para "Nuevo Paquete"
    const [isCreating, setIsCreating] = useState(false);

    const fetchPaquetes = async () => {
        setLoading(true);
        try {
            const res = await getPaquetesRecarga();
            setPaquetes(res.data);
        } catch (error) {
            console.error(error);
            alert("Error cargando paquetes");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (isOpen) {
            fetchPaquetes();
        }
    }, [isOpen]);

    const resetForm = () => {
        setFormData({ nombre: '', cantidad_registros: '', precio: '', activo: true });
        setEditingId(null);
        setIsCreating(false);
    };

    const handleEdit = (pkg) => {
        setEditingId(pkg.id);
        setFormData({
            nombre: pkg.nombre,
            cantidad_registros: pkg.cantidad_registros,
            precio: pkg.precio,
            activo: pkg.activo
        });
        setIsCreating(true); // Reusamos la vista de creación para editar
    };

    const handleDelete = async (id) => {
        if (!confirm("¿Eliminar este paquete?")) return;
        try {
            await deletePaqueteRecarga(id);
            fetchPaquetes();
        } catch (e) {
            alert("Error eliminando");
        }
    };

    const handleSave = async (e) => {
        e.preventDefault();
        try {
            const payload = {
                ...formData,
                cantidad_registros: parseInt(formData.cantidad_registros),
                precio: parseInt(formData.precio)
            };

            if (editingId) {
                await updatePaqueteRecarga(editingId, payload);
            } else {
                await createPaqueteRecarga(payload);
            }
            fetchPaquetes();
            resetForm();
        } catch (error) {
            alert("Error guardando paquete");
        }
    };

    if (!isOpen) return null;

    return (
        <div className="modal modal-open bg-black/50 backdrop-blur-sm z-50">
            <div className="modal-box w-11/12 max-w-4xl bg-white shadow-2xl rounded-2xl border border-gray-100 p-0">
                {/* Header Integrado */}
                <div className="bg-gray-50 px-6 py-4 border-b flex justify-between items-center rounded-t-2xl">
                    <div>
                        <h3 className="font-bold text-lg text-gray-800">📦 Configuración de Precios y Paquetes</h3>
                        <p className="text-xs text-gray-500">Define las opciones de recarga disponibles para los clientes.</p>
                    </div>
                    <button onClick={onClose} className="btn btn-circle btn-ghost btn-sm text-gray-400 hover:bg-gray-200">
                        <FaTimes />
                    </button>
                </div>

                <div className="p-6">
                    {/* Toolbar Acciones */}
                    <div className="flex justify-between items-center mb-6">
                        <h4 className="text-sm font-bold text-gray-400 uppercase tracking-wider">Paquetes Activos</h4>
                        {!isCreating && (
                            <button onClick={() => setIsCreating(true)} className="btn btn-sm btn-primary gap-2 shadow-sm font-normal">
                                <FaPlus size={12} /> Nuevo Paquete
                            </button>
                        )}
                    </div>

                    {/* Formulario de EDICIÓN / CREACIÓN (Inline pero limpio) */}
                    {isCreating && (
                        <form onSubmit={handleSave} className="bg-indigo-50/50 p-5 rounded-xl border border-indigo-100 grid grid-cols-1 md:grid-cols-12 gap-4 items-end mb-6 animate-fadeIn">
                            <div className="md:col-span-3">
                                <label className="text-xs font-bold text-gray-500 mb-1 block">Nombre Etiqueta</label>
                                <input className="input input-sm w-full input-bordered focus:border-indigo-500"
                                    required autoFocus
                                    value={formData.nombre}
                                    onChange={e => setFormData({ ...formData, nombre: e.target.value })}
                                    placeholder="Ej: Recarga Básica" />
                            </div>
                            <div className="md:col-span-2">
                                <label className="text-xs font-bold text-gray-500 mb-1 block">Registros</label>
                                <input className="input input-sm w-full input-bordered text-center font-mono"
                                    required type="number"
                                    value={formData.cantidad_registros}
                                    onChange={e => setFormData({ ...formData, cantidad_registros: e.target.value })}
                                    placeholder="100" />
                            </div>
                            <div className="md:col-span-3">
                                <label className="text-xs font-bold text-gray-500 mb-1 block">Precio Venta ($)</label>
                                <input className="input input-sm w-full input-bordered text-right font-mono"
                                    required type="number"
                                    value={formData.precio}
                                    onChange={e => setFormData({ ...formData, precio: e.target.value })}
                                    placeholder="15000" />
                            </div>
                            <div className="md:col-span-2 flex items-center justify-center pb-2">
                                <label className="cursor-pointer flex items-center gap-2 select-none">
                                    <input type="checkbox" className="toggle toggle-success toggle-sm"
                                        checked={formData.activo}
                                        onChange={e => setFormData({ ...formData, activo: e.target.checked })} />
                                    <span className="text-xs font-bold text-gray-600">{formData.activo ? 'Visible' : 'Oculto'}</span>
                                </label>
                            </div>
                            <div className="md:col-span-2 flex gap-2">
                                <button type="submit" className="btn btn-sm btn-success text-white w-full shadow-sm"><FaSave /> {editingId ? 'Actualizar' : 'Crear'}</button>
                                <button type="button" onClick={resetForm} className="btn btn-sm btn-ghost btn-square text-gray-400 hover:text-gray-600"><FaTimes /></button>
                            </div>
                        </form>
                    )}

                    {/* Tabla Limpia */}
                    <div className="overflow-hidden rounded-xl border border-gray-100">
                        <table className="table table-sm w-full">
                            <thead className="bg-gray-50 text-gray-500">
                                <tr>
                                    <th className="font-semibold">Nombre del Paquete</th>
                                    <th className="text-center font-semibold">Capacidad (Registros)</th>
                                    <th className="text-right font-semibold">Precio del Paquete</th>
                                    <th className="text-center font-semibold">Estado Dispo.</th>
                                    <th className="text-center font-semibold w-20">Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                {loading ? <tr><td colSpan="5" className="text-center py-8 text-gray-400">Cargando definición de precios...</td></tr> :
                                    paquetes.map(pkg => (
                                        <tr key={pkg.id} className="hover:bg-gray-50 transition-colors group">
                                            <td className="font-medium text-gray-700 py-3">{pkg.nombre}</td>
                                            <td className="text-center font-mono text-gray-600 bg-gray-50/50 rounded m-1">{pkg.cantidad_registros}</td>
                                            <td className="text-right font-mono font-bold text-gray-800">${pkg.precio.toLocaleString()}</td>
                                            <td className="text-center">
                                                {pkg.activo ?
                                                    <span className="badge badge-success badge-xs gap-1 text-white px-2 py-2">Activo</span> :
                                                    <span className="badge badge-ghost badge-xs gap-1 text-gray-400 px-2 py-2">Inactivo</span>
                                                }
                                            </td>
                                            <td className="text-center">
                                                <div className="flex justify-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                    <button onClick={() => handleEdit(pkg)} className="btn btn-xs btn-square btn-ghost text-indigo-500 hover:bg-indigo-50" title="Editar"><FaEdit /></button>
                                                    <button onClick={() => handleDelete(pkg.id)} className="btn btn-xs btn-square btn-ghost text-red-400 hover:bg-red-50" title="Eliminar"><FaTrash /></button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                {paquetes.length === 0 && !loading &&
                                    <tr>
                                        <td colSpan="5" className="text-center py-12">
                                            <div className="flex flex-col items-center gap-2 opacity-50">
                                                <FaEdit size={24} className="text-gray-300" />
                                                <span className="text-sm text-gray-500">No hay paquetes de recarga definidos.</span>
                                                <button onClick={() => setIsCreating(true)} className="btn btn-link btn-xs text-indigo-500 no-underline hover:underline">Crear el primero</button>
                                            </div>
                                        </td>
                                    </tr>
                                }
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
}
