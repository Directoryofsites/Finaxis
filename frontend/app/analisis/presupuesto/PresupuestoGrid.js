"use client";
import React, { useState, useEffect } from 'react';
import { apiService } from '../../../lib/apiService';
import { toast } from 'react-hot-toast';
import { FaCalculator, FaSave, FaArrowLeft, FaMagic, FaFilePdf } from 'react-icons/fa';

/**
 * Componente principal de Edición de Presupuesto (Grid)
 */
export default function PresupuestoGrid({ escenario, onBack }) {
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showProjectionModal, setShowProjectionModal] = useState(false);

    // Proyeccion Params
    const [projParams, setProjParams] = useState({
        base_year: escenario.anio - 1,
        metodo: 'PROMEDIO_HISTORICO',
        factor: 5.0
    });

    const fetchItems = async () => {
        setLoading(true);
        try {
            const res = await apiService.get(`/presupuesto/escenarios/${escenario.id}/items`);
            setItems(res.data);
        } catch (error) {
            console.error(error);
            toast.error("Error al cargar items");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchItems();
    }, [escenario.id]);

    const handleProyectar = async () => {
        const toastId = toast.loading("Calculando proyección...");
        try {
            await apiService.post(`/presupuesto/escenarios/${escenario.id}/proyectar`, null, {
                params: {
                    base_year: projParams.base_year,
                    metodo: projParams.metodo,
                    factor: projParams.factor
                }
            });
            toast.success("Proyeccion completada", { id: toastId });
            setShowProjectionModal(false);
            fetchItems(); // Recargar grid
        } catch (error) {
            console.error(error);
            toast.error("Error en proyección", { id: toastId });
        }
    };

    const handleDownloadPDF = async () => {
        const toastId = toast.loading("Generando PDF...");
        try {
            // 1. Obtener Token Seguro
            const res = await apiService.get(`/presupuesto/escenarios/${escenario.id}/pdf-token`);
            const token = res.data.token;

            // 2. Construir URL
            const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8002';
            const url = `${API_BASE}/api/presupuesto/escenarios/${escenario.id}/pdf?token=${token}`;

            // 3. Abrir
            window.open(url, '_blank');
            toast.dismiss(toastId);
        } catch (error) {
            console.error(error);
            toast.error("Error generando enlace de descarga", { id: toastId });
        }
    };

    if (loading) return <div className="p-8 text-center">Cargando datos contables...</div>;

    return (
        <div className="bg-white p-4 rounded shadow h-full flex flex-col">
            {/* Header Toolbar */}
            <div className="flex justify-between items-center mb-4 border-b pb-4">
                <div className="flex items-center gap-4">
                    <button onClick={onBack} className="text-gray-500 hover:text-gray-800">
                        <FaArrowLeft /> Atrás
                    </button>
                    <div>
                        <h2 className="text-xl font-bold">{escenario.nombre}</h2>
                        <span className="text-sm text-gray-500">Editando Año: {escenario.anio} | Base: {projParams.base_year}</span>
                    </div>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={handleDownloadPDF}
                        className="bg-gray-600 text-white px-4 py-2 rounded flex items-center gap-2 hover:bg-gray-700 shadow-sm"
                        title="Exportar Presupuesto a PDF"
                    >
                        <FaFilePdf /> PDF
                    </button>
                    <button
                        onClick={() => setShowProjectionModal(true)}
                        className="bg-purple-600 text-white px-4 py-2 rounded flex items-center gap-2 hover:bg-purple-700"
                    >
                        <FaMagic /> Proyección Inteligente
                    </button>
                </div>
            </div>

            {/* Grid Content */}
            <div className="flex-1 overflow-auto">
                <table className="min-w-full text-sm border-collapse">
                    <thead className="bg-gray-100 sticky top-0">
                        <tr>
                            <th className="p-2 border text-left">Cuenta</th>
                            <th className="p-2 border text-right">Ene</th>
                            <th className="p-2 border text-right">Feb</th>
                            <th className="p-2 border text-right">Mar</th>
                            <th className="p-2 border text-right">Abr</th>
                            <th className="p-2 border text-right">May</th>
                            <th className="p-2 border text-right">Jun</th>
                            <th className="p-2 border text-right">Jul</th>
                            <th className="p-2 border text-right">Ago</th>
                            <th className="p-2 border text-right">Sep</th>
                            <th className="p-2 border text-right">Oct</th>
                            <th className="p-2 border text-right">Nov</th>
                            <th className="p-2 border text-right">Dic</th>
                            <th className="p-2 border text-right font-bold">TOTAL ANUAL</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items.length === 0 && (
                            <tr>
                                <td colSpan={15} className="p-8 text-center text-gray-500">
                                    No hay items en este presupuesto. Usa el botón "Proyección Inteligente" para generar una base desde tu contabilidad.
                                </td>
                            </tr>
                        )}
                        {items.map(item => (
                            <tr key={item.id} className="hover:bg-gray-50">
                                <td className="p-2 border">
                                    <span className="font-mono font-bold mr-2">{item.cuenta?.codigo}</span>
                                    {item.cuenta?.nombre || `(ID: ${item.cuenta_id})`}
                                </td>
                                <td className="p-2 border text-right">{item.mes_01?.toLocaleString()}</td>
                                <td className="p-2 border text-right">{item.mes_02?.toLocaleString()}</td>
                                <td className="p-2 border text-right">{item.mes_03?.toLocaleString()}</td>
                                <td className="p-2 border text-right">{item.mes_04?.toLocaleString()}</td>
                                <td className="p-2 border text-right">{item.mes_05?.toLocaleString()}</td>
                                <td className="p-2 border text-right">{item.mes_06?.toLocaleString()}</td>
                                <td className="p-2 border text-right">{item.mes_07?.toLocaleString()}</td>
                                <td className="p-2 border text-right">{item.mes_08?.toLocaleString()}</td>
                                <td className="p-2 border text-right">{item.mes_09?.toLocaleString()}</td>
                                <td className="p-2 border text-right">{item.mes_10?.toLocaleString()}</td>
                                <td className="p-2 border text-right">{item.mes_11?.toLocaleString()}</td>
                                <td className="p-2 border text-right">{item.mes_12?.toLocaleString()}</td>
                                <td className="p-2 border text-right font-bold">{item.valor_total?.toLocaleString()}</td>
                                <td className="p-2 border text-xs">{item.metodo_proyeccion}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Modal Proyección */}
            {showProjectionModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white p-6 rounded shadow-lg max-w-lg w-full">
                        <div className="flex items-center gap-2 mb-4 text-purple-700">
                            <FaMagic className="text-xl" />
                            <h3 className="text-lg font-bold">Motor de Proyección Inteligente</h3>
                        </div>
                        <p className="text-sm text-gray-600 mb-6">
                            El sistema analizará los movimientos contables del año base seleccionado y calculará una proyección propuesta para el año {escenario.anio}.
                            <br /><br />
                            <strong>Advertencia:</strong> Esto sobreescribirá los valores actuales si ya existen.
                        </p>

                        <div className="space-y-4 bg-gray-50 p-4 rounded border">
                            <div>
                                <label className="block text-sm font-medium">Año Base (Fuente de Datos)</label>
                                <select
                                    className="w-full border p-2 rounded"
                                    value={projParams.base_year}
                                    onChange={e => setProjParams({ ...projParams, base_year: parseInt(e.target.value) })}
                                >
                                    {Array.from({ length: 41 }, (_, i) => 2010 + i).map(year => (
                                        <option key={year} value={year}>{year}</option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium">Método de Cálculo</label>
                                <select
                                    className="w-full border p-2 rounded"
                                    value={projParams.metodo}
                                    onChange={e => setProjParams({ ...projParams, metodo: e.target.value })}
                                >
                                    <option value="PROMEDIO_HISTORICO">Promedio Histórico (Suavizado)</option>
                                    <option value="EJECUCION_ANTERIOR">Copia Exacta Ejecución (Estacional)</option>
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium">Factor de Incremento (%)</label>
                                <div className="flex gap-2 items-center">
                                    <input
                                        type="number"
                                        className="w-24 border p-2 rounded"
                                        value={projParams.factor}
                                        onChange={e => setProjParams({ ...projParams, factor: parseFloat(e.target.value) })}
                                    />
                                    <span className="text-sm text-gray-500">Ej: 5.0 para aumento del 5% (IPC)</span>
                                </div>
                            </div>
                        </div>

                        <div className="flex justify-end gap-2 mt-6">
                            <button className="px-4 py-2 text-gray-600" onClick={() => setShowProjectionModal(false)}>Cancelar</button>
                            <button className="px-4 py-2 bg-purple-600 text-white rounded font-bold shadow hover:bg-purple-700" onClick={handleProyectar}>
                                Ejecutar Proyección
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
