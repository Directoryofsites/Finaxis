import { apiService } from './apiService';

const comprasService = {
  createCompra: async (payload) => {
    try {
      // Apuntamos al endpoint de compras en el backend
      const response = await apiService.post('/compras/', payload);
      return response.data;
    } catch (error) {
      console.error('Error al crear la factura de compra:', error);
      throw error;
    }
  },
};

export default comprasService;