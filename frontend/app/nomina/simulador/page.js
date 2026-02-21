"use client";
import React, { useState, useEffect } from 'react';
import { FaCog, FaCheckCircle, FaTimesCircle, FaCalculator, FaInfoCircle, FaBriefcase, FaUserTie, FaBuilding } from 'react-icons/fa';

export default function SimuladorLaboral() {
    // --- SECCIÓN 1: CONFIGURACIÓN DE PARÁMETROS ---
    const [configOpen, setConfigOpen] = useState(false);

    // Parámetros por defecto
    const [smmlv, setSmmlv] = useState(1750905);
    const [auxTransporte, setAuxTransporte] = useState(249095);
    const [pArl, setPArl] = useState(0.522);
    const [pCaja, setPCaja] = useState(4);
    const [pSena, setPSena] = useState(2);
    const [pIcbf, setPIcbf] = useState(3);

    // --- SECCIÓN 2: ESTADOS DEL IBC (SINCRONIZADOS) ---
    const [factorStr, setFactorStr] = useState("1.00");
    const [pesosStr, setPesosStr] = useState("1750905");

    // Sincronización Mínima: Si se edita en Pesos
    const handlePesosChange = (e) => {
        let val = e.target.value.replace(/\D/g, ''); // Solo números
        if (!val) val = "0";
        setPesosStr(val);

        const numPesos = parseInt(val, 10);
        if (smmlv > 0) {
            const computedFactor = (numPesos / smmlv).toFixed(2);
            setFactorStr(computedFactor);
        }
    };

    // Sincronización Mínima: Si se edita en Factor
    const handleFactorChange = (e) => {
        let val = e.target.value.replace(',', '.'); // Permite coma o punto
        // Permitimos escribir decimales o dejar a medias ej: "1."
        if (/[^0-9.]/.test(val)) return; // Bloquear no numéricos salvo punto
        setFactorStr(val);

        const numFactor = parseFloat(val);
        if (!isNaN(numFactor)) {
            const computedPesos = Math.round(numFactor * smmlv);
            setPesosStr(computedPesos.toString());
        }
    };

    // Helpers de Formato
    const formatCurrency = (val) => {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            maximumFractionDigits: 0
        }).format(val);
    };

    const formatInputPesos = (val) => {
        if (!val) return "";
        return new Intl.NumberFormat('es-CO').format(val);
    };

    // --- MOTOR DE CÁLCULO ---
    const ibc = parseInt(pesosStr, 10) || 0;
    const factorAplicado = parseFloat(factorStr) || 0;
    const ratioToSMMLV = smmlv > 0 ? (ibc / smmlv) : 0;

    // Regla 1 y 2
    const aplicaAuxilio = ratioToSMMLV <= 2;
    const aplicaDotacion = ratioToSMMLV <= 2;
    const valorAuxilio = aplicaAuxilio ? auxTransporte : 0;

    // Regla 3: Seguridad Social
    const saludEmpleado = ibc * 0.04;
    const pensionEmpleado = ibc * 0.04;

    const saludEmpresa = ibc * 0.085;
    const pensionEmpresa = ibc * 0.12;
    const arlEmpresa = ibc * (pArl / 100);

    // Regla 4: Parafiscales (Exención Ley 1607)
    const exentoSenaIcbf = ratioToSMMLV < 10;
    const cajaEmpresa = ibc * (pCaja / 100);
    const senaEmpresa = exentoSenaIcbf ? 0 : ibc * (pSena / 100);
    const icbfEmpresa = exentoSenaIcbf ? 0 : ibc * (pIcbf / 100);

    // Regla 5: Provisiones Prestaciones Sociales
    const baseProvisiones = ibc + valorAuxilio;
    const baseVacaciones = ibc;

    const provisionPrima = baseProvisiones * 0.0833;
    const provisionCesantias = baseProvisiones * 0.0833;
    const provisionIntCesantias = provisionCesantias * 0.12; // 1% mensual = 12% de las cesantías
    const provisionVacaciones = baseVacaciones * 0.0417;

    // --- TOTALES ---
    const costoBasico = ibc + valorAuxilio + saludEmpresa + pensionEmpresa + arlEmpresa;
    const costoParafiscales = cajaEmpresa + senaEmpresa + icbfEmpresa;
    const costoProvisiones = provisionPrima + provisionCesantias + provisionIntCesantias + provisionVacaciones;
    const costoTotalMensual = costoBasico + costoParafiscales + costoProvisiones;

    const netoPagarEmpleado = (ibc + valorAuxilio) - saludEmpleado - pensionEmpleado;

    return (
        <div className="min-h-screen bg-slate-900 text-slate-200 py-10 px-4 sm:px-6 lg:px-8 font-sans selection:bg-indigo-500 selection:text-white">
            <div className="max-w-5xl mx-auto space-y-6">

                {/* ENCABEZADO */}
                <div className="flex flex-col md:flex-row justify-between items-center bg-slate-800 p-6 rounded-2xl shadow-xl border border-slate-700">
                    <div>
                        <h1 className="text-2xl font-black text-white flex items-center gap-3 tracking-tight">
                            <FaCalculator className="text-indigo-400" />
                            MÓDULO LABORAL COLOMBIA
                        </h1>
                        <p className="text-slate-400 text-sm mt-1">Simulador de nómina, provisiones y parafiscales.</p>
                    </div>
                    <button
                        onClick={() => setConfigOpen(!configOpen)}
                        className="mt-4 md:mt-0 flex items-center gap-2 px-5 py-2.5 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm font-bold transition duration-300 ring-1 ring-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                        <FaCog className={configOpen ? "animate-spin-slow" : ""} />
                        Parámetros Globales
                    </button>
                </div>

                {/* SECCIÓN 1: CONFIGURACIÓN COLAPSABLE */}
                {configOpen && (
                    <div className="bg-slate-800 p-6 rounded-2xl shadow-xl border border-slate-700 animate-fadeIn">
                        <h2 className="text-sm font-bold text-indigo-400 uppercase tracking-widest mb-5">⚙️ Variables de Ley</h2>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                            <div>
                                <label className="block text-xs font-semibold text-slate-400 mb-1">SMMLV ($)</label>
                                <input type="number" value={smmlv} onChange={(e) => setSmmlv(Number(e.target.value))} className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-white text-sm focus:border-indigo-500 outline-none" />
                            </div>
                            <div>
                                <label className="block text-xs font-semibold text-slate-400 mb-1">Auxilio Transporte ($)</label>
                                <input type="number" value={auxTransporte} onChange={(e) => setAuxTransporte(Number(e.target.value))} className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-white text-sm focus:border-indigo-500 outline-none" />
                            </div>
                            <div>
                                <label className="block text-xs font-semibold text-slate-400 mb-1">ARL (%) <span className="text-slate-500 font-normal ml-1" title="0.522% Riesgo I, 1.044% Riesgo II...">(Ej: 0.522)</span></label>
                                <input type="number" step="0.001" value={pArl} onChange={(e) => setPArl(Number(e.target.value))} className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-white text-sm focus:border-indigo-500 outline-none" />
                            </div>
                            <div>
                                <label className="block text-xs font-semibold text-slate-400 mb-1">Caja Compensación (%)</label>
                                <input type="number" step="0.1" value={pCaja} onChange={(e) => setPCaja(Number(e.target.value))} className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-white text-sm focus:border-indigo-500 outline-none" />
                            </div>
                            <div>
                                <label className="block text-xs font-semibold text-slate-400 mb-1">SENA (%)</label>
                                <input type="number" step="0.1" value={pSena} onChange={(e) => setPSena(Number(e.target.value))} className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-white text-sm focus:border-indigo-500 outline-none" />
                            </div>
                            <div>
                                <label className="block text-xs font-semibold text-slate-400 mb-1">ICBF (%)</label>
                                <input type="number" step="0.1" value={pIcbf} onChange={(e) => setPIcbf(Number(e.target.value))} className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-white text-sm focus:border-indigo-500 outline-none" />
                            </div>
                        </div>
                    </div>
                )}

                {/* SECCIÓN 2: ENTRADA DEL IBC */}
                <div className="bg-slate-800 p-6 sm:p-8 rounded-2xl shadow-xl border border-slate-700">
                    <h2 className="text-sm font-bold text-indigo-400 uppercase tracking-widest mb-6">Ingreso Base de Cotización (IBC)</h2>
                    <div className="flex flex-col lg:flex-row gap-8 items-center justify-center bg-slate-900/50 p-6 rounded-xl border border-slate-700/50">
                        {/* FORMA A: Factor */}
                        <div className="flex-1 w-full relative">
                            <label className="block text-xs font-semibold text-slate-400 mb-2">FORMA A — Por factor de mínimos (SMMLV)</label>
                            <div className="relative">
                                <input
                                    type="text"
                                    value={factorStr}
                                    onChange={handleFactorChange}
                                    className="w-full bg-slate-900 border-2 border-slate-700 focus:border-indigo-500 rounded-xl py-3 pl-4 pr-16 text-white text-2xl font-mono font-bold outline-none transition-colors"
                                    placeholder="Ej: 1.5"
                                />
                                <span className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 font-bold select-none cursor-help" title="Salarios Mínimos Mensuales Legales Vigentes">SMMLV</span>
                            </div>
                        </div>

                        <div className="hidden lg:flex items-center text-slate-500">
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"></path></svg>
                        </div>

                        {/* FORMA B: Pesos */}
                        <div className="flex-1 w-full relative">
                            <label className="block text-xs font-semibold text-slate-400 mb-2">FORMA B — Valor directo (Pesos COP)</label>
                            <div className="relative">
                                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 font-bold select-none">$</span>
                                <input
                                    type="text"
                                    value={formatInputPesos(pesosStr)}
                                    onChange={handlePesosChange}
                                    className="w-full bg-slate-900 border-2 border-slate-700 focus:border-emerald-500 rounded-xl py-3 pl-8 pr-4 text-white text-2xl font-mono font-bold outline-none transition-colors"
                                    placeholder="Ej: 3.500.000"
                                />
                            </div>
                        </div>
                    </div>
                    <div className="mt-4 text-center">
                        <p className="text-slate-300 bg-slate-700/30 inline-block px-4 py-2 rounded-full text-sm font-medium border border-slate-700/50">
                            IBC Total: <strong className="text-white">{formatCurrency(ibc)}</strong> — equivalente a <strong className="text-indigo-300">{ratioToSMMLV.toFixed(2)}</strong> SMMLV
                        </p>
                    </div>
                </div>

                {/* ALERTAS E INDICADORES */}
                <div className="bg-slate-800 p-6 rounded-2xl shadow-xl border border-slate-700">
                    <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">🔔 Alertas e Indicadores de Reglas</h2>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        <div className={`flex items-center gap-3 p-4 rounded-xl border ${aplicaAuxilio ? 'bg-emerald-900/20 border-emerald-800/50' : 'bg-rose-900/20 border-rose-800/50'}`}>
                            {aplicaAuxilio ? <FaCheckCircle className="text-emerald-500 text-xl flex-shrink-0" /> : <FaTimesCircle className="text-rose-500 text-xl flex-shrink-0" />}
                            <div>
                                <p className="text-sm font-bold text-white">{aplicaAuxilio ? 'SÍ aplica' : 'NO aplica'}</p>
                                <p className="text-xs text-slate-400" title="Empleados que devengan hasta 2 SMMLV">Auxilio de transporte</p>
                            </div>
                        </div>
                        <div className={`flex items-center gap-3 p-4 rounded-xl border ${aplicaDotacion ? 'bg-emerald-900/20 border-emerald-800/50' : 'bg-rose-900/20 border-rose-800/50'}`}>
                            {aplicaDotacion ? <FaCheckCircle className="text-emerald-500 text-xl flex-shrink-0" /> : <FaTimesCircle className="text-rose-500 text-xl flex-shrink-0" />}
                            <div>
                                <p className="text-sm font-bold text-white">{aplicaDotacion ? 'SÍ aplica' : 'NO aplica'}</p>
                                <p className="text-xs text-slate-400" title="Derecho a vestido y calzado de labor">Dotación obligatoria</p>
                            </div>
                        </div>
                        <div className={`flex items-center gap-3 p-4 rounded-xl border ${exentoSenaIcbf ? 'bg-emerald-900/20 border-emerald-800/50' : 'bg-amber-900/20 border-amber-800/50'}`}>
                            {exentoSenaIcbf ? <FaCheckCircle className="text-emerald-500 text-xl flex-shrink-0" /> : <FaTimesCircle className="text-amber-500 text-xl flex-shrink-0" />}
                            <div>
                                <p className="text-sm font-bold text-white">{exentoSenaIcbf ? 'Exento (Ley 1607)' : 'Paga completos'}</p>
                                <p className="text-xs text-slate-400" title="Si el IBC es menor a 10 SMMLV, la empresa queda exenta de aportar SENA e ICBF, y salud empresa pasa del 8.5% a 0%? Asumimos según regla general que salud es 8.5% siempre a menos que se aclare, pero en la regla exigida se listó Salud 8.5% fijo y solo exención para SENA/ICBF.">Aportes SENA e ICBF</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* TARJETAS DE RESULTADO */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

                    {/* COSTO EMPLEADOR */}
                    <div className="bg-slate-800 rounded-2xl shadow-2xl border border-blue-900/50 overflow-hidden flex flex-col">
                        <div className="bg-gradient-to-r from-blue-900 to-slate-800 p-5 border-b border-blue-800/50 flex items-center gap-3">
                            <FaBuilding className="text-blue-400 text-xl" />
                            <h2 className="text-lg font-bold text-white uppercase tracking-wider">Costo Empleador</h2>
                        </div>

                        <div className="p-6 flex-1 space-y-4">
                            <div className="flex justify-between items-center pb-2 border-b border-slate-700/50">
                                <span className="text-slate-300 font-medium">IBC (Salario base)</span>
                                <span className="font-mono text-white text-right">{formatCurrency(ibc)}</span>
                            </div>
                            <div className="flex justify-between items-center pb-2 border-b border-slate-700/50">
                                <span className="text-slate-300 font-medium">Auxilio de transporte</span>
                                <span className="font-mono text-white text-right">{aplicaAuxilio ? formatCurrency(valorAuxilio) : <span className="text-slate-500">N/A</span>}</span>
                            </div>

                            <h3 className="text-xs font-bold font-mono text-blue-400 mt-4 mb-2">SEGURIDAD SOCIAL</h3>
                            <div className="flex justify-between items-center text-sm pb-1">
                                <span className="text-slate-400">Salud empresa (8.5%)</span>
                                <span className="font-mono text-white text-right">{formatCurrency(saludEmpresa)}</span>
                            </div>
                            <div className="flex justify-between items-center text-sm pb-1">
                                <span className="text-slate-400">Pensión empresa (12%)</span>
                                <span className="font-mono text-white text-right">{formatCurrency(pensionEmpresa)}</span>
                            </div>
                            <div className="flex justify-between items-center text-sm pb-1">
                                <span className="text-slate-400">ARL ({pArl}%)</span>
                                <span className="font-mono text-white text-right">{formatCurrency(arlEmpresa)}</span>
                            </div>

                            <h3 className="text-xs font-bold font-mono text-blue-400 mt-4 mb-2">PARAFISCALES</h3>
                            <div className="flex justify-between items-center text-sm pb-1">
                                <span className="text-slate-400">Caja de compensación ({pCaja}%)</span>
                                <span className="font-mono text-white text-right">{formatCurrency(cajaEmpresa)}</span>
                            </div>
                            <div className="flex justify-between items-center text-sm pb-1">
                                <span className="text-slate-400">SENA ({pSena}%) {exentoSenaIcbf && <span className="text-[10px] text-emerald-400 font-bold ml-1">EXENTO</span>}</span>
                                <span className="font-mono text-white text-right">{formatCurrency(senaEmpresa)}</span>
                            </div>
                            <div className="flex justify-between items-center text-sm pb-1">
                                <span className="text-slate-400">ICBF ({pIcbf}%) {exentoSenaIcbf && <span className="text-[10px] text-emerald-400 font-bold ml-1">EXENTO</span>}</span>
                                <span className="font-mono text-white text-right">{formatCurrency(icbfEmpresa)}</span>
                            </div>

                            <h3 className="text-xs font-bold font-mono text-blue-400 mt-4 mb-2">PROVISIONES (MENSUALES)</h3>
                            <div className="flex justify-between items-center text-sm pb-1">
                                <span className="text-slate-400 pt-0.5 cursor-help" title="Base: IBC + Transporte">Prima serv. (8.33%) <FaInfoCircle className="inline text-[10px] ml-1 opacity-50" /></span>
                                <span className="font-mono text-white text-right">{formatCurrency(provisionPrima)}</span>
                            </div>
                            <div className="flex justify-between items-center text-sm pb-1">
                                <span className="text-slate-400 pt-0.5 cursor-help" title="Base: IBC + Transporte">Cesantías (8.33%) <FaInfoCircle className="inline text-[10px] ml-1 opacity-50" /></span>
                                <span className="font-mono text-white text-right">{formatCurrency(provisionCesantias)}</span>
                            </div>
                            <div className="flex justify-between items-center text-sm pb-1">
                                <span className="text-slate-400 pt-0.5 cursor-help" title="12% EA sobre el total de cesantías">Int. Cesantías (1% pm) <FaInfoCircle className="inline text-[10px] ml-1 opacity-50" /></span>
                                <span className="font-mono text-white text-right">{formatCurrency(provisionIntCesantias)}</span>
                            </div>
                            <div className="flex justify-between items-center text-sm pb-1">
                                <span className="text-slate-400 pt-0.5 cursor-help" title="Base: Solo IBC">Vacaciones (4.17%) <FaInfoCircle className="inline text-[10px] ml-1 opacity-50" /></span>
                                <span className="font-mono text-white text-right">{formatCurrency(provisionVacaciones)}</span>
                            </div>
                        </div>

                        <div className="p-6 bg-slate-900 border-t border-slate-700/50 mt-auto">
                            <div className="flex justify-between items-end">
                                <span className="text-slate-400 text-xs font-bold uppercase">Costo Mensual Empresa</span>
                                <span className="text-3xl font-black text-blue-400 font-mono tracking-tight">{formatCurrency(costoTotalMensual)}</span>
                            </div>
                        </div>
                    </div>

                    {/* LIQUIDACIÓN EMPLEADO */}
                    <div className="bg-slate-800 rounded-2xl shadow-2xl border border-emerald-900/50 overflow-hidden flex flex-col h-fit">
                        <div className="bg-gradient-to-r from-emerald-900 to-slate-800 p-5 border-b border-emerald-800/50 flex items-center gap-3">
                            <FaUserTie className="text-emerald-400 text-xl" />
                            <h2 className="text-lg font-bold text-white uppercase tracking-wider">Liquidación Empleado</h2>
                        </div>

                        <div className="p-6 space-y-4">
                            <div className="flex justify-between items-center pb-2 border-b border-slate-700/50">
                                <span className="text-slate-300 font-medium pt-1">Salario base</span>
                                <span className="font-mono text-white text-right">{formatCurrency(ibc)}</span>
                            </div>
                            <div className="flex justify-between items-center pb-2 border-b border-slate-700/50">
                                <span className="text-emerald-300 font-medium">(+) Auxilio de transporte</span>
                                <span className="font-mono text-emerald-300 text-right">{aplicaAuxilio ? formatCurrency(valorAuxilio) : <span className="text-emerald-900">N/A</span>}</span>
                            </div>

                            <h3 className="text-xs font-bold font-mono text-rose-400 mt-6 mb-2">DEDUCCIONES DE LEY</h3>
                            <div className="flex justify-between items-center text-sm pb-1">
                                <span className="text-rose-300">(-) Salud empleado (4%)</span>
                                <span className="font-mono text-rose-300 text-right">-{formatCurrency(saludEmpleado)}</span>
                            </div>
                            <div className="flex justify-between items-center text-sm pb-1">
                                <span className="text-rose-300">(-) Pensión empleado (4%)</span>
                                <span className="font-mono text-rose-300 text-right">-{formatCurrency(pensionEmpleado)}</span>
                            </div>
                        </div>

                        <div className="p-6 bg-slate-900 border-t border-slate-700/50 mt-auto">
                            <div className="flex justify-between items-end">
                                <span className="text-slate-400 text-xs font-bold uppercase">Neto a pagar</span>
                                <span className="text-3xl font-black text-emerald-400 font-mono tracking-tight">{formatCurrency(netoPagarEmpleado)}</span>
                            </div>
                        </div>

                        {/* Gráfico Visual Simple */}
                        <div className="px-6 pb-6 bg-slate-900">
                            <div className="flex items-center gap-2 mb-2">
                                <div className="h-2 flex-grow bg-emerald-500/80 rounded-l-full" title="Ingresos" style={{ width: '92%' }}></div>
                                <div className="h-2 flex-grow bg-rose-500/80 rounded-r-full" title="Deducciones" style={{ width: '8%' }}></div>
                            </div>
                            <div className="flex justify-between text-[10px] text-slate-500 font-medium">
                                <span>Ingresos {formatCurrency(ibc + valorAuxilio)}</span>
                                <span>Total Ded. {formatCurrency(saludEmpleado + pensionEmpleado)}</span>
                            </div>
                        </div>

                    </div>
                </div>

                {/* NOTA LEGAL */}
                <div className="text-center mt-12 py-6 border-t border-slate-800">
                    <p className="text-xs text-slate-500">
                        Cálculos orientativos basados en normativa laboral colombiana 2026. <br />
                        <span className="italic">Consulte con su asesor contable o jurídico para tomar decisiones empresariales.</span>
                    </p>
                </div>

            </div>
        </div>
    );
}
