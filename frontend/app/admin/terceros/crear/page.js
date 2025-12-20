'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
    FaUserPlus,
    FaIdCard,
    FaBuilding,
    FaMapMarkerAlt,
    FaCity,
    FaPhone,
    FaEnvelope,
    FaTags,
    FaSave,
    FaSpinner,
    FaExclamationTriangle,
    FaInfoCircle
} from 'react-icons/fa';


import { useAuth } from '../../../context/AuthContext';
import { apiService } from '../../../../lib/apiService';
import { getListasPrecio } from '../../../../lib/listaPrecioService';

// --- ESTILOS REUSABLES (Manual v2.0) ---
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none pl-10";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white pl-10";

export default function CrearTerceroPage() {
    const router = useRouter();
    const { user, authLoading } = useAuth();

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
        lista_precio_id: ''
    });

    const [listasPrecio, setListasPrecio] = useState([]);
    const [listasLoading, setListasLoading] = useState(true);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [nameWarning, setNameWarning] = useState('');

    // Carga de Listas de Precio
    useEffect(() => {
        const fetchListas = async () => {
            if (user) {
                try {
                    setListasLoading(true);
                    const data = await getListasPrecio();
                    setListasPrecio(data || []);
                } catch (err) {
                    setError("Error al cargar las listas de precios.");
                    console.error(err);
                } finally {
                    setListasLoading(false);
                }
            }
        };
        if (!authLoading) {
            fetchListas();
        }
    }, [user, authLoading]);

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

        if (!user?.empresaId) {
            setError("No se pudo identificar la empresa del usuario. Por favor, inicie sesión de nuevo.");
            setIsLoading(false);
            return;
        }

        const listaPrecioIdFinal = formData.lista_precio_id ? parseInt(formData.lista_precio_id, 10) : null;

        const payload = {
            ...formData,
            empresa_id: user.empresaId,
            lista_precio_id: listaPrecioIdFinal,
            nombre_comercial: formData.nombre_comercial || null,
            direccion: formData.direccion || null,
            ciudad: formData.ciudad || null,
            telefono: formData.telefono || null,
            email: formData.email || null,
            responsabilidad_fiscal: formData.responsabilidad_fiscal || null,
            actividad_economica_ciiu: formData.actividad_economica_ciiu || null,
            dv: formData.dv || null,
        };

        try {
            await apiService.post('/terceros/', payload);
            router.push('/admin/terceros');
        } catch (err) {
            setError(err.response?.data?.detail || 'Ocurrió un error al crear el tercero.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleNameCheck = async () => {
        if (isLoading || !formData.razon_social || !user) {
            setNameWarning('');
            return;
        }
        try {
            const response = await apiService.get(`/terceros/check-name/?nombre=${encodeURIComponent(formData.razon_social)}`);
            if (response.data.existe) {
                setNameWarning('⚠️ Atención: Ya existe un tercero con un nombre similar.');
            } else {
                setNameWarning('');
            }
        } catch (err) {
            console.error("Error validación nombre:", err);
        }
    };

    if (authLoading || listasLoading) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
                <FaUserPlus className="text-indigo-300 text-6xl mb-4 animate-pulse" />
                <p className="text-indigo-600 font-semibold text-lg animate-pulse">Preparando formulario...</p>
            </div>
        );
    }

    if (!user) return null;

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
            <div className="max-w-5xl mx-auto">

                {/* ENCABEZADO */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                    <div>
                        <div className="flex items-center gap-3 mt-3">
                            <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                                <FaUserPlus className="text-2xl" />
                            </div>
                            <div>
                                <h1 className="text-3xl font-bold text-gray-800">Crear Nuevo Tercero</h1>
                                <p className="text-gray-500 text-sm">Registro maestro de clientes, proveedores o empleados.</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* CARD FORMULARIO */}
                <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-8 animate-fadeIn">
                    <form onSubmit={handleSubmit} className="space-y-8">

                        {/* SECCIÓN 1: IDENTIFICACIÓN */}
                        <div>
                            <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2 border-b border-gray-100 pb-2">
                                <span className="bg-indigo-100 text-indigo-600 w-6 h-6 flex items-center justify-center rounded-full text-xs">1</span>
                                Identificación Básica
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
                                <div className="md:col-span-5">
                                    <label htmlFor="nit" className={labelClass}>NIT / Cédula <span className="text-red-500">*</span></label>
                                    <div className="relative">
                                        <input type="text" name="nit" id="nit" value={formData.nit} onChange={handleChange} className={inputClass} required autoFocus />
                                        <FaIdCard className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                    </div>
                                </div>
                                <div className="md:col-span-1">
                                    <label htmlFor="dv" className={labelClass}>DV</label>
                                    <input type="text" name="dv" id="dv" maxLength="1" value={formData.dv} onChange={handleChange} className="w-full px-2 py-2 border border-gray-300 rounded-lg shadow-sm text-center text-sm focus:ring-2 focus:ring-indigo-500 outline-none" />
                                </div>
                                <div className="md:col-span-6">
                                    <label htmlFor="razon_social" className={labelClass}>Razón Social / Nombre <span className="text-red-500">*</span></label>
                                    <div className="relative">
                                        <input type="text" name="razon_social" id="razon_social" value={formData.razon_social} onChange={handleChange} onBlur={handleNameCheck} className={inputClass} required />
                                        <FaBuilding className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                    </div>
                                    {nameWarning && (
                                        <div className="mt-2 flex items-center gap-2 text-amber-600 text-xs font-bold bg-amber-50 p-2 rounded border border-amber-200">
                                            <FaInfoCircle /> {nameWarning}
                                        </div>
                                    )}
                                </div>
                                <div className="md:col-span-6">
                                    <label htmlFor="nombre_comercial" className={labelClass}>Nombre Comercial (Opcional)</label>
                                    <div className="relative">
                                        <input type="text" name="nombre_comercial" id="nombre_comercial" value={formData.nombre_comercial} onChange={handleChange} className={inputClass} />
                                        <FaBuilding className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* SECCIÓN 2: UBICACIÓN Y CONTACTO */}
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
                                    <label htmlFor="ciudad" className={labelClass}>Ciudad</label>
                                    <div className="relative">
                                        <input type="text" name="ciudad" id="ciudad" value={formData.ciudad} onChange={handleChange} className={inputClass} />
                                        <FaCity className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                    </div>
                                </div>
                                <div>
                                    <label htmlFor="telefono" className={labelClass}>Teléfono</label>
                                    <div className="relative">
                                        <input type="tel" name="telefono" id="telefono" value={formData.telefono} onChange={handleChange} className={inputClass} />
                                        <FaPhone className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                    </div>
                                </div>
                                <div>
                                    <label htmlFor="email" className={labelClass}>Email</label>
                                    <div className="relative">
                                        <input type="email" name="email" id="email" value={formData.email} onChange={handleChange} className={inputClass} />
                                        <FaEnvelope className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* SECCIÓN 3: CLASIFICACIÓN */}
                        <div>
                            <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2 border-b border-gray-100 pb-2">
                                <span className="bg-indigo-100 text-indigo-600 w-6 h-6 flex items-center justify-center rounded-full text-xs">3</span>
                                Clasificación y Fiscal
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <label htmlFor="lista_precio_id" className={labelClass}>Lista de Precios</label>
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
                                <div>
                                    <label htmlFor="responsabilidad_fiscal" className={labelClass}>Resp. Fiscal</label>
                                    <input type="text" name="responsabilidad_fiscal" id="responsabilidad_fiscal" placeholder="Ej: R-99-PN" value={formData.responsabilidad_fiscal} onChange={handleChange} className={`${inputClass} pl-4`} />
                                </div>
                                <div>
                                    <label htmlFor="actividad_economica_ciiu" className={labelClass}>Actividad CIIU</label>
                                    <input type="text" name="actividad_economica_ciiu" id="actividad_economica_ciiu" value={formData.actividad_economica_ciiu} onChange={handleChange} className={`${inputClass} pl-4`} />
                                </div>

                                {/* Checkboxes */}
                                <div className="md:col-span-2 space-y-3 pt-2">
                                    <div className="flex flex-wrap gap-4">
                                        <label className="flex items-center space-x-2 cursor-pointer bg-white px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                                            <input type="checkbox" name="es_cliente" checked={formData.es_cliente} onChange={handleChange} className="h-4 w-4 text-blue-600 rounded focus:ring-blue-500" />
                                            <span className="text-sm font-medium text-gray-700">Es Cliente</span>
                                        </label>
                                        <label className="flex items-center space-x-2 cursor-pointer bg-white px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                                            <input type="checkbox" name="es_proveedor" checked={formData.es_proveedor} onChange={handleChange} className="h-4 w-4 text-green-600 rounded focus:ring-green-500" />
                                            <span className="text-sm font-medium text-gray-700">Es Proveedor</span>
                                        </label>
                                        <label className="flex items-center space-x-2 cursor-pointer bg-white px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                                            <input type="checkbox" name="es_empleado" checked={formData.es_empleado} onChange={handleChange} className="h-4 w-4 text-purple-600 rounded focus:ring-purple-500" />
                                            <span className="text-sm font-medium text-gray-700">Es Empleado</span>
                                        </label>
                                    </div>

                                    <div className="flex items-center p-3 bg-gray-50 rounded-lg border border-gray-200 w-full md:w-1/2">
                                        <input type="checkbox" name="es_regimen_simple" checked={formData.es_regimen_simple} onChange={handleChange} className="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500" />
                                        <label className="ml-2 block text-sm text-gray-700">Pertenece al Régimen Simple de Tributación</label>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* MENSAJES DE ERROR */}
                        {error && (
                            <div className="p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded-r-lg flex items-center gap-3 animate-pulse">
                                <FaExclamationTriangle className="text-xl" />
                                <div>
                                    <p className="font-bold">Error al guardar:</p>
                                    <p className="text-sm">{error}</p>
                                </div>
                            </div>
                        )}

                        {/* BOTÓN FINAL */}
                        <div className="flex justify-end pt-4 border-t border-gray-100">
                            <button
                                type="submit"
                                disabled={isLoading || listasLoading}
                                className={`
                            px-8 py-3 rounded-lg shadow-lg font-bold text-white text-lg transition-all transform hover:-translate-y-0.5 flex items-center gap-2
                            ${isLoading ? 'bg-gray-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'}
                        `}
                            >
                                {isLoading ? (
                                    <> <FaSpinner className="animate-spin" /> Guardando... </>
                                ) : (
                                    <> <FaSave /> Guardar Tercero </>
                                )}
                            </button>
                        </div>

                    </form>
                </div>
            </div>
        </div>
    );
}