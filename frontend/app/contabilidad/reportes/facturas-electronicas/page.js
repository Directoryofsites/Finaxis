'use client';

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { apiService } from '../../../../lib/apiService';
import Link from 'next/link';

export default function ReporteFacturasElectronicas() {
    const { user } = useAuth();
    const [loading, setLoading] = useState(false);
    const [documentos, setDocumentos] = useState([]);

    // Filtros
    const [fechaInicio, setFechaInicio] = useState(new Date().toISOString().split('T')[0]); // Default hoy
    const [fechaFin, setFechaFin] = useState(new Date().toISOString().split('T')[0]);
    const [dianEstado, setDianEstado] = useState(''); // '' = Todos
    const [numero, setNumero] = useState('');

    const fetchDocumentos = useCallback(async () => {
        if (!user || !user.empresaId) return;

        setLoading(true);
        try {
            const payload = {
                tipoEntidad: 'DOCUMENTO', // Requerido por el esquema DocumentoGestionFiltros
                fechaInicio: fechaInicio,
                fechaFin: fechaFin,
                dianEstado: dianEstado || null,
                numero: numero || null,
                limite: 100, // Límite razonable para un reporte rápido
                pagina: 1
            };

            const response = await apiService.post('/documentos/buscar-para-gestion', payload);
            setDocumentos(response.data);
        } catch (error) {
            console.error("Error cargando reporte:", error);
            alert("Error al cargar el reporte: " + (error.response?.data?.message || error.message));
        } finally {
            setLoading(false);
        }
    }, [user, fechaInicio, fechaFin, dianEstado, numero]);

    useEffect(() => {
        fetchDocumentos();
    }, [fetchDocumentos]);

    // Función para copiar CUFE
    const copyCufe = (cufe) => {
        navigator.clipboard.writeText(cufe);
        alert("CUFE copiado al portapapeles");
    };

    const getStatusBadge = (estado) => {
        if (!estado) return <span className="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-600">PENDIENTE</span>;

        switch (estado.toUpperCase()) {
            case 'ACEPTADO': return <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">ACEPTADO</span>;
            case 'ENVIADO': return <span className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">ENVIADO</span>;
            case 'RECHAZADO': return <span className="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">RECHAZADO</span>;
            case 'ERROR': return <span className="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">ERROR</span>;
            default: return <span className="px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">{estado}</span>;
        }
    };

    return (
        <div className="container mx-auto p-6 bg-gray-50 min-h-screen">
            <h1 className="text-3xl font-bold text-gray-800 mb-6">Reporte de Facturación Electrónica</h1>

            {/* FILTROS */}
            <div className="bg-white p-4 rounded-lg shadow-md mb-6 grid grid-cols-1 md:grid-cols-5 gap-4 items-end">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Fecha Inicio</label>
                    <input type="date" value={fechaInicio} onChange={(e) => setFechaInicio(e.target.value)} className="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Fecha Fin</label>
                    <input type="date" value={fechaFin} onChange={(e) => setFechaFin(e.target.value)} className="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Estado DIAN</label>
                    <select value={dianEstado} onChange={(e) => setDianEstado(e.target.value)} className="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500">
                        <option value="">TODOS</option>
                        <option value="ACEPTADO">ACEPTADO</option>
                        <option value="ENVIADO">ENVIADO</option>
                        <option value="RECHAZADO">RECHAZADO</option>
                        <option value="ERROR">ERROR</option>
                        <option value="PENDIENTE">PENDIENTE (Sin info)</option>
                    </select>
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Número</label>
                    <input type="text" placeholder="Ej: 1001" value={numero} onChange={(e) => setNumero(e.target.value)} className="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" />
                </div>
                <div>
                    <button onClick={fetchDocumentos} className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition font-semibold">
                        Actualizar
                    </button>
                </div>
            </div>

            {/* TABLA DE RESULTADOS */}
            <div className="bg-white rounded-lg shadow-md overflow-hidden">
                {loading ? (
                    <div className="p-8 text-center text-gray-500">Cargando datos...</div>
                ) : documentos.length === 0 ? (
                    <div className="p-8 text-center text-gray-500">No se encontraron facturas con estos filtros.</div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Fecha</th>
                                    <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Documento</th>
                                    <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Cliente</th>
                                    <th className="px-6 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider">Total</th>
                                    <th className="px-6 py-3 text-center text-xs font-bold text-gray-500 uppercase tracking-wider">Estado DIAN</th>
                                    <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">CUFE</th>
                                    <th className="px-6 py-3 text-center text-xs font-bold text-gray-500 uppercase tracking-wider">Acciones</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {documentos.map((doc) => (
                                    <tr key={doc.id} className="hover:bg-gray-50 transition">
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{doc.fecha}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-blue-600 hover:text-blue-800">
                                            <Link href={`/contabilidad/documentos/${doc.id}?from=/contabilidad/reportes/facturas-electronicas`}>
                                                {doc.tipo_documento} - {doc.numero}
                                            </Link>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{doc.beneficiario || 'N/A'}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-mono font-bold text-gray-800">
                                            {new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(doc.total)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-center text-sm">{getStatusBadge(doc.dian_estado)}</td>
                                        <td className="px-6 py-4 text-xs text-gray-500 max-w-xs truncate cursor-help" title={doc.dian_cufe}>
                                            {doc.dian_cufe ? (
                                                <div className="flex items-center gap-2">
                                                    <span className="truncate w-24">{doc.dian_cufe}</span>
                                                    <button onClick={() => copyCufe(doc.dian_cufe)} className="text-gray-400 hover:text-blue-500 mdi mdi-content-copy">📋</button>
                                                </div>
                                            ) : '-'}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-center flex justify-center gap-2">
                                            {doc.dian_xml_url && (
                                                <>
                                                    <a href={doc.dian_xml_url} target="_blank" rel="noopener noreferrer" className="p-1 text-green-600 hover:bg-green-50 rounded border border-green-200" title="Ver Factura">
                                                        🔗
                                                    </a>
                                                    <a href={`https://wa.me/?text=${encodeURIComponent(`Hola, aquí tienes tu factura electrónica: ${doc.dian_xml_url}`)}`} target="_blank" rel="noopener noreferrer" className="p-1 text-white bg-green-500 hover:bg-green-600 rounded shadow" title="Enviar WhatsApp">
                                                        📱
                                                    </a>
                                                </>
                                            )}
                                            {!doc.dian_xml_url && doc.dian_estado !== 'ACEPTADO' && (
                                                <span className="text-xs text-gray-400 italic">No disponible</span>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}
