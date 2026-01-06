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

export const exportarDatos = async (payload) => {
  try {
    const response = await apiService.post('/utilidades/exportar-datos', payload, {
      responseType: 'blob' // Importante: Indicar que esperamos un archivo binario
    });

    // Crear URL de descarga
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;

    // Intentar obtener nombre del archivo del header
    let filename = `backup_sistema_${new Date().toISOString().slice(0, 10)}.json`;
    const contentDisposition = response.headers['content-disposition'];
    if (contentDisposition) {
      // Regex mejorado: capturar el contenido entre comillas O hasta el final si no hay comillas
      // Evita capturar la comilla de cierre.
      const fileNameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
      if (fileNameMatch && fileNameMatch.length === 2)
        filename = fileNameMatch[1];
    }

    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();

    // Limpieza
    link.remove();
    window.URL.revokeObjectURL(url);

    return response;
  } catch (error) {
    // Si el blob es un JSON de error, intentamos leerlo
    if (error.response && error.response.data instanceof Blob) {
      const errorText = await error.response.data.text();
      try {
        const errorJson = JSON.parse(errorText);
        error.response.data = errorJson; // Reemplazamos blob por json para que el catch superior lo lea
        throw error;
      } catch (e) {
        throw error;
      }
    }
    throw error;
  }
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