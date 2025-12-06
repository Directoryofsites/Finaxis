// frontend/lib/tiposDocumentoService.js (Refactorizado a Exportación Nombrada con SONDA)

import { apiService } from './apiService';

/**
 * Obtiene todos los tipos de documento.
 */
export const getTiposDocumento = async () => {
    try {
        // Asumiendo que la ruta es /tipos-documento/
        const response = await apiService.get('/tipos-documento/');
        
        // --- SONDA CRÍTICA ---
        console.log("SONDA: Tipos de Documento recibidos del Backend:", response.data);
        // --- FIN SONDA CRÍTICA ---
        
        return response.data;
    } catch (error) {
        console.error('Error al obtener tipos de documento:', error);
        throw error;
    }
};
// Las demás funciones relacionadas con documentos (si existen) deben usar 'export const'