'use client';

import { createContext, useContext, useState, useEffect, useCallback } from 'react';
// FIX: Robust import ensuring compatibility with different build environments
import * as jwtDecodeLib from 'jwt-decode';
const jwtDecode = jwtDecodeLib.jwtDecode || jwtDecodeLib.default || jwtDecodeLib;

import { apiService, setAuthToken } from '../../lib/apiService';

const AuthContext = createContext(null);
const TOKEN_KEY = 'authToken';

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);

  const logout = useCallback(() => {
    setUser(null);
    setAuthToken(null);
    if (typeof window !== 'undefined') {
      localStorage.removeItem(TOKEN_KEY);
      window.location.href = '/login';
    }
  }, []);

  const initializeAuth = useCallback(async (token) => {
    try {
      const decodedUser = jwtDecode(token);
      if (decodedUser.exp * 1000 < Date.now()) {
        throw new Error('Token expirado');
      }

      // 1. Establecer estado inicial básico desde el token (para evitar flicker blanco)
      console.log("--- SONDA AUTH CONTEXT ---");
      console.log("Token RAW decoded:", decodedUser);

      const initialUserData = {
        id: decodedUser.sub,
        email: decodedUser.sub,
        empresaId: decodedUser.empresa_id,
        // Rol básico mientras carga (opcional)
      };

      console.log("Initial User Data mapped:", initialUserData);

      setAuthToken(token);
      setUser(initialUserData);

      // 2. Fetch del perfil completo (Roles y Permisos) desde backend
      try {
        const response = await apiService.get('/usuarios/me');
        console.log("Perfil backend Loaded:", response.data);
        console.log("CHECK Campo Original:", response.data.empresa_original_nombre);

        // Mapeo explícito para asegurar que empresaId existe en camelCase si el backend manda snake_case
        const fullProfile = {
          ...response.data,
          empresaId: response.data.empresa_id || response.data.empresaId,
          empresaNombre: response.data.empresa?.razon_social || response.data.empresa?.nombre || 'Consorcio',
          empresaOriginal: response.data.empresa_original_nombre // Nuevo campo Matriz
        };
        console.log("Perfil Final SetUser:", fullProfile);

        setUser(fullProfile);
      } catch (fetchError) {
        console.error("Error cargando perfil completo:", fetchError);
        // Si falla el fetch de perfil, podríamos dejar al user básico O desloguear si es crítico.
        // Por ahora dejamos el básico pero alertamos en consola.
      }

      return true;
    } catch (error) {
      console.error("Fallo de autenticación (initializeAuth):", error.message);
      setUser(null);
      setAuthToken(null);
      return false;
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      const token = localStorage.getItem(TOKEN_KEY);
      if (token) {
        let success = initializeAuth(token);
        if (!success) {
          // RETRY STRATEGY: Wait 300ms and try again. 
          // This handles rare race conditions in new tabs where hydration/decoding might glitch.
          await new Promise(r => setTimeout(r, 300));
          success = initializeAuth(token);
        }
      }
      setAuthLoading(false);
    };
    init();
  }, [initializeAuth]);

  const login = (token) => {
    // Reutilizamos la lógica centralizada para evitar duplicar código
    const success = initializeAuth(token);
    if (success) {
      localStorage.setItem(TOKEN_KEY, token);
    } else {
      // Si el token de login es inválido por alguna razón, nos aseguramos de limpiar todo.
      logout();
    }
  };

  const switchCompany = async (empresaId) => {
    try {
      // 1. Llamar al endpoint de switch
      const response = await apiService.post('/auth/switch-company', { empresa_id: empresaId });
      const newToken = response.data.access_token;

      if (!newToken) throw new Error("No se recibió token");

      // 2. Actualizar estado y storage
      localStorage.setItem(TOKEN_KEY, newToken);
      setAuthToken(newToken);

      // 3. Re-inicializar perfil
      await initializeAuth(newToken);
      return true;
    } catch (error) {
      console.error("Error al cambiar de empresa:", error);
      return false;
    }
  };

  const value = { user, authLoading, login, logout, switchCompany };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth debe ser usado dentro de un AuthProvider');
  }
  return context;
};