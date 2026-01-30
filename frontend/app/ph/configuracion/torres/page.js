'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { useRecaudos } from '../../../../contexts/RecaudosContext';
import { phService } from '../../../../lib/phService';
import { FaBuilding, FaPlus, FaEdit, FaTrash, FaSave, FaTimes, FaLayerGroup } from 'react-icons/fa';

export default function GestionTorresPage() {
    const { user, loading: authLoading } = useAuth();
    const { labels } = useRecaudos();

    // States
    const [torres, setTorres] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [currentTorre, setCurrentTorre] = useState(null); // null = creating, object = editing

    // Form State
    const [formData, setFormData] = useState({
        nombre: '',
        descripcion: ''
    });

    useEffect(() => {
        if (!authLoading && user?.empresaId) {
            loadTorres();
        }
    }, [authLoading, user]);

    const loadTorres = async () => {
        try {
            setLoading(true);
            const data = await phService.getTorres();
            setTorres(data);
        } catch (error) {
            console.error("Error loading towers", error);
        } finally {
            setLoading(false);
        }
    };

    const handleOpenModal = (torre = null) => {
        if (torre) {
            setCurrentTorre(torre);
            setFormData({ nombre: torre.nombre, descripcion: torre.descripcion || '' });
        } else {
            setCurrentTorre(null);
            setFormData({ nombre: '', descripcion: '' });
        }
        setIsModalOpen(true);
    };

    const handleCloseModal = () => {
        setIsModalOpen(false);
        setCurrentTorre(null);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            if (currentTorre) {
                await phService.updateTorre(currentTorre.id, formData);
            } else {
                await phService.createTorre(formData);
            }
            loadTorres();
            handleCloseModal();
        } catch (error) {
            alert(`Error al guardar ${labels?.torre?.toLowerCase() || 'torre'}`);
            console.error(error);
        }
    };

    const handleDelete = async (id) => {
        if (window.confirm(`¿Está seguro de eliminar esta ${labels?.torre?.toLowerCase() || 'torre'}?`)) {
            try {
                await phService.deleteTorre(id);
                loadTorres();
            } catch (error) {
                alert('No se pudo eliminar. Verifique que no tenga unidades asociadas.');
            }
        }
    };

    if (loading && !torres.length) return <div className="p-8 text-center text-gray-500">Cargando...</div>;

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="flex justify-between items-center mb-6">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                            <FaLayerGroup className="text-2xl" />
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold text-gray-800">Grupos y {labels?.torre_plural || 'Torres'}</h1>
                            <p className="text-gray-500 text-sm">Organización estructural de la copropiedad.</p>
                        </div>
                    </div>
                    <button
                        onClick={() => handleOpenModal()}
                        className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors shadow-md font-bold"
                    >
                        <FaPlus /> Nueva {labels?.torre || 'Torre'}
                    </button>
                </div>

                {/* List */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Nombre</th>
                                <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Descripción</th>
                                <th className="px-6 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {torres.length === 0 ? (
                                <tr>
                                    <td colSpan="3" className="px-6 py-8 text-center text-gray-400 italic">No hay {labels?.torre_plural?.toLowerCase() || 'torres'} creadas aún.</td>
                                </tr>
                            ) : (
                                torres.map(t => (
                                    <tr key={t.id} className="hover:bg-gray-50">
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 border-l-4 border-l-transparent hover:border-l-indigo-500 transition-all">
                                            <div className="flex items-center gap-2">
                                                <FaBuilding className="text-gray-400" />
                                                {t.nombre}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{t.descripcion || '-'}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                            <button onClick={() => handleOpenModal(t)} className="text-indigo-600 hover:text-indigo-900 mr-3 p-2 hover:bg-indigo-50 rounded-full transition-colors"><FaEdit /></button>
                                            <button onClick={() => handleDelete(t.id)} className="text-red-600 hover:text-red-900 p-2 hover:bg-red-50 rounded-full transition-colors"><FaTrash /></button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Modal */}
                {isModalOpen && (
                    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 animate-fadeIn">
                        <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden transform transition-all scale-100">
                            <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
                                <h3 className="text-lg font-bold text-gray-800">{currentTorre ? `Editar ${labels?.torre || 'Torre'}` : `Nueva ${labels?.torre || 'Torre'}`}</h3>
                                <button onClick={handleCloseModal} className="text-gray-400 hover:text-gray-600"><FaTimes /></button>
                            </div>
                            <form onSubmit={handleSubmit} className="p-6">
                                <div className="space-y-4">
                                    <div>
                                        <label className="block text-sm font-bold text-gray-700 mb-1">Nombre</label>
                                        <input
                                            type="text"
                                            required
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                            placeholder="Ej: Torre A, Bloque 1"
                                            value={formData.nombre}
                                            onChange={e => setFormData({ ...formData, nombre: e.target.value })}
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-bold text-gray-700 mb-1">Descripción</label>
                                        <textarea
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                            placeholder="Detalle opcional..."
                                            rows="3"
                                            value={formData.descripcion}
                                            onChange={e => setFormData({ ...formData, descripcion: e.target.value })}
                                        ></textarea>
                                    </div>
                                </div>
                                <div className="mt-6 flex justify-end gap-3">
                                    <button type="button" onClick={handleCloseModal} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg font-medium">Cancelar</button>
                                    <button type="submit" className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-bold flex items-center gap-2">
                                        <FaSave /> Guardar
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
