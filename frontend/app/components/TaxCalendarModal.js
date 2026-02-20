import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { FaTimes, FaCalendarAlt, FaTable, FaSearch, FaInfoCircle, FaCity } from 'react-icons/fa';
import { TAX_CONSTANTS_2026, RETENTION_CONCEPTS_2026, RETEICA_ARMENIA_CONCEPTS, calculateTaxBase } from '../utils/taxData2026';

const formatCurrency = (val) => {
    return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(val);
};

export default function TaxCalendarModal({ isOpen, onClose, uvtValue }) {
    const [activeTab, setActiveTab] = useState('retencion'); // 'calendario' | 'retencion' | 'reteica'
    const [searchTerm, setSearchTerm] = useState('');
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
        return () => setMounted(false);
    }, []);

    if (!isOpen || !mounted) return null;

    // Current UVT to use (from props or default constant)
    const currentUvt = uvtValue || TAX_CONSTANTS_2026.UVT;

    // Filter Logic based on active tab
    const getFilteredData = () => {
        const term = searchTerm.toLowerCase();
        if (activeTab === 'retencion') {
            return RETENTION_CONCEPTS_2026.filter(item => item.concepto.toLowerCase().includes(term));
        } else if (activeTab === 'reteica') {
            return RETEICA_ARMENIA_CONCEPTS.filter(item => item.concepto.toLowerCase().includes(term));
        }
        return [];
    };

    const displayData = getFilteredData();

    return createPortal(
        <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn">
            <div className="bg-white w-full max-w-5xl h-[90vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-scaleIn">

                {/* Header */}
                <div className="h-16 bg-slate-900 text-white flex items-center justify-between px-6 shrink-0">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-indigo-500 rounded-lg">
                            <FaCalendarAlt className="text-white" />
                        </div>
                        <div>
                            <h2 className="text-lg font-bold">Asistente Tributario 2026</h2>
                            <p className="text-xs text-gray-400">Normativa Vigente • Decreto 2229 de 2023</p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-white/10 rounded-full transition-colors text-gray-400 hover:text-white"
                    >
                        <FaTimes size={20} />
                    </button>
                </div>

                {/* Tabs */}
                <div className="flex border-b border-gray-200 bg-gray-50 shrink-0 overflow-x-auto">
                    <button
                        onClick={() => { setActiveTab('retencion'); setSearchTerm(''); }}
                        className={`px-6 py-4 text-sm font-bold flex items-center gap-2 border-b-2 transition-colors whitespace-nowrap ${activeTab === 'retencion' ? 'border-indigo-600 text-indigo-700 bg-white' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
                    >
                        <FaTable /> Tabla de Retención
                    </button>
                    <button
                        onClick={() => { setActiveTab('reteica'); setSearchTerm(''); }}
                        className={`px-6 py-4 text-sm font-bold flex items-center gap-2 border-b-2 transition-colors whitespace-nowrap ${activeTab === 'reteica' ? 'border-orange-500 text-orange-600 bg-white' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
                    >
                        <FaCity /> ReteICA Armenia
                    </button>
                    <button
                        onClick={() => setActiveTab('calendario')}
                        className={`px-6 py-4 text-sm font-bold flex items-center gap-2 border-b-2 transition-colors whitespace-nowrap ${activeTab === 'calendario' ? 'border-indigo-600 text-indigo-700 bg-white' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
                    >
                        <FaCalendarAlt /> Calendario Anual (Próximamente)
                    </button>
                </div>

                {/* Main Content */}
                <div className="flex-1 overflow-hidden bg-white p-6 relative">

                    {(activeTab === 'retencion' || activeTab === 'reteica') && (
                        <div className="flex flex-col h-full">
                            {/* Toolbar */}
                            <div className="flex flex-col md:flex-row justify-between items-center mb-6 gap-4 shrink-0">
                                <div className="relative w-full md:w-96">
                                    <FaSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                                    <input
                                        type="text"
                                        placeholder={activeTab === 'reteica' ? "Buscar actividad ICA..." : "Buscar concepto de retención..."}
                                        className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl bg-gray-50 focus:bg-white focus:ring-2 focus:ring-indigo-100 focus:border-indigo-500 transition-all outline-none text-sm"
                                        value={searchTerm}
                                        onChange={(e) => setSearchTerm(e.target.value)}
                                        autoFocus
                                    />
                                </div>

                                <div className={`flex items-center gap-3 px-4 py-2 rounded-lg border ${activeTab === 'reteica' ? 'bg-orange-50 border-orange-100' : 'bg-indigo-50 border-indigo-100'}`}>
                                    <FaInfoCircle className={activeTab === 'reteica' ? "text-orange-500" : "text-indigo-500"} />
                                    <span className={`text-xs font-medium ${activeTab === 'reteica' ? "text-orange-800" : "text-indigo-800"}`}>
                                        UVT Base 2026: <span className="font-bold font-mono text-base ml-1">{formatCurrency(currentUvt)}</span>
                                    </span>
                                </div>
                            </div>

                            {/* Table Container */}
                            <div className="flex-1 overflow-y-auto border border-gray-200 rounded-xl shadow-inner scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent">
                                <table className="w-full text-sm text-left">
                                    <thead className="text-xs text-gray-500 uppercase bg-gray-100 sticky top-0 z-10">
                                        <tr>
                                            <th className="px-6 py-4 font-bold tracking-wider">Concepto / Actividad</th>
                                            <th className="px-6 py-4 font-bold tracking-wider text-right">Base Mínima (UVT)</th>
                                            <th className="px-6 py-4 font-bold tracking-wider text-right">Base Pesos ($)</th>
                                            <th className="px-6 py-4 font-bold tracking-wider text-center">Tarifa %</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-100">
                                        {displayData.map((item, idx) => (
                                            <tr key={idx} className={`transition-colors group ${activeTab === 'reteica' ? 'hover:bg-orange-50/30' : 'hover:bg-indigo-50/30'}`}>
                                                <td className={`px-6 py-4 font-medium text-gray-800 ${activeTab === 'reteica' ? 'group-hover:text-orange-700' : 'group-hover:text-indigo-700'}`}>
                                                    {item.concepto}
                                                </td>
                                                <td className="px-6 py-4 text-right text-gray-500 font-mono">
                                                    {item.base_uvt > 0 ? `${item.base_uvt} UVT` : 'Desde $1'}
                                                </td>
                                                <td className="px-6 py-4 text-right text-gray-800 font-bold font-mono">
                                                    {item.base_uvt > 0 ? formatCurrency(item.base_uvt * currentUvt) : '$0'}
                                                </td>
                                                <td className="px-6 py-4 text-center">
                                                    <span className={`inline-flex items-center justify-center px-3 py-1 rounded-full font-bold text-xs ${activeTab === 'reteica' ? 'bg-orange-100 text-orange-700' : 'bg-indigo-100 text-indigo-700'}`}>
                                                        {activeTab === 'reteica'
                                                            ? `${item.tarifa_porcentaje}%`
                                                            : `${item.tarifa}%`
                                                        }
                                                    </span>
                                                </td>
                                            </tr>
                                        ))}
                                        {displayData.length === 0 && (
                                            <tr>
                                                <td colSpan="4" className="px-6 py-12 text-center text-gray-400">
                                                    No se encontraron resultados para "{searchTerm}"
                                                </td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {activeTab === 'calendario' && (
                        <div className="h-full flex flex-col items-center justify-center text-center p-10">
                            <div className="bg-gray-100 p-6 rounded-full mb-4">
                                <FaCalendarAlt className="text-4xl text-gray-400" />
                            </div>
                            <h3 className="text-xl font-bold text-gray-700 mb-2">Vista de Calendario Detallado</h3>
                            <p className="text-gray-500 max-w-md">
                                Estamos preparando una vista visual completa del calendario tributario anual.
                                Por ahora, utiliza el panel lateral para consultar tus próximas fechas de vencimiento personalizadas.
                            </p>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 flex justify-between items-center text-xs text-gray-500 shrink-0">
                    <span>* Los valores son proyectados y deben verificarse con el Estatuto Tributario vigente.</span>
                    <button
                        onClick={onClose}
                        className="px-6 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg font-bold transition-colors"
                    >
                        Cerrar Asistente
                    </button>
                </div>
            </div>
        </div>,
        document.body
    );
}
