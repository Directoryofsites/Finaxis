'use client';

import React, { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';


import {
    FaSearch,
    FaPlus,
    FaBuilding,
    FaFileCsv,
    FaFilePdf,
    FaEdit,
    FaTrash,
    FaHome,
    FaCar,
    FaPaw,
    FaExclamationTriangle,
    FaBook,
    FaCheckSquare,
    FaSquare,
    FaLayerGroup
} from 'react-icons/fa';


import { useAuth } from '../../context/AuthContext';
import { phService } from '../../../lib/phService';
import { useRecaudos } from '../../../contexts/RecaudosContext'; // IMPORTED
import ManualButton from '../../components/ManualButton';

// --- ESTILOS REUSABLES (Estandarizados) ---
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none pl-10";

const MassEditModal = ({ selectedCount, availableModules, onClose, onExecute, loading }) => {
    const [changes, setChanges] = useState({}); // { modId: 'ADD' | 'REMOVE' | null }

    const toggleChange = (modId) => {
        setChanges(prev => {
            const current = prev[modId];
            let next;
            if (!current) next = 'ADD';
            else if (current === 'ADD') next = 'REMOVE';
            else next = null;

            return { ...prev, [modId]: next };
        });
    };

    const execute = () => {
        const toAdd = Object.keys(changes).filter(k => changes[k] === 'ADD').map(Number);
        const toRemove = Object.keys(changes).filter(k => changes[k] === 'REMOVE').map(Number);

        if (toAdd.length === 0 && toRemove.length === 0) {
            alert("No ha seleccionado ningún cambio. Por favor haga clic sobre los Módulos (Residencial/Local) para marcarlos en VERDE (Asignar) o ROJO (Remover) antes de aplicar.");
            return;
        }

        if (window.confirm(`¿Confirmar cambios en ${selectedCount} unidades?\n- Asignar: ${toAdd.length}\n- Remover: ${toRemove.length}`)) {
            onExecute(toAdd, toRemove);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 animate-fadeIn">
            <div className="bg-white rounded-xl shadow-2xl p-6 w-full max-w-lg">
                <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                    <FaLayerGroup className="text-indigo-600" />
                    Edición Masiva ({selectedCount} unidades)
                </h3>

                <p className="text-sm text-gray-500 mb-4 bg-blue-50 p-3 rounded-lg border border-blue-100">
                    <strong>Instrucción:</strong> Haga clic sobre los ítems de la lista para cambiar su estado:
                    <br />- <span className="text-green-600 font-bold">1 Clic (Verde):</span> Asignar Módulo.
                    <br />- <span className="text-red-500 font-bold">2 Clics (Rojo):</span> Remover Módulo.
                </p>

                <div className="space-y-2 mb-6 max-h-60 overflow-y-auto">
                    {availableModules.map(m => {
                        const status = changes[m.id];
                        let colorClass = "bg-gray-100 text-gray-400 border-gray-200";
                        let actionText = "Sin cambios";

                        if (status === 'ADD') {
                            colorClass = "bg-green-100 text-green-700 border-green-300";
                            actionText = "Asignar";
                        } else if (status === 'REMOVE') {
                            colorClass = "bg-red-100 text-red-700 border-red-300";
                            actionText = "Remover";
                        }

                        return (
                            <div
                                key={m.id}
                                onClick={() => toggleChange(m.id)}
                                className={`p-3 rounded-lg border cursor-pointer flex justify-between items-center transition-all ${colorClass}`}
                            >
                                <span className="font-semibold">{m.nombre}</span>
                                <span className="text-xs uppercase font-bold tracking-wider">{actionText}</span>
                            </div>
                        );
                    })}
                </div>

                <div className="flex justify-end gap-3">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                    >
                        Cancelar
                    </button>
                    <button
                        onClick={execute}
                        disabled={loading}
                        className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                    >
                        {loading ? 'Procesando...' : 'Aplicar Cambios'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default function GestionUnidadesPage() {
    const { user, loading: authLoading } = useAuth();
    const { labels } = useRecaudos(); // HOOK

    const [unidades, setUnidades] = useState([]);
    const [torres, setTorres] = useState([]); // New State
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedTorre, setSelectedTorre] = useState(''); // New Filter State

    // Mass Edit State
    const [selectedUnits, setSelectedUnits] = useState(new Set());
    const [showMassEditModal, setShowMassEditModal] = useState(false);
    const [availableModules, setAvailableModules] = useState([]);
    const [massActionLoading, setMassActionLoading] = useState(false);

    // Carga de datos
    useEffect(() => {
        if (!authLoading) {
            if (user && user.empresaId) {
                const fetchUnidades = async () => {
                    try {
                        setLoading(true);
                        setError(null);
                        const [unitsData, torresData, modulosData] = await Promise.all([
                            phService.getUnidades(),
                            phService.getTorres(),
                            phService.getModulos()
                        ]);
                        setUnidades(unitsData);
                        setTorres(torresData);
                        setAvailableModules(modulosData);
                    } catch (err) {
                        setError(err.response?.data?.detail || 'Error al obtener los datos');
                    } finally {
                        setLoading(false);
                    }
                };
                fetchUnidades();
            } else {
                setLoading(false);
                setError("No se pudo identificar la empresa del usuario.");
            }
        }
    }, [user, authLoading]);

    // Lógica de Búsqueda
    const unidadesFiltradas = useMemo(() => {
        let result = unidades;

        // Filter by Tower
        if (selectedTorre) {
            result = result.filter(u => u.torre_id === parseInt(selectedTorre));
        }

        // Filter by Search Term
        if (searchTerm.length >= 2) {
            const lowerTerm = searchTerm.toLowerCase();
            result = result.filter(u =>
                u.codigo.toLowerCase().includes(lowerTerm) ||
                (u.torre_nombre && u.torre_nombre.toLowerCase().includes(lowerTerm))
            );
        }
        return result;
    }, [unidades, searchTerm, selectedTorre]);

    const handleDelete = async (id, codigo) => {
        if (!window.confirm(`¿Estás seguro de eliminar: ${codigo}?`)) return;
        try {
            await phService.deleteUnidad(id);
            setUnidades(prev => prev.filter(u => u.id !== id));
            alert('Registro eliminado correctamente.');
        } catch (err) {
            alert('Error al eliminar: ' + (err.response?.data?.detail || err.message));
        }
    };

    // --- MASS SELECTION LOGIC ---
    const handleSelectAll = (checked) => {
        if (checked) {
            const allIds = new Set(unidadesFiltradas.map(u => u.id));
            setSelectedUnits(allIds);
        } else {
            setSelectedUnits(new Set());
        }
    };

    const handleSelectOne = (id, checked) => {
        const newSet = new Set(selectedUnits);
        if (checked) {
            newSet.add(id);
        } else {
            newSet.delete(id);
        }
        setSelectedUnits(newSet);
    };

    const handleMassUpdate = async (modulesToAdd, modulesToRemove) => {
        if (selectedUnits.size === 0) return;

        try {
            setMassActionLoading(true);
            await phService.massUpdateModules({
                unidades_ids: Array.from(selectedUnits),
                add_modules_ids: modulesToAdd,
                remove_modules_ids: modulesToRemove
            });

            alert('Actualización masiva completada');
            setShowMassEditModal(false);
            setSelectedUnits(new Set());

            // Reload data
            const freshData = await phService.getUnidades();
            setUnidades(freshData);

        } catch (err) {
            alert('Error updating modules: ' + (err.response?.data?.detail || err.message));
        } finally {
            setMassActionLoading(false);
        }
    };


    // --- PDF EXPORT FUNCTION ---
    const handleExportPDF = () => {
        try {
            const doc = new jsPDF();

            // Header
            doc.setFontSize(18);
            doc.setTextColor(40);
            doc.text(`Reporte de ${labels.unidad}s - ${labels.module}`, 14, 22);
            doc.setFontSize(11);
            doc.setTextColor(100);
            doc.text(`Generado el: ${new Date().toLocaleDateString()}`, 14, 30);

            // Table Data
            const tableColumn = ["Código", "Tipo", labels.coeficiente, "Grupo/Torre", "Matrícula"];
            const tableRows = unidadesFiltradas.map(u => [
                u.codigo,
                u.tipo,
                `${u.coeficiente}%`,
                u.torre_nombre || '',
                u.matricula_inmobiliaria || ''
            ]);

            // AutoTable
            autoTable(doc, {
                head: [tableColumn],
                body: tableRows,
                startY: 40,
                theme: 'grid',
                headStyles: { fillColor: [79, 70, 229] }, // Indigo-600
                styles: { fontSize: 10 },
            });

            doc.save(`activos_recaudo_${new Date().toISOString().slice(0, 10)}.pdf`);
        } catch (error) {
            console.error("Error exporting PDF:", error);
            alert("Error al generar el PDF. Por favor intente nuevamente.");
        }
    };

    if (authLoading || loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
                <FaBuilding className="text-indigo-300 text-6xl mb-4 animate-pulse" />
                <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando {labels.module}...</p>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
            {/* Scripts for PDF */}
            <div className="max-w-7xl mx-auto">

                {/* ENCABEZADO */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                    <div>
                        <div className="flex items-center gap-3 mt-3">
                            <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                                <FaHome className="text-2xl" />
                            </div>
                            <div>
                                <h1 className="text-3xl font-bold text-gray-800">Maestro de {labels.unidad}s</h1>
                                <p className="text-gray-500 text-sm">Administración de {labels.unidad.toLowerCase()}s y activos de cobro.</p>
                            </div>
                        </div>
                    </div>

                    <div className="flex gap-3">
                        <ManualButton 
                            manualPath="unidades.html"
                            title="Manual de Gestión de Unidades"
                            position="header"
                        />
                        {selectedUnits.size > 0 && (
                            <button
                                onClick={() => setShowMassEditModal(true)}
                                className="flex items-center gap-2 px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition-all shadow-md font-bold animate-pulse"
                            >
                                <FaLayerGroup /> <span>Acciones Masivas ({selectedUnits.size})</span>
                            </button>
                        )}
                        <button onClick={handleExportPDF} className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-all shadow-md font-medium">
                            <FaFilePdf /> <span>PDF</span>
                        </button>
                        <Link href="/ph/unidades/crear" className="flex items-center gap-2 px-5 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-all shadow-md transform hover:-translate-y-0.5 font-medium">
                            <FaPlus /> <span>Nueva {labels.unidad}</span>
                        </Link>
                    </div>
                </div>

                {showMassEditModal && (
                    <MassEditModal
                        selectedCount={selectedUnits.size}
                        availableModules={availableModules}
                        onClose={() => setShowMassEditModal(false)}
                        onExecute={handleMassUpdate}
                        loading={massActionLoading}
                    />
                )}

                {/* CARD PRINCIPAL */}
                <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 animate-fadeIn">

                    {/* FILTROS */}
                    <div className="flex flex-col md:flex-row justify-between items-end mb-6 gap-4">
                        <div className="w-full md:w-2/3 flex gap-4">
                            <div className="flex-1">
                                <label className={labelClass}>Buscar {labels.unidad}</label>
                                <div className="relative">
                                    <input
                                        type="text"
                                        placeholder={`Codigo, nombre o identificador...`}
                                        className={inputClass}
                                        value={searchTerm}
                                        onChange={(e) => setSearchTerm(e.target.value)}
                                    />
                                    <FaSearch className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                                </div>
                            </div>
                            <div className="w-1/3">
                                <label className={labelClass}>Filtrar por Grupo/Torre</label>
                                <select
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 text-sm outline-none"
                                    value={selectedTorre}
                                    onChange={(e) => setSelectedTorre(e.target.value)}
                                >
                                    <option value="">-- Todas --</option>
                                    {torres.map(t => (
                                        <option key={t.id} value={t.id}>{t.nombre}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    </div>

                    {error && (
                        <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded-r-lg flex items-center gap-3 animate-pulse">
                            <FaExclamationTriangle className="text-xl" />
                            <p>{error}</p>
                        </div>
                    )}

                    {/* TABLA */}
                    <div className="overflow-x-auto rounded-lg border border-gray-200">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-slate-100">
                                <tr>
                                    <th className="py-3 px-4 w-12 text-center">
                                        <button
                                            onClick={() => handleSelectAll(selectedUnits.size < unidadesFiltradas.length)}
                                            className="text-gray-500 hover:text-indigo-600"
                                        >
                                            {unidadesFiltradas.length > 0 && selectedUnits.size === unidadesFiltradas.length ? <FaCheckSquare /> : <FaSquare />}
                                        </button>
                                    </th>
                                    <th className="py-3 px-4 text-left text-xs font-bold text-gray-600 uppercase w-24">Código</th>
                                    <th className="py-3 px-4 text-left text-xs font-bold text-gray-600 uppercase">Tipo</th>
                                    <th className="py-3 px-4 text-left text-xs font-bold text-gray-600 uppercase">{labels.coeficiente}</th>
                                    <th className="py-3 px-4 text-center text-xs font-bold text-gray-600 uppercase">Grupo/Ubic</th>
                                    <th className="py-3 px-4 text-center text-xs font-bold text-gray-600 uppercase w-32">Acciones</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100 bg-white">
                                {unidadesFiltradas.length > 0 ? (
                                    unidadesFiltradas.map((u) => (
                                        <tr key={u.id} className={`hover:bg-indigo-50/20 transition-colors group ${selectedUnits.has(u.id) ? 'bg-indigo-50' : ''}`}>
                                            <td className="py-3 px-4 text-center">
                                                <button
                                                    onClick={() => handleSelectOne(u.id, !selectedUnits.has(u.id))}
                                                    className={`${selectedUnits.has(u.id) ? 'text-indigo-600' : 'text-gray-300 hover:text-gray-500'}`}
                                                >
                                                    {selectedUnits.has(u.id) ? <FaCheckSquare /> : <FaSquare />}
                                                </button>
                                            </td>
                                            <td className="py-3 px-4 text-sm font-bold text-indigo-900">
                                                {u.codigo}
                                            </td>
                                            <td className="py-3 px-4 text-sm text-gray-600">
                                                {u.tipo}
                                            </td>
                                            <td className="py-3 px-4 text-sm font-mono text-gray-800">
                                                {parseFloat(u.coeficiente).toFixed(4)}%
                                            </td>
                                            <td className="py-3 px-4 text-center">
                                                <div className="flex justify-center gap-3 text-gray-400">
                                                    {u.torre && <span title={`Grupo: ${u.torre.nombre}`}><FaBuilding className="text-gray-500" /> {u.torre.nombre}</span>}
                                                </div>
                                            </td>
                                            <td className="py-3 px-4 text-center">
                                                <div className="flex justify-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                    <Link href={`/ph/unidades/editar/${u.id}`} className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg" title="Editar">
                                                        <FaEdit />
                                                    </Link>
                                                    <button onClick={() => handleDelete(u.id, u.codigo)} className="p-2 text-red-600 hover:bg-red-50 rounded-lg" title="Eliminar">
                                                        <FaTrash />
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan="5" className="py-10 text-center text-gray-400 italic">
                                            No se encontraron registros.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
}
