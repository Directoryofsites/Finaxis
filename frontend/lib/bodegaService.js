// frontend/lib/bodegaService.js (Versión refactorizada con Exportaciones Nombradas)

import { apiService } from './apiService';

/**
 * Obtiene todas las bodegas de la empresa actual desde el backend.
 */
export const getBodegas = async () => {
  try {
    const response = await apiService.get('/bodegas/');
    return response.data;
  } catch (error) {
    console.error('Error al obtener las bodegas:', error);
    throw error;
  }
};

// Puedes añadir más funciones exportadas aquí en el futuro, ej:
/*
export const getBodegaById = async (id) => {
  try {
    const response = await apiService.get(`/bodegas/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error al obtener la bodega ${id}:`, error);
    throw error;
  }
};
*/