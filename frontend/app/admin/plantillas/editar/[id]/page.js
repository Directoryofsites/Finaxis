'use client';

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';

import { useAuth } from '../../../../context/AuthContext';
// --- ARQUITECTURA ESTANDARIZADA ---
import { apiService } from '../../../../../lib/apiService';

export default function EditarPlantillaPage() {
  const router = useRouter();
  const params = useParams();
  const { id } = params;
  const { user, authLoading } = useAuth();

  // Estados para datos maestros
  const [terceros, setTerceros] = useState([]);
  const [cuentas, setCuentas] = useState([]);
  const [tiposDocumento, setTiposDocumento] = useState([]);
  const [centrosCosto, setCentrosCosto] = useState([]);

  // Estados para datos de la plantilla
  const [nombrePlantilla, setNombrePlantilla] = useState('');
  const [beneficiarioId, setBeneficiarioId] = useState('');
  const [tipoDocId, setTipoDocId] = useState('');
  const [centroCostoId, setCentroCostoId] = useState('');
  const [detalles, setDetalles] = useState([]);

  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // --- EFECTO CORREGIDO CON APISERVICE ---
  const fetchInitialData = useCallback(async () => {
    if (!id || authLoading) return;
    setLoading(true);
    setError(null);
    try {
      // 1. Cargar la plantilla específica (URL corregida, sin empresa_id)
      const plantillaRes = await apiService.get(`/plantillas/${id}`);
      const plantillaData = plantillaRes.data;

      setNombrePlantilla(plantillaData.nombre_plantilla);
      setBeneficiarioId(plantillaData.beneficiario_id_sugerido || '');
      setTipoDocId(plantillaData.tipo_documento_id_sugerido || '');
      setCentroCostoId(plantillaData.centro_costo_id_sugerido || '');
      setDetalles(plantillaData.detalles.map(d => ({ ...d, rowId: Date.now() + Math.random() })));

      // 2. Cargar los maestros para los menús
      const [tercerosRes, pucRes, tiposDocRes, centrosCostoRes] = await Promise.all([
        apiService.get('/terceros/'),
        apiService.get('/plan-cuentas/list-flat/?permite_movimiento=true'),
        apiService.get('/tipos-documento/'),
        // --- INICIO: LÍNEA CORREGIDA ---
        apiService.get('/centros-costo/get-flat?permite_movimiento=true'),
        // --- FIN: LÍNEA CORREGIDA ---
      ]);

      setTerceros(tercerosRes.data.terceros || tercerosRes.data);
      setCuentas(pucRes.data);
      setTiposDocumento(tiposDocRes.data);
      setCentrosCosto(centrosCostoRes.data);

    } catch (err) {
      setError(err.response?.data?.detail || 'Error al cargar los datos iniciales.');
    } finally {
      setLoading(false);
    }
  }, [id, authLoading]);

  useEffect(() => {
    fetchInitialData();
  }, [fetchInitialData]);

  // --- El resto de las funciones de manejo del formulario ---

  const handleDetalleChange = (index, field, value) => {
    const nuevosDetalles = [...detalles];
    const updatedDetalle = { ...nuevosDetalles[index] };

    if (field === 'debito' && value !== '') updatedDetalle.credito = '';
    else if (field === 'credito' && value !== '') updatedDetalle.debito = '';

    updatedDetalle[field] = value;
    nuevosDetalles[index] = updatedDetalle;
    setDetalles(nuevosDetalles);
  };

  const agregarFila = () => {
    setDetalles([...detalles, { rowId: Date.now(), cuenta_id: '', concepto: '', debito: '', credito: '' }]);
  };

  const eliminarFila = (index) => {
    if (detalles.length <= 1) return;
    setDetalles(detalles.filter((_, i) => i !== index));
  };

  const totales = useMemo(() => {
    return detalles.reduce((acc, mov) => ({
      debito: acc.debito + (parseFloat(mov.debito) || 0),
      credito: acc.credito + (parseFloat(mov.credito) || 0),
    }), { debito: 0, credito: 0 });
  }, [detalles]);

  const estaBalanceado = useMemo(() => Math.abs(totales.debito - totales.credito) < 0.01 && totales.debito > 0, [totales]);

  // --- FUNCIÓN DE ENVÍO CORREGIDA ---
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!estaBalanceado) {
      setError("La plantilla no está balanceada. Revise débitos y créditos.");
      return;
    }
    setIsSubmitting(true);
    setError(null);

    const payload = {
      nombre_plantilla: nombrePlantilla,
      beneficiario_id_sugerido: beneficiarioId || null,
      tipo_documento_id_sugerido: tipoDocId || null,
      centro_costo_id_sugerido: centroCostoId || null,
      detalles: detalles.map(({ cuenta_id, concepto, debito, credito }) => ({
        cuenta_id: parseInt(cuenta_id),
        concepto,
        debito: parseFloat(debito) || 0,
        credito: parseFloat(credito) || 0,
      })),
    };

    try {
      // URL y método corregidos
      await apiService.put(`/plantillas/${id}`, payload);
      alert('¡Plantilla actualizada exitosamente!');
      router.push('/admin/plantillas');
    } catch (err) {
      setError(err.response?.data?.detail || 'Ocurrió un error al guardar los cambios.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) return <p className="text-center mt-8">Cargando plantilla...</p>;
  if (!authLoading && !user) return <p className="text-center mt-8">Por favor, inicie sesión para continuar.</p>;

  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-800">Editar Plantilla</h1>
      </div>

      {error && <div className="bg-red-100 text-red-700 p-4 rounded-md mb-6">{error}</div>}

      <form onSubmit={handleSubmit} className="space-y-8">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">Datos Generales</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="nombre_plantilla" className="block text-sm font-medium text-gray-700">Nombre *</label>
              <input type="text" name="nombre_plantilla" id="nombre_plantilla" value={nombrePlantilla} onChange={(e) => setNombrePlantilla(e.target.value)} className="mt-1 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md" required />
            </div>
            <div>
              <label htmlFor="beneficiario_id_sugerido" className="block text-sm font-medium text-gray-700">Beneficiario Sugerido</label>
              <select name="beneficiario_id_sugerido" id="beneficiario_id_sugerido" value={beneficiarioId} onChange={(e) => setBeneficiarioId(e.target.value)} className="mt-1 block w-full pl-3 pr-10 py-2 border-gray-300 sm:text-sm rounded-md">
                <option value="">Ninguno</option>
                {terceros.map(t => <option key={t.id} value={t.id}>{t.razon_social}</option>)}
              </select>
            </div>
            <div>
              <label htmlFor="tipo_documento_id_sugerido" className="block text-sm font-medium text-gray-700">Tipo Documento Sugerido</label>
              <select name="tipo_documento_id_sugerido" id="tipo_documento_id_sugerido" value={tipoDocId} onChange={(e) => setTipoDocId(e.target.value)} className="mt-1 block w-full pl-3 pr-10 py-2 border-gray-300 sm:text-sm rounded-md">
                <option value="">Ninguno</option>
                {tiposDocumento.map(td => <option key={td.id} value={td.id}>{td.nombre}</option>)}
              </select>
            </div>
            <div>
              <label htmlFor="centro_costo_id_sugerido" className="block text-sm font-medium text-gray-700">Centro de Costo Sugerido</label>
              <select name="centro_costo_id_sugerido" id="centro_costo_id_sugerido" value={centroCostoId} onChange={(e) => setCentroCostoId(e.target.value)} className="mt-1 block w-full pl-3 pr-10 py-2 border-gray-300 sm:text-sm rounded-md">
                <option value="">Ninguno</option>
                {centrosCosto.map(cc => <option key={cc.id} value={cc.id}>{cc.nombre}</option>)}
              </select>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">Detalles y Movimientos</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-50"><tr><th className="p-2 text-left">Cuenta</th><th className="p-2 text-left">Concepto</th><th className="p-2 text-left">Débito</th><th className="p-2 text-left">Crédito</th><th className="p-2"></th></tr></thead>
              <tbody>
                {detalles.map((detalle, index) => (
                  <tr key={detalle.rowId}>
                    <td className="p-1"><select required value={detalle.cuenta_id || ''} onChange={(e) => handleDetalleChange(index, 'cuenta_id', e.target.value)} className="w-full border-gray-300 rounded-md"><option value="">Seleccione</option>{cuentas.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}</select></td>
                    <td className="p-1"><input required type="text" value={detalle.concepto || ''} onChange={(e) => handleDetalleChange(index, 'concepto', e.target.value)} className="w-full border-gray-300 rounded-md" /></td>
                    <td className="p-1"><input type="number" value={detalle.debito || ''} onChange={(e) => handleDetalleChange(index, 'debito', e.target.value)} className="w-full border-gray-300 rounded-md text-right" /></td>
                    <td className="p-1"><input type="number" value={detalle.credito || ''} onChange={(e) => handleDetalleChange(index, 'credito', e.target.value)} className="w-full border-gray-300 rounded-md text-right" /></td>
                    <td className="p-1 text-center"><button type="button" onClick={() => eliminarFila(index)} className="text-red-500 hover:text-red-700 text-2xl font-bold">&times;</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <button type="button" onClick={agregarFila} className="mt-4 px-4 py-2 border rounded-md text-sm font-medium">Agregar Fila</button>
          <div className="flex justify-end mt-4 border-t pt-2">
            <p className={`font-bold ${estaBalanceado ? 'text-green-600' : 'text-red-600'}`}>
              Débitos: {totales.debito.toLocaleString('es-CO')} | Créditos: {totales.credito.toLocaleString('es-CO')} | {estaBalanceado ? 'BALANCEADO' : 'NO BALANCEADO'}
            </p>
          </div>
        </div>

        <div className="flex justify-end">
          <button type="submit" disabled={isSubmitting || !estaBalanceado} className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded-lg shadow-md disabled:bg-gray-400">
            {isSubmitting ? 'Guardando...' : 'Guardar Cambios'}
          </button>
        </div>
      </form>
    </div>
  );
}