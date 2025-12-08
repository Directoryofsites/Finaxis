'use client';
import React, { useState, useEffect } from 'react';
import { apiService } from '../../../lib/apiService';
import { FaBoxes, FaPlus, FaSave, FaTimes } from 'react-icons/fa';
import BotonRegresar from '../../components/BotonRegresar';

export default function CategoriasActivosPage() {
    const [categorias, setCategorias] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);

    // Estado del formulario
    const [formData, setFormData] = useState({
        nombre: '',
        vida_util_niif_meses: 0,
        vida_util_fiscal_meses: 0,
        metodo_depreciacion: 'LINEA_RECTA',
        cuenta_activo_id: null,
        cuenta_gasto_depreciacion_id: null,
        cuenta_depreciacion_acumulada_id: null
    });

    useEffect(() => {
        fetchCategorias();
    }, []);

    const fetchCategorias = async () => {
        try {
            const res = await apiService.get('/activos/categorias');
            setCategorias(res.data);
        } catch (error) {
            console.error("Error cargando categorías:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await apiService.post('/activos/categorias', formData);
            setShowModal(false);
            fetchCategorias();
            // Reset form
            setFormData({
                nombre: '',
                vida_util_niif_meses: 0,
                vida_util_fiscal_meses: 0,
                metodo_depreciacion: 'LINEA_RECTA',
                cuenta_activo_id: null,
                cuenta_gasto_depreciacion_id: null,
                cuenta_depreciacion_acumulada_id: null
            });
            alert('Categoría creada exitosamente');
        } catch (error) {
            console.error(error);
            alert('Error al crear la categoría');
        }
    };

    return (
        <div className="p-6 max-w-7xl mx-auto">
            <div className="flex justify-between items-center mb-6">
                <div className="flex items-center gap-4">
                    <BotonRegresar href="/activos" />
                    <h1 className="text-2xl font-bold text-gray-800">Categorías de Activos Fijos</h1>
                </div>
                <button
                    onClick={() => setShowModal(true)}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
                >
                    <FaPlus /> Nueva Categoría
                </button>
            </div>

            {/* LISTA DE CATEGORÍAS */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {categorias.map(cat => (
                    <div key={cat.id} className="bg-white p-5 rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition">
                        <div className="flex items-center gap-3 mb-3">
                            <div className="bg-blue-100 p-3 rounded-full text-blue-600">
                                <FaBoxes className="text-xl" />
                            </div>
                            <h3 className="font-bold text-lg text-gray-800">{cat.nombre}</h3>
                        </div>
                        <div className="text-sm text-gray-600 space-y-1">
                            <p className="flex justify-between">
                                <span>Vida Útil NIIF:</span>
                                <span className="font-semibold">{cat.vida_util_niif_meses} meses</span>
                            </p>
                            <p className="flex justify-between">
                                <span>Vida Útil Fiscal:</span>
                                <span className="font-semibold">{cat.vida_util_fiscal_meses} meses</span>
                            </p>
                            <p className="flex justify-between border-t pt-2 mt-2">
                                <span>Método:</span>
                                <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">{cat.metodo_depreciacion}</span>
                            </p>
                        </div>
                    </div>
                ))}
            </div>

            {/* MODAL CREACIÓN */}
            {showModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white p-6 rounded-lg w-full max-w-lg">
                        <h2 className="text-xl font-bold mb-4">Nueva Categoría de Activo</h2>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Nombre de la Categoría</label>
                                <input
                                    type="text"
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
                                    required
                                    value={formData.nombre}
                                    onChange={e => setFormData({ ...formData, nombre: e.target.value })}
                                    placeholder="Ej: Equipo de Computo y Comunicación"
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Vida Útil NIIF (Meses)</label>
                                    <input
                                        type="number"
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm border p-2"
                                        required
                                        min="0"
                                        value={formData.vida_util_niif_meses}
                                        onChange={e => setFormData({ ...formData, vida_util_niif_meses: parseInt(e.target.value) })}
                                    />
                                    <p className="text-xs text-gray-500 mt-1">Estimación real de uso</p>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Vida Útil Fiscal (Meses)</label>
                                    <input
                                        type="number"
                                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm border p-2"
                                        required
                                        min="0"
                                        value={formData.vida_util_fiscal_meses}
                                        onChange={e => setFormData({ ...formData, vida_util_fiscal_meses: parseInt(e.target.value) })}
                                    />
                                    <p className="text-xs text-gray-500 mt-1">Según tablas de DIAN</p>
                                </div>
                            </div>

                            <div className="flex justify-end gap-3 mt-6">
                                <button
                                    type="button"
                                    onClick={() => setShowModal(false)}
                                    className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 font-medium flex items-center gap-2"
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
