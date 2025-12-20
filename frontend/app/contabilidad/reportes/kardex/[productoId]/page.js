'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useSearchParams, useRouter } from 'next/navigation';
import {
    FaCube,
    FaCalendarAlt,
    FaWarehouse,
    FaFileCsv,
    FaFilePdf,
    FaExclamationTriangle,
    FaHistory,
    FaBook,
} from 'react-icons/fa';

import { getKardexPorProducto, generarPdfKardex } from '@/lib/reportesInventarioService';
import { getBodegas } from '@/lib/bodegaService';


// Estilos Reusables
const selectClass = "w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white";

const formatCurrency = (val, digits = 2) => {
    if (val === null || val === undefined) return '-';
    return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: digits, maximumFractionDigits: digits }).format(val);
};

const formatNumber = (val) => {
    if (val === null || val === undefined) return '-';
    return val.toFixed(2);
};

const KardexPage = () => {
    const params = useParams();
    const searchParams = useSearchParams();
    const router = useRouter();

    const productoId = params.productoId;
    const fecha_inicio = searchParams.get('desde');
    const fecha_fin = searchParams.get('hasta');
    const bodega_query = searchParams.get('bodega');

    const [kardexData, setKardexData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [isExportingPdf, setIsExportingPdf] = useState(false);
    const [bodegas, setBodegas] = useState([]);
    const [bodegaSeleccionadaId, setBodegaSeleccionadaId] = useState('');

    // --- LÓGICA DE DATOS (INTACTA) ---

    const fetchKardex = useCallback(async (bodegaIdParam) => {
        if (!productoId || !fecha_inicio || !fecha_fin) {
            setError('Faltan parámetros de consulta.');
            setLoading(false);
            return;
        }
        setError('');
        try {
            const data = await getKardexPorProducto(
                productoId,
                fecha_inicio,
                fecha_fin,
                bodegaIdParam
            );
            setKardexData(data);
        } catch (err) {
            console.error("Error al obtener Kardex:", err);
            setError(err.response?.data?.detail || 'Error al cargar los datos del Kardex.');
            setKardexData(null);
        }
    }, [productoId, fecha_inicio, fecha_fin]);

    const handleExportCSV = () => {
        if (!kardexData || !kardexData.items) return;
        const headers = ["Fecha", "Documento", "Tipo Movimiento", "Bodega", "Entrada Cantidad", "Entrada Costo Unitario", "Salida Cantidad", "Salida Costo Unitario", "Salida Costo Total", "Saldo Cantidad", "Saldo Costo Promedio", "Saldo Valor Total"];
        const rows = kardexData.items.map(item => {
            const fecha = new Date(item.fecha).toLocaleDateString('es-CO', { timeZone: 'UTC' });
            const documento = `"${item.documento_ref}"`;
            const tipoMov = item.tipo_movimiento;
            const bodega = `"${item.bodega_nombre || ''}"`;
            const entCant = item.entrada_cantidad != null ? item.entrada_cantidad.toFixed(2) : '';
            const entCosto = item.entrada_costo_unit != null ? item.entrada_costo_unit.toFixed(2) : '';
            const salCant = item.salida_cantidad != null ? item.salida_cantidad.toFixed(2) : '';
            const salCostoU = item.salida_costo_unit != null ? item.salida_costo_unit.toFixed(2) : '';
            const salCostoT = item.salida_costo_total != null ? item.salida_costo_total.toFixed(2) : '';
            const saldoCant = item.saldo_cantidad != null ? item.saldo_cantidad.toFixed(2) : '';
            const saldoCostoProm = item.saldo_costo_promedio != null ? item.saldo_costo_promedio.toFixed(2) : '';
            const saldoValor = item.saldo_valor_total != null ? item.saldo_valor_total.toFixed(2) : '';
            return [fecha, documento, tipoMov, bodega, entCant, entCosto, salCant, salCostoU, salCostoT, saldoCant, saldoCostoProm, saldoValor].join(',');
        });
        const csvContent = "\uFEFF" + headers.join(',') + "\n" + rows.join("\n");
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", "data:text/csv;charset=utf-8," + encodedUri);
        const productCode = kardexData.producto_codigo || 'kardex';
        const bodegaCode = bodegaSeleccionadaId ? `_B${bodegaSeleccionadaId}` : '';
        link.setAttribute("download", `Kardex_${productCode}${bodegaCode}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const handleExportPDF = async () => {
        if (!kardexData) return;
        setIsExportingPdf(true);
        setError('');

        const filtros = {
            producto_id: parseInt(productoId),
            fecha_inicio: fecha_inicio,
            fecha_fin: fecha_fin,
            bodega_id: bodegaSeleccionadaId === '' || bodegaSeleccionadaId === null ? null : parseInt(bodegaSeleccionadaId)
        };

        try {
            await generarPdfKardex(filtros);
        } catch (err) {
            console.error("Error al generar PDF:", err);
            let errorMsg = 'Ocurrió un error al generar el PDF.';
            if (err.response && err.response.data instanceof Blob) {
                const errorText = await err.response.data.text();
                try {
                    errorMsg = JSON.parse(errorText).detail || errorMsg;
                } catch (e) { }
            }
            setError(errorMsg);
        } finally {
            setIsExportingPdf(false);
        }
    };

    useEffect(() => {
        let isMounted = true;
        const initialBodega = bodega_query || '';

        const loadData = async () => {
            try {
                const bodegasRes = await getBodegas();
                if (isMounted) setBodegas(bodegasRes || []);
            } catch (error) {
                if (isMounted) setError("Error al cargar bodegas.");
            }
            setBodegaSeleccionadaId(initialBodega);

            if (isMounted) setLoading(true);
            try {
                const data = await getKardexPorProducto(productoId, fecha_inicio, fecha_fin, initialBodega);
                if (isMounted) setKardexData(data);
            } catch (err) {
                if (isMounted) {
                    setError(err.response?.data?.detail || 'Error al cargar los datos del Kardex.');
                    setKardexData(null);
                }
            } finally {
                if (isMounted) setLoading(false);
            }
        };
        loadData();
        return () => { isMounted = false; }
    }, [productoId, fecha_inicio, fecha_fin, bodega_query]);

    const handleBodegaChange = async (e) => {
        const newBodegaId = e.target.value;
        setBodegaSeleccionadaId(newBodegaId);
        const newSearchParams = new URLSearchParams(searchParams.toString());
        if (newBodegaId) newSearchParams.set('bodega', newBodegaId);
        else newSearchParams.delete('bodega');

        router.replace(`/contabilidad/reportes/kardex/${productoId}?${newSearchParams.toString()}`, undefined, { shallow: true });
        await fetchKardex(newBodegaId);
    };

    // --- RENDERIZADO ---

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
                <FaCube className="text-indigo-300 text-6xl mb-4 animate-pulse" />
                <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando Kardex...</p>
            </div>
        );
    }

    const totales = kardexData?.totales;

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
            <div className="max-w-[95%] mx-auto"> {/* Ancho extendido para la tabla grande */}

                {/* ENCABEZADO */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
                    <div>
                        {/* Empty left side or title if added */}
                    </div>
                    <div className="flex gap-3">
                        {kardexData && (
                            <>
                                <button onClick={handleExportCSV} className="flex items-center gap-2 px-4 py-2 bg-white border border-green-500 text-green-600 rounded-lg hover:bg-green-50 font-medium transition-colors shadow-sm text-sm">
                                    <FaFileCsv /> CSV
                                </button>
                                <button onClick={handleExportPDF} disabled={isExportingPdf} className="flex items-center gap-2 px-4 py-2 bg-white border border-red-500 text-red-600 rounded-lg hover:bg-red-50 font-medium transition-colors shadow-sm text-sm">
                                    {isExportingPdf ? <span className="loading loading-spinner loading-xs"></span> : <FaFilePdf />} PDF
                                </button>
                            </>
                        )}
                    </div>
                </div>

                {error && (
                    <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded-r-lg flex items-center gap-3 animate-pulse">
                        <FaExclamationTriangle className="text-xl" />
                        <p>{error}</p>
                    </div>
                )}

                {kardexData && (
                    <>
                        {/* CARD 1: INFORMACIÓN DEL PRODUCTO Y FILTROS */}
                        <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 mb-6 animate-fadeIn">
                            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">

                                <div className="flex items-center gap-4">
                                    <div className="p-3 bg-indigo-100 rounded-xl text-indigo-600">
                                        <FaCube className="text-3xl" />
                                    </div>
                                    <div>
                                        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                                            {kardexData.producto_nombre}
                                            <span className="text-sm font-mono font-normal bg-gray-100 text-gray-600 px-2 py-0.5 rounded">{kardexData.producto_codigo}</span>
                                            <button
                                                onClick={() => window.open('/manual/capitulo_46_kardex_detallado.html', '_blank')}
                                                className="ml-2 flex items-center gap-2 px-2 py-1 bg-white border border-indigo-200 text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors font-medium shadow-sm text-sm"
                                                type="button"
                                                title="Ver Manual de Usuario"
                                            >
                                                <span className="text-lg">📖</span> <span className="hidden md:inline">Manual</span>
                                            </button>
                                        </h1>
                                        <div className="text-sm text-gray-500 mt-1 flex items-center gap-4">
                                            <span className="flex items-center gap-1"><FaHistory className="text-gray-400" /> Periodo: {new Date(fecha_inicio + 'T00:00:00').toLocaleDateString('es-CO')} al {new Date(fecha_fin + 'T00:00:00').toLocaleDateString('es-CO')}</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="w-full md:w-auto min-w-[250px]">
                                    <label className="block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide">Filtrar por Bodega</label>
                                    <div className="relative">
                                        <select
                                            value={bodegaSeleccionadaId}
                                            onChange={handleBodegaChange}
                                            className={selectClass}
                                            disabled={loading}
                                        >
                                            <option value="">-- Todas (Consolidado) --</option>
                                            {bodegas.map(bodega => (
                                                <option key={bodega.id} value={bodega.id.toString()}>
                                                    {bodega.nombre}
                                                </option>
                                            ))}
                                        </select>
                                        <FaWarehouse className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* CARD 2: TABLA DE KARDEX */}
                        <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden animate-slideDown">
                            <div className="overflow-x-auto">
                                <table className="min-w-full divide-y divide-gray-200 text-sm">
                                    <thead>
                                        <tr className="bg-slate-100 text-gray-600 uppercase text-xs font-bold tracking-wider border-b border-gray-200">
                                            <th className="py-3 px-4 text-left border-r border-gray-200 w-32">Fecha</th>
                                            <th className="py-3 px-4 text-left border-r border-gray-200">Documento</th>
                                            <th className="py-3 px-4 text-left border-r border-gray-200 w-32">Movimiento</th>
                                            <th className="py-3 px-4 text-left border-r border-gray-200">Bodega</th>
                                            <th colSpan="2" className="py-2 text-center border-r border-emerald-200 bg-emerald-50 text-emerald-700">Entradas</th>
                                            <th colSpan="3" className="py-2 text-center border-r border-rose-200 bg-rose-50 text-rose-700">Salidas</th>
                                            <th colSpan="3" className="py-2 text-center bg-indigo-50 text-indigo-700">Saldo</th>
                                        </tr>
                                        <tr className="text-[10px] font-bold uppercase text-gray-500 border-b border-gray-200">
                                            <th colSpan="4" className="bg-slate-50 border-r border-gray-200"></th>
                                            {/* Entradas */}
                                            <th className="text-right px-2 py-1 bg-emerald-50/50 border-r border-emerald-100 w-20">Cant.</th>
                                            <th className="text-right px-2 py-1 bg-emerald-50/50 border-r border-emerald-200 w-24">Costo U.</th>
                                            {/* Salidas */}
                                            <th className="text-right px-2 py-1 bg-rose-50/50 border-r border-rose-100 w-20">Cant.</th>
                                            <th className="text-right px-2 py-1 bg-rose-50/50 border-r border-rose-100 w-24">Costo U.</th>
                                            <th className="text-right px-2 py-1 bg-rose-50/50 border-r border-rose-200 w-28">Total</th>
                                            {/* Saldos */}
                                            <th className="text-right px-2 py-1 bg-indigo-50/50 border-r border-indigo-100 w-20">Cant.</th>
                                            <th className="text-right px-2 py-1 bg-indigo-50/50 border-r border-indigo-100 w-24">Costo Prom.</th>
                                            <th className="text-right px-2 py-1 bg-indigo-50/50 w-28">Valor Total</th>
                                        </tr>
                                    </thead>

                                    <tbody className="divide-y divide-gray-100">
                                        {/* SALDO ANTERIOR */}
                                        <tr className="bg-yellow-50 border-b border-yellow-100">
                                            <td colSpan="9" className="px-4 py-2 text-right font-bold text-yellow-800 uppercase text-xs tracking-wider">
                                                Saldo Anterior al {new Date(fecha_inicio + 'T00:00:00').toLocaleDateString('es-CO')}:
                                            </td>
                                            <td className="px-2 py-2 text-right font-mono font-bold text-yellow-900 border-r border-yellow-200 bg-yellow-100/50">
                                                {formatNumber(totales?.saldo_inicial_cantidad)}
                                            </td>
                                            <td className="px-2 py-2 bg-yellow-50 border-r border-yellow-200"></td>
                                            <td className="px-2 py-2 text-right font-mono font-bold text-yellow-900 bg-yellow-100/50">
                                                {formatCurrency(totales?.saldo_inicial_valor, 0)}
                                            </td>
                                        </tr>

                                        {kardexData.items.map((item, index) => (
                                            <tr key={`${item.id}-${index}`} className="hover:bg-gray-50 transition-colors">
                                                <td className="px-4 py-2 whitespace-nowrap text-gray-600 font-mono border-r border-gray-100">
                                                    {new Date(item.fecha).toLocaleDateString('es-CO', { timeZone: 'UTC' })}
                                                </td>
                                                <td className="px-4 py-2 font-medium text-gray-800 border-r border-gray-100 truncate max-w-[150px]" title={item.documento_ref}>
                                                    {item.documento_ref}
                                                </td>
                                                <td className="px-4 py-2 text-gray-500 border-r border-gray-100">{item.tipo_movimiento}</td>
                                                <td className="px-4 py-2 text-gray-500 border-r border-gray-100 truncate max-w-[120px]" title={item.bodega_nombre}>
                                                    {item.bodega_nombre}
                                                </td>

                                                {/* Entradas */}
                                                <td className="px-2 py-2 text-right font-mono text-emerald-700 bg-emerald-50/10 border-r border-emerald-50">
                                                    {item.entrada_cantidad ? formatNumber(item.entrada_cantidad) : ''}
                                                </td>
                                                <td className="px-2 py-2 text-right font-mono text-gray-500 bg-emerald-50/10 border-r border-emerald-100">
                                                    {item.entrada_costo_unit ? formatCurrency(item.entrada_costo_unit) : ''}
                                                </td>

                                                {/* Salidas */}
                                                <td className="px-2 py-2 text-right font-mono text-rose-700 bg-rose-50/10 border-r border-rose-50">
                                                    {item.salida_cantidad ? formatNumber(item.salida_cantidad) : ''}
                                                </td>
                                                <td className="px-2 py-2 text-right font-mono text-gray-500 bg-rose-50/10 border-r border-rose-50">
                                                    {item.salida_costo_unit ? formatCurrency(item.salida_costo_unit) : ''}
                                                </td>
                                                <td className="px-2 py-2 text-right font-mono text-rose-800/70 bg-rose-50/10 border-r border-rose-100">
                                                    {item.salida_costo_total ? formatCurrency(item.salida_costo_total, 0) : ''}
                                                </td>

                                                {/* Saldos */}
                                                <td className="px-2 py-2 text-right font-mono font-bold text-indigo-900 bg-indigo-50/10 border-r border-indigo-50">
                                                    {formatNumber(item.saldo_cantidad)}
                                                </td>
                                                <td className="px-2 py-2 text-right font-mono text-gray-600 bg-indigo-50/10 border-r border-indigo-50">
                                                    {formatCurrency(item.saldo_costo_promedio)}
                                                </td>
                                                <td className="px-2 py-2 text-right font-mono font-bold text-indigo-700 bg-indigo-50/10">
                                                    {formatCurrency(item.saldo_valor_total, 0)}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default KardexPage;