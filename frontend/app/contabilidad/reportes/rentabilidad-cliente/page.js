// frontend/app/contabilidad/reportes/rentabilidad-cliente/page.js
'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { 
    getRentabilidadPorCliente, 
    generarPdfRentabilidadCliente, 
    exportarCsvRentabilidadCliente 
} from '../../../../lib/reportesFacturacionService';
import { getTerceros } from '../../../../lib/terceroService';
import { 
    FaSearch, FaFilePdf, FaFileCsv, FaCalendarAlt, FaUserTie, 
    FaChartPie, FaArrowDown, FaArrowUp, FaDollarSign, FaPercentage,
    FaExclamationTriangle, FaChevronDown, FaChevronUp, FaBoxOpen, FaFileInvoice
} from 'react-icons/fa';
import Select from 'react-select';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { motion, AnimatePresence } from 'framer-motion';

// --- Helpers ---
const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-CO', { 
        style: 'currency', 
        currency: 'COP', 
        minimumFractionDigits: 0 
    }).format(value);
};

const formatPercent = (value) => {
    return `${parseFloat(value).toFixed(1)}%`;
};

// --- Sub-componentes ---

const KPICard = ({ title, value, icon: Icon, color, trend, trendValue }) => (
    <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-xl shadow-sm border border-slate-100 p-5 flex flex-col justify-between hover:shadow-md transition-shadow"
    >
        <div className="flex justify-between items-start">
            <div>
                <p className="text-slate-500 text-sm font-medium uppercase tracking-wider">{title}</p>
                <h3 className="text-2xl font-bold text-slate-800 mt-1">{value}</h3>
            </div>
            <div className={`p-3 rounded-lg ${color} bg-opacity-10 text-xl`}>
                <Icon className={color.replace('bg-', 'text-')} />
            </div>
        </div>
        {trend && (
            <div className="mt-4 flex items-center text-sm">
                <span className={`flex items-center font-semibold ${trend === 'up' ? 'text-emerald-600' : 'text-rose-600'}`}>
                    {trend === 'up' ? <FaArrowUp className="mr-1" /> : <FaArrowDown className="mr-1" />}
                    {trendValue}
                </span>
                <span className="text-slate-400 ml-2 text-xs">vs periodo anterior</span>
            </div>
        )}
    </motion.div>
);

const ABCBadge = ({ category }) => {
    const styles = {
        'A': 'bg-indigo-100 text-indigo-700 border-indigo-200',
        'B': 'bg-emerald-100 text-emerald-700 border-emerald-200',
        'C': 'bg-slate-100 text-slate-600 border-slate-200',
        'CRÍTICO': 'bg-rose-100 text-rose-700 border-rose-200 animate-pulse'
    };
    
    const labels = {
        'A': 'Tier A (Top 80%)',
        'B': 'Tier B (Top 95%)',
        'C': 'Tier C (Resto)',
        'CRÍTICO': 'CRÍTICO (Pérdida)'
    };

    return (
        <span className={`px-3 py-1 rounded-full text-xs font-bold border ${styles[category] || styles['C']}`}>
            {labels[category] || category}
        </span>
    );
};

export default function RentabilidadClienteABC() {
    // --- Estados ---
    const [filtros, setFiltros] = useState({
        fecha_inicio: new Date(new Date().getFullYear(), new Date().getMonth(), 1),
        fecha_fin: new Date(),
        tercero_ids: [],
        margen_minimo: 0,
        solo_perdidas: false
    });
    
    const [clientesOptions, setClientesOptions] = useState([]);
    const [reporteData, setReporteData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [expandedRows, setExpandedRows] = useState({});

    // --- Carga Inicial ---
    useEffect(() => {
        const fetchData = async () => {
            try {
                const data = await getTerceros();
                const list = Array.isArray(data) ? data : (data.terceros || []);
                setClientesOptions(list.map(c => ({ value: c.id, label: c.razon_social })));
                
                // Ejecutar búsqueda inicial
                handleSearch();
            } catch (err) {
                toast.error("Error al inicializar datos.");
            }
        };
        fetchData();
    }, []);

    // --- Handlers ---
    const handleSearch = async (e) => {
        if (e) e.preventDefault();
        setLoading(true);
        try {
            const params = {
                fecha_inicio: filtros.fecha_inicio.toISOString().split('T')[0],
                fecha_fin: filtros.fecha_fin.toISOString().split('T')[0],
                tercero_ids: filtros.tercero_ids.length > 0 ? filtros.tercero_ids.map(o => o.value) : null,
                margen_minimo_porcentaje: parseFloat(filtros.margen_minimo) || 0,
                mostrar_solo_perdidas: filtros.solo_perdidas
            };
            const data = await getRentabilidadPorCliente(params);
            setReporteData(data);
        } catch (err) {
            toast.error("Error al generar el análisis.");
        } finally {
            setLoading(false);
        }
    };

    const toggleRow = (id) => {
        setExpandedRows(prev => ({ ...prev, [id]: !prev[id] }));
    };

    const handleExportPdf = async () => {
        try {
            const params = {
                fecha_inicio: filtros.fecha_inicio.toISOString().split('T')[0],
                fecha_fin: filtros.fecha_fin.toISOString().split('T')[0],
                tercero_ids: filtros.tercero_ids.length > 0 ? filtros.tercero_ids.map(o => o.value) : null,
                expandir_detalles: true
            };
            const blob = await generarPdfRentabilidadCliente(params);
            const url = window.URL.createObjectURL(new Blob([blob], { type: 'application/pdf' }));
            window.open(url, '_blank');
        } catch (err) {
            toast.error("Error al generar PDF.");
        }
    };

    const handleExportCsv = async () => {
        try {
            const params = {
                fecha_inicio: filtros.fecha_inicio.toISOString().split('T')[0],
                fecha_fin: filtros.fecha_fin.toISOString().split('T')[0],
            };
            await exportarCsvRentabilidadCliente(params);
        } catch (err) {
            toast.error("Error al exportar CSV.");
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 p-4 md:p-8 space-y-8">
            <ToastContainer />
            
            {/* Header Section */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Análisis ABC de Rentabilidad</h1>
                    <p className="text-slate-500 mt-1">Gestión estratégica de clientes basada en contribución a la utilidad.</p>
                </div>
                <div className="flex gap-2">
                    <button onClick={handleExportCsv} className="flex items-center px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg hover:bg-slate-50 font-medium transition-all shadow-sm">
                        <FaFileCsv className="mr-2 text-emerald-600" /> Exportar CSV
                    </button>
                    <button onClick={handleExportPdf} className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium transition-all shadow-sm">
                        <FaFilePdf className="mr-2" /> Reporte Gerencial PDF
                    </button>
                </div>
            </div>

            {/* Filter Section */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
                <form onSubmit={handleSearch} className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div className="space-y-2">
                        <label className="text-xs font-bold text-slate-500 uppercase flex items-center">
                            <FaCalendarAlt className="mr-1" /> Rango de Fecha
                        </label>
                        <div className="flex gap-2">
                            <DatePicker
                                selected={filtros.fecha_inicio}
                                onChange={(date) => setFiltros(f => ({...f, fecha_inicio: date}))}
                                className="w-full text-sm border-slate-200 rounded-lg"
                                dateFormat="dd/MM/yyyy"
                            />
                            <DatePicker
                                selected={filtros.fecha_fin}
                                onChange={(date) => setFiltros(f => ({...f, fecha_fin: date}))}
                                className="w-full text-sm border-slate-200 rounded-lg"
                                dateFormat="dd/MM/yyyy"
                            />
                        </div>
                    </div>
                    
                    <div className="space-y-2">
                        <label className="text-xs font-bold text-slate-500 uppercase flex items-center">
                            <FaUserTie className="mr-1" /> Clientes Específicos
                        </label>
                        <Select
                            isMulti
                            options={clientesOptions}
                            value={filtros.tercero_ids}
                            onChange={(vals) => setFiltros(f => ({...f, tercero_ids: vals || []}))}
                            placeholder="Todos los clientes..."
                            className="text-sm"
                            theme={(theme) => ({ ...theme, borderRadius: 8 })}
                        />
                    </div>

                    <div className="space-y-2">
                        <label className="text-xs font-bold text-slate-500 uppercase flex items-center">
                            <FaPercentage className="mr-1" /> Margen Mínimo %
                        </label>
                        <input 
                            type="number"
                            value={filtros.margen_minimo}
                            onChange={(e) => setFiltros(f => ({...f, margen_minimo: e.target.value}))}
                            className="w-full text-sm border-slate-200 rounded-lg h-[38px] placeholder-slate-400"
                            placeholder="Ej: 15"
                        />
                    </div>

                    <div className="flex items-end">
                        <button 
                            type="submit" 
                            disabled={loading}
                            className="w-full bg-slate-900 text-white rounded-lg h-[38px] hover:bg-slate-800 transition-colors flex items-center justify-center font-bold"
                        >
                            {loading ? <div className="animate-spin h-5 w-5 border-2 border-white/30 border-t-white rounded-full" /> : <><FaSearch className="mr-2"/> ANALIZAR NEGOCIO</>}
                        </button>
                    </div>
                </form>
            </div>

            {/* KPI Cards Section */}
            {reporteData && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <KPICard 
                        title="Ventas Totales" 
                        value={formatCurrency(reporteData.gran_total_venta)} 
                        icon={FaDollarSign} 
                        color="bg-blue-500" 
                    />
                    <KPICard 
                        title="Utilidad Total" 
                        value={formatCurrency(reporteData.gran_total_utilidad)} 
                        icon={FaArrowUp} 
                        color={reporteData.gran_total_utilidad >= 0 ? "bg-emerald-500" : "bg-rose-500"} 
                    />
                    <KPICard 
                        title="Margen Promedio" 
                        value={formatPercent(reporteData.margen_global_porcentaje)} 
                        icon={FaPercentage} 
                        color="bg-indigo-500" 
                    />
                    <KPICard 
                        title="Clientes 'A' (Core)" 
                        value={reporteData.conteo_clientes_a} 
                        icon={FaUserTie} 
                        color="bg-amber-500" 
                    />
                </div>
            )}

            {/* Main Content: ABC Analysis Table */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
                <div className="p-6 border-b border-slate-50 flex flex-col md:flex-row justify-between items-center gap-4">
                    <h2 className="text-xl font-bold text-slate-800 flex items-center">
                        <FaChartPie className="mr-2 text-indigo-500" /> Clasificación de Rentabilidad ABC
                    </h2>
                    <div className="flex items-center gap-3">
                        <label className="flex items-center text-sm font-medium text-slate-600 cursor-pointer">
                            <input 
                                type="checkbox" 
                                checked={filtros.solo_perdidas}
                                onChange={(e) => setFiltros(f => ({...f, solo_perdidas: e.target.checked}))}
                                className="mr-2 rounded text-indigo-600 focus:ring-indigo-500"
                            />
                            Mostrar solo críticos (Pérdidas)
                        </label>
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-slate-50 text-slate-600 text-xs font-bold uppercase">
                                <th className="px-6 py-4 w-12 text-center">ABC</th>
                                <th className="px-6 py-4 min-w-[200px]">Cliente</th>
                                <th className="px-6 py-4 text-right">Venta</th>
                                <th className="px-6 py-4 text-right">Utilidad</th>
                                <th className="px-6 py-4 text-center">
                                    <div className="flex flex-col items-center">
                                        <span>% Vta</span>
                                    </div>
                                </th>
                                <th className="px-6 py-4 text-center">
                                    <div className="flex flex-col items-center">
                                        <span>% Ut</span>
                                    </div>
                                </th>
                                <th className="px-6 py-4 text-center">Margen</th>
                                <th className="px-6 py-4 text-center">Acción</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 italic text-sm">
                            {loading ? (
                                <tr>
                                    <td colSpan="8" className="px-6 py-12 text-center text-slate-400">
                                        <div className="flex flex-col items-center gap-2">
                                            <div className="animate-spin h-8 w-8 border-4 border-indigo-200 border-t-indigo-600 rounded-full" />
                                            <span>Analizando rentabilidad...</span>
                                        </div>
                                    </td>
                                </tr>
                            ) : reporteData?.items?.length > 0 ? (
                                reporteData.items.map((item) => (
                                    <React.Fragment key={item.tercero_id}>
                                        <tr className={`hover:bg-slate-50 transition-colors group ${item.total_utilidad < 0 ? 'bg-rose-50/30' : ''}`}>
                                            <td className="px-6 py-4 text-center">
                                                <ABCBadge category={item.categoria_abc} />
                                            </td>
                                            <td className="px-6 py-4">
                                                <div className="flex flex-col">
                                                    <span className="font-bold text-slate-800">{item.tercero_nombre}</span>
                                                    <span className="text-[10px] text-slate-400 font-mono uppercase">{item.tercero_identificacion}</span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 text-right font-medium text-slate-700">
                                                {formatCurrency(item.total_venta)}
                                            </td>
                                            <td className={`px-6 py-4 text-right font-bold ${item.total_utilidad < 0 ? 'text-rose-600' : 'text-slate-800'}`}>
                                                {formatCurrency(item.total_utilidad)}
                                                {item.total_utilidad < 0 && <FaExclamationTriangle className="inline ml-1 mb-1" />}
                                            </td>
                                            <td className="px-6 py-4 text-center text-slate-500 font-medium">
                                                {item.participacion_vta.toFixed(0)}%
                                            </td>
                                            <td className={`px-6 py-4 text-center font-bold ${item.total_utilidad < 0 ? 'text-rose-600' : 'text-indigo-600'}`}>
                                                {item.total_utilidad < 0 ? `-${item.participacion_util.toFixed(0)}%` : `${item.participacion_util.toFixed(0)}%`}
                                            </td>
                                            <td className="px-6 py-4 text-center">
                                                <div className="flex items-center justify-center">
                                                    <div className="w-16 h-1.5 bg-slate-100 rounded-full mr-2 overflow-hidden">
                                                        <div 
                                                            className={`h-full rounded-full ${item.margen_porcentaje < 10 ? 'bg-rose-500' : item.margen_porcentaje < 20 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                                                            style={{ width: `${Math.min(Math.max(item.margen_porcentaje, 0), 100)}%` }}
                                                        />
                                                    </div>
                                                    <span className="text-[10px] font-bold text-slate-600">{item.margen_porcentaje.toFixed(0)}%</span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 text-center">
                                                <button 
                                                    onClick={() => toggleRow(item.tercero_id)}
                                                    className="p-2 hover:bg-white rounded-md text-slate-400 hover:text-indigo-600 transition-all border border-transparent hover:border-slate-100"
                                                >
                                                    {expandedRows[item.tercero_id] ? <FaChevronUp /> : <FaChevronDown />}
                                                </button>
                                            </td>
                                        </tr>
                                        {/* Row Expandida: Detalles */}
                                        <AnimatePresence>
                                            {expandedRows[item.tercero_id] && (
                                                <tr>
                                                    <td colSpan="8" className="px-6 py-0 border-none">
                                                        <motion.div 
                                                            initial={{ opacity: 0, height: 0 }}
                                                            animate={{ opacity: 1, height: 'auto' }}
                                                            exit={{ opacity: 0, height: 0 }}
                                                            className="overflow-hidden bg-slate-50/50 rounded-b-xl mb-4 border border-t-0 border-slate-100"
                                                        >
                                                            <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-8">
                                                                {/* Top Productos Componente */}
                                                                <div className="space-y-3">
                                                                    <div className="flex items-center text-slate-700 font-bold text-sm uppercase tracking-wider">
                                                                        <FaBoxOpen className="mr-2 text-indigo-400" /> Top Productos Comprados
                                                                    </div>
                                                                    <div className="bg-white rounded-lg shadow-sm border border-slate-100 overflow-hidden">
                                                                        <table className="w-full text-xs">
                                                                            <thead className="bg-slate-50 text-slate-500">
                                                                                <tr>
                                                                                    <th className="px-3 py-2">Código</th>
                                                                                    <th className="px-3 py-2">Nombre</th>
                                                                                    <th className="px-3 py-2 text-center">Cant</th>
                                                                                    <th className="px-3 py-2 text-right">Margen</th>
                                                                                </tr>
                                                                            </thead>
                                                                            <tbody className="divide-y divide-slate-50">
                                                                                {item.detalle_productos.slice(0, 5).map(prod => (
                                                                                    <tr key={prod.producto_id}>
                                                                                        <td className="px-3 py-2 font-mono text-slate-400">{prod.producto_codigo}</td>
                                                                                        <td className="px-3 py-2 font-medium">{prod.producto_nombre}</td>
                                                                                        <td className="px-3 py-2 text-center text-slate-600">{prod.cantidad}</td>
                                                                                        <td className={`px-3 py-2 text-right font-bold ${prod.margen < 0 ? 'text-rose-500' : 'text-emerald-600'}`}>{prod.margen.toFixed(1)}%</td>
                                                                                    </tr>
                                                                                ))}
                                                                            </tbody>
                                                                        </table>
                                                                    </div>
                                                                </div>

                                                                {/* Documentos Historial */}
                                                                <div className="space-y-3">
                                                                    <div className="flex items-center text-slate-700 font-bold text-sm uppercase tracking-wider">
                                                                        <FaFileInvoice className="mr-2 text-indigo-400" /> Trazabilidad de Facturación
                                                                    </div>
                                                                    <div className="bg-white rounded-lg shadow-sm border border-slate-100 overflow-hidden">
                                                                        <table className="w-full text-xs">
                                                                             <thead className="bg-slate-50 text-slate-500">
                                                                                <tr>
                                                                                    <th className="px-3 py-2">Factura</th>
                                                                                    <th className="px-3 py-2">Fecha</th>
                                                                                    <th className="px-3 py-2 text-right">Venta</th>
                                                                                    <th className="px-3 py-2 text-right">Utilidad</th>
                                                                                </tr>
                                                                            </thead>
                                                                            <tbody className="divide-y divide-slate-50">
                                                                                {item.detalle_documentos.slice(0, 5).map(doc => (
                                                                                    <tr key={doc.documento_id}>
                                                                                        <td className="px-3 py-2 font-bold text-indigo-600">{doc.documento_ref}</td>
                                                                                        <td className="px-3 py-2 text-slate-500">{new Date(doc.fecha).toLocaleDateString()}</td>
                                                                                        <td className="px-3 py-2 text-right font-medium text-slate-700">{formatCurrency(doc.total_venta)}</td>
                                                                                        <td className={`px-3 py-2 text-right font-bold ${doc.utilidad < 0 ? 'text-rose-500' : 'text-slate-800'}`}>{formatCurrency(doc.utilidad)}</td>
                                                                                    </tr>
                                                                                ))}
                                                                            </tbody>
                                                                        </table>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        </motion.div>
                                                    </td>
                                                </tr>
                                            )}
                                        </AnimatePresence>
                                    </React.Fragment>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan="8" className="px-6 py-12 text-center text-slate-400 italic">
                                        No se encontraron datos para los filtros seleccionados.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* ABC Footer Description */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-sm text-slate-500">
                <div className="bg-indigo-50/50 rounded-xl p-6 border border-indigo-100">
                    <h4 className="font-bold text-indigo-900 mb-2">Entendiendo la Clasificación ABC</h4>
                    <ul className="space-y-2">
                        <li><span className="font-bold text-indigo-700">Tier A:</span> Representa el core de tu negocio. El 20% de tus clientes que generan el 80% de la utilidad. ¡Cuídalos!</li>
                        <li><span className="font-bold text-emerald-700">Tier B:</span> Clientes con potencial. Representan el siguiente 15% de la utilidad total.</li>
                        <li><span className="font-bold text-slate-700">Tier C:</span> Clientes residuales. Aportan poco a la utilidad total pero requieren gestión administrativa.</li>
                    </ul>
                </div>
                <div className="bg-rose-50/50 rounded-xl p-6 border border-rose-100">
                    <h4 className="font-bold text-rose-900 mb-2">Alertas Criticas</h4>
                    <p>Los clientes marcados como <span className="font-extrabold text-rose-600">CRÍTICO</span> han generado una utilidad negativa en el periodo analizado. Esto significa que los costos operativos/venta superaron los ingresos facturados. Se recomienda revisar precios o costos de adquisición urgentemente.</p>
                </div>
            </div>

            <style jsx global>{`
                .react-datepicker-wrapper { width: 100%; }
                .animate-pulse {
                    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
                }
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: .7; }
                }
            `}</style>
        </div>
    );
}
