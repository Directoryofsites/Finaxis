'use client';
import React, { useState, useEffect } from 'react';
import { apiService } from '../../../lib/apiService';
import BotonRegresar from '../../components/BotonRegresar';
import { FaFileInvoice, FaSync, FaFileContract } from 'react-icons/fa';

export default function ReporteRemisionesPage() {
    const [loading, setLoading] = useState(true);
    const [data, setData] = useState([]);
    const [maestros, setMaestros] = useState({ terceros: [] });

    // Filters
    const [filtroEstado, setFiltroEstado] = useState('TODOS');
    const [filtroCliente, setFiltroCliente] = useState('');

    useEffect(() => {
        fetchMaestros();
        fetchData();
    }, []);

    const fetchMaestros = async () => {
        try {
            const res = await apiService.get('/terceros/');
            setMaestros({ terceros: res.data });
        } catch (err) {
            console.error(err);
        }
    };

    const fetchData = async () => {
        setLoading(true);
        try {
            // We fetch all remissions and flatten the details for the report
            const res = await apiService.get('/remisiones/');
            const remisiones = res.data.remisiones;

            const flatten = [];
            remisiones.forEach(r => {
                r.detalles.forEach(d => {
                    flatten.push({
                        remision_id: r.id,
                        numero: r.numero,
                        fecha: r.fecha,
                        tercero_id: r.tercero_id, // Needed for filter
                        tercero: r.tercero_nombre,
                        estado_remision: r.estado,
                        producto_id: d.producto_id,
                        producto_nombre: d.producto_nombre || `Prod ID ${d.producto_id}`, // Uses enriched name from backend
                        cantidad_solicitada: d.cantidad_solicitada,
                        cantidad_facturada: d.cantidad_facturada,
                        cantidad_pendiente: d.cantidad_pendiente,
                        precio_unitario: d.precio_unitario
                    });
                });
            });
            setData(flatten);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleDownloadPDF = async () => {
        try {
            const params = {};
            if (filtroEstado !== 'TODOS') params.filtro_estado = filtroEstado;
            if (filtroCliente) params.tercero = filtroCliente;

            const response = await apiService.get('/remisiones/pdf/reporte-completo', {
                params,
                responseType: 'blob'
            });
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', 'Reporte_Remisionado_Facturado.pdf');
            document.body.appendChild(link);
            link.click();
            link.parentNode.removeChild(link);
        } catch (error) {
            console.error("Error downloading PDF", error);
        }
    };

    const filteredData = data.filter(item => {
        let match = true;

        // Filter by Client
        if (filtroCliente && item.tercero_id !== parseInt(filtroCliente)) {
            match = false;
        }

        // Filter by State
        if (match && filtroEstado !== 'TODOS') {
            if (filtroEstado === 'PENDIENTES') {
                // Special logic for Pendientes
                if (item.cantidad_pendiente <= 0 || item.estado_remision === 'ANULADA') match = false;
            } else {
                // Exact match for other states
                if (item.estado_remision !== filtroEstado) match = false;
            }
        }

        return match;
    });

    return (
        <div className="p-6 max-w-7xl mx-auto">
            <div className="flex justify-between items-center mb-6">
                <div className="flex items-center gap-4">
                    <BotonRegresar href="/" />
                    <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                        <FaFileInvoice /> Reporte: Remisionado vs Facturado
                    </h1>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={handleDownloadPDF}
                        className="bg-red-600 text-white px-4 py-2 rounded shadow hover:bg-red-700 flex items-center gap-2 font-medium"
                    >
                        <FaFileContract /> Exportar PDF
                    </button>
                    <button
                        onClick={fetchData}
                        className="text-indigo-600 hover:text-indigo-800 flex items-center gap-2 bg-white border border-indigo-200 px-4 py-2 rounded shadow-sm"
                    >
                        <FaSync className={loading ? 'animate-spin' : ''} /> Actualizar
                    </button>
                </div>
            </div>

            <div className="mb-6 bg-white p-4 rounded-lg shadow-sm border grid grid-cols-1 md:grid-cols-2 gap-4 items-center">

                {/* Client Filter */}
                <div>
                    <label className="block font-bold text-gray-700 text-sm mb-1">Filtrar por Cliente:</label>
                    <select
                        value={filtroCliente}
                        onChange={e => setFiltroCliente(e.target.value)}
                        className="w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                    >
                        <option value="">Todos los Clientes</option>
                        {maestros.terceros.map(t => (
                            <option key={t.id} value={t.id}>{t.razon_social}</option>
                        ))}
                    </select>
                </div>

                {/* Status Filter */}
                <div>
                    <label className="block font-bold text-gray-700 text-sm mb-1">Filtrar por Estado:</label>
                    <select
                        value={filtroEstado}
                        onChange={e => setFiltroEstado(e.target.value)}
                        className="w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                    >
                        <option value="TODOS">Ver Todo</option>
                        <option value="PENDIENTES">Solo Pendientes por Facturar</option>
                        <option disabled>──────────</option>
                        <option value="BORRADOR">Borrador</option>
                        <option value="APROBADA">Aprobada</option>
                        <option value="FACTURADA_PARCIAL">Facturada Parcial</option>
                        <option value="FACTURADA_TOTAL">Facturada Total</option>
                        <option value="ANULADA">Anulada</option>
                    </select>
                </div>
            </div>

            <div className="bg-white shadow-lg rounded-lg overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-indigo-50">
                        <tr>
                            <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase">Remisión</th>
                            <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase">Fecha</th>
                            <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase">Cliente</th>
                            <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase">Producto</th>
                            <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase">Solicitado</th>
                            <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase bg-green-50">Facturado</th>
                            <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase bg-orange-50">Pendiente</th>
                            <th className="px-4 py-3 text-center text-xs font-bold text-gray-600 uppercase">Estado</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                        {filteredData.map((row, idx) => (
                            <tr key={idx} className="hover:bg-gray-50">
                                <td className="px-4 py-2 font-medium text-indigo-600">#{row.numero}</td>
                                <td className="px-4 py-2 text-sm">{row.fecha}</td>
                                <td className="px-4 py-2 text-sm">{row.tercero}</td>
                                <td className="px-4 py-2 text-sm text-gray-500">{row.producto_nombre}</td>
                                <td className="px-4 py-2 text-right font-bold">{row.cantidad_solicitada}</td>
                                <td className="px-4 py-2 text-right text-green-700 bg-green-50">{row.cantidad_facturada}</td>
                                <td className="px-4 py-2 text-right text-orange-700 font-bold bg-orange-50">{row.cantidad_pendiente}</td>
                                <td className="px-4 py-2 text-center text-xs">
                                    <span className={`px-2 py-1 rounded-full ${row.estado_remision === 'FACTURADA_TOTAL' ? 'bg-green-100 text-green-800' :
                                        row.estado_remision === 'ANULADA' ? 'bg-red-100 text-red-800' :
                                            row.cantidad_pendiente > 0 ? 'bg-orange-100 text-orange-800' : 'bg-gray-100'
                                        }`}>
                                        {row.estado_remision}
                                    </span>
                                </td>
                            </tr>
                        ))}
                        {filteredData.length === 0 && (
                            <tr>
                                <td colSpan="8" className="p-8 text-center text-gray-500">No hay datos para mostrar.</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
