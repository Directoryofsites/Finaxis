// frontend/lib/centrosCostoService.js (Versión CORREGIDA para apuntar a /get-flat)

import { apiService } from './apiService';

/**
 * Obtiene una lista plana (no jerárquica) de todos los centros de costo.
 * --- CORRECCIÓN: Esta función ahora apunta al endpoint /get-flat ---
 */
export const getCentrosCosto = async () => { // Mantenemos el nombre getCentrosCosto para compatibilidad con page.js
  try {
    // --- CORRECCIÓN: Apuntar al endpoint correcto ---
    const response = await apiService.get('/centros-costo/get-flat');
    return response.data;
  } catch (error) {
    console.error('Error al obtener los centros de costo (flat):', error);
    throw error;
  }
};

/**
 * (Opcional) Si en el futuro necesitas la lista jerárquica (árbol),
 * deberás crear un endpoint GET / en el backend y una función aquí para llamarlo.
 */
// export const getCentrosCostoTree = async () => { ... }


// --- Otras funciones CRUD (Añadir si son necesarias) ---
/*
export const createCentroCosto = async (data) => {
    try {
        const response = await apiService.post('/centros-costo/', data);
        return response.data;
    } catch (error) {
        console.error('Error al crear centro de costo:', error);
        throw error;
    }
};
// ... update, delete, etc.
*/