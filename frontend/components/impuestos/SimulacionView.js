"use client";
import React, { useState, useEffect } from 'react';
import { FaPlus, FaPlay, FaTrash, FaSave } from 'react-icons/fa';
import { toast } from 'react-toastify';

export default function SimulacionView({ impuesto }) {
    // State for scenarios list
    const [escenarios, setEscenarios] = useState([]);

    // State for current simulation form
    const [form, setForm] = useState({
        id: null,
        nombre: '',
        ingresos: 0,
        gastos: 0,
        resultado: 0
    });

    // Load from localStorage
    useEffect(() => {
        if (typeof window !== 'undefined' && impuesto) {
            const saved = localStorage.getItem(`impuestos_simulacion_${impuesto}`);
            if (saved) {
                setEscenarios(JSON.parse(saved));
            }
        }
    }, [impuesto]);

    // Save to localStorage whenever scenarios change
    useEffect(() => {
        if (typeof window !== 'undefined' && impuesto && escenarios.length > 0) {
            localStorage.setItem(`impuestos_simulacion_${impuesto}`, JSON.stringify(escenarios));
        }
    }, [escenarios, impuesto]);

    const handleNew = () => {
        setForm({ id: null, nombre: '', ingresos: 0, gastos: 0, resultado: 0 });
        toast.info("Nuevo escenario listo para configurar.");
    };

    const handleRun = () => {
        if (!form.nombre) {
            toast.warning("Asigne un nombre al escenario.");
            return;
        }

        // Simple mock calculation logic
        const base = parseFloat(form.ingresos) - parseFloat(form.gastos);
        const tarifa = 0.19; // Mock 19%
        const impuestoEstimado = base > 0 ? base * tarifa : 0;

        const newScenario = {
            ...form,
            id: form.id || Date.now(),
            resultado: impuestoEstimado
        };

        setForm(newScenario);

        // Update list
        setEscenarios(prev => {
            const exists = prev.find(e => e.id === newScenario.id);
            if (exists) {
                return prev.map(e => e.id === newScenario.id ? newScenario : e);
            } else {
                return [...prev, newScenario];
            }
        });

        toast.success(`Simulación ejecutada. Impuesto estimado: $${impuestoEstimado.toLocaleString()}`);
    };

    const loadScenario = (esc) => {
        setForm(esc);
        toast.info(`Escenario "${esc.nombre}" cargado.`);
    };

    const handleDelete = (id, e) => {
        e.stopPropagation();
        if (window.confirm("¿Eliminar este escenario?")) {
            setEscenarios(prev => prev.filter(s => s.id !== id));
            if (form.id === id) handleNew();
            toast.success("Escenario eliminado.");
        }
    };

    return (
        <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow-md">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-xl font-semibold text-gray-800">Simulador de Escenarios - {impuesto}</h2>
                    <button
                        onClick={handleNew}
                        className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 flex items-center"
                    >
                        <FaPlus className="mr-2" /> Nuevo Escenario
                    </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Lista de Escenarios */}
                    <div className="space-y-4">
                        <h3 className="font-semibold text-gray-700">Historial de Simulaciones</h3>
                        {escenarios.length === 0 && <p className="text-gray-500 text-sm">No hay escenarios guardados.</p>}
                        {escenarios.map((esc) => (
                            <div
                                key={esc.id}
                                onClick={() => loadScenario(esc)}
                                className={`border rounded-lg p-4 cursor-pointer transition-colors relative group ${form.id === esc.id ? 'border-blue-500 bg-blue-50' : 'hover:bg-gray-50'}`}
                            >
                                <div className="flex justify-between items-center">
                                    <h3 className="font-bold text-gray-700">{esc.nombre}</h3>
                                    <button
                                        onClick={(e) => handleDelete(esc.id, e)}
                                        className="text-red-400 hover:text-red-600 opacity-0 group-hover:opacity-100 transition-opacity"
                                    >
                                        <FaTrash />
                                    </button>
                                </div>
                                <p className="text-sm text-gray-500 mt-2">
                                    Impuesto estimado: <span className="font-semibold text-gray-900">${esc.resultado.toLocaleString()}</span>
                                </p>
                            </div>
                        ))}
                    </div>

                    {/* Panel de Control de Simulación */}
                    <div className="bg-gray-50 p-4 rounded-lg border h-fit">
                        <h3 className="font-semibold text-gray-700 mb-4">Parámetros de Simulación</h3>
                        <div className="space-y-3">
                            <div>
                                <label className="block text-sm font-medium text-gray-600">Nombre del Escenario</label>
                                <input
                                    type="text"
                                    className="w-full border rounded p-2 focus:ring-blue-500 focus:border-blue-500"
                                    placeholder="Ej: Ventas proyectadas Diciembre"
                                    value={form.nombre}
                                    onChange={(e) => setForm({ ...form, nombre: e.target.value })}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-600">Proyección de Ingresos</label>
                                <input
                                    type="number"
                                    className="w-full border rounded p-2 focus:ring-blue-500 focus:border-blue-500"
                                    value={form.ingresos}
                                    onChange={(e) => setForm({ ...form, ingresos: e.target.value })}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-600">Gastos Deducibles</label>
                                <input
                                    type="number"
                                    className="w-full border rounded p-2 focus:ring-blue-500 focus:border-blue-500"
                                    value={form.gastos}
                                    onChange={(e) => setForm({ ...form, gastos: e.target.value })}
                                />
                            </div>

                            <div className="pt-4 border-t mt-4">
                                <div className="flex justify-between items-center mb-4">
                                    <span className="font-semibold text-gray-700">Resultado Estimado:</span>
                                    <span className="text-xl font-bold text-blue-600">${form.resultado.toLocaleString()}</span>
                                </div>
                                <button
                                    onClick={handleRun}
                                    className="w-full bg-blue-600 text-white py-2 rounded flex justify-center items-center hover:bg-blue-700 font-semibold"
                                >
                                    <FaPlay className="mr-2" /> Ejecutar y Guardar
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
