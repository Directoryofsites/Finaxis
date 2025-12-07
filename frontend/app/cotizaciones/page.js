'use client';
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { apiService } from '../../lib/apiService';
import { FaCalendarAlt, FaSearch, FaFilter, FaTimes, FaFileContract, FaPlus } from 'react-icons/fa';
import BotonRegresar from '../components/BotonRegresar';

export default function CotizacionesListPage() {
    const [cotizaciones, setCotizaciones] = useState([]);
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
        fetchCotizaciones();
    }, []);

    const fetchMaestros = async () => {
        try {
            const res = await apiService.get('/terceros/');
            setMaestros({ terceros: res.data });
        } catch (err) {
            console.error("Error loading filters", err);
        }
    };

    const fetchCotizaciones = async () => {
        setLoading(true);
        try {
            const params = {};
            if (filtros.numero) params.numero = filtros.numero;
            if (filtros.tercero) params.tercero = filtros.tercero;
            if (filtros.estado) params.estado = filtros.estado;
            if (filtros.fechaInicio) params.fecha_inicio = filtros.fechaInicio.toISOString().split('T')[0];
            if (filtros.fechaFin) params.fecha_fin = filtros.fechaFin.toISOString().split('T')[0];

            const res = await apiService.get('/cotizaciones/', { params });
            if (res.data && res.data.cotizaciones) {
                setCotizaciones(res.data.cotizaciones);
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
        fetchCotizaciones();
    };

    const handleClearFilters = () => {
        setFiltros({
            numero: '',
            tercero: '',
            estado: '',
            fechaInicio: null,
            fechaFin: null
        });
        fetchCotizaciones_Direct({});
    };

    const fetchCotizaciones_Direct = async (overrideParams) => {
        setLoading(true);
        try {
            const res = await apiService.get('/cotizaciones/', { params: overrideParams });
            if (res.data && res.data.cotizaciones) {
                setCotizaciones(res.data.cotizaciones);
            }
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const inputClass = "w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm px-3 py-2 border";

    return (
        <div className="p-6 max-w-7xl mx-auto">
            <div className="flex justify-between items-center mb-6">
                <div className="flex items-center gap-4">
                    <BotonRegresar href="/" />
                    <h1 className="text-2xl font-bold text-gray-800">Cotizaciones</h1>
                </div>
                <div className="flex gap-2">
                    <Link href="/cotizaciones/crear" className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 font-medium flex items-center gap-2">
                        <FaPlus /> Nueva Cotización
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
                            <option value="FACTURADA">Facturada</option>
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
                        className="bg-blue-600 text-white px-6 py-2 rounded-lg shadow-sm hover:bg-blue-700 font-semibold flex items-center gap-2"
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
                            <th className="px-6 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider">Total Est.</th>
                            <th className="px-6 py-3 text-center text-xs font-bold text-gray-500 uppercase tracking-wider">Estado</th>
                            <th className="px-6 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider">Acciones</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {loading ? (
                            <tr><td colSpan="6" className="text-center py-8 text-gray-500">Cargando cotizaciones...</td></tr>
                        ) : cotizaciones.length === 0 ? (
                            <tr><td colSpan="6" className="text-center py-8 text-gray-500">No se encontraron cotizaciones.</td></tr>
                        ) : (
                            cotizaciones.map((cot) => (
                                <tr key={cot.id} className="hover:bg-gray-50 transition-colors">
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 border-l-4 border-transparent hover:border-blue-500">
                                        <Link href={`/cotizaciones/crear?cotizacion_id=${cot.id}`} className="text-blue-600 hover:text-blue-900">
                                            #{cot.numero}
                                        </Link>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{cot.fecha}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-medium">{cot.tercero_nombre}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900 font-bold">
                                        {(cot.total_estimado || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP' })}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-center">
                                        <EstadoBadge estado={cot.estado} />
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                        <Link href={`/cotizaciones/crear?cotizacion_id=${cot.id}`} className="text-blue-600 hover:text-blue-900 bg-blue-50 px-3 py-1 rounded-md">Ver / Editar</Link>
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
        'APROBADA': 'bg-blue-100 text-blue-800 border-blue-200', // Blue for offer ready
        'FACTURADA': 'bg-green-100 text-green-800 border-green-200', // Green for success
        'ANULADA': 'bg-red-100 text-red-800 border-red-200'
    };

    return (
        <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full border ${styles[estado] || 'bg-gray-100 text-gray-800'}`}>
            {estado}
        </span>
    );
}
