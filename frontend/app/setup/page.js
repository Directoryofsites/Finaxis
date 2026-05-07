'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Rocket, Store, User, Lock, Calendar, CheckCircle } from 'lucide-react';
import toast, { Toaster } from 'react-hot-toast';

export default function SetupPage() {
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  
  const [formData, setFormData] = useState({
    razon_social: '',
    nit: '',
    fecha_inicio: '2026-01-01',
    admin_email: '',
    admin_password: '',
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/setup/initialize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (response.ok) {
        toast.success('¡Finaxis configurado con éxito! Bienvenido.');
        setTimeout(() => router.push('/login'), 2000);
      } else {
        toast.error(data.detail || 'Error al inicializar el sistema');
      }
    } catch (error) {
      toast.error('Error de conexión con el servidor');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 p-4 font-sans">
      <Toaster position="top-right" />
      
      <div className="max-w-2xl w-full bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col md:flex-row">
        {/* Lado Izquierdo - Bienvenida */}
        <div className="md:w-1/3 bg-emerald-600 p-8 flex flex-col items-center justify-center text-white text-center">
          <div className="bg-white/20 p-4 rounded-2xl mb-6">
            <Rocket size={48} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold mb-2">¡Hola!</h1>
          <p className="text-emerald-50 text-sm">Estás a un paso de comenzar tu experiencia con Finaxis.</p>
        </div>

        {/* Lado Derecho - Formulario */}
        <div className="md:w-2/3 p-8 bg-white">
          <div className="mb-8">
            <h2 className="text-xl font-bold text-slate-800">Configuración Inicial</h2>
            <p className="text-slate-500 text-sm">Completa los datos de tu empresa y administrador.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Nombre de la Empresa</label>
                <input 
                  required
                  name="razon_social"
                  value={formData.razon_social}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none transition-all"
                  placeholder="Empresa S.A.S"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">NIT</label>
                <input 
                  required
                  name="nit"
                  value={formData.nit}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none transition-all"
                  placeholder="900.123.456-1"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Fecha Inicio Operaciones</label>
              <input 
                required
                type="date"
                name="fecha_inicio"
                value={formData.fecha_inicio}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none transition-all"
              />
            </div>

            <div className="pt-4 border-t border-slate-100">
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Email del Administrador</label>
              <input 
                required
                type="email"
                name="admin_email"
                value={formData.admin_email}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none transition-all"
                placeholder="admin@correo.com"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Contraseña Maestro</label>
              <input 
                required
                type="password"
                name="admin_password"
                value={formData.admin_password}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none transition-all"
                placeholder="••••••••"
              />
            </div>

            <button 
              type="submit"
              disabled={loading}
              className="w-full mt-6 bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 rounded-xl shadow-lg shadow-emerald-200 transition-all transform hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50"
            >
              {loading ? 'Inicializando...' : 'Finalizar y Comenzar'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
