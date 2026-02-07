'use client';

import React, { useState, useEffect } from 'react';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

// Hooks y Servicios
import { useAuth } from '../../../context/AuthContext';
import { apiService } from '../../../../lib/apiService';
import { useMemo } from 'react';
import { FaPrint, FaSync, FaCalendarAlt, FaFilter, FaSearch, FaBolt, FaHashtag, FaUser, FaBookOpen } from 'react-icons/fa';

export default function MonitorAsientosPage() {
    const { user } = useAuth();
    const [loading, setLoading] = useState(false);
    const [movimientos, setMovimientos] = useState([]);
    const [filtros, setFiltros] = useState({
        fechaInicio: new Date(new Date().getFullYear(), new Date().getMonth(), 1),
        fechaFin: new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0)
    });

    // Nuevos Filtros Locales
    const [filtroTipo, setFiltroTipo] = useState('');
    const [filtroNumero, setFiltroNumero] = useState('');
    const [filtroBeneficiario, setFiltroBeneficiario] = useState('');
    const [filtroConcepto, setFiltroConcepto] = useState('');

    // Refrescar al cargar
    useEffect(() => {
        fetchMonitorData();
    }, [filtros.fechaInicio, filtros.fechaFin]);

    const fetchMonitorData = async () => {
        setLoading(true);
        try {
            const inicio = filtros.fechaInicio.toISOString().split('T')[0];
            const fin = filtros.fechaFin.toISOString().split('T')[0];

            const queryParams = new URLSearchParams();
            queryParams.append('fecha_inicio', inicio);
            queryParams.append('fecha_fin', fin);

            const res = await apiService.get('/reports/journal', { params: queryParams });

            // Ordenar: Documento ID Descendente
            const sorted = Array.isArray(res.data)
                ? res.data.sort((a, b) => b.id - a.id)
                : [];

            setMovimientos(sorted);
        } catch (err) {
            console.error("Error cargando monitor:", err);
            toast.error("Error al cargar movimientos.");
        } finally {
            setLoading(false);
        }
    };

    // Lógica de Filtrado Local (Client-Side)
    const movimientosFiltrados = useMemo(() => {
        return movimientos.filter(mov => {
            // 1. Filtro Tipo
            if (filtroTipo && mov.tipo_documento_codigo !== filtroTipo) return false;

            // 2. Filtro Número
            if (filtroNumero && !String(mov.numero_documento).includes(filtroNumero)) return false;

            // 3. Filtro Beneficiario (Inteligente: busca en nombre o NIT)
            if (filtroBeneficiario && filtroBeneficiario.length >= 2) {
                const term = filtroBeneficiario.toLowerCase();
                const nombre = (mov.beneficiario_nombre || '').toLowerCase();
                const nit = (mov.beneficiario_nit || '').toLowerCase();
                if (!nombre.includes(term) && !nit.includes(term)) return false;
            }

            // 4. Filtro Concepto
            if (filtroConcepto && filtroConcepto.length >= 3) {
                const term = filtroConcepto.toLowerCase();
                const concepto = (mov.concepto || '').toLowerCase();
                if (!concepto.includes(term)) return false;
            }

            return true;
        });
    }, [movimientos, filtroTipo, filtroNumero, filtroBeneficiario, filtroConcepto]);

    // Extraer lista única de tipos para el Select
    const tiposDisponibles = useMemo(() => {
        const tipos = new Set(movimientos.map(m => m.tipo_documento_codigo).filter(Boolean));
        return Array.from(tipos).sort();
    }, [movimientos]);

    const handleImprimirDocumento = async (id) => {
        if (!id) {
            toast.error("Error: ID de documento no válido.");
            return;
        }
        toast.info("Generando PDF... \u23F3", { autoClose: 2000 });
        try {
            const response = await apiService.get(`/documentos/${id}/pdf`, {
                responseType: 'blob'
            });
            const file = new Blob([response.data], { type: 'application/pdf' });
            const fileURL = URL.createObjectURL(file);
            window.open(fileURL, '_blank');
        } catch (error) {
            console.error("Error al imprimir documento:", error);
            toast.error("Error al generar el PDF del documento.");
        }
    };

    const handleVerAuxiliar = (cuentaCodigo) => {
        if (!cuentaCodigo) return;

        const inicio = filtros.fechaInicio.toISOString().split('T')[0];
        const fin = filtros.fechaFin.toISOString().split('T')[0];

        // Construir URL para el reporte Auxiliar por Cuenta
        const url = `/contabilidad/reportes/auxiliar-cuenta?cuenta=${cuentaCodigo}&fecha_inicio=${inicio}&fecha_fin=${fin}`;

        window.open(url, '_blank');
    };

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col font-sans text-gray-800">
            <ToastContainer position="top-right" autoClose={3000} />

            {/* HEADER FIJO */}
            <header className="bg-white border-b border-gray-200 shadow-sm px-6 py-4 sticky top-0 z-10 flex flex-col xl:flex-row justify-between items-start xl:items-center gap-4">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                        <FaBolt />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold text-gray-800 leading-tight">Monitor de Asientos</h1>
                        <p className="text-xs text-gray-500">
                            {movimientosFiltrados.length} movimientos encontrados
                        </p>
                    </div>
                </div>

                <div className="flex flex-wrap items-center gap-3 w-full xl:w-auto">

                    {/* FILTRO TIPO DOCUMENTO */}
                    <div className="relative group">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                            <FaFilter />
                        </div>
                        <select
                            value={filtroTipo}
                            onChange={(e) => setFiltroTipo(e.target.value)}
                            className="pl-9 pr-8 py-2 border border-gray-300 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500 bg-white shadow-sm appearance-none hover:border-gray-400 transition-colors w-32"
                            title="Filtrar por Tipo"
                        >
                            <option value="">Tipo</option>
                            {tiposDisponibles.map(t => (
                                <option key={t} value={t}>{t}</option>
                            ))}
                        </select>
                    </div>

                    {/* FILTRO NÚMERO */}
                    <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                            <FaHashtag />
                        </div>
                        <input
                            type="text"
                            placeholder="Número"
                            value={filtroNumero}
                            onChange={(e) => setFiltroNumero(e.target.value)}
                            className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500 w-28 shadow-sm"
                        />
                    </div>

                    {/* FILTRO BENEFICIARIO */}
                    <div className="relative flex-grow xl:flex-grow-0">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                            <FaUser />
                        </div>
                        <input
                            type="text"
                            placeholder="Beneficiario (3 letras)..."
                            value={filtroBeneficiario}
                            onChange={(e) => setFiltroBeneficiario(e.target.value)}
                            className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500 w-full xl:w-48 shadow-sm"
                        />
                    </div>

                    {/* FILTRO CONCEPTO */}
                    <div className="relative flex-grow xl:flex-grow-0">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                            <FaBookOpen />
                        </div>
                        <input
                            type="text"
                            placeholder="Concepto (3 letras)..."
                            value={filtroConcepto}
                            onChange={(e) => setFiltroConcepto(e.target.value)}
                            className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500 w-full xl:w-48 shadow-sm"
                        />
                    </div>

                    <div className="h-6 w-px bg-gray-300 mx-1 hidden sm:block"></div>

                    {/* CONTROL DE FECHAS */}
                    <div className="flex items-center bg-gray-100 rounded-lg p-1 border border-gray-200 text-sm shadow-inner">
                        <DatePicker
                            selected={filtros.fechaInicio}
                            onChange={date => setFiltros({ ...filtros, fechaInicio: date })}
                            dateFormat="dd/MM"
                            className="w-16 bg-transparent text-center font-medium focus:outline-none cursor-pointer text-gray-700"
                        />
                        <span className="text-gray-400 mx-1">-</span>
                        <DatePicker
                            selected={filtros.fechaFin}
                            onChange={date => setFiltros({ ...filtros, fechaFin: date })}
                            dateFormat="dd/MM"
                            className="w-16 bg-transparent text-center font-medium focus:outline-none cursor-pointer text-gray-700"
                        />
                    </div>

                    <button
                        onClick={fetchMonitorData}
                        disabled={loading}
                        className={`p-2 rounded-lg transition-all shadow-sm ${loading ? 'bg-gray-100 text-gray-400' : 'bg-indigo-50 text-indigo-600 hover:bg-indigo-100 border border-indigo-200'}`}
                        title="Actualizar datos"
                    >
                        <FaSync className={loading ? 'animate-spin' : ''} />
                    </button>
                </div>
            </header>

            {/* CONTENIDO SCROLLABLE */}
            <main className="flex-1 overflow-auto p-6">
                <div className="max-w-7xl mx-auto">

                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                        <table className="min-w-full divide-y divide-gray-200 text-sm">
                            <thead className="bg-gray-50 sticky top-0 z-0">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider w-24">Fecha</th>
                                    <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider w-32">Documento</th>
                                    <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider w-1/4">Tercero</th>
                                    <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Detalle / Concepto</th>
                                    <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider w-24">Cuenta</th>
                                    <th className="px-6 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider w-32">Débito</th>
                                    <th className="px-6 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider w-32">Crédito</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-100">
                                {loading && movimientos.length === 0 ? (
                                    <tr>
                                        <td colSpan="6" className="px-6 py-12 text-center text-gray-500 animate-pulse">
                                            Cargando movimientos...
                                        </td>
                                    </tr>
                                ) : movimientosFiltrados.length === 0 ? (
                                    <tr>
                                        <td colSpan="6" className="px-6 py-12 text-center text-gray-400 italic">
                                            {movimientos.length === 0
                                                ? "No hay movimientos registrados en este rango de fechas."
                                                : "No se encontraron coincidencias con los filtros aplicados."}
                                        </td>
                                    </tr>
                                ) : (
                                    movimientosFiltrados.map((mov) => (
                                        <tr key={mov.id} className="hover:bg-indigo-50/50 transition-colors group">
                                            <td className="px-6 py-3 whitespace-nowrap text-gray-500 font-mono text-xs">
                                                {new Date(mov.fecha).toLocaleDateString()}
                                            </td>
                                            <td className="px-6 py-3 whitespace-nowrap">
                                                <button
                                                    onClick={() => handleImprimirDocumento(mov.documento_id)}
                                                    className="font-bold text-indigo-600 hover:text-indigo-800 hover:underline flex items-center gap-2 group-hover:scale-105 transition-transform"
                                                    title="Clic para reimprimir PDF"
                                                >
                                                    {mov.tipo_documento_codigo || 'DOC'} {mov.numero_documento || mov.documento_numero}
                                                    <FaPrint className="opacity-0 group-hover:opacity-100 text-xs transition-opacity" />
                                                </button>
                                            </td>
                                            <td className="px-6 py-3 text-gray-700 truncate max-w-xs" title={mov.beneficiario_nombre}>
                                                {mov.beneficiario_nombre || 'Sin Beneficiario'}
                                            </td>
                                            <td className="px-6 py-3 text-gray-600 truncate max-w-sm" title={mov.concepto}>
                                                {mov.concepto}
                                            </td>
                                            <td className="px-6 py-3 whitespace-nowrap">
                                                <button
                                                    onClick={() => handleVerAuxiliar(mov.cuenta_codigo)}
                                                    className="inline-flex items-center px-2 py-1 rounded bg-gray-100 text-gray-700 font-mono text-xs hover:bg-indigo-100 hover:text-indigo-700 transition-colors border border-gray-200"
                                                    title={`Ver auxiliar de cuenta ${mov.cuenta_codigo}`}
                                                >
                                                    {mov.cuenta_codigo}
                                                </button>
                                            </td>
                                            <td className="px-6 py-3 whitespace-nowrap text-right font-mono font-medium text-gray-700">
                                                {mov.debito > 0 ? parseFloat(mov.debito).toLocaleString('es-CO', { minimumFractionDigits: 2 }) : '-'}
                                            </td>
                                            <td className="px-6 py-3 whitespace-nowrap text-right font-mono font-medium text-gray-700">
                                                {mov.credito > 0 ? parseFloat(mov.credito).toLocaleString('es-CO', { minimumFractionDigits: 2 }) : '-'}
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>

                </div>
            </main>
        </div>
    );
}
