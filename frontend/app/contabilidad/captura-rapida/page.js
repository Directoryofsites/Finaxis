'use client';

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import {
  FaBolt,
  FaSave,
  FaPlus,
  FaCalendarAlt,
  FaUserTag,
  FaBuilding,
  FaBook,
  FaCheckCircle,
  FaExclamationTriangle,
  FaMagic
} from 'react-icons/fa';

// Importaciones
import { useAuth } from '../../context/AuthContext';
import { apiService } from '../../../lib/apiService';


// Estilos reusables
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white";

export default function CapturaRapidaPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();

  // --- ESTADOS DE DATOS MAESTROS ---
  const [cuentas, setCuentas] = useState([]);
  const [terceros, setTerceros] = useState([]);
  const [centrosCosto, setCentrosCosto] = useState([]);
  const [plantillas, setPlantillas] = useState([]);
  const [conceptos, setConceptos] = useState([]);

  // --- ESTADOS DE UI Y NOTIFICACIONES ---
  const [pageIsLoading, setPageIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [mensaje, setMensaje] = useState('');
  const [isSubmittingDoc, setIsSubmittingDoc] = useState(false);

  // Estados de Modales y Formularios Auxiliares
  const [isTerceroModalOpen, setIsTerceroModalOpen] = useState(false);
  const [isConceptoModalOpen, setIsConceptoModalOpen] = useState(false);
  const [nuevoTercero, setNuevoTercero] = useState({ nit: '', razon_social: '' });
  const [nuevoConcepto, setNuevoConcepto] = useState({ descripcion: '' });
  const [terceroModalError, setTerceroModalError] = useState('');
  const [conceptoModalError, setConceptoModalError] = useState('');
  const [isSubmittingTercero, setIsSubmittingTercero] = useState(false);
  const [isSubmittingConcepto, setIsSubmittingConcepto] = useState(false);

  // --- ESTADOS DEL FORMULARIO PRINCIPAL ---
  const [fecha, setFecha] = useState(new Date());
  const [plantillaId, setPlantillaId] = useState('');
  const [beneficiarioId, setBeneficiarioId] = useState('');
  const [centroCostoId, setCentroCostoId] = useState('');
  const [movimientos, setMovimientos] = useState([]);
  const [valorUnico, setValorUnico] = useState('');
  const [totales, setTotales] = useState({ debito: 0, credito: 0 });

  // --- CÁLCULOS DERIVADOS ---
  const plantillasValidas = useMemo(() => plantillas || [], [plantillas]);

  const estaBalanceado = useMemo(() => {
    const diff = Math.abs(totales.debito - totales.credito);
    return totales.debito > 0 && diff < 0.01;
  }, [totales]);

  // --- FUNCIONES DE LÓGICA ---

  // 1. Manejo de Plantillas
  const handlePlantillaChange = (id) => {
    setPlantillaId(id);
    if (!id) {
      setMovimientos([]);
      setValorUnico('');
      return;
    }

    const plantilla = plantillas.find(p => p.id === parseInt(id));
    if (plantilla && plantilla.detalles) {
      // Cargar movimientos base de la plantilla
      const nuevosMovimientos = plantilla.detalles.map(d => ({
        cuenta_id: d.cuenta_id || (cuentas.find(c => c.codigo === d.cuenta_codigo)?.id),
        centro_costo_id: d.centro_costo_id,
        concepto: d.concepto,
        debito: 0,  // Se calculan al meter el valor
        credito: 0,
        naturaleza: d.debito > 0 ? 'D' : 'C', // Detectar naturaleza base
        base_calculo: d.debito || d.credito || 0 // Guardar proporción si existe
      }));
      setMovimientos(nuevosMovimientos);
      setValorUnico(''); // Resetear valor para obligar recálculo
      setTotales({ debito: 0, credito: 0 });
    }
  };

  // 2. Distribución del Valor Único (La Magia de Captura Rápida)
  const handleValorUnicoChange = (val) => {
    setValorUnico(val);
    const monto = parseFloat(val) || 0;

    if (monto === 0) return;

    const nuevosMovs = movimientos.map(m => {
      return {
        ...m,
        debito: m.naturaleza === 'D' ? monto : 0,
        credito: m.naturaleza === 'C' ? monto : 0
      };
    });

    setMovimientos(nuevosMovs);
    setTotales({ debito: monto, credito: monto });
  };

  const handleConceptoChange = (index, val) => {
    const newMovs = [...movimientos];
    newMovs[index].concepto = val;

    // --- CORRECCIÓN UX: EFECTO ESPEJO ---
    // Si escribo en la primera línea (index 0), replicar automáticamente a la segunda (index 1)
    // Esto agiliza la digitación en asientos simples.
    if (index === 0 && newMovs.length > 1) {
      newMovs[1].concepto = val;
    }

    setMovimientos(newMovs);
  };

  const resetFormulario = () => {
    setPlantillaId('');
    setBeneficiarioId('');
    setCentroCostoId('');
    setMovimientos([]);
    setValorUnico('');
    setTotales({ debito: 0, credito: 0 });
    setFecha(new Date());
  };

  // --- MANEJO DE ENVÍO ---
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMensaje('');

    if (!plantillaId || !estaBalanceado) {
      setError('Seleccione una plantilla válida y asegúrese de que el asiento esté balanceado.');
      return;
    }

    setIsSubmittingDoc(true);
    try {
      const plantillaSeleccionada = plantillas.find(p => p.id === parseInt(plantillaId));
      if (!plantillaSeleccionada) throw new Error("Plantilla no encontrada.");

      const tipoDocId = plantillaSeleccionada.tipo_documento_id_sugerido;
      if (!tipoDocId) throw new Error("La plantilla no tiene un Tipo de Documento asociado.");

      const payload = {
        fecha: fecha.toISOString().split('T')[0],
        tipo_documento_id: tipoDocId,
        beneficiario_id: beneficiarioId ? parseInt(beneficiarioId) : null,
        centro_costo_id: centroCostoId ? parseInt(centroCostoId) : null,
        movimientos: movimientos.map(m => ({
          cuenta_id: m.cuenta_id,
          centro_costo_id: centroCostoId ? parseInt(centroCostoId) : (m.centro_costo_id || null),
          concepto: m.concepto,
          debito: m.debito,
          credito: m.credito,
        }))
      };

      const response = await apiService.post('/documentos/', payload);
      setMensaje(`✅ Documento #${response.data.numero} guardado exitosamente.`);
      resetFormulario();
      window.scrollTo({ top: 0, behavior: 'smooth' });

    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error al guardar el documento.';
      console.error("Error en handleSubmit:", err);
      setError(errorMsg);
    } finally {
      setIsSubmittingDoc(false);
    }
  };

  // --- CREACIÓN AUXILIARES ---
  const handleCreateTercero = async () => {
    setTerceroModalError('');
    if (!nuevoTercero.nit || !nuevoTercero.razon_social) {
      setTerceroModalError('El NIT y el Nombre son obligatorios.');
      return;
    }
    setIsSubmittingTercero(true);
    try {
      const payload = { ...nuevoTercero, empresa_id: user.empresaId };
      const response = await apiService.post('/terceros/', payload);
      const terceroCreado = response.data;
      setTerceros(prev => [...prev, terceroCreado].sort((a, b) => a.razon_social.localeCompare(b.razon_social)));
      setBeneficiarioId(String(terceroCreado.id));
      setIsTerceroModalOpen(false);
      setNuevoTercero({ nit: '', razon_social: '' });
      setMensaje(`Tercero "${terceroCreado.razon_social}" creado exitosamente.`);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Error al crear el tercero.';
      setTerceroModalError(errorMsg);
    } finally {
      setIsSubmittingTercero(false);
    }
  };

  const handleCreateConcepto = async () => {
    setConceptoModalError('');
    if (!nuevoConcepto.descripcion) return;
    setIsSubmittingConcepto(true);
    try {
      const payload = { ...nuevoConcepto, empresa_id: user.empresaId };
      // --- CORRECCIÓN API: Ruta correcta basada en estructura backend ---
      await apiService.post('/conceptos-favoritos/', payload);
      setIsConceptoModalOpen(false);
      setMensaje("Concepto guardado en librería.");
    } catch (err) {
      console.error("Error creando concepto:", err);
      setConceptoModalError("Error al guardar concepto. Verifique conexión.");
    } finally {
      setIsSubmittingConcepto(false);
    }
  };

  // --- EFECTOS ---
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === 'Insert') {
        event.preventDefault();
        setIsTerceroModalOpen(true);
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  useEffect(() => {
    if (authLoading) return;
    if (!user || !user.empresaId) {
      router.push('/login');
      return;
    }
    const fetchMaestros = async () => {
      if (cuentas.length > 0) {
        setPageIsLoading(false);
        return;
      }
      setPageIsLoading(true);
      setError('');
      try {
        // Se asume que las rutas GET funcionan (ya que no reportaste error aquí)
        const [cuentasRes, tercerosRes, ccostoRes, plantillasRes, conceptosRes] = await Promise.all([
          apiService.get('/plan-cuentas/'),
          apiService.get('/terceros/'),
          apiService.get('/centros-costo/get-flat?permite_movimiento=true'),
          apiService.get('/plantillas/'),
          apiService.get('/favoritos/')
        ]);

        const aplanarCuentas = (cuentas) => {
          let listaPlana = [];
          const recorrer = (cuenta) => {
            if (cuenta.permite_movimiento) { listaPlana.push(cuenta); }
            if (cuenta.children) { cuenta.children.forEach(recorrer); }
          };
          cuentas.forEach(recorrer);
          return listaPlana;
        };

        setCuentas(aplanarCuentas(cuentasRes.data));
        setTerceros(tercerosRes.data);
        setCentrosCosto(ccostoRes.data);
        setPlantillas(plantillasRes.data);
        setConceptos(conceptosRes.data);
      } catch (err) {
        const errorMsg = err.response?.data?.detail || 'Error fatal al cargar los datos maestros.';
        console.error("Error en fetchMaestros:", err);
        setError(errorMsg);
      } finally {
        setPageIsLoading(false);
      }
    };
    fetchMaestros();
  }, [user, authLoading, router, cuentas.length]);

  if (pageIsLoading || authLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
        <FaBolt className="text-indigo-300 text-6xl mb-4 animate-pulse" />
        <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando herramientas de captura...</p>
      </div>
    );
  }

  if (error && !cuentas.length) {
    return (
      <div className="min-h-screen bg-gray-50 p-6 flex items-center justify-center">
        <div className="bg-white p-8 rounded-xl shadow-lg border border-red-100 max-w-2xl text-center">
          <div className="flex justify-center mb-4">
            <div className="p-4 bg-red-100 rounded-full">
              <FaExclamationTriangle className="text-3xl text-red-500" />
            </div>
          </div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Error de Carga</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <div className="flex justify-center">
            {/* Botón de regreso eliminado */}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
      <div className="max-w-6xl mx-auto">

        {/* ENCABEZADO */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
          <div>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-100 rounded-lg text-amber-600">
                <FaBolt />
              </div>
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="text-3xl font-bold text-gray-800">Captura Rápida</h1>
                  <button
                    onClick={() => window.open('/manual/capitulo_25_captura_rapida.html', '_blank')}
                    className="flex items-center gap-2 px-2 py-1 bg-white border border-indigo-200 text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors font-medium shadow-sm"
                    title="Ver Manual de Usuario"
                  >
                    <FaBook /> <span className="hidden md:inline">Manual</span>
                  </button>
                </div>
                <p className="text-gray-500 text-sm">Contabilización acelerada basada en plantillas.</p>
              </div>
            </div>
          </div>
        </div>

        {/* NOTIFICACIONES */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded-r-lg animate-pulse">
            <p className="font-bold">Atención</p>
            <p>{error}</p>
          </div>
        )}
        {mensaje && (
          <div className="mb-6 p-4 bg-green-50 border-l-4 border-green-500 text-green-700 rounded-r-lg animate-fadeIn">
            <div className="flex items-center gap-2">
              <FaCheckCircle className="text-xl" />
              <p className="font-bold">{mensaje}</p>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">

          {/* CARD 1: CONFIGURACIÓN INICIAL */}
          <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 animate-fadeIn">
            <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2">
              <span className="bg-indigo-100 text-indigo-600 w-6 h-6 flex items-center justify-center rounded-full text-xs">1</span>
              Datos del Asiento
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">

              {/* FECHA */}
              <div>
                <label htmlFor="fecha" className={labelClass}>Fecha</label>
                <div className="relative">
                  <DatePicker
                    selected={fecha}
                    onChange={(date) => setFecha(date || new Date())}
                    dateFormat="dd/MM/yyyy"
                    className={inputClass}
                    id="fecha"
                  />
                  <FaCalendarAlt className="absolute right-3 top-3 text-gray-400 pointer-events-none" />
                </div>
              </div>

              {/* PLANTILLA (DESTACADO) */}
              <div className="lg:col-span-1">
                <label htmlFor="plantilla" className="block text-xs font-bold text-indigo-600 uppercase mb-1 tracking-wide">
                  ⚡ Plantilla (Requerido)
                </label>
                <div className="relative">
                  <select
                    id="plantilla"
                    value={plantillaId}
                    onChange={e => handlePlantillaChange(e.target.value)}
                    className={`${selectClass} border-indigo-300 bg-indigo-50 focus:ring-indigo-500 text-indigo-900 font-semibold`}
                  >
                    <option value="">Seleccione...</option>
                    {plantillasValidas.map(p => (<option key={p.id} value={p.id}>{p.nombre_plantilla}</option>))}
                  </select>
                  <FaMagic className="absolute right-8 top-3 text-indigo-400 pointer-events-none" />
                </div>
              </div>

              {/* BENEFICIARIO */}
              <div className="lg:col-span-1">
                <label htmlFor="beneficiario" className={labelClass}>Beneficiario</label>
                <div className="flex gap-2">
                  <div className="relative w-full">
                    <select id="beneficiario" value={beneficiarioId} onChange={e => setBeneficiarioId(e.target.value)} className={selectClass}>
                      <option value="">Seleccione...</option>
                      {terceros.map(t => <option key={t.id} value={t.id}>{t.razon_social}</option>)}
                    </select>
                    <FaUserTag className="absolute right-8 top-3 text-gray-400 pointer-events-none" />
                  </div>
                  <button
                    type="button"
                    onClick={() => setIsTerceroModalOpen(true)}
                    className="px-3 bg-indigo-100 text-indigo-600 rounded-lg hover:bg-indigo-200 transition-colors"
                    title="Crear nuevo tercero"
                  >
                    <FaPlus />
                  </button>
                </div>
              </div>

              {/* CENTRO DE COSTO */}
              <div>
                <label htmlFor="centroCosto" className={labelClass}>Centro de Costo</label>
                <div className="relative">
                  <select id="centroCosto" value={centroCostoId} onChange={e => setCentroCostoId(e.target.value)} className={selectClass}>
                    <option value="">Ninguno</option>
                    {centrosCosto.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
                  </select>
                  <FaBuilding className="absolute right-8 top-3 text-gray-400 pointer-events-none" />
                </div>
              </div>
            </div>
          </div>

          {/* CARD 2: DETALLES (SOLO SI HAY PLANTILLA) */}
          {plantillaId && (
            <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 animate-slideDown">
              <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2">
                <span className="bg-indigo-100 text-indigo-600 w-6 h-6 flex items-center justify-center rounded-full text-xs">2</span>
                Valores y Conceptos
              </h3>

              {/* INPUT DE VALOR GIGANTE */}
              <div className="mb-8 max-w-md mx-auto text-center">
                <label htmlFor="valorUnico" className="block text-sm font-bold text-gray-500 uppercase mb-2">
                  Valor Total del Asiento
                </label>
                <div className="relative">
                  <span className="absolute left-4 top-4 text-2xl text-gray-400 font-mono">$</span>
                  <input
                    id="valorUnico"
                    type="number"
                    value={valorUnico}
                    onChange={e => handleValorUnicoChange(e.target.value)}
                    className="w-full pl-10 px-4 py-3 text-3xl font-mono font-bold text-gray-800 border-2 border-indigo-200 rounded-xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 outline-none transition-all text-center shadow-inner bg-gray-50"
                    placeholder="0.00"
                    required
                    autoFocus
                  />
                </div>
              </div>

              {/* TABLA DE MOVIMIENTOS */}
              <div className="overflow-hidden rounded-xl border border-gray-200">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-slate-100">
                    <tr>
                      <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Cuenta Contable</th>
                      <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider w-1/3">Concepto / Detalle</th>
                      <th className="px-6 py-4 text-right text-xs font-bold text-gray-500 uppercase tracking-wider">Débito</th>
                      <th className="px-6 py-4 text-right text-xs font-bold text-gray-500 uppercase tracking-wider">Crédito</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-100">
                    {movimientos.map((mov, index) => (
                      <tr key={index} className="hover:bg-gray-50 transition-colors">
                        <td className="px-6 py-4 text-sm text-gray-700">
                          <div className="font-mono font-bold text-indigo-900">
                            {cuentas.find(c => c.id === mov.cuenta_id)?.codigo}
                          </div>
                          <div className="text-xs text-gray-500">
                            {cuentas.find(c => c.id === mov.cuenta_id)?.nombre}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <input
                              type="text"
                              value={mov.concepto || ''}
                              onChange={(e) => handleConceptoChange(index, e.target.value)}
                              className="w-full px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-indigo-200 outline-none"
                              placeholder="Descripción del movimiento..."
                            />
                            <button
                              type="button"
                              onClick={() => { setNuevoConcepto({ descripcion: mov.concepto }); setIsConceptoModalOpen(true); }}
                              className="p-2 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-md transition-colors"
                              title="Guardar concepto en librería"
                            >
                              <FaBook />
                            </button>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-right text-sm font-mono font-medium text-gray-700">
                          {parseFloat(mov.debito) > 0 ? parseFloat(mov.debito).toLocaleString('es-CO', { minimumFractionDigits: 2 }) : '-'}
                        </td>
                        <td className="px-6 py-4 text-right text-sm font-mono font-medium text-gray-700">
                          {parseFloat(mov.credito) > 0 ? parseFloat(mov.credito).toLocaleString('es-CO', { minimumFractionDigits: 2 }) : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>

                  {/* FOOTER DE TOTALES */}
                  <tfoot className="bg-slate-50 border-t-2 border-slate-200">
                    <tr>
                      <td colSpan="2" className="px-6 py-4 text-right text-sm font-bold text-gray-600 uppercase">Totales Control</td>
                      <td className={`px-6 py-4 text-right text-sm font-bold font-mono ${estaBalanceado ? 'text-green-600' : 'text-red-500'}`}>
                        {totales.debito.toLocaleString('es-CO', { minimumFractionDigits: 2 })}
                      </td>
                      <td className={`px-6 py-4 text-right text-sm font-bold font-mono ${estaBalanceado ? 'text-green-600' : 'text-red-500'}`}>
                        {totales.credito.toLocaleString('es-CO', { minimumFractionDigits: 2 })}
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>

              {!estaBalanceado && totales.debito > 0 && (
                <div className="mt-4 text-center text-sm text-red-500 font-semibold animate-pulse">
                  ⚠️ El asiento no está balanceado. Revise los valores.
                </div>
              )}
            </div>
          )}

          {/* BOTÓN DE GUARDADO FINAL */}
          <div className="mt-8 flex justify-end">
            <button
              type="submit"
              disabled={!estaBalanceado || isSubmittingDoc}
              className={`
                      px-10 py-4 rounded-xl shadow-lg font-bold text-white text-lg transition-all transform hover:-translate-y-1 flex items-center gap-3
                      ${!estaBalanceado || isSubmittingDoc
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-green-600 hover:bg-green-700 hover:shadow-green-200'}
                  `}
            >
              {isSubmittingDoc ? (
                'Guardando...'
              ) : (
                <>
                  <FaSave className="text-xl" /> Guardar Documento
                </>
              )}
            </button>
          </div>
        </form>

        {/* --- MODALES (ESTILIZADOS) --- */}

        {/* MODAL TERCERO */}
        {isTerceroModalOpen && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex justify-center items-center z-50 animate-fadeIn">
            <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-md border border-gray-100">
              <h2 className="text-2xl font-bold mb-6 text-gray-800">Nuevo Tercero (Rápido)</h2>
              {terceroModalError && <div className="p-3 mb-4 rounded-lg bg-red-50 text-red-600 border border-red-100 text-sm">{terceroModalError}</div>}

              <div className="space-y-4">
                <div>
                  <label htmlFor="nuevoTerceroNit" className={labelClass}>NIT / Identificación</label>
                  <input type="text" id="nuevoTerceroNit" value={nuevoTercero.nit} onChange={(e) => setNuevoTercero({ ...nuevoTercero, nit: e.target.value })} className={inputClass} autoFocus />
                </div>
                <div>
                  <label htmlFor="nuevoTerceroNombre" className={labelClass}>Nombre o Razón Social</label>
                  <input type="text" id="nuevoTerceroNombre" value={nuevoTercero.razon_social} onChange={(e) => setNuevoTercero({ ...nuevoTercero, razon_social: e.target.value })} className={inputClass} />
                </div>
              </div>

              <div className="mt-8 flex justify-end gap-3">
                <button onClick={() => setIsTerceroModalOpen(false)} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors" disabled={isSubmittingTercero}>Cancelar</button>
                <button onClick={handleCreateTercero} className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 shadow-md disabled:bg-gray-400" disabled={isSubmittingTercero}>
                  {isSubmittingTercero ? 'Guardando...' : 'Crear Tercero'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* MODAL CONCEPTO */}
        {isConceptoModalOpen && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex justify-center items-center z-50 animate-fadeIn">
            <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-md border border-gray-100">
              <h2 className="text-2xl font-bold mb-6 text-gray-800 flex items-center gap-2">
                <FaBook className="text-indigo-500" /> Guardar Concepto
              </h2>
              {conceptoModalError && <div className="p-3 mb-4 rounded-lg bg-red-50 text-red-600 border border-red-100 text-sm">{conceptoModalError}</div>}

              <label className={labelClass}>Descripción del Concepto</label>
              <input type="text" value={nuevoConcepto.descripcion || ''} onChange={(e) => setNuevoConcepto({ descripcion: e.target.value })} className={inputClass} autoFocus />

              <div className="mt-8 flex justify-end gap-3">
                <button onClick={() => setIsConceptoModalOpen(false)} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">Cancelar</button>
                <button onClick={handleCreateConcepto} disabled={isSubmittingConcepto} className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 shadow-md disabled:bg-gray-400">
                  {isSubmittingConcepto ? 'Guardando...' : 'Guardar en Librería'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}