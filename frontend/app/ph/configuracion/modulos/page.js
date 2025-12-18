'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { phService } from '../../../../lib/phService';
import BotonRegresar from '../../../components/BotonRegresar';
import { FaLayerGroup, FaPlus, FaEdit, FaTrash, FaSave, FaTimes } from 'react-icons/fa';

export default function ModulosConfigPage() {
    const { user } = useAuth();
    const [modulos, setModulos] = useState([]);
    const [loading, setLoading] = useState(true);
    const [modalOpen, setModalOpen] = useState(false);
    const [editingId, setEditingId] = useState(null);
    const [formData, setFormData] = useState({
        nombre: '',
        descripcion: '',
        tipo_distribucion: 'COEFICIENTE'
    });

    useEffect(() => {
        loadModulos();
    }, []);

    const loadModulos = async () => {
        setLoading(true);
        try {
            const data = await phService.getModulos();
            setModulos(data);
        } catch (error) {
            console.error("Error loading modules", error);
            alert("Error cargando módulos de contribución.");
        } finally {
            setLoading(false);
        }
    };

    const handleOpenModal = (modulo = null) => {
        if (modulo) {
            setEditingId(modulo.id);
            setFormData({
                nombre: modulo.nombre,
                descripcion: modulo.descripcion || '',
                tipo_distribucion: modulo.tipo_distribucion
            });
        } else {
            setEditingId(null);
            setFormData({
                nombre: '',
                descripcion: '',
                tipo_distribucion: 'COEFICIENTE'
            });
        }
        setModalOpen(true);
    };

    const handleCloseModal = () => {
        setModalOpen(false);
        setEditingId(null);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            if (editingId) {
                await phService.updateModulo(editingId, formData);
            } else {
                await phService.createModulo(formData);
            }
            handleCloseModal();
            loadModulos();
        } catch (error) {
            console.error("Error saving module", error);
            alert("Error al guardar el módulo.");
        }
    };

    const handleDelete = async (id) => {
        if (!confirm('¿Estás seguro de eliminar este módulo?')) return;
        try {
            await phService.deleteModulo(id);
            loadModulos();
        } catch (error) {
            console.error("Error deleting module", error);
            alert("No se puede eliminar el módulo (posiblemente esté en uso).");
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans">
            <div className="max-w-4xl mx-auto">
                <div className="flex justify-between items-center mb-6">
                    <div className="flex items-center gap-4">
                        <BotonRegresar />
                        <div>
                            <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                                <div className="p-2 bg-purple-100 rounded-lg text-purple-600"><FaLayerGroup /></div>
                                Módulos de Contribución
                            </h1>
                            <p className="text-sm text-gray-500">Define sectores para cobros diferenciados (PH Mixta)</p>
                        </div>
                    </div>
                </div>

                {/* INFO CARD */}
                <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-6 rounded-r-lg">
                    <p className="text-sm text-blue-700">
                        <strong>¿Para qué sirve esto?</strong> Aquí defines grupos de unidades que pagan gastos específicos.
                        <br />Ejemplos: <em>"Sector Comercial"</em> (Solo locales), <em>"Torre A"</em> (Solo aptos Torre A), <em>"Parqueaderos"</em>.
                        <br />Luego, asigna cada unidad a sus respectivos módulos en el menú de Unidades.
                    </p>
                </div>

                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                    <div className="flex justify-between items-center mb-4">
                        <h2 className="text-lg font-bold text-gray-700">Listado de Módulos</h2>
                        <button
                            onClick={() => handleOpenModal()}
                            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2 font-medium text-sm transition-colors"
                        >
                            <FaPlus /> Nuevo Módulo
                        </button>
                    </div>

                    {loading ? (
                        <p className="text-center text-gray-500 py-8">Cargando...</p>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-left border-collapse">
                                <thead>
                                    <tr className="bg-gray-50 text-gray-600 uppercase text-xs">
                                        <th className="p-3 font-bold border-b">Nombre</th>
                                        <th className="p-3 font-bold border-b">Descripción</th>
                                        <th className="p-3 font-bold border-b">Distribución</th>
                                        <th className="p-3 font-bold border-b text-right">Acciones</th>
                                    </tr>
                                </thead>
                                <tbody className="text-sm divide-y divide-gray-100">
                                    {modulos.length === 0 ? (
                                        <tr>
                                            <td colSpan="4" className="p-6 text-center text-gray-400 italic">
                                                No hay módulos definidos. Crea el primero como "General" o "Residencial".
                                            </td>
                                        </tr>
                                    ) : (
                                        modulos.map((m) => (
                                            <tr key={m.id} className="hover:bg-gray-50 transition-colors">
                                                <td className="p-3 font-medium text-gray-800">{m.nombre}</td>
                                                <td className="p-3 text-gray-500">{m.descripcion || '-'}</td>
                                                <td className="p-3">
                                                    <span className={`px-2 py-1 rounded-full text-xs font-bold ${m.tipo_distribucion === 'COEFICIENTE' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>
                                                        {m.tipo_distribucion}
                                                    </span>
                                                </td>
                                                <td className="p-3 text-right">
                                                    <div className="flex justify-end gap-2">
                                                        <button
                                                            onClick={() => handleOpenModal(m)}
                                                            className="p-2 text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                                                            title="Editar"
                                                        >
                                                            <FaEdit />
                                                        </button>
                                                        <button
                                                            onClick={() => handleDelete(m.id)}
                                                            className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                                            title="Eliminar"
                                                        >
                                                            <FaTrash />
                                                        </button>
                                                    </div>
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>

            {/* MODAL */}
            {modalOpen && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
                    <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden transform transition-all">
                        <div className="bg-gray-50 px-6 py-4 border-b flex justify-between items-center">
                            <h3 className="text-lg font-bold text-gray-800">
                                {editingId ? 'Editar Módulo' : 'Nuevo Módulo'}
                            </h3>
                            <button onClick={handleCloseModal} className="text-gray-400 hover:text-gray-600">
                                <FaTimes />
                            </button>
                        </div>

                        <form onSubmit={handleSubmit} className="p-6 space-y-4">
                            <div>
                                <label className="block text-sm font-bold text-gray-700 mb-1">Nombre del Sector *</label>
                                <input
                                    required
                                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                                    placeholder="Ej: Sector Locales, Torre B"
                                    value={formData.nombre}
                                    onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-bold text-gray-700 mb-1">Tipo de Distribución</label>
                                <select
                                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none bg-white"
                                    value={formData.tipo_distribucion}
                                    onChange={(e) => setFormData({ ...formData, tipo_distribucion: e.target.value })}
                                >
                                    <option value="COEFICIENTE">Por Coeficiente (Recomendado)</option>
                                    <option value="IGUALITARIO">Igualitario (Todos pagan lo mismo)</option>
                                </select>
                                <p className="text-xs text-gray-500 mt-1">
                                    Define cómo se reparte el gasto entre los miembros de este módulo.
                                </p>
                            </div>

                            <div>
                                <label className="block text-sm font-bold text-gray-700 mb-1">Descripción</label>
                                <textarea
                                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                                    placeholder="Opcional..."
                                    rows="3"
                                    value={formData.descripcion}
                                    onChange={(e) => setFormData({ ...formData, descripcion: e.target.value })}
                                />
                            </div>

                            <div className="pt-4 flex justify-end gap-3">
                                <button
                                    type="button"
                                    onClick={handleCloseModal}
                                    className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg font-medium transition-colors"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 shadow-md font-bold flex items-center gap-2 transition-transform active:scale-95"
                                >
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
