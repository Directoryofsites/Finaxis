'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  FaSearch,
  FaTrash,
  FaBan,
  FaEdit,
  FaRedo,
  FaFilter,
  FaCheckCircle,
  FaExclamationTriangle,
  FaFileExport,
  FaBook
} from 'react-icons/fa';

import { useAuth } from '../../../context/AuthContext';
import { apiService } from '../../../../lib/apiService';
import BotonRegresar from '../../../components/BotonRegresar';

// Estilos reusables (Manual v2.0)
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white";

export default function EliminacionMasivaPage() {

  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [tiposDocumento, setTiposDocumento] = useState([]);
  const [terceros, setTerceros] = useState([]);
  const [cuentas, setCuentas] = useState([]);
  const [centrosCosto, setCentrosCosto] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const [filtros, setFiltros] = useState({
    tipoDocId: '', numero: '', fechaInicio: '', fechaFin: '',
    terceroId: '', cuentaId: '', centroCostoId: '',
    conceptoKeyword: '', valorOperador: 'mayor', valorMonto: ''
  });

  const [incluirAnulados, setIncluirAnulados] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [documentosEncontrados, setDocumentosEncontrados] = useState([]);
  const [seleccionados, setSeleccionados] = useState(new Set());
  const [razon, setRazon] = useState('');
  const [mensaje, setMensaje] = useState({ text: '', type: 'info' });

  useEffect(() => {
    if (authLoading) {
      setIsLoading(true);
      return;
    }
    if (!user || !user.empresaId) {
      setIsLoading(false);
      return;
    }

    const fetchMaestros = async () => {
      setIsLoading(true);
      setMensaje({ text: '', type: 'info' });
      try {
        const [
          tiposRes,
          tercerosRes,
          cuentasRes,
          ccRes
        ] = await Promise.all([
          apiService.get('/tipos-documento/'),
          apiService.get('/terceros/'),
          apiService.get('/plan-cuentas/list-flat/'),
          apiService.get('/centros-costo/get-flat'),
        ]);

        setTiposDocumento(tiposRes.data);
        setTerceros(tercerosRes.data);
        setCuentas(cuentasRes.data);
        setCentrosCosto(ccRes.data);

      } catch (err) {
        setMensaje({ text: parseApiError(err), type: 'error' });
      } finally {
        setIsLoading(false);
      }
    };

    fetchMaestros();

  }, [user, authLoading]);

  const handleFiltroChange = (e) => {
    const { name, value } = e.target;
    setFiltros(prev => ({ ...prev, [name]: value }));
  };

  const handleBuscar = async () => {
    setIsSearching(true);
    setMensaje({ text: '', type: 'info' });
    setDocumentosEncontrados([]);
    setSeleccionados(new Set());
    try {
      const filtrosParaApi = { ...filtros };

      const camposNumericos = ['tipoDocId', 'terceroId', 'cuentaId', 'centroCostoId', 'valorMonto'];
      camposNumericos.forEach(key => {
        if (filtrosParaApi[key]) {
          const numValue = parseFloat(filtrosParaApi[key]);
          if (!isNaN(numValue)) {
            // Mapeo especial para coincidir con DocumentoGestionFiltros del backend (Listas)
            if (key === 'tipoDocId') filtrosParaApi.tipoDocIds = [numValue];
            else if (key === 'terceroId') filtrosParaApi.terceroIds = [numValue];
            else if (key === 'cuentaId') filtrosParaApi.cuentaIds = [numValue];
            else if (key === 'centroCostoId') filtrosParaApi.centroCostoIds = [numValue];
            else filtrosParaApi[key] = numValue; // valorMonto se queda igual
          }
          // Limpiamos la clave singular original para no ensuciar
          if (['tipoDocId', 'terceroId', 'cuentaId', 'centroCostoId'].includes(key)) {
            delete filtrosParaApi[key];
          } else if (isNaN(numValue)) {
            delete filtrosParaApi[key];
          }
        } else {
          delete filtrosParaApi[key];
        }
      });

      if (!filtrosParaApi.fechaInicio) delete filtrosParaApi.fechaInicio;
      if (!filtrosParaApi.fechaFin) delete filtrosParaApi.fechaFin;

      const payload = {
        ...filtrosParaApi,
        incluirAnulados: incluirAnulados,
        tipoEntidad: 'documento'
      };

      const res = await apiService.post('/documentos/buscar-para-gestion', payload);

      setDocumentosEncontrados(res.data);
      if (res.data.length === 0) {
        setMensaje({ text: 'No se encontraron documentos con esos criterios.', type: 'info' });
      }
    } catch (err) {
      setMensaje({ text: parseApiError(err), type: 'error' });
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      const idsParaSeleccionar = documentosEncontrados.filter(d => !d.anulado).map(d => d.id);
      setSeleccionados(new Set(idsParaSeleccionar));
    } else {
      setSeleccionados(new Set());
    }
  };

  const handleSelectOne = (id, isAnulado) => {
    if (isAnulado) {
      alert("No se pueden seleccionar documentos anulados para acciones masivas. Use la acción 'Reactivar' individualmente.");
      return;
    }
    const nuevosSeleccionados = new Set(seleccionados);
    nuevosSeleccionados.has(id) ? nuevosSeleccionados.delete(id) : nuevosSeleccionados.add(id);
    setSeleccionados(nuevosSeleccionados);
  };

  const handleAction = async (actionType) => {
    setMensaje({ text: '', type: 'info' });
    const endpointMap = { anular: 'anulacion-masiva', eliminar: 'eliminacion-masiva' };
    const endpoint = `/documentos/${endpointMap[actionType]}`;

    if (actionType === 'eliminar') {
      const confirmText = 'ELIMINAR';
      const promptMessage = `ACCIÓN DE ALTO RIESGO\n\nEstás a punto de eliminar ${seleccionados.size} documento(s).\nEsta acción puede liberar consecutivos para ser reutilizados.\n\nPara confirmar, escribe la palabra "${confirmText}" en el campo de abajo.`;
      const userInput = window.prompt(promptMessage);
      if (userInput !== confirmText) {
        if (userInput !== null) alert('La palabra no coincide. La operación ha sido cancelada.');
        return;
      }
    } else {
      if (!window.confirm(`¿Estás seguro de que deseas ANULAR ${seleccionados.size} documento(s)?`)) return;
    }

    setIsSearching(true);
    try {
      const payload = {
        documentoIds: Array.from(seleccionados),
        razon: razon
      };

      const result = await apiService.post(endpoint, payload);

      alert(result.data.message);
      handleBuscar();
      setRazon('');
      setSeleccionados(new Set());

    } catch (err) {
      setMensaje({ text: parseApiError(err), type: 'error' });
    } finally {
      setIsSearching(false);
    }
  };

  const handleReactivar = async (docId) => {
    if (!window.confirm("¿Estás seguro de que deseas reactivar este documento?")) return;
    setMensaje({ text: '', type: 'info' });
    setIsSearching(true);
    try {
      const res = await apiService.put(`/documentos/${docId}/reactivar`);
      alert(`Documento ${res.data.numero} reactivado exitosamente.`);
      handleBuscar();
    } catch (err) {
      setMensaje({ text: parseApiError(err), type: 'error' });
    } finally {
      setIsSearching(false);
    }
  };

  const handleModificar = () => {
    if (seleccionados.size !== 1) {
      alert("Por favor, seleccione un único documento para poder modificarlo.");
      return;
    }
    const [documentoId] = seleccionados;
    router.push(`/contabilidad/documentos/detalle/${documentoId}?from=/admin/utilidades/eliminacion-masiva`);
  };

  const handleSendToTemplate = async () => {
    if (seleccionados.size !== 1) {
      alert("Por favor, seleccione un único documento para enviar a plantilla.");
      return;
    }
    const [documentoId] = seleccionados;

    const newName = window.prompt("Por favor, ingresa un nombre para la nueva plantilla:");
    if (!newName || newName.trim() === '') {
      if (newName !== null) alert("El nombre no puede estar vacío. Operación cancelada.");
      return;
    }

    setIsSearching(true);
    setMensaje({ text: `Creando plantilla "${newName.trim()}"...`, type: 'info' });

    try {
      const payload = { nombre_plantilla: newName.trim() };
      const res = await apiService.post(`/documentos/${documentoId}/crear-plantilla`, payload);
      setMensaje({ text: `¡Éxito! Plantilla "${res.data.nombre_plantilla}" creada correctamente.`, type: 'info' });
      setSeleccionados(new Set());
    } catch (err) {
      setMensaje({ text: parseApiError(err), type: 'error' });
    } finally {
      setIsSearching(false);
    }
  };

  const parseApiError = (err) => {
    const detail = err.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      const firstError = detail[0];
      const field = firstError.loc?.slice(1)?.join(' -> ') || 'desconocido';
      return `Error de validación en campo '${field}': ${firstError.msg}`;
    }
    return err.message || 'Ocurrió un error inesperado.';
  };

  if (isLoading || authLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
        <FaSearch className="text-indigo-300 text-6xl mb-4 animate-pulse" />
        <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando herramientas de gestión...</p>
      </div>
    );
  }

  if (!user) return <p className="text-center text-red-500 p-8">No se pudo verificar la sesión.</p>;

  return (
    <div className="min-h-screen bg-gray-50 p-6 font-sans">
      <div className="max-w-7xl mx-auto">

        {/* ENCABEZADO */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
          <div>
            <BotonRegresar />
            <div className="flex items-center gap-3 mt-3">
              <div className="p-2 bg-red-100 rounded-lg text-red-600">
                <FaTrash className="text-xl" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-800">Gestión Masiva de Documentos</h1>
                <p className="text-gray-500 text-sm">Búsqueda avanzada para anular, eliminar o modificar documentos.</p>
              </div>
            </div>
          </div>
          <button
            onClick={() => window.open('/manual/capitulo_11_eliminacion.html', '_blank')}
            className="btn btn-ghost text-indigo-600 hover:bg-indigo-50 gap-2 flex items-center"
            title="Ver Manual de Usuario"
          >
            <FaBook className="text-lg" /> <span className="font-bold hidden md:inline">Manual</span>
          </button>
        </div>

        {/* CARD 1: FILTROS DE BÚSQUEDA */}
        <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 animate-fadeIn mb-8">
          <div className="flex items-center gap-2 mb-6 border-b border-gray-100 pb-2">
            <FaFilter className="text-indigo-500" />
            <h2 className="text-lg font-bold text-gray-700">Criterios de Búsqueda</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Columna 1: Identificación */}
            <div className="space-y-4">
              <div><label className={labelClass}>Tipo de Documento</label><select name="tipoDocId" value={filtros.tipoDocId} onChange={handleFiltroChange} className={selectClass}><option value="">Todos</option>{tiposDocumento.map(t => <option key={t.id} value={t.id}>{t.nombre}</option>)}</select></div>
              <div><label className={labelClass}>Tercero (Beneficiario)</label><select name="terceroId" value={filtros.terceroId} onChange={handleFiltroChange} className={selectClass}><option value="">Todos</option>{terceros.map(t => <option key={t.id} value={t.id}>{t.razon_social}</option>)}</select></div>
              <div><label className={labelClass}>Número(s) de Documento</label><input type="text" name="numero" value={filtros.numero} onChange={handleFiltroChange} placeholder="Ej: 101, 105, 210" className={inputClass} /><p className="text-xs text-gray-400 mt-1">Separar por comas para varios.</p></div>
            </div>

            {/* Columna 2: Clasificación */}
            <div className="space-y-4">
              <div><label className={labelClass}>Cuenta Contable</label><select name="cuentaId" value={filtros.cuentaId} onChange={handleFiltroChange} className={selectClass}><option value="">Todas</option>{cuentas.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}</select></div>
              <div><label className={labelClass}>Centro de Costo</label><select name="centroCostoId" value={filtros.centroCostoId} onChange={handleFiltroChange} className={selectClass}><option value="">Todos</option>{centrosCosto.map(c => <option key={c.id} value={c.id}>{c.nombre}</option>)}</select></div>
              <div><label className={labelClass}>Palabra en Concepto</label><input type="text" name="conceptoKeyword" value={filtros.conceptoKeyword} onChange={handleFiltroChange} placeholder="Ej: Arriendo" className={inputClass} /></div>
            </div>

            {/* Columna 3: Rango y Valor */}
            <div className="space-y-4">
              <div><label className={labelClass}>Rango de Fechas</label><div className="flex gap-2"><input type="date" name="fechaInicio" value={filtros.fechaInicio} onChange={handleFiltroChange} className={inputClass} /><input type="date" name="fechaFin" value={filtros.fechaFin} onChange={handleFiltroChange} className={inputClass} /></div></div>
              <div><label className={labelClass}>Filtro por Valor</label><div className="flex gap-2"><select name="valorOperador" value={filtros.valorOperador} onChange={handleFiltroChange} className={`${selectClass} w-1/3`}><option value="mayor">Mayor</option><option value="menor">Menor</option><option value="igual">Igual</option></select><input type="number" name="valorMonto" value={filtros.valorMonto} onChange={handleFiltroChange} placeholder="0.00" className={inputClass} /></div></div>
            </div>
          </div>

          <div className="flex justify-between items-center mt-8 pt-4 border-t border-gray-100">
            <div className="flex items-center bg-gray-50 px-4 py-2 rounded-lg border border-gray-200">
              <input id="incluir-anulados" type="checkbox" checked={incluirAnulados} onChange={(e) => setIncluirAnulados(e.target.checked)} className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded cursor-pointer" />
              <label htmlFor="incluir-anulados" className="ml-2 block text-sm font-bold text-gray-700 cursor-pointer">Incluir Documentos Anulados</label>
            </div>
            <button type="button" onClick={handleBuscar} disabled={isSearching} className="bg-indigo-600 hover:bg-indigo-800 text-white font-bold py-2 px-8 rounded-lg shadow-lg transform hover:-translate-y-0.5 transition-all flex items-center gap-2">
              {isSearching ? <><span className="loading loading-spinner loading-sm"></span> Buscando...</> : <><FaSearch /> Buscar Documentos</>}
            </button>
          </div>
        </div>

        {/* MENSAJES DE ESTADO */}
        {mensaje.text && (
          <div className={`mb-6 p-4 rounded-lg border-l-4 shadow-sm flex items-start gap-3 ${mensaje.type === 'error' ? 'bg-red-50 border-red-500 text-red-700' : 'bg-blue-50 border-blue-500 text-blue-700'}`}>
            {mensaje.type === 'error' ? <FaExclamationTriangle className="text-xl mt-1" /> : <FaCheckCircle className="text-xl mt-1" />}
            <div>
              <p className="font-bold">{mensaje.type === 'error' ? 'Error' : 'Información'}</p>
              <p className="text-sm">{mensaje.text}</p>
            </div>
          </div>
        )}

        {/* CARD 2: RESULTADOS */}
        {documentosEncontrados.length > 0 && (
          <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 animate-slideDown">
            <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
              <span className="bg-gray-100 text-gray-600 w-8 h-8 flex items-center justify-center rounded-full text-sm">
                {documentosEncontrados.length}
              </span>
              Resultados Encontrados
            </h2>

            <div className="overflow-x-auto mb-6 rounded-lg border border-gray-200">
              <table className="min-w-full bg-white">
                <thead className="bg-slate-100">
                  <tr>
                    <th className="py-3 px-4 text-center w-10 border-b border-gray-200"><input type="checkbox" onChange={handleSelectAll} className="cursor-pointer checkbox checkbox-xs" checked={documentosEncontrados.filter(d => !d.anulado).length > 0 && seleccionados.size === documentosEncontrados.filter(d => !d.anulado).length} /></th>
                    <th className="py-3 px-4 text-left text-xs font-bold text-gray-600 uppercase tracking-wider border-b border-gray-200">Fecha</th>
                    <th className="py-3 px-4 text-left text-xs font-bold text-gray-600 uppercase tracking-wider border-b border-gray-200">Documento</th>
                    <th className="py-3 px-4 text-left text-xs font-bold text-gray-600 uppercase tracking-wider border-b border-gray-200">Beneficiario</th>
                    <th className="py-3 px-4 text-right text-xs font-bold text-gray-600 uppercase tracking-wider border-b border-gray-200">Total</th>
                    <th className="py-3 px-4 text-center text-xs font-bold text-gray-600 uppercase tracking-wider border-b border-gray-200">Estado</th>
                    <th className="py-3 px-4 text-center text-xs font-bold text-gray-600 uppercase tracking-wider border-b border-gray-200">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {documentosEncontrados.map(doc => (
                    <tr key={doc.id} className={`hover:bg-indigo-50/30 transition-colors ${doc.anulado ? 'bg-red-50/50' : ''}`}>
                      <td className="py-3 px-4 text-center"><input type="checkbox" onChange={() => handleSelectOne(doc.id, doc.anulado)} checked={seleccionados.has(doc.id)} disabled={doc.anulado} className="cursor-pointer checkbox checkbox-xs" /></td>
                      <td className="py-3 px-4 text-sm text-gray-600">{new Date(doc.fecha + 'T00:00:00').toLocaleDateString('es-CO')}</td>
                      <td className="py-3 px-4 text-sm font-medium text-gray-800">
                        <span className="block text-xs text-gray-500">{doc.tipo_documento}</span>
                        <span className="font-mono">#{doc.numero}</span>
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-600">{doc.beneficiario}</td>
                      <td className="py-3 px-4 text-right text-sm font-mono font-bold text-gray-700">{new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(doc.total)}</td>
                      <td className="py-3 px-4 text-center">
                        <span className={`px-2 py-1 text-xs font-bold rounded-full ${doc.anulado ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'}`}>
                          {doc.anulado ? 'ANULADO' : 'ACTIVO'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center">
                        {doc.anulado && (
                          <button onClick={() => handleReactivar(doc.id)} className="text-teal-600 hover:text-teal-800 hover:bg-teal-50 p-2 rounded-lg transition-colors" title="Reactivar Documento" disabled={isSearching}>
                            <FaRedo />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* ZONA DE ACCIONES FINALES */}
            <div className="bg-gray-50 p-4 rounded-xl border border-gray-200">
              <div className="mb-4">
                <label htmlFor="razon" className={labelClass}>Justificación (Obligatoria para eliminar)</label>
                <textarea id="razon" name="razon" rows="2" value={razon} onChange={(e) => setRazon(e.target.value)} className={inputClass} placeholder="Escriba el motivo de la anulación o eliminación..."></textarea>
              </div>

              <div className="flex flex-wrap justify-end gap-3">
                <button onClick={handleSendToTemplate} className="btn bg-purple-600 hover:bg-purple-700 text-white border-none shadow-md flex gap-2" disabled={seleccionados.size !== 1 || isSearching}>
                  <FaFileExport /> Guardar como Plantilla
                </button>
                <button onClick={handleModificar} className="btn bg-blue-600 hover:bg-blue-700 text-white border-none shadow-md flex gap-2" disabled={seleccionados.size !== 1 || isSearching}>
                  <FaEdit /> Modificar
                </button>
                <div className="w-px bg-gray-300 mx-2 hidden md:block"></div>
                <button onClick={() => handleAction('anular')} className="btn bg-orange-500 hover:bg-orange-600 text-white border-none shadow-md flex gap-2" disabled={seleccionados.size === 0 || isSearching}>
                  <FaBan /> Anular Seleccionados
                </button>
                <button onClick={() => handleAction('eliminar')} className="btn bg-red-600 hover:bg-red-700 text-white border-none shadow-md flex gap-2" disabled={seleccionados.size === 0 || !razon || isSearching}>
                  {isSearching ? <span className="loading loading-spinner loading-sm"></span> : <><FaTrash /> Eliminar Definitivamente</>}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}