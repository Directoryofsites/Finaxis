'use client';

import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { jwtDecode } from 'jwt-decode';
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
      console.error("Fallo de autenticación:", error.message);
      setUser(null);
      setAuthToken(null);
      if (typeof window !== 'undefined') {
        localStorage.removeItem(TOKEN_KEY);
      }
      return false;
    }
  }, []);

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
      initializeAuth(token);
    }
    setAuthLoading(false);
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