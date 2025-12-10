"use client";
import React, { useState, useEffect } from 'react';
import { getEmpleados, previewLiquidacion, guardarLiquidacion } from '../../../lib/nominaService';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { FaCalculator, FaMoneyBillWave } from 'react-icons/fa';

export default function LiquidadorPage() {
    const [empleados, setEmpleados] = useState([]);
    const [selectedEmp, setSelectedEmp] = useState('');
    const [anio, setAnio] = useState(new Date().getFullYear());
    const [mes, setMes] = useState(new Date().getMonth() + 1);
    const [dias, setDias] = useState(30);
    const [extras, setExtras] = useState(0);
    const [comisiones, setComisiones] = useState(0);
    const [resultado, setResultado] = useState(null);
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        getEmpleados().then(setEmpleados).catch(err => toast.error("Error cargando empleados"));
    }, []);

    const handleLiquidar = async (e) => {
        e.preventDefault();
        if (!selectedEmp) return toast.warning("Seleccione un empleado");

        setLoading(true);
        try {
            const res = await previewLiquidacion(selectedEmp, dias, extras, comisiones);
            setResultado(res);
            toast.info("Simulación actualizada");
        } catch (error) {
            toast.error("Error al calcular: " + (error.response?.data?.detail || error.message));
            console.error("Error liquidando:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleGuardar = async () => {
        if (!selectedEmp || !resultado) return;
        setSaving(true);
        try {
            await previewLiquidacion(selectedEmp, dias, extras, comisiones); // Recalcular seguro
            const res = await guardarLiquidacion({
                empleado_id: selectedEmp,
                anio: anio,
                mes: mes,
                dias_trabajados: dias,
                horas_extras: extras,
                comisiones: comisiones
            });
            toast.success("Liquidación Guardada y Contabilizada");
            setResultado(null); // Limpiar
            setSelectedEmp('');
        } catch (error) {
            toast.error("Error al guardar liquidación");
        } finally {
            setSaving(false);
        }
    };

    const formatMoney = (val) => new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(val);

    return (
        <div className="p-8 max-w-6xl mx-auto">
            <ToastContainer />
            <h1 className="text-2xl font-light text-gray-800 mb-6 flex items-center">
                <FaCalculator className="mr-3 text-green-600" /> Liquidador de Nómina y Contabilización
            </h1>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {/* Formulario */}
                <div className="md:col-span-1 bg-white p-6 rounded shadow-lg h-fit border-t-4 border-green-500">
                    <form onSubmit={handleLiquidar} className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-bold text-gray-700 mb-1">Año</label>
                                <input type="number" className="w-full border p-2 rounded" value={anio} onChange={e => setAnio(e.target.value)} />
                            </div>
                            <div>
                                <label className="block text-sm font-bold text-gray-700 mb-1">Mes</label>
                                <select className="w-full border p-2 rounded" value={mes} onChange={e => setMes(e.target.value)}>
                                    {[...Array(12).keys()].map(m => <option key={m + 1} value={m + 1}>{m + 1}</option>)}
                                </select>
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-bold text-gray-700 mb-1">Empleado</label>
                            <select className="w-full border p-2 rounded" value={selectedEmp} onChange={e => setSelectedEmp(e.target.value)} required>
                                <option value="">-- Seleccionar --</option>
                                {empleados.map(emp => (
                                    <option key={emp.id} value={emp.id}>{emp.nombres} {emp.apellidos}</option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-bold text-gray-700 mb-1">Días Trabajados</label>
                            <input type="number" className="w-full border p-2 rounded" value={dias} onChange={e => setDias(e.target.value)} min="1" max="30" required />
                        </div>
                        <div>
                            <label className="block text-sm font-bold text-gray-700 mb-1">Horas Extras ($)</label>
                            <input type="number" className="w-full border p-2 rounded" value={extras} onChange={e => setExtras(e.target.value)} />
                        </div>
                        <div>
                            <label className="block text-sm font-bold text-gray-700 mb-1">Comisiones ($)</label>
                            <input type="number" className="w-full border p-2 rounded" value={comisiones} onChange={e => setComisiones(e.target.value)} />
                        </div>
                        <button type="submit" className="w-full bg-blue-600 text-white font-bold py-2 rounded hover:bg-blue-700 transition" disabled={loading}>
                            {loading ? 'Calculando...' : '1. Simular / Previsualizar'}
                        </button>
                    </form>
                </div>

                {/* Resultados */}
                <div className="md:col-span-2">
                    {resultado ? (
                        <div className="bg-white p-0 rounded shadow-lg overflow-hidden animate-fadeIn">
                            <div className="bg-gray-800 text-white p-4 flex justify-between items-center">
                                <div>
                                    <h3 className="text-lg font-light">Desprendible Preliminar</h3>
                                    <p className="font-bold text-xl">{resultado.empleado}</p>
                                </div>
                                <div className="text-right text-xs opacity-70">
                                    Periodo: {anio}-{mes}
                                </div>
                            </div>
                            <div className="p-6 grid grid-cols-2 gap-x-8 gap-y-4 text-sm">

                                {/* Devengados */}
                                <div>
                                    <h4 className="font-bold text-green-700 border-b border-green-200 pb-1 mb-2">Devengados (Ingresos)</h4>
                                    <div className="flex justify-between py-1"><span>Sueldo Básico</span> <span>{formatMoney(resultado.detalle.sueldo_basico_periodo)}</span></div>
                                    <div className="flex justify-between py-1"><span>Auxilio Transporte</span> <span>{formatMoney(resultado.detalle.auxilio_transporte)}</span></div>
                                    <div className="flex justify-between py-1"><span>Horas Extras</span> <span>{formatMoney(resultado.detalle.horas_extras)}</span></div>
                                    <div className="flex justify-between py-1"><span>Comisiones</span> <span>{formatMoney(resultado.detalle.comisiones)}</span></div>
                                    <div className="flex justify-between font-bold pt-2 border-t mt-2"><span>Total Devengado</span> <span>{formatMoney(resultado.detalle.total_devengado)}</span></div>
                                </div>

                                {/* Deducciones */}
                                <div>
                                    <h4 className="font-bold text-red-700 border-b border-red-200 pb-1 mb-2">Deducciones (Ley)</h4>
                                    <div className="flex justify-between py-1"><span>Salud (4%)</span> <span>{formatMoney(resultado.detalle.salud)}</span></div>
                                    <div className="flex justify-between py-1"><span>Pensión (4%)</span> <span>{formatMoney(resultado.detalle.pension)}</span></div>
                                    <div className="flex justify-between py-1"><span>Fondo Solidaridad</span> <span>{formatMoney(resultado.detalle.fsp)}</span></div>
                                    <div className="flex justify-between font-bold pt-2 border-t mt-2"><span>Total Deducciones</span> <span>{formatMoney(resultado.detalle.total_deducciones)}</span></div>
                                </div>
                            </div>

                            <div className="bg-gray-50 p-6 flex justify-between items-center bg-green-50 border-t border-green-100">
                                <span className="text-xl font-light text-gray-700">Neto a Pagar</span>
                                <span className="text-3xl font-bold text-green-700">{formatMoney(resultado.detalle.neto_pagar)}</span>
                            </div>

                            <div className="p-4 bg-gray-100 border-t flex justify-end">
                                <button
                                    onClick={handleGuardar}
                                    disabled={saving}
                                    className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded shadow-lg flex items-center transition transform hover:scale-105"
                                >
                                    <FaMoneyBillWave className="mr-2" />
                                    {saving ? 'Procesando...' : '2. Guardar y Contabilizar Definitivo'}
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className="h-full flex flex-col items-center justify-center text-gray-400 border-2 border-dashed border-gray-200 rounded p-12">
                            <FaMoneyBillWave size={48} className="mb-4 text-gray-300" />
                            <p>Seleccione un empleado y haga clic en Simular Pago para ver el desprendible.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
