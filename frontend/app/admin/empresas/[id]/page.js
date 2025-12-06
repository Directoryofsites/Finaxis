// frontend/app/admin/empresas/[id]/page.js
'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import BotonRegresar from '../../../components/BotonRegresar';
import { useAuth } from '../../../context/AuthContext';
import { apiService } from '../../../../lib/apiService';
import { FaBuilding, FaSave, FaUsers, FaExclamationTriangle } from 'react-icons/fa';

export default function DetalleEmpresaPage() {
    const params = useParams();
    const { id } = params;
    const { user } = useAuth();

    // Estado para el formulario de la empresa
    const [formData, setFormData] = useState({
        razon_social: '',
        nit: '',
        direccion: '',
        telefono: '',
        email: '',
        logo_url: '', // Para el logo en el PDF
        limite_registros: 0
    });

    const [usuarios, setUsuarios] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState(null);
    const [errorUsuarios, setErrorUsuarios] = useState(null); // Error específico para usuarios (403)
    const [success, setSuccess] = useState('');

    useEffect(() => {
        if (id && user) {
            const fetchData = async () => {
                setIsLoading(true);
                try {
                    // 1. Cargar Datos de la Empresa
                    const resEmpresa = await apiService.get(`/empresas/${id}`);
                    const emp = resEmpresa.data;
                    
                    // Pre-llenar formulario (usamos || '' para evitar warnings de React)
                    setFormData({
                        razon_social: emp.razon_social || '',
                        nit: emp.nit || '',
                        direccion: emp.direccion || '',
                        telefono: emp.telefono || '',
                        email: emp.email || '',
                        logo_url: emp.logo_url || '',
                        limite_registros: emp.limite_registros || 0
                    });

                    // 2. Intentar Cargar Usuarios (Puede fallar por permisos 403)
                    try {
                        const resUsuarios = await apiService.get(`/empresas/${id}/usuarios`);
                        setUsuarios(resUsuarios.data);
                    } catch (errUsers) {
                        console.warn("No se pudieron cargar usuarios:", errUsers);
                        setErrorUsuarios("No tienes permisos para ver o gestionar los usuarios de esta empresa.");
                    }

                } catch (err) {
                    setError(err.response?.data?.detail || 'Error cargando la empresa.');
                } finally {
                    setIsLoading(false);
                }
            };
            fetchData();
        }
    }, [id, user]);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleUpdateEmpresa = async (e) => {
        e.preventDefault();
        setIsSaving(true);
        setError(null);
        setSuccess('');

        try {
            // Enviamos PUT para actualizar
            await apiService.put(`/empresas/${id}`, formData);
            setSuccess('¡Datos de la empresa actualizados correctamente! El PDF ahora tomará estos cambios.');
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al guardar los cambios.');
        } finally {
            setIsSaving(false);
        }
    };

    if (isLoading) return <div className="p-10 text-center"><span className="loading loading-spinner text-indigo-600"></span></div>;

    return (
        <div className="container mx-auto p-6 max-w-5xl font-sans pb-20">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                    <FaBuilding className="text-indigo-600"/> Gestión de Empresa
                </h1>
                <BotonRegresar url="/admin/empresas" />
            </div>

            {/* 1. FORMULARIO DE DATOS (SOLUCIÓN A TU PROBLEMA DE DIRECCIÓN/TELÉFONO) */}
            <div className="bg-white p-8 rounded-xl shadow-lg border border-gray-100 mb-8">
                <h2 className="text-lg font-bold text-gray-700 mb-4 border-b pb-2">Datos Generales (Para Impresión)</h2>
                
                <form onSubmit={handleUpdateEmpresa}>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                        <div>
                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Razón Social</label>
                            <input type="text" name="razon_social" value={formData.razon_social} onChange={handleInputChange} className="input input-bordered w-full" required />
                        </div>
                        <div>
                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">NIT / Identificación</label>
                            <input type="text" name="nit" value={formData.nit} onChange={handleInputChange} className="input input-bordered w-full" required />
                        </div>
                        <div>
                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Dirección</label>
                            <input type="text" name="direccion" value={formData.direccion} onChange={handleInputChange} className="input input-bordered w-full" placeholder="Ej: Calle 123 # 45-67" />
                        </div>
                        <div>
                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Teléfono</label>
                            <input type="text" name="telefono" value={formData.telefono} onChange={handleInputChange} className="input input-bordered w-full" placeholder="Ej: 300 123 4567" />
                        </div>
                        <div>
                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Email de Contacto</label>
                            <input type="email" name="email" value={formData.email} onChange={handleInputChange} className="input input-bordered w-full" />
                        </div>
                        <div>
                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">URL del Logo (Opcional)</label>
                            <input type="text" name="logo_url" value={formData.logo_url} onChange={handleInputChange} className="input input-bordered w-full" placeholder="https://mi-sitio.com/logo.png" />
                        </div>
                    </div>

                    {/* Mensajes */}
                    {success && <div className="alert alert-success mb-4 text-sm">{success}</div>}
                    {error && <div className="alert alert-error mb-4 text-sm">{error}</div>}

                    <div className="flex justify-end">
                        <button type="submit" disabled={isSaving} className="btn btn-primary bg-indigo-600 hover:bg-indigo-700 text-white gap-2">
                            {isSaving ? <span className="loading loading-spinner loading-xs"></span> : <FaSave />} Guardar Datos
                        </button>
                    </div>
                </form>
            </div>

            {/* 2. GESTIÓN DE USUARIOS (CON MANEJO DE ERROR 403) */}
            <div className="bg-white p-8 rounded-xl shadow-lg border border-gray-100">
                <h3 className="text-lg font-bold text-gray-700 mb-4 border-b pb-2 flex items-center gap-2">
                    <FaUsers /> Usuarios Asociados
                </h3>

                {errorUsuarios ? (
                    <div className="alert alert-warning flex items-start gap-2">
                        <FaExclamationTriangle className="mt-1" />
                        <span>{errorUsuarios} (Aún puedes editar los datos de la empresa arriba)</span>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="table w-full">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th>Email</th>
                                    <th>Rol</th>
                                </tr>
                            </thead>
                            <tbody>
                                {usuarios.map(u => (
                                    <tr key={u.id}>
                                        <td>{u.email}</td>
                                        <td>{u.rol}</td>
                                    </tr>
                                ))}
                                {usuarios.length === 0 && <tr><td colSpan="3" className="text-center text-gray-500">No hay usuarios visibles.</td></tr>}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}