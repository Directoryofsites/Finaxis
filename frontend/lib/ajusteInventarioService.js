// frontend/lib/ajusteInventarioService.js (Corrected Version)

// Change the import to use curly braces { }
import { apiService } from './apiService';

export const procesarAjusteInventario = async (ajusteData) => {
  try {
    const response = await apiService.post('/ajuste-inventario/', ajusteData);
    return response.data;
  } catch (error) {
    console.error('Error al procesar el ajuste de inventario:', error);
    throw error.response?.data || { detail: 'Error de red o del servidor.' };
  }
};