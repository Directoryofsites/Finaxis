'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../context/AuthContext';
import { apiService } from '../../lib/apiService';
import { toast } from 'react-toastify';
import {
    BuildingOffice2Icon,
    ArrowRightOnRectangleIcon,
    PlusIcon,
    UserCircleIcon,
    ChartBarIcon
} from '@heroicons/react/24/outline';

export default function PortalDashboard() {
    const { user, switchCompany, logout } = useAuth();
    const router = useRouter();
    const [empresas, setEmpresas] = useState([]);
    const [loading, setLoading] = useState(true);
    const [switching, setSwitching] = useState(false);

    useEffect(() => {
        // Cargar empresas asignadas al usuario
        const fetchEmpresas = async () => {
            try {
                // Asumimos que hay un endpoint que devuelve las empresas permitidas
                // Puede ser /empresas (si es soporte) o filtrado en backend
                // O mejor: /usuarios/me/empresas (si existiera)
                // Por ahora usamos /empresas confiando en que el backend filtra para el usuario logueado
                // Si el usuario es 'contador', debería ver su holding y sus hijas.
                const response = await apiService.get('/empresas');
                setEmpresas(response.data);
            } catch (error) {
                console.error("Error cargando empresas:", error);
                toast.error("No se pudieron cargar las empresas.");
            } finally {
                setLoading(false);
            }
        };

        if (user) fetchEmpresas();
    }, [user]);

    const handleSwitch = async (empresaId) => {
        setSwitching(true);
        const success = await switchCompany(empresaId);
        if (success) {
            toast.success("Contexto cambiado exitosamente.");
            // Redirigir al dashboard principal o recargar
            router.push('/');
        } else {
            toast.error("Error al cambiar de empresa.");
        }
        setSwitching(false);
    };

    const handleCreateCompany = () => {
        // Abrir modal o redirigir a form de creación
        router.push('/portal/nueva-empresa');
    };

    const canCreateCompany = user?.roles?.some(r => ['contador', 'soporte'].includes(r.nombre?.toLowerCase()));

    if (loading) return <div className="p-10 text-center">Cargando portal...</div>;

    return (
        <div className="min-h-screen bg-slate-50">
            {/* Header Portal */}
            <header className="bg-slate-900 text-white shadow-lg">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex justify-between items-center">
                    <div className="flex items-center gap-3">
                        <BuildingOffice2Icon className="h-8 w-8 text-blue-400" />
                        <h1 className="text-xl font-bold tracking-tight">Torre de Control <span className="text-blue-400">Contable</span></h1>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="text-right hidden sm:block">
                            <p className="text-sm font-medium">{user?.nombre_completo || 'Usuario'}</p>
                            <p className="text-xs text-slate-400">{user?.roles?.map(r => r.nombre).join(', ')}</p>
                        </div>
                        <button onClick={logout} className="p-2 hover:bg-slate-800 rounded-full text-slate-400 hover:text-white transition-colors">
                            <ArrowRightOnRectangleIcon className="h-6 w-6" />
                        </button>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">

                {/* Welcome Section */}
                <div className="mb-10">
                    <h2 className="text-3xl font-bold text-slate-900">Bienvenido, {user?.empresaOriginal || user?.empresaNombre || 'Su Empresa'}.</h2>
                    <p className="mt-2 text-slate-600 text-lg">Seleccione una empresa para comenzar a operar o administre su cartera.</p>
                </div>

                {/* Action Bar */}
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-xl font-semibold text-slate-800 flex items-center gap-2">
                        <BuildingOffice2Icon className="h-5 w-5" />
                        Empresas Gestionadas
                    </h3>
                    {canCreateCompany && (
                        <button
                            onClick={handleCreateCompany}
                            className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg shadow-sm transition-all text-sm font-medium"
                        >
                            <PlusIcon className="h-5 w-5 mr-1" />
                            Nueva Empresa
                        </button>
                    )}
                </div>

                {/* Company Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {empresas.map((emp) => (
                        <div
                            key={emp.id}
                            className={`bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-all cursor-pointer relative group ${user?.empresaId === emp.id ? 'ring-2 ring-blue-500 bg-blue-50/10' : ''
                                }`}
                            onClick={() => handleSwitch(emp.id)}
                        >
                            {user?.empresaId === emp.id && (
                                <span className="absolute top-4 right-4 bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded-full font-medium">
                                    Activa
                                </span>
                            )}

                            <div className="flex items-start gap-4">
                                <div className="h-12 w-12 rounded-lg bg-slate-100 flex items-center justify-center text-xl font-bold text-slate-600 shrink-0">
                                    {emp.razon_social.charAt(0)}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <h4 className="text-lg font-semibold text-slate-900 truncate">{emp.razon_social}</h4>
                                    <p className="text-sm text-slate-500 truncate">NIT: {emp.nit}</p>

                                    {/* Stats Miniatures */}
                                    <div className="mt-4 flex flex-col gap-2">
                                        <div className="flex justify-between text-xs text-slate-500 mb-1">
                                            <span className="flex items-center gap-1"><ChartBarIcon className="h-3 w-3" /> Consumo Mes:</span>
                                            {emp.limite_registros_mensual > 0 ? (
                                                <span className={`font-bold ${emp.consumo_actual >= emp.limite_registros_mensual ? 'text-red-600' : 'text-slate-700'}`}>
                                                    {emp.consumo_actual || 0} / {emp.limite_registros_mensual}
                                                </span>
                                            ) : (
                                                <span className="font-bold text-slate-700">
                                                    {emp.consumo_actual || 0}
                                                </span>
                                            )}
                                        </div>
                                        {/* Progress Bar (Only if limit exists) */}
                                        {emp.limite_registros_mensual > 0 && (
                                            <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                                                <div
                                                    className={`h-full rounded-full transition-all duration-500 ${(emp.consumo_actual / emp.limite_registros_mensual) > 0.9 ? 'bg-red-500' :
                                                        (emp.consumo_actual / emp.limite_registros_mensual) > 0.7 ? 'bg-yellow-500' : 'bg-green-500'
                                                        }`}
                                                    style={{ width: `${Math.min(100, ((emp.consumo_actual || 0) / emp.limite_registros_mensual) * 100)}%` }}
                                                />
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>

                            {/* Hover Effect Action */}
                            <div className="absolute bottom-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
                                <span className="text-blue-600 text-sm font-medium flex items-center">
                                    Ingresar &rarr;
                                </span>
                            </div>
                        </div>
                    ))}

                    {/* Empty State */}
                    {empresas.length === 0 && (
                        <div className="col-span-full py-12 text-center border-2 border-dashed border-slate-300 rounded-xl">
                            <BuildingOffice2Icon className="h-12 w-12 mx-auto text-slate-400 mb-3" />
                            <p className="text-slate-500">No tiene empresas asignadas.</p>
                            {canCreateCompany && (
                                <button onClick={handleCreateCompany} className="mt-2 text-blue-600 hover:underline">
                                    Crear su primera empresa
                                </button>
                            )}
                        </div>
                    )}
                </div>
            </main>

            {/* Loading Overlay */}
            {switching && (
                <div className="fixed inset-0 bg-white/80 z-50 flex items-center justify-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                </div>
            )}
        </div>
    );
}
