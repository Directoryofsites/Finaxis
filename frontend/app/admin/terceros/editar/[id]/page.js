'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import {
    FaUserEdit,
    FaIdCard,
    FaBuilding,
    FaMapMarkerAlt,
    FaCity,
    FaPhone,
    FaEnvelope,
    FaTags,
    FaSave,
    FaSpinner,
    FaExclamationTriangle
} from 'react-icons/fa';


import { useAuth } from '../../../../context/AuthContext';
import { apiService } from '../../../../../lib/apiService';
import { getListasPrecio } from '../../../../../lib/listaPrecioService';
import { municipios } from '../../../../../data/municipios';

// --- ESTILOS REUSABLES (Manual v2.0) ---
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none pl-10";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white pl-10";
const disabledInputClass = "w-full px-4 py-2 border border-gray-200 rounded-lg bg-gray-100 text-gray-500 text-sm shadow-inner pl-10 cursor-not-allowed";

export default function EditarTerceroPage() {
    const { user, authLoading } = useAuth();
    const router = useRouter();
    const params = useParams();
    const { id } = params;

    const [formData, setFormData] = useState({
        nit: '',
        dv: '',
        razon_social: '',
        nombre_comercial: '',
        direccion: '',
        ciudad: '',
        telefono: '',
        email: '',
        es_cliente: false,
        es_proveedor: false,
        es_empleado: false,
        responsabilidad_fiscal: '',
        actividad_economica_ciiu: '',
        es_regimen_simple: false,
        email: '',
        es_cliente: false,
        es_proveedor: false,
        es_empleado: false,
        responsabilidad_fiscal: '',
        actividad_economica_ciiu: '',
        es_regimen_simple: false,
        lista_precio_id: '',
        municipio_dane: '' // Added for DANE support
    });

    const [listasPrecio, setListasPrecio] = useState([]);
    const [listasLoading, setListasLoading] = useState(true);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    // useEffect combinado (Lógica Original Intacta)
    useEffect(() => {
        const fetchData = async () => {
            if (id && user && !authLoading) {
                setIsLoading(true);
                setListasLoading(true);
                setError(null);

                try {
                    const [terceroResponse, listasResponse] = await Promise.all([
                        apiService.get(`/terceros/${id}`),
                        getListasPrecio()
                    ]);

                    const terceroData = terceroResponse.data;
                    setFormData({
                        nit: terceroData.nit || '',
                        dv: terceroData.dv || '',
                        razon_social: terceroData.razon_social || '',
                        nombre_comercial: terceroData.nombre_comercial || '',
                        direccion: terceroData.direccion || '',
                        ciudad: terceroData.ciudad || '',
                        telefono: terceroData.telefono || '',
                        email: terceroData.email || '',
                        es_cliente: terceroData.es_cliente || false,
                        es_proveedor: terceroData.es_proveedor || false,
                        es_empleado: terceroData.es_empleado || false,
                        responsabilidad_fiscal: terceroData.responsabilidad_fiscal || '',
                        actividad_economica_ciiu: terceroData.actividad_economica_ciiu || '',
                        es_regimen_simple: terceroData.es_regimen_simple || false,
                        es_regimen_simple: terceroData.es_regimen_simple || false,
                        lista_precio_id: terceroData.lista_precio_id ? String(terceroData.lista_precio_id) : '',
                        municipio_dane: terceroData.municipio_dane || '' // Load existing code
                    });

                    setListasPrecio(listasResponse || []);

                } catch (err) {
                    setError(err.response?.data?.detail || "Error al cargar los datos necesarios.");
                    console.error("Error fetching data:", err);
                } finally {
                    setIsLoading(false);
                    setListasLoading(false);
                }
            } else if (!authLoading && !user) {
                setError("Usuario no autenticado.");
                setIsLoading(false);
                setListasLoading(false);
            }
        };

        fetchData();
    }, [id, user, authLoading]);

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prevData => ({
            ...prevData,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        const listaPrecioIdFinal = formData.lista_precio_id ? parseInt(formData.lista_precio_id, 10) : null;

        const { nit, ...updatePayload } = formData;
        updatePayload.lista_precio_id = listaPrecioIdFinal;

        updatePayload.nombre_comercial = updatePayload.nombre_comercial || null;
        updatePayload.direccion = updatePayload.direccion || null;
        updatePayload.ciudad = updatePayload.ciudad || null;
        updatePayload.telefono = updatePayload.telefono || null;
        updatePayload.email = updatePayload.email || null;
        updatePayload.responsabilidad_fiscal = updatePayload.responsabilidad_fiscal || null;
        updatePayload.actividad_economica_ciiu = updatePayload.actividad_economica_ciiu || null;
        updatePayload.actividad_economica_ciiu = updatePayload.actividad_economica_ciiu || null;
        updatePayload.dv = updatePayload.dv || null;
        updatePayload.municipio_dane = updatePayload.municipio_dane || null;

        try {
            await apiService.put(`/terceros/${id}`, updatePayload);
            router.push('/admin/terceros');

        } catch (err) {
            setError(err.response?.data?.detail || 'Error al actualizar el tercero.');
            console.error("Error updating tercero:", err.response?.data || err);
        } finally {
            setIsLoading(false);
        }
    };

    if (authLoading || (isLoading && !formData.razon_social)) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
                <FaUserEdit className="text-indigo-300 text-6xl mb-4 animate-pulse" />
                <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando información del tercero...</p>
            </div>
        );
    }

    if (error && !formData.razon_social) {
        return (
            <div className="min-h-screen bg-gray-50 p-6 flex items-center justify-center">
                <div className="bg-white p-8 rounded-xl shadow-lg border border-red-100 max-w-2xl text-center">
                    <FaExclamationTriangle className="text-4xl text-red-500 mx-auto mb-4" />
                    <h2 className="text-2xl font-bold text-gray-800 mb-2">Error de Carga</h2>
                    <p className="text-gray-600 mb-6">{error}</p>
                    <div className="flex justify-center">
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
            <div className="max-w-5xl mx-auto">

                {/* ENCABEZADO */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                    <div>
                        <div className="flex items-center gap-3 mt-3">
                            <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                                <FaUserEdit className="text-2xl" />
                            </div>
                            <div>
                                <h1 className="text-3xl font-bold text-gray-800">Editar Tercero</h1>
                                <p className="text-gray-500 text-sm">Actualizar información maestra del cliente/proveedor.</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* FORMULARIO CARD */}
                <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-8 animate-fadeIn">
                    <form onSubmit={handleSubmit} className="space-y-8">

                        {/* SECCIÓN 1: IDENTIFICACIÓN Y BÁSICOS */}
                        <div>
                            <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2 border-b border-gray-100 pb-2">
                                <span className="bg-indigo-100 text-indigo-600 w-6 h-6 flex items-center justify-center rounded-full text-xs">1</span>
                                Identificación
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
                                {/* NIT (No Editable) */}
                                <div className="md:col-span-5">
                                    <label className={labelClass}>NIT / Cédula</label>
                                    <div className="relative">
                                        <input type="text" value={formData.nit} disabled className={disabledInputClass} />
                                        <FaIdCard className="absolute left-3 top-3 text-gray-400" />
                                    </div>
                                </div>
                                {/* DV */}
                                <div className="md:col-span-1">
                                    <label htmlFor="dv" className={labelClass}>DV</label>
                                    <input type="text" name="dv" id="dv" maxLength="1" value={formData.dv} onChange={handleChange} className="w-full px-2 py-2 border border-gray-300 rounded-lg shadow-sm text-center text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none" />
                                </div>
                                {/* Razón Social */}
                                <div className="md:col-span-6">
                                    <label htmlFor="razon_social" className={labelClass}>Razón Social / Nombre <span className="text-red-500">*</span></label>
                                    <div className="relative">
                                        <input type="text" name="razon_social" id="razon_social" value={formData.razon_social} onChange={handleChange} className={inputClass} required />
                                        <FaBuilding className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                    </div>
                                </div>
                                {/* Nombre Comercial */}
                                <div className="md:col-span-6">
                                    <label htmlFor="nombre_comercial" className={labelClass}>Nombre Comercial (Opcional)</label>
                                    <div className="relative">
                                        <input type="text" name="nombre_comercial" id="nombre_comercial" value={formData.nombre_comercial} onChange={handleChange} className={inputClass} />
                                        <FaBuilding className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* SECCIÓN 2: CONTACTO Y UBICACIÓN */}
                        <div>
                            <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2 border-b border-gray-100 pb-2">
                                <span className="bg-indigo-100 text-indigo-600 w-6 h-6 flex items-center justify-center rounded-full text-xs">2</span>
                                Ubicación y Contacto
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <label htmlFor="direccion" className={labelClass}>Dirección</label>
                                    <div className="relative">
                                        <input type="text" name="direccion" id="direccion" value={formData.direccion} onChange={handleChange} className={inputClass} />
                                        <FaMapMarkerAlt className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                    </div>
                                </div>
                                <div>
                                    <label htmlFor="municipio_dane" className={labelClass}>Ciudad / Municipio (DANE)</label>
                                    <div className="relative">
                                        <select
                                            name="municipio_dane"
                                            id="municipio_dane"
                                            value={formData.municipio_dane}
                                            onChange={(e) => {
                                                const selected = municipios.find(m => m.codigo === e.target.value);
                                                setFormData(prev => ({
                                                    ...prev,
                                                    municipio_dane: e.target.value,
                                                    ciudad: selected ? selected.nombre : ''
                                                }));
                                            }}
                                            className={selectClass}
                                        >
                                            <option value="">-- Seleccione Ciudad --</option>
                                            {municipios.map(m => (
                                                <option key={m.codigo} value={m.codigo}>{m.nombre} - {m.departmento}</option>
                                            ))}
                                        </select>
                                        <FaCity className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                    </div>
                                    <input type="hidden" name="ciudad" value={formData.ciudad} />
                                </div>
                                <div>
                                    <label htmlFor="telefono" className={labelClass}>Teléfono</label>
                                    <div className="relative">
                                        <input type="tel" name="telefono" id="telefono" value={formData.telefono} onChange={handleChange} className={inputClass} />
                                        <FaPhone className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                    </div>
                                </div>
                                <div>
                                    <label htmlFor="email" className={labelClass}>Correo Electrónico</label>
                                    <div className="relative">
                                        <input type="email" name="email" id="email" value={formData.email} onChange={handleChange} className={inputClass} />
                                        <FaEnvelope className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* SECCIÓN 3: INFORMACIÓN FISCAL Y COMERCIAL */}
                        <div>
                            <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2 border-b border-gray-100 pb-2">
                                <span className="bg-indigo-100 text-indigo-600 w-6 h-6 flex items-center justify-center rounded-full text-xs">3</span>
                                Detalles Fiscales y Comerciales
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <label htmlFor="responsabilidad_fiscal" className={labelClass}>Responsabilidad Fiscal</label>
                                    <div className="relative">
                                        <select
                                            name="responsabilidad_fiscal"
                                            id="responsabilidad_fiscal"
                                            value={formData.responsabilidad_fiscal}
                                            onChange={handleChange}
                                            className={selectClass}
                                        >
                                            <option value="R-99-PN">No Aplica - Otros (R-99-PN)</option>
                                            {/* Importar lista de municipios si es necesario o hardcodear si import falla */}
                                            <option value="O-13">Gran Contribuyente</option>
                                            <option value="O-15">Autorretenedor</option>
                                            <option value="O-23">Agente de Retención IVA</option>
                                            <option value="O-47">Régimen Simple de Tributación</option>
                                        </select>
                                        <FaTags className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                    </div>
                                </div>
                                <div>
                                    <label htmlFor="actividad_economica_ciiu" className={labelClass}>Actividad Económica (CIIU)</label>
                                    <input type="text" name="actividad_economica_ciiu" id="actividad_economica_ciiu" value={formData.actividad_economica_ciiu} onChange={handleChange} className={`${inputClass} pl-4`} />
                                </div>

                                <div className="md:col-span-2">
                                    <div className="flex items-center p-3 bg-gray-50 rounded-lg border border-gray-200">
                                        <input type="checkbox" id="es_regimen_simple" name="es_regimen_simple" checked={formData.es_regimen_simple} onChange={handleChange} className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded cursor-pointer" />
                                        <label htmlFor="es_regimen_simple" className="ml-2 block text-sm text-gray-700 font-medium cursor-pointer">Pertenece al Régimen Simple de Tributación</label>
                                    </div>
                                </div>

                                {/* Lista de Precios */}
                                <div className="md:col-span-2">
                                    <label htmlFor="lista_precio_id" className={labelClass}>Lista de Precios Asignada</label>
                                    <div className="relative">
                                        <select name="lista_precio_id" id="lista_precio_id" value={formData.lista_precio_id} onChange={handleChange} className={selectClass}>
                                            <option value="">-- Ninguna (Precio Base) --</option>
                                            {listasPrecio.map((lista) => (
                                                <option key={lista.id} value={lista.id}>{lista.nombre}</option>
                                            ))}
                                        </select>
                                        <FaTags className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                    </div>
                                </div>

                                {/* Clasificación */}
                                <div className="md:col-span-2">
                                    <label className={labelClass}>Tipo de Tercero</label>
                                    <div className="flex flex-wrap gap-4 mt-2">
                                        <label className="flex items-center space-x-2 cursor-pointer bg-white px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                                            <input type="checkbox" name="es_cliente" checked={formData.es_cliente} onChange={handleChange} className="h-4 w-4 text-blue-600 rounded focus:ring-blue-500" />
                                            <span className="text-sm font-medium text-gray-700">Cliente</span>
                                        </label>
                                        <label className="flex items-center space-x-2 cursor-pointer bg-white px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                                            <input type="checkbox" name="es_proveedor" checked={formData.es_proveedor} onChange={handleChange} className="h-4 w-4 text-green-600 rounded focus:ring-green-500" />
                                            <span className="text-sm font-medium text-gray-700">Proveedor</span>
                                        </label>
                                        <label className="flex items-center space-x-2 cursor-pointer bg-white px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                                            <input type="checkbox" name="es_empleado" checked={formData.es_empleado} onChange={handleChange} className="h-4 w-4 text-purple-600 rounded focus:ring-purple-500" />
                                            <span className="text-sm font-medium text-gray-700">Empleado</span>
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* MENSAJE DE ERROR EN GUARDADO */}
                        {error && (
                            <div className="p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded-r-lg flex items-center gap-3 animate-pulse">
                                <FaExclamationTriangle className="text-xl" />
                                <div>
                                    <p className="font-bold">Error al guardar:</p>
                                    <p className="text-sm">{error}</p>
                                </div>
                            </div>
                        )}

                        {/* BOTÓN GUARDAR */}
                        <div className="flex justify-end pt-4 border-t border-gray-100">
                            <button
                                type="submit"
                                disabled={isLoading}
                                className={`
                            px-8 py-3 rounded-lg shadow-lg font-bold text-white text-lg transition-all transform hover:-translate-y-0.5 flex items-center gap-2
                            ${isLoading ? 'bg-gray-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'}
                        `}
                            >
                                {isLoading ? (
                                    <> <FaSpinner className="animate-spin" /> Guardando... </>
                                ) : (
                                    <> <FaSave /> Guardar Cambios </>
                                )}
                            </button>
                        </div>

                    </form>
                </div>
            </div>
        </div>
    );
}