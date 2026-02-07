'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'next/navigation';
import {
  FaLayerGroup,
  FaPlus,
  FaEdit,
  FaTrash,
  FaFolder,
  FaFolderOpen,
  FaFileInvoice,
  FaExclamationTriangle,
  FaCheckCircle,
  FaSitemap
} from 'react-icons/fa';

import {
  FaBook,
} from 'react-icons/fa';

import { useAuth } from '../../context/AuthContext'; // Ajusta rutas si es necesario (../../ vs ../)
import { apiService } from '../../../lib/apiService';


// Estilos Reusables (Manual v2.0)
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white";

// --- MODAL FORMULARIO (REDISEÑADO) ---
const FormModal = ({ isOpen, onClose, onSubmit, centro, setCentro, isLoading, centrosCosto, isEdit }) => {
  if (!isOpen) return null;

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setCentro(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit();
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex justify-center items-center z-50 animate-fadeIn p-4">
      <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-lg border border-gray-100 transform transition-all scale-100">
        <div className="flex justify-between items-center mb-6 border-b border-gray-100 pb-4">
          <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
            {isEdit ? <FaEdit className="text-indigo-500" /> : <FaPlus className="text-green-500" />}
            {isEdit ? 'Editar Centro de Costo' : 'Nuevo Centro de Costo'}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors text-2xl">&times;</button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">

          {/* Selector de Padre (Solo al crear) */}
          {!isEdit && (
            <div>
              <label htmlFor="centro_costo_padre_id" className={labelClass}>
                Ubicación (Padre)
              </label>
              <div className="relative">
                <select
                  id="centro_costo_padre_id"
                  name="centro_costo_padre_id"
                  value={centro.centro_costo_padre_id || ''}
                  onChange={handleChange}
                  className={selectClass}
                >
                  <option value="">-- Nivel Principal (Raíz) --</option>
                  {centrosCosto
                    .filter(cc => !cc.permite_movimiento) // Solo padres
                    .map(cc => (
                      <option key={cc.id} value={cc.id}>
                        {'\u00A0'.repeat((cc.nivel > 1 ? cc.nivel - 1 : 0) * 4)} 📂 {cc.nombre}
                      </option>
                    ))}
                </select>
              </div>
              <p className="text-xs text-gray-400 mt-1">Seleccione "Nivel Principal" para crear una carpeta raíz.</p>
            </div>
          )}

          {/* Código */}
          <div>
            <label htmlFor="codigo" className={labelClass}>Código</label>
            <input
              type="text"
              name="codigo"
              id="codigo"
              value={centro.codigo || ''}
              onChange={handleChange}
              required
              className={`${inputClass} font-mono`}
              placeholder="Ej: 10.01"
            />
          </div>

          {/* Nombre */}
          <div>
            <label htmlFor="nombre" className={labelClass}>Nombre</label>
            <input
              type="text"
              name="nombre"
              id="nombre"
              value={centro.nombre || ''}
              onChange={handleChange}
              required
              className={inputClass}
              placeholder="Ej: Departamento de Ventas"
            />
          </div>

          {/* Checkbox Tipo */}
          <div className="flex items-center p-4 bg-gray-50 rounded-lg border border-gray-200">
            <input
              type="checkbox"
              name="permite_movimiento"
              id="permite_movimiento"
              checked={centro.permite_movimiento}
              onChange={handleChange}
              className="h-5 w-5 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500 cursor-pointer"
            />
            <div className="ml-3">
              <label htmlFor="permite_movimiento" className="block text-sm font-bold text-gray-900 cursor-pointer">
                Es Auxiliar (Recibe Movimientos)
              </label>
              <p className="text-xs text-gray-500">
                Marcar si aquí se registrarán gastos/costos. Desmarcar si es un título agrupador (Carpeta).
              </p>
            </div>
          </div>

          {/* Footer Botones */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors font-medium"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 shadow-md disabled:bg-gray-400 font-bold flex items-center gap-2"
            >
              {isLoading ? <span className="loading loading-spinner loading-sm"></span> : <><FaCheckCircle /> Guardar</>}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// --- CONTENIDO PRINCIPAL (Componente Interno) ---
function GestionCentrosCostoContent() {
  const { user, loading: authLoading } = useAuth();
  const searchParams = useSearchParams();
  const [centros, setCentros] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentCentro, setCurrentCentro] = useState(null);
  const [formIsLoading, setFormIsLoading] = useState(false);

  // --- DEEP LINKING TRIGGER (Nuevo CC) ---
  useEffect(() => {
    const trigger = searchParams.get('trigger');
    if (trigger === 'new_cc') {
      const newUrl = window.location.pathname;
      window.history.replaceState({}, '', newUrl);
      setTimeout(() => handleOpenCreateModal(), 500);
    }
  }, [searchParams]);

  const fetchCentrosCosto = useCallback(async () => {
    if (!user) return;
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiService.get('/centros-costo/get-flat');
      setCentros(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'No se pudo cargar la lista de centros de costo.');
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  useEffect(() => {
    if (!authLoading) {
      fetchCentrosCosto();
    }
  }, [user, authLoading, fetchCentrosCosto]);

  const handleOpenCreateModal = (parent = null) => {
    const newCentro = {
      codigo: parent ? `${parent.codigo}.` : '',
      nombre: '',
      permite_movimiento: true,
      centro_costo_padre_id: parent ? parent.id : null,
    };
    setCurrentCentro(newCentro);
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (centroToEdit) => {
    setCurrentCentro({ ...centroToEdit });
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setCurrentCentro(null);
  };

  const handleFormSubmit = async () => {
    setFormIsLoading(true);
    setError(null);
    const isCreating = !currentCentro.id;
    const payload = {
      codigo: currentCentro.codigo,
      nombre: currentCentro.nombre,
      permite_movimiento: currentCentro.permite_movimiento,
    };
    if (isCreating) {
      payload.centro_costo_padre_id = currentCentro.centro_costo_padre_id || null;
    }

    try {
      if (isCreating) {
        await apiService.post('/centros-costo/', payload);
      } else {
        await apiService.put(`/centros-costo/${currentCentro.id}`, payload);
      }
      await fetchCentrosCosto();
      handleCloseModal();
    } catch (err) {
      const errorMessage = err.response?.data?.detail || `Error al ${isCreating ? 'crear' : 'actualizar'}.`;
      setError(errorMessage);
    } finally {
      setFormIsLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("¿Estás seguro de eliminar este centro de costo?\n\nEsta acción no se puede deshacer.")) {
      return;
    }
    setError(null);
    try {
      await apiService.delete(`/centros-costo/${id}`);
      await fetchCentrosCosto();
    } catch (err) {
      setError(err.response?.data?.detail || 'No se pudo eliminar el centro de costo.');
    }
  };

  const getIndentationPadding = (level) => {
    // Nivel 1 = 0px, Nivel 2 = 24px, Nivel 3 = 48px...
    return (level > 1 ? (level - 1) * 32 : 0) + 'px';
  };

  if (authLoading || isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
        <FaLayerGroup className="text-indigo-300 text-6xl mb-4 animate-pulse" />
        <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando Estructura de Costos...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
      <div className="max-w-6xl mx-auto">

        {/* ENCABEZADO */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
          <div>
            <div className="flex items-center gap-3 mt-3">
              <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                <FaSitemap className="text-2xl" />
              </div>
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="text-3xl font-bold text-gray-800">Centros de Costo</h1>
                  <button
                    onClick={() => window.open('/manual/capitulo_50_centros_de_costo.html', '_blank')}
                    className="flex items-center gap-2 px-2 py-1 bg-white border border-indigo-200 text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors font-medium shadow-sm"
                    type="button"
                  >
                    <FaBook /> <span className="hidden md:inline">Manual</span>
                  </button>
                </div>
                <p className="text-gray-500 text-sm">Estructura jerárquica para imputación de gastos e ingresos.</p>
              </div>
            </div>
          </div>
          <button
            onClick={() => handleOpenCreateModal()}
            className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl shadow-lg transform hover:-translate-y-0.5 transition-all flex items-center gap-2"
          >
            <FaPlus /> Crear Nivel Principal
          </button>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded-r-lg flex items-center gap-3 animate-pulse">
            <FaExclamationTriangle className="text-xl" />
            <p>{error}</p>
          </div>
        )}

        {/* CARD TABLA */}
        <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden animate-fadeIn">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-slate-100">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-bold text-gray-600 uppercase tracking-wider w-2/3">Estructura (Código y Nombre)</th>
                  <th className="px-6 py-4 text-center text-xs font-bold text-gray-600 uppercase tracking-wider">Tipo</th>
                  <th className="px-6 py-4 text-center text-xs font-bold text-gray-600 uppercase tracking-wider">Acciones</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100 text-sm">
                {centros.length === 0 ? (
                  <tr>
                    <td colSpan="3" className="px-6 py-10 text-center text-gray-400 italic">
                      No hay centros de costo definidos. Comience creando el nivel principal.
                    </td>
                  </tr>
                ) : (
                  centros.map((cc) => (
                    <tr key={cc.id} className="hover:bg-indigo-50/30 transition-colors group">
                      <td className="px-6 py-3 whitespace-nowrap">
                        <div className="flex items-center" style={{ paddingLeft: getIndentationPadding(cc.nivel) }}>
                          {/* Líneas Guía Visuales */}
                          {cc.nivel > 1 && <div className="w-4 h-px bg-gray-300 mr-2"></div>}

                          {/* Icono Jerárquico */}
                          <div className={`mr-3 ${!cc.permite_movimiento ? 'text-amber-500' : 'text-indigo-400'}`}>
                            {!cc.permite_movimiento ? (cc.nivel === 1 ? <FaFolderOpen className="text-lg" /> : <FaFolder />) : <FaFileInvoice />}
                          </div>

                          <div className="flex flex-col">
                            <span className={`font-mono text-xs ${!cc.permite_movimiento ? 'font-bold text-gray-800' : 'text-gray-500'}`}>{cc.codigo}</span>
                            <span className={`text-sm ${!cc.permite_movimiento ? 'font-bold text-gray-800' : 'text-gray-700'}`}>{cc.nombre}</span>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-3 whitespace-nowrap text-center">
                        {cc.permite_movimiento ?
                          <span className="px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-50 text-blue-700 border border-blue-100">
                            Auxiliar
                          </span>
                          :
                          <span className="px-3 py-1 inline-flex text-xs leading-5 font-bold rounded-full bg-amber-50 text-amber-700 border border-amber-100">
                            Título
                          </span>
                        }
                      </td>
                      <td className="px-6 py-3 whitespace-nowrap text-center">
                        <div className="flex justify-center items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          {!cc.permite_movimiento && (
                            <button
                              onClick={() => handleOpenCreateModal(cc)}
                              className="p-2 bg-green-50 text-green-600 hover:bg-green-100 rounded-lg transition-colors"
                              title="Crear Sub-nivel"
                            >
                              <FaPlus />
                            </button>
                          )}
                          <button
                            onClick={() => handleOpenEditModal(cc)}
                            className="p-2 bg-blue-50 text-blue-600 hover:bg-blue-100 rounded-lg transition-colors"
                            title="Editar"
                          >
                            <FaEdit />
                          </button>
                          <button
                            onClick={() => handleDelete(cc.id)}
                            className="p-2 bg-red-50 text-red-600 hover:bg-red-100 rounded-lg transition-colors"
                            title="Eliminar"
                          >
                            <FaTrash />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* RENDER DEL MODAL */}
        {isModalOpen && <FormModal
          isOpen={isModalOpen}
          onClose={handleCloseModal}
          onSubmit={handleFormSubmit}
          centro={currentCentro}
          setCentro={setCurrentCentro}
          isLoading={formIsLoading}
          centrosCosto={centros}
          isEdit={!!currentCentro?.id}
        />}
      </div>
    </div>
  );
}

// --- default EXPORT WRAPPER ---
export default function GestionCentrosCostoPage() {
  return (
    <React.Suspense fallback={<div className="h-screen flex items-center justify-center text-indigo-500">Cargando...</div>}>
      <GestionCentrosCostoContent />
    </React.Suspense>
  );
}