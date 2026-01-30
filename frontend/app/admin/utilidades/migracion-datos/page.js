'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { FaDatabase, FaExclamationTriangle, FaCheckCircle, FaSpinner, FaBook } from 'react-icons/fa'; // Iconos para feedback visual
import { useAuth } from '../../../context/AuthContext';


import { apiService } from '../../../../lib/apiService';
import ExportacionForm from '../../../components/Migracion/ExportacionForm';
import RestauracionForm from '../../../components/Migracion/RestauracionForm';
import TransformacionForm from '../../../components/Migracion/TransformacionForm';
import LegacyImportForm from '../../../components/Migracion/LegacyImportForm';
import UniversalImportForm from '../../../components/Migracion/UniversalImportForm';

export default function MigracionDatosPage() {
  const { user, authLoading } = useAuth();

  // --- SONDA DE DEPURACIÓN (Solicitada por Usuario) ---
  useEffect(() => {
    if (!authLoading) {
      console.log("--- SONDA MIGRACION PAGE ---");
      console.log("User Object:", user);
      console.log("User Class:", user?.constructor?.name);
      console.log("EmpresaID (Direct):", user?.empresaId);
      console.log("EmpresaID (Snake):", user?.empresa_id);
      console.log("----------------------------");
    }
  }, [user, authLoading]);

  const [maestros, setMaestros] = useState({
    tiposDocumento: [],
    terceros: [],
    cuentas: [],
    centrosCosto: [],
    empresas: [],
  });
  const [empresaActual, setEmpresaActual] = useState(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState('');

  const fetchMaestros = useCallback(async () => {
    if (!user?.empresaId) {
      // CORRECCIÓN: Si no hay empresaId, dejar de cargar y mostrar error
      setIsLoading(false);
      setError("No se ha detectado una empresa activa en su sesión. Por favor recargue la página o contacte a soporte.");
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const results = await Promise.allSettled([
        apiService.get('/tipos-documento/'),
        apiService.get('/terceros/'),
        apiService.get('/plan-cuentas/list-flat/'),
        apiService.get('/centros-costo/get-flat'),
        apiService.get('/empresas/')
      ]);

      const [tiposRes, tercerosRes, cuentasRes, ccRes, empresasRes] = results;

      if (empresasRes.status !== 'fulfilled') {
        if (empresasRes.reason.response && empresasRes.reason.response.status === 403) {
          throw new Error('No tienes los permisos necesarios para acceder a esta herramienta.');
        }
        throw new Error(empresasRes.reason.response?.data?.detail || 'Error fatal cargando los datos iniciales.');
      }
      const empresasData = empresasRes.value.data;

      setMaestros({
        tiposDocumento: tiposRes.status === 'fulfilled' ? tiposRes.value.data : [],
        terceros: tercerosRes.status === 'fulfilled' ? tercerosRes.value.data : [],
        cuentas: cuentasRes.status === 'fulfilled' ? cuentasRes.value.data : [],
        centrosCosto: ccRes.status === 'fulfilled' ? ccRes.value.data : [],
        empresas: empresasData,
      });

      setEmpresaActual(empresasData.find(e => e.id === user.empresaId));

    } catch (err) {
      const errorMsg = err.message || 'Ocurrió un error desconocido.';
      setError(`Error al cargar datos maestros: ${errorMsg}`);
    } finally {
      setIsLoading(false);
    }
  }, [user?.empresaId]);

  useEffect(() => {
    if (!authLoading) {
      fetchMaestros();
    }
  }, [authLoading, fetchMaestros]);

  // --- PANTALLA DE CARGA INICIAL ---
  if (authLoading || isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
        <FaDatabase className="text-indigo-300 text-6xl mb-4 animate-pulse" />
        <p className="text-indigo-600 font-semibold text-lg animate-pulse">
          {authLoading ? 'Verificando credenciales...' : 'Cargando maestros de migración...'}
        </p>
      </div>
    );
  }

  // --- PANTALLA DE ERROR DE CARGA ---
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-6 flex items-center justify-center">
        <div className="bg-white p-8 rounded-xl shadow-lg border border-red-100 max-w-2xl text-center">
          <div className="flex justify-center mb-4">
            <div className="p-4 bg-red-100 rounded-full">
              <FaExclamationTriangle className="text-3xl text-red-500" />
            </div>
          </div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Error de Inicialización</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <div className="flex justify-center">
            <button onClick={() => window.history.back()} className="text-indigo-600 hover:underline">Regresar</button>
          </div>
        </div>
      </div>
    );
  }

  // --- INTERFAZ PRINCIPAL ---
  return (
    <div className="bg-gray-50 p-6 font-sans h-[calc(100vh-80px)] overflow-y-auto pb-32">
      <div className="max-w-7xl mx-auto">

        {/* ENCABEZADO CON JERARQUÍA VISUAL */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
          <div>
            <div className="flex items-center gap-3 mt-3">
              <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                <FaDatabase />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-2">
                  Migración de Datos
                  <button
                    onClick={() => window.open('/manual/capitulo_6_copias.html', '_blank')}
                    className="flex items-center gap-2 px-2 py-1 bg-white border border-indigo-200 text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors font-medium shadow-sm text-sm"
                    title="Ver Manual de Usuario"
                  >
                    <FaBook /> <span className="hidden md:inline">Manual</span>
                  </button>
                </h1>
                <p className="text-gray-500 text-sm">Herramientas de Exportación, Restauración y Transformación Masiva.</p>
              </div>
            </div>
          </div>
        </div>

        {/* ZONA DE NOTIFICACIONES Y ESTADO */}
        <div className="space-y-4 mb-8">
          {/* Indicador de Procesamiento */}
          {isProcessing && (
            <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-r-lg shadow-sm animate-fadeIn flex items-center">
              <FaSpinner className="animate-spin text-blue-600 mr-3 text-xl" />
              <div>
                <p className="font-bold text-blue-800">Procesando Solicitud...</p>
                <p className="text-sm text-blue-600">Por favor espere, esto puede tomar unos momentos.</p>
              </div>
            </div>
          )}

          {/* Mensajes de Éxito/Info */}
          {message && (
            <div className="bg-green-50 border-l-4 border-green-500 p-4 rounded-r-lg shadow-sm animate-fadeIn flex items-center">
              <FaCheckCircle className="text-green-600 mr-3 text-xl" />
              <div>
                <p className="font-bold text-green-800">Resultado del Proceso</p>
                <p className="text-sm text-green-700">{message}</p>
              </div>
            </div>
          )}
        </div>

        {/* CONTENEDOR DE HERRAMIENTAS */}
        <div className="space-y-8">

          {/* Sección 1: Exportación */}
          <section className="animate-fadeIn" style={{ animationDelay: '0.1s' }}>
            <ExportacionForm
              maestros={maestros}
              empresaActual={empresaActual}
              isProcessing={isProcessing}
              setIsProcessing={setIsProcessing}
              setMessage={setMessage}
              setError={setError}
            />
          </section>

          {/* Sección 2: Restauración */}
          <section className="animate-fadeIn" style={{ animationDelay: '0.2s' }}>
            <RestauracionForm
              empresas={maestros.empresas.filter(e => e.id === user.empresaId)}
              isProcessing={isProcessing}
              setIsProcessing={setIsProcessing}
              setMessage={setMessage}
              setError={setError}
            />
          </section>

          {/* Sección 3: Transformación */}
          <section className="animate-fadeIn" style={{ animationDelay: '0.3s' }}>
            <TransformacionForm
              tiposDocumento={maestros.tiposDocumento}
            />
          </section>

          {/* Sección 4: Importación Legacy (TXT - DOS) */}
          <section className="animate-fadeIn" style={{ animationDelay: '0.4s' }}>
            <LegacyImportForm
              maestros={maestros}
              empresaActual={empresaActual}
              isProcessing={isProcessing}
              setIsProcessing={setIsProcessing}
              setMessage={setMessage}
              setError={setError}
            />
          </section>

          {/* Sección 5: Importación Universal (Excel - Nuevo Estándar) */}
          <section className="animate-fadeIn" style={{ animationDelay: '0.5s' }}>
            <UniversalImportForm
              maestros={maestros}
              empresaActual={empresaActual}
              isProcessing={isProcessing}
              setIsProcessing={setIsProcessing}
              setMessage={setMessage}
              setError={setError}
            />
          </section>

        </div>

      </div>
    </div>
  );
}