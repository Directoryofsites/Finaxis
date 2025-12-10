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

export const updateReceta = async (id, recetaData) => {
    try {
        const response = await api.put(`/produccion/recetas/${id}`, recetaData);
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

// --- LIFECYCLE ---

export const anularOrden = async (id, motivo) => {
    try {
        const response = await api.post(`/produccion/ordenes/${id}/anular`, { motivo });
        return response.data;
    } catch (error) {
        throw error;
    }
};

export const archivarOrden = async (id, archivada) => {
    try {
        const response = await api.post(`/produccion/ordenes/${id}/archivar`, { archivada });
        return response.data;
    } catch (error) {
        throw error;
    }
};

export const deleteOrden = async (id) => {
    try {
        const response = await api.delete(`/produccion/ordenes/${id}`);
        return response.data;
    } catch (error) {
        throw error;
    }
};

export const deleteReceta = async (id) => {
    try {
        const response = await api.delete(`/produccion/recetas/${id}`);
        return response.data;
    } catch (error) {
        throw error;
    }
};

// --- CONFIGURACION ---

export const getConfigProduccion = async () => {
    try {
        const response = await api.get('/produccion/configuracion');
        return response.data;
    } catch (error) {
        throw error;
    }
};

export const saveConfigProduccion = async (config) => {
    try {
        const response = await api.post('/produccion/configuracion', config);
        return response.data;
    } catch (error) {
        throw error;
    }
};

export const downloadOrdenPDF = async (ordenId) => {
    try {
        const response = await api.get(`/produccion/ordenes/${ordenId}/pdf`, {
            responseType: 'blob'
        });
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `Orden_${ordenId}.pdf`);
        document.body.appendChild(link);
        link.click();
        link.remove();
    } catch (error) {
        throw error;
    }
};

export const downloadRecetaPDF = async (recetaId) => {
    try {
        const response = await api.get(`/produccion/recetas/${recetaId}/pdf`, {
            responseType: 'blob'
        });
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `Receta_${recetaId}.pdf`);
        document.body.appendChild(link);
        link.click();
        link.remove();
    } catch (error) {
        throw error;
    }
};
