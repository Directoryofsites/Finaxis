"use client";
import React, { useState, useEffect } from 'react';
import { getHistorial, downloadDesprendible, deleteDesprendible } from '../../../lib/nominaService';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { FaFileInvoiceDollar, FaDownload, FaSearch, FaTrash, FaFilter } from 'react-icons/fa';

export default function DesprendiblesPage() {
    const [historial, setHistorial] = useState([]);
    const [loading, setLoading] = useState(false);
    const [downloading, setDownloading] = useState(null);
    const [deleting, setDeleting] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        setLoading(true);
        try {
            const data = await getHistorial();
            setHistorial(data);
        } catch (error) {
            toast.error("Error cargando historial");
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

    // --- FILTER LOGIC ---
    const filteredHistorial = historial.filter(item => {
        const term = searchTerm.toLowerCase();
        return (
            item.empleado.toLowerCase().includes(term) ||
            item.documento.toLowerCase().includes(term) ||
            item.periodo.toLowerCase().includes(term)
        );
    });

    return (
        <div className="p-8 max-w-7xl mx-auto">
            <ToastContainer />
            <div className="flex flex-col md:flex-row justify-between items-center mb-6 gap-4">
                <h1 className="text-2xl font-light text-gray-800 flex items-center">
                    <FaFileInvoiceDollar className="mr-3 text-purple-600" /> Histórico de Desprendibles
                </h1>

                <div className="flex gap-2 w-full md:w-auto">
                    <div className="relative w-full md:w-64">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <FaSearch className="text-gray-400" />
                        </div>
                        <input
                            type="text"
                            placeholder="Buscar empleado, periodo..."
                            className="pl-10 pr-4 py-2 border rounded shadow-sm w-full focus:ring-2 focus:ring-purple-300 outline-none transition"
                            value={searchTerm}
                            onChange={e => setSearchTerm(e.target.value)}
                        />
                    </div>
                    <button onClick={loadData} className="text-blue-600 hover:text-blue-800 font-medium text-sm px-3">Refrescar</button>
                </div>
            </div>

            <div className="bg-white rounded-lg shadow-md overflow-hidden border border-gray-100">
                <table className="w-full text-left">
                    <thead className="bg-gray-50 text-gray-600 uppercase text-xs font-semibold tracking-wider">
                        <tr>
                            <th className="p-4 border-b">Periodo</th>
                            <th className="p-4 border-b">Empleado</th>
                            <th className="p-4 border-b">Documento</th>
                            <th className="p-4 border-b text-right">Neto Pagado</th>
                            <th className="p-4 border-b text-center">Acciones</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {filteredHistorial.map(item => (
                            <tr key={item.id} className="hover:bg-purple-50 transition duration-150">
                                <td className="p-4 whitespace-nowrap">
                                    <span className="bg-purple-100 text-purple-800 py-1 px-2 rounded text-xs font-bold">{item.periodo}</span>
                                </td>
                                <td className="p-4 font-medium text-gray-900">{item.empleado}</td>
                                <td className="p-4 text-gray-500 text-sm">{item.documento}</td>
                                <td className="p-4 text-right font-mono text-green-700 font-bold">
                                    {new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(item.neto)}
                                </td>
                                <td className="p-4 flex justify-center gap-2">
                                    <button
                                        onClick={() => handleDownload(item)}
                                        disabled={downloading === item.id}
                                        title="Descargar PDF"
                                        className="bg-purple-100 text-purple-700 hover:bg-purple-200 p-2 rounded-full transition shadow-sm"
                                    >
                                        <FaDownload className={`${downloading === item.id ? 'animate-bounce' : ''}`} size={14} />
                                    </button>
                                    <button
                                        onClick={() => handleDelete(item)}
                                        disabled={deleting === item.id}
                                        title="Eliminar Liquidación"
                                        className="bg-red-100 text-red-600 hover:bg-red-200 p-2 rounded-full transition shadow-sm"
                                    >
                                        <FaTrash size={14} />
                                    </button>
                                </td>
                            </tr>
                        ))}
                        {filteredHistorial.length === 0 && !loading && (
                            <tr><td colSpan="5" className="p-12 text-center text-gray-400 italic">No se encontraron resultados.</td></tr>
                        )}
                        {loading && (
                            <tr><td colSpan="5" className="p-12 text-center text-gray-400">Cargando...</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
            <div className="mt-4 text-right text-xs text-gray-400">
                Mostrando {filteredHistorial.length} registros
            </div>
        </div>
    );
}
