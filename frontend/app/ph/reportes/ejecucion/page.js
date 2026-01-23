'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { phService } from '../../../../lib/phService';
import { FaTable, FaFileDownload, FaSpinner, FaChevronDown, FaChevronRight, FaFilePdf, FaFileCsv, FaSearch, FaCalendarAlt } from 'react-icons/fa';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';

const getPosibleParentCode = (codigo) => {
    if (!codigo || codigo.length <= 1) return null;
    const len = codigo.length;
    if (len === 2) return codigo.substring(0, 1);
    if (len === 4) return codigo.substring(0, 2);
    if (len === 6) return codigo.substring(0, 4);
    if (len >= 8 && len % 2 === 0) return codigo.substring(0, len - 2);
    return codigo.substring(0, len - 1);
};

export default function EjecucionPresupuestalPage() {
    const { user, loading: authLoading } = useAuth();
    const [loading, setLoading] = useState(false);

    // Data
    const [fullTree, setFullTree] = useState([]);
    const [filteredTree, setFilteredTree] = useState([]);
    const [expandedNodes, setExpandedNodes] = useState({});

    const [globalTotals, setGlobalTotals] = useState({ pres: 0, ejec: 0, var: 0 });
    const [searchTerm, setSearchTerm] = useState('');

    // Dates (Rango)
    const today = new Date();
    const firstDay = new Date(today.getFullYear(), 0, 1); // Ene 1
    const lastDay = new Date(today.getFullYear(), 11, 31); // Dic 31

    const formatDate = (d) => d.toISOString().split('T')[0];

    const [fechaInicio, setFechaInicio] = useState(formatDate(firstDay));
    const [fechaFin, setFechaFin] = useState(formatDate(lastDay)); // Default ANNUAL

    useEffect(() => {
        if (!authLoading && user?.empresaId) {
            loadReporte();
        }
    }, [authLoading, user, fechaInicio, fechaFin]); // Reload on range change

    useEffect(() => {
        if (!fullTree.length) return;
        if (!searchTerm) {
            setFilteredTree(fullTree);
            return;
        }

        const lowerTerm = searchTerm.toLowerCase();

        const filterNode = (nodes) => {
            const res = [];
            nodes.forEach(n => {
                const matchOwn = n.cuenta_codigo.toLowerCase().includes(lowerTerm) ||
                    n.cuenta_nombre.toLowerCase().includes(lowerTerm);

                const matchingChildren = filterNode(n.children);

                if (matchOwn || matchingChildren.length > 0) {
                    const newNode = { ...n, children: matchingChildren };
                    if (matchOwn && n.children.length > 0 && matchingChildren.length === 0) {
                        newNode.children = n.children;
                    }
                    res.push(newNode);
                }
            });
            return res;
        };

        const filtered = filterNode(fullTree);
        setFilteredTree(filtered);

        if (filtered.length > 0) {
            const allExpanded = {};
            const expandRec = (nodes) => {
                nodes.forEach(n => {
                    allExpanded[n.cuenta_codigo] = true;
                    expandRec(n.children);
                });
            };
            expandRec(filtered);
            setExpandedNodes(allExpanded);
        }

    }, [searchTerm, fullTree]);


    const buildTree = (flatItems) => {
        const map = {};
        const roots = [];

        flatItems.forEach(item => {
            map[item.cuenta_codigo] = {
                ...item,
                children: [],
                is_virtual: false,
                total_pres: parseFloat(item.presupuestado) || 0,
                total_ejec: parseFloat(item.ejecutado) || 0,
                total_var: parseFloat(item.variacion_absoluta) || 0
            };
        });

        const initialCodes = Object.keys(map);
        initialCodes.forEach(code => {
            let currentCode = code;
            while (true) {
                const parentCode = getPosibleParentCode(currentCode);
                if (!parentCode) break;
                if (!map[parentCode]) {
                    map[parentCode] = {
                        cuenta_id: `virt_${parentCode}`,
                        cuenta_codigo: parentCode,
                        cuenta_nombre: `GRUPO ${parentCode}`,
                        presupuestado: 0,
                        ejecutado: 0,
                        variacion_absoluta: 0,
                        children: [],
                        is_virtual: true,
                        total_pres: 0,
                        total_ejec: 0,
                        total_var: 0,
                        cumplimiento_porcentaje: 0
                    };
                }
                currentCode = parentCode;
            }
        });

        Object.values(map).forEach(node => {
            const parentCode = getPosibleParentCode(node.cuenta_codigo);
            if (parentCode && map[parentCode]) {
                map[parentCode].children.push(node);
            } else {
                roots.push(node);
            }
        });

        return roots;
    };

    const recalculateRollups = (nodes) => {
        let sumPres = 0;
        let sumEjec = 0;
        let sumVar = 0;

        nodes.sort((a, b) => a.cuenta_codigo.localeCompare(b.cuenta_codigo));

        nodes.forEach(node => {
            const childs = recalculateRollups(node.children);

            const ownPres = node.is_virtual ? 0 : (parseFloat(node.presupuestado) || 0);
            const ownEjec = node.is_virtual ? 0 : (parseFloat(node.ejecutado) || 0);
            const ownVar = node.is_virtual ? 0 : (parseFloat(node.variacion_absoluta) || 0);

            node.total_pres = childs.pres + ownPres;
            node.total_ejec = childs.ejec + ownEjec;
            node.total_var = childs.var + ownVar;

            if (node.total_pres !== 0) {
                node.cumplimiento_porcentaje = (node.total_ejec / node.total_pres) * 100;
            } else {
                node.cumplimiento_porcentaje = 0;
            }

            sumPres += node.total_pres;
            sumEjec += node.total_ejec;
            sumVar += node.total_var;
        });

        return { pres: sumPres, ejec: sumEjec, var: sumVar };
    };

    const loadReporte = async () => {
        setLoading(true);
        try {
            // Updated Service Call with Date Range
            // Note: phService.getEjecucionPresupuestal needs to support 3rd/4th arg or object
            // We assume I need to update phService or use axios directly? 
            // Let's assume phService wrapper forwards args. If not, I'll need to update it.
            // Actually, I should update phService first? 
            // Or I can pass them as query params if I construct URL.
            // But let's assume valid service call:

            const result = await phService.getEjecucionPresupuestal(null, null, fechaInicio, fechaFin);

            if (result && result.items) {
                const roots = buildTree(result.items);
                const grandTotals = recalculateRollups(roots);

                setFullTree(roots);
                setFilteredTree(roots);
                setGlobalTotals(grandTotals);

                const initialExp = {};
                roots.forEach(r => initialExp[r.cuenta_codigo] = true);
                setExpandedNodes(initialExp);
            }
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const toggleNode = (code) => {
        setExpandedNodes(prev => ({ ...prev, [code]: !prev[code] }));
    };

    const handlePrintPDF = () => {
        const doc = new jsPDF('p', 'mm', 'a4');
        doc.setFontSize(16);
        doc.text("Informe de Ejecución Presupuestal", 14, 20);
        doc.setFontSize(10);
        doc.text(`Empresa: ${user?.empresaNombre || 'Consorcio'}`, 14, 28);
        doc.text(`Rango: ${fechaInicio} a ${fechaFin}`, 14, 34);

        const rows = [];
        const traverse = (nodes, level = 0) => {
            nodes.forEach(n => {
                rows.push([
                    n.cuenta_codigo,
                    { content: '  '.repeat(level) + n.cuenta_nombre, styles: { fontStyle: n.children.length ? 'bold' : 'normal' } },
                    { content: '$ ' + n.total_pres.toLocaleString('es-CO'), styles: { halign: 'right' } },
                    { content: '$ ' + n.total_ejec.toLocaleString('es-CO'), styles: { halign: 'right', fontStyle: 'bold' } },
                    {
                        content: '$ ' + n.total_var.toLocaleString('es-CO'),
                        styles: {
                            halign: 'right',
                            textColor: n.total_var < 0 ? [200, 0, 0] : [0, 100, 0]
                        }
                    },
                    { content: n.cumplimiento_porcentaje.toFixed(1) + '%', styles: { halign: 'right' } }
                ]);
                traverse(n.children, level + 1);
            });
        };
        traverse(filteredTree);

        rows.push([
            { content: 'TOTALES', colSpan: 2, styles: { fontStyle: 'bold', halign: 'right' } },
            '$ ' + globalTotals.pres.toLocaleString('es-CO'),
            '$ ' + globalTotals.ejec.toLocaleString('es-CO'),
            '$ ' + globalTotals.var.toLocaleString('es-CO'),
            '-'
        ]);

        autoTable(doc, {
            head: [["Cuenta", "Nombre", "Presupuesto", "Ejecutado", "Variación", "%"]],
            body: rows,
            startY: 40,
            theme: 'grid',
            headStyles: { fillColor: [41, 128, 185] },
            columnStyles: { 0: { cellWidth: 25 }, 2: { cellWidth: 30 }, 3: { cellWidth: 30 }, 4: { cellWidth: 30 } }
        });
        doc.save(`Ejecucion_${fechaInicio}_${fechaFin}.pdf`);
    };

    const handleExportCSV = () => {
        if (!filteredTree.length) return;

        const rows = [];
        const header = ["Cuenta", "Nombre", "Presupuesto", "Ejecutado", "Variacion ($)", "Cumplimiento (%)"];
        rows.push(header.join(';'));

        const traverse = (nodes) => {
            nodes.forEach(n => {
                const row = [
                    `"${n.cuenta_codigo}"`,
                    `"${n.cuenta_nombre}"`,
                    n.total_pres,
                    n.total_ejec,
                    n.total_var,
                    n.cumplimiento_porcentaje.toFixed(2).replace('.', ',')
                ];
                rows.push(row.join(';'));
                traverse(n.children);
            });
        };
        traverse(filteredTree);

        const totalRow = [
            "TOTALES",
            "",
            globalTotals.pres,
            globalTotals.ejec,
            globalTotals.var,
            ""
        ];
        rows.push(totalRow.join(';'));

        const csvString = "\uFEFF" + rows.join('\n');
        const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', `Ejecucion_${fechaInicio}_${fechaFin}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const renderNode = (node, level = 0) => {
        const hasChildren = node.children.length > 0;
        const isExpanded = expandedNodes[node.cuenta_codigo];
        const isGroup = hasChildren;

        const isGasto = node.cuenta_codigo.startsWith('5') || node.cuenta_codigo.startsWith('6');
        const isGood = isGasto ? node.total_var <= 0 : node.total_var >= 0;
        const varColor = isGood ? 'text-green-600' : 'text-red-600';

        return (
            <React.Fragment key={node.cuenta_codigo}>
                <tr className={`hover:bg-gray-50 border-b border-gray-100 ${level === 0 ? 'bg-gray-50' : ''}`}>
                    <td className="pl-4 py-2 whitespace-nowrap">
                        <div className="flex items-center" style={{ marginLeft: level * 20 }}>
                            {hasChildren ? (
                                <button onClick={() => toggleNode(node.cuenta_codigo)} className="mr-2 text-indigo-600 focus:outline-none">
                                    {isExpanded ? <FaChevronDown size={12} /> : <FaChevronRight size={12} />}
                                </button>
                            ) : <span className="w-5 inline-block"></span>}
                            <span className={`font-mono text-sm ${isGroup ? 'font-bold' : ''}`}>{node.cuenta_codigo}</span>
                        </div>
                    </td>
                    <td className="py-2 text-sm font-medium text-gray-700">
                        {node.cuenta_nombre} {node.is_virtual && <span className="text-xs text-orange-400 italic font-normal">(Calc)</span>}
                    </td>
                    <td className="py-2 pr-4 text-right font-mono text-sm text-gray-600">
                        ${node.total_pres.toLocaleString('es-CO')}
                    </td>
                    <td className="py-2 pr-4 text-right font-mono text-sm font-bold text-gray-800">
                        ${node.total_ejec.toLocaleString('es-CO')}
                    </td>
                    <td className={`py-2 pr-4 text-right font-mono text-sm font-bold ${varColor}`}>
                        ${node.total_var.toLocaleString('es-CO')}
                    </td>
                    <td className="py-2 text-center text-xs font-bold text-gray-500">
                        {node.cumplimiento_porcentaje.toFixed(1)}%
                    </td>
                </tr>
                {hasChildren && isExpanded && node.children.map(child => renderNode(child, level + 1))}
            </React.Fragment>
        );
    };

    if (authLoading) return <div>Cargando...</div>;

    return (
        <div className="min-h-screen bg-gray-50 p-6 md:p-8 font-sans">
            <div className="max-w-7xl mx-auto">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-8 gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-2">
                            <div className="p-2 bg-indigo-100 rounded text-indigo-600"><FaTable /></div>
                            Ejecución Presupuestal
                        </h1>
                        <p className="text-sm text-gray-500 mt-1 ml-1">Análisis por Rango de Fechas</p>
                    </div>

                    <div className="flex flex-wrap items-center gap-3 bg-white p-2 rounded-lg shadow-sm border border-gray-100">
                        {/* DATE RANGE PICKER */}
                        <div className="flex items-center gap-1 border-r pr-3 mr-1">
                            <span className="text-gray-400 text-xs font-bold uppercase mr-1">Desde:</span>
                            <input
                                type="date"
                                value={fechaInicio}
                                onChange={(e) => setFechaInicio(e.target.value)}
                                className="input input-xs font-bold border-gray-300 w-32"
                            />
                        </div>
                        <div className="flex items-center gap-1 border-r pr-3 mr-1">
                            <span className="text-gray-400 text-xs font-bold uppercase mr-1">Hasta:</span>
                            <input
                                type="date"
                                value={fechaFin}
                                onChange={(e) => setFechaFin(e.target.value)}
                                className="input input-xs font-bold border-gray-300 w-32"
                            />
                        </div>

                        <div className="relative">
                            <FaSearch className="absolute left-2 top-2 text-gray-300 transform scale-75" />
                            <input
                                type="text"
                                placeholder="Filtrar..."
                                className="input input-xs pl-7 w-32 border-gray-300 focus:border-indigo-500 transition-all"
                                value={searchTerm}
                                onChange={e => setSearchTerm(e.target.value)}
                            />
                        </div>

                        <div className="flex items-center ml-2 gap-2">
                            <button
                                onClick={handleExportCSV}
                                disabled={!filteredTree.length || loading}
                                className="btn btn-sm bg-green-600 hover:bg-green-700 text-white border-none shadow px-4 gap-2"
                                title="Exportar a CSV"
                            >
                                <FaFileCsv size={16} /> CSV
                            </button>

                            <button
                                onClick={handlePrintPDF}
                                disabled={!filteredTree.length || loading}
                                className="btn btn-sm bg-rose-600 hover:bg-rose-700 text-white border-none shadow px-4 gap-2"
                                title="Descargar PDF"
                            >
                                <FaFilePdf size={16} /> PDF
                            </button>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="bg-white p-5 rounded-lg shadow-sm border-l-4 border-blue-500">
                        <h3 className="text-gray-400 text-[10px] font-bold uppercase tracking-wider">Presupuesto (Total)</h3>
                        <p className="text-xl font-bold text-gray-800">${globalTotals.pres.toLocaleString('es-CO')}</p>
                    </div>
                    <div className="bg-white p-5 rounded-lg shadow-sm border-l-4 border-indigo-500">
                        <h3 className="text-gray-400 text-[10px] font-bold uppercase tracking-wider">Ejecución (Total)</h3>
                        <p className="text-xl font-bold text-gray-800">${globalTotals.ejec.toLocaleString('es-CO')}</p>
                    </div>
                    <div className={`bg-white p-5 rounded-lg shadow-sm border-l-4 ${globalTotals.var >= 0 ? 'border-green-500' : 'border-red-500'}`}>
                        <h3 className="text-gray-400 text-[10px] font-bold uppercase tracking-wider">Variación (Total)</h3>
                        <p className={`text-xl font-bold ${globalTotals.var >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            ${globalTotals.var.toLocaleString('es-CO')}
                        </p>
                    </div>
                </div>

                <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden min-h-[400px] p-4">
                    {loading ? (
                        <div className="flex justify-center items-center h-64"><FaSpinner className="animate-spin text-3xl text-indigo-500" /></div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-left">
                                <thead className="bg-gray-100 border-b">
                                    <tr>
                                        <th className="py-3 pl-8 text-xs font-bold text-gray-600 uppercase w-[30%]">Cuenta</th>
                                        <th className="py-3 text-xs font-bold text-gray-600 uppercase w-[25%]">Concepto</th>
                                        <th className="py-3 pr-4 text-right text-xs font-bold text-gray-600 uppercase w-[15%]">Presupuesto</th>
                                        <th className="py-3 pr-4 text-right text-xs font-bold text-gray-600 uppercase w-[15%]">Ejecutado</th>
                                        <th className="py-3 pr-4 text-right text-xs font-bold text-gray-600 uppercase w-[15%]">Variación</th>
                                        <th className="py-3 text-center text-xs font-bold text-gray-600 uppercase w-[5%]">%</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredTree.length > 0 ? filteredTree.map((node) => renderNode(node)) : (
                                        <tr><td colSpan="6" className="text-center py-20 text-gray-400">No hay datos que coincidan</td></tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
