// frontend/lib/listaPrecioService.js

import { apiService } from './apiService'; // Asume que apiService está en la misma carpeta o ruta correcta

/**
 * Obtiene todas las listas de precios para la empresa actual.
 */
export const getListasPrecio = async () => {
  try {
    const response = await apiService.get('/listas-precio/'); // Ajusta la ruta si es diferente
    return response.data;
  } catch (error) {
    console.error("Error fetching listas de precio:", error);
    throw error; // Re-lanzar para que el componente pueda manejarlo
  }
};

/**
 * Crea una nueva lista de precios.
 * @param {object} listaData - Datos de la lista a crear (ej: { nombre: 'Nueva Lista' })
 */
export const createListaPrecio = async (listaData) => {
    try {
        const response = await apiService.post('/listas-precio/', listaData);
        return response.data;
    } catch (error) {
        console.error("Error creating lista de precio:", error);
        throw error;
    }
};

/**
 * Actualiza una lista de precios existente.
 * @param {number} id - ID de la lista a actualizar.
 * @param {object} listaData - Datos a actualizar (ej: { nombre: 'Nombre Actualizado' })
 */
export const updateListaPrecio = async (id, listaData) => {
    try {
        const response = await apiService.put(`/listas-precio/${id}`, listaData);
        return response.data;
    } catch (error) {
        console.error(`Error updating lista de precio ${id}:`, error);
        throw error;
    }
};

/**
 * Elimina una lista de precios.
 * @param {number} id - ID de la lista a eliminar.
 */
export const deleteListaPrecio = async (id) => {
    try {
        await apiService.delete(`/listas-precio/${id}`);
    } catch (error) {
        console.error(`Error deleting lista de precio ${id}:`, error);
        throw error;
    }
};