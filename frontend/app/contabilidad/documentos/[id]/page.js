'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import { useAuth } from '../../../context/AuthContext';
import Link from 'next/link';
import { useParams, useSearchParams } from 'next/navigation';

export default function DocumentoDetallePage() {
  const { user } = useAuth();
  const { id } = useParams();
  const searchParams = useSearchParams();
  const returnPath = searchParams.get('from');

  // --- ESTADOS ---
  const [documento, setDocumento] = useState(null);
  const [editedDocument, setEditedDocument] = useState(null);
  const [isEditing, setIsEditing] = useState(false);

  const [cuentas, setCuentas] = useState([]);
  const [terceros, setTerceros] = useState([]);
  const [centrosCosto, setCentrosCosto] = useState([]);
  const [tiposDocumento, setTiposDocumento] = useState([]); // Añadido para tener todos los maestros
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // --- CARGA DE DATOS ---
  const fetchAllData = useCallback(async () => {
    if (!id || !user || !user.empresaId) return;
    setIsLoading(true);
    setError('');
    try {
      // --- CÓDIGO CORREGIDO ---
      // Se añade user.empresaId a todas las llamadas de datos maestros
      const [
        docRes,
        cuentasRes,
        tercerosRes,
        tiposDocRes,
        costoRes
      ] = await Promise.all([
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/documentos/${id}`),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/plan-cuentas/puc?empresa_id=${user.empresaId}`),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/terceros?empresa_id=${user.empresaId}`),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/tipos-documento?empresa_id=${user.empresaId}`),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/centros-costo?empresa_id=${user.empresaId}&permite_movimiento=true`),
      ]);

      const responses = [docRes, cuentasRes, tercerosRes, tiposDocRes, costoRes];
      for (const res of responses) {
        if (!res.ok) {
          const errorData = await res.json().catch(() => ({ message: `Error de red en ${res.url}` }));
          throw new Error(errorData.message || 'Error al cargar datos maestros.');
        }
      }

      const [docData, cuentasData, tercerosData, tiposDocData, costoData] = await Promise.all(responses.map(res => res.json()));

      setDocumento(docData);
      setCuentas(cuentasData);
      setTerceros(tercerosData);
      setTiposDocumento(tiposDocData);
      setCentrosCosto(costoData);

    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [id, user]);

  useEffect(() => {
    fetchAllData();
  }, [fetchAllData]);

  // --- CÁLCULOS Y VALIDACIONES ---
  const formatCurrency = (value) => new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(parseFloat(value) || 0);

  const readOnlyTotals = useMemo(() => {
    if (!documento) return { debito: 0, credito: 0 };
    return documento.movimientos.reduce((acc, mov) => {
      acc.debito += parseFloat(mov.debito) || 0;
      acc.credito += parseFloat(mov.credito) || 0;
      return acc;
    }, { debito: 0, credito: 0 });
  }, [documento]);

  const editTotals = useMemo(() => {
    if (!isEditing || !editedDocument) return { debito: 0, credito: 0 };
    return editedDocument.movimientos.reduce((acc, mov) => {
      acc.debito += parseFloat(mov.debito) || 0;
      acc.credito += parseFloat(mov.credito) || 0;
      return acc;
    }, { debito: 0, credito: 0 });
  }, [editedDocument, isEditing]);

  const isEditFormBalanced = useMemo(() => {
    const difference = Math.abs(editTotals.debito - editTotals.credito);
    return difference < 0.01 && editTotals.debito !== 0; // Tolerancia para decimales
  }, [editTotals]);

  // --- MANEJADORES DE EVENTOS ---
  const handleFormChange = (e) => {
    const { name, value } = e.target;
    const isNumericId = ['beneficiario_id', 'centro_costo_id', 'tipo_documento_id'].includes(name);
    setEditedDocument(prev => ({ ...prev, [name]: isNumericId ? parseInt(value, 10) || null : value }));
  };

  const handleMovementChange = (index, e) => {
    const { name, value } = e.target;
    const newMovements = [...editedDocument.movimientos];
    newMovements[index] = { ...newMovements[index], [name]: value };
    setEditedDocument(prev => ({ ...prev, movimientos: newMovements }));
  };

  const handleAddNewRow = () => {
    setEditedDocument(prev => ({
      ...prev,
      movimientos: [...prev.movimientos, { cuenta_id: '', concepto: '', debito: 0, credito: 0 }]
    }));
  };

  const handleRemoveRow = (index) => {
    setEditedDocument(prev => ({
      ...prev,
      movimientos: prev.movimientos.filter((_, i) => i !== index)
    }));
  };

  const handleSaveChanges = async () => {
    if (!isEditFormBalanced) {
      alert("No se puede guardar un documento descuadrado.");
      return;
    }
    setIsLoading(true);
    setError('');
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/documentos/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editedDocument),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.message || 'Error al actualizar.');
      alert(result.message);

      // Volvemos a cargar los datos para reflejar los nombres y no solo los IDs
      await fetchAllData();

      setIsEditing(false);
    } catch (err) {
      setError(err.message);
      alert(`Error: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // --- RENDERIZADO PRINCIPAL ---
  if (isLoading) return <div className="flex justify-center items-center h-screen"><p>Cargando documento...</p></div>;
  if (error) return <div className="flex justify-center items-center h-screen"><p className="text-red-500">Error: {error}</p></div>;
  if (!documento) return <div className="flex justify-center items-center h-screen"><p>No se encontró el documento.</p></div>;

  return (
    <div className="container mx-auto p-8 bg-gray-50 min-h-screen">
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-4">
          <h1 className="text-3xl font-bold text-gray-800">
            {isEditing ? `Editando Documento` : `Detalle del Documento`}
          </h1>
          {!isEditing && (
            <button
              onClick={() => window.open('/manual/capitulo_10_edicion.html', '_blank')}
              className="px-2 py-1 text-indigo-600 hover:bg-indigo-50 rounded-md font-bold flex items-center gap-2"
              title="Ver Manual de Usuario"
            >
              <span className="text-lg">📖</span> <span className="hidden md:inline">Manual</span>
            </button>
          )}
        </div>

        <div className="flex gap-2">
          {!isEditing ? (
            <>
              {!documento.anulado && (
                <button onClick={() => { setIsEditing(true); setEditedDocument(JSON.parse(JSON.stringify(documento))); }} className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700">Editar</button>
              )}
            </>
          ) : (
            <>
              <button onClick={() => setIsEditing(false)} className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600">Cancelar</button>
              <button onClick={handleSaveChanges} disabled={!isEditFormBalanced || isLoading} className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400">Guardar Cambios</button>
            </>
          )}
        </div>
      </div>

      {documento.anulado && (
        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 my-6" role="alert">
          <p className="font-bold">Documento Anulado</p>
          <p>Este documento ha sido anulado y su efecto en la contabilidad es nulo.</p>
        </div>
      )}

      {isEditing && editedDocument ? (
        // MODO EDICIÓN
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg shadow-md grid grid-cols-2 md:grid-cols-4 gap-4">
            <div><label className="text-sm font-medium text-gray-500">Tipo Documento</label><select name="tipo_documento_id" value={editedDocument.tipo_documento_id || ''} onChange={handleFormChange} className="mt-1 block w-full border-gray-300 rounded-md"><option value="">Seleccione...</option>{tiposDocumento.map(t => <option key={t.id} value={t.id}>{t.nombre}</option>)}</select></div>
            <div><label className="text-sm font-medium text-gray-500">Número</label><input type="text" name="numero" value={editedDocument.numero} onChange={handleFormChange} className="mt-1 block w-full border-gray-300 rounded-md bg-gray-100" readOnly /></div>
            <div><label className="text-sm font-medium text-gray-500">Fecha</label><input type="date" name="fecha" value={new Date(editedDocument.fecha).toISOString().split('T')[0]} onChange={handleFormChange} className="mt-1 block w-full border-gray-300 rounded-md" /></div>
            <div><label className="text-sm font-medium text-gray-500">Tercero</label><select name="beneficiario_id" value={editedDocument.beneficiario_id || ''} onChange={handleFormChange} className="mt-1 block w-full border-gray-300 rounded-md"><option value="">Seleccione...</option>{terceros.map(t => <option key={t.id} value={t.id}>{t.razon_social}</option>)}</select></div>
            <div><label className="text-sm font-medium text-gray-500">Centro de Costo</label><select name="centro_costo_id" value={editedDocument.centro_costo_id || ''} onChange={handleFormChange} className="mt-1 block w-full border-gray-300 rounded-md"><option value="">Seleccione...</option>{centrosCosto.map(c => <option key={c.id} value={c.id}>{c.nombre}</option>)}</select></div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-xl font-semibold mb-4">Editar Movimientos</h2>
            <table className="min-w-full">
              <thead><tr><th className="text-left py-2 w-2/5">Cuenta</th><th className="text-left py-2 w-2/5">Concepto</th><th className="text-left py-2">Débito</th><th className="text-left py-2">Crédito</th><th className="py-2"></th></tr></thead>
              <tbody>
                {editedDocument.movimientos.map((mov, index) => (
                  <tr key={index}>
                    <td className="pr-2 py-1"><select name="cuenta_id" value={mov.cuenta_id} onChange={(e) => handleMovementChange(index, e)} className="w-full border-gray-300 rounded-md text-sm">{cuentas.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}</select></td>
                    <td className="pr-2 py-1"><input type="text" name="concepto" value={mov.concepto} onChange={(e) => handleMovementChange(index, e)} className="w-full border-gray-300 rounded-md text-sm" /></td>
                    <td className="pr-2 py-1"><input type="number" step="0.01" name="debito" value={mov.debito} onChange={(e) => handleMovementChange(index, e)} className="w-full border-gray-300 rounded-md text-right text-sm" /></td>
                    <td className="py-1"><input type="number" step="0.01" name="credito" value={mov.credito} onChange={(e) => handleMovementChange(index, e)} className="w-full border-gray-300 rounded-md text-right text-sm" /></td>
                    <td className="py-1"><button onClick={() => handleRemoveRow(index)} className="text-red-500 hover:text-red-700">X</button></td>
                  </tr>
                ))}
              </tbody>
              <tfoot className="bg-gray-100 font-bold"><tr><td colSpan="2" className="text-right pr-4 py-2">TOTALES</td><td className="text-right pr-1 py-2 font-mono">{formatCurrency(editTotals.debito)}</td><td className="text-right py-2 font-mono">{formatCurrency(editTotals.credito)}</td><td></td></tr></tfoot>
            </table>
            <button onClick={handleAddNewRow} className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 text-sm">+ Añadir Fila</button>
            {!isEditFormBalanced && <p className="text-center text-red-500 font-semibold mt-4">El documento no está balanceado.</p>}
          </div>
        </div>
      ) : (
        // MODO VISTA
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-xl font-semibold mb-4 border-b pb-2">Información General</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div><p className="text-sm font-medium text-gray-500">Tipo</p><p>{documento.tipo_documento}</p></div>
              <div><p className="text-sm font-medium text-gray-500">Número</p><p>{documento.numero || 'N/A'}</p></div>
              <div><p className="text-sm font-medium text-gray-500">Fecha</p><p>{new Date(documento.fecha).toLocaleDateString('es-CO')}</p></div>
              <div><p className="text-sm font-medium text-gray-500">Beneficiario</p><p>{documento.beneficiario}</p></div>
              <div><p className="text-sm font-medium text-gray-500">C. Costo</p><p>{documento.centro_costo || 'N/A'}</p></div>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-xl font-semibold mb-4">Movimientos Contables</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50"><tr className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider"><th className="px-6 py-3">Cuenta</th><th className="px-6 py-3">Concepto</th><th className="px-6 py-3 text-right">Débito</th><th className="px-6 py-3 text-right">Crédito</th></tr></thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {documento.movimientos.map((mov) => (<tr key={mov.id}><td className="px-6 py-4 whitespace-nowrap">{mov.cuenta_codigo} - {mov.cuenta_nombre}</td><td className="px-6 py-4">{mov.concepto}</td><td className="px-6 py-4 text-right font-mono">{formatCurrency(mov.debito)}</td><td className="px-6 py-4 text-right font-mono">{formatCurrency(mov.credito)}</td></tr>))}
                </tbody>
                <tfoot className="bg-gray-50 font-bold"><tr><td colSpan="2" className="px-6 py-3 text-right">TOTALES</td><td className="px-6 py-4 text-right font-mono">{formatCurrency(readOnlyTotals.debito)}</td><td className="px-6 py-4 text-right font-mono">{formatCurrency(readOnlyTotals.credito)}</td></tr></tfoot>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}