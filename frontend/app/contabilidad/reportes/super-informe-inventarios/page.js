// frontend/app/contabilidad/reportes/super-informe-inventarios/page.js
'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useSearchParams } from 'next/navigation';
import { useAuth } from '@/app/context/AuthContext';

import Paginacion from '@/app/components/ui/Paginacion';
import { FaTable, FaFilter, FaSearch, FaEraser, FaFilePdf, FaChevronDown, FaChevronUp } from 'react-icons/fa';
import { useAutoReport } from '@/hooks/useAutoReport';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import Select, { components } from 'react-select';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import {
    FaBook,
} from 'react-icons/fa';

// --- Servicios (Lógica Intacta) ---
import { getGruposInventario } from '@/lib/inventarioService';
import { getBodegas } from '@/lib/bodegaService';
import { getSuperInformeInventarios, generarPdfDirectoSuperInforme } from '@/lib/reportesInventarioService';
import { getTerceros } from '@/lib/terceroService';

// =============================================================================
// 🎨 COMPONENTE "ANTI-CHORRERO" (Estándar v2.0)
// =============================================================================
const CustomValueContainer = ({ children, ...props }) => {
    const selectedCount = props.getValue().length;
    if (selectedCount > 1) {
        return (
            <components.ValueContainer {...props}>
                <div className="flex items-center px-2">
                    <span className="inline-flex items-center gap-1 bg-indigo-50 text-indigo-700 text-xs font-bold px-2 py-1 rounded-md border border-indigo-100">
                        <FaCheckCircle className="text-indigo-500" /> {selectedCount} SELECCIONADOS
                    </span>
                </div>
                {React.Children.map(children, child =>
                    child && child.type && child.type.name === 'Input' ? child : null
                )}
            </components.ValueContainer>
        );
    }
    return <components.ValueContainer {...props}>{children}</components.ValueContainer>;
};

// --- Estilos Compartidos React-Select v2.0 ---
const customSelectStyles = {
    control: (base, state) => ({
        ...base,
        minHeight: '2.5rem', // 40px standard
        borderRadius: '0.5rem', // rounded-lg
        borderColor: state.isFocused ? '#6366f1' : '#d1d5db', // indigo-500 : gray-300
        boxShadow: state.isFocused ? '0 0 0 2px rgba(99, 102, 241, 0.2)' : '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        '&:hover': { borderColor: state.isFocused ? '#6366f1' : '#9ca3af' },
        fontSize: '0.875rem', // text-sm
    }),
    menu: (base) => ({ ...base, borderRadius: '0.5rem', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)', zIndex: 50 }),
    option: (base, state) => ({
        ...base,
        backgroundColor: state.isSelected ? '#4f46e5' : state.isFocused ? '#f3f4f6' : 'white',
        color: state.isSelected ? 'white' : '#374151',
        fontSize: '0.875rem',
        cursor: 'pointer',
    }),
    multiValue: (base) => ({ ...base, backgroundColor: '#e0e7ff', borderRadius: '0.25rem' }),
    multiValueLabel: (base) => ({ ...base, color: '#4338ca', fontWeight: 600 }),
    multiValueRemove: (base) => ({ ...base, color: '#4338ca', ':hover': { backgroundColor: '#c7d2fe', color: '#312e81' } }),
};

// --- Funciones de Formato ---
const formatCurrency = (value) => {
    const number = parseFloat(value);
    if (isNaN(number)) return '$ 0';
    return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(number);
};
const formatQuantity = (value) => {
    const number = parseFloat(value);
    if (isNaN(number)) return '0';
    return new Intl.NumberFormat('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 2 }).format(number);
};
const formatDateForAPI = (date) => {
    if (!date) return null;
    const utcDate = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
    return utcDate.toISOString().split('T')[0];
};

const INITIAL_FILTROS_STATE = {
    vista_reporte: 'MOVIMIENTOS',
    fecha_inicio: new Date(new Date().getFullYear(), 0, 1),
    fecha_fin: new Date(),
    bodega_ids: [],
    grupo_ids: [],
    producto_ids: [],
    tercero_id: '',
    search_term_doc: '',
    search_term_prod: '',
    pagina: 1,
    traerTodo: false,
};

const vistaOptions = [
    { value: 'MOVIMIENTOS', label: 'Movimientos Detallados' },
];

export default function SuperInformeInventariosPage() {
    const { user, authLoading } = useAuth();

    // --- Estados de Datos ---
    const [filtros, setFiltros] = useState(INITIAL_FILTROS_STATE);
    const [maestros, setMaestros] = useState({ bodegas: [], grupos: [], terceros: [], productos: [] });
    const [resultados, setResultados] = useState([]);
    const [totales, setTotales] = useState(null);
    const [dynamicHeaders, setDynamicHeaders] = useState([]);
    const [pagination, setPagination] = useState({ total_registros: 0, total_paginas: 1, pagina_actual: 1 });

    // --- Estados de UI ---
    const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
    const [isLoadingMaestros, setIsLoadingMaestros] = useState(true);
    const [isSearching, setIsSearching] = useState(false);
    const [error, setError] = useState(null);

    // --- AUTOMATIZACIÓN (HOOK UNIFICADO) ---
    // --- AUTOMATIZACIÓN (HOOK UNIFICADO) ---
    // Este hook maneja la detección de URL (ai_email, ai_accion) y el disparo de acciones
    // Nota: Pasamos una función anónima a handleExportPDF para evitar problemas de referencia temprana, 
    // aunque idealmente handleExportPDF debería definirse antes o usar hoisting.
    // Como handleExportPDF es const (no hoisting), usamos una referencia mutable o un wrapper.
    const { triggerAutoDispatch } = useAutoReport('super_informe_inventarios', () => handleExportPDF());

    // Efecto para activar el despacho automático cuando lleguen resultados
    useEffect(() => {
        if (resultados && resultados.length > 0 && !isSearching) {
            triggerAutoDispatch(filtros);
        }
    }, [resultados, isSearching, filtros, triggerAutoDispatch]);


    // --- Carga de Maestros ---
    useEffect(() => {
        const fetchMaestros = async () => {
            if (!user?.empresaId) return;
            setIsLoadingMaestros(true);
            setError(null);
            try {
                const [bodegasRes, gruposRes, tercerosRes] = await Promise.allSettled([
                    getBodegas(), getGruposInventario(), getTerceros(),
                ]);
                const mapResult = (result, mapper) => (result.status === 'fulfilled' && result.value ? (Array.isArray(result.value) ? result.value.map(mapper) : (result.value.items || []).map(mapper)) : []);

                setMaestros({
                    bodegas: mapResult(bodegasRes, b => ({ value: b.id, label: b.nombre })),
                    grupos: mapResult(gruposRes, g => ({ value: g.id, label: g.nombre })),
                    terceros: mapResult(tercerosRes, t => ({ value: t.id, label: `(${t.nit || 'N/A'}) ${t.razon_social}` })),
                    productos: [],
                });
            } catch (err) {
                console.error("Error crítico cargando maestros:", err);
                setError("No se pudieron cargar los datos maestros.");
                toast.error("Error cargando filtros.");
            } finally {
                setIsLoadingMaestros(false);
            }
        };
        if (user?.empresaId && !authLoading) fetchMaestros();
    }, [user, authLoading]);

    // --- Handlers ---
    const searchParams = useSearchParams();

    // AI SEARCH EFFECT
    useEffect(() => {
        if (isLoadingMaestros) return;
        const trigger = searchParams.get('trigger');

        if (trigger === 'ai_search') {
            const newFiltros = { ...INITIAL_FILTROS_STATE };
            let changed = false;

            if (searchParams.get('fecha_inicio')) { newFiltros.fecha_inicio = new Date(searchParams.get('fecha_inicio') + 'T00:00:00'); changed = true; }
            if (searchParams.get('fecha_fin')) { newFiltros.fecha_fin = new Date(searchParams.get('fecha_fin') + 'T00:00:00'); changed = true; }
            if (searchParams.get('search_term_prod')) { newFiltros.search_term_prod = searchParams.get('search_term_prod'); changed = true; }
            if (searchParams.get('search_term_doc')) { newFiltros.search_term_doc = searchParams.get('search_term_doc'); changed = true; }

            // --- AI TERCERO MAPPING ---
            const aiTercero = searchParams.get('ai_tercero');

            if (aiTercero && maestros.terceros.length > 0) {
                const normalize = s => s.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
                const target = normalize(aiTercero);

                const bestMatch = maestros.terceros.find(t => {
                    const label = normalize(t.label || '');
                    return label.includes(target);
                });

                if (bestMatch) {
                    newFiltros.tercero_id = bestMatch.value;
                    changed = true;
                }
            }

            // --- AI BODEGA MAPPING ---
            const aiBodega = searchParams.get('ai_bodega');
            if (aiBodega && maestros.bodegas.length > 0) {
                const normalize = s => s.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
                const target = normalize(aiBodega);

                const bestMatch = maestros.bodegas.find(b => normalize(b.label || '').includes(target));
                if (bestMatch) {
                    newFiltros.bodega_ids = [bestMatch.value];
                    changed = true;
                }
            }

            // --- AI GRUPO MAPPING ---
            const aiGrupo = searchParams.get('ai_grupo');
            if (aiGrupo && maestros.grupos.length > 0) {
                const normalize = s => s.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
                const target = normalize(aiGrupo);

                const bestMatch = maestros.grupos.find(g => normalize(g.label || '').includes(target));
                if (bestMatch) {
                    newFiltros.grupo_ids = [bestMatch.value];
                    changed = true;
                }
            }



            setFiltros(newFiltros); // Apply filters


            // TRIGGER SEARCH UI
            setTimeout(() => {
                const btn = document.getElementById('btn-inventario-search');
                if (btn) btn.click();
            }, 500);
        }
    }, [searchParams, maestros, isLoadingMaestros]);

    // --- AUTO PDF/EMAIL EXECUTION EFFECT ---


    const handleFiltroChange = (e) => {
        const { name, value } = e.target;
        setFiltros(prev => ({ ...prev, [name]: value, ...(name !== 'pagina' && { pagina: 1 }) }));
    };

    const handleDateChange = (name, date) => {
        setFiltros(prev => ({ ...prev, [name]: date, pagina: 1 }));
    };

    const handleMultiSelectChange = (name, selectedOptions) => {
        const values = selectedOptions ? selectedOptions.map(option => option.value) : [];
        setFiltros(prev => ({ ...prev, [name]: values, pagina: 1 }));
    };

    const handleVistaChange = (e) => {
        setFiltros(prev => ({ ...prev, vista_reporte: e.target.value, pagina: 1 }));
        setResultados([]); setTotales(null); setDynamicHeaders([]);
    };

    const handleLimpiarFiltros = () => {
        setFiltros(INITIAL_FILTROS_STATE);
        setResultados([]); setTotales(null);
        toast.info("Filtros limpiados.");
    };

    const handleSearch = useCallback(async (pagina = 1) => {
        setIsSearching(true); setError(null);
        if (pagina === 1) { setResultados([]); setTotales(null); setDynamicHeaders([]); }

        const payload = {
            vista_reporte: filtros.vista_reporte,
            fecha_inicio: formatDateForAPI(filtros.fecha_inicio),
            fecha_fin: formatDateForAPI(filtros.fecha_fin),
            bodega_ids: filtros.bodega_ids.length > 0 ? filtros.bodega_ids : null,
            grupo_ids: filtros.grupo_ids.length > 0 ? filtros.grupo_ids : null,
            producto_ids: filtros.producto_ids.length > 0 ? filtros.producto_ids : null,
            tercero_id: filtros.tercero_id ? parseInt(filtros.tercero_id) : null,
            search_term_doc: filtros.search_term_doc || null,
            search_term_prod: filtros.search_term_prod || null,
            pagina: pagina,
            traerTodo: filtros.traerTodo,
        };

        // Limpieza de payload
        Object.keys(payload).forEach(key => {
            if (payload[key] === null || payload[key] === '' || (Array.isArray(payload[key]) && payload[key].length === 0)) delete payload[key];
        });
        if (!payload.traerTodo) delete payload.traerTodo;

        try {
            const data = await getSuperInformeInventarios(payload);
            if (data && Array.isArray(data.items)) {
                if (data.items.length > 0) {
                    setResultados(data.items);
                    setTotales(data.totales || null);
                    setPagination(data.paginacion || { total_registros: data.items.length, total_paginas: 1, pagina_actual: 1 });

                    let headers = [];
                    if (data.vista_reporte === 'MOVIMIENTOS') {
                        headers = Object.keys(data.items[0]).filter(k => k !== 'movimiento_id');
                    } else {
                        headers = ["producto_codigo", "producto_nombre", "saldo_inicial_cantidad", "saldo_inicial_valor", "total_entradas_cantidad", "total_entradas_valor", "total_salidas_cantidad", "total_salidas_valor", "saldo_final_cantidad", "saldo_final_valor"];
                    }
                    setDynamicHeaders(headers);
                    toast.success(`Informe generado con ${data.items.length} ítems.`);
                } else {
                    setResultados([]); setTotales(null);
                    setPagination({ total_registros: 0, total_paginas: 1, pagina_actual: 1 });
                    setDynamicHeaders([]);
                    toast.info('No se encontraron resultados.');
                }
            } else {
                setError('Respuesta inesperada del servidor.'); toast.error('Error en respuesta.');
                setResultados([]); setTotales(null);
            }
        } catch (err) {
            const errorMsg = err.response?.data?.detail || err.message || 'Error al buscar.';
            setError(errorMsg); toast.error(errorMsg);
            setResultados([]); setTotales(null);
        } finally {
            setIsSearching(false);
        }
    }, [filtros]);

    const handleExportPDF = useCallback(async () => {
        if (isSearching) return;
        toast.info("Generando PDF...", { autoClose: 3000, toastId: 'pdf-pending' });

        const filtrosPDF = { ...filtros, traerTodo: true, pagina_actual: 1, items_por_pagina: 99999 };
        const payload = {};
        for (const key in filtrosPDF) {
            let value = filtrosPDF[key];
            if (value === null || value === '' || (Array.isArray(value) && value.length === 0)) value = null;
            if (value === null) continue;
            if (['tercero_id'].includes(key) && value !== null) value = parseInt(value);
            if (key === 'fecha_inicio' || key === 'fecha_fin') value = formatDateForAPI(value);
            if (key === 'traerTodo') payload[key] = true; else payload[key] = value;
        }

        try {
            await generarPdfDirectoSuperInforme(payload);
            toast.success("Descarga iniciada.", { toastId: 'pdf-pending' });
        } catch (error) {
            const errorMessage = error.response?.data?.detail || "Error al generar PDF.";
            toast.error(errorMessage, { toastId: 'pdf-pending' });
        }
    }, [filtros, isSearching]);

    // --- Renderizado Celdas ---
    const renderCellContent = (item, headerKeyOrIndex) => {
        try {
            const key = dynamicHeaders[headerKeyOrIndex];
            const value = item[key];
            if (key === 'fecha') return value ? new Date(value).toLocaleDateString('es-CO') : 'N/A';
            if (['cantidad', 'costo_unitario', 'costo_total', 'saldo_final_cantidad', 'total_entradas_cantidad', 'total_salidas_cantidad'].includes(key)) return formatQuantity(value);
            if (['total_venta', 'total_costo', 'total_utilidad', 'saldo_inicial_valor', 'saldo_final_valor', 'total_entradas_valor', 'total_salidas_valor'].includes(key)) return formatCurrency(value);

            return value ?? 'N/A';
        } catch (e) { return "Error"; }
    };

    // --- Clases Estándar v2.0 ---
    const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
    const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white";

    if (authLoading || isLoadingMaestros) {
        return (
            <div className="min-h-screen bg-gray-50 flex justify-center items-center">
                <span className="loading loading-spinner loading-lg text-indigo-600"></span>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
            <div className="max-w-7xl mx-auto">

                <ToastContainer position="top-right" autoClose={3000} />

                {/* 1. ENCABEZADO */}
                <div className="flex justify-between items-center mb-8">
                    <div className="flex items-center gap-3">
                        <div className="p-3 bg-indigo-100 text-indigo-600 rounded-xl shadow-sm">
                            <FaTable className="text-2xl" />
                        </div>
                        <div>
                            <div className="flex items-center gap-4">
                                <h1 className="text-3xl font-bold text-gray-800 tracking-tight">Super Informe Inventarios</h1>
                                <button
                                    onClick={() => window.open('/manual/capitulo_47_super_informe_inventarios.html', '_blank')}
                                    className="flex items-center gap-2 px-2 py-1 bg-white border border-indigo-200 text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors font-medium shadow-sm"
                                    type="button"
                                    title="Ver Manual de Usuario"
                                >
                                    <span className="text-lg">📖</span> <span className="font-bold text-sm hidden md:inline">Manual</span>
                                </button>
                            </div>
                            <p className="text-gray-500 text-sm mt-1">Análisis detallado de movimientos, costos y rentabilidad.</p>
                        </div>
                    </div>
                </div>

                {/* 2. CARD DE FILTROS */}
                <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 mb-8 animate-fadeIn">
                    <form onSubmit={(e) => { e.preventDefault(); handleSearch(1); }}>

                        {/* Nivel 1: Filtros Esenciales */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                            <div>
                                <label className={labelClass}>Vista del Reporte</label>
                                <select name="vista_reporte" value={filtros.vista_reporte} onChange={handleVistaChange} className={`${inputClass} font-semibold text-indigo-700 bg-indigo-50/50 border-indigo-200`}>
                                    {vistaOptions.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                                </select>
                            </div>
                            <div>
                                <label className={labelClass}>Fecha Inicio</label>
                                <DatePicker selected={filtros.fecha_inicio} onChange={(date) => handleDateChange('fecha_inicio', date || new Date())} selectsStart startDate={filtros.fecha_inicio} endDate={filtros.fecha_fin} dateFormat="dd/MM/yyyy" className={inputClass} />
                            </div>
                            <div>
                                <label className={labelClass}>Fecha Fin</label>
                                <DatePicker selected={filtros.fecha_fin} onChange={(date) => handleDateChange('fecha_fin', date || new Date())} selectsEnd startDate={filtros.fecha_inicio} endDate={filtros.fecha_fin} minDate={filtros.fecha_inicio} dateFormat="dd/MM/yyyy" className={inputClass} />
                            </div>
                        </div>

                        {/* Nivel 2: Filtros Avanzados (Acordeón) */}
                        <div className="border-t border-gray-100 pt-4">
                            <button
                                type="button"
                                onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                                className="flex items-center text-sm font-bold text-indigo-600 hover:text-indigo-800 focus:outline-none transition-colors group"
                            >
                                <span className="bg-indigo-50 p-1.5 rounded-md mr-2 group-hover:bg-indigo-100 transition-colors">
                                    <FaFilter />
                                </span>
                                {showAdvancedFilters ? 'Ocultar Filtros Avanzados' : 'Filtrar por Bodega, Grupo, Producto...'}
                                {showAdvancedFilters ? <FaChevronUp className="ml-1" /> : <FaChevronDown className="ml-1" />}
                            </button>

                            {showAdvancedFilters && (
                                <div className="mt-6 bg-gray-50 p-6 rounded-xl border border-gray-100 animate-slideDown grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                    {/* Bodegas */}
                                    <div>
                                        <label className={labelClass}>Bodegas</label>
                                        <Select
                                            isMulti name="bodega_ids" options={maestros.bodegas}
                                            placeholder="Todas las bodegas"
                                            onChange={(opts) => handleMultiSelectChange('bodega_ids', opts)}
                                            value={maestros.bodegas.filter(option => filtros.bodega_ids.includes(option.value))}
                                            components={{ ValueContainer: CustomValueContainer }}
                                            styles={customSelectStyles}
                                        />
                                    </div>
                                    {/* Grupos */}
                                    <div>
                                        <label className={labelClass}>Grupos</label>
                                        <Select
                                            isMulti name="grupo_ids" options={maestros.grupos}
                                            placeholder="Todos los grupos"
                                            onChange={(opts) => handleMultiSelectChange('grupo_ids', opts)}
                                            value={maestros.grupos.filter(option => filtros.grupo_ids.includes(option.value))}
                                            components={{ ValueContainer: CustomValueContainer }}
                                            styles={customSelectStyles}
                                        />
                                    </div>
                                    {/* Tercero */}
                                    <div className="md:col-span-2 lg:col-span-1">
                                        <label className={labelClass}>Tercero</label>
                                        <Select
                                            name="tercero_id" options={maestros.terceros}
                                            placeholder="Todos los terceros"
                                            onChange={(opt) => handleFiltroChange({ target: { name: 'tercero_id', value: opt ? opt.value : '' } })}
                                            value={maestros.terceros.find(t => t.value == filtros.tercero_id)}
                                            components={{ ValueContainer: CustomValueContainer }}
                                            styles={customSelectStyles}
                                        />
                                    </div>
                                    <div className="md:col-span-2 lg:col-span-2">
                                        <label className={labelClass}>Ref. Documento</label>
                                        <input type="text" name="search_term_doc" placeholder="Número de factura..." value={filtros.search_term_doc} onChange={handleFiltroChange} className={inputClass} />
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Nivel 3: Búsqueda Producto (Visible Siempre) */}
                        <div className="mt-6">
                            <label className={labelClass}>Búsqueda Producto</label>
                            <div className="relative">
                                <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                                    <FaSearch />
                                </span>
                                <input type="text" name="search_term_prod" placeholder="Nombre del producto, código, referencia..." value={filtros.search_term_prod} onChange={handleFiltroChange} className={`${inputClass} pl-10`} />
                            </div>
                        </div>

                        {/* Botones de Acción */}
                        <div className="flex flex-col md:flex-row justify-between items-center mt-8 pt-6 border-t border-gray-100 gap-4">

                            {/* Izquierda: Limpieza */}
                            <button type="button" onClick={handleLimpiarFiltros} disabled={isSearching} className="btn btn-ghost btn-sm text-gray-500 hover:text-gray-800 hover:bg-gray-100 transition-colors">
                                <FaEraser className="mr-2" /> Limpiar Filtros
                            </button>

                            {/* Derecha: Acciones Principales */}
                            <div className="flex items-center gap-3">
                                {/* Checkbox "Traer Todo" Estilizado */}
                                <label className="flex items-center cursor-pointer mr-2 px-3 py-2 rounded-lg hover:bg-gray-50 border border-transparent hover:border-gray-200 transition-all">
                                    <input
                                        type="checkbox"
                                        checked={filtros.traerTodo}
                                        onChange={() => setFiltros(prev => ({ ...prev, traerTodo: !prev.traerTodo }))}
                                        className="checkbox checkbox-xs checkbox-primary mr-2"
                                    />
                                    <span className="text-sm font-semibold text-gray-600">Todo para PDF</span>
                                </label>

                                <button type="button" onClick={handleExportPDF} disabled={isSearching || resultados.length === 0} className="btn btn-outline border-red-500 text-red-600 hover:bg-red-50 hover:border-red-600 btn-sm gap-2 shadow-sm">
                                    <FaFilePdf /> Exportar PDF
                                </button>

                                <button type="submit" id="btn-inventario-search" disabled={isSearching || isLoadingMaestros} className="btn btn-primary px-6 py-2 shadow-md hover:shadow-lg transition-all transform hover:-translate-y-0.5 font-bold">
                                    <FaSearch className={`mr-2 ${isSearching ? 'animate-spin' : ''}`} />
                                    {isSearching ? 'Procesando...' : 'Generar Reporte'}
                                </button>
                            </div>
                        </div>
                    </form>
                </div>

                {/* 3. RESULTADOS */}
                {error && !isSearching && <div className="alert alert-error shadow-lg mb-6 rounded-xl text-white"><span>{error}</span></div>}

                {
                    resultados.length > 0 && !isSearching && (
                        <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden animate-fadeIn flex flex-col">
                            <div className="p-4 bg-gray-50 border-b border-gray-200 flex justify-between items-center">
                                <h2 className="text-sm font-bold text-gray-700 uppercase tracking-wide flex items-center gap-2">
                                    <FaTable className="text-gray-400" /> Resultados
                                </h2>
                                <span className="badge badge-primary badge-outline font-mono font-bold">
                                    {pagination.total_registros} Registros
                                </span>
                            </div>

                            <div className="overflow-x-auto max-h-[65vh]">
                                <table className="table table-sm w-full">
                                    <thead className="sticky top-0 z-20 shadow-sm">
                                        <tr>
                                            {dynamicHeaders.map(key => {
                                                // Mapping de labels para mantener la tabla compacta
                                                const labels = {
                                                    'tipo_documento': 'DOC', 'documento_ref': 'REF', 'tipo_documento_codigo': 'TIPO',
                                                    'producto_codigo': 'CÓDIGO', 'producto_nombre': 'PRODUCTO', 'tercero_nombre': 'TERCERO',
                                                    'bodega_nombre': 'BODEGA', 'tipo_movimiento': 'MOV', 'costo_unitario': 'COSTO UNIT',
                                                    'costo_total': 'COSTO TOTAL', 'cantidad': 'CANTIDAD'
                                                };
                                                const isNumeric = ['cantidad', 'costo_unitario', 'costo_total', 'saldo_final_cantidad', 'saldo_final_valor'].includes(key);

                                                return (
                                                    <th key={key} className={`py-3 px-4 text-xs font-bold text-gray-600 uppercase bg-slate-100 border-b border-gray-200 whitespace-nowrap ${isNumeric ? 'text-right' : 'text-left'}`}>
                                                        {labels[key] || key.replace(/_/g, ' ')}
                                                    </th>
                                                );
                                            })}
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-100">
                                        {resultados.map((item, index) => (
                                            <tr key={item.movimiento_id || index} className="hover:bg-gray-50 transition-colors duration-150">
                                                {dynamicHeaders.map((headerKey, cellIndex) => {
                                                    const isNumeric = ['cantidad', 'costo_unitario', 'costo_total', 'saldo_final_cantidad', 'saldo_final_valor'].includes(headerKey);
                                                    return (
                                                        <td key={`${item.movimiento_id || index}-${headerKey}`}
                                                            className={`py-2 px-4 text-sm whitespace-nowrap border-b border-gray-50 ${isNumeric ? 'text-right font-mono text-gray-800' : 'text-left text-gray-600'}`}>
                                                            {renderCellContent(item, cellIndex)}
                                                        </td>
                                                    );
                                                })}
                                            </tr>
                                        ))}
                                    </tbody>

                                    {/* FOOTER TOTALES (Estilo v2.0 Oscuro) */}
                                    {totales && filtros.vista_reporte === 'MOVIMIENTOS' && (
                                        <tfoot className="sticky bottom-0 z-20 shadow-inner">
                                            <tr className="bg-slate-800 text-white font-bold text-sm">
                                                {(() => {
                                                    const totalCantidad = totales.total_cantidad || 0;
                                                    const totalCosto = totales.total_costo || 0;
                                                    const cantidadColIndex = dynamicHeaders.indexOf('cantidad');
                                                    const costoTotalColIndex = dynamicHeaders.indexOf('costo_total');
                                                    const colSpan = cantidadColIndex !== -1 ? cantidadColIndex : 1;

                                                    return dynamicHeaders.map((key, index) => {
                                                        if (index === 0) return <td key="label" colSpan={colSpan} className="py-3 px-4 text-right uppercase tracking-wider bg-slate-800">TOTALES:</td>;
                                                        if (index < colSpan) return null; // Celdas absorbidas por el colSpan

                                                        if (index === cantidadColIndex) return <td key="tc" className="py-3 px-4 text-right font-mono bg-slate-800">{formatQuantity(totalCantidad)}</td>;
                                                        if (index === costoTotalColIndex) return <td key="tct" className="py-3 px-4 text-right font-mono bg-slate-800">{formatCurrency(totalCosto)}</td>;

                                                        return <td key={`empty-${index}`} className="bg-slate-800"></td>;
                                                    });
                                                })()}
                                            </tr>
                                        </tfoot>
                                    )}
                                </table>
                            </div>

                            {/* Paginación */}
                            {pagination.total_paginas > 1 && (
                                <div className="p-4 bg-gray-50 border-t border-gray-200 flex justify-center">
                                    <Paginacion
                                        paginaActual={pagination.pagina_actual}
                                        totalPaginas={pagination.total_paginas}
                                        onPageChange={(page) => handleSearch(page)}
                                    />
                                </div>
                            )}
                        </div>
                    )
                }
            </div >
        </div >
    );
}