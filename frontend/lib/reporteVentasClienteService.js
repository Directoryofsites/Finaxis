import { apiService } from './apiService';

const API_URL = '/reportes-facturacion'; // Reusamos el prefijo base del router

export const getAnalisisVentasCliente = async (filtros) => {
    try {
        const response = await apiService.post(`${API_URL}/ventas-cliente`, filtros);
        return response.data;
    } catch (error) {
        throw error;
    }
};

export const generarPdfVentasCliente = async (filtros) => {
    try {
        const response = await apiService.post(`${API_URL}/ventas-cliente/pdf`, filtros, {
            responseType: 'blob'
        });
        return response.data;
    } catch (error) {
        throw error;
    }
};
