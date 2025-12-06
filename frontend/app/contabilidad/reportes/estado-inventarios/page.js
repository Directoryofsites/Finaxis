// frontend/app/contabilidad/reportes/estado-inventarios/page.js (REDISEÑO V2.0)
'use client';

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { getReporteAnalitico, generarPdfDirectoSuperInforme } from '@/lib/reportesInventarioService';
import { apiService } from '@/lib/apiService';
import { useReactTable, getCoreRowModel, getSortedRowModel, flexRender } from '@tanstack/react-table';
import BotonRegresar from '../../../components/BotonRegresar';
import DatePicker from 'react-datepicker';
import Select, { components } from 'react-select'; // Importamos React-Select
import 'react-datepicker/dist/react-datepicker.css';
import { FaFilePdf, FaSearch, FaFilter, FaChevronDown, FaChevronUp, FaEraser } from 'react-icons/fa';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// =============================================================================
// 🎨 COMPONENTE PERSONALIZADO "ANTI-CHORRERO" (Estándar v2.0)
// =============================================================================
const CustomValueContainer = ({ children, ...props }) => {
    const selectedCount = props.getValue().length;
    if (selectedCount > 1) {
        return (
            <components.ValueContainer {...props}>
                <div className="text-sm font-semibold text-indigo-600 px-2 flex items-center">
                   <span className="bg-indigo-100 px-2 py-0.5 rounded-md border border-indigo-200">
                      ✅ {selectedCount} Seleccionados
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

const formatCurrency = (value) => {
    const number = parseFloat(value);
    if (isNaN(number)) return '$ 0';
    return number.toLocaleString('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0, maximumFractionDigits: 0 });
};

const EstadoInventariosPage = () => {
    const { user } = useAuth();
    const today = new Date();
    const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);

    // --- Estados de Datos ---
    const [filtros, setFiltros] = useState({
        fecha_inicio: firstDayOfMonth,
        fecha_fin: today,
        bodega_ids: [], // Ahora es array
        grupo_ids: [],  // Ahora es array
    });
    
    const [maestros, setMaestros] = useState({ bodegas: [], grupos: [] });
    const [reportData, setReportData] = useState({ items: [], totales: {} });
    
    // --- Estados de UI ---
    const [loading, setLoading] = useState(false); // Control de búsqueda
    const [loadingMaestros, setLoadingMaestros] = useState(true);
    const [showAdvancedFilters, setShowAdvancedFilters] = useState(false); // Acordeón
    const [sorting, setSorting] = useState([]);
    const [isExportingPdf, setIsExportingPdf] = useState(false);

    // --- Carga de Maestros ---
    useEffect(() => {
        const fetchMaestros = async () => {
            setLoadingMaestros(true);
            try {
                const [bodegasRes, gruposRes] = await Promise.all([
                    apiService.get('/bodegas/'),
                    apiService.get('/inventario/grupos/')
                ]);
                // Transformar para React-Select
                setMaestros({
                    bodegas: bodegasRes.data.map(b => ({ value: b.id, label: b.nombre })),
                    grupos: gruposRes.data.map(g => ({ value: g.id, label: g.nombre }))
                });
            } catch (err) {
                console.error("Error cargando maestros:", err);
                toast.error("Error al cargar filtros.");
            } finally {
                setLoadingMaestros(false);
            }
        };
        if(user) fetchMaestros();
    }, [user]);

    // --- Búsqueda de Datos ---
    const fetchData = useCallback(async () => {
        setLoading(true);
        try {
             const filtrosParaApi = {
                fecha_inicio: filtros.fecha_inicio.toISOString().split('T')[0],
                fecha_fin: filtros.fecha_fin.toISOString().split('T')[0],
                // Enviamos los arrays directamente
                bodega_ids: filtros.bodega_ids.length > 0 ? filtros.bodega_ids : null,
                grupo_ids: filtros.grupo_ids.length > 0 ? filtros.grupo_ids : null,
                vista_por_valor: true,
             };

            const data = await getReporteAnalitico(filtrosParaApi);

             const adaptedItems = data.items.map(item => ({
                producto_id: item.producto_id,
                producto_codigo: item.producto_codigo,
                producto_nombre: item.producto_nombre,
                saldo_inicial_cantidad: 0,
                saldo_inicial_valor: item.saldo_inicial_valor,
                entradas_cantidad: 0,
                entradas_valor: item.total_entradas_valor,
                salidas_cantidad: 0,
                salidas_valor: item.total_salidas_valor,
                saldo_final_cantidad: 0,
                saldo_final_valor: item.saldo_final_valor
             }));

             const adaptedTotales = {
                 saldo_inicial_valor: data.totales.saldo_inicial_valor,
                 entradas_valor: data.totales.total_entradas_valor,
                 salidas_valor: data.totales.total_salidas_valor,
                 saldo_final_valor: data.totales.saldo_final_valor
             };

            setReportData({ items: adaptedItems, totales: adaptedTotales });
            if (adaptedItems.length === 0) toast.info("No se encontraron resultados.");

        } catch (err) {
            console.error("Error al generar reporte:", err);
            toast.error(err.response?.data?.detail || 'Error al generar el reporte.');
            setReportData({ items: [], totales: {} });
        } finally {
            setLoading(false);
        }
    }, [filtros]);

    // --- Handlers ---
    const handleDateChange = (name, date) => {
        setFiltros(prev => ({ ...prev, [name]: date || new Date() }));
    };

    const handleMultiSelectChange = (name, selectedOptions) => {
        const values = selectedOptions ? selectedOptions.map(option => option.value) : [];
        setFiltros(prev => ({ ...prev, [name]: values }));
    };

    const handleLimpiar = () => {
        setFiltros({
            fecha_inicio: firstDayOfMonth,
            fecha_fin: today,
            bodega_ids: [],
            grupo_ids: [],
        });
        setReportData({ items: [], totales: {} });
        toast.info("Filtros limpiados.");
    };

    const handleExportPDF = async () => {
         if (reportData.items.length === 0) return toast.warning("Genere el reporte primero.");
         setIsExportingPdf(true);
         try {
             const filtrosParaApi = {
                 fecha_inicio: filtros.fecha_inicio.toISOString().split('T')[0],
                 fecha_fin: filtros.fecha_fin.toISOString().split('T')[0],
                 bodega_ids: filtros.bodega_ids.length > 0 ? filtros.bodega_ids : null,
                 grupo_ids: filtros.grupo_ids.length > 0 ? filtros.grupo_ids : null,
                 vista_reporte: "ESTADO_GENERAL", 
                 traerTodo: true,
             };

             await generarPdfDirectoSuperInforme(filtrosParaApi);
             toast.success("PDF generado correctamente.");
             
         } catch (err) {
             console.error("Error al generar PDF:", err);
             toast.error(err.response?.data?.detail || 'Error al generar el PDF.');
         } finally {
             setIsExportingPdf(false);
         }
     };

     // --- Configuración de Tabla ---
     const columns = useMemo(() => [
        { accessorKey: 'producto_codigo', header: 'Código', cell: info => <span className="font-mono text-gray-600 text-xs">{info.getValue()}</span> },
        { accessorKey: 'producto_nombre', header: 'Producto', cell: info => <span className="font-medium text-gray-700">{info.getValue()}</span> },
        { accessorKey: 'saldo_inicial_valor', header: 'Sdo. Inicial', cell: info => <div className="text-right font-mono text-gray-600">{formatCurrency(info.getValue())}</div> },
        { accessorKey: 'entradas_valor', header: 'Entradas', cell: info => <div className="text-right font-mono text-green-600">{formatCurrency(info.getValue())}</div> },
        { accessorKey: 'salidas_valor', header: 'Salidas', cell: info => <div className="text-right font-mono text-red-600">{formatCurrency(info.getValue())}</div> },
        { accessorKey: 'saldo_final_valor', header: 'Sdo. Final', cell: info => <div className="text-right font-mono font-bold text-gray-900">{formatCurrency(info.getValue())}</div> },
    ], []);

    const table = useReactTable({
        data: reportData.items,
        columns,
        state: { sorting },
        onSortingChange: setSorting,
        getCoreRowModel: getCoreRowModel(),
        getSortedRowModel: getSortedRowModel(),
    });

    if (loadingMaestros) return <div className="flex justify-center items-center h-screen bg-gray-50"><span className="loading loading-spinner loading-lg text-indigo-600"></span></div>;

    // Clases reutilizables
    const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
    const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all";

    return (
        <div className="container mx-auto p-4 md:p-8 bg-gray-50 min-h-screen font-sans">
            <ToastContainer position="top-right" autoClose={3000} />
            
            {/* HEADER */}
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-gray-800 tracking-tight">Estado de Inventarios</h1>
                    <p className="text-gray-500 text-sm mt-1">Balance valorizado general.</p>
                </div>
                <BotonRegresar />
            </div>

            {/* CARD DE FILTROS */}
            <div className="bg-white p-6 md:p-8 rounded-xl shadow-lg border border-gray-100 mb-8 animate-fadeIn">
                 
                 {/* Nivel 1: Esenciales */}
                 <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                     <div>
                         <label className={labelClass}>Fecha Inicio</label>
                         <DatePicker selected={filtros.fecha_inicio} onChange={(date) => handleDateChange('fecha_inicio', date)} dateFormat="dd/MM/yyyy" className={inputClass} />
                     </div>
                     <div>
                         <label className={labelClass}>Fecha Fin</label>
                         <DatePicker selected={filtros.fecha_fin} onChange={(date) => handleDateChange('fecha_fin', date)} dateFormat="dd/MM/yyyy" className={inputClass} />
                     </div>
                 </div>

                 {/* Nivel 2: Avanzados (Bodegas y Grupos) */}
                 <div className="border-t border-gray-100 pt-4">
                    <button 
                        onClick={() => setShowAdvancedFilters(!showAdvancedFilters)} 
                        className="flex items-center text-sm font-bold text-indigo-600 hover:text-indigo-800 focus:outline-none transition-colors"
                    >
                        <FaFilter className="mr-2" /> 
                        {showAdvancedFilters ? 'Ocultar Filtros Avanzados' : 'Mostrar Filtros Avanzados (Bodegas, Grupos)'}
                        {showAdvancedFilters ? <FaChevronUp className="ml-1"/> : <FaChevronDown className="ml-1"/>}
                    </button>

                    {showAdvancedFilters && (
                        <div className="mt-6 bg-gray-50 p-6 rounded-xl border border-gray-200 animate-slideDown grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <label className={labelClass}>Bodegas</label>
                                <Select
                                    isMulti
                                    options={maestros.bodegas}
                                    value={maestros.bodegas.filter(op => filtros.bodega_ids.includes(op.value))}
                                    onChange={(opts) => handleMultiSelectChange('bodega_ids', opts)}
                                    placeholder="Todas"
                                    components={{ ValueContainer: CustomValueContainer }}
                                    styles={{ control: (base) => ({ ...base, minHeight: '2.5rem', borderRadius: '0.5rem' }) }}
                                    className="text-sm"
                                />
                            </div>
                            <div>
                                <label className={labelClass}>Grupos</label>
                                <Select
                                    isMulti
                                    options={maestros.grupos}
                                    value={maestros.grupos.filter(op => filtros.grupo_ids.includes(op.value))}
                                    onChange={(opts) => handleMultiSelectChange('grupo_ids', opts)}
                                    placeholder="Todos"
                                    components={{ ValueContainer: CustomValueContainer }}
                                    styles={{ control: (base) => ({ ...base, minHeight: '2.5rem', borderRadius: '0.5rem' }) }}
                                    className="text-sm"
                                />
                            </div>
                        </div>
                    )}
                 </div>

                 {/* Botones de Acción */}
                 <div className="flex flex-col md:flex-row justify-end items-center gap-4 mt-8 pt-6 border-t border-gray-100">
                     <button onClick={handleLimpiar} disabled={loading} className="btn btn-ghost btn-sm text-gray-500 hover:text-gray-700">
                        <FaEraser className="mr-2" /> Limpiar
                     </button>
                     
                     <button onClick={handleExportPDF} className="btn btn-outline btn-error btn-sm gap-2 shadow-sm" disabled={isExportingPdf || loading || !reportData.items.length}>
                         {isExportingPdf ? <span className="loading loading-spinner loading-xs"></span> : <FaFilePdf />} PDF
                     </button>

                     <button onClick={fetchData} disabled={loading} className="btn btn-primary px-8 py-2 shadow-md transform hover:scale-105 transition-transform">
                         <FaSearch className={`mr-2 ${loading ? 'animate-spin' : ''}`} /> 
                         {loading ? 'Procesando...' : 'Buscar'}
                     </button>
                 </div>
            </div>

            {/* CARD DE RESULTADOS */}
            {reportData.items.length > 0 && (
             <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden animate-fadeIn">
                 <div className="p-5 bg-gray-50 border-b border-gray-200">
                    <h2 className="text-lg font-bold text-gray-800">Resultados <span className="text-sm font-normal text-gray-500 ml-2">({reportData.items.length} productos)</span></h2>
                 </div>

                 <div className="overflow-x-auto max-h-[65vh]">
                     <table className="table table-sm w-full">
                         <thead className="bg-slate-100 text-gray-600 uppercase text-xs font-bold sticky top-0 z-10 shadow-sm">
                             {table.getHeaderGroups().map(headerGroup => (
                                 <tr key={headerGroup.id}>
                                     {headerGroup.headers.map(header => (
                                         <th key={header.id} onClick={header.column.getToggleSortingHandler()} className={`py-3 px-4 cursor-pointer border-b border-gray-200 whitespace-nowrap hover:bg-slate-200 transition-colors ${header.index > 1 ? 'text-right' : 'text-left'}`}>
                                             {flexRender(header.column.columnDef.header, header.getContext())}
                                             {{ asc: ' ▲', desc: ' ▼' }[header.column.getIsSorted()] ?? null}
                                         </th>
                                     ))}
                                 </tr>
                             ))}
                         </thead>
                         <tbody className="text-sm divide-y divide-gray-100">
                             {table.getRowModel().rows.map(row => (
                                 <tr key={row.id} className="hover:bg-indigo-50/30 transition-colors duration-150">
                                     {row.getVisibleCells().map(cell => (
                                         <td key={cell.id} className="py-2 px-4 whitespace-nowrap">
                                             {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                         </td>
                                     ))}
                                 </tr>
                             ))}
                         </tbody>
                         <tfoot className="bg-slate-200 font-bold text-sm sticky bottom-0 z-10 shadow-inner">
                             <tr>
                                 <td colSpan={2} className="py-3 px-4 text-right">TOTALES GENERALES</td>
                                 <td className="text-right px-4 font-mono text-gray-800">{formatCurrency(reportData.totales.saldo_inicial_valor)}</td>
                                 <td className="text-right px-4 font-mono text-green-700">{formatCurrency(reportData.totales.entradas_valor)}</td>
                                 <td className="text-right px-4 font-mono text-red-700">{formatCurrency(reportData.totales.salidas_valor)}</td>
                                 <td className="text-right px-4 font-mono text-gray-900">{formatCurrency(reportData.totales.saldo_final_valor)}</td>
                             </tr>
                         </tfoot>
                     </table>
                 </div>
             </div>
            )}
        </div>
    );
};

export default EstadoInventariosPage;