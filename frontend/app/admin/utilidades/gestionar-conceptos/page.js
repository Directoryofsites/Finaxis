'use client';

import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { useAuth } from '../../../context/AuthContext';
import { apiService } from '../../../../lib/apiService';

import { FaBook } from 'react-icons/fa';

// Función auxiliar para un manejo de errores consistente
const getErrorMessage = (err, defaultMessage = 'Ocurrió un error inesperado.') => {
  if (Array.isArray(err.response?.data?.detail) && err.response.data.detail.length > 0) {
    // Si es un error de validación de Pydantic, devuelve el primer mensaje de error
    return err.response.data.detail[0].msg;
  }
  return err.response?.data?.detail || defaultMessage;
};

export default function GestionarConceptosPage() {
  const { user, loading: authLoading } = useAuth();

  const [conceptos, setConceptos] = useState([]);
  const [seleccionados, setSeleccionados] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [mensaje, setMensaje] = useState('');

  // --- FIX 1: fetchConceptos (Ruta Corregida) ---
  const fetchConceptos = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // FIX CRÍTICO: Usamos la ruta corregida del backend: /conceptos-favoritos/
      const response = await apiService.get('/conceptos-favoritos/');
      setConceptos(response.data.sort((a, b) => a.descripcion.localeCompare(b.descripcion)));
    } catch (err) {
      setError(getErrorMessage(err, 'No se pudo obtener la lista de conceptos favoritos.'));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!authLoading && user) {
      fetchConceptos();
    }
  }, [user, authLoading]);

  const searchParams = useSearchParams();
  useEffect(() => {
    const trigger = searchParams.get('trigger');
    if (trigger === 'new_fav_concept') {
      const newUrl = window.location.pathname;
      window.history.replaceState({}, '', newUrl);
      // Wait slightly to ensure page is ready
      setTimeout(() => openNewModal(), 300);
    }
  }, [searchParams]);

  // --- Manejo de UI ---
  const handleCheckboxChange = (id) => {
    setSeleccionados(prev =>
      prev.includes(id) ? prev.filter(item => item !== id) : [...prev, id]
    );
  };

  // Estado para el modal de edición/creación
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState('new'); // 'new' or 'edit'
  const [nuevaDescripcion, setNuevaDescripcion] = useState('');
  const [conceptoAEditar, setConceptoAEditar] = useState(null);

  const openNewModal = () => {
    setModalMode('new');
    setNuevaDescripcion('');
    setConceptoAEditar(null);
    setIsModalOpen(true);
    setError(null);
    setMensaje('');
  };

  const closeModals = () => {
    setIsModalOpen(false);
    setConceptoAEditar(null);
  };

  // --- FIX 2: handleAddNew (Creación - Ruta Corregida y Payload Limpio) ---
  const handleAddNew = async (e) => {
    e.preventDefault();
    if (!nuevaDescripcion.trim()) {
      setError('La descripción no puede estar vacía.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setMensaje('');

    try {
      // FIX CRÍTICO: Eliminamos empresa_id del payload (lo inyecta el backend desde la sesión)
      // FIX RUTA: Cambiamos /conceptos/ a /conceptos-favoritos/
      const payload = {
        descripcion: nuevaDescripcion,
      };

      const response = await apiService.post('/conceptos-favoritos/', payload);

      setMensaje(`Concepto "${response.data.descripcion}" creado exitosamente.`);
      closeModals();
      setSeleccionados([]);
      fetchConceptos();
    } catch (err) {
      setError(getErrorMessage(err, 'Error al crear el nuevo concepto favorito.'));
      setIsLoading(false);
    }
  };

  const handleEdit = (concepto) => {
    setModalMode('edit');
    setConceptoAEditar(concepto);
    setNuevaDescripcion(concepto.descripcion);
    setIsModalOpen(true);
    setError(null);
    setMensaje('');
  };

  // --- FIX 4: handleUpdate (Actualización - Ruta Corregida) ---
  const handleUpdate = async (e) => {
    e.preventDefault();
    if (!nuevaDescripcion.trim()) {
      setError('La descripción no puede estar vacía.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setMensaje('');

    try {
      const descripcionFinal = nuevaDescripcion.trim();
      const payload = { descripcion: descripcionFinal };

      // FIX CRÍTICO: Usamos la ruta corregida /conceptos-favoritos/
      const response = await apiService.put(`/conceptos-favoritos/${conceptoAEditar.id}`, payload);

      setMensaje(`Concepto "${response.data.descripcion}" actualizado exitosamente.`);
      closeModals();
      setSeleccionados([]);
      fetchConceptos();
    } catch (err) {
      setError(getErrorMessage(err, 'Error al actualizar el concepto favorito.'));
      setIsLoading(false);
    }
  };

  // --- FIX 3: handleDeleteSelected (Eliminación - Ruta Corregida y Payload Limpio) ---
  const handleDeleteSelected = async () => {
    if (seleccionados.length === 0) return;

    if (!window.confirm(`¿Estás seguro de que deseas eliminar ${seleccionados.length} concepto(s) favorito(s)? Esta acción es irreversible.`)) {
      return;
    }

    setIsLoading(true);
    setError(null);
    setMensaje('');

    try {
      // FIX CRÍTICO: Eliminamos empresa_id del payload.
      // FIX RUTA: Cambiamos /conceptos/ a /conceptos-favoritos/
      const payload = {
        ids: seleccionados,
      };

      const response = await apiService.delete('/conceptos-favoritos/', { data: payload });

      setMensaje(response.data.detail);
      setSeleccionados([]);
      fetchConceptos();
    } catch (err) {
      setError(getErrorMessage(err, 'Error al eliminar los conceptos favoritos.'));
      setIsLoading(false);
    }
  };

  if (authLoading || isLoading) {
    return <div className="p-4">Cargando datos...</div>;
  }

  if (error && !mensaje) {
    // Si el error es durante la carga inicial y no hay mensaje de éxito
    return (
      <div className="p-4">
        <h1 className="text-2xl font-semibold mb-6 text-gray-800">Gestionar Conceptos Favoritos</h1>
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">Error:</strong>
          <span className="block sm:inline"> {error}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold text-gray-800">Gestionar Conceptos Favoritos</h1>
        <div className="flex gap-2">
          <button
            onClick={() => window.open('/manual/capitulo_4_conceptos.html', '_blank')}
            className="btn btn-ghost text-indigo-600 hover:bg-indigo-50 gap-2 flex items-center"
            title="Ver Manual de Usuario"
          >
            <FaBook className="text-lg" /> <span className="hidden md:inline font-bold">Manual</span>
          </button>
        </div>
      </div>

      {/* Mensajes de feedback */}
      {(error || mensaje) && (
        <div className={`mb-4 p-3 rounded ${error ? 'bg-red-100 border border-red-400 text-red-700' : 'bg-green-100 border border-green-400 text-green-700'}`} role="alert">
          {error || mensaje}
        </div>
      )}

      {/* Controles y Tabla */}
      <div className="flex justify-between items-center mb-4">
        <div>
          <button
            onClick={openNewModal}
            className="mr-2 px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition duration-150"
          >
            + Nuevo Concepto
          </button>
          <button
            onClick={handleDeleteSelected}
            disabled={seleccionados.length === 0 || isLoading}
            className={`px-4 py-2 font-medium rounded-lg transition duration-150 ${seleccionados.length > 0 && !isLoading ? 'bg-red-600 text-white hover:bg-red-700' : 'bg-gray-300 text-gray-500 cursor-not-allowed'}`}
          >
            Eliminar Seleccionados ({seleccionados.length})
          </button>
        </div>
        <div className="text-sm text-gray-500">
          Total de Conceptos: {conceptos.length}
        </div>
      </div>

      {/* Tabla de Conceptos */}
      <div className="overflow-x-auto shadow-lg rounded-lg border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-4 py-3 w-12 text-center text-sm font-medium text-gray-600 uppercase">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  checked={seleccionados.length === conceptos.length && conceptos.length > 0}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSeleccionados(conceptos.map(c => c.id));
                    } else {
                      setSeleccionados([]);
                    }
                  }}
                />
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600 uppercase">Descripción</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600 uppercase">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {conceptos.length > 0 ? (
              conceptos.map(concepto => (
                <tr key={concepto.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-center">
                    <input
                      type="checkbox"
                      className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      checked={seleccionados.includes(concepto.id)}
                      onChange={() => handleCheckboxChange(concepto.id)}
                    />
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">{concepto.descripcion}</td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <button
                      onClick={() => handleEdit(concepto)}
                      className="text-blue-600 hover:text-blue-800 font-medium"
                    >
                      Editar
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="3" className="text-center py-8 text-gray-500">No hay conceptos en la librería.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Modal de Creación/Edición */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75 flex justify-center items-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <h2 className="text-xl font-semibold mb-4">
              {modalMode === 'new' ? 'Crear Nuevo Concepto' : `Editar Concepto: ${conceptoAEditar?.descripcion}`}
            </h2>

            {error && (
              <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded" role="alert">
                {error}
              </div>
            )}

            <form onSubmit={modalMode === 'new' ? handleAddNew : handleUpdate}>
              <div className="mb-4">
                <label htmlFor="descripcion" className="block text-sm font-medium text-gray-700 mb-1">
                  Descripción
                </label>
                <input
                  id="descripcion"
                  type="text"
                  value={nuevaDescripcion}
                  onChange={(e) => setNuevaDescripcion(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  required
                  disabled={isLoading}
                />
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={closeModals}
                  className="px-4 py-2 bg-gray-200 text-gray-700 font-medium rounded-lg hover:bg-gray-300 transition duration-150"
                  disabled={isLoading}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition duration-150 disabled:bg-blue-400"
                  disabled={isLoading}
                >
                  {isLoading ? 'Guardando...' : (modalMode === 'new' ? 'Crear' : 'Guardar Cambios')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}