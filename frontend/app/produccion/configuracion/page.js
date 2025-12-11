"use client";
import React, { useState, useEffect } from 'react';
import { toast, ToastContainer } from 'react-toastify';
import { FaSave, FaCogs, FaArrowLeft } from 'react-icons/fa';
import Link from 'next/link';
import { getConfigProduccion, saveConfigProduccion } from '../../../lib/produccionService';
import { getTiposDocumento } from '../../../lib/tiposDocumentoService';

export default function ProduccionConfigPage() {
    const [config, setConfig] = useState({
        tipo_documento_orden_id: '',
        tipo_documento_anulacion_id: '',
        tipo_documento_consumo_id: '',
        tipo_documento_entrada_pt_id: ''
    });
    const [tiposDocumento, setTiposDocumento] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        setLoading(true);
        try {
            const [cfg, tips] = await Promise.all([
                getConfigProduccion(),
                getTiposDocumento()
            ]);
            if (cfg) {
                setConfig({
                    tipo_documento_orden_id: cfg.tipo_documento_orden_id || '',
                    tipo_documento_anulacion_id: cfg.tipo_documento_anulacion_id || '',
                    tipo_documento_consumo_id: cfg.tipo_documento_consumo_id || '',
                    tipo_documento_entrada_pt_id: cfg.tipo_documento_entrada_pt_id || ''
                });
            }
            setTiposDocumento(tips);
        } catch (error) {
            console.error(error);
            toast.error("Error cargando configuración.");
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            await saveConfigProduccion(config);
            toast.success("Configuración guardada.");
        } catch (error) {
            console.error(error);
            toast.error("Error guardando cambios.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-6 bg-gray-50 min-h-screen font-sans">
            <ToastContainer />
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <Link href="/produccion/ordenes" className="text-gray-500 hover:text-gray-700">
                        <FaArrowLeft size={20} />
                    </Link>
                    <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                        <FaCogs className="text-gray-600" /> Configuración de Producción
                    </h1>
                </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 max-w-2xl">
                <form onSubmit={handleSave} className="space-y-6">

                    {/* Sección Documentos Contables */}
                    <div>
                        <h3 className="text-lg font-semibold text-gray-700 mb-4 border-b pb-2">Documentos Contables</h3>
                        <p className="text-sm text-gray-500 mb-4">
                            Seleccione los tipos de documento que se usarán para generar la contabilidad automática.
                        </p>

                        <div className="grid grid-cols-1 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Tipo de Documento para Órdenes (Producción/Cierre)
                                </label>
                                <select
                                    value={config.tipo_documento_orden_id}
                                    onChange={(e) => setConfig({ ...config, tipo_documento_orden_id: e.target.value })}
                                    className="w-full border-gray-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500 p-2 border"
                                >
                                    <option value="">-- Seleccionar --</option>
                                    {tiposDocumento.map(t => (
                                        <option key={t.id} value={t.id}>{t.nombre} ({t.codigo})</option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Tipo de Documento para Anulaciones (Reversión)
                                </label>
                                <select
                                    value={config.tipo_documento_anulacion_id}
                                    onChange={(e) => setConfig({ ...config, tipo_documento_anulacion_id: e.target.value })}
                                    className="w-full border-gray-300 rounded-md shadow-sm focus:ring-red-500 focus:border-red-500 p-2 border"
                                >
                                    <option value="">-- Seleccionar --</option>
                                    {tiposDocumento.map(t => (
                                        <option key={t.id} value={t.id}>{t.nombre} ({t.codigo})</option>
                                    ))}
                                </select>
                                <p className="text-xs text-gray-400 mt-1">Usado para reversar movimientos de inventario y costo.</p>
                            </div>

                            <div className="border-t pt-4 mt-2">
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Tipo de Documento para Consumo de Materia Prima
                                </label>
                                <select
                                    value={config.tipo_documento_consumo_id}
                                    onChange={(e) => setConfig({ ...config, tipo_documento_consumo_id: e.target.value })}
                                    className="w-full border-gray-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500 p-2 border"
                                >
                                    <option value="">-- Seleccionar --</option>
                                    {tiposDocumento.map(t => (
                                        <option key={t.id} value={t.id}>{t.nombre} ({t.codigo})</option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Tipo de Documento para Entrada de Producto Terminado
                                </label>
                                <select
                                    value={config.tipo_documento_entrada_pt_id}
                                    onChange={(e) => setConfig({ ...config, tipo_documento_entrada_pt_id: e.target.value })}
                                    className="w-full border-gray-300 rounded-md shadow-sm focus:ring-emerald-500 focus:border-emerald-500 p-2 border"
                                >
                                    <option value="">-- Seleccionar --</option>
                                    {tiposDocumento.map(t => (
                                        <option key={t.id} value={t.id}>{t.nombre} ({t.codigo})</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    </div>

                    <div className="flex justify-end pt-4">
                        <button
                            type="submit"
                            disabled={loading}
                            className="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-2 rounded-lg font-medium shadow-sm transition-colors flex items-center gap-2"
                        >
                            <FaSave />
                            {loading ? 'Guardando...' : 'Guardar Configuración'}
                        </button>
                    </div>

                </form>
            </div>
        </div>
    );
}
