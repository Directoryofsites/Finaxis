import React from 'react';
import { formatCurrency } from '../../../utils/format';
import { FaCheckCircle, FaExclamationTriangle, FaTimesCircle } from 'react-icons/fa';

export default function BatchPreviewTable({ previewData }) {
    if (!previewData || !previewData.detalles) return null;

    return (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden mt-6">
            <div className="p-4 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
                <h3 className="font-bold text-gray-700">Vista Previa de Conciliación</h3>
                <div className="flex gap-4 text-sm">
                    <span className="flex items-center gap-1 text-green-600 font-medium">
                        <FaCheckCircle /> {previewData.filas_validas} Listos
                    </span>
                    <span className="flex items-center gap-1 text-red-500 font-medium">
                        <FaTimesCircle /> {previewData.filas_error} Errores
                    </span>
                    <span className="font-bold text-gray-800">
                        Total: {formatCurrency(previewData.total_recaudado)}
                    </span>
                </div>
            </div>
            
            <div className="overflow-x-auto max-h-[500px]">
                <table className="w-full text-left border-collapse text-sm">
                    <thead className="bg-gray-100 text-gray-600 sticky top-0 z-10 shadow-sm">
                        <tr>
                            <th className="py-3 px-4 border-b">Línea</th>
                            <th className="py-3 px-4 border-b">Ref. Banco</th>
                            <th className="py-3 px-4 border-b">Unidad</th>
                            <th className="py-3 px-4 border-b">Fecha Pago</th>
                            <th className="py-3 px-4 border-b text-right">Recibido</th>
                            <th className="py-3 px-4 border-b text-right">Deuda Act.</th>
                            <th className="py-3 px-4 border-b">Estado / Anticipo</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {previewData.detalles.map((fila, idx) => (
                            <tr key={idx} className={`hover:bg-gray-50 transition-colors ${!fila.is_valid ? 'bg-red-50' : ''}`}>
                                <td className="py-3 px-4 text-gray-500">{fila.line_number}</td>
                                <td className="py-3 px-4 font-mono text-xs">{fila.referencia}</td>
                                <td className="py-3 px-4 font-bold text-indigo-600">{fila.unidad_codigo || '-'}</td>
                                <td className="py-3 px-4">{fila.fecha_pago}</td>
                                <td className="py-3 px-4 text-right font-medium text-green-600">{formatCurrency(fila.monto_recibido)}</td>
                                <td className="py-3 px-4 text-right text-gray-600">{formatCurrency(fila.deuda_total)}</td>
                                <td className="py-3 px-4">
                                    {fila.is_valid ? (
                                        <div className="flex flex-col">
                                            <span className="inline-flex items-center gap-1 text-xs px-2 py-1 bg-green-100 text-green-700 rounded-full font-medium w-fit">
                                                <FaCheckCircle /> OK
                                            </span>
                                            {fila.excedente_anticipo > 0 && (
                                                <span className="inline-flex items-center gap-1 text-[10px] text-yellow-600 mt-1 font-bold">
                                                    <FaExclamationTriangle /> Anticipo: {formatCurrency(fila.excedente_anticipo)}
                                                </span>
                                            )}
                                        </div>
                                    ) : (
                                        <span className="inline-flex items-center gap-1 text-xs text-red-600 font-medium">
                                            <FaTimesCircle /> {fila.error_msg}
                                        </span>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
