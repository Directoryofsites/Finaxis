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

    getPropietarios: async () => {
        const response = await apiService.get('/ph/unidades/propietarios');
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

    // --- MÓDULOS (PH MIXTA) ---
    getModulos: async () => {
        const response = await apiService.get('/ph/modulos');
        return response.data;
    },

    createModulo: async (data) => {
        const response = await apiService.post('/ph/modulos', data);
        return response.data;
    },

    updateModulo: async (id, data) => {
        const response = await apiService.put(`/ph/modulos/${id}`, data);
        return response.data;
    },

    deleteModulo: async (id) => {
        const response = await apiService.delete(`/ph/modulos/${id}`);
        return response.data;
    },

    // --- FACTURACION ---
    checkFacturacionMasiva: async (fecha) => {
        // fecha: YYYY-MM-DD
        const response = await apiService.get('/ph/facturacion/masiva/check', { params: { fecha } });
        return response.data;
    },

    generarFacturacionMasiva: async (fecha, conceptosIds = []) => {
        const response = await apiService.post('/ph/facturacion/masiva', { fecha, conceptos_ids: conceptosIds });
        return response.data;
    },

    getHistorialFacturacion: async () => {
        const response = await apiService.get('/ph/facturacion/historial');
        return response.data;
    },

    deleteFacturacionMasiva: async (periodo) => {
        const response = await apiService.delete(`/ph/facturacion/masiva/${periodo}`);
        return response.data;
    },

    getDetalleFacturacion: async (periodo) => {
        const response = await apiService.get(`/ph/facturacion/detalle/${periodo}`);
        return response.data;
    },

    getPDFDetalleFacturacion: async (periodo) => {
        const response = await apiService.get(`/ph/facturacion/detalle/${periodo}/pdf`, {
            responseType: 'blob'
        });
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
    getHistorialCuenta: async (unidadId, params = {}) => {
        // params: { fecha_inicio, fecha_fin }
        const response = await apiService.get(`/ph/pagos/historial/${unidadId}`, { params });
        return response.data;
    },

    getEstadoCuentaPropietario: async (propietarioId) => {
        const response = await apiService.get(`/ph/pagos/estado-cuenta-propietario/${propietarioId}`);
        return response.data;
    },

    getHistorialCuentaPropietarioDetailed: async (propietarioId, params = {}) => {
        const response = await apiService.get(`/ph/pagos/historial-propietario/${propietarioId}`, { params });
        return response.data;
    },



    getCarteraPendiente: async (params) => {
        // params: { unidad_id, propietario_id }
        const response = await apiService.get('/ph/pagos/cartera-pendiente', { params });
        return response.data;
    },

    // --- REPORTES ---
    getReporteMovimientos: async (params) => {
        const response = await apiService.post('/ph/reportes/movimientos', null, { params });
        return response.data;
    },

    // --- UTILIDADES ---
    getTiposDocumento: async () => {
        const response = await apiService.get('/tipos-documento/');
        return response.data;
    }
};
