// frontend/lib/productosService.js (Versión COMPLETA y sin omisiones)

import { apiService } from './apiService';

export const getProductosByEmpresa = async () => {
  try {
    const response = await apiService.get('/inventario/productos/list-flat');
    return { productos: response.data }; // Wrap in object to match expected structure if needed, or check page usage
  } catch (error) {
    console.error('Error al obtener los productos:', error);
    throw error.response?.data || { detail: 'Error de red o del servidor.' };
  }
};

/**
 * Llama al nuevo endpoint de búsqueda avanzada de productos.
 * @param {object} filtros - El objeto con los filtros (bodega_ids, grupo_id, search_term).
 */
export const buscarProductos = async (filtros) => {
  try {
    const response = await apiService.post('/inventario/productos/buscar', filtros);
    return response.data;
  } catch (error) {
    console.error('Error al buscar productos:', error);
    throw error.response?.data || { detail: 'Error de red o del servidor.' };
  }
};