'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import DatePicker from 'react-datepicker';
import Select, { components } from 'react-select';
import 'react-datepicker/dist/react-datepicker.css';
import { useAuth } from '../../../context/AuthContext';
import { 
    FaChartLine, FaSearch, FaTags, FaFileInvoice, 
    FaEye, FaMinusCircle, FaFilter, FaChevronDown, FaChevronUp, FaPrint,
    FaCalendarAlt, FaEraser, FaBook, FaFilePdf, FaArrowRight, FaExclamationTriangle
} from 'react-icons/fa';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { debounce } from 'lodash';

// --- Servicios ---
import { getGruposInventario, searchProductosAutocomplete } from '../../../../lib/inventarioService'; 
import { getRentabilidadPorGrupo, generarPdfRentabilidad, getRentabilidadPorDocumento } from '../../../../lib/reportesFacturacionService';
import { getListasPrecio } from '../../../../lib/listaPrecioService'; 
import { getTerceros } from '../../../../lib/terceroService'; 
import BotonRegresar from '../../../components/BotonRegresar';

// --- ESTILOS REUSABLES (Manual v2.0) ---
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none pl-10 bg-white";
const selectStyles = {
    control: (base) => ({
        ...base,
        minHeight: '42px',
        borderRadius: '0.5rem',
        borderColor: '#D1D5DB',
        boxShadow: 'none',
        '&:hover': { borderColor: '#6366F1' }
    }),
    multiValue: (base) => ({ ...base, backgroundColor: '#E0E7FF' }),
    multiValueLabel: (base) => ({ ...base, color: '#3730A3', fontWeight: '600' }),
};

const safeFloat = (value) => parseFloat(value) || 0;
const SELECT_ALL_OPTION = { label: "Seleccionar Todo", value: "all" };

// Componente Multi-Select Personalizado
const CustomValueContainer = ({ children, ...props }) => {
    const selectedCount = props.getValue().length;
    if (selectedCount > 1) {
        return (
            <components.ValueContainer {...props}>
                <div className="text-sm font-semibold text-indigo-600 px-2 flex items-center">
                   <span className="bg-indigo-50 px-2 py-0.5 rounded-md border border-indigo-100 text-xs uppercase tracking-wide">
                      {selectedCount} SELECCIONADOS
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

export default function RentabilidadProductoPage() {
    const router = useRouter();
    const { user, loading: authLoading } = useAuth();
    
    // --- ESTADOS ---
    const [modoReporte, setModoReporte] = useState('producto'); 
    const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);

    const [filtros, setFiltros] = useState({
        fecha_inicio: new Date(new Date().setMonth(new Date().getMonth() - 1)),
        fecha_fin: new Date(),
        grupo_ids: [], 
        producto_ids: [], 
        tercero_ids: [], 
        lista_precio_ids: [], 
        margen_minimo: '', 
        mostrar_solo_perdidas: false, 
        tipo_documento_codigo: '', 
        numero_documento: '',
    });

    const [maestros, setMaestros] = useState({
        grupos: [],
        terceros: [], 
        listasPrecio: [],
    });

    const [productosSugeridos, setProductosSugeridos] = useState([]);
    const [reporteData, setReporteData] = useState({ items: [], totales: {}, detalleDocumento: null }); 
    const [pageIsLoading, setPageIsLoading] = useState(true);
    const [isSearching, setIsSearching] = useState(false);
    const [isProductSearching, setIsProductSearching] = useState(false);
    const [expandedRows, setExpandedRows] = useState({});

    // --- CÁLCULO DE OPCIONES ---
    const grupoOptions = useMemo(() => {
        if (maestros.grupos.length > 0) {
            return [SELECT_ALL_OPTION, ...maestros.grupos];
        }
        return maestros.grupos;
    }, [maestros.grupos]);

    // --- LÓGICA DE BÚSQUEDA Y CARGA ---
    const fetchProductSuggestions = useCallback(async (searchTerm) => {
        setIsProductSearching(true);
        const filtrosAutocomplete = { 
            search_term: searchTerm || null, 
            grupo_ids: filtros.grupo_ids.filter(g => g.value !== 'all').map(g => g.value), 
        };
        try {
            const res = await searchProductosAutocomplete(filtrosAutocomplete); 
            setProductosSugeridos(res.map(p => ({ label: `(${p.codigo}) ${p.nombre}`, value: p.id })));
        } catch (error) {
            console.error("Error buscando productos:", error.message); 
            setProductosSugeridos([]);
        } finally {
            setIsProductSearching(false);
        }
    }, [filtros.grupo_ids]);

    const debouncedProductSearch = useCallback(debounce(fetchProductSuggestions, 400), [fetchProductSuggestions]);
    
    const handleProductInputChange = (inputValue, actionMeta) => {
        if (actionMeta.action !== 'input-change') return;
        const safeInputValue = inputValue === null || inputValue === undefined ? '' : String(inputValue);
        debouncedProductSearch(safeInputValue);
    };

    const fetchTerceroSuggestions = useCallback(async (searchTerm) => {
        if (!searchTerm || searchTerm.length < 3) return;
        try {
            const res = await getTerceros({ filtro: searchTerm, limit: 10 });
            const listaTerceros = Array.isArray(res) ? res : (res.data || []);
            const options = listaTerceros.map(t => ({ label: `${t.razon_social} (${t.identificacion})`, value: t.id }));
            setMaestros(prev => ({ ...prev, terceros: options }));
        } catch (error) {
            console.error("Error buscando terceros:", error);
        }
    }, []);

    const debouncedTerceroSearch = useCallback(debounce(fetchTerceroSuggestions, 400), [fetchTerceroSuggestions]);

    const handleTerceroInputChange = (inputValue, actionMeta) => {
        if (actionMeta.action === 'input-change') debouncedTerceroSearch(inputValue);
    };

    useEffect(() => {
        if (authLoading) return;
        if (!user) {
            router.push('/login');
            return;
        }
        const fetchMaestros = async () => {
            try {
                const [gruposRes, listasRes] = await Promise.all([
                    getGruposInventario(),
                    getListasPrecio(), 
                ]);
                setMaestros(prev => ({
                    ...prev,
                    grupos: gruposRes.map(g => ({ label: g.nombre, value: g.id })),
                    listasPrecio: listasRes.map(lp => ({ label: lp.nombre, value: lp.id })), 
                }));
            } catch (error) {
                console.error("Error al cargar maestros:", error);
            } finally {
                setPageIsLoading(false);
            }
        };
        fetchMaestros();
    }, [user, authLoading, router]);

    const fetchReportePorGrupo = useCallback(async (currentFiltros) => {
        const grupoIdsFiltrados = currentFiltros.grupo_ids.filter(g => g.value !== 'all').map(g => g.value);
        const filtrosParaApi = {
            fecha_inicio: currentFiltros.fecha_inicio.toISOString().split('T')[0],
            fecha_fin: currentFiltros.fecha_fin.toISOString().split('T')[0],
            grupo_ids: grupoIdsFiltrados,
            producto_ids: currentFiltros.producto_ids.map(p => p.value),
            tercero_ids: currentFiltros.tercero_ids.map(t => t.value),
            lista_precio_ids: currentFiltros.lista_precio_ids.map(lp => lp.value),
            margen_minimo_porcentaje: safeFloat(currentFiltros.margen_minimo) || null,
            mostrar_solo_perdidas: currentFiltros.mostrar_solo_perdidas,
        };
        
        if (filtrosParaApi.grupo_ids.length === 0 && filtrosParaApi.producto_ids.length === 0) {
            toast.warning("Debe seleccionar al menos un Grupo o un Producto.");
            setIsSearching(false);
            return;
        }
        
        try {
            const data = await getRentabilidadPorGrupo(filtrosParaApi);
            setReporteData({ items: data.items, totales: data.totales || {}, detalleDocumento: null });
            setExpandedRows({});
            if (data.items.length === 0) toast.info("No se encontraron resultados.");
        } catch (error) {
            console.error(error);
            toast.error(error.response?.data?.detail || "Error al obtener el reporte.");
        } finally {
            setIsSearching(false);
        }
    }, []);
    
    const fetchReportePorDocumento = useCallback(async (currentFiltros) => {
        const { tipo_documento_codigo, numero_documento } = currentFiltros;
        if (!tipo_documento_codigo || !numero_documento) {
            toast.warning("Debe ingresar Código y Número de documento.");
            setIsSearching(false);
            return;
        }
        try {
            const filtrosParaApi = {
                tipo_documento_codigo: tipo_documento_codigo.trim().toUpperCase(),
                numero_documento: numero_documento.trim(),
            };
            const data = await getRentabilidadPorDocumento(filtrosParaApi); 
            setReporteData({ items: data.detalle, totales: data.totales, detalleDocumento: data });
            toast.success(`Reporte generado para ${data.documento_ref}.`);
        } catch (error) {
            console.error(error);
            toast.error(error.response?.data?.detail || "Error al obtener el reporte.");
            setReporteData({ items: [], totales: {}, detalleDocumento: null }); 
        } finally {
            setIsSearching(false);
        }
    }, []);
    
    const handleSearchClick = () => {
        setIsSearching(true);
        modoReporte === 'producto' ? fetchReportePorGrupo(filtros) : fetchReportePorDocumento(filtros);
    };

    const handleClearFiltros = () => {
        setFiltros({
            fecha_inicio: new Date(new Date().setMonth(new Date().getMonth() - 1)),
            fecha_fin: new Date(),
            grupo_ids: [], producto_ids: [], tercero_ids: [], lista_precio_ids: [], 
            margen_minimo: '', mostrar_solo_perdidas: false, tipo_documento_codigo: '', numero_documento: '',
        });
        setReporteData({ items: [], totales: {}, detalleDocumento: null });
        setProductosSugeridos([]);
        setExpandedRows({});
    };

    const toggleRow = (productoId) => {
        setExpandedRows(prev => ({ ...prev, [productoId]: !prev[productoId] }));
    };

    const handleFilterChange = (name, value) => {
        if (name === 'grupo_ids') {
            const isSelectAll = value.some(option => option.value === SELECT_ALL_OPTION.value);
            if (isSelectAll && value.length > 0) {
                const allOptions = [SELECT_ALL_OPTION, ...maestros.grupos];
                const uniqueGroups = Array.from(new Set(allOptions.map(o => o.value))).map(v => allOptions.find(o => o.value === v));
                setFiltros(prev => ({ ...prev, grupo_ids: uniqueGroups }));
                return;
            } 
            if (value.length > 0 && value.every(o => o.value !== SELECT_ALL_OPTION.value) && filtros.grupo_ids.some(o => o.value === SELECT_ALL_OPTION.value)) {
                setFiltros(prev => ({ ...prev, grupo_ids: value }));
                return;
            }
            if (!value.length) {
                 setFiltros(prev => ({ ...prev, grupo_ids: [] }));
                 return;
            }
        }
        setFiltros(prev => {
            const newFiltros = { ...prev, [name]: value };
            if (modoReporte === 'producto' && name === 'grupo_ids' && prev.grupo_ids !== value) {
                newFiltros.producto_ids = [];
                setProductosSugeridos([]);
            }
            return newFiltros;
        });
    };

    const handleGenerarPDFGlobal = async () => {
        if (reporteData.items.length === 0) return toast.warning("Genere el reporte primero.");
        setIsSearching(true);
        try {
            let pdfBlob;
            if (modoReporte === 'producto') {
                const grupoIdsFiltrados = filtros.grupo_ids.filter(g => g.value !== 'all').map(g => g.value);
                const filtrosParaApi = {
                    fecha_inicio: filtros.fecha_inicio.toISOString().split('T')[0],
                    fecha_fin: filtros.fecha_fin.toISOString().split('T')[0],
                    grupo_ids: grupoIdsFiltrados,
                    producto_ids: filtros.producto_ids.map(p => p.value),
                    tercero_ids: filtros.tercero_ids.map(t => t.value),
                    lista_precio_ids: filtros.lista_precio_ids.map(lp => lp.value),
                    margen_minimo_porcentaje: safeFloat(filtros.margen_minimo) || null,
                    mostrar_solo_perdidas: filtros.mostrar_solo_perdidas,
                };
                 pdfBlob = await generarPdfRentabilidad(filtrosParaApi); 
            } else {
                 pdfBlob = await getRentabilidadPorDocumento({
                    tipo_documento_codigo: filtros.tipo_documento_codigo.trim().toUpperCase(),
                    numero_documento: filtros.numero_documento.trim(),
                 }, true); 
            }
            const url = window.URL.createObjectURL(pdfBlob);
            window.open(url, '_blank');
        } catch (error) {
            console.error(error);
            toast.error("Error al generar PDF.");
        } finally {
            setIsSearching(false);
        }
    };

    const handleImprimirIndividual = async (documentoRef) => {
        if (!documentoRef || !documentoRef.includes('-')) return toast.error("Referencia de documento inválida.");
        const [tipoDoc, numDoc] = documentoRef.split('-');
        
        setIsSearching(true);
        try {
            toast.info(`Generando PDF para ${documentoRef}...`);
            const pdfBlob = await getRentabilidadPorDocumento({
                tipo_documento_codigo: tipoDoc,
                numero_documento: numDoc
            }, true);
            
            const url = window.URL.createObjectURL(pdfBlob);
            window.open(url, '_blank');
        } catch (error) {
            console.error("Error PDF Individual:", error);
            toast.error(`No se pudo generar el PDF para ${documentoRef}`);
        } finally {
            setIsSearching(false);
        }
    };

    if (pageIsLoading || authLoading) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
                <FaChartLine className="text-indigo-300 text-6xl mb-4 animate-pulse" />
                <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando Análisis de Rentabilidad...</p>
            </div>
        );
    }

    const totales = reporteData.totales || {};
    const totalUtilidad = safeFloat(modoReporte === 'producto' ? totales.total_utilidad_general : totales.total_utilidad_bruta_valor);
    const fmtMoneda = (val) => safeFloat(val).toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
    const fmtPorcentaje = (val) => safeFloat(val).toFixed(2) + '%';

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
            <div className="max-w-7xl mx-auto">
                <ToastContainer position="top-right" autoClose={4000} />
                
                {/* ENCABEZADO */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                    <div>

                            <div className="flex items-center gap-3 mb-3">
                            
                            {/* 1. Botón Regresar (Izquierda) */}
                            <BotonRegresar />

                            {/* 2. Botón Manual (Derecha) */}
                            <button
                                onClick={() => window.open('/manual?file=capitulo_44_rentabilidad_producto.md', '_blank')}
                                className="text-indigo-600 hover:bg-indigo-50 px-3 py-1 rounded-md flex items-center gap-2 transition-colors font-bold text-sm"
                                type="button"
                            >
                                <FaBook className="text-lg" /> Manual
                            </button>

                        </div>


                        <div className="flex items-center gap-3 mt-3">
                            <div className="p-3 bg-indigo-100 rounded-xl text-indigo-600">
                                <FaChartLine className="text-2xl" />
                            </div>
                            <div>
                                <h1 className="text-3xl font-bold text-gray-800">Rentabilidad</h1>
                                <p className="text-gray-500 text-sm">Análisis de márgenes y utilidad por producto o venta.</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* SELECTOR DE MODO */}
                <div className="flex justify-center mb-8">
                    <div className="bg-white p-1.5 rounded-xl shadow-sm border border-gray-200 inline-flex">
                        <button 
                            onClick={() => setModoReporte('producto')} 
                            className={`flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-bold transition-all ${modoReporte === 'producto' ? 'bg-indigo-100 text-indigo-700 shadow-sm' : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'}`}
                        >
                            <FaTags /> Por Producto
                        </button>
                        <button 
                            onClick={() => setModoReporte('documento')} 
                            className={`flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-bold transition-all ml-1 ${modoReporte === 'documento' ? 'bg-indigo-100 text-indigo-700 shadow-sm' : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'}`}
                        >
                            <FaFileInvoice /> Por Documento
                        </button>
                    </div>
                </div>

                {/* CARD 1: FILTROS */}
                <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 mb-8 animate-fadeIn">
                    {modoReporte === 'producto' ? (
                        <>
                            <div className="grid grid-cols-1 md:grid-cols-12 gap-6 mb-6 items-end">
                                {/* Fechas */}
                                <div className="md:col-span-3">
                                    <label className={labelClass}>Desde</label>
                                    <div className="relative">
                                        <DatePicker selected={filtros.fecha_inicio} onChange={d => handleFilterChange('fecha_inicio', d)} dateFormat="dd/MM/yyyy" className={inputClass} />
                                        <FaCalendarAlt className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                    </div>
                                </div>
                                <div className="md:col-span-3">
                                    <label className={labelClass}>Hasta</label>
                                    <div className="relative">
                                        <DatePicker selected={filtros.fecha_fin} onChange={d => handleFilterChange('fecha_fin', d)} dateFormat="dd/MM/yyyy" className={inputClass} />
                                        <FaCalendarAlt className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                    </div>
                                </div>
                                {/* Grupos */}
                                <div className="md:col-span-6">
                                    <label className={labelClass}>Grupos de Inventario</label>
                                    <Select 
                                        isMulti 
                                        options={grupoOptions} 
                                        value={filtros.grupo_ids} 
                                        onChange={s => handleFilterChange('grupo_ids', s)} 
                                        placeholder="Seleccione..." 
                                        components={{ ValueContainer: CustomValueContainer }}
                                        styles={selectStyles}
                                    />
                                </div>
                            </div>

                            {/* Filtros Avanzados */}
                            <div className="border-t border-gray-100 pt-4">
                                <button 
                                    onClick={() => setShowAdvancedFilters(!showAdvancedFilters)} 
                                    className="flex items-center text-sm font-bold text-indigo-600 hover:text-indigo-800 focus:outline-none transition-colors"
                                >
                                    <FaFilter className="mr-2" /> 
                                    {showAdvancedFilters ? 'Ocultar Filtros' : 'Más Filtros'}
                                    {showAdvancedFilters ? <FaChevronUp className="ml-1"/> : <FaChevronDown className="ml-1"/>}
                                </button>
                                
                                {showAdvancedFilters && (
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-6 bg-indigo-50/30 p-5 rounded-xl border border-indigo-100 animate-slideDown">
                                        <div>
                                            <label className={labelClass}>Producto Específico</label>
                                            <Select isMulti options={productosSugeridos} value={filtros.producto_ids} onChange={s => handleFilterChange('producto_ids', s)} onInputChange={handleProductInputChange} placeholder="Buscar..." isLoading={isProductSearching} styles={selectStyles} />
                                        </div>
                                        <div>
                                            <label className={labelClass}>Cliente</label>
                                            <Select isMulti options={maestros.terceros} value={filtros.tercero_ids} onChange={s => handleFilterChange('tercero_ids', s)} onInputChange={handleTerceroInputChange} placeholder="Buscar..." styles={selectStyles} />
                                        </div>
                                        <div>
                                            <label className={labelClass}>Lista de Precios</label>
                                            <Select isMulti options={maestros.listasPrecio} value={filtros.lista_precio_ids} onChange={s => handleFilterChange('lista_precio_ids', s)} placeholder="Seleccione..." styles={selectStyles} />
                                        </div>
                                        <div className="flex flex-col justify-end gap-2">
                                            <div>
                                                <label className={labelClass}>Margen Mínimo %</label>
                                                <input type="number" step="0.01" value={filtros.margen_minimo} onChange={e => handleFilterChange('margen_minimo', e.target.value)} className={inputClass} placeholder="Ej: 20" />
                                            </div>
                                            <label className="flex items-center cursor-pointer bg-white px-3 py-2 rounded-lg border border-red-100 hover:bg-red-50 transition-colors">
                                                <input type="checkbox" checked={filtros.mostrar_solo_perdidas} onChange={e => handleFilterChange('mostrar_solo_perdidas', e.target.checked)} className="checkbox checkbox-error checkbox-sm" />
                                                <span className="ml-2 text-xs font-bold text-red-600 uppercase">Solo Pérdidas</span>
                                            </label>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </>
                    ) : (
                        // MODO DOCUMENTO
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-end">
                            <div>
                                <label className={labelClass}>Código Tipo Doc.</label>
                                <input type="text" value={filtros.tipo_documento_codigo} onChange={e => handleFilterChange('tipo_documento_codigo', e.target.value)} className={inputClass} placeholder="Ej: FV" />
                            </div>
                            <div>
                                <label className={labelClass}>Número Consecutivo</label>
                                <input type="text" value={filtros.numero_documento} onChange={e => handleFilterChange('numero_documento', e.target.value)} className={inputClass} placeholder="Ej: 1050" />
                            </div>
                        </div>
                    )}

                    {/* Botones Acción */}
                    <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-100">
                        <button onClick={handleClearFiltros} className="btn btn-ghost btn-sm text-gray-500 hover:bg-gray-100" disabled={isSearching}>
                            <FaEraser className="mr-2"/> Limpiar
                        </button>
                        <button onClick={handleSearchClick} className="px-8 py-2 bg-indigo-600 text-white rounded-lg shadow-md font-bold flex items-center gap-2 hover:bg-indigo-700 transition-all transform hover:-translate-y-0.5" disabled={isSearching}>
                            {isSearching ? <span className="loading loading-spinner loading-sm"></span> : <><FaSearch /> Consultar Rentabilidad</>}
                        </button>
                    </div>
                </div>

                {/* CARD 2: RESULTADOS */}
                {reporteData.items.length > 0 && (
                    <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden animate-slideDown">
                        
                        {/* Cabecera Reporte */}
                        <div className="p-6 bg-gray-50 border-b border-gray-200 flex flex-col md:flex-row justify-between items-center gap-4">
                            <div>
                                <h2 className="text-xl font-bold text-gray-800">Resultados del Análisis</h2>
                                {modoReporte === 'documento' && reporteData.detalleDocumento && (
                                    <p className="text-sm text-gray-600 mt-1 flex items-center gap-2">
                                        <FaFileInvoice className="text-indigo-400"/>
                                        {reporteData.detalleDocumento.documento_ref} 
                                        <span className="text-gray-300">|</span> 
                                        {reporteData.detalleDocumento.tercero_nombre}
                                    </p>
                                )}
                            </div>
                            
                            <div className="flex items-center gap-6">
                                <div className="text-right">
                                    <p className="text-xs text-gray-400 uppercase font-bold tracking-wider">Utilidad Total</p>
                                    <p className={`text-2xl font-mono font-bold ${totalUtilidad >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                        ${fmtMoneda(totalUtilidad)}
                                    </p>
                                </div>
                                <button onClick={handleGenerarPDFGlobal} className="btn btn-outline btn-error btn-sm gap-2 shadow-sm bg-white hover:bg-red-50 border-red-200 text-red-600">
                                    <FaFilePdf /> Exportar PDF
                                </button>
                            </div>
                        </div>

                        {/* Tabla */}
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-slate-100 text-gray-600 text-xs font-bold uppercase tracking-wider">
                                    <tr>
                                        <th className="py-3 px-6 text-left">Código</th>
                                        <th className="py-3 px-6 text-left w-1/3">Producto</th>
                                        <th className="py-3 px-6 text-right">Cant.</th>
                                        <th className="py-3 px-6 text-right">Venta Total</th>
                                        <th className="py-3 px-6 text-right">Costo Total</th>
                                        <th className="py-3 px-6 text-right bg-indigo-50/50 text-indigo-900">Utilidad</th>
                                        <th className="py-3 px-6 text-right bg-indigo-50/50 text-indigo-900">Margen %</th>
                                        {modoReporte === 'producto' && <th className="py-3 px-6 text-center">Ver Detalle</th>}
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-100 text-sm">
                                    {reporteData.items.map((item) => {
                                        const key = item.producto_codigo + (item.linea_documento_id || item.producto_id);
                                        const margen = safeFloat(modoReporte === 'producto' ? item.margen_rentabilidad_porcentaje : item.utilidad_bruta_porcentaje);
                                        const utilidad = safeFloat(modoReporte === 'producto' ? item.total_utilidad : item.utilidad_bruta_valor);
                                        const isLoss = utilidad < 0;
                                        const isLowMargin = margen < 15 && !isLoss; // Alerta amarilla si margen bajo

                                        return (
                                            <React.Fragment key={key}>
                                                <tr className={`hover:bg-gray-50 transition-colors ${isLoss ? 'bg-red-50/30' : ''}`}>
                                                    <td className="py-3 px-6 font-mono text-xs text-gray-500">{item.producto_codigo}</td>
                                                    <td className="py-3 px-6 font-medium text-gray-800">{item.producto_nombre}</td>
                                                    <td className="py-3 px-6 text-right font-mono text-gray-600">{fmtMoneda(item.cantidad)}</td>
                                                    <td className="py-3 px-6 text-right font-mono text-gray-600">${fmtMoneda(modoReporte === 'producto' ? item.total_venta : item.valor_venta_total)}</td>
                                                    <td className="py-3 px-6 text-right font-mono text-gray-600">${fmtMoneda(modoReporte === 'producto' ? item.total_costo : item.costo_total)}</td>
                                                    
                                                    <td className={`py-3 px-6 text-right font-mono font-bold ${isLoss ? 'text-red-600' : 'text-green-600'} bg-slate-50/30`}>
                                                        ${fmtMoneda(utilidad)}
                                                    </td>
                                                    
                                                    <td className="py-3 px-6 text-right bg-slate-50/30">
                                                        <span className={`px-2 py-1 rounded-md text-xs font-bold ${isLoss ? 'bg-red-100 text-red-700' : isLowMargin ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-700'}`}>
                                                            {fmtPorcentaje(margen)}
                                                        </span>
                                                    </td>
                                                    
                                                    {modoReporte === 'producto' && (
                                                        <td className="py-3 px-6 text-center">
                                                            {item.trazabilidad_documentos?.length > 0 ? (
                                                                <button 
                                                                    onClick={() => toggleRow(item.producto_id)} 
                                                                    className={`p-1.5 rounded-full transition-colors ${expandedRows[item.producto_id] ? 'bg-indigo-100 text-indigo-600' : 'hover:bg-gray-100 text-gray-400 hover:text-indigo-500'}`}
                                                                >
                                                                    {expandedRows[item.producto_id] ? <FaMinusCircle /> : <FaEye />}
                                                                </button>
                                                            ) : <span className="text-gray-300 text-xs">-</span>}
                                                        </td>
                                                    )}
                                                </tr>

                                                {/* TRAZABILIDAD EXPANDIDA (DRILL-DOWN) */}
                                                {modoReporte === 'producto' && expandedRows[item.producto_id] && (
                                                    <tr>
                                                        <td colSpan="8" className="p-4 bg-gray-50 border-b border-gray-100 shadow-inner">
                                                            <div className="bg-white border border-gray-200 rounded-lg overflow-hidden max-w-3xl mx-auto shadow-sm">
                                                                <div className="bg-gray-100 px-4 py-2 text-xs font-bold text-gray-500 uppercase flex justify-between items-center">
                                                                    <span>Trazabilidad de Ventas</span>
                                                                    <span>{item.trazabilidad_documentos.length} documentos</span>
                                                                </div>
                                                                <table className="w-full text-xs">
                                                                    <thead className="bg-white text-gray-500 border-b border-gray-100">
                                                                        <tr>
                                                                            <th className="px-4 py-2 text-left">Documento</th>
                                                                            <th className="px-4 py-2 text-left">Fecha</th>
                                                                            <th className="px-4 py-2 text-right">Venta</th>
                                                                            <th className="px-4 py-2 text-right">Utilidad</th>
                                                                            <th className="px-4 py-2 text-center">PDF</th>
                                                                        </tr>
                                                                    </thead>
                                                                    <tbody className="divide-y divide-gray-50">
                                                                        {item.trazabilidad_documentos.map((doc, idx) => (
                                                                            <tr key={idx} className="hover:bg-blue-50/30">
                                                                                <td className="px-4 py-2 font-medium text-indigo-600">{doc.documento_ref}</td>
                                                                                <td className="px-4 py-2 text-gray-500">{new Date(doc.fecha).toLocaleDateString('es-CO')}</td>
                                                                                <td className="px-4 py-2 text-right text-gray-600">${fmtMoneda(doc.valor_venta)}</td>
                                                                                <td className={`px-4 py-2 text-right font-bold ${doc.utilidad_bruta_valor < 0 ? 'text-red-600' : 'text-green-600'}`}>
                                                                                    ${fmtMoneda(doc.utilidad_bruta_valor)}
                                                                                </td>
                                                                                <td className="px-4 py-2 text-center">
                                                                                    <button 
                                                                                        onClick={() => handleImprimirIndividual(doc.documento_ref)}
                                                                                        className="text-gray-400 hover:text-red-600 transition-colors"
                                                                                        title="Ver Documento PDF"
                                                                                    >
                                                                                        <FaPrint />
                                                                                    </button>
                                                                                </td>
                                                                            </tr>
                                                                        ))}
                                                                    </tbody>
                                                                </table>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                )}
                                            </React.Fragment>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}