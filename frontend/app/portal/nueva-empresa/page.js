'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiService } from '../../../lib/apiService';
import { toast } from 'react-toastify';
import {
    BuildingOffice2Icon,
    ArrowLeftIcon,
    CheckCircleIcon
} from '@heroicons/react/24/outline';

export default function NuevaEmpresaPage() {
    const router = useRouter();
    const [loading, setLoading] = useState(false);

    const [formData, setFormData] = useState({
        razon_social: '',
        nit: '',
        fecha_inicio_operaciones: new Date().toISOString().split('T')[0],
        direccion: '',
        telefono: '',
        email: '',
        template_category: '', // RETAIL, SERVICIOS, PH
    });

    const [usuarios, setUsuarios] = useState([
        { email: '', password: '' }
    ]);

    // --- ESTADO PARA PLANTILLAS DINÁMICAS ---
    const [templates, setTemplates] = useState([]);

    // Cargar plantillas al montar
    React.useEffect(() => {
        const fetchTemplates = async () => {
            try {
                const response = await apiService.get('/empresas/templates');
                // Axios returns data in response.data
                // Ensure it is an array
                const tpls = Array.isArray(response.data) ? response.data : [];
                setTemplates(tpls);
            } catch (err) {
                console.error("Error cargando plantillas:", err);
                setTemplates([]);
            }
        };
        fetchTemplates();
    }, []);

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleUserChange = (index, e) => {
        const newUsers = [...usuarios];
        newUsers[index][e.target.name] = e.target.value;
        setUsuarios(newUsers);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);

        try {
            // Construir payload
            const payload = {
                ...formData,
                usuarios: usuarios.filter(u => u.email && u.password) // Limpiar vacíos porsiaca
            };

            // Limpiar template si está vacío
            if (!payload.template_category) delete payload.template_category;

            const response = await apiService.post('/empresas', payload);
            toast.success("Empresa creada exitosamente.");
            router.push('/portal'); // Volver al lobby
        } catch (error) {
            console.error("Error creando empresa:", error);
            const msg = error.response?.data?.detail || "Error al crear la empresa.";
            toast.error(msg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 py-10 px-4 sm:px-6 lg:px-8">
            <div className="max-w-3xl mx-auto">

                {/* Header de Navegación */}
                <div className="mb-8 flex items-center justify-between">
                    <button
                        onClick={() => router.back()}
                        className="flex items-center text-slate-500 hover:text-slate-800 transition-colors"
                    >
                        <ArrowLeftIcon className="h-5 w-5 mr-2" />
                        Volver al Portal
                    </button>
                    <h1 className="text-2xl font-bold text-slate-900">Nueva Empresa</h1>
                </div>

                <form onSubmit={handleSubmit} className="bg-white shadow-xl rounded-2xl overflow-hidden border border-slate-100">

                    {/* Sección: Datos Básicos */}
                    <div className="p-8 border-b border-slate-100">
                        <h3 className="text-lg font-semibold text-slate-800 mb-4 flex items-center">
                            <BuildingOffice2Icon className="h-5 w-5 mr-2 text-blue-600" />
                            Información General
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="col-span-2">
                                <label className="block text-sm font-medium text-slate-700">Razón Social</label>
                                <input
                                    type="text" required name="razon_social"
                                    value={formData.razon_social} onChange={handleChange}
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border"
                                    placeholder="Ej: Mi Negocio S.A.S"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700">NIT</label>
                                <input
                                    type="text" required name="nit"
                                    value={formData.nit} onChange={handleChange}
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border"
                                    placeholder="Ej: 900.123.456-7"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700">Inicio Operaciones</label>
                                <input
                                    type="date" required name="fecha_inicio_operaciones"
                                    value={formData.fecha_inicio_operaciones} onChange={handleChange}
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Sección: Plantilla / Industria (DINÁMICA) */}
                    <div className="p-8 bg-blue-50/50 border-b border-slate-100">
                        <h3 className="text-lg font-semibold text-slate-800 mb-2">Configuración Inicial (Plantilla)</h3>
                        <p className="text-sm text-slate-500 mb-6">
                            Seleccione una plantilla para clonar automáticamente el Plan Único de Cuentas (PUC) y configuraciones base.
                        </p>

                        {templates.length === 0 ? (
                            <div className="text-center py-6 bg-white rounded-lg border border-dashed border-gray-300 text-gray-500">
                                No hay plantillas disponibles.
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                {templates.map((tpl) => (
                                    <div
                                        key={tpl.id}
                                        onClick={() => setFormData({
                                            ...formData,
                                            template_category: tpl.template_category,
                                            template_id: tpl.id // Store explicit ID
                                        })}
                                        className={`cursor-pointer border rounded-lg p-4 transition-all relative ${formData.template_id === tpl.id
                                            ? 'bg-white border-blue-500 shadow-md ring-2 ring-blue-500 ring-opacity-20'
                                            : 'bg-white border-slate-200 hover:border-blue-300'
                                            }`}
                                    >
                                        {formData.template_id === tpl.id && ( // Check by ID
                                            <CheckCircleIcon className="absolute top-2 right-2 h-5 w-5 text-blue-600" />
                                        )}
                                        <div className="font-semibold text-slate-900">{tpl.razon_social}</div>
                                        <div className="text-xs text-slate-500 mt-1">
                                            {tpl.owner_id ? 'Plantilla Privada (Tuya)' : 'Plantilla del Sistema'}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Sección: Usuario Administrador */}
                    <div className="p-8">
                        <h3 className="text-lg font-semibold text-slate-800 mb-4">Administrador Principal</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <label className="block text-sm font-medium text-slate-700">Email Admin</label>
                                <input
                                    type="email" required name="email"
                                    value={usuarios[0].email} onChange={(e) => handleUserChange(0, e)}
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700">Contraseña</label>
                                <input
                                    type="password" required name="password"
                                    value={usuarios[0].password} onChange={(e) => handleUserChange(0, e)}
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Footer Actions */}
                    <div className="px-8 py-5 bg-slate-50 flex justify-end items-center gap-4 border-t border-slate-200">
                        <button
                            type="button"
                            onClick={() => router.back()}
                            className="text-slate-600 hover:text-slate-900 font-medium text-sm"
                        >
                            Cancelar
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="inline-flex items-center px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg shadow-sm transition-all font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? 'Creando...' : 'Crear Empresa'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
