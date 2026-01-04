'use client';

import { createContext, useContext, useState, useEffect, useCallback } from 'react';
// FIX: Robust import ensuring compatibility with different build environments
import * as jwtDecodeLib from 'jwt-decode';
const jwtDecode = jwtDecodeLib.jwtDecode || jwtDecodeLib.default || jwtDecodeLib;

import apiService, { setAuthToken } from '../../lib/apiService';

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

  const initializeAuth = useCallback((token) => {
    try {
      const decodedUser = jwtDecode(token);
      if (decodedUser.exp * 1000 < Date.now()) {
        throw new Error('Token expirado');
      }

      const userData = {
        id: decodedUser.sub,
        email: decodedUser.sub,
        rol: decodedUser.rol,
        empresaId: decodedUser.empresa_id
      };

      setUser(userData);
      setAuthToken(token);
      return true;
    } catch (error) {
      console.error("Fallo de autenticación (initializeAuth):", error.message);
      // No eliminamos el token automáticamente para evitar que errores transitorios
      // (como en nuevas pestañas o condiciones de carrera) cierren la sesión globalmente.
      // Si el token es realmente inválido, el usuario verá la pantalla de login de todas formas
      // porque user será null.
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

  const value = { user, authLoading, login, logout };

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