import { apiService } from './apiService';

/**
 * Obtiene la lista de todos los períodos cerrados para la empresa del usuario actual.
 */
export const getPeriodosCerrados = async () => {
  try {
    const { data } = await apiService.get('/periodos/');
    return data;
  } catch (error) {
    console.error('Error al obtener los períodos cerrados:', error);
    throw error;
  }
};

/**
 * Envía la solicitud para cerrar un período contable específico.
 * @param {number} ano El año del período a cerrar.
 * @param {number} mes El mes del período a cerrar.
 */
export const cerrarPeriodo = async (ano, mes) => {
  try {
    const { data } = await apiService.post('/periodos/', { ano, mes });
    return data;
  } catch (error) {
    console.error(`Error al cerrar el período ${mes}/${ano}:`, error);
    throw error;
  }
};

/**
 * Envía la solicitud para reabrir un período contable específico.
 * @param {number} ano El año del período a reabrir.
 * @param {number} mes El mes del período a reabrir.
 */
export const reabrirPeriodo = async (ano, mes) => {
  try {
    const { data } = await apiService.delete(`/periodos/${ano}/${mes}`);
    return data;
  } catch (error) {
    console.error(`Error al reabrir el período ${mes}/${ano}:`, error);
    throw error;
  }
};