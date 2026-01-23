
'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { phService } from '../../../lib/phService';
import { useRecaudos } from '../../../contexts/RecaudosContext'; // IMPORT

import { FaBuilding, FaPrint, FaMoneyBillWave, FaHistory, FaSearch, FaUserTie, FaReceipt, FaFileInvoiceDollar } from 'react-icons/fa';

import AutocompleteInput from '../../components/AutocompleteInput';

export default function EstadoCuentaPage() {
    const { user, loading: authLoading } = useAuth();
    const { labels } = useRecaudos(); // HOOK

    // Modos
    const [searchMode, setSearchMode] = useState('UNIT'); // 'UNIT' | 'OWNER'
    const [viewMode, setViewMode] = useState('PENDING'); // 'PENDING' (Cartera) | 'HISTORY' (Auxiliar)

    // Selectores
    const [unidades, setUnidades] = useState([]);
    const [propietarios, setPropietarios] = useState([]);

    // Selección Actual
    const [selectedId, setSelectedId] = useState(null); // ID de unidad o propietario segun modo
    const [selectedItem, setSelectedItem] = useState(null); // Objeto completo seleccionado

    // Data
    const [resumen, setResumen] = useState(null); // Info general y saldo
    const [historial, setHistorial] = useState([]); // Movimientos
    const [pendientes, setPendientes] = useState([]); // Cartera

    // Filtros Historial
    const [fechaInicio, setFechaInicio] = useState('');
    const [fechaFin, setFechaFin] = useState('');

    // Estado Detalle Manual
    const [showPortfolioDetail, setShowPortfolioDetail] = useState(false);
    const [detailedPortfolio, setDetailedPortfolio] = useState([]);
    const [loadingDetail, setLoadingDetail] = useState(false);

    const [loading, setLoading] = useState(false);
    const [loadingMaestros, setLoadingMaestros] = useState(false);

    // Cargar listas iniciales
    useEffect(() => {
        if (!authLoading && user?.empresaId) {
            loadMaestros();
        }
    }, [authLoading, user]);

    // Recargar data al cambiar seleccion
    useEffect(() => {
        if (selectedId) {
            loadData(selectedId);
        } else {
            resetData();
        }
    }, [selectedId, searchMode]);

    const loadMaestros = async () => {
        setLoadingMaestros(true);
        try {
            const [dataUnidades, dataPropietarios] = await Promise.all([
                phService.getUnidades(),
                phService.getPropietarios()
            ]);
            setUnidades(dataUnidades);
            setPropietarios(dataPropietarios);
        } catch (error) {
            console.error("Error loading masters", error);
        } finally {
            setLoadingMaestros(false);
        }
    };

    const loadData = async (id) => {
        setLoading(true);
        try {
            let dataResumen = null;
            let dataHistorial = [];
            let dataPendientes = [];

            if (searchMode === 'UNIT') {
                // Modo Unidad - Secuencial para evitar race conditions en backend

                // 1. Historial
                const hist = await phService.getHistorialCuenta(id, {
                    fecha_inicio: fechaInicio || undefined,
                    fecha_fin: fechaFin || undefined
                });
                dataHistorial = hist.transacciones || [];

                // 2. Resumen (Dispara recalculo)
                const res = await phService.getEstadoCuenta(id);
                dataResumen = res;

                // 3. Pendientes (Lee recalculo fresco)
                const pend = await phService.getCarteraPendiente({ unidad_id: id });
                dataPendientes = pend;

            } else {
                // Modo Propietario
                // Ahora si traemos el historial unificado
                const [cons, pend, hist] = await Promise.all([
                    phService.getEstadoCuentaPropietario(id),
                    phService.getCarteraPendiente({ propietario_id: id }),
                    phService.getHistorialCuentaPropietarioDetailed(id, {
                        fecha_inicio: fechaInicio || undefined,
                        fecha_fin: fechaFin || undefined
                    })
                ]);

                dataResumen = {
                    saldo_total: cons.saldo_total_consolidado,
                    propietario_nombre: cons.propietario.nombre
                };
                dataPendientes = pend;
                dataHistorial = hist.transacciones || [];
            }

            setResumen(dataResumen);
            setHistorial(dataHistorial);
            setPendientes(dataPendientes);

        } catch (error) {
            console.error("Error loading details", error);
            alert("Error cargando información: " + error.message);
        } finally {
            setLoading(false);
        }
    };

    const resetData = () => {
        setResumen(null);
        setHistorial([]);
        setPendientes([]);
    };

    const handleSearchModeChange = (mode) => {
        setSearchMode(mode);
        setSelectedId(null);
        setSelectedItem(null);
        resetData();
    };

    const handlePrint = async () => {
        if (!selectedId) return;

        try {
            setLoading(true); // Mostrar loading mientras descarga

            // Construir Query Params
            const params = new URLSearchParams({
                mode: searchMode,
                view: viewMode,
            });
            if (fechaInicio) params.append('fecha_inicio', fechaInicio);
            if (fechaFin) params.append('fecha_fin', fechaFin);

            // Obtener Token
            const token = localStorage.getItem('authToken');

            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/ph/pagos/estado-cuenta/${selectedId}/pdf?${params.toString()}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || "Error al generar el PDF");
            }

            // Descargar Blob
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `EstadoCuenta_${searchMode}_${selectedId}_${viewMode}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();

        } catch (error) {
            console.error("Error downloading PDF:", error);
            alert("No se pudo descargar el reporte: " + error.message);
        } finally {
            setLoading(false);
        }
    };

    const handleOpenDetailReference = async () => {
        if (!selectedId) return;

        setLoadingDetail(true);
        try {
            const data = await phService.getCarteraDetallada(selectedId);
            setDetailedPortfolio(data);
            setShowPortfolioDetail(true);
        } catch (error) {
            console.error("Error cargando detalle cartera:", error);
            alert("Error al cargar detalle: " + error.message);
        } finally {
            setLoadingDetail(false);
        }
    };

    const handleDownloadDetailPDF = async () => {
        if (!selectedId) return;
        setLoadingDetail(true);
        try {
            const token = localStorage.getItem('authToken');
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/ph/pagos/cartera-detallada/${selectedId}/pdf`, {
                method: 'GET',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!response.ok) throw new Error("Error generando PDF");

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `DetalleCartera_${selectedId}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        } catch (error) {
            console.error("Error downloading PDF:", error);
            alert("Error al descargar PDF");
        } finally {
            setLoadingDetail(false);
        }
    };

    if (authLoading) return <div className="p-10 text-center">Cargando...</div>;

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans">
            <div className="max-w-6xl mx-auto">
                <div className="mb-6">
                    <div className="flex justify-between items-end mt-4">
                        <div className="flex items-center gap-3">
                            <div className="p-3 bg-blue-100 rounded-xl text-blue-600">
                                <FaBuilding className="text-2xl" />
                            </div>
                            <div>
                                <h1 className="text-3xl font-bold text-gray-800">Centro de Consulta {labels.module}</h1>
                                <p className="text-gray-500">Consulta integral de estados de cuenta y cartera.</p>
                            </div>
                        </div>
                        {selectedId && !loading && (
                            <button
                                onClick={handlePrint}
                                className="btn-secondary flex items-center gap-2 px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-colors shadow-md"
                            >
                                <FaPrint /> Imprimir {viewMode === 'PENDING' ? 'Cobro' : 'Historial'}
                            </button>
                        )}
                    </div>
                </div>

                {/* --- SECCIÓN 1: BUSCADOR --- */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 mb-6">
                    {/* Switcher Modo Busqueda */}
                    <div className="flex gap-4 mb-4 border-b pb-4">
                        <label className={`flex items-center gap-2 cursor-pointer px-4 py-2 rounded-lg transition-all ${searchMode === 'UNIT' ? 'bg-blue-100 text-blue-700 font-bold' : 'hover:bg-gray-100 text-gray-600'}`}>
                            <input type="radio" name="mode" className="hidden"
                                checked={searchMode === 'UNIT'} onChange={() => handleSearchModeChange('UNIT')} />
                            <FaBuilding /> Por {labels.unidad}
                        </label>
                        <label className={`flex items-center gap-2 cursor-pointer px-4 py-2 rounded-lg transition-all ${searchMode === 'OWNER' ? 'bg-blue-100 text-blue-700 font-bold' : 'hover:bg-gray-100 text-gray-600'}`}>
                            <input type="radio" name="mode" className="hidden"
                                checked={searchMode === 'OWNER'} onChange={() => handleSearchModeChange('OWNER')} />
                            <FaUserTie /> Por {labels.propietario} (Agrupado)
                        </label>
                    </div>

                    {/* Autocomplete */}
                    <div className="relative">
                        <label className="block text-sm font-bold text-gray-700 mb-2">
                            {searchMode === 'UNIT' ? `Buscar ${labels.unidad}` : `Buscar ${labels.propietario} (Nombre, Razón Social)`}
                        </label>
                        {searchMode === 'UNIT' ? (
                            <AutocompleteInput
                                items={unidades}
                                value={selectedItem?.codigo || ''}
                                placeholder={`Escriba código de ${labels.unidad}...`}
                                searchKey="codigo"
                                displayKey="codigo"
                                onChange={(val) => {
                                    setSelectedItem(val);
                                    setSelectedId(val?.id);
                                }}
                                renderOption={(u) => (
                                    <div className="flex justify-between w-full">
                                        <span className="font-bold">{u.codigo}</span>
                                        <span className="text-gray-500 text-sm">{u.propietario_nombre || 'Sin Propietario'}</span>
                                    </div>
                                )}
                            />
                        ) : (
                            <AutocompleteInput
                                items={propietarios}
                                value={selectedItem?.nombre || ''}
                                placeholder="Escriba nombre del propietario..."
                                searchKey="nombre" // La API retorna nombre
                                displayKey="nombre"
                                onChange={(val) => { // val es el objeto propietario: { id, nombre, ... }
                                    // OJO: getPropietarios retorna lista resumen { id, ... }
                                    setSelectedItem(val);
                                    setSelectedId(val?.id);
                                }}
                            />
                        )}
                    </div>
                </div>

                {loading && <div className="text-center py-10"><span className="loading loading-spinner loading-lg text-blue-600"></span></div>}

                {/* --- SECCIÓN 2: RESULTADOS --- */}
                {!loading && selectedId && resumen && (
                    <div className="animate-fadeIn">

                        {/* Resumen Header */}
                        <div className="bg-gradient-to-r from-gray-800 to-gray-900 text-white p-6 rounded-xl shadow-lg mb-6 flex flex-col md:flex-row justify-between items-center gap-4">
                            <div>
                                <h2 className="text-lg opacity-80">Saldo Total Pendiente</h2>
                                <p className="text-4xl font-bold text-green-400">
                                    ${parseFloat(resumen.saldo_total || 0).toLocaleString()}
                                </p>
                                <p className="text-sm mt-1 opacity-70">
                                    {searchMode === 'UNIT' ? `${labels.unidad}: ${selectedItem?.codigo}` : `${labels.propietario}: ${selectedItem?.nombre}`}
                                </p>
                            </div>

                            {/* Selector de VISTA (Tabs) */}
                            <div className="flex bg-gray-700 p-1 rounded-lg gap-1">
                                <button
                                    onClick={() => setViewMode('PENDING')}
                                    className={`px-3 py-2 rounded-md font-medium text-sm transition-all flex items-center gap-2 ${viewMode === 'PENDING' ? 'bg-blue-600 text-white shadow' : 'text-gray-300 hover:text-white'}`}
                                >
                                    <FaFileInvoiceDollar /> Cobro
                                </button>
                                <button
                                    onClick={handleOpenDetailReference}
                                    className={`px-3 py-2 rounded-md font-medium text-sm transition-all flex items-center gap-2 bg-yellow-600 text-white hover:bg-yellow-700 shadow`}
                                    title="Ver desglose por conceptos (Intereses, Multas, etc.)"
                                >
                                    <FaReceipt /> Detalle Conceptos
                                </button>
                                <button
                                    onClick={() => setViewMode('HISTORY')}
                                    className={`px-3 py-2 rounded-md font-medium text-sm transition-all flex items-center gap-2 ${viewMode === 'HISTORY' ? 'bg-blue-600 text-white shadow' : 'text-gray-300 hover:text-white'}`}
                                >
                                    <FaHistory /> Historial
                                </button>
                            </div>
                        </div>

                        {/* Historico Tabla */}
                        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden min-h-[300px]">
                            {viewMode === 'PENDING' ? (
                                /* TABLA PENDIENTES (CARTERA) */
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm">
                                        <thead className="bg-blue-50 text-blue-900 border-b border-blue-100">
                                            <tr>
                                                <th className="px-6 py-4 text-left font-semibold">Fecha Emisión</th>
                                                <th className="px-6 py-4 text-left font-semibold">Documento</th>
                                                <th className="px-6 py-4 text-left font-semibold">Unidad</th>
                                                <th className="px-6 py-4 text-right font-semibold">Valor Original</th>
                                                <th className="px-6 py-4 text-right font-extrabold">Saldo Pendiente</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-50">
                                            {pendientes.length === 0 ? (
                                                <tr><td colSpan="5" className="p-10 text-center text-gray-400">No hay movimientos pendientes. ¡Al día! 🎉</td></tr>
                                            ) : (
                                                pendientes.map((p, idx) => (
                                                    <tr key={idx} className="hover:bg-gray-50 transition-colors">
                                                        <td className="px-6 py-4 text-gray-600">{new Date(p.fecha).toLocaleDateString()}</td>
                                                        <td className="px-6 py-4 font-bold text-gray-800">{p.numero}</td>
                                                        <td className="px-6 py-4">
                                                            <span className="bg-gray-100 px-2 py-1 rounded text-xs font-mono">{p.unidad_codigo}</span>
                                                        </td>
                                                        <td className="px-6 py-4 text-right text-gray-500">${parseFloat(p.valor_total).toLocaleString()}</td>
                                                        <td className={`px-6 py-4 text-right font-bold ${parseFloat(p.saldo_pendiente) < 0 ? 'text-green-600' : 'text-red-600'}`}>
                                                            ${parseFloat(p.saldo_pendiente).toLocaleString()}
                                                        </td>
                                                    </tr>
                                                ))
                                            )}
                                        </tbody>
                                        {pendientes.length > 0 && (
                                            <tfoot className="bg-gray-50 font-bold text-gray-800">
                                                <tr>
                                                    <td colSpan="4" className="px-6 py-4 text-right">TOTAL CARTERA PENDIENTE:</td>
                                                    <td className="px-6 py-4 text-right text-lg border-t border-gray-300">
                                                        ${pendientes.reduce((acc, p) => acc + parseFloat(p.saldo_pendiente), 0).toLocaleString()}
                                                    </td>
                                                </tr>
                                            </tfoot>
                                        )}
                                    </table>
                                </div>
                            ) : (
                                /* TABLA HISTORIAL (MOVIMIENTOS) */
                                <div>
                                    {/* Barra Filtros Fecha */}
                                    <div className="p-4 bg-gray-50 border-b flex flex-wrap gap-4 items-end">
                                        <div>
                                            <label className="block text-xs font-bold text-gray-500 mb-1">Fecha Inicio</label>
                                            <input
                                                type="date"
                                                className="input-sm border rounded"
                                                value={fechaInicio}
                                                onChange={(e) => setFechaInicio(e.target.value)}
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-xs font-bold text-gray-500 mb-1">Fecha Fin</label>
                                            <input
                                                type="date"
                                                className="input-sm border rounded"
                                                value={fechaFin}
                                                onChange={(e) => setFechaFin(e.target.value)}
                                            />
                                        </div>
                                        <button
                                            onClick={() => loadData(selectedId)}
                                            className="px-4 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 shadow-sm"
                                        >
                                            Filtrar
                                        </button>
                                        <button
                                            onClick={() => { setFechaInicio(''); setFechaFin(''); setTimeout(() => loadData(selectedId), 100); }}
                                            className="px-4 py-1.5 bg-white border text-gray-600 rounded text-sm hover:bg-gray-50"
                                        >
                                            Limpiar
                                        </button>
                                    </div>

                                    <div className="overflow-x-auto">
                                        <table className="w-full text-sm">
                                            <thead className="bg-gray-50 text-gray-700 border-b">
                                                <tr>
                                                    <th className="px-6 py-4 text-left font-semibold">Fecha</th>
                                                    <th className="px-6 py-4 text-left font-semibold">Documento</th>
                                                    <th className="px-6 py-4 text-left font-semibold">Detalle</th>
                                                    <th className="px-6 py-4 text-right font-semibold">Cargos</th>
                                                    <th className="px-6 py-4 text-right font-semibold text-green-600">Pagos</th>
                                                    <th className="px-6 py-4 text-right font-bold">Saldo</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-gray-50">
                                                {historial.length === 0 ? (
                                                    <tr><td colSpan="6" className="p-10 text-center text-gray-400">No hay movimientos históricos registrados en este rango.</td></tr>
                                                ) : (
                                                    historial.map((h, idx) => (
                                                        <tr key={idx} className="hover:bg-gray-50 transition-colors">
                                                            <td className="px-6 py-4">{new Date(h.fecha).toLocaleDateString()}</td>
                                                            <td className="px-6 py-4 text-blue-600 font-mono text-xs">{h.documento}</td>
                                                            <td className="px-6 py-4 text-gray-600 max-w-xs">
                                                                <div className="truncate font-medium text-gray-700" title={h.concepto}>{h.concepto}</div>
                                                                {/* Mostrar desglose de pago si existe */}
                                                                {h.detalle_pago && h.detalle_pago.length > 0 && (
                                                                    <div className="text-xs text-green-700 bg-green-50 p-1.5 rounded mt-1 border border-green-200">
                                                                        {h.detalle_pago.map((d, i) => (
                                                                            <div key={i} className="flex gap-1 items-start">
                                                                                <span>•</span> <span>{d}</span>
                                                                            </div>
                                                                        ))}
                                                                    </div>
                                                                )}
                                                                {/* Mostrar desglose de factura si existe (opcional, pero útil) */}
                                                                {h.detalle_conceptos && h.detalle_conceptos.length > 0 && (
                                                                    <div className="text-xs text-gray-500 mt-1 pl-1 border-l-2 border-gray-300">
                                                                        {h.detalle_conceptos.slice(0, 3).map((c, i) => (
                                                                            <div key={i}>{c.concepto}: ${c.valor.toLocaleString()}</div>
                                                                        ))}
                                                                        {h.detalle_conceptos.length > 3 && <div>... (+{h.detalle_conceptos.length - 3})</div>}
                                                                    </div>
                                                                )}
                                                            </td>
                                                            <td className="px-6 py-4 text-right">{h.debito > 0 ? `$${parseFloat(h.debito).toLocaleString()}` : '-'}</td>
                                                            <td className="px-6 py-4 text-right text-green-600">{h.credito > 0 ? `$${parseFloat(h.credito).toLocaleString()}` : '-'}</td>
                                                            <td className="px-6 py-4 text-right font-bold bg-gray-50">${parseFloat(h.saldo).toLocaleString()}</td>
                                                        </tr>
                                                    ))
                                                )}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {!selectedId && !loading && (
                    <div className="flex flex-col items-center justify-center py-20 bg-white rounded-xl border border-dashed border-gray-300">
                        <FaSearch className="text-6xl text-gray-200 mb-4" />
                        <p className="text-gray-500 text-lg">Busque una unidad o propietario para comenzar.</p>
                    </div>
                )}
            </div>

            {/* MODAL DETALLE OBLIGACIONES */}
            {showPortfolioDetail && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm p-4 animate-fadeIn">
                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden transform transition-all scale-100">
                        {/* Header */}
                        <div className="bg-gray-800 text-white px-6 py-4 flex justify-between items-center">
                            <div>
                                <h3 className="text-xl font-bold">Detalle de Cartera</h3>
                                <p className="text-gray-400 text-sm">Desglose por Conceptos</p>
                            </div>
                            <button
                                onClick={() => setShowPortfolioDetail(false)}
                                className="text-gray-400 hover:text-white transition-colors"
                            >
                                <span className="text-2xl">&times;</span>
                            </button>
                        </div>

                        {/* Body */}
                        <div className="p-6 max-h-[60vh] overflow-y-auto">
                            {loadingDetail ? (
                                <div className="text-center py-10">
                                    <span className="loading loading-spinner text-blue-600"></span>
                                    <p className="mt-2 text-gray-500">Calculando distribución...</p>
                                </div>
                            ) : detailedPortfolio.length === 0 ? (
                                <div className="text-center py-10 text-gray-500">
                                    No hay obligaciones pendientes.
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    {/* Lista de Conceptos */}
                                    <div className="divide-y divide-dashed border rounded-xl overflow-hidden">
                                        {detailedPortfolio.map((item, idx) => (
                                            <div key={idx} className="flex justify-between items-center p-4 hover:bg-gray-50">
                                                <div className="flex items-center gap-3">
                                                    {/* Icono segun tipo */}
                                                    <div className={`p-2 rounded-full ${item.tipo === 'INTERES' ? 'bg-red-100 text-red-600' :
                                                        item.tipo === 'MULTA' ? 'bg-orange-100 text-orange-600' :
                                                            'bg-blue-100 text-blue-600'
                                                        }`}>
                                                        {item.tipo === 'INTERES' ? <span className="font-bold text-xs">INT</span> :
                                                            item.tipo === 'MULTA' ? <span className="font-bold text-xs">MUL</span> :
                                                                <FaFileInvoiceDollar />}
                                                    </div>
                                                    <div>
                                                        <p className="font-bold text-gray-800">{item.concepto}</p>
                                                        <p className="text-xs text-gray-500 badge badge-outline badge-sm mt-0.5">{item.tipo}</p>
                                                    </div>
                                                </div>
                                                <span className="font-bold text-gray-800 text-lg">
                                                    ${parseFloat(item.saldo).toLocaleString()}
                                                </span>
                                            </div>
                                        ))}
                                    </div>

                                    {/* Total Footer */}
                                    <div className="flex justify-between items-center bg-gray-100 p-4 rounded-xl border border-gray-200">
                                        <span className="font-bold text-gray-600">TOTAL ANALIZADO</span>
                                        <span className="font-extrabold text-xl text-gray-900">
                                            ${detailedPortfolio.reduce((acc, curr) => acc + parseFloat(curr.saldo), 0).toLocaleString()}
                                        </span>
                                    </div>

                                    <div className="bg-yellow-50 p-3 rounded-lg flex gap-3 items-start text-xs text-yellow-800 border border-yellow-100">
                                        <span className="text-lg">💡</span>
                                        <p>
                                            Este reporte simula la distribución de pagos realizados sobre las facturas pendientes aplicando la prelación:
                                            <b> 1. Intereses, 2. Multas, 3. Capital</b>.
                                        </p>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Footer Actions */}
                        <div className="bg-gray-50 px-6 py-4 flex justify-between">
                            <button
                                onClick={handleDownloadDetailPDF}
                                disabled={loadingDetail}
                                className="flex items-center gap-2 px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors font-bold"
                            >
                                <FaFileInvoiceDollar /> Descargar PDF
                            </button>
                            <button
                                onClick={() => setShowPortfolioDetail(false)}
                                className="btn btn-primary bg-gray-800 text-white px-6 py-2 rounded-lg hover:bg-gray-700"
                            >
                                Cerrar
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
