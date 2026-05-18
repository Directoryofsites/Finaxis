'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  FaBalanceScale,
  FaCalendarAlt,
  FaSearch,
  FaFilePdf,
  FaFileCsv,
  FaFilter,
  FaLayerGroup,
  FaExclamationTriangle,
  FaCheckCircle,
  FaBook,
  FaChartLine
} from 'react-icons/fa';
import { toast } from 'react-toastify';

import { useAuth } from '../../../../app/context/AuthContext';
import { apiService } from '../../../../lib/apiService';
import { useAIAutomation } from '../../../hooks/useAIAutomation';

// Estilos Reusables
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none pl-10";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white pl-10";

const NOMBRES_MESES = {
  1: "Enero",
  2: "Febrero",
  3: "Marzo",
  4: "Abril",
  5: "Mayo",
  6: "Junio",
  7: "Julio",
  8: "Agosto",
  9: "Septiembre",
  10: "Octubre",
  11: "Noviembre",
  12: "Diciembre"
};

export default function ComparacionSaldosPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
        <FaChartLine className="text-indigo-300 text-6xl mb-4 animate-pulse" />
        <p className="text-indigo-600 font-semibold text-lg animate-pulse">Iniciando Reporte de Comparación...</p>
      </div>
    }>
      <ComparacionSaldosContent />
    </Suspense>
  );
}

function ComparacionSaldosContent() {
  const { user, authLoading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  const anioActual = new Date().getFullYear();
  const [filtros, setFiltros] = useState({
    anio: anioActual,
    cuenta_codigo: '',
    nivel_maximo: 9,
    tipo_filtro: 'TODAS', // TODAS, BALANCE, RESULTADOS
    mes_inicio: 1,
    mes_fin: 12
  });

  const [reportData, setReportData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isPageReady, setPageReady] = useState(false);

  // Generar lista de años para el select
  const añosList = [];
  for (let a = anioActual; a >= anioActual - 6; a--) {
    añosList.push(a);
  }

  // Verificar sesión
  useEffect(() => {
    if (!authLoading) {
      if (user && user.empresaId) {
        setPageReady(true);
      } else {
        router.push('/login');
      }
    }
  }, [user, authLoading, router]);

  function parseBackendError(err, defaultMsg) {
    if (!err?.response?.data) {
      return err?.message || defaultMsg;
    }
    const data = err.response.data;
    if (typeof data.detail === 'string') {
      return data.detail;
    }
    if (Array.isArray(data.detail)) {
      return data.detail.map(d => `${d.loc ? d.loc.join('.') : 'campo'}: ${d.msg}`).join(', ');
    }
    if (data.detail && typeof data.detail === 'object') {
      return data.detail.message || JSON.stringify(data.detail);
    }
    if (data.message) {
      return data.message;
    }
    return defaultMsg;
  }

  function handleFiltroChange(e) {
    const { name, value } = e.target;
    setFiltros(prev => ({ 
      ...prev, 
      [name]: name === 'anio' || name === 'nivel_maximo' || name === 'mes_inicio' || name === 'mes_fin' 
        ? parseInt(value, 10) 
        : value 
    }));
  }

  async function handleGenerateReport() {
    setIsLoading(true);
    setError('');
    setReportData(null);

    try {
      const params = { ...filtros };
      if (!params.cuenta_codigo) delete params.cuenta_codigo;

      const res = await apiService.post('/reports/comparacion-saldos', params);
      setReportData(res.data);
    } catch (err) {
      setError(parseBackendError(err, 'Error al generar el reporte de comparación.'));
    } finally {
      setIsLoading(false);
    }
  }

  async function handleExportPDF() {
    if (!reportData) {
      setError("Primero debe generar un reporte para poder exportarlo.");
      return;
    }
    setIsLoading(true);
    setError('');
    try {
      const params = { ...filtros };
      if (!params.cuenta_codigo) delete params.cuenta_codigo;

      const res = await apiService.post('/reports/comparacion-saldos/get-signed-url', params);
      const token = res.data.signed_url_token;
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const pdfUrl = `${baseUrl}/api/reports/comparacion-saldos/imprimir?signed_token=${token}`;
      window.open(pdfUrl, '_blank');
    } catch (err) {
      setError(parseBackendError(err, 'Error al generar el PDF.'));
    } finally {
      setIsLoading(false);
    }
  }

  async function handleExportCSV() {
    if (!reportData) {
      setError("Primero debe generar un reporte para poder exportarlo.");
      return;
    }
    setIsLoading(true);
    setError('');
    try {
      const params = { ...filtros };
      if (!params.cuenta_codigo) delete params.cuenta_codigo;

      const res = await apiService.post('/reports/comparacion-saldos/csv', params, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `comparacion_saldos_${filtros.anio}.csv`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      toast.success("✅ CSV descargado correctamente");
    } catch (err) {
      setError(parseBackendError(err, 'Error al exportar a CSV.'));
    } finally {
      setIsLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter') {
      handleGenerateReport();
    }
  }

  function formatCurrency(value) {
    return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 2 }).format(value || 0);
  }

  function getNivelClass(nivel) {
    switch (nivel) {
      case 1: return 'bg-indigo-50 font-bold text-indigo-900';
      case 2: return 'bg-slate-50 font-semibold text-slate-800';
      case 3: return 'text-gray-700 font-medium';
      default: return 'text-gray-600';
    }
  }

  function getPaddingClass(nivel) {
    switch (nivel) {
      case 1: return '';
      case 2: return 'pl-4';
      case 3: return 'pl-8';
      default: return 'pl-12 border-l-2 border-indigo-100';
    }
  }

  // Integración con automatización IA
  useAIAutomation(isPageReady, filtros, setFiltros, handleGenerateReport);

  if (!isPageReady) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
        <FaChartLine className="text-indigo-300 text-6xl mb-4 animate-pulse" />
        <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando Comparación de Saldos...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
      <div className="max-w-7xl mx-auto">

        {/* ENCABEZADO */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
          <div>
            <div className="flex items-center gap-3 mt-3">
              <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                <FaChartLine className="text-2xl" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-800">Comparación Mensual de Saldos</h1>
                <p className="text-gray-500 text-sm">Evolución de saldos históricos a fin de mes por columnas.</p>
              </div>
            </div>
          </div>
        </div>

        {/* CARD 1: FILTROS */}
        <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 animate-fadeIn mb-8">
          <div className="flex items-center gap-2 mb-6 border-b border-gray-100 pb-2">
            <FaFilter className="text-indigo-500" />
            <h2 className="text-lg font-bold text-gray-700">Configuración del Reporte</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4 items-end">
            {/* Año */}
            <div>
              <label className={labelClass}>Año</label>
              <div className="relative">
                <select name="anio" value={filtros.anio} onChange={handleFiltroChange} className={selectClass}>
                  {añosList.map(a => (
                    <option key={a} value={a}>{a}</option>
                  ))}
                </select>
                <FaCalendarAlt className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
              </div>
            </div>

            {/* Rango Meses - Inicio */}
            <div>
              <label className={labelClass}>Mes Inicio</label>
              <div className="relative">
                <select name="mes_inicio" value={filtros.mes_inicio} onChange={handleFiltroChange} className={selectClass}>
                  {Object.entries(NOMBRES_MESES).map(([num, nombre]) => (
                    <option key={num} value={num}>{nombre}</option>
                  ))}
                </select>
                <FaCalendarAlt className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
              </div>
            </div>

            {/* Rango Meses - Fin */}
            <div>
              <label className={labelClass}>Mes Fin</label>
              <div className="relative">
                <select name="mes_fin" value={filtros.mes_fin} onChange={handleFiltroChange} className={selectClass}>
                  {Object.entries(NOMBRES_MESES).map(([num, nombre]) => (
                    <option key={num} value={num}>{nombre}</option>
                  ))}
                </select>
                <FaCalendarAlt className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
              </div>
            </div>

            {/* Nivel de Detalle */}
            <div>
              <label className={labelClass}>Nivel Detalle</label>
              <div className="relative">
                <select name="nivel_maximo" value={filtros.nivel_maximo} onChange={handleFiltroChange} className={selectClass}>
                  <option value="1">1 (Clase)</option>
                  <option value="2">2 (Grupo)</option>
                  <option value="3">3 (Cuenta)</option>
                  <option value="4">4 (Subcuenta)</option>
                  <option value="5">5 (Auxiliar)</option>
                  <option value="6">6</option>
                  <option value="7">7</option>
                  <option value="8">8</option>
                  <option value="9">9 (Máximo)</option>
                </select>
                <FaLayerGroup className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
              </div>
            </div>

            {/* Tipo de Cuentas */}
            <div>
              <label className={labelClass}>Tipo Filtro</label>
              <div className="relative">
                <select name="tipo_filtro" value={filtros.tipo_filtro} onChange={handleFiltroChange} className={selectClass}>
                  <option value="TODAS">Todas las Cuentas</option>
                  <option value="BALANCE">Cuentas Balance (1-3)</option>
                  <option value="RESULTADOS">Cuentas Resultados (4-7)</option>
                </select>
                <FaFilter className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
              </div>
            </div>

            {/* Código Cuenta */}
            <div>
              <label className={labelClass}>Cuenta PUC Específica</label>
              <div className="relative">
                <input
                  type="text"
                  name="cuenta_codigo"
                  value={filtros.cuenta_codigo}
                  onChange={handleFiltroChange} onKeyDown={handleKeyDown}
                  placeholder="Ej: 1105, 21"
                  className={inputClass}
                  autoComplete="off"
                />
                <FaSearch className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
              </div>
            </div>
          </div>

          <div className="flex flex-col md:flex-row justify-end gap-3 mt-6 pt-4 border-t border-gray-100">
            <button
              onClick={handleGenerateReport}
              disabled={isLoading}
              className={`
                px-6 py-2 rounded-lg shadow-md font-bold text-white transition-all transform hover:-translate-y-0.5 flex items-center justify-center gap-2 w-full md:w-auto
                ${isLoading ? 'bg-gray-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'}
              `}
            >
              {isLoading ? <span className="loading loading-spinner loading-sm"></span> : <><FaSearch /> Consultar</>}
            </button>

            <button
              onClick={handleExportCSV}
              disabled={!reportData || isLoading}
              className={`
                px-6 py-2 rounded-lg shadow-md font-bold border transition-all transform hover:-translate-y-0.5 flex items-center justify-center gap-2 w-full md:w-auto
                ${!reportData || isLoading
                  ? 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed'
                  : 'bg-white text-emerald-600 border-emerald-100 hover:bg-emerald-50'}
              `}
            >
              <FaFileCsv /> Exportar CSV
            </button>

            <button
              onClick={handleExportPDF}
              disabled={!reportData || isLoading}
              className={`
                px-6 py-2 rounded-lg shadow-md font-bold border transition-all transform hover:-translate-y-0.5 flex items-center justify-center gap-2 w-full md:w-auto
                ${!reportData || isLoading
                  ? 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed'
                  : 'bg-white text-red-600 border-red-100 hover:bg-red-50'}
              `}
            >
              <FaFilePdf /> Exportar PDF
            </button>
          </div>

          {error && (
            <div className="mt-4 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded-r-lg flex items-center gap-3 animate-pulse">
              <FaExclamationTriangle className="text-xl" />
              <p className="font-bold">{error}</p>
            </div>
          )}
        </div>

        {/* CARD 2: RESULTADOS */}
        {reportData && (
          <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden animate-slideDown">
            <div className="p-6 bg-gray-50 border-b border-gray-200 flex flex-col md:flex-row justify-between items-center gap-4">
              <div>
                <h2 className="text-xl font-bold text-gray-800">{user?.nombre_empresa}</h2>
                <p className="text-sm text-gray-600 font-medium mt-1">
                  Reporte de saldos del año <span className="text-indigo-600">{filtros.anio}</span>
                </p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-slate-100 text-gray-700">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider w-24">Código</th>
                    <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider min-w-[200px]">Nombre Cuenta</th>
                    <th className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider w-36 bg-slate-50">Saldo Inicial</th>
                    {reportData.meses.map(m => (
                      <th key={m} className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider w-36">
                        {NOMBRES_MESES[m]}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-100">
                  {reportData.filas.map(fila => (
                    <tr key={fila.codigo} className={`hover:bg-indigo-50/20 transition-colors ${getNivelClass(fila.nivel)}`}>
                      {/* Código de cuenta */}
                      <td className="px-4 py-2 font-mono text-sm whitespace-nowrap">
                        <a
                          href={`/contabilidad/reportes/auxiliar-cuenta?cuenta=${fila.codigo}&fecha_inicio=${filtros.anio}-01-01&fecha_fin=${filtros.anio}-12-31`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-indigo-600 hover:text-indigo-800 hover:underline flex items-center gap-1"
                          title="Ver Auxiliar detallado"
                        >
                          {fila.codigo} <FaBook className="text-xs opacity-50" />
                        </a>
                      </td>

                      {/* Nombre de cuenta */}
                      <td className={`px-4 py-2 text-sm ${getPaddingClass(fila.nivel)} whitespace-nowrap overflow-hidden text-ellipsis max-w-[250px]`}>
                        <a
                          href={`/contabilidad/reportes/auxiliar-cuenta?cuenta=${fila.codigo}&fecha_inicio=${filtros.anio}-01-01&fecha_fin=${filtros.anio}-12-31`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="hover:text-indigo-700 hover:underline cursor-pointer block"
                          title="Ver Auxiliar detallado"
                        >
                          {fila.nombre}
                        </a>
                      </td>

                      {/* Saldo Inicial */}
                      <td className="px-4 py-2 text-right font-mono text-sm bg-slate-50/50">
                        {formatCurrency(fila.saldo_inicial)}
                      </td>

                      {/* Columnas de meses dinámicas */}
                      {reportData.meses.map(m => {
                        const val = fila.saldos_mensuales[m] || 0;
                        return (
                          <td key={m} className="px-4 py-2 text-right font-mono text-sm">
                            {formatCurrency(val)}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
