'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { phService } from '../../../../lib/phService';
import * as planCuentasService from '../../../../lib/planCuentasService';
import { FaSave, FaCalculator, FaSync, FaChevronRight, FaChevronDown, FaFilePdf, FaSearch } from 'react-icons/fa';
import Swal from 'sweetalert2';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

// Helper: Float seguro
const safeFloat = (val) => {
    if (typeof val === 'number') return val;
    if (typeof val === 'string') {
        const clean = val.replace(/\./g, '').replace(/,/g, '.');
        return parseFloat(clean) || 0;
    }
    return 0;
};

// Helper: Detectar padre por codigo (Contabilidad)
// Ejs: 413505 -> 4135 -> 41 -> 4
const getPosibleParentCode = (codigo) => {
    if (!codigo || codigo.length <= 1) return null;

    // Nivel 1: 1 digito (4)
    // Nivel 2: 2 digitos (41)
    // Nivel 3: 4 digitos (4135)
    // Nivel 4: 6 digitos (413505)
    // Nivel 5: 8 digitos (41350501)

    const len = codigo.length;
    if (len === 2) return codigo.substring(0, 1); // 41 -> 4
    if (len === 4) return codigo.substring(0, 2); // 4135 -> 41
    if (len === 6) return codigo.substring(0, 4); // 413505 -> 4135
    if (len >= 8 && len % 2 === 0) return codigo.substring(0, len - 2); // 41350501 -> 413505

    // Fallback: quitar 1 car? Mejor logica estandar PUC:
    return codigo.substring(0, len - 1);
};

export default function GestionPresupuestoPage() {
    const { user, loading: authLoading } = useAuth();
    const [anio, setAnio] = useState(new Date().getFullYear());
    const [treeData, setTreeData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [expandedNodes, setExpandedNodes] = useState({});
    const [searchTerm, setSearchTerm] = useState('');
    const [availableYears, setAvailableYears] = useState([]);

    useEffect(() => {
        const currentYear = new Date().getFullYear();
        const years = [];
        for (let i = currentYear - 2; i <= 2060; i++) {
            years.push(i);
        }
        setAvailableYears(years);
    }, []);

    useEffect(() => {
        if (!authLoading && user?.empresaId) {
            setTreeData([]);
            loadData();
        }
    }, [authLoading, user, anio]);

    const formatNumber = (num) => {
        return new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 }).format(num || 0);
    };

    // --- LOGICA DEL ARBOL ROBUSTA ---
    const buildTree = (cuentasFlat, presupuestos) => {
        const map = {};
        const roots = [];

        // 0. Ordenar por codigo (Cortos primero ayuda a crear padres antes? No, map lo resuelve)
        // Mejor ordenar alfabéticamente para visualización
        cuentasFlat.sort((a, b) => a.codigo.localeCompare(b.codigo));

        // 1. Indexar todo
        cuentasFlat.forEach(c => {
            // Solo Clases 4, 5, 6
            if (!['4', '5', '6'].some(p => c.codigo.startsWith(p))) return;

            const pres = presupuestos.find(p => p.cuenta_id === c.id);
            let valAnual = 0;
            if (pres) valAnual = safeFloat(pres.valor_anual);

            map[c.codigo] = { // CLAVE ES CODIGO, NO ID (Mas seguro para PUC)
                ...c,
                children: [],
                presupuesto: {
                    ...(pres || {}),
                    cuenta_id: c.id,
                    valor_anual: valAnual,
                    is_modified: false
                },
                total_rollup: 0
            };
        });

        // 2. Armar Jerarquia basada en CODIGOS
        Object.values(map).forEach(node => {
            const parentCode = getPosibleParentCode(node.codigo);
            // Intentar encontrar padre en el mapa
            if (parentCode && map[parentCode]) {
                map[parentCode].children.push(node);
            } else {
                // Si no encuentro padre (y soy 4, 5, 6), soy root
                roots.push(node);
            }
        });

        return { roots };
    };

    const recalculateRollups = (nodes) => {
        let sum = 0;
        nodes.forEach(node => {
            const childrenSum = recalculateRollups(node.children);

            const ownVal = safeFloat(node.presupuesto.valor_anual);
            // La magia: Total = Mis Hijos + Mi Valor Directo
            node.total_rollup = childrenSum + ownVal;
            sum += node.total_rollup;
        });
        return sum;
    };

    const loadData = async () => {
        setLoading(true);
        try {
            const responseCuentas = await planCuentasService.getPlanCuentasFlat({});
            const rawCuentas = Array.isArray(responseCuentas) ? responseCuentas : (responseCuentas.data || []);
            const pres = await phService.getPresupuestos(anio);

            // Construir usando Codigos
            const { roots } = buildTree(rawCuentas, pres);

            // Recalculo
            recalculateRollups(roots);

            setTreeData(roots);

            // Expandir
            const initialExpanded = {};
            const expand = (nodes, depth) => {
                nodes.forEach(n => {
                    if (depth < 2) initialExpanded[n.id] = true;
                    if (n.children.length) expand(n.children, depth + 1);
                });
            };
            expand(roots, 0);
            setExpandedNodes(initialExpanded);

        } catch (error) {
            console.error(error);
            Swal.fire('Error', 'No se cargaron los datos.', 'error');
        } finally {
            setLoading(false);
        }
    };

    const toggleNode = (id) => {
        setExpandedNodes(prev => ({ ...prev, [id]: !prev[id] }));
    };

    const handleValueChange = (nodeId, strVal) => {
        const cleanStr = strVal.replace(/\./g, '');
        const val = parseFloat(cleanStr) || 0;

        const newTree = [...treeData]; // Shallow copy roots is enough if we traverse/mutate deep objects ref? 
        // No, React state needs new references to trigger render on affected nodes.
        // JSON parse/stringify is safest/easiest brute force for deep tree.
        const deepCopy = JSON.parse(JSON.stringify(newTree));

        const updateRecursive = (nodes) => {
            for (let node of nodes) {
                if (node.id === nodeId) {
                    node.presupuesto.valor_anual = val;
                    node.presupuesto.is_modified = true;
                    // Distribuir
                    const m = Math.round(val / 12);
                    for (let i = 1; i <= 12; i++) node.presupuesto[`mes_${i.toString().padStart(2, '0')}`] = m;
                    return true;
                }
                if (node.children.length) {
                    if (updateRecursive(node.children)) return true;
                }
            }
            return false;
        };

        updateRecursive(deepCopy);
        recalculateRollups(deepCopy);
        setTreeData(deepCopy);
    };

    const handleSave = async () => {
        const itemsToSave = [];
        const collect = (nodes) => {
            nodes.forEach(n => {
                if (n.presupuesto.valor_anual > 0 || n.presupuesto.is_modified) {
                    itemsToSave.push(n.presupuesto);
                }
                collect(n.children);
            });
        };
        collect(treeData);

        if (!itemsToSave.length) {
            Swal.fire('Info', 'Nada nuevo que guardar.', 'info');
            return;
        }

        setSaving(true);
        try {
            await phService.savePresupuestosMasivo({
                anio: parseInt(anio),
                items: itemsToSave
            });
            Swal.fire('Guardado', 'Presupuesto actualizado.', 'success');
        } catch (e) {
            console.error(e);
            Swal.fire('Error', 'Fallo al guardar.', 'error');
        } finally {
            setSaving(false);
        }
    };

    const generatePDF = () => {
        const doc = new jsPDF();
        doc.text(`Presupuesto Oficial ${anio}`, 14, 20);
        doc.setFontSize(10);
        doc.text(`${user?.empresaNombre || 'Consorcio'}`, 14, 26);
        doc.text(`Fecha: ${new Date().toLocaleDateString()}`, 14, 32);

        const rows = [];
        const traverse = (nodes, level = 0) => {
            nodes.forEach(n => {
                rows.push([
                    n.codigo,
                    { content: '  '.repeat(level) + n.nombre, styles: { fontStyle: n.children.length ? 'bold' : 'normal' } },
                    { content: '$ ' + formatNumber(n.total_rollup), styles: { halign: 'right', fontStyle: 'bold' } }
                ]);
                traverse(n.children, level + 1);
            });
        };
        traverse(treeData);

        autoTable(doc, {
            startY: 40,
            head: [['Código', 'Concepto', 'Presupuesto (Anual)']],
            body: rows,
            columnStyles: { 0: { cellWidth: 35 }, 2: { cellWidth: 45 } },
            theme: 'grid',
            headStyles: { fillColor: [50, 50, 50] }
        });
        doc.save(`Presupuesto_${anio}.pdf`);
    };

    const renderNode = (node, level = 0) => {
        if (searchTerm) {
            const hasMatch = (n) => {
                if (n.nombre.toLowerCase().includes(searchTerm.toLowerCase()) || n.codigo.includes(searchTerm)) return true;
                return n.children.some(hasMatch);
            };
            if (!hasMatch(node)) return null;
        }

        const hasChildren = node.children.length > 0;
        const isExpanded = searchTerm ? true : expandedNodes[node.id];
        const isGroup = hasChildren;

        return (
            <React.Fragment key={node.id}>
                <tr className={`${level === 0 ? 'bg-gray-100' : 'bg-white'} border-b border-gray-100 hover:bg-indigo-50 transition-colors`}>
                    <td className="py-2 pl-4">
                        <div className="flex items-center" style={{ marginLeft: level * 20 }}>
                            {hasChildren ? (
                                <button onClick={() => toggleNode(node.id)} className="mr-2 text-indigo-600 focus:outline-none">
                                    {isExpanded ? <FaChevronDown size={12} /> : <FaChevronRight size={12} />}
                                </button>
                            ) : <span className="w-5 inline-block"></span>}
                            <span className={`font-mono text-sm ${isGroup ? 'font-bold text-gray-800' : 'text-gray-600'}`}>{node.codigo}</span>
                        </div>
                    </td>
                    <td className="py-2">
                        <span className={`text-sm ${isGroup ? 'font-bold text-gray-800' : 'text-gray-600'}`}>{node.nombre}</span>
                    </td>
                    <td className="py-2 pr-6 text-right">
                        {isGroup ? (
                            // Solo Display
                            <span className="font-bold text-gray-900 text-sm">
                                $ {formatNumber(node.total_rollup)}
                            </span>
                        ) : (
                            // Input Editable
                            <input
                                type="text"
                                className="input input-sm w-40 text-right font-semibold border-gray-300 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded transition-all"
                                value={formatNumber(node.presupuesto.valor_anual)}
                                onChange={(e) => handleValueChange(node.id, e.target.value)}
                            />
                        )}
                    </td>
                </tr>
                {hasChildren && isExpanded && node.children.map(child => renderNode(child, level + 1))}
            </React.Fragment>
        );
    };

    if (authLoading) return <div className="p-10 flex justify-center"><span className="loading loading-spinner text-primary"></span></div>;

    return (
        <div className="min-h-screen bg-gray-50 p-8 font-sans">
            <div className="max-w-6xl mx-auto bg-white rounded-xl shadow-xl p-8 border border-gray-100">
                <div className="flex justify-between items-center mb-6">
                    <div>
                        <h1 className="text-3xl font-bold flex items-center gap-3 text-gray-800">
                            <div className="bg-indigo-100 p-2 rounded-lg text-indigo-600"><FaCalculator /></div>
                            Matriz Presupuestal
                        </h1>
                        <p className="text-sm text-gray-500 mt-1 ml-1">
                            Definición de proyecciones anuales (Valores se acumulan automáticamente).
                        </p>
                    </div>
                    <div className="flex items-center gap-3 bg-gray-100 p-2 rounded-lg">
                        <span className="font-bold text-sm text-gray-600 pl-2">Periodo Fiscal:</span>
                        <select value={anio} onChange={e => setAnio(e.target.value)} className="select select-bordered select-sm w-28 font-bold bg-white shadow-sm border-gray-300">
                            {availableYears.map(y => <option key={y} value={y}>{y}</option>)}
                        </select>
                    </div>
                </div>

                <div className="flex justify-between mb-6 bg-white p-1 rounded-xl">
                    <div className="relative w-1/3">
                        <FaSearch className="absolute left-3 top-3 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Buscar en el presupuesto..."
                            className="input input-sm pl-10 w-full border-gray-300 focus:border-indigo-500 rounded-lg"
                            value={searchTerm}
                            onChange={e => setSearchTerm(e.target.value)}
                        />
                    </div>
                    <div className="flex gap-3">
                        <button onClick={generatePDF} className="btn btn-sm btn-outline gap-2 border-gray-300 text-gray-700 hover:bg-gray-50 hover:text-red-600 hover:border-red-200">
                            <FaFilePdf className="text-red-500" /> Exportar PDF
                        </button>
                        <button onClick={handleSave} disabled={saving} className={`btn btn-sm px-6 gap-2 text-white ${saving ? 'bg-gray-400' : 'bg-indigo-600 hover:bg-indigo-700'} border-none shadow-md hover:shadow-lg transition-all`}>
                            <FaSave /> {saving ? 'Guardando...' : 'Guardar Cambios'}
                        </button>
                    </div>
                </div>

                <div className="border border-gray-200 rounded-lg overflow-hidden min-h-[500px]">
                    <table className="w-full text-left">
                        <thead className="bg-gray-50 border-b border-gray-200">
                            <tr>
                                <th className="py-4 pl-8 text-xs font-bold text-gray-500 uppercase tracking-wider w-[40%]">Código Contable</th>
                                <th className="py-4 text-xs font-bold text-gray-500 uppercase tracking-wider w-[35%]">Descripción / Rubro</th>
                                <th className="py-4 pr-8 text-right text-xs font-bold text-gray-500 uppercase tracking-wider w-[25%]">Monto Anual</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {treeData.length > 0 ? treeData.map(node => renderNode(node)) : (
                                <tr><td colSpan="3" className="p-10 text-center text-gray-400 italic">
                                    {loading ? 'Cargando estructura contable...' : 'No se encontraron cuentas.'}
                                </td></tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
