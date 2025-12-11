// frontend/app/contabilidad/reportes/gestion-ventas/page.js (CORREGIDO HYDRATION ERROR)
'use client';

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import BotonRegresar from '../../../components/BotonRegresar';
import { getReporteGestionVentas } from '../../../../lib/gestionVentasService';
import { getTerceros } from '../../../../lib/terceroService';
import { solicitarUrlImpresionRentabilidad } from '../../../../lib/documentoService';
import { useReactTable, getCoreRowModel, flexRender } from '@tanstack/react-table';
import { FaSearch, FaFilePdf, FaCalendarAlt, FaUser, FaFileInvoiceDollar } from 'react-icons/fa';
import Select from 'react-select';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import { 
    FaBook,
} from 'react-icons/fa';

export default function GestionVentasPage() {
    
    // --- Estados ---
    const [filtros, setFiltros] = useState({
        fecha_inicio: new Date(new Date().getFullYear(), new Date().getMonth(), 1),
        fecha_fin: new Date(),
        cliente_id: null,
    });
    const [clientesOptions, setClientesOptions] = useState([]);
    const [reporteData, setReporteData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [loadingPdfId, setLoadingPdfId] = useState(null); // ID del documento cargando PDF

    // --- Carga Inicial ---
    useEffect(() => {
        const fetchClientes = async () => {
            try {
                const data = await getTerceros();
                // Transformar para React-Select
                const options = Array.isArray(data) 
                    ? data.map(c => ({ value: c.id, label: c.razon_social }))
                    : (data.terceros || []).map(c => ({ value: c.id, label: c.razon_social })); // Manejo robusto
                setClientesOptions(options);
            } catch (err) {
                toast.error("Error al cargar lista de clientes.");
            }
        };
        fetchClientes();
    }, []);

    // --- Handlers ---
    const handleDateChange = (name, date) => {
        setFiltros(prev => ({ ...prev, [name]: date || new Date() }));
    };

    const handleClienteChange = (option) => {
        setFiltros(prev => ({ ...prev, cliente_id: option ? option.value : null }));
    };

    const handleSearch = async (e) => {
        if (e) e.preventDefault();
        setLoading(true);
        setReporteData(null);
        
        try {
            const filtrosParaAPI = {
                fecha_inicio: filtros.fecha_inicio.toISOString().split('T')[0],
                fecha_fin: filtros.fecha_fin.toISOString().split('T')[0],
                cliente_id: filtros.cliente_id ? parseInt(filtros.cliente_id) : null,
                estado: null, 
            };
            
            const data = await getReporteGestionVentas(filtrosParaAPI);
            setReporteData(data);
            if (!data.items || data.items.length === 0) toast.info("No se encontraron documentos.");
            
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Error al generar el reporte.');
        } finally {
            setLoading(false);
        }
    };

    const handleGenerarPdfRentabilidad = async (documentoId) => {
        setLoadingPdfId(documentoId);
        try {
            const response = await solicitarUrlImpresionRentabilidad(documentoId);
            window.open(response.signed_url, '_blank');
        } catch (err) {
            toast.error('Error al generar PDF. Intente nuevamente.');
        } finally {
            setLoadingPdfId(null);
        }
    };

    // --- Configuración Tabla ---
    const columns = useMemo(() => [
        { 
            accessorKey: 'fecha', 
            header: 'Fecha Emisión',
            cell: info => <span className="text-gray-700">{info.getValue()}</span> 
        },
        {
            header: 'Documento',
            accessorFn: row => `${row.tipo_documento}-${row.numero}`,
            cell: info => <span className="font-mono font-bold text-indigo-900">{info.getValue()}</span>
        },
        { 
            accessorKey: 'beneficiario_nombre', 
            header: 'Cliente',
            cell: info => <span className="font-medium text-gray-800">{info.getValue()}</span>
        },
        { 
            id: 'acciones', 
            header: 'Acción', 
            cell: ({ row }) => (
                <div className="text-center">
                    <button
                        onClick={() => handleGenerarPdfRentabilidad(row.original.id)}
                        disabled={loadingPdfId === row.original.id}
                        className="btn btn-sm btn-outline btn-error shadow-sm hover:shadow-md transition-all"
                        title="Ver Rentabilidad"
                    >
                        {loadingPdfId === row.original.id ? <span className="loading loading-spinner loading-xs"></span> : <FaFilePdf className="text-lg" />}
                    </button>
                </div>
            ), 
        },
    ], [loadingPdfId]);

    const table = useReactTable({
        data: reporteData?.items || [],
        columns,
        getCoreRowModel: getCoreRowModel(),
    });

    // Clases de Estilo V2.0
    const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
    const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none";

    return (
        <div className="container mx-auto p-4 md:p-8 bg-gray-50 min-h-screen font-sans">
            <ToastContainer position="top-right" autoClose={3000} />
            
            {/* HEADER */}
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-gray-800 tracking-tight">Control de Rentabilidad</h1>
                    <p className="text-gray-500 text-sm mt-1">Generación de reportes individuales por factura.</p>
                </div>


                            <div className="flex items-center gap-3 mb-3">
                            
                            {/* 1. Botón Regresar (Izquierda) */}
                            <BotonRegresar />

                            {/* 2. Botón Manual (Derecha) */}
                            <button
                                onClick={() => window.open('/manual/capitulo_49_gestion_ventas.html', '_blank')}
                                className="text-indigo-600 hover:bg-indigo-50 px-3 py-1 rounded-md flex items-center gap-2 transition-colors font-bold text-sm"
                                type="button"
                            >
                                <FaBook className="text-lg" /> Manual
                            </button>

                        </div>


            </div>

            {/* CARD DE FILTROS */}
            <div className="bg-white p-6 md:p-8 rounded-xl shadow-lg border border-gray-100 mb-8 animate-fadeIn">
                <form onSubmit={handleSearch} className="flex flex-col md:flex-row gap-6 items-end">
                    
                    {/* Rango de Fechas */}
                    <div className="flex-grow grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className={labelClass}><FaCalendarAlt className="inline mr-1 mb-0.5"/> Desde</label>
                            <DatePicker 
                                selected={filtros.fecha_inicio} 
                                onChange={date => handleDateChange('fecha_inicio', date)} 
                                selectsStart startDate={filtros.fecha_inicio} endDate={filtros.fecha_fin}
                                dateFormat="yyyy-MM-dd" className={inputClass} 
                            />
                        </div>
                        <div>
                            <label className={labelClass}><FaCalendarAlt className="inline mr-1 mb-0.5"/> Hasta</label>
                            <DatePicker 
                                selected={filtros.fecha_fin} 
                                onChange={date => handleDateChange('fecha_fin', date)} 
                                selectsEnd startDate={filtros.fecha_inicio} endDate={filtros.fecha_fin} minDate={filtros.fecha_inicio}
                                dateFormat="yyyy-MM-dd" className={inputClass} 
                            />
                        </div>
                    </div>

                    {/* Selector de Cliente */}
                    <div className="flex-grow md:flex-grow-[2]">
                        <label className={labelClass}><FaUser className="inline mr-1 mb-0.5"/> Cliente</label>
                        {/* FIX: instanceId agregado */}
                        <Select
                            instanceId="select-cliente" 
                            options={clientesOptions}
                            onChange={handleClienteChange}
                            placeholder="Todos los clientes..."
                            isClearable
                            className="text-sm"
                            styles={{ control: (base) => ({ ...base, minHeight: '2.6rem', borderRadius: '0.5rem', borderColor: '#D1D5DB' }) }}
                        />
                    </div>

                    {/* Botón Buscar */}
                    <div className="md:w-auto w-full">
                        <button 
                            type="submit" 
                            disabled={loading} 
                            className="btn btn-primary w-full md:w-auto px-8 py-2.5 shadow-md transform hover:scale-105 transition-transform flex items-center justify-center gap-2"
                        >
                            {loading ? <span className="loading loading-spinner loading-sm"></span> : <><FaSearch /> Buscar</>}
                        </button>
                    </div>
                </form>
            </div>

            {/* RESULTADOS */}
            {reporteData && (
                <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden animate-fadeIn">
                    
                    {/* Toolbar Tabla */}
                    <div className="p-5 bg-gray-50 border-b border-gray-200 flex items-center gap-2">
                        <FaFileInvoiceDollar className="text-indigo-500 text-lg" />
                        <h2 className="text-lg font-bold text-gray-800">Documentos Encontrados</h2>
                        <span className="text-xs font-semibold bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full border border-indigo-200">
                            {reporteData.items.length}
                        </span>
                    </div>

                    {/* Tabla */}
                    <div className="overflow-x-auto">
                        <table className="table w-full">
                            <thead className="bg-slate-100 text-gray-600 uppercase text-xs font-bold border-b border-gray-200 sticky top-0">
                                {table.getHeaderGroups().map(headerGroup => (
                                    <tr key={headerGroup.id}>
                                        {headerGroup.headers.map(header => (
                                            <th key={header.id} className="py-4 px-6 text-left first:pl-8 last:text-center">
                                                {flexRender(header.column.columnDef.header, header.getContext())}
                                            </th>
                                        ))}
                                    </tr>
                                ))}
                            </thead>
                            <tbody className="text-sm divide-y divide-gray-100">
                                {table.getRowModel().rows.map(row => (
                                    <tr key={row.id} className="hover:bg-indigo-50/30 transition-colors duration-150">
                                        {row.getVisibleCells().map(cell => (
                                            <td key={cell.id} className="py-3 px-6 first:pl-8 last:text-center whitespace-nowrap">
                                                {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                                {reporteData.items.length === 0 && (
                                    <tr>
                                        <td colSpan={4} className="text-center py-10 text-gray-400 italic">
                                            No se encontraron resultados con los filtros aplicados.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
}