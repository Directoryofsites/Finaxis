'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import Script from 'next/script';
import { useAuth } from '../../../context/AuthContext';

import { phService } from '../../../../lib/phService';
import { FaFilePdf, FaBuilding, FaUser, FaMoneyBillWave, FaSearch, FaHistory } from 'react-icons/fa';

// Estilos
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none";
const cardClass = "bg-white p-6 rounded-xl shadow-sm border border-gray-100";

export default function EstadoCuentaPage() {
    const { user, loading: authLoading } = useAuth();
    const [loading, setLoading] = useState(false);
    const [unidades, setUnidades] = useState([]);
    const [selectedUnidad, setSelectedUnidad] = useState('');
    const [reporte, setReporte] = useState(null);
    const [error, setError] = useState(null);

    // Cargar Lista de Unidades
    useEffect(() => {
        if (!authLoading && user?.empresaId) {
            phService.getUnidades().then(setUnidades).catch(console.error);
        }
    }, [user, authLoading]);

    // Generar Reporte
    const handleGenerar = async () => {
        if (!selectedUnidad) return;
        setLoading(true);
        setError(null);
        setReporte(null);
        try {
            const data = await phService.getHistorialCuenta(selectedUnidad);
            setReporte(data);
        } catch (err) {
            setError("No se pudo generar el estado de cuenta.");
        } finally {
            setLoading(false);
        }
    };

    // Exportar PDF
    const handleExportPDF = () => {
        if (!reporte || !window.jspdf) return;
        const doc = new window.jspdf.jsPDF();

        // Encabezado
        doc.setFontSize(16);
        doc.setTextColor(40);
        doc.text("ESTADO DE CUENTA - PROPIEDAD HORIZONTAL", 14, 20);

        doc.setFontSize(10);
        doc.setTextColor(100);
        doc.text(`Generado el: ${new Date().toLocaleString()}`, 14, 28);

        // Info Unidad / Propietario
        doc.setDrawColor(200);
        doc.line(14, 32, 196, 32);

        doc.setFontSize(11);
        doc.setTextColor(0);
        doc.text(`Unidad: ${reporte.unidad.codigo}`, 14, 40);
        doc.text(`Tipo: ${reporte.unidad.tipo}`, 80, 40);
        doc.text(`Propietario: ${reporte.propietario ? reporte.propietario.razon_social : 'Sin Asignar'}`, 14, 46);
        doc.text(`NIT/CC: ${reporte.propietario ? reporte.propietario.nit : ''}`, 14, 52);

        // Tabla
        const tableColumn = ["Fecha", "Documento", "Tipo", "Detalle", "Cargo", "Abono", "Saldo"];
        const tableRows = reporte.transacciones.map(t => [
            t.fecha,
            t.documento,
            t.tipo,
            t.detalle,
            t.cargo ? `$${parseFloat(t.cargo).toLocaleString()}` : '-',
            t.abono ? `$${parseFloat(t.abono).toLocaleString()}` : '-',
            `$${parseFloat(t.saldo).toLocaleString()}`
        ]);

        doc.autoTable({
            head: [tableColumn],
            body: tableRows,
            startY: 60,
            theme: 'grid',
            headStyles: { fillColor: [63, 81, 181] },
            columnStyles: {
                4: { halign: 'right' },
                5: { halign: 'right' },
                6: { halign: 'right', fontStyle: 'bold' }
            }
        });

        // Total
        const finalY = doc.lastAutoTable.finalY + 10;
        doc.setFontSize(12);
        doc.text(`Saldo Total a Pagar: $${parseFloat(reporte.saldo_actual).toLocaleString()}`, 14, finalY);

        doc.save(`estado_cuenta_${reporte.unidad.codigo}.pdf`);
    };

    if (authLoading) return <div className="p-10 text-center">Cargando...</div>;

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
            {/* Scripts PDF */}
            <Script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js" strategy="afterInteractive" />
            <Script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.5.28/jspdf.plugin.autotable.min.js" strategy="afterInteractive" />

            <div className="max-w-5xl mx-auto">
                {/* HEADER */}
                <div className="mb-8">
                    <div className="flex items-center gap-3 mt-3">
                        <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                            <FaHistory className="text-2xl" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold text-gray-800">Estado de Cuenta</h1>
                            <p className="text-gray-500 text-sm">Consulta de movimientos y saldos por unidad.</p>
                        </div>
                    </div>
                </div>

                {/* FILTRO */}
                <div className={cardClass + " mb-6"}>
                    <form onSubmit={(e) => { e.preventDefault(); handleGenerar(); }} className="flex flex-col md:flex-row gap-4 items-end">
                        <div className="flex-1">
                            <label className={labelClass}>Seleccione Unidad</label>
                            <select
                                className={inputClass}
                                value={selectedUnidad}
                                onChange={(e) => setSelectedUnidad(e.target.value)}
                            >
                                <option value="">-- Seleccionar Unidad --</option>
                                {unidades.map(u => (
                                    <option key={u.id} value={u.id}>{u.codigo} - {u.propietario_nombre || 'Sin Asignar'} {u.torre ? `(${u.torre.nombre})` : ''}</option>
                                ))}
                            </select>
                        </div>
                        <button
                            type="submit"
                            disabled={!selectedUnidad || loading}
                            className="bg-indigo-600 text-white px-6 py-2 rounded-lg font-bold hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2 h-10"
                        >
                            {loading ? 'Generando...' : <><FaSearch /> Consultar</>}
                        </button>
                    </form>
                </div>

                {error && <div className="bg-red-100 text-red-700 p-4 rounded-lg mb-6 border-l-4 border-red-500">{error}</div>}

                {/* REPORTE */}
                {reporte && (
                    <div className="animate-fadeIn space-y-6">

                        {/* INFO TARJETA */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div className="bg-white p-6 rounded-xl shadow-sm border-l-4 border-indigo-500">
                                <p className="text-xs text-gray-400 font-bold uppercase">Unidad</p>
                                <p className="text-2xl font-bold text-gray-800">{reporte.unidad.codigo}</p>
                                <p className="text-sm text-gray-500">{reporte.unidad.tipo}</p>
                            </div>
                            <div className="bg-white p-6 rounded-xl shadow-sm border-l-4 border-blue-500">
                                <p className="text-xs text-gray-400 font-bold uppercase">Propietario</p>
                                <p className="text-lg font-bold text-gray-800 truncate">{reporte.propietario ? reporte.propietario.razon_social : 'Sin Asignar'}</p>
                                <p className="text-sm text-gray-500">{reporte.propietario ? `NIT: ${reporte.propietario.nit}` : ''}</p>
                            </div>
                            <div className="bg-white p-6 rounded-xl shadow-sm border-l-4 border-green-500">
                                <p className="text-xs text-gray-400 font-bold uppercase">Saldo Actual</p>
                                <p className={`text-2xl font-bold ${reporte.saldo_actual > 0 ? 'text-red-600' : 'text-green-600'}`}>
                                    ${parseFloat(reporte.saldo_actual).toLocaleString()}
                                </p>
                                <p className="text-xs text-gray-400">Total a la fecha</p>
                            </div>
                        </div>

                        {/* TABLA MOVIMIENTOS */}
                        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                            <div className="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
                                <h3 className="font-bold text-gray-700">Historial de Transacciones</h3>
                                <button onClick={handleExportPDF} className="bg-red-600 text-white px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2 hover:bg-red-700 shadow-sm">
                                    <FaFilePdf /> Descargar PDF
                                </button>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="min-w-full divide-y divide-gray-200">
                                    <thead className="bg-gray-50">
                                        <tr>
                                            <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Fecha</th>
                                            <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Documento</th>
                                            <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Detalle</th>
                                            <th className="px-6 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider">Cargo</th>
                                            <th className="px-6 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider">Abono</th>
                                            <th className="px-6 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider">Saldo</th>
                                        </tr>
                                    </thead>
                                    <tbody className="bg-white divide-y divide-gray-200">
                                        {reporte.transacciones.length > 0 ? (
                                            reporte.transacciones.map((t, idx) => (
                                                <tr key={idx} className="hover:bg-gray-50">
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{t.fecha}</td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-indigo-600">{t.documento}</td>
                                                    <td className="px-6 py-4 text-sm text-gray-500 truncate max-w-xs" title={t.detalle}>{t.detalle}</td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-800 text-right">{t.cargo > 0 ? `$${parseFloat(t.cargo).toLocaleString()}` : '-'}</td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600 font-bold text-right">{t.abono > 0 ? `$${parseFloat(t.abono).toLocaleString()}` : '-'}</td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900 text-right">${parseFloat(t.saldo).toLocaleString()}</td>
                                                </tr>
                                            ))
                                        ) : (
                                            <tr>
                                                <td colSpan="6" className="px-6 py-10 text-center text-gray-400 italic">No hay movimientos registrados.</td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                    </div>
                )}
            </div>
        </div>
    );
}
