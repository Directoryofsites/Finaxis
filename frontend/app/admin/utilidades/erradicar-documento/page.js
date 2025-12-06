'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../../context/AuthContext';
import BotonRegresar from '../../../components/BotonRegresar';

export default function ErradicarDocumentoPage() {
  const { user } = useAuth();
  
  const [empresas, setEmpresas] = useState([]);
  const [tiposDocumento, setTiposDocumento] = useState([]);

  const [formData, setFormData] = useState({
    empresaId: '',
    tipoDocId: '',
    numero: '',
    fecha: '',
    fechaInicio: '',
    fechaFin: ''
  });
  const [confirmationText, setConfirmationText] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [resEmpresas, resTipos] = await Promise.all([

         fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/empresas`),
          fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/tipos-documento`)

        ]);
        if (!resEmpresas.ok) throw new Error('No se pudieron cargar las empresas');
        if (!resTipos.ok) throw new Error('No se pudieron cargar los tipos de documento');
        
        setEmpresas(await resEmpresas.json());
        setTiposDocumento(await resTipos.json());
      } catch (err) {
        setError(err.message);
      }
    };
    fetchData();
  }, []);
  
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleErradicar = async () => {
    setError('');
    setMessage('');

    if (!formData.empresaId || !formData.tipoDocId) {
      setError('Debe seleccionar una Empresa y un Tipo de Documento.');
      return;
    }
    if (confirmationText !== 'BORRAR') {
        setError("Debe escribir la palabra BORRAR en mayúsculas en el campo de confirmación para proceder.");
        return;
    }
    
    setIsSubmitting(true);
    try {
      // Preparamos el payload basado en el modo
      const isMassiveMode = formData.numero.trim() === '*.*';
      const isListMode = formData.numero.includes(',');
      
      const payload = {
        empresaId: formData.empresaId,
        tipoDocId: formData.tipoDocId,
        numero: formData.numero.trim(),
        fecha: (!isMassiveMode && !isListMode) ? formData.fecha : null,
        fechaInicio: isMassiveMode ? formData.fechaInicio : null,
        fechaFin: isMassiveMode ? formData.fechaFin : null,
      };

      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/utilidades/erradicar-documento`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const result = await res.json();
      if (!res.ok) {
        throw new Error(result.message || 'Error desconocido del servidor.');
      }
      setMessage(result.message);
      alert(`¡Operación Exitosa!\n\n${result.message}`);

    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
      setConfirmationText('');
    }
  };

  // --- Lógica para mostrar/ocultar campos de fecha ---
  const isListMode = formData.numero.includes(',');
  const isMassiveMode = formData.numero.trim() === '*.*';
  const isIndividualMode = !isMassiveMode && !isListMode && formData.numero.trim() !== '';

  const isButtonDisabled = isSubmitting || confirmationText !== 'BORRAR' || !formData.empresaId || !formData.tipoDocId;

  return (
    <div className="container mx-auto p-4 max-w-2xl">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold text-red-700">Herramienta de Soporte: Erradicación</h1>
        <BotonRegresar />
      </div>
      <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6" role="alert">
        <p className="font-bold">¡ADVERTENCIA DE ALTO RIESGO!</p>
        <p>Esta herramienta realiza eliminaciones permanentes. Solo para uso del personal de soporte autorizado.</p>
      </div>

      <div className="space-y-4 bg-white p-6 rounded-lg shadow-md">
        <div>
          <label htmlFor="empresaId" className="block text-sm font-medium text-gray-700">1. Seleccione la Empresa</label>
          <select id="empresaId" name="empresaId" value={formData.empresaId} onChange={handleInputChange} className="mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm">
            <option value="">-- Seleccionar Empresa --</option>

          {empresas.map(e => <option key={e.id} value={e.id}>{e.razon_social}</option>)}
          </select>
        </div>

        <div>
          <label htmlFor="tipoDocId" className="block text-sm font-medium text-gray-700">2. Seleccione el Tipo de Documento</label>
          <select id="tipoDocId" name="tipoDocId" value={formData.tipoDocId} onChange={handleInputChange} className="mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm">
            <option value="">-- Seleccionar Tipo --</option>
            {tiposDocumento.map(td => <option key={td.id} value={td.id}>{td.nombre}</option>)}
          </select>
        </div>

        <div>
          <label htmlFor="numero" className="block text-sm font-medium text-gray-700">3. Ingrese Número(s) de Documento</label>
          <input type="text" id="numero" name="numero" value={formData.numero} onChange={handleInputChange} className="mt-1 block w-full py-2 px-3 border border-gray-300 rounded-md shadow-sm" placeholder="Ej: 101 | 101,205,310 | *.*"/>
          <p className="text-xs text-gray-500 mt-1">Use un número, una lista separada por comas, o <code className="bg-gray-200 px-1 rounded">*.*</code> para un rango de fechas.</p>
        </div>
        
        {/* --- LÓGICA DE FECHAS CONDICIONAL --- */}
        {isIndividualMode && (
          <div>
            <label htmlFor="fecha" className="block text-sm font-medium text-gray-700">4. Fecha del Documento Individual</label>
            <input type="date" id="fecha" name="fecha" value={formData.fecha} onChange={handleInputChange} className="mt-1 block w-full py-2 px-3 border border-gray-300 rounded-md shadow-sm" />
          </div>
        )}
        
        {isMassiveMode && (
          <div className="p-4 bg-yellow-100 border border-yellow-300 rounded-md">
            <p className="font-bold text-yellow-800 mb-2">Modo Masivo Activado</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="fechaInicio" className="block text-sm font-medium text-gray-700">4. Fecha Desde</label>
                <input type="date" id="fechaInicio" name="fechaInicio" value={formData.fechaInicio} onChange={handleInputChange} className="mt-1 block w-full py-2 px-3 border border-gray-300 rounded-md shadow-sm" />
              </div>
              <div>
                <label htmlFor="fechaFin" className="block text-sm font-medium text-gray-700">5. Fecha Hasta</label>
                <input type="date" id="fechaFin" name="fechaFin" value={formData.fechaFin} onChange={handleInputChange} className="mt-1 block w-full py-2 px-3 border border-gray-300 rounded-md shadow-sm" />
              </div>
            </div>
          </div>
        )}

        {isListMode && (
            <div className="p-3 bg-blue-100 border border-blue-300 rounded-md">
                <p className="text-sm text-blue-800">Se buscarán los números de la lista en **todas las fechas**.</p>
            </div>
        )}

        <div className="mt-4 pt-4 border-t">
            <label htmlFor="confirmationText" className="block text-sm font-medium text-yellow-600">Para confirmar la operación, escriba BORRAR aquí:</label>
            <input 
                type="text"
                id="confirmationText"
                name="confirmationText"
                value={confirmationText}
                onChange={(e) => setConfirmationText(e.target.value)}
                className="mt-1 block w-full py-2 px-3 border border-red-500 rounded-md shadow-sm font-bold uppercase"
                autoComplete="off"
            />
        </div>
      </div>
      
      <div className="mt-6">
        <button onClick={handleErradicar} disabled={isButtonDisabled} className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:bg-gray-400 disabled:cursor-not-allowed">
          {isSubmitting ? 'Procesando...' : 'ERRADICAR DATOS PERMANENTEMENTE'}
        </button>
      </div>

      {message && <div className="mt-4 p-3 bg-green-100 text-green-800 rounded-md">{message}</div>}
      {error && <div className="mt-4 p-3 bg-red-100 text-red-800 rounded-md">{error}</div>}

    </div>
  );
}