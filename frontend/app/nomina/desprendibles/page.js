"use client";
import React, { useState, useEffect } from 'react';
import { getHistorial, downloadDesprendible } from '../../../lib/nominaService';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { FaFileInvoiceDollar, FaDownload, FaSearch } from 'react-icons/fa';

export default function DesprendiblesPage() {
    const [historial, setHistorial] = useState([]);
    const [loading, setLoading] = useState(false);
    const [downloading, setDownloading] = useState(null);

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

    return (
        <div className="p-8">
            <ToastContainer />
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-light text-gray-800 flex items-center">
                    <FaFileInvoiceDollar className="mr-3 text-purple-600" /> Histórico de Desprendibles
                </h1>
                <button onClick={loadData} className="text-blue-600 hover:underline text-sm">Refrescar Lista</button>
            </div>

            <div className="bg-white rounded shadow overflow-hidden">
                <table className="w-full text-left">
                    <thead className="bg-gray-100 text-gray-600 uppercase text-xs">
                        <tr>
                            <th className="p-4">Periodo</th>
                            <th className="p-4">Empleado</th>
                            <th className="p-4">Documento</th>
                            <th className="p-4 text-right">Neto Pagado</th>
                            <th className="p-4 text-center">Acciones</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {historial.map(item => (
                            <tr key={item.id} className="hover:bg-gray-50 transition">
                                <td className="p-4 font-bold text-gray-700">{item.periodo}</td>
                                <td className="p-4">{item.empleado}</td>
                                <td className="p-4 text-gray-500 text-sm">{item.documento}</td>
                                <td className="p-4 text-right font-mono text-green-700 font-bold">
                                    {new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(item.neto)}
                                </td>
                                <td className="p-4 flex justify-center">
                                    <button
                                        onClick={() => handleDownload(item)}
                                        disabled={downloading === item.id}
                                        className="bg-purple-100 text-purple-700 hover:bg-purple-200 px-3 py-1 rounded flex items-center text-xs font-bold transition"
                                    >
                                        <FaDownload className={`mr-2 ${downloading === item.id ? 'animate-bounce' : ''}`} />
                                        {downloading === item.id ? 'Generando...' : 'PDF'}
                                    </button>
                                </td>
                            </tr>
                        ))}
                        {historial.length === 0 && !loading && (
                            <tr><td colSpan="5" className="p-12 text-center text-gray-400">No hay nóminas guardadas aún.</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
