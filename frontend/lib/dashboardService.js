// frontend/lib/dashboardService.js (REEMPLAZO COMPLETO - FIX DE CONVERSIÓN DE FECHAS)

import { apiService } from './apiService';

/**
 * Obtiene las 9 Razones Financieras reales del Dashboard en un rango de fechas.
 * Ahora utiliza POST para enviar las fechas al backend.
 * @param {string} fechaInicioStr Cadena en formato 'YYYY-MM-DD'
 * @param {string} fechaFinStr Cadena en formato 'YYYY-MM-DD'
 * @returns {Promise<object>} Objeto con las 9 Razones y saldos calculados.
 */
export const getFinancialRatios = async (fechaInicioStr, fechaFinStr) => {
    try {

        // FIX CRÍTICO: Convertimos las cadenas de texto (strings) de los inputs a objetos Date 
        // para poder usar el método .toISOString() y asegurar que el formato sea correcto.
        // Usamos fechaInicioStr + 'T00:00:00' para evitar el problema de zona horaria y garantizar la fecha correcta.
        const fechaInicioDate = new Date(fechaInicioStr + 'T00:00:00');
        const fechaFinDate = new Date(fechaFinStr + 'T00:00:00');

        const payload = {
            // Utilizamos la conversión y la separamos para enviar solo 'YYYY-MM-DD'
            fecha_inicio: fechaInicioDate.toISOString().split('T')[0],
            fecha_fin: fechaFinDate.toISOString().split('T')[0]
        };

        // Llama al endpoint POST /api/dashboard/ratios-financieros (Nuevo endpoint)
        const response = await apiService.post('/dashboard/ratios-financieros', payload);
        return response.data;
    } catch (error) {
        console.error('Error al obtener las Razones Financieras:', error);
        throw error; // Propagar el error para que la página lo maneje
    }
}

export const getHorizontalAnalysis = async (p1Start, p1End, p2Start, p2End) => {
    try {
        const payload = {
            fecha_inicio_1: p1Start,
            fecha_fin_1: p1End,
            fecha_inicio_2: p2Start,
            fecha_fin_2: p2End
        };
        const response = await apiService.post('/dashboard/analisis-horizontal', payload);
        return response.data;
    } catch (error) {
        console.error('Error Horizontal Analysis:', error);
        throw error;
    }
};

export const getVerticalAnalysis = async (start, end) => {
    try {
        const payload = {
            fecha_inicio: start,
            fecha_fin: end
        };
        const response = await apiService.post('/dashboard/analisis-vertical', payload);
        return response.data;
    } catch (error) {
        console.error('Error Vertical Analysis:', error);
        throw error;
    }
};


// Se mantiene getFavoritos si existe en otro servicio, sino se ignora aquí.