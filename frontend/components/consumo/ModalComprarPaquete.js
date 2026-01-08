'use client';
import React, { useState, useEffect } from 'react';
import { apiService } from '@/lib/apiService';
import { FaBolt } from 'react-icons/fa';
import { toast } from 'react-toastify';

export default function ModalComprarPaquete({ isOpen, onClose, onSuccess }) {
    const [paquetes, setPaquetes] = useState([]);
    const [selectedPaquete, setSelectedPaquete] = useState(null);
    const [compraLoading, setCompraLoading] = useState(false);
    const [loadingPaquetes, setLoadingPaquetes] = useState(false);

    useEffect(() => {
        if (isOpen) {
            cargarPaquetes();
        }
    }, [isOpen]);

    const cargarPaquetes = async () => {
        setLoadingPaquetes(true);
        try {
            const res = await apiService.get('/consumo/paquetes');
            setPaquetes(res.data);
        } catch (error) {
            console.error(error);
            toast.error("Error al cargar los paquetes de recarga.");
        } finally {
            setLoadingPaquetes(false);
        }
    };

    const handleComprar = async () => {
        if (!selectedPaquete) return;

        setCompraLoading(true);
        try {
            await apiService.post('/consumo/recargas', { paquete_id: selectedPaquete.id });
            toast.success("¡Recarga exitosa! Su cupo ha sido actualizado.");
            onClose();
            if (onSuccess) onSuccess();
        } catch (error) {
            console.error(error);
            toast.error("Error al procesar la compra. Intente nuevamente.");
        } finally {
            setCompraLoading(false);
        }
    };

    const fmtMoney = (val) => new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(val);

    if (!isOpen) return null;

    return (
        <div className="modal modal-open z-50">
            <div className="modal-box relative max-w-lg">
                <button onClick={onClose} className="btn btn-sm btn-circle absolute right-2 top-2">✕</button>
                <h3 className="text-lg font-bold flex items-center gap-2">
                    <FaBolt className="text-amber-500" /> Comprar Recarga Adicional
                </h3>
                <p className="py-4 text-sm text-gray-500">
                    Seleccione un paquete para aumentar su cupo inmediatamente.
                </p>

                {loadingPaquetes ? (
                    <div className="py-10 text-center"><span className="loading loading-dots loading-lg text-amber-500"></span></div>
                ) : (
                    <div className="grid grid-cols-1 gap-4 mb-6 max-h-96 overflow-y-auto">
                        {paquetes.length === 0 ? (
                            <div className="text-center py-4 text-gray-400">No hay paquetes disponibles en este momento.</div>
                        ) : (
                            paquetes.map(pkg => (
                                <div
                                    key={pkg.id}
                                    onClick={() => setSelectedPaquete(pkg)}
                                    className={`p-4 rounded-xl border-2 cursor-pointer transition-all flex justify-between items-center ${selectedPaquete?.id === pkg.id ? 'border-amber-500 bg-amber-50' : 'border-gray-100 hover:border-amber-200'}`}
                                >
                                    <div>
                                        <h4 className="font-bold text-gray-800">{pkg.nombre}</h4>
                                        <p className="text-xs text-gray-500">+{pkg.cantidad_registros || pkg.cantidad} registros</p>
                                    </div>
                                    <div className="text-right">
                                        <span className="block font-bold text-lg text-indigo-600">{fmtMoney(pkg.precio)}</span>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                )}

                <div className="modal-action">
                    <button onClick={onClose} className="btn btn-ghost">Cancelar</button>
                    <button
                        onClick={handleComprar}
                        disabled={!selectedPaquete || compraLoading}
                        className="btn btn-warning text-white font-bold"
                    >
                        {compraLoading ? <span className="loading loading-spinner"></span> : 'Confirmar Compra'}
                    </button>
                </div>
            </div>
        </div>
    );
}
