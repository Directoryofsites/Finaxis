'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import BotonRegresar from '../../components/BotonRegresar';
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
                <h1 className="text-2xl font-bold text-gray-800">Gestión de Empresas Clientes</h1>
                <div className="flex gap-2">
                    <button
                        onClick={() => window.open('/manual?file=capitulo_5_empresas.md', '_blank')}
                        className="btn btn-ghost text-indigo-600 hover:bg-indigo-50 gap-2 flex items-center"
                        title="Ver Manual de Usuario"
                    >
                        <FaBook className="text-lg" /> <span className="hidden md:inline font-bold">Manual</span>
                    </button>
                    <BotonRegresar />
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