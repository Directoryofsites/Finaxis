'use client';
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { apiService } from '../../lib/apiService';
import { FaPlus, FaSearch, FaCogs, FaTractor, FaCalculator, FaFileInvoiceDollar, FaPlay } from 'react-icons/fa';
import BotonRegresar from '../components/BotonRegresar';

export default function ActivosFijosListPage() {
    const [activos, setActivos] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    // Estado para Depreciación Masiva
    const [showModalDepreciacion, setShowModalDepreciacion] = useState(false);
    const [tiposDocumento, setTiposDocumento] = useState([]);
    const [depreciacionData, setDepreciacionData] = useState({
        anio: new Date().getFullYear(),
        mes: new Date().getMonth() + 1, // Por defecto mes actual
        tipo_documento_id: ''
    });

    useEffect(() => {
        fetchActivos();
    }, []);

    // Cargar tipos de documento solo cuando se abra el modal
    useEffect(() => {
        if (showModalDepreciacion && tiposDocumento.length === 0) {
            fetchTiposDocumento();
        }
    }, [showModalDepreciacion]);

    const fetchActivos = async () => {
        setLoading(true);
        try {
            const params = {};
            if (searchTerm) params.q = searchTerm;
            const res = await apiService.get('/activos/', { params });
            setActivos(res.data);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const fetchTiposDocumento = async () => {
        try {
            const res = await apiService.get('/tipos-documento/');
            setTiposDocumento(res.data);
        } catch (error) {
            console.error("Error cargando tipos de documento:", error);
        }
    };

    const handleSearch = (e) => {
        e.preventDefault();
        fetchActivos();
    };

    const handleEjecutarDepreciacion = async (e) => {
        e.preventDefault();
        if (!depreciacionData.tipo_documento_id) {
            alert("Seleccione un tipo de documento para generar la nota contable.");
            return;
        }

        if (!confirm(`¿Está seguro de ejecutar la depreciación para ${depreciacionData.mes}/${depreciacionData.anio}? Esto generará asentios contables.`)) return;

        try {
            const res = await apiService.post('/activos/depreciar', {
                anio: parseInt(depreciacionData.anio),
                mes: parseInt(depreciacionData.mes),
                tipo_documento_id: parseInt(depreciacionData.tipo_documento_id)
            });
            alert(`✅ ¡Proceso Exitoso!\n\nSe generó el documento: #${res.data.numero}`);
            setShowModalDepreciacion(false);
            fetchActivos(); // Refrescar para ver nuevos valores (si se mostraran)
        } catch (error) {
            console.error(error);
            alert("Error al ejecutar depreciación: " + (error.response?.data?.detail || error.message));
        }
    };

    return (
        <div className="p-6 max-w-7xl mx-auto">
            <div className="flex justify-between items-center mb-8">
                <div className="flex items-center gap-4">
                    <BotonRegresar href="/" />
                    <div>
                        <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-2">
                            <FaTractor className="text-blue-600" />
                            Activos Fijos
                        </h1>
                        <p className="text-gray-500">Gestión de Propiedad, Planta y Equipo</p>
                    </div>
                </div>
                <div className="flex gap-3">
                    {/* BOTÓN NUEVO: DEPRECIACIÓN */}
                    <button
                        onClick={() => setShowModalDepreciacion(true)}
                        className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 flex items-center gap-2 font-bold shadow-md"
                        title="Ejecutar Cierre Mensual de Activos"
                    >
                        <FaCalculator /> Ejecutar Depreciación
                    </button>

                    <Link
                        href="/activos/movimientos-contables"
                        className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center gap-2 font-medium shadow-sm"
                        title="Ver documentos contables generados por depreciaciones"
                    >
                        <FaFileInvoiceDollar /> Movimientos Contables
                    </Link>
                    <Link
                        href="/activos/categorias"
                        className="bg-white text-gray-700 border border-gray-300 px-4 py-2 rounded-lg hover:bg-gray-50 flex items-center gap-2 font-medium shadow-sm"
                    >
                        <FaCogs /> Categorías
                    </Link>
                    <Link
                        href="/activos/crear"
                        className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2 font-bold shadow-md transform hover:scale-105 transition"
                    >
                        <FaPlus /> Nuevo Activo
                    </Link>
                </div>
            </div>

            {/* BARRA DE BÚSQUEDA */}
            <form onSubmit={handleSearch} className="mb-6 flex gap-2">
                <input
                    type="text"
                    className="flex-1 rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-3 border"
                    placeholder="Buscar por placa, nombre o serial..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                />
                <button type="submit" className="bg-gray-800 text-white px-6 rounded-lg font-medium hover:bg-gray-900">
                    <FaSearch />
                </button>
            </form>

            {/* TABLA DE ACTIVOS */}
            <div className="bg-white shadow-lg rounded-xl overflow-hidden border border-gray-200">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Código / Placa</th>
                            <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Activo</th>
                            <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Categoría</th>
                            <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Ubicación</th>
                            <th className="px-6 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider">Costo</th>
                            <th className="px-6 py-3 text-center text-xs font-bold text-gray-500 uppercase tracking-wider">Estado</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {loading ? (
                            <tr><td colSpan="6" className="text-center py-10 text-gray-500">Cargando inventario de activos...</td></tr>
                        ) : activos.length === 0 ? (
                            <tr><td colSpan="6" className="text-center py-10 text-gray-500">No hay activos registrados. ¡Crea el primero!</td></tr>
                        ) : (
                            activos.map((activo) => (
                                <tr
                                    key={activo.id}
                                    onClick={() => window.location.href = `/activos/${activo.id}`} // Usamos window.location para simplicidad o router.push si importamos hook
                                    className="hover:bg-blue-50 transition cursor-pointer"
                                >
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono font-bold text-blue-600">
                                        {activo.codigo}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                        {activo.nombre}
                                        <div className="text-xs text-gray-500">{activo.serial ? `S/N: ${activo.serial}` : ''}</div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 px-2">
                                        <span className="bg-gray-100 text-gray-800 py-1 px-2 rounded-full text-xs">
                                            {activo.categoria_id} {/* TODO: Traer nombre de categoría */}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {activo.ubicacion || 'Sin asignar'}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-bold text-gray-800">
                                        ${parseFloat(activo.costo_adquisicion).toLocaleString('es-CO')}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-center">
                                        <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full 
                                            ${activo.estado === 'ACTIVO' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                            {activo.estado}
                                        </span>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* MODAL DE DEPRECIACIÓN */}
            {showModalDepreciacion && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-md border-t-4 border-orange-500">
                        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2 text-gray-800">
                            <FaCalculator className="text-orange-600" /> Ejecutar Depreciación
                        </h2>
                        <p className="text-gray-600 text-sm mb-6">
                            Este proceso calculará el desgaste de todos los activos activos para el período seleccionado y generará automáticamente el asiento contable.
                        </p>

                        <form onSubmit={handleEjecutarDepreciacion} className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-bold text-gray-700">Mes</label>
                                    <select
                                        className="w-full border rounded p-2"
                                        value={depreciacionData.mes}
                                        onChange={e => setDepreciacionData({ ...depreciacionData, mes: e.target.value })}
                                    >
                                        {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map(m => (
                                            <option key={m} value={m}>{m}</option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-bold text-gray-700">Año</label>
                                    <input
                                        type="number"
                                        className="w-full border rounded p-2"
                                        value={depreciacionData.anio}
                                        onChange={e => setDepreciacionData({ ...depreciacionData, anio: e.target.value })}
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-bold text-gray-700 mb-1">Tipo de Documento (Nota)</label>
                                <select
                                    className="w-full border rounded p-2"
                                    required
                                    value={depreciacionData.tipo_documento_id}
                                    onChange={e => setDepreciacionData({ ...depreciacionData, tipo_documento_id: e.target.value })}
                                >
                                    <option value="">-- Seleccione --</option>
                                    {tiposDocumento.map(t => (
                                        <option key={t.id} value={t.id}>{t.codigo} - {t.nombre}</option>
                                    ))}
                                </select>
                                <p className="text-xs text-gray-500 mt-1">Seleccione "Nota Contable" o similar.</p>
                            </div>

                            <div className="flex justify-end gap-3 mt-8 pt-4 border-t">
                                <button
                                    type="button"
                                    onClick={() => setShowModalDepreciacion(false)}
                                    className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    className="bg-orange-600 text-white px-6 py-2 rounded-lg hover:bg-orange-700 font-bold flex items-center gap-2 shadow-lg"
                                >
                                    <FaPlay className="text-xs" /> Procesar
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
