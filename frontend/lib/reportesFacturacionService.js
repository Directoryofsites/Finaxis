// frontend/lib/reportesFacturacionService.js (Versión con FIX DE BUILD ERROR y NUEVA FUNCIÓN POR DOCUMENTO)

import { apiService } from './apiService'; // Asumiendo que apiService está configurado correctamente

// --- Función Existente para Reporte Detallado ---
const generarReporteFacturacion = async (filtros) => {
  try {
    console.log('Llamando a la API de reporte detallado con los filtros:', filtros);
    const response = await apiService.post('/reportes-facturacion/', filtros);
    return response.data;
  } catch (error) {
    console.error('Error al generar el reporte de facturación:', error.response?.data || error.message);
    throw error;
  }
};

// --- Función Existente para PDF del Reporte Detallado ---
const solicitarUrlPdfReporteFacturacion = async (filtros) => {
  try {
    console.log('Solicitando URL para PDF detallado con filtros:', filtros);
    const response = await apiService.post('/reportes-facturacion/solicitar-pdf', filtros);
    return response.data;
  } catch (error) {
    console.error('Error al solicitar la URL del PDF detallado:', error.response?.data || error.message);
    throw error;
  }
};

// --- Función Existente para Rentabilidad por Producto/Grupo ---
const getRentabilidadPorGrupo = async (filtros) => { 
  try {
    console.log('Llamando a la API de rentabilidad con los filtros:', filtros);
    const response = await apiService.post('/reportes-facturacion/rentabilidad-producto', filtros);
    return response.data;
  } catch (error) {
    console.error('Error al obtener la rentabilidad por producto/grupo:', error.response?.data || error.message);
    throw error;
  }
};

// =================================================================================
// === NUEVA FUNCIÓN: RENTABILIDAD POR DOCUMENTO (IMPLEMENTACIÓN) ===
// =================================================================================
/**
 * Llama al endpoint del backend para obtener la rentabilidad línea por línea de un documento.
 * @param {object} filtros - Objeto con tipo_documento_id y numero_documento.
 * @param {boolean} [generarPdf=false] - Si es true, llama a la ruta de PDF directo.
 * @returns {Promise<object|Blob>} La promesa que resuelve con los datos JSON o el Blob del PDF.
 */
const getRentabilidadPorDocumento = async (filtros, generarPdf = false) => {
  const endpoint = generarPdf 
    ? '/reportes-facturacion/rentabilidad-documento/generar-pdf' // Endpoint de PDF
    : '/reportes-facturacion/rentabilidad-documento';          // Endpoint de Datos JSON
  
  const responseType = generarPdf ? 'blob' : 'json';

  try {
    console.log(`Llamando a la API de Rentabilidad por Documento (${generarPdf ? 'PDF' : 'JSON'}) con filtros:`, filtros);
    
    const response = await apiService.post(endpoint, filtros, {
      responseType: responseType,
    });
    
    // Si esperamos PDF, devolvemos el Blob para que el componente lo maneje (window.open)
    if (generarPdf) {
      return response.data; // Es un Blob
    }
    
    return response.data; // Es el JSON de detalle y totales
  } catch (error) {
    console.error('Error al obtener la rentabilidad por documento:', error.response?.data || error.message);
    // Lógica para intentar leer el error del Blob (similar a generarPdfRentabilidad)
     if (error.response && error.response.data instanceof Blob && error.response.data.type === 'application/json') {
         try {
             const errorText = await error.response.data.text();
             const errorJson = JSON.parse(errorText);
             console.error("Detalle del error (JSON):", errorJson);
             throw new Error(errorJson.detail || 'Error al generar el reporte.');
         } catch (parseError) {
              console.error("No se pudo parsear el error blob como JSON.");
         }
    }
    throw error;
  }
};
// =================================================================================


// --- INICIO: NUEVA FUNCIÓN PARA GENERAR PDF RENTABILIDAD (DIRECTO) ---
/**
 * Llama al endpoint del backend para generar el PDF de rentabilidad (por grupo/producto) directamente.
 * @param {object} filtros - El objeto con los filtros (grupo_ids, fechas, etc.).
 * @returns {Promise<Blob>} La promesa que resuelve con el Blob del PDF.
 */
const generarPdfRentabilidad = async (filtros) => {
  try {
    console.log('Llamando a la API para generar PDF de rentabilidad con filtros:', filtros);
    // Llamamos al nuevo endpoint POST para generación directa
    const response = await apiService.post('/reportes-facturacion/rentabilidad-producto/generar-pdf', filtros, {
      responseType: 'blob', // ¡Importante! Indicar que esperamos un archivo binario
    });
    // Axios devuelve el blob directamente en response.data cuando responseType es 'blob'
    return response.data;
  } catch (error) {
    console.error('Error al generar el PDF de rentabilidad:', error.response?.data || error.message);
    // Si el error viene en el blob, intentar leerlo como texto (puede dar más pistas)
    if (error.response && error.response.data instanceof Blob && error.response.data.type === 'application/json') {
         try {
             const errorJson = JSON.parse(await error.response.data.text());
             console.error("Detalle del error (JSON):", errorJson);
             throw new Error(errorJson.detail || 'Error al generar PDF');
         } catch (parseError) {
              console.error("No se pudo parsear el error blob como JSON.");
         }
    }
    throw error; // Re-lanzar el error original si no se pudo leer el blob
  }
};
// --- FIN: NUEVA FUNCIÓN PARA GENERAR PDF RENTABILIDAD ---

// Exportar todas las funciones necesarias
export {
    generarReporteFacturacion,
    solicitarUrlPdfReporteFacturacion,
    getRentabilidadPorGrupo, 
    generarPdfRentabilidad,
    // ¡CRÍTICO! Exportar la nueva función de reporte por documento
    getRentabilidadPorDocumento,
};

// --- FUNCIÓN DE GENERACIÓN DIRECTA DE PDF ---
/**
 * Llama al endpoint de generación directa de PDF y maneja la descarga.
 * @param {object} filtros - Objeto de filtros (ReporteFacturacionFiltros del backend).
 */
export const generarPdfDirectoReporteFacturacion = async (filtros) => {
    try {
        const response = await apiService.post(
            // La ruta que definimos en el Paso 1
            '/reportes-facturacion/generar-pdf-detallado', 
            filtros,
            {
                responseType: 'blob' // CRÍTICO: Respuesta binaria para descarga
            }
        );

        // Lógica de descarga
        const filename = response.headers['content-disposition'] 
            ? response.headers['content-disposition'].split('filename=')[1].replace(/\"/g, '')
            : `ReporteFacturacion_${new Date().toISOString().slice(0, 10)}.pdf`;

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
        console.error('Error al generar PDF del Reporte de Facturación:', error.response?.data || error.message);
        throw error;
    }
};