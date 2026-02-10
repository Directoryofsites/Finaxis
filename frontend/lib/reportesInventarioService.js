// frontend/lib/reportesInventarioService.js (VERSIÓN COMPLETA CON NUEVA FUNCIÓN PDF)

import { apiService } from './apiService';

// Funciones existentes de JSON... (Movimiento Analítico / Super Informe)
export const getReporteAnalitico = async (filtros) => {
    try {
        const response = await apiService.post('/reportes-inventario/movimiento-analitico', filtros);
        return response.data;
    } catch (error) {
        console.error('Error al obtener el Reporte Analítico:', error);
        throw error;
    }
};

export const getSuperInformeInventarios = async (filtros) => {
    try {
        const response = await apiService.post('/reportes-inventario/super-informe-inventarios', filtros);
        return response.data;
    } catch (error) {
        console.error('Error al obtener el Super Informe de Inventarios:', error);
        throw error;
    }
};

export const getKardexPorProducto = async (productoId, fecha_inicio, fecha_fin, bodegaId = null) => {
    try {
        const params = { fecha_inicio, fecha_fin };
        if (bodegaId !== null && bodegaId !== '') {
            params.bodega = bodegaId;
        }

        const response = await apiService.get(`/reportes-inventario/kardex/${productoId}`, { params });
        return response.data;
    } catch (error) {
        console.error('Error al obtener el Kardex:', error);
        throw error;
    }
};


// --- FUNCIÓN DE GENERACIÓN RÁPIDA DE PDF PARA SUPER INFORME (MANTENIDA) ---
export const generarPdfDirectoSuperInforme = async (filtros) => {
    try {
        const response = await apiService.post(
            '/reportes-inventario/super-informe-inventarios/generar-pdf-directo',
            filtros,
            {
                responseType: 'blob'
            }
        );

        const filename = response.headers['content-disposition']
            ? response.headers['content-disposition'].split('filename=')[1].replace(/"/g, '')
            : `SuperInforme_${new Date().toISOString().slice(0, 10)}.pdf`;

        const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', filename);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);

        return { success: true, message: `PDF generado y descargado como ${filename}` };

    } catch (error) {
        console.error('Error al generar PDF de Super Informe (Directo):', error.response || error);
        throw error;
    }
};

// =================================================================================
// === [NUEVA FUNCIÓN] GENERAR PDF MOVIMIENTO ANALÍTICO ===
// Esta es la función que faltaba y causaba el error de compilación.
// =================================================================================
export const generarPdfMovimientoAnalitico = async (filtros) => {
    try {
        const response = await apiService.post(
            '/reportes-inventario/movimiento-analitico/pdf',
            filtros,
            { responseType: 'blob' }
        );

        const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `Movimiento_Analitico_${new Date().toISOString().slice(0, 10)}.pdf`);
        document.body.appendChild(link);
        link.click();
        link.parentNode.removeChild(link);
        window.URL.revokeObjectURL(url);

        return true;
    } catch (error) {
        console.error("Error al generar PDF Analítico:", error);
        throw error;
    }
};

// =================================================================================
// === FUNCIÓN CRÍTICA: KARDEX (IMPLEMENTACIÓN DE URL FIRMADA) ===
// =================================================================================
export const generarPdfKardex = async (filtros) => {
    try {
        const response = await apiService.post('/reportes-inventario/kardex/token-pdf', filtros);
        const { token } = response.data;

        if (!token) throw new Error("El Backend no devolvió un token de descarga.");

        const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'https://finaxis.com.co';
        const urlDescarga = `${backendUrl}/api/reportes-inventario/kardex/pdf/${token}`;

        const newTab = window.open(urlDescarga, '_blank');
        if (!newTab) throw new Error("El navegador bloqueó la apertura de la ventana de descarga.");

        return { success: true, message: "PDF solicitado." };

    } catch (error) {
        console.error('Error al solicitar el PDF de Kardex:', error.response || error);
        throw error;
    }
};

// =================================================================================
// === FUNCIONES REPORTE DE TOPES ===
// =================================================================================
export const getReporteTopes = async (filtros) => {
    try {
        const response = await apiService.get('/reportes-inventario/topes', { params: filtros });
        return response.data;
    } catch (error) {
        console.error('Error al obtener el Reporte de Topes:', error);
        throw error;
    }
};

export const crearTokenTopesPDF = async (filtros) => {
    try {
        const response = await apiService.post('/reportes-inventario/topes/token-pdf', filtros);
        return response.data.token;
    } catch (error) {
        console.error('Error al solicitar token de Topes PDF:', error);
        throw error;
    }
};

export const generarPdfTopes = async (filtros) => {
    try {
        const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'https://finaxis.com.co';
        const urlDescarga = `${backendUrl}/api/reportes-inventario/topes/pdf?fecha_corte=${filtros.fecha_corte}&tipo_alerta=${filtros.tipo_alerta}&bodega_ids=${filtros.bodega_ids ? filtros.bodega_ids.join(',') : ''}&grupo_ids=${filtros.grupo_ids ? filtros.grupo_ids.join(',') : ''}`;

        const newTab = window.open(urlDescarga, '_blank');
        if (!newTab) throw new Error("El navegador bloqueó la apertura.");
        return { success: true, message: "PDF solicitado." };

    } catch (error) {
        console.error('Error al generar PDF de Topes:', error.response || error);
        throw error;
    }
};