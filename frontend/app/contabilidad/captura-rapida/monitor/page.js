'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

// Hooks y Servicios
import { useAuth } from '../../../context/AuthContext';
import { apiService, API_URL } from '../../../../lib/apiService';
import { useMemo } from 'react';
import { FaPrint, FaSync, FaCalendarAlt, FaFilter, FaSearch, FaBolt, FaHashtag, FaUser, FaBookOpen, FaFilePdf, FaEdit, FaDollarSign, FaSitemap, FaUserTie, FaBox, FaListOl } from 'react-icons/fa';

export default function MonitorAsientosPage() {
    const { user } = useAuth();
    const router = useRouter();
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
    const [filtroCuenta, setFiltroCuenta] = useState('');
    const [filtroValor, setFiltroValor] = useState('');
    const [filtroOperadorValor, setFiltroOperadorValor] = useState('>='); // '>=', '<=', '=='
    const [filtroCC, setFiltroCC] = useState('');
    const [filtroVendedor, setFiltroVendedor] = useState('');
    const [filtroProducto, setFiltroProducto] = useState('');

    // Refrescar al cargar
    useEffect(() => {
        fetchMonitorData();
    }, [filtros.fechaInicio, filtros.fechaFin]);

    const fetchMonitorData = async () => {
        if (!filtros.fechaInicio || !filtros.fechaFin) return;

        setLoading(true);
        try {
            const inicio = filtros.fechaInicio instanceof Date && !isNaN(filtros.fechaInicio)
                ? filtros.fechaInicio.toISOString().split('T')[0]
                : new Date().toISOString().split('T')[0];
            const fin = filtros.fechaFin instanceof Date && !isNaN(filtros.fechaFin)
                ? filtros.fechaFin.toISOString().split('T')[0]
                : new Date().toISOString().split('T')[0];

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

            // 5. Filtro Cuenta
            if (filtroCuenta && !mov.cuenta_codigo.startsWith(filtroCuenta)) return false;

            // 6. Filtro Valor (Aplica a Débito o Crédito)
            if (filtroValor) {
                const valorFiltro = parseFloat(filtroValor);
                const valorMax = Math.max(mov.debito || 0, mov.credito || 0);
                
                if (filtroOperadorValor === '>=') {
                    if (!(valorMax >= valorFiltro)) return false;
                } else if (filtroOperadorValor === '<=') {
                    if (!(valorMax <= valorFiltro)) return false;
                } else if (filtroOperadorValor === '==') {
                    if (Math.abs(valorMax - valorFiltro) > 0.01) return false;
                }
            }

            // 7. Filtro Centro de Costo
            if (filtroCC && !mov.centro_costo_codigo.toLowerCase().includes(filtroCC.toLowerCase())) return false;

            // 8. Filtro Vendedor
            if (filtroVendedor && !mov.vendedor_nombre.toLowerCase().includes(filtroVendedor.toLowerCase())) return false;

            // 9. Filtro Producto
            if (filtroProducto && !mov.producto_nombre.toLowerCase().includes(filtroProducto.toLowerCase())) return false;

            return true;
        });
    }, [movimientos, filtroTipo, filtroNumero, filtroBeneficiario, filtroConcepto, filtroCuenta, filtroValor, filtroOperadorValor, filtroCC, filtroVendedor, filtroProducto]);


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

    const handleExportarReportePDF = async () => {
        toast.info("Generando reporte PDF... \u23F3", { autoClose: 2000 });
        try {
            const inicio = filtros.fechaInicio.toISOString().split('T')[0];
            const fin = filtros.fechaFin.toISOString().split('T')[0];

            // Obtener IDs de tipos seleccionados (si hay filtro de tipo, es uno solo en este UI actual)
            // Pero el monitor aplica filtro local, así que mandamos los términos de búsqueda al backend
            const params = {
                fecha_inicio: inicio,
                fecha_fin: fin,
                numero_documento: filtroNumero || undefined,
                beneficiario_filtro: filtroBeneficiario || undefined,
                concepto_filtro: filtroConcepto || undefined,
                cuenta_filtro: filtroCuenta || undefined,
                valor_filtro: filtroValor || undefined,
                operador_valor: filtroOperadorValor || undefined,
                centro_costo_filtro: filtroCC || undefined,
                vendedor_filtro: filtroVendedor || undefined,
                producto_filtro: filtroProducto || undefined
            };

            const res = await apiService.get('/reports/journal/get-signed-url', { params });
            const signedToken = res.data.signed_url_token;

            const pdfUrl = `${API_URL}/api/reports/journal/imprimir?signed_token=${signedToken}`;
            window.open(pdfUrl, '_blank');
        } catch (error) {
            console.error("Error exportando PDF:", error);
            toast.error("No se pudo generar el reporte PDF.");
        }
    };

    const handleEditarDocumento = (docId) => {
        if (!docId) return;
        router.push(`/contabilidad/documentos/${docId}?edit=true`);
    };

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col font-sans text-gray-800">
            <ToastContainer position="top-right" autoClose={3000} />

            {/* HEADER FIJO */}
            <header className="bg-white border-b border-gray-200 shadow-sm px-6 py-4 sticky top-0 z-10 flex flex-col gap-4">
                <div className="flex flex-col xl:flex-row justify-between items-start xl:items-center gap-4">
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
                        <div className="h-6 w-px bg-gray-300 mx-1 hidden sm:block"></div>

                        {/* CONTROL DE FECHAS */}
                        <div className="flex items-center bg-gray-100 rounded-lg p-1 border border-gray-200 text-sm shadow-inner">
                            <DatePicker
                                selected={filtros.fechaInicio}
                                onChange={date => setFiltros({ ...filtros, fechaInicio: date })}
                                dateFormat="dd/MM/yyyy"
                                className="w-24 bg-transparent text-center font-medium focus:outline-none cursor-pointer text-gray-700"
                            />
                            <span className="text-gray-400 mx-1">-</span>
                            <DatePicker
                                selected={filtros.fechaFin}
                                onChange={date => setFiltros({ ...filtros, fechaFin: date })}
                                dateFormat="dd/MM/yyyy"
                                className="w-24 bg-transparent text-center font-medium focus:outline-none cursor-pointer text-gray-700"
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

                        <button
                            onClick={handleExportarReportePDF}
                            disabled={loading || movimientosFiltrados.length === 0}
                            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all shadow-sm ${loading || movimientosFiltrados.length === 0 ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-red-50 text-red-600 hover:bg-red-100 border border-red-200'}`}
                            title="Exportar vista actual a PDF"
                        >
                            <FaFilePdf />
                            <span className="font-bold text-sm">PDF</span>
                        </button>
                    </div>
                </div>

                {/* FILTROS AVANZADOS - FILA 1 */}
                <div className="flex flex-wrap items-center gap-3 bg-gray-50/50 p-2 rounded-xl border border-dashed border-gray-300">
                    
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

                    {/* FILTRO CUENTA */}
                    <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                            <FaListOl />
                        </div>
                        <input
                            type="text"
                            placeholder="Cuenta"
                            value={filtroCuenta}
                            onChange={(e) => setFiltroCuenta(e.target.value)}
                            className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500 w-32 shadow-sm"
                        />
                    </div>

                    {/* FILTRO VALOR */}
                    <div className="flex items-center gap-1">
                        <select
                            value={filtroOperadorValor}
                            onChange={(e) => setFiltroOperadorValor(e.target.value)}
                            className="py-2 border border-gray-300 rounded-l-lg text-xs focus:ring-indigo-500 focus:border-indigo-500 bg-white shadow-sm appearance-none hover:border-gray-400 transition-colors w-12 text-center"
                        >
                            <option value=">=">&gt;=</option>
                            <option value="<=">&lt;=</option>
                            <option value="==">==</option>
                        </select>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                                <FaDollarSign className="text-xs" />
                            </div>
                            <input
                                type="number"
                                placeholder="Valor"
                                value={filtroValor}
                                onChange={(e) => setFiltroValor(e.target.value)}
                                className="pl-8 pr-3 py-2 border border-gray-300 rounded-r-lg text-sm focus:ring-indigo-500 focus:border-indigo-500 w-28 shadow-sm"
                            />
                        </div>
                    </div>

                    <div className="h-6 w-px bg-gray-300 mx-1"></div>

                    {/* FILTRO BENEFICIARIO */}
                    <div className="relative flex-grow xl:flex-grow-0">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                            <FaUser />
                        </div>
                        <input
                            type="text"
                            placeholder="Beneficiario..."
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
                            placeholder="Concepto..."
                            value={filtroConcepto}
                            onChange={(e) => setFiltroConcepto(e.target.value)}
                            className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500 w-full xl:w-48 shadow-sm"
                        />
                    </div>

                    {/* FILTRO CC */}
                    <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                            <FaSitemap />
                        </div>
                        <input
                            type="text"
                            placeholder="C. Costo"
                            value={filtroCC}
                            onChange={(e) => setFiltroCC(e.target.value)}
                            className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500 w-28 shadow-sm"
                        />
                    </div>

                    {/* FILTRO VENDEDOR */}
                    <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                            <FaUserTie />
                        </div>
                        <input
                            type="text"
                            placeholder="Vendedor"
                            value={filtroVendedor}
                            onChange={(e) => setFiltroVendedor(e.target.value)}
                            className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500 w-32 shadow-sm"
                        />
                    </div>

                    {/* FILTRO PRODUCTO */}
                    <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                            <FaBox />
                        </div>
                        <input
                            type="text"
                            placeholder="Producto"
                            value={filtroProducto}
                            onChange={(e) => setFiltroProducto(e.target.value)}
                            className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-indigo-500 focus:border-indigo-500 w-32 shadow-sm"
                        />
                    </div>

                    {/* BOTÓN LIMPIAR */}
                    <button
                        onClick={() => {
                            setFiltroTipo('');
                            setFiltroNumero('');
                            setFiltroBeneficiario('');
                            setFiltroConcepto('');
                            setFiltroCuenta('');
                            setFiltroValor('');
                            setFiltroCC('');
                            setFiltroVendedor('');
                            setFiltroProducto('');
                        }}
                        className="text-xs text-indigo-600 hover:text-indigo-800 font-medium px-2 py-1 rounded hover:bg-indigo-50 transition-colors"
                    >
                        Limpiar
                    </button>
                </div>
            </header>

            {/* CONTENIDO SCROLLABLE */}
            <main className="flex-1 overflow-auto p-6">
                <div className="max-w-full mx-auto">

                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                        <table className="min-w-full divide-y divide-gray-200 text-sm">
                            <thead className="bg-gray-50 sticky top-0 z-0">
                                <tr>
                                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider w-24">Fecha</th>
                                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider w-32">Documento</th>
                                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider w-1/4">Tercero / Vendedor</th>
                                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Concepto / Producto</th>
                                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider w-24">Cuenta / CC</th>
                                    <th className="px-4 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider w-28">Débito</th>
                                    <th className="px-4 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider w-28">Crédito</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-100">
                                {loading && movimientos.length === 0 ? (
                                    <tr>
                                        <td colSpan="7" className="px-6 py-12 text-center text-gray-500 animate-pulse">
                                            Cargando movimientos...
                                        </td>
                                    </tr>
                                ) : movimientosFiltrados.length === 0 ? (
                                    <tr>
                                        <td colSpan="7" className="px-6 py-12 text-center text-gray-400 italic">
                                            {movimientos.length === 0
                                                ? "No hay movimientos registrados en este rango de fechas."
                                                : "No se encontraron coincidencias con los filtros aplicados."}
                                        </td>
                                    </tr>
                                ) : (
                                    movimientosFiltrados.map((mov) => (
                                        <tr key={mov.id} className="hover:bg-indigo-50/50 transition-colors group">
                                            <td className="px-4 py-2 whitespace-nowrap text-gray-500 font-mono text-[10px]">
                                                {new Date(mov.fecha).toLocaleDateString()}
                                            </td>
                                            <td className="px-4 py-2 whitespace-nowrap">
                                                <div className="flex items-center gap-2">
                                                    <button
                                                        onClick={() => handleEditarDocumento(mov.documento_id)}
                                                        className="font-bold text-indigo-600 hover:text-indigo-800 hover:underline transition-colors flex items-center gap-1 text-xs"
                                                        title="Ver / Editar Documento"
                                                    >
                                                        {mov.tipo_documento_codigo || 'DOC'} {mov.numero_documento || mov.documento_numero}
                                                        <FaEdit className="text-[10px] opacity-50" />
                                                    </button>
                                                    <button
                                                        onClick={() => handleImprimirDocumento(mov.documento_id)}
                                                        className="p-1 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded transition-all"
                                                        title="Imprimir PDF del documento"
                                                    >
                                                        <FaPrint className="text-[10px]" />
                                                    </button>
                                                </div>
                                            </td>
                                            <td className="px-4 py-2 text-gray-700 truncate max-w-xs">
                                                <div className="font-medium truncate text-xs" title={mov.beneficiario_nombre}>
                                                    {mov.beneficiario_nombre || 'Sin Beneficiario'}
                                                </div>
                                                {mov.vendedor_nombre && (
                                                    <div className="text-[10px] text-gray-400 italic truncate flex items-center gap-1">
                                                        <FaUserTie className="text-[8px]" /> {mov.vendedor_nombre}
                                                    </div>
                                                )}
                                            </td>
                                            <td className="px-4 py-2 text-gray-600 truncate max-w-sm">
                                                <div className="truncate text-xs" title={mov.concepto}>
                                                    {mov.concepto}
                                                </div>
                                                {mov.producto_nombre && (
                                                    <div className="text-[10px] text-indigo-400 italic truncate flex items-center gap-1">
                                                        <FaBox className="text-[8px]" /> {mov.producto_nombre}
                                                    </div>
                                                )}
                                            </td>
                                            <td className="px-4 py-2 whitespace-nowrap">
                                                <div className="flex flex-col gap-0.5">
                                                    <button
                                                        onClick={() => handleVerAuxiliar(mov.cuenta_codigo)}
                                                        className="inline-flex self-start items-center px-1.5 py-0.5 rounded bg-gray-100 text-gray-700 font-mono text-[10px] hover:bg-indigo-100 hover:text-indigo-700 transition-colors border border-gray-200"
                                                        title={`Ver auxiliar de cuenta ${mov.cuenta_codigo}`}
                                                    >
                                                        {mov.cuenta_codigo}
                                                    </button>
                                                    {mov.centro_costo_codigo && (
                                                        <div className="text-[9px] text-gray-400 font-mono flex items-center gap-1">
                                                            <FaSitemap className="text-[8px]" /> {mov.centro_costo_codigo}
                                                        </div>
                                                    )}
                                                </div>
                                            </td>
                                            <td className="px-4 py-2 whitespace-nowrap text-right font-mono font-medium text-gray-700 text-xs">
                                                {mov.debito > 0 ? parseFloat(mov.debito).toLocaleString('es-CO', { minimumFractionDigits: 2 }) : '-'}
                                            </td>
                                            <td className="px-4 py-2 whitespace-nowrap text-right font-mono font-medium text-gray-700 text-xs">
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
