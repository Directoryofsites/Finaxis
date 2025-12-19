import { apiService } from './apiService';

export const getEmpleados = async (params = {}) => {
    try {
        const response = await apiService.get('/nomina/empleados', { params });
        return response.data;
    } catch (error) {
        throw error;
    }
};

export const createEmpleado = async (empleadoData) => {
    try {
        const response = await apiService.post('/nomina/empleados', empleadoData);
        return response.data;
    } catch (error) {
        throw error;
    }
};

export const updateEmpleado = async (id, empleadoData) => {
    try {
        const response = await apiService.put(`/nomina/empleados/${id}`, empleadoData);
        return response.data;
    } catch (error) {
        throw error;
    }
};

export const previewLiquidacion = async (empleadoId, diasTrabajados, horasExtras = 0, comisiones = 0) => {
    try {
        const payload = {
            empleado_id: empleadoId,
            dias_trabajados: diasTrabajados,
            horas_extras: horasExtras,
            comisiones: comisiones
        };
        const response = await apiService.post('/nomina/liquidar-preview', payload);
        return response.data;
    } catch (error) {
        throw error;
    }
};

export const guardarLiquidacion = async (liquidacionData) => {
    // liquidacionData: { empleado_id, anio, mes, dias, extras, comisiones }
    try {
        const response = await apiService.post('/nomina/liquidar/guardar', liquidacionData);
        return response.data;
    } catch (error) {
        throw error;
    }
};

export const getConfig = async (params = {}) => {
    try {
        const response = await apiService.get('/nomina/configuracion', { params });
        return response.data;
    } catch (error) {
        throw error;
    }
};

export const saveConfig = async (config) => {
    try {
        const response = await apiService.post('/nomina/configuracion', config);
        return response.data;
    } catch (error) {
        throw error;
    }
};

export const getHistorial = async (params = {}) => {
    try {
        const response = await apiService.get('/nomina/historial', { params });
        return response.data;
    } catch (error) {
        throw error;
    }
};

export const deleteDesprendible = async (id) => {
    try {
        const response = await apiService.delete(`/nomina/desprendibles/${id}`);
        return response.data;
    } catch (error) {
        throw error;
    }
};

export const downloadDesprendible = async (id, filename) => {
    try {
        const response = await apiService.get(`/nomina/desprendibles/${id}/pdf`, { responseType: 'blob' });

        // Crear Blob y Descargar
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', filename || `desprendible_${id}.pdf`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        return true;
    } catch (error) {
        throw error;
    }
};

export const downloadResumenNomina = async (anio, mes, tipoNominaId, filename) => {
    try {
        const params = { anio, mes };
        if (tipoNominaId) params.tipo_nomina_id = tipoNominaId;

        const response = await apiService.get('/nomina/resumen-pdf', {
            params,
            responseType: 'blob'
        });

        // Crear Blob y Descargar
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', filename || `Resumen_Nomina_${anio}_${mes}.pdf`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        return true;
    } catch (error) {
        throw error;
    }
};


// --- TIPOS DE NOMINA ---

export const getTiposNomina = async () => {
    try {
        const response = await apiService.get('/nomina/tipos');
        return response.data;
    } catch (error) {
        throw error;
    }
};

export const createTipoNomina = async (tipoData) => {
    try {
        const response = await apiService.post('/nomina/tipos', tipoData);
        return response.data;
    } catch (error) {
        throw error;
    }
};

export const updateTipoNomina = async (id, tipoData) => {
    try {
        const response = await apiService.put(`/nomina/tipos/${id}`, tipoData);
        return response.data;
    } catch (error) {
        throw error;
    }
};


export const downloadEmpleadosPdf = async (tipoNominaId, filename) => {
    try {
        const params = {};
        if (tipoNominaId) params.tipo_nomina_id = tipoNominaId;

        const response = await apiService.get('/nomina/empleados/pdf', {
            params,
            responseType: 'blob'
        });

        // Crear Blob y Descargar
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', filename || `Empleados_Listado.pdf`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        return true;
    } catch (error) {
        throw error;
    }
};

export const deleteTipoNomina = async (id) => {
    try {
        const response = await apiService.delete(`/nomina/tipos/${id}`);
        return response.data;
    } catch (error) {
        throw error;
    }
};
