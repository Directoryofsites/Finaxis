'use client';

import React, { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import Script from 'next/script';
import {
  FaSearch,
  FaPlus,
  FaObjectGroup,
  FaFileCsv,
  FaFilePdf,
  FaEdit,
  FaTrash,
  FaUsers,
  FaIdCard,
  FaExclamationTriangle,
  FaBook
} from 'react-icons/fa';

import BotonRegresar from '../../components/BotonRegresar';
import { useAuth } from '../../context/AuthContext';
import { apiService } from '../../../lib/apiService';

// --- ESTILOS REUSABLES (Estandarizados v2.0) ---
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none pl-10";

export default function GestionTercerosPage() {
  const { user, loading: authLoading } = useAuth();
  const [terceros, setTerceros] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Carga de datos
  useEffect(() => {
    if (!authLoading) {
      if (user && user.empresaId) {
        const fetchTerceros = async () => {
          try {
            setLoading(true);
            setError(null);
            const response = await apiService.get('/terceros/');
            setTerceros(response.data);
          } catch (err) {
            setError(err.response?.data?.detail || 'Error al obtener los datos de los terceros');
          } finally {
            setLoading(false);
          }
        };
        fetchTerceros();
      } else {
        setLoading(false);
        setError("No se pudo identificar la empresa del usuario.");
      }
    }
  }, [user, authLoading]);

  // Lógica de Búsqueda
  const tercerosFiltrados = useMemo(() => {
    if (searchTerm.length < 3) return terceros;
    const lowerTerm = searchTerm.toLowerCase();
    return terceros.filter(t =>
      (t.razon_social && t.razon_social.toLowerCase().includes(lowerTerm)) ||
      (t.nit && t.nit.toString().includes(lowerTerm))
    );
  }, [terceros, searchTerm]);

  const handleDelete = async (terceroId, razonSocial) => {
    if (!window.confirm(`¿Estás seguro de que deseas eliminar a "${razonSocial}"?`)) return;
    try {
      setError(null);
      await apiService.delete(`/terceros/${terceroId}`);
      setTerceros(prev => prev.filter(t => t.id !== terceroId));
      alert('Tercero eliminado exitosamente.');
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al eliminar el tercero.');
    }
  };

  // --- EXPORTACIÓN ---
  const handleExportCSV = () => {
    if (tercerosFiltrados.length === 0) return;
    const headers = ['NIT', 'Razón Social', 'Email', 'Teléfono', 'Dirección', 'Ciudad'];
    const csvRows = [
      headers.join(','),
      ...tercerosFiltrados.map(t => [
        `"${t.nit || ''}"`, `"${t.razon_social || ''}"`, `"${t.email || ''}"`,
        `"${t.telefono || ''}"`, `"${t.direccion || ''}"`, `"${t.ciudad || ''}"`
      ].join(','))
    ];
    const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.setAttribute('download', `terceros_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleExportPDF = () => {
    if (tercerosFiltrados.length === 0) return;
    if (!window.jspdf) return alert("Librería PDF cargando. Intente de nuevo.");
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();

    doc.setFontSize(18);
    doc.text("Listado de Terceros", 14, 22);
    doc.setFontSize(11);
    doc.text(`Fecha: ${new Date().toLocaleDateString()}`, 14, 30);

    if (searchTerm.length >= 3) {
      doc.setFontSize(10);
      doc.setTextColor(100);
      doc.text(`Filtro: "${searchTerm}"`, 14, 36);
    }

    const tableColumn = ["NIT", "Razón Social", "Email", "Teléfono", "Ciudad"];
    const tableRows = tercerosFiltrados.map(t => [t.nit, t.razon_social, t.email, t.telefono, t.ciudad]);

    doc.autoTable({
      startY: searchTerm.length >= 3 ? 40 : 35,
      head: [tableColumn],
      body: tableRows,
      theme: 'grid',
      styles: { fontSize: 8 },
      headStyles: { fillColor: [79, 70, 229] }
    });
    doc.save(`terceros_${new Date().toISOString().split('T')[0]}.pdf`);
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
        <FaUsers className="text-indigo-300 text-6xl mb-4 animate-pulse" />
        <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando Directorio...</p>
      </div>
    );
  }

  return (
    <>
      <Script src="https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js" />
      <Script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js" />
      <Script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.8.2/jspdf.plugin.autotable.min.js" />

      <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
        <div className="max-w-7xl mx-auto">

          {/* ENCABEZADO */}
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
            <div>
              <BotonRegresar />
              <div className="flex items-center gap-3 mt-3">
                <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                  <FaUsers className="text-2xl" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold text-gray-800">Gestión de Terceros</h1>
                  <p className="text-gray-500 text-sm">Directorio de clientes, proveedores y empleados.</p>
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => window.open('/manual/capitulo_34_gestion_terceros.html', '_blank')}
                className="flex items-center gap-2 px-4 py-2 bg-white border border-indigo-200 text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors font-medium shadow-sm"
                title="Ver Manual de Usuario"
              >
                <FaBook /> <span>Manual</span>
              </button>
              <Link href="/admin/terceros/fusionar" className="flex items-center gap-2 px-4 py-2 bg-white border border-amber-500 text-amber-600 rounded-lg hover:bg-amber-50 transition-colors font-medium shadow-sm">
                <FaObjectGroup /> <span>Fusionar</span>
              </Link>
              <Link href="/admin/terceros/crear" className="flex items-center gap-2 px-5 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-all shadow-md transform hover:-translate-y-0.5 font-medium">
                <FaPlus /> <span>Crear Tercero</span>
              </Link>
            </div>
          </div>

          {/* CARD PRINCIPAL */}
          <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 animate-fadeIn">

            {/* FILTROS Y ACCIONES */}
            <div className="flex flex-col md:flex-row justify-between items-end mb-6 gap-4">
              <div className="w-full md:w-1/2">
                <label className={labelClass}>Búsqueda Rápida (NIT o Nombre)</label>
                <div className="relative">
                  <input
                    type="text"
                    placeholder="Escriba al menos 3 caracteres..."
                    className={inputClass}
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                  <FaSearch className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                </div>
                {searchTerm.length > 0 && searchTerm.length < 3 && (
                  <p className="text-xs text-amber-500 mt-1 ml-1">Escriba {3 - searchTerm.length} caracteres más...</p>
                )}
              </div>

              <div className="flex gap-3">
                <button onClick={handleExportCSV} disabled={tercerosFiltrados.length === 0} className="flex items-center gap-2 px-4 py-2 bg-white border border-green-500 text-green-600 rounded-lg hover:bg-green-50 font-medium transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed">
                  <FaFileCsv /> CSV
                </button>
                <button onClick={handleExportPDF} disabled={tercerosFiltrados.length === 0} className="flex items-center gap-2 px-4 py-2 bg-white border border-red-500 text-red-600 rounded-lg hover:bg-red-50 font-medium transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed">
                  <FaFilePdf /> PDF
                </button>
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
                    <th className="py-3 px-4 text-left text-xs font-bold text-gray-600 uppercase tracking-wider w-32">NIT</th>
                    <th className="py-3 px-4 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">Razón Social</th>
                    <th className="py-3 px-4 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">Datos de Contacto</th>
                    <th className="py-3 px-4 text-center text-xs font-bold text-gray-600 uppercase tracking-wider w-32">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 bg-white">
                  {tercerosFiltrados.length > 0 ? (
                    tercerosFiltrados.map((tercero) => (
                      <tr key={tercero.id} className="hover:bg-indigo-50/20 transition-colors group">
                        <td className="py-3 px-4 text-sm font-mono text-indigo-900 font-bold">
                          {tercero.nit}
                        </td>
                        <td className="py-3 px-4 text-sm font-medium text-gray-800">
                          <div className="flex items-center gap-2">
                            <FaIdCard className="text-gray-400" />
                            {tercero.razon_social}
                          </div>
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-600">
                          <div className="flex flex-col gap-1">
                            <span className="truncate max-w-xs">{tercero.email}</span>
                            <span className="text-xs text-gray-400 font-mono">{tercero.telefono}</span>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-center">
                          <div className="flex justify-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <Link
                              href={`/admin/terceros/editar/${tercero.id}`}
                              className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                              title="Editar"
                            >
                              <FaEdit />
                            </Link>
                            <button
                              onClick={() => handleDelete(tercero.id, tercero.razon_social)}
                              className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                              title="Eliminar"
                            >
                              <FaTrash />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="4" className="py-10 text-center text-gray-400 italic">
                        {searchTerm.length > 0
                          ? `No se encontraron resultados para "${searchTerm}"`
                          : "No hay terceros registrados."}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="mt-4 text-xs text-gray-400 text-right">
              Mostrando {tercerosFiltrados.length} registro(s)
            </div>

          </div>
        </div>
      </div>
    </>
  );
}