'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../context/AuthContext'; // Corregido para usar el contexto
import { apiService } from '../../lib/apiService';
import { jwtDecode } from 'jwt-decode';

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth(); // Usamos la función del contexto

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage('');

    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const response = await apiService.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      const { access_token } = response.data;

      // La clave: Informamos al contexto sobre el login exitoso
      // 1. Informamos al contexto sobre el login exitoso (establece estado y localstorage)
      login(access_token);
      setMessage('Inicio de sesión exitoso. Redirigiendo...');

      // 2. Decodificamos el token para saber el rol y redirigir inteligentemente
      try {
        const decoded = jwtDecode(access_token);
        console.log("Decoded Token for Redirect:", decoded);
        const roles = decoded.roles || []; // Asumimos que viene como lista de strings o objetos

        // Normalización de roles (si vienen como objetos {nombre: 'x'} o strings)
        const roleNames = roles.map(r => (typeof r === 'string' ? r : r.nombre));

        if (roleNames.includes('contador')) {
          router.push('/portal');
        } else {
          router.push('/');
        }
      } catch (decodeErr) {
        console.error("Error decoding token for redirect logic:", decodeErr);
        router.push('/'); // Fallback seguro
      }

    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Credenciales inválidas o error en el servidor.';
      setMessage(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-24 bg-gray-50">
      <div className="w-full max-w-md bg-white rounded-lg shadow-md p-8">
        <h1 className="text-2xl font-bold mb-6 text-center text-gray-800">
          Iniciar Sesión
        </h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">Email</label>
            <input type="email" id="email" className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700">Contraseña</label>
            <input type="password" id="password" className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          <button type="submit" disabled={isLoading} className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300">
            {isLoading ? 'Iniciando...' : 'Iniciar Sesión'}
          </button>
        </form>
        {message && (
          <p className={`mt-4 text-center text-sm font-medium ${message.includes('exitoso') ? 'text-green-600' : 'text-red-600'}`}>
            {message}
          </p>
        )}
      </div>
    </main>
  );
}