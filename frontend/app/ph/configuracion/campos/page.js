'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { FaPlus, FaTrash, FaEdit, FaSave, FaArrowLeft, FaLayerGroup } from 'react-icons/fa';

import { useAuth } from '../../../context/AuthContext';
import { phService } from '../../../../lib/phService';

export default function CamposPersonalizadosPage() {
    const { user, loading: authLoading } = useAuth();
    
    const [campos, setCampos] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    
    const [isEditing, setIsEditing] = useState(false);
    const [currentCampo, setCurrentCampo] = useState({
        entidad: 'unidades',
        etiqueta: '',
        llave_json: '',
        tipo: 'text',
        activo: true
    });

    useEffect(() => {
        if (!authLoading && user?.empresaId) {
            fetchCampos();
        }
    }, [authLoading, user]);

    const fetchCampos = async () => {
        try {
            setLoading(true);
            const data = await phService.getCamposPersonalizados('unidades');
            setCampos(data);
        } catch (err) {
            setError('Error cargando campos personalizados.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleEdit = (campo) => {
        setCurrentCampo(campo);
        setIsEditing(true);
    };

    const handleDelete = async (id) => {
        if (!window.confirm("¿Seguro de eliminar este campo? Las unidades perderán esta información en futuras ediciones.")) return;
        try {
            await phService.deleteCampoPersonalizado(id);
            setCampos(campos.filter(c => c.id !== id));
        } catch (err) {
            alert('Error eliminando campo: ' + err.message);
        }
    };

    const handleSave = async (e) => {
        e.preventDefault();
        try {
            // Auto generar llave_json si esta vacia (solo minúsculas y guiones bajos)
            const payload = { ...currentCampo };
            if (!payload.llave_json) {
                payload.llave_json = payload.etiqueta.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '');
            }

            if (currentCampo.id) {
                const updated = await phService.updateCampoPersonalizado(currentCampo.id, payload);
                setCampos(campos.map(c => c.id === updated.id ? updated : c));
            } else {
                const created = await phService.createCampoPersonalizado(payload);
                setCampos([...campos, created]);
            }
            
            // Reset
            setCurrentCampo({ entidad: 'unidades', etiqueta: '', llave_json: '', tipo: 'text', activo: true });
            setIsEditing(false);
        } catch (err) {
            alert('Error guardando campo: ' + (err.response?.data?.detail || err.message));
        }
    };

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setCurrentCampo(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    if (authLoading || loading) return <p className="p-8 text-center text-gray-500">Cargando...</p>;

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
            <div className="max-w-4xl mx-auto">
                <div className="mb-6 flex justify-between items-center">
                    <div>
                        <Link href="/ph/configuracion" className="flex items-center gap-2 text-indigo-600 hover:text-indigo-800 mb-2 font-semibold">
                            <FaArrowLeft /> Volver a Configuración
                        </Link>
                        <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-3">
                            <FaLayerGroup className="text-pink-600" />
                            Campos Personalizados (Metadata)
                        </h1>
                        <p className="text-gray-500 mt-1 text-sm">Añade campos de información dinámica a tus registros sin necesidad de programación.</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="md:col-span-1">
                        <form onSubmit={handleSave} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 sticky top-6">
                            <h2 className="text-lg font-bold text-gray-700 mb-4 border-b pb-2 flex items-center gap-2">
                                {isEditing ? <><FaEdit /> Editar Campo</> : <><FaPlus /> Nuevo Campo</>}
                            </h2>
                            
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Nombre (Etiqueta)</label>
                                    <input 
                                        type="text" 
                                        name="etiqueta" 
                                        value={currentCampo.etiqueta} 
                                        onChange={handleChange} 
                                        required 
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                                        placeholder="Ej: Placa Vehículo"
                                    />
                                </div>
                                
                                <div>
                                    <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Tipo de Dato</label>
                                    <select 
                                        name="tipo" 
                                        value={currentCampo.tipo} 
                                        onChange={handleChange} 
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                                    >
                                        <option value="text">Texto Corto (Letras y Números)</option>
                                        <option value="number">Número (Cantidades)</option>
                                    </select>
                                </div>

                                {isEditing && (
                                    <div>
                                        <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Llave Interna (Oculto)</label>
                                        <input 
                                            type="text" 
                                            disabled
                                            value={currentCampo.llave_json} 
                                            className="w-full px-4 py-2 border border-gray-200 bg-gray-100 text-gray-500 rounded-lg shadow-sm text-sm"
                                        />
                                    </div>
                                )}

                                <div className="flex items-center gap-2 pt-2">
                                    <input 
                                        type="checkbox" 
                                        name="activo" 
                                        id="activo"
                                        checked={currentCampo.activo} 
                                        onChange={handleChange} 
                                        className="w-4 h-4 text-indigo-600 rounded border-gray-300 focus:ring-indigo-500"
                                    />
                                    <label htmlFor="activo" className="text-sm font-bold text-gray-700 cursor-pointer">Campo Activo (Visible en Formularios)</label>
                                </div>

                                <div className="pt-4 flex gap-2">
                                    <button type="submit" className="flex-1 bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-700 font-bold text-sm transition-colors">
                                        <FaSave className="inline mr-2"/> Guardar
                                    </button>
                                    {isEditing && (
                                        <button type="button" onClick={() => { setIsEditing(false); setCurrentCampo({ entidad: 'unidades', etiqueta: '', llave_json: '', tipo: 'text', activo: true }); }} className="flex-1 bg-gray-200 text-gray-800 py-2 rounded-lg hover:bg-gray-300 font-bold text-sm transition-colors">
                                            Cancelar
                                        </button>
                                    )}
                                </div>
                            </div>
                        </form>
                    </div>

                    <div className="md:col-span-2">
                        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-slate-50">
                                    <tr>
                                        <th className="py-3 px-4 text-left text-xs font-bold text-gray-600 uppercase">Etiqueta</th>
                                        <th className="py-3 px-4 text-left text-xs font-bold text-gray-600 uppercase">Tipo</th>
                                        <th className="py-3 px-4 text-center text-xs font-bold text-gray-600 uppercase">Estado</th>
                                        <th className="py-3 px-4 text-center text-xs font-bold text-gray-600 uppercase">Acciones</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100 bg-white">
                                    {campos.length > 0 ? campos.map(c => (
                                        <tr key={c.id} className="hover:bg-indigo-50 transition-colors">
                                            <td className="py-3 px-4 text-sm font-bold text-gray-800">{c.etiqueta}</td>
                                            <td className="py-3 px-4 text-sm text-gray-500">{c.tipo === 'number' ? 'Número' : 'Texto'}</td>
                                            <td className="py-3 px-4 text-center">
                                                {c.activo ? 
                                                    <span className="bg-green-100 text-green-700 px-2 py-1 rounded-full text-xs font-bold">Activo</span> : 
                                                    <span className="bg-gray-100 text-gray-500 px-2 py-1 rounded-full text-xs font-bold">Inactivo</span>
                                                }
                                            </td>
                                            <td className="py-3 px-4 text-center">
                                                <div className="flex justify-center gap-2">
                                                    <button onClick={() => handleEdit(c)} className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg">
                                                        <FaEdit />
                                                    </button>
                                                    <button onClick={() => handleDelete(c.id)} className="p-2 text-red-600 hover:bg-red-50 rounded-lg">
                                                        <FaTrash />
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    )) : (
                                        <tr>
                                            <td colSpan="4" className="py-8 text-center text-gray-400 italic">No has creado campos dinámicos.</td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
