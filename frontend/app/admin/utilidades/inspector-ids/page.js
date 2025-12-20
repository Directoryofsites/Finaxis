'use client';

import React, { useState } from 'react';


export default function InspectorIdsPage() {

  // Lista de entidades que el backend puede resolver
  const entidadesSoportadas = [
    'Documento',
    'Tercero',
    'Cuenta Contable',
    'Tipo de Documento',
    'Centro de Costo',
    'Usuario'
  ];

  // Estados del componente
  const [entidad, setEntidad] = useState(entidadesSoportadas[0]);
  const [idBusqueda, setIdBusqueda] = useState('');
  const [resultado, setResultado] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleBuscarId = async () => {
    if (!idBusqueda) {
      setError('Por favor, ingrese un ID para buscar.');
      return;
    }

    setIsLoading(true);
    setError('');
    setResultado(null);

    try {
      const payload = {
        entidad: entidad,
        id: idBusqueda
      };

      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/utilidades/resolver-id`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.message || `Error ${res.status} del servidor.`);
      }

      setResultado(data);

    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-4 max-w-4xl">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold text-gray-800">Herramienta de Soporte: Inspector de IDs</h1>

      </div>
      <div className="bg-blue-100 border-l-4 border-blue-500 text-blue-700 p-4 mb-6" role="alert">
        <p>Esta herramienta permite consultar la información detallada de un registro a partir de su ID de base de datos.</p>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          <div className="md:col-span-1">
            <label htmlFor="entidad" className="block text-sm font-medium text-gray-700">1. Tipo de Entidad</label>
            <select
              id="entidad"
              value={entidad}
              onChange={(e) => setEntidad(e.target.value)}
              className="mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm"
            >
              {entidadesSoportadas.map(e => <option key={e} value={e}>{e}</option>)}
            </select>
          </div>
          <div className="md:col-span-1">
            <label htmlFor="idBusqueda" className="block text-sm font-medium text-gray-700">2. ID a Buscar</label>
            <input
              type="number"
              id="idBusqueda"
              value={idBusqueda}
              onChange={(e) => setIdBusqueda(e.target.value)}
              className="mt-1 block w-full py-2 px-3 border border-gray-300 rounded-md shadow-sm"
              placeholder="Ej: 558"
            />
          </div>
          <div className="md:col-span-1">
            <button
              onClick={handleBuscarId}
              disabled={isLoading}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400"
            >
              {isLoading ? 'Buscando...' : 'Buscar ID'}
            </button>
          </div>
        </div>
      </div>

      {/* --- ÁREA DE RESULTADOS --- */}
      <div className="mt-6">
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
            <strong className="font-bold">Error: </strong>
            <span className="block sm:inline">{error}</span>
          </div>
        )}
        {resultado && (
          <div className="bg-gray-100 p-4 rounded-lg shadow-inner">
            <h3 className="text-lg font-semibold mb-2">Resultado para {entidad} ID: {idBusqueda}</h3>
            <pre className="bg-gray-900 text-green-400 text-xs p-4 rounded-md overflow-auto">
              <code>
                {JSON.stringify(resultado, null, 2)}
              </code>
            </pre>
          </div>
        )}
      </div>

    </div>
  );
}