// frontend/app/admin/tipos-documento/page.js
'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../context/AuthContext';
import { apiService } from '../../../lib/apiService';


// --- Iconos Estándar v2.0 ---
import { FaFileInvoice, FaPlus, FaEdit, FaTrashAlt, FaPencilRuler, FaCheckCircle, FaExclamationCircle, FaBook, FaEraser } from 'react-icons/fa';

export default function TiposDocumentoPage() {
    const { user, loading: authLoading } = useAuth();
    const router = useRouter();

    const [tiposDoc, setTiposDoc] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (authLoading) return;
        if (!user) {
            router.push('/login');
            return;
        }
        fetchTiposDocumento();
    }, [user, authLoading, router]);

    const fetchTiposDocumento = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await apiService.get('/tipos-documento/');
            setTiposDoc(response.data);
        } catch (err) {
            setError(err.response?.data?.detail || 'No se pudo cargar los tipos de documento.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm('¿Está seguro de que desea eliminar este tipo de documento?')) return;
        setError(null);
        try {
            await apiService.delete(`/tipos-documento/${id}`);
            setTiposDoc(prevTipos => prevTipos.filter(tipo => tipo.id !== id));
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al eliminar el tipo de documento.');
        }
    };

    const handlePurge = async (id, nombre) => {
        if (!window.confirm(`⚠️ ADVERTENCIA DE LIMPIEZA ⚠️\n\nEstá a punto de PURGAR el tipo de documento: ${nombre}.\n\nEsto eliminará PERMANENTEMENTE los documentos ANULADOS y ELIMINADOS asociados a este tipo.\n\nÚselo solo para limpiar tipos de documento creados por error (basura).\n\n¿CONFIRMA LA DESTRUCCIÓN DE DATOS?`)) return;

        setError(null);
        setIsLoading(true);
        try {
            // New endpoint for Hard Delete
            const response = await apiService.delete(`/utilidades/purgar-tipo-documento/${id}`);
            alert(response.data.msg);
            setTiposDoc(prevTipos => prevTipos.filter(tipo => tipo.id !== id));
        } catch (err) {
            console.error(err);
            const msg = err.response?.data?.detail || 'Error al purgar el tipo de documento.';
            alert(`❌ ERROR: ${msg}`);
            setError(msg);
        } finally {
            setIsLoading(false);
        }
    };

    // --- Loading State v2.0 ---
    if (authLoading || isLoading) {
        return (
            <div className="min-h-screen bg-gray-50 flex justify-center items-center">
                <span className="loading loading-spinner loading-lg text-indigo-600"></span>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
            <div className="max-w-7xl mx-auto">

                {/* 1. ENCABEZADO */}
                <div className="flex justify-between items-center mb-8">
                    <div className="flex items-center gap-3">
                        <div className="p-3 bg-indigo-100 text-indigo-600 rounded-xl shadow-sm">
                            <FaFileInvoice className="text-2xl" />
                        </div>
                        <div>
                            <div className="flex items-center gap-3">
                                <h1 className="text-3xl font-bold text-gray-800 tracking-tight">Tipos de Documento</h1>
                                <button
                                    onClick={() => window.open('/manual/capitulo_2_tipos_documento.html', '_blank')}
                                    className="flex items-center gap-2 px-2 py-1 bg-white border border-indigo-200 text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors font-medium shadow-sm"
                                    type="button"
                                >
                                    <FaBook /> <span className="hidden md:inline">Manual</span>
                                </button>
                            </div>
                            <p className="text-gray-500 text-sm mt-1">Configuración de comprobantes contables y numeración.</p>
                        </div>
                    </div>

                    {/* Botones de Acción Superior */}
                    <div className="flex gap-2">
                        {/* Empty container now, actions consolidated */}
                    </div>
                </div>

                {/* 2. BARRA DE CONTROL (Acciones Principales) */}
                <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 mb-8 animate-fadeIn flex flex-col md:flex-row justify-between items-center gap-4">
                    <div>
                        <h2 className="text-sm font-bold text-gray-500 uppercase tracking-wide">Gestión de Maestros</h2>
                    </div>
                    <Link
                        href="/admin/tipos-documento/crear"
                        className="btn btn-primary bg-indigo-600 hover:bg-indigo-700 text-white shadow-md rounded-lg font-bold px-6 border-0 flex items-center gap-2"
                    >
                        <FaPlus /> Crear Nuevo Tipo
                    </Link>
                </div>

                {/* 3. MENSAJES DE ERROR */}
                {error && (
                    <div className="alert alert-error shadow-lg mb-6 rounded-xl text-white animate-fadeIn">
                        <FaExclamationCircle className="text-xl" />
                        <span>{error}</span>
                    </div>
                )}

                {/* 4. TABLA DE RESULTADOS */}
                <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden animate-slideDown">
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-slate-100 border-b border-gray-200">
                                <tr>
                                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">Código</th>
                                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">Nombre</th>
                                    <th className="px-6 py-4 text-center text-xs font-bold text-gray-600 uppercase tracking-wider">Modo Numeración</th>
                                    <th className="px-6 py-4 text-center text-xs font-bold text-gray-600 uppercase tracking-wider">Consecutivo</th>
                                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">Función Especial</th>
                                    <th className="px-6 py-4 text-center text-xs font-bold text-gray-600 uppercase tracking-wider">Diseño</th>
                                    <th className="px-6 py-4 text-center text-xs font-bold text-gray-600 uppercase tracking-wider">Acciones</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-50 bg-white">
                                {tiposDoc.map((tipo) => (
                                    <tr key={tipo.id} className="hover:bg-gray-50 transition-colors duration-150">
                                        {/* Código */}
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className="font-mono font-bold text-indigo-600 bg-indigo-50 px-2 py-1 rounded text-sm">
                                                {tipo.codigo}
                                            </span>
                                        </td>

                                        {/* Nombre */}
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-800 font-medium">
                                            {tipo.nombre}
                                        </td>

                                        {/* Numeración */}
                                        <td className="px-6 py-4 whitespace-nowrap text-center">
                                            {tipo.numeracion_manual ? (
                                                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-100">
                                                    Manual
                                                </span>
                                            ) : (
                                                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-100">
                                                    <FaCheckCircle className="text-[10px]" /> Automática
                                                </span>
                                            )}
                                        </td>

                                        {/* Último Consecutivo */}
                                        <td className="px-6 py-4 whitespace-nowrap text-center font-mono text-sm text-gray-600">
                                            {tipo.numeracion_manual ? (
                                                <span className="text-gray-400 text-xs italic">N/A</span>
                                            ) : (
                                                tipo.consecutivo_actual
                                            )}
                                        </td>

                                        {/* Función Especial */}
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            {tipo.funcion_especial ? (
                                                <span className="inline-flex px-2 py-1 rounded text-xs font-bold bg-purple-50 text-purple-700 border border-purple-100 uppercase tracking-wide">
                                                    {tipo.funcion_especial}
                                                </span>
                                            ) : (
                                                <span className="text-gray-400 text-xs">-</span>
                                            )}
                                        </td>

                                        {/* Diseño de Formato */}
                                        <td className="px-6 py-4 whitespace-nowrap text-center">
                                            <Link
                                                href={`/admin/tipos-documento/disenar/${tipo.id}`}
                                                className="btn btn-sm btn-ghost text-indigo-600 hover:bg-indigo-50 hover:text-indigo-800 tooltip"
                                                data-tip="Diseñar Formato"
                                            >
                                                <FaPencilRuler /> <span className="hidden lg:inline ml-1 text-xs">Diseñar</span>
                                            </Link>
                                        </td>

                                        {/* Acciones */}
                                        <td className="px-6 py-4 whitespace-nowrap text-center">
                                            <div className="flex justify-center items-center gap-2">
                                                <Link
                                                    href={`/admin/tipos-documento/editar/${tipo.id}`}
                                                    className="btn btn-sm btn-square btn-ghost text-gray-500 hover:text-indigo-600 hover:bg-indigo-50 transition-colors tooltip"
                                                    data-tip="Editar"
                                                >
                                                    <FaEdit />
                                                </Link>
                                                {/* Botón Purgar (Limpieza de Basura) */}
                                                <button
                                                    onClick={() => handlePurge(tipo.id, tipo.nombre)}
                                                    className="btn btn-sm btn-square btn-ghost text-gray-400 hover:text-red-700 hover:bg-red-50 transition-colors tooltip tooltip-error"
                                                    data-tip="Purgar (Limpieza Profunda)"
                                                >
                                                    <FaEraser />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}

                                {tiposDoc.length === 0 && (
                                    <tr>
                                        <td colSpan="7" className="px-6 py-12 text-center text-gray-500">
                                            <p className="text-base italic">No hay tipos de documento configurados.</p>
                                            <p className="text-sm mt-1 text-gray-400">Comienza creando uno nuevo con el botón superior.</p>
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>

                    {/* Footer de Tabla */}
                    <div className="bg-gray-50 px-6 py-3 border-t border-gray-200 text-xs text-gray-500 text-right font-medium">
                        Total Registros: {tiposDoc.length}
                    </div>
                </div>
            </div >
        </div >
    );
}