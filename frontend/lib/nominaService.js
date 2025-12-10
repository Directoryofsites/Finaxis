import { apiService } from './apiService';

export const getEmpleados = async () => {
    try {
        const response = await apiService.get('/nomina/empleados');
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

export const getConfig = async () => {
    try {
        const response = await apiService.get('/nomina/configuracion');
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

export const getHistorial = async () => {
    try {
        const response = await apiService.get('/nomina/historial');
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
