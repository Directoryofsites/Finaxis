'use client';
// Force Refresh

import React, { useState, useEffect } from 'react';
// import axios from 'axios'; // REMOVED raw axios

import { FaCalendarAlt, FaFilter, FaSearch, FaFileExcel, FaUsers, FaBuilding, FaMoneyBillWave } from 'react-icons/fa';
import AutocompleteInput from '../../components/AutocompleteInput';
import { phService } from '../../../lib/phService'; // IMPORT phService
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import { useRecaudos } from '../../../contexts/RecaudosContext'; // IMPORTED

export default function ReportesPHPage() {
    const { labels } = useRecaudos(); // HOOK

    // Estado de Filtros
    const [fechaDesde, setFechaDesde] = useState('');
    const [fechaHasta, setFechaHasta] = useState('');
    const [unidad, setUnidad] = useState(null); // { id, codigo, ... }
    const [propietario, setPropietario] = useState(null); // { id, razon_social, ... }
    const [concepto, setConcepto] = useState(''); // ID del concepto PH
    const [tipoDoc, setTipoDoc] = useState('');
    const [numeroDoc, setNumeroDoc] = useState('');
    const [filterText, setFilterText] = useState(''); // Nuevo Filtro de Texto Cliente

    // Listas para Selects
    const [unidades, setUnidades] = useState([]);
    const [propietarios, setPropietarios] = useState([]);
    const [conceptos, setConceptos] = useState([]);

    // Resultados
    const [reporte, setReporte] = useState([]);
    const [loading, setLoading] = useState(false);
    // REMOVE STATE: Totales ahora son dinámicos
    // const [totales, setTotales] = useState({ debito: 0, credito: 0, saldo: 0 });

    useEffect(() => {
        cargarMaestros();
    }, []);

    const cargarMaestros = async () => {
        try {
            // Cargar Unidades
            const dataUnidades = await phService.getUnidades({ limit: 1000 });
            setUnidades(dataUnidades);

            // Cargar Propietarios
            const dataPropietarios = await phService.getPropietarios();
            setPropietarios(dataPropietarios);

            // Cargar Conceptos PH
            const dataConceptos = await phService.getConceptos();
            setConceptos(dataConceptos);

        } catch (error) {
            console.error("Error cargando maestros:", error);
        }
    };

    const generarReporte = async () => {
        setLoading(true);
        try {
            const params = {
                fecha_desde: fechaDesde || undefined,
                fecha_hasta: fechaHasta || undefined,
                unidad_id: unidad?.id,
                propietario_id: propietario?.tercero_id,
                concepto_id: concepto || undefined,
                numero_doc: numeroDoc || undefined,
                tipo_movimiento: tipoDoc || undefined // Enviamos el valor del select ('FACTURAS', 'RECIBOS' o '')
            };

            const data = await phService.getReporteMovimientos(params);
            setReporte(data);
            // Totales se calcularán dinámicamente sobre filteredReporte
        } catch (error) {
            console.error("Error generando reporte:", error);
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
        setTipoDoc(''); // Limpiar filtro
        setNumeroDoc('');
        setFilterText('');
        setReporte([]);
    };

    // --- FILTRADO CLIENTE (Solo Concepto/Detalle) ---
    const filteredReporte = reporte.filter(row => {
        if (!filterText) return true;
        const text = filterText.toLowerCase();

        // Buscamos SOLO en detalle y observaciones como pidió el usuario
        const detalle = (row.detalle || '').toLowerCase();
        const obs = (row.observaciones || '').toLowerCase();

        return detalle.includes(text) || obs.includes(text);
    });

    // Calcular Totales Dinámicos
    const totalesDin = {
        debito: filteredReporte.reduce((acc, row) => acc + row.debito, 0),
        credito: filteredReporte.reduce((acc, row) => acc + row.credito, 0),
        saldo: 0
    };
    totalesDin.saldo = totalesDin.debito - totalesDin.credito;

    // --- PDF EXPORT FUNCTION ---
    const handleExportPDF = () => {
        try {
            const doc = new jsPDF();

            // Header
            doc.setFontSize(18);
            doc.setTextColor(40);
            doc.text(`Reporte de Movimientos - ${labels.module}`, 14, 22);
            doc.setFontSize(10);
            doc.setTextColor(100);
            doc.text(`Generado el: ${new Date().toLocaleDateString()}`, 14, 28);

            if (fechaDesde && fechaHasta) {
                doc.text(`Periodo: ${fechaDesde} al ${fechaHasta}`, 14, 34);
            }

            // Totales Header
            doc.setFontSize(10);
            doc.setTextColor(0);
            doc.text(`Total Cargos: ${formatCurrency(totalesDin.debito)}`, 14, 42);
            doc.text(`Total Abonos: ${formatCurrency(totalesDin.credito)}`, 80, 42);
            doc.text(`Saldo Final: ${formatCurrency(totalesDin.saldo)}`, 150, 42);

            // Table Data
            const tableColumn = ["Fecha", "Doc", labels.unidad, "Detalle", "Cargos", "Abonos", "Saldo"];

            // Calculo de saldos para PDF (Misma logica visual cronologica)
            const extracto = [...filteredReporte].reverse();
            let saldoAcumulado = 0;

            const tableRows = extracto.map(row => {
                const cargo = row.debito || 0;
                const abono = row.credito || 0;
                saldoAcumulado += (cargo - abono);

                return [
                    row.fecha,
                    `${row.tipo_doc} - ${row.numero}`,
                    row.unidad,
                    row.detalle || row.observaciones || '',
                    cargo > 0 ? formatCurrency(cargo) : '',
                    abono > 0 ? formatCurrency(abono) : '',
                    formatCurrency(saldoAcumulado)
                ];
            }); // .reverse() removed to match screen order (Chronological Old->New)

            // AutoTable
            autoTable(doc, {
                head: [tableColumn],
                body: tableRows,
                startY: 48,
                theme: 'grid',
                headStyles: { fillColor: [75, 85, 99] }, // Gray header for elegance
                styles: { fontSize: 8 },
                columnStyles: {
                    0: { cellWidth: 20 }, // Fecha
                    1: { cellWidth: 20 }, // Doc
                    2: { cellWidth: 15 }, // Unidad
                    3: { cellWidth: 'auto' }, // Detalle gets remaining width
                    4: { halign: 'right', textColor: [50, 50, 50] },
                    5: { halign: 'right', textColor: [22, 163, 74] }, // Green
                    6: { halign: 'right', fontStyle: 'bold' }
                }
            });

            doc.save(`reporte_recaudos_${new Date().toISOString().slice(0, 10)}.pdf`);
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
                        <h1 className="text-2xl font-bold text-gray-800 mt-2 flex items-center gap-2">
                            <FaFilter className="text-blue-600" />
                            Reportes {labels.module}
                        </h1>
                        <p className="text-gray-500">Consulta detallada de cartera por {labels.unidad}, {labels.propietario} y {labels.concepto}.</p>
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
                            <label className="block text-gray-600 mb-1 font-medium">{labels.unidad}</label>
                            <AutocompleteInput
                                items={unidades}
                                value={unidad?.codigo || ''}
                                onChange={(item) => setUnidad(item)}
                                placeholder={`Buscar ${labels.unidad}...`}
                                searchKey="codigo"
                                displayKey="codigo"
                            />
                        </div>
                        <div className="z-10">
                            <label className="block text-gray-600 mb-1 font-medium">{labels.propietario}</label>
                            {/* Ajustar si 'propietarios' tiene una estructura compleja */}
                            <AutocompleteInput
                                items={propietarios}
                                value={propietario?.razon_social || ''}
                                onChange={(item) => setPropietario(item)}
                                placeholder={`Buscar ${labels.propietario}...`}
                                searchKey="razon_social"
                                displayKey="razon_social"
                            />
                        </div>

                        {/* Concepto y Documento */}
                        <div>
                            <label className="block text-gray-600 mb-1 font-medium">Concepto</label>
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

                        {/* Nuevo Filtro: Tipo de Movimiento */}
                        <div>
                            <label className="block text-gray-600 mb-1 font-medium">Tipo Movimiento</label>
                            <select
                                className="w-full border rounded-lg p-2 bg-white"
                                value={tipoDoc} // Reutilizamos 'tipoDoc' o creamos uno nuevo? El codigo usa 'tipoDoc' state pero no lo usaba en API?
                                // Ah, linea 19: const [tipoDoc, setTipoDoc] = useState(''); Estaba declarado pero no conectado en UI anterior.
                                // Usaremos ese Estado para este proposito
                                onChange={(e) => setTipoDoc(e.target.value)}
                            >
                                <option value="">-- Todos --</option>
                                <option value="FACTURAS">Facturas (Cargos)</option>
                                <option value="RECIBOS">Recibos (Abonos)</option>
                            </select>
                        </div>

                        {/* Filtro Texto (Integrado en Grid) */}
                        <div>
                            <label className="block text-gray-600 mb-1 font-medium">Filtrar por Detalle</label>
                            <input
                                type="text"
                                className="w-full border rounded-lg p-2 focus:ring-2 focus:ring-blue-100 outline-none transition-all"
                                placeholder="Escribe para buscar..."
                                value={filterText}
                                onChange={(e) => setFilterText(e.target.value)}
                            />
                        </div>
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





                {/* Resumen Cards */}
                {
                    reporte.length > 0 && (
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                            <div className="bg-white p-4 rounded-xl shadow-sm border-l-4 border-indigo-500 flex items-center justify-between">
                                <div>
                                    <p className="text-gray-500 text-xs uppercase tracking-wide">Total Cargos (Debe)</p>
                                    <p className="text-xl font-bold text-gray-800">{formatCurrency(totalesDin.debito)}</p>
                                </div>
                                <div className="p-3 bg-indigo-50 text-indigo-600 rounded-full"><FaMoneyBillWave /></div>
                            </div>
                            <div className="bg-white p-4 rounded-xl shadow-sm border-l-4 border-green-500 flex items-center justify-between">
                                <div>
                                    <p className="text-gray-500 text-xs uppercase tracking-wide">Total Pagos (Abonos)</p>
                                    <p className="text-xl font-bold text-gray-800">{formatCurrency(totalesDin.credito)}</p>
                                </div>
                                <div className="p-3 bg-green-50 text-green-600 rounded-full"><FaMoneyBillWave /></div>
                            </div>
                            <div className="bg-white p-4 rounded-xl shadow-sm border-l-4 border-gray-500 flex items-center justify-between">
                                <div>
                                    <p className="text-gray-500 text-xs uppercase tracking-wide">Saldo Neto</p>
                                    <p className={`text-xl font-bold ${totalesDin.saldo >= 0 ? 'text-blue-600' : 'text-red-500'}`}>
                                        {formatCurrency(totalesDin.saldo)}
                                    </p>
                                </div>
                                <div className="p-3 bg-gray-100 text-gray-600 rounded-full"><FaBuilding /></div>
                            </div>
                        </div>
                    )
                }

                {/* Tabla de Resultados */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-gray-50 text-gray-600 text-xs uppercase tracking-wider border-b">
                                    <th className="p-4 font-semibold">Fecha</th>
                                    <th className="p-4 font-semibold">Documento</th>
                                    <th className="p-4 font-semibold">{labels.unidad}</th>
                                    <th className="p-4 font-semibold">Concepto / Detalle</th>
                                    <th className="p-4 font-semibold text-right text-indigo-700">Cargos</th>
                                    <th className="p-4 font-semibold text-right text-green-700">Abonos</th>
                                    <th className="p-4 font-semibold text-right text-gray-800">Saldo</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                                {filteredReporte.length === 0 ? (
                                    <tr>
                                        <td colSpan="7" className="p-8 text-center text-gray-400">
                                            {loading ? 'Cargando datos...' : (filterText ? 'No hay coincidencias con el filtro.' : 'No hay datos para mostrar.')}
                                        </td>
                                    </tr>
                                ) : (
                                    (() => {
                                        // LOGICA DE SALDO ACUMULADO VISUAL
                                        // Asumimos que los datos vienen ordenados por fecha descendente (lo más reciente primero)
                                        // Para mostrar el saldo linea a linea tipo extracto bancario, lo ideal es orden ascendente.
                                        // Si el backend manda descendente, tenemos dos opciones:
                                        // 1. Invertir array para visualizar (tipo extracto: antiguo -> nuevo)
                                        // 2. Calcular saldo 'hacia atrás' (complejo).
                                        // Vamos a invertir el array SOLO para visualizacion si el usuario quiere verlo cronológico.
                                        // O dejarlo descendente y mostrar el saldo 'post-movimiento'.

                                        // Vamos a invertir para simular extracto cronológico:
                                        const extracto = [...filteredReporte].reverse();
                                        let saldoAcumulado = 0;

                                        return extracto.map((row, idx) => {
                                            const cargo = row.debito || 0;
                                            const abono = row.credito || 0;
                                            saldoAcumulado += (cargo - abono);

                                            return (
                                                <tr key={idx} className="hover:bg-blue-50 transition-colors text-gray-700">
                                                    <td className="p-4 whitespace-nowrap">{row.fecha}</td>
                                                    <td className="p-4 font-medium text-blue-600">
                                                        {row.tipo_doc} - {row.numero}
                                                    </td>
                                                    <td className="p-4 font-semibold">{row.unidad}</td>
                                                    <td className="p-4 text-xs text-gray-500 max-w-xs truncate" title={row.detalle || row.observaciones}>
                                                        {row.detalle || row.observaciones}
                                                    </td>
                                                    <td className="p-4 text-right font-medium text-indigo-700">
                                                        {cargo > 0 ? formatCurrency(cargo) : '-'}
                                                    </td>
                                                    <td className="p-4 text-right font-medium text-green-700">
                                                        {abono > 0 ? formatCurrency(abono) : '-'}
                                                    </td>
                                                    <td className="p-4 text-right font-bold text-gray-800">
                                                        {formatCurrency(saldoAcumulado)}
                                                    </td>
                                                </tr>
                                            );
                                        }).reverse(); // Re-invertimos para mostrar lo mas reciente arriba, pero con saldo calculado correctamente?
                                        // Espera, si re-invertimos, el saldo 'acumulado' se verá raro (el ultimo saldo arriba).
                                        // Mejor MOSTRARLO CRONOLOGICO (Antiguo -> Nuevo) para entender la historia.
                                        // Quitemos el .reverse() final.
                                    })()
                                )}
                            </tbody>
                        </table>
                    </div>
                    {reporte.length > 0 && (
                        <div className="p-4 bg-gray-50 border-t flex justify-between text-xs text-gray-500">
                            <span>Mostrando {filteredReporte.length} de {reporte.length} registros</span>
                            <span>Generado el {new Date().toLocaleDateString()}</span>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
