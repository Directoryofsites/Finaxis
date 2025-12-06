'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import BotonRegresar from '../../../components/BotonRegresar';
import { useAuth } from '../../../context/AuthContext';
import { apiService } from '../../../../lib/apiService';

export default function CrearPlantillaPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();

  const [maestra, setMaestra] = useState({
    nombre_plantilla: '',
    tipo_documento_id_sugerido: '',
    beneficiario_id_sugerido: '',
    centro_costo_id_sugerido: ''
  });
  const [detalles, setDetalles] = useState([
    { cuenta_id: '', concepto: '', debito: '', credito: '' },
    { cuenta_id: '', concepto: '', debito: '', credito: '' },
  ]);
  const [terceros, setTerceros] = useState([]);
  const [cuentas, setCuentas] = useState([]);
  const [tiposDocumento, setTiposDocumento] = useState([]);
  const [centrosCosto, setCentrosCosto] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [pageIsLoading, setPageIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!authLoading && user) {
      const fetchMaestros = async () => {
        setPageIsLoading(true);
        setError(null);
        try {
          const [tercerosRes, pucRes, tiposDocRes, centrosCostoRes] = await Promise.all([
            apiService.get('/terceros/'),
            apiService.get('/plan-cuentas/'),
            apiService.get('/tipos-documento/'),

            apiService.get('/centros-costo/get-flat'),
          ]);
          setTerceros(tercerosRes.data);
          const aplanarCuentas = (cuentas) => {
            let listaPlana = [];
            const recorrer = (cuenta) => {
                if (cuenta.permite_movimiento) listaPlana.push(cuenta);
                if (cuenta.children) cuenta.children.forEach(recorrer);
            };
            cuentas.forEach(recorrer);
            return listaPlana;
          };
          setCuentas(aplanarCuentas(pucRes.data));
          setTiposDocumento(tiposDocRes.data);
          setCentrosCosto(centrosCostoRes.data.filter(cc => cc.permite_movimiento));
        } catch (err) {
          setError(err.response?.data?.detail || 'Error al cargar los datos maestros.');
        } finally {
          setPageIsLoading(false);
        }
      };
      fetchMaestros();
    } else if (!authLoading && !user) {
        setPageIsLoading(false);
        setError('No se pudo identificar al usuario. Por favor, inicie sesión de nuevo.');
    }
  }, [user, authLoading]);
  
  const handleMaestraChange = (e) => {
    const { name, value } = e.target;
    setMaestra(prev => ({ ...prev, [name]: value }));
  };
  const handleDetalleChange = (index, field, value) => {
    const nuevosDetalles = [...detalles];
    nuevosDetalles[index][field] = value;
    setDetalles(nuevosDetalles);
  };
  const agregarFila = () => setDetalles([...detalles, { cuenta_id: '', concepto: '', debito: '', credito: '' }]);
  const eliminarFila = (index) => {
    if (detalles.length > 1) setDetalles(detalles.filter((_, i) => i !== index));
  };
  const totales = useMemo(() => detalles.reduce((acc, mov) => ({
    debito: acc.debito + (parseFloat(mov.debito) || 0),
    credito: acc.credito + (parseFloat(mov.credito) || 0),
  }), { debito: 0, credito: 0 }), [detalles]);
  const estaBalanceado = useMemo(() => totales.debito === totales.credito && totales.debito > 0, [totales]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!maestra.nombre_plantilla || maestra.nombre_plantilla.trim() === '') {
        setError('El nombre de la plantilla es obligatorio.');
        return;
    }
    const detallesValidos = detalles.filter(d => d.cuenta_id || d.debito || d.credito);
    if (detallesValidos.length === 0) {
      setError("Debe haber al menos una fila con datos en la plantilla.");
      return;
    }
    for (const detalle of detallesValidos) {
      if (!detalle.cuenta_id || !detalle.concepto) {
        setError("Todas las filas con valores deben tener una cuenta y un concepto.");
        return;
      }
    }
    if (!estaBalanceado) {
      setError('La plantilla debe estar balanceada y los totales deben ser mayores a cero.');
      return;
    }
    
    setIsSubmitting(true);
    try {
      const sanitizedDetalles = detallesValidos.map(d => ({
        concepto: d.concepto,
        cuenta_id: parseInt(d.cuenta_id),
        debito: parseFloat(d.debito) || 0,
        credito: parseFloat(d.credito) || 0,
      }));
      const payload = {
        nombre_plantilla: maestra.nombre_plantilla.trim(),
        tipo_documento_id_sugerido: maestra.tipo_documento_id_sugerido ? parseInt(maestra.tipo_documento_id_sugerido) : null,
        beneficiario_id_sugerido: maestra.beneficiario_id_sugerido ? parseInt(maestra.beneficiario_id_sugerido) : null,
        centro_costo_id_sugerido: maestra.centro_costo_id_sugerido ? parseInt(maestra.centro_costo_id_sugerido) : null,
        
        detalles: sanitizedDetalles,
      };
      await apiService.post('/plantillas/', payload);
      alert('¡Plantilla creada exitosamente!');
      router.push('/admin/plantillas');
    } catch (err) {
      let errorMessage = 'Error desconocido al guardar la plantilla.';
      if (Array.isArray(err.response?.data?.detail)) {
          const errorDetail = err.response.data.detail[0];
          const fieldPath = errorDetail.loc.slice(1).join(' -> ');
          errorMessage = `Error en el campo '${fieldPath}': ${errorDetail.msg}`;
      } else if (err.response?.data?.detail) {
          errorMessage = err.response.data.detail;
      }
      setError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  if (authLoading || pageIsLoading) return <div className="text-center mt-10">Cargando datos maestros...</div>;

  return (
    <div className="container mx-auto p-4">
      <BotonRegresar />
      <h1 className="text-3xl font-bold mb-6 text-gray-800">Crear Nueva Plantilla</h1>
      <form onSubmit={handleSubmit} className="space-y-8">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">Datos Generales de la Plantilla</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="nombre_plantilla" className="block text-sm font-medium text-gray-700">Nombre de la Plantilla *</label>
              <input type="text" name="nombre_plantilla" id="nombre_plantilla" value={maestra.nombre_plantilla || ''} onChange={handleMaestraChange} className="mt-1 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md" required />
            </div>
            <div>
              <label htmlFor="beneficiario_id_sugerido" className="block text-sm font-medium text-gray-700">Beneficiario Sugerido (Opcional)</label>
              <select name="beneficiario_id_sugerido" id="beneficiario_id_sugerido" value={maestra.beneficiario_id_sugerido || ''} onChange={handleMaestraChange} className="mt-1 block w-full pl-3 pr-10 py-2 border-gray-300 sm:text-sm rounded-md">
                <option value="">Ninguno</option>
                {terceros.map(t => <option key={t.id} value={t.id}>{t.razon_social}</option>)}
              </select>
            </div>
            <div>
              <label htmlFor="tipo_documento_id_sugerido" className="block text-sm font-medium text-gray-700">Tipo de Documento Sugerido (Opcional)</label>
              <select name="tipo_documento_id_sugerido" id="tipo_documento_id_sugerido" value={maestra.tipo_documento_id_sugerido || ''} onChange={handleMaestraChange} className="mt-1 block w-full pl-3 pr-10 py-2 border-gray-300 sm:text-sm rounded-md">
                <option value="">Ninguno</option>
                {tiposDocumento.map(td => <option key={td.id} value={td.id}>{td.nombre}</option>)}
              </select>
            </div>
            <div>
              <label htmlFor="centro_costo_id_sugerido" className="block text-sm font-medium text-gray-700">Centro de Costo Sugerido (Opcional)</label>
              <select name="centro_costo_id_sugerido" id="centro_costo_id_sugerido" value={maestra.centro_costo_id_sugerido || ''} onChange={handleMaestraChange} className="mt-1 block w-full pl-3 pr-10 py-2 border-gray-300 sm:text-sm rounded-md">
                <option value="">Ninguno</option>
                {centrosCosto.map(cc => <option key={cc.id} value={cc.id}>{cc.nombre}</option>)}
              </select>
            </div>
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">Detalles y Movimientos de la Plantilla</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead><tr><th className="px-2 py-2">Cuenta</th><th className="px-2 py-2">Concepto</th><th className="px-2 py-2">Débito</th><th className="px-2 py-2">Crédito</th><th className="px-2 py-2"></th></tr></thead>
              <tbody>
                {detalles.map((detalle, index) => (
                  <tr key={index}>
                    <td className="pr-2"><select value={detalle.cuenta_id || ''} onChange={(e) => handleDetalleChange(index, 'cuenta_id', e.target.value)} className="w-full border-gray-300 rounded-md"><option value="">Seleccione</option>{cuentas.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}</select></td>
                    <td className="pr-2"><input type="text" value={detalle.concepto || ''} onChange={(e) => handleDetalleChange(index, 'concepto', e.target.value)} className="w-full border-gray-300 rounded-md" /></td>
                    <td className="pr-2"><input type="number" placeholder="0.00" value={detalle.debito || ''} onChange={(e) => handleDetalleChange(index, 'debito', e.target.value)} className="w-full border-gray-300 rounded-md text-right" /></td>
                    <td className="pr-2"><input type="number" placeholder="0.00" value={detalle.credito || ''} onChange={(e) => handleDetalleChange(index, 'credito', e.target.value)} className="w-full border-gray-300 rounded-md text-right" /></td>
                    <td><button type="button" onClick={() => eliminarFila(index)} className="text-red-600 hover:text-red-900 font-bold text-lg">&times;</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <button type="button" onClick={agregarFila} className="mt-4 px-4 py-2 border border-gray-400 rounded-md text-sm font-medium hover:bg-gray-100">Agregar Fila</button>
          <div className="flex justify-end mt-4 border-t pt-2">
            <p className={`font-bold text-lg ${estaBalanceado ? 'text-green-600' : 'text-red-600'}`}>
              Total Débitos: {totales.debito.toLocaleString('es-CO', {style:'currency', currency:'COP'})} | Total Créditos: {totales.credito.toLocaleString('es-CO', {style:'currency', currency:'COP'})} | {estaBalanceado ? 'BALANCEADO' : 'DESBALANCEADO'}
            </p>
          </div>
        </div>
        {error && <p className="text-center text-red-500 font-semibold p-4 bg-red-100 rounded-md">{error}</p>}
        <div className="flex justify-end">
          <button type="submit" disabled={isSubmitting || !estaBalanceado} className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-6 rounded-lg shadow-md disabled:bg-gray-400">
            {isSubmitting ? 'Guardando...' : 'Guardar Plantilla'}
          </button>
        </div>
      </form>
    </div>
  );
}