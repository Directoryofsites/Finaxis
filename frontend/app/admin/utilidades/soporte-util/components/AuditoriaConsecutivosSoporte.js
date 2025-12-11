'use client';

import React, { useState, useEffect } from 'react';
import { FaBook } from 'react-icons/fa';
// 1. CORRECCIÓN CLAVE: Se usa la importación nombrada con llaves {}.
import { soporteApiService } from '../../../../../lib/soporteApiService';

// (Las funciones de formato no cambian, las mantenemos por consistencia)
const formatDateTime = (dateString) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleString('es-CO');
};

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleDateString('es-CO', { timeZone: 'UTC' });
};

const formatCurrency = (value) => {
  if (value === null || value === undefined || isNaN(value)) return '$ 0';
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(value);
};

const getRowClass = (estado) => {
  if (estado === 'HUECO') return 'bg-yellow-100 font-bold';
  return '';
};

export default function AuditoriaConsecutivosSoporte({ todasLasEmpresas }) {
  const [selectedEmpresa, setSelectedEmpresa] = useState('');
  const [tiposDocumento, setTiposDocumento] = useState([]);
  const [selectedTipoDoc, setSelectedTipoDoc] = useState('');

  const [auditResult, setAuditResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isAuditing, setIsAuditing] = useState(false);
  const [error, setError] = useState(null);

  // Efecto para cargar los tipos de documento cuando se elige una empresa
  useEffect(() => {
    const fetchTiposDocumento = async () => {
      if (!selectedEmpresa) {
        setTiposDocumento([]);
        setSelectedTipoDoc('');
        setAuditResult(null);
        return;
      }
      setIsLoading(true);
      setError(null);
      setAuditResult(null);
      try {
        const response = await soporteApiService.post('/utilidades/tipos-documento-por-empresa', { empresaId: selectedEmpresa });
        setTiposDocumento(response.data || []);
      } catch (err) {
        setError('No se pudieron cargar los tipos de documento para la empresa seleccionada.');
        setTiposDocumento([]);
      } finally {
        setIsLoading(false);
      }
    };
    fetchTiposDocumento();
  }, [selectedEmpresa]);

  // Función que se ejecuta al presionar el botón de auditar
  const handleAudit = async () => {
    if (!selectedTipoDoc) {
      setError('Por favor, selecciona un tipo de documento para auditar.');
      return;
    }
    setIsAuditing(true);
    setError(null);
    setAuditResult(null);
    try {
      const response = await soporteApiService.get(`/utilidades/auditoria/consecutivos/${selectedEmpresa}/${selectedTipoDoc}`);
      setAuditResult(response.data);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Ocurrió un error al realizar la auditoría.';
      setError(errorMsg);
    } finally {
      setIsAuditing(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-xl border border-gray-200">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold text-gray-800">Auditoría Detallada de Consecutivos (Soporte)</h2>
        <button
          onClick={() => window.open('/manual/capitulo_17_auditoria_soporte.html', '_blank')}
          className="text-indigo-600 hover:bg-indigo-50 px-3 py-1 rounded-md flex items-center gap-2 transition-colors"
          title="Ver Manual de Usuario"
        >
          <FaBook className="text-lg" /> <span className="font-bold text-sm">Manual</span>
        </button>
      </div>

      <div className="flex flex-col md:flex-row items-end gap-4 mb-6">
        <div className="flex-grow w-full">
          <label htmlFor="empresa" className="block text-sm font-medium text-gray-700">1. Seleccionar Empresa</label>
          <select
            id="empresa"
            value={selectedEmpresa}
            onChange={(e) => setSelectedEmpresa(e.target.value)}
            className="mt-1 block w-full py-2 px-3 border border-gray-300 rounded-md"
          >
            <option value="">-- Seleccione una empresa --</option>
            {todasLasEmpresas.map(emp => <option key={emp.id} value={emp.id}>{emp.razon_social}</option>)}
          </select>
        </div>
        <div className="flex-grow w-full">
          <label htmlFor="tipoDoc" className="block text-sm font-medium text-gray-700">2. Seleccionar Documento</label>
          <select
            id="tipoDoc"
            value={selectedTipoDoc}
            onChange={(e) => setSelectedTipoDoc(e.target.value)}
            className="mt-1 block w-full py-2 px-3 border border-gray-300 rounded-md"
            disabled={!selectedEmpresa || isLoading}
          >
            <option value="">-- Seleccione un documento --</option>
            {tiposDocumento.map(td => <option key={td.id} value={td.id}>{td.nombre}</option>)}
          </select>
        </div>
        <button
          onClick={handleAudit}
          disabled={isAuditing || !selectedTipoDoc}
          className="px-6 py-2 bg-blue-600 text-white font-bold rounded-lg shadow-md hover:bg-blue-700 disabled:bg-gray-400 w-full md:w-auto"
        >
          {isAuditing ? 'Auditando...' : 'Auditar'}
        </button>
      </div>

      {error && <p className="text-red-600 my-4 p-4 bg-red-100 rounded-md">{error}</p>}
      {isLoading && <p>Cargando tipos de documento...</p>}

      {auditResult && (
        <div className="mt-8">
          <h3 className="text-xl font-bold text-gray-800 mb-4">
            Resultado de la Auditoría: {auditResult.tipo_documento_nombre}
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 text-sm bg-gray-100 p-4 rounded-md">
            <div><span className="font-semibold">Último Consecutivo:</span> {auditResult.ultimo_consecutivo_registrado}</div>
            <div><span className="font-semibold">Documentos Encontrados:</span> {auditResult.total_documentos_encontrados}</div>
            <div className="text-red-600"><span className="font-semibold">Huecos Detectados:</span> {auditResult.total_huecos_encontrados}</div>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-200">
                <tr>
                  <th className="py-2 px-3 text-left font-semibold text-gray-600">Número</th>
                  <th className="py-2 px-3 text-left font-semibold text-gray-600">Estado</th>
                  <th className="py-2 px-3 text-left font-semibold text-gray-600">Fecha Creación</th>
                  <th className="py-2 px-3 text-left font-semibold text-gray-600">Fecha Documento</th>
                  <th className="py-2 px-3 text-left font-semibold text-gray-600">Beneficiario</th>
                  <th className="py-2 px-3 text-right font-semibold text-gray-600">Valor</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {auditResult.resultados.map((row, index) => (
                  <tr key={index} className={getRowClass(row.estado)}>
                    {row.estado === 'HUECO' ? (
                      <td colSpan="6" className="py-2 px-3 text-center">
                        ¡ALERTA! Faltan {row.cantidad_faltante} consecutivos desde el #{row.numero_faltante_inicio} hasta el #{row.numero_faltante_fin}
                      </td>
                    ) : (
                      <>
                        <td className="py-2 px-3 font-mono">{row.numero}</td>
                        <td className="py-2 px-3">{row.estado}</td>
                        <td className="py-2 px-3">{formatDateTime(row.fecha_operacion)}</td>
                        <td className="py-2 px-3">{formatDate(row.fecha_documento)}</td>
                        <td className="py-2 px-3">{row.beneficiario_nombre || 'N/A'}</td>
                        <td className="py-2 px-3 text-right">{formatCurrency(row.total_documento)}</td>
                      </>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}