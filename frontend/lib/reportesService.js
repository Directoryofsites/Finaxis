import { apiService } from './apiService';

/**
 * Llama al endpoint del backend para generar el reporte de Balance de Prueba.
 * @param {object} filtros - El objeto con los filtros del reporte.
 * @returns {Promise} La promesa de la llamada de Axios.
 */
export const getBalanceDePrueba = (filtros) => {
  return apiService.post('/reports/balance-de-prueba', filtros);
};

/**
 * Llama al endpoint del backend para obtener una URL firmada para el PDF del Balance de Prueba.
 * @param {object} filtros - El objeto con los filtros del reporte.
 * @returns {Promise} La promesa de la llamada de Axios.
 */
export const getSignedUrlForBalanceDePrueba = (filtros) => {
  return apiService.post('/reports/balance-de-prueba/get-signed-url', filtros);
};


// --- INICIO: NUEVAS FUNCIONES "GEMELAS" PARA CENTROS DE COSTO ---

/**
 * Llama al endpoint del backend para generar el reporte de Balance de Prueba por CC.
 * @param {object} filtros - El objeto con los filtros del reporte.
 * @returns {Promise} La promesa de la llamada de Axios.
 */
export const getBalanceDePruebaCC = (filtros) => {
  return apiService.post('/reports/balance-de-prueba-cc', filtros);
};

/**
 * Llama al endpoint del backend para obtener una URL firmada para el PDF del Balance de Prueba por CC.
 * @param {object} filtros - El objeto con los filtros del reporte.
 * @returns {Promise} La promesa de la llamada de Axios.
 */
export const getSignedUrlForBalanceDePruebaCC = (filtros) => {
  return apiService.post('/reports/balance-de-prueba-cc/get-signed-url', filtros);
};

// --- FIN: NUEVAS FUNCIONES "GEMELAS" ---


/**
 * Llama al endpoint del backend para disparar el recálculo de la cuenta
 * corriente de un tercero específico.
 * @param {number} terceroId - El ID del tercero (cliente o proveedor) a recalcular.
 * @returns {Promise} La promesa de la llamada de Axios.
 */
export const recalcularSaldosTercero = (terceroId) => {
  return apiService.post(`/reports/recalcular-tercero/${terceroId}`);
};