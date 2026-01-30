'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useRecaudos } from '../../../contexts/RecaudosContext'; // IMPORT
import ManualButton from '../../components/ManualButton';

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
    FaFilePdf,
    FaFilter,
    FaSearch
} from 'react-icons/fa';

export default function FacturacionPHPage() {
    const { user, loading: authLoading } = useAuth();
    const { labels } = useRecaudos(); // HOOK

    // --- ESTADOS DE FECHA ---
    const [fechaPeriodo, setFechaPeriodo] = useState(new Date().toISOString().slice(0, 7));
    const [fechaRegistro, setFechaRegistro] = useState(new Date().toISOString().slice(0, 10));

    // --- ESTADOS DE DATOS ---
    const [conceptos, setConceptos] = useState([]);
    const [selectedConceptos, setSelectedConceptos] = useState([]); // IDs
    const [historial, setHistorial] = useState([]);
    const [unidades, setUnidades] = useState([]); // Todas las unidades para el selector
    const [torres, setTorres] = useState([]); // Nuevas Torres para filtro

    // --- CONFIGURACIÓN FLEXIBLE (EXCEPCIONES) ---
    // Estructura: { conceptoId: [unidadId1, unidadId2] }
    // Si existe la clave y el array no está vacío, SOLO se cobra a esas unidades.
    const [conceptConfigs, setConceptConfigs] = useState({});

    // --- ESTADOS DE UI ---
    const [loading, setLoading] = useState(false);
    const [resultado, setResultado] = useState(null);
    const [error, setError] = useState(null);
    const [showWarningModal, setShowWarningModal] = useState(false);
    const [warningData, setWarningData] = useState({ cantidad: 0 });

    // --- MODAL DE SELECCIÓN DE UNIDADES ---
    const [showUnitModal, setShowUnitModal] = useState(false);
    const [currentConceptId, setCurrentConceptId] = useState(null);
    const [tempSelectedUnits, setTempSelectedUnits] = useState([]); // Selección temporal en el modal
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        if (!authLoading && user?.empresaId) {
            loadInitialData();
        }
    }, [authLoading, user]);

    const loadInitialData = async () => {
        try {
            const [conceptosData, historialData, unidadesData, torresData] = await Promise.all([
                phService.getConceptos(),
                phService.getHistorialFacturacion(),
                phService.getUnidades({ limit: 1000 }), // Traer todas para el selector
                phService.getTorres() // Fetch torres
            ]);
            // Filtrar solo activos y ordenar por nombre
            const activos = conceptosData.filter(c => c.activo).sort((a, b) => a.nombre.localeCompare(b.nombre));
            setConceptos(activos);
            setUnidades(unidadesData);
            setTorres(torresData || []); // Set torres

            // --- AUTO-SELECCIÓN INTELIGENTE ---
            const conceptosFijos = activos.filter(c => c.es_fijo || c.es_interes).map(c => c.id);
            setSelectedConceptos(conceptosFijos);

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

    // --- HANDLERS SELECCIÓN CONCEPTOS ---
    const toggleConcepto = (id) => {
        if (selectedConceptos.includes(id)) {
            setSelectedConceptos(prev => prev.filter(x => x !== id));
        } else {
            setSelectedConceptos(prev => [...prev, id]);
        }
    };

    const toggleAll = () => {
        if (selectedConceptos.length === conceptos.length) {
            setSelectedConceptos([]);
        } else {
            setSelectedConceptos(conceptos.map(c => c.id));
        }
    };

    // --- MANEJO DE CONFIGURACIÓN FLEXIBLE (FILTROS) ---
    const openUnitFilter = (e, conceptoId) => {
        e.stopPropagation(); // Evitar toggle del concepto
        setCurrentConceptId(conceptoId);
        // Cargar selección actual o vacía
        setTempSelectedUnits(conceptConfigs[conceptoId] || []);
        setSearchTerm('');
        setShowUnitModal(true);

        // Asegurar que el concepto esté seleccionado si abro su filtro
        if (!selectedConceptos.includes(conceptoId)) {
            setSelectedConceptos(prev => [...prev, conceptoId]);
        }
    };

    const toggleUnitSelection = (unitId) => {
        if (tempSelectedUnits.includes(unitId)) {
            setTempSelectedUnits(prev => prev.filter(x => x !== unitId));
        } else {
            setTempSelectedUnits(prev => [...prev, unitId]);
        }
    };

    const saveUnitFilter = () => {
        setConceptConfigs(prev => ({
            ...prev,
            [currentConceptId]: tempSelectedUnits
        }));
        setShowUnitModal(false);
    };

    const clearUnitFilter = (e, conceptoId) => {
        e.stopPropagation();
        const newConfigs = { ...conceptConfigs };
        delete newConfigs[conceptoId];
        setConceptConfigs(newConfigs);
    };

    // --- NUEVO HANDLER: SELECCION POR TORRE ---
    const handleToggleTower = (torreId) => {
        // 1. Identificar unidades de esta torre
        // Asumiendo que unidad tiene torre_id (verificado en modelo)
        const unidadesTorre = unidades.filter(u => u.torre_id === torreId).map(u => u.id);

        if (unidadesTorre.length === 0) return;

        // 2. Verificar estado actual (¿Todos seleccionados?)
        const allSelected = unidadesTorre.every(uid => tempSelectedUnits.includes(uid));

        if (allSelected) {
            // Deseleccionar todos
            setTempSelectedUnits(prev => prev.filter(uid => !unidadesTorre.includes(uid)));
        } else {
            // Seleccionar todos (Union)
            // Usamos Set para evitar duplicados
            const parking = new Set([...tempSelectedUnits, ...unidadesTorre]);
            setTempSelectedUnits(Array.from(parking));
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

        const fechaCheck = `${fechaPeriodo}-01`;

        try {
            setLoading(true);
            const check = await phService.checkFacturacionMasiva(fechaCheck);
            setLoading(false);

            if (check.existe) {
                setWarningData({ cantidad: check.cantidad });
                setShowWarningModal(true);
            } else {
                if (confirm(`¿Confirmas generar la facturación para el periodo ${fechaPeriodo}?`)) {
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
                await phService.deleteFacturacionMasiva(fechaPeriodo);
                await ejecutarGeneracion(true);
            } catch (err) {
                setLoading(false);
                alert("Error al eliminar facturas anteriores: " + (err.response?.data?.detail || err.message));
            }
        } else if (accion === 'APPEND') {
            ejecutarGeneracion(false);
        }
    };

    const ejecutarGeneracion = async (skipConfirm) => {
        setLoading(true);
        try {
            // PREPARAR CONFIGURACIÓN DE EXCEPCIONES PARA EL BACKEND
            // Formato Backend: [{ concepto_id: 1, unidades_ids: [10, 20] }]
            const configuracionPayload = Object.keys(conceptConfigs).map(cId => ({
                concepto_id: parseInt(cId),
                unidades_ids: conceptConfigs[cId]
            })).filter(c => c.unidades_ids.length > 0); // Solo enviar si tiene unidades seleccionadas

            const data = await phService.generarFacturacionMasiva(
                fechaRegistro,
                selectedConceptos,
                configuracionPayload
            );

            setResultado(data);
            loadHistorial();
        } catch (err) {
            setError(err.response?.data?.detail || 'Error crítico al generar facturación.');
        } finally {
            setLoading(false);
        }
    };

    // ... (El resto de funciones auxiliares como handleDownloadPDF, handleDeleteFromHistory, handleVerDetalle se mantienen iguales)
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
            alert("Error cargando detalle: " + (error.response?.data?.detail || error.message));
            setShowDetailModal(false);
        } finally {
            setLoadingDetalle(false);
        }
    };

    if (authLoading) return <div className="p-10 text-center text-gray-500">Cargando módulo...</div>;

    // Unidades filtradas para el modal
    const filteredUnits = unidades.filter(u =>
        u.codigo.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (u.propietario?.razon_social || '').toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans pb-24">
            <div className="max-w-6xl mx-auto">
                {/* HEADER */}
                <div className="mb-8">
                    <div className="flex justify-between items-start">
                        <div className="flex items-center gap-3 mt-4">
                            <div className="p-3 bg-gradient-to-tr from-indigo-600 to-purple-600 rounded-xl text-white shadow-lg">
                                <FaFileInvoiceDollar className="text-3xl" />
                            </div>
                            <div>
                                <h1 className="text-3xl font-extrabold text-gray-800 tracking-tight">Facturación Masiva</h1>
                                <p className="text-gray-500 font-medium">Generación y causación de cuotas de {labels.module.toLowerCase()}.</p>
                            </div>
                        </div>
                        <div className="mt-4">
                            <ManualButton 
                                manualPath="facturacion.html"
                                title="Manual de Facturación Masiva"
                                position="header"
                            />
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
                                    <input type="month" value={fechaPeriodo} onChange={(e) => setFechaPeriodo(e.target.value)}
                                        className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none font-bold text-gray-700" />
                                </div>
                                <div>
                                    <label className="block text-sm font-bold text-gray-700 mb-2">Fecha de Registro Contable</label>
                                    <input type="date" value={fechaRegistro} onChange={(e) => setFechaRegistro(e.target.value)}
                                        className="w-full px-4 py-3 bg-indigo-50 border border-indigo-100 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none font-bold text-indigo-800" />
                                </div>
                            </div>
                        </div>

                        {/* 2. SELECCIÓN DE CONCEPTOS (GRID) */}
                        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-2 text-indigo-700 font-bold uppercase text-xs tracking-wider">
                                    <FaList /> Paso 2: Seleccionar Conceptos
                                </div>
                                <button onClick={toggleAll} className="text-xs font-bold text-indigo-600 hover:text-indigo-800 flex items-center gap-1 bg-indigo-50 px-3 py-1 rounded-full">
                                    {selectedConceptos.length === conceptos.length ? <FaCheckSquare /> : <FaRegSquare />}
                                    {selectedConceptos.length === conceptos.length ? 'Deseleccionar Todos' : 'Seleccionar Todos'}
                                </button>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[500px] overflow-y-auto p-1">
                                {conceptos.length === 0 && <p className="text-sm text-gray-400 italic">No hay conceptos configurados.</p>}

                                {conceptos.map(c => {
                                    const isSelected = selectedConceptos.includes(c.id);
                                    const exceptions = conceptConfigs[c.id] || [];
                                    const hasExceptions = exceptions.length > 0;

                                    return (
                                        <div key={c.id} onClick={() => toggleConcepto(c.id)}
                                            className={`relative p-4 rounded-xl border-2 cursor-pointer transition-all duration-200 group
                                                ${isSelected ? 'border-indigo-600 bg-indigo-50 shadow-md' : 'border-gray-100 bg-white hover:border-indigo-200'}
                                            `}
                                        >
                                            <div className="flex items-start justify-between">
                                                <div className="flex-1">
                                                    <div className="flex items-center gap-2">
                                                        <h4 className={`font-bold text-sm ${isSelected ? 'text-indigo-900' : 'text-gray-700'}`}>{c.nombre}</h4>
                                                        {hasExceptions && (
                                                            <span className="bg-red-100 text-red-700 text-[10px] px-2 py-0.5 rounded-full font-bold flex items-center gap-1">
                                                                <FaFilter /> SOLO {exceptions.length} UNIDADES
                                                            </span>
                                                        )}
                                                    </div>

                                                    <div className="flex flex-wrap gap-2 mt-2">
                                                        <span className={`text-[10px] px-2 py-0.5 rounded-md font-medium ${isSelected ? 'bg-indigo-200 text-indigo-800' : 'bg-gray-100 text-gray-500'}`}>
                                                            {c.usa_coeficiente ? labels.coeficiente : 'Valor Fijo'}
                                                        </span>
                                                        <span className="text-[10px] px-2 py-0.5 rounded-md bg-green-100 text-green-700 font-mono">
                                                            ${parseFloat(c.valor_defecto).toLocaleString()}
                                                        </span>
                                                    </div>
                                                </div>

                                                <div className="flex flex-col items-center gap-2">
                                                    <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors
                                                        ${isSelected ? 'bg-indigo-600 border-indigo-600 text-white' : 'border-gray-300 bg-gray-50'}
                                                    `}>
                                                        {isSelected && <FaCheckCircle className="text-sm" />}
                                                    </div>

                                                    {/* BOTÓN FILTRO */}
                                                    <button
                                                        onClick={(e) => openUnitFilter(e, c.id)}
                                                        className={`p-2 rounded-lg text-xs transition-colors z-10
                                                            ${hasExceptions
                                                                ? 'bg-red-100 text-red-600 hover:bg-red-200'
                                                                : 'bg-gray-100 text-gray-400 hover:bg-indigo-100 hover:text-indigo-600'}
                                                        `}
                                                        title="Filtrar Unidades (Cobrar solo a específicos)"
                                                    >
                                                        <FaFilter />
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>

                        {/* MENSAJES DE ERROR / RESULTADO */}
                        {error && (
                            <div className="p-4 bg-red-50 text-red-700 rounded-xl border border-red-200 flex items-center gap-3 animate-fadeIn">
                                <FaExclamationTriangle className="text-xl shrink-0" />
                                <div><p className="font-bold">Error en el proceso</p><p className="text-sm">{error}</p></div>
                            </div>
                        )}

                        {resultado && (
                            <div className="p-6 bg-emerald-50 text-emerald-800 rounded-xl border border-emerald-200 animate-slideUp relative overflow-hidden">
                                <h3 className="text-lg font-bold flex items-center gap-2 mb-4"><FaCheckCircle /> Proceso Finalizado Exitosamente</h3>
                                <div className="grid grid-cols-2 gap-4 mb-4 relative z-10">
                                    <div className="bg-white/60 p-3 rounded-lg"><p className="text-2xl font-bold">{resultado.generadas}</p><p className="text-xs uppercase font-bold opacity-70">Facturas</p></div>
                                    <div className="bg-white/60 p-3 rounded-lg"><p className="text-2xl font-bold text-red-600">{resultado.errores}</p><p className="text-xs uppercase font-bold opacity-70 text-red-600">Errores</p></div>
                                </div>
                                <div className="max-h-40 overflow-y-auto text-xs font-mono bg-white/50 p-2 rounded relative z-10">
                                    {resultado.detalles.map((d, i) => <div key={i}>{d}</div>)}
                                </div>
                            </div>
                        )}

                        {/* BOTÓN EJECUTAR */}
                        <button onClick={handlePreGenerate} disabled={loading}
                            className={`w-full py-5 rounded-2xl font-extrabold text-lg shadow-xl shadow-indigo-200 flex items-center justify-center gap-3 transition-all transform hover:scale-[1.02] active:scale-95
                                ${loading ? 'bg-gray-300 text-gray-500 cursor-not-allowed' : 'bg-indigo-600 text-white hover:bg-indigo-700 hover:shadow-indigo-300'}
                            `}
                        >
                            {loading ? <span>Procesando...</span> : <><FaPlay /> EJECUTAR LIQUIDACIÓN</>}
                        </button>
                    </div>

                    {/* HISTORIAL */}
                    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                        <div className="p-6 bg-gray-50 border-b border-gray-100 flex items-center gap-2">
                            <FaHistory className="text-gray-500 text-xl" />
                            <h3 className="font-bold text-gray-800 text-lg">Historial de Facturaciones</h3>
                        </div>
                        <div className="max-h-[500px] overflow-y-auto">
                            {historial.map((h, i) => (
                                <div key={i} className="flex items-center justify-between p-4 border-b border-gray-100 hover:bg-gray-50">
                                    <div>
                                        <p className="font-bold text-indigo-900">{h.periodo}</p>
                                        <span className="text-xs text-gray-500">{h.cantidad} Documentos</span>
                                    </div>
                                    <div className="text-right">
                                        <p className="font-bold">${parseFloat(h.total).toLocaleString()}</p>
                                        <div className="flex gap-2 mt-1 justify-end">
                                            <button onClick={() => handleVerDetalle(h.periodo)} className="text-indigo-600 text-xs font-bold hover:underline"><FaEye /> Ver Detalle</button>
                                            <button onClick={() => handleDeleteFromHistory(h.periodo)} className="text-red-500 text-xs hover:text-red-700"><FaTrash /></button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* MODAL ADVERTENCIA REGENERACIÓN */}
                {showWarningModal && (
                    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                        <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
                            <h3 className="text-xl font-bold mb-4">Periodo ya Liquidado</h3>
                            <button onClick={() => handleModalOption('DELETE_AND_REGENERATE')} className="w-full py-3 bg-red-600 text-white rounded-xl font-bold mb-2">Borrar y Regenerar</button>
                            <button onClick={() => handleModalOption('APPEND')} className="w-full py-3 bg-indigo-100 text-indigo-700 rounded-xl font-bold mb-2">Completar (Delta)</button>
                            <button onClick={() => handleModalOption('CANCEL')} className="w-full py-3 text-gray-500">Cancelar</button>
                        </div>
                    </div>
                )}

                {/* MODAL SELECCION UNIDADES */}
                {showUnitModal && (
                    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fadeIn">
                        <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl h-[80vh] flex flex-col">
                            <div className="p-4 border-b flex justify-between items-center bg-gray-50 rounded-t-2xl">
                                <h3 className="font-bold text-lg text-gray-800">Filtrar Unidades para Concepto</h3>
                                <button onClick={() => setShowUnitModal(false)}><FaTimes /></button>
                            </div>

                            <div className="p-4 border-b bg-white">
                                <div className="relative">
                                    <FaSearch className="absolute left-3 top-3 text-gray-400" />
                                    <input
                                        type="text"
                                        placeholder="Buscar por código o propietario..."
                                        className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                        value={searchTerm}
                                        onChange={(e) => setSearchTerm(e.target.value)}
                                    />
                                </div>
                                <div className="mt-2 flex justify-between text-sm">
                                    <span className="text-indigo-600 font-bold">{tempSelectedUnits.length} Unidades Seleccionadas</span>
                                    {tempSelectedUnits.length > 0 &&
                                        <button onClick={() => setTempSelectedUnits([])} className="text-red-500 text-xs hover:underline">Limpiar Selección</button>
                                    }
                                </div>
                            </div>

                            {/* FILTRO POR TORRES (NUEVO) */}
                            {torres.length > 0 && (
                                <div className="p-3 bg-white border-b overflow-x-auto">
                                    <div className="flex gap-2 min-w-max">
                                        <span className="text-xs font-bold text-gray-500 uppercase tracking-wider py-1">Agrupar por:</span>
                                        {torres.map(t => {
                                            // Calcular si está "full", "partial" o "none"
                                            const unitsInTower = unidades.filter(u => u.torre_id === t.id).map(u => u.id);
                                            const selectedInTower = unitsInTower.filter(uid => tempSelectedUnits.includes(uid));

                                            let statusClass = "bg-gray-100 text-gray-600 border-gray-200";
                                            let icon = <FaRegSquare className="text-gray-400" />;

                                            if (unitsInTower.length > 0) {
                                                if (selectedInTower.length === unitsInTower.length) {
                                                    statusClass = "bg-indigo-100 text-indigo-700 border-indigo-200 font-bold";
                                                    icon = <FaCheckSquare className="text-indigo-600" />;
                                                } else if (selectedInTower.length > 0) {
                                                    statusClass = "bg-indigo-50 text-indigo-600 border-indigo-200 border-dashed";
                                                    icon = <div className="w-3 h-3 bg-indigo-500 rounded-sm"></div>; // Indeterminate look
                                                }
                                            }

                                            return (
                                                <button
                                                    key={t.id}
                                                    onClick={() => handleToggleTower(t.id)}
                                                    className={`px-3 py-1 rounded-full text-xs border flex items-center gap-2 transition-all hover:scale-105 active:scale-95 ${statusClass}`}
                                                    title={`Seleccionar toda la ${t.nombre}`}
                                                >
                                                    {icon}
                                                    {t.nombre}
                                                    <span className="opacity-60 text-[10px]">({selectedInTower.length}/{unitsInTower.length})</span>
                                                </button>
                                            );
                                        })}
                                    </div>
                                </div>
                            )}

                            <div className="flex-1 overflow-y-auto p-2 bg-gray-50">
                                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                                    {filteredUnits.length === 0 ? <p className="col-span-3 text-center text-gray-400 py-10">No se encontraron unidades.</p> :
                                        filteredUnits.map(u => (
                                            <div key={u.id}
                                                onClick={() => toggleUnitSelection(u.id)}
                                                className={`p-3 rounded-lg border cursor-pointer text-sm flex items-center gap-2 hover:shadow-sm transition-all
                                                ${tempSelectedUnits.includes(u.id) ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-white border-gray-200 text-gray-700'}
                                            `}
                                            >
                                                <div className={`w-4 h-4 rounded border flex items-center justify-center shrink-0
                                                ${tempSelectedUnits.includes(u.id) ? 'bg-white border-white' : 'border-gray-400'}
                                            `}>
                                                    {tempSelectedUnits.includes(u.id) && <FaCheckCircle className="text-indigo-600 text-xs" />}
                                                </div>
                                                <div className="overflow-hidden">
                                                    <div className="font-bold truncate">{u.codigo}</div>
                                                    <div className={`text-[10px] truncate ${tempSelectedUnits.includes(u.id) ? 'text-indigo-100' : 'text-gray-400'}`}>
                                                        {u.propietario?.razon_social || 'Sin Propietario'}
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                </div>
                            </div>

                            <div className="p-4 border-t bg-white rounded-b-2xl flex justify-end gap-3">
                                <button onClick={(e) => clearUnitFilter(e, currentConceptId)} className="px-4 py-2 text-red-500 hover:bg-red-50 rounded-lg">Quitar Filtro (Cobrar a Todos)</button>
                                <button onClick={saveUnitFilter} className="px-6 py-2 bg-indigo-600 text-white font-bold rounded-lg hover:bg-indigo-700 shadow-lg shadow-indigo-200">
                                    Aplicar Filtro
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* MODAL DETALLE FACTURAS (Reutilizado) */}
                {showDetailModal && (
                    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-6">
                        <div className="bg-white rounded-2xl shadow-2xl w-full max-w-5xl h-[80vh] flex flex-col overflow-hidden">
                            <div className="p-6 bg-indigo-600 text-white flex justify-between items-center shrink-0">
                                <h3 className="text-xl font-bold flex items-center gap-2"><FaFileInvoiceDollar /> Detalle</h3>
                                <div className="flex gap-2">
                                    <button onClick={handleDownloadPDF} className="bg-white/20 px-3 py-1 rounded text-sm hover:bg-white/30 flex items-center gap-1"><FaFilePdf /> PDF</button>
                                    <button onClick={() => setShowDetailModal(false)}><FaTimes /></button>
                                </div>
                            </div>
                            <div className="flex-1 overflow-y-auto p-4">
                                {loadingDetalle ? <p className="text-center p-10">Cargando...</p> :
                                    <table className="w-full text-sm">
                                        <thead className="bg-gray-100 text-left">
                                            <tr><th className="p-2">Factura</th><th className="p-2">Fecha</th><th className="p-2">Tercero</th><th className="p-2 text-right">Total</th><th className="p-2 text-center">Estado</th></tr>
                                        </thead>
                                        <tbody>
                                            {detalleFacturas.map(f => (
                                                <tr key={f.id} className="border-b">
                                                    <td className="p-2 font-mono text-indigo-600 font-bold">{f.consecutivo}</td>
                                                    <td className="p-2">{f.fecha}</td>
                                                    <td className="p-2">{f.tercero_nombre} <span className="text-xs text-gray-400">({f.detalle})</span></td>
                                                    <td className="p-2 text-right font-bold">${parseFloat(f.total).toLocaleString()}</td>
                                                    <td className="p-2 text-center"><span className="badge badge-sm">{f.estado}</span></td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                }
                            </div>
                        </div>
                    </div>
                )}

            </div>
        </div>
    );
}
