'use client';
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { apiService } from '../../lib/apiService';
import { FaCalendarAlt, FaSearch, FaFilter, FaTimes, FaFileContract } from 'react-icons/fa';


export default function RemisionesListPage() {
    const [remisiones, setRemisiones] = useState([]);
    const [loading, setLoading] = useState(true);
    const [maestros, setMaestros] = useState({ terceros: [] });

    // Filters State
    const [filtros, setFiltros] = useState({
        numero: '',
        tercero: '',
        estado: '',
        fechaInicio: null,
        fechaFin: null
    });

    useEffect(() => {
        fetchMaestros();
        fetchRemisiones();
    }, []);

    const fetchMaestros = async () => {
        try {
            const res = await apiService.get('/terceros/');
            setMaestros({ terceros: res.data });
        } catch (err) {
            console.error("Error loading filters", err);
        }
    };

    const fetchRemisiones = async () => {
        setLoading(true);
        try {
            const params = {};
            if (filtros.numero) params.numero = filtros.numero;
            if (filtros.tercero) params.tercero = filtros.tercero;
            if (filtros.estado) params.estado = filtros.estado;
            if (filtros.fechaInicio) params.fecha_inicio = filtros.fechaInicio.toISOString().split('T')[0];
            if (filtros.fechaFin) params.fecha_fin = filtros.fechaFin.toISOString().split('T')[0];

            const res = await apiService.get('/remisiones/', { params });
            if (res.data && res.data.remisiones) {
                setRemisiones(res.data.remisiones);
            }
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleFilterChange = (field, value) => {
        setFiltros(prev => ({ ...prev, [field]: value }));
    };

    const handleSearch = () => {
        fetchRemisiones();
    };

    const handleClearFilters = () => {
        setFiltros({
            numero: '',
            tercero: '',
            estado: '',
            fechaInicio: null,
            fechaFin: null
        });
        // Reset search
        fetchRemisiones_Direct({});
    };

    const fetchRemisiones_Direct = async (overrideParams) => {
        setLoading(true);
        try {
            const res = await apiService.get('/remisiones/', { params: overrideParams });
            if (res.data && res.data.remisiones) {
                setRemisiones(res.data.remisiones);
            }
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleDownloadPDF = async () => {
        try {
            const params = {};
            if (filtros.numero) params.numero = filtros.numero;
            if (filtros.tercero) params.tercero = filtros.tercero;
            if (filtros.estado) params.estado = filtros.estado;
            if (filtros.fechaInicio) params.fecha_inicio = filtros.fechaInicio.toISOString().split('T')[0];
            if (filtros.fechaFin) params.fecha_fin = filtros.fechaFin.toISOString().split('T')[0];

            const response = await apiService.get('/remisiones/pdf/listado', {
                params,
                responseType: 'blob'
            });

            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', 'Listado_Remisiones.pdf');
            document.body.appendChild(link);
            link.click();
            link.parentNode.removeChild(link);
        } catch (error) {
            console.error("Error downloading PDF", error);
        }
    };

    const inputClass = "w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm px-3 py-2 border";


    return (
        <div className="p-6 max-w-7xl mx-auto">
            <div className="flex justify-between items-center mb-6">
                <div className="flex items-center gap-4">
                    <h1 className="text-2xl font-bold text-gray-800">Remisiones</h1>
                </div>
                <div className="flex gap-2">
                    <button onClick={handleDownloadPDF} className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 flex items-center gap-2 font-medium">
                        <FaFileContract /> PDF
                    </button>
                    {/* Removed Ver Reportes link */}
                    <Link href="/remisiones/crear" className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700 font-medium">
                        Nueva Remisión
                    </Link>
                </div>
            </div>

            {/* FILTROS */}
            <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-200 mb-6">
                <div className="flex items-center gap-2 mb-4 text-gray-500">
                    <FaFilter />
                    <span className="text-sm font-bold uppercase tracking-wider">Filtros de Búsqueda</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-6 gap-4 items-end">
                    <div>
                        <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Número</label>
                        <input
                            type="number"
                            className={inputClass}
                            placeholder="#"
                            value={filtros.numero}
                            onChange={(e) => handleFilterChange('numero', e.target.value)}
                        />
                    </div>
                    <div className="col-span-1 md:col-span-2">
                        <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Cliente</label>
                        <select
                            className={`${inputClass} bg-white`}
                            value={filtros.tercero}
                            onChange={(e) => handleFilterChange('tercero', e.target.value)}
                        >
                            <option value="">Todos los clientes</option>
                            {maestros.terceros.map(t => (
                                <option key={t.id} value={t.id}>{t.razon_social} ({t.numero_identificacion})</option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Estado</label>
                        <select
                            className={`${inputClass} bg-white`}
                            value={filtros.estado}
                            onChange={(e) => handleFilterChange('estado', e.target.value)}
                        >
                            <option value="">Todos</option>
                            <option value="BORRADOR">Borrador</option>
                            <option value="APROBADA">Aprobada</option>
                            <option value="FACTURADA_PARCIAL">Fact. Parcial</option>
                            <option value="FACTURADA_TOTAL">Fact. Total</option>
                            <option value="ANULADA">Anulada</option>
                        </select>
                    </div>
                    {/* FECHAS */}
                    <div className="col-span-1 md:col-span-2 grid grid-cols-2 gap-2">
                        <div>
                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Desde</label>
                            <div className="relative">
                                <DatePicker
                                    selected={filtros.fechaInicio}
                                    onChange={(date) => handleFilterChange('fechaInicio', date)}
                                    className={inputClass}
                                    dateFormat="dd/MM/yyyy"
                                    placeholderText="Inicio"
                                />
                            </div>
                        </div>
                        <div>
                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Hasta</label>
                            <div className="relative">
                                <DatePicker
                                    selected={filtros.fechaFin}
                                    onChange={(date) => handleFilterChange('fechaFin', date)}
                                    className={inputClass}
                                    dateFormat="dd/MM/yyyy"
                                    placeholderText="Fin"
                                />
                            </div>
                        </div>
                    </div>
                </div>

                <div className="flex justify-end gap-3 mt-4 border-t border-gray-100 pt-4">
                    <button
                        onClick={handleClearFilters}
                        className="text-gray-600 hover:text-gray-800 px-4 py-2 text-sm font-semibold flex items-center gap-2"
                    >
                        <FaTimes /> Limpiar
                    </button>
                    <button
                        onClick={handleSearch}
                        className="bg-indigo-600 text-white px-6 py-2 rounded-lg shadow-sm hover:bg-indigo-700 font-semibold flex items-center gap-2"
                    >
                        <FaSearch /> Buscar
                    </button>
                </div>
            </div>

            {/* TABLA */}
            <div className="bg-white shadow-sm rounded-xl border border-gray-200 overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Número</th>
                            <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Fecha</th>
                            <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Cliente</th>
                            <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Bodega</th>
                            <th className="px-6 py-3 text-center text-xs font-bold text-gray-500 uppercase tracking-wider">Estado</th>
                            <th className="px-6 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider">Acciones</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {loading ? (
                            <tr><td colSpan="6" className="text-center py-8 text-gray-500">Cargando remisiones...</td></tr>
                        ) : remisiones.length === 0 ? (
                            <tr><td colSpan="6" className="text-center py-8 text-gray-500">No se encontraron remisiones con los filtros seleccionados.</td></tr>
                        ) : (
                            remisiones.map((rem) => (
                                <tr key={rem.id} className="hover:bg-gray-50 transition-colors">
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 border-l-4 border-transparent hover:border-indigo-500">
                                        <Link href={`/remisiones/detalle/${rem.id}`} className="text-indigo-600 hover:text-indigo-900">
                                            #{rem.numero}
                                        </Link>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{rem.fecha}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-medium">{rem.tercero_nombre}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{rem.bodega_nombre}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-center">
                                        <EstadoBadge estado={rem.estado} />
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                        <Link href={`/remisiones/detalle/${rem.id}`} className="text-indigo-600 hover:text-indigo-900 bg-indigo-50 px-3 py-1 rounded-md">Ver Detalle</Link>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function EstadoBadge({ estado }) {
    const styles = {
        'BORRADOR': 'bg-gray-100 text-gray-800 border-gray-200',
        'APROBADA': 'bg-green-100 text-green-800 border-green-200',
        'FACTURADA_PARCIAL': 'bg-blue-100 text-blue-800 border-blue-200',
        'FACTURADA_TOTAL': 'bg-blue-800 text-white border-blue-900',
        'ANULADA': 'bg-red-100 text-red-800 border-red-200',
        'VENCIDA': 'bg-orange-100 text-orange-800 border-orange-200'
    };

    return (
        <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full border ${styles[estado] || 'bg-gray-100 text-gray-800'}`}>
            {estado}
        </span>
    );
}
