'use client';

import React, { useState, useEffect } from 'react';
import {
  FaDownload,
  FaDatabase,
  FaFileExport,
  FaCheckSquare,
  FaSquare,
  FaCalendarAlt,
  FaFilter,
  FaBuilding,
  FaClock,
  FaSave,
  FaTimes,
  FaFolderOpen
} from 'react-icons/fa';
import { exportarDatos, apiService } from '../../../lib/apiService';
// Note: apiService used for config, exportarDatos usually in utilidadesService but we can use apiService directly or keep import if invalid. 
// Correcting imports based on context:
import { exportarDatos as exportarDatosService } from '../../../lib/utilidadesService';

// --- ESTILOS REUSABLES (Manual v2.0) ---
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white";
const checkboxClass = "h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded cursor-pointer mr-2";

export default function ExportacionForm({
  maestros,
  empresaActual,
  isProcessing,
  setIsProcessing,
  setMessage,
  setError
}) {
  const initialState = {
    paquetes: {
      maestros: {
        plan_cuentas: false,
        terceros: false,
        centros_costo: false,
        tipos_documento: false,
        bodegas: false,
        grupos_inventario: false,
        tasas_impuesto: false,
        productos: false,
      },
      modulos_especializados: {
        propiedad_horizontal: false,
        activos_fijos: false,
        favoritos: false,
        // --- NUEVOS MÓDULOS AGREGADOS ---
        cotizaciones: false,
        produccion: false,
        conciliacion_bancaria: false,
        nomina: false
      },
      transacciones_contabilidad: false,
      transacciones_inventario: false,
      configuraciones: {
        plantillas_documentos: false,
        libreria_conceptos: false
      }
    },
    tipoDocId: '',
    numero: '',
    fechaInicio: '',
    fechaFin: '',
    terceroId: '',
    cuentaId: '',
    centroCostoId: '',
    conceptoKeyword: '',
    valorOperador: 'mayor',
    valorMonto: ''
  };

  const [filtros, setFiltros] = useState(initialState);

  // ... [AUTO CONFIG STATE AND EFFECT REMAIN UNCHANGED] ...
  const [showAutoModal, setShowAutoModal] = useState(false);
  const [autoConfig, setAutoConfig] = useState({
    enabled: false,
    hora_ejecucion: '02:00',
    ruta_local: 'C:/Backups_Finaxis',
    dias_retencion: 30
  });

  useEffect(() => {
    // Cargar config actual al montar
    const loadConfig = async () => {
      try {
        const res = await apiService.get('/utilidades/backup-auto-config');
        if (res.data) setAutoConfig(res.data);
      } catch (e) {
        console.error("Error loading auto backup config", e);
      }
    };
    loadConfig();
  }, []);

  const saveAutoConfig = async () => {
    try {
      await apiService.post('/utilidades/backup-auto-config', autoConfig);
      alert("Configuración Guardada Exitosamente");
      setShowAutoModal(false);
    } catch (e) {
      alert("Error guardando configuración");
    }
  };

  const handleFiltroChange = (e) => {
    const { name, value } = e.target;
    setFiltros(prev => ({ ...prev, [name]: value }));
  };

  const handlePaqueteChange = (e) => {
    const { name, checked, dataset } = e.target;
    const { category } = dataset;

    if (category === 'root') {
      // Manejar campos directos de paquetes (transacciones_contabilidad, etc)
      setFiltros(p => ({ ...p, paquetes: { ...p.paquetes, [name]: checked } }));
    } else {
      setFiltros(prev => ({
        ...prev,
        paquetes: {
          ...prev.paquetes,
          [category]: {
            ...prev.paquetes[category],
            [name]: checked,
          }
        }
      }));
    }
  };

  const handleExportar = async () => {
    setIsProcessing(true);
    setMessage('');
    setError('');
    try {
      // 1. Limpieza de datos (Convertir '' a null para evitar error 422 en backend)
      const cleanFiltros = { ...filtros };
      ['tipoDocId', 'terceroId', 'cuentaId', 'centroCostoId', 'valorMonto'].forEach(field => {
        if (cleanFiltros[field] === '') cleanFiltros[field] = null;
        else if (cleanFiltros[field]) cleanFiltros[field] = Number(cleanFiltros[field]);
      });
      ['fechaInicio', 'fechaFin', 'numero', 'conceptoKeyword', 'valorOperador'].forEach(field => {
        if (cleanFiltros[field] === '') cleanFiltros[field] = null;
      });

      // 2. Estructurar payload
      const payload = {
        ...cleanFiltros,
        paquetes: {
          ...cleanFiltros.paquetes,
          transacciones: cleanFiltros.paquetes.transacciones_contabilidad || cleanFiltros.paquetes.transacciones_inventario
        }
      };

      await exportarDatosService(payload);
      setMessage('Backup generado exitosamente. La descarga iniciará en breve.');
    } catch (err) {
      console.error("Error Export:", err);
      let errorMsg = err.message;

      // Mejorar mensaje de error de validación (422)
      if (err.response?.data?.detail) {
        if (Array.isArray(err.response.data.detail)) {
          errorMsg = err.response.data.detail.map(e => `${e.loc.join('.')}: ${e.msg}`).join(' | ');
        } else {
          errorMsg = err.response.data.detail;
        }
      }

      setError('Error generando el backup: ' + errorMsg);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* HEADER EXPORTACIÓN */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 rounded-2xl p-8 text-white shadow-xl relative overflow-hidden">
        <div className="relative z-10">
          <h2 className="text-3xl font-bold flex items-center gap-3 mb-2">
            <FaFileExport className="text-blue-200" /> Asistente de Exportación
          </h2>
          <p className="text-blue-100 max-w-2xl text-lg">
            Seleccione los módulos y datos que desea incluir en su copia de seguridad.
            Puede generar copias parciales o completas según su necesidad.
          </p>

          <button
            onClick={() => setShowAutoModal(true)}
            className="mt-6 bg-white/10 hover:bg-white/20 text-white border border-white/30 px-4 py-2 rounded-lg backdrop-blur-sm transition-all flex items-center gap-2 text-sm font-bold"
          >
            <FaClock /> Configurar Copias Automáticas
          </button>
        </div>
        <div className="absolute right-0 top-0 h-full w-1/3 bg-white/5 skew-x-12 transform translate-x-12"></div>
      </div>

      {/* ERROR / MESSAGE */}
      {/* Estos son manejados por el componente padre, pero si quisiéramos mostrarlos aquí... */}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

        {/* COLUMNA 1: SELETOR DE PAQUETES */}
        <div className="bg-white p-6 rounded-xl shadow-lg border border-gray-100 space-y-6 h-fit">
          {/* LOGICA DE SELECCION MASIVA */}
          <div className="flex items-center justify-between mb-4 pb-2 border-b border-gray-100">
            <div className="flex items-center gap-2">
              <FaCheckSquare className="text-blue-600" />
              <h3 className="font-bold text-gray-700">Paquetes de Datos</h3>
            </div>
            <button
              type="button"
              onClick={() => {
                const allSelected =
                  Object.values(filtros.paquetes.maestros).every(v => v) &&
                  Object.values(filtros.paquetes.modulos_especializados).every(v => v) &&
                  Object.values(filtros.paquetes.configuraciones).every(v => v) &&
                  filtros.paquetes.transacciones_contabilidad &&
                  filtros.paquetes.transacciones_inventario;

                const newState = !allSelected;

                setFiltros(prev => {
                  const newMaestros = {};
                  Object.keys(prev.paquetes.maestros).forEach(k => newMaestros[k] = newState);

                  const newModulos = {};
                  Object.keys(prev.paquetes.modulos_especializados).forEach(k => newModulos[k] = newState);

                  const newConfig = {};
                  Object.keys(prev.paquetes.configuraciones).forEach(k => newConfig[k] = newState);

                  return {
                    ...prev,
                    paquetes: {
                      ...prev.paquetes,
                      maestros: newMaestros,
                      modulos_especializados: newModulos,
                      configuraciones: newConfig,
                      transacciones_contabilidad: newState,
                      transacciones_inventario: newState
                    }
                  };
                });
              }}
              className="text-xs font-bold text-indigo-600 hover:bg-indigo-50 px-3 py-1 rounded-full border border-indigo-200 transition-colors"
            >
              {
                (Object.values(filtros.paquetes.maestros).every(v => v) &&
                  Object.values(filtros.paquetes.modulos_especializados).every(v => v) &&
                  filtros.paquetes.transacciones_contabilidad &&
                  filtros.paquetes.transacciones_inventario)
                  ? 'Desmarcar Todos' : 'Marcar Todos'
              }
            </button>
          </div>

          {/* Maestros */}
          <div className="bg-blue-50 p-5 rounded-xl border border-blue-100">
            <h3 className="font-bold text-blue-800 mb-3 flex items-center gap-2">
              <FaDatabase className="text-blue-600" /> Maestros Generales
            </h3>
            <div className="grid grid-cols-2 gap-y-2 gap-x-4">
              {Object.keys(filtros.paquetes.maestros).map(key => (
                <label key={key} className="flex items-center cursor-pointer hover:text-blue-800 transition-colors">
                  <input type="checkbox" name={key} data-category="maestros" checked={filtros.paquetes.maestros[key]} onChange={handlePaqueteChange} className={checkboxClass} />
                  <span className="text-sm capitalize">{key.replace(/_/g, ' ')}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Módulos Especializados (NUEVO) */}
          <div className="bg-indigo-50 p-5 rounded-xl border border-indigo-200">
            <h3 className="font-bold text-indigo-800 mb-3 flex items-center gap-2">
              <FaDatabase className="text-indigo-600" /> Módulos Especializados
            </h3>
            <div className="space-y-2 pl-1">
              {Object.keys(filtros.paquetes.modulos_especializados).map(key => {
                const descriptions = {
                  propiedad_horizontal: "Propiedad Horizontal - Torres, unidades, conceptos y configuraciones",
                  activos_fijos: "Activos Fijos - Categorías, activos y novedades",
                  favoritos: "Favoritos - Menús y accesos rápidos de usuarios",
                  cotizaciones: "Cotizaciones - Cotizaciones maestras y sus detalles",
                  produccion: "Producción - Recetas, órdenes, recursos e insumos",
                  conciliacion_bancaria: "Conciliación Bancaria - Configuraciones, sesiones y movimientos",
                  nomina: "Nómina - Configuración, empleados, tipos y documentos"
                };

                return (
                  <label key={key} className="flex items-start cursor-pointer hover:text-indigo-800 transition-colors">
                    <input
                      type="checkbox"
                      name={key}
                      data-category="modulos_especializados"
                      checked={filtros.paquetes.modulos_especializados[key]}
                      onChange={handlePaqueteChange}
                      className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded cursor-pointer mr-2 mt-0.5"
                    />
                    <div>
                      <span className="text-sm font-bold capitalize">{key.replace(/_/g, ' ')}</span>
                      <p className="text-xs text-indigo-600 mt-0.5">{descriptions[key]}</p>
                    </div>
                  </label>
                );
              })}
            </div>
          </div>

          {/* Configuraciones */}
          <div className="bg-gray-50 p-5 rounded-xl border border-gray-200">
            <h3 className="font-bold text-gray-700 mb-3 flex items-center gap-2">
              <FaDatabase className="text-amber-500" /> Configuraciones
            </h3>
            <div className="space-y-2 pl-1">
              {Object.keys(filtros.paquetes.configuraciones).map(key => (
                <label key={key} className="flex items-center cursor-pointer hover:text-amber-600 transition-colors">
                  <input type="checkbox" name={key} data-category="configuraciones" checked={filtros.paquetes.configuraciones[key]} onChange={handlePaqueteChange} className={checkboxClass} />
                  <span className="text-sm capitalize">{key.replace(/_/g, ' ')}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Transacciones (Switches Separados) */}
          <div className="space-y-4">
            {/* 1. Contabilidad */}
            <div className={`p-4 rounded-xl border transition-all duration-300 ${filtros.paquetes.transacciones_contabilidad ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'}`}>
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  name="transacciones_contabilidad"
                  data-category="root"
                  checked={filtros.paquetes.transacciones_contabilidad}
                  onChange={handlePaqueteChange}
                  className="h-5 w-5 text-green-600 focus:ring-green-500 border-gray-300 rounded mr-3"
                />
                <span className={`font-bold text-md ${filtros.paquetes.transacciones_contabilidad ? 'text-green-700' : 'text-gray-600'}`}>
                  Movimientos Contables (Asientos)
                </span>
              </label>
              <p className="text-xs text-gray-500 mt-1 ml-8">
                Exporta asientos de diario, facturas y recibos contables. Necesario para Balances.
              </p>
            </div>

            {/* 2. Inventario */}
            <div className={`p-4 rounded-xl border transition-all duration-300 ${filtros.paquetes.transacciones_inventario ? 'bg-teal-50 border-teal-200' : 'bg-gray-50 border-gray-200'}`}>
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  name="transacciones_inventario"
                  data-category="root"
                  checked={filtros.paquetes.transacciones_inventario}
                  onChange={handlePaqueteChange}
                  className="h-5 w-5 text-teal-600 focus:ring-teal-500 border-gray-300 rounded mr-3"
                />
                <span className={`font-bold text-md ${filtros.paquetes.transacciones_inventario ? 'text-teal-700' : 'text-gray-600'}`}>
                  Movimientos de Inventario (Kardex)
                </span>
              </label>
              <p className="text-xs text-gray-500 mt-1 ml-8">
                Exporta entradas, salidas y costos de inventario. Necesario para Valuación de Stock.
              </p>
            </div>
          </div>
        </div>

        {/* COLUMNA 2 y 3: FILTROS AVANZADOS (Condicional) */}
        <div className={`lg:col-span-2 p-6 rounded-xl border border-gray-200 transition-all duration-300 ${!(filtros.paquetes.transacciones_contabilidad || filtros.paquetes.transacciones_inventario) ? 'bg-gray-50 opacity-60 pointer-events-none grayscale' : 'bg-white shadow-sm'}`}>
          <div className="flex items-center gap-2 mb-6 pb-2 border-b border-gray-100">
            <FaFilter className="text-gray-400" />
            <h3 className="font-bold text-gray-700">Filtros de Transacciones</h3>
            <span className="text-xs bg-gray-100 text-gray-500 px-2 py-1 rounded-full ml-auto">Opcional</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <label className={labelClass}>Tipo de Documento</label>
                <select name="tipoDocId" value={filtros.tipoDocId} onChange={handleFiltroChange} className={inputClass} disabled={!(filtros.paquetes.transacciones_contabilidad || filtros.paquetes.transacciones_inventario)}>

                  <option value="">Todos</option>
                  {maestros.tiposDocumento.map(t => <option key={t.id} value={t.id}>{t.nombre}</option>)}
                </select>
              </div>
              <div>
                <label className={labelClass}>Tercero</label>
                <select name="terceroId" value={filtros.terceroId} onChange={handleFiltroChange} className={inputClass} disabled={!filtros.paquetes.transacciones}>
                  <option value="">Todos</option>
                  {maestros.terceros.map(t => <option key={t.id} value={t.id}>{t.razon_social}</option>)}
                </select>
              </div>
              <div>
                <label className={labelClass}>Cuenta Contable</label>
                <select name="cuentaId" value={filtros.cuentaId} onChange={handleFiltroChange} className={inputClass} disabled={!filtros.paquetes.transacciones}>
                  <option value="">Todas</option>
                  {maestros.cuentas.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
                </select>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className={labelClass}>Centro de Costo</label>
                <select name="centroCostoId" value={filtros.centroCostoId} onChange={handleFiltroChange} className={inputClass} disabled={!filtros.paquetes.transacciones}>
                  <option value="">Todos</option>
                  {maestros.centrosCosto.map(c => <option key={c.id} value={c.id}>{c.nombre}</option>)}
                </select>
              </div>
              <div>
                <label className={labelClass}>Rango de Fechas</label>
                <div className="flex gap-2">
                  <div className="relative w-full">
                    <input type="date" name="fechaInicio" value={filtros.fechaInicio} onChange={handleFiltroChange} className={inputClass} disabled={!filtros.paquetes.transacciones} />
                    <FaCalendarAlt className="absolute right-3 top-3 text-gray-400 pointer-events-none" />
                  </div>
                  <div className="relative w-full">
                    <input type="date" name="fechaFin" value={filtros.fechaFin} onChange={handleFiltroChange} className={inputClass} disabled={!filtros.paquetes.transacciones} />
                    <FaCalendarAlt className="absolute right-3 top-3 text-gray-400 pointer-events-none" />
                  </div>
                </div>
              </div>
              <div>
                <label className={labelClass}>Palabra Clave (Concepto)</label>
                <input type="text" name="conceptoKeyword" value={filtros.conceptoKeyword} onChange={handleFiltroChange} placeholder="Ej: Arriendo..." className={inputClass} disabled={!filtros.paquetes.transacciones} />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="flex justify-end mt-8 pt-6 border-t border-gray-100">
        <button
          type="button"
          onClick={handleExportar}
          disabled={isProcessing}
          className={`
                px-8 py-3 rounded-lg shadow-lg font-bold text-white text-lg transition-all transform hover:-translate-y-0.5 flex items-center gap-2
                ${isProcessing ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 hover:shadow-blue-200'}
            `}
        >
          {isProcessing ? <><FaDatabase className="animate-pulse" /> Procesando...</> : <><FaDownload /> Generar Backup JSON</>}
        </button>
      </div>

      {/* MODAL CONFIGURACIÓN AUTOMÁTICA */}
      {showAutoModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden animate-fadeIn">
            <div className="bg-indigo-600 p-4 flex justify-between items-center text-white">
              <h3 className="font-bold flex items-center gap-2"><FaClock /> Configurar Copias Automáticas</h3>
              <button onClick={() => setShowAutoModal(false)} className="hover:text-indigo-200"><FaTimes /></button>
            </div>
            <div className="p-6 space-y-4">
              <p className="text-sm text-gray-500 mb-4">
                El sistema generará automáticamente una copia completa de seguridad (todos los módulos) a la hora y ruta indicadas.
              </p>

              <label className="flex items-center gap-3 p-3 border rounded-lg hover:bg-gray-50 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoConfig.enabled}
                  onChange={e => setAutoConfig({ ...autoConfig, enabled: e.target.checked })}
                  className="h-5 w-5 text-indigo-600"
                />
                <span className="font-bold text-gray-700">Habilitar Copia Automática</span>
              </label>

              <div>
                <label className={labelClass}>Hora de Ejecución (Formato 24h)</label>
                <input
                  type="time"
                  value={autoConfig.hora_ejecucion}
                  onChange={e => setAutoConfig({ ...autoConfig, hora_ejecucion: e.target.value })}
                  className={inputClass}
                />
              </div>

              <div>
                <label className={labelClass}>Ruta Local de Guardado</label>
                <div className="relative">
                  <input
                    type="text"
                    value={autoConfig.ruta_local}
                    onChange={e => setAutoConfig({ ...autoConfig, ruta_local: e.target.value })}
                    className={inputClass}
                    placeholder="C:/Backups_Finaxis"
                  />
                  <FaFolderOpen className="absolute right-3 top-3 text-gray-400" />
                </div>
                <p className="text-xs text-orange-500 mt-1">* Asegúrese que la carpeta exista y el usuario tenga permisos de escritura.</p>
              </div>

              <div>
                <label className={labelClass}>Días de Retención</label>
                <input
                  type="number"
                  value={autoConfig.dias_retencion}
                  onChange={e => setAutoConfig({ ...autoConfig, dias_retencion: parseInt(e.target.value) })}
                  className={inputClass}
                  min="1"
                />
                <p className="text-xs text-gray-400 mt-1">Las copias más antiguas se borrarán automáticamente.</p>
              </div>

            </div>
            <div className="bg-gray-50 p-4 border-t flex justify-end gap-2">
              <button onClick={() => setShowAutoModal(false)} className="px-4 py-2 text-gray-600 font-bold hover:bg-gray-200 rounded-lg">Cancelar</button>
              <button onClick={saveAutoConfig} className="px-4 py-2 bg-indigo-600 text-white font-bold rounded-lg hover:bg-indigo-700 flex items-center gap-2">
                <FaSave /> Guardar Configuración
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
