'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import BotonRegresar from '../../components/BotonRegresar';
import { phService } from '../../../lib/phService';
import {
    FaFileInvoiceDollar,
    FaPlay,
    FaCheckCircle,
    FaExclamationTriangle,
    FaList,
    FaHistory,
    FaTrash,
    FaCalendarAlt,
    FaCheckSquare,
    FaRegSquare,
    FaLayerGroup,
    FaEye,
    FaTimes,
    FaFilePdf
} from 'react-icons/fa';

export default function FacturacionPHPage() {
    const { user, loading: authLoading } = useAuth();

    // --- ESTADOS DE FECHA ---
    // fechaPeriodo: Define el "Mes" lógico de la facturación (YYYY-MM). Usado para historial y detectar duplicados.
    const [fechaPeriodo, setFechaPeriodo] = useState(new Date().toISOString().slice(0, 7));

    // fechaRegistro: Define la fecha contable exacta del asiento (YYYY-MM-DD).
    const [fechaRegistro, setFechaRegistro] = useState(new Date().toISOString().slice(0, 10));

    // --- ESTADOS DE DATOS ---
    const [conceptos, setConceptos] = useState([]);
    const [selectedConceptos, setSelectedConceptos] = useState([]); // IDs
    const [historial, setHistorial] = useState([]);

    // --- ESTADOS DE UI ---
    const [loading, setLoading] = useState(false);
    const [resultado, setResultado] = useState(null);
    const [error, setError] = useState(null);
    const [showWarningModal, setShowWarningModal] = useState(false);
    const [warningData, setWarningData] = useState({ cantidad: 0 });

    useEffect(() => {
        if (!authLoading && user?.empresaId) {
            loadInitialData();
        }
    }, [authLoading, user]);

    const loadInitialData = async () => {
        try {
            const [conceptosData, historialData] = await Promise.all([
                phService.getConceptos(),
                phService.getHistorialFacturacion() // Esto carga el historial general
            ]);
            // Filtrar solo activos y ordenar por nombre
            const activos = conceptosData.filter(c => c.activo).sort((a, b) => a.nombre.localeCompare(b.nombre));
            setConceptos(activos);
            setHistorial(historialData);
        } catch (err) {
            console.error("Error cargando datos iniciales", err);
            setError("Error cargando datos del servidor.");
        }
    };

    const loadHistorial = async () => {
        try {
            const data = await phService.getHistorialFacturacion();
            setHistorial(data);
        } catch (error) {
            console.error("Error refreshing history", error);
        }
    };

    // --- HANDLERS SELECCIÓN ---
    const toggleConcepto = (id) => {
        if (selectedConceptos.includes(id)) {
            setSelectedConceptos(prev => prev.filter(x => x !== id));
        } else {
            setSelectedConceptos(prev => [...prev, id]);
        }
    };

    const toggleAll = () => {
        if (selectedConceptos.length === conceptos.length) {
            setSelectedConceptos([]); // Deseleccionar todo
        } else {
            setSelectedConceptos(conceptos.map(c => c.id)); // Seleccionar todo
        }
    };

    // --- LÓGICA DE EJECUCIÓN ---
    const handlePreGenerate = async () => {
        if (selectedConceptos.length === 0) {
            alert("⚠️ Selecciona al menos un concepto para facturar.");
            return;
        }

        setError(null);
        setResultado(null);

        // El chequeo de duplicidad se hace sobre el PERIODO (Mes), no sobre el día exacto.
        // Asumimos que la lógica de negocio es "Una facturación por mes".
        const fechaCheck = `${fechaPeriodo}-01`;

        try {
            setLoading(true);
            const check = await phService.checkFacturacionMasiva(fechaCheck);
            setLoading(false);

            if (check.existe) {
                setWarningData({ cantidad: check.cantidad });
                setShowWarningModal(true);
            } else {
                // Confirmación simple
                if (confirm(`¿Confirmas generar la facturación para el periodo ${fechaPeriodo} con fecha de registro ${fechaRegistro}?`)) {
                    ejecutarGeneracion(false);
                }
            }
        } catch (err) {
            setLoading(false);
            console.error(err);
            alert("Error verificando historial.");
        }
    };

    const handleModalOption = async (accion) => {
        setShowWarningModal(false);
        if (accion === 'CANCEL') return;

        if (accion === 'DELETE_AND_REGENERATE') {
            try {
                setLoading(true);
                // Borrar el periodo detectado
                await phService.deleteFacturacionMasiva(fechaPeriodo);
                // Generar
                await ejecutarGeneracion(true);
            } catch (err) {
                setLoading(false);
                alert("Error al eliminar facturas anteriores: " + (err.response?.data?.detail || err.message));
            }
        } else if (accion === 'APPEND') {
            ejecutarGeneracion(false);
        }
    };

    const handleDownloadPDF = async () => {
        try {
            const blob = await phService.getPDFDetalleFacturacion(detallePeriodo);
            const url = window.URL.createObjectURL(new Blob([blob]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `Detalle_Facturacion_${detallePeriodo}.pdf`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (error) {
            console.error("Error downloading PDF", error);
            alert("Error al descargar el PDF");
        }
    };

    const ejecutarGeneracion = async (skipConfirm) => {
        setLoading(true);
        try {
            // ENVIAMOS LA FECHA EXACTA DE REGISTRO
            // El backend usará esta fecha para "fecha" del documento.
            const data = await phService.generarFacturacionMasiva(fechaRegistro, selectedConceptos);
            setResultado(data);
            loadHistorial();
        } catch (err) {
            setError(err.response?.data?.detail || 'Error crítico al generar facturación.');
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteFromHistory = async (periodo) => {
        if (!confirm(`🚨 ¿Estás seguro de ELIMINAR todo el periodo ${periodo}?\nSe reversarán asientos y anularán facturas.`)) return;
        try {
            setLoading(true);
            const res = await phService.deleteFacturacionMasiva(periodo);
            alert(res.mensaje);
            loadHistorial();
        } catch (error) {
            alert("Error eliminando: " + (error.response?.data?.detail || error.message));
        } finally {
            setLoading(false);
        }
    };

    // --- LÓGICA DE DETALLE ---
    const [showDetailModal, setShowDetailModal] = useState(false);
    const [detalleFacturas, setDetalleFacturas] = useState([]);
    const [loadingDetalle, setLoadingDetalle] = useState(false);
    const [detallePeriodo, setDetallePeriodo] = useState('');

    const handleVerDetalle = async (periodo) => {
        setDetallePeriodo(periodo);
        setShowDetailModal(true);
        setLoadingDetalle(true);
        setDetalleFacturas([]);

        try {
            const data = await phService.getDetalleFacturacion(periodo);
            setDetalleFacturas(data);
        } catch (error) {
            console.error(error);
            alert("Error cargando detalle: " + (error.response?.data?.detail || error.message));
            setShowDetailModal(false);
        } finally {
            setLoadingDetalle(false);
        }
    };

    if (authLoading) return <div className="p-10 text-center text-gray-500">Cargando módulo...</div>;

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans pb-24">
            <div className="max-w-6xl mx-auto">
                {/* HEADER */}
                <div className="mb-8">
                    <BotonRegresar />
                    <div className="flex items-center gap-3 mt-4">
                        <div className="p-3 bg-gradient-to-tr from-indigo-600 to-purple-600 rounded-xl text-white shadow-lg">
                            <FaFileInvoiceDollar className="text-3xl" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-extrabold text-gray-800 tracking-tight">Facturación Masiva</h1>
                            <p className="text-gray-500 font-medium">Generación y causación de cuotas de administración.</p>
                        </div>
                    </div>
                </div>

                <div className="space-y-12">

                    {/* SECCIÓN SUPERIOR: CONFIGURACIÓN Y EJECUCIÓN */}
                    <div className="max-w-4xl mx-auto space-y-6">

                        {/* 1. SELECCIÓN DE FECHAS */}
                        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                            <div className="flex items-center gap-2 mb-4 text-indigo-700 font-bold uppercase text-xs tracking-wider">
                                <FaCalendarAlt /> Paso 1: Definir Periodo y Fecha
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <label className="block text-sm font-bold text-gray-700 mb-2">Mes a Liquidar (Periodo)</label>
                                    <input
                                        type="month"
                                        value={fechaPeriodo}
                                        onChange={(e) => setFechaPeriodo(e.target.value)}
                                        className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none font-bold text-gray-700"
                                    />
                                    <p className="text-xs text-gray-400 mt-1 ml-1">Referencia para el historial.</p>
                                </div>
                                <div>
                                    <label className="block text-sm font-bold text-gray-700 mb-2">Fecha de Registro Contable</label>
                                    <input
                                        type="date"
                                        value={fechaRegistro}
                                        onChange={(e) => setFechaRegistro(e.target.value)}
                                        className="w-full px-4 py-3 bg-indigo-50 border border-indigo-100 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none font-bold text-indigo-800"
                                    />
                                    <p className="text-xs text-indigo-400 mt-1 ml-1">Fecha real de causación.</p>
                                </div>
                            </div>
                        </div>

                        {/* 2. SELECCIÓN DE CONCEPTOS (GRID) */}
                        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-2 text-indigo-700 font-bold uppercase text-xs tracking-wider">
                                    <FaList /> Paso 2: Seleccionar Conceptos
                                </div>
                                <button
                                    onClick={toggleAll}
                                    className="text-xs font-bold text-indigo-600 hover:text-indigo-800 flex items-center gap-1 bg-indigo-50 px-3 py-1 rounded-full transition-colors"
                                >
                                    {selectedConceptos.length === conceptos.length ? <FaCheckSquare /> : <FaRegSquare />}
                                    {selectedConceptos.length === conceptos.length ? 'Deseleccionar Todos' : 'Seleccionar Todos'}
                                </button>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[400px] overflow-y-auto p-1">
                                {conceptos.length === 0 && <p className="text-sm text-gray-400 italic p-4 text-center w-full col-span-2">No hay conceptos configurados.</p>}

                                {conceptos.map(c => {
                                    const isSelected = selectedConceptos.includes(c.id);
                                    return (
                                        <div
                                            key={c.id}
                                            onClick={() => toggleConcepto(c.id)}
                                            className={`
                                                relative p-4 rounded-xl border-2 cursor-pointer transition-all duration-200 group
                                                ${isSelected
                                                    ? 'border-indigo-600 bg-indigo-50 shadow-md'
                                                    : 'border-gray-100 bg-white hover:border-indigo-200 hover:shadow-sm'
                                                }
                                            `}
                                        >
                                            <div className="flex items-start justify-between">
                                                <div className="flex-1">
                                                    <h4 className={`font-bold text-sm ${isSelected ? 'text-indigo-900' : 'text-gray-700'}`}>{c.nombre}</h4>
                                                    <div className="flex flex-wrap gap-2 mt-2">
                                                        <span className={`text-[10px] px-2 py-0.5 rounded-md font-medium ${isSelected ? 'bg-indigo-200 text-indigo-800' : 'bg-gray-100 text-gray-500'}`}>
                                                            {c.usa_coeficiente ? 'Coeficiente' : 'Valor Fijo'}
                                                        </span>
                                                        <span className="text-[10px] px-2 py-0.5 rounded-md bg-green-100 text-green-700 font-mono">
                                                            ${parseFloat(c.valor_defecto).toLocaleString()}
                                                        </span>
                                                    </div>

                                                    {/* Indicador de Módulo (si aplica) */}
                                                    {c.modulos && c.modulos.length > 0 && (
                                                        <div className="mt-2 flex items-center gap-1 text-[10px] text-orange-600 font-bold bg-orange-50 px-2 py-1 rounded inline-block">
                                                            <FaLayerGroup /> {c.modulos.length} Módulos
                                                        </div>
                                                    )}
                                                </div>
                                                <div className={`
                                                    w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors
                                                    ${isSelected ? 'bg-indigo-600 border-indigo-600 text-white' : 'border-gray-300 bg-gray-50'}
                                                `}>
                                                    {isSelected && <FaCheckCircle className="text-sm" />}
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                            <div className="mt-4 text-center text-xs text-gray-400 font-medium">
                                {selectedConceptos.length} conceptos seleccionados
                            </div>
                        </div>

                        {/* MENSAJES DE ERROR / RESULTADO */}
                        {error && (
                            <div className="p-4 bg-red-50 text-red-700 rounded-xl border border-red-200 flex items-center gap-3 animate-fadeIn">
                                <FaExclamationTriangle className="text-xl shrink-0" />
                                <div>
                                    <p className="font-bold">Error en el proceso</p>
                                    <p className="text-sm">{error}</p>
                                </div>
                            </div>
                        )}

                        {resultado && (
                            <div className="p-6 bg-emerald-50 text-emerald-800 rounded-xl border border-emerald-200 animate-slideUp relative overflow-hidden">
                                <div className="absolute top-0 right-0 p-4 opacity-10">
                                    <FaCheckCircle className="text-9xl" />
                                </div>
                                <h3 className="text-lg font-bold flex items-center gap-2 mb-4">
                                    <FaCheckCircle /> Proceso Finalizado Exitosamente
                                </h3>
                                <div className="grid grid-cols-2 gap-4 mb-4 relative z-10">
                                    <div className="bg-white/60 p-3 rounded-lg">
                                        <p className="text-2xl font-bold">{resultado.generadas}</p>
                                        <p className="text-xs uppercase tracking-wide font-bold opacity-70">Facturas</p>
                                    </div>
                                    <div className="bg-white/60 p-3 rounded-lg">
                                        <p className="text-2xl font-bold text-red-600">{resultado.errores}</p>
                                        <p className="text-xs uppercase tracking-wide font-bold opacity-70 text-red-600">Errores</p>
                                    </div>
                                </div>
                                <div className="max-h-40 overflow-y-auto text-xs font-mono bg-white/50 p-2 rounded relative z-10">
                                    {resultado.detalles.map((d, i) => <div key={i}>{d}</div>)}
                                </div>
                            </div>
                        )}

                        {/* BOTÓN EJECUTAR */}
                        <button
                            onClick={handlePreGenerate}
                            disabled={loading}
                            className={`
                                w-full py-5 rounded-2xl font-extrabold text-lg shadow-xl shadow-indigo-200 flex items-center justify-center gap-3 transition-all transform hover:scale-[1.02] active:scale-95
                                ${loading
                                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                    : 'bg-indigo-600 text-white hover:bg-indigo-700 hover:shadow-indigo-300'
                                }
                            `}
                        >
                            {loading ? (
                                <>
                                    <span className="loading loading-spinner"></span>
                                    <span>Procesando...</span>
                                </>
                            ) : (
                                <>
                                    <FaPlay /> EJECUTAR LIQUIDACIÓN
                                </>
                            )}
                        </button>
                    </div>

                    {/* SECCIÓN INFERIOR: HISTORIAL FULL WIDTH */}
                    <div className="w-full">
                        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                            <div className="p-6 bg-gray-50 border-b border-gray-100 flex items-center gap-2">
                                <FaHistory className="text-gray-500 text-xl" />
                                <h3 className="font-bold text-gray-800 text-lg">Historial de Facturaciones</h3>
                            </div>

                            <div className="max-h-[500px] overflow-y-auto">
                                {historial.length === 0 ? (
                                    <div className="p-12 text-center text-gray-400 italic">
                                        No hay registros históricos aún.
                                    </div>
                                ) : (
                                    <table className="w-full text-sm">
                                        <thead className="bg-gray-50 text-gray-500 text-xs uppercase sticky top-0 z-10">
                                            <tr>
                                                <th className="px-6 py-4 text-left">Periodo</th>
                                                <th className="px-6 py-4 text-center">Facturas Generadas</th>
                                                <th className="px-6 py-4 text-right">Monto Total</th>
                                                <th className="px-6 py-4 text-right">Acciones</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-100">
                                            {historial.map((h, i) => (
                                                <tr key={i} className="hover:bg-indigo-50 transition-colors group">
                                                    <td className="px-6 py-4">
                                                        <p className="font-bold text-indigo-900 text-lg">{h.periodo}</p>
                                                        <div className="flex items-center gap-2 mt-1">
                                                            <span className="badge badge-sm badge-ghost text-xs">Causado</span>
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-4 text-center">
                                                        <span className="inline-block px-3 py-1 bg-white border border-gray-200 rounded-lg font-bold text-gray-600">
                                                            {h.cantidad} Docts
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 text-right font-mono text-gray-800 font-bold text-lg">
                                                        ${parseFloat(h.total).toLocaleString()}
                                                    </td>
                                                    <td className="px-6 py-4 text-right">
                                                        <div className="flex items-center justify-end gap-2">
                                                            <button
                                                                onClick={() => handleVerDetalle(h.periodo)}
                                                                className="px-4 py-2 text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-lg transition-colors flex items-center gap-2 font-bold text-xs"
                                                                title="Ver lista de facturas"
                                                            >
                                                                <FaEye /> Ver Detalle
                                                            </button>
                                                            <button
                                                                onClick={() => handleDeleteFromHistory(h.periodo)}
                                                                className="px-4 py-2 text-red-500 hover:bg-red-100 rounded-lg transition-colors flex items-center gap-2 opacity-70 hover:opacity-100"
                                                                title="Eliminar todo este periodo"
                                                            >
                                                                <FaTrash />
                                                            </button>
                                                        </div>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                )}
                            </div>
                        </div>
                    </div>

                </div>

                {/* MODAL ADVERTENCIA REGENERACIÓN */}
                {showWarningModal && (
                    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fadeIn">
                        <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 border-t-8 border-orange-500">
                            <div className="flex flex-col items-center text-center mb-6">
                                <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center text-orange-600 mb-4">
                                    <FaExclamationTriangle className="text-3xl" />
                                </div>
                                <h3 className="text-2xl font-bold text-gray-800">¡Periodo ya Liquidado!</h3>
                                <p className="text-gray-600 mt-2">
                                    El periodo <strong>{fechaPeriodo}</strong> ya tiene <span className="font-bold text-orange-600">{warningData.cantidad} facturas</span> generadas.
                                </p>
                            </div>

                            <div className="space-y-3">
                                <button
                                    onClick={() => handleModalOption('DELETE_AND_REGENERATE')}
                                    className="w-full py-3 bg-red-600 text-white font-bold rounded-xl hover:bg-red-700 flex items-center justify-center gap-2 shadow-lg shadow-red-200"
                                >
                                    <FaTrash /> Borrar Todo y Regenerar
                                </button>
                                <button
                                    onClick={() => handleModalOption('APPEND')}
                                    className="w-full py-3 bg-white border-2 border-orange-100 text-orange-600 font-bold rounded-xl hover:bg-orange-50 flex items-center justify-center gap-2"
                                >
                                    <FaCheckCircle /> Completar Faltantes (Delta)
                                </button>
                            </div>

                            <button
                                onClick={() => handleModalOption('CANCEL')}
                                className="w-full mt-4 text-sm text-gray-500 hover:text-gray-800 underline"
                            >
                                Cancelar operación
                            </button>
                        </div>
                    </div>
                )}

                {/* MODAL DETALLE PERIODICO */}
                {showDetailModal && (
                    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-6 animate-fadeIn">
                        <div className="bg-white rounded-2xl shadow-2xl w-full max-w-5xl h-[80vh] flex flex-col overflow-hidden">
                            {/* Header Modal */}
                            <div className="p-6 bg-indigo-600 text-white flex justify-between items-center shrink-0">
                                <div>
                                    <h3 className="text-xl font-bold flex items-center gap-2">
                                        <FaFileInvoiceDollar /> Detalle de Facturación
                                    </h3>
                                    <p className="text-indigo-200 text-sm">Periodo: {detallePeriodo}</p>
                                </div>
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={handleDownloadPDF}
                                        className="bg-white/20 hover:bg-white/30 px-4 py-2 rounded-lg text-white transition-colors flex items-center gap-2 font-bold text-sm"
                                        title="Descargar PDF"
                                    >
                                        <FaFilePdf /> Generar PDF
                                    </button>
                                    <button onClick={() => setShowDetailModal(false)} className="bg-white/20 hover:bg-white/30 p-2 rounded-full text-white transition-colors">
                                        <FaTimes className="text-xl" />
                                    </button>
                                </div>
                            </div>

                            {/* Body Modal */}
                            <div className="flex-1 overflow-y-auto p-6 bg-gray-50">
                                {loadingDetalle ? (
                                    <div className="flex flex-col items-center justify-center h-full text-gray-400">
                                        <span className="loading loading-spinner loading-lg"></span>
                                        <p className="mt-4">Cargando facturas...</p>
                                    </div>
                                ) : (
                                    detalleFacturas.length === 0 ? (
                                        <div className="text-center text-gray-400 mt-20">No se encontraron datos para este periodo.</div>
                                    ) : (
                                        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                                            <table className="w-full text-sm">
                                                <thead className="bg-gray-100 text-gray-600 font-bold uppercase text-xs sticky top-0">
                                                    <tr>
                                                        <th className="px-4 py-3 text-left">Factura</th>
                                                        <th className="px-4 py-3 text-left">Fecha</th>
                                                        <th className="px-4 py-3 text-left">Tercero / Propietario</th>
                                                        <th className="px-4 py-3 text-left">Concepto / Unidad</th>
                                                        <th className="px-4 py-3 text-right">Total</th>
                                                        <th className="px-4 py-3 text-center">Estado</th>
                                                    </tr>
                                                </thead>
                                                <tbody className="divide-y divide-gray-100">
                                                    {detalleFacturas.map((fact) => (
                                                        <tr key={fact.id} className="hover:bg-indigo-50 transition-colors">
                                                            <td className="px-4 py-3 font-mono font-bold text-indigo-600">{fact.consecutivo}</td>
                                                            <td className="px-4 py-3 text-gray-500">{fact.fecha}</td>
                                                            <td className="px-4 py-3 font-medium text-gray-800">{fact.tercero_nombre}</td>
                                                            <td className="px-4 py-3 text-gray-600 text-xs">{fact.unidad}</td>
                                                            <td className="px-4 py-3 text-right font-mono font-bold">
                                                                ${parseFloat(fact.total).toLocaleString()}
                                                            </td>
                                                            <td className="px-4 py-3 text-center">
                                                                <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase
                                                                    ${fact.estado === 'ACTIVO' ? 'bg-green-100 text-green-700' :
                                                                        fact.estado === 'ANULADO' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-500'}
                                                                `}>
                                                                    {fact.estado}
                                                                </span>
                                                            </td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                                <tfoot className="bg-gray-50 font-bold text-gray-700">
                                                    <tr>
                                                        <td colSpan="4" className="px-4 py-3 text-right">TOTAL PERIODO:</td>
                                                        <td className="px-4 py-3 text-right text-indigo-700 text-lg">
                                                            ${detalleFacturas.reduce((sum, f) => sum + parseFloat(f.total), 0).toLocaleString()}
                                                        </td>
                                                        <td></td>
                                                    </tr>
                                                </tfoot>
                                            </table>
                                        </div>
                                    )
                                )}
                            </div>
                        </div>
                    </div>
                )}

            </div>
        </div>
    );
}
