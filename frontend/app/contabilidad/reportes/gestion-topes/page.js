// frontend/app/contabilidad/reportes/gestion-topes/page.js (REDISEÑO V2.0)

'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { FaDownload, FaExclamationTriangle, FaCheckCircle, FaBan, FaSearch } from 'react-icons/fa';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import BotonRegresar from '@/app/components/BotonRegresar';

import { 
    FaBook,
} from 'react-icons/fa';

// Servicios
import { getReporteTopes, crearTokenTopesPDF } from '@/lib/reportesInventarioService'; 

const formatNumber = (num) => {
  if (isNaN(num) || num === null) return '0.00';
  return new Intl.NumberFormat('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(num);
};

const GestionTopesPage = () => {
  
  // --- ESTADOS ---
  const [reporte, setReporte] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  
  // --- FILTROS ---
  const [fechaCorte, setFechaCorte] = useState(new Date().toISOString().split('T')[0]);
  const [tipoAlerta, setTipoAlerta] = useState('MINIMO'); // MINIMO, MAXIMO

  // --- CARGA INICIAL ---
  useEffect(() => {
    handleSearch('MINIMO');
  }, []); 

  // --- BÚSQUEDA ---
  const handleSearch = useCallback(async (alerta = tipoAlerta) => {
    if (!fechaCorte) { toast.error("Debe seleccionar una fecha de corte."); return; }
    
    setLoading(true);
    setReporte(null);

    const filtros = {
      fecha_corte: fechaCorte,
      bodega_ids: undefined, 
      grupo_ids: undefined,  
      tipo_alerta: alerta,   
    };

    try {
      const response = await getReporteTopes(filtros); 
      setReporte(response);
      setTipoAlerta(alerta); 
      
      if (response.items.length === 0) {
          toast.info(`No hay productos que cumplan la condición de Stock ${alerta}.`);
      }
    } catch (e) {
      console.error("Error:", e);
      toast.error('Fallo al cargar el reporte.');
    } finally {
      setLoading(false); 
    }
  }, [fechaCorte, tipoAlerta]);
  
  // --- PDF ---
  const handleDownloadPdf = useCallback(async () => {
    if (!reporte || reporte.items.length === 0) { toast.warn("No hay datos para descargar."); return; }
    
    setIsDownloading(true);
    const filtros = { fecha_corte: fechaCorte, bodega_ids: undefined, grupo_ids: undefined, tipo_alerta: tipoAlerta };

    try {
        const token = await crearTokenTopesPDF(filtros);
        const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const urlDescarga = `${backendUrl}/api/reportes-inventario/topes/pdf/${token}`;
        const newTab = window.open(urlDescarga, '_blank');
        if (!newTab) throw new Error("Pop-up bloqueado.");
        toast.success("PDF solicitado.");
    } catch (e) {
      toast.error(`Error descarga: ${e.message}`);
    } finally {
      setIsDownloading(false);
    }
  }, [reporte, fechaCorte, tipoAlerta]);
  
  // --- CONTEO ---
  const { totalMinimo, totalMaximo, totalItems } = useMemo(() => {
    if (!reporte) return { totalMinimo: 0, totalMaximo: 0, totalItems: 0 };
    return {
        totalMinimo: reporte.totales_topes?.MINIMO || 0,
        totalMaximo: reporte.totales_topes?.MAXIMO || 0,
        totalItems: reporte.items.length
    };
  }, [reporte]);

  // Clases V2.0
  const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
  const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none";

  return (
    <div className="container mx-auto p-4 md:p-8 bg-gray-50 min-h-screen font-sans">
      <ToastContainer position="top-right" autoClose={3000} />
      
      {/* HEADER */}
      <div className="flex justify-between items-center mb-8">
        <div>
            <h1 className="text-3xl font-bold text-gray-800 tracking-tight">Gestión de Topes</h1>
            <p className="text-gray-500 text-sm mt-1">Control de mínimos y máximos de inventario.</p>
        </div>


                        <div className="flex items-center gap-3 mb-3">
                            
                            {/* 1. Botón Regresar (Izquierda) */}
                            <BotonRegresar />

                            {/* 2. Botón Manual (Derecha) */}
                            <button
                                onClick={() => window.open('/manual?file=capitulo_48_gestion_topes.md', '_blank')}
                                className="text-indigo-600 hover:bg-indigo-50 px-3 py-1 rounded-md flex items-center gap-2 transition-colors font-bold text-sm"
                                type="button"
                            >
                                <FaBook className="text-lg" /> Manual
                            </button>

                        </div>


      </div>

      {/* CARD DE CONTROL */}
      <div className="bg-white p-6 md:p-8 rounded-xl shadow-lg border border-gray-100 mb-8 animate-fadeIn">
        
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-end">
            {/* Fecha Corte */}
            <div className="md:col-span-4">
                <label className={labelClass}>Fecha de Corte (Saldos a)</label>
                <input type="date" value={fechaCorte} onChange={(e) => setFechaCorte(e.target.value)} className={inputClass} required />
            </div>
            
            {/* Selector de Estrategia (Botones Grandes) */}
            <div className="md:col-span-8 flex gap-4">
                <button 
                    onClick={() => handleSearch('MINIMO')}
                    className={`flex-1 py-3 px-4 rounded-lg border transition-all flex items-center justify-center gap-2 font-bold text-sm shadow-sm
                        ${tipoAlerta === 'MINIMO' 
                            ? 'bg-yellow-50 border-yellow-400 text-yellow-700 ring-2 ring-yellow-200' 
                            : 'bg-white border-gray-200 text-gray-500 hover:bg-gray-50'
                        }`}
                    disabled={loading}
                >
                    <FaExclamationTriangle className={tipoAlerta === 'MINIMO' ? 'text-yellow-600' : 'text-gray-400'} />
                    🚨 Mínimo: HACER PEDIDO
                </button>

                <button 
                    onClick={() => handleSearch('MAXIMO')}
                    className={`flex-1 py-3 px-4 rounded-lg border transition-all flex items-center justify-center gap-2 font-bold text-sm shadow-sm
                        ${tipoAlerta === 'MAXIMO' 
                            ? 'bg-red-50 border-red-400 text-red-700 ring-2 ring-red-200' 
                            : 'bg-white border-gray-200 text-gray-500 hover:bg-gray-50'
                        }`}
                    disabled={loading}
                >
                    <FaBan className={tipoAlerta === 'MAXIMO' ? 'text-red-600' : 'text-gray-400'} />
                    ⚠️ Máximo: NO COMPRAR
                </button>
            </div>
        </div>
      </div>

      {/* KPI CARDS */}
      {reporte && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 animate-fadeIn">
            <div className="bg-white p-5 rounded-xl shadow-md border border-yellow-100 flex flex-col items-center">
                <span className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">Alertas Mínimas</span>
                <span className="text-2xl font-mono font-bold text-yellow-600">{totalMinimo}</span>
            </div>
            <div className="bg-white p-5 rounded-xl shadow-md border border-red-100 flex flex-col items-center">
                <span className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">Alertas Máximas</span>
                <span className="text-2xl font-mono font-bold text-red-600">{totalMaximo}</span>
            </div>
            <div className="bg-white p-5 rounded-xl shadow-md border border-indigo-100 flex flex-col items-center bg-indigo-50">
                <span className="text-xs font-bold text-indigo-400 uppercase tracking-widest mb-1">Total en Lista</span>
                <span className="text-2xl font-mono font-bold text-indigo-700">{totalItems}</span>
            </div>
        </div>
      )}

      {/* CARD DE RESULTADOS */}
      <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden animate-fadeIn min-h-[400px]">
        
        {/* Toolbar Tabla */}
        <div className="p-5 bg-gray-50 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                Resultados <span className="text-sm font-normal text-gray-500 bg-white px-2 py-0.5 rounded-md border border-gray-200 shadow-sm">{totalItems} ítems</span>
            </h2>
            <button onClick={handleDownloadPdf} disabled={isDownloading || !reporte?.items.length} className="btn btn-outline btn-error btn-sm gap-2 shadow-sm">
                {isDownloading ? <span className="loading loading-spinner loading-xs"></span> : <FaDownload />} 
                PDF
            </button>
        </div>

        {/* Tabla */}
        <div className="overflow-x-auto">
            {loading ? (
                <div className="flex flex-col justify-center items-center py-20 text-gray-500">
                    <span className="loading loading-spinner loading-lg text-indigo-600 mb-4"></span>
                    <p>Calculando alertas de stock...</p>
                </div>
            ) : !reporte || reporte.items.length === 0 ? (
                <div className="flex flex-col justify-center items-center py-20 text-gray-400">
                    <FaCheckCircle className="text-5xl text-green-100 mb-4" />
                    <p className="text-lg font-medium text-green-600">¡Todo en orden!</p>
                    <p className="text-sm">No hay productos en alerta de {tipoAlerta === 'MINIMO' ? 'Mínimos' : 'Máximos'}.</p>
                </div>
            ) : (
                <table className="table table-sm w-full">
                    <thead className="bg-slate-100 text-gray-600 uppercase text-xs font-bold sticky top-0 z-10 shadow-sm">
                        <tr>
                            <th className="py-3 px-4 text-left">Código</th>
                            <th className="py-3 px-4 text-left">Producto</th>
                            <th className="py-3 px-4 text-left">Bodega</th>
                            <th className="py-3 px-4 text-right">Saldo Actual</th>
                            <th className="py-3 px-4 text-right">Mínimo</th>
                            <th className="py-3 px-4 text-right">Máximo</th>
                            <th className="py-3 px-4 text-right font-black">Diferencia</th>
                            <th className="py-3 px-4 text-center">Decisión</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 text-sm">
                        {reporte.items.map((item, idx) => {
                            const colorClass = item.estado_tope === 'MINIMO' ? 'text-yellow-600 font-bold bg-yellow-50' : 'text-red-600 font-bold bg-red-50';
                            const decisionText = item.estado_tope === 'MINIMO' ? 'PEDIR' : 'NO COMPRAR';
                            
                            return (
                                <tr key={`${item.producto_id}-${idx}`} className="hover:bg-indigo-50/30 transition-colors">
                                    <td className="py-2 px-4 font-mono text-xs text-gray-500">{item.producto_codigo}</td>
                                    <td className="py-2 px-4 font-medium text-gray-700">{item.producto_nombre}</td>
                                    <td className="py-2 px-4 text-gray-600 text-xs">{item.bodega_nombre}</td>
                                    <td className="py-2 px-4 text-right font-mono font-bold text-gray-800">{formatNumber(item.saldo_actual)}</td>
                                    <td className="py-2 px-4 text-right font-mono text-gray-500">{formatNumber(item.stock_minimo)}</td>
                                    <td className="py-2 px-4 text-right font-mono text-gray-500">{formatNumber(item.stock_maximo)}</td>
                                    <td className={`py-2 px-4 text-right font-mono ${item.estado_tope === 'MINIMO' ? 'text-yellow-600' : 'text-red-600'}`}>
                                        {formatNumber(item.diferencia)}
                                    </td>
                                    <td className="py-2 px-4 text-center">
                                        <span className={`px-2 py-1 rounded text-xs border ${item.estado_tope === 'MINIMO' ? 'border-yellow-200 bg-yellow-100 text-yellow-800' : 'border-red-200 bg-red-100 text-red-800'}`}>
                                            {decisionText}
                                        </span>
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            )}
        </div>
      </div>
    </div>
  );
};

export default GestionTopesPage;