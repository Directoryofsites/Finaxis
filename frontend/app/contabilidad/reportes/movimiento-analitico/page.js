'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import Select from 'react-select';
import AsyncSelect from 'react-select/async';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { 
  FaCube, 
  FaSearch, 
  FaFilter, 
  FaChevronDown, 
  FaChevronUp, 
  FaEraser, 
  FaFilePdf, 
  FaCalendarAlt,
  FaWarehouse,
  FaBoxOpen,
  FaBook,
  FaLayerGroup
} from 'react-icons/fa';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// --- LÓGICA Y SERVICIOS (INTACTOS) ---
import { useAuth } from '../../../context/AuthContext';
import BotonRegresar from '../../../components/BotonRegresar';
import { getReporteAnalitico, generarPdfMovimientoAnalitico } from '../../../../lib/reportesInventarioService';
import { getBodegas, searchProductosAutocomplete } from '../../../../lib/inventarioService';
import { apiService } from '../../../../lib/apiService';

// --- UTILS ---
const formatValue = (value, isCurrency) => {
  const number = parseFloat(value);
  if (isNaN(number)) return isCurrency ? '$ 0' : '0';
  const options = isCurrency
    ? { style: 'currency', currency: 'COP', minimumFractionDigits: 0, maximumFractionDigits: 0 }
    : { minimumFractionDigits: 0, maximumFractionDigits: 2 };
  return new Intl.NumberFormat('es-CO', options).format(number);
};

const formatDateForURL = (date) => { 
    if (!date) return ''; 
    const d = date instanceof Date ? date : new Date(date); 
    return d.toISOString().split('T')[0]; 
};

// --- ESTILOS REUSABLES ---
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all bg-white";

export default function MovimientoAnaliticoPage() {
  const { user, loading: authLoading } = useAuth(); // Usamos loading del AuthContext
  
  // Estados
  const [filtros, setFiltros] = useState({ 
      fecha_inicio: new Date(new Date().getFullYear(), 0, 1), 
      fecha_fin: new Date(), 
      bodega_id: '', 
      grupo_id: null, 
      producto_id: null, 
      vista_por_valor: false 
  });
  
  const [reporteData, setReporteData] = useState({ items: [], totales: {} });
  const [isLoading, setIsLoading] = useState(false); // Carga de reporte
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);
  const [bodegasOptions, setBodegasOptions] = useState([]);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);

  // Carga Inicial
   useEffect(() => {
       if (user) {
           const fetchData = async () => {
               try {
                   const bodegasRes = await getBodegas();
                   setBodegasOptions(bodegasRes.map(b => ({ value: b.id, label: b.nombre })));
               } catch (err) { 
                   // Corrección: Usamos 'err' capturado
                   toast.error("Error cargando bodegas."); 
               }
           };
           fetchData();
       }
   }, [user]);

  // Selects Asíncronos
  const loadGrupos = (inputValue, callback) => {
      apiService.get(`/inventario/grupos/search?search_term=${inputValue || ''}`)
        .then(res => callback(res.data.map(g => ({ value: g.id, label: g.nombre }))))
        .catch(() => callback([]));
  };

  const loadProductos = (inputValue, callback) => {
      searchProductosAutocomplete({ search_term: inputValue || '' })
        .then(res => callback(res.map(p => ({ value: p.id, label: `(${p.codigo}) ${p.nombre}` }))))
        .catch(() => callback([]));
  };

  // Handlers
  const handleFiltroChange = (name, value) => {
      setFiltros(prev => ({ ...prev, [name]: value }));
  };

  const handleLimpiarFiltros = () => {
      setFiltros({ 
          fecha_inicio: new Date(new Date().getFullYear(), 0, 1), 
          fecha_fin: new Date(), 
          bodega_id: '', 
          grupo_id: null, 
          producto_id: null, 
          vista_por_valor: false 
      });
      setReporteData({ items: [], totales: {} });
      toast.info("Filtros reiniciados.");
  };

  const prepararFiltrosAPI = () => {
      const filtrosParaApi = { 
          fecha_inicio: formatDateForURL(filtros.fecha_inicio), 
          fecha_fin: formatDateForURL(filtros.fecha_fin), 
          vista_por_valor: filtros.vista_por_valor,
          bodega_ids: filtros.bodega_id ? [parseInt(filtros.bodega_id.value)] : null, 
          grupo_ids: filtros.grupo_id ? [parseInt(filtros.grupo_id.value)] : null, 
          producto_ids: filtros.producto_id ? [parseInt(filtros.producto_id.value)] : null
      };
      Object.keys(filtrosParaApi).forEach(key => {
          if (filtrosParaApi[key] === null || filtrosParaApi[key] === '') delete filtrosParaApi[key];
      });
      return filtrosParaApi;
  };

  const handleSearch = async () => {
    setIsLoading(true);
    try { 
        const data = await getReporteAnalitico(prepararFiltrosAPI()); 
        setReporteData(data || { items: [], totales: {} }); 
        if (data?.items?.length === 0) toast.info("No se encontraron movimientos en el periodo.");
    }
    catch (err) { 
        toast.error(err.response?.data?.detail || 'Error al generar el reporte.');
        setReporteData({ items: [], totales: {} }); 
    }
    finally { setIsLoading(false); }
  };

  const handleGenerarPdf = async () => {
      if (isLoading || isGeneratingPdf) return;
      if (reporteData.items.length === 0) return toast.warn("Genere el reporte en pantalla primero.");

      setIsGeneratingPdf(true);
      try {
          await generarPdfMovimientoAnalitico(prepararFiltrosAPI());
      } catch (err) {
          toast.error(err.message || 'Error PDF.');
      } finally {
          setIsGeneratingPdf(false);
      }
  };

  if (authLoading) {
      return (
        <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center">
            <p className="text-indigo-600 font-semibold animate-pulse">Cargando...</p>
        </div>
      );
  }

  return (
    <div className="container mx-auto p-4 md:p-6 bg-slate-50 min-h-screen font-sans pb-20">
      <ToastContainer position="top-right" autoClose={3000} />
      
      {/* HEADER */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>


                            <div className="flex items-center gap-3 mb-3">
                            
                            {/* 1. Botón Regresar (Izquierda) */}
                            <BotonRegresar />

                            {/* 2. Botón Manual (Derecha) */}
                            <button
                                onClick={() => window.open('/manual?file=capitulo_45_movimiento_analitico.md', '_blank')}
                                className="text-indigo-600 hover:bg-indigo-50 px-3 py-1 rounded-md flex items-center gap-2 transition-colors font-bold text-sm"
                                type="button"
                            >
                                <FaBook className="text-lg" /> Manual
                            </button>

                        </div>

            <div className="flex items-center gap-3 mt-3">
                <div className="p-3 bg-purple-100 rounded-xl text-purple-600 shadow-sm">
                    <FaCube className="text-2xl" />
                </div>
                <div>
                    <h1 className="text-3xl font-bold text-gray-800 tracking-tight">Kardex Analítico</h1>
                    <p className="text-gray-500 text-sm">Movimientos detallados de inventario por producto.</p>
                </div>
            </div>
        </div>
      </div>

      {/* PANEL DE CONTROL (FILTROS) */}
      <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 mb-8 animate-fadeIn">
         
         {/* Nivel 1: Filtros Esenciales */}
         <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div>
               <label className={labelClass}>Desde</label>
               <div className="relative">
                   <DatePicker 
                        selected={filtros.fecha_inicio} 
                        onChange={(date) => handleFiltroChange('fecha_inicio', date || new Date())} 
                        selectsStart 
                        startDate={filtros.fecha_inicio} 
                        endDate={filtros.fecha_fin} 
                        dateFormat="dd/MM/yyyy" 
                        className={inputClass} 
                    />
                   <FaCalendarAlt className="absolute right-3 top-3 text-gray-400 pointer-events-none" />
               </div>
            </div>
             <div>
               <label className={labelClass}>Hasta</label>
               <div className="relative">
                   <DatePicker 
                        selected={filtros.fecha_fin} 
                        onChange={(date) => handleFiltroChange('fecha_fin', date || new Date())} 
                        selectsEnd 
                        startDate={filtros.fecha_inicio} 
                        endDate={filtros.fecha_fin} 
                        minDate={filtros.fecha_inicio} 
                        dateFormat="dd/MM/yyyy" 
                        className={inputClass} 
                    />
                   <FaCalendarAlt className="absolute right-3 top-3 text-gray-400 pointer-events-none" />
               </div>
            </div>
            <div>
              <label className={labelClass}>Bodega</label>
              <div className="relative">
                  <Select 
                    instanceId="select-bodega"
                    value={filtros.bodega_id} 
                    onChange={(opt) => handleFiltroChange('bodega_id', opt)} 
                    options={bodegasOptions} 
                    placeholder="Todas las Bodegas" 
                    isClearable
                    styles={{ control: (base) => ({ ...base, minHeight: '2.6rem', borderRadius: '0.5rem', borderColor: '#D1D5DB' }) }}
                  />
                  <FaWarehouse className="absolute right-9 top-3 text-gray-400 pointer-events-none" />
              </div>
            </div>
         </div>

         {/* Barra de Acciones */}
         <div className="flex flex-col md:flex-row justify-between items-center gap-4 border-t border-gray-100 pt-4">
            
            <button 
                onClick={() => setShowAdvancedFilters(!showAdvancedFilters)} 
                className="flex items-center text-sm font-bold text-indigo-600 hover:text-indigo-800 focus:outline-none transition-colors flex-shrink-0"
            >
                <FaFilter className="mr-2" /> 
                {showAdvancedFilters ? 'Menos Filtros' : 'Más Filtros (Producto/Grupo)'}
                {showAdvancedFilters ? <FaChevronUp className="ml-1"/> : <FaChevronDown className="ml-1"/>}
            </button>

            <div className="flex items-center gap-3 w-full md:w-auto justify-end">
                 <button onClick={handleLimpiarFiltros} disabled={isLoading || isGeneratingPdf} className="btn btn-ghost btn-sm text-gray-400 hover:text-red-500 transition-colors">
                    <FaEraser />
                 </button>

                 <button 
                    onClick={handleGenerarPdf} 
                    disabled={isLoading || isGeneratingPdf || reporteData.items.length === 0} 
                    className="btn btn-outline btn-error btn-sm gap-2 shadow-sm"
                    title="Generar PDF con los filtros actuales"
                 >
                     {isGeneratingPdf ? <span className="loading loading-spinner loading-xs"></span> : <FaFilePdf />} PDF
                 </button>

                 <button onClick={handleSearch} disabled={isLoading} className="btn btn-primary px-6 py-2 shadow-md transform hover:scale-105 transition-all">
                    {isLoading ? <><span className="loading loading-spinner loading-sm mr-2"></span> Generando...</> : <><FaSearch className="mr-2"/> Consultar</>}
                 </button>
            </div>
         </div>

         {/* Filtros Avanzados */}
         {showAdvancedFilters && (
            <div className="mt-6 bg-slate-50 p-5 rounded-xl border border-slate-200 animate-slideDown grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div>
                  <label className={labelClass}><FaLayerGroup className="inline mr-1"/> Grupo Inventario</label>
                  <AsyncSelect 
                    instanceId="select-grupo" cacheOptions defaultOptions loadOptions={loadGrupos} 
                    onChange={(opt) => handleFiltroChange('grupo_id', opt)} value={filtros.grupo_id} 
                    placeholder="Buscar grupo..." isClearable styles={{ control: (base) => ({ ...base, borderRadius: '0.5rem' }) }} 
                  />
                </div>
                <div className="lg:col-span-2">
                  <label className={labelClass}><FaBoxOpen className="inline mr-1"/> Producto Específico</label>
                  <AsyncSelect 
                    instanceId="select-producto" cacheOptions defaultOptions loadOptions={loadProductos} 
                    onChange={(opt) => handleFiltroChange('producto_id', opt)} value={filtros.producto_id} 
                    placeholder="Buscar por nombre o código..." isClearable styles={{ control: (base) => ({ ...base, borderRadius: '0.5rem' }) }} 
                  />
                </div>
                
                <div className="md:col-span-3 flex items-center justify-end gap-3 mt-2">
                    <span className="text-sm font-semibold text-gray-600 mr-2">Ver reporte en:</span>
                    <div className="bg-white p-1 rounded-lg border border-gray-300 inline-flex">
                        <button type="button" onClick={() => handleFiltroChange('vista_por_valor', false)} className={`px-4 py-1 rounded-md text-xs font-bold transition-colors ${!filtros.vista_por_valor ? 'bg-indigo-100 text-indigo-700 shadow-sm' : 'text-gray-500 hover:bg-gray-50'}`}>Cantidad</button>
                        <button type="button" onClick={() => handleFiltroChange('vista_por_valor', true)} className={`px-4 py-1 rounded-md text-xs font-bold transition-colors ml-1 ${filtros.vista_por_valor ? 'bg-indigo-100 text-indigo-700 shadow-sm' : 'text-gray-500 hover:bg-gray-50'}`}>Valor ($)</button>
                    </div>
                </div>
            </div>
         )}
      </div>

      {/* RESULTADOS (TABLA ANALÍTICA) */}
      {reporteData.items.length > 0 && !isLoading && (
        <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden animate-slideDown">
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                  {/* Nivel 1: Categorías */}
                  <tr className="bg-slate-100 text-gray-600 uppercase text-xs font-bold tracking-wider border-b border-gray-200">
                      <th className="py-3 px-4 text-left border-r border-gray-200 w-1/3">Producto</th>
                      <th colSpan="2" className="py-2 text-center border-r border-gray-200 bg-slate-50 text-gray-500">Saldo Inicial</th>
                      <th colSpan="2" className="py-2 text-center border-r border-emerald-200 bg-emerald-50 text-emerald-700">Entradas (+)</th>
                      <th colSpan="2" className="py-2 text-center border-r border-rose-200 bg-rose-50 text-rose-700">Salidas (-)</th>
                      <th colSpan="2" className="py-2 text-center bg-indigo-50 text-indigo-700">Saldo Final</th>
                  </tr>
                  {/* Nivel 2: Detalles */}
                  <tr className="text-[10px] font-bold uppercase text-gray-500 border-b border-gray-200">
                      <th className="px-4 py-2 bg-slate-50 border-r border-gray-200">Referencia / Nombre</th>
                      
                      <th className="text-right px-2 py-1 bg-gray-50 border-r border-gray-100 w-20">Cant.</th>
                      <th className="text-right px-2 py-1 bg-gray-50 border-r border-gray-200 w-28">Valor</th>
                      
                      <th className="text-right px-2 py-1 bg-emerald-50/50 border-r border-emerald-100 w-20">Cant.</th>
                      <th className="text-right px-2 py-1 bg-emerald-50/50 border-r border-emerald-200 w-28">Valor</th>
                      
                      <th className="text-right px-2 py-1 bg-rose-50/50 border-r border-rose-100 w-20">Cant.</th>
                      <th className="text-right px-2 py-1 bg-rose-50/50 border-r border-rose-200 w-28">Valor</th>
                      
                      <th className="text-right px-2 py-1 bg-indigo-50/50 border-r border-indigo-100 w-20">Cant.</th>
                      <th className="text-right px-2 py-1 bg-indigo-50/50 w-28">Valor</th>
                  </tr>
              </thead>
              
              <tbody className="divide-y divide-gray-100">
                {reporteData.items.map((item, idx) => (
                  <tr key={item.producto_id} className={`hover:bg-gray-50 transition-colors ${idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/30'}`}>
                    <td className="py-3 px-4 border-r border-gray-100">
                        <div className="flex flex-col">
                            <span className="font-bold text-gray-700 text-sm">{item.producto_nombre}</span>
                            <span className="font-mono text-xs text-gray-400">{item.producto_codigo}</span>
                        </div>
                    </td>
                    
                    {/* Inicial */}
                    <td className="text-right px-2 font-mono text-gray-500 border-r border-gray-100">{formatValue(item.saldo_inicial_cantidad, false)}</td>
                    <td className="text-right px-2 font-mono text-gray-500 border-r border-gray-200">{formatValue(item.saldo_inicial_valor, true)}</td>
                    
                    {/* Entradas */}
                    <td className="text-right px-2 font-mono bg-emerald-50/10 border-r border-emerald-50">
                        {item.total_entradas_cantidad > 0 ? (
                              <Link href={`/contabilidad/reportes/kardex/${item.producto_id}?desde=${formatDateForURL(filtros.fecha_inicio)}&hasta=${formatDateForURL(filtros.fecha_fin)}${filtros.bodega_id ? '&bodega='+filtros.bodega_id.value : ''}`} target="_blank" className="text-emerald-600 hover:text-emerald-800 font-bold hover:underline">
                                  {formatValue(item.total_entradas_cantidad, false)}
                              </Link>
                         ) : <span className="text-gray-300">-</span> }
                    </td>
                    <td className="text-right px-2 font-mono text-emerald-600/80 bg-emerald-50/10 border-r border-emerald-100">{item.total_entradas_valor > 0 ? formatValue(item.total_entradas_valor, true) : '-'}</td>
                    
                    {/* Salidas */}
                    <td className="text-right px-2 font-mono bg-rose-50/10 border-r border-rose-50">
                         {item.total_salidas_cantidad > 0 ? (
                              <Link href={`/contabilidad/reportes/kardex/${item.producto_id}?desde=${formatDateForURL(filtros.fecha_inicio)}&hasta=${formatDateForURL(filtros.fecha_fin)}${filtros.bodega_id ? '&bodega='+filtros.bodega_id.value : ''}`} target="_blank" className="text-rose-600 hover:text-rose-800 font-bold hover:underline">
                                  {formatValue(item.total_salidas_cantidad, false)}
                              </Link>
                         ) : <span className="text-gray-300">-</span> }
                    </td>
                    <td className="text-right px-2 font-mono text-rose-600/80 bg-rose-50/10 border-r border-rose-100">{item.total_salidas_valor > 0 ? formatValue(item.total_salidas_valor, true) : '-'}</td>
                    
                    {/* Final */}
                    <td className="text-right px-2 font-mono font-bold text-indigo-900 bg-indigo-50/10 border-r border-indigo-50">{formatValue(item.saldo_final_cantidad, false)}</td>
                    <td className="text-right px-2 font-mono font-bold text-indigo-900 bg-indigo-50/10">{formatValue(item.saldo_final_valor, true)}</td>
                  </tr>
                ))}
              </tbody>
              
              {/* FOOTER TOTALES */}
               <tfoot className="bg-slate-800 text-white text-xs font-bold uppercase">
                  <tr>
                      <td className="py-3 px-4 text-right border-r border-slate-600">TOTALES PERIODO</td>
                      {/* Inicial */}
                      <td className="text-right px-2 font-mono border-r border-slate-700 opacity-70">{formatValue(reporteData.totales.saldo_inicial_cantidad, false)}</td>
                      <td className="text-right px-2 font-mono border-r border-slate-600 opacity-70">{formatValue(reporteData.totales.saldo_inicial_valor, true)}</td>
                      {/* Entradas */}
                      <td className="text-right px-2 font-mono border-r border-slate-700 text-emerald-400">{formatValue(reporteData.totales.total_entradas_cantidad, false)}</td>
                      <td className="text-right px-2 font-mono border-r border-slate-600 text-emerald-400">{formatValue(reporteData.totales.total_entradas_valor, true)}</td>
                      {/* Salidas */}
                      <td className="text-right px-2 font-mono border-r border-slate-700 text-rose-400">{formatValue(reporteData.totales.total_salidas_cantidad, false)}</td>
                      <td className="text-right px-2 font-mono border-r border-slate-600 text-rose-400">{formatValue(reporteData.totales.total_salidas_valor, true)}</td>
                      {/* Final */}
                      <td className="text-right px-2 font-mono border-r border-slate-700 text-indigo-300">{formatValue(reporteData.totales.saldo_final_cantidad, false)}</td>
                      <td className="text-right px-2 font-mono text-indigo-300">{formatValue(reporteData.totales.saldo_final_valor, true)}</td>
                  </tr>
              </tfoot>
            </table>
          </div>
        </div>
      )}
      
      {!isLoading && reporteData.items.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 text-gray-400 opacity-50">
              <FaLayerGroup className="text-6xl mb-4"/>
              <p>Seleccione fechas y genere el reporte para ver el análisis.</p>
          </div>
      )}
    </div>
  );
}