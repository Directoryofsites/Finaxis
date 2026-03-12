// frontend/lib/apiService.js (Versión COMPLETA y Corregida)

import axios from 'axios';

// --- CIRUGÍA ARQUITECTÓNICA ---
// Se exporta como una constante nombrada y se simplifica la baseURL.
export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';

export const apiService = axios.create({
    baseURL: `${API_URL}/api`,
    headers: {
        'Content-Type': 'application/json'
    },
    paramsSerializer: {
        indexes: null // Evita que los arrays se envíen como meses[]=1&meses[]=2, los envía como meses=1&meses=2
    }
});
// --- FIN DE LA CIRUGÍA ---

apiService.interceptors.request.use(
    (config) => {
        try {
            const token = localStorage.getItem('authToken');
            if (token) {
                config.headers['Authorization'] = `Bearer ${token}`;
            }
        } catch (e) {
            console.error('No se pudo acceder a localStorage:', e);
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// --- FIX SEGURIDAD: REDIRECCIÓN 401 EN RESPUESTA ---
apiService.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            // Token expirado o inválido
            if (typeof window !== 'undefined') {
                localStorage.removeItem('authToken');
                // Evitar bucles de redireccion
                if (window.location.pathname !== '/login') {
                    window.location.href = '/login';
                }
            }
        }
        return Promise.reject(error);
    }
);
// --- FIN FIX SEGURIDAD ---

export const setAuthToken = (token) => {
    if (token) {
        apiService.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
        delete apiService.defaults.headers.common['Authorization'];
    }
};

export const getAuditoriaConsecutivos = (empresaId = null) => {
    const payload = empresaId ? { empresa_id: empresaId } : {};
    return apiService.post('/utilidades/auditoria-consecutivos', payload);
};

export const getPrecioRegistroPublic = () => {
    return apiService.get('/consumo/precio-unitario');
};

// La línea 'export default' se ha eliminado para mantener la consistencia.