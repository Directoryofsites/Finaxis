'use client';
import React, { useState, useEffect } from 'react';
import { apiService } from '../../../lib/apiService';
import { FaFileInvoiceDollar, FaCalendarAlt, FaSearch, FaEye, FaDownload, FaTrash, FaExclamationTriangle } from 'react-icons/fa';
import BotonRegresar from '../../components/BotonRegresar';

export default function MovimientosContablesActivosPage() {
    const [documentos, setDocumentos] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filtros, setFiltros] = useState({
        fechaInicio: '',
        fechaFin: '',
        busqueda: ''
    });

    useEffect(() => {
        loadMovimientosContables();
    }, []);

    const loadMovimientosContables = async () => {
        try {
            setLoading(true);
            
            // Usar el endpoint específico para documentos de activos fijos
            const response = await apiService.get('/activos/documentos-contables');
            
            // La API devuelve {total: number, documentos: array}
            const documentosData = response.data?.documentos || [];
            setDocumentos(documentosData);
        } catch (error) {
            console.error("Error cargando movimientos contables:", error);
            // En caso de error, establecer array vacío
            setDocumentos([]);
            
            // Solo mostrar alerta si no es un error 404 (no hay documentos)
            if (error.response?.status !== 404) {
                alert("Error al cargar los movimientos contables de activos fijos");
            }
        } finally {
            setLoading(false);
        }
    };

    const handleFiltrar = async () => {
        try {
            setLoading(true);
            
            const params = {
                observaciones: 'depreciación',
                limit: 100
            };
            
            if (filtros.fechaInicio) params.fecha_inicio = filtros.fechaInicio;
            if (filtros.fechaFin) params.fecha_fin = filtros.fechaFin;
            if (filtros.busqueda) params.numero = filtros.busqueda;
            
            const response = await apiService.get('/documentos/', { params });
            const documentosData = response.data?.documentos || [];
            setDocumentos(documentosData);
        } catch (error) {
            console.error("Error filtrando:", error);
        } finally {
            setLoading(false);
        }
    };

    const verDetalle = (documentoId) => {
        window.open(`/contabilidad/documentos/detalle/${documentoId}`, '_blank');
    };

    const descargarPDF = (documentoId) => {
        window.open(`/api/documentos/${documentoId}/pdf`, '_blank');
    };

    const eliminarDocumento = async (documentoId, numeroDoc) => {
        if (!confirm(`⚠️ ¿Está seguro de eliminar el documento ${numeroDoc}?\n\nEsta acción NO se puede deshacer y eliminará:\n- El documento contable\n- Todos sus movimientos\n- Las novedades de depreciación asociadas\n\n¿Continuar?`)) {
            return;
        }

        try {
            const razon = `Eliminación de documento de depreciación ${numeroDoc} para pruebas`;
            await apiService.delete(`/documentos/${documentoId}`, {
                data: { razon }
            });
            
            alert(`✅ Documento ${numeroDoc} eliminado exitosamente`);
            loadMovimientosContables(); // Recargar la lista
        } catch (error) {
            console.error("Error eliminando documento:", error);
            alert('❌ Error al eliminar: ' + (error.response?.data?.detail || error.message));
        }
    };

    const limpiarDepreciacionesPrueba = async () => {
        if (!confirm(`🧹 ¿Limpiar TODAS las depreciaciones de prueba?\n\nEsto eliminará:\n- Todos los documentos de depreciación\n- Todas las novedades de depreciación\n- Resetear depreciación acumulada de activos\n\n⚠️ SOLO usar para pruebas. ¿Continuar?`)) {
            return;
        }

        try {
            // Llamar a un endpoint especial para limpiar depreciaciones
            await apiService.post('/activos/limpiar-depreciaciones-prueba');
            
            alert(`✅ ¡Depreciaciones de prueba limpiadas!\n\nYa puedes ejecutar nuevas depreciaciones para tus ensayos.`);
            loadMovimientosContables(); // Recargar la lista
        } catch (error) {
            console.error("Error limpiando depreciaciones:", error);
            alert('❌ Error al limpiar: ' + (error.response?.data?.detail || error.message));
        }
    };

    const formatearFecha = (fecha) => {
        return new Date(fecha).toLocaleDateString('es-CO');
    };

    const formatearMoneda = (valor) => {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0
        }).format(valor);
    };

    const calcularTotalDocumento = (documento) => {
        // Si el documento tiene total_debito directamente, usarlo
        if (documento.total_debito) {
            return parseFloat(documento.total_debito) || 0;
        }
        // Fallback: calcular desde movimientos si existen
        return documento.movimientos_contables?.reduce((sum, mov) => sum + (parseFloat(mov.debito) || 0), 0) || 0;
    };

    if (loading) return <div className="p-6">Cargando movimientos contables...</div>;

    return (
        <div className="p-6">
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-4">
                    <BotonRegresar href="/activos" />
                    <div>
                        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                            <FaFileInvoiceDollar className="text-blue-600" />
                            Movimientos Contables - Activos Fijos
                        </h1>
                        <p className="text-gray-600 text-sm">
                            Documentos contables generados por depreciaciones y otros movimientos de activos
                        </p>
                    </div>
                </div>
                
                <div className="flex gap-2">
                    <button
                        onClick={limpiarDepreciacionesPrueba}
                        className="bg-red-600 text-white px-4 py-2 rounded-lg font-semibold shadow-md hover:bg-red-700 transition flex items-center gap-2"
                        title="Limpiar todas las depreciaciones para poder hacer nuevas pruebas"
                    >
                        <FaExclamationTriangle /> Limpiar Pruebas
                    </button>
                </div>
            </div>

            {/* Filtros */}
            <div className="bg-white p-4 rounded-lg shadow-md mb-6">
                <h3 className="text-lg font-semibold mb-4 text-gray-700">Filtros de Búsqueda</h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            <FaCalendarAlt className="inline mr-1" />
                            Fecha Inicio
                        </label>
                        <input
                            type="date"
                            className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
                            value={filtros.fechaInicio}
                            onChange={(e) => setFiltros({...filtros, fechaInicio: e.target.value})}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            <FaCalendarAlt className="inline mr-1" />
                            Fecha Fin
                        </label>
                        <input
                            type="date"
                            className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
                            value={filtros.fechaFin}
                            onChange={(e) => setFiltros({...filtros, fechaFin: e.target.value})}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            <FaSearch className="inline mr-1" />
                            Número Documento
                        </label>
                        <input
                            type="text"
                            placeholder="Buscar por número..."
                            className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
                            value={filtros.busqueda}
                            onChange={(e) => setFiltros({...filtros, busqueda: e.target.value})}
                        />
                    </div>
                    <div className="flex items-end">
                        <button
                            onClick={handleFiltrar}
                            className="bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold shadow-md hover:bg-blue-700 transition flex items-center gap-2 w-full justify-center"
                        >
                            <FaSearch /> Filtrar
                        </button>
                    </div>
                </div>
            </div>

            {/* Resumen */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-blue-50 p-4 rounded-lg border-l-4 border-blue-500">
                    <h3 className="text-lg font-semibold text-blue-700">Total Documentos</h3>
                    <p className="text-2xl font-bold text-blue-800">{Array.isArray(documentos) ? documentos.length : 0}</p>
                </div>
                <div className="bg-green-50 p-4 rounded-lg border-l-4 border-green-500">
                    <h3 className="text-lg font-semibold text-green-700">Total Depreciación</h3>
                    <p className="text-2xl font-bold text-green-800">
                        {formatearMoneda(
                            Array.isArray(documentos) ? documentos.reduce((sum, doc) => sum + calcularTotalDocumento(doc), 0) : 0
                        )}
                    </p>
                </div>
                <div className="bg-orange-50 p-4 rounded-lg border-l-4 border-orange-500">
                    <h3 className="text-lg font-semibold text-orange-700">Último Período</h3>
                    <p className="text-lg font-bold text-orange-800">
                        {Array.isArray(documentos) && documentos.length > 0 ? formatearFecha(documentos[0]?.fecha) : 'N/A'}
                    </p>
                </div>
            </div>

            {/* Tabla de Documentos */}
            <div className="bg-white shadow-lg rounded-xl overflow-hidden">
                <div className="px-6 py-4 bg-gray-50 border-b">
                    <h3 className="text-lg font-semibold text-gray-800">
                        Documentos Contables de Activos Fijos
                    </h3>
                </div>

                {!Array.isArray(documentos) || documentos.length === 0 ? (
                    <div className="p-8 text-center">
                        <FaFileInvoiceDollar className="mx-auto text-6xl text-gray-300 mb-4" />
                        <h3 className="text-xl font-semibold text-gray-600 mb-2">
                            No hay movimientos contables
                        </h3>
                        <p className="text-gray-500">
                            Aún no se han generado documentos contables por depreciaciones de activos fijos.
                        </p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Documento
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Fecha
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Tipo
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Observaciones
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Total
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Estado
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Acciones
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {Array.isArray(documentos) && documentos.map((documento) => (
                                    <tr key={documento.id} className="hover:bg-gray-50">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm font-medium text-gray-900">
                                                {documento.tipo_documento_codigo || 'SIN-TIPO'}-{documento.numero}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {formatearFecha(documento.fecha)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {documento.tipo_documento_nombre || 'Sin tipo asignado'}
                                        </td>
                                        <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                                            {documento.observaciones || 'Sin observaciones'}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                            {formatearMoneda(calcularTotalDocumento(documento))}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                                documento.estado === 'ACTIVO' 
                                                    ? 'bg-green-100 text-green-800' 
                                                    : 'bg-red-100 text-red-800'
                                            }`}>
                                                {documento.estado}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                            <div className="flex gap-2">
                                                <button
                                                    onClick={() => verDetalle(documento.id)}
                                                    className="text-blue-600 hover:text-blue-900 flex items-center gap-1"
                                                    title="Ver detalle"
                                                >
                                                    <FaEye /> Ver
                                                </button>
                                                <button
                                                    onClick={() => descargarPDF(documento.id)}
                                                    className="text-green-600 hover:text-green-900 flex items-center gap-1"
                                                    title="Descargar PDF"
                                                >
                                                    <FaDownload /> PDF
                                                </button>
                                                <button
                                                    onClick={() => eliminarDocumento(documento.id, `${documento.tipo_documento_codigo || 'SIN-TIPO'}-${documento.numero}`)}
                                                    className="text-red-600 hover:text-red-900 flex items-center gap-1"
                                                    title="Eliminar documento"
                                                >
                                                    <FaTrash /> Eliminar
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                )) || []}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Información adicional */}
            <div className="mt-6 bg-blue-50 p-4 rounded-lg border-l-4 border-blue-500">
                <h4 className="font-semibold text-blue-800 mb-2">💡 Información sobre Movimientos Contables</h4>
                <ul className="text-sm text-blue-700 space-y-1">
                    <li>• Los documentos de depreciación se generan automáticamente al ejecutar el proceso mensual</li>
                    <li>• Cada documento afecta las cuentas de gasto (516xxx) y depreciación acumulada (159xxx)</li>
                    <li>• Puedes ver el detalle completo haciendo clic en "Ver" en cada documento</li>
                    <li>• Los PDFs incluyen el asiento contable completo con todas las cuentas afectadas</li>
                </ul>
            </div>
        </div>
    );
}