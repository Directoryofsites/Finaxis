// frontend/app/admin/utilidades/soporte-util/components/ErradicadorUniversal.js (FIX COMPLETO)
'use client';
import React, { useState, useCallback } from 'react';
import { FaBook } from 'react-icons/fa';
// CORRECCIÓN: Se usa la importación nombrada con llaves {}.
import { soporteApiService } from '@/lib/soporteApiService';
import Swal from 'sweetalert2';

const entidades = [
  // FIX CRÍTICO: Se añade la entidad de Inventario a la lista de opciones
  { value: 'inventario', label: 'Cartilla de Inventario y Movimientos' },
  { value: 'movimientos_documentos', label: 'Movimientos y Documentos' },
  { value: 'auditoria_papelera', label: 'Registros de la Papelera de Reciclaje' },
  { value: 'plantillas_documentos', label: 'Plantillas de Documentos' },
  { value: 'conceptos_favoritos', label: 'Conceptos Favoritos' },
  { value: 'terceros', label: 'Cartilla de Terceros' },
  { value: 'plan_cuentas', label: 'Cartilla de Plan de Cuentas' },
  { value: 'centros_costo', label: 'Cartilla de Centros de Costo' },
  { value: 'tipos_documento', label: 'Cartilla de Tipos de Documento' },
  { value: 'formatos_impresion', label: 'Formatos de Impresión' },
  // Se añade 'logs_operaciones' que fue añadida en el backend
  { value: 'logs_operaciones', label: 'Logs de Operaciones y Auditoría' }
];

export default function ErradicadorUniversal({ todasLasEmpresas }) {
  const [selectedEmpresaId, setSelectedEmpresaId] = useState('');
  const [entidadesSeleccionadas, setEntidadesSeleccionadas] = useState([]);
  const [confirmationText, setConfirmationText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleCheckboxChange = useCallback((e) => {
    const { value, checked } = e.target;
    setEntidadesSeleccionadas(prev =>
      checked ? [...prev, value] : prev.filter(item => item !== value)
    );
  }, []);

  const handleSelectAll = useCallback(() => {
    if (entidadesSeleccionadas.length === entidades.length) {
      setEntidadesSeleccionadas([]);
    } else {
      setEntidadesSeleccionadas(entidades.map(e => e.value));
    }
  }, [entidadesSeleccionadas.length]);

  const handleErradicar = useCallback(async () => {
    setMessage('');
    setError('');

    if (!selectedEmpresaId) {
      setError('Por favor, seleccione una empresa.');
      return;
    }
    if (entidadesSeleccionadas.length === 0) {
      setError('Por favor, seleccione al menos una entidad para erradicar.');
      return;
    }

    const empresa = todasLasEmpresas.find(e => e.id.toString() === selectedEmpresaId);
    const confirmPhrase = `ERRADICAR DATOS DE ${empresa?.razon_social}`;

    if (confirmationText !== confirmPhrase) {
      setError(`La frase de confirmación no coincide. Por favor, escriba "${confirmPhrase}" exactamente.`);
      return;
    }

    const swalResult = await Swal.fire({
      title: '¿Está absolutamente seguro?',
      html: `Esta acción es irreversible y eliminará los datos seleccionados (y sus dependencias) de la empresa <b>${empresa?.razon_social}</b>.`,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#d33',
      cancelButtonColor: '#3085d6',
      confirmButtonText: 'Sí, erradicar permanentemente',
      cancelButtonText: 'Cancelar'
    });

    if (!swalResult.isConfirmed) {
      setMessage('Operación de erradicación cancelada.');
      return;
    }

    setIsLoading(true);
    try {
      const payload = {
        empresa_id: parseInt(selectedEmpresaId, 10),
        entidades_a_erradicar: entidadesSeleccionadas,
        confirmacion: true,
      };

      const res = await soporteApiService.post('/utilidades/erradicar-universal', payload);

      setMessage(res.data.message);
      Swal.fire('¡Éxito!', `${res.data.message} Detalles: ${JSON.stringify(res.data.resumen)}`, 'success');

      setSelectedEmpresaId('');
      setEntidadesSeleccionadas([]);
      setConfirmationText('');

    } catch (err) {
      console.error("Error en ErradicadorUniversal:", err);
      const errorDetail = err.response?.data?.detail;

      const errMessage = typeof errorDetail === 'string'
        ? errorDetail
        : JSON.stringify(errorDetail, null, 2) || 'Ocurrió un error desconocido.';

      setError(errMessage);
      Swal.fire('Error', errMessage, 'error');

    } finally {
      setIsLoading(false);
    }
  }, [selectedEmpresaId, entidadesSeleccionadas, confirmationText, todasLasEmpresas]);

  const empresaSeleccionada = todasLasEmpresas.find(e => e.id.toString() === selectedEmpresaId);
  const confirmPhrase = empresaSeleccionada ? `ERRADICAR DATOS DE ${empresaSeleccionada.razon_social}` : '';

  return (
    <div className="bg-white p-6 rounded-lg shadow-xl border border-red-200">
      <div className="flex justify-between items-center mb-4 border-b pb-2">
        <h2 className="text-2xl font-bold text-red-700">Exterminador Universal de Datos</h2>
        <button
          onClick={() => window.open('/manual/capitulo_23_erradicador.html', '_blank')}
          className="text-red-600 hover:bg-red-50 px-3 py-1 rounded-md flex items-center gap-2 transition-colors"
          title="Ver Manual de Usuario"
        >
          <FaBook className="text-lg" /> <span className="font-bold text-sm">Manual</span>
        </button>
      </div>
      <p className="text-sm text-gray-600 mb-4">
        Esta herramienta eliminará permanentemente los datos seleccionados de una empresa. ¡Esta operación es irreversible!
      </p>

      <div className="mb-4">
        <label htmlFor="empresa-select" className="block text-sm font-medium text-gray-700">Seleccione la Empresa</label>
        <select
          id="empresa-select"
          value={selectedEmpresaId}
          onChange={(e) => {
            setSelectedEmpresaId(e.target.value);
            setEntidadesSeleccionadas([]);
            setConfirmationText('');
          }}
          className="mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm"
        >
          <option value="">-- Seleccionar Empresa --</option>
          {todasLasEmpresas.map(emp => (
            <option key={emp.id} value={emp.id}>{emp.razon_social}</option>
          ))}
        </select>
      </div>

      <div className="mb-4 bg-red-50 p-4 rounded-md border border-red-300">
        <h3 className="font-semibold text-red-800 mb-2">Entidades a Erradicar:</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {entidades.map(entidad => (
            <div key={entidad.value} className="flex items-center">
              <input
                id={`checkbox-${entidad.value}`}
                type="checkbox"
                value={entidad.value}
                checked={entidadesSeleccionadas.includes(entidad.value)}
                onChange={handleCheckboxChange}
                className="h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300 rounded"
              />
              <label htmlFor={`checkbox-${entidad.value}`} className="ml-2 text-sm text-gray-700">{entidad.label}</label>
            </div>
          ))}
        </div>
        <div className="mt-4">
          <button onClick={handleSelectAll} className="text-red-600 hover:text-red-800 font-medium text-sm underline">
            {entidadesSeleccionadas.length === entidades.length ? 'Deseleccionar todo' : 'Seleccionar todo'}
          </button>
        </div>
      </div>

      {selectedEmpresaId && (
        <div className="mb-4">
          <label htmlFor="confirmacion" className="block text-sm font-medium text-red-700">
            Confirme escribiendo: <code className="font-bold">{confirmPhrase}</code>
          </label>
          <input
            id="confirmacion"
            type="text"
            value={confirmationText}
            onChange={(e) => setConfirmationText(e.target.value)}
            className="mt-1 block w-full py-2 px-3 border border-red-400 rounded-md shadow-sm"
          />
        </div>
      )}

      <div className="mt-6">
        {error && <div className="p-3 mb-4 text-sm text-red-700 bg-red-100 rounded-lg"><pre>{error}</pre></div>}
        {message && <div className="p-3 mb-4 text-sm text-green-700 bg-green-100 rounded-lg">{message}</div>}
        <button
          onClick={handleErradicar}
          disabled={isLoading || !selectedEmpresaId || entidadesSeleccionadas.length === 0 || confirmationText !== confirmPhrase}
          className="w-full py-3 px-4 border border-transparent rounded-md shadow-sm text-lg font-medium text-white bg-red-600 hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Ejecutando erradicación...' : 'Ejecutar Erradicación Universal'}
        </button>
      </div>
    </div>
  );
}