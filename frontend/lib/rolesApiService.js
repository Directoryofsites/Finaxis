import { apiService } from './apiService';

// --- ROLES ---
export const getRoles = () => {
    return apiService.get('/roles').then(res => res.data);
};

export const createRol = (rolData) => {
    return apiService.post('/roles', rolData).then(res => res.data);
};

export const updateRol = (rolId, rolData) => {
    return apiService.put(`/roles/${rolId}`, rolData).then(res => res.data);
};

export const deleteRol = (rolId) => {
    return apiService.delete(`/roles/${rolId}`).then(res => res.data); // Likely returns a dict
};

// --- PERMISOS ---
export const getPermisos = () => {
    return apiService.get('/roles/permisos').then(res => res.data);
};

// --- USUARIOS (AUTOSERVICIO) ---
export const getCompanyUsers = () => {
    return apiService.get('/usuarios').then(res => res.data);
};

export const createCompanyUser = (userData) => {
    return apiService.post('/usuarios', userData).then(res => res.data);
};

export const updateCompanyUser = (userId, userData) => {
    return apiService.put(`/usuarios/${userId}`, userData).then(res => res.data);
};

export const deleteCompanyUser = (userId) => {
    return apiService.delete(`/usuarios/${userId}`).then(res => res.data);
};

// --- EXCEPCIONES DE PERMISOS (Capa 3) ---
// Obtiene TODOS los permisos con su estado real para un usuario
// (hereda del rol, tiene excepción, estado_efectivo)
export const getPermisosConEstado = (userId) => {
    return apiService.get(`/usuarios/${userId}/permisos`).then(res => res.data);
};

// Guarda un batch de excepciones (CONCEDER / REVOCAR)
// excepciones = [{ permiso_id, permitido: true|false }]
export const upsertExcepciones = (userId, excepciones) => {
    return apiService.put(`/usuarios/${userId}/permisos/excepciones`, { excepciones }).then(res => res.data);
};

// Elimina UNA excepción específica (el usuario vuelve a heredar su rol)
export const deleteExcepcion = (userId, permisoId) => {
    return apiService.delete(`/usuarios/${userId}/permisos/excepciones/${permisoId}`).then(res => res.data);
};

// Resetea TODAS las excepciones de un usuario (limpieza total)
export const resetExcepciones = (userId) => {
    return apiService.delete(`/usuarios/${userId}/permisos/excepciones`).then(res => res.data);
};
