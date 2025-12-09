import { apiService } from './apiService';

export const phService = {
    // --- UNIDADES ---
    getUnidades: async (params = {}) => {
        const response = await apiService.get('/ph/unidades', { params });
        return response.data;
    },

    getUnidadById: async (id) => {
        const response = await apiService.get(`/ph/unidades/${id}`);
        return response.data;
    },

    createUnidad: async (data) => {
        const response = await apiService.post('/ph/unidades', data);
        return response.data;
    },

    updateUnidad: async (id, data) => {
        const response = await apiService.put(`/ph/unidades/${id}`, data);
        return response.data;
    },

    deleteUnidad: async (id) => {
        const response = await apiService.delete(`/ph/unidades/${id}`);
        return response.data;
    },

    // --- CONFIGURACION ---
    getConfiguracion: async () => {
        const response = await apiService.get('/ph/configuracion');
        return response.data;
    },

    updateConfiguracion: async (data) => {
        const response = await apiService.put('/ph/configuracion', data);
        return response.data;
    },

    // --- CONCEPTOS ---
    getConceptos: async () => {
        const response = await apiService.get('/ph/conceptos');
        return response.data;
    },

    createConcepto: async (data) => {
        const response = await apiService.post('/ph/conceptos', data);
        return response.data;
    },

    updateConcepto: async (id, data) => {
        const response = await apiService.put(`/ph/conceptos/${id}`, data);
        return response.data;
    },

    deleteConcepto: async (id) => {
        const response = await apiService.delete(`/ph/conceptos/${id}`);
        return response.data;
    },

    // --- FACTURACION ---
    generarFacturacionMasiva: async (fecha, conceptosIds = []) => {
        const response = await apiService.post('/ph/facturacion/masiva', { fecha, conceptos_ids: conceptosIds });
        return response.data;
    },

    // --- PAGOS ---
    getEstadoCuenta: async (unidadId) => {
        const response = await apiService.get(`/ph/pagos/estado-cuenta/${unidadId}`);
        return response.data;
    },
    registrarPago: async (pagoData) => {
        const response = await apiService.post('/ph/pagos/registrar', pagoData);
        return response.data;
    },
    getHistorialCuenta: async (unidadId) => {
        const response = await apiService.get(`/ph/pagos/historial/${unidadId}`);
        return response.data;
    },

    // --- UTILIDADES ---
    getTiposDocumento: async () => {
        const response = await apiService.get('/tipos-documento/');
        return response.data;
    }
};
