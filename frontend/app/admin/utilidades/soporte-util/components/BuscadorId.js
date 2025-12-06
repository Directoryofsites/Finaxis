'use client';

import React, { useState, useEffect } from 'react';
// CORRECCIÓN: Se usa la importación nombrada con llaves {}.
import { soporteApiService } from '../../../../../lib/soporteApiService';

// Este componente recibe la lista de todas las empresas como un "prop"
export default function BuscadorId({ todasLasEmpresas }) {
  const [tipoBusqueda, setTipoBusqueda] = useState('tercero_por_nit');
  const [empresaId, setEmpresaId] = useState('');
  const [valor1, setValor1] = useState('');
  const [valor2, setValor2] = useState('');
  
  const [tiposDoc, setTiposDoc] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [resultado, setResultado] = useState(null);

  useEffect(() => {
    const fetchTiposDoc = async () => {
      if (!empresaId) {
        setTiposDoc([]);
        return;
      }
      try {
        const res = await soporteApiService.post('/utilidades/get-tipos-documento', {
          empresaId: parseInt(empresaId, 10)
        });
        setTiposDoc(res.data);
      } catch (err) {
        setError(`Error al cargar tipos de documento: ${err.response?.data?.detail || err.message}`);
      }
    };

    if (tipoBusqueda === 'documento_por_numero') {
      fetchTiposDoc();
    }
  }, [empresaId, tipoBusqueda]);

  const handleBuscar = async () => {
    setIsLoading(true);
    setError('');
    setResultado(null);

    try {
      const payload = {
        tipoBusqueda: tipoBusqueda,
        empresaId: parseInt(empresaId, 10),
        valor1: valor1,
        valor2: valor2,
      };
      
      const res = await soporteApiService.post('/utilidades/buscar-id-por-llave-natural', payload);
      setResultado(res.data);

    } catch (err) {
      setError(err.response?.data?.detail || 'Error al realizar la búsqueda.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section className="bg-white p-6 rounded-lg shadow-xl border border-gray-200">
      <h2 className="text-2xl font-bold mb-4 text-gray-800 border-b pb-2">Buscador de ID por Llave de Negocio</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-4 items-end">
        <div>
          <label className="block text-sm font-medium text-gray-600">1. Tipo de Dato</label>
          <select 
            value={tipoBusqueda}
            onChange={(e) => { setTipoBusqueda(e.target.value); setValor1(''); setValor2(''); }}
            className="mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm"
          >
            <option value="tercero_por_nit">NIT de Tercero</option>
            <option value="cuenta_por_codigo">Cód. Cuenta Contable</option>
            <option value="cc_por_codigo">Cód. Centro de Costo</option>
            <option value="tipodoc_por_codigo">Cód. Tipo de Documento</option>
            <option value="documento_por_numero">Número de Documento</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-600">2. Empresa</label>
          <select
            value={empresaId}
            onChange={(e) => setEmpresaId(e.target.value)}
            className="mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm"
          >
            <option value="">Seleccione...</option>
            {todasLasEmpresas.map(e => (<option key={e.id} value={e.id}>{e.razon_social}</option>))}
          </select>
        </div>

        {tipoBusqueda === 'documento_por_numero' ? (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-600">3. Tipo de Documento</label>
              <select 
                value={valor1}
                onChange={(e) => setValor1(e.target.value)}
                className="mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm"
              >
                <option value="">Seleccione Tipo...</option>
                {tiposDoc.map(t => <option key={t.id} value={t.id}>{`${t.codigo} - ${t.nombre}`}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-600">4. Número de Documento</label>
              <input
                type="number"
                value={valor2}
                onChange={(e) => setValor2(e.target.value)}
                className="mt-1 block w-full py-2 px-3 border border-gray-300 rounded-md shadow-sm"
                placeholder="Ej: 101"
              />
            </div>
          </>
        ) : (
          <div className="lg:col-span-2">
            <label className="block text-sm font-medium text-gray-600">3. Valor a Buscar</label>
            <input
              type="text"
              value={valor1}
              onChange={(e) => setValor1(e.target.value)}
              className="mt-1 block w-full py-2 px-3 border border-gray-300 rounded-md shadow-sm"
              placeholder="Ingrese el código o NIT..."
            />
          </div>
        )}
      </div>
      
      <div className="mt-4">
          <button
            onClick={handleBuscar}
            disabled={isLoading || !empresaId || !valor1 || (tipoBusqueda === 'documento_por_numero' && !valor2)}
            className="py-2 px-6 border rounded-md shadow-sm text-sm font-medium text-white bg-cyan-600 hover:bg-cyan-700 disabled:bg-gray-400"
          >
            {isLoading ? 'Buscando...' : 'Buscar ID'}
          </button>
      </div>

      <div className="mt-4">
        {error && <p className="text-red-600 text-sm">{error}</p>}
        {resultado && (
          <div className="flex items-center space-x-3 bg-green-100 p-3 rounded-md">
            <p className="text-sm font-medium text-green-800">ID Encontrado:</p>
            <strong className="text-lg font-mono text-green-900">{resultado.id}</strong>
          </div>
        )}
      </div>
    </section>
  );
}