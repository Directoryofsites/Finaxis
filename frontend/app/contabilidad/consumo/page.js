'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/app/context/AuthContext';
import { apiService } from '@/lib/apiService';
import { FaChartPie, FaLeaf, FaBolt, FaHistory, FaCalendarAlt } from 'react-icons/fa';
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

    // Estados para Compra de Recarga
    const [showRecargaModal, setShowRecargaModal] = useState(false);

    useEffect(() => {
        if (user && (user.empresaId || user.empresa_id)) {
            fetchData();
        }
    }, [user, selectedMonth, selectedYear]); // Trigger reload when date changes

    const fetchData = async () => {
        try {
            setLoading(true);
            const [dataResumen, dataHistorial] = await Promise.all([
                // Pasamos los parámetros de fecha seleccionados
                apiService.get(`/consumo/resumen?mes=${selectedMonth}&anio=${selectedYear}`),
                apiService.get('/consumo/historial?limit=50')
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

    // --- LÓGICA DE COMPRA ---

    // Función auxiliar para formatear moneda/fecha
    const getMonthName = (monthIndex) => { // 1-based index
        const date = new Date();
        date.setMonth(monthIndex - 1);
        return date.toLocaleString('es-CO', { month: 'long' });
    };

    // Generar opciones de años (desde 2020 hasta año actual + 2)
    const years = [];
    const currentYear = new Date().getFullYear();
    for (let y = 2020; y <= currentYear + 2; y++) {
        years.push(y);
    }
    const months = Array.from({ length: 12 }, (_, i) => i + 1);

    if (authLoading) { // Solo mostrar loading full screen en carga inicial de auth
        return (
            <div className="h-screen flex items-center justify-center bg-gray-50">
                <span className="loading loading-spinner text-indigo-600 loading-lg"></span>
            </div>
        );
    }

    // Si está cargando datos pero tenemos auth, mostramos esqueleto o spinner overlay
    // Por simplicidad, spinner centrado si loading es true inicial, o overlay si es update
    if (loading && !resumen) {
        return (
            <div className="h-screen flex items-center justify-center bg-gray-50">
                <div className="flex flex-col items-center gap-4">
                    <span className="loading loading-spinner text-indigo-600 loading-lg"></span>
                    <p className="text-gray-500 font-medium animate-pulse">Cargando métricas de {getMonthName(selectedMonth)}...</p>
                </div>
            </div>
        );
    }

    if (!resumen) return <div className="p-10 text-center">No hay información de consumo disponible.</div>;

    // Cálculos para barra de progreso del plan
    const plan = resumen.plan_actual;
    // Si no hay limite asignado (0), asumimos ilimitado para la visualización o 100%
    const porcentajePlan = plan && plan.limite_asignado > 0
        ? Math.round(((plan.limite_asignado - plan.cantidad_disponible) / plan.limite_asignado) * 100)
        : 0;

    const colorBarra = porcentajePlan > 90 ? 'progress-error' : porcentajePlan > 75 ? 'progress-warning' : 'progress-primary';

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
            <ToastContainer />
            <div className="max-w-7xl mx-auto space-y-8">

                {/* 1. HEADER & DATE SELECTOR */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-gray-200 pb-6">
                    <div className="flex items-center gap-4">
                        <div className="p-4 bg-indigo-600 text-white rounded-2xl shadow-lg shadow-indigo-200">
                            <FaChartPie className="text-3xl" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-extrabold text-gray-800 tracking-tight">Mi Plan y Consumo</h1>
                            <p className="text-gray-500 text-sm mt-1">Gestión de cupos, bolsas y recargas adicionales.</p>
                        </div>
                    </div>

                    {/* SELECTOR DE FECHA */}
                    <div className="flex items-center gap-2 bg-white p-2 rounded-lg shadow-sm border border-gray-200">
                        <FaCalendarAlt className="text-gray-400 ml-2" />

                        <select
                            value={selectedMonth}
                            onChange={(e) => setSelectedMonth(parseInt(e.target.value))}
                            className="select select-sm select-ghost w-auto focus:outline-none focus:ring-0 text-gray-700 font-bold capitalize"
                        >
                            {months.map(m => (
                                <option key={m} value={m}>{getMonthName(m)}</option>
                            ))}
                        </select>

                        <select
                            value={selectedYear}
                            onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                            className="select select-sm select-ghost w-auto focus:outline-none focus:ring-0 text-gray-700 font-bold"
                        >
                            {years.map(y => (
                                <option key={y} value={y}>{y}</option>
                            ))}
                        </select>
                    </div>
                </div>

                {/* 2. KPI CARDS */}
                <div className={`grid grid-cols-1 md:grid-cols-3 gap-6 transition-opacity duration-300 ${loading ? 'opacity-50 pointer-events-none' : 'opacity-100'}`}>

                    {/* CARD PLAN MENSUAL */}
                    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 relative overflow-hidden group hover:shadow-md transition-shadow">
                        <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                            <FaChartPie className="text-8xl text-indigo-600" />
                        </div>

                        <div className="flex justify-between items-start mb-4">
                            <div>
                                <h3 className="text-gray-500 font-bold text-xs uppercase tracking-wider">Plan Mensual</h3>
                                <p className="text-sm text-gray-400 capitalize font-bold">
                                    {getMonthName(selectedMonth)} {selectedYear}
                                </p>
                            </div>
                            <span className={`badge ${plan?.estado === 'ABIERTO' ? 'badge-success badge-outline' : 'badge-ghost'}`}>
                                {plan?.estado || 'No Iniciado'}
                            </span>
                        </div>

                        <div className="mb-4">
                            {plan ? (
                                <>
                                    <div className="flex items-end gap-2">
                                        <span className="text-4xl font-black text-gray-800">{plan.cantidad_disponible}</span>
                                        <span className="text-gray-400 font-medium mb-1">/ {plan.limite_asignado}</span>
                                    </div>
                                    <p className="text-xs text-gray-500">Registros disponibles</p>
                                </>
                            ) : (
                                <div className="py-2">
                                    <p className="text-gray-400 italic text-sm">Sin plan activo para este periodo.</p>
                                </div>
                            )}
                        </div>

                        {plan && (
                            <>
                                <div className="w-full bg-gray-100 rounded-full h-3 mb-2">
                                    <div
                                        className={`h-3 rounded-full transition-all duration-1000 ${colorBarra === 'progress-primary' ? 'bg-indigo-600' : colorBarra === 'progress-warning' ? 'bg-amber-500' : 'bg-red-500'}`}
                                        style={{ width: `${porcentajePlan}%` }}
                                    ></div>
                                </div>
                                <div className="flex justify-between text-xs font-bold text-gray-400">
                                    <span>0%</span>
                                    <span>{porcentajePlan}% Consumido</span>
                                    <span>100%</span>
                                </div>
                            </>
                        )}
                    </div>

                    {/* CARD BOLSA (ACUMULADO) */}
                    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 relative overflow-hidden group hover:shadow-md transition-shadow">
                        <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                            <FaLeaf className="text-8xl text-emerald-600" />
                        </div>

                        <div className="mb-6">
                            <h3 className="text-gray-500 font-bold text-xs uppercase tracking-wider mb-1">Bolsa de Excedentes</h3>
                            <span className="text-xs text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full font-bold">Vigencia 1 año</span>
                        </div>

                        <div className="flex items-end gap-2 mb-2">
                            <span className="text-4xl font-black text-gray-800">
                                {resumen.bolsas_vigentes.reduce((acc, b) => acc + b.cantidad_disponible, 0)}
                            </span>
                            <span className="text-gray-400 text-sm mb-1.5 font-medium">disp.</span>
                        </div>
                        <p className="text-xs text-gray-500 mb-4">Acumulado disponible en este periodo.</p>

                        <div className="divider my-0"></div>
                        <div className="pt-3">
                            <p className="text-xs font-bold text-gray-400">{resumen.bolsas_vigentes.length} Tramos activos</p>
                        </div>
                    </div>

                    {/* CARD RECARGAS */}
                    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 relative overflow-hidden group hover:shadow-md transition-shadow">
                        <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                            <FaBolt className="text-8xl text-amber-500" />
                        </div>

                        <div className="mb-6">
                            <h3 className="text-gray-500 font-bold text-xs uppercase tracking-wider mb-1">Recargas Adicionales</h3>
                            <span className="text-xs text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full font-bold">Vence fin de mes</span>
                        </div>

                        <div className="flex items-end gap-2 mb-2">
                            <span className="text-4xl font-black text-gray-800">
                                {resumen.recargas_vigentes.reduce((acc, r) => acc + r.cantidad_disponible, 0)}
                            </span>
                            <span className="text-gray-400 text-sm mb-1.5 font-medium">disp.</span>
                        </div>
                        <p className="text-xs text-gray-500 mb-4">Compras extra disponibles.</p>

                        <button
                            onClick={() => setShowRecargaModal(true)}
                            className="btn btn-sm btn-warning w-full text-white font-bold shadow-amber-200 shadow-lg"
                        >
                            <FaBolt /> Comprar Recarga
                        </button>
                    </div>
                </div>

                {/* 3. DETALLES (GRID 2) */}
                <div className={`grid grid-cols-1 lg:grid-cols-2 gap-8 ${loading ? 'opacity-50' : 'opacity-100'}`}>

                    {/* TABLA BOLSAS */}
                    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                        <div className="px-6 py-4 border-b border-gray-100 bg-gray-50/50 flex justify-between items-center">
                            <h3 className="font-bold text-gray-700 flex items-center gap-2">
                                <FaLeaf className="text-emerald-500" /> Detalle de Bolsas Vigentes
                            </h3>
                        </div>
                        <div className="overflow-x-auto max-h-64">
                            <table className="table table-pin-rows table-xs w-full">
                                <thead>
                                    <tr>
                                        <th>Origen</th>
                                        <th>Vencimiento</th>
                                        <th className="text-right">Inicial</th>
                                        <th className="text-right">Disponible</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {resumen.bolsas_vigentes.length === 0 ? (
                                        <tr><td colSpan="4" className="text-center py-8 text-gray-400 italic">No había bolsas vigentes en este periodo.</td></tr>
                                    ) : (
                                        resumen.bolsas_vigentes.map(b => (
                                            <tr key={b.id} className="hover:bg-gray-50">
                                                <td className="font-bold text-gray-600">{b.mes_origen}/{b.anio_origen}</td>
                                                <td className="text-gray-500">{new Date(b.fecha_vencimiento).toLocaleDateString()}</td>
                                                <td className="text-right text-gray-400">{b.cantidad_inicial}</td>
                                                <td className="text-right font-bold text-emerald-600">{b.cantidad_disponible}</td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* TABLA RECARGAS */}
                    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                        <div className="px-6 py-4 border-b border-gray-100 bg-gray-50/50 flex justify-between items-center">
                            <h3 className="font-bold text-gray-700 flex items-center gap-2">
                                <FaBolt className="text-amber-500" /> Detalle de Recargas Vigentes
                            </h3>
                        </div>
                        <div className="overflow-x-auto max-h-64">
                            <table className="table table-pin-rows table-xs w-full">
                                <thead>
                                    <tr>
                                        <th>Fecha Compra</th>
                                        <th className="text-right">Comprado</th>
                                        <th className="text-right">Disponible</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {resumen.recargas_vigentes.length === 0 ? (
                                        <tr><td colSpan="3" className="text-center py-8 text-gray-400 italic">No había recargas vigentes.</td></tr>
                                    ) : (
                                        resumen.recargas_vigentes.map(r => (
                                            <tr key={r.id} className="hover:bg-gray-50">
                                                <td className="text-gray-600">{new Date(r.fecha_compra).toLocaleDateString()}</td>
                                                <td className="text-right text-gray-400">{r.cantidad_comprada}</td>
                                                <td className="text-right font-bold text-amber-600">{r.cantidad_disponible}</td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                {/* 4. HISTORIAL DE CONSUMO (Global o Filtrado? Actualmente global ultimos 50) */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden animate-fadeIn">
                    <div className="px-6 py-5 border-b border-gray-100 flex justify-between items-center">
                        <h3 className="font-bold text-gray-800 text-lg flex items-center gap-2">
                            <FaHistory className="text-gray-400" /> Audit Log de Consumo
                        </h3>
                        <span className="text-xs text-gray-400">Últimos 50 movimientos globales</span>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="table w-full">
                            <thead className="bg-gray-50 text-gray-500 uppercase text-xs font-bold">
                                <tr>
                                    <th>Fecha y Hora</th>
                                    <th>Operación</th>
                                    <th>Fuente</th>
                                    <th>Documento ID</th>
                                    <th className="text-right">Cantidad</th>
                                    <th className="text-right">Saldo Final</th>
                                </tr>
                            </thead>
                            <tbody>
                                {historial.length === 0 ? (
                                    <tr><td colSpan="6" className="text-center py-10 text-gray-400">No hay movimientos registrados.</td></tr>
                                ) : (
                                    historial.map(h => (
                                        <tr key={h.id} className="hover:bg-gray-50 border-b border-gray-50 transition-colors">
                                            <td className="text-xs text-gray-500 font-mono">
                                                {new Date(h.fecha).toLocaleString()}
                                            </td>
                                            <td>
                                                {h.tipo_operacion === 'CONSUMO' && <span className="badge badge-error badge-xs badge-outline font-bold">CONSUMO</span>}
                                                {h.tipo_operacion === 'REVERSION' && <span className="badge badge-success badge-xs badge-outline font-bold">REVERSIÓN</span>}
                                                {h.tipo_operacion === 'EXPIRACION' && <span className="badge badge-ghost badge-xs font-bold">EXPIRACIÓN</span>}
                                            </td>
                                            <td className="text-xs font-bold text-gray-600">
                                                {h.fuente_tipo} {h.fuente_id ? <span className="text-gray-300 font-normal">#{h.fuente_id}</span> : ''}
                                            </td>
                                            <td className="text-xs font-mono text-indigo-500">
                                                {h.documento_id || '-'}
                                            </td>
                                            <td className={`text-right font-bold font-mono ${h.tipo_operacion === 'REVERSION' ? 'text-emerald-600' : 'text-gray-700'}`}>
                                                {h.tipo_operacion === 'REVERSION' ? '+' : '-'}{h.cantidad}
                                            </td>
                                            <td className="text-right text-xs text-gray-400 font-mono">
                                                {h.saldo_fuente_despues}
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* 5. MODAL DE COMPRA */}
                <ModalComprarPaquete
                    isOpen={showRecargaModal}
                    onClose={() => setShowRecargaModal(false)}
                    onSuccess={fetchData}
                />

            </div>
        </div>
    );
}
