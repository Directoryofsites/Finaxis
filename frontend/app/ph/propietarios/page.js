'use client';

import React, { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import { FaUsers, FaBuilding, FaSearch, FaPhone, FaEnvelope, FaIdCard, FaFileExcel, FaHandshake, FaPlus, FaFilePdf, FaExchangeAlt } from 'react-icons/fa';
import BotonRegresar from '../../components/BotonRegresar';
import { useAuth } from '../../context/AuthContext';
import { phService } from '../../../lib/phService';

export default function DirectorioPropietariosPage() {
    const { user, loading: authLoading } = useAuth();
    const [propietarios, setPropietarios] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        if (!authLoading && user?.empresaId) {
            loadPropietarios();
        }
    }, [user, authLoading]);

    const loadPropietarios = async () => {
        try {
            setLoading(true);
            const data = await phService.getPropietarios();
            setPropietarios(data);
        } catch (error) {
            console.error("Error cargando directorio:", error);
            alert("Error al cargar el directorio de propietarios.");
        } finally {
            setLoading(false);
        }
    };

    const propietariosFiltrados = useMemo(() => {
        if (!searchTerm) return propietarios;
        const lower = searchTerm.toLowerCase();
        return propietarios.filter(p =>
            (p.razon_social || '').toLowerCase().includes(lower) ||
            (p.numero_documento || '').includes(lower) ||
            p.unidades.some(u => u.codigo.toLowerCase().includes(lower))
        );
    }, [propietarios, searchTerm]);

    // --- PDF EXPORT FUNCTION ---
    const handleExportPDF = () => {
        try {
            const doc = new jsPDF();

            // Header
            doc.setFontSize(18);
            doc.setTextColor(40);
            doc.text("Directorio de Propietarios - Propiedad Horizontal", 14, 22);
            doc.setFontSize(11);
            doc.setTextColor(100);
            doc.text(`Generado el: ${new Date().toLocaleDateString()}`, 14, 30);

            // Table Data
            const tableColumn = ["Propietario / Razón Social", "Identificación", "Teléfono", "Email", "Propiedades", "Coeficiente"];
            const tableRows = propietariosFiltrados.map(p => [
                p.razon_social || '',
                p.numero_documento || '',
                p.contacto_telefono,
                p.contacto_email,
                p.unidades.map(u => u.codigo).join(", "),
                `${p.total_coeficiente.toFixed(4)}%`
            ]);

            // AutoTable
            autoTable(doc, {
                head: [tableColumn],
                body: tableRows,
                startY: 40,
                theme: 'grid',
                headStyles: { fillColor: [59, 130, 246] }, // Blue-500
                styles: { fontSize: 9 },
            });

            doc.save(`directorio_propietarios_${new Date().toISOString().slice(0, 10)}.pdf`);
        } catch (error) {
            console.error("Error exporting PDF:", error);
            alert("Error al generar el PDF. Por favor intente nuevamente.");
        }
    };

    if (authLoading || loading) {
        return <div className="p-8 text-center text-gray-500 animate-pulse">Cargando directorio...</div>;
    }

    return (
        <div className="min-h-screen bg-gray-50 p-6">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                {/* Header */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                    <div>
                        <BotonRegresar href="/ph" />
                        <div className="flex items-center gap-3 mt-3">
                            <div className="p-3 bg-blue-100 rounded-xl text-blue-600">
                                <FaUsers className="text-2xl" />
                            </div>
                            <div>
                                <h1 className="text-3xl font-bold text-gray-800">Directorio de Propietarios</h1>
                                <p className="text-gray-500">Gestión unificada de propietarios y sus unidades inmobiliarias.</p>
                            </div>
                        </div>
                    </div>

                    <div className="flex gap-3">
                        <button onClick={handleExportPDF} className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-all shadow-md font-medium">
                            <FaFilePdf /> <span>PDF</span>
                        </button>
                        <Link href="/ph/unidades" className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-all shadow-md font-medium">
                            <FaExchangeAlt /> <span>Asignar Unidades</span>
                        </Link>
                        <Link href="/admin/terceros" className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-all shadow-md font-medium">
                            <FaPlus /> <span>Nuevo Propietario</span>
                        </Link>
                    </div>
                </div>

                {/* Search */}
                <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 mb-6 flex gap-4">
                    <div className="relative flex-1">
                        <FaSearch className="absolute left-3 top-3.5 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Buscar por nombre, documento o número de unidad..."
                            className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                </div>

                {/* Grid / Table */}
                <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Propietario / Razón Social</th>
                                <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Identificación</th>
                                <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Datos de Contacto</th>
                                <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Propiedades Asociadas</th>
                                <th className="px-6 py-4 text-right text-xs font-bold text-gray-500 uppercase tracking-wider">Coef. Total</th>
                                <th className="px-6 py-4 text-center text-xs font-bold text-gray-500 uppercase tracking-wider">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-100">
                            {propietariosFiltrados.length > 0 ? (
                                propietariosFiltrados.map((p) => (
                                    <tr key={p.tercero_id} className="hover:bg-blue-50/30 transition-colors">
                                        <td className="px-6 py-4">
                                            <div className="text-sm font-bold text-gray-900">{p.razon_social}</div>
                                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 mt-1">
                                                {p.total_unidades} Unidad(es)
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-sm text-gray-600 font-mono">
                                            <div className="flex items-center gap-2">
                                                <FaIdCard className="text-gray-400" />
                                                {p.numero_documento}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-sm text-gray-600">
                                            <div className="flex flex-col gap-1">
                                                <div className="flex items-center gap-2" title="Teléfono">
                                                    <FaPhone className="text-green-500 text-xs" /> {p.contacto_telefono}
                                                </div>
                                                <div className="flex items-center gap-2" title="Email">
                                                    <FaEnvelope className="text-orange-500 text-xs" />
                                                    <span className="truncate max-w-[150px]">{p.contacto_email}</span>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex flex-wrap gap-1">
                                                {p.unidades.map((u, idx) => (
                                                    <Link key={idx} href={`/ph/unidades/editar/${u.id}`} className="group relative inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-100 hover:bg-indigo-600 hover:text-white transition-all cursor-pointer shadow-sm">
                                                        <FaBuilding className="mr-1 text-indigo-400 group-hover:text-white" /> {u.codigo}
                                                    </Link>
                                                ))}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-right text-sm font-mono font-bold text-gray-700">
                                            {p.total_coeficiente.toFixed(4)}%
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <Link
                                                href={`/admin/terceros/editar/${p.tercero_id}`}
                                                className="text-blue-600 hover:text-blue-800 font-medium text-sm flex justify-center items-center gap-1"
                                                title="Editar Datos del Tercero"
                                            >
                                                <FaHandshake /> Ver
                                            </Link>
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan="6" className="px-6 py-10 text-center text-gray-400 italic bg-gray-50">
                                        No se encontraron propietarios. Asegúrate de asignar unidades a terceros en la gestión de Unidades.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
