'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/app/context/AuthContext';
import { apiService } from '@/lib/apiService';
import { FaChartPie, FaLeaf, FaBolt, FaHistory, FaCalendarAlt, FaArrowUp, FaArrowDown, FaFilter, FaChevronLeft, FaChevronRight } from 'react-icons/fa';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import ModalComprarPaquete from '@/components/consumo/ModalComprarPaquete';

/**
 * COMPONENTE REUTILIZABLE: DASHBOARD CONSUMO
 * Funciona en dos modos:
 * 1. Modo Cliente Normal: Usa useAuth().empresaId implícito en el backend.
 * 2. Modo Soporte/Espejo: Recibe 'empresaIdOverride' y lo envía al backend.
 */
export default function DashboardConsumoView({ empresaIdOverride = null, apiClient = null }) {
    // Intentar usar useAuth de forma segura. Si falla (fuera de provider), user será null.
    let authContext = {};
    try {
        authContext = useAuth();
    } catch (e) {
        console.warn("DashboardConsumoView: AuthProvider missing (Expected in Support Mode)");
    }
    const { user, authLoading } = authContext || {};

    // Determinar qué cliente API usar
    const finalApiService = apiClient || apiService;

    // Configuración de fecha por defecto
    const today = new Date();
    const [selectedMonth, setSelectedMonth] = useState(today.getMonth() + 1); // 1-12
    const [selectedYear, setSelectedYear] = useState(today.getFullYear());

    const [resumen, setResumen] = useState(null);
    const [historial, setHistorial] = useState([]);
    const [totalConsumo, setTotalConsumo] = useState(0);
    const [loading, setLoading] = useState(true);

    // Estados para Filtros Historial
    const [filterStartDate, setFilterStartDate] = useState('');
    const [filterEndDate, setFilterEndDate] = useState('');
    const [filterType, setFilterType] = useState('TODOS');
    const [page, setPage] = useState(1);
    const LIMIT = 10;

    // Estados para Compra de Recarga
    const [showRecargaModal, setShowRecargaModal] = useState(false);

    // Estados Filtro Recargas (Client-side)
    const [filterRecargasStart, setFilterRecargasStart] = useState('');
    const [filterRecargasEnd, setFilterRecargasEnd] = useState('');

    useEffect(() => {
        // En modo soporte, no dependemos de user.empresaId, sino de que el componente monte
        if (empresaIdOverride) {
            fetchData();
        } else if (user && (user.empresaId || user.empresa_id)) {
            fetchData();
        }
    }, [user, selectedMonth, selectedYear, filterStartDate, filterEndDate, filterType, page, empresaIdOverride]);

    const fetchData = async () => {
        try {
            setLoading(true);

            // Construir Query Params adicionales si hay Override
            let extraParams = '';
            if (empresaIdOverride) {
                extraParams = `&empresa_id=${empresaIdOverride}`;
            }

            const [dataResumen, dataHistorial] = await Promise.all([
                finalApiService.get(`/consumo/resumen?mes=${selectedMonth}&anio=${selectedYear}${extraParams}`),
                finalApiService.get(`/consumo/historial?limit=${LIMIT}&skip=${(page - 1) * LIMIT}&fecha_inicio=${filterStartDate}&fecha_fin=${filterEndDate}&tipo_operacion=${filterType}&filtro_fecha_doc=true${extraParams}`)
            ]);

            setResumen(dataResumen.data);
            // Handle new response structure { items: [], total_cantidad: ... }
            if (dataHistorial.data.items) {
                setHistorial(dataHistorial.data.items);
                setTotalConsumo(dataHistorial.data.total_cantidad);
            } else {
                // Fallback for old structure (just in case)
                setHistorial(dataHistorial.data);
            }
        } catch (error) {
            console.error(error);
            toast.error("Error cargando información de consumo.");
        } finally {
            setLoading(false);
        }
    };

    const getMonthName = (monthIndex) => {
        const date = new Date();
        date.setMonth(monthIndex - 1);
        return date.toLocaleString('es-CO', { month: 'long' });
    };

    const years = [];
    const currentYear = new Date().getFullYear();
    for (let y = 2020; y <= currentYear + 2; y++) {
        years.push(y);
    }
    const months = Array.from({ length: 12 }, (_, i) => i + 1);

    if (!empresaIdOverride && authLoading) return null;

    if (loading && !resumen) {
        return (
            <div className="flex items-center justify-center p-12 bg-slate-50 rounded-lg">
                <div className="animate-pulse flex flex-col items-center">
                    <div className="h-12 w-12 bg-indigo-200 rounded-full mb-4"></div>
                    <div className="h-4 w-32 bg-indigo-100 rounded"></div>
                    <span className="text-gray-400 text-sm mt-2">Cargando datos de consumo...</span>
                </div>
            </div>
        );
    }

    if (!resumen) return <div className="p-10 text-center text-gray-500">No hay información disponible.</div>;

    const plan = resumen.plan_actual;
    // Asegurar valores numéricos para evitar NaN
    const cantidadConsumida = plan?.cantidad_consumida ?? 0;
    const limitAsignado = plan?.limite_asignado ?? 0;

    const porcentajePlan = plan && limitAsignado > 0
        ? Math.round((cantidadConsumida / limitAsignado) * 100)
        : 0;

    // Calcular porcentaje de uso total (incluyendo extras)
    const usoTotal = cantidadConsumida;
    // El 'total_disponible' retornado por API es el REMANENTE.
    // Capacidad operativa aproximada = Consumido + Disponible
    const capacidadEstimada = usoTotal + resumen.total_disponible;

    // Filtrar recargas activas en frontend si se desea
    let recargasFiltradas = resumen.recargas_vigentes;
    if (filterRecargasStart && filterRecargasEnd) {
        // Implementar filtro local si es necesario, o dejarlo visual
    }

    const totalPendienteRecargas = resumen.recargas_vigentes.reduce((acc, r) => acc + (r.valor_total || 0), 0);

    return (
        <div className="space-y-6">
            <ToastContainer />

            {/* HEADER CONTEXTUAL */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center bg-slate-900 text-white p-6 rounded-xl shadow-lg">
                <div>

                    {empresaIdOverride ? (
                        <h1 className="text-2xl font-bold flex items-center gap-2 text-yellow-400">
                            <FaHistory /> VISTA ESPEJO ADMIN
                        </h1>
                    ) : (
                        <h1 className="text-2xl font-bold flex items-center gap-2">
                            <FaHistory /> Gestión de Consumo
                        </h1>
                    )}
                    <p className="text-slate-400 text-sm mt-1">
                        {empresaIdOverride ? "Estás viendo los datos tal como los ve el cliente." : "Monitorea tu plan, recargas y actividad histórica detallada."}
                    </p>
                </div>

                <div className="flex gap-3 mt-4 md:mt-0">
                    <select
                        value={selectedMonth}
                        onChange={(e) => setSelectedMonth(parseInt(e.target.value))}
                        className="bg-slate-800 border-none text-white rounded px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500"
                    >
                        {months.map(m => (
                            <option key={m} value={m}>{getMonthName(m)}</option>
                        ))}
                    </select>

                    <select
                        value={selectedYear}
                        onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                        className="bg-slate-800 border-none text-white rounded px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500"
                    >
                        {years.map(y => (
                            <option key={y} value={y}>{y}</option>
                        ))}
                    </select>
                </div>
            </div>

            {/* TARJETAS SUPERIORES */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

                {/* 1. PLAN MENSUAL */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 flex flex-col justify-between">
                    <div>
                        <div className="flex justify-between items-start mb-4">
                            <div>
                                <h3 className="tex-sm font-semibold text-slate-500 uppercase tracking-wider">Plan Mensual</h3>
                                <p className="text-xs text-slate-400">{getMonthName(selectedMonth)} {selectedYear}</p>
                            </div>
                            <div className={`p-2 rounded-full ${plan?.estado === 'ABIERTO' ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'}`}>
                                <FaCalendarAlt />
                            </div>
                        </div>

                        {plan ? (
                            <>
                                <div className="flex items-end gap-2 mb-2">
                                    <span className="text-4xl font-bold text-slate-800">{cantidadConsumida}</span>
                                    <span className="text-lg text-slate-400 font-medium mb-1">/ {limitAsignado}</span>
                                </div>

                                {/* Barra de Progreso */}
                                <div className="w-full bg-slate-100 rounded-full h-2.5 mb-2 overflow-hidden">
                                    <div
                                        className={`h-2.5 rounded-full ${porcentajePlan > 90 ? 'bg-red-500' : porcentajePlan > 75 ? 'bg-orange-500' : 'bg-indigo-600'}`}
                                        style={{ width: `${Math.min(porcentajePlan, 100)}%` }}
                                    ></div>
                                </div>
                                <div className="flex justify-between text-xs text-slate-500">
                                    <span>{porcentajePlan}% Usado</span>
                                    <span>{limitAsignado - cantidadConsumida} Disp. (Plan)</span>
                                </div>
                            </>
                        ) : (
                            <p className="text-sm text-gray-400 italic">No hay plan configurado para este mes.</p>
                        )}
                    </div>
                </div>

                {/* 2. DISPONIBILIDAD TOTAL (Real Time) */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 flex flex-col justify-between relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-50 rounded-full -mr-10 -mt-10 opacity-50"></div>

                    <div>
                        <div className="flex justify-between items-start mb-4 relative z-10">
                            <h3 className="tex-sm font-semibold text-indigo-600 uppercase tracking-wider">Capacidad Operativa Total</h3>
                            <FaBolt className="text-indigo-400" />
                        </div>

                        <div className="relative z-10">
                            <span className="text-5xl font-black text-slate-800">{resumen.total_disponible}</span>
                            <p className="text-sm text-slate-500 mt-2">Registros disponibles HOY</p>
                            <p className="text-xs text-slate-400 mt-1">Suma de Plan + Bolsas + Recargas activas</p>
                        </div>
                    </div>

                    <button
                        onClick={() => setShowRecargaModal(true)}
                        className="mt-4 w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition shadow-md hover:shadow-lg relative z-10"
                    >
                        Comprar Paquete Extra
                    </button>
                </div>

                {/* 3. BOLSAS Y EXCEDENTES */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 overflow-y-auto max-h-60">
                    <div className="flex justify-between items-center mb-4 sticky top-0 bg-white pb-2 border-b border-slate-50">
                        <h3 className="tex-sm font-semibold text-teal-600 uppercase tracking-wider">Bolsas Acumuladas</h3>
                        <FaLeaf className="text-teal-400" />
                    </div>

                    <div className="space-y-3">
                        {resumen.bolsas_vigentes.length > 0 ? (
                            resumen.bolsas_vigentes.map(bolsa => (
                                <div key={bolsa.id} className="flex justify-between items-center bg-teal-50 p-3 rounded-lg border border-teal-100">
                                    <div>
                                        <p className="text-xs font-bold text-teal-800">Origen: {getMonthName(bolsa.mes_origen)} {bolsa.anio_origen}</p>
                                        <p className="text-[10px] text-teal-600">Vence: {new Date(bolsa.fecha_vencimiento).toLocaleDateString()}</p>
                                    </div>
                                    <span className="text-lg font-bold text-teal-700">+{bolsa.cantidad_disponible}</span>
                                </div>
                            ))
                        ) : (
                            <p className="text-sm text-slate-400 italic text-center py-4">No tienes bolsas acumuladas vigentes.</p>
                        )}
                    </div>
                </div>
            </div>

            {/* SECCIÓN INFERIOR: HISTORIAL Y DETALLE */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* COLUMNA IZQ: RECARGAS ACTIVAS */}
                <div className="lg:col-span-1 bg-slate-800 text-white rounded-xl shadow-lg p-6 h-fit">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="font-bold text-lg flex items-center gap-2">
                            <FaBolt className="text-yellow-400" /> Recargas Activas
                        </h3>
                        <span className="bg-slate-700 px-2 py-1 rounded text-xs text-slate-300">Este Mes</span>
                    </div>

                    <div className="space-y-4">
                        {resumen.recargas_vigentes.length > 0 ? (
                            resumen.recargas_vigentes.map(recarga => (
                                <div key={recarga.id} className="bg-slate-700/50 p-4 rounded-lg border border-slate-600">
                                    <div className="flex justify-between items-start mb-2">
                                        <div>
                                            <p className="text-xs text-slate-400">{new Date(recarga.fecha_compra).toLocaleDateString()}</p>
                                            <p className="text-sm font-medium text-white">Compra Adicional</p>
                                        </div>
                                        <span className={`text-xs px-2 py-1 rounded font-bold ${recarga.facturado ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
                                            {recarga.facturado ? 'PAGADO' : 'PENDIENTE'}
                                        </span>
                                    </div>
                                    <div className="flex justify-between items-end">
                                        <div>
                                            <span className="text-xs text-slate-400">Saldo:</span>
                                            <div className="text-xl font-bold text-white">{recarga.cantidad_disponible} <span className="text-xs font-normal text-slate-400">/ {recarga.cantidad_comprada}</span></div>
                                        </div>
                                        <div className="text-right">
                                            <span className="text-xs text-slate-400">Valor:</span>
                                            <div className="font-mono text-indigo-300">$ {recarga.valor_total?.toLocaleString()}</div>
                                        </div>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="text-center py-8 text-slate-500">
                                <p>No has comprado recargas extras este mes.</p>
                            </div>
                        )}
                    </div>

                    <div className="mt-6 pt-4 border-t border-slate-700">
                        <div className="flex justify-between items-center text-sm">
                            <span className="text-slate-400">Total Pendiente Pago:</span>
                            <span className="font-bold text-yellow-400 text-lg">$ {totalPendienteRecargas.toLocaleString()}</span>
                        </div>
                    </div>
                </div>

                {/* COLUMNA DER: HISTORIAL DE TRANSACCIONES */}
                <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-slate-100 flex flex-col">

                    {/* Toolbar Filtros */}
                    <div className="p-4 border-b border-slate-100 flex flex-wrap gap-4 items-center justify-between bg-slate-50/50 rounded-t-xl">
                        <h3 className="font-bold text-slate-700 flex items-center gap-2">
                            <FaHistory className="text-slate-400" /> Actividad Reciente
                        </h3>

                        <div className="flex flex-wrap gap-2">
                            <input
                                type="date"
                                value={filterStartDate}
                                onChange={(e) => setFilterStartDate(e.target.value)}
                                className="px-2 py-1 text-xs border border-slate-200 rounded focus:ring-1 focus:ring-indigo-500"
                            />
                            <span className="text-slate-400">-</span>
                            <input
                                type="date"
                                value={filterEndDate}
                                onChange={(e) => setFilterEndDate(e.target.value)}
                                className="px-2 py-1 text-xs border border-slate-200 rounded focus:ring-1 focus:ring-indigo-500"
                            />
                            <select
                                value={filterType}
                                onChange={(e) => setFilterType(e.target.value)}
                                className="px-2 py-1 text-xs border border-slate-200 rounded focus:ring-1 focus:ring-indigo-500 bg-white"
                            >
                                <option value="TODOS">Todas las Operaciones</option>
                                <option value="CONSUMO">Consumos</option>
                                <option value="COMPRA">Compras Recargas</option>
                                <option value="REVERSION">Reversiones (Anulaciones)</option>
                                <option value="EXPIRACION">Expiraciones</option>
                            </select>

                            {/* Exportar PDF Button */}
                            <button
                                onClick={async () => {
                                    try {
                                        let extraParams = '';
                                        if (empresaIdOverride) extraParams = `&empresa_id=${empresaIdOverride}`;

                                        const url = `/consumo/reporte/pdf?fecha_inicio=${filterStartDate}&fecha_fin=${filterEndDate}&tipo_operacion=${filterType}&filtro_fecha_doc=true&t=${new Date().getTime()}${extraParams}`;
                                        const response = await finalApiService.get(url, { responseType: 'blob' });
                                        const blob = new Blob([response.data], { type: 'application/pdf' });
                                        const link = document.createElement('a');
                                        link.href = window.URL.createObjectURL(blob);
                                        link.download = `Historial_Consumo_${new Date().toISOString().split('T')[0]}.pdf`;
                                        link.click();
                                    } catch (err) {
                                        toast.error("Error descargando PDF");
                                    }
                                }}
                                className="ml-2 px-3 py-1 bg-red-50 text-red-600 border border-red-200 rounded text-xs font-medium hover:bg-red-100 flex items-center gap-1"
                            >
                                <FaFilter /> PDF
                            </button>
                        </div>
                    </div>

                    {/* Lista Transacciones */}
                    <div className="flex-1 overflow-auto p-4 min-h-[400px]">
                        <div className="space-y-3">
                            {historial.length > 0 ? (
                                historial.map((item, idx) => (
                                    <div key={idx} className="flex items-center justify-between p-3 border border-slate-100 rounded-lg hover:bg-slate-50 transition">

                                        {/* Izquierda: Fecha y Hora */}
                                        <div className="w-24 shrink-0">
                                            <p className="text-xs font-bold text-slate-700">
                                                {new Date(item.fecha).toLocaleDateString()}
                                            </p>
                                            <p className="text-[10px] text-slate-400">
                                                {new Date(item.fecha).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                            </p>
                                        </div>

                                        {/* Centro: Icono + Detalle */}
                                        <div className="flex-1 flex items-center gap-3 px-4">
                                            <div className={`p-2 rounded-full shrink-0 ${item.tipo_operacion === 'CONSUMO' ? 'bg-indigo-50 text-indigo-500' :
                                                item.tipo_operacion === 'COMPRA' ? 'bg-yellow-50 text-yellow-600' :
                                                    item.tipo_operacion === 'REVERSION' ? 'bg-green-50 text-green-600' :
                                                        'bg-slate-100 text-slate-500'
                                                }`}>
                                                {item.tipo_operacion === 'CONSUMO' && <FaArrowDown />}
                                                {item.tipo_operacion === 'COMPRA' && <FaArrowUp />}
                                                {item.tipo_operacion === 'REVERSION' && <FaHistory />}
                                            </div>

                                            <div>
                                                <p className="text-sm font-semibold text-slate-700 capitalize">
                                                    {item.tipo_operacion === 'COMPRA' ? 'Compra Recarga' : item.tipo_operacion.toLowerCase()}
                                                </p>
                                                <p className="text-xs text-slate-400 uppercase tracking-wide">
                                                    {item.fuente_tipo}
                                                    {item.bolsa_origen && <span className="ml-1 bg-teal-100 text-teal-700 px-1 rounded text-[9px]">{item.bolsa_origen}</span>}
                                                </p>
                                                {item.documento_numero && (
                                                    <p className="text-xs text-indigo-500 font-bold">Doc #{item.documento_numero}</p>
                                                )}
                                            </div>
                                        </div>

                                        {/* Derecha: Cantidad */}
                                        <div className={`text-right w-20 font-bold text-lg ${['REVERSION', 'COMPRA'].includes(item.tipo_operacion) ? 'text-green-500' : 'text-slate-800'
                                            }`}>
                                            {['REVERSION', 'COMPRA'].includes(item.tipo_operacion) ? '+' : '-'}{item.cantidad}
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <div className="text-center py-20 text-gray-300">
                                    <FaHistory className="mx-auto text-4xl mb-3 opacity-30" />
                                    No hay registros de historia para este filtro.
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Pagination Footer */}
                    <div className="p-4 border-t border-slate-100 flex justify-between items-center bg-slate-50 rounded-b-xl">
                        <button
                            onClick={() => setPage(p => Math.max(1, p - 1))}
                            disabled={page === 1}
                            className={`flex items-center gap-1 text-xs font-semibold px-3 py-2 rounded ${page === 1 ? 'text-slate-300 cursor-not-allowed' : 'text-slate-600 hover:bg-white border'}`}
                        >
                            <FaChevronLeft /> Anterior
                        </button>

                        <span className="text-xs font-bold text-slate-500">Página {page}</span>

                        <button
                            onClick={() => setPage(p => p + 1)}
                            // disabled={historial.length < LIMIT} // Simple check
                            className="flex items-center gap-1 text-xs font-semibold px-3 py-2 rounded text-slate-600 hover:bg-white border"
                        >
                            Siguiente <FaChevronRight />
                        </button>
                    </div>

                    {/* Footer Totals */}
                    <div className="px-6 py-2 bg-slate-100 text-right text-xs text-slate-500 border-t border-slate-200">
                        Total acumulado en periodo: <span className="font-bold">{totalConsumo}</span>
                    </div>

                </div>
            </div>

            {/* MODAL COMPRA (Solo para usuario normal, no soporte mirror) */}
            {!empresaIdOverride && showRecargaModal && (
                <ModalComprarPaquete
                    isOpen={showRecargaModal}
                    onClose={() => setShowRecargaModal(false)}
                    onSuccess={() => {
                        fetchData();
                        setShowRecargaModal(false);
                    }}
                />
            )}
        </div>
    );
}
