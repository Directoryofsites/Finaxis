import React, { useState, useEffect } from 'react';
import { FaSave, FaSync, FaCalculator } from 'react-icons/fa';
import { toast } from 'react-toastify';
import { apiService } from '../../lib/apiService';

export default function BorradorView({ impuesto }) {
    const [rows, setRows] = useState([]);
    const [loading, setLoading] = useState(false);
    const [periodo, setPeriodo] = useState('01'); // Default Period
    const [anio, setAnio] = useState(new Date().getFullYear());

    // Load structure from Backend Config on "Update"
    const handleUpdate = async () => {
        setLoading(true);
        toast.info(`Calculando borrador de ${impuesto}...`);

        try {
            // Call the calculation endpoint directly
            const response = await apiService.get(`/impuestos/declaracion/${impuesto.toUpperCase()}`, {
                params: {
                    anio: anio,
                    periodo: periodo
                }
            });

            // Backend returns { renglones: [ {r, c, v, is_header}, ... ] }
            if (response.data && response.data.renglones) {
                setRows(response.data.renglones);
                toast.success("Borrador calculado exitosamente.");
            } else {
                toast.warning("No se recibieron datos del servidor.");
            }

        } catch (error) {
            console.error("Error calculating draft:", error);
            toast.error(error.response?.data?.detail || "Error al calcular el borrador.");
        } finally {
            setLoading(false);
        }
    };

    // Save locally (Optional, maybe sends to backend later?)
    const handleSave = () => {
        if (rows.length === 0) return;
        localStorage.setItem(`impuestos_borrador_${impuesto}`, JSON.stringify(rows));
        toast.success("Borrador guardado localmente.");
    };

    // Load locally saved draft on mount
    useEffect(() => {
        const saved = localStorage.getItem(`impuestos_borrador_${impuesto}`);
        if (saved) {
            try {
                setRows(JSON.parse(saved));
            } catch (e) { console.error("Error loading saved draft", e); }
        }
    }, [impuesto]);

    return (
        <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
                <div>
                    <h2 className="text-xl font-semibold text-gray-800">Borrador - {impuesto}</h2>
                    <p className="text-gray-500 text-sm">Simulación basada en la configuración actual.</p>
                </div>

                <div className="flex flex-wrap gap-2 items-center">
                    {/* Period Selector Simplificado */}
                    <select
                        value={periodo}
                        onChange={(e) => setPeriodo(e.target.value)}
                        className="border rounded-md px-3 py-2 text-sm bg-gray-50"
                    >
                        {impuesto === 'renta' ? (
                            <option value="00">Anual</option>
                        ) : (
                            <>
                                <option value="01">Enero / Bim 1</option>
                                <option value="02">Febrero / Bim 2</option>
                                <option value="03">Marzo / Bim 3</option>
                                <option value="04">Abril / Bim 4</option>
                                <option value="05">Mayo / Bim 5</option>
                                <option value="06">Junio / Bim 6</option>
                                {/* Add more if needed */}
                            </>
                        )}
                    </select>

                    <input
                        type="number"
                        value={anio}
                        onChange={(e) => setAnio(e.target.value)}
                        className="border rounded-md px-3 py-2 text-sm w-20 bg-gray-50"
                    />

                    <button
                        onClick={handleUpdate}
                        disabled={loading}
                        className={`bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 flex items-center shadow-sm ${loading ? 'opacity-50' : ''}`}
                    >
                        <FaSync className={`mr-2 ${loading ? 'animate-spin' : ''}`} />
                        {loading ? 'Calculando...' : 'Calcular'}
                    </button>

                    <button
                        onClick={handleSave}
                        className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 flex items-center shadow-sm"
                    >
                        <FaSave className="mr-2" /> Guardar
                    </button>
                </div>
            </div>

            {/* Table */}
            <div className="border border-gray-200 rounded-lg overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase">Renglón</th>
                            <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase">Concepto</th>
                            <th className="px-4 py-3 text-right text-xs font-bold text-gray-500 uppercase">Valor</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {rows.length === 0 ? (
                            <tr>
                                <td colSpan="3" className="px-6 py-8 text-center text-gray-500">
                                    No hay datos calculados. Presione "Calcular" para generar el borrador.
                                </td>
                            </tr>
                        ) : (
                            rows.map((row, idx) => {
                                if (row.is_header) {
                                    return (
                                        <tr key={idx} className="bg-gray-100">
                                            <td colSpan="3" className="px-4 py-2 font-bold text-gray-800 uppercase text-xs tracking-wider">
                                                {row.c}
                                            </td>
                                        </tr>
                                    );
                                }
                                return (
                                    <tr key={idx} className="hover:bg-gray-50 transition-colors">
                                        <td className="px-4 py-2 text-center font-mono text-sm font-bold text-gray-600 w-16">
                                            {row.r}
                                        </td>
                                        <td className="px-4 py-2 text-sm text-gray-800">
                                            {row.c}
                                        </td>
                                        <td className="px-4 py-2 text-right font-mono text-sm font-medium text-gray-900">
                                            {new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(row.v)}
                                        </td>
                                    </tr>
                                );
                            })
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
