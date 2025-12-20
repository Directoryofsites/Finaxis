'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

import { apiService } from '../../../../lib/apiService';

export default function FusionarTercerosPage() {
  const router = useRouter();
  const [terceros, setTerceros] = useState([]);
  const [origenId, setOrigenId] = useState('');
  const [destinoId, setDestinoId] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState('');

  // Cargar la lista de todos los terceros al iniciar
  useEffect(() => {
    const fetchTerceros = async () => {
      try {
        // CAMBIO FINAL Y VICTORIOSO: Extraemos la propiedad 'data' de la respuesta de Axios.
        const { data } = await apiService.get('/terceros');

        if (Array.isArray(data)) {
          setTerceros(data);
        } else {
          console.error("La respuesta interna de la API no es un array:", data);
          setTerceros([]);
          setError('La estructura de la respuesta del servidor no fue la esperada.');
        }
      } catch (err) {
        setError(err.response?.data?.detail || err.message || 'No se pudo cargar la lista de terceros.');
      }
    };
    fetchTerceros();
  }, []);

  const handleFusion = async () => {
    // Validaciones
    if (!origenId || !destinoId) {
      setError('Debe seleccionar un tercero de origen y uno de destino.');
      return;
    }
    if (origenId === destinoId) {
      setError('El tercero de origen y destino no pueden ser el mismo.');
      return;
    }

    // Doble confirmación para una acción tan delicada
    const confirmacion1 = window.confirm(`¿Está SEGURO de que desea mover TODOS los documentos del tercero seleccionado como ORIGEN al tercero de DESTINO?`);
    if (!confirmacion1) return;

    const confirmacion2 = window.confirm(`ESTA ACCIÓN ES IRREVERSIBLE y el tercero de origen será ELIMINADO. ¿Desea continuar?`);
    if (!confirmacion2) return;

    setIsSubmitting(true);
    setError(null);
    setSuccess('');

    try {
      // Usamos apiService.post para mantener la consistencia y la autenticación automática
      const result = await apiService.post('/terceros/fusionar', {
        origenId: parseInt(origenId),
        destinoId: parseInt(destinoId)
      });

      setSuccess(`${result.data.message} Se movieron ${result.data.documentosMovidos} documento(s).`);

      setTimeout(() => {
        router.push('/admin/terceros');
      }, 4000);

    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Ocurrió un error en el servidor.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="container mx-auto p-4">

      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold mb-6 text-gray-800">Utilidad de Fusión de Terceros</h1>

        <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-6" role="alert">
          <p className="font-bold">¡Atención! Acción Peligrosa</p>
          <p>Esta herramienta transfiere todos los movimientos de un tercero (origen) a otro (destino) y luego elimina permanentemente al tercero de origen. Úsela con extrema precaución.</p>
        </div>

        <div className="bg-white p-8 rounded-lg shadow-md space-y-6">
          <div>
            <label htmlFor="origen" className="block text-sm font-medium text-gray-700 mb-1">
              1. Seleccione el Tercero Origen (El incorrecto, será ELIMINADO)
            </label>
            <select id="origen" value={origenId} onChange={(e) => setOrigenId(e.target.value)} className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md bg-red-50">
              <option value="">-- Seleccione un tercero a eliminar --</option>
              {terceros.map(t => <option key={t.id} value={t.id}>ID: {t.id} | NIT: {t.nit} | Nombre: {t.razon_social}</option>)}
            </select>
          </div>

          <div>
            <label htmlFor="destino" className="block text-sm font-medium text-gray-700 mb-1">
              2. Seleccione el Tercero Destino (El correcto, recibirá los movimientos)
            </label>
            <select id="destino" value={destinoId} onChange={(e) => setDestinoId(e.target.value)} className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md bg-green-50">
              <option value="">-- Seleccione un tercero a conservar --</option>
              {terceros.map(t => <option key={t.id} value={t.id}>ID: {t.id} | NIT: {t.nit} | Nombre: {t.razon_social}</option>)}
            </select>
          </div>

          <div className="pt-4">
            <button
              onClick={handleFusion}
              disabled={isSubmitting}
              className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-lg font-medium text-white bg-red-600 hover:bg-red-700 disabled:bg-gray-400"
            >
              {isSubmitting ? 'Fusionando...' : 'Iniciar Fusión'}
            </button>
          </div>
        </div>

        {error && <p className="text-center text-red-600 font-bold mt-4">{error}</p>}
        {success && <p className="text-center text-green-600 font-bold mt-4">{success}</p>}
      </div>
    </div>
  );
}