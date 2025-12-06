'use client';

import React, { useState } from 'react';
import {
    FaBook,
    FaCalendarAlt,
    FaLock,
    FaPrint,
    FaFilePdf,
    FaCheckCircle,
    FaExclamationTriangle,
    FaInfoCircle
} from 'react-icons/fa';

import BotonRegresar from '@/app/components/BotonRegresar';
import { apiService } from '@/lib/apiService';

// Estilos Reusables (Manual v2.0)
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none pl-10";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white pl-10";

const LibrosOficialesPage = () => {
    // Estados para filtros
    const [tipoLibro, setTipoLibro] = useState('diario');
    const [ano, setAno] = useState(new Date().getFullYear());
    const [mes, setMes] = useState(new Date().getMonth() + 1);
    const [modo, setModo] = useState('borrador');

    // Estados de UI
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [successMsg, setSuccessMsg] = useState(null);

    const handleGenerateReport = async () => {
        setLoading(true);
        setError(null);
        setSuccessMsg(null);

        try {
            let endpointSuffix = '';
            const params = new URLSearchParams();

            const fecha_inicio = new Date(ano, mes - 1, 1);
            const fecha_fin = new Date(ano, mes, 0);
            const fecha_corte = fecha_fin;

            switch (tipoLibro) {
                case 'diario':
                    endpointSuffix = '/reports/journal';
                    params.append('fecha_inicio', fecha_inicio.toISOString().split('T')[0]);
                    params.append('fecha_fin', fecha_fin.toISOString().split('T')[0]);
                    break;
                case 'mayor':
                    endpointSuffix = '/reports/mayor-y-balances';
                    params.append('fecha_inicio', fecha_inicio.toISOString().split('T')[0]);
                    params.append('fecha_fin', fecha_fin.toISOString().split('T')[0]);
                    break;
                case 'inventarios':
                    endpointSuffix = '/reports/inventarios-y-balances';
                    params.append('fecha_corte', fecha_corte.toISOString().split('T')[0]);
                    break;
                default:
                    throw new Error('Tipo de libro no válido');
            }

            if (modo === 'oficial') {
                if (!window.confirm("⚠️ ADVERTENCIA DE CIERRE\n\nEstás a punto de generar un LIBRO OFICIAL.\nEsta acción CERRARÁ EL PERÍODO contable seleccionado, impidiendo modificaciones futuras.\n\n¿Estás seguro de continuar?")) {
                    setLoading(false);
                    return;
                }
                params.append('modo', 'oficial');
            }

            const response = await apiService.get(`${endpointSuffix}/get-signed-url?${params.toString()}`);

            const signedToken = response.data.signed_url_token;
            if (!signedToken) throw new Error('El servidor no devolvió el token de autorización.');

            const apiBaseUrl = apiService.defaults.baseURL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
            const cleanBaseUrl = apiBaseUrl.endsWith('/') ? apiBaseUrl.slice(0, -1) : apiBaseUrl;
            const cleanEndpoint = endpointSuffix.startsWith('/') ? endpointSuffix : `/${endpointSuffix}`;

            const downloadUrl = `${cleanBaseUrl}${cleanEndpoint}/imprimir?signed_token=${signedToken}`;

            const link = document.createElement('a');
            link.href = downloadUrl;
            link.setAttribute('download', `Libro_${tipoLibro}_${ano}_${mes}.pdf`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            if (modo === 'oficial') {
                setSuccessMsg(`El período ${mes}/${ano} ha sido CERRADO exitosamente y el reporte oficial se está descargando.`);
            }

        } catch (err) {
            console.error("Error completo:", err);
            let mensaje = "Error desconocido al generar el reporte.";
            if (err.response) {
                mensaje = err.response.data?.detail || `Error del servidor (${err.response.status})`;
            } else if (err.request) {
                mensaje = "No se pudo conectar con el servidor. Verifica tu conexión.";
            } else {
                mensaje = err.message;
            }
            setError(mensaje);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans">
            <div className="max-w-4xl mx-auto">

                {/* ENCABEZADO */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                    <div>
                        <BotonRegresar />
                        <div className="flex items-center gap-3 mt-3">
                            <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                                <FaBook className="text-2xl" />
                            </div>
                            <div>
                                <h1 className="text-3xl font-bold text-gray-800">Libros Oficiales</h1>
                                <p className="text-gray-500 text-sm">Generación y cierre de libros contables oficiales.</p>
                            </div>
                        </div>
                    </div>
                    <button
                        onClick={() => window.open('/manual?file=capitulo_32_libros_oficiales.md', '_blank')}
                        className="text-indigo-600 hover:bg-indigo-50 px-3 py-1 rounded-md flex items-center gap-2 transition-colors"
                        title="Ver Manual de Usuario"
                    >
                        <FaBook className="text-lg" /> <span className="font-bold text-sm">Manual</span>
                    </button>
                </div>

                {/* CARD PRINCIPAL */}
                <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-8 animate-fadeIn">
                    <div className="space-y-8">

                        {/* SECCIÓN 1: CONFIGURACIÓN */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* Tipo de Libro */}
                            <div className="md:col-span-2">
                                <label className={labelClass}>Tipo de Libro Oficial</label>
                                <div className="relative">
                                    <select
                                        value={tipoLibro}
                                        onChange={(e) => setTipoLibro(e.target.value)}
                                        className={selectClass}
                                    >
                                        <option value="diario">📘 Libro Diario</option>
                                        <option value="mayor">📗 Libro Mayor y Balances</option>
                                        <option value="inventarios">📙 Libro de Inventarios y Balances</option>
                                    </select>
                                    <FaBook className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                </div>
                            </div>

                            {/* Año */}
                            <div>
                                <label className={labelClass}>Año Gravable</label>
                                <div className="relative">
                                    <input
                                        type="number"
                                        value={ano}
                                        onChange={(e) => setAno(parseInt(e.target.value, 10))}
                                        className={inputClass}
                                    />
                                    <FaCalendarAlt className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                </div>
                            </div>

                            {/* Mes */}
                            <div>
                                <label className={labelClass}>Mes de Cierre</label>
                                <div className="relative">
                                    <select
                                        value={mes}
                                        onChange={(e) => setMes(parseInt(e.target.value, 10))}
                                        className={selectClass}
                                    >
                                        {[...Array(12).keys()].map(m => (
                                            <option key={m + 1} value={m + 1}>
                                                {new Date(0, m).toLocaleString('es-CO', { month: 'long' }).charAt(0).toUpperCase() + new Date(0, m).toLocaleString('es-CO', { month: 'long' }).slice(1)}
                                            </option>
                                        ))}
                                    </select>
                                    <FaCalendarAlt className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                </div>
                            </div>
                        </div>

                        {/* SECCIÓN 2: MODO DE OPERACIÓN (TARJETAS SELECCIONABLES) */}
                        <div className="pt-4 border-t border-gray-100">
                            <label className={labelClass}>Modo de Operación</label>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
                                {/* Tarjeta Borrador */}
                                <div
                                    onClick={() => setModo('borrador')}
                                    className={`cursor-pointer p-4 rounded-xl border-2 transition-all duration-200 flex items-start gap-4 hover:shadow-md
                                        ${modo === 'borrador'
                                            ? 'bg-indigo-50 border-indigo-500 ring-1 ring-indigo-200'
                                            : 'bg-white border-gray-100 hover:border-indigo-200 hover:bg-gray-50'}
                                    `}
                                >
                                    <div className={`mt-1 p-2 rounded-full ${modo === 'borrador' ? 'bg-indigo-200 text-indigo-700' : 'bg-gray-100 text-gray-400'}`}>
                                        <FaPrint />
                                    </div>
                                    <div>
                                        <div className="font-bold text-gray-800 flex items-center gap-2">
                                            Modo Borrador
                                            {modo === 'borrador' && <FaCheckCircle className="text-indigo-600" />}
                                        </div>
                                        <p className="text-xs text-gray-500 mt-1 leading-relaxed">
                                            Genera el PDF para revisión. <strong>NO cierra el período</strong> y permite seguir editando documentos. Ideal para pruebas.
                                        </p>
                                    </div>
                                </div>

                                {/* Tarjeta Oficial (Zona de Peligro) */}
                                <div
                                    onClick={() => setModo('oficial')}
                                    className={`cursor-pointer p-4 rounded-xl border-2 transition-all duration-200 flex items-start gap-4 hover:shadow-md
                                        ${modo === 'oficial'
                                            ? 'bg-red-50 border-red-500 ring-1 ring-red-200'
                                            : 'bg-white border-gray-100 hover:border-red-200 hover:bg-red-50/30'}
                                    `}
                                >
                                    <div className={`mt-1 p-2 rounded-full ${modo === 'oficial' ? 'bg-red-200 text-red-700' : 'bg-gray-100 text-gray-400'}`}>
                                        <FaLock />
                                    </div>
                                    <div>
                                        <div className="font-bold text-gray-800 flex items-center gap-2">
                                            Modo Oficial
                                            {modo === 'oficial' && <FaExclamationTriangle className="text-red-600" />}
                                        </div>
                                        <p className="text-xs text-red-600/80 mt-1 leading-relaxed">
                                            <strong>ACCIÓN DEFINITIVA.</strong> Cierra el período contable en la base de datos y bloquea cualquier modificación futura en estas fechas.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* MENSAJES DE ESTADO */}
                        {error && (
                            <div className="p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded-r-lg flex items-start gap-3 animate-pulse">
                                <FaExclamationTriangle className="mt-1 text-xl" />
                                <div>
                                    <p className="font-bold">No se pudo generar el libro:</p>
                                    <p className="text-sm">{error}</p>
                                </div>
                            </div>
                        )}

                        {successMsg && (
                            <div className="p-4 bg-green-50 border-l-4 border-green-500 text-green-700 rounded-r-lg flex items-start gap-3 animate-fadeIn">
                                <FaCheckCircle className="mt-1 text-xl" />
                                <div>
                                    <p className="font-bold">Operación Exitosa</p>
                                    <p className="text-sm">{successMsg}</p>
                                </div>
                            </div>
                        )}

                        {/* BOTÓN DE ACCIÓN */}
                        <div className="pt-4 border-t border-gray-100 flex justify-end">
                            <button
                                onClick={handleGenerateReport}
                                disabled={loading}
                                className={`
                                    px-8 py-3 rounded-lg shadow-lg font-bold text-white text-lg transition-all transform hover:-translate-y-0.5 flex items-center gap-2
                                    ${loading
                                        ? 'bg-gray-400 cursor-not-allowed'
                                        : modo === 'oficial' ? 'bg-red-600 hover:bg-red-700 shadow-red-200' : 'bg-indigo-600 hover:bg-indigo-700 shadow-indigo-200'
                                    }
                                `}
                            >
                                {loading ? (
                                    <> <span className="loading loading-spinner loading-sm"></span> Procesando... </>
                                ) : (
                                    <>
                                        {modo === 'oficial' ? <FaLock /> : <FaFilePdf />}
                                        {modo === 'oficial' ? 'Cerrar Período y Generar' : 'Generar Borrador'}
                                    </>
                                )}
                            </button>
                        </div>

                    </div>
                </div>
            </div>
        </div>
    );
};

export default LibrosOficialesPage;