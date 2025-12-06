// frontend/lib/gestionVentasService.js (VERSIÓN CORREGIDA Y FINAL)

import { apiService } from './apiService'; // CORRECCIÓN: Se usa la importación nombrada

export const getReporteGestionVentas = async (filtros) => {
    // CORRECCIÓN: Se usa el nombre de variable correcto 'apiService' en lugar de 'api'
    const { data } = await apiService.post('/gestion-ventas/reporte', filtros);
    return data;
};

// FIX CRÍTICO: Se corrige la ruta a la que realmente existe en el backend (/solicitar-impresion-reporte)
export const solicitarUrlPdfGestionVentas = async (filtros) => {
    const { data } = await apiService.post('/gestion-ventas/solicitar-impresion-reporte', filtros);
    return data;
};