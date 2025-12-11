'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../../context/AuthContext';
import BotonRegresar from '../../../components/BotonRegresar';
import { apiService } from '../../../../lib/apiService';
import { FaBook } from 'react-icons/fa';

const formatCurrency = (value) => {
  if (value === null || value === undefined || isNaN(value)) return '$ 0';
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(value);
};

const formatDateTime = (dateString) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleString('es-CO');
};

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  // La opción timeZone: 'UTC' previene errores de un día por la conversión de zona horaria
  return new Date(dateString).toLocaleDateString('es-CO', { timeZone: 'UTC' });
};

export default function AuditoriaConsecutivosPage() {
  const { user } = useAuth();
  const [tiposDocumento, setTiposDocumento] = useState([]);
  const [selectedTipoDoc, setSelectedTipoDoc] = useState('');
  const [auditResult, setAuditResult] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuditing, setIsAuditing] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchTiposDocumento = async () => {
      if (!user?.empresaId) return;
      try {
        const response = await apiService.get('/tipos-documento/');
        setTiposDocumento(response.data || []);
      } catch (err) {
        setError('No se pudieron cargar los tipos de documento.');
      } finally {
        setIsLoading(false);
      }
    };
    fetchTiposDocumento();
  }, [user?.empresaId]);

  const handleAudit = async () => {
    if (!selectedTipoDoc) {
      setError('Por favor, selecciona un tipo de documento para auditar.');
      return;
    }
    setIsAuditing(true);
    setError(null);
    setAuditResult(null);
    try {
      const response = await apiService.get(`/auditoria/consecutivos/${selectedTipoDoc}`);
      setAuditResult(response.data);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Ocurrió un error al realizar la auditoría.';
      setError(errorMsg);
    } finally {
      setIsAuditing(false);
    }
  };

  const getRowClass = (estado) => {
    switch (estado) {
      case 'ANULADO':
        return 'bg-green-50';
      case 'ELIMINADO':
        return 'bg-red-50';
      case 'HUECO':
        return 'bg-yellow-100 font-bold';
      default:
        return 'bg-white';
    }
  };

  const renderAuditTable = () => {
    if (!auditResult) return null;

    return (
      <div className="mt-8">
        <h2 className="text-xl font-bold text-gray-800 mb-4">
          Resultado de la Auditoría: {auditResult.tipo_documento_nombre}
        </h2>
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
                {/* --- INICIO DE LA MEJORA --- */}
                <th className="py-2 px-3 text-left font-semibold text-gray-600">Fecha Creación (Registro)</th>
                <th className="py-2 px-3 text-left font-semibold text-gray-600">Fecha Documento</th>
                {/* --- FIN DE LA MEJORA --- */}
                <th className="py-2 px-3 text-left font-semibold text-gray-600">Beneficiario</th>
                <th className="py-2 px-3 text-right font-semibold text-gray-600">Valor</th>
                <th className="py-2 px-3 text-left font-semibold text-gray-600">Usuario</th>
                <th className="py-2 px-3 text-left font-semibold text-gray-600">Justificación</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {auditResult.resultados.map((row, index) => (
                <tr key={index} className={getRowClass(row.estado)}>
                  {row.estado === 'HUECO' ? (
                    <td colSpan="8" className="py-2 px-3 text-center">
                      ¡ALERTA DE AUDITORÍA! Faltan {row.cantidad_faltante} consecutivos desde el #{row.numero_faltante_inicio} hasta el #{row.numero_faltante_fin}
                    </td>
                  ) : (
                    <>
                      <td className="py-2 px-3 font-mono">{row.numero}</td>
                      <td className="py-2 px-3">{row.estado}</td>
                      {/* --- INICIO DE LA CORRECCIÓN DEL BUG --- */}
                      <td className="py-2 px-3">{formatDateTime(row.fecha_operacion)}</td>
                      <td className="py-2 px-3">{formatDate(row.fecha_documento)}</td>
                      {/* --- FIN DE LA CORRECCIÓN DEL BUG --- */}
                      <td className="py-2 px-3">{row.beneficiario_nombre || 'N/A'}</td>
                      <td className="py-2 px-3 text-right">{formatCurrency(row.total_documento)}</td>
                      <td className="py-2 px-3">{row.usuario_operacion || 'N/A'}</td>
                      <td className="py-2 px-3">{row.razon_operacion || ''}</td>
                    </>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  return (
    <div className="container mx-auto p-4 md:p-8 bg-gray-50 min-h-screen">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-800">Auditoría de Consecutivos</h1>
        <div className="flex gap-2">
          <BotonRegresar />
          <button
            onClick={() => window.open('/manual/capitulo_8_auditoria.html', '_blank')}
            className="btn btn-ghost text-indigo-600 hover:bg-indigo-50 gap-2 flex items-center"
            title="Ver Manual de Usuario"
          >
            <FaBook className="text-lg" /> <span className="font-bold hidden md:inline">Manual</span>
          </button>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md">
        <div className="flex items-end gap-4">
          <div className="flex-grow">
            <label htmlFor="tipoDoc" className="block text-sm font-medium text-gray-700">
              Tipo de Documento a Auditar
            </label>
            <select
              id="tipoDoc"
              value={selectedTipoDoc}
              onChange={(e) => setSelectedTipoDoc(e.target.value)}
              className="mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm"
              disabled={isLoading || isAuditing}
            >
              <option value="">-- Selecciona un tipo de documento --</option>
              {tiposDocumento.map(td => <option key={td.id} value={td.id}>{td.nombre}</option>)}
            </select>
          </div>
          <button
            onClick={handleAudit}
            disabled={isAuditing || !selectedTipoDoc}
            className="px-6 py-2 bg-blue-600 text-white font-bold rounded-lg shadow-md hover:bg-blue-700 disabled:bg-gray-400"
          >
            {isAuditing ? 'Auditando...' : 'Auditar'}
          </button>
        </div>
        {error && <p className="text-red-600 mt-4">{error}</p>}
      </div>

      {renderAuditTable()}

    </div>
  );
}