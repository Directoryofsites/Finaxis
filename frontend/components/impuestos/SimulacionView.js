"use client";
import React, { useState, useEffect } from 'react';
import { FaPlus, FaPlay, FaTrash, FaSave } from 'react-icons/fa';
import { toast } from 'react-toastify';
import { apiService } from '../../lib/apiService';

export default function SimulacionView({ impuesto }) {
    const [escenarios, setEscenarios] = useState([]);
    const [activeScenario, setActiveScenario] = useState(null); // { id, nombre, rows: [] }
    const [config, setConfig] = useState([]);

    // Comparison State
    const [anio, setAnio] = useState(new Date().getFullYear());
    const [periodo, setPeriodo] = useState('01');
    const [realValues, setRealValues] = useState({}); // Map: { "27": 100000 }
    const [loadingReal, setLoadingReal] = useState(false);
    const [periodoConfig, setPeriodoConfig] = useState('Bimestral');

    // Load Period Config
    useEffect(() => {
        if (impuesto) {
            const savedPeriod = localStorage.getItem(`impuestos_periodicidad_${impuesto}`);
            if (savedPeriod) {
                setPeriodoConfig(savedPeriod);
            }
        }
    }, [impuesto]);

    // Load active configuration
    useEffect(() => {
        const loadConfig = async () => {
            if (!impuesto) return;
            try {
                const res = await apiService.get(`/impuestos/configuracion/${impuesto.toUpperCase()}`);
                if (res.data && res.data.length > 0) {
                    setConfig(res.data);
                }
            } catch (error) {
                console.error("Error loading config", error);
            }
        };
        loadConfig();
    }, [impuesto]);

    // Load scenarios from storage
    useEffect(() => {
        if (typeof window !== 'undefined' && impuesto) {
            const saved = localStorage.getItem(`impuestos_simulacion_${impuesto}`);
            if (saved) setEscenarios(JSON.parse(saved));
        }
    }, [impuesto]);

    // Save scenarios
    const saveToLocal = (updated) => {
        localStorage.setItem(`impuestos_simulacion_${impuesto}`, JSON.stringify(updated));
        setEscenarios(updated);
    };

    // Load Real Data for Comparison
    const loadRealData = async () => {
        if (!impuesto) return;
        setLoadingReal(true);
        try {
            const res = await apiService.get(`/impuestos/declaracion/${impuesto.toUpperCase()}`, {
                params: { anio, periodo }
            });
            if (res.data && res.data.renglones) {
                const map = {};
                res.data.renglones.forEach(r => map[r.r] = r.v);
                setRealValues(map);
                toast.success(`Datos reales cargados: ${anio} - P${periodo}`);
            }
        } catch (error) {
            console.error(error);
            toast.error("No se pudieron cargar datos reales.");
        } finally {
            setLoadingReal(false);
        }
    };

    const handleNew = () => {
        const initialRows = config.map(c => ({
            r: c.renglon,
            c: c.concepto,
            v: 0,
            cuentas: c.cuentas_ids || [],
            is_header: c.is_header
        }));

        const newScen = {
            id: Date.now(),
            nombre: 'Nuevo Escenario',
            rows: initialRows
        };
        setActiveScenario(newScen);
        // Automatically try to load real data if not loaded or empty?
        if (Object.keys(realValues).length === 0) loadRealData();
    };

    const handleLoad = (scen) => {
        // Merge with current config structure
        let mergedRows = config.map(c => {
            const existingRow = scen.rows.find(r => r.r === c.renglon);
            return {
                r: c.renglon,
                c: c.concepto,
                v: existingRow ? existingRow.v : 0,
                cuentas: c.cuentas_ids || [],
                is_header: c.is_header
            };
        });
        setActiveScenario({ ...scen, rows: mergedRows });
        if (Object.keys(realValues).length === 0) loadRealData();
    };

    const handleDelete = (id, e) => {
        e.stopPropagation();
        if (window.confirm("¿Eliminar este escenario?")) {
            const updated = escenarios.filter(s => s.id !== id);
            saveToLocal(updated);
            if (activeScenario && activeScenario.id === id) setActiveScenario(null);
        }
    };

    const handleSaveScenario = () => {
        if (!activeScenario) return;
        if (!activeScenario.nombre.trim()) {
            toast.warning("Asigne un nombre.");
            return;
        }
        const updatedList = [...escenarios];
        const idx = updatedList.findIndex(e => e.id === activeScenario.id);
        if (idx >= 0) updatedList[idx] = activeScenario;
        else updatedList.push(activeScenario);
        saveToLocal(updatedList);
        toast.success("Guardado.");
    };

    const calculateAll = (currentRows) => {
        let valuesMap = {};
        currentRows.forEach(row => valuesMap[row.r] = row.v);
        let updatedRows = [...currentRows];
        for (let pass = 0; pass < 3; pass++) {
            updatedRows = updatedRows.map(row => {
                if (row.is_header) return row;
                const cuentasList = row.cuentas;
                if (cuentasList && cuentasList.length === 1 && typeof cuentasList[0] === 'string') {
                    const formulaStr = cuentasList[0];
                    if (formulaStr.includes('[') || formulaStr.includes('+') || formulaStr.includes('-')) {
                        try {
                            let expr = formulaStr.replace(/\[(\w+)\]/g, (match, code) => valuesMap[code] !== undefined ? valuesMap[code] : 0);
                            expr = expr.replace(/max\(/g, 'Math.max(');
                            // eslint-disable-next-line no-new-func
                            const result = new Function('return ' + expr)();
                            row.v = result;
                            valuesMap[row.r] = result;
                        } catch (e) { }
                    }
                }
                return row;
            });
        }
        return updatedRows;
    };

    const handleValueChange = (index, value) => {
        if (!activeScenario) return;
        const rawValue = parseFloat(value.replace(/\./g, '')) || 0;
        let newRows = [...activeScenario.rows];
        newRows[index] = { ...newRows[index], v: rawValue };
        newRows = calculateAll(newRows);
        setActiveScenario({ ...activeScenario, rows: newRows });
    };

    const fmt = (val) => new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 }).format(val);

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center bg-white p-4 rounded-lg shadow-sm">
                <div>
                    <h2 className="text-xl font-semibold text-gray-800">Simulador de {impuesto}</h2>
                    <p className="text-gray-500 text-sm">Compare datos reales vs simulados.</p>
                </div>
                <div className="flex space-x-2">
                    <button onClick={handleNew} className="bg-blue-600 text-white px-4 py-2 rounded flex items-center hover:bg-blue-700">
                        <FaPlus className="mr-2" /> Nuevo
                    </button>
                    {activeScenario && (
                        <button onClick={handleSaveScenario} className="bg-green-600 text-white px-4 py-2 rounded flex items-center hover:bg-green-700">
                            <FaSave className="mr-2" /> Guardar
                        </button>
                    )}
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {/* Sidebar */}
                <div className="md:col-span-1 space-y-3">
                    <h3 className="font-semibold text-gray-700">Escenarios</h3>
                    {escenarios.length === 0 && <p className="text-gray-400 text-sm italic">Sin escenarios.</p>}
                    {escenarios.map(scen => (
                        <div
                            key={scen.id}
                            onClick={() => handleLoad(scen)}
                            className={`p-3 rounded border cursor-pointer hover:bg-gray-50 relative group ${activeScenario && activeScenario.id === scen.id ? 'border-blue-500 bg-blue-50 ring-1 ring-blue-500' : 'border-gray-200'}`}
                        >
                            <div className="flex justify-between">
                                <span className="font-medium text-gray-800 truncate">{scen.nombre}</span>
                                <button onClick={(e) => handleDelete(scen.id, e)} className="text-red-400 hover:text-red-600 opacity-0 group-hover:opacity-100">
                                    <FaTrash />
                                </button>
                            </div>
                            <span className="text-xs text-gray-500">{new Date(scen.id).toLocaleDateString()}</span>
                        </div>
                    ))}
                </div>

                {/* Main Table */}
                <div className="md:col-span-3 bg-white rounded-lg shadow-md p-6">
                    {!activeScenario ? (
                        <div className="text-center py-20 text-gray-400">Seleccione o cree un escenario.</div>
                    ) : (
                        <div>
                            <div className="flex flex-wrap gap-4 mb-4 items-end bg-gray-50 p-3 rounded">
                                <div className="flex-1">
                                    <label className="block text-sm font-medium text-gray-700">Nombre Escenario</label>
                                    <input
                                        type="text"
                                        value={activeScenario.nombre}
                                        onChange={(e) => setActiveScenario({ ...activeScenario, nombre: e.target.value })}
                                        className="mt-1 w-full border rounded px-2 py-1 focus:ring-blue-500"
                                    />
                                </div>
                                <div className="w-24">
                                    <label className="block text-sm font-medium text-gray-700">Año</label>
                                    <input type="number" value={anio} onChange={(e) => setAnio(e.target.value)} className="mt-1 w-full border rounded px-2 py-1" />
                                </div>
                                <div className="w-32">
                                    <label className="block text-sm font-medium text-gray-700">Periodo</label>
                                    <select value={periodo} onChange={(e) => setPeriodo(e.target.value)} className="mt-1 w-full border rounded px-2 py-1">
                                        {periodoConfig === 'Mensual' ? (
                                            <>
                                                <option value="01">01. Ene</option>
                                                <option value="02">02. Feb</option>
                                                <option value="03">03. Mar</option>
                                                <option value="04">04. Abr</option>
                                                <option value="05">05. May</option>
                                                <option value="06">06. Jun</option>
                                                <option value="07">07. Jul</option>
                                                <option value="08">08. Ago</option>
                                                <option value="09">09. Sep</option>
                                                <option value="10">10. Oct</option>
                                                <option value="11">11. Nov</option>
                                                <option value="12">12. Dic</option>
                                            </>
                                        ) : (
                                            <>
                                                <option value="01">01. Ene-Feb</option>
                                                <option value="02">02. Mar-Abr</option>
                                                <option value="03">03. May-Jun</option>
                                                <option value="04">04. Jul-Ago</option>
                                                <option value="05">05. Sep-Oct</option>
                                                <option value="06">06. Nov-Dic</option>
                                            </>
                                        )}
                                    </select>
                                </div>
                                <button onClick={loadRealData} className="bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 text-sm h-9 flex items-center">
                                    {loadingReal ? '...' : <FaPlay className="mr-1" />} <span className="text-xs">Traer Real</span>
                                </button>
                            </div>

                            <div className="border border-gray-200 rounded overflow-hidden">
                                <table className="min-w-full divide-y divide-gray-200 text-sm">
                                    <thead className="bg-gray-100">
                                        <tr>
                                            <th className="px-3 py-2 text-left w-12 text-gray-600">No.</th>
                                            <th className="px-3 py-2 text-left text-gray-600">Concepto</th>
                                            <th className="px-3 py-2 text-right w-32 text-blue-800 bg-blue-50">Real</th>
                                            <th className="px-3 py-2 text-right w-32 text-green-800 bg-green-50">Simulado</th>
                                            <th className="px-3 py-2 text-right w-32 text-gray-600">Variación</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-200 bg-white">
                                        {activeScenario.rows.map((row, idx) => {
                                            if (row.is_header) {
                                                return (
                                                    <tr key={idx} className="bg-gray-50 border-t-2 border-gray-100">
                                                        <td colSpan="5" className="px-4 py-3 font-bold text-gray-800 uppercase text-xs tracking-wider">
                                                            {row.c}
                                                        </td>
                                                    </tr>
                                                );
                                            }

                                            const isFormula = row.cuentas && row.cuentas.length === 1 && typeof row.cuentas[0] === 'string' && (row.cuentas[0].includes('[') || row.cuentas[0].includes('+'));
                                            const realVal = realValues[row.r] || 0;
                                            const diff = row.v - realVal;

                                            return (
                                                <tr key={idx} className="hover:bg-gray-50">
                                                    <td className="px-3 py-1 text-center text-gray-500 font-mono text-xs">{row.r}</td>
                                                    <td className="px-3 py-1 text-gray-800">{row.c}</td>
                                                    {/* Real */}
                                                    <td className="px-3 py-1 text-right font-mono text-gray-600 bg-blue-50 bg-opacity-30">
                                                        {fmt(realVal)}
                                                    </td>
                                                    {/* Simulado Input */}
                                                    <td className="px-3 py-1 text-right bg-green-50 bg-opacity-30">
                                                        <input
                                                            type="text"
                                                            value={row.v ? fmt(row.v) : '0'} // Format on display
                                                            disabled={isFormula}
                                                            onFocus={(e) => e.target.select()} // Auto-select on click
                                                            onChange={(e) => handleValueChange(idx, e.target.value)}
                                                            className={`w-full text-right border-0 bg-transparent focus:ring-0 p-0 font-mono ${isFormula ? 'font-bold text-gray-800' : 'text-green-700 font-bold'}`}
                                                        />
                                                    </td>
                                                    {/* Diferencia */}
                                                    <td className={`px-3 py-1 text-right font-mono font-medium ${diff > 0 ? 'text-green-600' : diff < 0 ? 'text-red-500' : 'text-gray-400'}`}>
                                                        {diff !== 0 ? (diff > 0 ? '+' : '') + fmt(diff) : '-'}
                                                    </td>
                                                </tr>
                                            )
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
