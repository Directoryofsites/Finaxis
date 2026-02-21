import React, { useState, useEffect } from 'react';
import { FaMoneyBillWave, FaLandmark, FaChartLine, FaEdit, FaSave, FaTimes, FaCalculator, FaCoins, FaCalendarCheck, FaSearch, FaExternalLinkAlt, FaSync, FaPercent } from 'react-icons/fa';
import { indicadoresApiService } from '@/lib/indicadoresApiService';
import { toast } from 'react-toastify';
import { useAuth } from '@/app/context/AuthContext';
import { TAX_CONSTANTS_2026, getTaxDeadlines, RETENTION_CONCEPTS_2026 } from '../utils/taxData2026';
import TaxCalendarModal from './TaxCalendarModal';

const formatCurrency = (val) => {
    if (val === undefined || val === null) return '$0';
    return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(val);
};

export default function EconomicIndicatorsPanel({ isOpen, onClose, sidebarExpanded }) {
    const { user } = useAuth();
    const [activeTab, setActiveTab] = useState('laboral');
    const [loading, setLoading] = useState(false);
    const [showTaxModal, setShowTaxModal] = useState(false);

    // TRIBUTARIO STATE
    const [nitTerminacion, setNitTerminacion] = useState('');
    const [tipoPersona, setTipoPersona] = useState('juridica'); // 'juridica' | 'natural'
    const [periodicidadIva, setPeriodicidadIva] = useState('bimestral'); // 'bimestral' | 'cuatrimestral'
    const [taxSearch, setTaxSearch] = useState('');
    const [deadlines, setDeadlines] = useState({ renta: '', iva: '', retencion: '' });

    // Dynamic Position Class
    const rightPositionClass = sidebarExpanded ? 'right-[350px]' : 'right-[48px]';

    const [indicators, setIndicators] = useState({
        salario_minimo: 1300000,
        auxilio_transporte: 162000,
        uvt: TAX_CONSTANTS_2026.UVT, // Default 2026
        trm: 4100, // Approx
        euro: 4400,
        tasa_usura: 28.5, // Approx (placeholder)
        sancion_minima: TAX_CONSTANTS_2026.UVT * 10
    });

    // Simulador State
    const [salaryBase, setSalaryBase] = useState(1300000);
    const [isEditing, setIsEditing] = useState(false);
    const [editValues, setEditValues] = useState({});

    const currentYear = new Date().getFullYear();

    useEffect(() => {
        if (isOpen) {
            fetchIndicators();
        }
    }, [isOpen]);

    // Recalcular fechas cuando cambien los inputs
    useEffect(() => {
        if (nitTerminacion.length >= 1) {
            const fechas = getTaxDeadlines(nitTerminacion, tipoPersona, periodicidadIva);
            if (fechas) {
                setDeadlines(fechas);
            }
        } else {
            setDeadlines({ renta: '', iva: '', retencion: '' });
        }
    }, [nitTerminacion, tipoPersona, periodicidadIva]);

    const fetchIndicators = async () => {
        setLoading(true);
        try {
            // 1. Defaults 2026 Base
            let finalData = {
                ...indicators,
                uvt: TAX_CONSTANTS_2026.UVT,
                sancion_minima: TAX_CONSTANTS_2026.UVT * 10
            };

            // 2. Try LocalStorage
            try {
                const local = localStorage.getItem(`indicadores_${currentYear}`);
                if (local) {
                    finalData = { ...finalData, ...JSON.parse(local) };
                }
            } catch (e) { console.error("LS Error", e); }

            // 3. Try API
            try {
                const data = await indicadoresApiService.getByVigencia(currentYear);
                if (data && Object.keys(data).length > 0) {
                    finalData = { ...finalData, ...data };
                }
            } catch (apiErr) {
                console.warn("API Fetch Error (using defaults)", apiErr);
            }

            setIndicators(finalData);

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
            const newData = { ...indicators, ...editValues };
            localStorage.setItem(`indicadores_${currentYear}`, JSON.stringify(newData));
            setIndicators(newData);
            setIsEditing(false);
            toast.success("Indicadores guardados (Local)");
            try {
                await indicadoresApiService.update(currentYear, editValues);
            } catch (apiErr) {
                console.error("API Sync failed", apiErr);
            }
        } catch (err) {
            toast.error("Error guardando cambios");
        }
    };

    const startEditing = () => {
        setEditValues({
            trm: indicators.trm,
            salario_minimo: indicators.salario_minimo,
            auxilio_transporte: indicators.auxilio_transporte,
            uvt: indicators.uvt,
            tasa_usura: indicators.tasa_usura || 0
        });
        setIsEditing(true);
    };

    const handleSyncForce = async () => {
        setLoading(true);
        try {
            const freshData = await indicadoresApiService.syncForce(currentYear);
            toast.success("TRM y Euro actualizados (SFC y Frankfurter)");

            const newData = { ...indicators, ...freshData };
            localStorage.setItem(`indicadores_${currentYear}`, JSON.stringify(newData));
            setIndicators(newData);

        } catch (err) {
            toast.error("Error al sincronizar con Datos Abiertos de Colombia");
        } finally {
            setLoading(false);
        }
    };

    // --- CALCULOS TRIBUTARIOS ---
    // La lógica se movió al useEffect y a getTaxDeadlines importado

    // Filter Retention Concepts for Sidebar
    const sidebarRetention = RETENTION_CONCEPTS_2026.filter(item =>
        item.concepto.toLowerCase().includes(taxSearch.toLowerCase())
    ).slice(0, 3); // Solo mostrar top 3

    // --- CÁLCULOS SIMULADOR LABORAL ---
    const totalDevengado = salaryBase + (salaryBase <= (indicators.salario_minimo * 2) ? indicators.auxilio_transporte : 0);
    const saludEmp = salaryBase * 0.04;
    const pensionEmp = salaryBase * 0.04;
    const netoPagar = totalDevengado - saludEmp - pensionEmp;
    const tieneExoneracion = salaryBase < (10 * indicators.salario_minimo);
    const saludCia = tieneExoneracion ? 0 : (salaryBase * 0.085);
    const pensionCia = salaryBase * 0.12;
    const arlCia = salaryBase * 0.00522;
    const parafiscalesCia = tieneExoneracion ? 0 : (salaryBase * 0.09);
    const caja = salaryBase * 0.04;
    const costoTotal = totalDevengado + saludCia + pensionCia + arlCia + (tieneExoneracion ? caja : parafiscalesCia);

    return (
        <>
            <div className={`fixed inset-y-0 ${rightPositionClass} w-[400px] z-[70] bg-white shadow-2xl transform transition-all duration-300 ease-in-out border-l border-gray-200 ${isOpen ? 'translate-x-0 opacity-100' : 'translate-x-10 opacity-0 pointer-events-none'}`}>
                {/* Header */}
                <div className="h-16 bg-gradient-to-r from-gray-900 to-gray-800 text-white flex items-center justify-between px-6">
                    <div>
                        <h2 className="font-bold text-lg flex items-center gap-2">
                            <FaChartLine className="text-yellow-400" /> Indicadores {currentYear}
                            <button onClick={handleSyncForce} title="Actualizar Datos Oficiales" className="text-indigo-300 hover:text-white transition-colors ml-1" disabled={loading}>
                                <FaSync className={loading ? "animate-spin" : ""} size={12} />
                            </button>
                        </h2>
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
                                        </div>
                                        <div className="space-y-3">
                                            <div className="flex justify-between items-center p-2 bg-green-50 rounded-lg border border-green-100">
                                                <span className="text-xs text-green-800 font-medium">Neto a Pagar Empleado</span>
                                                <span className="font-bold text-green-700">{formatCurrency(netoPagar)}</span>
                                            </div>
                                            <div className="flex justify-between items-center p-2 bg-orange-50 rounded-lg border border-orange-100">
                                                <span className="text-xs text-orange-800 font-medium">Costo Total Empresa</span>
                                                <span className="font-bold text-orange-700">{formatCurrency(costoTotal * 1.0833 + indicators.auxilio_transporte)}*</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {activeTab === 'tributario' && (
                                <div className="space-y-6 animate-fadeIn">
                                    {/* CALENDARIO WIDGET */}
                                    <div className="bg-white p-5 rounded-xl shadow-sm border border-indigo-100">
                                        <h3 className="text-xs font-bold text-indigo-900 uppercase tracking-widest mb-4 flex items-center">
                                            <FaCalendarCheck className="mr-2" /> Mis Vencimientos 2026
                                        </h3>

                                        <div className="grid grid-cols-2 gap-3 mb-4">
                                            <div>
                                                <label className="block text-[10px] uppercase text-gray-400 font-bold mb-1">NIT (Sin DV)</label>
                                                <input
                                                    type="text"
                                                    maxLength="15"
                                                    placeholder="Ej: 900123456"
                                                    value={nitTerminacion}
                                                    onChange={(e) => setNitTerminacion(e.target.value)}
                                                    className="w-full p-2 bg-gray-50 border border-gray-200 rounded text-sm font-mono focus:border-indigo-500 outline-none"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-[10px] uppercase text-gray-400 font-bold mb-1">Tipo Persona</label>
                                                <select
                                                    value={tipoPersona}
                                                    onChange={(e) => setTipoPersona(e.target.value)}
                                                    className="w-full p-2 bg-gray-50 border border-gray-200 rounded text-xs focus:border-indigo-500 outline-none"
                                                >
                                                    <option value="juridica">Jurídica</option>
                                                    <option value="natural">Natural</option>
                                                </select>
                                            </div>
                                        </div>

                                        <div className="mb-4">
                                            <label className="block text-[10px] uppercase text-gray-400 font-bold mb-1">Periodicidad IVA</label>
                                            <div className="flex bg-gray-50 p-1 rounded-lg border border-gray-200">
                                                <button
                                                    onClick={() => setPeriodicidadIva('bimestral')}
                                                    className={`flex-1 text-[10px] py-1 rounded-md transition-colors ${periodicidadIva === 'bimestral' ? 'bg-white shadow text-indigo-600 font-bold' : 'text-gray-400'}`}
                                                >
                                                    Bimestral
                                                </button>
                                                <button
                                                    onClick={() => setPeriodicidadIva('cuatrimestral')}
                                                    className={`flex-1 text-[10px] py-1 rounded-md transition-colors ${periodicidadIva === 'cuatrimestral' ? 'bg-white shadow text-indigo-600 font-bold' : 'text-gray-400'}`}
                                                >
                                                    Cuatrimestral
                                                </button>
                                            </div>
                                        </div>

                                        {nitTerminacion ? (
                                            <div className="space-y-2 bg-indigo-50/50 p-3 rounded-lg border border-indigo-100">
                                                <div className="flex justify-between items-center text-xs">
                                                    <span className="text-gray-600 font-medium">Renta y Comp.</span>
                                                    <span className="font-bold text-indigo-700 max-w-[120px] text-right truncate" title={deadlines.renta}>{deadlines.renta}</span>
                                                </div>
                                                <div className="flex justify-between items-center text-xs">
                                                    <span className="text-gray-600 font-medium">IVA Prox.</span>
                                                    <span className="font-bold text-indigo-700 max-w-[120px] text-right truncate" title={deadlines.iva}>{deadlines.iva}</span>
                                                </div>
                                                <div className="flex justify-between items-center text-xs">
                                                    <span className="text-gray-600 font-medium">Retención</span>
                                                    <span className="font-bold text-indigo-700 max-w-[120px] text-right truncate" title={deadlines.retencion}>{deadlines.retencion}</span>
                                                </div>
                                            </div>
                                        ) : (
                                            <div className="text-center p-4 bg-gray-50 rounded-lg border border-dashed border-gray-200">
                                                <p className="text-xs text-gray-400">Ingresa tu NIT para ver fechas</p>
                                            </div>
                                        )}
                                    </div>

                                    {/* RETENCION WIDGET */}
                                    <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100/50">
                                        <div className="flex justify-between items-center mb-4">
                                            <h3 className="text-xs font-bold text-gray-600 uppercase tracking-widest flex items-center">
                                                <FaSearch className="mr-2" /> Buscar Retenciones
                                            </h3>
                                            <span className="text-[10px] px-2 py-0.5 bg-yellow-100 text-yellow-800 rounded-full font-bold">UVT: {formatCurrency(indicators.uvt)}</span>
                                        </div>

                                        <input
                                            type="text"
                                            placeholder="Ej: Honorarios, Servicios, Arrendamiento..."
                                            value={taxSearch}
                                            onChange={(e) => setTaxSearch(e.target.value)}
                                            className="w-full p-2 mb-3 bg-white border border-gray-200 rounded-lg text-xs focus:ring-2 focus:ring-indigo-100 outline-none transition-shadow"
                                        />

                                        <div className="space-y-2 max-h-[150px] overflow-hidden">
                                            {sidebarRetention.map((item, idx) => (
                                                <div key={idx} className="flex justify-between items-center p-2 hover:bg-gray-50 rounded border-b border-gray-50 transition-colors">
                                                    <div className="flex-1 pr-2">
                                                        <p className="text-xs font-medium text-gray-700 truncate" title={item.concepto}>{item.concepto}</p>
                                                        <p className="text-[10px] text-gray-400">Base: {item.base_uvt > 0 ? `${item.base_uvt} UVT` : '$0'}</p>
                                                    </div>
                                                    <div className="text-right">
                                                        <span className="block text-xs font-bold text-indigo-600">{item.tarifa}%</span>
                                                        <span className="block text-[9px] text-gray-400">{item.base_uvt > 0 ? formatCurrency(item.base_uvt * indicators.uvt) : '$0'}</span>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>

                                        <button
                                            onClick={() => setShowTaxModal(true)}
                                            className="w-full mt-3 py-2 text-xs font-bold text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-lg transition-colors flex justify-center items-center gap-2"
                                        >
                                            <FaExternalLinkAlt /> Ver Calendario y Tablas Completas
                                        </button>
                                    </div>
                                </div>
                            )}

                            {activeTab === 'financiero' && (
                                <div className="space-y-6 animate-fadeIn">
                                    <div className="bg-gradient-to-br from-green-50 to-emerald-100 p-6 rounded-xl border border-emerald-200 text-center relative overflow-hidden group">
                                        <FaMoneyBillWave className="absolute -right-4 -bottom-4 text-6xl text-emerald-200 opacity-50 transform rotate-12 transition-transform group-hover:scale-110" />
                                        <h3 className="text-sm font-bold text-emerald-800 uppercase mb-2">Dólar TRM Oficial (Hoy)</h3>
                                        <div className="text-4xl font-mono font-black text-emerald-700 tracking-tight">{formatCurrency(indicators.trm)}</div>
                                        <span className="text-[9px] text-emerald-600 block mt-2">Fuente: Datos Abiertos (SFC)</span>
                                    </div>
                                    <div className="bg-gradient-to-br from-blue-50 to-indigo-100 p-6 rounded-xl border border-blue-200 text-center relative overflow-hidden group">
                                        <FaCoins className="absolute -right-4 -bottom-4 text-6xl text-blue-200 opacity-50 transform rotate-12 transition-transform group-hover:scale-110" />
                                        <h3 className="text-sm font-bold text-blue-800 uppercase mb-2">Euro Hoy</h3>
                                        <div className="text-4xl font-mono font-black text-blue-700 tracking-tight">{formatCurrency(indicators.euro)}</div>
                                        <span className="text-[9px] text-blue-600 block mt-2">Fuente: Frankfurter (BCE)</span>
                                    </div>
                                    <div className="bg-gradient-to-br from-orange-50 to-red-50 p-6 rounded-xl border border-orange-200 text-center relative overflow-hidden group">
                                        <FaPercent className="absolute -right-4 -bottom-4 text-6xl text-orange-200 opacity-50 transform rotate-12 transition-transform group-hover:scale-110" />
                                        <h3 className="text-sm font-bold text-orange-800 uppercase mb-2">Tasa de Usura Mensual</h3>
                                        <div className="text-4xl font-mono font-black text-orange-700 tracking-tight">{indicators.tasa_usura || 0}%</div>
                                        <span className="text-[9px] text-orange-600 block mt-2">EA (Efectivo Anual) Modificable</span>
                                    </div>
                                </div>
                            )}

                            {isEditing && (
                                <div className="mt-8 border-t border-gray-200 pt-4 animate-slideInUp">
                                    <h4 className="font-bold text-gray-700 mb-3 text-sm flex items-center gap-2"><FaEdit /> Editar Variables Globales</h4>
                                    <div className="space-y-3">
                                        <div className="grid grid-cols-2 gap-2">
                                            <div>
                                                <label className="text-xs font-bold text-gray-500">TRM Manual</label>
                                                <input type="number" value={editValues.trm} onChange={(e) => setEditValues({ ...editValues, trm: Number(e.target.value) })} className="w-full p-2 border border-gray-300 rounded text-sm" />
                                            </div>
                                            <div>
                                                <label className="text-xs font-bold text-gray-500">Usura (%)</label>
                                                <input type="number" step="0.01" value={editValues.tasa_usura} onChange={(e) => setEditValues({ ...editValues, tasa_usura: Number(e.target.value) })} className="w-full p-2 border border-gray-300 rounded text-sm" />
                                            </div>
                                        </div>
                                        <div>
                                            <label className="text-xs font-bold text-gray-500">UVT {currentYear}</label>
                                            <input type="number" value={editValues.uvt} onChange={(e) => setEditValues({ ...editValues, uvt: Number(e.target.value) })} className="w-full p-2 border border-gray-300 rounded text-sm" />
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
                                <button onClick={handleSave} className="flex-1 py-2 bg-indigo-600 text-white rounded-lg text-sm font-bold hover:bg-indigo-700 flex justify-center items-center gap-2"><FaSave /> Guardar</button>
                            </div>
                        ) : (
                            <button onClick={startEditing} className="w-full py-2 border-2 border-gray-200 text-gray-500 rounded-lg text-xs font-bold hover:border-gray-300 hover:text-gray-700 uppercase tracking-wider transition-all">
                                Configurar Valores
                            </button>
                        )
                    )}
                </div>
            </div>

            {/* FULL SCREEN MODAL */}
            <TaxCalendarModal
                isOpen={showTaxModal}
                onClose={() => setShowTaxModal(false)}
                uvtValue={indicators.uvt}
            />
        </>
    );
}
