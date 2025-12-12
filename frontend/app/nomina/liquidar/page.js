"use client";
import React, { useState, useEffect } from 'react';
import { getEmpleados, previewLiquidacion, guardarLiquidacion, getTiposNomina, downloadResumenNomina } from '../../../lib/nominaService';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { FaCalculator, FaMoneyBillWave, FaFilter, FaCheckSquare, FaSquare, FaSave, FaPlay, FaFilePdf } from 'react-icons/fa';

export default function LiquidadorPage() {
    // 1. Configuración Inicial
    const [tiposNomina, setTiposNomina] = useState([]);
    const [selectedTipo, setSelectedTipo] = useState('');
    const [anio, setAnio] = useState(new Date().getFullYear());
    const [mes, setMes] = useState(new Date().getMonth() + 1);

    // 2. Data Grid State
    // Format: { ...empleadoData, dias: 30, extras: 0, comisiones: 0, selected: false, status: 'PENDIENTE', liquidacion: null }
    const [rows, setRows] = useState([]);
    const [loading, setLoading] = useState(false);
    const [processing, setProcessing] = useState(false); // For bulk actions
    const [downloading, setDownloading] = useState(false);

    // 3. Load Tipos
    useEffect(() => {
        getTiposNomina()
            .then(setTiposNomina)
            .catch(err => toast.error("Error cargando tipos de nómina"));
    }, []);

    // 4. Load Employees & Build Grid
    useEffect(() => {
        if (selectedTipo) {
            setLoading(true);
            getEmpleados({ tipo_nomina_id: selectedTipo })
                .then(data => {
                    const initialRows = data.map(emp => ({
                        ...emp,
                        dias: 30,
                        extras: 0,
                        comisiones: 0,
                        selected: true, // Select all by default for convenience
                        status: 'PENDIENTE', // PENDIENTE | CALCULADO | GUARDADO | ERROR
                        liquidacion: null,
                        errorMsg: ''
                    }));
                    setRows(initialRows);
                })
                .catch(err => toast.error("Error cargando empleados"))
                .finally(() => setLoading(false));
        } else {
            setRows([]);
        }
    }, [selectedTipo]);

    // --- GRID HANDLERS ---

    const handleRowChange = (id, field, value) => {
        setRows(prev => prev.map(row =>
            row.id === id ? { ...row, [field]: value, status: 'PENDIENTE' } : row
        ));
    };

    const toggleSelect = (id) => {
        setRows(prev => prev.map(row =>
            row.id === id ? { ...row, selected: !row.selected } : row
        ));
    };

    const toggleSelectAll = (e) => {
        const checked = e.target.checked;
        setRows(prev => prev.map(row => ({ ...row, selected: checked })));
    };

    // --- BULK ACTIONS ---

    const simulateSelected = async () => {
        const toSimulate = rows.filter(r => r.selected);
        if (toSimulate.length === 0) return toast.warning("Seleccione empleados para simular.");

        setProcessing(true);
        let updatedRows = [...rows];
        let successCount = 0;

        // Process in parallel requests (could limit concurrency if list is huge)
        const promises = toSimulate.map(async (row) => {
            try {
                const res = await previewLiquidacion(row.id, row.dias, row.extras, row.comisiones);
                const idx = updatedRows.findIndex(r => r.id === row.id);
                if (idx !== -1) {
                    updatedRows[idx] = {
                        ...updatedRows[idx],
                        liquidacion: res,
                        status: 'CALCULADO',
                        errorMsg: ''
                    };
                    successCount++;
                }
            } catch (error) {
                const idx = updatedRows.findIndex(r => r.id === row.id);
                if (idx !== -1) {
                    updatedRows[idx] = {
                        ...updatedRows[idx],
                        status: 'ERROR',
                        errorMsg: error.response?.data?.detail || error.message
                    };
                }
            }
        });

        await Promise.all(promises);
        setRows(updatedRows);
        setProcessing(false);
        if (successCount > 0) toast.info(`${successCount} empleados simulados correctamente.`);
    };

    const saveSelected = async () => {
        // Only save rows that are selected AND have been calculated ('CALCULADO' or 'GUARDADO' to prevent re-save logic if needed, but here we enforce CALCULADO)
        const toSave = rows.filter(r => r.selected && r.status === 'CALCULADO');

        if (toSave.length === 0) {
            const hasPending = rows.some(r => r.selected && r.status === 'PENDIENTE');
            if (hasPending) return toast.warning("Primero debe SIMULAR los empleados seleccionados.");
            return toast.warning("No hay empleados calculados listos para guardar.");
        }

        setProcessing(true);
        let updatedRows = [...rows];
        let successCount = 0;

        const promises = toSave.map(async (row) => {
            try {
                await guardarLiquidacion({
                    empleado_id: row.id,
                    anio: anio,
                    mes: mes,
                    dias_trabajados: row.dias,
                    horas_extras: row.extras,
                    comisiones: row.comisiones
                });

                const idx = updatedRows.findIndex(r => r.id === row.id);
                if (idx !== -1) {
                    updatedRows[idx] = {
                        ...updatedRows[idx],
                        status: 'GUARDADO',
                        errorMsg: ''
                    };
                    successCount++;
                }
            } catch (error) {
                const idx = updatedRows.findIndex(r => r.id === row.id);
                if (idx !== -1) {
                    updatedRows[idx] = {
                        ...updatedRows[idx],
                        status: 'ERROR',
                        errorMsg: error.response?.data?.detail || 'Error guardando'
                    };
                    // Mostrar error específico si es el candado
                    if (error.response?.data?.detail) {
                        toast.error(`${row.nombres}: ${error.response.data.detail}`);
                    }
                }
            }
        });

        await Promise.all(promises);
        setRows(updatedRows);
        setProcessing(false);
        if (successCount > 0) toast.success(`${successCount} liquidaciones guardadas!`);
    };

    const handleDownloadReport = async () => {
        if (!selectedTipo) return toast.warning("Seleccione una nómina.");
        setDownloading(true);
        try {
            await downloadResumenNomina(anio, mes, selectedTipo);
            toast.success("Informe generado correctamente.");
        } catch (error) {
            console.error(error);
            toast.error("Error generando informe. Verifique que existan empleados liquidados.");
        } finally {
            setDownloading(false);
        }
    };

    // Stats
    const totalNeto = rows
        .filter(r => r.liquidacion?.detalle?.neto_pagar)
        .reduce((sum, r) => sum + r.liquidacion.detalle.neto_pagar, 0);

    const formatMoney = (val) => new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(val);

    return (
        <div className="p-4 md:p-8 max-w-7xl mx-auto">
            <ToastContainer />
            <h1 className="text-2xl font-light text-gray-800 mb-6 flex items-center">
                <FaCalculator className="mr-3 text-green-600" /> Liquidación Masiva de Nómina
            </h1>

            {/* CONTROLES SUPERIORES */}
            <div className="bg-white p-4 rounded shadow mb-6 border border-gray-200 grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                <div>
                    <label className="block text-xs font-bold text-gray-500 mb-1">Tipo de Nómina</label>
                    <select
                        className="border rounded p-2 text-sm w-full"
                        value={selectedTipo}
                        onChange={e => setSelectedTipo(e.target.value)}
                    >
                        <option value="">-- Seleccione --</option>
                        {tiposNomina.map(tipo => (
                            <option key={tipo.id} value={tipo.id}>{tipo.nombre} ({tipo.periodo_pago})</option>
                        ))}
                    </select>
                </div>
                <div>
                    <label className="block text-xs font-bold text-gray-500 mb-1">Año</label>
                    <input type="number" className="w-full border p-2 rounded text-sm" value={anio} onChange={e => setAnio(e.target.value)} />
                </div>
                <div>
                    <label className="block text-xs font-bold text-gray-500 mb-1">Mes</label>
                    <select className="w-full border p-2 rounded text-sm" value={mes} onChange={e => setMes(e.target.value)}>
                        {[...Array(12).keys()].map(m => <option key={m + 1} value={m + 1}>{m + 1}</option>)}
                    </select>
                </div>
                <div className="text-right">
                    <div className="text-xs text-gray-500">Total a Pagar (Simulado)</div>
                    <div className="text-xl font-bold text-green-700">{formatMoney(totalNeto)}</div>
                </div>
            </div>

            {selectedTipo && (
                <div className="bg-white rounded shadow text-sm overflow-hidden animate-fadeIn">
                    {/* TOOLBAR */}
                    <div className="p-3 bg-gray-50 border-b flex justify-between items-center">
                        <div className="flex gap-2">
                            <button
                                onClick={simulateSelected}
                                disabled={processing}
                                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded shadow flex items-center"
                            >
                                <FaPlay className="mr-2" size={12} /> Simular Seleccionados
                            </button>
                            <button
                                onClick={saveSelected}
                                disabled={processing}
                                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded shadow flex items-center"
                            >
                                <FaSave className="mr-2" size={12} /> Guardar Definitivo
                            </button>
                            <button
                                onClick={handleDownloadReport}
                                disabled={processing || downloading}
                                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded shadow flex items-center ml-2"
                                title="Ver Informe PDF de la Nómina Liquidada"
                            >
                                {downloading ? 'Generando...' : <><FaFilePdf className="mr-2" size={12} /> Ver Informe</>}
                            </button>
                        </div>
                        <div className="text-xs text-gray-400">
                            {rows.filter(r => r.selected).length} empleados seleccionados
                        </div>
                    </div>

                    {/* TABLE */}
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="bg-gray-100 text-left text-gray-600">
                                    <th className="p-3 w-10 text-center">
                                        <input type="checkbox" onChange={toggleSelectAll} checked={rows.length > 0 && rows.every(r => r.selected)} />
                                    </th>
                                    <th className="p-3">Empleado</th>
                                    <th className="p-3 w-24">Días</th>
                                    <th className="p-3 w-32">Hrs Extras ($)</th>
                                    <th className="p-3 w-32">Comisiones ($)</th>
                                    <th className="p-3 w-32">Neto Pagar</th>
                                    <th className="p-3 w-28">Estado</th>
                                </tr>
                            </thead>
                            <tbody>
                                {rows.map(row => (
                                    <tr key={row.id} className={`border-b hover:bg-gray-50 ${!row.selected ? 'opacity-50 bg-gray-50' : ''}`}>
                                        <td className="p-3 text-center">
                                            <input
                                                type="checkbox"
                                                checked={row.selected}
                                                onChange={() => toggleSelect(row.id)}
                                            />
                                        </td>
                                        <td className="p-3">
                                            <div className="font-bold">{row.nombres} {row.apellidos}</div>
                                            <div className="text-xs text-gray-400">{row.numero_documento}</div>
                                            {row.errorMsg && <div className="text-xs text-red-500 mt-1">{row.errorMsg}</div>}
                                        </td>
                                        <td className="p-3">
                                            <input
                                                type="number"
                                                className="w-full border rounded p-1 text-center"
                                                value={row.dias}
                                                onChange={(e) => handleRowChange(row.id, 'dias', parseInt(e.target.value) || 0)}
                                                min="0" max="30"
                                            />
                                        </td>
                                        <td className="p-3">
                                            <input
                                                type="number"
                                                className="w-full border rounded p-1 text-right"
                                                value={row.extras}
                                                onChange={(e) => handleRowChange(row.id, 'extras', parseInt(e.target.value) || 0)}
                                            />
                                        </td>
                                        <td className="p-3">
                                            <input
                                                type="number"
                                                className="w-full border rounded p-1 text-right"
                                                value={row.comisiones}
                                                onChange={(e) => handleRowChange(row.id, 'comisiones', parseInt(e.target.value) || 0)}
                                            />
                                        </td>
                                        <td className="p-3 font-bold text-green-700 text-right">
                                            {row.liquidacion ? formatMoney(row.liquidacion.detalle.neto_pagar) : '-'}
                                        </td>
                                        <td className="p-3 text-center">
                                            <StatusBadge status={row.status} />
                                        </td>
                                    </tr>
                                ))}
                                {rows.length === 0 && !loading && (
                                    <tr>
                                        <td colSpan="7" className="p-8 text-center text-gray-400">
                                            No se encontraron empleados para este filtro.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
}

function StatusBadge({ status }) {
    switch (status) {
        case 'PENDIENTE':
            return <span className="bg-gray-100 text-gray-600 px-2 py-1 rounded text-xs font-bold">Pendiente</span>;
        case 'CALCULADO':
            return <span className="bg-blue-100 text-blue-600 px-2 py-1 rounded text-xs font-bold">Simulado</span>;
        case 'GUARDADO':
            return <span className="bg-green-100 text-green-600 px-2 py-1 rounded text-xs font-bold">Guardado</span>;
        case 'ERROR':
            return <span className="bg-red-100 text-red-600 px-2 py-1 rounded text-xs font-bold">Error</span>;
        default:
            return null;
    }
}
