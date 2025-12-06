import { apiService } from './apiService';

const facturacionService = {
  /**
   * Endpoint para crear un nuevo documento de factura.
   */
  createFactura: async (payload) => {
    try {
      const response = await apiService.post('/facturacion/', payload);
      return response.data;
    } catch (error) {
      console.error('Error al crear la factura:', error);
      throw error;
    }
  },

  // === INICIO: FIX CRÍTICO - FUNCIÓN FALTANTE PARA CALCULAR PRECIO ===
  /**
   * Llama al servicio de inventario para calcular el precio de venta dinámico
   * en función de la lista de precios asignada al cliente.
   * @param {number} productoId El ID del producto.
   * @param {number} listaPrecioId La lista de precios asignada al cliente.
   * @returns {number} El precio calculado (float).
   */
  getPrecioVenta: async (productoId, listaPrecioId) => {
    try {
      const endpoint = `/inventario/productos/${productoId}/precio-venta`;
      const params = {
        lista_precio: listaPrecioId // Coincide con el alias en app/api/inventario/routes.py
      };

      const response = await apiService.get(endpoint, { params });
      
      // El backend devuelve: { "precio_calculado": 123.45 }
      return response.data.precio_calculado;
      
    } catch (error) {
      console.error(`[CRÍTICO] Error al obtener precio de venta para Producto ${productoId} con Lista ${listaPrecioId}:`, error);
      // Retornar 0 o lanzar error, dependiendo de la lógica de fallback del Frontend.
      // Retornamos 0 para evitar un crash en la UI, pero el log de error queda registrado.
      return 0; 
    }
  }
  // === FIN: FIX CRÍTICO ===
};

export default facturacionService;