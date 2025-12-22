import React from 'react';
import { FaFileInvoice, FaCalendarAlt, FaUser, FaHashtag, FaAlignLeft, FaMoneyBillWave, FaTags, FaUniversity } from 'react-icons/fa';

const formatCurrency = (value) => {
    if (value === null || value === undefined || isNaN(value)) return '$ 0';
    return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(value);
};

const VerticalTransactionCard = ({ item }) => {
    // Detectar si es un movimiento Débito o Crédito principal
    const isDebito = item.debito > 0;
    const monto = isDebito ? item.debito : item.credito;
    const colorMonto = isDebito ? 'text-green-600' : 'text-red-600'; // Débito Green (Entrada/Activo), Crédito Red (Salida/Pasivo) - Convención visual simple

    return (
        <div className={`bg-white rounded-xl shadow-md border-l-4 p-5 hover:shadow-lg transition-all ${isDebito ? 'border-green-500' : 'border-red-500'}`}>

            {/* HEADER: Documento y Fecha */}
            <div className="flex justify-between items-start mb-4 border-b border-gray-100 pb-3">
                <div className="flex items-center gap-3">
                    <div className={`p-3 rounded-full ${isDebito ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'}`}>
                        <FaFileInvoice className="text-xl" />
                    </div>
                    <div>
                        <h3 className="font-bold text-gray-800 text-lg flex items-center gap-2">
                            {item.tipo_documento_nombre || item.tipo_documento_codigo}
                            <span className="text-gray-400">#</span>{item.numero}
                        </h3>
                        <div className="flex items-center text-xs text-gray-500 font-medium mt-1 gap-4">
                            <span className="flex items-center gap-1"><FaCalendarAlt /> {new Date(item.fecha).toLocaleDateString()}</span>
                            {item.estado === 'ANULADO' && <span className="text-xs font-bold text-red-100 bg-red-500 px-2 py-0.5 rounded-full">ANULADO</span>}
                        </div>
                    </div>
                </div>
                <div className={`text-xl font-bold font-mono ${colorMonto}`}>
                    {formatCurrency(monto)}
                </div>
            </div>

            {/* BODY: Detalles Verticales */}
            <div className="space-y-3">

                {/* Tercero */}
                <div className="flex gap-3 items-start">
                    <FaUser className="mt-1 text-gray-400 shrink-0" />
                    <div>
                        <p className="text-xs font-bold text-gray-400 uppercase">Tercero / Beneficiario</p>
                        <p className="text-sm font-semibold text-gray-700">{item.tercero_nombre || 'N/A'}</p>
                        <p className="text-xs text-gray-500 font-mono">NIT: {item.tercero_identificacion || 'N/A'}</p>
                    </div>
                </div>

                {/* Cuenta */}
                <div className="flex gap-3 items-start">
                    <FaUniversity className="mt-1 text-gray-400 shrink-0" />
                    <div>
                        <p className="text-xs font-bold text-gray-400 uppercase">Cuenta Contable</p>
                        <p className="text-sm font-semibold text-indigo-700 font-mono">{item.cuenta_codigo}</p>
                        <p className="text-xs text-gray-600">{item.cuenta_nombre}</p>
                    </div>
                </div>

                {/* Concepto */}
                <div className="flex gap-3 items-start bg-gray-50 p-3 rounded-lg">
                    <FaAlignLeft className="mt-1 text-gray-400 shrink-0" />
                    <div>
                        <p className="text-xs font-bold text-gray-400 uppercase">Detalle / Concepto</p>
                        <p className="text-sm text-gray-700 italic">"{item.concepto || item.detalle || 'Sin concepto'}"</p>
                    </div>
                </div>

                {/* Footer info extra */}
                {item.centro_costo_nombre && (
                    <div className="flex gap-2 items-center text-xs text-gray-400 pt-2">
                        <FaTags /> CC: {item.centro_costo_nombre}
                    </div>
                )}

            </div>
        </div>
    );
};

export default VerticalTransactionCard;
