'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../context/AuthContext';
import { apiService } from '../../lib/apiService';
import { jwtDecode } from 'jwt-decode';

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();

  // --- Estado: Paso 1 (Credenciales) ---
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // --- Estado: Paso 2 (2FA TOTP) ---
  const [show2FA, setShow2FA] = useState(false);
  const [totpCode, setTotpCode] = useState('');
  const [tempToken, setTempToken] = useState(null);
  const [is2FALoading, setIs2FALoading] = useState(false);
  const [totpTimer, setTotpTimer] = useState(30);
  const totpInputRef = useRef(null);

  // Temporizador visual del ciclo TOTP (30 segundos)
  useEffect(() => {
    if (!show2FA) return;
    const interval = setInterval(() => {
      const now = Math.floor(Date.now() / 1000);
      setTotpTimer(30 - (now % 30));
    }, 1000);
    return () => clearInterval(interval);
  }, [show2FA]);

  // Auto-focus en el input de TOTP cuando aparece
  useEffect(() => {
    if (show2FA && totpInputRef.current) {
      setTimeout(() => totpInputRef.current?.focus(), 100);
    }
  }, [show2FA]);

  // --- PASO 1: Envío de credenciales ---
  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage('');

    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const response = await apiService.post('/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });

      const data = response.data;

      // ¿El backend solicita 2FA?
      if (data.requires_2fa && data.temp_token) {
        sessionStorage.setItem('_2fa_temp', data.temp_token);
        setTempToken(data.temp_token);
        setShow2FA(true);
        setMessage('');
        return;
      }

      // Flujo normal (sin 2FA)
      finalizarLogin(data.access_token);

    } catch (error) {
      let errorMessage = 'Credenciales inválidas o error en el servidor.';
      if (error.response?.status === 429) {
        errorMessage = 'Por seguridad, ha superado el límite de intentos. Espere 5 minutos.';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }
      setMessage(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  // --- PASO 2: Verificación del código TOTP ---
  const handleVerify2FA = async (e) => {
    e.preventDefault();
    if (totpCode.length !== 6) return;
    setIs2FALoading(true);
    setMessage('');

    try {
      const token = tempToken || sessionStorage.getItem('_2fa_temp');
      const response = await apiService.post('/auth/verify-2fa', {
        temp_token: token,
        totp_code: totpCode,
      });

      sessionStorage.removeItem('_2fa_temp');
      finalizarLogin(response.data.access_token);

    } catch (error) {
      let errorMessage = 'Código incorrecto o expirado.';
      if (error.response?.status === 429) {
        errorMessage = 'Demasiados intentos. Por seguridad, inicia sesión nuevamente.';
        handleCancelar2FA();
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }
      setMessage(errorMessage);
      setTotpCode('');
      totpInputRef.current?.focus();
    } finally {
      setIs2FALoading(false);
    }
  };

  // Auto-envía cuando se completan los 6 dígitos
  const handleTotpChange = (value) => {
    const cleaned = value.replace(/\D/g, '').slice(0, 6);
    setTotpCode(cleaned);
    if (cleaned.length === 6) {
      setTimeout(() => {
        document.getElementById('btn-verify-2fa')?.click();
      }, 150);
    }
  };

  const handleCancelar2FA = () => {
    sessionStorage.removeItem('_2fa_temp');
    setShow2FA(false);
    setTempToken(null);
    setTotpCode('');
    setMessage('');
  };

  // Completa el login y redirige según rol
  const finalizarLogin = (access_token) => {
    login(access_token);
    setMessage('Inicio de sesión exitoso. Redirigiendo...');
    try {
      const decoded = jwtDecode(access_token);
      const roles = decoded.roles || [];
      const roleNames = roles.map(r => (typeof r === 'string' ? r : r.nombre));
      if (roleNames.includes('contador')) {
        router.push('/portal');
      } else {
        router.push('/');
      }
    } catch {
      router.push('/');
    }
  };

  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center p-4 sm:p-24 overflow-hidden">
      {/* Fondo */}
      <div
        className="absolute inset-0 z-0 bg-cover bg-center bg-no-repeat transition-opacity duration-1000"
        style={{ backgroundImage: "url('https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=75&w=1920&auto=format&fit=crop')" }}
      />
      <div className="absolute inset-0 z-0 bg-gradient-to-br from-indigo-900/90 via-blue-900/80 to-slate-900/95 mix-blend-multiply" />
      <div className="absolute inset-0 z-0 opacity-30">
        <div className="absolute top-0 -left-1/4 w-1/2 h-1/2 bg-blue-500 rounded-full mix-blend-screen filter blur-[150px] animate-blob" />
        <div className="absolute bottom-0 -right-1/4 w-1/2 h-1/2 bg-indigo-600 rounded-full mix-blend-screen filter blur-[150px] animate-blob animation-delay-2000" />
      </div>

      <div className="z-10 w-full max-w-md bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl shadow-[0_8px_32px_0_rgba(0,0,0,0.37)] p-8 sm:p-10 transform transition-all">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-extrabold text-white tracking-tight mb-2">Finaxis</h1>
          <p className="text-indigo-200 text-sm font-medium">
            {show2FA ? 'Verificación de Seguridad' : 'Plataforma Financiera Inteligente'}
          </p>
        </div>

        {/* ====== PASO 1: Formulario de Credenciales ====== */}
        {!show2FA && (
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="email" className="block text-sm font-semibold text-gray-100 mb-1.5 ml-1">Usuario o Email</label>
              <input
                type="text" id="email"
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
                type="password" id="password"
                className="mt-1 block w-full px-4 py-3 bg-white/90 border border-white/30 text-gray-900 placeholder-gray-500 rounded-xl shadow-inner focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:bg-white transition-colors text-sm"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <div className="pt-2">
              <button
                type="submit" disabled={isLoading}
                className="w-full flex justify-center py-3.5 px-4 border border-transparent rounded-xl shadow-lg text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-400 focus:ring-offset-slate-900 transition-all duration-200 transform hover:scale-[1.02] disabled:opacity-50 disabled:hover:scale-100"
              >
                {isLoading ? 'Autenticando...' : 'Iniciar Sesión'}
              </button>
            </div>
          </form>
        )}

        {/* ====== PASO 2: Verificación 2FA / TOTP ====== */}
        {show2FA && (
          <form onSubmit={handleVerify2FA} className="space-y-6">
            {/* Ícono de escudo */}
            <div className="flex flex-col items-center gap-3">
              <div className="w-16 h-16 rounded-full bg-indigo-500/20 border border-indigo-400/40 flex items-center justify-center">
                <svg className="w-8 h-8 text-indigo-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <p className="text-gray-200 text-sm text-center leading-relaxed">
                Abre tu app autenticadora (Google Authenticator, Authy, etc.) e ingresa el código de <strong className="text-white">6 dígitos</strong>.
              </p>
            </div>

            {/* Input del código */}
            <div>
              <label className="block text-sm font-semibold text-gray-100 mb-2 text-center">Código de Autenticación</label>
              <input
                ref={totpInputRef}
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                maxLength={6}
                autoComplete="one-time-code"
                className="block w-full px-4 py-4 bg-white/90 border-2 border-indigo-300 text-gray-900 rounded-xl shadow-inner focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:bg-white transition-colors text-2xl font-mono tracking-[0.5em] text-center"
                placeholder="000000"
                value={totpCode}
                onChange={(e) => handleTotpChange(e.target.value)}
              />
            </div>

            {/* Temporizador visual */}
            <div className="flex items-center justify-center gap-2 text-xs text-indigo-200">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>El código se renueva en <span className={`font-bold ${totpTimer <= 5 ? 'text-red-300' : 'text-white'}`}>{totpTimer}s</span></span>
            </div>

            {/* Botones */}
            <div className="flex gap-3">
              <button
                type="button"
                onClick={handleCancelar2FA}
                className="flex-1 py-3 px-4 border border-white/30 rounded-xl text-sm font-semibold text-gray-200 hover:bg-white/10 transition-all duration-200"
              >
                ← Volver
              </button>
              <button
                id="btn-verify-2fa"
                type="submit"
                disabled={is2FALoading || totpCode.length !== 6}
                className="flex-1 py-3 px-4 border border-transparent rounded-xl shadow-lg text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-400 transition-all duration-200 disabled:opacity-50"
              >
                {is2FALoading ? 'Verificando...' : 'Verificar'}
              </button>
            </div>
          </form>
        )}

        {/* Mensaje de error/éxito */}
        {message && (
          <div className={`mt-6 p-4 rounded-xl text-center text-sm font-medium border backdrop-blur-md ${message.includes('exitoso') ? 'bg-green-500/20 text-green-200 border-green-500/30' : 'bg-red-500/20 text-red-200 border-red-500/30 shadow-[0_0_15px_rgba(239,68,68,0.2)]'}`}>
            {message}
          </div>
        )}
      </div>

      <div className="absolute bottom-6 text-center z-10">
        <p className="text-gray-400 text-xs tracking-wider">
          &copy; {new Date().getFullYear()} Finaxis. Todos los derechos reservados.
        </p>
      </div>
    </main>
  );
}