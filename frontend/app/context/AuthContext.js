'use client';

import { createContext, useContext, useState, useEffect, useCallback } from 'react';
// FIX: Robust import ensuring compatibility with different build environments
import { jwtDecode } from 'jwt-decode';

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
      // FIX SEGURIDAD: Limpieza profunda (Deep Logout) conservando Preferencias
      // Se extraen las llaves permitidas para historiales e indicadores
      const keysToKeep = ['app_history', 'smart_hub_notes', 'theme', 'voice_history'];
      const savedData = {};
      
      try {
        // 1. Guardar llaves exactas
        keysToKeep.forEach(key => {
          const val = localStorage.getItem(key);
          if (val) savedData[key] = val;
        });

        // 2. Guardar llaves dinámicas (Historiales por usuario e Indicadores)
        for (let i = 0; i < localStorage.length; i++) {
           const key = localStorage.key(i);
           if (!key) continue;

           if (key.startsWith('indicadores_') || key.startsWith('app_history_')) {
               savedData[key] = localStorage.getItem(key);
           }
        }
      } catch (e) {
        console.error("Error salvaguardando localStorage", e);
      }

      localStorage.clear();
      sessionStorage.clear();

      // Restaurar permitidos
      Object.keys(savedData).forEach(key => {
        localStorage.setItem(key, savedData[key]);
      });
      window.location.href = '/login';
    }
  }, []);

  const initializeAuth = useCallback(async (token) => {
    // Si no se pasa token, intentar leerlo del localStorage (para refresco de perfil)
    const activeToken = token || (typeof window !== 'undefined' ? localStorage.getItem(TOKEN_KEY) : null);
    if (!activeToken) return false;
    try {
      const decodedUser = jwtDecode(activeToken);
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

      setAuthToken(activeToken);
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
      // Solo forzamos logout si estamos en el cliente y hay un error real (evita loops en SSR)
      if (typeof window !== 'undefined') {
        logout();
      } else {
        setUser(null);
        setAuthToken(null);
      }
      return false;
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      const token = localStorage.getItem(TOKEN_KEY);
      if (token) {
        let success = await initializeAuth(token);
        if (!success) {
          // RETRY STRATEGY: Wait 300ms and try again. 
          // This handles rare race conditions in new tabs where hydration/decoding might glitch.
          await new Promise(r => setTimeout(r, 300));
          success = await initializeAuth(token);
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

  // Helper centralizado: devuelve permisos efectivos con fallback a roles si 'permissions' llegó vacío
  const getEffectivePermissions = useCallback(() => {
    if (!user) return [];
    // Si el backend ya entregó permisos calculados (Capa 3), usarlos
    if (user.permissions && user.permissions.length > 0) {
      return user.permissions;
    }
    // Fallback: calcular desde roles (sin excepciones individuales)
    if (user.roles && user.roles.length > 0) {
      const fromRoles = new Set();
      user.roles.forEach(role => {
        (role.permisos || []).forEach(p => fromRoles.add(p.nombre));
      });
      return Array.from(fromRoles);
    }
    return [];
  }, [user]);

  const value = { user, authLoading, login, logout, switchCompany, initializeAuth, getEffectivePermissions };

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