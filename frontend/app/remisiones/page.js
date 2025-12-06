'use client';
import { useState, useEffect } from 'react';
import { apiService } from '../../lib/apiService';
import Link from 'next/link';

export default function RemisionesListPage() {
    const [remisiones, setRemisiones] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchRemisiones();
    }, []);

    const fetchRemisiones = async () => {
        try {
            const data = await apiService.get('/remisiones/');
            if (data && data.remisiones) {
                setRemisiones(data.remisiones);
            }
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-6">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold">Remisiones</h1>
                <Link href="/remisiones/crear" className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
                    Nueva Remisión
                </Link>
            </div>

            <div className="bg-white shadow rounded-lg overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Número</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cliente</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Bodega</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {loading ? (
                            <tr><td colSpan="6" className="text-center py-4">Cargando...</td></tr>
                        ) : remisiones.length === 0 ? (
                            <tr><td colSpan="6" className="text-center py-4">No hay remisiones registradas.</td></tr>
                        ) : (
                            remisiones.map((rem) => (
                                <tr key={rem.id}>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                        <Link href={`/remisiones/detalle/${rem.id}`} className="text-blue-600 hover:underline">
                                            #{rem.numero}
                                        </Link>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{rem.fecha}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{rem.tercero_nombre}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{rem.bodega_nombre}</td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                      ${rem.estado === 'APROBADA' ? 'bg-green-100 text-green-800' :
                                                rem.estado === 'BORRADOR' ? 'bg-gray-100 text-gray-800' :
                                                    rem.estado === 'ANULADA' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'}`}>
                                            {rem.estado}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                        <Link href={`/remisiones/detalle/${rem.id}`} className="text-indigo-600 hover:text-indigo-900">Ver</Link>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
