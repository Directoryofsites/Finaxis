// frontend/lib/inventarioService.js (VERSIÓN FINAL CON MIGRACIÓN DE AUTOCOMPLETE A POST)

import { apiService } from './apiService';

// --- FUNCIÓN AUXILIAR CRÍTICA PARA SANEAMIENTO DE FILTROS ---
/**
 * Elimina propiedades con valores nulos, indefinidos o cadenas vacías.
 * Crucial para evitar errores 422 Unprocessable Entity en el backend.
 */
const cleanFilters = (filters) => {
    const cleaned = {};
    for (const key in filters) {
        const value = filters[key];
        // Solo incluir valores que NO son null, undefined, ni una cadena vacía
        if (value !== null && value !== undefined && value !== '') {
            // Caso especial para arrays (como grupo_ids) que pueden ser vacíos
            if (Array.isArray(value) && value.length === 0) {
                continue; // Omitir arrays vacíos
            }
            cleaned[key] = value;
        }
    }
    return cleaned;
};
// ------------------------------------------------------------


/**
 * Obtiene todas las bodegas de la empresa actual desde el backend.
 */
export const getBodegas = async () => {
  try {
    // FIX DE RUTA DENTRO DEL SERVICIO: Debe ir bajo el prefijo /inventario/
    const response = await apiService.get('/inventario/bodegas');
    return response.data;
  } catch (error) {
    console.error('Error al obtener las bodegas:', error);
    throw error;
  }
};

/**
 * Obtiene todos los grupos de inventario de la empresa actual desde el backend.
 */
export const getGruposInventario = async () => {
  try {
    const response = await apiService.get('/inventario/grupos');
    return response.data;
  } catch (error) {
    console.error('Error al obtener los grupos de inventario:', error);
    throw error;
  }
};

/**
 * Obtiene todas las tasas de impuesto de la empresa actual desde el backend.
 */
export const getImpuestos = async () => {
  try {
    const response = await apiService.get('/inventario/tasas-impuesto/');
    return response.data;
  } catch (error) {
    console.error('Error al obtener las tasas de impuesto:', error);
    throw error;
  }
};

/**
 * Obtiene la lista completa de productos (para selectores).
 */
export const getProductos = async () => {
  try {
    const response = await apiService.get('/inventario/productos/');
    return response.data;
  } catch (error) {
    console.error('Error al obtener la lista de productos:', error);
    throw error;
  }
};

/**
 * Llama al backend para calcular el precio de venta de un producto
 * basado en una lista de precios específica.
 */
export const calcularPrecioVenta = async (productoId, listaPrecioId) => {
    if (!productoId || !listaPrecioId) {
        console.error("calcularPrecioVenta requiere productoId y listaPrecioId");
        throw new Error("Faltan parámetros para calcular el precio.");
    }
    try {
        const url = `/inventario/productos/${productoId}/precio-venta?lista_precio=${listaPrecioId}`;
        const response = await apiService.get(url);
        return response.data.precio_calculado;
    } catch (error) {
        console.error(`Error al calcular precio para producto ${productoId} con lista ${listaPrecioId}:`, error.response?.data || error);
        throw error;
    }
};

/**
 * **LISTA DE PRODUCTOS PARA TABLA PRINCIPAL.** (Usa POST)
 */
export const getProductosFiltrados = async (filtros = {}) => {
  try {
    const cleanedFilters = cleanFilters(filtros);
    console.log("Llamando a getProductosFiltrados (POST /productos/filtrar) con filtros saneados:", cleanedFilters);
    // >>> FIX CRÍTICO DE URL: Apuntamos a la ruta de filtrado correcta
    const response = await apiService.post('/inventario/productos/filtrar', cleanedFilters); 
    // <<< FIN FIX CRÍTICO
    return response.data;
  } catch (error) {
    // BLINDAJE DE ERRORES 422
    console.error('Error buscando productos:', error.response?.data || error.message);
    let errorMessage = 'Error desconocido al buscar productos.';

    if (error.response && error.response.status === 422) {
      try {
        const detail = error.response.data.detail;
        if (Array.isArray(detail) && detail.length > 0) {
          const loc = detail[0].loc[1] || 'filtro';
          errorMessage = `Filtro inválido en ${loc}: ${detail[0].msg}`;
        } else {
          errorMessage = 'Error de validación de filtros (422).';
        }
      } catch (e) {
        errorMessage = 'Error de validación (422) con formato desconocido.';
      }
    } else {
      errorMessage = error.message;
    }
    throw new Error(errorMessage);
  }
};


/**
 * **FUNCIÓN DE AUTOCOMPLETAR. (MIGRADA A POST PARA EVITAR 422)**
 */
export const searchProductosAutocomplete = async (filtros = {}) => {
  try {
    // --- FIX DEFINITIVO 422: MIGRACIÓN A POST ---
    const cleanedFilters = cleanFilters(filtros);
    console.log("Llamando a searchProductosAutocomplete (POST /productos/search-by-body) con filtros saneados:", cleanedFilters);
    
    // El endpoint /search-by-body asume que recibimos los filtros en el BODY (POST)
    const response = await apiService.post('/inventario/productos/search-by-body', cleanedFilters); 
    // --- FIN FIX DEFINITIVO ---
    return response.data;
  } catch (error) {
    // BLINDAJE DE ERRORES 422 (Mantenido)
    console.error('Error buscando productos:', error.response?.data || error.message);
    let errorMessage = 'Error desconocido al buscar productos.';

    if (error.response && error.response.status === 422) {
      try {
        const detail = error.response.data.detail;
        if (Array.isArray(detail) && detail.length > 0) {
          const loc = detail[0].loc[1] || 'filtro';
          errorMessage = `Filtro inválido en ${loc}: ${detail[0].msg}`;
        } else {
          errorMessage = 'Error de validación de filtros (422).';
        }
      } catch (e) {
        errorMessage = 'Error de validación (422) con formato desconocido.';
      }
    } else {
      errorMessage = error.message;
    }
    throw new Error(errorMessage);
  }
};

// --- RESTO DE FUNCIONES (Mantenidas) ---

export const deleteProducto = async (productoId) => {
  if (!productoId) {
    console.error("deleteProducto requiere productoId");
    throw new Error("Falta el ID del producto para eliminar.");
  }
  try {
    await apiService.delete(`/inventario/productos/${productoId}`);
  } catch (error) {
    console.error(`Error al eliminar el producto ${productoId}:`, error.response?.data || error.message);
    throw error;
  }
};

export const generarPdfListaProductos = async (filtros) => {
    try {
        const cleanedFilters = cleanFilters(filtros);
        
        const response_token = await apiService.post(
            '/inventario/productos/solicitar-pdf', 
            cleanedFilters
        );
        
        const token = response_token.data.token;
        
        const response = await apiService.get(
            `/inventario/productos/imprimir/${token}`,
            {
                responseType: 'blob' 
            }
        );

        const contentDisposition = response.headers['content-disposition'];
        const filenameMatch = contentDisposition && contentDisposition.match(/filename\*?=['"]?(.*)['"]?/i);
        
        let filename = `Cartilla_Inventario_${new Date().toISOString().slice(0, 10)}.pdf`;
        if (filenameMatch && filenameMatch[1]) {
             filename = decodeURIComponent(filenameMatch[1].replace(/\"/g, ''));
        }

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
        console.error('Error al generar PDF de la lista de productos:', error.response?.data || error.message);
        throw error;
    }
};

// frontend/lib/inventarioService.js (LISTA DE EXPORTACIÓN FINAL Y COMPLETA)

export {
    getBodegas,
    getGruposInventario,
    getImpuestos,
    getProductos,
    calcularPrecioVenta,
    getProductosFiltrados, 
    searchProductosAutocomplete, 
    deleteProducto,
    generarPdfListaProductos 
};