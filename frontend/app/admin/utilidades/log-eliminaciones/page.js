'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import Script from 'next/script';
import { useAuth } from '../../../context/AuthContext'; 

export default function LogEliminacionesPage() {
  const { user } = useAuth();
  const [logs, setLogs] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [fechas, setFechas] = useState({ inicio: '', fin: '' });

  // PASO 1: ESTADO 'pdfReady' ELIMINADO

  const handleFiltrar = async () => {
    if (!user?.empresaId) return;
    setIsLoading(true);
    setError(null);
    setLogs([]);
    try {
      const body = { empresa_id: user.empresaId };
      if (fechas.inicio && fechas.fin) {
        body.fecha_inicio = fechas.inicio;
        body.fecha_fin = fechas.fin;
      }

      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/documentos/log-eliminaciones`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.message || 'No se pudo cargar el registro de auditoría.');
      }
      const data = await res.json();
      setLogs(data);
      if (data.length === 0) {
        setError('No se encontraron registros para los filtros seleccionados.');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  // PASO 2: NUEVA FUNCIÓN PARA EXPORTAR A CSV
  const handleExportCSV = () => {
    if (logs.length === 0) {
      alert("No hay datos para exportar.");
      return;
    }

    if (typeof window.Papa === 'undefined') {
      alert("La librería para exportar a CSV no está lista. Por favor, intente de nuevo en un segundo.");
      return;
    }

    const dataToExport = [];
    logs.forEach(log => {
      dataToExport.push({
        'ID Log': log.id,
        'Usuario': log.email_usuario,
        'Fecha Operación': formatDate(log.fecha_operacion),
        'Tipo Operación': log.tipo_operacion,
        'Justificación': log.razon,
        '---': '---', // Separador
        'Doc. Tipo': '', 'Doc. Número': '', 'Doc. Fecha': '', 'Doc. Beneficiario': '', 
        'Mov. Código': '', 'Mov. Cuenta': '', 'Mov. Débito': '', 'Mov. Crédito': ''
      });
      if (log.documentos_eliminados && Array.isArray(log.documentos_eliminados)) {
        log.documentos_eliminados.forEach(docAfectado => {
          if (docAfectado.movimientos && Array.isArray(docAfectado.movimientos)) {
            docAfectado.movimientos.forEach(mov => {
              dataToExport.push({
                'ID Log': '', 'Usuario': '', 'Fecha Operación': '', 'Tipo Operación': '', 'Justificación': '',
                '---': '',
                'Doc. Tipo': docAfectado.tipo_documento,
                'Doc. Número': docAfectado.numero,
                'Doc. Fecha': new Date(docAfectado.fecha).toLocaleDateString('es-CO'),
                'Doc. Beneficiario': docAfectado.beneficiario,
                'Mov. Código': mov.cuenta_codigo,
                'Mov. Cuenta': mov.cuenta_nombre,
                'Mov. Débito': (parseFloat(mov.debito) || 0),
                'Mov. Crédito': (parseFloat(mov.credito) || 0)
              });
            });
          }
        });
      }
    });

    const csv = window.Papa.unparse(dataToExport);
    const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', 'informe_auditoria_operaciones.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleExportPDF = () => {
    if (typeof window.jspdf === 'undefined') {
      return alert("La librería PDF aún no está lista. Por favor, espere un segundo.");
    }
    if (logs.length === 0) {
      alert("No hay datos para generar el PDF.");
      return;
    }
    try {
      const { jsPDF } = window.jspdf;
      const doc = new jsPDF({ orientation: 'landscape' });
      if (typeof doc.autoTable !== 'function') {
        throw new Error("La librería autoTable no ha cargado.");
      }
      doc.setFontSize(16);
      doc.text("Informe de Auditoría de Operaciones", 14, 22);
      doc.setFontSize(10);
      if (fechas.inicio && fechas.fin) {
        doc.text(`Período consultado: ${fechas.inicio} al ${fechas.fin}`, 14, 28);
      }

      logs.forEach((log, logIndex) => {
        if (logIndex > 0) {
            doc.addPage();
        }
        doc.autoTable({
            body: [
                [{content: 'Usuario:', styles: {fontStyle: 'bold'}}, log.email_usuario],
                [{content: 'Fecha Operación:', styles: {fontStyle: 'bold'}}, formatDate(log.fecha_operacion)],
                [{content: 'Operación:', styles: {fontStyle: 'bold'}}, log.tipo_operacion],
                [{content: 'Justificación:', styles: {fontStyle: 'bold'}}, log.razon],
            ],
            startY: 35, theme: 'plain', styles: { fontSize: 10 }
        });
        const lastY = doc.lastAutoTable.finalY;

        if (log.documentos_eliminados && log.documentos_eliminados.length > 0) {
            doc.setFontSize(12);
            doc.text("Detalle de Documentos y Movimientos Afectados", 14, lastY + 10);
            const body = [];
            log.documentos_eliminados.forEach(docAfectado => {
                body.push([
                    { content: `Doc: ${docAfectado.tipo_documento} #${docAfectado.numero} | Fecha: ${new Date(docAfectado.fecha).toLocaleDateString('es-CO')} | Benef: ${docAfectado.beneficiario}`, colSpan: 4, styles: { fontStyle: 'bold', fillColor: [230, 230, 230] } }
                ]);
                body.push([
                    { content: 'Cód. Cuenta', styles: { fontStyle: 'bold', halign: 'left' } },
                    { content: 'Nombre Cuenta', styles: { fontStyle: 'bold', halign: 'left' } },
                    { content: 'Débito', styles: { fontStyle: 'bold', halign: 'right' } },
                    { content: 'Crédito', styles: { fontStyle: 'bold', halign: 'right' } }
                ]);
                if (docAfectado.movimientos && Array.isArray(docAfectado.movimientos)) {
                  docAfectado.movimientos.forEach(mov => {
                      body.push([
                          mov.cuenta_codigo, mov.cuenta_nombre,
                          { content: (parseFloat(mov.debito) || 0).toLocaleString('es-CO'), styles: { halign: 'right' } },
                          { content: (parseFloat(mov.credito) || 0).toLocaleString('es-CO'), styles: { halign: 'right' } }
                      ]);
                  });
                }
            });
            doc.autoTable({
                body: body, startY: lastY + 15, theme: 'grid',
                styles: { fontSize: 8, cellPadding: 1.5 },
                columnStyles: { 2: { halign: 'right' }, 3: { halign: 'right' } }
            });
        }
      });
      doc.save('informe_auditoria_operaciones.pdf');
    } catch (e) {
      alert("Error al generar PDF: " + e.message);
    }
  };
  
  const formatDate = (isoString) => {
    if (!isoString) return 'N/A';
    return new Date(isoString).toLocaleString('es-CO', {
      year: 'numeric', month: 'long', day: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };

  if (!user) return <p className="text-center p-8">Debes iniciar sesión para ver este informe.</p>;

  return (
    <>
      {/* PASO 4: SCRIPTS ESTÁNDAR DESDE CDN */}
      <Script src="https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js" />
      <Script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js" />
      <Script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.8.2/jspdf.plugin.autotable.min.js" />

      <div className="container mx-auto p-8 bg-gray-50 min-h-screen">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800">Informe de Auditoría de Operaciones</h1>
          <Link href="/" className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600">&larr; Regresar al Inicio</Link>
        </div>

        <div className="bg-white p-4 rounded-lg shadow-md mb-8 flex items-end gap-4">
          <div>
            <label htmlFor="fechaInicio" className="block text-sm font-medium text-gray-700">Desde</label>
            <input type="date" id="fechaInicio" value={fechas.inicio} onChange={(e) => setFechas({ ...fechas, inicio: e.target.value })} className="mt-1 block w-full py-2 px-3 border border-gray-300 rounded-md shadow-sm"/>
          </div>
          <div>
            <label htmlFor="fechaFin" className="block text-sm font-medium text-gray-700">Hasta</label>
            <input type="date" id="fechaFin" value={fechas.fin} onChange={(e) => setFechas({ ...fechas, fin: e.target.value })} className="mt-1 block w-full py-2 px-3 border border-gray-300 rounded-md shadow-sm"/>
          </div>
          <button onClick={handleFiltrar} disabled={isLoading} className="bg-blue-600 hover:bg-blue-800 text-white font-bold py-2 px-4 rounded-lg shadow-md disabled:bg-gray-400">
            {isLoading ? 'Filtrando...' : 'Filtrar'}
          </button>
          
          {/* PASO 3: BOTONES SIMPLIFICADOS (CSV AÑADIDO) */}
          <div className="flex-grow flex justify-end gap-2">
            <button onClick={handleExportCSV} disabled={logs.length === 0} className="bg-green-600 hover:bg-green-800 text-white font-bold py-2 px-4 rounded-lg shadow-md disabled:bg-gray-400">
              Exportar a CSV
            </button>
            <button onClick={handleExportPDF} disabled={logs.length === 0} className="bg-red-600 hover:bg-red-800 text-white font-bold py-2 px-4 rounded-lg shadow-md disabled:bg-gray-400">
              Descargar PDF
            </button>
          </div>
        </div>
        
        {isLoading ? (
          <p className="text-center p-4">Buscando registros...</p>
        ) : error ? (
          <p className="text-center text-yellow-700 bg-yellow-100 p-4 rounded-md">{error}</p>
        ) : logs.length > 0 ? (
          <div className="space-y-6">
            {logs.map(log => (
              <div key={log.id} className={`bg-white p-6 rounded-lg shadow-md border-l-4 ${log.tipo_operacion === 'ANULACION' ? 'border-orange-500' : 'border-red-700'}`}>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div>
                    <p className="text-sm font-semibold text-gray-500">Usuario</p>
                    <p className="text-gray-800">{log.email_usuario}</p>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-gray-500">Fecha de Operación</p>
                    <p className="text-gray-800">{formatDate(log.fecha_operacion)}</p>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-gray-500">Tipo de Operación</p>
                    <span className={`px-3 py-1 text-sm font-bold rounded-full ${log.tipo_operacion === 'ANULACION' ? 'bg-orange-100 text-orange-800' : 'bg-red-100 text-red-800'}`}>
                      {log.tipo_operacion}
                    </span>
                  </div>
                </div>
                <div className="mb-4">
                  <p className="text-sm font-semibold text-gray-500">Justificación</p>
                  <p className="text-gray-700 bg-gray-50 p-3 rounded-md mt-1">{log.razon}</p>
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-500 mb-2">Documentos Afectados ({log.documentos_eliminados.length})</p>
                  <div className="overflow-x-auto border rounded-md">
                    <table className="min-w-full text-sm">
                      <thead className="bg-gray-100">
                        <tr>
                          <th className="py-2 px-3 text-left">Tipo</th><th className="py-2 px-3 text-left">Número</th>
                          <th className="py-2 px-3 text-left">Fecha</th><th className="py-2 px-3 text-left">Beneficiario</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white">
                        {log.documentos_eliminados.map((doc, i) => (
                          <React.Fragment key={`doc-fragment-${doc.id || i}`}>
                            <tr className="bg-gray-100 font-semibold border-b-2 border-gray-300">
                              <td className="py-2 px-3">{doc.tipo_documento}</td>
                              <td className="py-2 px-3">{doc.numero}</td>
                              <td className="py-2 px-3">{new Date(doc.fecha).toLocaleDateString('es-CO')}</td>
                              <td className="py-2 px-3">{doc.beneficiario}</td>
                            </tr>
                            {doc.movimientos && doc.movimientos.length > 0 && (
                              <tr>
                                <td colSpan="4" className="p-0 bg-gray-50">
                                  <div className="px-6 py-3">
                                    <table className="min-w-full text-xs">
                                      <thead className="bg-slate-200">
                                        <tr>
                                          <th className="px-2 py-1 text-left font-medium text-slate-600">Cuenta</th>
                                          <th className="px-2 py-1 text-left font-medium text-slate-600">Nombre Cuenta</th>
                                          <th className="px-2 py-1 text-right font-medium text-slate-600">Débito</th>
                                          <th className="px-2 py-1 text-right font-medium text-slate-600">Crédito</th>
                                        </tr>
                                      </thead>
                                      <tbody className="divide-y divide-slate-200">
                                        {doc.movimientos.map((mov, movIndex) => (
                                          <tr key={movIndex}>
                                            <td className="px-2 py-1">{mov.cuenta_codigo}</td>
                                            <td className="px-2 py-1">{mov.cuenta_nombre}</td>
                                            <td className="px-2 py-1 text-right font-mono">{(parseFloat(mov.debito) || 0).toLocaleString('es-CO')}</td>
                                            <td className="px-2 py-1 text-right font-mono">{(parseFloat(mov.credito) || 0).toLocaleString('es-CO')}</td>
                                          </tr>
                                        ))}
                                      </tbody>
                                    </table>
                                  </div>
                                </td>
                              </tr>
                            )}
                          </React.Fragment>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (

        <p className="text-center text-gray-500 mt-8">Por favor, selecciona un rango de fechas y haz clic en Filtrar para ver el registro de auditoría.</p>
        )}
      </div>
    </>
  );
}