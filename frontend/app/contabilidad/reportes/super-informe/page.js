// frontend/app/contabilidad/reportes/super-informe/page.js (VERSIÓN PULIDA V2.1)
'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../../../context/AuthContext';
import BotonRegresar from '../../../components/BotonRegresar';
import { apiService } from '../../../../lib/apiService';
import Paginacion from '../../../components/ui/Paginacion';
import MultiSelect from '../../../components/ui/MultiSelect'; // Importar MultiSelect
import { FaSearch, FaFilePdf, FaFilter, FaChevronDown, FaChevronUp, FaEraser, FaTable, FaBook } from 'react-icons/fa';

const formatCurrency = (value) => {
  if (value === null || value === undefined || isNaN(value)) return '$ 0';
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(value);
};

const INITIAL_FILTROS_STATE = {
  tipoEntidad: 'movimientos',
  estadoDocumento: 'activos',
  fechaInicio: '',
  fechaFin: '',
  tipoDocIds: [], // Antes tipoDocId
  numero: '',
  terceroIds: [], // Antes terceroId
  cuentaIds: [], // Antes cuentaId
  centroCostoIds: [], // Antes centroCostoId
  productoIds: [], // NUEVO: Filtro Productos
  conceptoKeyword: '',
  valorOperador: 'mayor',
  valorMonto: '',
  traerTodo: false,
  terceroKeyword: '',
  esCliente: null,
  esProveedor: null,
  cuentaCodigoKeyword: '',
  cuentaNivel: '',
  permiteMovimiento: null,
  pagina: 1,
};

// Estilos reusables (Manual v2.0)
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white";
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";

export default function SuperInformePage() {
  const { user, authLoading } = useAuth();
  const [maestros, setMaestros] = useState({ tiposDocumento: [], terceros: [], cuentas: [], centrosCosto: [], productos: [] }); // Añadir productos
  const [filtros, setFiltros] = useState(INITIAL_FILTROS_STATE);
  const [resultados, setResultados] = useState([]);

  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);

  const [pagination, setPagination] = useState({
    total_registros: 0,
    total_paginas: 1,
    pagina_actual: 1
  });

  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState(null);
  const [isLoadingMaestros, setIsLoadingMaestros] = useState(true);
  const [dynamicHeaders, setDynamicHeaders] = useState([]);

  const dataFetchedRef = useRef(false);

  const fetchMaestros = useCallback(async () => {
    if (!user?.empresaId) return;
    setIsLoadingMaestros(true);
    try {
      const results = await Promise.allSettled([
        apiService.get('/tipos-documento/'),
        apiService.get('/terceros/'),
        apiService.get('/plan-cuentas/list-flat/'),
        apiService.get('/centros-costo/get-flat'),
        apiService.get('/inventario/productos/list-flat/')
      ]);

      setMaestros({
        tiposDocumento: results[0].status === 'fulfilled' ? results[0].value.data : [],
        terceros: results[1].status === 'fulfilled' ? (results[1].value.data.terceros || results[1].value.data || []) : [],
        cuentas: results[2].status === 'fulfilled' ? results[2].value.data : [],
        centrosCosto: results[3].status === 'fulfilled' ? results[3].value.data : [],
        productos: results[4].status === 'fulfilled' ? results[4].value.data : []
      });
      setError(null);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'No se pudieron cargar los datos maestros.';
      setError(errorMsg);
    } finally {
      setIsLoadingMaestros(false);
    }
  }, [user?.empresaId]);

  useEffect(() => {
    if (authLoading || dataFetchedRef.current) return;
    if (user) {
      fetchMaestros();
      dataFetchedRef.current = true;
    }
  }, [authLoading, user, fetchMaestros]);

  const preparePayload = (filtrosActuales) => {
    const payload = { ...filtrosActuales };
    for (const key in payload) {
      if (payload[key] === '' || payload[key] === null || (Array.isArray(payload[key]) && payload[key].length === 0)) {
        delete payload[key];
      }
    }
    if (payload.valorMonto) {
      payload.valorMonto = parseFloat(payload.valorMonto);
    }
    return payload;
  };

  const handleFiltroChange = (e) => {
    // Manejo Legacy para inputs normales
    const { name, value, type, checked } = e.target;
    let finalValue;
    if (type === 'checkbox') finalValue = checked;
    else if (['esCliente', 'esProveedor', 'permiteMovimiento'].includes(name)) finalValue = value === "true" ? true : value === "false" ? false : null;
    else finalValue = value;
    setFiltros(prev => ({ ...prev, [name]: finalValue, pagina: 1 }));
  };

  // Manejador Específico para MultiSelect
  const handleMultiSelectChange = (name, newValue) => {
    setFiltros(prev => ({ ...prev, [name]: newValue, pagina: 1 }));
  };

  const handleTipoEntidadChange = (e) => {
    const newTipoEntidad = e.target.value;
    setFiltros({ ...INITIAL_FILTROS_STATE, tipoEntidad: newTipoEntidad });
    setResultados([]);
    setPagination({ total_registros: 0, total_paginas: 1, pagina_actual: 1 });
    setError(null);
  };

  const handleLimpiarFiltros = () => {
    setFiltros({ ...INITIAL_FILTROS_STATE, tipoEntidad: filtros.tipoEntidad });
    setResultados([]);
    setError(null);
  };

  const handleBuscar = useCallback(async (pagina = 1) => {
    setIsSearching(true);
    setError(null);
    if (pagina === 1) {
      setResultados([]);
      setDynamicHeaders([]);
    }

    const filtrosConPagina = { ...filtros, pagina };

    try {
      const payloadLimpio = preparePayload(filtrosConPagina);
      const response = await apiService.post('/reports/super-informe', payloadLimpio);

      const data = response.data;
      if (data && Array.isArray(data.resultados) && data.resultados.length > 0) {
        setResultados(data.resultados);
        setPagination({
          total_registros: data.total_registros,
          total_paginas: data.total_paginas,
          pagina_actual: data.pagina_actual
        });
        const headersToShow = Object.keys(data.resultados[0]).filter(key => !['estado', 'anulado', 'documento_id', 'movimiento_id', 'usuario_creador_id', 'usuario_operacion_id'].includes(key));
        setDynamicHeaders(headersToShow);
      } else {
        setResultados([]);
        setPagination({ total_registros: 0, total_paginas: 1, pagina_actual: 1 });
        setError('No se encontraron resultados que coincidan con la búsqueda.');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al realizar la búsqueda.');
    } finally {
      setIsSearching(false);
    }
  }, [filtros]);

  const handlePageChange = (newPage) => {
    handleBuscar(newPage);
  };

  const handleExportPDF = async () => {
    if (resultados.length === 0) return alert("No hay datos para generar el PDF.");

    setIsSearching(true);
    setError(null);

    try {
      const payloadSinPagina = { ...filtros, traerTodo: true };
      const payloadLimpio = preparePayload(payloadSinPagina);

      const response = await apiService.post('/reports/super-informe/get-signed-url', payloadLimpio);
      const signedToken = response.data.signed_url_token;

      if (!signedToken) throw new Error("No se recibió token de descarga.");

      const pdfUrl = `${process.env.NEXT_PUBLIC_API_URL}/api/reports/super-informe/imprimir?signed_token=${signedToken}`;

      const link = document.createElement('a');
      link.href = pdfUrl;
      link.setAttribute('download', `Super_Informe.pdf`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || "Error al iniciar la descarga del PDF.");
    } finally {
      setIsSearching(false);
    }
  };

  if (authLoading || isLoadingMaestros) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
        <FaTable className="text-indigo-300 text-6xl mb-4 animate-pulse" />
        <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando Super Informe...</p>
      </div>
    );
  }

  // FUNCIÓN DE RENDERIZADO DE CELDA MEJORADA
  const renderCell = (item, header) => {
    const value = item[header];
    if (typeof value === 'boolean') return value ? 'Sí' : 'No';

    const headerLower = header.toLowerCase();

    // Alineación y formato para Moneda
    if (['debito', 'credito', 'total', 'saldo', 'valor'].some(h => headerLower.includes(h))) {
      return <div className="text-right font-mono text-gray-700">{formatCurrency(value)}</div>;
    }

    // Formato Fecha
    if (headerLower.includes('fecha')) {
      return <div className="text-center text-gray-600 text-xs">{value ? new Date(value + 'T00:00:00').toLocaleDateString('es-CO') : 'N/A'}</div>;
    }

    // Formato para Cuentas
    if (headerLower.includes('cuenta_codigo')) {
      return <div className="font-mono font-bold text-indigo-700">{value}</div>;
    }

    // Formato para Conceptos Largos
    if (headerLower.includes('concepto') || headerLower.includes('justificacion')) {
      return <div className="truncate max-w-xs" title={value}>{value}</div>;
    }

    return <div className="text-gray-700">{value ?? 'N/A'}</div>;
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
      <div className="max-w-full mx-auto"> {/* Ancho completo para acomodar muchas columnas */}

        {/* HEADER */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
          <div>
            <BotonRegresar />
            <div className="flex items-center gap-3 mt-3">
              <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                <FaTable className="text-2xl" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-800">Super Informe</h1>
                <p className="text-gray-500 text-sm">Consultas avanzadas de movimientos y maestros.</p>
              </div>
            </div>
          </div>
        </div>
        <button
          onClick={() => window.open('/manual?file=capitulo_33_super_informe.md', '_blank')}
          className="text-indigo-600 hover:bg-indigo-50 px-3 py-1 rounded-md flex items-center gap-2 transition-colors"
          title="Ver Manual de Usuario"
        >
          <FaBook className="text-lg" /> <span className="font-bold text-sm">Manual</span>
        </button>


        {/* PANEL DE FILTROS (CARD 1) */}
        <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 animate-fadeIn mb-8">

          {/* Nivel 1: Filtros Esenciales */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 mb-6 items-end">
            <div className="md:col-span-4">
              <label htmlFor="tipoEntidad" className={labelClass}>Consultar en:</label>
              <select name="tipoEntidad" value={filtros.tipoEntidad} onChange={handleTipoEntidadChange} className={inputClass}>
                <option value="movimientos">Movimientos Contables</option>
                <option value="terceros">Maestro de Terceros</option>
                <option value="cuentas">Plan de Cuentas (PUC)</option>
              </select>
            </div>

            {filtros.tipoEntidad === 'movimientos' && (
              <>
                <div className="md:col-span-3">
                  <label className={labelClass}>Fecha Desde</label>
                  <input type="date" name="fechaInicio" value={filtros.fechaInicio} onChange={handleFiltroChange} className={inputClass} />
                </div>
                <div className="md:col-span-3">
                  <label className={labelClass}>Fecha Hasta</label>
                  <input type="date" name="fechaFin" value={filtros.fechaFin} onChange={handleFiltroChange} className={inputClass} />
                </div>
                <div className="md:col-span-2">
                  <label className={labelClass}>Estado</label>
                  <select name="estadoDocumento" value={filtros.estadoDocumento} onChange={handleFiltroChange} className={inputClass}>
                    <option value="activos">Activos</option>
                    <option value="anulados">Anulados</option>
                    <option value="eliminados">Eliminados</option>
                  </select>
                </div>
              </>
            )}
          </div>

          {/* Nivel 2: Filtros Avanzados (Acordeón) */}
          {filtros.tipoEntidad === 'movimientos' && (
            <div className="border-t border-gray-100 pt-4">
              <button
                onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                className="flex items-center text-sm font-bold text-indigo-600 hover:text-indigo-800 focus:outline-none transition-colors"
              >
                <FaFilter className="mr-2" />
                {showAdvancedFilters ? 'Ocultar Filtros Avanzados' : 'Mostrar Filtros Avanzados'}
                {showAdvancedFilters ? <FaChevronUp className="ml-1" /> : <FaChevronDown className="ml-1" />}
              </button>

              {showAdvancedFilters && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6 bg-indigo-50/30 p-5 rounded-xl border border-indigo-100 animate-slideDown">
                  {/* Bloque Documento */}
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Filtros de Documento</h4>
                    <MultiSelect
                      label="Tipo Documento"
                      placeholder="Todos los Tipos..."
                      options={maestros.tiposDocumento.map(td => ({ value: td.id, label: td.nombre }))}
                      value={filtros.tipoDocIds}
                      onChange={(val) => handleMultiSelectChange('tipoDocIds', val)}
                    />
                    <div><label className={labelClass}>Número Doc.</label><input type="text" name="numero" placeholder="Ej: 101" value={filtros.numero} onChange={handleFiltroChange} className={inputClass} /></div>
                    <div><label className={labelClass}>Concepto (Palabra Clave)</label><input type="text" name="conceptoKeyword" placeholder="Ej: Venta..." value={filtros.conceptoKeyword} onChange={handleFiltroChange} className={inputClass} /></div>
                  </div>

                  {/* Bloque Contable */}
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Filtros Contables</h4>
                    <MultiSelect
                      label="Tercero (Beneficiario)"
                      placeholder="Todos los Terceros..."
                      options={maestros.terceros.map(t => ({ value: t.id, label: t.razon_social }))}
                      value={filtros.terceroIds}
                      onChange={(val) => handleMultiSelectChange('terceroIds', val)}
                    />
                    <MultiSelect
                      label="Cuentas Contables"
                      placeholder="Todas las Cuentas..."
                      options={maestros.cuentas.map(c => ({ value: c.id, label: `${c.codigo} - ${c.nombre}` }))}
                      value={filtros.cuentaIds}
                      onChange={(val) => handleMultiSelectChange('cuentaIds', val)}
                    />
                    <MultiSelect
                      label="Centros de Costo"
                      placeholder="Todos los CC..."
                      options={maestros.centrosCosto.map(cc => ({ value: cc.id, label: cc.nombre }))}
                      value={filtros.centroCostoIds}
                      onChange={(val) => handleMultiSelectChange('centroCostoIds', val)}
                    />
                  </div>

                  {/* Bloque Valores */}
                  <div className="space-y-3 md:col-span-1">
                    <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Filtros de Valor</h4>
                    <div className="grid grid-cols-2 gap-2">
                      <div><label className={labelClass}>Condición</label><select name="valorOperador" value={filtros.valorOperador} onChange={handleFiltroChange} className={inputClass}><option value="mayor">Mayor que</option><option value="menor">Menor que</option><option value="igual">Igual a</option></select></div>
                      <div><label className={labelClass}>Monto</label><input type="number" name="valorMonto" placeholder="0" value={filtros.valorMonto} onChange={handleFiltroChange} className={inputClass} /></div>
                    </div>

                    <div className="space-y-3 mt-4 md:mt-0">
                      <h4 className="text-xs font-bold text-indigo-500 uppercase tracking-wider">Filtros de Inventario (NUEVO)</h4>
                      <MultiSelect
                        label="Productos"
                        placeholder="Todos los Productos..."
                        options={maestros.productos.map(p => ({ value: p.id, label: `${p.codigo} - ${p.nombre}` }))}
                        value={filtros.productoIds}
                        onChange={(val) => handleMultiSelectChange('productoIds', val)}
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Botones de Acción */}
          <div className="flex flex-col md:flex-row justify-between items-center gap-4 mt-6 pt-4 border-t border-gray-100">
            <div className="flex items-center">
              <input id="traerTodo" name="traerTodo" type="checkbox" checked={filtros.traerTodo} onChange={handleFiltroChange} className="checkbox checkbox-sm checkbox-primary mr-2 cursor-pointer" />
              <label htmlFor="traerTodo" className="text-sm font-medium text-gray-600 cursor-pointer select-none">Traer TODO para Exportar PDF (Puede ser lento)</label>
            </div>

            <div className="flex gap-3">
              <button onClick={handleLimpiarFiltros} disabled={isSearching} className="btn btn-ghost btn-sm text-gray-500 hover:bg-gray-100">
                <FaEraser className="mr-2" /> Limpiar
              </button>

              <button onClick={() => handleBuscar(1)} disabled={isSearching} className="px-8 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg shadow-md font-bold flex items-center transition-all transform hover:-translate-y-0.5">
                {isSearching ? <><span className="loading loading-spinner loading-sm mr-2"></span> Buscando...</> : <><FaSearch className="mr-2" /> Generar Informe</>}
              </button>
            </div>
          </div>
        </div>

        {/* MENSAJES DE ERROR */}
        {
          error && (
            <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-4 rounded-r-lg mb-6 shadow-sm flex items-center gap-3 animate-pulse">
              <span>{error}</span>
            </div>
          )
        }

        {/* CARD 2: RESULTADOS */}
        {
          resultados.length > 0 && (
            <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden animate-slideDown">
              {/* Cabecera Tabla */}
              <div className="p-4 bg-gray-50 border-b border-gray-200 flex justify-between items-center">
                <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                  Resultados
                  <span className="bg-gray-200 text-gray-700 px-2 py-0.5 rounded-md text-xs font-mono">
                    {pagination.total_registros} registros
                  </span>
                </h2>
                <button onClick={handleExportPDF} className="flex items-center gap-2 px-4 py-2 bg-white border border-red-500 text-red-600 rounded-lg hover:bg-red-50 font-medium transition-colors shadow-sm text-sm" disabled={isSearching}>
                  <FaFilePdf /> Exportar PDF
                </button>
              </div>

              {/* Tabla */}
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-slate-100 text-gray-600 uppercase text-xs font-bold">
                    <tr>
                      {dynamicHeaders.map(key => (
                        <th key={key} className="py-3 px-4 text-left whitespace-nowrap tracking-wider">
                          {key.replace(/_/g, ' ')}
                        </th>
                      ))}
                    </tr>
                  </thead>

                  <tbody className="bg-white divide-y divide-gray-100 text-sm">
                    {resultados.map((item, index) => (
                      <tr
                        key={`${item.movimiento_id || item.id}-${index}`}
                        className={`hover:bg-indigo-50/20 transition-colors ${item.estado === 'ANULADO' ? 'bg-yellow-50 text-yellow-800' : item.estado === 'ELIMINADO' ? 'bg-red-50 text-red-800' : ''}`}
                      >
                        {dynamicHeaders.map(header => (
                          <td key={`${item.movimiento_id || item.id}-${header}-${index}`} className="py-2 px-4 whitespace-nowrap">
                            {renderCell(item, header)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Paginación */}
              <div className="p-4 border-t border-gray-100 bg-gray-50">
                <Paginacion
                  paginaActual={pagination.pagina_actual}
                  totalPaginas={pagination.total_paginas}
                  onPageChange={handlePageChange}
                />
              </div>
            </div>
          )
        }
      </div >
    </div >
  );
}