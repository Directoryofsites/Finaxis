// frontend/lib/apiService.js (Versión COMPLETA y Corregida)

import axios from 'axios';

// --- CIRUGÍA ARQUITECTÓNICA ---
const getDynamicApiUrl = () => {
    if (typeof window !== 'undefined') {
        const { hostname, protocol } = window.location;
        // El backend del ejecutable corre en el puerto 8765
        const isIpOrLocal = /^(localhost|127\.|192\.|10\.|172\.)/.test(hostname);
        
        if (isIpOrLocal) {
            return `http://${hostname}:8765`;
        }
        
        // Para dominios reales (finaxis.com.co) usamos la variable de Vercel
        return process.env.NEXT_PUBLIC_API_URL;
    }
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8765';
};

export const API_URL = getDynamicApiUrl();

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