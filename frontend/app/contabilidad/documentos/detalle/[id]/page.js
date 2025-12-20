'use client';

import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { useRouter, useParams, useSearchParams } from 'next/navigation';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { useAuth } from '../../../../context/AuthContext';
import { apiService } from '../../../../../lib/apiService';


export default function DetalleDocumentoPage() {
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
  const { user, loading: authLoading } = useAuth();

  const documentoId = params.id;
  const fromPath = searchParams.get('from') || '/contabilidad/documentos';

  // --- ESTADOS ---
  const [cuentas, setCuentas] = useState([]);
  const [terceros, setTerceros] = useState([]);
  const [centrosCosto, setCentrosCosto] = useState([]);
  const [tiposDocumento, setTiposDocumento] = useState([]);
  const [documentoOriginal, setDocumentoOriginal] = useState(null);
  const [isReadOnly, setIsReadOnly] = useState(true);

  const [fecha, setFecha] = useState(new Date());
  const [beneficiarioId, setBeneficiarioId] = useState('');
  const [centroCostoId, setCentroCostoId] = useState('');
  const [movimientos, setMovimientos] = useState([]);

  const [pageIsLoading, setPageIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [mensaje, setMensaje] = useState('');

  // --- INICIO: IMPLEMENTACIÓN DEL PATRÓN GUARDIÁN ---
  const dataFetchedRef = useRef(false);
  // --- FIN: IMPLEMENTACIÓN DEL PATRÓN GUARDIÁN ---

  const totales = useMemo(() => {
    return movimientos.reduce((acc, mov) => ({
      debito: acc.debito + (parseFloat(mov.debito) || 0),
      credito: acc.credito + (parseFloat(mov.credito) || 0),
    }), { debito: 0, credito: 0 });
  }, [movimientos]);

  const estaBalanceado = useMemo(() => {
    const diff = Math.abs(totales.debito - totales.credito);
    return diff < 0.01 && totales.debito > 0 && totales.debito === totales.credito;
  }, [totales]);

  // La función fetchMaestrosAndDocumento se mantiene igual
  const fetchMaestrosAndDocumento = useCallback(async () => {
    setPageIsLoading(true);
    setError('');
    try {
      const [tiposRes, tercerosRes, cuentasRes, ccRes, docRes] = await Promise.all([
        apiService.get('/tipos-documento/'),
        apiService.get('/terceros/'),
        apiService.get('/plan-cuentas/list-flat/', { params: { permite_movimiento: true } }),
        apiService.get('/centros-costo/get-flat'),
        apiService.get(`/documentos/${documentoId}`)
      ]);

      const doc = docRes.data;
      const cuentasData = cuentasRes.data;

      setTiposDocumento(tiposRes.data);
      setTerceros(tercerosRes.data);
      setCuentas(cuentasData);
      setCentrosCosto(ccRes.data);

      setDocumentoOriginal(doc);
      setFecha(new Date(doc.fecha + 'T00:00:00'));
      setBeneficiarioId(doc.beneficiario_id || '');
      setCentroCostoId(doc.centro_costo_id || '');
      setIsReadOnly(doc.anulado);

      const movsFormateados = doc.movimientos.map(m => {
        const cuenta = cuentasData.find(c => c.id === m.cuenta_id);
        return {
          rowId: m.id,
          cuentaId: m.cuenta_id,
          cuentaInput: cuenta ? `${cuenta.codigo} - ${cuenta.nombre}` : '',
          concepto: m.concepto,
          debito: m.debito,
          credito: m.credito
        };
      });
      setMovimientos(movsFormateados);

    } catch (err) {
      setError(err.response?.data?.detail || 'Error al cargar los datos del documento.');
    } finally {
      setPageIsLoading(false);
    }
  }, [documentoId]);

  // --- INICIO: useEffect protegido por el Guardián ---
  useEffect(() => {
    // Si la autenticación está en curso, o el guardián ya se activó, no hacemos nada.
    if (authLoading || dataFetchedRef.current) {
      return;
    }

    // Si la autenticación terminó y tenemos un usuario, cargamos los datos.
    if (user) {
      fetchMaestrosAndDocumento();
      // Activamos el guardián para no volver a ejecutar esta carga.
      dataFetchedRef.current = true;
    }
  }, [user, authLoading, fetchMaestrosAndDocumento]);
  // --- FIN: useEffect protegido ---

  const handleMovimientoChange = (index, field, value) => {
    const newMovimientos = [...movimientos];
    newMovimientos[index][field] = value;

    // Lógica para asegurar que solo haya débito o crédito, no ambos
    if (field === 'debito' && value !== '') {
      newMovimientos[index]['credito'] = '';
    } else if (field === 'credito' && value !== '') {
      newMovimientos[index]['debito'] = '';
    }

    setMovimientos(newMovimientos);
  };

  const handleCuentaBlur = (index, value) => {
    if (!value) return;

    const cuentaEncontrada = cuentas.find(c =>
      c.codigo === value ||
      (c.nombre && c.nombre.toLowerCase() === value.toLowerCase())
    );

    if (cuentaEncontrada) {
      const newMovimientos = [...movimientos];
      newMovimientos[index]['cuentaId'] = cuentaEncontrada.id;
      newMovimientos[index]['cuentaInput'] = `${cuentaEncontrada.codigo} - ${cuentaEncontrada.nombre}`;
      setMovimientos(newMovimientos);
    }
  };

  const handleUpdate = async () => {
    setError('');
    setMensaje('');
    if (!estaBalanceado) {
      setError('El documento no está balanceado.');
      return;
    }

    setIsSubmitting(true);
    try {
      const payload = {
        fecha: fecha.toISOString().split('T')[0],
        tipo_documento_id: documentoOriginal.tipo_documento_id,
        numero: documentoOriginal.numero,
        beneficiario_id: beneficiarioId ? parseInt(beneficiarioId, 10) : null,
        centro_costo_id: centroCostoId ? parseInt(centroCostoId, 10) : null,
        fecha_vencimiento: null,
        movimientos: movimientos.filter(m => m.cuentaId).map(m => ({
          cuenta_id: m.cuentaId,
          concepto: m.concepto,
          debito: parseFloat(m.debito) || 0,
          credito: parseFloat(m.credito) || 0
        })),
        aplicaciones: null
      };

      const res = await apiService.put(`/documentos/${documentoId}`, payload);
      setMensaje('¡Documento actualizado exitosamente!');
      setDocumentoOriginal(res.data);

    } catch (err) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        setError(detail);
      } else {
        setError('Ocurrió un error al actualizar el documento.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const agregarFila = () => {
    setMovimientos(prev => [...prev, { rowId: Date.now(), cuentaId: '', concepto: '', debito: '', credito: '', cuentaInput: '' }]);
  };

  const eliminarFila = (index) => {
    if (movimientos.length > 1) {
      setMovimientos(movimientos.filter((_, i) => i !== index));
    }
  };

  if (pageIsLoading) return <div className="text-center p-8">Cargando documento...</div>;

  const tipoDocActual = tiposDocumento.find(t => t.id === documentoOriginal?.tipo_documento_id);

  return (
    <div className="container mx-auto p-4 md:p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl md:text-3xl font-bold">
          Editando Documento: {tipoDocActual?.nombre || ''} #{documentoOriginal?.numero}
          {documentoOriginal?.anulado && <span className="text-red-500 ml-4">(ANULADO)</span>}
        </h1>
      </div>

      {mensaje && <div className="p-3 my-4 rounded-md bg-blue-100 text-blue-800">{mensaje}</div>}
      {error && <div className="p-3 my-4 rounded-md bg-red-100 text-red-800">{error}</div>}

      <div className="bg-white p-6 rounded-lg shadow-lg mb-8 border">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div>
            <label htmlFor="fecha" className="block text-sm font-medium text-gray-700">Fecha</label>
            <DatePicker
              selected={fecha}
              onChange={(date) => setFecha(date || new Date())}
              dateFormat="dd/MM/yyyy"
              className="mt-1 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
              disabled={isReadOnly}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Tipo de Documento</label>
            <input type="text" value={tipoDocActual?.nombre || ''} disabled className="mt-1 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md bg-gray-100" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Número</label>
            <input type="text" value={documentoOriginal?.numero || ''} disabled className="mt-1 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md bg-gray-100" />
          </div>
          <div>
            <label htmlFor="beneficiario" className="block text-sm font-medium text-gray-700">Beneficiario</label>
            <select
              id="beneficiario"
              value={beneficiarioId}
              onChange={e => setBeneficiarioId(e.target.value)}
              className="mt-1 block w-full py-2 border-gray-300 rounded-md"
              disabled={isReadOnly}
            >
              <option value="">Seleccione...</option>
              {terceros.map(t => <option key={t.id} value={t.id}>{t.razon_social}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="centroCosto" className="block text-sm font-medium text-gray-700">Centro de Costo</label>
            <select
              id="centroCosto"
              value={centroCostoId}
              onChange={e => setCentroCostoId(e.target.value)}
              className="mt-1 block w-full py-2 border-gray-300 rounded-md"
              disabled={isReadOnly}
            >
              <option value="">Ninguno</option>
              {centrosCosto.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
            </select>
          </div>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-lg border">
        <h2 className="text-xl font-semibold mb-4">Movimientos Contables</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase w-2/5">Cuenta</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase w-2/5">Concepto</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Débito</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Crédito</th>
                {!isReadOnly && <th className="px-4 py-2"></th>}
              </tr>
            </thead>
            <tbody>
              {movimientos.map((mov, index) => (
                <tr key={mov.rowId}>

                  <td className="p-2">
                    <input
                      list="cuentas-list"
                      placeholder="Digita código o nombre..."
                      value={mov.cuentaInput}
                      onChange={e => handleMovimientoChange(index, 'cuentaInput', e.target.value)}
                      onBlur={e => (mov.cuentaId === '' || mov.cuentaId === null) && handleCuentaBlur(index, e.target.value)}
                      className="w-full border-gray-300 rounded-md"
                      disabled={isReadOnly}
                    />
                    <datalist id="cuentas-list">
                      {cuentas.map(c => <option key={c.id} value={c.codigo}>{`${c.codigo} - ${c.nombre}`}</option>)}
                    </datalist>
                  </td>

                  <td className="p-2">
                    <input
                      type="text"
                      placeholder="Concepto del movimiento"
                      value={mov.concepto || ''}
                      onChange={e => handleMovimientoChange(index, 'concepto', e.target.value)}
                      className="w-full border-gray-300 rounded-md"
                      disabled={isReadOnly}
                    />
                  </td>
                  <td className="p-2">
                    <input
                      type="number"
                      placeholder="0.00"
                      value={mov.debito || ''}
                      onChange={e => handleMovimientoChange(index, 'debito', e.target.value)}
                      className="w-full border-gray-300 rounded-md text-right"
                      disabled={isReadOnly}
                    />
                  </td>
                  <td className="p-2">
                    <input
                      type="number"
                      placeholder="0.00"
                      value={mov.credito || ''}
                      onChange={e => handleMovimientoChange(index, 'credito', e.target.value)}
                      className="w-full border-gray-300 rounded-md text-right"
                      disabled={isReadOnly}
                    />
                  </td>
                  {!isReadOnly && (
                    <td className="p-2 text-center">
                      <button
                        type="button"
                        onClick={() => eliminarFila(index)}
                        className="text-red-500 hover:text-red-800 text-2xl font-bold px-2"
                      >&times;</button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="flex justify-between items-center mt-4">
          {!isReadOnly && <button type="button" onClick={agregarFila} className="px-4 py-2 border rounded-md text-sm font-medium hover:bg-gray-100">Agregar Fila</button>}
          <div className="flex items-center space-x-4 ml-auto">
            <div className="text-right"><p className="font-semibold text-gray-600">Total Débito:</p><p className="font-mono text-xl font-bold">${totales.debito.toLocaleString('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p></div>
            <div className="text-right"><p className="font-semibold text-gray-600">Total Crédito:</p><p className="font-mono text-xl font-bold">${totales.credito.toLocaleString('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p></div>
          </div>
        </div>
      </div>

      {!isReadOnly && (
        <div className="flex justify-center mt-8">
          <button
            onClick={handleUpdate}
            disabled={isSubmitting || !estaBalanceado}
            className="w-full md:w-auto flex-grow justify-center py-3 px-6 border rounded-md shadow-sm text-lg font-medium text-white bg-green-600 hover:bg-green-700 disabled:bg-gray-400"
          >
            {isSubmitting ? 'Guardando Cambios...' : 'Guardar Cambios'}
          </button>
        </div>
      )}
    </div>
  );
}