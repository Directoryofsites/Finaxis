import { apiService } from './apiService';

export const indicadoresApiService = {
    getByVigencia: async (vigencia) => {
        try {
            return await apiService.get(`/indicadores/${vigencia}`);
        } catch (error) {
            console.error("Error fetching indicadores", error);
            throw error;
        }
    },

    update: async (vigencia, data) => {
        try {
            // Data structure: { trm, salario_minimo, uvt ... } - fields are optional
            return await apiService.put(`/indicadores/${vigencia}`, data);
        } catch (error) {
            console.error("Error updating indicadores", error);
            throw error;
        }
    }
};
