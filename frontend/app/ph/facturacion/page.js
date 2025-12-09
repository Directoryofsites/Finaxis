'use client';

import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import BotonRegresar from '../../components/BotonRegresar';
import { phService } from '../../../lib/phService';
import { FaFileInvoiceDollar, FaPlay, FaCheckCircle, FaExclamationTriangle, FaList } from 'react-icons/fa';

export default function FacturacionPHPage() {
    const { user, loading: authLoading } = useAuth();

    const [fecha, setFecha] = useState(new Date().toISOString().slice(0, 7)); // YYYY-MM
    const [loading, setLoading] = useState(false);
    const [resultado, setResultado] = useState(null);
    const [error, setError] = useState(null);

    // Concept Selection State
    const [conceptos, setConceptos] = useState([]);
    const [selectedConceptos, setSelectedConceptos] = useState([]); // IDs

    React.useEffect(() => {
        if (!authLoading && user?.empresaId) {
            loadConceptos();
        }
    }, [authLoading, user]);

    const loadConceptos = async () => {
        try {
            const data = await phService.getConceptos();
            const activos = data.filter(c => c.activo);
            setConceptos(activos);
            setSelectedConceptos(activos.map(c => c.id)); // Default select all
        } catch (err) {
            console.error("Error loading concepts", err);
        }
    };

    const handleGenerar = async () => {
        if (selectedConceptos.length === 0) {
            alert("Debe seleccionar al menos un concepto para facturar.");
            return;
        }

        if (!confirm(`¿Estás seguro de generar la facturación masiva para ${fecha}? Esto creará documentos contables reales.`)) return;

        setLoading(true);
        setError(null);
        setResultado(null);

        try {
            // Añadir día 01 para ser compatible con backend date
            const fechaCompleta = `${fecha}-01`;
            const data = await phService.generarFacturacionMasiva(fechaCompleta, selectedConceptos);
            setResultado(data);
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al generar facturación.');
        } finally {
            setLoading(false);
        }
    };

    if (authLoading) return <p className="p-8 text-center">Cargando...</p>;

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
            <div className="max-w-4xl mx-auto">
                <div className="mb-8">
                    <BotonRegresar />
                    <div className="flex items-center gap-3 mt-3">
                        <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                            <FaFileInvoiceDollar className="text-2xl" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold text-gray-800">Facturación Masiva PH</h1>
                            <p className="text-gray-500 text-sm">Generación automática de cuentas de cobro para todas las unidades.</p>
                        </div>
                    </div>
                </div>

                <div className="bg-white p-8 rounded-xl shadow-lg border border-gray-100 text-center">

                    <div className="max-w-md mx-auto space-y-6">
                        <div>
                            <label className="block text-sm font-bold text-gray-700 mb-2">Seleccione Periodo a Facturar</label>
                            <input
                                type="month"
                                value={fecha}
                                onChange={(e) => setFecha(e.target.value)}
                                className="w-full px-4 py-3 border border-gray-300 rounded-lg text-lg text-center font-mono shadow-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                            />
                        </div>

                        <button
                            onClick={handleGenerar}
                            disabled={loading}
                            className={`w-full py-4 rounded-xl text-white font-bold text-lg shadow-md flex justify-center items-center gap-2 transition-all transform hover:scale-105 ${loading ? 'bg-gray-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'}`}
                        >
                            {loading ? (
                                <span className="loading loading-spinner text-white"></span>
                            ) : (
                                <>
                                    <FaPlay /> GENERAR FACTURACIÓN
                                </>
                            )}
                        </button>
                    </div>

                    {error && (
                        <div className="mt-8 p-4 bg-red-50 text-red-700 rounded-lg border border-red-200 flex items-center gap-2 justify-center animate-fadeIn">
                            <FaExclamationTriangle />
                            <span>{error}</span>
                        </div>
                    )}

                    {resultado && (
                        <div className="mt-8 text-left animate-slideUp">
                            <div className="grid grid-cols-2 gap-4 mb-6">
                                <div className="p-4 bg-green-50 rounded-lg border border-green-100 text-center">
                                    <p className="text-green-800 font-bold text-3xl">{resultado.generadas}</p>
                                    <p className="text-green-600 text-sm uppercase tracking-wide font-bold">Facturas Generadas</p>
                                </div>
                                <div className="p-4 bg-red-50 rounded-lg border border-red-100 text-center">
                                    <p className="text-red-800 font-bold text-3xl">{resultado.errores}</p>
                                    <p className="text-red-600 text-sm uppercase tracking-wide font-bold">Errores</p>
                                </div>
                            </div>

                            <div className="bg-slate-50 p-4 rounded-lg border border-gray-200 max-h-60 overflow-y-auto font-mono text-xs">
                                <h3 className="font-bold text-gray-500 mb-2 sticky top-0 bg-slate-50 pb-2 border-b flex items-center gap-2">
                                    <FaList /> LOG DE EJECUCIÓN
                                </h3>
                                <ul className="space-y-1">
                                    {resultado.detalles.map((line, idx) => (
                                        <li key={idx} className={line.includes('Error') ? 'text-red-600 font-bold' : 'text-gray-600'}>
                                            {line}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    )}

                </div>
            </div>
        </div>
    );
}
