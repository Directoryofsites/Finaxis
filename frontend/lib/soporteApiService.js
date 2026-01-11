import axios from 'axios';

// NOTE: We change roles endpoint to allow fetching system roles (no empresa_id needed for support)
export const getRoles = (empresaId = null) => {
  let url = '/roles/';
  if (empresaId) {
    url += `?empresa_id=${empresaId}`;
  }
  return soporteApiService.get(url);
};

const SOPORTE_TOKEN_KEY = 'soporteAuthToken';

// --- CONFIGURACIÓN DE PRECIOS POR EMPRESA (NUEVO) ---
export const getPrecioEmpresa = (empresaId) => {
  return soporteApiService.get(`/empresas/${empresaId}/config-precio`);
};

export const setPrecioEmpresa = (empresaId, precio) => {
  return soporteApiService.put(`/empresas/${empresaId}/config-precio`, { precio });
};

export const soporteApiService = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/api` : 'http://127.0.0.1:8000/api',
  // CORRECCIÓN CLAVE: Se elimina la cabecera 'Content-Type' por defecto.
  headers: {}
});

soporteApiService.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem(SOPORTE_TOKEN_KEY);
      if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

soporteApiService.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.data && error.response.data.detail) {
      const errorDetail = error.response.data.detail;
      const safeErrorMessage =
        typeof errorDetail === 'string'
          ? errorDetail
          : JSON.stringify(errorDetail, null, 2);
      error.response.data.detail = safeErrorMessage;
    }
    return Promise.reject(error);
  }
);

export const setSoporteAuthToken = (token) => {
  if (token) {
    localStorage.setItem(SOPORTE_TOKEN_KEY, token);
  } else {
    localStorage.removeItem(SOPORTE_TOKEN_KEY);
  }
};

export const getDashboardData = () => {
  return soporteApiService.get('/soporte/dashboard-data');
};

export const crearEmpresaConUsuarios = (payload) => {
  return soporteApiService.post('/empresas/', payload);
};

export const deleteEmpresa = (empresaId) => {
  return soporteApiService.delete(`/empresas/${empresaId}`);
};

export const updateEmpresa = (empresaId, empresaData) => {
  return soporteApiService.put(`/empresas/${empresaId}`, empresaData);
};

export const createUserForCompany = (empresaId, userData) => {
  return soporteApiService.post(`/empresas/${empresaId}/usuarios`, userData);
};

export const updateLimiteRegistros = (empresaId, limite) => {
  const payload = {
    limite_registros: limite === '' || isNaN(parseInt(limite, 10)) ? null : parseInt(limite, 10)
  };
  return soporteApiService.put(`/empresas/${empresaId}/limite`, payload);
};

export const deleteUser = (userId) => {
  return soporteApiService.delete(`/usuarios/${userId}`);
};

export const updateUser = (userId, userData) => {
  return soporteApiService.put(`/usuarios/${userId}`, userData);
};

export const getMaestrosSoporte = () => {
  return soporteApiService.get('/utilidades/soporte/maestros');
};

export const inspeccionarEntidades = (payload) => {
  return soporteApiService.post('/utilidades/inspeccionar-entidades', payload);
};

export const erradicarEntidadesMaestras = (payload) => {
  return soporteApiService.post('/utilidades/erradicar-entidades-maestras', payload);
};

export const iniciarReseteoPassword = (payload) => {
  return soporteApiService.post('/utilidades/iniciar-reseteo-password', payload);
};

export const analizarErradicacion = (payload) => {
  return soporteApiService.post('/utilidades/analizar-erradicacion', payload);
};

export const getConteoRegistros = () => {
  return soporteApiService.get('/utilidades/conteo-registros');
};

export const getSoporteUsers = () => {
  return soporteApiService.get('/usuarios/soporte');
};

export const createSoporteUser = (userData) => {
  return soporteApiService.post('/usuarios/soporte', userData);
};

export const updateSoporteUserPassword = (userId, passwordData) => {
  return soporteApiService.put(`/usuarios/soporte/${userId}/password`, passwordData);
};

// getRoles removed (duplicate)

// --- FUNCIÓN CORREGIDA (Usaba 'soporteApi' en vez de 'soporteApiService') ---
export const setCupoAdicional = (empresaId, anio, mes, cantidad) => {
  return soporteApiService.post(`/empresas/${empresaId}/adicionales`, {
    anio: parseInt(anio),
    mes: parseInt(mes),
    cantidad_adicional: parseInt(cantidad)
  });
};

// EN frontend/lib/soporteApiService.js

export const getConsumoEmpresa = (empresaId, mes, anio) => {
  return soporteApiService.get(`/empresas/${empresaId}/consumo`, {
    params: { mes, anio }
  });
};

export const getRecargasEmpresa = (empresaId, mes, anio) => {
  return soporteApiService.get(`/utilidades/recargas-empresa/${empresaId}`, {
    params: { mes, anio }
  });
};

export const deleteRecargaEmpresa = (recargaId) => {
  return soporteApiService.delete(`/utilidades/recargas-empresa/${recargaId}`);
};


export const getPaquetesRecarga = () => {
  return soporteApiService.get('/utilidades/paquetes-recarga');
};

export const createPaqueteRecarga = (data) => {
  return soporteApiService.post('/utilidades/paquetes-recarga', data);
};

export const updatePaqueteRecarga = (id, data) => {
  return soporteApiService.put(`/utilidades/paquetes-recarga/${id}`, data);
};

export const deletePaqueteRecarga = (id) => {
  return soporteApiService.delete(`/utilidades/paquetes-recarga/${id}`);
};

export const getPrecioRegistro = () => {
  return soporteApiService.get('/utilidades/config/precio-registro');
};

export const setPrecioRegistro = (precio) => {
  return soporteApiService.post('/utilidades/config/precio-registro', { precio });
};

export const markRecargaPaid = (recargaId, pagado) => {
  return soporteApiService.put(`/consumo/recargas/${recargaId}/pago`, { pagado });
};

export const updatePlanMensualManual = (empresaId, anio, mes, limite) => {
  return soporteApiService.put(`/empresas/${empresaId}/plan-mensual`, {
    anio: parseInt(anio),
    mes: parseInt(mes),
    limite: parseInt(limite),
    es_manual: true
  });
};
