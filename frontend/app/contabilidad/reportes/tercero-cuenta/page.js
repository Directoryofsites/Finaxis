'use client';

import React, { useState, useEffect, useRef, Suspense } from 'react';

import { useRouter, useSearchParams } from 'next/navigation';
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
import { toast } from 'react-toastify';

import { useAuth } from '../../../context/AuthContext';
import { apiService } from '../../../../lib/apiService';
import { recalcularSaldosTercero } from '../../../../lib/reportesService';

// --- ESTILOS REUSABLES (Manual v2.0) ---
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none pl-10";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white pl-10 text-gray-900";
const multiSelectClass = "w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white h-32";

const CheckboxMultiSelect = ({ options, selected, onChange, placeholder = "Seleccionar..." }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filteredOptions = options.filter(opt =>
    (opt.label || opt.nombre || opt.razon_social || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
    (opt.codigo || "").toLowerCase().includes(searchTerm.toLowerCase())
  );

  const isAllSelected = selected.includes('all');

  let displayLabel = placeholder;
  if (isAllSelected) {
    displayLabel = "Todos Seleccionados";
  } else if (selected.length > 0) {
    displayLabel = `${selected.length} Seleccionado(s)`;
  }

  const toggleOption = (value) => {
    if (value === 'all') {
      onChange(isAllSelected ? [] : ['all']);
    } else {
      let newSelected = [...selected];
      if (isAllSelected) {
        newSelected = [value];
      } else {
        if (newSelected.includes(value)) {
          newSelected = newSelected.filter(id => id !== value);
        } else {
          newSelected.push(value);
        }
      }
      onChange(newSelected);
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <div
        className="w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm bg-white text-sm cursor-pointer flex justify-between items-center"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex flex-col items-start overflow-hidden">
          <span className={`truncate font-bold ${selected.length === 0 ? 'text-gray-400' : 'text-indigo-700'}`}>
            {displayLabel}
          </span>
          {isAllSelected && <span className="text-xs text-gray-500 font-normal">Se incluirán todos los registros</span>}
        </div>
        <span className="text-gray-400">▼</span>
      </div>

      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-xl max-h-60 flex flex-col">
          <div className="p-2 border-b border-gray-100">
            <input
              type="text"
              className="w-full px-2 py-1 border border-gray-200 rounded text-xs focus:outline-none focus:border-indigo-500"
              placeholder="Buscar..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              autoFocus
            />
          </div>
          <div className="overflow-y-auto flex-1 p-2 space-y-1">
            <label className="flex items-center gap-2 px-2 py-1.5 hover:bg-indigo-50 rounded cursor-pointer border-b border-gray-100 mb-1">
              <input
                type="checkbox"
                className="rounded text-indigo-600 focus:ring-indigo-500 transform scale-110"
                checked={isAllSelected}
                onChange={() => toggleOption('all')}
              />
              <span className="text-sm font-bold text-gray-800">-- TODOS --</span>
            </label>
            {filteredOptions.map(option => {
              const isSelected = selected.includes(option.id);
              return (
                <label key={option.id} className={`flex items-center gap-2 px-2 py-1.5 rounded cursor-pointer transition-colors ${isSelected ? 'bg-indigo-50' : 'hover:bg-gray-50'}`}>
                  <input
                    type="checkbox"
                    className="rounded text-indigo-600 focus:ring-indigo-500"
                    checked={isSelected}
                    onChange={() => toggleOption(option.id)}
                  />
                  <div className="flex flex-col overflow-hidden">
                    <span className="text-sm text-gray-700 font-medium truncate">
                      {option.codigo ? `${option.codigo} - ` : ''}{option.label || option.nombre || option.razon_social}
                    </span>
                    {option.nit && <span className="text-xs text-gray-400">NIT: {option.nit}</span>}
                  </div>
                </label>
              );
            })}
            {filteredOptions.length === 0 && (
              <div className="text-center text-xs text-gray-400 py-2">No hay resultados</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

function ReporteTerceroCuentaContent() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const dataFetchedRef = useRef(false);

  // Estados
  const [terceros, setTerceros] = useState([]);
  const [selectedTercero, setSelectedTercero] = useState('');
  const [cuentasDelTercero, setCuentasDelTercero] = useState([]);
  const [selectedCuentas, setSelectedCuentas] = useState(['all']);

  // NUEVO: Estado para Modo Inverso (Cuenta -> Terceros)
  const [reportMode, setReportMode] = useState('tercero_first'); // 'tercero_first' | 'cuenta_first'
  const [cuentasAll, setCuentasAll] = useState([]); // Lista completa para el select
  const [selectedCuentaPrincipal, setSelectedCuentaPrincipal] = useState('');
  const [tercerosDelReporte, setTercerosDelReporte] = useState([]); // Terceros filtrados
  const [selectedTercerosMulti, setSelectedTercerosMulti] = useState(['all']);

  const [fechas, setFechas] = useState({
    inicio: new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0],
    fin: new Date().toISOString().split('T')[0]
  });

  const [reportData, setReportData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [recalculoStatus, setRecalculoStatus] = useState({ loading: false, message: '', error: '' });
  const [isPageReady, setPageReady] = useState(false);
  const [shouldAutoRun, setShouldAutoRun] = useState(false);

  // Estados para Automatización (Voz)
  const [autoPdfTrigger, setAutoPdfTrigger] = useState(false);
  const [wppNumber, setWppNumber] = useState(null);
  const [emailAddress, setEmailAddress] = useState(null);
  const lastProcessedParams = useRef('');

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

  const searchParams = useSearchParams();

  // Carga de Terceros (Solo Inicial)
  useEffect(() => {
    if (authLoading || dataFetchedRef.current) return;
    if (user) {
      const fetchTerceros = async () => {
        try {
          const res = await apiService.get('/terceros');
          setTerceros(res.data);
          dataFetchedRef.current = true;
        } catch (err) {
          setError("Error cargando terceros");
        }
      };
      fetchTerceros();
    }

  }, [user, authLoading]);

  // NUEVO: Carga de Cuentas Completas (Solo si se activa modo inverso)
  useEffect(() => {
    if (reportMode === 'cuenta_first' && user && cuentasAll.length === 0) {
      const fetchAllCuentas = async () => {
        try {
          const res = await apiService.get('/plan-cuentas/list-flat?permite_movimiento=true');
          setCuentasAll(res.data);
        } catch (err) {
          console.error("Error cargando cuentas", err);
        }
      };
      fetchAllCuentas();
    }
  }, [reportMode, user, cuentasAll]);

  // Carga de Configuración desde IA (Reactiva a URL/SearchParams)
  useEffect(() => {
    if (!authLoading && user && terceros.length > 0 && searchParams.size > 0) {
      const aiTercero = searchParams.get('tercero');
      const aiCuenta = searchParams.get('cuenta');
      const aiMode = searchParams.get('mode');
      const aiFechaInicio = searchParams.get('fecha_inicio');
      const aiFechaFin = searchParams.get('fecha_fin');
      const pAutoPdf = searchParams.get('auto_pdf');
      const pWpp = searchParams.get('wpp');
      const pEmail = searchParams.get('email');

      const currentSignature = `${aiTercero}-${aiCuenta}-${aiMode}-${aiFechaInicio}-${aiFechaFin}-${pAutoPdf}-${pWpp}-${pEmail}`;

      if (lastProcessedParams.current === currentSignature) return;

      // 0. Configurar MODO
      if (aiMode === 'cuenta_first' && reportMode !== 'cuenta_first') {
        setReportMode('cuenta_first');
        toast.info("🔄 Cambiando a vista por cuenta...");
      }

      // 1. Configurar Fechas
      if (aiFechaInicio) setFechas(prev => ({ ...prev, inicio: aiFechaInicio }));
      if (aiFechaFin) setFechas(prev => ({ ...prev, fin: aiFechaFin }));

      // 2. BUSQUEDA DE TERCERO (MODO NORMAL)
      if (aiTercero && aiMode !== 'cuenta_first') {
        const normalize = (str) => {
          if (!str) return "";
          return str.toLowerCase()
            .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
            .replace(/v/g, "b")
            .replace(/z/g, "s")
            .replace(/c/g, "s")
            .replace(/g/g, "j").replace(/h/g, "").replace(/[^a-z0-9\s]/g, "");
        };

        const searchNormalized = normalize(aiTercero);
        const searchWords = searchNormalized.split(" ").filter(w => w.length > 2);

        const scoredTerceros = terceros.map(t => {
          let score = 0;
          const fullName = (t.razon_social || '') + " " + (t.primer_nombre || '') + " " + (t.primer_apellido || '');
          const nombreNorm = normalize(fullName);
          const nitNorm = normalize(t.numero_identificacion || '');

          if (nombreNorm.includes(searchNormalized) || nitNorm.includes(searchNormalized)) score += 100;
          searchWords.forEach(word => {
            if (nombreNorm.includes(word) || nitNorm.includes(word)) score += 20;
          });
          return { ...t, score };
        });

        const bestMatches = scoredTerceros.filter(t => t.score > 0).sort((a, b) => b.score - a.score);
        const found = bestMatches.length > 0 ? bestMatches[0] : null;

        if (found) {
          setSelectedTercero(found.id);
        }
      }

      // 3. BUSQUEDA DE CUENTA (MODO INVERSO)
      if (aiCuenta && aiMode === 'cuenta_first') {
        if (cuentasAll.length === 0) {
          toast.info("⏳ Cargando catálogo de cuentas...");
          return;
        }

        toast.info(`🔍 Buscando cuenta: ${aiCuenta}...`);
        const normalize = (str) => {
          if (!str) return "";
          return str.toLowerCase()
            .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
            .replace(/v/g, "b")
            .replace(/z/g, "s")
            .replace(/c/g, "s")
            .replace(/[^a-z0-9\s]/g, "");
        };

        const searchNormalized = normalize(aiCuenta);
        const scoredCuentas = cuentasAll.map(c => {
          let score = 0;
          const codigoNorm = normalize(c.codigo);
          const nombreNorm = normalize(c.nombre);
          if (codigoNorm === searchNormalized || nombreNorm === searchNormalized) score += 1000;
          if (codigoNorm.includes(searchNormalized) || nombreNorm.includes(searchNormalized)) score += 500;
          if (c.codigo.length > 6) score += 100;
          return { ...c, score };
        });
        const best = scoredCuentas.filter(c => c.score > 0).sort((a, b) => b.score - a.score);
        if (best.length > 0) {
          toast.success(`✅ Cuenta encontrada: ${best[0].codigo}`);
          setSelectedCuentaPrincipal(best[0].id);
          setSelectedTercerosMulti(['all']); // Seleccionar todos por defecto como pide el usuario
          setShouldAutoRun(true); // Usar el estado de auto-run seguro
        } else {
          toast.warn(`⚠️ No encontramos la cuenta "${aiCuenta}"`);
        }
      }

      if (pAutoPdf === 'true') setAutoPdfTrigger(true);
      if (pWpp) setWppNumber(pWpp);
      if (pEmail) setEmailAddress(pEmail);

      lastProcessedParams.current = currentSignature;
    }
  }, [terceros, cuentasAll, searchParams, user, authLoading]);

  // Carga de Cuentas al seleccionar Tercero
  useEffect(() => {
    if (selectedTercero && !authLoading && user) {
      const fetchCuentas = async () => {
        try {
          const res = await apiService.get(`/terceros/${selectedTercero}/cuentas`);
          const cuentas = res.data;
          setCuentasDelTercero(cuentas);

          // --- AUTO-CONFIGURACION CUENTAS Y FECHAS (IA) ---
          // --- AUTO-CONFIGURACION CUENTAS Y FECHAS (IA) ---
          const aiCuenta = searchParams.get('cuenta');
          const aiFechaInicio = searchParams.get('fecha_inicio');
          const aiFechaFin = searchParams.get('fecha_fin');

          // 1. Configurar Fechas si vienen en URL (CRITICO: Hacerlo siempre que existan)
          if (aiFechaInicio && aiFechaFin) {
            setFechas({ inicio: aiFechaInicio, fin: aiFechaFin });
          }

          // Normalizar texto para búsqueda fonética agresiva
          // 1. Lowercase, sin tildes
          // 2. v -> b
          // 3. z, c -> s (Aproximación para seseo/ceceo)
          // 4. Eliminar caracteres especiales
          if (aiCuenta && cuentas.length > 0) {
            const normalize = (str) => {
              if (!str) return "";
              return str.toLowerCase()
                .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
                .replace(/v/g, "b")
                .replace(/z/g, "s")
                .replace(/c/g, "s") // Ojo: esto convierte 'casa' en 'sasa', pero 'caza' en 'sasa' tb. Útil para búsqueda fonética.
                .replace(/[^a-z0-9\s]/g, "");
            };

            const searchNormalized = normalize(aiCuenta);
            const searchWords = searchNormalized.split(" ").filter(w => w.length > 2);

            // LOGICA DE CLASE: Si es un dígito (1-9), marcar todas las que empiecen por ahí
            if (/^[1-9]$/.test(aiCuenta)) {
              const matchedIds = cuentas
                .filter(c => c.codigo.startsWith(aiCuenta))
                .map(c => c.id);

              if (matchedIds.length > 0) {
                setSelectedCuentas(matchedIds);
                if (aiFechaInicio && aiFechaFin) {
                  setTimeout(() => {
                    toast.success(`⚡ Consultando movimientos de Clase ${aiCuenta}...`);
                    document.getElementById('btn-consultar-reporte')?.click();
                    setTimeout(() => window.history.replaceState(null, '', window.location.pathname), 2000);
                  }, 1500);
                }
                return; // Detener aquí si es match de clase
              }
            }

            console.warn("IA Debug - Search:", searchNormalized, "Words:", searchWords);

            // SCORING SYSTEM
            const scoredCuentas = cuentas.map(c => {
              let score = 0;
              const codigoNorm = normalize(c.codigo);
              const nombreNorm = normalize(c.nombre);

              // 1. COINCIDENCIA EXACTA TOTAL (AGRESIVA) -> MÁXIMA PRIORIDAD
              if (codigoNorm === searchNormalized || nombreNorm === searchNormalized) {
                score += 1000;
              }

              // 2. COINCIDENCIA PARCIAL (INCLUYE EL TÉRMINO COMPLETO)
              if (codigoNorm.includes(searchNormalized) || nombreNorm.includes(searchNormalized)) {
                score += 500;
              }

              // 3. COINCIDENCIA POR PALABRAS INDIVIDUALES
              searchWords.forEach(word => {
                if (codigoNorm.includes(word) || nombreNorm.includes(word)) {
                  score += 100;
                }
              });

              // 4. BOOST: Priorizar cuentas de movimiento (nivel detalle)
              // Esto es crucial para que el reporte sea útil
              if (c.es_auxiliar || c.permite_movimiento || c.codigo.length > 6) {
                score += 150;
              } else if (c.codigo.length <= 4) {
                score -= 100; // Penalizar cuentas de grupo/clase si hay auxiliar
              }

              return { ...c, score };
            });

            // Filtrar las que tengan algún match y ordenar por puntaje + longitud (detalle)
            const bestMatches = scoredCuentas.filter(c => c.score > 0).sort((a, b) => {
              if (b.score !== a.score) return b.score - a.score;
              return b.nombre.length - a.nombre.length;
            });

            if (bestMatches.length > 0) {
              // Tomar las mejores (ej: las que tengan el puntaje máximo o cercano)
              const maxScore = bestMatches[0].score;
              // Permitir un pequeño margen o solo las top exactas
              const topCandidates = bestMatches.filter(c => c.score >= maxScore);

              const ids = topCandidates.map(c => c.id);
              setSelectedCuentas(ids);

              // Auto-ejecutar AHORA que tenemos tercero, fechas y cuentas
              if (aiFechaInicio && aiFechaFin) {
                setTimeout(() => {
                  toast.success("⚡ Ejecutando consulta...");
                  document.getElementById('btn-consultar-reporte')?.click();
                  setTimeout(() => window.history.replaceState(null, '', window.location.pathname), 2000); // Limpieza diferida
                }, 1500);
              }
            } else {
              // Si pidió cuenta pero no encontró, advertir al usuario pero EJECUTAR con todas
              setError(`No se encontró la cuenta "${aiCuenta}". Se seleccionaron todas.`);
              toast.warn(`⚠️ Cuenta "${aiCuenta}" no encontrada. Mostrando todas.`);
              setSelectedCuentas(['all']);
              if (aiFechaInicio && aiFechaFin) {
                setTimeout(() => {
                  toast.success("⚡ Ejecutando consulta (Todas las cuentas)...");
                  document.getElementById('btn-consultar-reporte')?.click();
                  setTimeout(() => window.history.replaceState(null, '', window.location.pathname), 2000);
                }, 2000); // Un poco más de tiempo para que el usuario lea el warning
              }
            }
          } else {
            // Comportamiento normal (o lista vacía)
            setSelectedCuentas(['all']);
            // Ejecutar siempre que tengamos fechas
            if (aiFechaInicio && aiFechaFin) {
              setTimeout(() => {
                toast.success("⚡ Ejecutando consulta...");
                document.getElementById('btn-consultar-reporte')?.click();
                setTimeout(() => window.history.replaceState(null, '', window.location.pathname), 2000);
              }, 1500);
            }
          }

        } catch (err) {
          setError("Error cargando cuentas del tercero: " + (err.response?.data?.detail || err.message));
        }
      };
      fetchCuentas();
    } else {
      setCuentasDelTercero([]);
      setSelectedCuentas(['all']);
    }
  }, [selectedTercero, user, authLoading, searchParams]);

  // HANDLE: Enviar por Correo
  const handleSendEmail = async () => {
    if (!reportData || !emailAddress) return;
    toast.info(`📤 Enviando reporte a ${emailAddress}...`);
    try {
      const params = {
        tercero_id: selectedTercero,
        fecha_inicio: fechas.inicio,
        fecha_fin: fechas.fin,
      };
      if (selectedCuentas.length > 0 && !selectedCuentas.includes('all')) {
        params.cuenta_ids = selectedCuentas.join(',');
      }

      await apiService.post('/reports/dispatch-email', {
        report_type: 'tercero_cuenta',
        email_to: emailAddress,
        filtros: params
      });
      toast.success(`✅ Correo enviado a ${emailAddress}`);
    } catch (err) {
      console.error("Error sending email:", err);
      toast.error("❌ Falló el envío del correo.");
    }
  };

  // EFECTO: Automatización (PDF -> WhatsApp -> Email)
  useEffect(() => {
    if (autoPdfTrigger && reportData && !isLoading) {
      // 1. PDF
      handleExportPDF();

      // 2. WhatsApp
      if (wppNumber) {
        const terceroName = terceros.find(t => t.id == selectedTercero)?.razon_social || 'el tercero';
        const message = `Hola, adjunto el Auxiliar de *${terceroName}* del periodo ${fechas.inicio} al ${fechas.fin}.`;
        const wppUrl = `https://wa.me/${wppNumber}?text=${encodeURIComponent(message)}`;
        setTimeout(() => window.open(wppUrl, '_blank'), 1500);
      }

      // 3. Email
      if (emailAddress) {
        handleSendEmail();
      }

      // Reset
      setAutoPdfTrigger(false);
      setWppNumber(null);
      setEmailAddress(null);
    }
  }, [reportData, autoPdfTrigger, isLoading, wppNumber, emailAddress]);

  // EFFECT PARA AUTO-EJECUCION SEGURA
  useEffect(() => {
    if (!shouldAutoRun || isLoading) return;

    const hasDates = fechas.inicio && fechas.fin;
    const isTerceroReady = reportMode === 'tercero_first' && selectedTercero;
    const isCuentaReady = reportMode === 'cuenta_first' && selectedCuentaPrincipal;

    if (shouldAutoRun && hasDates && (isTerceroReady || isCuentaReady)) {
      toast.success("⚡ Consultando movimientos automáticamente...");
      handleGenerateReport();
      setShouldAutoRun(false);
      // Limpieza URL
      setTimeout(() => {
        window.history.replaceState(null, '', window.location.pathname);
      }, 1000);
    }
  }, [shouldAutoRun, reportMode, selectedTercero, selectedCuentaPrincipal, fechas, isLoading]);

  const handleGenerateReport = async () => {
    if (!fechas.inicio || !fechas.fin) {
      setError("Por favor, seleccione un rango de fechas.");
      return;
    }
    setIsLoading(true);
    setError(null);
    setReportData(null);
    setRecalculoStatus({ loading: false, message: '', error: '' });

    const params = {
      fecha_inicio: fechas.inicio,
      fecha_fin: fechas.fin,
    };

    // LOGICA DUAL SEGUN MODO
    if (reportMode === 'tercero_first') {
      if (!selectedTercero) { setError("Seleccione un tercero."); setIsLoading(false); return; }
      params.tercero_id = selectedTercero;
      if (selectedCuentas.length > 0 && !selectedCuentas.includes('all')) {
        params.cuenta_ids = selectedCuentas.join(',');
      }
    } else {
      // MODO INVERSO
      if (!selectedCuentaPrincipal) { setError("Seleccione una cuenta principal."); setIsLoading(false); return; }
      // Para usar el mismo endpoint, necesitamos adaptarnos.
      // El endpoint actual espera 1 tercero.
      // SI el usuario elige "Todos los Terceros", necesitamos un nuevo endpoint o iterar.
      // DECISIÓN: Usaremos el nuevo endpoint 'relacion-saldos' O 'auxiliar-inverso'. 
      // Por ahora, para mantener compatibilidad con la solicitud del usuario ("agregar una pestañita"),
      // vamos a intentar usar un endpoint ad-hoc o asumir que el backend lo soportará.
      // VAMOS A ENVIAR params.cuenta_principal_id y params.tercero_ids

      params.cuenta_id = selectedCuentaPrincipal; // Cambio semántico
      if (selectedTercerosMulti.length > 0 && !selectedTercerosMulti.includes('all')) {
        params.tercero_ids = selectedTercerosMulti.join(',');
      }
      // Nota: Backend debe ser actualizado para esto.
    }

    try {
      let endpoint = '/reports/tercero-cuenta';
      if (reportMode === 'cuenta_first') {
        endpoint = '/reports/auxiliar-inverso';
      }

      const res = await apiService.get(endpoint, { params: params });
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

  const loadPapaParse = () => {
    return new Promise((resolve, reject) => {
      if (window.Papa) {
        resolve(window.Papa);
        return;
      }
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js';
      script.onload = () => resolve(window.Papa);
      script.onerror = () => reject(new Error("Failed to load PapaParse"));
      document.body.appendChild(script);
    });
  };

  const handleExportCSV = async () => {
    if (!reportData) return;

    try {
      await loadPapaParse();
    } catch (e) {
      return alert("Librería CSV no pudo cargarse.");
    }

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
      if (reportMode === 'tercero_first') {
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
        const pdfUrl = `${process.env.NEXT_PUBLIC_API_URL || ''}/api/reports/tercero-cuenta/imprimir?signed_token=${token}`;
        window.open(pdfUrl, '_blank');
      } else {
        // MODO INVERSO
        const params = {
          fecha_inicio: fechas.inicio,
          fecha_fin: fechas.fin,
          cuenta_id: selectedCuentaPrincipal
        };
        if (selectedTercerosMulti.length > 0 && !selectedTercerosMulti.includes('all')) {
          params.tercero_ids = selectedTercerosMulti.join(',');
        }

        const res = await apiService.get('/reports/auxiliar-inverso/get-signed-url', { params });
        const token = res.data.signed_url_token;
        const pdfUrl = `${process.env.NEXT_PUBLIC_API_URL || ''}/api/reports/auxiliar-inverso/imprimir?signed_token=${token}`;
        window.open(pdfUrl, '_blank');
      }

    } catch (err) {
      // Fix React Error by ensuring string
      const msg = err.response?.data?.detail || err.message || 'Error generando PDF.';
      setError(typeof msg === 'object' ? JSON.stringify(msg) : msg);
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
    <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
      <div className="max-w-7xl mx-auto">

        {/* ENCABEZADO */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
          <div>
            <div className="flex items-center gap-3 mt-3">
              <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                <FaUserTag className="text-2xl" />
              </div>
              <div>
                <div className="flex items-center gap-4">
                  <h1 className="text-3xl font-bold text-gray-800">Auxiliar por Tercero</h1>
                  <button
                    onClick={() => window.open('/manual/capitulo_35_tercero_cuenta.html', '_blank')}
                    className="flex items-center gap-2 px-2 py-1 bg-white border border-indigo-200 text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors font-medium shadow-sm"
                    title="Ver Manual de Usuario"
                  >
                    <span className="text-lg">📖</span> <span className="font-bold text-sm hidden md:inline">Manual</span>
                  </button>
                </div>

                <p className="text-gray-500 text-sm">Auditoría detallada de movimientos por cuenta para un tercero.</p>
                {/* STATUS INDICATOR */}
                {(wppNumber || autoPdfTrigger || emailAddress) && (
                  <div className="mt-2 text-sm font-bold text-green-600 flex items-center gap-2 animate-bounce">
                    <span>⚡ Procesando comando: Generando PDF {wppNumber ? 'para WhatsApp...' : emailAddress ? 'para Email...' : '...'}</span>
                  </div>
                )}
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

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 items-start">

            {/* TOGGLE DE MODO */}
            <div className="md:col-span-4 flex justify-center mb-4 border-b border-gray-100 pb-4">
              <div className="bg-gray-100 p-1 rounded-lg flex gap-1">
                <button
                  onClick={() => setReportMode('tercero_first')}
                  className={`px-4 py-2 rounded-md text-sm font-bold transition-all ${reportMode === 'tercero_first' ? 'bg-white text-indigo-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                >
                  Por Tercero
                </button>
                <button
                  onClick={() => setReportMode('cuenta_first')}
                  className={`px-4 py-2 rounded-md text-sm font-bold transition-all ${reportMode === 'cuenta_first' ? 'bg-white text-indigo-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                >
                  Por Cuenta (Inverso)
                </button>
              </div>
            </div>

            {/* MODO NORMAL: Tercero -> Cuentas */}
            {reportMode === 'tercero_first' && (
              <>
                <div className="md:col-span-2">
                  <label className={labelClass}>Tercero</label>
                  <div className="relative">
                    <select value={selectedTercero} onChange={(e) => setSelectedTercero(e.target.value)} className={selectClass}>
                      <option value="">-- Seleccione Tercero --</option>
                      {terceros.map(t => <option key={t.id} value={t.id}>{t.razon_social}</option>)}
                    </select>
                    <FaUserTag className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                  </div>
                </div>
              </>
            )}

            {/* MODO INVERSO: Cuenta -> Terceros */}
            {reportMode === 'cuenta_first' && (
              <>
                <div className="md:col-span-2">
                  <label className={labelClass}>Cuenta Principal</label>
                  <div className="relative">
                    {/* Idealmente un Autocomplete, por ahora Select simple */}
                    <select value={selectedCuentaPrincipal} onChange={(e) => setSelectedCuentaPrincipal(e.target.value)} className={selectClass}>
                      <option value="">-- Seleccione Cuenta --</option>
                      {cuentasAll.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
                    </select>
                    <FaBook className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                  </div>
                </div>
              </>
            )}

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

            {/* Cuentas MultiSelect (MODO NORMAL) */}
            {reportMode === 'tercero_first' && (
              <div className="md:col-span-4">
                <label className={labelClass}>Filtrar Cuentas (Opcional)</label>
                <CheckboxMultiSelect
                  options={cuentasDelTercero}
                  selected={selectedCuentas}
                  onChange={setSelectedCuentas}
                  placeholder="Seleccionar Cuentas..."
                />
                <p className="text-xs text-gray-400 mt-1">Seleccione una o varias cuentas para filtrar los resultados.</p>
              </div>
            )}

            {/* Terceros MultiSelect (MODO INVERSO) */}
            {reportMode === 'cuenta_first' && (
              <div className="md:col-span-4">
                <label className={labelClass}>Filtrar Terceros (Opcional)</label>
                <CheckboxMultiSelect
                  options={terceros.map(t => ({ id: t.id, codigo: t.numero_identificacion, label: t.razon_social }))}
                  selected={selectedTercerosMulti}
                  onChange={setSelectedTercerosMulti}
                  placeholder="Seleccionar Terceros..."
                />
                <p className="text-xs text-gray-400 mt-1">Busque por nombre o NIT. Seleccione '-- TODOS --' para el reporte completo.</p>
              </div>
            )}
          </div>

          <div className="flex justify-end mt-6 pt-4 border-t border-gray-100">
            <button
              onClick={handleGenerateReport}
              disabled={isLoading}
              className={`
                            px-8 py-2 rounded-lg shadow-md font-bold text-white transition-all transform hover:-translate-y-0.5 flex items-center gap-2
                            ${isLoading ? 'bg-gray-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'}
                        `}
              id="btn-consultar-reporte"
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
                    // LÓGICA DE AGRUPACIÓN DINÁMICA
                    let isNewGroup = false;
                    let groupHeader = null;
                    let groupSaldoProps = { label: '', value: 0 };

                    if (reportMode === 'tercero_first') {
                      // Agrupar por Cuenta
                      isNewGroup = index === 0 || mov.cuenta_id !== reportData.movimientos[index - 1].cuenta_id;
                      if (isNewGroup) {
                        groupHeader = <span>Cuenta: <span className="text-indigo-600">{mov.cuenta_codigo} - {mov.cuenta_nombre}</span></span>;
                        groupSaldoProps = {
                          label: 'Saldo Inicial Cuenta:',
                          value: reportData.saldos_iniciales_por_cuenta ? reportData.saldos_iniciales_por_cuenta[String(mov.cuenta_id)] : 0
                        };
                      }
                    } else {
                      // Agrupar por Tercero (Inverso)
                      // Nota: El backend de auxiliar inverso debe retornar 'tercero_id' y 'tercero_nombre' en cada movimiento
                      isNewGroup = index === 0 || mov.tercero_id !== reportData.movimientos[index - 1].tercero_id;
                      if (isNewGroup) {
                        groupHeader = <span>Tercero: <span className="text-indigo-600">{mov.tercero_nombre}</span></span>;
                        // El backend retorna 'saldos_iniciales_por_tercero' en modo inverso
                        groupSaldoProps = {
                          label: 'Saldo Inicial Tercero:',
                          value: reportData.saldos_iniciales_por_tercero ? reportData.saldos_iniciales_por_tercero[String(mov.tercero_id)] : 0
                        };
                      }
                    }

                    return (
                      <React.Fragment key={`group-${index}`}>
                        {isNewGroup && (
                          <tr className="bg-gray-100 border-t border-gray-200">
                            <td colSpan={4} className="px-4 py-2 text-xs font-bold text-gray-600 uppercase">
                              {groupHeader}
                            </td>
                            <td colSpan={2} className="px-4 py-2 text-right text-xs font-bold text-gray-500">{groupSaldoProps.label}</td>
                            <td className="px-4 py-2 text-right text-xs font-mono font-bold text-gray-700 bg-gray-200">
                              {formatCurrency(groupSaldoProps.value)}
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
  );
}

export default function ReporteTerceroCuentaPage() {
  const { loading: authLoading } = useAuth();

  if (authLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
        <FaUserTag className="text-indigo-300 text-6xl mb-4 animate-pulse" />
        <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando Auditoría de Terceros...</p>
      </div>
    );
  }

  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
        <FaUserTag className="text-indigo-300 text-6xl mb-4 animate-pulse" />
        <p className="text-indigo-600 font-semibold text-lg animate-pulse">Preparando Auditoría...</p>
      </div>
    }>
      <ReporteTerceroCuentaContent />
    </Suspense>
  );
}