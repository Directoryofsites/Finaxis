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
