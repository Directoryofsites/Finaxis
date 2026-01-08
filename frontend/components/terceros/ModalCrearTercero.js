import React, { useState, useEffect } from 'react';
import {
    FaUserPlus,
    FaIdCard,
    FaBuilding,
    FaMapMarkerAlt,
    FaCity,
    FaPhone,
    FaEnvelope,
    FaSave,
    FaSpinner,
    FaExclamationTriangle,
    FaTimes
} from 'react-icons/fa';
import { apiService } from '../../lib/apiService';
import { useAuth } from '../../app/context/AuthContext';

// Estilos reusables
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-3 py-2 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none";

export default function ModalCrearTercero({ isOpen, onClose, onSuccess }) {
    const { user } = useAuth(); // Necesitamos user para el empresaId

    // Estado del formulario
    const [formData, setFormData] = useState({
        nit: '',
        dv: '',
        razon_social: '',
        nombre_comercial: '',
        direccion: '',
        ciudad: '',
        telefono: '',
        email: '',
        es_cliente: true, // Por defecto asumimos cliente para agilizar
        es_proveedor: false,
        es_empleado: false,
        responsabilidad_fiscal: 'R-99-PN', // Valor por defecto común
        // Omitimos validaciones complejas en el modal rápido para velocidad
        lista_precio_id: ''
    });

    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    // Resetear form al abrir
    useEffect(() => {
        if (isOpen) {
            setFormData({
                nit: '',
                dv: '',
                razon_social: '',
                nombre_comercial: '',
                direccion: '',
                ciudad: '',
                telefono: '',
                email: '',
                es_cliente: true,
                es_proveedor: false,
                es_empleado: false,
                responsabilidad_fiscal: 'R-99-PN',
                lista_precio_id: ''
            });
            setError(null);
        }
    }, [isOpen]);

    if (!isOpen) return null;

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!user?.empresaId) {
            setError("No se identificó la empresa. Recargue la página.");
            return;
        }

        setIsLoading(true);
        setError(null);

        const payload = {
            ...formData,
            empresa_id: user.empresaId,
            // Convertir vacíos a null para campos opcionales
            nombre_comercial: formData.nombre_comercial || null,
            direccion: formData.direccion || null,
            ciudad: formData.ciudad || null,
            telefono: formData.telefono || null,
            email: formData.email || null,
            lista_precio_id: formData.lista_precio_id ? parseInt(formData.lista_precio_id) : null,
            responsabilidad_fiscal: formData.responsabilidad_fiscal || 'R-99-PN'
        };

        try {
            const response = await apiService.post('/terceros/', payload);
            if (onSuccess) {
                onSuccess(response.data);
            }
            onClose(); // Cerrar modal
        } catch (err) {
            console.error("Error creando tercero:", err);
            const detail = err.response?.data?.detail;
            setError(typeof detail === 'string' ? detail : "Error al guardar el tercero. Verifique los campos obligatorios.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm p-4">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto animate-fadeIn">

                {/* HEADER */}
                <div className="flex justify-between items-center p-4 border-b border-gray-100 sticky top-0 bg-white z-10">
                    <div className="flex items-center gap-2">
                        <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                            <FaUserPlus />
                        </div>
                        <h2 className="text-xl font-bold text-gray-800">Crear Tercero (Rápido)</h2>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100 transition-colors"
                    >
                        <FaTimes className="text-xl" />
                    </button>
                </div>

                {/* BODY */}
                <form onSubmit={handleSubmit} className="p-6 space-y-6">

                    {/* Sección 1: Identificación */}
                    <div className="grid grid-cols-12 gap-4">
                        <div className="col-span-8 md:col-span-5">
                            <label className={labelClass}>NIT / Cédula <span className="text-red-500">*</span></label>
                            <div className="relative">
                                <FaIdCard className="absolute left-3 top-2.5 text-gray-400" />
                                <input
                                    type="text"
                                    name="nit"
                                    value={formData.nit}
                                    onChange={handleChange}
                                    className={`${inputClass} pl-9`}
                                    required
                                    autoFocus
                                    placeholder="Número de documento"
                                />
                            </div>
                        </div>
                        <div className="col-span-4 md:col-span-2">
                            <label className={labelClass}>DV</label>
                            <input
                                type="text"
                                name="dv"
                                value={formData.dv}
                                onChange={handleChange}
                                className={`${inputClass} text-center`}
                                maxLength={1}
                                placeholder="-"
                            />
                        </div>
                        <div className="col-span-12 md:col-span-5">
                            <label className={labelClass}>Razón Social / Nombre <span className="text-red-500">*</span></label>
                            <div className="relative">
                                <FaBuilding className="absolute left-3 top-2.5 text-gray-400" />
                                <input
                                    type="text"
                                    name="razon_social"
                                    value={formData.razon_social}
                                    onChange={handleChange}
                                    className={`${inputClass} pl-9`}
                                    required
                                    placeholder="Nombre completo o Empresa"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Sección 2: Contacto Básico */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className={labelClass}>Teléfono</label>
                            <div className="relative">
                                <FaPhone className="absolute left-3 top-2.5 text-gray-400" />
                                <input
                                    type="text"
                                    name="telefono"
                                    value={formData.telefono}
                                    onChange={handleChange}
                                    className={`${inputClass} pl-9`}
                                    placeholder="Opcional"
                                />
                            </div>
                        </div>
                        <div>
                            <label className={labelClass}>Email</label>
                            <div className="relative">
                                <FaEnvelope className="absolute left-3 top-2.5 text-gray-400" />
                                <input
                                    type="email"
                                    name="email"
                                    value={formData.email}
                                    onChange={handleChange}
                                    className={`${inputClass} pl-9`}
                                    placeholder="contacto@ejemplo.com"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Sección 3: Ubicación (Simplificada) */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className={labelClass}>Dirección</label>
                            <div className="relative">
                                <FaMapMarkerAlt className="absolute left-3 top-2.5 text-gray-400" />
                                <input
                                    type="text"
                                    name="direccion"
                                    value={formData.direccion}
                                    onChange={handleChange}
                                    className={`${inputClass} pl-9`}
                                    placeholder="Calle 123 # 45-67"
                                />
                            </div>
                        </div>
                        <div>
                            <label className={labelClass}>Ciudad</label>
                            <div className="relative">
                                <FaCity className="absolute left-3 top-2.5 text-gray-400" />
                                <input
                                    type="text"
                                    name="ciudad"
                                    value={formData.ciudad}
                                    onChange={handleChange}
                                    className={`${inputClass} pl-9`}
                                    placeholder="Bogotá, Medellín..."
                                />
                            </div>
                        </div>
                    </div>

                    {/* Sección 4: Roles */}
                    <div className="border-t border-gray-100 pt-4">
                        <label className={labelClass}>Tipo de Tercero</label>
                        <div className="flex gap-4 mt-2">
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input type="checkbox" name="es_cliente" checked={formData.es_cliente} onChange={handleChange} className="rounded text-indigo-600 focus:ring-indigo-500" />
                                <span className="text-sm font-medium">Es Cliente</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input type="checkbox" name="es_proveedor" checked={formData.es_proveedor} onChange={handleChange} className="rounded text-indigo-600 focus:ring-indigo-500" />
                                <span className="text-sm font-medium">Es Proveedor</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input type="checkbox" name="es_empleado" checked={formData.es_empleado} onChange={handleChange} className="rounded text-indigo-600 focus:ring-indigo-500" />
                                <span className="text-sm font-medium">Es Empleado</span>
                            </label>
                        </div>
                    </div>

                    {/* ERRORES */}
                    {error && (
                        <div className="p-3 bg-red-50 border border-red-200 rounded text-red-600 text-sm flex items-center gap-2">
                            <FaExclamationTriangle /> {error}
                        </div>
                    )}

                    {/* FOOTER ACCIONES */}
                    <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium transition-colors"
                        >
                            Cancelar
                        </button>
                        <button
                            type="submit"
                            disabled={isLoading}
                            className={`px-4 py-2 text-white rounded-lg font-bold flex items-center gap-2 shadow-lg transition-all transform hover:-translate-y-0.5 ${isLoading ? 'bg-indigo-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'}`}
                        >
                            {isLoading ? <FaSpinner className="animate-spin" /> : <FaSave />}
                            Guardar Tercero
                        </button>
                    </div>

                </form>
            </div>
        </div>
    );
}
