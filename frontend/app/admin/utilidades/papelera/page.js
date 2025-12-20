'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { apiService } from '../../../../lib/apiService';

import { FaBook, FaPrint, FaTimes } from 'react-icons/fa';

export default function PapeleraPage() {
    const { user, authLoading } = useAuth();
    const [documentosEliminados, setDocumentosEliminados] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isRestoring, setIsRestoring] = useState(null);
    const [mensaje, setMensaje] = useState({ text: '', type: 'info' });

    const fetchDocumentosEliminados = useCallback(async () => {
        if (!user) return;
        setIsLoading(true);
        setMensaje({ text: '', type: 'info' });
        try {
            const response = await apiService.get('/papelera/');
            setDocumentosEliminados(response.data);
        } catch (err) {
            // --- MEJORA: Manejo de errores de permisos desde el backend ---
            if (err.response && err.response.status === 403) {
                setMensaje({ text: 'No tienes los permisos necesarios para acceder a la papelera.', type: 'error' });
            } else {
                const errorMsg = err.response?.data?.detail || 'Error al cargar los documentos de la papelera.';
                setMensaje({ text: errorMsg, type: 'error' });
            }
        } finally {
            setIsLoading(false);
        }
    }, [user]);

    useEffect(() => {
        // --- LÓGICA SIMPLIFICADA: Se quita la comprobación de rol obsoleta ---
        if (!authLoading && user) {
            fetchDocumentosEliminados();
        }
    }, [user, authLoading, fetchDocumentosEliminados]);

    const handleRestaurar = async (docId) => {
        if (!window.confirm("¿Estás seguro de que deseas restaurar este documento?")) {
            return;
        }
        setIsRestoring(docId);
        setMensaje({ text: '', type: 'info' });
        try {
            const response = await apiService.post(`/papelera/${docId}/restaurar`);
            setMensaje({ text: 'Documento restaurado con éxito. Actualizando lista...', type: 'success' });
            // Volvemos a cargar los datos para reflejar el cambio
            fetchDocumentosEliminados();
        } catch (err) {
            if (err.response && err.response.status === 403) {
                setMensaje({ text: 'Error: No tienes permisos para restaurar documentos.', type: 'error' });
            } else {
                const errorMsg = err.response?.data?.detail || 'Ocurrió un error al restaurar.';
                setMensaje({ text: errorMsg, type: 'error' });
            }
        } finally {
            setIsRestoring(null);
        }
    };

    if (authLoading) return <p className="text-center p-8">Verificando autenticación...</p>;

    // --- ELIMINADO: Antigua verificación de permisos. Ahora se maneja con el estado 'mensaje' ---

    // Si la carga inicial resultó en un error (incluyendo permisos), lo mostramos aquí.
    if (!isLoading && mensaje.type === 'error') {
        return (
            <div className="container mx-auto p-8 text-center">
                <div className="flex justify-between items-center mb-8">
                    <h1 className="text-3xl font-bold text-gray-800">Papelera de Reciclaje</h1>
                </div>
                <p className="text-center text-red-500 p-8 bg-red-50 rounded-lg">{mensaje.text}</p>
            </div>
        );
    }

    if (isLoading) return <p className="text-center p-8">Cargando documentos...</p>;

    return (
        <div className="container mx-auto p-8">
            <div className="flex justify-between items-center mb-8">
                <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-2">
                    Papelera de Reciclaje
                    <button
                        onClick={() => window.open('/manual/capitulo_12_papelera.html', '_blank')}
                        className="flex items-center gap-2 px-2 py-1 bg-white border border-indigo-200 text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors font-medium shadow-sm text-sm"
                        title="Ver Manual de Usuario"
                    >
                        <FaBook /> <span className="hidden md:inline">Manual</span>
                    </button>
                </h1>
            </div>

            {mensaje.text && mensaje.type === 'success' && (
                <div className="p-4 mb-6 rounded-md bg-green-100 text-green-700">
                    {mensaje.text}
                </div>
            )}
            {mensaje.text && mensaje.type === 'error' && !isLoading && (
                <div className="p-4 mb-6 rounded-md bg-red-100 text-red-700">
                    {mensaje.text}
                </div>
            )}

            <div className="bg-white p-6 rounded-lg shadow-md">
                <div className="overflow-x-auto">
                    <table className="min-w-full bg-white">
                        <thead className="bg-gray-200 text-gray-600 uppercase text-sm leading-normal">
                            <tr>
                                <th className="py-3 px-6 text-left">ID Original</th>
                                <th className="py-3 px-6 text-left">Tipo Documento</th>
                                <th className="py-3 px-6 text-left">Valor Documento</th>
                                <th className="py-3 px-6 text-left">Número</th>
                                <th className="py-3 px-6 text-left">Fecha Original</th>
                                <th className="py-3 px-6 text-left">Fecha Eliminación</th>
                                <th className="py-3 px-6 text-left">Eliminado por</th>
                                <th className="py-3 px-6 text-center">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="text-gray-600 text-sm font-light">
                            {documentosEliminados.length > 0 ? (
                                documentosEliminados.map(doc => (
                                    <tr key={doc.id} className="border-b border-gray-200 hover:bg-gray-100">
                                        <td className="py-3 px-6 text-left">{doc.id_original}</td>
                                        <td className="py-3 px-6 text-left font-medium">{doc.tipo_documento_nombre}</td>
                                        <td className="py-3 px-6 text-right font-mono">
                                            {new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(doc.valor_documento)}
                                        </td>
                                        <td className="py-3 px-6 text-left">{doc.numero}</td>
                                        <td className="py-3 px-6 text-left">{new Date(doc.fecha + 'T00:00:00').toLocaleDateString('es-CO')}</td>
                                        <td className="py-3 px-6 text-left">{new Date(doc.fecha_eliminacion).toLocaleString('es-CO')}</td>
                                        <td className="py-3 px-6 text-left">{doc.usuario_eliminacion || 'N/A'}</td>
                                        <td className="py-3 px-6 text-center">
                                            <button
                                                onClick={() => handleRestaurar(doc.id)}
                                                className="bg-blue-600 text-white px-3 py-1 rounded text-xs hover:bg-blue-800 disabled:bg-gray-400"
                                                disabled={isRestoring === doc.id}
                                            >
                                                {isRestoring === doc.id ? 'Restaurando...' : 'Restaurar'}
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan="8" className="text-center py-6 text-gray-500">
                                        La papelera de reciclaje está vacía.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}