import { apiService } from './apiService';

/**
 * Obtiene la lista jerárquica de cuentas.
 * @param {object} params - Parámetros opcionales, ej: { limit: 5000 }
 * @returns {Promise}
 */
export const getPlanCuentas = (params) => {
  return apiService.get('/plan-cuentas/', { params });
};

/**
 * Obtiene la lista plana de cuentas (para desplegables).
 * @param {object} params - Parámetros opcionales, ej: { permite_movimiento: true }
 * @returns {Promise}
 */
export const getPlanCuentasFlat = (params) => {
  return apiService.get('/plan-cuentas/list-flat', { params });
};

/**
 * Crea una nueva cuenta.
 * @param {object} cuentaData - Los datos de la cuenta a crear.
 * @returns {Promise}
 */
export const createCuenta = (cuentaData) => {
  return apiService.post('/plan-cuentas/', cuentaData);
};

/**
 * Actualiza una cuenta existente.
 * @param {number} id - El ID de la cuenta a actualizar.
 * @param {object} cuentaData - Los datos para actualizar.
 * @returns {Promise}
 */
export const updateCuenta = (id, cuentaData) => {
  return apiService.put(`/plan-cuentas/${id}`, cuentaData);
};

/**
 * Llama al endpoint para analizar qué cuentas de una rama se pueden eliminar.
 * @param {number} cuentaId - El ID de la cuenta padre desde donde iniciar el análisis.
 * @returns {Promise}
 */
export const analizarDepuracion = (cuentaId) => {
  return apiService.get(`/plan-cuentas/analizar-depuracion/${cuentaId}`);
};

/**
 * Llama al endpoint para ejecutar la eliminación de una lista de cuentas.
 * @param {Array<number>} ids - Un array con los IDs de las cuentas a eliminar.
 * @returns {Promise}
 */
export const ejecutarDepuracion = (ids) => {
  const payload = { ids_a_eliminar: ids };
  return apiService.post('/plan-cuentas/ejecutar-depuracion', payload);
};

/**
 * Analiza un array de cuentas (desde JSON/CSV) contra la DB.
 * @param {Array} cuentas - Array de objetos {codigo, nombre, ...}
 * @returns {Promise} { cuentas_analizadas, total_nuevas, ... }
 */
export const analizarImportacion = (cuentas) => {
  return apiService.post('/plan-cuentas/analizar-importacion', cuentas);
};

/**
 * Importa el lote de cuentas definitivas.
 * @param {Array} cuentas - Array de cuentas seleccionadas para crear.
 * @returns {Promise}
 */
export const importarLote = (cuentas) => {
  return apiService.post('/plan-cuentas/importar-lote', { cuentas });
};