'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '../../context/AuthContext';
import { useRecaudos } from '../../../contexts/RecaudosContext';

import { phService } from '../../../lib/phService';
import BuscadorCuentas from '../../../components/BuscadorCuentas';
import { FaCogs, FaSave, FaPlus, FaTrash, FaEdit, FaExclamationTriangle, FaListUl, FaMoneyBillWave, FaLayerGroup, FaBuilding, FaLightbulb } from 'react-icons/fa';
import ManualButton from '../../components/ManualButton';

// Estilos
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none";
const sectionTitleClass = "text-lg font-bold text-gray-700 flex items-center gap-2 border-b pb-2 mb-4";

export default function ConfiguracionPHPage() {
    const { user, loading: authLoading } = useAuth();
    const { labels, refreshConfig } = useRecaudos();

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
        cuenta_ingreso_intereses_nombre: '',
        cuenta_anticipos_id: '',
        cuenta_anticipos_codigo: '',
        cuenta_anticipos_nombre: '',
        cuenta_descuento_id: '',
        cuenta_descuento_codigo: '',
        cuenta_descuento_nombre: ''
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
                cuenta_anticipos_codigo: configData.cuenta_anticipos ? configData.cuenta_anticipos.codigo : '',
                cuenta_anticipos_nombre: configData.cuenta_anticipos ? configData.cuenta_anticipos.nombre : '',
                cuenta_descuento_codigo: configData.cuenta_descuento ? configData.cuenta_descuento.codigo : '',
                cuenta_descuento_nombre: configData.cuenta_descuento ? configData.cuenta_descuento.nombre : '',
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
            const payload = {
                interes_mora_mensual: parseFloat(config.interes_mora_mensual) || 0,
                dia_corte: parseInt(config.dia_corte) || 1,
                dia_limite_pago: parseInt(config.dia_limite_pago) || 1,
                dia_limite_pronto_pago: parseInt(config.dia_limite_pronto_pago) || 1,
                descuento_pronto_pago: parseFloat(config.descuento_pronto_pago) || 0,
                mensaje_factura: config.mensaje_factura || null,
                interes_mora_habilitado: Boolean(config.interes_mora_habilitado),
                descuento_pronto_pago_habilitado: Boolean(config.descuento_pronto_pago_habilitado),
                tipo_negocio: config.tipo_negocio || 'PH_RESIDENCIAL',
                cuenta_ingreso_intereses_id: config.cuenta_ingreso_intereses_id || null,
                cuenta_anticipos_id: config.cuenta_anticipos_id || null,
                cuenta_descuento_id: config.cuenta_descuento_id || null,
                tipo_documento_factura_id: config.tipo_documento_factura_id || null,
                tipo_documento_recibo_id: config.tipo_documento_recibo_id || null,
                tipo_documento_cruce_id: config.tipo_documento_cruce_id || null,
                tipo_documento_mora_id: config.tipo_documento_mora_id || null,
                cuenta_cartera_id: config.cuenta_cartera_id || null,
                cuenta_caja_id: config.cuenta_caja_id || null
            };
            await phService.updateConfiguracion(payload);
            await refreshConfig(); // Actualizar el contexto con el nuevo tipo de negocio
            alert('Configuración guardada correctamente.');
        } catch (err) {
            console.error(err);
            console.error(err.response?.data);
            alert(`Error guardando configuración: ${JSON.stringify(err.response?.data?.detail || err.message)}`);
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
                    <div className="flex justify-between items-start">
                        <div className="flex items-center gap-3 mt-3">
                            <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                                <FaCogs className="text-2xl" />
                            </div>
                            <div>
                                <h1 className="text-3xl font-bold text-gray-800">Configuración de Gestión</h1>
                                <p className="text-gray-500 text-sm">Parámetros generales y conceptos de facturación.</p>
                            </div>
                        </div>
                        <div className="mt-3 flex gap-2">
                            <ManualButton
                                manualPath="configuracion.html"
                                title="Manual de Configuración"
                                position="header"
                            />
                            <ManualButton
                                manualPath="manual_recaudos_super.html"
                                title="Súper Manual de Consultoría"
                                position="header"
                                icon={<FaLightbulb className="text-sm" />}
                                className="bg-purple-600 hover:bg-purple-700 shadow-purple-100"
                            />
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

                    <Link href="/ph/configuracion/torres" className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-all group cursor-pointer flex items-center gap-4">
                        <div className="p-4 bg-indigo-100 text-indigo-600 rounded-full group-hover:scale-110 transition-transform">
                            <FaBuilding className="text-xl" />
                        </div>
                        <div>
                            <h3 className="font-bold text-gray-800 group-hover:text-indigo-700 transition-colors">Gestionar {labels?.torre_plural || 'Torres'}</h3>
                            <p className="text-xs text-gray-500 mt-1">Definir {labels?.torre_plural?.toLowerCase() || 'torres'}, bloques o zonas.</p>
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
                                <div className="grid grid-cols-1 gap-6">
                                    {/* BLOQUE 1: INTERESES DE MORA Y PARÁMETROS BÁSICOS */}
                                    <div className="space-y-4 p-5 bg-orange-50 rounded-xl border border-orange-100 shadow-sm">
                                        <div className="flex items-center justify-between border-b border-orange-200 pb-3">
                                            <div>
                                                <h3 className="font-bold text-orange-800 text-lg">Cobrar Intereses de Mora</h3>
                                                <p className="text-xs text-orange-600">Calcula y agrega intereses automáticos a unidades en mora.</p>
                                            </div>
                                            <div className="relative inline-block w-12 mr-2 align-middle select-none transition duration-200 ease-in">
                                                <input type="checkbox" name="interes_mora_habilitado" id="toggle_mora" checked={config.interes_mora_habilitado} onChange={(e) => setConfig({ ...config, interes_mora_habilitado: e.target.checked })} className="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 appearance-none cursor-pointer" style={{ right: config.interes_mora_habilitado ? '0' : '50%' }} />
                                                <label htmlFor="toggle_mora" className={`toggle-label block overflow-hidden h-6 rounded-full cursor-pointer ${config.interes_mora_habilitado ? 'bg-orange-500' : 'bg-gray-300'}`}></label>
                                            </div>
                                        </div>

                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <div>
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
                                            </div>
                                            <div>
                                                <label className="block text-xs font-bold text-orange-800 uppercase mb-1 tracking-wide">Día Límite de Pago (Inicio de Mora)</label>
                                                <input type="number" min="1" max="31" name="dia_limite_pago" value={config.dia_limite_pago} onChange={handleConfigChange} className="w-full px-4 py-2 border border-orange-300 rounded-lg shadow-sm focus:ring-2 focus:ring-orange-500 text-sm bg-white" required />
                                                <p className="text-xs text-orange-600 mt-1">Días posteriores generan mora.</p>
                                            </div>
                                        </div>

                                        {config.interes_mora_habilitado && (
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
                                                <div>
                                                    <label className="block text-xs font-bold text-orange-800 uppercase mb-1 tracking-wide">Tasa Mensual (%)</label>
                                                    <div className="relative">
                                                        <input type="number" step="0.01" name="interes_mora_mensual" value={config.interes_mora_mensual} onChange={handleConfigChange} className="w-full px-4 py-2 border border-orange-300 rounded-lg shadow-sm focus:ring-2 focus:ring-orange-500 text-sm bg-white" required />
                                                        <span className="absolute right-3 top-2 text-gray-400 text-sm">%</span>
                                                    </div>
                                                </div>
                                                <div>
                                                    <label className="block text-xs font-bold text-orange-800 uppercase mb-1 tracking-wide">Cuenta Ingreso (Intereses)</label>
                                                    <BuscadorCuentas
                                                        onSelect={(cta) => setConfig({ ...config, cuenta_ingreso_intereses_id: cta ? cta.id : null, cuenta_ingreso_intereses_codigo: cta ? cta.codigo : '', cuenta_ingreso_intereses_nombre: cta ? cta.nombre : '' })}
                                                        selectedCodigo={config.cuenta_ingreso_intereses_codigo}
                                                        placeholder="421005 - Intereses"
                                                        filterPrefix="4"
                                                    />
                                                    <p className="text-xs text-orange-600 mt-1">{config.cuenta_ingreso_intereses_nombre}</p>
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    {/* BLOQUE 2: DESCUENTO PRONTO PAGO */}
                                    <div className="space-y-4 p-5 bg-teal-50 rounded-xl border border-teal-100 shadow-sm">
                                        <div className="border-b border-teal-200 pb-2 flex justify-between items-center">
                                            <div>
                                                <h3 className="font-bold text-teal-800 text-lg">Descuento por Pronto Pago</h3>
                                                <p className="text-xs text-teal-600">Incentiva el recaudo temprano ofreciendo reducciones automáticas.</p>
                                            </div>
                                            <div className="relative inline-block w-12 mr-2 align-middle select-none transition duration-200 ease-in">
                                                <input type="checkbox" name="descuento_pronto_pago_habilitado" id="toggle_dpp" checked={config.descuento_pronto_pago_habilitado !== false} onChange={(e) => setConfig({ ...config, descuento_pronto_pago_habilitado: e.target.checked })} className="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 appearance-none cursor-pointer" style={{ right: config.descuento_pronto_pago_habilitado !== false ? '0' : '50%' }} />
                                                <label htmlFor="toggle_dpp" className={`toggle-label block overflow-hidden h-6 rounded-full cursor-pointer ${config.descuento_pronto_pago_habilitado !== false ? 'bg-teal-500' : 'bg-gray-300'}`}></label>
                                            </div>
                                        </div>
                                        
                                        {config.descuento_pronto_pago_habilitado !== false && (
                                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                            <div>
                                                <label className="block text-xs font-bold text-teal-800 uppercase mb-1 tracking-wide">Día Límite (Pronto Pago)</label>
                                                <input type="number" min="1" max="31" name="dia_limite_pronto_pago" value={config.dia_limite_pronto_pago} onChange={handleConfigChange} className="w-full px-4 py-2 border border-teal-300 rounded-lg shadow-sm focus:ring-2 focus:ring-teal-500 text-sm bg-white" />
                                                <p className="text-xs text-teal-600 mt-1">Pagos hasta este día tienen Dto.</p>
                                            </div>
                                            <div>
                                                <label className="block text-xs font-bold text-teal-800 uppercase mb-1 tracking-wide">Descuento (%)</label>
                                                <div className="relative">
                                                    <input type="number" step="0.01" name="descuento_pronto_pago" value={config.descuento_pronto_pago} onChange={handleConfigChange} className="w-full px-4 py-2 border border-teal-300 rounded-lg shadow-sm focus:ring-2 focus:ring-teal-500 text-sm bg-white" />
                                                    <span className="absolute right-3 top-2 text-gray-400 text-sm">%</span>
                                                </div>
                                            </div>
                                            <div>
                                                <label className="block text-xs font-bold text-teal-800 uppercase mb-1 tracking-wide">Cuenta Contable</label>
                                                <BuscadorCuentas
                                                    onSelect={(cta) => setConfig({ ...config, cuenta_descuento_id: cta ? cta.id : null, cuenta_descuento_codigo: cta ? cta.codigo : '', cuenta_descuento_nombre: cta ? cta.nombre : '' })}
                                                    selectedCodigo={config.cuenta_descuento_codigo}
                                                    placeholder="4175... Menor Valor"
                                                    filterPrefix="4"
                                                />
                                                <p className="text-xs text-teal-600 mt-1">{config.cuenta_descuento_nombre}</p>
                                            </div>
                                        </div>
                                        )}
                                    </div>

                                    {/* BLOQUE 3: OTRAS CONFIGURACIONES DE FACTURA */}
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div>
                                            <label className={labelClass}>Día Corte Factura</label>
                                            <input type="number" min="1" max="31" name="dia_corte" value={config.dia_corte} onChange={handleConfigChange} className={inputClass} required />
                                            <p className="text-xs text-gray-400 mt-1">Día del mes que se genera la factura.</p>
                                        </div>
                                        <div>
                                            <label className={labelClass}>Mensaje Fijo en Factura</label>
                                            <textarea name="mensaje_factura" value={config.mensaje_factura || ''} onChange={handleConfigChange} className={inputClass} rows="2" placeholder="Ej: Recuerde realizar su pago puntualmente..."></textarea>
                                        </div>
                                    </div>
                                </div>

                                <div className="pt-6 border-t border-dashed bg-gray-50 -mx-8 px-8 pb-4">
                                    <p className="text-xs text-indigo-600 mb-4 font-bold uppercase tracking-wider flex items-center gap-2">
                                        <FaMoneyBillWave /> Integración Contable Global
                                    </p>
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                        <div>
                                            <label className={labelClass}>Tipo Doc. Facturación</label>
                                            <select name="tipo_documento_factura_id" value={config.tipo_documento_factura_id || ''} onChange={(e) => setConfig({ ...config, tipo_documento_factura_id: e.target.value ? parseInt(e.target.value) : null })} className={inputClass}>
                                                <option value="">-- Seleccionar --</option>
                                                {(Array.isArray(tiposDoc) ? tiposDoc : []).filter(t => t.funcion_especial !== 'PAGO_PROVEEDOR').map(t => (
                                                    <option key={t.id} value={t.id}>{t.codigo} - {t.nombre}</option>
                                                ))}
                                            </select>
                                            <p className="text-xs text-gray-400 mt-1">Usado para generar Cuentas de Cobro.</p>
                                        </div>
                                        <div>
                                            <label className={labelClass}>Tipo Doc. Recaudo</label>
                                            <select name="tipo_documento_recibo_id" value={config.tipo_documento_recibo_id || ''} onChange={(e) => setConfig({ ...config, tipo_documento_recibo_id: e.target.value ? parseInt(e.target.value) : null })} className={inputClass}>
                                                <option value="">-- Seleccionar --</option>
                                                {(Array.isArray(tiposDoc) ? tiposDoc : []).filter(t => t.funcion_especial !== 'FACTURA_VENTA').map(t => (
                                                    <option key={t.id} value={t.id}>{t.codigo} - {t.nombre}</option>
                                                ))}
                                            </select>
                                            <p className="text-xs text-gray-400 mt-1">Usado para registrar pagos de propietarios.</p>
                                        </div>
                                        <div>
                                            <label className={labelClass}>Tipo Doc. Cruce Anticipos</label>
                                            <select name="tipo_documento_cruce_id" value={config.tipo_documento_cruce_id || ''} onChange={(e) => setConfig({ ...config, tipo_documento_cruce_id: e.target.value ? parseInt(e.target.value) : null })} className={inputClass}>
                                                <option value="">-- Seleccionar --</option>
                                                {(Array.isArray(tiposDoc) ? tiposDoc : []).map(t => (
                                                    <option key={t.id} value={t.id}>{t.codigo} - {t.nombre}</option>
                                                ))}
                                            </select>
                                            <p className="text-xs text-gray-400 mt-1">Usado para aplicar saldos a favor (Ej. NC).</p>
                                        </div>
                                        <div className="md:col-span-1">
                                            <label className="block text-xs font-bold text-indigo-800 uppercase mb-1">Cuenta de Anticipos (Pasivo)</label>
                                            <BuscadorCuentas
                                                onSelect={(cta) => setConfig({ ...config, cuenta_anticipos_id: cta ? cta.id : null, cuenta_anticipos_codigo: cta ? cta.codigo : '', cuenta_anticipos_nombre: cta ? cta.nombre : '' })}
                                                selectedCodigo={config.cuenta_anticipos_codigo}
                                                placeholder="280505 - Anticipos"
                                                filterPrefix="2"
                                            />
                                            <p className="text-xs text-indigo-700 mt-1">{config.cuenta_anticipos_nombre || 'Mueve excedentes de pago a este Pasivo automáticamente.'}</p>
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
