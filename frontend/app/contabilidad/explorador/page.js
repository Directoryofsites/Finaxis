// frontend/app/contabilidad/explorador/page.js
'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/app/context/AuthContext';
import { apiService } from '@/lib/apiService';
import BotonRegresar from '@/app/components/BotonRegresar';

// --- Iconos Estándar v2.0 ---
import {
    FaSearch, FaPrint, FaEraser,
    FaFileInvoice, FaFilter, FaCalendarAlt, FaBook
} from 'react-icons/fa';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

export default function ExploradorDocumentosPage() {
    const router = useRouter();
    const { user, authLoading } = useAuth();

    // --- ESTADOS DE DATOS ---
    const [documentos, setDocumentos] = useState([]);
    const [tiposDoc, setTiposDoc] = useState([]);
    const [terceros, setTerceros] = useState([]);
    const [hasSearched, setHasSearched] = useState(false); // Controla si ya se buscó

    // --- ESTADOS DE FILTRO ---
    const [filtros, setFiltros] = useState({
        fecha_inicio: '',
        fecha_fin: '',
        tipo_documento_id: '', // <--- CORREGIDO: Nombre estándar de BD
        tercero_id: '',
        numero: ''
    });

    // --- PAGINACIÓN ---
    const [paginacion, setPaginacion] = useState({
        page: 1,
        limit: 20,
        total: 0
    });

    const [isLoading, setIsLoading] = useState(false);
    const [isPrinting, setIsPrinting] = useState(null);

    // --- CARGA DE MAESTROS (Solo al iniciar) ---
    useEffect(() => {
        if (user?.empresaId) {
            const cargarMaestros = async () => {
                try {
                    const [resTipos, resTerceros] = await Promise.all([
                        apiService.get('/tipos-documento'),
                        apiService.get('/terceros')
                    ]);
                    setTiposDoc(resTipos.data || []);
                    setTerceros(resTerceros.data || []);
                } catch (err) {
                    console.error("Error cargando filtros", err);
                    toast.error("No se pudieron cargar los filtros.");
                }
            };
            cargarMaestros();
        }
    }, [user]);

    // --- BÚSQUEDA MANUAL ---
    const fetchDocumentos = useCallback(async (page = 1) => {
        if (!user?.empresaId) return;

        setIsLoading(true);
        setHasSearched(true); // Activamos la vista de resultados

        try {
            // Construimos Query Params
            const params = new URLSearchParams();
            params.append('skip', (page - 1) * paginacion.limit);
            params.append('limit', paginacion.limit);

            // Agregamos filtros solo si tienen valor
            if (filtros.fecha_inicio) params.append('fecha_inicio', filtros.fecha_inicio);
            if (filtros.fecha_fin) params.append('fecha_fin', filtros.fecha_fin);

            // CORRECCIÓN CRÍTICA: Usamos el nombre correcto 'tipo_documento_id'
            if (filtros.tipo_documento_id && filtros.tipo_documento_id !== "") {
                params.append('tipo_documento_id', filtros.tipo_documento_id);
            }

            if (filtros.tercero_id && filtros.tercero_id !== "") {
                params.append('tercero_id', filtros.tercero_id);
            }

            if (filtros.numero) params.append('numero', filtros.numero);

            const response = await apiService.get(`/documentos/?${params.toString()}`);

            setDocumentos(response.data.documentos);
            setPaginacion(prev => ({ ...prev, page, total: response.data.total }));

        } catch (err) {
            console.error(err);
            toast.error("Error al buscar documentos.");
            setDocumentos([]);
        } finally {
            setIsLoading(false);
        }
    }, [user, filtros, paginacion.limit]);

    // --- MANEJADORES ---
    const handleFilterChange = (e) => {
        const { name, value } = e.target;
        setFiltros(prev => ({ ...prev, [name]: value }));
    };

    const handleLimpiar = () => {
        setFiltros({
            fecha_inicio: '',
            fecha_fin: '',
            tipo_documento_id: '', // Limpieza corregida
            tercero_id: '',
            numero: ''
        });
        setDocumentos([]);
        setHasSearched(false);
        setPaginacion(prev => ({ ...prev, page: 1, total: 0 }));
    };

    // --- REIMPRESIÓN ---
    const handleReimprimir = async (docId) => {
        setIsPrinting(docId);
        try {
            const response = await apiService.post(`/documentos/${docId}/solicitar-impresion`);
            const { signed_url } = response.data;
            window.open(signed_url, '_blank');
            toast.success("Documento generado.");
        } catch (error) {
            console.error(error);
            toast.error("Error al generar PDF.");
        } finally {
            setIsPrinting(null);
        }
    };

    const fmtMoney = (val) => new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(val);

    if (authLoading) return <div className="h-screen flex items-center justify-center"><span className="loading loading-spinner text-indigo-600"></span></div>;

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
            <ToastContainer />
            <div className="max-w-7xl mx-auto">

                {/* 1. ENCABEZADO */}
                <div className="flex justify-between items-center mb-8">
                    <div className="flex items-center gap-3">
                        <div className="p-3 bg-indigo-100 text-indigo-600 rounded-xl shadow-sm">
                            <FaFileInvoice className="text-2xl" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold text-gray-800 tracking-tight">Explorador de Documentos</h1>
                            <p className="text-gray-500 text-sm mt-1">Consulta histórica y reimpresión de comprobantes.</p>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <BotonRegresar />
                        <button
                            onClick={() => window.open('/manual?file=capitulo_26_explorador.md', '_blank')}
                            className="btn btn-sm btn-ghost text-indigo-600 gap-2"
                            title="Ver Manual"
                        >
                            <FaBook /> Manual
                        </button>
                    </div>
                </div>

                {/* 2. CARD DE FILTROS */}
                <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 mb-8 animate-fadeIn">
                    <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 items-end">

                        {/* Filtro Fechas */}
                        <div className="lg:col-span-1">
                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Desde</label>
                            <input type="date" name="fecha_inicio" value={filtros.fecha_inicio} onChange={handleFilterChange} className="input input-bordered input-sm w-full" />
                        </div>
                        <div className="lg:col-span-1">
                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Hasta</label>
                            <input type="date" name="fecha_fin" value={filtros.fecha_fin} onChange={handleFilterChange} className="input input-bordered input-sm w-full" />
                        </div>

                        {/* Filtro Tipo (CORREGIDO NAME Y VALUE) */}
                        <div className="lg:col-span-1">
                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Tipo Documento</label>
                            <select
                                name="tipo_documento_id"
                                value={filtros.tipo_documento_id}
                                onChange={handleFilterChange}
                                className="select select-bordered select-sm w-full"
                            >
                                <option value="">-- Todos --</option>
                                {tiposDoc.map(t => <option key={t.id} value={t.id}>{t.codigo} - {t.nombre}</option>)}
                            </select>
                        </div>

                        {/* Filtro Tercero */}
                        <div className="lg:col-span-1">
                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Tercero</label>
                            <select name="tercero_id" value={filtros.tercero_id} onChange={handleFilterChange} className="select select-bordered select-sm w-full">
                                <option value="">-- Todos --</option>
                                {terceros.map(t => <option key={t.id} value={t.id}>{t.razon_social}</option>)}
                            </select>
                        </div>

                        {/* Filtro Número y Botones */}
                        <div className="lg:col-span-1 flex gap-2">
                            <div className="flex-1">
                                <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Número</label>
                                <input type="text" name="numero" value={filtros.numero} onChange={handleFilterChange} placeholder="#" className="input input-bordered input-sm w-full" />
                            </div>

                            <button onClick={() => fetchDocumentos(1)} className="btn btn-sm btn-primary bg-indigo-600 border-none text-white mt-6 tooltip" data-tip="Buscar">
                                <FaSearch />
                            </button>

                            <button onClick={handleLimpiar} className="btn btn-sm btn-ghost text-gray-400 mt-6 tooltip" data-tip="Limpiar">
                                <FaEraser />
                            </button>
                        </div>
                    </div>
                </div>

                {/* 3. TABLA DE RESULTADOS */}
                <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden animate-slideDown">

                    {/* Estado Vacío Inicial */}
                    {!hasSearched && (
                        <div className="p-16 text-center flex flex-col items-center justify-center text-gray-400">
                            <div className="p-6 bg-gray-50 rounded-full mb-4">
                                <FaFilter className="text-4xl text-indigo-200" />
                            </div>
                            <h3 className="text-lg font-semibold text-gray-600">Listo para buscar</h3>
                            <p className="text-sm mt-1">Aplique los filtros superiores para consultar el historial.</p>
                        </div>
                    )}

                    {/* Tabla de Datos */}
                    {hasSearched && (
                        <div className="overflow-x-auto">
                            <table className="table w-full">
                                <thead className="bg-slate-100 text-gray-600 uppercase text-xs font-bold">
                                    <tr>
                                        <th>Fecha</th>
                                        <th>Tipo</th>
                                        <th>Número</th>
                                        <th>Beneficiario</th>
                                        <th className="text-right">Valor Total</th>
                                        <th className="text-center">Estado</th>
                                        <th className="text-center">Acciones</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {documentos.map(doc => (
                                        <tr key={doc.id} className="hover:bg-gray-50 transition-colors border-b border-gray-50">
                                            <td className="font-mono text-xs">{new Date(doc.fecha).toLocaleDateString('es-CO')}</td>
                                            <td className="font-bold text-xs text-gray-700">{doc.tipo_documento_nombre || doc.tipo_documento}</td>
                                            <td className="font-mono text-indigo-600 font-bold">{doc.numero}</td>
                                            <td className="text-xs truncate max-w-[200px]" title={doc.beneficiario_nombre || doc.beneficiario}>
                                                {doc.beneficiario_nombre || doc.beneficiario || 'N/A'}
                                            </td>
                                            <td className="text-right font-mono font-bold text-gray-700">
                                                {fmtMoney(doc.total_debito || doc.total)}
                                            </td>
                                            <td className="text-center">
                                                {doc.anulado ?
                                                    <span className="badge badge-error badge-xs gap-1 text-white">ANULADO</span> :
                                                    <span className="badge badge-success badge-outline badge-xs">ACTIVO</span>
                                                }
                                            </td>
                                            <td className="text-center">
                                                {/* BOTÓN REIMPRIMIR ÚNICO */}
                                                <button
                                                    onClick={() => handleReimprimir(doc.id)}
                                                    disabled={isPrinting === doc.id}
                                                    className="btn btn-sm btn-ghost text-indigo-600 hover:bg-indigo-50 hover:text-indigo-800 gap-2"
                                                    title="Reimprimir Documento"
                                                >
                                                    {isPrinting === doc.id ? <span className="loading loading-spinner loading-xs"></span> : <FaPrint />}
                                                    <span className="hidden md:inline text-xs font-bold">Imprimir</span>
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                    {documentos.length === 0 && !isLoading && (
                                        <tr>
                                            <td colSpan="7" className="text-center py-10 text-gray-400 italic">
                                                No se encontraron documentos con estos criterios.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {/* Footer Paginación */}
                    {hasSearched && documentos.length > 0 && (
                        <div className="p-4 border-t border-gray-100 flex justify-between items-center bg-gray-50">
                            <span className="text-xs text-gray-500 font-medium">Total registros: {paginacion.total}</span>
                            <div className="join">
                                <button
                                    className="join-item btn btn-sm bg-white border-gray-300"
                                    disabled={paginacion.page === 1}
                                    onClick={() => fetchDocumentos(paginacion.page - 1)}
                                >« Anterior</button>
                                <button className="join-item btn btn-sm bg-white border-gray-300 no-animation">Pág {paginacion.page}</button>
                                <button
                                    className="join-item btn btn-sm bg-white border-gray-300"
                                    disabled={documentos.length < paginacion.limit}
                                    onClick={() => fetchDocumentos(paginacion.page + 1)}
                                >Siguiente »</button>
                            </div>
                        </div>
                    )}
                </div>

            </div>
        </div>
    );
}