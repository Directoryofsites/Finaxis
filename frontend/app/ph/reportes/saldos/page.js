'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { phService } from '../../../../lib/phService';
import {
    FaChartBar,
    FaFileDownload,
    FaFileCsv,
    FaSearch,
    FaFilter,
    FaCalendarAlt,
    FaBuilding,
    FaPlay,
    FaUser,
    FaBox,
    FaChevronDown,
    FaChevronUp,
    FaInfoCircle,
    FaUsers,
    FaCalculator,
    FaMoneyBillWave,
    FaLayerGroup
} from 'react-icons/fa';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import { useRecaudos } from '../../../../contexts/RecaudosContext';

export default function ReporteSaldosPage() {
    const { user, loading: authLoading } = useAuth();
    const { labels } = useRecaudos();

    // Filtros
    const [fechaCorte, setFechaCorte] = useState('');
    const [selectedTorre, setSelectedTorre] = useState('');
    const [conceptoBusqueda, setConceptoBusqueda] = useState('');
    const [selectedPropietario, setSelectedPropietario] = useState('');
    const [selectedUnidad, setSelectedUnidad] = useState('');
    const [selectedModulo, setSelectedModulo] = useState('');
    const [operadorMonto, setOperadorMonto] = useState('>');
    const [valorMonto, setValorMonto] = useState('');
    const [agruparPropietario, setAgruparPropietario] = useState(false);

    // Datos Auxiliares
    const [torres, setTorres] = useState([]);
    const [conceptos, setConceptos] = useState([]);
    const [propietarios, setPropietarios] = useState([]);
    const [modulos, setModulos] = useState([]);
    const [unidadesRaw, setUnidadesRaw] = useState([]); // Todas las unidades para el select

    // UI State
    const [expandedGroups, setExpandedGroups] = useState({}); // {ownerName: bool}
    const [mostrarDetalleGrupos, setMostrarDetalleGrupos] = useState(true);


    // Estado Reporte
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);

    // Carga Inicial
    useEffect(() => {
        if (!authLoading && user?.empresaId) {
            loadAuxData();
            loadReporte();
        }
    }, [authLoading, user]);

    const loadAuxData = async () => {
        try {
            const [t, c, p, m, u] = await Promise.all([
                phService.getTorres(),
                phService.getConceptos(),
                phService.getPropietarios(),
                phService.getModulos(),
                phService.getUnidades({ limit: 5000 })
            ]);
            setTorres(t || []);
            setConceptos(c || []);
            setPropietarios(p || []);
            setModulos(m || []);
            setUnidadesRaw(u || []);
        } catch (e) {
            console.error("Error cargando datos auxiliares", e);
        }
    };


    const loadReporte = async () => {
        setLoading(true);
        try {
            const params = {};
            if (fechaCorte) params.fecha_corte = fechaCorte;
            if (selectedTorre) params.torre_id = selectedTorre;
            if (conceptoBusqueda) params.concepto_busqueda = conceptoBusqueda;
            if (selectedPropietario) params.propietario_id = selectedPropietario;
            if (selectedUnidad) params.unidad_id = selectedUnidad;
            if (selectedModulo) params.modulo_id = selectedModulo;
            if (valorMonto !== '') {
                params.operador_monto = operadorMonto;
                params.valor_monto = parseFloat(valorMonto);
            }
            params.agrupar_por_propietario = agruparPropietario;

            const result = await phService.getReporteSaldos(params);
            setData(result);
            
            // Expandir todos los grupos por defecto si es agrupado
            if (result.is_grouped) {
                const initialExpanded = {};
                result.items_agrupados.forEach(g => {
                    initialExpanded[g.propietario_nombre] = mostrarDetalleGrupos;
                });
                setExpandedGroups(initialExpanded);
            }
        } catch (error) {
            console.error("Error loading report", error);
        } finally {
            setLoading(false);
        }
    };

    // Efecto para recargar al cambiar filtros (debounce opcional)
    useEffect(() => {
        // Carga inicial solo si no hay datos.
        // Si el usuario cambia filtros, debe dar click en el botón.
        if (!authLoading && user?.empresaId && !data && !loading) {
            loadReporte();
        }
    }, [authLoading, user]);

    // Exportar CSV
    const handleDownloadCSV = () => {
        if (!data || !data.items) return;

        let csvContent = `${labels?.torre || 'Torre'};${labels?.unidad || 'Unidad'};${labels?.propietario || 'Propietario'};Saldo;Detalle\n`;
        
        if (data.is_grouped && data.items_agrupados) {
            data.items_agrupados.forEach(grupo => {
                // Fila de cabecera de grupo
                csvContent += `---;---;RESUMEN: ${grupo.propietario_nombre};${grupo.saldo_total};${grupo.unidades_count} ${grupo.unidades_count === 1 ? (labels?.unidad || 'Unidad') : (labels?.unidad_plural || 'Unidades')}\n`;
                
                // Solo incluir detalles si el switch está activo
                if (mostrarDetalleGrupos) {
                    grupo.items.forEach(item => {
                        csvContent += `${item.torre_nombre};${item.unidad_codigo};${item.propietario_nombre};${item.saldo};${item.detalle}\n`;
                    });
                }
            });
        } else {
            data.items.forEach(item => {
                csvContent += `${item.torre_nombre};${item.unidad_codigo};${item.propietario_nombre};${item.saldo};${item.detalle}\n`;
            });
        }

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', `Reporte_Saldos_${fechaCorte || 'HOY'}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    // Exportar PDF
    const handleDownloadPDF = () => {
        if (!data) return;

        const doc = new jsPDF();
        
        // Header
        doc.setFontSize(18);
        doc.setTextColor(40, 40, 40);
        doc.text("Reporte de Saldos de Cartera", 14, 22);

        doc.setFontSize(10);
        doc.text(`Empresa: ${user?.empresaNombre || user?.empresa?.razon_social || 'Copropiedad'}`, 14, 28);
        doc.text(`Fecha de Corte: ${fechaCorte || new Date().toLocaleDateString()}`, 14, 34);
        
        let subHeaderY = 40;
        if (conceptoBusqueda) { doc.text(`Filtro Concepto: ${conceptoBusqueda}`, 14, subHeaderY); subHeaderY += 6; }
        if (agruparPropietario) { doc.text(`Informe Agrupado por ${labels?.propietario || 'Propietario'}`, 14, subHeaderY); subHeaderY += 6; }

        const tableColumn = [labels?.torre || "Torre", labels?.unidad || "Unidad", labels?.propietario || "Propietario", "Saldo", "Detalle"];
        const tableRows = [];

        if (data.is_grouped && data.items_agrupados) {
            data.items_agrupados.forEach(grupo => {
                // Fila de cabecera de grupo
                tableRows.push([
                    { content: `TOTAL ${labels?.propietario?.toUpperCase() || 'PROPIETARIO'}: ${grupo.propietario_nombre}`, colSpan: 3, styles: { fillColor: [240, 240, 240], fontStyle: 'bold' } },
                    { content: `$${grupo.saldo_total.toLocaleString()}`, styles: { fillColor: [240, 240, 240], fontStyle: 'bold', halign: 'right' } },
                    { content: `${grupo.unidades_count} ${grupo.unidades_count === 1 ? (labels?.unidad || 'Unidad') : (labels?.unidad_plural || 'Unidades')}`, styles: { fillColor: [240, 240, 240], fontSize: 7 } }
                ]);
                
                // Solo incluir detalles si el switch está activo
                if (mostrarDetalleGrupos) {
                    grupo.items.forEach(item => {
                        tableRows.push([
                            item.torre_nombre,
                            item.unidad_codigo,
                            item.propietario_nombre,
                            `$${item.saldo.toLocaleString()}`,
                            item.detalle
                        ]);
                    });
                }
            });
        } else {
            data.items.forEach(item => {
                tableRows.push([
                    item.torre_nombre,
                    item.unidad_codigo,
                    item.propietario_nombre,
                    `$${item.saldo.toLocaleString()}`,
                    item.detalle
                ]);
            });
        }

        // Add Total Row
        tableRows.push([
            { content: "TOTAL GENERAL CARTERA", colSpan: 3, styles: { fillColor: [79, 70, 229], textColor: [255, 255, 255], fontStyle: 'bold', halign: 'right' } },
            { content: `$${data.total_general.toLocaleString()}`, styles: { fillColor: [79, 70, 229], textColor: [255, 255, 255], fontStyle: 'bold', halign: 'right' } },
            { content: "", styles: { fillColor: [79, 70, 229] } }
        ]);

        autoTable(doc, {
            head: [tableColumn],
            body: tableRows,
            startY: subHeaderY + 5,
            theme: 'striped',
            headStyles: { fillColor: [79, 70, 229] },
            styles: { fontSize: 8 },
            columnStyles: {
                3: { halign: 'right' }
            }
        });

        doc.save(`Reporte_Saldos_${fechaCorte || 'HOY'}.pdf`);
    };

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8 flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-indigo-100 text-indigo-600 rounded-xl">
                            <FaChartBar className="text-3xl" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold text-gray-800">Balance General de Cartera</h1>
                            <p className="text-gray-500">{labels?.descripcion || 'Informe detallado de saldos por concepto.'}</p>
                        </div>
                    </div>
                </div>
                {/* Resumen KPIs */}
                {data && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                        <div className="bg-gradient-to-br from-indigo-500 to-indigo-700 p-6 rounded-2xl shadow-lg text-white">
                            <div className="flex justify-between items-start">
                                <div>
                                    <p className="text-indigo-100 text-xs font-bold uppercase tracking-wider mb-1">Total Cartera Bruta</p>
                                    <h3 className="text-3xl font-black">${(data.total_general > 0 ? data.total_general : 0).toLocaleString()}</h3>
                                </div>
                                <div className="bg-white/20 p-3 rounded-xl backdrop-blur-md">
                                    <FaMoneyBillWave className="text-2xl" />
                                </div>
                            </div>
                            <p className="text-indigo-200 text-[10px] mt-4 flex items-center gap-1">
                                <FaInfoCircle /> Saldo pendiente acumulado por cobrar
                            </p>
                        </div>

                        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                            <div className="flex justify-between items-start">
                                <div>
                                    <p className="text-gray-400 text-xs font-bold uppercase tracking-wider mb-1">
                                        {labels?.unidad_plural || 'Unidades'} Reportadas
                                    </p>
                                    <h3 className="text-3xl font-black text-gray-800">
                                        {data.is_grouped ? data.items_agrupados.reduce((acc, g) => acc + g.unidades_count, 0) : data.items.length}
                                    </h3>
                                </div>
                                <div className="bg-indigo-50 p-3 rounded-xl">
                                    <FaBox className="text-2xl text-indigo-500" />
                                </div>
                            </div>
                            <p className="text-gray-400 text-[10px] mt-4 flex items-center gap-1">
                                <FaBuilding /> Total de {labels?.unidad_plural?.toLowerCase() || 'unidades'} con saldo pendiente
                            </p>
                        </div>

                        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                            <div className="flex justify-between items-start">
                                <div>
                                    <p className="text-gray-400 text-xs font-bold uppercase tracking-wider mb-1">Total General Neto</p>
                                    <h3 className={`text-3xl font-black ${data.total_general < 0 ? 'text-green-600' : 'text-indigo-600'}`}>
                                        ${data.total_general.toLocaleString()}
                                    </h3>
                                </div>
                                <div className="bg-indigo-50 p-3 rounded-xl">
                                    <FaCalculator className="text-2xl text-indigo-500" />
                                </div>
                            </div>
                            <p className="text-gray-400 text-[10px] mt-4">
                                {data.total_general < 0 ? 'Excedente (Saldos a favor superan deuda)' : 'Balance neto por recaudar'}
                            </p>
                        </div>
                    </div>
                )}

                {/* Filtros Avanzados */}
                <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 mb-8">
                    <div className="grid grid-cols-1 md:grid-cols-4 lg:grid-cols-6 gap-4">
                        {/* Fecha Corte */}
                        <div className="lg:col-span-1">
                            <label className="block text-[11px] font-bold text-gray-400 uppercase mb-2 flex items-center gap-2">
                                <FaCalendarAlt className="text-indigo-500" /> Corte
                            </label>
                            <input
                                type="date"
                                className="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm"
                                value={fechaCorte}
                                onChange={(e) => setFechaCorte(e.target.value)}
                            />
                        </div>

                        {/* Torre */}
                        <div className="lg:col-span-1">
                            <label className="block text-[11px] font-bold text-gray-400 uppercase mb-2 flex items-center gap-2">
                                <FaBuilding className="text-indigo-500" /> {labels?.torre || 'Torre'}
                            </label>
                            <select
                                className="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none bg-white text-sm"
                                value={selectedTorre}
                                onChange={(e) => setSelectedTorre(e.target.value)}
                            >
                                <option value="">Todas</option>
                                {torres.map(t => (
                                    <option key={t.id} value={t.id}>{t.nombre}</option>
                                ))}
                            </select>
                        </div>

                        {/* Propietario */}
                        <div className="lg:col-span-1">
                            <label className="block text-[11px] font-bold text-gray-400 uppercase mb-2 flex items-center gap-2">
                                <FaUser className="text-indigo-500" /> {labels?.propietario || 'Propietario'}
                            </label>
                            <select
                                className="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none bg-white text-sm"
                                value={selectedPropietario}
                                onChange={(e) => setSelectedPropietario(e.target.value)}
                            >
                                <option value="">Todos</option>
                                {propietarios.map(p => (
                                    <option key={p.id} value={p.id}>{p.nombre}</option>
                                ))}
                            </select>
                        </div>

                        {/* Unidad */}
                        <div className="lg:col-span-1">
                            <label className="block text-[11px] font-bold text-gray-400 uppercase mb-2 flex items-center gap-2">
                                <FaBox className="text-indigo-500" /> {labels?.unidad || 'Unidad'}
                            </label>
                            <select
                                className="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none bg-white text-sm"
                                value={selectedUnidad}
                                onChange={(e) => setSelectedUnidad(e.target.value)}
                            >
                                <option value="">Todas</option>
                                {unidadesRaw.map(u => (
                                    <option key={u.id} value={u.id}>{u.codigo}</option>
                                ))}
                            </select>
                        </div>

                        {/* Módulo */}
                        <div className="lg:col-span-1">
                            <label className="block text-[11px] font-bold text-gray-400 uppercase mb-2 flex items-center gap-2">
                                <FaFilter className="text-indigo-500" /> {labels?.modulo || 'Módulo'}
                            </label>
                            <select
                                className="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none bg-white text-sm"
                                value={selectedModulo}
                                onChange={(e) => setSelectedModulo(e.target.value)}
                            >
                                <option value="">Todos</option>
                                {modulos.map(m => (
                                    <option key={m.id} value={m.id}>{m.nombre}</option>
                                ))}
                            </select>
                        </div>

                        {/* Rango Monto */}
                        <div className="lg:col-span-1">
                            <label className="block text-[11px] font-bold text-gray-400 uppercase mb-2 flex items-center gap-2">
                                <FaMoneyBillWave className="text-indigo-500" /> Saldo
                            </label>
                            <div className="flex gap-1">
                                <select 
                                    className="px-1 py-2 border rounded-l-xl outline-none text-xs bg-gray-50"
                                    value={operadorMonto}
                                    onChange={(e) => setOperadorMonto(e.target.value)}
                                >
                                    <option value=">">{'>'}</option>
                                    <option value="<">{'<'}</option>
                                    <option value="=">{'='}</option>
                                </select>
                                <input
                                    type="number"
                                    placeholder="Valor"
                                    className="w-full px-3 py-2 border rounded-r-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm"
                                    value={valorMonto}
                                    onChange={(e) => setValorMonto(e.target.value)}
                                />
                            </div>
                        </div>

                        {/* Concepto (Texto) */}
                        <div className="md:col-span-2 lg:col-span-2">
                            <label className="block text-[11px] font-bold text-gray-400 uppercase mb-2">
                                Filtrar por Concepto Específico
                            </label>
                            <select
                                className="w-full px-3 py-2 border rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none bg-white text-sm"
                                value={conceptoBusqueda}
                                onChange={(e) => setConceptoBusqueda(e.target.value)}
                            >
                                <option value="">Todos los Conceptos</option>
                                {conceptos.map(c => (
                                    <option key={c.id} value={c.nombre}>{c.nombre}</option>
                                ))}
                            </select>
                        </div>

                        {/* Agrupación */}
                        <div className="md:col-span-2 lg:col-span-2 flex items-center gap-3 pt-6">
                            <label className="relative inline-flex items-center cursor-pointer">
                                <input 
                                    type="checkbox" 
                                    className="sr-only peer" 
                                    checked={agruparPropietario}
                                    onChange={(e) => setAgruparPropietario(e.target.checked)}
                                />
                                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
                                <span className="ml-3 text-sm font-bold text-gray-700">Agrupar por Propietario</span>
                            </label>
                        </div>

                        {/* Botón Ejecutar */}
                        <div className="md:col-span-4 lg:col-span-2 flex items-end">
                            <button
                                onClick={loadReporte}
                                disabled={loading}
                                className="w-full py-2.5 bg-indigo-600 text-white font-bold rounded-xl shadow-md hover:bg-indigo-700 transition-all flex justify-center items-center gap-2 disabled:opacity-50"
                            >
                                {loading ? <span className="loading loading-spinner loading-sm"></span> : <FaPlay />}
                                {loading ? 'Cargando...' : 'Actualizar Informe'}
                            </button>
                        </div>
                    </div>
                </div>

                {/* Resumen Totales */}
                {data && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                        <div className="bg-gradient-to-br from-indigo-600 to-indigo-800 text-white p-6 rounded-2xl shadow-lg">
                            <p className="text-indigo-200 text-sm font-bold uppercase tracking-wider mb-1">Total General Cartera</p>
                            <h2 className="text-4xl font-black">${data.total_general.toLocaleString()}</h2>
                            <p className="text-xs mt-2 opacity-80">Saldo Neto (Incluye anticipos restados)</p>
                        </div>
                        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-center justify-between">
                            <div>
                                <p className="text-gray-500 text-sm font-bold uppercase">
                                    {data.is_grouped ? 'Propietarios Responsables' : (labels?.unidad_plural || labels?.unidad || 'Unidades')}
                                </p>
                                <h2 className="text-3xl font-bold text-gray-800">
                                    {data.is_grouped ? data.items_agrupados.length : data.items.length}
                                </h2>
                            </div>
                            <div className="bg-indigo-50 p-3 rounded-full text-indigo-600">
                                {data.is_grouped ? <FaUsers className="text-xl" /> : <FaBuilding className="text-xl" />}
                            </div>
                        </div>
                        <div className="flex flex-col gap-2 justify-center">
                            <button
                                onClick={handleDownloadPDF}
                                className="flex items-center justify-center gap-2 px-6 py-3 bg-red-600 text-white rounded-xl shadow-lg hover:bg-red-700 transition-all font-bold w-full"
                            >
                                <FaFileDownload className="text-xl" /> PDF
                            </button>
                            <button
                                onClick={handleDownloadCSV}
                                className="flex items-center justify-center gap-2 px-6 py-3 bg-green-600 text-white rounded-xl shadow-lg hover:bg-green-700 transition-all font-bold w-full"
                            >
                                <FaFileCsv className="text-xl" /> CSV / Excel
                            </button>
                        </div>
                    </div>
                )}

                {/* Tabla Resultados */}
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                    {data?.is_grouped && (
                        <div className="bg-indigo-50/50 p-4 border-b border-indigo-100 flex justify-between items-center">
                            <div className="flex items-center gap-3">
                                <FaLayerGroup className="text-indigo-500" />
                                <span className="text-sm font-bold text-gray-700">Vista de Grupos por {labels?.propietario || 'Responsable'}</span>
                            </div>
                            <button
                                onClick={() => {
                                    const nextVal = !mostrarDetalleGrupos;
                                    setMostrarDetalleGrupos(nextVal);
                                    const newExpanded = {};
                                    data.items_agrupados.forEach(g => {
                                        newExpanded[g.propietario_nombre] = nextVal;
                                    });
                                    setExpandedGroups(newExpanded);
                                }}
                                className={`px-4 py-2 rounded-xl text-xs font-black transition-all flex items-center gap-2 ${
                                    mostrarDetalleGrupos 
                                        ? 'bg-indigo-600 text-white shadow-md shadow-indigo-200 hover:bg-indigo-700' 
                                        : 'bg-white border border-indigo-200 text-indigo-600 hover:bg-indigo-50'
                                }`}
                            >
                                {mostrarDetalleGrupos ? <FaChevronUp /> : <FaChevronDown />}
                                {mostrarDetalleGrupos ? 'RECOGER TODOS (RESUMEN)' : 'DESPLEGAR TODOS (DETALLE)'}
                            </button>
                        </div>
                    )}
                    {loading ? (
                        <div className="p-12 flex flex-col items-center justify-center">
                            <span className="loading loading-spinner loading-lg text-indigo-600 mb-4"></span>
                            <p className="text-gray-500 font-bold animate-pulse">Analizando saldos históricos...</p>
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-left border-collapse">
                                <thead>
                                    <tr className="bg-gray-50 text-gray-500 uppercase text-xs tracking-wider font-bold">
                                        <th className="p-4 border-b">{labels?.torre || 'Torre'}</th>
                                        <th className="p-4 border-b">{labels?.unidad || 'Unidad'}</th>
                                        <th className="p-4 border-b">{labels?.propietario || 'Propietario'}</th>
                                        <th className="p-4 border-b">Detalle / {labels?.concepto || 'Conceptos'}</th>
                                        <th className="p-4 border-b text-right">Saldo Total</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100">
                                {data?.is_grouped ? (
                                    data?.items_agrupados.map((grupo, gIdx) => (
                                        <React.Fragment key={gIdx}>
                                            <tr 
                                                className="bg-gray-50/80 cursor-pointer hover:bg-indigo-50 transition-colors border-l-4 border-indigo-500"
                                                onClick={() => setExpandedGroups(prev => ({ ...prev, [grupo.propietario_nombre]: !prev[grupo.propietario_nombre] }))}
                                            >
                                                <td colSpan="4" className="p-4">
                                                    <div className="flex items-center gap-4">
                                                        <div className={`p-1.5 rounded-lg transition-transform ${expandedGroups[grupo.propietario_nombre] ? 'rotate-0' : '-rotate-90'} bg-white shadow-sm border`}>
                                                            <FaChevronDown className="text-indigo-600 text-[10px]" />
                                                        </div>
                                                        <div className="flex flex-col">
                                                            <div className="flex items-center gap-2">
                                                                <span className="font-black text-gray-800 tracking-tight">{grupo.propietario_nombre}</span>
                                                                <span className="text-[10px] bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full font-black uppercase tracking-tighter">
                                                                    {grupo.unidades_count} {grupo.unidades_count === 1 ? (labels?.unidad || 'Unidad') : (labels?.unidad_plural || 'Unidades')}
                                                                </span>
                                                            </div>
                                                            <span className="text-[10px] text-gray-400 font-medium">Responsable de pago consolidado</span>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="p-4 text-right">
                                                    <div className="flex flex-col items-end">
                                                        <span className="text-lg font-black text-indigo-700 leading-none">
                                                            ${grupo.saldo_total.toLocaleString()}
                                                        </span>
                                                        <span className="text-[10px] text-gray-400 font-bold uppercase tracking-widest mt-1">Total Deuda</span>
                                                    </div>
                                                </td>
                                            </tr>
                                            {expandedGroups[grupo.propietario_nombre] && grupo.items.map((item, idx) => (
                                                <tr key={`${gIdx}-${idx}`} className="hover:bg-white transition-colors group border-l-4 border-transparent hover:border-indigo-200">
                                                    <td className="p-4 text-xs text-gray-400 pl-14">
                                                        <div className="flex items-center gap-2">
                                                            <FaBuilding className="text-[10px]" />
                                                            {item.torre_nombre}
                                                        </div>
                                                    </td>
                                                    <td className="p-4">
                                                        <div className="flex flex-col">
                                                            <span className="text-sm font-black text-indigo-600">{item.unidad_codigo}</span>
                                                            <span className="text-[9px] text-gray-400 uppercase font-bold">{labels?.unidad || 'Unidad'}</span>
                                                        </div>
                                                    </td>
                                                    <td className="p-4 text-xs text-gray-500 italic">
                                                        <div className="flex items-center gap-2">
                                                            <div className="w-2 h-2 rounded-full bg-indigo-200"></div>
                                                            Vínculo verificado
                                                        </div>
                                                    </td>
                                                    <td className="p-4">
                                                        <div className="max-w-xs">
                                                            <p className="text-[11px] text-gray-600 leading-tight line-clamp-2" title={item.detalle}>
                                                                {item.detalle}
                                                            </p>
                                                        </div>
                                                    </td>
                                                    <td className="p-4 text-right">
                                                        <span className="text-sm font-bold text-gray-700">
                                                            ${item.saldo.toLocaleString()}
                                                        </span>
                                                    </td>
                                                </tr>
                                            ))}
                                        </React.Fragment>
                                    ))
                                ) : (
                                    data?.items.length === 0 ? (
                                        <tr>
                                            <td colSpan="5" className="p-8 text-center text-gray-400 italic">No se encontraron saldos con los filtros aplicados.</td>
                                        </tr>
                                    ) : (
                                        data?.items.map((item, idx) => (
                                            <tr key={idx} className="hover:bg-indigo-50 transition-colors group">
                                                <td className="p-4 text-sm text-gray-600">{item.torre_nombre}</td>
                                                <td className="p-4 text-sm font-bold text-indigo-600">{item.unidad_codigo}</td>
                                                <td className="p-4 text-sm text-gray-800">{item.propietario_nombre}</td>
                                                <td className="p-4 text-xs text-gray-500 max-w-xs truncate" title={item.detalle}>
                                                    {item.detalle}
                                                </td>
                                                <td className="p-4 text-sm font-bold text-right text-gray-800">
                                                    ${item.saldo.toLocaleString()}
                                                </td>
                                            </tr>
                                        ))
                                    )
                                )}
                            </tbody>
                            {data && (data?.items?.length > 0 || data?.items_agrupados?.length > 0) && (
                                <tfoot className="bg-gray-50 border-t-2 border-gray-100">
                                    <tr>
                                        <td colSpan="4" className="p-6 text-right font-bold text-gray-500 uppercase tracking-widest">Total General Cartera:</td>
                                        <td className="p-6 text-right font-black text-indigo-700 text-2xl">
                                            ${data.total_general.toLocaleString()}
                                        </td>
                                    </tr>
                                </tfoot>
                            )}
                            </table>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
