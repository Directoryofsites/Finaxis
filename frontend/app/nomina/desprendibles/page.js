"use client";
import React, { useState, useEffect } from 'react';
import { getHistorial, downloadDesprendible, deleteDesprendible, getTiposNomina } from '../../../lib/nominaService';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { FaFileInvoiceDollar, FaDownload, FaSearch, FaTrash, FaFilter, FaTimes } from 'react-icons/fa';

export default function DesprendiblesPage() {
    const [historial, setHistorial] = useState([]);
    const [loading, setLoading] = useState(false);
    const [downloading, setDownloading] = useState(null);
    const [deleting, setDeleting] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');

    // State for Advanced Filters
    const currentYear = new Date().getFullYear();
    const currentMonth = new Date().getMonth() + 1;

    const [filterAnio, setFilterAnio] = useState(currentYear);
    const [filterMes, setFilterMes] = useState(currentMonth);
    const [filterTipo, setFilterTipo] = useState(''); // Empty = All

    // Catalogs
    const [tiposNomina, setTiposNomina] = useState([]);

    useEffect(() => {
        loadCatalogs();
        loadData();
    }, []);

    // Reload when filters change (optional - or use a search button. Let's use Search Button pattern for clarity or auto-reload)
    // "Consultarlo de esa manera" implies specific action. But auto-reload often feels better. 
    // Let's make a "Consultar" button to avoid too many requests if they change year then month rapidly.
    // Actually, React 18 is fast. Let's do auto-reload on useEffect dependencies for smooth UX, removing the "Consultar" button requirement unless specific.
    // But user said: "que yo pueda elegir tipo de nómina ahí... Consultarlo de esa manera". 
    // I'll stick to a "Aplicar Filtros" or just "Refrescar" reusing the loadData logic effectively.
    // Let's auto-load on mount, and then let user click "Refrescar" or Trigger it when filters change? 
    // Filters changing causing re-fetch is standard modern UX.

    useEffect(() => {
        loadData();
    }, [filterAnio, filterMes, filterTipo]);

    const loadCatalogs = async () => {
        try {
            const types = await getTiposNomina();
            setTiposNomina(types);
        } catch (error) {
            console.error("Error loading types", error);
        }
    };

    const loadData = async () => {
        setLoading(true);
        try {
            const params = {
                anio: filterAnio,
                mes: filterMes,
                tipo_nomina_id: filterTipo || undefined
            };
            const data = await getHistorial(params);
            setHistorial(data);
        } catch (error) {
            toast.error("Error cargando historial");
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleDownload = async (item) => {
        setDownloading(item.id);
        try {
            const filename = `Nomina_${item.documento}_${item.periodo}.pdf`;
            await downloadDesprendible(item.id, filename);
            toast.success("Descarga iniciada");
        } catch (error) {
            toast.error("Error descargando PDF");
        } finally {
            setDownloading(null);
        }
    };

    const handleDelete = async (item) => {
        if (!window.confirm(`¿Está seguro de eliminar el desprendible de ${item.empleado} (${item.periodo})? Esto permitirá volver a liquidarlo.`)) return;

        setDeleting(item.id);
        try {
            await deleteDesprendible(item.id);
            toast.success("Desprendible eliminado");
            loadData(); // Reload list
        } catch (error) {
            toast.error("Error eliminando desprendible");
            console.error(error);
        } finally {
            setDeleting(null);
        }
    };

    // --- CLIENT-SIDE FILTER LOGIC (For text search on the fetched results) ---
    const filteredHistorial = historial.filter(item => {
        const term = searchTerm.toLowerCase();
        return (
            item.empleado.toLowerCase().includes(term) ||
            item.documento.toLowerCase().includes(term)
        );
    });

    // Calculate Totals
    const totalNeto = filteredHistorial.reduce((sum, item) => sum + parseFloat(item.neto || 0), 0);

    return (
        <div className="p-8 max-w-7xl mx-auto">
            <ToastContainer />

            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-light text-gray-800 flex items-center mb-2">
                    <FaFileInvoiceDollar className="mr-3 text-purple-600" /> Histórico de Desprendibles
                </h1>
                <p className="text-gray-500 text-sm pl-1">
                    Gestione y descargue los comprobantes de pago generados. Utilice los filtros para refinar su búsqueda.
                </p>
            </div>

            {/* Smart Filter Bar */}
            <div className="bg-white p-5 rounded-lg shadow-sm border border-gray-100 mb-6">
                <div className="flex flex-col lg:flex-row gap-4 items-end lg:items-center justify-between">

                    {/* Primary Filters (Server Side) */}
                    <div className="flex flex-wrap gap-4 w-full lg:w-auto">

                        {/* Periodo: Año */}
                        <div className="flex flex-col gap-1">
                            <label className="text-xs font-bold text-gray-500 uppercase">Año</label>
                            <select
                                value={filterAnio}
                                onChange={e => setFilterAnio(e.target.value)}
                                className="border border-gray-300 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-purple-200 outline-none bg-gray-50 font-medium"
                            >
                                <option value="2024">2024</option>
                                <option value="2025">2025</option>
                                <option value="2023">2023</option>
                            </select>
                        </div>

                        {/* Periodo: Mes */}
                        <div className="flex flex-col gap-1">
                            <label className="text-xs font-bold text-gray-500 uppercase">Mes</label>
                            <select
                                value={filterMes}
                                onChange={e => setFilterMes(e.target.value)}
                                className="border border-gray-300 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-purple-200 outline-none bg-gray-50 font-medium w-32"
                            >
                                {Array.from({ length: 12 }, (_, i) => (
                                    <option key={i + 1} value={i + 1}>
                                        {new Date(0, i).toLocaleString('es-ES', { month: 'long' }).charAt(0).toUpperCase() + new Date(0, i).toLocaleString('es-ES', { month: 'long' }).slice(1)}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* Tipo Nómina */}
                        <div className="flex flex-col gap-1">
                            <label className="text-xs font-bold text-gray-500 uppercase">Tipo Nómina</label>
                            <select
                                value={filterTipo}
                                onChange={e => setFilterTipo(e.target.value)}
                                className="border border-gray-300 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-purple-200 outline-none bg-gray-50 font-medium min-w-[180px]"
                            >
                                <option value="">Todos los Tipos</option>
                                {tiposNomina.map(t => (
                                    <option key={t.id} value={t.id}>{t.nombre}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {/* Secondary Search (Client Side) & Actions */}
                    <div className="flex flex-col sm:flex-row gap-3 w-full lg:w-auto items-center">
                        <div className="relative w-full sm:w-64">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <FaSearch className="text-gray-400" />
                            </div>
                            <input
                                type="text"
                                placeholder="Filtrar por nombre o cédula..."
                                className="pl-10 pr-4 py-2 border border-gray-200 rounded text-sm w-full focus:ring-2 focus:ring-purple-100 outline-none transition"
                                value={searchTerm}
                                onChange={e => setSearchTerm(e.target.value)}
                            />
                            {searchTerm && (
                                <button
                                    onClick={() => setSearchTerm('')}
                                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
                                >
                                    <FaTimes size={12} />
                                </button>
                            )}
                        </div>
                        <button
                            onClick={loadData}
                            className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded text-sm font-medium shadow-sm transition flex items-center gap-2 whitespace-nowrap"
                        >
                            <FaFilter size={12} /> Consultar
                        </button>
                    </div>
                </div>
            </div>

            {/* Results Table */}
            <div className="bg-white rounded-lg shadow-md overflow-hidden border border-gray-100">
                <table className="w-full text-left">
                    <thead className="bg-gray-50 text-gray-600 uppercase text-xs font-semibold tracking-wider">
                        <tr>
                            <th className="p-4 border-b">Periodo</th>
                            <th className="p-4 border-b">Empleado</th>
                            <th className="p-4 border-b">Documento ID</th>
                            <th className="p-4 border-b">Ref. Contable</th>
                            <th className="p-4 border-b text-right">Neto Pagado</th>
                            <th className="p-4 border-b text-center">Acciones</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {filteredHistorial.map(item => (
                            <tr key={item.id} className="hover:bg-purple-50 transition duration-150">
                                <td className="p-4 whitespace-nowrap">
                                    <div className="flex flex-col">
                                        <span className="font-bold text-gray-700 text-sm">{item.periodo}</span>
                                        <span className="text-[10px] text-gray-400 uppercase tracking-wide">Mensual</span>
                                    </div>
                                </td>
                                <td className="p-4">
                                    <div className="font-medium text-gray-900">{item.empleado}</div>
                                    {/* Placeholder for Job Title if we had it, for now just show name clearly */}
                                </td>
                                <td className="p-4 text-gray-500 text-sm font-mono">{item.documento}</td>
                                <td className="p-4 text-gray-600 text-sm font-mono">
                                    {item.doc_contable_id ? (
                                        <span className="bg-gray-100 text-gray-700 px-2 py-0.5 rounded text-xs border border-gray-200">
                                            {item.doc_contable_tipo}-{item.doc_contable_numero}
                                        </span>
                                    ) : (
                                        <span className="text-gray-300 text-xs italic">Pendiente</span>
                                    )}
                                </td>
                                <td className="p-4 text-right font-mono text-gray-900 font-bold">
                                    {new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(item.neto)}
                                </td>
                                <td className="p-4 flex justify-center gap-2">
                                    <button
                                        onClick={() => handleDownload(item)}
                                        disabled={downloading === item.id}
                                        title="Descargar Comprobante PDF"
                                        className="bg-purple-50 text-purple-600 hover:bg-purple-100 hover:text-purple-800 p-2 rounded-lg transition border border-transparent hover:border-purple-200"
                                    >
                                        <FaDownload className={`${downloading === item.id ? 'animate-bounce' : ''}`} size={14} />
                                    </button>
                                    <button
                                        onClick={() => handleDelete(item)}
                                        disabled={deleting === item.id}
                                        title="Anular y Eliminar Liquidación"
                                        className="bg-red-50 text-red-600 hover:bg-red-100 hover:text-red-800 p-2 rounded-lg transition border border-transparent hover:border-red-200"
                                    >
                                        <FaTrash size={14} />
                                    </button>
                                </td>
                            </tr>
                        ))}
                        {filteredHistorial.length === 0 && !loading && (
                            <tr>
                                <td colSpan="6" className="p-16 text-center">
                                    <div className="flex flex-col items-center justify-center text-gray-400">
                                        <FaSearch size={48} className="mb-4 text-gray-200" />
                                        <p className="text-lg font-medium text-gray-500">No se encontraron desprendibles</p>
                                        <p className="text-sm">Intente ajustar los filtros de periodo o tipo de nómina.</p>
                                    </div>
                                </td>
                            </tr>
                        )}
                        {loading && (
                            <tr><td colSpan="6" className="p-12 text-center text-purple-600 font-medium animate-pulse">Cargando resultados...</td></tr>
                        )}
                    </tbody>

                    {/* Footer Totals */}
                    {filteredHistorial.length > 0 && (
                        <tfoot className="bg-gray-50 font-semibold text-gray-700">
                            <tr>
                                <td colSpan="4" className="p-4 text-right uppercase text-xs tracking-wider">Total Pagado en Periodo:</td>
                                <td className="p-4 text-right text-green-700 text-lg border-t-2 border-purple-100">
                                    {new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(totalNeto)}
                                </td>
                                <td></td>
                            </tr>
                        </tfoot>
                    )}
                </table>
            </div>

            <div className="mt-4 flex justify-between text-xs text-gray-400">
                <span>* Los filtros de fecha aplican sobre el periodo devengado, no la fecha de pago.</span>
                <span>Mostrando {filteredHistorial.length} registros</span>
            </div>
        </div>
    );
}
