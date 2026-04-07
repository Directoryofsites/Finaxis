// frontend/app/contabilidad/reportes/gestion-ventas/page.js
'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { getReporteGestionVentas } from '../../../../lib/gestionVentasService';
import { getTerceros } from '../../../../lib/terceroService';
import { solicitarUrlImpresionRentabilidad } from '../../../../lib/documentoService';
import { API_URL } from '../../../../lib/apiService';
import { useReactTable, getCoreRowModel, flexRender } from '@tanstack/react-table';
import { 
    FaSearch, FaFilePdf, FaCalendarAlt, FaUser, FaFileInvoiceDollar, 
    FaChartLine, FaArrowUp, FaMoneyBillWave, FaPercentage, FaShoppingCart 
} from 'react-icons/fa';
import Select from 'react-select';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// Chart.js imports
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const formatCurrency = (value) => {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(value);
};

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
    const [loadingPdfId, setLoadingPdfId] = useState(null);

    // --- Carga Inicial ---
    useEffect(() => {
        const fetchClientes = async () => {
            try {
                const data = await getTerceros();
                const options = Array.isArray(data)
                    ? data.map(c => ({ value: c.id, label: c.razon_social }))
                    : (data.terceros || []).map(c => ({ value: c.id, label: c.razon_social }));
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
        try {
            const filtrosParaAPI = {
                fecha_inicio: filtros.fecha_inicio.toISOString().split('T')[0],
                fecha_fin: filtros.fecha_fin.toISOString().split('T')[0],
                cliente_id: filtros.cliente_id ? parseInt(filtros.cliente_id) : null,
            };
            const data = await getReporteGestionVentas(filtrosParaAPI);
            setReporteData(data);
            if (!data.items || data.items.length === 0) toast.info("No se encontraron facturas.");
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
            const absoluteUrl = response.signed_url.startsWith('http') ? response.signed_url : `${API_URL}${response.signed_url}`;
            window.open(absoluteUrl, '_blank');
        } catch (err) {
            toast.error('Error al generar PDF.');
        } finally {
            setLoadingPdfId(null);
        }
    };

    // --- Configuración Tabla ---
    const columns = useMemo(() => [
        { accessorKey: 'fecha', header: 'Fecha', cell: info => <span className="text-gray-600">{info.getValue()}</span> },
        { 
            header: 'Documento', 
            accessorFn: row => `${row.tipo_documento}-${row.numero}`,
            cell: info => <span className="font-mono font-bold text-indigo-900">{info.getValue()}</span>
        },
        { accessorKey: 'beneficiario_nombre', header: 'Cliente', cell: info => <span className="font-medium text-gray-800">{info.getValue()}</span> },
        { 
            accessorKey: 'total', 
            header: 'Total Venta',
            cell: info => <span className="font-mono font-semibold text-gray-700">{formatCurrency(info.getValue())}</span>
        },
        {
            id: 'acciones',
            header: 'Acción',
            cell: ({ row }) => (
                <div className="text-center">
                    <button
                        onClick={() => handleGenerarPdfRentabilidad(row.original.id)}
                        disabled={loadingPdfId === row.original.id}
                        className="btn btn-xs btn-outline btn-error"
                    >
                        {loadingPdfId === row.original.id ? <span className="loading loading-spinner loading-xs"></span> : <FaFilePdf />}
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

    // --- Chart Data Helpers ---
    const trendData = {
        labels: reporteData?.graficos?.ventas_por_dia?.map(d => d.label) || [],
        datasets: [{
            label: 'Ventas Diarias',
            data: reporteData?.graficos?.ventas_por_dia?.map(d => d.value) || [],
            borderColor: 'rgb(79, 70, 229)',
            backgroundColor: 'rgba(79, 70, 229, 0.1)',
            fill: true,
            tension: 0.4,
            pointRadius: 4,
            pointHoverRadius: 6,
        }]
    };

    const clientsData = {
        labels: reporteData?.graficos?.top_clientes?.map(d => d.label) || [],
        datasets: [{
            label: 'Venta por Cliente',
            data: reporteData?.graficos?.top_clientes?.map(d => d.value) || [],
            backgroundColor: 'rgba(99, 102, 241, 0.8)',
            borderRadius: 6,
        }]
    };

    const productsData = {
        labels: reporteData?.graficos?.top_productos?.map(d => d.label) || [],
        datasets: [{
            label: 'Venta por Producto',
            data: reporteData?.graficos?.top_productos?.map(d => d.value) || [],
            backgroundColor: 'rgba(16, 185, 129, 0.8)',
            borderRadius: 6,
        }]
    };

    const chartOptions = {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' } }, x: { grid: { display: false } } }
    };

    return (
        <div className="min-h-screen bg-slate-50 p-4 md:p-8 font-sans">
            <ToastContainer position="top-right" autoClose={3000} />

            {/* HEADER */}
            <div className="max-w-7xl mx-auto mb-8 animate-fadeIn">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-indigo-600 rounded-lg text-white">
                                <FaChartLine className="text-2xl" />
                            </div>
                            <h1 className="text-3xl font-extrabold text-slate-800 tracking-tight">Dashboard Gerencial de Ventas</h1>
                        </div>
                        <p className="text-slate-500 mt-2 font-medium">Análisis estratégico y control de rentabilidad en tiempo real.</p>
                    </div>
                    <button
                        onClick={() => window.open('/manual/capitulo_49_gestion_ventas.html', '_blank')}
                        className="px-4 py-2 bg-white border border-slate-200 text-slate-600 rounded-xl hover:bg-slate-50 transition-all font-bold shadow-sm flex items-center gap-2"
                    >
                        <span>📖</span> Ver Manual
                    </button>
                </div>
            </div>

            {/* FILTROS */}
            <div className="max-w-7xl mx-auto mb-8 bg-white p-6 rounded-2xl shadow-sm border border-slate-200 animate-fadeIn" style={{animationDelay: '0.1s'}}>
                <form onSubmit={handleSearch} className="grid grid-cols-1 md:grid-cols-4 gap-6 items-end">
                    <div>
                        <label className="text-xs font-bold text-slate-400 uppercase mb-2 block">Desde</label>
                        <DatePicker selected={filtros.fecha_inicio} onChange={date => handleDateChange('fecha_inicio', date)} dateFormat="yyyy-MM-dd" className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm font-semibold" />
                    </div>
                    <div>
                        <label className="text-xs font-bold text-slate-400 uppercase mb-2 block">Hasta</label>
                        <DatePicker selected={filtros.fecha_fin} onChange={date => handleDateChange('fecha_fin', date)} dateFormat="yyyy-MM-dd" className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm font-semibold" />
                    </div>
                    <div className="md:col-span-1">
                        <label className="text-xs font-bold text-slate-400 uppercase mb-2 block">Cliente</label>
                        <Select instanceId="select-cliente" options={clientesOptions} onChange={handleClienteChange} placeholder="Todos los clientes..." isClearable className="text-sm" />
                    </div>
                    <button type="submit" disabled={loading} className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2.5 rounded-xl transition-all shadow-lg shadow-indigo-200 flex items-center justify-center gap-2">
                        {loading ? <span className="loading loading-spinner loading-sm"></span> : <><FaSearch /> Actualizar Dashboard</>}
                    </button>
                </form>
            </div>

            {/* DASHBOARD CONTENT */}
            {reporteData && (
                <div className="max-w-7xl mx-auto space-y-8 animate-fadeIn" style={{animationDelay: '0.2s'}}>
                    
                    {/* KPI CARDS */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        <KPICard title="Ventas Totales" value={formatCurrency(reporteData.kpis.total_facturado)} icon={<FaMoneyBillWave />} color="indigo" />
                        <KPICard title="Utilidad Periodo" value={formatCurrency(reporteData.kpis.total_utilidad)} icon={<FaArrowUp />} color="emerald" trend={reporteData.kpis.total_utilidad < 0 ? "negative" : "positive"} />
                        <KPICard title="% Margen Prom." value={`${reporteData.kpis.margen_promedio}%`} icon={<FaPercentage />} color="amber" />
                        <KPICard title="Ticket Promedio" value={formatCurrency(reporteData.kpis.ticket_promedio)} icon={<FaShoppingCart />} color="blue" />
                    </div>

                    {/* CHARTS */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
                            <h3 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2"><FaChartLine className="text-indigo-500" /> Tendencia de Ventas Diarias</h3>
                            <div className="h-64"><Line data={trendData} options={chartOptions} /></div>
                        </div>
                        <div className="grid grid-cols-1 gap-8">
                            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
                                <h3 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2"><FaUser className="text-indigo-500" /> Top 5 Clientes</h3>
                                <div className="h-48"><Bar data={clientsData} options={chartOptions} /></div>
                            </div>
                            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
                                <h3 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2"><FaFileInvoiceDollar className="text-emerald-500" /> Top 5 Productos</h3>
                                <div className="h-48"><Bar data={productsData} options={chartOptions} /></div>
                            </div>
                        </div>
                    </div>

                    {/* DATA TABLE */}
                    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden mt-12">
                        <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
                            <h2 className="font-bold text-slate-800 flex items-center gap-2 text-xl">
                                <FaFileInvoiceDollar className="text-indigo-600" /> Detalle de Documentos
                            </h2>
                            <span className="bg-white border border-slate-200 px-3 py-1 rounded-lg text-sm font-bold text-indigo-600 shadow-sm">
                                {reporteData.items.length} Registros
                            </span>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-left">
                                <thead className="bg-indigo-50/50 text-indigo-900 text-xs font-bold uppercase tracking-wider">
                                    {table.getHeaderGroups().map(headerGroup => (
                                        <tr key={headerGroup.id}>
                                            {headerGroup.headers.map(header => (
                                                <th key={header.id} className="py-4 px-6">{flexRender(header.column.columnDef.header, header.getContext())}</th>
                                            ))}
                                        </tr>
                                    ))}
                                </thead>
                                <tbody className="divide-y divide-slate-100 text-sm">
                                    {table.getRowModel().rows.map(row => (
                                        <tr key={row.id} className="hover:bg-slate-50/80 transition-colors">
                                            {row.getVisibleCells().map(cell => (
                                                <td key={cell.id} className="py-4 px-6">{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>
                                            ))}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

function KPICard({ title, value, icon, color, trend }) {
    const colors = {
        indigo: "bg-indigo-600 shadow-indigo-100 text-indigo-600",
        emerald: "bg-emerald-600 shadow-emerald-100 text-emerald-600",
        amber: "bg-amber-500 shadow-amber-100 text-amber-500",
        blue: "bg-blue-600 shadow-blue-100 text-blue-600"
    };

    return (
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all group overflow-hidden relative">
            <div className="relative z-10">
                <div className="flex justify-between items-start mb-4">
                    <span className={`p-2.5 rounded-xl bg-slate-50 ${colors[color].split(' ')[2]} border border-slate-100 transition-colors group-hover:bg-indigo-600 group-hover:text-white`}>
                        {React.cloneElement(icon, { className: "text-xl" })}
                    </span>
                    {trend && (
                        <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${trend === 'positive' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
                            {trend === 'positive' ? 'En Meta' : 'Alerta'}
                        </span>
                    )}
                </div>
                <h4 className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-1">{title}</h4>
                <p className={`text-2xl font-black ${trend === 'negative' ? 'text-rose-600' : 'text-slate-800'}`}>{value}</p>
            </div>
            <div className={`absolute -right-4 -bottom-4 w-24 h-24 rounded-full opacity-[0.03] ${colors[color].split(' ')[0]} transition-transform group-hover:scale-150`}></div>
        </div>
    );
}