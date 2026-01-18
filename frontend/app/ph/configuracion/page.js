'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '../../context/AuthContext';

import { phService } from '../../../lib/phService';
import BuscadorCuentas from '../../../components/BuscadorCuentas';
import { FaCogs, FaSave, FaPlus, FaTrash, FaEdit, FaExclamationTriangle, FaListUl, FaMoneyBillWave, FaLayerGroup } from 'react-icons/fa';

// Estilos
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none";
const sectionTitleClass = "text-lg font-bold text-gray-700 flex items-center gap-2 border-b pb-2 mb-4";

export default function ConfiguracionPHPage() {
    const { user, loading: authLoading } = useAuth();

    // Estados Globales
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [saving, setSaving] = useState(false);

    // Estados Configuración
    const [config, setConfig] = useState({
        interes_mora_mensual: 1.5,
        interes_mora_habilitado: true,
        dia_corte: 1,
        dia_limite_pago: 10,
        dia_limite_pronto_pago: 5,
        descuento_pronto_pago: 0,
        mensaje_factura: '',
        tipo_documento_factura_id: '',
        tipo_documento_recibo_id: '',
        cuenta_ingreso_intereses_id: '',
        cuenta_ingreso_intereses_codigo: '',
        cuenta_ingreso_intereses_nombre: ''
    });

    const [tiposDoc, setTiposDoc] = useState([]);

    useEffect(() => {
        if (!authLoading && user?.empresaId) {
            fetchData();
        }
    }, [authLoading, user]);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [configData, tiposData] = await Promise.all([
                phService.getConfiguracion(),
                phService.getTiposDocumento()
            ]);
            setConfig({
                ...configData,
                interes_mora_habilitado: configData.interes_mora_habilitado ?? true,
                cuenta_ingreso_intereses_codigo: configData.cuenta_ingreso_intereses ? configData.cuenta_ingreso_intereses.codigo : '',
                cuenta_ingreso_intereses_nombre: configData.cuenta_ingreso_intereses ? configData.cuenta_ingreso_intereses.nombre : '',
                tipo_negocio: configData.tipo_negocio || 'PH_RESIDENCIAL'
            });
            setTiposDoc(tiposData);
        } catch (err) {
            setError('Error cargando configuración.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    // --- MANEJO DE CONFIGURACIÓN ---
    const handleSaveConfig = async (e) => {
        e.preventDefault();
        try {
            setSaving(true);
            await phService.updateConfiguracion(config);
            alert('Configuración guardada correctamente.');
        } catch (err) {
            alert('Error guardando configuración.');
        } finally {
            setSaving(false);
        }
    };

    const handleConfigChange = (e) => {
        const { name, value } = e.target;
        setConfig(prev => ({ ...prev, [name]: value }));
    };



    if (authLoading || loading) return <p className="p-8 text-center text-gray-500">Cargando...</p>;

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
            <div className="max-w-6xl mx-auto">
                {/* HEAD */}
                <div className="mb-8">
                    <div className="flex items-center gap-3 mt-3">
                        <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                            <FaCogs className="text-2xl" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold text-gray-800">Configuración de Gestión</h1>
                            <p className="text-gray-500 text-sm">Parámetros generales y conceptos de facturación.</p>
                        </div>
                    </div>
                </div>

                {/* NAV CARDS */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 max-w-4xl mx-auto">
                    <Link href="/ph/configuracion/modulos" className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-all group cursor-pointer flex items-center gap-4">
                        <div className="p-4 bg-purple-100 text-purple-600 rounded-full group-hover:scale-110 transition-transform">
                            <FaLayerGroup className="text-xl" />
                        </div>
                        <div>
                            <h3 className="font-bold text-gray-800 group-hover:text-purple-700 transition-colors">Módulos de Contribución</h3>
                            <p className="text-xs text-gray-500 mt-1">Definir sectores y grupos de gasto.</p>
                        </div>
                    </Link>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-1 gap-6 max-w-4xl mx-auto">

                    {/* PANEL CENTRAL: CONFIGURACIÓN GENERAL */}
                    <div className="md:col-span-1">
                        <form onSubmit={handleSaveConfig} className="bg-white p-8 rounded-xl shadow-sm border border-gray-100">
                            <h2 className={sectionTitleClass}><FaCogs /> Parámetros Generales</h2>
                            <p className="text-sm text-gray-500 mb-6">Defina aquí las reglas de negocio globales para la facturación y cartera.</p>

                            <div className="space-y-6">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div className="md:col-span-2 space-y-4 p-4 bg-orange-50 rounded-lg border border-orange-100">
                                        <div className="flex items-center justify-between">
                                            <div>
                                                <label className="font-bold text-orange-800">Cobrar Intereses de Mora</label>
                                                <p className="text-xs text-orange-600">Calcula y agrega intereses automáticos a unidades en mora.</p>
                                            </div>
                                            <div className="relative inline-block w-12 mr-2 align-middle select-none transition duration-200 ease-in">
                                                <input type="checkbox" name="interes_mora_habilitado" id="toggle" checked={config.interes_mora_habilitado} onChange={(e) => setConfig({ ...config, interes_mora_habilitado: e.target.checked })} className="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 appearance-none cursor-pointer" style={{ right: config.interes_mora_habilitado ? '0' : '50%' }} />
                                                <label htmlFor="toggle" className={`toggle-label block overflow-hidden h-6 rounded-full cursor-pointer ${config.interes_mora_habilitado ? 'bg-orange-500' : 'bg-gray-300'}`}></label>
                                            </div>
                                        </div>

                                        {/* SECTOR / TIPO DE NEGOCIO */}
                                        <div className="mt-4 pt-4 border-t border-orange-200">
                                            <label className="block text-xs font-bold text-orange-800 uppercase mb-1 tracking-wide">Tipología de Recaudo (Sector)</label>
                                            <select
                                                name="tipo_negocio"
                                                value={config.tipo_negocio || 'PH_RESIDENCIAL'}
                                                onChange={handleConfigChange}
                                                className="w-full px-4 py-2 border border-orange-300 rounded-lg shadow-sm focus:ring-2 focus:ring-orange-500 focus:border-orange-500 text-sm bg-white"
                                            >
                                                <option value="PH_RESIDENCIAL">Propiedad Horizontal (Residencial)</option>
                                                <option value="PH_COMERCIAL">Centro Comercial / Locales</option>
                                                <option value="TRANSPORTE">Cooperativa de Transporte</option>
                                                <option value="EDUCATIVO">Institución Educativa</option>
                                                <option value="PARQUEADERO">Parqueadero / Alquiler Espacios</option>
                                                <option value="CREDITO">Cartera Financiera / Créditos</option>
                                                <option value="GENERICO">Gestión Genérica de Recaudos</option>
                                            </select>
                                            <p className="text-xs text-orange-700 mt-1">Ajusta la terminología del sistema según su negocio (Ej. Unidad vs Vehículo).</p>
                                        </div>

                                        {config.interes_mora_habilitado && (
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                                                <div>
                                                    <label className={labelClass}>Tasa Mensual (%)</label>
                                                    <div className="relative">
                                                        <input type="number" step="0.01" name="interes_mora_mensual" value={config.interes_mora_mensual} onChange={handleConfigChange} className={inputClass} required />
                                                        <span className="absolute right-3 top-2 text-gray-400 text-sm">%</span>
                                                    </div>
                                                </div>
                                                <div>
                                                    <label className={labelClass}>Cuenta Ingreso (Intereses)</label>
                                                    <BuscadorCuentas
                                                        onSelect={(cta) => setConfig({ ...config, cuenta_ingreso_intereses_id: cta.id, cuenta_ingreso_intereses_codigo: cta.codigo, cuenta_ingreso_intereses_nombre: cta.nombre })}
                                                        selectedCodigo={config.cuenta_ingreso_intereses_codigo}
                                                        placeholder="421005 - Intereses"
                                                    />
                                                    <p className="text-xs text-gray-400 mt-1">{config.cuenta_ingreso_intereses_nombre}</p>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                    <div>
                                        <label className={labelClass}>Día Corte Factura</label>
                                        <input type="number" min="1" max="31" name="dia_corte" value={config.dia_corte} onChange={handleConfigChange} className={inputClass} required />
                                        <p className="text-xs text-gray-400 mt-1">Día del mes que se genera la factura.</p>
                                    </div>
                                    <div>
                                        <label className={labelClass}>Día Límite Pago</label>
                                        <input type="number" min="1" max="31" name="dia_limite_pago" value={config.dia_limite_pago} onChange={handleConfigChange} className={inputClass} required />
                                        <p className="text-xs text-gray-400 mt-1">Fecha límite sin mora.</p>
                                    </div>
                                    <div>
                                        <label className={labelClass}>Día Pronto Pago</label>
                                        <input type="number" min="1" max="31" name="dia_limite_pronto_pago" value={config.dia_limite_pronto_pago} onChange={handleConfigChange} className={inputClass} />
                                        <p className="text-xs text-gray-400 mt-1">Límite para descuento.</p>
                                    </div>
                                </div>

                                <div className="pt-4 border-t border-dashed">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div>
                                            <label className={labelClass}>Descuento Pronto Pago (%)</label>
                                            <input type="number" step="0.01" name="descuento_pronto_pago" value={config.descuento_pronto_pago} onChange={handleConfigChange} className={inputClass} />
                                        </div>
                                    </div>
                                </div>

                                <div>
                                    <label className={labelClass}>Mensaje en Factura</label>
                                    <textarea name="mensaje_factura" value={config.mensaje_factura || ''} onChange={handleConfigChange} className={inputClass} rows="3" placeholder="Ej: Recuerde realizar su pago puntualmente..."></textarea>
                                </div>

                                <div className="pt-6 border-t border-dashed bg-gray-50 -mx-8 px-8 pb-4">
                                    <p className="text-xs text-indigo-600 mb-4 font-bold uppercase tracking-wider flex items-center gap-2">
                                        <FaMoneyBillWave /> Integración Contable Global
                                    </p>
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                        <div>
                                            <label className={labelClass}>Tipo Doc. Facturación</label>
                                            <select name="tipo_documento_factura_id" value={config.tipo_documento_factura_id || ''} onChange={handleConfigChange} className={inputClass}>
                                                <option value="">-- Seleccionar --</option>
                                                {tiposDoc.filter(t => t.funcion_especial !== 'PAGO_PROVEEDOR').map(t => (
                                                    <option key={t.id} value={t.id}>{t.codigo} - {t.nombre}</option>
                                                ))}
                                            </select>
                                            <p className="text-xs text-gray-400 mt-1">Usado para generar Cuentas de Cobro.</p>
                                        </div>
                                        <div>
                                            <label className={labelClass}>Tipo Doc. Recaudo</label>
                                            <select name="tipo_documento_recibo_id" value={config.tipo_documento_recibo_id || ''} onChange={handleConfigChange} className={inputClass}>
                                                <option value="">-- Seleccionar --</option>
                                                {tiposDoc.filter(t => t.funcion_especial !== 'FACTURA_VENTA').map(t => (
                                                    <option key={t.id} value={t.id}>{t.codigo} - {t.nombre}</option>
                                                ))}
                                            </select>
                                            <p className="text-xs text-gray-400 mt-1">Usado para registrar pagos de propietarios.</p>
                                        </div>
                                        <div>
                                            <label className={labelClass}>Tipo Doc. Mora/Ajuste</label>
                                            <select name="tipo_documento_mora_id" value={config.tipo_documento_mora_id || ''} onChange={handleConfigChange} className={inputClass}>
                                                <option value="">-- Seleccionar --</option>
                                                {tiposDoc.map(t => (
                                                    <option key={t.id} value={t.id}>{t.codigo} - {t.nombre}</option>
                                                ))}
                                            </select>
                                            <p className="text-xs text-gray-400 mt-1">Usado para cargar la Mora Automática.</p>
                                        </div>
                                    </div>
                                </div>



                                <button type="submit" disabled={saving} className="w-full flex justify-center items-center gap-2 bg-indigo-600 text-white py-3 rounded-lg hover:bg-indigo-700 transition-colors shadow-lg shadow-indigo-200 font-bold text-sm tracking-wide mt-4">
                                    <FaSave /> {saving ? 'Guardando cambios...' : 'GUARDAR PARÁMETROS'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div >
        </div >
    );
}
