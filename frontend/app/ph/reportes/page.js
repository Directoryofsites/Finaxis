'use client';

import React, { useState, useEffect } from 'react';
// import axios from 'axios'; // REMOVED raw axios
import BotonRegresar from '../../components/BotonRegresar';
import { FaCalendarAlt, FaFilter, FaSearch, FaFileExcel, FaUsers, FaBuilding, FaMoneyBillWave } from 'react-icons/fa';
import AutocompleteInput from '../../components/AutocompleteInput';
import { phService } from '../../../lib/phService'; // IMPORT phService
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';

export default function ReportesPHPage() {
    // Estado de Filtros
    const [fechaDesde, setFechaDesde] = useState('');
    const [fechaHasta, setFechaHasta] = useState('');
    const [unidad, setUnidad] = useState(null); // { id, codigo, ... }
    const [propietario, setPropietario] = useState(null); // { id, razon_social, ... }
    const [concepto, setConcepto] = useState(''); // ID del concepto PH
    const [tipoDoc, setTipoDoc] = useState('');
    const [numeroDoc, setNumeroDoc] = useState('');

    // Listas para Selects
    const [unidades, setUnidades] = useState([]);
    const [propietarios, setPropietarios] = useState([]);
    const [conceptos, setConceptos] = useState([]);

    // Resultados
    const [reporte, setReporte] = useState([]);
    const [loading, setLoading] = useState(false);
    const [totales, setTotales] = useState({ debito: 0, credito: 0, saldo: 0 });

    useEffect(() => {
        cargarMaestros();
    }, []);

    const cargarMaestros = async () => {
        console.log("--- [LOG ESPIA] INICIANDO CARGA DE MAESTROS ---");
        try {
            // Cargar Unidades
            console.log("--- [LOG ESPIA] Cargando Unidades... ---");
            const dataUnidades = await phService.getUnidades({ limit: 1000 });
            console.log(`--- [LOG ESPIA] Unidades cargadas: ${dataUnidades.length} ---`);
            setUnidades(dataUnidades);

            // Cargar Propietarios
            console.log("--- [LOG ESPIA] Cargando Propietarios... ---");
            const dataPropietarios = await phService.getPropietarios();
            console.log(`--- [LOG ESPIA] Propietarios cargados: ${dataPropietarios.length} ---`);
            setPropietarios(dataPropietarios);

            // Cargar Conceptos PH
            console.log("--- [LOG ESPIA] Cargando Conceptos... ---");
            const dataConceptos = await phService.getConceptos();
            console.log(`--- [LOG ESPIA] Conceptos cargados: ${dataConceptos.length} ---`);
            setConceptos(dataConceptos);

        } catch (error) {
            console.error("--- [LOG ESPIA] ERROR CRITICO EN CARGA DE MAESTROS ---", error);
            // Si el error es 401, probablemente apiService maneja redirección o el hook de auth
        }
    };

    const generarReporte = async () => {
        console.log("--- [LOG ESPIA] GENERANDO REPORTE ---");
        setLoading(true);
        try {
            const params = {
                fecha_desde: fechaDesde || undefined,
                fecha_hasta: fechaHasta || undefined,
                unidad_id: unidad?.id,
                propietario_id: propietario?.tercero_id,
                concepto_id: concepto || undefined,
                numero_doc: numeroDoc || undefined
            };
            console.log("--- [LOG ESPIA] Parámetros enviados:", params);

            const data = await phService.getReporteMovimientos(params);
            console.log(`--- [LOG ESPIA] Datos recibidos: ${data.length} registros ---`);
            setReporte(data);

            // Calcular Totales
            const totalDebito = data.reduce((acc, row) => acc + row.debito, 0);
            const totalCredito = data.reduce((acc, row) => acc + row.credito, 0);
            setTotales({
                debito: totalDebito,
                credito: totalCredito,
                saldo: totalDebito - totalCredito
            });

        } catch (error) {
            console.error("--- [LOG ESPIA] ERROR GENERANDO REPORTE ---", error);
            alert("Error al generar el reporte. Verifique los filtros.");
        } finally {
            setLoading(false);
        }
    };

    const limpiarFiltros = () => {
        setFechaDesde('');
        setFechaHasta('');
        setUnidad(null);
        setPropietario(null);
        setConcepto('');
        setNumeroDoc('');
        setReporte([]);
        setTotales({ debito: 0, credito: 0, saldo: 0 });
    };

    // --- PDF EXPORT FUNCTION ---
    const handleExportPDF = () => {
        try {
            const doc = new jsPDF();

            // Header
            doc.setFontSize(18);
            doc.setTextColor(40);
            doc.text("Reporte de Movimientos - Propiedad Horizontal", 14, 22);
            doc.setFontSize(10);
            doc.setTextColor(100);
            doc.text(`Generado el: ${new Date().toLocaleDateString()}`, 14, 28);

            if (fechaDesde && fechaHasta) {
                doc.text(`Periodo: ${fechaDesde} al ${fechaHasta}`, 14, 34);
            }

            // Totales Header
            doc.setFontSize(10);
            doc.setTextColor(0);
            doc.text(`Total Débito: ${formatCurrency(totales.debito)}`, 14, 42);
            doc.text(`Total Crédito: ${formatCurrency(totales.credito)}`, 80, 42);
            doc.text(`Saldo: ${formatCurrency(totales.saldo)}`, 150, 42);

            // Table Data
            const tableColumn = ["Fecha", "Doc", "Nro", "Unidad", "Propietario", "Detalle", "Débito", "Crédito"];
            const tableRows = reporte.map(row => [
                row.fecha,
                row.tipo_doc,
                row.numero,
                row.unidad,
                row.propietario,
                row.detalle || row.observaciones || '',
                formatCurrency(row.debito),
                formatCurrency(row.credito)
            ]);

            // AutoTable
            autoTable(doc, {
                head: [tableColumn],
                body: tableRows,
                startY: 48,
                theme: 'grid',
                headStyles: { fillColor: [65, 105, 225] },
                styles: { fontSize: 8 },
                columnStyles: {
                    0: { cellWidth: 20 }, // Fecha
                    1: { cellWidth: 15 }, // Doc
                    2: { cellWidth: 15 }, // Nro
                    5: { cellWidth: 'auto' }, // Detalle gets remaining width
                    6: { halign: 'right' },
                    7: { halign: 'right' }
                }
            });

            doc.save(`reporte_ph_${new Date().toISOString().slice(0, 10)}.pdf`);
        } catch (error) {
            console.error("Error exporting PDF:", error);
            alert("Error al generar el PDF.");
        }
    };

    // Formateador de Moneda
    const formatCurrency = (val) => {
        return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(val);
    };

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans text-sm">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-6 flex justify-between items-center">
                    <div>
                        <BotonRegresar href="/ph" />
                        <h1 className="text-2xl font-bold text-gray-800 mt-2 flex items-center gap-2">
                            <FaFilter className="text-blue-600" />
                            Reportes Propiedad Horizontal
                        </h1>
                        <p className="text-gray-500">Consulta detallada de movimientos por Unidad, Propietario y Concepto.</p>
                    </div>
                </div>

                {/* Filtros */}
                <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100 mb-6">
                    <div className="flex items-center gap-2 mb-4 text-blue-800 font-semibold border-b pb-2">
                        <FaSearch /> Filtros de Búsqueda
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        {/* Rango de Fechas */}
                        <div>
                            <label className="block text-gray-600 mb-1 font-medium">Desde</label>
                            <input
                                type="date"
                                className="w-full border rounded-lg p-2 focus:ring-2 focus:ring-blue-100 outline-none transition-all"
                                value={fechaDesde}
                                onChange={(e) => setFechaDesde(e.target.value)}
                            />
                        </div>
                        <div>
                            <label className="block text-gray-600 mb-1 font-medium">Hasta</label>
                            <input
                                type="date"
                                className="w-full border rounded-lg p-2 focus:ring-2 focus:ring-blue-100 outline-none transition-all"
                                value={fechaHasta}
                                onChange={(e) => setFechaHasta(e.target.value)}
                            />
                        </div>

                        {/* Unidad y Propietario (Autocompletes) */}
                        <div className="z-20">
                            <label className="block text-gray-600 mb-1 font-medium">Unidad Privada</label>
                            <AutocompleteInput
                                items={unidades}
                                value={unidad?.codigo || ''}
                                onChange={(item) => setUnidad(item)}
                                placeholder="Buscar Apto/Local..."
                                searchKey="codigo"
                                displayKey="codigo"
                            />
                        </div>
                        <div className="z-10">
                            <label className="block text-gray-600 mb-1 font-medium">Propietario</label>
                            {/* Ajustar si 'propietarios' tiene una estructura compleja */}
                            <AutocompleteInput
                                items={propietarios}
                                value={propietario?.razon_social || ''}
                                onChange={(item) => setPropietario(item)}
                                placeholder="Buscar Propietario..."
                                searchKey="razon_social"
                                displayKey="razon_social"
                            />
                        </div>

                        {/* Concepto y Documento */}
                        <div>
                            <label className="block text-gray-600 mb-1 font-medium">Concepto de Cobro</label>
                            <select
                                className="w-full border rounded-lg p-2 bg-white"
                                value={concepto}
                                onChange={(e) => setConcepto(e.target.value)}
                            >
                                <option value="">-- Todos --</option>
                                {conceptos.map(c => (
                                    <option key={c.id} value={c.id}>{c.nombre}</option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className="block text-gray-600 mb-1 font-medium">Nro. Documento</label>
                            <input
                                type="text"
                                className="w-full border rounded-lg p-2"
                                placeholder="# Documento"
                                value={numeroDoc}
                                onChange={(e) => setNumeroDoc(e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="flex justify-end gap-3 mt-6">
                        <button
                            onClick={limpiarFiltros}
                            className="px-4 py-2 text-gray-500 hover:text-gray-700 font-medium transition-colors"
                        >
                            Limpiar
                        </button>
                        <button
                            onClick={generarReporte}
                            disabled={loading}
                            className={`px-6 py-2 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 transition-all font-semibold flex items-center gap-2 ${loading ? 'opacity-70 cursor-wait' : ''}`}
                        >
                            {loading ? 'Generando...' : <><FaSearch /> Generar Reporte</>}
                        </button>
                        {reporte.length > 0 && (
                            <button
                                onClick={handleExportPDF}
                                className="px-6 py-2 bg-red-600 text-white rounded-lg shadow hover:bg-red-700 transition-all font-semibold flex items-center gap-2"
                            >
                                <FaFileExcel /> Exportar PDF
                            </button>
                        )}
                    </div>
                </div>

                {/* Resumen Cards */}
                {reporte.length > 0 && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                        <div className="bg-white p-4 rounded-xl shadow-sm border-l-4 border-blue-500 flex items-center justify-between">
                            <div>
                                <p className="text-gray-500 text-xs uppercase tracking-wide">Total Débitos (Cargos)</p>
                                <p className="text-xl font-bold text-gray-800">{formatCurrency(totales.debito)}</p>
                            </div>
                            <div className="p-3 bg-blue-50 text-blue-600 rounded-full"><FaMoneyBillWave /></div>
                        </div>
                        <div className="bg-white p-4 rounded-xl shadow-sm border-l-4 border-green-500 flex items-center justify-between">
                            <div>
                                <p className="text-gray-500 text-xs uppercase tracking-wide">Total Créditos (Pagos)</p>
                                <p className="text-xl font-bold text-gray-800">{formatCurrency(totales.credito)}</p>
                            </div>
                            <div className="p-3 bg-green-50 text-green-600 rounded-full"><FaMoneyBillWave /></div>
                        </div>
                        <div className="bg-white p-4 rounded-xl shadow-sm border-l-4 border-gray-500 flex items-center justify-between">
                            <div>
                                <p className="text-gray-500 text-xs uppercase tracking-wide">Saldo Neto (Periodo)</p>
                                <p className={`text-xl font-bold ${totales.saldo >= 0 ? 'text-blue-600' : 'text-red-500'}`}>
                                    {formatCurrency(totales.saldo)}
                                </p>
                            </div>
                            <div className="p-3 bg-gray-100 text-gray-600 rounded-full"><FaBuilding /></div>
                        </div>
                    </div>
                )}

                {/* Tabla de Resultados */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-gray-50 text-gray-600 text-xs uppercase tracking-wider border-b">
                                    <th className="p-4 font-semibold">Fecha</th>
                                    <th className="p-4 font-semibold">Documento</th>
                                    <th className="p-4 font-semibold">Unidad</th>
                                    <th className="p-4 font-semibold">Propietario</th>
                                    <th className="p-4 font-semibold">Concepto / Detalle</th>
                                    <th className="p-4 font-semibold text-right">Débito</th>
                                    <th className="p-4 font-semibold text-right">Crédito</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                                {reporte.length === 0 ? (
                                    <tr>
                                        <td colSpan="7" className="p-8 text-center text-gray-400">
                                            {loading ? 'Cargando datos...' : 'No hay datos para mostrar. Aplique filtros y presione Generar.'}
                                        </td>
                                    </tr>
                                ) : (
                                    reporte.map((row, idx) => (
                                        <tr key={idx} className="hover:bg-blue-50 transition-colors text-gray-700">
                                            <td className="p-4 whitespace-nowrap">{row.fecha}</td>
                                            <td className="p-4 font-medium text-blue-600">
                                                {row.tipo_doc} - {row.numero}
                                            </td>
                                            <td className="p-4 font-semibold">{row.unidad}</td>
                                            <td className="p-4 text-xs max-w-xs truncate" title={row.propietario}>
                                                {row.propietario}
                                            </td>
                                            <td className="p-4 text-xs text-gray-500 max-w-xs truncate" title={row.detalle || row.observaciones}>
                                                {row.detalle || row.observaciones}
                                            </td>
                                            <td className="p-4 text-right font-medium text-gray-800">
                                                {row.debito > 0 ? formatCurrency(row.debito) : '-'}
                                            </td>
                                            <td className="p-4 text-right font-medium text-green-600">
                                                {row.credito > 0 ? formatCurrency(row.credito) : '-'}
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                    {reporte.length > 0 && (
                        <div className="p-4 bg-gray-50 border-t flex justify-between text-xs text-gray-500">
                            <span>Mostrando {reporte.length} registros</span>
                            <span>Generado el {new Date().toLocaleDateString()}</span>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
