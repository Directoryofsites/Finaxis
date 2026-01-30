"use client";
import React, { useState, useEffect } from 'react';
import { FaPlus, FaTrash, FaEdit, FaCalculator, FaChartLine } from 'react-icons/fa';
import { useAuth } from '../../context/AuthContext';
import PresupuestoGrid from './PresupuestoGrid';
import ReporteEjecucion from './ReporteEjecucion';

import { apiService } from '../../../lib/apiService';
import { toast } from 'react-hot-toast';

export default function EscenariosList({ onSelectEscenario }) {
    const { user } = useAuth();

    // UI State
    const [escenarios, setEscenarios] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);

    // View State
    const [selectedEscenario, setSelectedEscenario] = useState(null);
    const [selectedReporte, setSelectedReporte] = useState(null);

    // Form State
    const [newItem, setNewItem] = useState({
        nombre: '',
        anio: new Date().getFullYear() + 1,
        tipo_sector: 'PRIVADO'
    });

    const fetchEscenarios = async () => {
        try {
            if (!user?.empresa_id) return;
            const res = await apiService.get(`/presupuesto/escenarios`, { params: { empresa_id: user.empresa_id } });
            setEscenarios(res.data);
        } catch (error) {
            console.error(error);
            toast.error("Error cargando escenarios");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchEscenarios();
    }, [user?.empresa_id]);

    const handleCreate = async () => {
        const empresaId = user?.empresa_id;
        if (!empresaId) {
            toast.error("Error: No hay una empresa activa identificada en la sesión.");
            return;
        }

        try {
            const response = await apiService.post(`/presupuesto/escenarios`, newItem, { params: { empresa_id: empresaId } });
            toast.success("Escenario creado");
            setShowModal(false);
            fetchEscenarios();
            setNewItem({ ...newItem, nombre: '' }); // Reset partial
        } catch (error) {
            console.error(error);
            const msg = error.response?.data?.detail || "Error creando escenario";
            toast.error(msg);
        }
    };

    const handleDelete = async (id, nombre) => {
        if (!window.confirm(`¿Estás seguro de eliminar el escenario "${nombre}"? Esta acción no se puede deshacer.`)) {
            return;
        }

        try {
            await apiService.delete(`/presupuesto/escenarios/${id}`);
            toast.success("Escenario eliminado");
            fetchEscenarios();
        } catch (error) {
            console.error(error);
            toast.error("Error eliminando escenario");
        }
    };

    const handleBack = () => {
        setSelectedEscenario(null);
        setSelectedReporte(null);
        fetchEscenarios();
    };

    if (loading) return <div>Cargando escenarios...</div>;

    // View Switching
    if (selectedEscenario) {
        return <PresupuestoGrid escenario={selectedEscenario} onBack={handleBack} />;
    }

    if (selectedReporte) {
        return <ReporteEjecucion escenario={selectedReporte} onBack={handleBack} />;
    }

    return (
        <div className="bg-white p-4 rounded shadow mb-6">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold">Escenarios de Presupuesto</h2>
                <button
                    onClick={() => setShowModal(true)}
                    className="bg-blue-600 text-white px-4 py-2 rounded flex items-center gap-2 hover:bg-blue-700"
                >
                    <FaPlus /> Nuevo Escenario
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {escenarios.map(esc => (
                    <div key={esc.id} className="border p-4 rounded hover:shadow-lg transition">
                        <div className="flex justify-between items-start">
                            <div className="cursor-pointer" onClick={() => setSelectedEscenario(esc)}>
                                <h3 className="font-bold text-lg">{esc.nombre}</h3>
                                <span className={`text-xs px-2 py-1 rounded ${esc.estado === 'BORRADOR' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'}`}>
                                    {esc.estado}
                                </span>
                                <span className="ml-2 text-xs text-gray-500">{esc.tipo_sector} - {esc.anio}</span>
                            </div>
                            <button className="text-red-500 hover:text-red-700" onClick={(e) => {
                                e.stopPropagation();
                                handleDelete(esc.id, esc.nombre);
                            }}>
                                <FaTrash />
                            </button>
                        </div>
                        <div className="mt-4 pt-4 border-t flex justify-between items-center text-sm text-gray-600">
                            <span>Creado: {new Date(esc.created_at).toLocaleDateString()}</span>
                            <div className="flex gap-2">
                                <button
                                    className="text-purple-600 font-semibold flex items-center gap-1 hover:bg-purple-50 px-2 py-1 rounded"
                                    onClick={() => setSelectedReporte(esc)}
                                >
                                    <FaChartLine /> Reporte
                                </button>
                                <button
                                    className="text-blue-600 font-semibold flex items-center gap-1 hover:bg-blue-50 px-2 py-1 rounded"
                                    onClick={() => setSelectedEscenario(esc)}
                                >
                                    <FaEdit /> Editar
                                </button>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Modal Simple */}
            {showModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white p-6 rounded shadow-lg max-w-md w-full">
                        <h3 className="text-lg font-bold mb-4">Crear Nuevo Escenario</h3>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium">Nombre</label>
                                <input
                                    className="w-full border p-2 rounded"
                                    value={newItem.nombre}
                                    onChange={e => setNewItem({ ...newItem, nombre: e.target.value })}
                                    placeholder="Ej: Presupuesto Base 2026"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium">Año Fiscal</label>
                                <input
                                    type="number"
                                    className="w-full border p-2 rounded"
                                    value={newItem.anio}
                                    onChange={e => setNewItem({ ...newItem, anio: parseInt(e.target.value) })}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium">Sector</label>
                                <select
                                    className="w-full border p-2 rounded"
                                    value={newItem.tipo_sector}
                                    onChange={e => setNewItem({ ...newItem, tipo_sector: e.target.value })}
                                >
                                    <option value="PRIVADO">Privado (Gestión)</option>
                                    <option value="PUBLICO">Público (Normativo)</option>
                                </select>
                            </div>
                            <div className="flex justify-end gap-2 mt-6">
                                <button className="px-4 py-2 text-gray-600" onClick={() => setShowModal(false)}>Cancelar</button>
                                <button className="px-4 py-2 bg-blue-600 text-white rounded" onClick={handleCreate}>Crear</button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
