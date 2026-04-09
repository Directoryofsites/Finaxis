// frontend/app/contabilidad/reportes/gestion-compras/page.js
// v1.0.1 - Forzando despliegue
'use client';

import React, { useState, useEffect, useMemo } from 'react';
import comprasService from '../../../../lib/comprasService';
import { getTerceros } from '../../../../lib/terceroService';
import { getProductosByEmpresa } from '../../../../lib/productosService';
import { getCentrosCosto } from '../../../../lib/centrosCostoService';
import { getBodegas } from '../../../../lib/bodegaService';
import { useReactTable, getCoreRowModel, flexRender } from '@tanstack/react-table';
import { 
    FaSearch, FaFilePdf, FaFileCsv, FaCalendarAlt, FaUser, FaBoxOpen,
    FaChartLine, FaArrowDown, FaMoneyBillWave, FaPercentage, FaShoppingCart,
    FaStore, FaWarehouse, FaSyncAlt, FaInfoCircle
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

export default function GestionComprasPage() {

    // --- Estados ---
    const [filtros, setFiltros] = useState({
        fecha_inicio: new Date(new Date().getFullYear(), new Date().getMonth(), 1),
        fecha_fin: new Date(),
        proveedor_id: null,
        producto_id: null,
        centro_costo_id: null,
        bodega_id: null,
        documento_tipo: '',
        documento_numero: ''
    });

    const [options, setOptions] = useState({
        proveedores: [],
        productos: [],
        centrosCosto: [],
        bodegas: []
    });

    const [reporteData, setReporteData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [exporting, setExporting] = useState({ pdf: false, csv: false });

    // --- Carga Inicial de Maestros ---
    useEffect(() => {
        const fetchMaestros = async () => {
            try {
                const [terceros, prods, ccs, bgs] = await Promise.all([
                    getTerceros(),
                    getProductosByEmpresa(),
                    getCentrosCosto(),
                    getBodegas()
                ]);

                setOptions({
                    proveedores: (Array.isArray(terceros) ? terceros : (terceros.terceros || [])).map(t => ({ value: t.id, label: t.razon_social })),
                    productos: (prods.productos || []).map(p => ({ value: p.id, label: p.nombre })),
                    centrosCosto: (ccs || []).map(cc => ({ value: cc.id, label: cc.nombre })),
                    bodegas: (bgs || []).map(b => ({ value: b.id, label: b.nombre }))
                });
            } catch (err) {
                toast.error("Error al cargar maestros para filtros.");
            }
        };
        fetchMaestros();
    }, []);

    // --- Handlers ---
    const handleDateChange = (name, date) => {
        setFiltros(prev => ({ ...prev, [name]: date || new Date() }));
    };

    const handleSelectChange = (name, option) => {
        setFiltros(prev => ({ ...prev, [name]: option ? option.value : null }));
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFiltros(prev => ({ ...prev, [name]: value }));
    };

    const prepareFiltros = () => ({
        ...filtros,
        fecha_inicio: filtros.fecha_inicio.toISOString().split('T')[0],
        fecha_fin: filtros.fecha_fin.toISOString().split('T')[0],
        codigo_documento: filtros.documento_tipo || null,
        numero_documento: filtros.documento_numero || null,
    });

    const handleSearch = async (e) => {
        if (e) e.preventDefault();
        setLoading(true);
        try {
            const data = await comprasService.getReporteDetallado(prepareFiltros());
            setReporteData(data);
            if (!data.items || data.items.length === 0) toast.info("No se encontraron registros de compra.");
        } catch (err) {
            toast.error('Error al generar el reporte.');
        } finally {
            setLoading(false);
        }
    };

    const handleExport = async (type) => {
        setExporting(prev => ({ ...prev, [type]: true }));
        try {
            const f = prepareFiltros();
            if (type === 'pdf') await comprasService.downloadReporteDetalladoPDF(f);
            else await comprasService.downloadReporteDetalladoCSV(f);
            toast.success(`Reporte ${type.toUpperCase()} generado.`);
        } catch (err) {
            toast.error(`Error al generar ${type.toUpperCase()}.`);
        } finally {
            setExporting(prev => ({ ...prev, [type]: false }));
        }
    };

    // --- Configuración Tabla ---
    const columns = useMemo(() => [
        { accessorKey: 'fecha', header: 'Fecha' },
        { 
            header: 'Documento', 
            accessorFn: row => `${row.tipo_documento_nombre} ${row.numero}`,
            cell: info => <span className="font-bold text-indigo-900">{info.getValue()}</span>
        },
        { accessorKey: 'proveedor_nombre', header: 'Proveedor' },
        { accessorKey: 'producto_nombre', header: 'Producto' },
        { accessorKey: 'bodega_nombre', header: 'Bodega' },
        { 
            accessorKey: 'subtotal', 
            header: 'Subtotal Base',
            cell: info => <span className={info.getValue() < 0 ? 'text-red-500 font-mono' : 'font-mono'}>{formatCurrency(info.getValue())}</span>
        },
        { 
            accessorKey: 'iva', 
            header: 'IVA',
            cell: info => <span className={info.getValue() < 0 ? 'text-red-500 font-mono' : 'font-mono'}>{formatCurrency(info.getValue())}</span>
        },
        { 
            accessorKey: 'total', 
            header: 'Total Neto',
            cell: info => <span className={`font-mono font-bold ${info.getValue() < 0 ? 'text-red-600' : 'text-slate-800'}`}>{formatCurrency(info.getValue())}</span>
        },
    ], []);

    const table = useReactTable({
        data: reporteData?.items || [],
        columns,
        getCoreRowModel: getCoreRowModel(),
    });

    // --- Chart Data ---
    const trendData = {
        labels: reporteData?.graficos?.compras_por_dia?.map(d => d.label) || [],
        datasets: [{
            label: 'Compras Diarias',
            data: reporteData?.graficos?.compras_por_dia?.map(d => d.value) || [],
            borderColor: 'rgb(59, 130, 246)',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            fill: true,
            tension: 0.3,
        }]
    };

    const providersData = {
        labels: reporteData?.graficos?.top_proveedores?.map(d => d.label) || [],
        datasets: [{
            label: 'Compras por Proveedor',
            data: reporteData?.graficos?.top_proveedores?.map(d => d.value) || [],
            backgroundColor: 'rgba(99, 102, 241, 0.8)',
            borderRadius: 4,
        }]
    };

    const productsData = {
        labels: reporteData?.graficos?.top_productos?.map(d => d.label) || [],
        datasets: [{
            label: 'Compras por Producto',
            data: reporteData?.graficos?.top_productos?.map(d => d.value) || [],
            backgroundColor: 'rgba(239, 68, 68, 0.8)',
            borderRadius: 4,
        }]
    };

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true }, x: { grid: { display: false } } }
    };

    return (
        <div className="min-h-screen bg-slate-50 p-4 md:p-8 font-sans">
            <ToastContainer position="top-right" autoClose={3000} />

            {/* HEADER */}
            <div className="max-w-7xl mx-auto mb-8 animate-fadeIn">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-blue-600 rounded-xl text-white shadow-lg">
                                <FaShoppingCart className="text-2xl" />
                            </div>
                            <h1 className="text-3xl font-extrabold text-slate-800 tracking-tight">Dashboard de Compras Detallado</h1>
                        </div>
                        <p className="text-slate-500 mt-2 font-medium flex items-center gap-2">
                             <FaInfoCircle className="text-blue-400" /> Auditoría integral de adquisiciones, devoluciones e IVA discriminado.
                        </p>
                    </div>
                </div>
            </div>

            {/* FILTROS AVANZADOS */}
            <div className="max-w-7xl mx-auto mb-8 bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
                <form onSubmit={handleSearch} className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                    <div>
                        <label className="text-xs font-bold text-slate-400 uppercase mb-1.5 block">Fecha Inicio</label>
                        <DatePicker selected={filtros.fecha_inicio} onChange={date => handleDateChange('fecha_inicio', date)} dateFormat="yyyy-MM-dd" className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none text-sm" />
                    </div>
                    <div>
                        <label className="text-xs font-bold text-slate-400 uppercase mb-1.5 block">Fecha Fin</label>
                        <DatePicker selected={filtros.fecha_fin} onChange={date => handleDateChange('fecha_fin', date)} dateFormat="yyyy-MM-dd" className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none text-sm" />
                    </div>
                    <div>
                        <label className="text-xs font-bold text-slate-400 uppercase mb-1.5 block">Proveedor</label>
                        <Select options={options.proveedores} onChange={opt => handleSelectChange('proveedor_id', opt)} placeholder="Todos..." isClearable className="text-sm" />
                    </div>
                    <div>
                        <label className="text-xs font-bold text-slate-400 uppercase mb-1.5 block">Producto</label>
                        <Select options={options.productos} onChange={opt => handleSelectChange('producto_id', opt)} placeholder="Todos..." isClearable className="text-sm" />
                    </div>
                    <div>
                        <label className="text-xs font-bold text-slate-400 uppercase mb-1.5 block">Centro de Costo</label>
                        <Select options={options.centrosCosto} onChange={opt => handleSelectChange('centro_costo_id', opt)} placeholder="Todos..." isClearable className="text-sm" />
                    </div>
                    <div>
                        <label className="text-xs font-bold text-slate-400 uppercase mb-1.5 block">Bodega</label>
                        <Select options={options.bodegas} onChange={opt => handleSelectChange('bodega_id', opt)} placeholder="Todas..." isClearable className="text-sm" />
                    </div>
                    <div className="flex gap-2">
                        <div className="w-1/3">
                            <label className="text-xs font-bold text-slate-400 uppercase mb-1.5 block">Tipo Doc</label>
                            <input name="documento_tipo" value={filtros.documento_tipo} onChange={handleInputChange} placeholder="Ex: FC" className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm" />
                        </div>
                        <div className="w-2/3">
                            <label className="text-xs font-bold text-slate-400 uppercase mb-1.5 block">Número</label>
                            <input name="documento_number" value={filtros.documento_numero} onChange={handleInputChange} placeholder="Número doc..." className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm" />
                        </div>
                    </div>
                    <button type="submit" disabled={loading} className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 rounded-xl transition-all shadow-lg flex items-center justify-center gap-2">
                        {loading ? <span className="loading loading-spinner loading-sm"></span> : <><FaSearch /> Buscar Reporte</>}
                    </button>
                </form>
            </div>

            {reporteData && (
                <div className="max-w-7xl mx-auto space-y-8">
                    
                    {/* KPIs */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                            <h4 className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-1">Subtotal Base (Antes de Impuestos)</h4>
                            <p className="text-3xl font-black text-slate-800">{formatCurrency(reporteData.total_base)}</p>
                            <div className="mt-2 text-xs font-semibold text-blue-500 flex items-center gap-1"><FaBoxOpen /> Valor Neto Compras</div>
                        </div>
                        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                            <h4 className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-1">IVA Total Recuperable</h4>
                            <p className="text-3xl font-black text-blue-600">{formatCurrency(reporteData.total_iva)}</p>
                            <div className="mt-2 text-xs font-semibold text-blue-500 flex items-center gap-1"><FaPercentage /> Impuesto Discriminado</div>
                        </div>
                        <div className="bg-white p-6 rounded-2xl border-l-8 border-l-blue-600 bg-blue-50/30 border border-slate-200 shadow-sm">
                            <h4 className="text-blue-900/60 text-xs font-bold uppercase tracking-wider mb-1">Total Gran Compras (Con IVA)</h4>
                            <p className="text-3xl font-black text-blue-900">{formatCurrency(reporteData.total_general)}</p>
                            <div className="mt-2 text-xs font-semibold text-blue-900/60 flex items-center gap-1"><FaMoneyBillWave /> Total Pagado / Por Pagar</div>
                        </div>
                    </div>

                    {/* GRÁFICOS */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 col-span-1 lg:col-span-1">
                            <h3 className="text-sm font-bold text-slate-800 mb-6 flex items-center gap-2"><FaChartLine className="text-blue-500" /> Histórico Diario</h3>
                            <div className="h-64"><Line data={trendData} options={chartOptions} /></div>
                        </div>
                        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
                            <h3 className="text-sm font-bold text-slate-800 mb-6 flex items-center gap-2"><FaUser className="text-indigo-500" /> Top Proveedores</h3>
                            <div className="h-64"><Bar data={providersData} options={chartOptions} /></div>
                        </div>
                        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
                            <h3 className="text-sm font-bold text-slate-800 mb-6 flex items-center gap-2"><FaBoxOpen className="text-red-500" /> Top Productos</h3>
                            <div className="h-64"><Bar data={productsData} options={chartOptions} /></div>
                        </div>
                    </div>

                    {/* TABLA DETALLE */}
                    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                        <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
                            <h2 className="font-bold text-slate-800 flex items-center gap-2">Detalle Itemizado de Facturación y Notas</h2>
                            <div className="flex gap-2">
                                <button onClick={() => handleExport('pdf')} disabled={exporting.pdf} className="btn btn-sm btn-error text-white gap-2 font-bold rounded-lg shadow-md px-4">
                                    {exporting.pdf ? <span className="loading loading-spinner loading-xs"></span> : <FaFilePdf />} PDF
                                </button>
                                <button onClick={() => handleExport('csv')} disabled={exporting.csv} className="btn btn-sm btn-success text-white gap-2 font-bold rounded-lg shadow-md px-4">
                                    {exporting.csv ? <span className="loading loading-spinner loading-xs"></span> : <FaFileCsv />} EXCEL
                                </button>
                            </div>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-left">
                                <thead className="bg-slate-100 text-slate-600 text-[10px] font-bold uppercase tracking-wider">
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
                                        <tr key={row.id} className="hover:bg-blue-50/30 transition-colors">
                                            {row.getVisibleCells().map(cell => (
                                                <td key={cell.id} className="py-3 px-6">{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>
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
