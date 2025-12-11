// frontend/lib/favoritosService.js

import { apiService } from './apiService'; // Asume que apiService está en la ruta correcta

/**
 * Obtiene los accesos rápidos definidos por el usuario actual.
 * @returns {Promise<Array>} Lista de objetos de favoritos.
 */
export const getFavoritos = async () => {
    try {
        // Llama al endpoint GET /api/favoritos/
        const response = await apiService.get('/favoritos/');
        return response.data;
    } catch (error) {
        console.error('Error al obtener los favoritos:', error);
        // Si no hay favoritos o hay un error, devuelve un array vacío para no romper la UI
        return []; 
    }
};

/**
 * Crea un nuevo acceso rápido.
 * @param {object} data - { ruta_enlace, nombre_personalizado, orden (1-24) }
 */
export const createFavorito = async (data) => {
    // Llama al endpoint POST /api/favoritos/
    const response = await apiService.post('/favoritos/', data);
    return response.data;
};

/**
 * Actualiza un acceso rápido existente.
 * @param {number} id - ID del favorito a actualizar.
 * @param {object} data - { ruta_enlace?, nombre_personalizado?, orden? }
 */
export const updateFavorito = async (id, data) => {
    // Llama al endpoint PUT /api/favoritos/{id}
    const response = await apiService.put(`/favoritos/${id}`, data);
    return response.data;
};

/**
 * Elimina un acceso rápido.
 * @param {number} id - ID del favorito a eliminar.
 */
export const deleteFavorito = async (id) => {
    // Llama al endpoint DELETE /api/favoritos/{id}
    await apiService.delete(`/favoritos/${id}`);
    return true;
};