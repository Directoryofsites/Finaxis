'use client';

import React, { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import Script from 'next/script';
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
    FaBook
} from 'react-icons/fa';

import BotonRegresar from '../../components/BotonRegresar';
import { useAuth } from '../../context/AuthContext';
import { phService } from '../../../lib/phService';

// --- ESTILOS REUSABLES (Estandarizados) ---
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none pl-10";

export default function GestionUnidadesPage() {
    const { user, loading: authLoading } = useAuth();
    const [unidades, setUnidades] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');

    // Carga de datos
    useEffect(() => {
        if (!authLoading) {
            if (user && user.empresaId) {
                const fetchUnidades = async () => {
                    try {
                        setLoading(true);
                        setError(null);
                        const data = await phService.getUnidades();
                        setUnidades(data);
                    } catch (err) {
                        setError(err.response?.data?.detail || 'Error al obtener las unidades');
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
        if (searchTerm.length < 2) return unidades;
        const lowerTerm = searchTerm.toLowerCase();
        return unidades.filter(u =>
            u.codigo.toLowerCase().includes(lowerTerm) ||
            (u.torre_nombre && u.torre_nombre.toLowerCase().includes(lowerTerm))
        );
    }, [unidades, searchTerm]);

    const handleDelete = async (id, codigo) => {
        if (!window.confirm(`¿Estás seguro de eliminar la unidad ${codigo}?`)) return;
        try {
            await phService.deleteUnidad(id);
            setUnidades(prev => prev.filter(u => u.id !== id));
            alert('Unidad eliminada correctamente.');
        } catch (err) {
            alert('Error al eliminar: ' + (err.response?.data?.detail || err.message));
        }
    };

    // --- PDF EXPORT FUNCTION ---
    const handleExportPDF = () => {
        if (typeof window !== 'undefined' && window.jspdf && window.jspdf.jsPDF) {
            const doc = new window.jspdf.jsPDF();

            // Header
            doc.setFontSize(18);
            doc.setTextColor(40);
            doc.text("Reporte de Unidades - Propiedad Horizontal", 14, 22);
            doc.setFontSize(11);
            doc.setTextColor(100);
            doc.text(`Generado el: ${new Date().toLocaleDateString()}`, 14, 30);

            // Table Data
            const tableColumn = ["Código", "Tipo", "Coeficiente", "Torre", "Matrícula"];
            const tableRows = unidadesFiltradas.map(u => [
                u.codigo,
                u.tipo,
                `${u.coeficiente}%`,
                u.torre ? u.torre.nombre : '',
                u.matricula_inmobiliaria || ''
            ]);

            // AutoTable
            doc.autoTable({
                head: [tableColumn],
                body: tableRows,
                startY: 40,
                theme: 'grid',
                headStyles: { fillColor: [79, 70, 229] }, // Indigo-600
                styles: { fontSize: 10 },
            });

            doc.save(`unidades_ph_${new Date().toISOString().slice(0, 10)}.pdf`);
        } else {
            alert('Librería PDF no cargada. Por favor recarga la página.');
        }
    };

    if (authLoading || loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
                <FaBuilding className="text-indigo-300 text-6xl mb-4 animate-pulse" />
                <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando Catastro PH...</p>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
            {/* Scripts for PDF */}
            <Script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js" strategy="afterInteractive" />
            <Script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.5.28/jspdf.plugin.autotable.min.js" strategy="afterInteractive" />

            <div className="max-w-7xl mx-auto">

                {/* ENCABEZADO */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                    <div>
                        <BotonRegresar />
                        <div className="flex items-center gap-3 mt-3">
                            <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                                <FaHome className="text-2xl" />
                            </div>
                            <div>
                                <h1 className="text-3xl font-bold text-gray-800">Maestro de Unidades</h1>
                                <p className="text-gray-500 text-sm">Administración de apartamentos, casas y zonas privadas.</p>
                            </div>
                        </div>
                    </div>

                    <div className="flex gap-3">
                        <button onClick={handleExportPDF} className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-all shadow-md font-medium">
                            <FaFilePdf /> <span>PDF</span>
                        </button>
                        <Link href="/ph/unidades/crear" className="flex items-center gap-2 px-5 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-all shadow-md transform hover:-translate-y-0.5 font-medium">
                            <FaPlus /> <span>Nueva Unidad</span>
                        </Link>
                    </div>
                </div>

                {/* CARD PRINCIPAL */}
                <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 animate-fadeIn">

                    {/* FILTROS */}
                    <div className="flex flex-col md:flex-row justify-between items-end mb-6 gap-4">
                        <div className="w-full md:w-1/2">
                            <label className={labelClass}>Buscar Unidad</label>
                            <div className="relative">
                                <input
                                    type="text"
                                    placeholder="Número de apartamento, torre..."
                                    className={inputClass}
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                />
                                <FaSearch className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
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
                                    <th className="py-3 px-4 text-left text-xs font-bold text-gray-600 uppercase w-24">Código</th>
                                    <th className="py-3 px-4 text-left text-xs font-bold text-gray-600 uppercase">Tipo</th>
                                    <th className="py-3 px-4 text-left text-xs font-bold text-gray-600 uppercase">Coeficiente</th>
                                    <th className="py-3 px-4 text-center text-xs font-bold text-gray-600 uppercase">Detalles</th>
                                    <th className="py-3 px-4 text-center text-xs font-bold text-gray-600 uppercase w-32">Acciones</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100 bg-white">
                                {unidadesFiltradas.length > 0 ? (
                                    unidadesFiltradas.map((u) => (
                                        <tr key={u.id} className="hover:bg-indigo-50/20 transition-colors group">
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
                                                    {u.torre && <span title={`Torre: ${u.torre.nombre}`}><FaBuilding className="text-gray-500" /></span>}
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
                                            No se encontraron unidades.
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
