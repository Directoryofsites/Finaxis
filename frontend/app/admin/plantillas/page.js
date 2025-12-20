'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';

import { useAuth } from '../../context/AuthContext';
import { apiService } from '../../../lib/apiService';
import { FaBook } from 'react-icons/fa';

export default function GestionPlantillasPage() {
  const { user, loading: authLoading } = useAuth();

  const [plantillas, setPlantillas] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (authLoading) return;

    if (user) {
      fetchPlantillas();
    } else {
      setIsLoading(false);
      setError("Por favor, inicie sesión para ver las plantillas.");
    }
  }, [user, authLoading]);

  const fetchPlantillas = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiService.get('/plantillas/');
      setPlantillas(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'No se pudo cargar las plantillas.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm(`¿Estás seguro de que deseas eliminar la plantilla? Esta acción no se puede deshacer.`)) {
      return;
    }
    setError(null);
    try {
      await apiService.delete(`/plantillas/${id}`);
      setPlantillas(prevPlantillas => prevPlantillas.filter(plantilla => plantilla.id !== id));
      alert('Plantilla eliminada exitosamente.');
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al eliminar la plantilla.');
    }
  };

  if (authLoading || isLoading) {
    return <p className="text-center mt-10">Cargando...</p>;
  }

  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold text-gray-800">Administración de Plantillas de Documentos</h1>
          <button
            onClick={() => window.open('/manual/capitulo_3_plantillas.html', '_blank')}
            className="flex items-center gap-2 px-2 py-1 bg-white border border-indigo-200 text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors font-medium shadow-sm"
            title="Ver Manual de Usuario"
          >
            <FaBook /> <span className="hidden md:inline">Manual</span>
          </button>
        </div>
      </div>

      <div className="flex justify-start mb-6">
        <Link href="/admin/plantillas/crear" className="bg-blue-600 hover:bg-blue-800 text-white font-bold py-2 px-4 rounded-lg shadow-md transition duration-300">
          Crear Nueva Plantilla
        </Link>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-md relative mb-4" role="alert">
          <strong className="font-bold">Error: </strong>
          <span className="block sm:inline">{error}</span>
        </div>
      )}

      {!isLoading && !error && (
        <div className="overflow-x-auto shadow-lg rounded-lg">
          <table className="min-w-full bg-white">
            <thead className="bg-gray-200 text-gray-600 uppercase text-sm leading-normal">
              <tr>
                <th className="py-3 px-6 text-left">Nombre de la Plantilla</th>
                <th className="py-3 px-6 text-center">Acciones</th>
              </tr>
            </thead>
            <tbody className="text-gray-600 text-sm font-light">
              {plantillas.length > 0 ? plantillas.map((plantilla) => (
                <tr key={plantilla.id} className="border-b border-gray-200 hover:bg-gray-100">
                  <td className="py-3 px-6 text-left font-semibold">{plantilla.nombre_plantilla}</td>
                  <td className="py-3 px-6 text-center">
                    <div className="flex item-center justify-center">
                      <Link href={`/admin/plantillas/editar/${plantilla.id}`} className="text-blue-600 hover:text-blue-900 font-semibold">Editar</Link>
                      <span className="mx-2">|</span>
                      <button onClick={() => handleDelete(plantilla.id)} className="text-red-600 hover:text-red-900 font-semibold">Eliminar</button>
                    </div>
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan="2" className="text-center py-4">No hay plantillas creadas.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}