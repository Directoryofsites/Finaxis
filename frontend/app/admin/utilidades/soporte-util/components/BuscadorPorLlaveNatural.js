'use client';

import React, { useState } from 'react';
import { FaBook } from 'react-icons/fa';
import { soporteApiService } from '@/lib/soporteApiService';
// NOTA: Se eliminaron las importaciones de Heroicons (CheckCircleIcon, XCircleIcon, InformationCircleIcon)
// para evitar el error de compilación "Module not found".

export default function BuscadorPorLlaveNatural({ todasLasEmpresas }) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [resultado, setResultado] = useState(null);

  const [formData, setFormData] = useState({
    empresaId: '',
    tipoBusqueda: 'tercero_por_nit', // ESTANDARIZADO CON BACKEND
    valor1: '',
    valor2: ''
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setResultado(null);

    // 1. Validaciones Preventivas
    if (!formData.empresaId || !formData.valor1) {
      setError("Debe seleccionar una empresa e ingresar un valor de búsqueda.");
      setIsLoading(false);
      return;
    }

    // El tipo de documento requiere ambos valores para ser una llave natural compuesta
    if (formData.tipoBusqueda === 'documento_por_numero' && !formData.valor2) {
      setError("Para buscar un documento, debe ingresar el ID del Tipo de Documento y el Número.");
      setIsLoading(false);
      return;
    }

    // 2. Preparación del Payload
    const empresaIdInt = parseInt(formData.empresaId, 10);

    if (isNaN(empresaIdInt)) {
      setError("El ID de la empresa es inválido. Por favor, recargue la página.");
      setIsLoading(false);
      return;
    }

    // Limpieza de Payload: Se asegura que solo se envíen campos necesarios para evitar el 400 Bad Request
    let payload = {
      empresaId: empresaIdInt,
      tipoBusqueda: formData.tipoBusqueda,
      valor1: formData.valor1,
    };

    // Añadir valor2 solo si la búsqueda lo requiere y tiene valor (contrato Optional[str] del Backend)
    if (formData.tipoBusqueda === 'documento_por_numero' && formData.valor2) {
      payload.valor2 = formData.valor2;
    }

    // 🔍 SONDA DE DIAGNÓSTICO: Protocolo de la Caja Negra (MANTENIDA)
    // Se deja activa para verificar el 400 Bad Request final, si persiste.
    console.log('🔍 PAYLOAD A LA API (Buscador Llave Natural):', payload);

    // 3. Llamada a la API
    try {
      const response = await soporteApiService.post('/utilidades/buscar-id-por-llave-natural', payload);

      if (response && response.id) {
        setResultado({ success: true, id: response.id, mensaje: `ID Encontrado: ${response.id}` });
      } else {
        setResultado({ success: false, mensaje: response.mensaje || "Búsqueda exitosa, pero no se encontró un ID para la llave natural proporcionada." });
      }

    } catch (err) {
      console.error('Error en la búsqueda (detalle):', err);

      // Manejo de error para extraer el detalle del 400 Bad Request
      const detail = err.response?.data?.detail
        ? JSON.stringify(err.response.data.detail, null, 2)
        : 'Error en la comunicación con el servidor. Revise la consola (F12) para el detalle del error 400/500.';

      setError(`❌ Error HTTP. Revise Consola. Detalle: ${detail}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Definición de tipos de búsqueda para el select
  const busquedaTipos = [
    { value: 'tercero_por_nit', label: 'Tercero por NIT/C.C.' },
    { value: 'cuenta_por_codigo', label: 'Cuenta por Código Contable' },
    { value: 'cc_por_codigo', label: 'Centro de Costo por Código' },
    { value: 'tipodoc_por_codigo', label: 'Tipo de Doc. por Código' },
    { value: 'documento_por_numero', label: 'Documento por Tipo y Número' },
  ];

  return (
    <div className="bg-white shadow-lg rounded-xl p-6 mb-8 border border-teal-200">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-xl font-semibold text-teal-800 flex items-center">
          ℹ️ Buscador de ID por Llave Natural
        </h3>
        <button
          onClick={() => window.open('/manual?file=capitulo_19_buscador_llave.md', '_blank')}
          className="text-teal-600 hover:bg-teal-50 px-3 py-1 rounded-md flex items-center gap-2 transition-colors"
          title="Ver Manual de Usuario"
        >
          <FaBook className="text-lg" /> <span className="font-bold text-sm">Manual</span>
        </button>
      </div>
      <p className="text-sm text-gray-600 mb-6">
        Herramienta de soporte para encontrar el ID primario de un registro usando su llave natural.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="empresaId" className="block text-sm font-medium text-gray-700">Seleccionar Empresa</label>
          <select id="empresaId" name="empresaId" value={formData.empresaId} onChange={handleInputChange} className="mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm" required>
            <option value="">-- Seleccione una empresa --</option>
            {/* Se asume que todasLasEmpresas tiene .id y .razon_social */}
            {todasLasEmpresas && todasLasEmpresas.map(empresa => (
              <option key={empresa.id} value={empresa.id}>{empresa.razon_social}</option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="tipoBusqueda" className="block text-sm font-medium text-gray-700">Tipo de Búsqueda</label>
          <select id="tipoBusqueda" name="tipoBusqueda" value={formData.tipoBusqueda} onChange={handleInputChange} className="mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm">
            {busquedaTipos.map(tipo => (
              <option key={tipo.value} value={tipo.value}>{tipo.label}</option>
            ))}
          </select>
        </div>

        {formData.tipoBusqueda === 'documento_por_numero' ? (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="valor1" className="block text-sm font-medium text-gray-700">ID del Tipo de Documento (valor1)</label>
              <input type="number" id="valor1" name="valor1" value={formData.valor1} onChange={handleInputChange} className="mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm" placeholder="Ej: 1 (Factura de Venta)" required />
            </div>
            <div>
              <label htmlFor="valor2" className="block text-sm font-medium text-gray-700">Número del Documento (valor2)</label>
              <input type="text" id="valor2" name="valor2" value={formData.valor2} onChange={handleInputChange} className="mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm" placeholder="Ej: 1020" required />
            </div>
          </div>
        ) : (
          <div>
            <label htmlFor="valor1" className="block text-sm font-medium text-gray-700">Valor a Buscar (valor1)</label>
            <input type="text" id="valor1" name="valor1" value={formData.valor1} onChange={handleInputChange} className="mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm" placeholder="Ej: 900.123.456-7 o 110505" required />
          </div>
        )}

        <div className="flex justify-end">
          <button type="submit" disabled={isLoading} className="bg-teal-600 hover:bg-teal-700 text-white font-bold py-2 px-4 rounded-md disabled:bg-teal-300">
            {isLoading ? 'Buscando...' : 'Buscar ID'}
          </button>
        </div>
      </form>

      {error && <div className="bg-red-100 text-red-700 p-3 my-4 rounded-md flex items-center">🚫 {error}</div>}

      {resultado && (
        <div className={`p-4 my-4 rounded-md flex items-center ${resultado.success ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
          {resultado.success ? '✅' : '⚠️'}
          <p className="font-medium">{resultado.mensaje}</p>
          {resultado.success && <span className="ml-auto font-bold text-lg">{resultado.id}</span>}
        </div>
      )}
    </div>
  );
}