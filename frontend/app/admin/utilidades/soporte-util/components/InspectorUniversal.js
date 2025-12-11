'use client';

import React, { useState } from 'react';
import { FaBook } from 'react-icons/fa';
// CORRECCIÓN FINAL: Se usa la importación nombrada con llaves {}.
import { soporteApiService } from '@/lib/soporteApiService';

// --- Sub-componente para renderizar de forma inteligente cada resultado ---
const ResultCard = ({ result }) => {
  const { tabla_origen, datos } = result;

  // Función para renderizar filas de datos de forma segura
  const renderDataRows = (dataObject) => {
    return Object.entries(dataObject).map(([key, value]) => (
      <tr key={key} className="hover:bg-gray-50">
        <td className="px-3 py-1 font-semibold text-gray-600 align-top">{key}</td>
        <td className="px-3 py-1 text-gray-800 break-all">{String(value ?? 'N/A')}</td>
      </tr>
    ));
  };

  // Título legible para cada tabla
  const getTitle = (tabla) => {
    const titles = {
      documentos: 'Documento',
      terceros: 'Tercero',
      plan_cuentas: 'Cuenta Contable',
      centros_costo: 'Centro de Costo',
      tipos_documento: 'Tipo de Documento',
      usuarios: 'Usuario',
      log_operaciones: 'Log de Auditoría',
      plantillas_maestras: 'Plantilla',
      movimientos_contables: 'Movimiento Contable',
    };
    return titles[tabla] || tabla;
  };

  return (
    <div className="border border-gray-300 rounded-lg overflow-hidden">
      <div className="bg-gray-100 p-2 border-b">
        <h4 className="font-bold text-gray-700">Coincidencia encontrada en: <span className="text-purple-700">{getTitle(tabla_origen)}</span></h4>
      </div>
      <table className="min-w-full text-sm">
        <tbody>
          {renderDataRows(datos)}
        </tbody>
      </table>
    </div>
  );
};


// --- Componente Principal: InspectorUniversal ---
export default function InspectorUniversal() {
  const [idToInspect, setIdToInspect] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [results, setResults] = useState([]);

  const handleSearch = async () => {
    if (!idToInspect) {
      setError("Por favor, ingrese un ID numérico.");
      return;
    }
    setIsLoading(true);
    setError('');
    setResults([]);

    try {
      const payload = { idToInspect: parseInt(idToInspect) };
      const response = await soporteApiService.post('/utilidades/inspector-universal-id', payload);
      setResults(response.data);
    } catch (err) {
      setResults([]);
      setError(err.response?.data?.detail || 'Error al realizar la inspección.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md border-l-4 border-purple-600">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-xl font-bold text-purple-800">Inspector Universal por ID</h3>
        <button
          onClick={() => window.open('/manual/capitulo_20_inspector_id.html', '_blank')}
          className="text-purple-600 hover:bg-purple-50 px-3 py-1 rounded-md flex items-center gap-2 transition-colors"
          title="Ver Manual de Usuario"
        >
          <FaBook className="text-lg" /> <span className="font-bold text-sm">Manual</span>
        </button>
      </div>
      <p className="text-sm text-gray-600 mb-4">
        Introduzca un ID numérico interno de la base de datos para encontrar el registro correspondiente en cualquier tabla principal.
      </p>

      <div className="flex items-center gap-4">
        <input
          type="number"
          value={idToInspect}
          onChange={(e) => setIdToInspect(e.target.value)}
          placeholder="Ingrese ID a buscar..."
          className="flex-grow p-2 border border-gray-300 rounded-md shadow-sm"
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
        />
        <button
          onClick={handleSearch}
          disabled={isLoading}
          className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded-md disabled:bg-purple-300"
        >
          {isLoading ? 'Buscando...' : 'Inspeccionar ID'}
        </button>
      </div>

      {error && <div className="bg-red-100 text-red-700 p-3 my-4 rounded-md text-sm">{error}</div>}

      {results.length > 0 && (
        <div className="mt-6 space-y-4">
          <p className='text-sm font-semibold'>{`Se encontraron ${results.length} coincidencia(s) para el ID ${idToInspect}:`}</p>
          {results.map((result, index) => (
            <ResultCard key={`${result.tabla_origen}-${index}`} result={result} />
          ))}
        </div>
      )}
    </div>
  );
}