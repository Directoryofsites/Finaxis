// frontend/lib/terceroService.js (Versión con FIX de retorno)

import { apiService } from './apiService'; // Asumiendo que apiService está en la misma carpeta o ruta correcta

/**
 * Obtiene la lista paginada o completa de terceros.
 * @param {object} params - Opcional: { filtro, skip, limit }
 */
const getTerceros = async (params = {}) => {
    try {
        // Construir query string si hay parámetros
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `/terceros/?${queryString}` : '/terceros/';
        const response = await apiService.get(url);
        // CRÍTICO: Devolver la respuesta completa para que page.js pueda acceder a .data
        return response.data; 
    } catch (error) {
        console.error('Error al obtener los terceros:', error);
        throw error; // Re-lanzar para que el componente maneje
    }
};

// --- INICIO NUEVA FUNCIÓN ---
/**
 * Obtiene los detalles completos de un tercero específico por su ID.
 * @param {number} id - El ID del tercero a buscar.
 * @returns {Promise<object>} Los datos completos del tercero.
 */
const getTerceroById = async (id) => {
    if (!id) {
        console.error("getTerceroById requiere un ID.");
        throw new Error("ID de tercero no proporcionado.");
    }
    try {
        // La ruta en el backend es /terceros/{tercero_id}
        const response = await apiService.get(`/terceros/${id}`);
        return response.data; // Devuelve el objeto completo del tercero
    } catch (error) {
        console.error(`Error al obtener el tercero con ID ${id}:`, error);
        // Si el backend devuelve 404, el error se propagará
        throw error; // Re-lanzar para que el componente maneje
    }
};
// --- FIN NUEVA FUNCIÓN ---


// Si en el futuro necesitas más funciones para terceros, las puedes añadir aquí como constantes exportadas.
// Ejemplo:
/*
const createTercero = async (terceroData) => {
    try {
        const response = await apiService.post('/terceros/', terceroData);
        return response.data;
    } catch (error) {
        console.error('Error al crear tercero:', error);
        throw error;
    }
};
*/

// Cambiamos a exportaciones nombradas para mayor claridad y evitar errores 'default'
export {
    getTerceros,
    getTerceroById
    // , createTercero // Exportar otras funciones si se añaden
};

// Eliminamos el export default
// export default terceroService;