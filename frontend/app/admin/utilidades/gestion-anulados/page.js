'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../../context/AuthContext';
import BotonRegresar from '../../../components/BotonRegresar';
import { apiService } from '../../../../lib/apiService';
import Swal from 'sweetalert2';

const formatCurrency = (value) => {
  if (value === null || value === undefined || isNaN(value)) return '$ 0';
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(value);
};

export default function GestionAnuladosPage() {
  const { user } = useAuth();
  const [documentosAnulados, setDocumentosAnulados] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDocumentosAnulados = useCallback(async () => {
    if (!user?.empresaId) return;
    setIsLoading(true);
    try {
      const response = await apiService.get('/documentos/anulados-para-gestion');
      setDocumentosAnulados(response.data || []);
      setError(null);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'No se pudieron cargar los documentos anulados.';
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  }, [user?.empresaId]);

  useEffect(() => {
    fetchDocumentosAnulados();
  }, [fetchDocumentosAnulados]);

  const handleReactivar = async (documentoId) => {
    Swal.fire({
      title: '¿Estás seguro?',
      text: "Esta acción reactivará el documento y sus movimientos contables.",
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#3085d6',
      cancelButtonColor: '#d33',
      confirmButtonText: 'Sí, reactivar',
      cancelButtonText: 'Cancelar'
    }).then(async (result) => {
      if (result.isConfirmed) {
        try {
          await apiService.put(`/documentos/${documentoId}/reactivar`);
          Swal.fire(
            '¡Reactivado!',
            'El documento ha sido reactivado exitosamente.',
            'success'
          );
          // Refrescar la lista para que el documento reactivado desaparezca de ella
          fetchDocumentosAnulados();
        } catch (err) {
          const errorMsg = err.response?.data?.detail || 'Ocurrió un error al reactivar el documento.';
          Swal.fire(
            'Error',
            errorMsg,
            'error'
          );
        }
      }
    });
  };

  const renderContent = () => {
    if (isLoading) {
      return <p className="text-center p-8 text-gray-500">Cargando documentos anulados...</p>;
    }

    if (error) {
      return <p className="text-center text-red-600 bg-red-100 p-4 rounded-md my-4">{error}</p>;
    }

    if (documentosAnulados.length === 0) {
      return <p className="text-center p-8 text-gray-500">No se encontraron documentos anulados.</p>;
    }

    return (
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-100">
            <tr>
              <th className="py-2 px-3 text-left font-semibold text-gray-600">Fecha</th>
              <th className="py-2 px-3 text-left font-semibold text-gray-600">Tipo Documento</th>
              <th className="py-2 px-3 text-left font-semibold text-gray-600">Número</th>
              <th className="py-2 px-3 text-left font-semibold text-gray-600">Beneficiario</th>
              <th className="py-2 px-3 text-right font-semibold text-gray-600">Total</th>
              <th className="py-2 px-3 text-center font-semibold text-gray-600">Acción</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {documentosAnulados.map((doc) => (
              <tr key={doc.id}>
                <td className="py-2 px-3 whitespace-nowrap">{new Date(doc.fecha + 'T00:00:00').toLocaleDateString('es-CO')}</td>
                <td className="py-2 px-3 whitespace-nowrap">{doc.tipo_documento}</td>
                <td className="py-2 px-3 whitespace-nowrap">{doc.numero}</td>
                <td className="py-2 px-3 whitespace-nowrap">{doc.beneficiario || 'N/A'}</td>
                <td className="py-2 px-3 whitespace-nowrap text-right">{formatCurrency(doc.total)}</td>
                <td className="py-2 px-3 whitespace-nowrap text-center">
                  <button
                    onClick={() => handleReactivar(doc.id)}
                    className="px-3 py-1 bg-green-600 text-white font-bold rounded-md shadow-sm hover:bg-green-700 disabled:bg-gray-400"
                  >
                    Reactivar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div className="container mx-auto p-4 md:p-8 bg-gray-50 min-h-screen">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-800">Gestión de Documentos Anulados</h1>
        <BotonRegresar />
      </div>
      <div className="bg-white p-4 md:p-6 rounded-lg shadow-md">
        {renderContent()}
      </div>
    </div>
  );
}