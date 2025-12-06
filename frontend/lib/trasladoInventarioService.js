// frontend/lib/trasladoInventarioService.js

import { apiService } from './apiService';

/**
 * Registra un traslado atómico de inventario entre dos bodegas.
 * @param {object} trasladoData - Payload con bodegas_origen_id, bodega_destino_id y items.
 */
export const createTraslado = async (trasladoData) => {
    try {
        const response = await apiService.post('/traslados-inventario', trasladoData);
        return response.data;
    } catch (error) {
        console.error("Error al crear traslado de inventario:", error);
        throw error;
    }
};

export default {
    createTraslado,
};