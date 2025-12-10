import { apiService as api } from './apiService';

// --- RECETAS ---

export const getRecetas = async () => {
    try {
        const response = await api.get('/produccion/recetas');
        return response.data;
    } catch (error) {
        throw error;
    }
};

export const getRecetaById = async (id) => {
    try {
        const response = await api.get(`/produccion/recetas/${id}`);
        return response.data;
    } catch (error) {
        throw error;
    }
};

export const createReceta = async (recetaData) => {
    try {
        const response = await api.post('/produccion/recetas', recetaData);
        return response.data;
    } catch (error) {
        throw error;
    }
};

// --- ORDENES DE PRODUCCION ---

export const getOrdenes = async () => {
    try {
        const response = await api.get('/produccion/ordenes');
        return response.data;
    } catch (error) {
        throw error;
    }
};

export const getOrdenById = async (id) => {
    try {
        const response = await api.get(`/produccion/ordenes/${id}`);
        return response.data;
    } catch (error) {
        throw error;
    }
};

export const createOrden = async (ordenData) => {
    try {
        const response = await api.post('/produccion/ordenes', ordenData);
        return response.data;
    } catch (error) {
        throw error;
    }
};

// --- ACCIONES ---

export const registrarConsumo = async (ordenId, items, bodegaOrigenId) => {
    try {
        const payload = items; // El backend espera Lista[RecetaDetalleCreate] en el body
        const response = await api.post(`/produccion/ordenes/${ordenId}/consumo`, payload, {
            params: { bodega_origen_id: bodegaOrigenId }
        });
        return response.data;
    } catch (error) {
        throw error;
    }
};

export const cerrarOrden = async (ordenId, cantidadReal) => {
    try {
        const response = await api.post(`/produccion/ordenes/${ordenId}/cierre`, {}, {
            params: { cantidad_real: cantidadReal }
        });
        return response.data;
    } catch (error) {
        throw error;
    }
};
