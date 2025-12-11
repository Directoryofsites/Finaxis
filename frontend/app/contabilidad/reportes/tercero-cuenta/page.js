'use client';

import React, { useState, useEffect, useRef } from 'react';
import Script from 'next/script';
import { useRouter } from 'next/navigation';
import {
  FaUserTag,
  FaListOl,
  FaCalendarAlt,
  FaSearch,
  FaFileCsv,
  FaFilePdf,
  FaSync,
  FaExclamationTriangle,
  FaCheckCircle,
  FaFilter,
  FaBook
} from 'react-icons/fa';

import BotonRegresar from '../../../components/BotonRegresar';
import { useAuth } from '../../../context/AuthContext';
import { apiService } from '../../../../lib/apiService';
import { recalcularSaldosTercero } from '../../../../lib/reportesService';

// --- ESTILOS REUSABLES (Manual v2.0) ---
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none pl-10";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white pl-10";
const multiSelectClass = "w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white h-32";

const MultiSelect = ({ options, selected, onChange }) => {
  const handleSelect = (e) => {
    const selectedOptions = Array.from(e.target.selectedOptions, option => option.value);
    onChange(selectedOptions);
  };
  return (
    <div className="relative">
      <select multiple={true} value={selected} onChange={handleSelect} className={multiSelectClass}>
        <option value="all">-- Todas las Cuentas --</option>
        {options.map(option => (
          <option key={option.id} value={option.id}>
            {option.codigo} - {option.nombre}
          </option>
        ))}
      </select>
    </div>
  );
};

export default function ReporteTerceroCuentaPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const dataFetchedRef = useRef(false);

  // Estados
  const [terceros, setTerceros] = useState([]);
  const [selectedTercero, setSelectedTercero] = useState('');
  const [cuentasDelTercero, setCuentasDelTercero] = useState([]);
  const [selectedCuentas, setSelectedCuentas] = useState(['all']);
  const [fechas, setFechas] = useState({ inicio: '', fin: '' });

  const [reportData, setReportData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [recalculoStatus, setRecalculoStatus] = useState({ loading: false, message: '', error: '' });
  const [isPageReady, setPageReady] = useState(false);

  // Autenticación
  useEffect(() => {
    if (!authLoading) {
      if (user && user.empresaId) {
        setPageReady(true);
      } else {
        router.push('/login');
      }
    }
  }, [user, authLoading, router]);

  // Carga de Terceros (Protegida)
  useEffect(() => {
    if (authLoading || dataFetchedRef.current) return;
    if (user) {
      const fetchTerceros = async () => {
        try {
          const res = await apiService.get('/terceros');
          setTerceros(res.data);
        } catch (err) {
          setError("Error cargando terceros: " + (err.response?.data?.detail || err.message));
        }
      };
      fetchTerceros();
      dataFetchedRef.current = true;
    }
  }, [user, authLoading]);

  // Carga de Cuentas al seleccionar Tercero
  useEffect(() => {
    if (selectedTercero && !authLoading && user) {
      const fetchCuentas = async () => {
        try {
          const res = await apiService.get(`/terceros/${selectedTercero}/cuentas`);
          setCuentasDelTercero(res.data);
          setSelectedCuentas(['all']);
        } catch (err) {
          setError("Error cargando cuentas del tercero: " + (err.response?.data?.detail || err.message));
        }
      };
      fetchCuentas();
    } else {
      setCuentasDelTercero([]);
      setSelectedCuentas(['all']);
    }
  }, [selectedTercero, user, authLoading]);

  const handleGenerateReport = async () => {
    if (!selectedTercero || !fechas.inicio || !fechas.fin) {
      setError("Por favor, seleccione un tercero y un rango de fechas.");
      return;
    }
    setIsLoading(true);
    setError(null);
    setReportData(null);
    setRecalculoStatus({ loading: false, message: '', error: '' });

    const params = {
      tercero_id: selectedTercero,
      fecha_inicio: fechas.inicio,
      fecha_fin: fechas.fin,
    };
    if (selectedCuentas.length > 0 && !selectedCuentas.includes('all')) {
      params.cuenta_ids = selectedCuentas.join(',');
    }

    try {
      const res = await apiService.get('/reports/tercero-cuenta', { params: params });
      setReportData(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al generar el reporte.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRecalcularSaldos = async () => {
    if (!selectedTercero) {
      setRecalculoStatus({ loading: false, message: '', error: 'Debe seleccionar un tercero.' });
      return;
    }
    const terceroNombre = terceros.find(t => t.id == selectedTercero)?.razon_social || `ID ${selectedTercero}`;
    if (!window.confirm(`¿Desea recalcular saldos y cruces para "${terceroNombre}"?\n\nEsta operación reconstruirá el historial de pagos.`)) {
      return;
    }

    setRecalculoStatus({ loading: true, message: 'Procesando...', error: '' });
    setError(null);

    try {
      const response = await recalcularSaldosTercero(selectedTercero);
      setRecalculoStatus({ loading: false, message: response.data.message, error: '' });
      if (fechas.inicio && fechas.fin) handleGenerateReport();
    } catch (err) {
      setRecalculoStatus({ loading: false, message: '', error: err.response?.data?.detail || 'Error en recálculo.' });
    }
  };

  const handleExportCSV = () => {
    if (!reportData) return;
    if (typeof window.Papa === 'undefined') return alert("Librería CSV no lista.");

    const dataToExport = [];
    dataToExport.push(['Fecha', 'Documento', 'Cuenta', 'Concepto', 'Débito', 'Crédito', 'Saldo Parcial']);
    dataToExport.push(['', '', '', 'SALDO INICIAL TERCERO', '', '', parseFloat(reportData.saldoAnterior).toFixed(2)]);

    let currentCuentaId = null;
    for (const mov of reportData.movimientos) {
      if (mov.cuenta_id !== currentCuentaId) {
        currentCuentaId = mov.cuenta_id;
        const saldoInicial = reportData.saldos_iniciales_por_cuenta[String(mov.cuenta_id)] || 0;
        dataToExport.push(['', '', `${mov.cuenta_codigo} - ${mov.cuenta_nombre}`, 'SALDO INICIAL CUENTA', '', '', parseFloat(saldoInicial).toFixed(2)]);
      }
      dataToExport.push([
        new Date(mov.fecha).toLocaleDateString('es-CO', { timeZone: 'UTC' }),
        `${mov.tipo_documento} #${mov.numero_documento}`,
        `${mov.cuenta_codigo} - ${mov.cuenta_nombre}`,
        mov.concepto,
        parseFloat(mov.debito).toFixed(2),
        parseFloat(mov.credito).toFixed(2),
        parseFloat(mov.saldo_parcial).toFixed(2)
      ]);
    }
    const finalBalance = reportData.movimientos.length > 0 ? parseFloat(reportData.movimientos[reportData.movimientos.length - 1].saldo_parcial) : parseFloat(reportData.saldoAnterior);
    dataToExport.push(['', '', '', 'SALDO FINAL TERCERO', '', '', finalBalance.toFixed(2)]);

    const csv = window.Papa.unparse(dataToExport);
    const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    const terceroName = terceros.find(t => t.id == selectedTercero)?.razon_social.replace(/ /g, '_') || 'tercero';
    link.setAttribute('download', `Auxiliar_${terceroName}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleExportPDF = async () => {
    if (!reportData) return;
    setIsLoading(true);
    setError(null);
    try {
      const params = {
        fecha_inicio: fechas.inicio,
        fecha_fin: fechas.fin,
        tercero_id: selectedTercero,
      };
      if (selectedCuentas.length > 0 && !selectedCuentas.includes('all')) {
        params.cuenta_ids = selectedCuentas.join(',');
      }
      const res = await apiService.get('/reports/tercero-cuenta/get-signed-url', { params });
      const token = res.data.signed_url_token;
      const pdfUrl = `${process.env.NEXT_PUBLIC_API_URL}/api/reports/tercero-cuenta/imprimir?signed_token=${token}`;

      const link = document.createElement('a');
      link.href = pdfUrl;
      link.setAttribute('download', `Auxiliar_Tercero_${fechas.inicio}.pdf`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error PDF.');
    } finally {
      setIsLoading(false);
    }
  };

  const formatCurrency = (val) => {
    return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 2 }).format(val || 0);
  };

  if (!isPageReady) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
        <FaUserTag className="text-indigo-300 text-6xl mb-4 animate-pulse" />
        <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando Auditoría de Terceros...</p>
      </div>
    );
  }

  return (
    <>
      <Script src="https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js" />

      <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
        <div className="max-w-7xl mx-auto">

          {/* ENCABEZADO */}
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
            <div>
              <BotonRegresar />
              <div className="flex items-center gap-3 mt-3">
                <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                  <FaUserTag className="text-2xl" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold text-gray-800">Auxiliar por Tercero</h1>
                  <p className="text-gray-500 text-sm">Auditoría detallada de movimientos por cuenta para un tercero.</p>
                </div>
              </div>
            </div>

            <button
              onClick={() => window.open('/manual/capitulo_35_tercero_cuenta.html', '_blank')}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-indigo-200 text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors font-medium shadow-sm"
              title="Ver Manual de Usuario"
            >
              <FaBook /> <span>Manual</span>
            </button>
          </div>

          {/* CARD 1: FILTROS */}
          <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 animate-fadeIn mb-8">
            <div className="flex items-center gap-2 mb-6 border-b border-gray-100 pb-2">
              <FaFilter className="text-indigo-500" />
              <h2 className="text-lg font-bold text-gray-700">Configuración del Reporte</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 items-start">
              {/* Tercero */}
              <div className="md:col-span-2">
                <label className={labelClass}>Tercero</label>
                <div className="relative">
                  <select value={selectedTercero} onChange={(e) => setSelectedTercero(e.target.value)} className={selectClass}>
                    <option value="">-- Seleccione Tercero --</option>
                    <option value="all">-- Todos los Terceros --</option>
                    {terceros.map(t => <option key={t.id} value={t.id}>{t.razon_social}</option>)}
                  </select>
                  <FaUserTag className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                </div>
              </div>

              {/* Fechas */}
              <div>
                <label className={labelClass}>Desde</label>
                <div className="relative">
                  <input type="date" value={fechas.inicio} onChange={(e) => setFechas({ ...fechas, inicio: e.target.value })} className={inputClass} />
                  <FaCalendarAlt className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                </div>
              </div>
              <div>
                <label className={labelClass}>Hasta</label>
                <div className="relative">
                  <input type="date" value={fechas.fin} onChange={(e) => setFechas({ ...fechas, fin: e.target.value })} className={inputClass} />
                  <FaCalendarAlt className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                </div>
              </div>

              {/* Cuentas MultiSelect */}
              <div className="md:col-span-4">
                <label className={labelClass}>Filtrar Cuentas (Opcional)</label>
                <MultiSelect options={cuentasDelTercero} selected={selectedCuentas} onChange={setSelectedCuentas} />
                <p className="text-xs text-gray-400 mt-1">Mantenga presionado Ctrl (Windows) o Cmd (Mac) para seleccionar varias.</p>
              </div>
            </div>

            <div className="flex justify-end mt-6 pt-4 border-t border-gray-100">
              <button
                onClick={handleGenerateReport}
                disabled={isLoading}
                className={`
                            px-8 py-2 rounded-lg shadow-md font-bold text-white transition-all transform hover:-translate-y-0.5 flex items-center gap-2
                            ${isLoading ? 'bg-gray-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'}
                        `}
              >
                {isLoading ? <span className="loading loading-spinner loading-sm"></span> : <><FaSearch /> Consultar Movimientos</>}
              </button>
            </div>
          </div>

          {/* MENSAJES DE ESTADO */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded-r-lg flex items-center gap-3 animate-pulse">
              <FaExclamationTriangle className="text-xl" />
              <p className="font-bold">{error}</p>
            </div>
          )}
          {recalculoStatus.error && (
            <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded-r-lg flex items-center gap-3 animate-pulse">
              <FaExclamationTriangle className="text-xl" />
              <p>Error de Recálculo: {recalculoStatus.error}</p>
            </div>
          )}
          {recalculoStatus.message && (
            <div className="mb-6 p-4 bg-green-50 border-l-4 border-green-500 text-green-700 rounded-r-lg flex items-center gap-3 animate-fadeIn">
              <FaCheckCircle className="text-xl" />
              <p>{recalculoStatus.message}</p>
            </div>
          )}

          {/* CARD 2: RESULTADOS */}
          {reportData && (
            <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden animate-slideDown">
              {/* Cabecera Reporte */}
              <div className="p-6 bg-gray-50 border-b border-gray-200 flex flex-col md:flex-row justify-between items-center gap-4">
                <div>
                  <h2 className="text-xl font-bold text-gray-800">
                    {terceros.find(t => t.id == selectedTercero)?.razon_social}
                  </h2>
                  <p className="text-sm text-gray-600 font-medium mt-1">
                    Periodo: <span className="text-indigo-600">{fechas.inicio}</span> al <span className="text-indigo-600">{fechas.fin}</span>
                  </p>
                </div>

                <div className="flex flex-wrap gap-3 justify-end">
                  <button
                    onClick={handleRecalcularSaldos}
                    disabled={isLoading || recalculoStatus.loading}
                    className="flex items-center gap-2 px-4 py-2 bg-yellow-50 text-yellow-700 border border-yellow-300 rounded-lg hover:bg-yellow-100 font-medium transition-colors shadow-sm disabled:opacity-50"
                    title="Forzar reconstrucción de saldos"
                  >
                    {recalculoStatus.loading ? <span className="loading loading-spinner loading-xs"></span> : <FaSync />} Recalcular
                  </button>
                  <button onClick={handleExportCSV} disabled={isLoading} className="flex items-center gap-2 px-4 py-2 bg-white border border-green-500 text-green-600 rounded-lg hover:bg-green-50 font-medium transition-colors shadow-sm disabled:opacity-50"><FaFileCsv /> CSV</button>
                  <button onClick={handleExportPDF} disabled={isLoading} className="flex items-center gap-2 px-4 py-2 bg-white border border-red-500 text-red-600 rounded-lg hover:bg-red-50 font-medium transition-colors shadow-sm disabled:opacity-50"><FaFilePdf /> PDF</button>
                </div>
              </div>

              {/* Tabla */}
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-slate-100">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">Fecha</th>
                      <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">Documento</th>
                      <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">Cuenta</th>
                      <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider w-1/4">Concepto</th>
                      <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase tracking-wider">Débito</th>
                      <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase tracking-wider">Crédito</th>
                      <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase tracking-wider bg-slate-200/50">Saldo Parcial</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-100">
                    {/* Saldo Inicial Global */}
                    <tr className="bg-indigo-50 border-b border-indigo-100">
                      <td colSpan={6} className="px-4 py-3 text-right text-sm font-bold text-indigo-800 uppercase tracking-wide">
                        Saldo Inicial Tercero:
                      </td>
                      <td className="px-4 py-3 text-right text-sm font-mono font-bold text-indigo-900">
                        {formatCurrency(reportData.saldoAnterior)}
                      </td>
                    </tr>

                    {reportData.movimientos.map((mov, index) => {
                      const isNewAccountGroup = index === 0 || mov.cuenta_id !== reportData.movimientos[index - 1].cuenta_id;
                      return (
                        <React.Fragment key={`group-${mov.cuenta_id}-${index}`}>
                          {isNewAccountGroup && (
                            <tr className="bg-gray-100 border-t border-gray-200">
                              <td colSpan={4} className="px-4 py-2 text-xs font-bold text-gray-600 uppercase">
                                Cuenta: <span className="text-indigo-600">{mov.cuenta_codigo} - {mov.cuenta_nombre}</span>
                              </td>
                              <td colSpan={2} className="px-4 py-2 text-right text-xs font-bold text-gray-500">Saldo Inicial Cuenta:</td>
                              <td className="px-4 py-2 text-right text-xs font-mono font-bold text-gray-700 bg-gray-200">
                                {formatCurrency(reportData.saldos_iniciales_por_cuenta[String(mov.cuenta_id)])}
                              </td>
                            </tr>
                          )}
                          <tr className="hover:bg-indigo-50/20 transition-colors">
                            <td className="px-4 py-2 text-sm text-gray-600 font-mono whitespace-nowrap">
                              {new Date(mov.fecha).toLocaleDateString('es-CO', { timeZone: 'UTC' })}
                            </td>
                            <td className="px-4 py-2 text-sm font-medium text-gray-800">
                              {mov.tipo_documento} #{mov.numero_documento}
                            </td>
                            <td className="px-4 py-2 text-xs text-gray-500 font-mono">
                              {mov.cuenta_codigo}
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-600 italic truncate max-w-xs" title={mov.concepto}>
                              {mov.concepto}
                            </td>
                            <td className="px-4 py-2 text-right text-sm font-mono text-gray-700">
                              {parseFloat(mov.debito) > 0 ? formatCurrency(mov.debito) : '-'}
                            </td>
                            <td className="px-4 py-2 text-right text-sm font-mono text-gray-700">
                              {parseFloat(mov.credito) > 0 ? formatCurrency(mov.credito) : '-'}
                            </td>
                            <td className="px-4 py-2 text-right text-sm font-mono font-bold text-indigo-900 bg-slate-50">
                              {formatCurrency(mov.saldo_parcial)}
                            </td>
                          </tr>
                        </React.Fragment>
                      );
                    })}
                  </tbody>

                  {/* Totales Finales */}
                  <tfoot className="bg-slate-800 text-white border-t-4 border-indigo-500">
                    <tr>
                      <td colSpan={4} className="px-4 py-4 text-right text-sm font-bold uppercase tracking-wider">TOTALES TERCERO:</td>
                      <td className="px-4 py-4 text-right font-mono font-bold text-green-400">
                        {formatCurrency(reportData.movimientos.reduce((sum, mov) => sum + parseFloat(mov.debito), 0))}
                      </td>
                      <td className="px-4 py-4 text-right font-mono font-bold text-green-400">
                        {formatCurrency(reportData.movimientos.reduce((sum, mov) => sum + parseFloat(mov.credito), 0))}
                      </td>
                      <td className="px-4 py-4 text-right text-lg font-mono font-bold text-white bg-slate-700">
                        {formatCurrency(reportData.movimientos.length > 0
                          ? reportData.movimientos[reportData.movimientos.length - 1].saldo_parcial
                          : reportData.saldoAnterior
                        )}
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}