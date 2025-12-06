'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Script from 'next/script';
import { 
  FaBuilding, 
  FaListOl, 
  FaCalendarAlt, 
  FaSearch, 
  FaFilePdf, 
  FaFileCsv, 
  FaFilter, 
  FaExclamationTriangle,
  FaLayerGroup 
} from 'react-icons/fa';

import { 
FaBook,
} from 'react-icons/fa';

import { useAuth } from '../../../context/AuthContext';
import { apiService } from '../../../../lib/apiService';
import BotonRegresar from '../../../components/BotonRegresar';

// Estilos Reusables (Manual v2.0)
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none pl-10";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white pl-10";

export default function AuxiliarCcCuentaPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [filtros, setFiltros] = useState({
    centroCostoId: '',
    cuentaId: '',
    fechaInicio: '',
    fechaFin: ''
  });
  const [centrosCosto, setCentrosCosto] = useState([]);
  const [cuentas, setCuentas] = useState([]);
  const [reportData, setReportData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isPageReady, setPageReady] = useState(false);

  // Verificación de sesión
  useEffect(() => {
    if (!authLoading) {
        if (user && user.empresaId) {
            setPageReady(true);
        } else {
            router.push('/login');
        }
    }
  }, [user, authLoading, router]);

  // Carga de maestros
  useEffect(() => {
    if (isPageReady) {
      const fetchMaestros = async () => {
        try {
          const [resCC, resCuentas] = await Promise.all([
            apiService.get(`/centros-costo/get-flat`),
            apiService.get(`/plan-cuentas/`)
          ]);

          // Filtramos solo los que permiten movimiento (Hijos)
          const ccFiltrados = resCC.data.filter(cc => cc.permite_movimiento);
          setCentrosCosto(ccFiltrados);

          // Aplanar cuentas
          const aplanarCuentas = (cuentasArray) => {
            let listaPlana = [];
            cuentasArray.forEach(cuenta => {
              listaPlana.push({ id: cuenta.id, codigo: cuenta.codigo, nombre: cuenta.nombre });
              if (cuenta.children && cuenta.children.length > 0) {
                listaPlana = listaPlana.concat(aplanarCuentas(cuenta.children));
              }
            });
            return listaPlana;
          };
          setCuentas(aplanarCuentas(resCuentas.data));

        } catch (err) {
          setError("Error cargando datos maestros: " + (err.response?.data?.detail || err.message));
        }
      };
      fetchMaestros();
    }
  }, [isPageReady]);

  const handleFiltroChange = (e) => {
    const { name, value } = e.target;
    setFiltros(prev => ({ ...prev, [name]: value }));
  };

  const handleGenerateReport = async () => {
    if (!filtros.centroCostoId || !filtros.fechaInicio || !filtros.fechaFin) {
      setError("Por favor, seleccione un centro de costo y un rango de fechas.");
      return;
    }
    setIsLoading(true);
    setError(null);
    setReportData(null);

    const params = {
      centro_costo_id: filtros.centroCostoId,
      fecha_inicio: filtros.fechaInicio,
      fecha_fin: filtros.fechaFin
    };
    if (filtros.cuentaId && filtros.cuentaId !== 'TODAS') {
      params.cuenta_id = filtros.cuentaId;
    }

    try {
      const res = await apiService.get('/reports/auxiliar-cc-cuenta', { params: params });
      setReportData(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al generar el reporte.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExportCSV = () => {
    if (!reportData || reportData.movimientos.length === 0) return alert("No hay datos para exportar.");
    if (typeof window.Papa === 'undefined') return alert("La librería CSV no está lista. Recargue la página.");

    const formatCurrencyCSV = (value) => parseFloat(value).toFixed(2);
    const dataToExport = [];
    
    // Encabezados
    dataToExport.push(['Fecha', 'Documento', 'Cuenta', 'Nombre Cuenta', 'Beneficiario', 'Concepto', 'Debito', 'Credito', 'Saldo Parcial']);
    
    // Saldo Inicial Global
    dataToExport.push(['', '', '', '', '', 'SALDO INICIAL CENTRO COSTO', '', '', formatCurrencyCSV(reportData.saldoAnteriorGlobal)]);

    let currentAccount = null;
    reportData.movimientos.forEach(mov => {
        if (mov.cuenta_id !== currentAccount) {
            dataToExport.push(['', '', mov.cuenta_codigo, mov.cuenta_nombre, '', 'SALDO INICIAL CUENTA', '', '', formatCurrencyCSV(reportData.saldos_iniciales_por_cuenta[mov.cuenta_id])]);
            currentAccount = mov.cuenta_id;
        }
        dataToExport.push([
            new Date(mov.fecha).toLocaleDateString('es-CO', {timeZone: 'UTC'}),
            `${mov.tipo_documento}-${mov.numero_documento}`,
            mov.cuenta_codigo,
            mov.cuenta_nombre,
            mov.beneficiario || '',
            mov.concepto,
            formatCurrencyCSV(mov.debito),
            formatCurrencyCSV(mov.credito),
            formatCurrencyCSV(mov.saldo_parcial)
        ]);
    });

    // Saldo Final
    const finalBalance = reportData.movimientos.length > 0 ? reportData.movimientos[reportData.movimientos.length - 1].saldo_parcial : reportData.saldoAnteriorGlobal;
    dataToExport.push(['', '', '', '', '', 'SALDO FINAL', '', '', formatCurrencyCSV(finalBalance)]);

    const csv = window.Papa.unparse(dataToExport);
    const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.setAttribute("download", `Auxiliar_CC_${filtros.centroCostoId}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleExportPDF = async () => {
    if (!reportData || reportData.movimientos.length === 0) return alert("No hay datos para generar el PDF.");
    setIsLoading(true);
    try {
      const paramsForSignedUrl = {
        centro_costo_id: filtros.centroCostoId,
        fecha_inicio: filtros.fechaInicio,
        fecha_fin: filtros.fechaFin,
      };
      if (filtros.cuentaId && filtros.cuentaId !== 'TODAS') {
        paramsForSignedUrl.cuenta_id = filtros.cuentaId;
      }

      const signedUrlRes = await apiService.get('/reports/auxiliar-cc-cuenta/get-signed-url', { params: paramsForSignedUrl });
      const signedToken = signedUrlRes.data.signed_url_token;
      const finalPdfUrl = `${process.env.NEXT_PUBLIC_API_URL}/api/reports/auxiliar-cc-cuenta/imprimir?signed_token=${signedToken}`;

      const link = document.createElement('a');
      link.href = finalPdfUrl;
      link.setAttribute('download', `Auxiliar_CC_${filtros.centroCostoId}.pdf`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

    } catch (err) {
      setError(err.response?.data?.detail || 'Error al obtener el PDF.');
    } finally {
      setIsLoading(false);
    }
  };

  const formatCurrency = (val) => {
    return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 2 }).format(val);
  };

  const getSelectedCcName = () => {
    const cc = centrosCosto.find(c => c.id == filtros.centroCostoId);
    return cc ? `${cc.codigo} - ${cc.nombre}` : '';
  };

  if (!isPageReady) {
    return (
        <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
            <FaLayerGroup className="text-indigo-300 text-6xl mb-4 animate-pulse" />
            <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando Reporte...</p>
        </div>
    );
  }

  // Lógica de renderizado de filas con agrupación visual
  const renderTableRows = () => {
    if (!reportData || reportData.movimientos.length === 0) {
        return <tr><td colSpan="9" className="text-center py-8 text-gray-400 italic">No hay movimientos para este Centro de Costo en el periodo.</td></tr>;
    }

    let rows = [];
    let currentAccountId = null;

    // Fila Inicial Global
    rows.push(
        <tr key="saldo-inicial-global" className="bg-indigo-50 border-b border-indigo-100">
            <td colSpan={8} className="px-4 py-3 text-right text-sm font-bold text-indigo-800 uppercase tracking-wide">
                Saldo Inicial Centro de Costo:
            </td>
            <td className="px-4 py-3 text-right text-sm font-mono font-bold text-indigo-900">
                {formatCurrency(reportData.saldoAnteriorGlobal)}
            </td>
        </tr>
    );

    reportData.movimientos.forEach((mov, index) => {
        // Cambio de Cuenta: Insertar Sub-Cabecera
        if (mov.cuenta_id !== currentAccountId) {
            rows.push(
                <tr key={`header-${mov.cuenta_id}`} className="bg-gray-100 border-t-2 border-gray-200">
                    <td colSpan={2} className="px-4 py-2 text-left text-xs font-bold text-gray-600 uppercase">
                        Cuenta: <span className="text-indigo-600">{mov.cuenta_codigo}</span>
                    </td>
                    <td colSpan={6} className="px-4 py-2 text-left text-xs font-bold text-gray-600 uppercase">
                        {mov.cuenta_nombre}
                    </td>
                    <td className="px-4 py-2 text-right text-xs font-mono font-bold text-gray-700 bg-gray-200">
                        Ini: {formatCurrency(reportData.saldos_iniciales_por_cuenta[mov.cuenta_id])}
                    </td>
                </tr>
            );
            currentAccountId = mov.cuenta_id;
        }

        // Fila de Movimiento
        rows.push(
            <tr key={mov.movimiento_id || index} className="hover:bg-indigo-50/20 transition-colors border-b border-gray-50">
                <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-600 font-mono">
                    {new Date(mov.fecha).toLocaleDateString('es-CO', { timeZone: 'UTC' })}
                </td>
                <td className="px-4 py-2 whitespace-nowrap text-sm font-medium text-gray-800">
                    {`${mov.tipo_documento}-${mov.numero_documento}`}
                </td>
                <td className="px-4 py-2 whitespace-nowrap text-xs text-gray-500 font-mono">
                    {mov.cuenta_codigo}
                </td>
                <td className="px-4 py-2 whitespace-nowrap text-xs text-gray-500 truncate max-w-[150px]" title={mov.cuenta_nombre}>
                    {mov.cuenta_nombre}
                </td>
                <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-600 truncate max-w-[150px]" title={mov.beneficiario}>
                    {mov.beneficiario || '-'}
                </td>
                <td className="px-4 py-2 text-sm text-gray-500 italic truncate max-w-[200px]" title={mov.concepto}>
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
        );
    });

    return rows;
  };

  return (
    <>
      <Script src="https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js" />
      
      <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
        <div className="max-w-7xl mx-auto">
            
            {/* ENCABEZADO */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                <div>


                   <div className="flex items-center gap-3 mb-3">
                            
                            {/* 1. Botón Regresar (Izquierda) */}
                            <BotonRegresar />

                            {/* 2. Botón Manual (Derecha) */}
                            <button
                                onClick={() => window.open('/manual?file=capitulo_51_auxiliar_cc_cuenta.md', '_blank')}
                                className="text-indigo-600 hover:bg-indigo-50 px-3 py-1 rounded-md flex items-center gap-2 transition-colors font-bold text-sm"
                                type="button"
                            >
                                <FaBook className="text-lg" /> Manual
                            </button>

                        </div>


                    <div className="flex items-center gap-3 mt-3">
                        <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                            <FaLayerGroup className="text-2xl" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold text-gray-800">Auxiliar por Centro de Costo</h1>
                            <p className="text-gray-500 text-sm">Análisis detallado de movimientos imputados a centros de costo.</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* CARD 1: FILTROS */}
            <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 animate-fadeIn mb-8">
                <div className="flex items-center gap-2 mb-6 border-b border-gray-100 pb-2">
                    <FaFilter className="text-indigo-500" />
                    <h2 className="text-lg font-bold text-gray-700">Criterios de Búsqueda</h2>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 items-end">
                    {/* Centro Costo */}
                    <div>
                        <label className={labelClass}>Centro de Costo <span className="text-red-500">*</span></label>
                        <div className="relative">
                            <select name="centroCostoId" value={filtros.centroCostoId} onChange={handleFiltroChange} className={selectClass}>
                                <option value="">Seleccione...</option>
                                {centrosCosto.map(cc => <option key={cc.id} value={cc.id}>{cc.codigo} - {cc.nombre}</option>)}
                            </select>
                            <FaBuilding className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                        </div>
                    </div>

                    {/* Cuenta */}
                    <div>
                        <label className={labelClass}>Cuenta (Opcional)</label>
                        <div className="relative">
                            <select name="cuentaId" value={filtros.cuentaId} onChange={handleFiltroChange} className={selectClass}>
                                <option value="">-- TODAS --</option>
                                {cuentas.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
                            </select>
                            <FaListOl className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                        </div>
                    </div>

                    {/* Fechas */}
                    <div>
                        <label className={labelClass}>Desde</label>
                        <div className="relative">
                            <input type="date" name="fechaInicio" value={filtros.fechaInicio} onChange={handleFiltroChange} className={inputClass} />
                            <FaCalendarAlt className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                        </div>
                    </div>
                    <div>
                        <label className={labelClass}>Hasta</label>
                        <div className="relative">
                            <input type="date" name="fechaFin" value={filtros.fechaFin} onChange={handleFiltroChange} className={inputClass} />
                            <FaCalendarAlt className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                        </div>
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
                        {isLoading ? <span className="loading loading-spinner loading-sm"></span> : <><FaSearch /> Generar Reporte</>}
                    </button>
                </div>
            </div>

            {/* MENSAJE ERROR */}
            {error && (
                <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded-r-lg flex items-center gap-3 animate-pulse">
                    <FaExclamationTriangle className="text-xl" />
                    <p className="font-bold">{error}</p>
                </div>
            )}

            {/* CARD 2: RESULTADOS */}
            {reportData && (
                <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden animate-slideDown">
                    <div className="p-6 bg-gray-50 border-b border-gray-200 flex flex-col md:flex-row justify-between items-center gap-4">
                        <div>
                            <h2 className="text-xl font-bold text-gray-800">{getSelectedCcName()}</h2>
                            <p className="text-sm text-gray-600 font-medium mt-1">
                                Periodo: <span className="text-indigo-600">{filtros.fechaInicio}</span> al <span className="text-indigo-600">{filtros.fechaFin}</span>
                            </p>
                        </div>
                        <div className="flex gap-3">
                            <button onClick={handleExportCSV} disabled={isLoading} className="flex items-center gap-2 px-4 py-2 bg-white border border-green-500 text-green-600 rounded-lg hover:bg-green-50 font-medium transition-colors shadow-sm disabled:opacity-50"><FaFileCsv /> CSV</button>
                            <button onClick={handleExportPDF} disabled={isLoading} className="flex items-center gap-2 px-4 py-2 bg-white border border-red-500 text-red-600 rounded-lg hover:bg-red-50 font-medium transition-colors shadow-sm disabled:opacity-50"><FaFilePdf /> PDF</button>
                        </div>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-slate-100">
                                <tr>
                                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider w-24">Fecha</th>
                                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider w-32">Documento</th>
                                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider w-20">Cta.</th>
                                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">Nombre Cuenta</th>
                                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">Beneficiario</th>
                                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider w-40">Concepto</th>
                                    <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase tracking-wider w-28">Débito</th>
                                    <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase tracking-wider w-28">Crédito</th>
                                    <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase tracking-wider w-28 bg-slate-200/50">Saldo</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-100">
                                {renderTableRows()}
                            </tbody>
                            
                            {/* FOOTER SALDO FINAL */}
                            <tfoot className="bg-slate-800 text-white border-t-4 border-indigo-500">
                                <tr>
                                    <td colSpan="8" className="px-4 py-4 text-right text-sm font-bold uppercase tracking-wider">Saldo Final Centro de Costo:</td>
                                    <td className="px-4 py-4 text-right text-lg font-mono font-bold text-white bg-slate-700">
                                        {formatCurrency(reportData.movimientos.length > 0 ? reportData.movimientos[reportData.movimientos.length - 1].saldo_parcial : reportData.saldoAnteriorGlobal)}
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