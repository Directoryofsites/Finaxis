// frontend/lib/dashboardService.js

import { apiService } from './apiService'; 

/**
 * Obtiene los 12 KPIs financieros reales del Dashboard.
 * @returns {Promise<object>} Objeto con los 12 KPIs calculados.
 */
export const getFinancialKPIs = async () => {
    try {
        const response = await apiService.get('/dashboard/kpis-financieros');
        return response.data;
    } catch (error) {
        console.error('Error al obtener los KPIs financieros:', error);
        throw error; 
    }
};