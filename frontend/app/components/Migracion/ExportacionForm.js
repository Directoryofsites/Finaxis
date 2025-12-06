'use client';

import React, { useState } from 'react';
import { 
  FaDownload, 
  FaDatabase, 
  FaFileExport, 
  FaCheckSquare, 
  FaSquare, 
  FaCalendarAlt, 
  FaFilter, 
  FaBuilding
} from 'react-icons/fa';
import { exportarDatos } from '../../../lib/utilidadesService';

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
      transacciones: false,
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

  const handleFiltroChange = (e) => {
    const { name, value } = e.target;
    setFiltros(prev => ({ ...prev, [name]: value }));
  };

  const handlePaqueteChange = (e) => {
    const { name, checked, dataset } = e.target;
    const { category } = dataset;

    if (category === 'transacciones') {
        setFiltros(p => ({...p, paquetes: {...p.paquetes, transacciones: checked}}));
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
    setMessage('Iniciando proceso de exportación... Esto puede tardar unos segundos.');
    setError(null);
    setIsProcessing(true);

    try {
      const payload = { ...filtros };

      for (const key in payload) {
          if (payload[key] === '') {
              payload[key] = null;
          }
      }
      if (payload.valorMonto) {
          payload.valorMonto = parseFloat(payload.valorMonto);
      }
      
      const { data: backupData } = await exportarDatos(payload);

      const jsonString = JSON.stringify(backupData, null, 2);
      const blob = new Blob([jsonString], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      const fechaHoy = new Date().toISOString().split('T')[0];
      link.download = `backup_contable_${empresaActual?.razon_social || 'export'}_${fechaHoy}.json`;
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      setMessage('¡Exportación completada! El archivo JSON se está descargando.');

    } catch (err) {
      let errorMsg = 'Ocurrió un error inesperado.'; 
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (Array.isArray(detail)) {
          errorMsg = detail.map(e => `${e.loc.length > 1 ? e.loc[1] : e.loc[0]}: ${e.msg}`).join('; ');
        } else {
          errorMsg = String(detail);
        }
      } else if (err.message) {
        errorMsg = err.message;
      }
      setError(`Error en la exportación: ${errorMsg}`);
      setMessage('');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="bg-white p-8 rounded-xl shadow-lg border border-gray-100 mb-8 animate-fadeIn">
      
      <div className="flex items-center gap-3 mb-6 pb-4 border-b border-gray-100">
        <div className="p-3 bg-blue-100 rounded-full text-blue-600">
            <FaFileExport className="text-xl" />
        </div>
        <div>
            <h2 className="text-xl font-bold text-gray-800">Exportar Datos</h2>
            <p className="text-gray-500 text-sm">Crear copia de seguridad o paquete de migración.</p>
        </div>
      </div>

      <div className="mb-8">
        <label htmlFor="sourceEmpresaName" className={labelClass}>
          Empresa Origen
        </label>
        <div className="relative">
            <input
            type="text"
            id="sourceEmpresaName"
            value={empresaActual?.razon_social || 'Cargando...'}
            readOnly
            className="w-full px-4 py-3 border border-gray-200 rounded-lg bg-gray-50 text-gray-700 font-medium shadow-inner pl-10"
            />
            <FaBuilding className="absolute left-3 top-3.5 text-gray-400" />
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* COLUMNA 1: SELECCIÓN DE PAQUETES */}
        <div className="lg:col-span-1 space-y-6">
            
            {/* Maestros */}
            <div className="bg-gray-50 p-5 rounded-xl border border-gray-200">
                <h3 className="font-bold text-gray-700 mb-3 flex items-center gap-2">
                    <FaDatabase className="text-indigo-500"/> Datos Maestros
                </h3>
                <div className="space-y-2 pl-1">
                    {Object.keys(filtros.paquetes.maestros).map(key => (
                        <label key={key} className="flex items-center cursor-pointer hover:text-indigo-600 transition-colors">
                            <input type="checkbox" name={key} data-category="maestros" checked={filtros.paquetes.maestros[key]} onChange={handlePaqueteChange} className={checkboxClass} />
                            <span className="text-sm capitalize">{key.replace(/_/g, ' ')}</span>
                        </label>
                    ))}
                </div>
            </div>

            {/* Configuraciones */}
            <div className="bg-gray-50 p-5 rounded-xl border border-gray-200">
                <h3 className="font-bold text-gray-700 mb-3 flex items-center gap-2">
                    <FaDatabase className="text-amber-500"/> Configuraciones
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

            {/* Transacciones (Switch Principal) */}
            <div className={`p-5 rounded-xl border transition-all duration-300 ${filtros.paquetes.transacciones ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'}`}>
                <label className="flex items-center cursor-pointer">
                    <input 
                        type="checkbox" 
                        name="transacciones" 
                        data-category="transacciones" 
                        checked={filtros.paquetes.transacciones} 
                        onChange={handlePaqueteChange} 
                        className="h-5 w-5 text-green-600 focus:ring-green-500 border-gray-300 rounded mr-3" 
                    />
                    <span className={`font-bold text-md ${filtros.paquetes.transacciones ? 'text-green-700' : 'text-gray-600'}`}>
                        Incluir Movimientos Contables
                    </span>
                </label>
                <p className="text-xs text-gray-500 mt-2 ml-8">
                    Marcar para exportar facturas, recibos y asientos contables.
                </p>
            </div>
        </div>

        {/* COLUMNA 2 y 3: FILTROS AVANZADOS (Condicional) */}
        <div className={`lg:col-span-2 p-6 rounded-xl border border-gray-200 transition-all duration-300 ${!filtros.paquetes.transacciones ? 'bg-gray-50 opacity-60 pointer-events-none grayscale' : 'bg-white shadow-sm'}`}>
          <div className="flex items-center gap-2 mb-6 pb-2 border-b border-gray-100">
            <FaFilter className="text-gray-400" />
            <h3 className="font-bold text-gray-700">Filtros de Transacciones</h3>
            <span className="text-xs bg-gray-100 text-gray-500 px-2 py-1 rounded-full ml-auto">Opcional</span>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <label className={labelClass}>Tipo de Documento</label>
                <select name="tipoDocId" value={filtros.tipoDocId} onChange={handleFiltroChange} className={inputClass} disabled={!filtros.paquetes.transacciones}>
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
          {isProcessing ? <><FaDatabase className="animate-pulse"/> Procesando...</> : <><FaDownload /> Generar Backup JSON</>}
        </button>
      </div>
    </div>
  );
}