'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';

import { useAuth } from '../../context/AuthContext';
import { apiService } from '../../../lib/apiService';
import { FaBook } from 'react-icons/fa';

export default function GestionEmpresasPage() {
    const { user } = useAuth();
    const [empresas, setEmpresas] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchEmpresas = async () => {
            setIsLoading(true);
            setError(null);

            try {
                const response = await apiService.get('/empresas');
                setEmpresas(response.data);
            } catch (err) {
                setError(err.response?.data?.detail || 'No se pudo obtener la lista de empresas.');
            } finally {
                setIsLoading(false);
            }
        };

        if (user) {
            fetchEmpresas();
        } else {
            setIsLoading(false);
        }
    }, [user]);

    return (
        <div className="container mx-auto p-4 max-w-4xl">
            <div className="flex justify-between items-center mb-6">
                <div className="flex items-center gap-3">
                    <h1 className="text-2xl font-bold text-gray-800">Gestión de Empresas Clientes</h1>
                    <button
                        onClick={() => window.open('/manual/capitulo_5_empresas.html', '_blank')}
                        className="flex items-center gap-2 px-2 py-1 bg-white border border-indigo-200 text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors font-medium shadow-sm"
                        title="Ver Manual de Usuario"
                    >
                        <FaBook /> <span className="hidden md:inline">Manual</span>
                    </button>
                </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
                {/* --- INICIO DEL CAMBIO: SE ELIMINA EL BOTÓN DE CREAR --- */}
                {/* El botón "+ Crear Nueva Empresa" ha sido removido de esta sección. */}
                {/* --- FIN DEL CAMBIO --- */}

                {isLoading && <p className="text-center py-4">Cargando empresas...</p>}
                {error && <p className="text-center text-red-500 bg-red-100 p-3 rounded-md">{error}</p>}

                {!isLoading && !error && (
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Razón Social</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {empresas.length > 0 ? (
                                    empresas.map((empresa) => (
                                        <tr key={empresa.id}>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{empresa.id}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{empresa.razon_social}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                                <Link href={`/admin/empresas/${empresa.id}`}>
                                                    <button className="text-indigo-600 hover:text-indigo-900">Gestionar</button>
                                                </Link>
                                            </td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan="3" className="px-6 py-4 text-center text-gray-500">No hay empresas creadas.</td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}