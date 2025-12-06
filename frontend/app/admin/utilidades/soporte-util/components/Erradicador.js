'use client';

import React, { useState, useEffect } from 'react';
import { FaBook } from 'react-icons/fa';
// CORRECCIÓN: Se usa la importación nombrada con llaves {}.
import { soporteApiService } from '../../../../../lib/soporteApiService';

export default function Erradicador({ todasLasEmpresas }) {
  const [tiposDocumento, setTiposDocumento] = useState([]);
  const [mapTiposDocumento, setMapTiposDocumento] = useState(new Map());
  const [filtros, setFiltros] = useState({ empresaId: '', tipoDocId: '', numero: '' });
  const [fechas, setFechas] = useState({ inicio: '', fin: '' });

  const [searchResult, setSearchResult] = useState([]);
  const [selectedItems, setSelectedItems] = useState(new Set());

  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const isDateRangeMode = filtros.numero.trim() === '*.*';

  useEffect(() => {
    const fetchTiposDocumento = async () => {
      if (!filtros.empresaId) {
        setTiposDocumento([]);
        setMapTiposDocumento(new Map());
        return;
      }
      try {
        const res = await soporteApiService.post('/utilidades/get-tipos-documento', { empresaId: parseInt(filtros.empresaId) });
        setTiposDocumento(res.data);
        setMapTiposDocumento(new Map(res.data.map(t => [t.id, t])));
      } catch (err) {
        setError(`Error al cargar tipos de documento: ${err.response?.data?.detail || err.message}`);
      }
    };
    fetchTiposDocumento();
  }, [filtros.empresaId]);

  const handleInputChange = (e) => setFiltros(prev => ({ ...prev, [e.target.name]: e.target.value }));
  const handleDateChange = (e) => setFechas(prev => ({ ...prev, [e.target.name]: e.target.value }));

  const handleBuscar = async () => {
    let hasError = false;
    if (!filtros.empresaId || !filtros.tipoDocId || !filtros.numero) {
      setError('Por favor, complete los filtros principales (Empresa, Tipo de Doc., Número).');
      hasError = true;
    }
    if (isDateRangeMode && (!fechas.inicio || !fechas.fin)) {
      setError('En modo rango (*.*), debe seleccionar Fecha Desde y Fecha Hasta.');
      hasError = true;
    }
    if (hasError) return;

    setIsLoading(true);
    setError('');
    setMessage('');
    setSearchResult([]);
    setSelectedItems(new Set());
    try {
      const payload = { ...filtros, empresaId: parseInt(filtros.empresaId), tipoDocId: parseInt(filtros.tipoDocId) };
      if (isDateRangeMode) {
        payload.fechaInicio = fechas.inicio;
        payload.fechaFin = fechas.fin;
      }

      const res = await soporteApiService.post('/utilidades/buscar-documento-universal', payload);
      setSearchResult(res.data);
      if (res.data.length === 0) {
        setMessage('No se encontraron resultados para los criterios de búsqueda.');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al realizar la búsqueda.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleErradicar = async () => {
    if (selectedItems.size === 0) {
      setError("No hay items seleccionados para erradicar.");
      return;
    }

    const confirmation = window.prompt(`ALTO: Esta acción es IRREVERSIBLE y eliminará permanentemente ${selectedItems.size} registros del sistema.\n\nEscriba "ERRADICAR" para confirmar:`);
    if (confirmation !== 'ERRADICAR') {
      setMessage("Operación de erradicación cancelada por el usuario.");
      return;
    }

    setIsLoading(true);
    setError('');
    setMessage('');

    try {
      const documentoIds = [];
      const logIds = [];

      searchResult.forEach(item => {
        if (selectedItems.has(item.id)) {
          if (item.estado === 'ACTIVO' || item.estado === 'ANULADO') {
            documentoIds.push(item.id);
          } else { // ELIMINADO
            logIds.push(item.id);
          }
        }
      });

      const payload = {
        documentoIds,
        logIds,
        empresaId: parseInt(filtros.empresaId)
      };

      const res = await soporteApiService.post('/utilidades/erradicar-documento', payload);

      setMessage(res.data.message);
      alert(res.data.message);
      handleBuscar();

    } catch (err) {
      setError(err.response?.data?.detail || 'Error durante la erradicación.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectItem = (itemId) => {
    setSelectedItems(prev => {
      const newSelected = new Set(prev);
      if (newSelected.has(itemId)) newSelected.delete(itemId);
      else newSelected.add(itemId);
      return newSelected;
    });
  };

  const handleSelectAll = (e) => {
    if (e.target.checked) setSelectedItems(new Set(searchResult.map(item => item.id)));
    else setSelectedItems(new Set());
  };

  const getStatusClass = (estado) => {
    if (estado === 'ACTIVO') return 'bg-green-100 text-green-800';
    if (estado === 'ANULADO') return 'bg-yellow-100 text-yellow-800';
    if (estado === 'ELIMINADO') return 'bg-red-100 text-red-800';
    return 'bg-gray-100 text-gray-800';
  };

  const isButtonDisabled = isLoading || !filtros.empresaId || !filtros.tipoDocId || !filtros.numero || (isDateRangeMode && (!fechas.inicio || !fechas.fin));

  return (
    <section className="bg-white p-6 rounded-lg shadow-xl border border-gray-200">
      <div className="flex justify-between items-center mb-4 border-b pb-2">
        <h2 className="text-2xl font-bold text-gray-800">Inspector y Erradicador Universal</h2>
        <button
          onClick={() => window.open('/manual?file=capitulo_23_erradicador.md', '_blank')}
          className="text-indigo-600 hover:bg-indigo-50 px-3 py-1 rounded-md flex items-center gap-2 transition-colors"
          title="Ver Manual de Usuario"
        >
          <FaBook className="text-lg" /> <span className="font-bold text-sm">Manual</span>
        </button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className='space-y-4'>
          <div>
            <label className="block text-sm font-medium text-gray-700">1. Seleccione Empresa</label>
            <select name="empresaId" value={filtros.empresaId} onChange={handleInputChange} className="mt-1 block w-full py-2 px-3 border rounded-md">
              <option value="">-- Seleccionar --</option>
              {todasLasEmpresas.map(e => <option key={e.id} value={e.id}>{e.razon_social}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">2. Seleccione Tipo de Doc.</label>
            <select name="tipoDocId" value={filtros.tipoDocId} onChange={handleInputChange} className="mt-1 block w-full py-2 px-3 border rounded-md">
              <option value="">-- Seleccionar --</option>
              {tiposDocumento.map(t => <option key={t.id} value={t.id}>{`${t.codigo} - ${t.nombre}`}</option>)}
            </select>
          </div>
        </div>
        <div className='space-y-4'>
          <div>
            <label className="block text-sm font-medium text-gray-700">3. Ingrese Número o Comodín (*.*)</label>
            <input type="text" name="numero" value={filtros.numero} onChange={handleInputChange} className="mt-1 block w-full py-2 px-3 border rounded-md" placeholder="Ej: 246 o *.*" />
          </div>
          <div className='flex items-center space-x-4'>
            <div className='flex-1'>
              <label className="block text-sm font-medium text-gray-700">4. Fecha Desde</label>
              <input type="date" name="inicio" value={fechas.inicio} onChange={handleDateChange} disabled={!isDateRangeMode} className="mt-1 block w-full py-2 px-3 border rounded-md disabled:bg-gray-100" />
            </div>
            <div className='flex-1'>
              <label className="block text-sm font-medium text-gray-700">5. Fecha Hasta</label>
              <input type="date" name="fin" value={fechas.fin} onChange={handleDateChange} disabled={!isDateRangeMode} className="mt-1 block w-full py-2 px-3 border rounded-md disabled:bg-gray-100" />
            </div>
          </div>
        </div>
      </div>
      <div className="text-center mt-6">
        <button onClick={handleBuscar} disabled={isButtonDisabled} className="w-full md:w-auto py-2 px-8 border rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400">
          {isLoading ? 'Buscando...' : 'Buscar Documentos'}
        </button>
      </div>

      <div className="mt-6">
        {error && <div className="p-4 mb-4 text-sm text-red-700 bg-red-100 rounded-lg">{error}</div>}
        {message && <div className="p-4 mb-4 text-sm text-blue-700 bg-blue-100 rounded-lg">{message}</div>}

        {searchResult.length > 0 && (
          <div className="mt-4 bg-white p-4 rounded-lg shadow-md border">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold text-gray-700">Resultados: {searchResult.length} ({selectedItems.size} seleccionados)</h3>
              <button onClick={handleErradicar} disabled={selectedItems.size === 0 || isLoading} className="text-white bg-red-600 hover:bg-red-700 font-medium rounded-lg text-sm px-4 py-2 disabled:bg-gray-400">
                Erradicar Seleccionados
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="p-4"><input type="checkbox" onChange={handleSelectAll} /></th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo Doc</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Número</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Estado</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fecha</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Detalle</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {searchResult.map(item => {
                    const tipoDoc = mapTiposDocumento.get(item.tipo_documento_id);
                    return (
                      <tr key={`${item.estado}-${item.id}`}>
                        <td className="p-4"><input type="checkbox" checked={selectedItems.has(item.id)} onChange={() => handleSelectItem(item.id)} /></td>
                        <td className="px-4 py-4 text-sm font-mono">{item.id}</td>
                        <td className="px-4 py-4 text-sm">{tipoDoc ? `${tipoDoc.codigo} - ${tipoDoc.nombre}` : `ID: ${item.tipo_documento_id}`}</td>
                        <td className="px-4 py-4 text-sm font-bold">{item.numero}</td>
                        <td className="px-4 py-4 text-sm"><span className={`px-2 inline-flex text-xs font-semibold rounded-full ${getStatusClass(item.estado)}`}>{item.estado}</span></td>
                        <td className="px-4 py-4 text-sm">{new Date(item.fecha + 'T00:00:00').toLocaleDateString('es-CO')}</td>
                        <td className="px-4 py-4 text-sm">{item.detalle}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}