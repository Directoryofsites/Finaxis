'use client';
import React, { useState } from 'react';
import { resetConsumoFactory, soporteApiService } from '@/lib/soporteApiService';
import { FaTrash, FaExclamationTriangle, FaTools, FaEye } from 'react-icons/fa';
import DashboardConsumoView from '@/components/consumo/DashboardConsumoView';

export default function ResetConsumoPanel({ todasLasEmpresas = [] }) {
    const [selectedEmpresaId, setSelectedEmpresaId] = useState('');
    const [mensaje, setMensaje] = useState({ texto: '', tipo: '' });
    const [isProcessing, setIsProcessing] = useState(false);
    const [confirmacion, setConfirmacion] = useState('');

    // Checkboxes State
    const [borrarHistorial, setBorrarHistorial] = useState(false); // Default OFF safe
    const [borrarRecargas, setBorrarRecargas] = useState(true);
    const [borrarBolsas, setBorrarBolsas] = useState(true);
    const [resetPlan, setResetPlan] = useState(true);

    const [activeTab, setActiveTab] = useState('technician'); // 'technician' | 'mirror'

    const handleReset = async () => {
        if (!selectedEmpresaId) {
            setMensaje({ texto: 'Seleccione una empresa.', tipo: 'error' });
            return;
        }

        const empresa = todasLasEmpresas.find(e => e.id === parseInt(selectedEmpresaId));
        const nombreEmpresa = empresa ? empresa.razon_social : 'la empresa seleccionada';

        if (confirmacion !== 'BORRAR TODO') {
            setMensaje({ texto: 'Debe escribir "BORRAR TODO" en el campo de confirmación.', tipo: 'error' });
            return;
        }

        if (!window.confirm(`⚠️ PELIGRO EXTREMO ⚠️\n\n¿Está 100% seguro de que desea reiniciar la fábrica de consumo para:\n\n${nombreEmpresa}?\n\nEsta acción eliminará TODO el historial de consumo, bolsas y recargas. ES IRREVERSIBLE.`)) {
            return;
        }

        setIsProcessing(true);
        setMensaje({ texto: '', tipo: '' });

        try {
            const params = {
                borrar_historial: borrarHistorial,
                borrar_recargas: borrarRecargas,
                borrar_bolsas: borrarBolsas,
                reset_plan: resetPlan
            };
            const response = await resetConsumoFactory(selectedEmpresaId, params);
            setMensaje({ texto: response.data.message || 'Reinicio de fábrica completado.', tipo: 'success' });
            setConfirmacion('');
        } catch (error) {
            const errorMsg = error.response?.data?.detail || 'Error al ejecutar el reinicio.';
            setMensaje({ texto: 'Error: ' + errorMsg, tipo: 'error' });
        } finally {
            setIsProcessing(false);
        }
    };

    return (
        <div className="bg-white p-6 rounded-lg shadow-md border border-slate-200">
            {/* SELECTOR DE EMPRESA GLOBAL (COMÚN A AMBAS PESTAÑAS) */}
            <div className="mb-6">
                <label className="block text-gray-700 text-sm font-bold mb-2">Empresa Objetivo</label>
                <select
                    value={selectedEmpresaId}
                    onChange={(e) => setSelectedEmpresaId(e.target.value)}
                    className="shadow border rounded w-full py-2 px-3 text-gray-700 focus:ring-2 focus:ring-indigo-500"
                >
                    <option value="">-- Seleccione Empresa --</option>
                    {todasLasEmpresas.map(emp => (
                        <option key={emp.id} value={emp.id}>
                            {emp.razon_social} (NIT: {emp.nit})
                        </option>
                    ))}
                </select>
            </div>

            {/* PESTAÑAS DE NAVEGACIÓN */}
            <div className="flex border-b border-gray-200 mb-6">
                <button
                    onClick={() => setActiveTab('technician')}
                    className={`flex items-center gap-2 py-2 px-4 border-b-2 font-medium text-sm transition-colors ${activeTab === 'technician'
                        ? 'border-indigo-500 text-indigo-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                >
                    <FaTools /> Gestión Técnica (Reset)
                </button>
                <button
                    onClick={() => setActiveTab('mirror')}
                    className={`flex items-center gap-2 py-2 px-4 border-b-2 font-medium text-sm transition-colors ${activeTab === 'mirror'
                        ? 'border-indigo-500 text-indigo-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                >
                    <FaEye /> Vista Cliente (Espejo)
                </button>
            </div>

            {/* CONTENIDO PESTAÑA TÉCNICA */}
            {activeTab === 'technician' && (
                <div className="animate-fadeIn">
                    <h2 className="text-xl font-bold text-red-700 flex items-center gap-2 mb-4">
                        <FaExclamationTriangle /> Reinicio de Fábrica - Consumo
                    </h2>

                    <div className="bg-red-50 p-4 rounded-md border border-red-100 mb-6 text-sm text-red-800">
                        <p className="font-bold">⚠️ ZONA DE PELIGRO</p>
                        <p>Esta herramienta está diseñada para entornos de PRUEBAS. Ejecutarla eliminará:</p>
                        <ul className="list-disc ml-5 mt-2 space-y-1">
                            <li>Todo el historial de consumos y reversiones.</li>
                            <li>Todas las bolsas de excedentes acumuladas.</li>
                            <li>Todas las recargas adicionales compradas.</li>
                            <li>Reiniciará el Plan Mensual actual a su estado original.</li>
                        </ul>
                    </div>

                    {mensaje.texto && (
                        <div className={`p-4 mb-4 rounded-md font-bold ${mensaje.tipo === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                            {mensaje.texto}
                        </div>
                    )}

                    <div className="space-y-4 max-w-lg">
                        <div>
                            <label className="block text-red-700 text-sm font-bold mb-2">Confirmación de Seguridad</label>
                            <input
                                type="text"
                                value={confirmacion}
                                onChange={(e) => setConfirmacion(e.target.value)}
                                placeholder='Escriba "BORRAR TODO" para confirmar'
                                className="shadow border border-red-300 rounded w-full py-2 px-3 text-red-900 placeholder-red-200 focus:outline-none focus:ring-2 focus:ring-red-500"
                            />
                        </div>

                        {/* CHECKBOXES DE SELECCIÓN */}
                        <div className="bg-slate-50 p-4 rounded border border-slate-200 space-y-3">
                            <p className="font-bold text-slate-700 text-xs uppercase tracking-wider mb-2">Seleccione qué eliminar:</p>

                            <label className="flex items-center space-x-2 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={borrarHistorial}
                                    onChange={(e) => setBorrarHistorial(e.target.checked)}
                                    className="form-checkbox h-4 w-4 text-red-600 rounded focus:ring-red-500"
                                />
                                <span className="text-sm text-slate-700">Borrar Historial de Consumo (Reversiones incluidas)</span>
                            </label>

                            <label className="flex items-center space-x-2 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={borrarRecargas}
                                    onChange={(e) => setBorrarRecargas(e.target.checked)}
                                    className="form-checkbox h-4 w-4 text-red-600 rounded focus:ring-red-500"
                                />
                                <span className="text-sm text-slate-700">Borrar Recargas Adicionales</span>
                            </label>

                            <label className="flex items-center space-x-2 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={borrarBolsas}
                                    onChange={(e) => setBorrarBolsas(e.target.checked)}
                                    className="form-checkbox h-4 w-4 text-red-600 rounded focus:ring-red-500"
                                />
                                <span className="text-sm text-slate-700">Borrar Bolsas de Excedentes</span>
                            </label>

                            <label className="flex items-center space-x-2 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={resetPlan}
                                    onChange={(e) => setResetPlan(e.target.checked)}
                                    className="form-checkbox h-4 w-4 text-red-600 rounded focus:ring-red-500"
                                />
                                <span className="text-sm text-slate-700">Reiniciar Plan Mensual</span>
                            </label>
                        </div>

                        <div className="pt-4">
                            <button
                                onClick={handleReset}
                                disabled={isProcessing || !selectedEmpresaId || confirmacion !== 'BORRAR TODO'}
                                className="w-full bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white font-bold py-3 px-4 rounded flex items-center justify-center gap-2 transition-colors"
                            >
                                {isProcessing ? 'Purgando sistema...' : <><FaTrash /> EJECUTAR REINICIO DE FÁBRICA</>}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* CONTENIDO PESTAÑA ESPEJO */}
            {activeTab === 'mirror' && (
                <div className="animate-fadeIn">
                    {!selectedEmpresaId ? (
                        <div className="text-center py-10 bg-slate-50 rounded border border-slate-200 text-slate-500">
                            <FaExclamationTriangle className="mx-auto text-2xl mb-2 text-yellow-400" />
                            Por favor seleccione una empresa arriba para cargar su vista espejo.
                        </div>
                    ) : (
                        <div className="bg-slate-100 p-4 rounded border border-slate-200">
                            <DashboardConsumoView empresaIdOverride={parseInt(selectedEmpresaId)} />
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
