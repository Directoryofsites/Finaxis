'use client';

import React, { useState } from 'react';
import { FaBook } from 'react-icons/fa';
// Se importa la nueva función del servicio de soporte
import { inspeccionarEntidades, erradicarEntidadesMaestras, iniciarReseteoPassword } from '../../../../../lib/soporteApiService';

export default function InspectorMaestros({ todasLasEmpresas }) {
  const [empresaId, setEmpresaId] = useState('');
  const [tipoEntidad, setTipoEntidad] = useState('usuarios'); // Cambiado a 'usuarios' por defecto
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [reporte, setReporte] = useState(null);
  const [selection, setSelection] = useState(new Set());

  // Estado dedicado para la acción de reseteo para no mezclar mensajes
  const [resetStatus, setResetStatus] = useState({ loading: false, message: '', error: '' });

  const handleInspect = async () => {
    if (!empresaId || !tipoEntidad) {
      setError("Por favor, seleccione una empresa y un tipo de entidad.");
      return;
    }
    setIsLoading(true);
    setError('');
    setMessage('');
    setReporte(null);
    setSelection(new Set());
    setResetStatus({ loading: false, message: '', error: '' }); // Limpiar estado de reseteo

    try {
      const payload = { empresa_id: parseInt(empresaId), tipo_entidad: tipoEntidad };
      const { data } = await inspeccionarEntidades(payload);
      setReporte(data);
      setMessage(`Inspección completada. Se encontraron ${data.length} registros.`);
    } catch (err) {
      // Manejo de errores robusto para evitar el crash de React
      const errorDetail = err.response?.data?.detail;
      if (Array.isArray(errorDetail) && errorDetail.length > 0) {
        // Si es un error de validación de Pydantic, muestra el primer mensaje.
        setError(`Error de validación: ${errorDetail[0].msg}`);
      } else if (typeof errorDetail === 'string') {
        // Si es un string, muéstralo directamente.
        setError(errorDetail);
      } else {
        setError('Ocurrió un error desconocido al realizar la inspección.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetPassword = async (emailUsuario) => {
    if (!emailUsuario) {
      setResetStatus({ loading: false, message: '', error: 'El registro seleccionado no tiene un email válido para el reseteo.' });
      return;
    }

    const confirmMessage = `¿Está seguro de que desea iniciar el reseteo de contraseña para el usuario "${emailUsuario}"? Se generará un nuevo enlace de acceso.`;
    if (!window.confirm(confirmMessage)) {
      return;
    }

    setResetStatus({ loading: true, message: '', error: '' });
    setMessage(''); // Limpiar mensajes generales
    setError('');

    try {
      const payload = { email: emailUsuario };
      const { data } = await iniciarReseteoPassword(payload);
      setResetStatus({ loading: false, message: data.msg, error: '' });

      // Mostramos al operador el enlace/token para que pueda dárselo al usuario
      alert(`Éxito:\n\n${data.msg}\n\nEnlace de Ejemplo (para desarrollo):\n${data.reset_url_ejemplo}`);

      // --- NUEVO LOG PARA FACILITAR COPIADO ---
      console.log("URL de Reseteo (para copiar):", data.reset_url_ejemplo);

    } catch (err) {
      const errorDetail = err.response?.data?.detail || 'Error al iniciar el reseteo de contraseña.';
      setResetStatus({ loading: false, message: '', error: errorDetail });
    }
  };

  const handleEradicate = async () => {
    if (selection.size === 0) {
      setError("No ha seleccionado ningún registro para erradicar.");
      return;
    }

    const confirmMessage = `¿Está seguro de que desea erradicar ${selection.size} registro(s) de tipo '${tipoEntidad}' de la empresa seleccionada? ESTA ACCIÓN ES IRREVERSIBLE Y BORRARÁ TODOS LOS DATOS ASOCIADOS (DOCUMENTOS, MOVIMIENTOS, ETC.).`;
    if (!window.confirm(confirmMessage)) {
      return;
    }

    setIsLoading(true);
    setError('');
    setMessage('');

    try {
      const payload = {
        empresa_id: parseInt(empresaId),
        tipo_entidad: tipoEntidad,
        ids_a_erradicar: Array.from(selection)
      };
      const { data } = await erradicarEntidadesMaestras(payload);
      setMessage(data.message);
      setReporte(null);
      setSelection(new Set());
      handleInspect(); // Re-inspeccionar para ver el resultado
    } catch (err) {
      setError(err.response?.data?.detail || 'Error durante la erradicación.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectionChange = (id) => {
    setSelection(prevSelection => {
      const newSelection = new Set(prevSelection);
      if (newSelection.has(id)) {
        newSelection.delete(id);
      } else {
        newSelection.add(id);
      }
      return newSelection;
    });
  };

  const handleSelectAll = () => {
    if (reporte) {
      if (selection.size === reporte.length) {
        setSelection(new Set()); // Deseleccionar todos
      } else {
        setSelection(new Set(reporte.map(item => item.id))); // Seleccionar todos
      }
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md border-l-4 border-red-600">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-xl font-bold text-red-800">Inspector y Erradicador de Datos Maestros</h3>
        <button
          onClick={() => window.open('/manual?file=capitulo_18_inspector_maestros.md', '_blank')}
          className="text-indigo-600 hover:bg-indigo-50 px-3 py-1 rounded-md flex items-center gap-2 transition-colors"
          title="Ver Manual de Usuario"
        >
          <FaBook className="text-lg" /> <span className="font-bold text-sm">Manual</span>
        </button>
      </div>

      <div className="flex flex-wrap gap-4 items-end bg-gray-50 p-4 rounded-md border">
        <div>
          <label htmlFor="empresa" className="block text-sm font-medium text-gray-700">1. Seleccione Empresa</label>
          <select id="empresa" value={empresaId} onChange={(e) => setEmpresaId(e.target.value)} className="mt-1 block w-full md:w-64 py-2 px-3 border border-gray-300 rounded-md">
            <option value="">-- Empresa --</option>
            {todasLasEmpresas.map(e => <option key={e.id} value={e.id}>{e.razon_social}</option>)}
          </select>
        </div>

        <div>
          <label htmlFor="entidad" className="block text-sm font-medium text-gray-700">2. Seleccione Cartilla</label>
          <select id="entidad" value={tipoEntidad} onChange={(e) => setTipoEntidad(e.target.value)} className="mt-1 block w-full md:w-64 py-2 px-3 border border-gray-300 rounded-md">
            <option value="usuarios">Usuarios</option>
            <option value="terceros">Terceros</option>
            <option value="plan_cuentas">Plan de Cuentas</option>
            <option value="centros_costo">Centros de Costo</option>
            <option value="tipos_documento">Tipos de Documento</option>
            <option value="plantillas_maestras">Plantillas de Documentos</option>
            <option value="conceptos_favoritos">Conceptos Favoritos</option>
          </select>
        </div>

        <button onClick={handleInspect} disabled={isLoading || !empresaId} className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md disabled:bg-gray-400">
          {isLoading ? 'Inspeccionando...' : '3. Inspeccionar'}
        </button>
      </div>

      {error && <div className="bg-red-100 text-red-700 p-3 my-4 rounded-md text-sm">{error}</div>}
      {message && <div className="bg-green-100 text-green-700 p-3 my-4 rounded-md text-sm">{message}</div>}
      {resetStatus.error && <div className="bg-red-100 text-red-700 p-3 my-4 rounded-md text-sm">{resetStatus.error}</div>}
      {resetStatus.message && <div className="bg-blue-100 text-blue-700 p-3 my-4 rounded-md text-sm">{resetStatus.message}</div>}

      {reporte && (
        <div className="mt-6">
          <div className="flex justify-between items-center mb-2">
            <h4 className="text-lg font-semibold">Resultado de la Inspección ({reporte.length} registros)</h4>
            <button onClick={handleEradicate} disabled={isLoading || selection.size === 0} className="bg-red-600 hover:bg-red-800 text-white font-bold py-2 px-4 rounded-md disabled:bg-red-300">
              {`Erradicar (${selection.size}) Seleccionado(s)`}
            </button>
          </div>
          <div className="overflow-x-auto border rounded-md">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-100">
                <tr>
                  <th className="px-4 py-2 text-left"><input type="checkbox" onChange={handleSelectAll} checked={reporte.length > 0 && selection.size === reporte.length} /></th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Descripción Principal</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Descripción Secundaria</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Dependencias</th>
                  {(tipoEntidad === 'terceros' || tipoEntidad === 'usuarios') && (
                    <th className="px-4 py-2 text-left font-medium text-gray-600">Acciones</th>
                  )}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {reporte.length > 0 ? reporte.map(item => (
                  <tr key={item.id} className={item.dependencias.length > 0 ? 'bg-yellow-50' : ''}>
                    <td className="px-4 py-2"><input type="checkbox" checked={selection.has(item.id)} onChange={() => handleSelectionChange(item.id)} /></td>
                    <td className="px-4 py-2">{item.descripcion_principal}</td>
                    <td className="px-4 py-2 text-gray-500">{item.descripcion_secundaria}</td>
                    <td className="px-4 py-2">
                      {item.dependencias.length > 0
                        ? item.dependencias.map(dep => <span key={dep.tipo} className="inline-block bg-yellow-200 text-yellow-800 text-xs font-semibold mr-2 px-2.5 py-0.5 rounded-full">{dep.descripcion}</span>)
                        : <span className="text-green-600">Sin dependencias</span>
                      }
                    </td>
                    {(tipoEntidad === 'terceros' || tipoEntidad === 'usuarios') && (
                      <td className="px-4 py-2">
                        {item.email && (
                          <button
                            onClick={() => handleResetPassword(item.email)}
                            disabled={resetStatus.loading}
                            className="bg-gray-500 hover:bg-gray-600 text-white text-xs font-bold py-1 px-2 rounded-md disabled:bg-gray-300"
                          >
                            Resetear Contraseña
                          </button>
                        )}
                      </td>
                    )}
                  </tr>
                )) : (
                  <tr><td colSpan={(tipoEntidad === 'terceros' || tipoEntidad === 'usuarios') ? 5 : 4} className="text-center py-4">No se encontraron registros para esta entidad.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}