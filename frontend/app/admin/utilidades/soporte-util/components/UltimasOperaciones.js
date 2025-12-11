'use client';

import React, { useState, useEffect, useRef } from 'react';
import { FaBook } from 'react-icons/fa';
// CORRECCIÓN: Se usa la importación nombrada con llaves {}.
import { soporteApiService } from '../../../../../lib/soporteApiService';

export default function UltimasOperaciones({ todasLasEmpresas }) {
  const [reporteDocs, setReporteDocs] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const [filtros, setFiltros] = useState({
    limit: 50,
    selectedEmpresas: [],
    fecha_creacion_inicio: '',
    fecha_creacion_fin: '',
    fecha_documento_inicio: '',
    fecha_documento_fin: ''
  });

  const orderByRef = useRef(null);

  const handleFiltroChange = (e) => {
    const { name, value, type } = e.target;
    if (type === 'select-multiple') {
      const options = Array.from(e.target.selectedOptions, option => option.value);
      setFiltros(prev => ({ ...prev, [name]: options }));
    } else {
      setFiltros(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleConsultar = async () => {
    setError('');
    setIsLoading(true);
    try {
      const orderByValue = orderByRef.current.value;
      console.log("Enviando Payload al Backend con orderBy (leído directamente):", orderByValue);

      const payload = {
        limit: parseInt(filtros.limit, 10) || 50,
        orderBy: orderByValue,
        empresaIds: filtros.selectedEmpresas.length > 0
          ? filtros.selectedEmpresas.map(id => parseInt(id, 10))
          : null,
        fecha_creacion_inicio: filtros.fecha_creacion_inicio || null,
        fecha_creacion_fin: filtros.fecha_creacion_fin || null,
        fecha_documento_inicio: filtros.fecha_documento_inicio || null,
        fecha_documento_fin: filtros.fecha_documento_fin || null
      };

      const res = await soporteApiService.post('/utilidades/ultimas-operaciones', payload);
      setReporteDocs(res.data);

    } catch (err) {
      const errorMsg = err.response?.data?.detail
        ? JSON.stringify(err.response.data.detail)
        : 'Error al obtener las últimas operaciones.';
      setError(errorMsg);
      setReporteDocs([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    handleConsultar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const getStatusClass = (estado) => {
    if (estado === 'CREACIÓN') return 'bg-green-100 text-green-800';
    if (estado === 'ANULACIÓN') return 'bg-yellow-100 text-yellow-800';
    if (estado === 'ELIMINACIÓN') return 'bg-red-100 text-red-800';
    return 'bg-gray-100 text-gray-800';
  };

  return (
    <section className="bg-white p-6 rounded-lg shadow-xl border border-gray-200">
      <div className="flex justify-between items-center mb-4 border-b pb-2">
        <h2 className="text-2xl font-bold text-gray-800">Consultar Últimas Operaciones (Auditoría Global)</h2>
        <button
          onClick={() => window.open('/manual/capitulo_21_ultimas_operaciones.html', '_blank')}
          className="text-indigo-600 hover:bg-indigo-50 px-3 py-1 rounded-md flex items-center gap-2 transition-colors"
          title="Ver Manual de Usuario"
        >
          <FaBook className="text-lg" /> <span className="font-bold text-sm">Manual</span>
        </button>
      </div>

      <div className="space-y-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div>
            <label htmlFor="limit" className="block text-sm font-medium text-gray-700">Límite</label>
            <input
              type="number"
              id="limit"
              name="limit"
              value={filtros.limit}
              onChange={handleFiltroChange}
              className="mt-1 block w-full py-2 px-3 border border-gray-300 rounded-md"
              min="1"
            />
          </div>
          <div>
            <label htmlFor="orderBy" className="block text-sm font-medium text-gray-700">Ordenar Por</label>
            <select
              id="orderBy"
              name="orderBy"
              ref={orderByRef}
              defaultValue="fecha_evento"
              className="mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md"
            >
              <option value="fecha_evento">Fecha de Creación</option>
              <option value="fecha_documento">Fecha del Documento</option>
            </select>
          </div>
          <div className="col-span-1 md:col-span-2">
            <label htmlFor="selectedEmpresas" className="block text-sm font-medium text-gray-700">Filtrar por Empresa(s)</label>
            <select
              id="selectedEmpresas"
              name="selectedEmpresas"
              multiple
              value={filtros.selectedEmpresas}
              onChange={handleFiltroChange}
              className="mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md h-24"
            >
              {todasLasEmpresas.map(emp => (
                <option key={emp.id} value={emp.id}>{emp.razon_social}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 border-t pt-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Por Fecha de Creación (Registro)</label>
            <div className="flex items-center space-x-2 mt-1">
              <input type="date" name="fecha_creacion_inicio" value={filtros.fecha_creacion_inicio} onChange={handleFiltroChange} className="w-full border-gray-300 rounded-md" />
              <span>hasta</span>
              <input type="date" name="fecha_creacion_fin" value={filtros.fecha_creacion_fin} onChange={handleFiltroChange} className="w-full border-gray-300 rounded-md" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Por Fecha del Documento (Transacción)</label>
            <div className="flex items-center space-x-2 mt-1">
              <input type="date" name="fecha_documento_inicio" value={filtros.fecha_documento_inicio} onChange={handleFiltroChange} className="w-full border-gray-300 rounded-md" />
              <span>hasta</span>
              <input type="date" name="fecha_documento_fin" value={filtros.fecha_documento_fin} onChange={handleFiltroChange} className="w-full border-gray-300 rounded-md" />
            </div>
          </div>
        </div>
      </div>

      <div className="flex justify-center">
        <button
          onClick={handleConsultar}
          disabled={isLoading}
          className="w-full md:w-1-2 justify-center py-2 px-8 border rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400"
        >
          {isLoading ? 'Consultando...' : 'Aplicar Filtros y Consultar'}
        </button>
      </div>

      {error && <div className="p-4 mt-4 text-sm text-red-700 bg-red-100 rounded-lg break-words"><pre>{error}</pre></div>}

      {reporteDocs.length > 0 && (
        <div className="mt-6 bg-gray-50 p-4 rounded-lg border overflow-x-auto">
          <h3 className="font-bold text-gray-700 mb-4">Resultados:</h3>
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase">Empresa</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase">Fecha Oper. (Registro)</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase">Fecha Documento</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase">Usuario</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase">Operación</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase">Detalle Documento</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {reporteDocs.map((log) => (
                <tr key={`${log.id}-${log.tipo_operacion}`} className="hover:bg-gray-50">
                  <td className="px-4 py-4 text-sm">{log.empresa_razon_social}</td>
                  <td className="px-4 py-4 text-sm">{log.fecha_operacion ? new Date(log.fecha_operacion).toLocaleString('es-CO') : 'N/A'}</td>
                  <td className="px-4 py-4 text-sm">{log.fecha_documento ? new Date(log.fecha_documento).toLocaleDateString('es-CO', { timeZone: 'UTC' }) : 'N/A'}</td>
                  <td className="px-4 py-4 text-sm">{log.email_usuario || 'N/A'}</td>
                  <td className="px-4 py-4 text-sm">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusClass(log.tipo_operacion)}`}>
                      {log.tipo_operacion}
                    </span>
                  </td>
                  <td className="px-4 py-4 text-sm">{log.detalle_documento}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}