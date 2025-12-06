'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { apiService } from '../../lib/apiService'; // Usamos el apiService normal para la llamada

function ResetPasswordComponent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [token, setToken] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const tokenFromUrl = searchParams.get('token');
    if (tokenFromUrl) {
      setToken(tokenFromUrl);
    } else {
      setError('No se proporcionó un token de reseteo válido en la URL.');
    }
  }, [searchParams]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!password || !confirmPassword) {
      setError('Por favor, complete ambos campos de contraseña.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Las contraseñas no coinciden.');
      return;
    }
    if (password.length < 6) {
        setError('La contraseña debe tener al menos 6 caracteres.');
        return;
    }

    setIsLoading(true);
    setError('');
    setMessage('');

    try {
      // --- INICIO DE LA CORRECCIÓN CLAVE ---
      const payload = {
        token: token,
        nueva_password: password // Se corrige el nombre de la clave para que coincida con el backend
      };
      // --- FIN DE LA CORRECCIÓN CLAVE ---

      const response = await apiService.post('/utilidades/resetear-password', payload);

      setMessage(response.data.msg + " Serás redirigido a la página de inicio de sesión en 5 segundos.");

      setTimeout(() => {
        router.push('/login');
      }, 5000);

    } catch (err) {
      // --- INICIO: BLINDAJE DEL MANEJO DE ERRORES ---
      let errorMessage = 'Ocurrió un error al resetear la contraseña.';
      if (err.response?.data?.detail) {
          // Si el detalle es un array (error de validación de Pydantic), tomamos el primer mensaje.
          if (Array.isArray(err.response.data.detail)) {
              errorMessage = err.response.data.detail[0].msg || errorMessage;
          } else {
              // Si es un string (error HTTP normal), lo usamos directamente.
              errorMessage = err.response.data.detail;
          }
      }
      setError(errorMessage);
      // --- FIN: BLINDAJE DEL MANEJO DE ERRORES ---
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-md">
        <h2 className="text-2xl font-bold text-center text-gray-800">Establecer Nueva Contraseña</h2>

        {message ? (
          <div className="p-4 text-center bg-green-100 text-green-800 border border-green-300 rounded-md">
            <p>{message}</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">Nueva Contraseña</label>
              <input
                id="password"
                name="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="block w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">Confirmar Nueva Contraseña</label>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                className="block w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {error && (
              <div className="p-3 text-sm text-red-800 bg-red-100 border border-red-300 rounded-md">
                {error}
              </div>
            )}

            <div>
              <button
                type="submit"
                disabled={isLoading || !token}
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-400"
              >
                {isLoading ? 'Actualizando...' : 'Actualizar Contraseña'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
    return (
        <Suspense fallback={<div>Cargando...</div>}>
            <ResetPasswordComponent />
        </Suspense>
    )
}