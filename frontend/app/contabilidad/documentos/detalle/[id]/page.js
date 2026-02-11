'use client';

import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { useRouter, useParams, useSearchParams } from 'next/navigation';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { useAuth } from '../../../../context/AuthContext';
import { apiService } from '../../../../../lib/apiService';


import { phService } from '../../../../../lib/phService'; // NEW IMPORT

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

  // --- ESTADOS PARA CREACIÓN DE TERCEROS ---
  const [isTerceroModalOpen, setIsTerceroModalOpen] = useState(false);
  const [nuevoTercero, setNuevoTercero] = useState({ nit: '', razon_social: '' });
  const [terceroModalError, setTerceroModalError] = useState('');
  const [isSubmittingTercero, setIsSubmittingTercero] = useState(false);

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
    if (!value) {
      // User cleared the field
      const newMovimientos = [...movimientos];
      newMovimientos[index]['cuentaId'] = null;
      newMovimientos[index]['cuentaInput'] = '';
      setMovimientos(newMovimientos);
      return;
    }

    const cuentaEncontrada = cuentas.find(c =>
      c.codigo === value ||
      (c.nombre && c.nombre.toLowerCase() === value.toLowerCase()) ||
      `${c.codigo} - ${c.nombre}` === value // Allow matching full string if user didn't change it but triggered blur
    );

    if (cuentaEncontrada) {
      const newMovimientos = [...movimientos];
      newMovimientos[index]['cuentaId'] = cuentaEncontrada.id;
      newMovimientos[index]['cuentaInput'] = `${cuentaEncontrada.codigo} - ${cuentaEncontrada.nombre}`;
      setMovimientos(newMovimientos);
    } else {
      // Optional: Reset if invalid? Or leave as is to let user correct it? 
      // For now, let's reset to avoid saving bad data, or just alert?
      // Let's just clear ID if it doesn't match known account to force valid selection
      const newMovimientos = [...movimientos];
      newMovimientos[index]['cuentaId'] = null;
      // Keep input text so user can fix it, but ID is null
      setMovimientos(newMovimientos);
    }
  };

  const handleCreateTercero = async () => {
    setTerceroModalError('');
    if (!nuevoTercero.nit || !nuevoTercero.razon_social) {
      setTerceroModalError('El NIT y el Nombre son obligatorios.');
      return;
    }
    setIsSubmittingTercero(true);
    try {
      const payload = { ...nuevoTercero, empresa_id: user.empresaId };
      const response = await apiService.post('/terceros/', payload);
      const terceroCreado = response.data;

      // Actualizar lista local
      setTerceros(prev => [...prev, terceroCreado].sort((a, b) => a.razon_social.localeCompare(b.razon_social)));

      // Seleccionar el nuevo tercero
      setBeneficiarioId(String(terceroCreado.id));

      // Cerrar modal y limpiar
      setIsTerceroModalOpen(false);
      setNuevoTercero({ nit: '', razon_social: '' });
      setMensaje(`Tercero "${terceroCreado.razon_social}" creado y seleccionado.`);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Error al crear el tercero.';
      setTerceroModalError(errorMsg);
    } finally {
      setIsSubmittingTercero(false);
    }
  };

  // --- MODAL RECALCULO ---
  const [showRecalculoModal, setShowRecalculoModal] = useState(false);
  const [recalculoData, setRecalculoData] = useState(null); // { unidad_id, fecha }
  const [recalculando, setRecalculando] = useState(false);
  const [recalculoResult, setRecalculoResult] = useState(null);

  const handleUpdate = async () => {
    setError('');
    setMensaje('');
    setRecalculoResult(null); // Reset

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

      // --- DETECCION RECALCULO INTELIGENTE ---
      // Detectar si es un documento de PH (Recibo o Factura) asociado a una unidad
      // Necesitamos la unidad_ph_id. Si el doc tiene unidad_ph_id o si se puede inferir.
      // El endpoint de update retorna el documento con unidad_ph_id si la tiene.

      const docUpdated = res.data;
      if (docUpdated.unidad_ph_id) {
        const fechaDoc = new Date(payload.fecha);
        const hoy = new Date();
        const mesDoc = new Date(fechaDoc.getFullYear(), fechaDoc.getMonth(), 1);
        const mesActual = new Date(hoy.getFullYear(), hoy.getMonth(), 1);

        if (mesDoc < mesActual) {
          setRecalculoData({ unidad_id: docUpdated.unidad_ph_id, fecha: payload.fecha });
          setShowRecalculoModal(true);
        }
      }

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

  const handleRecalcular = async () => {
    if (!recalculoData) return;
    setRecalculando(true);
    try {
      const res = await phService.recalcularIntereses(recalculoData.unidad_id, recalculoData.fecha);
      setRecalculoResult(res);
      setMensaje(`¡Documento actualizado y se ajustaron ${res.actualizadas} facturas posteriores!`);
      setTimeout(() => setShowRecalculoModal(false), 3000);
    } catch (err) {
      alert("Error recalculando: " + (err.response?.data?.detail || err.message));
    } finally {
      setRecalculando(false);
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
            <div className="flex gap-2">
              <select
                id="beneficiario"
                value={beneficiarioId}
                onChange={e => setBeneficiarioId(e.target.value)}
                className="mt-1 block w-full py-2 border-gray-300 rounded-md shadow-sm sm:text-sm focus:ring-indigo-500 focus:border-indigo-500"
                disabled={isReadOnly}
              >
                <option value="">Seleccione...</option>
                {terceros.map(t => <option key={t.id} value={t.id}>{t.razon_social}</option>)}
              </select>
              {!isReadOnly && (
                <button
                  type="button"
                  onClick={() => setIsTerceroModalOpen(true)}
                  className="mt-1 px-3 bg-indigo-100 text-indigo-600 rounded-md hover:bg-indigo-200 transition-colors"
                  title="Crear nuevo tercero"
                >
                  +
                </button>
              )}
            </div>
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
                      onBlur={e => handleCuentaBlur(index, e.target.value)}
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

      {/* MODAL RECALCULO */}
      {showRecalculoModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 animate-scaleIn border-t-4 border-indigo-500">
            <div className="flex items-center gap-3 mb-4 text-indigo-700">
              <div className="text-3xl">⚠️</div>
              <h3 className="text-xl font-bold">¡Edición Retroactiva Detectada!</h3>
            </div>
            <p className="text-gray-600 mb-6">
              Has modificado un documento con fecha anterior a este mes. Es posible que existan facturas posteriores con intereses de mora calculados sobre el saldo antiguo.
              <br /><br />
              <strong>¿Deseas recalcular automáticamente los intereses de las facturas futuras?</strong>
            </p>

            {recalculoResult ? (
              <div className="bg-green-100 text-green-700 p-3 rounded mb-4">
                <strong>¡Listo!</strong> Se actualizaron {recalculoResult.actualizadas} facturas.
              </div>
            ) : (
              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => setShowRecalculoModal(false)}
                  className="px-4 py-2 text-gray-500 hover:bg-gray-100 rounded-lg font-bold"
                  disabled={recalculando}
                >
                  No, dejar así
                </button>
                <button
                  onClick={handleRecalcular}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg font-bold hover:bg-indigo-700 shadow-lg flex items-center gap-2"
                  disabled={recalculando}
                >
                  {recalculando ? 'Procesando...' : 'SÍ, RECALCULAR INTERESES'}
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* MODAL TERCERO RÁPIDO */}
      {isTerceroModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex justify-center items-center z-50 animate-fadeIn">
          <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-sm border border-gray-100">
            <h2 className="text-xl font-bold mb-4 text-gray-800">Nuevo Tercero</h2>
            {terceroModalError && (
              <div className="p-3 mb-4 rounded-lg bg-red-50 text-red-600 border border-red-100 text-xs font-medium">
                {terceroModalError}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label htmlFor="modalNit" className="block text-xs font-bold text-gray-500 uppercase mb-1">NIT / ID</label>
                <input
                  type="text"
                  id="modalNit"
                  value={nuevoTercero.nit}
                  onChange={(e) => setNuevoTercero({ ...nuevoTercero, nit: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                  autoFocus
                />
              </div>
              <div>
                <label htmlFor="modalNombre" className="block text-xs font-bold text-gray-500 uppercase mb-1">Nombre / Razón Social</label>
                <input
                  type="text"
                  id="modalNombre"
                  value={nuevoTercero.razon_social}
                  onChange={(e) => setNuevoTercero({ ...nuevoTercero, razon_social: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => setIsTerceroModalOpen(false)}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg text-sm"
                disabled={isSubmittingTercero}
              >
                Cancelar
              </button>
              <button
                onClick={handleCreateTercero}
                disabled={isSubmittingTercero}
                className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 shadow-md disabled:bg-gray-400 text-sm font-bold"
              >
                {isSubmittingTercero ? 'Guardando...' : 'Crear y Seleccionar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}