'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import DatePicker from 'react-datepicker';
import Select from 'react-select';
import 'react-datepicker/dist/react-datepicker.css';
import { useAuth } from '../../../context/AuthContext';
import {
    FaSearch, FaFilter, FaPrint, FaCalendarAlt, FaEraser,
    FaChevronDown, FaChevronUp, FaFileInvoiceDollar, FaChartLine
} from 'react-icons/fa';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// Servicios
import { getGruposInventario, searchProductosAutocomplete } from '../../../../lib/inventarioService';
import { getTerceros } from '../../../../lib/terceroService';
import { getAnalisisVentasCliente, generarPdfVentasCliente } from '../../../../lib/reporteVentasClienteService';

// Estilos
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm transition-all outline-none pl-10 bg-white";

// Formateador
const fmtMoneda = (val) => new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(val);
const fmtNumero = (val) => new Intl.NumberFormat('es-CO', { maximumFractionDigits: 2 }).format(val);
const fmtPorcentaje = (val) => `${parseFloat(val).toFixed(2)}%`;

export default function AnalisisVentasClientePage() {
    const router = useRouter();
    const { user, loading: authLoading } = useAuth();

    // Estados de Filtros
    const [filtros, setFiltros] = useState({
        fecha_inicio: new Date(new Date().setMonth(new Date().getMonth() - 1)),
        fecha_fin: new Date(),
        tercero_ids: [],
        producto_ids: [],
        grupo_ids: [],
    });

    // Estado de Maestros (Para selects)
    const [maestros, setMaestros] = useState({
        grupos: [],
        terceros: [], // Se llenará con búsqueda
        productos: [], // Se llenará con búsqueda
    });

    // Estado del Reporte
    const [reporteData, setReporteData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [expandedRows, setExpandedRows] = useState({});

    // Carga Inicial de Grupos
    useEffect(() => {
        if (authLoading) return;
        if (!user) { router.push('/login'); return; }

        getGruposInventario().then(res => {
            setMaestros(prev => ({ ...prev, grupos: res.map(g => ({ label: g.nombre, value: g.id })) }));
        }).catch(err => console.error(err));
    }, [user, authLoading, router]);

    // Handlers de Búsqueda Asíncrona (Selects)
    const handleSearchTerceros = (inputValue) => {
        if (inputValue.length < 3) return;
        getTerceros({ filtro: inputValue, limit: 10 }).then(res => {
            const lista = Array.isArray(res) ? res : (res.data || []);
            setMaestros(prev => ({ ...prev, terceros: lista.map(t => ({ label: `${t.razon_social} (${t.identificacion})`, value: t.id })) }));
        });
    };

    const handleSearchProductos = (inputValue) => {
        if (inputValue.length < 3) return;
        searchProductosAutocomplete({ search_term: inputValue }).then(res => {
            setMaestros(prev => ({ ...prev, productos: res.map(p => ({ label: `(${p.codigo}) ${p.nombre}`, value: p.id })) }));
        });
    };

    // Handler Principal de Búsqueda
    const handleGenerarReporte = async () => {
        setLoading(true);
        try {
            const payload = {
                fecha_inicio: filtros.fecha_inicio.toISOString().split('T')[0],
                fecha_fin: filtros.fecha_fin.toISOString().split('T')[0],
                tercero_ids: filtros.tercero_ids.map(t => t.value),
                producto_ids: filtros.producto_ids.map(p => p.value),
                grupo_ids: filtros.grupo_ids.map(g => g.value),
            };

            const data = await getAnalisisVentasCliente(payload);
            setReporteData(data);
            setExpandedRows({}); // Resetear expansiones
            if (data.items.length === 0) toast.info("No se encontraron resultados.");
        } catch (error) {
            console.error(error);
            toast.error("Error al generar reporte.");
        } finally {
            setLoading(false);
        }
    };

    const handleGenerarPDF = async () => {
        if (!reporteData) return toast.warning("Primero genere el reporte.");
        setLoading(true);
        try {
            const payload = {
                fecha_inicio: filtros.fecha_inicio.toISOString().split('T')[0],
                fecha_fin: filtros.fecha_fin.toISOString().split('T')[0],
                tercero_ids: filtros.tercero_ids.map(t => t.value),
                producto_ids: filtros.producto_ids.map(p => p.value),
                grupo_ids: filtros.grupo_ids.map(g => g.value),
                clientes_expandidos: Object.keys(expandedRows).filter(k => expandedRows[k]).map(Number),
            };
            const blob = await generarPdfVentasCliente(payload);
            const url = window.URL.createObjectURL(blob);
            window.open(url, '_blank');
        } catch (error) {
            console.error(error);
            toast.error("Error al generar PDF.");
        } finally {
            setLoading(false);
        }
    };

    const handleExportarCSV = () => {
        if (!reporteData || !reporteData.items.length) return toast.warning("No hay datos para exportar.");

        // Encabezados
        let csvContent = "NIT,Cliente,Venta Total,Costo Total,Utilidad Total,Margen %,Cantidad Items,Num Facturas\n";

        // Filas
        reporteData.items.forEach(item => {
            const row = [
                `"${item.tercero_identificacion || ''}"`,
                `"${item.tercero_nombre || ''}"`,
                Math.round(item.total_venta),
                Math.round(item.total_costo),
                Math.round(item.total_utilidad),
                parseFloat(item.margen_porcentaje).toFixed(2),
                item.cantidad_items,
                item.conteo_documentos
            ].join(",");
            csvContent += row + "\n";
        });

        // Descarga
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.setAttribute("href", url);
        link.setAttribute("download", `Analisis_Ventas_Clientes_${new Date().toISOString().slice(0, 10)}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const toggleRow = (id) => {
        setExpandedRows(prev => ({ ...prev, [id]: !prev[id] }));
    };

    return (
        <div className="p-6 bg-gray-50 min-h-screen font-sans text-gray-800">
            <ToastContainer />
            <div className="max-w-7xl mx-auto">

                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-3">
                            <FaChartLine className="text-blue-600" />
                            Análisis Integral de Ventas
                        </h1>
                        <p className="text-gray-500 mt-1">Explora ventas, costos y rentabilidad por cliente.</p>
                    </div>
                </div>

                {/* Filtros */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 mb-8">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">

                        {/* Fechas */}
                        <div>
                            <label className={labelClass}>Fecha Inicio</label>
                            <div className="relative">
                                <FaCalendarAlt className="absolute left-3 top-3 text-gray-400" />
                                <DatePicker
                                    selected={filtros.fecha_inicio}
                                    onChange={d => setFiltros({ ...filtros, fecha_inicio: d })}
                                    className={inputClass}
                                    dateFormat="yyyy-MM-dd"
                                />
                            </div>
                        </div>
                        <div>
                            <label className={labelClass}>Fecha Fin</label>
                            <div className="relative">
                                <FaCalendarAlt className="absolute left-3 top-3 text-gray-400" />
                                <DatePicker
                                    selected={filtros.fecha_fin}
                                    onChange={d => setFiltros({ ...filtros, fecha_fin: d })}
                                    className={inputClass}
                                    dateFormat="yyyy-MM-dd"
                                />
                            </div>
                        </div>

                        {/* Clientes */}
                        <div className="lg:col-span-2">
                            <label className={labelClass}>Filtrar Clientes (Opcional)</label>
                            <Select
                                instanceId="select-clientes"
                                isMulti
                                options={maestros.terceros}
                                onInputChange={handleSearchTerceros}
                                onChange={opt => setFiltros({ ...filtros, tercero_ids: opt })}
                                placeholder="Escribe para buscar cliente..."
                                className="text-sm"
                            />
                        </div>

                        {/* Productos y Grupos */}
                        <div className="lg:col-span-2">
                            <label className={labelClass}>Filtrar Productos (Opcional)</label>
                            <Select
                                instanceId="select-productos"
                                isMulti
                                options={maestros.productos}
                                onInputChange={handleSearchProductos}
                                onChange={opt => setFiltros({ ...filtros, producto_ids: opt })}
                                placeholder="Escribe para buscar producto..."
                                className="text-sm"
                            />
                        </div>
                        <div className="lg:col-span-2">
                            <label className={labelClass}>Filtrar por Grupo (Opcional)</label>
                            <Select
                                instanceId="select-grupos"
                                isMulti
                                options={maestros.grupos}
                                onChange={opt => setFiltros({ ...filtros, grupo_ids: opt })}
                                placeholder="Selecciona grupos..."
                                className="text-sm"
                            />
                        </div>
                    </div>

                    <div className="mt-6 flex justify-end gap-3 border-t pt-4 border-gray-100">
                        <button
                            onClick={() => setFiltros({
                                fecha_inicio: new Date(new Date().setMonth(new Date().getMonth() - 1)),
                                fecha_fin: new Date(),
                                tercero_ids: [], producto_ids: [], grupo_ids: []
                            })}
                            className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg flex items-center gap-2 font-medium"
                        >
                            <FaEraser /> Limpiar
                        </button>
                        <button
                            onClick={handleGenerarReporte}
                            disabled={loading}
                            className={`px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 font-medium shadow-sm transition-all ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                            {loading ? 'Procesando...' : <><FaSearch /> Generar Reporte</>}
                        </button>
                    </div>
                </div>

                {/* Dashboard KPI */}
                {reporteData && (
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200 text-center">
                            <p className="text-xs text-gray-500 uppercase font-bold tracking-wider">Ventas Totales</p>
                            <p className="text-2xl font-bold text-gray-800 mt-1">{fmtMoneda(reporteData.gran_total_venta)}</p>
                        </div>
                        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200 text-center">
                            <p className="text-xs text-gray-500 uppercase font-bold tracking-wider">Costo Total</p>
                            <p className="text-2xl font-bold text-gray-600 mt-1">{fmtMoneda(reporteData.gran_total_costo)}</p>
                        </div>
                        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200 text-center">
                            <p className="text-xs text-gray-500 uppercase font-bold tracking-wider">Utilidad Global</p>
                            <p className={`text-2xl font-bold mt-1 ${reporteData.gran_total_utilidad >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {fmtMoneda(reporteData.gran_total_utilidad)}
                            </p>
                        </div>
                        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200 text-center">
                            <p className="text-xs text-gray-500 uppercase font-bold tracking-wider">Margen Global</p>
                            <p className={`text-2xl font-bold mt-1 ${reporteData.margen_global_porcentaje >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {fmtPorcentaje(reporteData.margen_global_porcentaje)}
                            </p>
                        </div>
                    </div>
                )}

                {/* Tabla de Resultados */}
                {reporteData && (
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                        <div className="p-4 border-b border-gray-200 flex justify-between items-center bg-gray-50">
                            <h2 className="font-bold text-gray-700">Resultados por Cliente ({reporteData.items.length})</h2>
                            <div className="flex gap-2">
                                <button onClick={handleExportarCSV} className="px-4 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 flex items-center gap-2">
                                    <FaFileInvoiceDollar /> Exportar CSV
                                </button>
                                <button onClick={handleGenerarPDF} className="px-4 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 flex items-center gap-2">
                                    <FaPrint /> Exportar PDF
                                </button>
                            </div>
                        </div>

                        <div className="overflow-x-auto">
                            <table className="w-full text-sm text-left">
                                <thead className="bg-gray-100 text-gray-600 uppercase text-xs font-bold">
                                    <tr>
                                        <th className="px-6 py-3 min-w-[30px]"></th>
                                        <th className="px-6 py-3">Cliente</th>
                                        <th className="px-6 py-3 text-right">Venta</th>
                                        <th className="px-6 py-3 text-right">Costo</th>
                                        <th className="px-6 py-3 text-right">Utilidad</th>
                                        <th className="px-6 py-3 text-right">Margen %</th>
                                        <th className="px-6 py-3 text-center">Docs</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100">
                                    {reporteData.items.map(item => {
                                        const isExpanded = expandedRows[item.tercero_id];
                                        return (
                                            <React.Fragment key={item.tercero_id}>
                                                <tr
                                                    onClick={() => toggleRow(item.tercero_id)}
                                                    className={`hover:bg-blue-50 cursor-pointer transition-colors ${isExpanded ? 'bg-blue-50' : ''}`}
                                                >
                                                    <td className="px-6 py-4 text-center text-gray-400">
                                                        {isExpanded ? <FaChevronUp /> : <FaChevronDown />}
                                                    </td>
                                                    <td className="px-6 py-4 font-medium text-gray-900">
                                                        {item.tercero_nombre}
                                                        <span className="block text-xs text-gray-500 font-normal">{item.tercero_identificacion}</span>
                                                    </td>
                                                    <td className="px-6 py-4 text-right font-medium">{fmtMoneda(item.total_venta)}</td>
                                                    <td className="px-6 py-4 text-right text-gray-600">{fmtMoneda(item.total_costo)}</td>
                                                    <td className={`px-6 py-4 text-right font-bold ${item.total_utilidad >= 0 ? 'text-green-600' : 'text-red-500'}`}>
                                                        {fmtMoneda(item.total_utilidad)}
                                                    </td>
                                                    <td className={`px-6 py-4 text-right font-bold ${item.margen_porcentaje >= 0 ? 'text-green-600' : 'text-red-500'}`}>
                                                        {fmtPorcentaje(item.margen_porcentaje)}
                                                    </td>
                                                    <td className="px-6 py-4 text-center">
                                                        <span className="bg-gray-200 text-gray-700 py-1 px-3 rounded-full text-xs font-bold">
                                                            {item.conteo_documentos}
                                                        </span>
                                                    </td>
                                                </tr>

                                                {/* DRILL-DOWN */}
                                                {isExpanded && (
                                                    <tr className="bg-gray-50">
                                                        <td colspan="7" className="p-4 pl-16">
                                                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                                                                {/* TOP PRODUCTOS */}
                                                                <div className="bg-white rounded-lg border border-gray-200 p-4">
                                                                    <h3 className="font-bold text-gray-700 mb-3 text-xs uppercase border-b pb-2">Top Productos Comprados</h3>
                                                                    <div className="overflow-y-auto max-h-[300px]">
                                                                        <table className="w-full text-xs">
                                                                            <thead>
                                                                                <tr className="text-gray-500 border-b">
                                                                                    <th className="text-left pb-2">Producto</th>
                                                                                    <th className="text-right pb-2">Cant</th>
                                                                                    <th className="text-right pb-2">Venta</th>
                                                                                    <th className="text-right pb-2">Utilidad</th>
                                                                                </tr>
                                                                            </thead>
                                                                            <tbody className="divide-y divide-gray-100">
                                                                                {item.detalle_productos.map((prod, idx) => (
                                                                                    <tr key={idx} className="hover:bg-gray-50">
                                                                                        <td className="py-2 pr-2">
                                                                                            <div className="font-medium text-gray-800">{prod.producto_nombre}</div>
                                                                                            <div className="text-gray-400 text-[10px]">{prod.producto_codigo}</div>
                                                                                        </td>
                                                                                        <td className="py-2 text-right">{fmtNumero(prod.cantidad)}</td>
                                                                                        <td className="py-2 text-right">{fmtMoneda(prod.total_venta)}</td>
                                                                                        <td className={`py-2 text-right font-bold ${prod.utilidad >= 0 ? 'text-green-600' : 'text-red-500'}`}>
                                                                                            {fmtMoneda(prod.utilidad)}
                                                                                        </td>
                                                                                    </tr>
                                                                                ))}
                                                                            </tbody>
                                                                        </table>
                                                                    </div>
                                                                </div>

                                                                {/* DOCUMENTOS */}
                                                                <div className="bg-white rounded-lg border border-gray-200 p-4">
                                                                    <h3 className="font-bold text-gray-700 mb-3 text-xs uppercase border-b pb-2">Historial de Facturas</h3>
                                                                    <div className="overflow-y-auto max-h-[300px]">
                                                                        <table className="w-full text-xs">
                                                                            <thead>
                                                                                <tr className="text-gray-500 border-b">
                                                                                    <th className="text-left pb-2">Ref</th>
                                                                                    <th className="text-center pb-2">Fecha</th>
                                                                                    <th className="text-right pb-2">Venta</th>
                                                                                    <th className="text-right pb-2">Utilidad</th>
                                                                                </tr>
                                                                            </thead>
                                                                            <tbody className="divide-y divide-gray-100">
                                                                                {item.detalle_documentos.map((doc, idx) => (
                                                                                    <tr key={idx} className="hover:bg-gray-50">
                                                                                        <td className="py-2 font-medium text-blue-600">{doc.documento_ref}</td>
                                                                                        <td className="py-2 text-center text-gray-500">{doc.fecha}</td>
                                                                                        <td className="py-2 text-right">{fmtMoneda(doc.total_venta)}</td>
                                                                                        <td className={`py-2 text-right font-bold ${doc.utilidad >= 0 ? 'text-green-600' : 'text-red-500'}`}>
                                                                                            {fmtMoneda(doc.utilidad)}
                                                                                        </td>
                                                                                    </tr>
                                                                                ))}
                                                                            </tbody>
                                                                        </table>
                                                                    </div>
                                                                </div>

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
