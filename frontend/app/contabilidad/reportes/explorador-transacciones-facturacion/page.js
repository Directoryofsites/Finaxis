// frontend/app/contabilidad/reportes/explorador-transacciones-facturacion/page.js
'use client';

import { useState, useEffect } from 'react';

import { generarReporteFacturacion, generarPdfDirectoReporteFacturacion } from '@/lib/reportesFacturacionService'; // <--- FIX: Usar la función de GENERACIÓN DIRECTA
import { apiService } from '@/lib/apiService';
import { toast, ToastContainer } from 'react-toastify'; // Importar Toast
import 'react-toastify/dist/ReactToastify.css';

const formatCurrency = (value) => {
  if (typeof value !== 'number') return '$ 0';
  return value.toLocaleString('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0, maximumFractionDigits: 0 });
};

const ExploradorTransaccionesPage = () => {
  const [filtros, setFiltros] = useState({
    fecha_inicio: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0],
    fecha_fin: new Date().toISOString().split('T')[0],
    tercero_id: '',
    centro_costo_id: '',
    tipo_reporte: 'ventas'
  });

  const [reporteData, setReporteData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [terceros, setTerceros] = useState([]);
  const [centrosCosto, setCentrosCosto] = useState([]);
  const [isExportingPdf, setIsExportingPdf] = useState(false);

  useEffect(() => {
    const cargarFiltrosData = async () => {
      try {
        const [tercerosRes, centrosCostoRes] = await Promise.all([
          apiService.get('/terceros/'),
          apiService.get('/centros-costo/get-flat')
        ]);
        setTerceros(tercerosRes.data);
        setCentrosCosto(centrosCostoRes.data);
      } catch (err) {
        setError('Error al cargar los datos para los filtros.');
      }
    };
    cargarFiltrosData();
  }, []);

  const handleFiltroChange = (e) => {
    const { name, value } = e.target;
    setFiltros(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setReporteData(null);

    try {
      const filtrosParaAPI = {
        ...filtros,
        tercero_id: filtros.tercero_id ? parseInt(filtros.tercero_id, 10) : null,
        centro_costo_id: filtros.centro_costo_id ? parseInt(filtros.centro_costo_id, 10) : null,
      };
      const data = await generarReporteFacturacion(filtrosParaAPI);
      setReporteData(data);
    } catch (err) {
      // Si err.message es "Network Error" o similar, la API no se alcanzó
      setError(err.response?.data?.detail || err.message || 'Error al generar el reporte.');
    } finally {
      setLoading(false);
    }
  };

  // --- INICIO: LÓGICA DE EXPORTACIÓN REEMPLAZADA ---
  const handleExportPDF = async () => {
    if (!reporteData) {
      toast.warning("Genere el reporte primero antes de exportar.");
      return;
    }

    setIsExportingPdf(true);
    setError('');

    try {
      const filtrosParaAPI = {
        ...filtros,
        tercero_id: filtros.tercero_id ? parseInt(filtros.tercero_id, 10) : null,
        centro_costo_id: filtros.centro_costo_id ? parseInt(filtros.centro_costo_id, 10) : null,
      };

      // 1. Llamar a la función de Generación Directa (que maneja el blob y la descarga)
      // Se asume que generarPdfDirectoReporteFacturacion existe en el servicio.
      await generarPdfDirectoReporteFacturacion(filtrosParaAPI);

      toast.success("El PDF se está descargando...");

    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error al generar el PDF.';
      setError(errorMsg);
      toast.error(`Error de PDF: ${errorMsg}`);
    } finally {
      setIsExportingPdf(false);
    }
  };
  // --- FIN: LÓGICA DE EXPORTACIÓN REEMPLAZADA ---


  return (
    <div className="container mx-auto p-4">
      <ToastContainer position="top-right" autoClose={3000} />
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Explorador de Transacciones</h1>
      </div>

      <div className="card bg-base-100 shadow-xl mb-6">
        <div className="card-body">
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4 items-end">
              <div>
                <label className="label"><span className="label-text font-bold">Tipo de Reporte</span></label>
                <select name="tipo_reporte" value={filtros.tipo_reporte} onChange={handleFiltroChange} className="select select-bordered w-full">
                  <option value="ventas">Ventas</option>
                  <option value="compras">Compras</option>
                </select>
              </div>
              <div className="lg:col-span-2">
                <label className="label"><span className="label-text">Rango de Fechas</span></label>
                <div className="flex items-center space-x-2">
                  <input type="date" name="fecha_inicio" value={filtros.fecha_inicio} onChange={handleFiltroChange} className="input input-bordered w-full" required />
                  <span>-</span>
                  <input type="date" name="fecha_fin" value={filtros.fecha_fin} onChange={handleFiltroChange} className="input input-bordered w-full" required />
                </div>
              </div>
              <button type="submit" className="btn btn-primary w-full" disabled={loading}>
                {loading ? <span className="loading loading-spinner"></span> : 'Generar Reporte'}
              </button>
              <div>
                <label className="label"><span className="label-text">Tercero (Cliente/Proveedor)</span></label>
                <select name="tercero_id" value={filtros.tercero_id} onChange={handleFiltroChange} className="select select-bordered w-full">
                  <option value="">Todos</option>
                  {terceros.map(t => <option key={t.id} value={t.id}>{t.razon_social}</option>)}
                </select>
              </div>
              <div>
                <label className="label"><span className="label-text">Centro de Costo</span></label>
                <select name="centro_costo_id" value={filtros.centro_costo_id} onChange={handleFiltroChange} className="select select-bordered w-full">
                  <option value="">Todos</option>
                  {centrosCosto.map(cc => <option key={cc.id} value={cc.id}>{cc.nombre}</option>)}
                </select>
              </div>
            </div>
          </form>
        </div>
      </div>

      {loading && <div className="text-center my-10"><span className="loading loading-spinner loading-lg text-primary"></span></div>}
      {error && <div className="alert alert-error"><span>{error}</span></div>}

      {reporteData && (
        <div className="space-y-6">
          <div className="flex justify-end gap-2">
            <button onClick={handleExportPDF} className="btn btn-secondary" disabled={isExportingPdf || !reporteData}>
              {isExportingPdf ? 'Generando PDF...' : 'Exportar a PDF'}
            </button>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="stat bg-base-200 rounded-lg p-4 text-center">
              <div className="stat-title">{filtros.tipo_reporte === 'ventas' ? 'Total Facturado' : 'Total Comprado'}</div>
              <div className="stat-value text-primary">{formatCurrency(reporteData.kpis.total_valor)}</div>
            </div>
            {filtros.tipo_reporte === 'ventas' && (
              <>
                <div className="stat bg-base-200 rounded-lg p-4 text-center">
                  <div className="stat-title">Costo Total</div>
                  <div className="stat-value text-secondary">{formatCurrency(reporteData.kpis.total_costo)}</div>
                </div>
                <div className="stat bg-base-200 rounded-lg p-4 text-center">
                  <div className="stat-title">Utilidad Bruta</div>
                  <div className="stat-value text-accent">{formatCurrency(reporteData.kpis.utilidad_bruta_valor_total)}</div>
                </div>
                <div className="stat bg-base-200 rounded-lg p-4 text-center">
                  <div className="stat-title">Margen Promedio</div>
                  <div className="stat-value">{(reporteData.kpis.utilidad_bruta_porcentaje_promedio ?? 0).toFixed(2)}%</div>
                </div>
              </>
            )}
          </div>
          <div className="overflow-x-auto">
            <table className="table table-zebra w-full">
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Documento</th>
                  <th>Tercero</th>
                  <th>Producto</th>
                  <th className="text-right">Cantidad</th>
                  <th className="text-right">Vr. Unitario</th>
                  <th className="text-right">Vr. Total</th>
                  {filtros.tipo_reporte === 'ventas' && (
                    <>
                      <th className="text-right">Costo Total</th>
                      <th className="text-right">Utilidad</th>
                      <th className="text-right">% Margen</th>
                    </>
                  )}
                </tr>
              </thead>
              <tbody>
                {reporteData.items.map((item, index) => (
                  <tr key={`${item.documento_id}-${item.producto_codigo}-${index}`}>
                    <td>{item.fecha}</td>
                    <td>{item.documento_ref}</td>
                    <td>{item.tercero_nombre}</td>
                    <td>{item.producto_nombre} ({item.producto_codigo})</td>
                    <td className="text-right">{(item.cantidad ?? 0).toFixed(2)}</td>
                    <td className="text-right">{formatCurrency(item.valor_unitario)}</td>
                    <td className="text-right font-bold">{formatCurrency(item.valor_total_linea)}</td>
                    {filtros.tipo_reporte === 'ventas' && (
                      <>
                        <td className="text-right">{formatCurrency(item.costo_total_linea)}</td>
                        <td className="text-right text-success">{formatCurrency(item.utilidad_bruta_valor)}</td>
                        <td className="text-right">{(item.utilidad_bruta_porcentaje ?? 0).toFixed(2)}%</td>
                      </>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExploradorTransaccionesPage;