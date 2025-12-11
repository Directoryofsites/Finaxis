'use client';

import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { 
  FaClipboardList, 
  FaSearch, 
  FaFilter, 
  FaChevronDown, 
  FaChevronUp, 
  FaBoxOpen, 
  FaSave,
  FaWarehouse,
  FaCalendarAlt,
  FaLayerGroup,
  FaBook,
  FaHashtag,
  FaBalanceScale
} from 'react-icons/fa';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import BotonRegresar from '@/app/components/BotonRegresar'; 
import { getBodegas, getGruposInventario } from '@/lib/inventarioService';
import { buscarProductos } from '@/lib/productosService';
import { procesarAjusteInventario } from '@/lib/ajusteInventarioService';

const formatNumber = (num) => {
  if (isNaN(num) || num === null) return '$ 0,00';
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(num);
};

// Estilos Reusables (Manual v2.0)
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none pl-10";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white pl-10";

const TomaInventarioFisicoPage = () => {
  
  // --- ESTADOS ---
  const [productos, setProductos] = useState([]);
  const [grupos, setGrupos] = useState([]);
  const [bodegas, setBodegas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [fechaAjuste, setFechaAjuste] = useState(new Date().toISOString().split('T')[0]);
  const [filtroGrupoId, setFiltroGrupoId] = useState('');
  const [filtroBodegaId, setFiltroBodegaId] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  
  const [conteoFisicos, setConteosFisicos] = useState({}); 
  const [itemsParaAjustar, setItemsParaAjustar] = useState(new Set()); 
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const initialDataLoaded = useRef(false); 

  // --- LÓGICA ---

  const handleSearch = useCallback(async () => {
    if (!filtroBodegaId) {
        setLoading(false);
        setProductos([]); 
        return;
    }
    
    setLoading(true);
    setError(null);
    setProductos([]); 
    setConteosFisicos({}); 
    setItemsParaAjustar(new Set()); 

    const bodegaIds = [parseInt(filtroBodegaId)];
    const filtros = {
      grupo_id: filtroGrupoId || null,
      search_term: searchTerm || null,
      bodega_ids: bodegaIds, 
    };

    try {
      const response = await buscarProductos(filtros); 
      setProductos(response);
    } catch (e) {
      console.error("Error al buscar productos:", e);
      setError('Error al cargar productos.');
      setProductos([]);
    } finally {
      setLoading(false); 
    }
  }, [filtroBodegaId, searchTerm, filtroGrupoId]);

  useEffect(() => {
    if (initialDataLoaded.current) return;
    
    const loadDataAndSearch = async () => {
      try {
        const [bodegasData, gruposData] = await Promise.all([
          getBodegas(),
          getGruposInventario()
        ]);
        setBodegas(bodegasData);
        setGrupos(gruposData);

        let bodegaIdInicial = '';
        if (bodegasData.length > 0) {
            bodegaIdInicial = bodegasData[0].id.toString();
            setFiltroBodegaId(bodegaIdInicial); 
        }
        setLoading(false); 
        initialDataLoaded.current = true; 

      } catch (e) {
        toast.error("Error al cargar datos maestros.");
        setLoading(false); 
      }
    };
    loadDataAndSearch();
  }, []); 
  
  useEffect(() => {
      if (filtroBodegaId && initialDataLoaded.current) {
          handleSearch();
      }
  }, [filtroBodegaId, handleSearch]);


  const handleToggleAjuste = useCallback((productId) => {
    setItemsParaAjustar(prev => {
      const newSet = new Set(prev);
      if (newSet.has(productId)) {
        newSet.delete(productId);
      } else {
        newSet.add(productId);
      }
      return newSet;
    });
  }, []);

  const productosAjustables = useMemo(() => {
    return productos.filter(p => itemsParaAjustar.has(p.id));
  }, [productos, itemsParaAjustar]);

  const handleSubmit = useCallback(async () => {
    if (!filtroBodegaId) {
        toast.error("Debe seleccionar una bodega.");
        return;
    }
    
    const conteos = conteoFisicos || {}; 
    
    const items = productosAjustables.map(p => {
        const stockSistema = parseFloat(p.stock_actual) || 0; 
        const costoPromedio = parseFloat(p.costo_promedio) || 0; 
        const conteoFisico = parseFloat(conteos[p.id]) || 0;
        const diferencia = parseFloat((conteoFisico - stockSistema).toFixed(2)); 
        
        return {
            producto_id: parseInt(p.id), 
            diferencia: diferencia, 
            costo_promedio: costoPromedio, 
        };
    }).filter(item => Math.abs(item.diferencia) > 1e-6); 
    
    if (items.length === 0) {
        toast.warn("No hay diferencias detectadas o productos seleccionados.");
        return;
    }

    if (!window.confirm(`¿Está seguro de procesar el ajuste para ${items.length} productos?\nEsta acción afectará el inventario y la contabilidad.`)) {
        return;
    }

    const ajustePayload = {
        fecha: fechaAjuste,
        bodega_id: parseInt(filtroBodegaId), 
        concepto: `Ajuste Físico - Bodega ${bodegas.find(b => b.id == filtroBodegaId)?.nombre}`, 
        items: items
    };

    setIsSubmitting(true);
    try {
        await procesarAjusteInventario(ajustePayload);
        toast.success(`Ajuste procesado con éxito para ${items.length} items.`);
        await handleSearch(); 
    } catch (e) {
        console.error("Error al procesar el ajuste:", e);
        const errorDetail = e.response?.data?.detail 
            ? (Array.isArray(e.response.data.detail) ? (e.response.data.detail[0].msg || 'Error') : e.response.data.detail) 
            : 'Error desconocido.';
        toast.error(`Fallo al procesar ajuste: ${errorDetail}`);
    } finally {
        setIsSubmitting(false);
    }
  }, [filtroBodegaId, fechaAjuste, productosAjustables, conteoFisicos, handleSearch, bodegas]); 


  const totales = useMemo(() => {
    let valorSistema = 0, valorFisico = 0; 
    const conteos = conteoFisicos || {}; 
    productos.forEach(p => { 
        const stockSistema = p.stock_actual ?? 0.0;
        const costoPromedio = p.costo_promedio || 0.0; 
        const conteoDigitado = conteos[p.id]; 
        const conteoFisico = conteoDigitado !== undefined && conteoDigitado !== '' ? parseFloat(conteoDigitado) : stockSistema; 
        
        if (!isNaN(conteoFisico)) { 
            valorSistema += (parseFloat(stockSistema) || 0) * (parseFloat(costoPromedio) || 0); 
            valorFisico += conteoFisico * (parseFloat(costoPromedio) || 0); 
        } 
    }); 
    return { valorSistema, valorFisico, diferencia: valorFisico - valorSistema };
  }, [productos, conteoFisicos]);


  // --- RENDER ---
  return (
    <div className="container mx-auto p-4 md:p-8 bg-gray-50 min-h-screen font-sans pb-32">
      <ToastContainer position="top-right" autoClose={3000} />
      
      {/* ENCABEZADO */}
      <div className="flex justify-between items-center mb-8">
        <div>
            <h1 className="text-3xl font-bold text-gray-800 tracking-tight">Toma Física de Inventario</h1>
            <p className="text-gray-500 text-sm mt-1">Ajuste de existencias y conciliación de bodegas.</p>
        </div>

                            <div className="flex items-center gap-3 mb-3">
                            
                            {/* 1. Botón Regresar (Izquierda) */}
                            <BotonRegresar />

                            {/* 2. Botón Manual (Derecha) */}
                            <button
                                onClick={() => window.open('/manual/capitulo_43_ajuste_inventario.html', '_blank')}
                                className="text-indigo-600 hover:bg-indigo-50 px-3 py-1 rounded-md flex items-center gap-2 transition-colors font-bold text-sm"
                                type="button"
                            >
                                <FaBook className="text-lg" /> Manual
                            </button>

                        </div>

      </div>

      {/* CARD 1: CONFIGURACIÓN Y FILTROS */}
      <div className="bg-white p-6 md:p-8 rounded-xl shadow-lg border border-gray-100 mb-8 animate-fadeIn">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div>
                <label className={labelClass}>Fecha del Ajuste</label>
                <div className="relative">
                    <input
                        type="date"
                        value={fechaAjuste}
                        onChange={(e) => setFechaAjuste(e.target.value)}
                        className={inputClass}
                        required
                    />
                    <FaCalendarAlt className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                </div>
            </div>
            <div>
                <label className={labelClass}>Bodega a Inventariar</label>
                <div className="relative">
                    <select
                        value={filtroBodegaId}
                        onChange={(e) => setFiltroBodegaId(e.target.value)}
                        className={`${selectClass} font-bold text-indigo-900 bg-indigo-50 border-indigo-200`}
                    >
                        <option value="">Seleccione Bodega...</option>
                        {bodegas.map(b => <option key={b.id} value={b.id}>{b.nombre}</option>)}
                    </select>
                    <FaWarehouse className="absolute left-3 top-3 text-indigo-400 pointer-events-none" />
                </div>
            </div>
        </div>

        {/* Filtros Avanzados (Acordeón) */}
        <div className="border-t border-gray-100 pt-4">
            <button 
                onClick={() => setShowAdvancedFilters(!showAdvancedFilters)} 
                className="flex items-center text-sm font-bold text-indigo-600 hover:text-indigo-800 focus:outline-none transition-colors"
            >
                <FaFilter className="mr-2" /> 
                {showAdvancedFilters ? 'Ocultar Filtros' : 'Filtrar por Grupo o Nombre'}
                {showAdvancedFilters ? <FaChevronUp className="ml-1"/> : <FaChevronDown className="ml-1"/>}
            </button>

            {showAdvancedFilters && (
                <div className="mt-4 bg-gray-50 p-4 rounded-xl border border-gray-200 animate-slideDown grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <label className={labelClass}>Grupo de Inventario</label>
                        <div className="relative">
                            <select
                                value={filtroGrupoId}
                                onChange={(e) => setFiltroGrupoId(e.target.value)}
                                className={selectClass}
                            >
                                <option value="">Todos los Grupos</option>
                                {grupos.map(g => <option key={g.id} value={g.id}>{g.nombre}</option>)}
                            </select>
                            <FaLayerGroup className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                        </div>
                    </div>
                    <div>
                        <label className={labelClass}>Buscar Producto</label>
                        <div className="relative">
                            <input
                                type="text"
                                placeholder="Código o nombre..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className={inputClass}
                            />
                            <FaSearch className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                        </div>
                    </div>
                </div>
            )}
        </div>

        <div className="flex justify-end mt-6 pt-4 border-t border-gray-100">
            <button onClick={handleSearch} className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 shadow-md flex items-center gap-2 transition-all" disabled={loading}>
                {loading ? <span className="loading loading-spinner loading-sm"></span> : <><FaSearch /> Cargar Inventario</>}
            </button>
        </div>
      </div>

      {/* CARD 2: KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white p-5 rounded-xl shadow-sm border border-blue-100 flex flex-col items-center">
              <div className="p-2 bg-blue-50 text-blue-600 rounded-full mb-2"><FaHashtag /></div>
              <span className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">Valor en Sistema</span>
              <span className="text-xl font-mono font-bold text-blue-700">{formatNumber(totales.valorSistema)}</span>
          </div>
          <div className="bg-white p-5 rounded-xl shadow-sm border border-green-100 flex flex-col items-center">
              <div className="p-2 bg-green-50 text-green-600 rounded-full mb-2"><FaClipboardList /></div>
              <span className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">Valor Físico</span>
              <span className="text-xl font-mono font-bold text-green-700">{formatNumber(totales.valorFisico)}</span>
          </div>
          <div className={`bg-white p-5 rounded-xl shadow-sm border flex flex-col items-center ${totales.diferencia < 0 ? 'border-red-100 bg-red-50' : 'border-gray-100'}`}>
              <div className={`p-2 rounded-full mb-2 ${totales.diferencia < 0 ? 'bg-red-100 text-red-600' : 'bg-gray-100 text-gray-600'}`}><FaBalanceScale /></div>
              <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">Diferencia Neta</span>
              <span className={`text-xl font-mono font-bold ${totales.diferencia >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {totales.diferencia > 0 ? '+' : ''}{formatNumber(totales.diferencia)}
              </span>
          </div>
      </div>

      {/* CARD 3: TABLA DE CONTEO */}
      <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden animate-fadeIn">
        
        <div className="p-5 bg-gray-50 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                <FaBoxOpen className="text-gray-500"/> Listado de Productos
            </h2>
            <span className="text-sm font-medium text-gray-500 bg-white px-3 py-1 rounded-full border border-gray-200 shadow-sm">
                {productos.length} items cargados
            </span>
        </div>

        <div className="overflow-x-auto max-h-[60vh]">
            <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-slate-100 sticky top-0 z-10 shadow-sm">
                    <tr>
                        <th className="py-3 px-4 text-left text-xs font-bold text-gray-600 uppercase w-24">Código</th>
                        <th className="py-3 px-4 text-left text-xs font-bold text-gray-600 uppercase">Producto</th>
                        <th className="py-3 px-4 text-right text-xs font-bold text-gray-600 uppercase w-32">Costo Prom.</th>
                        <th className="py-3 px-4 text-right text-xs font-bold text-gray-600 uppercase w-24 bg-slate-50">Saldo Sist.</th>
                        <th className="py-3 px-4 text-center text-xs font-bold text-indigo-800 uppercase w-40 bg-amber-50 border-l border-r border-amber-100">
                            <FaClipboardList className="inline mr-1"/> Conteo Físico
                        </th>
                        <th className="py-3 px-4 text-right text-xs font-bold text-gray-600 uppercase w-24">Dif. Cant.</th>
                        <th className="py-3 px-4 text-right text-xs font-bold text-gray-600 uppercase w-32">Dif. Valor</th>
                        <th className="py-3 px-4 text-center text-xs font-bold text-gray-600 uppercase w-20">Incluir</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 text-sm">
                    {loading && productos.length === 0 ? (
                        <tr><td colSpan="8" className="text-center py-10 text-gray-500">Cargando datos...</td></tr>
                    ) : productos.length === 0 ? (
                        <tr>
                            <td colSpan="8" className="text-center py-12 text-gray-400 italic">
                                {!filtroBodegaId ? "Seleccione una bodega para comenzar." : "No se encontraron productos."}
                            </td>
                        </tr>
                    ) : (
                        productos.map(p => {
                            const stockSistema = parseFloat(p.stock_actual || 0); 
                            const conteos = conteoFisicos || {};
                            const conteoDigitado = conteos[p.id]; 
                            // Si no hay conteo, asumimos igualdad para visualización, pero el cálculo real dependerá de si se marca el check
                            const conteoFisico = conteoDigitado !== undefined && conteoDigitado !== '' ? parseFloat(conteoDigitado) : stockSistema;
                            
                            const diferencia = conteoFisico - stockSistema;
                            const valorDiferencia = diferencia * (p.costo_promedio || 0);
                            
                            const isSelected = itemsParaAjustar.has(p.id);
                            const hasDiff = Math.abs(diferencia) > 0.0001;

                            return (
                                <tr key={p.id} className={`transition-colors ${isSelected ? 'bg-indigo-50 hover:bg-indigo-100' : 'hover:bg-gray-50'}`}>
                                    <td className="py-3 px-4 font-mono text-gray-600">{p.codigo}</td>
                                    <td className="py-3 px-4 font-medium text-gray-800">{p.nombre}</td>
                                    <td className="py-3 px-4 text-right font-mono text-gray-500">{formatNumber(p.costo_promedio)}</td>
                                    <td className="py-3 px-4 text-right font-mono font-bold text-gray-700 bg-slate-50/50">{stockSistema.toFixed(2)}</td>
                                    
                                    <td className="py-2 px-2 text-center bg-amber-50/30 border-l border-r border-amber-100">
                                        <input
                                            type="number" 
                                            className="w-full px-2 py-1 border border-amber-300 rounded text-center font-bold text-gray-800 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none"
                                            value={conteoDigitado || ''}
                                            onChange={(e) => setConteosFisicos(prev => ({ ...prev, [p.id]: e.target.value }))}
                                            placeholder={stockSistema.toFixed(2)} 
                                            min="0" step="any"
                                        />
                                    </td>
                                    
                                    <td className={`py-3 px-4 text-right font-mono font-bold ${diferencia > 0 ? 'text-green-600' : diferencia < 0 ? 'text-red-600' : 'text-gray-300'}`}>
                                        {diferencia > 0 ? '+' : ''}{diferencia !== 0 ? diferencia.toFixed(2) : '-'}
                                    </td>
                                    <td className={`py-3 px-4 text-right font-mono text-xs ${valorDiferencia !== 0 ? 'font-bold' : 'text-gray-300'}`}>
                                        {valorDiferencia !== 0 ? formatNumber(valorDiferencia) : '-'}
                                    </td>
                                    
                                    <td className="py-3 px-4 text-center">
                                        <input
                                            type="checkbox" 
                                            className={`h-5 w-5 cursor-pointer rounded border-gray-300 ${hasDiff ? 'text-red-600 focus:ring-red-500' : 'text-indigo-600 focus:ring-indigo-500'}`}
                                            checked={isSelected}
                                            onChange={() => handleToggleAjuste(p.id)}
                                        />
                                    </td>
                                </tr>
                            );
                        })
                    )}
                </tbody>
            </table>
        </div>

        {/* FOOTER DE ACCIÓN */}
        <div className="p-6 bg-white border-t border-gray-200 flex justify-between items-center">
            <div className="text-sm text-gray-600">
                <span className="font-bold text-indigo-600 text-lg mr-2">{productosAjustables.length}</span>
                items seleccionados para ajuste.
            </div>
            <button
                onClick={handleSubmit}
                disabled={isSubmitting || productosAjustables.length === 0 || !filtroBodegaId}
                className={`
                    px-8 py-3 rounded-lg shadow-lg font-bold text-white text-lg transition-all transform hover:-translate-y-0.5 flex items-center gap-2
                    ${productosAjustables.length > 0 
                        ? 'bg-green-600 hover:bg-green-700 hover:shadow-green-200' 
                        : 'bg-gray-400 cursor-not-allowed'}
                `}
            >
                {isSubmitting ? (
                    <> <span className="loading loading-spinner loading-sm mr-2"></span> Procesando... </>
                ) : (
                    <> <FaSave /> Procesar Ajuste </>
                )}
            </button>
        </div>
      </div>
    </div>
  );
};

export default TomaInventarioFisicoPage;