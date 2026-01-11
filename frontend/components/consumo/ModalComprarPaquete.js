'use client';
import React, { useState, useEffect } from 'react';
import { apiService, getPrecioRegistroPublic } from '@/lib/apiService';
import { FaBolt, FaBoxOpen, FaCalculator } from 'react-icons/fa';
import { toast } from 'react-toastify';

export default function ModalComprarPaquete({ isOpen, onClose, onSuccess, month, year }) {
    const [activeTab, setActiveTab] = useState('paquetes'); // 'paquetes' | 'custom'
    const [paquetes, setPaquetes] = useState([]);
    const [selectedPaquete, setSelectedPaquete] = useState(null);

    // Custom Logic
    const [customQty, setCustomQty] = useState('');
    const [unitPrice, setUnitPrice] = useState(150);

    const [compraLoading, setCompraLoading] = useState(false);
    const [loadingData, setLoadingData] = useState(false);

    useEffect(() => {
        if (isOpen) {
            loadData();
            // Reset states
            setCustomQty('');
            setSelectedPaquete(null);
            setActiveTab('paquetes');
        }
    }, [isOpen]);

    const loadData = async () => {
        setLoadingData(true);
        try {
            const [resPkgs, resPrice] = await Promise.all([
                apiService.get('/consumo/paquetes'),
                getPrecioRegistroPublic()
            ]);
            setPaquetes(resPkgs.data);
            setUnitPrice(resPrice.data.precio);
        } catch (error) {
            console.error(error);
            // toast.error("Error cargando opciones."); // Silenciar para no molestar si falla algo menor
        } finally {
            setLoadingData(false);
        }
    };

    const handleComprar = async () => {
        let payload = { mes: month, anio: year };

        if (activeTab === 'paquetes') {
            if (!selectedPaquete) return;
            payload.paquete_id = selectedPaquete.id;
        } else {
            const qty = parseInt(customQty);
            if (!qty || qty <= 0) {
                toast.warning("Ingrese una cantidad válida.");
                return;
            }
            payload.cantidad_custom = qty;
        }

        setCompraLoading(true);
        try {
            await apiService.post('/consumo/recargas', payload);
            toast.success("¡Recarga exitosa! Su cupo ha sido actualizado.");
            onClose();
            if (onSuccess) onSuccess();
        } catch (error) {
            console.error(error);
            toast.error(error.response?.data?.detail || "Error al procesar la compra.");
        } finally {
            setCompraLoading(false);
        }
    };

    const fmtMoney = (val) => new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(val);

    const getMonthName = (m) => {
        if (!m) return "";
        const date = new Date();
        date.setMonth(m - 1);
        return date.toLocaleString('es-CO', { month: 'long' });
    };

    // Cálculos para custom
    const customTotal = (parseInt(customQty) || 0) * unitPrice;

    if (!isOpen) return null;

    return (
        <div className="modal modal-open z-50 bg-black/60 backdrop-blur-sm">
            <div className="modal-box relative max-w-lg bg-white p-0 overflow-hidden rounded-2xl shadow-2xl">
                {/* Header */}
                <div className="bg-gray-50 p-5 border-b">
                    <button onClick={onClose} className="btn btn-sm btn-circle btn-ghost absolute right-3 top-3 text-gray-400">✕</button>
                    <h3 className="text-xl font-bold flex items-center gap-2 text-gray-800">
                        <FaBolt className="text-amber-500" /> Recargar Cupo
                    </h3>
                    <p className="text-xs text-gray-500 mt-1">
                        {month && year ? (
                            <span>Aplicando para: <strong className="text-gray-700 uppercase">{getMonthName(month)} {year}</strong></span>
                        ) : 'Aumenta tu límite de registros disponibles.'}
                    </p>
                </div>

                {/* Tabs */}
                <div className="flex border-b bg-gray-50/50">
                    <button
                        className={`flex-1 py-3 text-sm font-bold flex justify-center items-center gap-2 transition-colors ${activeTab === 'paquetes' ? 'text-indigo-600 border-b-2 border-indigo-600 bg-white' : 'text-gray-500 hover:bg-gray-100'}`}
                        onClick={() => setActiveTab('paquetes')}
                    >
                        <FaBoxOpen /> Paquetes
                    </button>
                    <button
                        className={`flex-1 py-3 text-sm font-bold flex justify-center items-center gap-2 transition-colors ${activeTab === 'custom' ? 'text-indigo-600 border-b-2 border-indigo-600 bg-white' : 'text-gray-500 hover:bg-gray-100'}`}
                        onClick={() => setActiveTab('custom')}
                    >
                        <FaCalculator /> A la Medida
                    </button>
                </div>

                <div className="p-6 bg-white min-h-[300px]">
                    {loadingData ? (
                        <div className="flex justify-center items-center h-48"><span className="loading loading-dots loading-lg text-amber-500"></span></div>
                    ) : (
                        <>
                            {/* VISTA PAQUETES */}
                            {activeTab === 'paquetes' && (
                                <div className="grid grid-cols-1 gap-3 max-h-80 overflow-y-auto pr-1">
                                    {paquetes.length === 0 ? (
                                        <div className="text-center py-10 text-gray-400 italic">No hay paquetes predefinidos.</div>
                                    ) : (
                                        paquetes.map(pkg => (
                                            <div
                                                key={pkg.id}
                                                onClick={() => setSelectedPaquete(pkg)}
                                                className={`p-4 rounded-xl border-2 cursor-pointer transition-all flex justify-between items-center group ${selectedPaquete?.id === pkg.id ? 'border-indigo-500 bg-indigo-50 shadow-sm' : 'border-gray-100 hover:border-indigo-200 hover:shadow-sm'}`}
                                            >
                                                <div>
                                                    <h4 className={`font-bold ${selectedPaquete?.id === pkg.id ? 'text-indigo-900' : 'text-gray-700'}`}>{pkg.nombre}</h4>
                                                    <p className="text-xs text-gray-500 font-medium">+{pkg.cantidad_registros || pkg.cantidad} registros</p>
                                                </div>
                                                <div className="text-right">
                                                    <span className="block font-bold text-lg text-gray-800">{fmtMoney(pkg.precio)}</span>
                                                </div>
                                            </div>
                                        ))
                                    )}
                                </div>
                            )}

                            {/* VISTA CUSTOM */}
                            {activeTab === 'custom' && (
                                <div className="animate-fadeIn">
                                    <div className="bg-amber-50 rounded-xl p-5 border border-amber-100 mb-6">
                                        <label className="label-text text-xs font-bold text-amber-800 uppercase mb-2 block">¿Cuántos registros necesitas?</label>
                                        <div className="flex items-center gap-2">
                                            <input
                                                type="number"
                                                autoFocus
                                                value={customQty}
                                                onChange={e => setCustomQty(e.target.value)}
                                                className="input input-lg input-bordered w-full text-center font-mono text-2xl font-bold text-gray-800 focus:border-amber-500 focus:ring-2 focus:ring-amber-200"
                                                placeholder="0"
                                            />
                                        </div>
                                        <p className="text-right text-xs text-amber-600 mt-2 font-medium">
                                            Tarifa: {fmtMoney(unitPrice)} / registro
                                        </p>
                                    </div>

                                    <div className="flex justify-between items-end border-t border-dashed border-gray-200 pt-4">
                                        <span className="text-gray-500 text-sm font-medium">Total a Pagar:</span>
                                        <span className="text-3xl font-bold text-indigo-700">{fmtMoney(customTotal)}</span>
                                    </div>
                                </div>
                            )}
                        </>
                    )}
                </div>

                <div className="modal-action bg-gray-50 p-4 m-0 flex justify-between items-center border-t">
                    <button onClick={onClose} className="btn btn-ghost text-gray-500 hover:bg-gray-200">Cancelar</button>
                    <button
                        onClick={handleComprar}
                        disabled={loadingData || compraLoading || (activeTab === 'paquetes' && !selectedPaquete) || (activeTab === 'custom' && (!customQty || customQty <= 0))}
                        className="btn px-8 bg-gray-200 hover:bg-gray-300 text-gray-900 font-bold shadow-lg border-none"
                    >
                        {compraLoading ? <span className="loading loading-spinner text-gray-900"></span> : (activeTab === 'custom' ? 'Comprar Ahora' : 'Confirmar Paquete')}
                    </button>
                </div>
            </div>
        </div>
    );
}
