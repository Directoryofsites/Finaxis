'use client';

import React, { useState, useEffect } from 'react';
import Script from 'next/script';
import {
  FaUserTag,
  FaCalendarAlt,
  FaSearch,
  FaFileCsv,
  FaFilePdf,
  FaMoneyBillWave,
  FaFileInvoiceDollar,
  FaExchangeAlt,
  FaExclamationTriangle,
  FaBook
} from 'react-icons/fa';

import { useAuth } from '../../../../app/context/AuthContext';
import { apiService } from '../../../../lib/apiService';
import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';

// --- ESTILOS REUSABLES (Manual v2.0) ---
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none pl-10";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white pl-10";

// --- COMPONENTES DE VISTA ---

const VistaPorFacturas = ({ reporte }) => {
  if (!reporte || !Array.isArray(reporte.facturas)) return null;

  return (
    <table className="min-w-full">
      <thead className="bg-slate-100">
        <tr>
          <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider w-32">Fecha</th>
          <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">Documento</th>
          <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase tracking-wider">Valor Original</th>
          <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase tracking-wider text-green-600">Total Abonos</th>
          <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase tracking-wider text-indigo-600">Saldo Factura</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-100">
        {reporte.facturas.map((factura) => (
          <React.Fragment key={factura.id}>
            <tr className="bg-white hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3 text-sm text-gray-600 font-mono">
                {new Date(factura.fecha + 'T00:00:00').toLocaleDateString('es-CO')}
              </td>
              <td className="px-4 py-3 text-sm font-semibold text-gray-800">{factura.documento}</td>
              <td className="px-4 py-3 text-sm text-right font-mono text-gray-700">
                ${(factura.valor_original || 0).toLocaleString('es-CO', { minimumFractionDigits: 2 })}
              </td>
              <td className="px-4 py-3 text-sm text-right font-mono text-green-600 font-medium">
                ${(factura.total_abonos || 0).toLocaleString('es-CO', { minimumFractionDigits: 2 })}
              </td>
              <td className="px-4 py-3 text-sm text-right font-mono font-bold text-indigo-900 bg-slate-50">
                ${(factura.saldo_factura || 0).toLocaleString('es-CO', { minimumFractionDigits: 2 })}
              </td>
            </tr>
            {/* Sub-tabla de Abonos */}
            {factura.abonos_detalle && factura.abonos_detalle.length > 0 && (
              <tr className="bg-gray-50 border-b border-gray-200">
                <td colSpan="5" className="px-4 py-2">
                  <div className="ml-8 pl-4 border-l-2 border-gray-300 py-1">
                    <p className="text-xs font-bold text-gray-500 uppercase mb-1">Detalle de Abonos:</p>
                    <ul className="space-y-1">
                      {factura.abonos_detalle
                        .sort((a, b) => {
                          const numA = parseInt(a.documento.match(/\d+/) || [0])
                          const numB = parseInt(b.documento.match(/\d+/) || [0])
                          return numA - numB || a.documento.localeCompare(b.documento)
                        })
                        .map((abono, index) => (
                          <li key={index} className="text-xs text-gray-600 flex items-center gap-2">
                            <FaMoneyBillWave className="text-green-500" />
                            <span>Abonado por <strong>{abono.documento}</strong>:</span>
                            <span className="font-mono font-bold">${parseFloat(abono.valor).toLocaleString('es-CO')}</span>
                          </li>
                        ))}
                    </ul>
                  </div>
                </td>
              </tr>
            )}
          </React.Fragment>
        ))}
      </tbody>
      <tfoot className="bg-slate-800 text-white border-t-4 border-indigo-500">
        <tr>
          <td colSpan="2" className="px-4 py-4 text-right text-sm font-bold uppercase tracking-wider">TOTALES:</td>
          <td className="px-4 py-4 text-right font-mono font-bold text-slate-300">
            ${(reporte.totales.total_facturas || 0).toLocaleString('es-CO', { minimumFractionDigits: 2 })}
          </td>
          <td className="px-4 py-4 text-right font-mono font-bold text-green-400">
            ${(reporte.totales.total_abonos || 0).toLocaleString('es-CO', { minimumFractionDigits: 2 })}
          </td>
          <td className="px-4 py-4 text-right font-mono font-bold text-white text-lg bg-slate-700">
            ${(reporte.totales.saldo_final || 0).toLocaleString('es-CO', { minimumFractionDigits: 2 })}
          </td>
        </tr>
      </tfoot>
    </table>
  );
}

const VistaPorRecibos = ({ reporte }) => {
  if (!reporte || !Array.isArray(reporte.recibos)) return null;

  return (
    <table className="min-w-full">
      <thead className="bg-green-50">
        <tr>
          <th className="px-4 py-3 text-left text-xs font-bold text-green-800 uppercase tracking-wider w-32">Fecha</th>
          <th className="px-4 py-3 text-left text-xs font-bold text-green-800 uppercase tracking-wider">Documento (Recibo)</th>
          <th className="px-4 py-3 text-right text-xs font-bold text-green-800 uppercase tracking-wider">Valor Recibo</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-green-100">
        {reporte.recibos.map((recibo) => (
          <React.Fragment key={recibo.id}>
            <tr className="bg-white hover:bg-green-50/30 transition-colors">
              <td className="px-4 py-3 text-sm text-gray-600 font-mono">
                {new Date(recibo.fecha + 'T00:00:00').toLocaleDateString('es-CO')}
              </td>
              <td className="px-4 py-3 text-sm font-semibold text-gray-800">{recibo.documento}</td>
              <td className="px-4 py-3 text-sm text-right font-mono font-bold text-green-700">
                ${(recibo.valor_total || 0).toLocaleString('es-CO', { minimumFractionDigits: 2 })}
              </td>
            </tr>
            {/* Sub-tabla de Facturas Afectadas */}
            {recibo.facturas_afectadas && recibo.facturas_afectadas.length > 0 && (
              <tr className="bg-green-50/20 border-b border-green-100">
                <td colSpan="3" className="px-4 py-2">
                  <div className="ml-8 pl-4 border-l-2 border-green-300 py-1">
                    <p className="text-xs font-bold text-green-700 uppercase mb-1">Cruces con Facturas:</p>
                    <ul className="space-y-1">
                      {recibo.facturas_afectadas
                        .sort((a, b) => {
                          const numA = parseInt(a.documento.match(/\d+/) || [0])
                          const numB = parseInt(b.documento.match(/\d+/) || [0])
                          return numA - numB || a.documento.localeCompare(b.documento)
                        })
                        .map((factura, index) => (
                          <li key={index} className="text-xs text-gray-600 flex items-center gap-2">
                            <FaExchangeAlt className="text-indigo-400" />
                            <span>Abona a <strong>{factura.documento}</strong>:</span>
                            <span className="font-mono font-bold">${parseFloat(factura.valor).toLocaleString('es-CO')}</span>
                          </li>
                        ))}
                    </ul>
                  </div>
                </td>
              </tr>
            )}
          </React.Fragment>
        ))}
      </tbody>
      <tfoot className="bg-green-800 text-white border-t-4 border-green-600">
        <tr>
          <td colSpan="2" className="px-4 py-4 text-right text-sm font-bold uppercase tracking-wider">TOTAL RECAUDADO:</td>
          <td className="px-4 py-4 text-right font-mono font-bold text-xl">
            ${(reporte.totales.total_recibos || 0).toLocaleString('es-CO', { minimumFractionDigits: 2 })}
          </td>
        </tr>
      </tfoot>
    </table>
  );
}



// ... (Rest of imports same)

// --- COMPONENTES DE VISTA (Same) ---

function AuxiliarCarteraContent() {
  const { user, authLoading } = useAuth();
  const searchParams = useSearchParams(); // NEW: Hook params

  const [terceros, setTerceros] = useState([]);
  const [filtros, setFiltros] = useState({
    terceroId: '',
    fechaInicio: new Date().toISOString().split('T')[0].slice(0, 8) + '01',
    fechaFin: new Date().toISOString().split('T')[0],
    perspective: 'facturas'
  });

  const [reportData, setReportData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isPageReady, setPageReady] = useState(false);
  const [autoPdfTrigger, setAutoPdfTrigger] = useState(false); // NEW: Auto PDF State

  // Autenticación
  useEffect(() => {
    if (!authLoading) {
      if (user && user.empresaId) {
        setPageReady(true);
      }
    }
  }, [user, authLoading]);

  // Carga inicial de clientes y Lógica IA
  useEffect(() => {
    if (user?.empresaId) {
      const fetchTercerosAndConfig = async () => {
        try {
          // 1. Cargar Terceros
          const response = await apiService.get('/terceros', { params: { es_cliente: true } });
          const tercerosLoaded = response.data || [];
          setTerceros(tercerosLoaded);

          // 2. Lógica IA / URL Params
          const aiTercero = searchParams.get('ai_tercero');
          const aiFechaInicio = searchParams.get('fecha_inicio');
          const aiFechaFin = searchParams.get('fecha_fin');
          const aiPerspective = searchParams.get('perspective');
          const aiAutoPdf = searchParams.get('auto_pdf');

          let foundTerceroId = '';

          // A. Resolver Tercero
          if (aiTercero && tercerosLoaded.length > 0) {
            const normalize = (str) => str.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
            const searchNorm = normalize(aiTercero);

            // Prioridad 1: Match Exacto
            const exact = tercerosLoaded.find(t => normalize(t.razon_social) === searchNorm || t.nit === searchNorm);
            if (exact) foundTerceroId = exact.id;
            else {
              // Prioridad 2: Contains
              const match = tercerosLoaded.find(t => normalize(t.razon_social).includes(searchNorm));
              if (match) foundTerceroId = match.id;
            }
          }

          // B. Configurar Filtros
          setFiltros(prev => {
            const next = { ...prev };
            if (foundTerceroId) next.terceroId = foundTerceroId;

            // Fechas: Si no vienen, y es trigger IA, usar Defaults (2020 -> Hoy) para historial completo
            if (aiFechaInicio) next.fechaInicio = aiFechaInicio;
            else if (searchParams.get('trigger') === 'ai_search') next.fechaInicio = '2020-01-01'; // DEFAULT IA

            if (aiFechaFin) next.fechaFin = aiFechaFin;

            if (aiPerspective) next.perspective = aiPerspective;
            return next;
          });

          // C. Trigger Auto Search
          if (foundTerceroId) {
            setTimeout(() => document.getElementById('btn-generar-reporte')?.click(), 500);
          }

          // D. Trigger Auto PDF
          if (aiAutoPdf === 'true') {
            setAutoPdfTrigger(true);
          }

        } catch (err) {
          setError("Error cargando configuración inicial.");
          console.error(err);
        }
      };

      fetchTercerosAndConfig();
    }
  }, [user, searchParams]); // Dependencia crítica searchParams para re-ejecutar si cambia URL

  const handleFiltroChange = (e) => {
    const { name, value } = e.target;
    setFiltros(prev => ({ ...prev, [name]: value }));
  };

  const handleGenerateReport = async () => {
    if (!filtros.terceroId || !filtros.fechaInicio || !filtros.fechaFin) {
      setError("Por favor, seleccione un cliente y un rango de fechas.");
      return;
    }
    setIsLoading(true);
    setError('');
    setReportData(null);

    try {
      const response = await apiService.get('/reports/auxiliar-cartera', {
        params: {
          tercero_id: filtros.terceroId,
          fecha_inicio: filtros.fechaInicio,
          fecha_fin: filtros.fechaFin,
          perspective: filtros.perspective
        }
      });
      setReportData(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Error al generar el reporte.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleExportCSV = () => {
    if (!reportData) return alert("No hay datos para exportar.");
    if (typeof window.Papa === 'undefined') return alert("Librería CSV no lista.");

    let dataParaCSV = [];
    const perspective = filtros.perspective;

    if (perspective === 'facturas' && reportData.facturas) {
      reportData.facturas.forEach(f => {
        dataParaCSV.push({
          'Fecha': new Date(f.fecha).toLocaleDateString('es-CO'),
          'Tipo Doc': f.tipo_documento || 'Venta',
          'Número': f.numero_documento || f.numero,
          'Nit/CC': f.beneficiario_nit || '',
          'Documento Completo': f.documento,
          'Valor Original': f.valor_original.toFixed(2),
          'Total Abonos': f.total_abonos.toFixed(2),
          'Saldo Factura': f.saldo_factura.toFixed(2)
        });
      });
    } else if (perspective === 'recibos' && reportData.recibos) {
      reportData.recibos.forEach(r => {
        dataParaCSV.push({
          'Fecha': new Date(r.fecha).toLocaleDateString('es-CO'),
          'Tipo Doc': r.tipo_documento || 'Recibo',
          'Número': r.numero_documento || r.numero,
          'Nit/CC': r.beneficiario_nit || '',
          'Documento Completo': r.documento,
          'Valor Recibo': r.valor_total.toFixed(2)
        });
      });
    }

    const csv = window.Papa.unparse(dataParaCSV, { delimiter: ';' });
    const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `auxiliar_cartera_${perspective}_${filtros.terceroId}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // NEW IMPORT: useCallback
  const handleExportPDF = React.useCallback(async () => {
    if (!reportData) return alert("Genere el reporte primero.");
    // setIsLoading(true); // Don't trigger loading for download if possible, or handle carefully
    try {
      const response = await apiService.get('/reports/auxiliar-cartera/get-signed-url', {
        params: {
          tercero_id: filtros.terceroId,
          fecha_inicio: filtros.fechaInicio,
          fecha_fin: filtros.fechaFin,
          perspective: filtros.perspective
        }
      });
      const signedToken = response.data.signed_url_token;
      const pdfUrl = `${process.env.NEXT_PUBLIC_API_URL}/api/reports/auxiliar-cartera/imprimir?signed_token=${signedToken}`;

      // ABRIR EN NUEVA PESTAÑA (Request Usuario)
      window.open(pdfUrl, '_blank');

      if (autoPdfTrigger) setAutoPdfTrigger(false); // Reset trigger

    } catch (err) {
      setError(err.response?.data?.detail || "Error PDF.");
    }
  }, [reportData, filtros, autoPdfTrigger]);

  // AUTO PDF TRIGGER EFFECT
  useEffect(() => {
    if (autoPdfTrigger && reportData && !isLoading) {
      console.log("IA: Ejecutando Auto-PDF...");
      handleExportPDF();
    }
  }, [autoPdfTrigger, reportData, isLoading, handleExportPDF]);

  if (!isPageReady) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
        <FaMoneyBillWave className="text-indigo-300 text-6xl mb-4 animate-pulse" />
        <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando Auxiliar de Cartera...</p>
      </div>
    );
  }

  return (
    <>
      <Script src="https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js" />

      <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
        <div className="max-w-5xl mx-auto">

          {/* ENCABEZADO */}
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
            <div>
              <div className="flex items-center gap-3 mt-3">
                <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                  <FaMoneyBillWave className="text-2xl" />
                </div>
                <div>
                  <div className="flex items-center gap-4">
                    <h1 className="text-3xl font-bold text-gray-800">Auxiliar de Cartera</h1>
                    <button
                      onClick={() => window.open('/manual/capitulo_37_auxiliar_cartera.html', '_blank')}
                      className="flex items-center gap-2 px-2 py-1 bg-white border border-indigo-200 text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors font-medium shadow-sm"
                      title="Ver Manual de Usuario"
                    >
                      <span className="text-lg">📖</span> <span className="font-bold text-sm hidden md:inline">Manual</span>
                    </button>
                  </div>
                  <p className="text-gray-500 text-sm">Cruce detallado entre facturación y recaudos.</p>
                </div>
              </div>
            </div>
          </div>

          {/* CARD 1: FILTROS */}
          <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 animate-fadeIn mb-8">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 items-end">

              {/* Cliente */}
              <div className="md:col-span-2">
                <label htmlFor="terceroId" className={labelClass}>Cliente</label>
                <div className="relative">
                  <select
                    id="terceroId"
                    name="terceroId"
                    value={filtros.terceroId}
                    onChange={handleFiltroChange}
                    className={selectClass}
                  >
                    <option value="">Seleccione un cliente...</option>
                    {terceros.map(t => (<option key={t.id} value={t.id}>{t.razon_social}</option>))}
                  </select>
                  <FaUserTag className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                </div>
              </div>

              {/* Fecha Inicio */}
              <div className="md:col-span-1">
                <label htmlFor="fechaInicio" className={labelClass}>Desde</label>
                <div className="relative">
                  <input
                    type="date"
                    name="fechaInicio"
                    value={filtros.fechaInicio}
                    onChange={handleFiltroChange}
                    className={inputClass}
                  />
                  <FaCalendarAlt className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                </div>
              </div>

              {/* Fecha Fin */}
              <div className="md:col-span-1">
                <label htmlFor="fechaFin" className={labelClass}>Hasta</label>
                <div className="relative">
                  <input
                    type="date"
                    name="fechaFin"
                    value={filtros.fechaFin}
                    onChange={handleFiltroChange}
                    className={inputClass}
                  />
                  <FaCalendarAlt className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                </div>
              </div>
            </div>

            {/* PERSPECTIVA */}
            <div className="mt-6 pt-4 border-t border-gray-100">
              <label className={labelClass}>Ver reporte desde la perspectiva de:</label>
              <div className="flex flex-wrap gap-4 mt-2">
                <div
                  onClick={() => setFiltros(prev => ({ ...prev, perspective: 'facturas' }))}
                  className={`cursor-pointer px-4 py-2 rounded-lg border flex items-center gap-2 transition-all ${filtros.perspective === 'facturas' ? 'bg-indigo-50 border-indigo-500 text-indigo-700 ring-1 ring-indigo-500' : 'bg-white border-gray-200 text-gray-500 hover:bg-gray-50'}`}
                >
                  <div className={`p-1 rounded-full ${filtros.perspective === 'facturas' ? 'bg-indigo-200' : 'bg-gray-200'}`}>
                    <FaFileInvoiceDollar className="text-sm" />
                  </div>
                  <span className="font-bold text-sm">Facturas (Cuentas de Cobro)</span>
                </div>

                <div
                  onClick={() => setFiltros(prev => ({ ...prev, perspective: 'recibos' }))}
                  className={`cursor-pointer px-4 py-2 rounded-lg border flex items-center gap-2 transition-all ${filtros.perspective === 'recibos' ? 'bg-green-50 border-green-500 text-green-700 ring-1 ring-green-500' : 'bg-white border-gray-200 text-gray-500 hover:bg-gray-50'}`}
                >
                  <div className={`p-1 rounded-full ${filtros.perspective === 'recibos' ? 'bg-green-200' : 'bg-gray-200'}`}>
                    <FaMoneyBillWave className="text-sm" />
                  </div>
                  <span className="font-bold text-sm">Recibos de Caja (Pagos)</span>
                </div>
              </div>
            </div>

            <div className="flex justify-end mt-6">
              <button
                id="btn-generar-reporte"
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

              {/* Cabecera Reporte */}
              <div className="p-6 bg-gray-50 border-b border-gray-200 flex flex-col md:flex-row justify-between items-center gap-4">
                <div>
                  <h2 className="text-xl font-bold text-gray-800">
                    {terceros.find(t => t.id == filtros.terceroId)?.razon_social}
                  </h2>
                  <p className="text-sm text-gray-600 font-medium mt-1">
                    Periodo: <span className="text-indigo-600">{filtros.fechaInicio}</span> al <span className="text-indigo-600">{filtros.fechaFin}</span>
                  </p>
                </div>
                <div className="flex gap-3">
                  <button onClick={handleExportCSV} disabled={isLoading} className="flex items-center gap-2 px-4 py-2 bg-white border border-green-500 text-green-600 rounded-lg hover:bg-green-50 font-medium transition-colors shadow-sm disabled:opacity-50"><FaFileCsv /> CSV</button>
                  <button onClick={handleExportPDF} disabled={isLoading} className="flex items-center gap-2 px-4 py-2 bg-white border border-red-500 text-red-600 rounded-lg hover:bg-red-50 font-medium transition-colors shadow-sm disabled:opacity-50"><FaFilePdf /> PDF</button>
                </div>
              </div>

              {/* Tabla Dinámica */}
              <div className="overflow-x-auto">
                {filtros.perspective === 'facturas' && <VistaPorFacturas reporte={reportData} />}
                {filtros.perspective === 'recibos' && <VistaPorRecibos reporte={reportData} />}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

export default function AuxiliarCarteraPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
        <FaMoneyBillWave className="text-indigo-300 text-6xl mb-4 animate-pulse" />
        <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando...</p>
      </div>
    }>
      <AuxiliarCarteraContent />
    </Suspense>
  );
}