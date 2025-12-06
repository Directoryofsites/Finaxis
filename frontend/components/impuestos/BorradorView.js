"use client";
import React, { useState, useEffect } from 'react';
import { FaSave, FaSync, FaCalculator } from 'react-icons/fa';
import { toast } from 'react-toastify';
import { getBalanceDePrueba } from '../../lib/reportesService';

export default function BorradorView({ impuesto }) {
    // Initial mock data structure
    const initialRows = [
        { r: 27, c: 'Ingresos Brutos', v: 0 },
        { r: 28, c: 'Devoluciones en ventas', v: 0 },
        { r: 29, c: 'Ingresos Netos', v: 0 }, // Calculated
        { r: 40, c: 'Compras de bienes gravados', v: 0 },
        { r: 57, c: 'Impuesto Generado', v: 0 },
        { r: 65, c: 'Impuesto Descontable', v: 0 },
        { r: 82, c: 'Saldo a Pagar', v: 0 }, // Calculated
    ];

    const [rows, setRows] = useState(initialRows);
    const [loading, setLoading] = useState(false);

    // Load from localStorage on mount
    useEffect(() => {
        if (typeof window !== 'undefined' && impuesto) {
            const saved = localStorage.getItem(`impuestos_borrador_${impuesto}`);
            if (saved) {
                setRows(JSON.parse(saved));
            }
        }
    }, [impuesto]);

    // Handle input changes
    const handleChange = (index, value) => {
        setRows(prev => prev.map((row, i) =>
            i === index ? { ...row, v: parseFloat(value) || 0 } : row
        ));
    };

    // Helper: Round to nearest 1000 (DIAN Rule)
    const roundToDian = (value) => {
        return Math.round(value / 1000) * 1000;
    };

    // Real data fetching from Accounting module
    const handleUpdate = async () => {
        setLoading(true);
        toast.info("Consultando contabilidad en tiempo real...");

        try {
            // 1. Read Mapping Rules
            const savedMapping = localStorage.getItem(`impuestos_mapping_${impuesto}`);
            let mapping = [];
            if (savedMapping) {
                mapping = JSON.parse(savedMapping);
            }

            // 2. Define Period (Default to current year for now, or read from Parametros)
            const currentYear = new Date().getFullYear();
            const fechaInicio = `${currentYear}-01-01`;
            const fechaFin = `${currentYear}-12-31`;

            // 3. Fetch Balance de Prueba
            const response = await getBalanceDePrueba({
                fecha_inicio: fechaInicio,
                fecha_fin: fechaFin,
                nivel_maximo: 6,
                filtro_cuentas: 'CON_SALDO_O_MOVIMIENTO'
            });

            const balanceData = response.data.filas || [];

            // 4. Process Data based on Mapping
            const newRows = rows.map(row => {
                const rule = mapping.find(m => m.r === row.r);

                if (rule && rule.cuentas && rule.cuentas.trim() !== '') {
                    const cuentasToSum = rule.cuentas.split(',').map(c => c.trim());
                    let totalValue = 0;

                    balanceData.forEach(account => {
                        const accountCode = account.codigo.trim();
                        const isRelevant = cuentasToSum.some(mappedCode => accountCode.startsWith(mappedCode));

                        if (isRelevant) {
                            if (cuentasToSum.includes(accountCode)) {
                                totalValue += parseFloat(account.nuevo_saldo) || 0;
                            }
                        }
                    });

                    if (totalValue === 0) {
                        balanceData.forEach(account => {
                            const accountCode = account.codigo.trim();
                            const isChild = cuentasToSum.some(mappedCode => accountCode.startsWith(mappedCode) && accountCode !== mappedCode);

                            if (isChild && account.nivel >= 4) {
                                if (account.nivel === 6) {
                                    totalValue += parseFloat(account.nuevo_saldo) || 0;
                                }
                            }
                        });
                    }

                    // Apply DIAN Rounding
                    return { ...row, v: roundToDian(Math.abs(totalValue)) };
                }
                return row;
            });

            setRows(newRows);
            toast.success("Datos actualizados y aproximados (DIAN).");

        } catch (error) {
            console.error("Error fetching balance:", error);
            toast.error("Error al consultar contabilidad.");
        } finally {
            setLoading(false);
        }
    };

    // Save to localStorage
    const handleSave = () => {
        try {
            localStorage.setItem(`impuestos_borrador_${impuesto}`, JSON.stringify(rows));
            toast.success(`Borrador de ${impuesto} guardado exitosamente.`);
        } catch (error) {
            console.error(error);
            toast.error("Error al guardar el borrador.");
        }
    };

    // Simple calculation logic
    const calculateTotals = () => {
        const newRows = [...rows];
        // Ingresos Netos = Brutos - Devoluciones
        newRows[2].v = roundToDian(newRows[0].v - newRows[1].v);

        // Saldo a Pagar = Generado - Descontable
        const generado = newRows[4].v;
        const descontable = newRows[5].v;
        const saldo = generado - descontable;

        // Note: The saldo itself is difference of rounded numbers, so it should be rounded, 
        // but good practice to ensure it.
        const saldoRounded = roundToDian(saldo);

        if (saldoRounded < 0) {
            newRows[6].c = 'Saldo a Favor';
            newRows[6].v = Math.abs(saldoRounded);
        } else {
            newRows[6].c = 'Saldo a Pagar';
            newRows[6].v = saldoRounded;
        }

        setRows(newRows);
        toast.info("Cálculos actualizados (Cifras DIAN).");
    };

    return (
        <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold text-gray-800">Borrador del Formulario - {impuesto}</h2>
                <div className="space-x-2">
                    <button
                        onClick={handleUpdate}
                        disabled={loading}
                        className={`bg-gray-100 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-200 flex items-center inline-flex ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                        <FaSync className={`mr-2 ${loading ? 'animate-spin' : ''}`} />
                        {loading ? 'Actualizando...' : 'Actualizar desde Contabilidad'}
                    </button>
                    <button
                        onClick={calculateTotals}
                        className="bg-yellow-500 text-white px-4 py-2 rounded-md hover:bg-yellow-600 flex items-center inline-flex"
                    >
                        <FaCalculator className="mr-2" /> Recalcular
                    </button>
                    <button
                        onClick={handleSave}
                        className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center inline-flex"
                    >
                        <FaSave className="mr-2" /> Guardar Borrador
                    </button>
                </div>
            </div>

            {/* Form Grid */}
            <div className="border border-gray-300 rounded-md p-4 bg-gray-50">
                <div className="grid grid-cols-12 gap-4 text-sm font-medium text-gray-700 border-b pb-2 mb-2">
                    <div className="col-span-1">Renglón</div>
                    <div className="col-span-8">Concepto</div>
                    <div className="col-span-3 text-right">Valor</div>
                </div>

                {/* Rows */}
                {rows.map((row, idx) => (
                    <div key={idx} className="grid grid-cols-12 gap-4 items-center mb-2">
                        <div className="col-span-1 bg-white border rounded px-2 py-1 text-center font-bold text-gray-600">{row.r}</div>
                        <div className="col-span-8">{row.c}</div>
                        <div className="col-span-3">
                            <input
                                type="number"
                                value={row.v}
                                onChange={(e) => handleChange(idx, e.target.value)}
                                className="w-full border rounded px-2 py-1 text-right focus:ring-blue-500 focus:border-blue-500 font-mono"
                            />
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
