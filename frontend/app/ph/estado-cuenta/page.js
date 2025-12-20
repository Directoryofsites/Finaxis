
'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { phService } from '../../../lib/phService';

import { FaBuilding, FaPrint, FaMoneyBillWave, FaHistory, FaSearch, FaUserTie, FaReceipt, FaFileInvoiceDollar } from 'react-icons/fa';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import AutocompleteInput from '../../components/AutocompleteInput';

export default function EstadoCuentaPage() {
    const { user, loading: authLoading } = useAuth();

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

    const handlePrint = () => {
        if (!selectedId) return;
        const doc = new jsPDF();
        const title = viewMode === 'PENDING' ? "RELACIÓN DE COBRO (PENDIENTES)" : "ESTADO DE CUENTA (HISTÓRICO)";

        // Header
        doc.setFontSize(18);
        doc.text(title, 105, 20, { align: 'center' });

        doc.setFontSize(12);
        if (searchMode === 'UNIT') {
            doc.text(`Unidad: ${selectedItem?.codigo} - ${selectedItem?.propietario_nombre || ''}`, 14, 35);
        } else {
            doc.text(`Propietario: ${selectedItem?.razon_social || ''}`, 14, 35);
        }
        doc.text(`Fecha Impresión: ${new Date().toLocaleDateString()}`, 14, 42);

        // Resumen
        if (resumen) {
            doc.setFillColor(240, 240, 240);
            doc.rect(14, 48, 180, 15, 'F');
            doc.setFontSize(14);
            doc.text(`Total a Pagar: $${parseFloat(resumen.saldo_total || 0).toLocaleString()}`, 105, 58, { align: 'center' });
        }

        // Tabla
        let head = [];
        let body = [];
        let styles = {};

        if (viewMode === 'PENDING') {
            head = [['Fecha', 'Documento', 'Unidad', 'Total Doc', 'Saldo Pendiente']];
            body = pendientes.map(p => [
                new Date(p.fecha).toLocaleDateString(),
                p.numero, // Mostrar numero doc
                p.unidad_codigo || 'N/A',
                `$${parseFloat(p.valor_total).toLocaleString()}`,
                `$${parseFloat(p.saldo_pendiente).toLocaleString()}`
            ]);
            styles = { 4: { halign: 'right', fontStyle: 'bold' } };
        } else {
            head = [['Fecha', 'Doc', 'Detalle', 'Cargos', 'Pagos', 'Saldo']];
            body = historial.map(h => [
                new Date(h.fecha).toLocaleDateString(),
                h.documento,
                h.concepto,
                h.debito > 0 ? `$${parseFloat(h.debito).toLocaleString()}` : '-',
                h.credito > 0 ? `$${parseFloat(h.credito).toLocaleString()}` : '-',
                `$${parseFloat(h.saldo).toLocaleString()}`
            ]);
            styles = { 5: { halign: 'right', fontStyle: 'bold' } };
        }

        autoTable(doc, {
            startY: 70,
            head: head,
            body: body,
            theme: 'grid',
            headStyles: { fillColor: [63, 81, 181] },
            columnStyles: styles
        });

        doc.save(`EstadoCuenta_${searchMode}_${new Date().toISOString().slice(0, 10)}.pdf`);
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
                                <h1 className="text-3xl font-bold text-gray-800">Centro de Consulta PH</h1>
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
                            <FaBuilding /> Por Unidad Privada
                        </label>
                        <label className={`flex items-center gap-2 cursor-pointer px-4 py-2 rounded-lg transition-all ${searchMode === 'OWNER' ? 'bg-blue-100 text-blue-700 font-bold' : 'hover:bg-gray-100 text-gray-600'}`}>
                            <input type="radio" name="mode" className="hidden"
                                checked={searchMode === 'OWNER'} onChange={() => handleSearchModeChange('OWNER')} />
                            <FaUserTie /> Por Propietario (Agrupado)
                        </label>
                    </div>

                    {/* Autocomplete */}
                    <div className="relative">
                        <label className="block text-sm font-bold text-gray-700 mb-2">
                            {searchMode === 'UNIT' ? 'Buscar Inmueble (Apto, Casa, Local...)' : 'Buscar Propietario (Nombre, Razón Social)'}
                        </label>
                        {searchMode === 'UNIT' ? (
                            <AutocompleteInput
                                items={unidades}
                                value={selectedItem?.codigo || ''}
                                placeholder="Escriba código de unidad..."
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
                                value={selectedItem?.razon_social || ''}
                                placeholder="Escriba nombre del propietario..."
                                searchKey="razon_social" // La API retorna razon_social
                                displayKey="razon_social"
                                onChange={(val) => { // val es el objeto propietario: { tercero_id, razon_social, ... }
                                    // OJO: getPropietarios retorna lista resumen { tercero_id, ... }
                                    setSelectedItem(val);
                                    setSelectedId(val?.tercero_id);
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
                                    {searchMode === 'UNIT' ? `Unidad: ${selectedItem?.codigo}` : `Propietario: ${selectedItem?.razon_social}`}
                                </p>
                            </div>

                            {/* Selector de VISTA (Tabs) */}
                            <div className="flex bg-gray-700 p-1 rounded-lg">
                                <button
                                    onClick={() => setViewMode('PENDING')}
                                    className={`px-4 py-2 rounded-md font-medium text-sm transition-all flex items-center gap-2 ${viewMode === 'PENDING' ? 'bg-blue-600 text-white shadow' : 'text-gray-300 hover:text-white'}`}
                                >
                                    <FaFileInvoiceDollar /> Relación de Cobro
                                </button>
                                <button
                                    onClick={() => setViewMode('HISTORY')}
                                    className={`px-4 py-2 rounded-md font-medium text-sm transition-all flex items-center gap-2 ${viewMode === 'HISTORY' ? 'bg-blue-600 text-white shadow' : 'text-gray-300 hover:text-white'}`}
                                >
                                    <FaHistory /> Historial Detallado
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
                                                            <td className="px-6 py-4 text-gray-600 max-w-xs truncate" title={h.concepto}>{h.concepto}</td>
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
        </div>
    );
}
