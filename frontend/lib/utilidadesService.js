import { apiService } from './apiService';

/**
 * Servicio para encapsular todas las llamadas a la API
 * relacionadas con las utilidades de migración y soporte.
 */

// --- Servicios para los Selects / Dropdowns ---

export const getMaestrosParaMigracion = () => {
  // apiService ya incluye el empresaId del usuario logueado en el token
  // por lo que no necesitamos enviarlo. El backend lo extrae.
  return Promise.all([
    apiService.get('/tipos-documento'),
    apiService.get('/terceros'),
    apiService.get('/plan-cuentas/list-flat?permite_movimiento=true'),
    apiService.get('/centros-costo?permite_movimiento=true'),
    // Esta es una ruta especial que no depende de la empresa del usuario
    apiService.get('/empresas')
  ]);
};

// --- Servicios para el Módulo de Exportación ---

export const exportarDatos = (payload) => {
  return apiService.post('/utilidades/exportar-datos', payload);
};

// --- Servicios para el Módulo de Restauración ---

export const analizarBackup = (payload) => {
  return apiService.post('/utilidades/analizar-backup', payload);
};

export const ejecutarRestauracion = (payload) => {
  return apiService.post('/utilidades/ejecutar-restauracion', payload);
};

// --- Servicios para el Módulo de Transformación ---
// (Por ahora no requiere llamadas a la API, la lógica es local)

// --- Servicios para Importación Legacy ---
export const importarLegacy = (formData) => {
  return apiService.post('/utilidades/importar-legacy', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};