import React, { useState, useEffect } from 'react';
import { FaMoneyBillWave, FaLandmark, FaChartLine, FaEdit, FaSave, FaTimes, FaCalculator, FaCoins } from 'react-icons/fa';
import { indicadoresApiService } from '@/lib/indicadoresApiService';
import { toast } from 'react-toastify';
import { useAuth } from '@/app/context/AuthContext';

const formatCurrency = (val) => {
    if (val === undefined || val === null) return '$0';
    return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(val);
};

export default function EconomicIndicatorsPanel({ isOpen, onClose, sidebarExpanded }) {
    const { user } = useAuth();
    const [activeTab, setActiveTab] = useState('laboral');
    const [loading, setLoading] = useState(false);

    // Dynamic Position Class
    // Fixed Viewport Positioning strategies
    // Sidebar is z-[60]. We use z-[70] to guarantee we are ON TOP of any sidebar content if overlap happens.
    // We adjust 'right' to sit perfectly next to the sidebar (350px open, 48px closed).
    const rightPositionClass = sidebarExpanded ? 'right-[350px]' : 'right-[48px]';

    const [indicators, setIndicators] = useState({
        salario_minimo: 1300000,
        auxilio_transporte: 162000,
        uvt: 47065,
        trm: 3900,
        euro: 4200,
        sancion_minima: 470650
    });

    // Simulador State
    const [salaryBase, setSalaryBase] = useState(1300000); // Default to SMMLV
    const [isEditing, setIsEditing] = useState(false);
    const [editValues, setEditValues] = useState({}); // Temp storage for editing

    const currentYear = new Date().getFullYear();

    useEffect(() => {
        if (isOpen) {
            fetchIndicators();
        }
    }, [isOpen]);

    const fetchIndicators = async () => {
        setLoading(true);
        try {
            // 1. Load Defaults
            let finalData = { ...indicators };

            // 2. Try LocalStorage (Immediate feedback / Offline support)
            try {
                const local = localStorage.getItem(`indicadores_${currentYear}`);
                if (local) {
                    finalData = { ...finalData, ...JSON.parse(local) };
                }
            } catch (e) { console.error("LS Error", e); }

            // 3. Try API (Source of Truth)
            try {
                const data = await indicadoresApiService.getByVigencia(currentYear);
                // Only merge if data has actual keys
                if (data && Object.keys(data).length > 0) {
                    finalData = { ...finalData, ...data };
                }
            } catch (apiErr) {
                console.warn("API Fetch Error (using local/defaults)", apiErr);
            }

            setIndicators(finalData);

            // Update Simulator Base if fresh load
            if (salaryBase === 1300000 && finalData.salario_minimo !== 1300000) {
                setSalaryBase(finalData.salario_minimo);
            }

        } catch (err) {
            toast.error("Error cargando indicadores");
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        try {
            // 1. Merge current + edits
            const newData = { ...indicators, ...editValues };

            // 2. Save LocalStorage (Instant persistence)
            localStorage.setItem(`indicadores_${currentYear}`, JSON.stringify(newData));

            // 3. Optimistic UI Update
            setIndicators(newData);
            setIsEditing(false);
            toast.success("Indicadores guardados (Local)");

            // 4. Try API Sync (Background)
            try {
                await indicadoresApiService.update(currentYear, editValues);
                // toast.info("Sincronizado con nube"); // Optional noise
            } catch (apiErr) {
                console.error("API Sync failed", apiErr);
                toast.warning("Guardado localmente. Error sincronizando nube.");
            }

        } catch (err) {
            toast.error("Error guardando cambios");
        }
    };

    const startEditing = () => {
        // Pre-fill with current values to ensure inputs are not empty
        setEditValues({
            trm: indicators.trm,
            salario_minimo: indicators.salario_minimo,
            auxilio_transporte: indicators.auxilio_transporte,
            uvt: indicators.uvt
        });
        setIsEditing(true);
    };

    // --- CÁLCULOS SIMULADOR ---
    const totalDevengado = salaryBase + (salaryBase <= (indicators.salario_minimo * 2) ? indicators.auxilio_transporte : 0);

    // Aportes Empleado
    const saludEmp = salaryBase * 0.04;
    const pensionEmp = salaryBase * 0.04;
    const netoPagar = totalDevengado - saludEmp - pensionEmp;

    // Aportes Empresa
    // Exoneración Salud (Art 114-1 ET): Asumimos SI para simplificar, pero mostramos data normal si salario > 10 SMMLV
    const tieneExoneracion = salaryBase < (10 * indicators.salario_minimo);
    const saludCia = tieneExoneracion ? 0 : (salaryBase * 0.085);
    const pensionCia = salaryBase * 0.12;
    const arlCia = salaryBase * 0.00522; // Nivel 1
    const parafiscalesCia = tieneExoneracion ? 0 : (salaryBase * 0.09); // Caja + ICBF + Sena (Simplificado)


    const caja = salaryBase * 0.04; // Caja siempre se paga

    // Costo Total Empresa
    const costoTotal = totalDevengado + saludCia + pensionCia + arlCia + (tieneExoneracion ? caja : parafiscalesCia);

    // RENDER: FIXED positioning to be safe. Z-70 to be visible. Right offset to be polite.
    // When closed: opacity-0 to disappear, pointer-events-none to click-through. Use translate-x-10 to nudge it slightly right/in.
    return (
        <div className={`fixed inset-y-0 ${rightPositionClass} w-[400px] z-[70] bg-white shadow-2xl transform transition-all duration-300 ease-in-out border-l border-gray-200 ${isOpen ? 'translate-x-0 opacity-100' : 'translate-x-10 opacity-0 pointer-events-none'}`}>
            {/* Header */}
            <div className="h-16 bg-gradient-to-r from-gray-900 to-gray-800 text-white flex items-center justify-between px-6">
                <div>
                    <h2 className="font-bold text-lg flex items-center gap-2"><FaChartLine className="text-yellow-400" /> Indicadores {currentYear}</h2>
                    <p className="text-[10px] text-gray-300">TRM Hoy: <span className="text-yellow-300 font-mono font-bold text-sm tracking-wide">{formatCurrency(indicators.trm)}</span></p>
                </div>
                <button onClick={onClose} className="text-gray-400 hover:text-white"><FaTimes /></button>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-gray-100">
                <button onClick={() => setActiveTab('laboral')} className={`flex-1 py-3 text-sm font-medium transition-colors ${activeTab === 'laboral' ? 'text-indigo-600 border-b-2 border-indigo-600 bg-indigo-50/50' : 'text-gray-500 hover:bg-gray-50'}`}>
                    <FaMoneyBillWave className="inline mb-1 mr-1" /> Laboral
                </button>
                <button onClick={() => setActiveTab('tributario')} className={`flex-1 py-3 text-sm font-medium transition-colors ${activeTab === 'tributario' ? 'text-indigo-600 border-b-2 border-indigo-600 bg-indigo-50/50' : 'text-gray-500 hover:bg-gray-50'}`}>
                    <FaLandmark className="inline mb-1 mr-1" /> Tributario
                </button>
                <button onClick={() => setActiveTab('financiero')} className={`flex-1 py-3 text-sm font-medium transition-colors ${activeTab === 'financiero' ? 'text-indigo-600 border-b-2 border-indigo-600 bg-indigo-50/50' : 'text-gray-500 hover:bg-gray-50'}`}>
                    <FaCoins className="inline mb-1 mr-1" /> Tasas
                </button>
            </div>

            {/* Content */}
            <div className="p-6 pb-32 overflow-y-auto h-[calc(100%-130px)] bg-gray-50/30">
                {loading ? <div className="text-center py-10 text-gray-400 animate-pulse">Cargando indicadores...</div> : (
                    <>
                        {activeTab === 'laboral' && (
                            <div className="space-y-6 animate-fadeIn">
                                {/* SIMULADOR CARD */}
                                <div className="bg-white p-5 rounded-xl shadow-sm border border-indigo-100">
                                    <h3 className="text-xs font-bold text-indigo-900 uppercase tracking-widest mb-4 flex items-center"><FaCalculator className="mr-2" /> Simulador Costos</h3>

                                    <div className="mb-4">
                                        <label className="block text-xs font-medium text-gray-500 mb-1">Salario Base Mensual</label>
                                        <input
                                            type="number"
                                            value={salaryBase}
                                            onChange={(e) => setSalaryBase(Number(e.target.value))}
                                            className="w-full text-right font-mono font-bold text-gray-800 text-lg border-b-2 border-indigo-100 focus:border-indigo-500 outline-none bg-transparent"
                                        />
                                        <div className="flex justify-between mt-1">
                                            <button onClick={() => setSalaryBase(indicators.salario_minimo)} className="text-[10px] text-blue-500 hover:underline">Usar Mínimo</button>
                                            <button onClick={() => setSalaryBase(indicators.salario_minimo * 2)} className="text-[10px] text-blue-500 hover:underline">2 SMMLV</button>
                                        </div>
                                    </div>

                                    <div className="space-y-3">
                                        <div className="flex justify-between items-center p-2 bg-green-50 rounded-lg border border-green-100">
                                            <span className="text-xs text-green-800 font-medium">Neto a Pagar Empleado</span>
                                            <span className="font-bold text-green-700">{formatCurrency(netoPagar)}</span>
                                        </div>
                                        <div className="flex justify-between items-center p-2 bg-orange-50 rounded-lg border border-orange-100">
                                            <span className="text-xs text-orange-800 font-medium">Costo Total Empresa (Estimado)</span>
                                            <span className="font-bold text-orange-700">{formatCurrency(costoTotal * 1.0833 + indicators.auxilio_transporte)}*</span>
                                        </div>
                                        <p className="text-[9px] text-gray-400 text-right mt-1">*Incluye estimación de Prestaciones (~21%)</p>
                                    </div>
                                </div>

                                {/* DETALLE TABLE */}
                                <div>
                                    <h4 className="text-xs font-bold text-gray-500 mb-2 uppercase">Desglose Detallado</h4>
                                    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden text-xs">
                                        <table className="w-full">
                                            <thead className="bg-gray-50 text-gray-500 font-medium">
                                                <tr>
                                                    <th className="p-2 text-left">Concepto</th>
                                                    <th className="p-2 text-right">Empleado</th>
                                                    <th className="p-2 text-right">Empresa</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-gray-100">
                                                <tr>
                                                    <td className="p-2 text-gray-600">Salud</td>
                                                    <td className="p-2 text-right text-red-600">-{formatCurrency(saludEmp)}</td>
                                                    <td className="p-2 text-right text-gray-800">{formatCurrency(saludCia)}</td>
                                                </tr>
                                                <tr>
                                                    <td className="p-2 text-gray-600">Pensión</td>
                                                    <td className="p-2 text-right text-red-600">-{formatCurrency(pensionEmp)}</td>
                                                    <td className="p-2 text-right text-gray-800">{formatCurrency(pensionCia)}</td>
                                                </tr>
                                                <tr>
                                                    <td className="p-2 text-gray-600">Parafiscales</td>
                                                    <td className="p-2 text-right text-gray-300">-</td>
                                                    <td className="p-2 text-right text-gray-800">{formatCurrency(tieneExoneracion ? caja : parafiscalesCia)}</td>
                                                </tr>
                                                <tr>
                                                    <td className="p-2 text-gray-600 font-bold">Aux. Transporte</td>
                                                    <td className="p-2 text-right text-green-600 font-bold">+{formatCurrency(salaryBase <= (indicators.salario_minimo * 2) ? indicators.auxilio_transporte : 0)}</td>
                                                    <td className="p-2 text-right text-gray-800 font-bold">{formatCurrency(salaryBase <= (indicators.salario_minimo * 2) ? indicators.auxilio_transporte : 0)}</td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeTab === 'tributario' && (
                            <div className="space-y-4 animate-fadeIn">
                                <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
                                    <div className="flex justify-between items-center mb-3">
                                        <span className="text-sm text-gray-600 font-bold">Unidad Valor Tributario (UVT)</span>
                                        <span className="text-xl font-mono text-indigo-700 bg-indigo-50 px-2 py-1 rounded">{formatCurrency(indicators.uvt)}</span>
                                    </div>
                                    <div className="text-xs text-gray-500 space-y-2">
                                        <div className="flex justify-between border-t border-gray-100 pt-2">
                                            <span>Sanción Mínima (10 UVT)</span>
                                            <strong>{formatCurrency(indicators.uvt * 10)}</strong>
                                        </div>
                                        <div className="flex justify-between">
                                            <span>Base Ret. Compras (27 UVT)</span>
                                            <strong>{formatCurrency(indicators.uvt * 27)}</strong>
                                        </div>
                                        <div className="flex justify-between">
                                            <span>Base Ret. Servicios (4 UVT)</span>
                                            <strong>{formatCurrency(indicators.uvt * 4)}</strong>
                                        </div>
                                        <div className="flex justify-between">
                                            <span>Declarar Renta (Patrimonio)</span>
                                            <strong>{formatCurrency(indicators.uvt * 4500)}</strong>
                                        </div>
                                    </div>
                                </div>

                                <div className="p-3 bg-yellow-50 text-yellow-800 rounded-lg text-xs leading-relaxed border border-yellow-200">
                                    🚀 <strong>Tip:</strong> Estos valores se calculan automáticamente con el valor UVT ingresado. Mantén la UVT al día.
                                </div>
                            </div>
                        )}

                        {activeTab === 'financiero' && (
                            <div className="space-y-6 animate-fadeIn">
                                {/* TRM CARD */}
                                <div className="bg-gradient-to-br from-green-50 to-emerald-100 p-6 rounded-xl border border-emerald-200 text-center relative overflow-hidden">
                                    <FaMoneyBillWave className="absolute -right-4 -bottom-4 text-6xl text-emerald-200 opacity-50 transform rotate-12" />
                                    <h3 className="text-sm font-bold text-emerald-800 uppercase mb-2">Dólar TRM Hoy</h3>
                                    <div className="text-4xl font-mono font-black text-emerald-700 tracking-tight">{formatCurrency(indicators.trm)}</div>
                                    <p className="text-xs text-emerald-600 mt-2">Tasa Representativa del Mercado</p>
                                </div>

                                {/* EURO CARD */}
                                <div className="bg-gradient-to-br from-blue-50 to-indigo-100 p-6 rounded-xl border border-blue-200 text-center relative overflow-hidden">
                                    <FaCoins className="absolute -right-4 -bottom-4 text-6xl text-blue-200 opacity-50 transform rotate-12" />
                                    <h3 className="text-sm font-bold text-blue-800 uppercase mb-2">Euro Hoy</h3>
                                    <div className="text-4xl font-mono font-black text-blue-700 tracking-tight">{formatCurrency(indicators.euro)}</div>
                                </div>
                            </div>
                        )}

                        {/* EDIT MODE OVERLAY */}
                        {isEditing && (
                            <div className="mt-8 border-t border-gray-200 pt-4 animate-slideInUp">
                                <h4 className="font-bold text-gray-700 mb-3 text-sm flex items-center gap-2"><FaEdit /> Editar Variables Globales</h4>
                                <div className="space-y-3">
                                    <div>
                                        <label className="text-xs font-bold text-gray-500">TRM (Dólar)</label>
                                        <input type="number" value={editValues.trm} onChange={(e) => setEditValues({ ...editValues, trm: Number(e.target.value) })} className="w-full p-2 border border-gray-300 rounded text-sm" />
                                    </div>
                                    <div>
                                        <label className="text-xs font-bold text-gray-500">UVT {currentYear}</label>
                                        <input type="number" value={editValues.uvt} onChange={(e) => setEditValues({ ...editValues, uvt: Number(e.target.value) })} className="w-full p-2 border border-gray-300 rounded text-sm" />
                                    </div>
                                    <div>
                                        <label className="text-xs font-bold text-gray-500">Salario Mínimo</label>
                                        <input type="number" value={editValues.salario_minimo} onChange={(e) => setEditValues({ ...editValues, salario_minimo: Number(e.target.value) })} className="w-full p-2 border border-gray-300 rounded text-sm" />
                                    </div>
                                    <div>
                                        <label className="text-xs font-bold text-gray-500">Aux. Transporte</label>
                                        <input type="number" value={editValues.auxilio_transporte} onChange={(e) => setEditValues({ ...editValues, auxilio_transporte: Number(e.target.value) })} className="w-full p-2 border border-gray-300 rounded text-sm" />
                                    </div>
                                </div>
                            </div>
                        )}
                    </>
                )}
            </div>

            {/* Footer Actions */}
            <div className="absolute bottom-0 left-0 right-0 p-4 bg-white border-t border-gray-200 flex justify-between items-center h-[70px]">
                {loading ? <span className="text-xs text-gray-400">Sincronizando...</span> : (
                    isEditing ? (
                        <div className="flex gap-2 w-full">
                            <button onClick={() => setIsEditing(false)} className="flex-1 py-2 bg-gray-100 text-gray-600 rounded-lg text-sm font-bold hover:bg-gray-200">Cancelar</button>
                            <button onClick={handleSave} className="flex-1 py-2 bg-indigo-600 text-white rounded-lg text-sm font-bold hover:bg-indigo-700 flex justify-center items-center gap-2"><FaSave /> Guardar Cambios</button>
                        </div>
                    ) : (
                        <button onClick={startEditing} className="w-full py-2 border-2 border-gray-200 text-gray-500 rounded-lg text-xs font-bold hover:border-gray-300 hover:text-gray-700 uppercase tracking-wider transition-all">
                            Configurar Valores
                        </button>
                    )
                )}
            </div>
        </div>
    );
}
