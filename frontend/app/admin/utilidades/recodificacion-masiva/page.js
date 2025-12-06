'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  FaExchangeAlt,
  FaUserTag,
  FaLayerGroup,
  FaListOl,
  FaExclamationTriangle,
  FaCheckCircle,
  FaSpinner,
  FaArrowRight,
  FaBook
} from 'react-icons/fa';

import { useAuth } from '../../../context/AuthContext';
import BotonRegresar from '../../../components/BotonRegresar';
import { apiService } from '../../../../lib/apiService';

export default function RecodificacionMasivaPage() {
  const { user, authLoading } = useAuth();

  const [activeTab, setActiveTab] = useState('cuenta');
  const [tiposDocumento, setTiposDocumento] = useState([]);
  const [cuentas, setCuentas] = useState([]);
  const [terceros, setTerceros] = useState([]);
  const [centrosCosto, setCentrosCosto] = useState([]);

  const [filtros, setFiltros] = useState({ tipoDocId: '', numero: '', fechaInicio: '', fechaFin: '' });
  const [recodificacion, setRecodificacion] = useState({ origenId: '', destinoId: '' });

  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');

  // --- LÓGICA DE CARGA (INTACTA) ---
  const fetchMaestros = useCallback(async () => {
    if (authLoading || !user) return;
    setIsLoading(true);
    setError(null);
    try {
      const results = await Promise.allSettled([
        apiService.get('/tipos-documento/'),
        apiService.get('/plan-cuentas/list-flat/'),
        apiService.get('/terceros/'),
        apiService.get('/centros-costo/get-flat?permite_movimiento=true')
      ]);

      const [tdRes, cuentasRes, tercerosRes, ccRes] = results;

      setTiposDocumento(tdRes.status === 'fulfilled' ? tdRes.value.data : []);
      setCuentas(cuentasRes.status === 'fulfilled' ? cuentasRes.value.data : []);
      setTerceros(tercerosRes.status === 'fulfilled' ? (tercerosRes.value.data.terceros || tercerosRes.value.data) : []);
      setCentrosCosto(ccRes.status === 'fulfilled' ? ccRes.value.data : []);

    } catch (err) {
      setError(err.response?.data?.detail || 'Falló la carga de datos maestros.');
    } finally {
      setIsLoading(false);
    }
  }, [user, authLoading]);

  useEffect(() => {
    fetchMaestros();
  }, [fetchMaestros]);

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setFiltros({ tipoDocId: '', numero: '', fechaInicio: '', fechaFin: '' });
    setRecodificacion({ origenId: '', destinoId: '' });
    setError(null);
    setSuccessMessage('');
  };

  const handleFiltroChange = (e) => setFiltros(prev => ({ ...prev, [e.target.name]: e.target.value }));
  const handleRecodificacionChange = (e) => setRecodificacion(prev => ({ ...prev, [e.target.name]: e.target.value }));

  // --- LÓGICA DE ENVÍO (INTACTA) ---
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccessMessage('');

    const endpointPath = activeTab.replace(/([A-Z])/g, '-$1').toLowerCase();
    const endpoint = `/utilidades/recodificar-${endpointPath}`;

    const { origenId, destinoId } = recodificacion;
    const itemType = activeTab === 'cuenta' ? 'cuenta' : activeTab === 'tercero' ? 'tercero' : 'centro de costo';

    if (!filtros.tipoDocId || !origenId || !destinoId) {
      setError(`Error: Debes seleccionar un Tipo de Documento, un ${itemType} de Origen y un ${itemType} de Destino.`);
      return;
    }
    if (origenId === destinoId) {
      setError(`Error: El ${itemType} de origen y destino no pueden ser el mismo.`);
      return;
    }
    if (!window.confirm(`¡ADVERTENCIA!\n\nEstás a punto de cambiar masivamente el ${itemType.toUpperCase()}.\nEsta acción NO SE PUEDE DESHACER.\n\n¿Estás seguro de que deseas continuar?`)) return;

    setIsSubmitting(true);
    try {
      const filtrosLimpios = { ...filtros };
      if (!filtrosLimpios.numero) delete filtrosLimpios.numero;
      if (!filtrosLimpios.fechaInicio) delete filtrosLimpios.fechaInicio;
      if (!filtrosLimpios.fechaFin) delete filtrosLimpios.fechaFin;

      const payload = {
        filtros: {
          ...filtrosLimpios,
          tipoDocId: parseInt(filtros.tipoDocId, 10),
        },
        recodificacion: {
          origenId: parseInt(recodificacion.origenId, 10),
          destinoId: parseInt(recodificacion.destinoId, 10),
        }
      };

      const response = await apiService.post(endpoint, payload);

      setSuccessMessage(response.data.message);
      setRecodificacion({ origenId: '', destinoId: '' });

    } catch (err) {
      let errorMessage = 'Ocurrió un error desconocido en el servidor.';
      if (err.response && err.response.data) {
        const detail = err.response.data.detail;
        if (typeof detail === 'string') {
          errorMessage = detail;
        } else if (Array.isArray(detail)) {
          errorMessage = detail.map(e => `${e.loc.join(' -> ')}: ${e.msg}`).join('; ');
        }
      }
      setError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  // --- RENDERIZADO DEL FORMULARIO ---
  const renderCurrentForm = () => {
    let origenDestinoOptions = [];
    let label = '';
    let Icono = FaListOl;

    if (activeTab === 'cuenta') {
      origenDestinoOptions = cuentas;
      label = 'Cuenta Contable';
      Icono = FaListOl;
    } else if (activeTab === 'tercero') {
      origenDestinoOptions = terceros;
      label = 'Tercero';
      Icono = FaUserTag;
    } else if (activeTab === 'centroCosto') {
      origenDestinoOptions = centrosCosto;
      label = 'Centro de Costo';
      Icono = FaLayerGroup;
    }

    const getOptionLabel = (o) => {
      switch (activeTab) {
        case 'cuenta': return `${o.codigo} - ${o.nombre}`;
        case 'tercero': return o.razon_social;
        case 'centroCosto': return o.nombre;
        default: return o.id;
      }
    };

    // Estilos comunes
    const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
    const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none";
    const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white";

    return (
      <form onSubmit={handleSubmit} className="space-y-8 animate-fadeIn">

        {/* SECCIÓN 1: FILTROS */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <div className="flex items-center gap-2 mb-6 border-b border-gray-100 pb-2">
            <span className="bg-indigo-100 text-indigo-600 w-8 h-8 flex items-center justify-center rounded-full font-bold text-sm">1</span>
            <h2 className="text-lg font-bold text-gray-800">Definir Alcance (Filtros)</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="col-span-1 md:col-span-2">
              <label className={labelClass}>Tipo de Documento <span className="text-red-500">*</span></label>
              <select name="tipoDocId" value={filtros.tipoDocId} onChange={handleFiltroChange} required className={selectClass}>
                <option value="">Seleccione Tipo de Documento...</option>
                {tiposDocumento.map(td => <option key={td.id} value={td.id}>{td.nombre}</option>)}
              </select>
              <p className="text-xs text-gray-400 mt-1">Solo se modificarán los documentos de este tipo.</p>
            </div>

            <div>
              <label className={labelClass}>Por Número (Opcional)</label>
              <input type="text" name="numero" placeholder="Ej: 1050 (Dejar vacío para todos)" value={filtros.numero} onChange={handleFiltroChange} className={inputClass} />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelClass}>Desde Fecha</label>
                <input type="date" name="fechaInicio" value={filtros.fechaInicio} onChange={handleFiltroChange} className={inputClass} />
              </div>
              <div>
                <label className={labelClass}>Hasta Fecha</label>
                <input type="date" name="fechaFin" value={filtros.fechaFin} onChange={handleFiltroChange} className={inputClass} />
              </div>
            </div>
          </div>
        </div>

        {/* SECCIÓN 2: TRANSFORMACIÓN */}
        <div className="bg-orange-50 p-6 rounded-xl shadow-sm border border-orange-100">
          <div className="flex items-center gap-2 mb-6 border-b border-orange-200 pb-2">
            <span className="bg-orange-200 text-orange-700 w-8 h-8 flex items-center justify-center rounded-full font-bold text-sm">2</span>
            <h2 className="text-lg font-bold text-gray-800">Definir Transformación</h2>
          </div>

          <div className="flex flex-col md:flex-row items-center gap-4 justify-center">

            {/* ORIGEN */}
            <div className="w-full md:w-5/12">
              <label className="block text-xs font-bold text-orange-800 uppercase mb-1 tracking-wide">
                Reemplazar ESTE {label}:
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                  <Icono />
                </div>
                <select name="origenId" value={recodificacion.origenId} onChange={handleRecodificacionChange} required className={`${selectClass} pl-10 border-orange-300 focus:ring-orange-500`}>
                  <option value="">Seleccione Origen...</option>
                  {origenDestinoOptions.map(o => <option key={o.id} value={o.id}>{getOptionLabel(o)}</option>)}
                </select>
              </div>
            </div>

            {/* FLECHA */}
            <div className="w-full md:w-2/12 flex justify-center py-2 md:py-0">
              <div className="bg-white p-3 rounded-full shadow-md text-orange-500 border border-orange-200">
                <FaArrowRight className="text-xl hidden md:block" />
                <FaExchangeAlt className="text-xl md:hidden" />
              </div>
            </div>

            {/* DESTINO */}
            <div className="w-full md:w-5/12">
              <label className="block text-xs font-bold text-green-700 uppercase mb-1 tracking-wide">
                POR ESTE NUEVO {label}:
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                  <Icono />
                </div>
                <select name="destinoId" value={recodificacion.destinoId} onChange={handleRecodificacionChange} required className={`${selectClass} pl-10 border-green-300 focus:ring-green-500`}>
                  <option value="">Seleccione Destino...</option>
                  {origenDestinoOptions.map(o => <option key={o.id} value={o.id}>{getOptionLabel(o)}</option>)}
                </select>
              </div>
            </div>

          </div>
        </div>

        {/* BOTÓN DE ACCIÓN */}
        <div className="flex justify-end pt-4 border-t border-gray-200 mt-4">
          <button
            type="submit"
            disabled={isSubmitting || isLoading}
            className={`
                px-8 py-3 rounded-lg shadow-lg font-bold text-white text-lg transition-all transform hover:-translate-y-0.5
                flex items-center gap-2
                ${isSubmitting ? 'bg-gray-400 cursor-not-allowed' : 'bg-red-600 hover:bg-red-700 hover:shadow-red-200'}
            `}
          >
            {isSubmitting ? (
              <>
                <FaSpinner className="animate-spin" /> Procesando...
              </>
            ) : (
              <>
                <FaExchangeAlt /> Ejecutar Recodificación Masiva
              </>
            )}
          </button>
        </div>
      </form>
    );
  };

  // --- PANTALLA DE CARGA INICIAL ---
  if (authLoading || isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
        <FaExchangeAlt className="text-indigo-300 text-6xl mb-4 animate-pulse" />
        <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando maestros...</p>
      </div>
    );
  }

  // --- RENDER PRINCIPAL ---
  return (
    <div className="min-h-screen bg-gray-50 p-6 font-sans">
      <div className="max-w-5xl mx-auto">

        {/* ENCABEZADO */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
          <div>
            <BotonRegresar />
            <div className="flex items-center gap-3 mt-3">
              <div className="p-2 bg-red-100 rounded-lg text-red-600">
                <FaExchangeAlt />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-800">Recodificación Masiva</h1>
                <p className="text-gray-500 text-sm">Herramienta de corrección de registros contables.</p>
              </div>
            </div>
          </div>
          <button
            onClick={() => window.open('/manual?file=capitulo_13_recodificacion.md', '_blank')}
            className="btn btn-ghost text-indigo-600 hover:bg-indigo-50 gap-2 flex items-center"
            title="Ver Manual de Usuario"
          >
            <FaBook className="text-lg" /> <span className="font-bold hidden md:inline">Manual</span>
          </button>
        </div>

        {/* TABS (DISEÑO CARD SELECTORA) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          {[
            { id: 'cuenta', label: 'Cambiar Cuenta', icon: FaListOl },
            { id: 'tercero', label: 'Cambiar Tercero', icon: FaUserTag },
            { id: 'centroCosto', label: 'Cambiar C. Costo', icon: FaLayerGroup },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id)}
              className={`
                            flex items-center justify-center gap-3 p-4 rounded-xl border transition-all duration-200
                            ${activeTab === tab.id
                  ? 'bg-white border-indigo-500 ring-2 ring-indigo-100 shadow-md text-indigo-700'
                  : 'bg-white border-gray-200 text-gray-500 hover:bg-gray-50 hover:border-indigo-200'}
                        `}
            >
              <tab.icon className="text-xl" />
              <span className="font-bold">{tab.label}</span>
            </button>
          ))}
        </div>

        {/* CONTENEDOR PRINCIPAL */}
        <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-8 animate-fadeIn">

          {/* MENSAJES DE ESTADO */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded-r-lg flex items-start gap-3 animate-pulse">
              <FaExclamationTriangle className="mt-1 text-xl" />
              <div>
                <p className="font-bold">Error de Validación</p>
                <p className="text-sm">{error}</p>
              </div>
            </div>
          )}

          {successMessage && (
            <div className="mb-6 p-4 bg-green-50 border-l-4 border-green-500 text-green-700 rounded-r-lg flex items-start gap-3">
              <FaCheckCircle className="mt-1 text-xl" />
              <div>
                <p className="font-bold">Operación Exitosa</p>
                <p className="text-sm">{successMessage}</p>
              </div>
            </div>
          )}

          {/* FORMULARIO */}
          {renderCurrentForm()}

        </div>
      </div>
    </div>
  );
}