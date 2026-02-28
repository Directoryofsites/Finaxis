import { apiService } from './apiService';

export const indicadoresApiService = {
    getByVigencia: async (vigencia) => {
        try {
            const res = await apiService.get(`/indicadores/${vigencia}`);
            return res.data;
        } catch (error) {
            console.error("Error fetching indicadores", error);
            throw error;
        }
    },

    update: async (vigencia, data) => {
        try {
            // Data structure: { trm, salario_minimo, uvt ... } - fields are optional
            const res = await apiService.put(`/indicadores/${vigencia}`, data);
            return res.data;
        } catch (error) {
            console.error("Error updating indicadores", error);
            throw error;
        }
    },

    syncForce: async (vigencia) => {
        try {
            const res = await apiService.post(`/indicadores/${vigencia}/sync_force`);
            return res.data;
        } catch (error) {
            console.error("Error force syncing indicadores", error);
            throw error;
        }
    }
};
