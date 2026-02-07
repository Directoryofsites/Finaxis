'use client';

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { toast } from 'react-toastify';
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
  FaMagic,
  FaPrint
} from 'react-icons/fa';

// Importaciones
import { useAuth } from '../../context/AuthContext';
import { apiService } from '../../../lib/apiService';


// Estilos reusables
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white";

function CapturaRapidaContent() {
  const router = useRouter();
  const searchParams = useSearchParams(); // Hook initializes searchParams
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

  const [isSeleccionarConceptoModalOpen, setIsSeleccionarConceptoModalOpen] = useState(false);
  const [conceptoBusqueda, setConceptoBusqueda] = useState('');
  const [movimientoIndexSeleccionado, setMovimientoIndexSeleccionado] = useState(null);

  // --- ESTADOS DE FLUJO DE VERIFICACIÓN (NUEVO CENTRO DE CONTROL) ---
  const [imprimirAlGuardar, setImprimirAlGuardar] = useState(false);
  const [isMonitorOpen, setIsMonitorOpen] = useState(false);
  const [monitorData, setMonitorData] = useState([]); // Datos para la tabla de asientos
  const [monitorLoading, setMonitorLoading] = useState(false);
  const [monitorFilters, setMonitorFilters] = useState({
    fechaInicio: new Date(new Date().getFullYear(), new Date().getMonth(), 1), // Primer día del mes
    fechaFin: new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0) // Último día del mes
  });

  // --- ESTADOS DE REIMPRESIÓN ---
  const [isReimprimirModalOpen, setIsReimprimirModalOpen] = useState(false);
  const [reimprimirBusqueda, setReimprimirBusqueda] = useState('');
  const [documentosRecientes, setDocumentosRecientes] = useState([]);

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
    if (plantilla) {
      // Aplicar maestros sugeridos si existen en la plantilla
      if (plantilla.beneficiario_id_sugerido) {
        setBeneficiarioId(String(plantilla.beneficiario_id_sugerido));
      }
      if (plantilla.centro_costo_id_sugerido) {
        setCentroCostoId(String(plantilla.centro_costo_id_sugerido));
      }

      if (plantilla.detalles) {
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
      const docId = response.data.id; // Asumimos que el back devuelve el ID
      const docNumero = response.data.numero;

      setMensaje(`✅ Documento #${docNumero} guardado exitosamente.`);

      // --- LÓGICA DE IMPRESIÓN AUTOMÁTICA ---
      if (imprimirAlGuardar && docId) {
        handleImprimirDocumento(docId);
        toast.info("Generando PDF de impresión... 🖨️");
      }

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

  // --- MONITOR CONTABLE & REIMPRESIÓN LOGIC ---

  // 1. Cargar datos del Monitor
  useEffect(() => {
    if (isMonitorOpen) {
      const fetchMonitorData = async () => {
        setMonitorLoading(true);
        try {
          const inicio = monitorFilters.fechaInicio.toISOString().split('T')[0];
          const fin = monitorFilters.fechaFin.toISOString().split('T')[0];

          const queryParams = new URLSearchParams();
          queryParams.append('fecha_inicio', inicio);
          queryParams.append('fecha_fin', fin);

          const res = await apiService.get('/reports/journal', { params: queryParams });
          // Ordenar por ID descendente para ver lo último arriba
          const sorted = res.data.sort((a, b) => b.id - a.id);
          setMonitorData(sorted);
        } catch (err) {
          console.error("Error cargando monitor:", err);
          toast.error("Error al cargar movimientos del mes.");
        } finally {
          setMonitorLoading(false);
        }
      };

      fetchMonitorData();
    }
  }, [isMonitorOpen, monitorFilters]);

  // 2. Búsqueda de Documentos para Reimpresión
  useEffect(() => {
    if (isReimprimirModalOpen) {
      // Cargar últimos 10 al abrir
      const fetchRecientes = async () => {
        try {
          const res = await apiService.get('/documentos/?limit=10&skip=0'); // Ajustar endpoint según API real
          // Asegurar que sea array
          setDocumentosRecientes(Array.isArray(res.data) ? res.data : []);
        } catch (err) {
          console.error(err);
          setDocumentosRecientes([]); // Fallback a array vacio
        }
      };
      fetchRecientes();
    }
  }, [isReimprimirModalOpen]);

  const handleSearchReimprimir = async (term) => {
    setReimprimirBusqueda(term);
    if (!term) {
      // Recargar recientes si limpia
      const res = await apiService.get('/documentos/?limit=10&skip=0');
      setDocumentosRecientes(Array.isArray(res.data) ? res.data : []);
      return;
    }

    if (term.length > 2) {
      try {
        let queryParams = '';

        // 1. Detección Inteligente
        if (/^\d+$/.test(term)) {
          // Es un número -> Buscar por Número de Documento (prioridad) o NIT
          queryParams = `numero=${term}`;
        } else {
          // Es texto -> 
          // A. Intentar buscar Tercero (Nombre) en memoria local
          const terceroEncontrado = terceros.find(t =>
            t.razon_social.toLowerCase().includes(term.toLowerCase()) ||
            (t.primer_nombre && t.primer_nombre.toLowerCase().includes(term.toLowerCase()))
          );

          if (terceroEncontrado) {
            queryParams = `tercero_id=${terceroEncontrado.id}`;
          } else {
            // B. Si no es tercero, buscar en Observaciones
            queryParams = `observaciones=${term}`;
          }
        }

        const res = await apiService.get(`/documentos/?${queryParams}`);
        setDocumentosRecientes(Array.isArray(res.data) ? res.data : []);
      } catch (err) {
        console.error("Error buscando documentos:", err);
        setDocumentosRecientes([]);
      }
    }
  };

  const handleImprimirDocumento = async (id) => {
    try {
      const response = await apiService.get(`/documentos/${id}/pdf`, {
        responseType: 'blob'
      });
      const file = new Blob([response.data], { type: 'application/pdf' });
      const fileURL = URL.createObjectURL(file);
      window.open(fileURL, '_blank');
    } catch (error) {
      console.error("Error al imprimir documento:", error);
      toast.error("Error al generar el PDF del documento.");
    }
  };

  // --- STATE FOR AUTO SAVE PERSISTENCE ---
  const [shouldAutoSaveState, setShouldAutoSaveState] = useState(false);

  // --- IA AUTO-FILL STAGE 1 & INIT ---
  useEffect(() => {
    // Capture auto-save intent immediately on mount or param change
    if (searchParams.get('ai_autosave') === 'true') {
      setShouldAutoSaveState(true);
    }
  }, [searchParams]);

  // --- IA AUTO-FILL STAGE 1: MATCHING (PLANTILLA & TERCERO) ---
  useEffect(() => {
    // Stage 1: Solo si hay parametros y maestros, pero NO hemos asignado plantilla aun
    if (pageIsLoading || plantillas.length === 0 || terceros.length === 0) return;
    if (plantillaId) return; // Ya se asignó plantilla, evitar re-run

    const aiPlantilla = searchParams.get('ai_plantilla');
    if (aiPlantilla) {
      // 1. Fuzzy Match Plantilla
      const normalize = (str) => str ? str.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "") : "";
      const searchNorm = normalize(aiPlantilla);

      const bestPlantilla = plantillas.map(p => {
        const nameNorm = normalize(p.nombre_plantilla);
        let score = 0;
        if (nameNorm === searchNorm) score = 100;
        else if (nameNorm.includes(searchNorm)) score = 50;
        else if (searchNorm.split(' ').some(w => nameNorm.includes(w) && w.length > 3)) score = 20;
        return { ...p, score };
      }).sort((a, b) => b.score - a.score)[0];

      if (bestPlantilla && bestPlantilla.score > 0) {
        handlePlantillaChange(bestPlantilla.id);
        toast.info(`IA: Plantilla detectada: ${bestPlantilla.nombre_plantilla}`);

        // 2. Fuzzy Match Tercero
        const aiTercero = searchParams.get('ai_tercero');
        if (aiTercero) {
          const searchTercero = normalize(aiTercero);
          const searchWords = searchTercero.split(' ');

          const bestTercero = terceros.map(t => {
            let score = 0;
            const name = normalize(t.razon_social + ' ' + (t.primer_nombre || '') + ' ' + (t.primer_apellido || ''));
            if (name === searchTercero) score += 100;
            if (name.includes(searchTercero)) score += 50;
            searchWords.forEach(w => { if (w.length > 3 && name.includes(w)) score += 10; });
            return { ...t, score };
          }).sort((a, b) => b.score - a.score)[0];

          if (bestTercero && bestTercero.score > 0) {
            setBeneficiarioId(bestTercero.id);
            toast.info(`IA: Beneficiario: ${bestTercero.razon_social}`);
          }
        }
      }
    }
  }, [plantillas, terceros, pageIsLoading, searchParams, plantillaId]);

  // --- IA AUTO-FILL STAGE 2: VALUE & EXECUTION ---
  useEffect(() => {
    // Stage 2: Esperar a que existan movimientos cargados (producto de Stage 1)
    if (movimientos.length === 0) return;

    const aiValor = searchParams.get('ai_valor');
    if (aiValor && !valorUnico) { // Solo si hay valor en URL y no hemos puesto nada aun
      // Aplicar Valor
      handleValorUnicoChange(aiValor);
      toast.success(`IA: Valor asignado: ${formatCurrency(parseInt(aiValor))}`);

      // Limpiar URL para evitar loops
      const newUrl = window.location.pathname;
      window.history.replaceState({}, '', newUrl); // CLEAN URL HERE
    }
  }, [movimientos, searchParams, valorUnico]);

  // --- IA AUTO-FILL STAGE 3: AUTO SAVE ---
  useEffect(() => {
    // Use saved state instead of transient url param
    if (shouldAutoSaveState && estaBalanceado && totales.debito > 0 && valorUnico) {
      const timer = setTimeout(() => {
        const btn = document.getElementById('btn-guardar-captura');
        if (btn && !btn.disabled) {
          toast.success("IA: Todo listo. Guardando automáticamente... 💾");
          btn.click();
        }
      }, 2000); // 2 segundos para que el usuario vea el resultado antes de guardar
      return () => clearTimeout(timer);
    }
  }, [estaBalanceado, totales, valorUnico, shouldAutoSaveState]);
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
          apiService.get('/conceptos-favoritos/')
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

  // --- BLINDAJE AUDITORÍA/CLON ---
  if (user?.empresa?.modo_operacion === 'AUDITORIA_READONLY') {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-6 text-center">
        <div className="bg-white p-8 rounded-xl shadow-lg border border-yellow-200 max-w-lg">
          <FaExclamationTriangle className="text-5xl text-yellow-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Restricción de Auditoría</h2>
          <p className="text-gray-600 mb-6">
            Esta empresa está en <strong>Modo Auditoría / Clon</strong>.
            La función de <strong>Captura Rápida</strong> está deshabilitada para prevenir la creación manual de registros nuevos.
            Solo se permite la importación y consulta de datos.
          </p>
          <button
            onClick={() => router.push('/contabilidad/documentos')}
            className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-bold"
          >
            Volver a Documentos
          </button>
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

        {/* BARRA DE HERRAMIENTAS (CENTRO DE CONTROL) */}
        <div className="flex items-center gap-3 animate-fadeIn mt-4 md:mt-0">

          {/* TOGGLE IMPRIMIR AL GUARDAR */}
          <div className="flex items-center gap-2 bg-white px-3 py-2 rounded-lg border border-indigo-100 shadow-sm transition-all hover:shadow-md cursor-pointer" onClick={() => setImprimirAlGuardar(!imprimirAlGuardar)}>
            <div className={`w-8 h-4 flex items-center bg-gray-300 rounded-full p-1 duration-300 ease-in-out ${imprimirAlGuardar ? 'bg-indigo-600' : ''}`}>
              <div className={`bg-white w-3 h-3 rounded-full shadow-md transform duration-300 ease-in-out ${imprimirAlGuardar ? 'translate-x-3' : ''}`}></div>
            </div>
            <span className="text-sm font-bold text-gray-600 select-none">Imprimir</span>
          </div>

          {/* BOTÓN VER ASIENTOS (MONITOR EXTERNO) */}
          <button
            type="button"
            onClick={() => window.open('/contabilidad/captura-rapida/monitor', 'MonitorAsientos', 'width=1200,height=800,resizable=yes,scrollbars=yes')}
            className="flex items-center gap-2 px-3 py-2 bg-indigo-600 text-white border border-indigo-600 rounded-lg hover:bg-indigo-700 shadow-md transition-all transform hover:scale-105 text-sm font-medium"
            title="Abrir monitor en ventana independiente"
          >
            <FaMagic /> Monitor de Asientos
          </button>

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
                              <FaSave />
                            </button>
                            {/* BOTÓN BUSCAR CONCEPTO (SOLO PRIMER REGISTRO) */}
                            {index === 0 && (
                              <button
                                type="button"
                                onClick={() => {
                                  setMovimientoIndexSeleccionado(index);
                                  setIsSeleccionarConceptoModalOpen(true);
                                  setConceptoBusqueda('');
                                }}
                                className="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-md transition-colors"
                                title="Buscar concepto en librería"
                              >
                                <FaBook />
                              </button>
                            )}
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
        {/* MODAL SELECCIONAR CONCEPTO */}
        {isSeleccionarConceptoModalOpen && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex justify-center items-center z-50 animate-fadeIn">
            <div className="bg-white p-6 rounded-xl shadow-2xl w-full max-w-lg border border-gray-100 flex flex-col max-h-[80vh]">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                  <FaBook className="text-green-500" /> Librería de Conceptos
                </h2>
                <button onClick={() => setIsSeleccionarConceptoModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                  ✕
                </button>
              </div>

              <input
                type="text"
                placeholder="Buscar concepto..."
                value={conceptoBusqueda}
                onChange={(e) => setConceptoBusqueda(e.target.value)}
                className={`${inputClass} mb-4`}
                autoFocus
              />

              <div className="flex-1 overflow-y-auto space-y-2 pr-2 custom-scrollbar">
                {conceptos
                  .filter(c => !conceptoBusqueda || c.descripcion.toLowerCase().includes(conceptoBusqueda.toLowerCase()))
                  .map((c) => (
                    <button
                      key={c.id}
                      onClick={() => {
                        handleConceptoChange(movimientoIndexSeleccionado, c.descripcion);
                        setIsSeleccionarConceptoModalOpen(false);
                      }}
                      className="w-full text-left p-3 rounded-lg hover:bg-indigo-50 border border-gray-100 hover:border-indigo-200 transition-all text-sm text-gray-700 flex justify-between group"
                    >
                      <span>{c.descripcion}</span>
                      <span className="text-indigo-400 opacity-0 group-hover:opacity-100 transition-opacity text-xs italic">Seleccionar</span>
                    </button>
                  ))}
                {conceptos.length === 0 && (
                  <p className="text-center text-gray-400 py-4 italic">No hay conceptos guardados aún.</p>
                )}
              </div>

              <div className="mt-4 pt-4 border-t border-gray-100 flex justify-end">
                <button onClick={() => setIsSeleccionarConceptoModalOpen(false)} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
                  Cerrar
                </button>
              </div>
            </div>
          </div>
        )}
        {/* MODAL REIMPRIMIR */}
        {isReimprimirModalOpen && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex justify-center items-center z-[60] animate-fadeIn">
            <div className="bg-white p-6 rounded-xl shadow-2xl w-full max-w-lg border border-gray-100 flex flex-col max-h-[80vh]">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                  <FaPrint className="text-gray-500" /> Reimprimir Documento
                </h2>
                <button onClick={() => setIsReimprimirModalOpen(false)} className="text-gray-400 hover:text-gray-600">✕</button>
              </div>

              <div className="mb-4">
                <input
                  type="text"
                  className={inputClass}
                  placeholder="Buscar por número, tercero o valor..."
                  value={reimprimirBusqueda}
                  onChange={(e) => handleSearchReimprimir(e.target.value)}
                  autoFocus
                />
              </div>

              <div className="flex-1 overflow-y-auto space-y-2 p-1 custom-scrollbar bg-gray-50 rounded-lg min-h-[200px]">
                {!Array.isArray(documentosRecientes) || documentosRecientes.length === 0 ? (
                  <p className="text-center text-gray-400 py-10 italic">No se encontraron documentos.</p>
                ) : (
                  <div className="space-y-2">
                    {documentosRecientes.map(doc => (
                      <div key={doc.id} className="bg-white p-3 rounded-lg border border-gray-100 shadow-sm flex justify-between items-center hover:shadow-md transition-shadow">
                        <div>
                          <div className="font-bold text-gray-800 text-sm">
                            {doc.tipo_documento?.codigo || 'DOC'} #{doc.numero}
                          </div>
                          <div className="text-xs text-gray-500">
                            {new Date(doc.fecha).toLocaleDateString()} - {doc.beneficiario?.razon_social || 'Sin Beneficiario'}
                          </div>
                        </div>
                        <button
                          onClick={() => handleImprimirDocumento(doc.id)}
                          className="p-2 text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                          title="Imprimir"
                        >
                          <FaPrint />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
        {isMonitorOpen && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex justify-center items-end z-[60] animate-fadeIn">
            <div className="bg-white w-full h-[85vh] rounded-t-2xl shadow-2xl flex flex-col animate-slideUp">
              {/* HEADER MONITOR */}
              <div className="p-4 border-b border-gray-200 flex justify-between items-center bg-gray-50 rounded-t-2xl">
                <div>
                  <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                    <FaMagic className="text-indigo-600" /> Monitor de Asientos
                  </h2>
                  <p className="text-sm text-gray-500">Visualizando movimientos del mes actual en tiempo real.</p>
                </div>
                <button
                  onClick={() => setIsMonitorOpen(false)}
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-200 rounded-full transition-colors"
                >
                  ✕
                </button>
              </div>

              {/* BODY MONITOR (TABLA DE DATOS) */}
              <div className="flex-1 p-6 overflow-y-auto bg-slate-50">
                {monitorLoading ? (
                  <div className="flex justify-center items-center h-full">
                    <FaBolt className="text-4xl text-indigo-300 animate-pulse" />
                  </div>
                ) : monitorData.length === 0 ? (
                  <div className="text-center py-20 opacity-50">
                    <FaMagic className="text-6xl text-gray-300 mx-auto mb-4" />
                    <p className="text-gray-500">No hay movimientos registrados en este periodo.</p>
                  </div>
                ) : (
                  <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                    <table className="min-w-full divide-y divide-gray-200 text-sm">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-3 text-left font-bold text-gray-500">Fecha</th>
                          <th className="px-4 py-3 text-left font-bold text-gray-500">Documento</th>
                          <th className="px-4 py-3 text-left font-bold text-gray-500">Tercero</th>
                          <th className="px-4 py-3 text-left font-bold text-gray-500">Detalle</th>
                          <th className="px-4 py-3 text-right font-bold text-gray-500">Débito</th>
                          <th className="px-4 py-3 text-right font-bold text-gray-500">Crédito</th>
                          <th className="px-4 py-3 text-center font-bold text-gray-500">Acción</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {monitorData.map((row, idx) => (
                          <tr key={idx} className="hover:bg-indigo-50/30 transition-colors">
                            <td className="px-4 py-2 text-gray-600 whitespace-nowrap">
                              {new Date(row.fecha).toLocaleDateString('es-CO')}
                            </td>
                            <td className="px-4 py-2 font-mono text-indigo-600 font-medium">
                              {row.tipo_documento_codigo} {row.numero_documento}
                            </td>
                            <td className="px-4 py-2 text-gray-700 truncate max-w-xs" title={row.beneficiario_nombre}>
                              {row.beneficiario_nombre}
                            </td>
                            <td className="px-4 py-2 text-gray-500 italic truncate max-w-xs" title={row.concepto}>
                              {row.concepto}
                            </td>
                            <td className="px-4 py-2 text-right font-mono text-gray-700">
                              {parseFloat(row.debito) > 0 ? parseFloat(row.debito).toLocaleString('es-CO') : '-'}
                            </td>
                            <td className="px-4 py-2 text-right font-mono text-gray-700">
                              {parseFloat(row.credito) > 0 ? parseFloat(row.credito).toLocaleString('es-CO') : '-'}
                            </td>
                            <td className="px-4 py-2 text-center">
                              {/* Usamos el ID del documento si viene en el reporte, o asumimos que podemos construirlo */}
                              {/* El reporte journal devuelve filas planas, no objetos documento. Necesitamos el ID del documento para imprimir */}
                              {/* Si el row no tiene document_id, no podemos imprimir directo. Revisar API */}
                              {row.documento_id && (
                                <button
                                  onClick={() => handleImprimirDocumento(row.documento_id)}
                                  className="text-gray-400 hover:text-indigo-600 transition-colors"
                                  title="Reimprimir Documento"
                                >
                                  <FaPrint />
                                </button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function CapturaRapidaPage() {
  return (
    <React.Suspense fallback={<div className="h-screen flex items-center justify-center text-indigo-500">Cargando Captura Rápida...</div>}>
      <CapturaRapidaContent />
    </React.Suspense>
  );
}