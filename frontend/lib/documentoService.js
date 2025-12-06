// frontend/lib/documentoService.js
import { apiService } from './apiService';

/**
 * Obtiene los detalles completos de un documento específico por su ID.
 * @param {number} id - El ID del documento a consultar.
 * @returns {Promise<object>} Los detalles del documento.
 */
export const getDocumentoById = async (id) => {
  try {
    const response = await apiService.get(`/documentos/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error al obtener el documento con ID ${id}:`, error);
    throw error;
  }
};

// --- INICIO: NUEVA FUNCIÓN PARA PDF DE RENTABILIDAD ---
/**
 * Solicita al backend una URL firmada y temporal para imprimir el reporte de rentabilidad de una factura.
 * @param {number} documentoId - El ID de la factura.
 * @returns {Promise<object>} Una promesa que resuelve a un objeto con la URL firmada, ej: { signed_url: '...' }.
 */
export const solicitarUrlImpresionRentabilidad = async (documentoId) => {
  try {
    // Hacemos una petición POST al nuevo endpoint que creamos en el backend.
    const response = await apiService.post(`/documentos/${documentoId}/solicitar-impresion-rentabilidad`);
    return response.data;
  } catch (error) {
    console.error(`Error al solicitar la URL de impresión de rentabilidad para el documento ${documentoId}:`, error);
    throw error;
  }
};
// --- FIN: NUEVA FUNCIÓN ---