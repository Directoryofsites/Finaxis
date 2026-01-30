'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/app/context/AuthContext';
import { apiService } from '@/lib/apiService';
import { toast } from 'react-toastify';
import {
    FaBuilding, FaUserLock, FaSave, FaExclamationTriangle
} from 'react-icons/fa';

export default function PerfilConfigPage() {
    const { user } = useAuth();
    const [activeTab, setActiveTab] = useState('empresa');
    const [isLoading, setIsLoading] = useState(false);

    // Estado Empresa
    const [empresaData, setEmpresaData] = useState({
        razon_social: '',
        nit: '',
        direccion: '',
        telefono: '',
        email: '',
        logo_url: ''
    });

    // Estado Password
    const [passData, setPassData] = useState({
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
    });

    useEffect(() => {
        if (user?.empresaId) {
            loadEmpresa();
        }
    }, [user]);

    const loadEmpresa = async () => {
        try {
            const res = await apiService.get(`/empresas/${user.empresaId}`);
            setEmpresaData({
                razon_social: res.data.razon_social,
                nit: res.data.nit,
                direccion: res.data.direccion || '',
                telefono: res.data.telefono || '',
                email: res.data.email || '',
                logo_url: res.data.logo_url || ''
            });
        } catch (error) {
            console.error("Error loading empresa:", error);
            toast.error("Error al cargar datos de empresa");
        }
    };

    const handleSaveEmpresa = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        try {
            // Solo enviamos los campos editables
            const payload = {
                direccion: empresaData.direccion,
                telefono: empresaData.telefono,
                email: empresaData.email,
                logo_url: empresaData.logo_url
            };

            await apiService.put(`/empresas/${user.empresaId}`, payload);
            toast.success("Información de empresa actualizada");
        } catch (error) {
            console.error(error);
            toast.error("Error al guardar cambios");
        } finally {
            setIsLoading(false);
        }
    };

    const handleChangePassword = async (e) => {
        e.preventDefault();
        if (passData.newPassword !== passData.confirmPassword) {
            return toast.warning("Las nuevas contraseñas no coinciden");
        }
        if (passData.newPassword.length < 6) {
            return toast.warning("La contraseña debe tener al menos 6 caracteres");
        }

        setIsLoading(true);
        try {
            // Usamos endpoint de usuario. Si no existe uno específico de "change-password",
            // intentamos actualizar el usuario actual enviando el password.
            // NOTA: Dependiendo de la implementación del backend, esto puede variar.
            // Asumimos un endpoint standard o autoservicio.
            // Si el backend requiere currentPassword para validación, se enviaría.
            // Por ahora intentaremos PUT /usuarios/{id} con password.

            const payload = {
                password: passData.newPassword
            };

            // Verificamos si update_user en backend soporta password directo
            await apiService.put(`/usuarios/${user.id}`, payload);

            toast.success("Contraseña actualizada correctamente");
            setPassData({ currentPassword: '', newPassword: '', confirmPassword: '' });
        } catch (error) {
            console.error(error);
            toast.error(error.response?.data?.detail || "Error al cambiar contraseña");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="p-6 max-w-4xl mx-auto space-y-6">
            <header className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 mb-6">
                <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-3">
                    Configuración General
                </h1>
                <p className="text-gray-500 mt-1">Gestione los datos de su empresa y seguridad de su cuenta.</p>
            </header>

            <div className="flex flex-col md:flex-row gap-6">
                {/* Sidebar Tabs */}
                <div className="md:w-64 flex flex-col gap-2">
                    <button
                        onClick={() => setActiveTab('empresa')}
                        className={`text-left px-4 py-3 rounded-lg font-medium flex items-center gap-3 transition-colors ${activeTab === 'empresa' ? 'bg-indigo-50 text-indigo-700' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
                    >
                        <FaBuilding /> Datos Empresa
                    </button>
                    <button
                        onClick={() => setActiveTab('seguridad')}
                        className={`text-left px-4 py-3 rounded-lg font-medium flex items-center gap-3 transition-colors ${activeTab === 'seguridad' ? 'bg-indigo-50 text-indigo-700' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
                    >
                        <FaUserLock /> Seguridad
                    </button>
                </div>

                {/* Content Area */}
                <div className="flex-1 bg-white rounded-xl shadow-sm border border-gray-100 p-6 min-h-[400px]">

                    {activeTab === 'empresa' && (
                        <form onSubmit={handleSaveEmpresa} className="space-y-6 animate-fadeIn">
                            <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-4">
                                <div className="flex">
                                    <div className="flex-shrink-0">
                                        <FaExclamationTriangle className="h-5 w-5 text-blue-400" />
                                    </div>
                                    <div className="ml-3">
                                        <p className="text-sm text-blue-700">
                                            La Razón Social y el NIT son datos fiscales que no pueden ser modificados. Contacte a soporte si requiere cambios legales.
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <label className="block text-sm font-bold text-gray-700 mb-1">Razón Social</label>
                                    <input
                                        type="text"
                                        value={empresaData.razon_social}
                                        disabled
                                        className="w-full bg-gray-100 border border-gray-300 rounded-lg px-3 py-2 text-gray-500 cursor-not-allowed"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-bold text-gray-700 mb-1">NIT</label>
                                    <input
                                        type="text"
                                        value={empresaData.nit}
                                        disabled
                                        className="w-full bg-gray-100 border border-gray-300 rounded-lg px-3 py-2 text-gray-500 cursor-not-allowed"
                                    />
                                </div>

                                <div className="col-span-2 border-t pt-4 mt-2">
                                    <label className="block text-sm font-bold text-gray-700 mb-1">Dirección Física</label>
                                    <input
                                        type="text"
                                        value={empresaData.direccion}
                                        onChange={e => setEmpresaData({ ...empresaData, direccion: e.target.value })}
                                        className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                                        placeholder="Ej: Calle 123 # 45 - 67, Of 301"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-bold text-gray-700 mb-1">Teléfono / Celular</label>
                                    <input
                                        type="text"
                                        value={empresaData.telefono}
                                        onChange={e => setEmpresaData({ ...empresaData, telefono: e.target.value })}
                                        className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                                        placeholder="Ej: 300 123 4567"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-bold text-gray-700 mb-1">Correo Electrónico (Contacto)</label>
                                    <input
                                        type="email"
                                        value={empresaData.email}
                                        onChange={e => setEmpresaData({ ...empresaData, email: e.target.value })}
                                        className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                                        placeholder="contacto@suempresa.com"
                                    />
                                </div>
                            </div>

                            <div className="flex justify-end pt-4 border-t">
                                <button
                                    type="submit"
                                    disabled={isLoading}
                                    className="bg-indigo-600 text-white px-6 py-2 rounded-lg font-bold hover:bg-indigo-700 transition-colors flex items-center gap-2 shadow-sm"
                                >
                                    {isLoading ? 'Guardando...' : <><FaSave /> Guardar Cambios</>}
                                </button>
                            </div>
                        </form>
                    )}

                    {activeTab === 'seguridad' && (
                        <form onSubmit={handleChangePassword} className="space-y-6 max-w-md animate-fadeIn">
                            <h3 className="text-lg font-bold text-gray-800 border-b pb-2">Cambiar Contraseña</h3>

                            <div>
                                <label className="block text-sm font-bold text-gray-700 mb-1">Nueva Contraseña</label>
                                <input
                                    type="password"
                                    value={passData.newPassword}
                                    onChange={e => setPassData({ ...passData, newPassword: e.target.value })}
                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 outline-none"
                                    required
                                    minLength={6}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-bold text-gray-700 mb-1">Confirmar Nueva Contraseña</label>
                                <input
                                    type="password"
                                    value={passData.confirmPassword}
                                    onChange={e => setPassData({ ...passData, confirmPassword: e.target.value })}
                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 outline-none"
                                    required
                                    minLength={6}
                                />
                            </div>

                            <div className="text-sm text-gray-500 bg-gray-50 p-3 rounded">
                                Nota: Al cambiar su contraseña, es posible que deba iniciar sesión nuevamente en otros dispositivos.
                            </div>

                            <div className="flex justify-start pt-2">
                                <button
                                    type="submit"
                                    disabled={isLoading}
                                    className="bg-gray-800 text-white px-6 py-2 rounded-lg font-bold hover:bg-black transition-colors flex items-center gap-2"
                                >
                                    {isLoading ? 'Actualizando...' : 'Actualizar Contraseña'}
                                </button>
                            </div>
                        </form>
                    )}

                </div>
            </div>
        </div>
    );
}
