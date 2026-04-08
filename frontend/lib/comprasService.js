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

  getReporteDetallado: async (filtros) => {
    try {
      const response = await apiService.post('/reports/purchases-detailed', filtros);
      return response.data;
    } catch (error) {
      console.error('Error al obtener reporte detallado de compras:', error);
      throw error;
    }
  },

  downloadReporteDetalladoPDF: async (filtros) => {
    try {
      const response = await apiService.post('/reports/purchases-detailed/pdf', filtros, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      let filename = `Reporte_Compras_Detallado_${filtros.fecha_inicio}.pdf`;
      const contentDisposition = response.headers['content-disposition'];
      if (contentDisposition) {
        const fileNameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
        if (fileNameMatch && fileNameMatch.length === 2) filename = fileNameMatch[1];
      }
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error al descargar PDF de compras:', error);
      throw error;
    }
  },

  downloadReporteDetalladoCSV: async (filtros) => {
    try {
      const response = await apiService.post('/reports/purchases-detailed/csv', filtros, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      let filename = `Reporte_Compras_Detallado_${filtros.fecha_inicio}.csv`;
      const contentDisposition = response.headers['content-disposition'];
      if (contentDisposition) {
        const fileNameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
        if (fileNameMatch && fileNameMatch.length === 2) filename = fileNameMatch[1];
      }
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error al descargar CSV de compras:', error);
      throw error;
    }
  }
};

export default comprasService;