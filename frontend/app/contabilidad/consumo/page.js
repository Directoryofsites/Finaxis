'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/app/context/AuthContext';
import { apiService } from '@/lib/apiService';
// ... (imports remain)
import { FaChartPie, FaLeaf, FaBolt, FaHistory, FaCalendarAlt, FaArrowUp, FaArrowDown, FaFilter, FaChevronLeft, FaChevronRight } from 'react-icons/fa';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import ModalComprarPaquete from '@/components/consumo/ModalComprarPaquete';

export default function DashboardConsumoPage() {
    const { user, authLoading } = useAuth();

    // Configuración de fecha por defecto
    const today = new Date();
    const [selectedMonth, setSelectedMonth] = useState(today.getMonth() + 1); // 1-12
    const [selectedYear, setSelectedYear] = useState(today.getFullYear());

    const [resumen, setResumen] = useState(null);
    const [historial, setHistorial] = useState([]);
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
        if (user && (user.empresaId || user.empresa_id)) {
            fetchData();
        }
    }, [user, selectedMonth, selectedYear, filterStartDate, filterEndDate, filterType, page]);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [dataResumen, dataHistorial] = await Promise.all([
                apiService.get(`/consumo/resumen?mes=${selectedMonth}&anio=${selectedYear}`),
                apiService.get(`/consumo/historial?limit=${LIMIT}&skip=${(page - 1) * LIMIT}&fecha_inicio=${filterStartDate}&fecha_fin=${filterEndDate}&tipo_operacion=${filterType}`)
            ]);

            setResumen(dataResumen.data);
            setHistorial(dataHistorial.data);
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

    if (authLoading) return null;

    if (loading && !resumen) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-slate-50">
                <div className="animate-pulse flex flex-col items-center">
                    <div className="h-12 w-12 bg-indigo-200 rounded-full mb-4"></div>
                    <div className="h-4 w-32 bg-indigo-100 rounded"></div>
                </div>
            </div>
        );
    }

    if (!resumen) return <div className="p-10 text-center text-gray-500">No hay información disponible.</div>;

    const plan = resumen.plan_actual;
    const porcentajePlan = plan && plan.limite_asignado > 0
        ? Math.round(((plan.limite_asignado - plan.cantidad_disponible) / plan.limite_asignado) * 100)
        : 0;

    const totalBolsa = resumen.bolsas_vigentes.reduce((acc, b) => acc + b.cantidad_disponible, 0);
    const totalRecargas = resumen.recargas_vigentes.reduce((acc, r) => acc + r.cantidad_disponible, 0);
    const totalOperativo = (plan ? plan.cantidad_disponible : 0) + totalBolsa + totalRecargas;

    return (
        <div className="min-h-screen bg-slate-50 p-6 md:p-12 font-sans text-slate-800">
            <ToastContainer position="bottom-right" theme="colored" />

            <div className="max-w-7xl mx-auto space-y-10">

                {/* HEADER FLOATING */}
                <div className="flex flex-col md:flex-row justify-between items-end md:items-center gap-6">
                    <div>
                        <h1 className="text-4xl font-black text-slate-900 tracking-tight mb-2">Mi Consumo</h1>
                        <p className="text-slate-500 font-medium">Gestiona tu capacidad operativa inteligentemente.</p>
                    </div>

                    <div className="flex items-center gap-4 bg-white p-2 rounded-2xl shadow-xl shadow-slate-200/50 pr-6">
                        <div className="bg-indigo-50 p-3 rounded-xl">
                            <FaCalendarAlt className="text-indigo-600 " />
                        </div>
                        <div className="flex gap-2">
                            <select
                                value={selectedMonth}
                                onChange={(e) => setSelectedMonth(parseInt(e.target.value))}
                                className="bg-transparent font-bold text-slate-700 focus:outline-none capitalize cursor-pointer hover:text-indigo-600 transition-colors"
                            >
                                {months.map(m => <option key={m} value={m}>{getMonthName(m)}</option>)}
                            </select>
                            <span className="text-slate-300">|</span>
                            <select
                                value={selectedYear}
                                onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                                className="bg-transparent font-bold text-slate-700 focus:outline-none cursor-pointer hover:text-indigo-600 transition-colors"
                            >
                                {years.map(y => <option key={y} value={y}>{y}</option>)}
                            </select>
                        </div>
                    </div>
                </div>

                {/* ✨ TOTAL OPERATIVO BANNER (NUEVO) ✨ */}
                <div className="bg-slate-900 rounded-3xl p-6 md:p-8 text-white shadow-xl shadow-slate-300 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-600 rounded-full blur-[80px] opacity-40 -mr-20 -mt-20"></div>
                    <div className="relative z-10 flex flex-col md:flex-row justify-between items-center gap-6">
                        <div>
                            <h2 className="text-slate-400 font-bold uppercase tracking-wider text-sm mb-2">Capacidad Operativa Total</h2>
                            <div className="flex items-baseline gap-3">
                                <span className="text-6xl font-black tracking-tighter text-white">{totalOperativo.toLocaleString()}</span>
                                <span className="text-xl text-slate-400 font-medium">registros disponibles hoy</span>
                            </div>
                            <p className="text-slate-400 text-sm mt-2 flex items-center gap-2">
                                <span className={`w-2 h-2 rounded-full ${totalOperativo > 0 ? "bg-green-400" : "bg-red-500"}`}></span>
                                {totalOperativo > 0
                                    ? "Sistema habilitado para crear documentos."
                                    : "Sistema detenido. Se requiere recarga."}
                            </p>
                        </div>
                        {totalOperativo <= 50 && totalOperativo > 0 && (
                            <div className="bg-amber-500/20 text-amber-200 px-4 py-3 rounded-xl border border-amber-500/30 text-sm font-bold flex items-center gap-3 animate-pulse">
                                <FaBolt className="text-xl" />
                                <div>
                                    <p>Saldo Bajo</p>
                                    <p className="text-xs font-normal text-amber-100/70">Considera adquirir un paquete.</p>
                                </div>
                            </div>
                        )}
                        {totalOperativo <= 0 && (
                            <button
                                onClick={() => setShowRecargaModal(true)}
                                className="bg-red-500 hover:bg-red-600 text-white px-6 py-3 rounded-xl font-bold shadow-lg shadow-red-500/40 transition-transform hover:scale-105 flex items-center gap-2"
                            >
                                <FaBolt /> Recargar Ahora
                            </button>
                        )}
                    </div>
                </div>

                {/* KPI GRID */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">

                    {/* CARD 1: PLAN MENSUAL */}
                    <div className="bg-white rounded-[2rem] p-8 shadow-2xl shadow-indigo-100/50 relative overflow-hidden group hover:-translate-y-1 transition-transform duration-300">
                        <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-50 rounded-bl-full -mr-10 -mt-10 transition-transform group-hover:scale-110"></div>
                        <FaChartPie className="absolute top-8 right-8 text-indigo-200 text-3xl relative z-10" />

                        <div className="relative z-10">
                            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-6">Plan Mensual</h3>

                            {plan ? (
                                <>
                                    <div className="flex items-baseline gap-2 mb-4">
                                        <span className="text-5xl font-black text-slate-900 tracking-tighter">
                                            {plan.cantidad_disponible.toLocaleString()}
                                        </span>
                                        <span className="text-slate-400 font-bold text-lg">/ {plan.limite_asignado.toLocaleString()}</span>
                                    </div>

                                    {/* Custom Progress Bar */}
                                    <div className="h-4 w-full bg-slate-100 rounded-full overflow-hidden mb-3">
                                        <div
                                            className="h-full bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full shadow-lg shadow-indigo-200"
                                            style={{ width: `${porcentajePlan}%` }}
                                        ></div>
                                    </div>
                                    <p className="text-slate-500 text-sm font-medium">Has consumido el <span className="text-indigo-600 font-bold">{porcentajePlan}%</span> de tu plan base.</p>
                                </>
                            ) : (
                                <p className="text-slate-400 italic">No tienes un plan activo este mes.</p>
                            )}
                        </div>
                    </div>

                    {/* CARD 2: BOLSA */}
                    <div className="bg-white rounded-[2rem] p-8 shadow-2xl shadow-emerald-100/50 relative overflow-hidden group hover:-translate-y-1 transition-transform duration-300">
                        <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-50 rounded-bl-full -mr-10 -mt-10 transition-transform group-hover:scale-110"></div>
                        <FaLeaf className="absolute top-8 right-8 text-emerald-200 text-3xl relative z-10" />

                        <div className="relative z-10">
                            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-6">Bolsa Acumulada</h3>

                            <div className="flex items-baseline gap-2 mb-2">
                                <span className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-br from-emerald-500 to-teal-700 tracking-tighter">
                                    {totalBolsa.toLocaleString()}
                                </span>
                                <span className="text-emerald-600/50 font-bold text-sm">registros</span>
                            </div>
                            <p className="text-slate-500 font-medium leading-relaxed">
                                Tienes <strong className="text-slate-800">{resumen.bolsas_vigentes.length} tramos</strong> disponibles de meses anteriores.
                            </p>
                        </div>
                    </div>

                    {/* CARD 3: RECARGAS */}
                    <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-[2rem] p-8 shadow-2xl shadow-slate-400/50 relative overflow-hidden group hover:-translate-y-1 transition-transform duration-300 text-white">
                        <div className="absolute -bottom-10 -right-10 w-48 h-48 bg-white/5 rounded-full blur-2xl"></div>
                        <FaBolt className="absolute top-8 right-8 text-amber-400 text-3xl" />

                        <div className="relative z-10 h-full flex flex-col justify-between">
                            <div>
                                <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-6">Recargas Extra</h3>
                                <div className="flex items-baseline gap-2 mb-2">
                                    <span className="text-5xl font-black text-amber-400 tracking-tighter">
                                        {totalRecargas.toLocaleString()}
                                    </span>
                                    <span className="text-slate-400 font-bold text-sm">registros</span>
                                </div>

                                <div className="mt-4 p-4 bg-white/5 rounded-2xl border border-white/10 backdrop-blur-sm">
                                    <p className="text-[10px] font-bold text-amber-200/70 uppercase tracking-wider mb-1">Total a Pagar (Pendiente)</p>
                                    <p className="text-3xl font-black text-white">
                                        ${resumen.recargas_vigentes
                                            .filter(r => !r.facturado) // Solo las no facturadas
                                            .reduce((acc, r) => acc + (r.valor_total || 0), 0)
                                            .toLocaleString('es-CO')}
                                    </p>
                                    <p className="text-[10px] text-amber-100/50 mt-1">Acumulado de recargas no facturadas.</p>
                                </div>
                            </div>

                            <button
                                onClick={() => setShowRecargaModal(true)}
                                className="w-full py-4 mt-4 bg-white/10 hover:bg-white/20 backdrop-blur-md rounded-xl font-bold text-white transition-all flex items-center justify-center gap-2 group-hover:shadow-lg group-hover:shadow-amber-500/20"
                            >
                                <FaBolt className="text-amber-400" /> Comprar Más
                            </button>
                        </div>
                    </div>
                </div>

                {/* DETALLES SECTION */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

                    {/* LEFT COLUMN (Bolsas & Recargas List) - SPAN 5 */}
                    <div className="lg:col-span-5 space-y-8">
                        {/* BOLSAS */}
                        <div className="bg-white rounded-3xl shadow-xl shadow-slate-200/40 p-6">
                            <h3 className="font-bold text-slate-800 mb-6 flex items-center gap-2">
                                <span className="w-8 h-8 rounded-lg bg-emerald-100 flex items-center justify-center text-emerald-600"><FaLeaf size={14} /></span>
                                Detalle de Bolsas
                            </h3>
                            <div className="space-y-3">
                                {resumen.bolsas_vigentes.length === 0 ? (
                                    <p className="text-slate-400 text-sm italic p-4 text-center bg-slate-50 rounded-xl">Sin bolsas vigentes.</p>
                                ) : (
                                    resumen.bolsas_vigentes.map(b => (
                                        <div key={b.id} className="flex justify-between items-center p-4 bg-slate-50 rounded-2xl hover:bg-emerald-50/50 transition-colors group">
                                            <div>
                                                <p className="font-bold text-slate-700 text-sm">Origen {b.mes_origen}/{b.anio_origen}</p>
                                                <p className="text-xs text-slate-400">Vence: {new Date(b.fecha_vencimiento).toLocaleDateString()}</p>
                                            </div>
                                            <div className="text-right">
                                                <span className="block font-black text-emerald-600">{b.cantidad_disponible.toLocaleString()}</span>
                                                <span className="text-[10px] text-slate-400 uppercase tracking-wide">Disponible</span>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>

                        {/* RECARGAS */}
                        <div className="bg-white rounded-3xl shadow-xl shadow-slate-200/40 p-6">
                            <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
                                <span className="w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center text-amber-600"><FaBolt size={14} /></span>
                                Recargas Activas
                            </h3>

                            {/* Filtros de Fecha para Recargas */}
                            <div className="flex gap-2 mb-4 bg-slate-50 p-2 rounded-lg">
                                <input
                                    type="date"
                                    value={filterRecargasStart}
                                    onChange={(e) => setFilterRecargasStart(e.target.value)}
                                    className="w-full bg-white border-transparent text-[10px] rounded hover:bg-slate-50 focus:bg-white focus:ring-0 text-slate-500"
                                    placeholder="Desde"
                                />
                                <span className="text-slate-300 self-center">-</span>
                                <input
                                    type="date"
                                    value={filterRecargasEnd}
                                    onChange={(e) => setFilterRecargasEnd(e.target.value)}
                                    className="w-full bg-white border-transparent text-[10px] rounded hover:bg-slate-50 focus:bg-white focus:ring-0 text-slate-500"
                                    placeholder="Hasta"
                                />
                            </div>

                            <div className="space-y-3 max-h-[300px] overflow-y-auto pr-1">
                                {resumen.recargas_vigentes
                                    .filter(r => {
                                        if (!filterRecargasStart && !filterRecargasEnd) return true;
                                        const fecha = new Date(r.fecha_compra);
                                        const start = filterRecargasStart ? new Date(filterRecargasStart) : new Date('2000-01-01');
                                        const end = filterRecargasEnd ? new Date(filterRecargasEnd) : new Date('2100-01-01');
                                        end.setHours(23, 59, 59);
                                        return fecha >= start && fecha <= end;
                                    })
                                    .length === 0 ? (
                                    <p className="text-slate-400 text-sm italic p-4 text-center bg-slate-50 rounded-xl">
                                        {(filterRecargasStart || filterRecargasEnd) ? 'No se encontraron recargas.' : 'Sin recargas activas.'}
                                    </p>
                                ) : (
                                    resumen.recargas_vigentes
                                        .filter(r => {
                                            if (!filterRecargasStart && !filterRecargasEnd) return true;
                                            const fecha = new Date(r.fecha_compra);
                                            const start = filterRecargasStart ? new Date(filterRecargasStart) : new Date('2000-01-01');
                                            const end = filterRecargasEnd ? new Date(filterRecargasEnd) : new Date('2100-01-01');
                                            end.setHours(23, 59, 59);
                                            return fecha >= start && fecha <= end;
                                        })
                                        .map(r => (
                                            <div key={r.id} className="flex justify-between items-center p-4 bg-slate-50 rounded-2xl hover:bg-amber-50/50 transition-colors group">
                                                <div>
                                                    <p className="font-bold text-slate-700 text-sm">Compra {new Date(r.fecha_compra).toLocaleDateString()}</p>
                                                    <p className="text-xs text-slate-400">Extraordinaria</p>
                                                </div>
                                                <div className="text-right">
                                                    <div className="text-xs text-slate-400 mb-1">
                                                        <span className="font-semibold text-slate-600">Original: {r.cantidad_comprada?.toLocaleString()}</span>
                                                    </div>
                                                    <span className="block font-black text-amber-600 text-lg">{r.cantidad_disponible.toLocaleString()}</span>
                                                    <span className="text-[10px] text-slate-400 uppercase tracking-wide">Disponible</span>
                                                </div>
                                            </div>
                                        ))
                                )}
                            </div>
                        </div>
                    </div>

                    {/* RIGHT COLUMN (Historial) - SPAN 7 */}
                    <div className="lg:col-span-7">
                        <div className="bg-white rounded-3xl shadow-xl shadow-slate-200/40 p-8 h-full flex flex-col">
                            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
                                <h3 className="font-bold text-slate-800 flex items-center gap-2">
                                    <span className="w-8 h-8 rounded-lg bg-indigo-100 flex items-center justify-center text-indigo-600"><FaHistory size={14} /></span>
                                    Actividad Reciente
                                </h3>

                                {/* FILTERS TOOLBAR */}
                                <div className="flex flex-wrap items-center gap-2 bg-slate-50 p-2 rounded-xl border border-slate-100">
                                    <div className="flex items-center gap-2 text-slate-400 text-xs font-bold px-2">
                                        <FaFilter />
                                    </div>
                                    <select
                                        value={filterType}
                                        onChange={(e) => { setFilterType(e.target.value); setPage(1); }}
                                        className="bg-white border-slate-200 text-xs font-bold text-slate-600 rounded-lg py-1 px-2 focus:ring-0 focus:border-indigo-500"
                                    >
                                        <option value="TODOS">Tipos: Todos</option>
                                        <option value="CONSUMO">Consumos</option>
                                        <option value="REVERSION">Reversiones</option>
                                        <option value="COMPRA">Recargas</option>
                                        <option value="CIERRE">Cierres Mensuales</option>
                                        <option value="EXPIRACION">Expiraciones</option>
                                    </select>
                                    <input
                                        type="date"
                                        value={filterStartDate}
                                        onChange={(e) => { setFilterStartDate(e.target.value); setPage(1); }}
                                        className="bg-white border-slate-200 text-xs text-slate-600 rounded-lg py-1 px-2 focus:ring-0 w-28"
                                    />
                                    <span className="text-slate-300">-</span>
                                    <input
                                        type="date"
                                        value={filterEndDate}
                                        onChange={(e) => { setFilterEndDate(e.target.value); setPage(1); }}
                                        className="bg-white border-slate-200 text-xs text-slate-600 rounded-lg py-1 px-2 focus:ring-0 w-28"
                                    />
                                </div>
                            </div>

                            <div className="flex-1 overflow-auto">
                                <table className="w-full border-separate border-spacing-y-3">
                                    <thead>
                                        <tr className="text-left text-xs font-bold text-slate-400 uppercase tracking-wider">
                                            <th className="pl-4 pb-2">Fecha</th>
                                            <th className="pb-2">Operación</th>
                                            <th className="text-right pr-4 pb-2">Impacto</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {historial.length === 0 ? (
                                            <tr><td colSpan="3" className="text-center py-10 text-slate-400 italic">Sin actividad registrada.</td></tr>
                                        ) : (
                                            historial.map(h => (
                                                <tr key={h.id} className="shadow-sm hover:shadow-md transition-shadow bg-slate-50/50 rounded-xl group">
                                                    <td className="p-4 rounded-l-xl">
                                                        <div className="flex flex-col">
                                                            <span className="font-bold text-slate-700 text-sm">
                                                                {new Date(h.fecha).toLocaleDateString()}
                                                            </span>
                                                            <span className="text-xs text-slate-400 font-mono">
                                                                {new Date(h.fecha).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                            </span>
                                                        </div>
                                                    </td>
                                                    <td className="p-4">
                                                        <div className="flex items-center gap-3">
                                                            <div className={`w-2 h-2 rounded-full 
                                                                ${h.tipo_operacion === 'CONSUMO' ? 'bg-indigo-400' :
                                                                    h.tipo_operacion === 'REVERSION' ? 'bg-emerald-400' :
                                                                        h.tipo_operacion === 'COMPRA' ? 'bg-amber-400' : 'bg-slate-400'}`}></div>
                                                            <div>
                                                                <p className="text-sm font-bold text-slate-700 capitalize">
                                                                    {h.tipo_operacion === 'COMPRA' ? 'Compra Recarga' : h.tipo_operacion.toLowerCase()}
                                                                </p>
                                                                <p className="text-xs text-slate-400 flex items-center gap-1">
                                                                    {h.fuente_tipo}
                                                                    {(h.documento_numero || h.documento_id) && (
                                                                        <span className="text-indigo-400 bg-indigo-50 px-1 rounded flex items-center gap-1 font-bold">
                                                                            Doc #{h.documento_numero || h.documento_id}
                                                                        </span>
                                                                    )}
                                                                </p>
                                                            </div>
                                                        </div>
                                                    </td>
                                                    <td className="p-4 rounded-r-xl text-right">
                                                        <span className={`font-black text-lg ${h.tipo_operacion === 'REVERSION' || h.tipo_operacion === 'COMPRA' ? 'text-emerald-500' : 'text-slate-800'
                                                            }`}>
                                                            {h.tipo_operacion === 'REVERSION' || h.tipo_operacion === 'COMPRA' ? '+' : '-'}{h.cantidad}
                                                        </span>
                                                    </td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                </table>
                            </div>

                            {/* PAGINATION CONTROLS */}
                            <div className="flex justify-between items-center mt-4 pt-4 border-t border-slate-100">
                                <button
                                    onClick={() => setPage(p => Math.max(1, p - 1))}
                                    disabled={page === 1}
                                    className="flex items-center gap-2 text-xs font-bold text-slate-500 disabled:opacity-30 hover:text-indigo-600 px-3 py-2 rounded-lg hover:bg-slate-50 transition-colors"
                                >
                                    <FaChevronLeft /> Anterior
                                </button>
                                <span className="text-xs font-bold text-slate-400">Página {page}</span>
                                <button
                                    onClick={() => setPage(p => p + 1)}
                                    disabled={historial.length < LIMIT}
                                    className="flex items-center gap-2 text-xs font-bold text-slate-500 disabled:opacity-30 hover:text-indigo-600 px-3 py-2 rounded-lg hover:bg-slate-50 transition-colors"
                                >
                                    Siguiente <FaChevronRight />
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <ModalComprarPaquete
                    isOpen={showRecargaModal}
                    onClose={() => setShowRecargaModal(false)}
                    onSuccess={fetchData}
                    month={selectedMonth}
                    year={selectedYear}
                />
            </div>
        </div>
    );
}
