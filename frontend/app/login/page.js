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
      let errorMessage = 'Credenciales inválidas o error en el servidor.';
      if (error.response?.status === 429) {
        errorMessage = 'Por seguridad, ha superado el límite de intentos. Por favor, espere 5 minutos antes de intentar nuevamente.';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }
      setMessage(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center p-4 sm:p-24 overflow-hidden">
      {/* Fondo de Imagen Financiera/Tecnológica (Ligera) */}
      <div
        className="absolute inset-0 z-0 bg-cover bg-center bg-no-repeat transition-opacity duration-1000"
        style={{
          // Usando una imagen optimizada de baja calidad/resolución web para carga rápida (Analytics/Finance)
          backgroundImage: "url('https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=75&w=1920&auto=format&fit=crop')",
        }}
      ></div>

      {/* Overlay Degradado (Mezcla Azul Oscuro a Negro para contraste, dando el look moderno) */}
      <div className="absolute inset-0 z-0 bg-gradient-to-br from-indigo-900/90 via-blue-900/80 to-slate-900/95 mix-blend-multiply"></div>

      {/* Partículas o Elementos abstractos decorativos (Puro CSS) */}
      <div className="absolute inset-0 z-0 opacity-30">
        <div className="absolute top-0 -left-1/4 w-1/2 h-1/2 bg-blue-500 rounded-full mix-blend-screen filter blur-[150px] animate-blob"></div>
        <div className="absolute bottom-0 -right-1/4 w-1/2 h-1/2 bg-indigo-600 rounded-full mix-blend-screen filter blur-[150px] animate-blob animation-delay-2000"></div>
      </div>

      <div className="z-10 w-full max-w-md bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl shadow-[0_8px_32px_0_rgba(0,0,0,0.37)] p-8 sm:p-10 transform transition-all">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-extrabold text-white tracking-tight mb-2">
            Finaxis
          </h1>
          <p className="text-indigo-200 text-sm font-medium">
            Plataforma Financiera Inteligente
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label htmlFor="email" className="block text-sm font-semibold text-gray-100 mb-1.5 ml-1">Usuario o Email</label>
            <input
              type="text"
              id="email"
              className="mt-1 block w-full px-4 py-3 bg-white/90 border border-white/30 text-gray-900 placeholder-gray-500 rounded-xl shadow-inner focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:bg-white transition-colors text-sm"
              placeholder="tu@correo.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm font-semibold text-gray-100 mb-1.5 ml-1">Contraseña</label>
            <input
              type="password"
              id="password"
              className="mt-1 block w-full px-4 py-3 bg-white/90 border border-white/30 text-gray-900 placeholder-gray-500 rounded-xl shadow-inner focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:bg-white transition-colors text-sm"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center py-3.5 px-4 border border-transparent rounded-xl shadow-lg text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-400 focus:ring-offset-slate-900 transition-all duration-200 transform hover:scale-[1.02] disabled:opacity-50 disabled:hover:scale-100"
            >
              {isLoading ? 'Autenticando...' : 'Iniciar Sesión'}
            </button>
          </div>
        </form>

        {message && (
          <div className={`mt-6 p-4 rounded-xl text-center text-sm font-medium border backdrop-blur-md ${message.includes('exitoso') ? 'bg-green-500/20 text-green-200 border-green-500/30' : 'bg-red-500/20 text-red-200 border-red-500/30 shadow-[0_0_15px_rgba(239,68,68,0.2)]'}`}>
            {message}
          </div>
        )}
      </div>

      {/* Pie de página pequeño */}
      <div className="absolute bottom-6 text-center z-10">
        <p className="text-gray-400 text-xs tracking-wider">
          &copy; {new Date().getFullYear()} Finaxis. Todos los derechos reservados.
        </p>
      </div>
    </main>
  );
}