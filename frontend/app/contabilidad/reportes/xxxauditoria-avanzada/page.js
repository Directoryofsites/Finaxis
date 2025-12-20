'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { useAuth } from '../../../context/AuthContext';

import Script from 'next/script';

export default function AuditoriaAvanzadaPage() {
  const { user } = useAuth();

  const [tiposDocumento, setTiposDocumento] = useState([]);
  const [terceros, setTerceros] = useState([]);
  const [cuentas, setCuentas] = useState([]);
  const [centrosCosto, setCentrosCosto] = useState([]);

  const [filtros, setFiltros] = useState({
    tipoDocId: '', numero: '', beneficiarioId: '', cuentaId: '',
    centroCostoId: '', fechaInicio: '', fechaFin: '',
    operador: 'mayor', valor: ''
  });

  const [resultados, setResultados] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const totales = useMemo(() => {
    return resultados.reduce((acc, mov) => {
      acc.debito += parseFloat(mov.debito) || 0;
      acc.credito += parseFloat(mov.credito) || 0;
      return acc;
    }, { debito: 0, credito: 0 });
  }, [resultados]);

  useEffect(() => {
    if (user) {
      const fetchMaestros = async () => {
        try {
          const [tiposDocRes, tercerosRes, pucRes, centrosCostoRes] = await Promise.all([
            fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/tipos-documento`),
            fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/terceros`),
            fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/plan-cuentas/puc`),
            fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/centros-costo`)
          ]);
          if (!tiposDocRes.ok || !tercerosRes.ok || !pucRes.ok || !centrosCostoRes.ok) {
            throw new Error('No se pudieron cargar los datos para los filtros.');
          }
          setTiposDocumento(await tiposDocRes.json());
          setTerceros(await tercerosRes.json());
          setCuentas(await pucRes.json());
          setCentrosCosto(await centrosCostoRes.json());
        } catch (err) {
          setError(err.message);
        } finally {
          setIsLoading(false);
        }
      };
      fetchMaestros();
    }
  }, [user]);

  const handleFiltroChange = (e) => {
    const { name, value } = e.target;
    setFiltros(prev => ({ ...prev, [name]: value }));
  };

  const handleBuscar = async () => {
    setIsSearching(true);
    setError(null);
    setResultados([]);
    try {
      const body = { ...filtros, empresa_id: user.empresaId };
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/reports/auditoria-avanzada`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.message || 'Error al realizar la búsqueda.');
      }
      const data = await res.json();
      setResultados(data);
      if (data.length === 0) {
        setError('No se encontraron movimientos que coincidan con los criterios de búsqueda.');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSearching(false);
    }
  };

  const handleExportCSV = () => {
    if (resultados.length === 0) return alert("No hay datos para exportar.");

    // VERIFICACIÓN DE SEGURIDAD (MODELO ESTÁNDAR)
    if (typeof window.Papa === 'undefined') {
      alert("La librería para exportar a CSV no está lista. Por favor, intente de nuevo en un segundo.");
      return;
    }

    const csvData = resultados.map(r => ({
      Fecha: new Date(r.fecha).toLocaleDateString('es-CO'),
      'Tipo Documento': r.tipo_documento,
      'Numero': r.numero,
      'Beneficiario': r.beneficiario,
      'Codigo Cuenta': r.cuenta_codigo,
      'Nombre Cuenta': r.cuenta_nombre,
      'Concepto': `"${(r.concepto || '').replace(/"/g, '""')}"`,
      'Debito': r.debito,
      'Credito': r.credito
    }));
    const header = Object.keys(csvData[0]).join(',');
    const body = csvData.map(row => Object.values(row).join(',')).join('\n');
    const csvContent = `\uFEFF${header}\n${body}`;
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.setAttribute('download', 'reporte_auditoria.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleExportPDF = () => {
    if (resultados.length === 0) return alert("No hay datos para generar el PDF.");

    // VERIFICACIÓN DE SEGURIDAD (MODELO ESTÁNDAR)
    if (typeof window.jspdf === 'undefined' || typeof window.jspdf.jsPDF === 'undefined') {
      alert("La librería para generar PDF no está lista. Por favor, intente de nuevo en un segundo.");
      return;
    }

    try {
      const { jsPDF } = window.jspdf;
      const doc = new jsPDF({ orientation: 'landscape' });

      if (typeof doc.autoTable !== 'function') {
        alert("La extensión para tablas PDF (autoTable) no está lista. Por favor, intente de nuevo.");
        return;
      }

      doc.setFontSize(16);
      doc.text("Reporte de Auditoría Avanzada", 14, 20);
      doc.setFontSize(10);
      doc.text(`Resultados generados el: ${new Date().toLocaleString('es-CO')}`, 14, 26);

      const head = [['Fecha', 'Documento', 'Num', 'Beneficiario', 'Cuenta', 'Concepto', 'Debito', 'Credito']];
      const body = resultados.map(r => [
        new Date(r.fecha).toLocaleDateString('es-CO'), r.tipo_documento, r.numero,
        r.beneficiario, `${r.cuenta_codigo} - ${r.cuenta_nombre}`, r.concepto,
        new Intl.NumberFormat('es-CO').format(r.debito), new Intl.NumberFormat('es-CO').format(r.credito)
      ]);
      body.push([
        { content: 'SUMA TOTALES:', colSpan: 6, styles: { halign: 'right', fontStyle: 'bold' } },
        { content: new Intl.NumberFormat('es-CO').format(totales.debito), styles: { halign: 'right', fontStyle: 'bold' } },
        { content: new Intl.NumberFormat('es-CO').format(totales.credito), styles: { halign: 'right', fontStyle: 'bold' } }
      ]);
      body.push([
        { content: 'DIFERENCIA (Débito - Crédito):', colSpan: 6, styles: { halign: 'right', fontStyle: 'bold' } },
        { content: new Intl.NumberFormat('es-CO').format(totales.debito - totales.credito), colSpan: 2, styles: { halign: 'center', fontStyle: 'bold', fontSize: 9 } }
      ]);

      doc.autoTable({
        startY: 32, head: head, body: body, theme: 'striped',
        styles: { fontSize: 7, cellPadding: 1.5 }, headStyles: { fillColor: [44, 62, 80] }
      });
      doc.save('reporte_auditoria_avanzada.pdf');
    } catch (err) {
      alert('Error al generar PDF: ' + err.message);
    }
  };

  if (isLoading) return <p className="text-center p-8">Cargando datos del formulario...</p>;

  return (
    <>
      <div className="container mx-auto p-8 bg-gray-50 min-h-screen">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800">Auditoría Avanzada de Movimientos</h1>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md mb-8">
          {/* ... (código del formulario de filtros no cambia) ... */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="space-y-4">
              <div>
                <label htmlFor="tipoDocId" className="block text-sm font-medium text-gray-700">Tipo de Documento</label>
                <select name="tipoDocId" value={filtros.tipoDocId} onChange={handleFiltroChange} className="mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm">
                  <option value="">Todos</option>
                  {tiposDocumento.map(td => <option key={td.id} value={td.id}>{td.nombre}</option>)}
                </select>
              </div>
              <div>
                <label htmlFor="numero" className="block text-sm font-medium text-gray-700">Número de Documento</label>
                <input type="text" name="numero" placeholder="Ej: 102030" value={filtros.numero} onChange={handleFiltroChange} className="mt-1 block w-full py-2 px-3 border border-gray-300 rounded-md shadow-sm" />
              </div>
            </div>
            <div className="space-y-4">
              <div>
                <label htmlFor="beneficiarioId" className="block text-sm font-medium text-gray-700">Beneficiario</label>
                <select name="beneficiarioId" value={filtros.beneficiarioId} onChange={handleFiltroChange} className="mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm">
                  <option value="">Todos</option>
                  {terceros.map(t => <option key={t.id} value={t.id}>{t.razon_social}</option>)}
                </select>
              </div>
              <div>
                <label htmlFor="cuentaId" className="block text-sm font-medium text-gray-700">Cuenta Contable</label>
                <select name="cuentaId" value={filtros.cuentaId} onChange={handleFiltroChange} className="mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm">
                  <option value="">Todas</option>
                  {cuentas.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
                </select>
              </div>
            </div>
            <div className="space-y-4">
              <div>
                <label htmlFor="centroCostoId" className="block text-sm font-medium text-gray-700">Centro de Costo</label>
                <select name="centroCostoId" value={filtros.centroCostoId} onChange={handleFiltroChange} className="mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm">
                  <option value="">Todos</option>
                  {centrosCosto.map(cc => <option key={cc.id} value={cc.id}>{cc.nombre}</option>)}
                </select>
              </div>
              <div>
                <label htmlFor="fechaInicio" className="block text-sm font-medium text-gray-700">Fecha Desde</label>
                <input type="date" name="fechaInicio" value={filtros.fechaInicio} onChange={handleFiltroChange} className="mt-1 block w-full py-2 px-3 border border-gray-300 rounded-md shadow-sm" />
              </div>
            </div>
            <div className="space-y-4">
              <div>
                <label htmlFor="fechaFin" className="block text-sm font-medium text-gray-700">Fecha Hasta</label>
                <input type="date" name="fechaFin" value={filtros.fechaFin} onChange={handleFiltroChange} className="mt-1 block w-full py-2 px-3 border border-gray-300 rounded-md shadow-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Filtrar por Valor</label>
                <div className="flex items-center mt-1">
                  <select name="operador" value={filtros.operador} onChange={handleFiltroChange} className="py-2 pl-3 pr-8 border-gray-300 bg-white rounded-l-md shadow-sm">
                    <option value="mayor">Mayor que</option><option value="menor">Menor que</option><option value="igual">Igual a</option>
                  </select>
                  <input type="number" name="valor" placeholder="0.00" value={filtros.valor} onChange={handleFiltroChange} className="block w-full py-2 px-3 border border-l-0 border-gray-300 rounded-r-md shadow-sm" />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="flex justify-end mt-4">
          <button onClick={handleBuscar} disabled={isSearching} className="px-8 py-3 bg-blue-600 text-white font-bold rounded-lg shadow-md hover:bg-blue-700 disabled:bg-gray-400 transition-all">
            {isSearching ? 'Buscando...' : 'Buscar Movimientos'}
          </button>
        </div>

        <div className="mt-8">
          {isSearching && <p className="text-center">Buscando...</p>}
          {error && !resultados.length && <p className="text-center text-gray-600 bg-yellow-100 p-4 rounded-md">{error}</p>}
          {resultados.length > 0 && (
            <div className="bg-white p-4 rounded-lg shadow-md">
              <h2 className="text-xl font-semibold mb-4">Resultados de la Auditoría</h2>
              {/* ===== BOTONES SIMPLIFICADOS ===== */}
              <div className="flex justify-end gap-4 mb-4">
                <button
                  onClick={handleExportCSV}
                  disabled={isSearching || resultados.length === 0}
                  className="px-4 py-2 bg-green-700 text-white text-sm font-medium rounded-md hover:bg-green-800 disabled:bg-gray-400"
                >
                  Exportar a CSV
                </button>
                <button
                  onClick={handleExportPDF}
                  disabled={isSearching || resultados.length === 0}
                  className="px-4 py-2 bg-red-700 text-white text-sm font-medium rounded-md hover:bg-red-800 disabled:bg-gray-400"
                >
                  Descargar PDF
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  {/* ... (código de la tabla no cambia) ... */}
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="py-2 px-3 text-left">Fecha</th><th className="py-2 px-3 text-left">Documento</th>
                      <th className="py-2 px-3 text-left">Número</th><th className="py-2 px-3 text-left">Beneficiario</th>
                      <th className="py-2 px-3 text-left">Cuenta</th><th className="py-2 px-3 text-left">Concepto</th>
                      <th className="py-2 px-3 text-right">Débito</th><th className="py-2 px-3 text-right">Crédito</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {resultados.map((mov, index) => (
                      <tr key={mov.documento_id + '-' + index}>
                        <td className="py-2 px-3 whitespace-nowrap">{new Date(mov.fecha).toLocaleDateString('es-CO')}</td>
                        <td className="py-2 px-3">{mov.tipo_documento}</td><td className="py-2 px-3">{mov.numero}</td>
                        <td className="py-2 px-3">{mov.beneficiario}</td><td className="py-2 px-3 whitespace-nowrap">{mov.cuenta_codigo} - {mov.cuenta_nombre}</td>
                        <td className="py-2 px-3">{mov.concepto}</td>
                        <td className="py-2 px-3 text-right font-mono">{mov.debito > 0 ? new Intl.NumberFormat('es-CO').format(mov.debito) : '-'}</td>
                        <td className="py-2 px-3 text-right font-mono">{mov.credito > 0 ? new Intl.NumberFormat('es-CO').format(mov.credito) : '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot className="bg-gray-200 font-bold text-gray-800">
                    <tr>
                      <td colSpan="6" className="py-3 px-3 text-right">SUMA TOTALES:</td>
                      <td className="py-3 px-3 text-right font-mono">{new Intl.NumberFormat('es-CO').format(totales.debito)}</td>
                      <td className="py-3 px-3 text-right font-mono">{new Intl.NumberFormat('es-CO').format(totales.credito)}</td>
                    </tr>
                    <tr className="border-t-2 border-gray-400">
                      <td colSpan="6" className="py-3 px-3 text-right">DIFERENCIA (Débito - Crédito):</td>
                      <td colSpan="2" className="py-3 px-3 text-center font-mono text-lg">{new Intl.NumberFormat('es-CO').format(totales.debito - totales.credito)}</td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ===== SCRIPTS ESTÁNDAR DESDE CDN ===== */}
      <Script src="https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js" />
      <Script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js" />
      <Script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.8.2/jspdf.plugin.autotable.min.js" />
    </>
  );
}