'use client';

import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import {
  FaFileAlt,
  FaSave,
  FaPlus,
  FaCalendarAlt,
  FaUserTag,
  FaBuilding,
  FaHashtag,
  FaMoneyBillWave,
  FaTrash,
  FaPrint,
  FaBook,
  FaCheckCircle,
  FaExclamationTriangle,
  FaList
} from 'react-icons/fa';

// Importaciones de dependencias
import { useAuth } from '../../context/AuthContext';
import { apiService } from '../../../lib/apiService';
import { FuncionEspecial } from '../../../lib/constants';
import ModalCrearTercero from '../../../components/terceros/ModalCrearTercero';

// Estilos reusables (Manual v2.0)
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none text-gray-900";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white text-gray-900";
const tableInputClass = "w-full px-2 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-indigo-500 outline-none text-gray-900";

export default function NuevoDocumentoPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();

  // Estados del Formulario Principal
  const [fecha, setFecha] = useState(new Date());
  const [tipoDocumentoId, setTipoDocumentoId] = useState('');
  const [beneficiarioId, setBeneficiarioId] = useState('');
  const [centroCostoId, setCentroCostoId] = useState('');
  const [numero, setNumero] = useState('');
  const [numeroEditable, setNumeroEditable] = useState(false);
  const [movimientos, setMovimientos] = useState([
    { rowId: Date.now(), cuentaId: '', concepto: '', debito: '', credito: '', cuentaInput: '' },
    { rowId: Date.now() + 1, cuentaId: '', concepto: '', debito: '', credito: '', cuentaInput: '' },
  ]);

  // Estados de UI y Notificaciones
  const [pageIsLoading, setPageIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [mensaje, setMensaje] = useState('');
  const [documentoRecienCreadoId, setDocumentoRecienCreadoId] = useState(null);

  // Estados para Cartera y Proveedores
  // Estados para Cartera y Proveedores
  const [fechaVencimiento, setFechaVencimiento] = useState(null);
  const [tipoDocSeleccionado, setTipoDocSeleccionado] = useState(null);
  const [facturasPendientes, setFacturasPendientes] = useState([]);
  const [aplicaciones, setAplicaciones] = useState({});
  const [isCarteraLoading, setIsCarteraLoading] = useState(false);
  const [valorAAbonar, setValorAAbonar] = useState('');
  const [cuentasConfiguradas, setCuentasConfiguradas] = useState({ debitoId: null, creditoId: null });

  // --- NUEVO: ESTADO MODAL TERCERO ---
  const [showTerceroModal, setShowTerceroModal] = useState(false);

  // Referencias para navegación por teclado
  const formRefs = useRef({});
  const order = useRef([]);

  // --- ARQUITECTURA DE DATOS MAESTROS ---
  const [maestros, setMaestros] = useState({
    cuentas: [],
    terceros: [],
    centrosCosto: [],
    tiposDocumento: [],
    plantillas: [],
    conceptos: [],
  });

  const addRef = (name, el) => {
    if (el) {
      formRefs.current[name] = el;
      if (!order.current.includes(name)) {
        order.current.push(name);
      }
    }
  };

  const totales = useMemo(() => {
    return movimientos.reduce((acc, mov) => ({
      debito: acc.debito + (parseFloat(mov.debito) || 0),
      credito: acc.credito + (parseFloat(mov.credito) || 0),
    }), { debito: 0, credito: 0 });
  }, [movimientos]);

  const estaBalanceado = useMemo(() => {
    const diff = Math.abs(totales.debito - totales.credito);
    return diff < 0.01 && totales.credito > 0;
  }, [totales]);

  const totalAplicado = useMemo(() => {
    return Object.values(aplicaciones).reduce((sum, val) => sum + (parseFloat(val) || 0), 0);
  }, [aplicaciones]);

  const totalAbono = useMemo(() => {
    return parseFloat(valorAAbonar) || 0;
  }, [valorAAbonar]);

  const handleMovimientoChange = (index, field, value) => {
    const newMovimientos = [...movimientos];
    if (field === 'debito' && value !== '') {
      newMovimientos[index]['credito'] = '';
    } else if (field === 'credito' && value !== '') {
      newMovimientos[index]['debito'] = '';
    }
    newMovimientos[index][field] = value;
    setMovimientos(newMovimientos);
  };

  const handleCuentaBlur = (index, value) => {
    if (!value) {
      handleMovimientoChange(index, 'cuentaId', '');
      handleMovimientoChange(index, 'cuentaInput', '');
      return;
    }
    const cuentaEncontrada = maestros.cuentas.find(c => c.codigo === value || c.nombre.toLowerCase() === value.toLowerCase());
    if (cuentaEncontrada) {
      if (!cuentaEncontrada.permite_movimiento) {
        setError(`La cuenta ${cuentaEncontrada.codigo} - ${cuentaEncontrada.nombre} no permite movimientos.`);
        handleMovimientoChange(index, 'cuentaId', '');
        handleMovimientoChange(index, 'cuentaInput', '');
      } else {
        handleMovimientoChange(index, 'cuentaId', cuentaEncontrada.id);
        handleMovimientoChange(index, 'cuentaInput', `${cuentaEncontrada.codigo} - ${cuentaEncontrada.nombre}`);
        setError('');
      }
    } else {
      setError('Cuenta no encontrada o no válida.');
      handleMovimientoChange(index, 'cuentaId', '');
    }
  };

  const handleTipoDocumentoChange = async (tipoId) => {
    setError('');
    setMensaje('');
    setDocumentoRecienCreadoId(null);
    setTipoDocumentoId(tipoId);
    setNumero('');
    setNumeroEditable(false);

    setFechaVencimiento(null);
    setFacturasPendientes([]);
    setAplicaciones({});
    setValorAAbonar('');
    setTipoDocSeleccionado(null);
    setCuentasConfiguradas({ debitoId: null, creditoId: null });

    if (!tipoId) return;

    const tipoSel = maestros.tiposDocumento.find(t => t.id === parseInt(tipoId));
    setTipoDocSeleccionado(tipoSel);

    if (tipoSel?.funcion_especial === FuncionEspecial.RC_CLIENTE) {
      setCuentasConfiguradas({
        debitoId: tipoSel.cuenta_debito_cxc_id,
        creditoId: tipoSel.cuenta_credito_cxc_id,
      });
    } else if (tipoSel?.funcion_especial === FuncionEspecial.PAGO_PROVEEDOR) {
      setCuentasConfiguradas({
        debitoId: tipoSel.cuenta_debito_cxp_id,
        creditoId: tipoSel.cuenta_credito_cxp_id,
      });
    }

    try {
      const res = await apiService.get(`/tipos-documento/${tipoId}/siguiente-numero`);
      setNumeroEditable(res.data.es_manual);
      if (!res.data.es_manual) {
        setNumero(String(res.data.siguiente_numero).padStart(7, '0'));
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al obtener el siguiente número.');
    }
  };

  const handleBeneficiarioChange = (beneficiarioId) => {
    setBeneficiarioId(beneficiarioId);
    setFacturasPendientes([]);
    setAplicaciones({});
    setValorAAbonar('');
  };

  const fetchFacturasPendientes = useCallback(async (terceroId) => {
    if (!terceroId || !user?.empresaId || !tipoDocSeleccionado?.funcion_especial) return;

    const esCartera = tipoDocSeleccionado.funcion_especial === FuncionEspecial.RC_CLIENTE;
    const esProveedores = tipoDocSeleccionado.funcion_especial === FuncionEspecial.PAGO_PROVEEDOR;

    if (!esCartera && !esProveedores) {
      setFacturasPendientes([]);
      return;
    }

    const endpoint = esCartera
      ? `/cartera/facturas-pendientes/${terceroId}`
      : `/proveedores/facturas-pendientes/${terceroId}`;

    setIsCarteraLoading(true);
    setError('');
    try {
      const res = await apiService.get(endpoint);
      setFacturasPendientes(res.data);
    } catch (err) {
      console.error("ERROR en fetchFacturasPendientes:", err);
      setError(err.response?.data?.detail || 'Error al cargar las facturas pendientes.');
      setFacturasPendientes([]);
    } finally {
      setIsCarteraLoading(false);
    }
  }, [user, tipoDocSeleccionado]);

  const handleAplicacionChange = (facturaId, monto) => {
    const numericMonto = parseFloat(monto);
    if (isNaN(numericMonto) || numericMonto <= 0) {
      setAplicaciones(prev => {
        const newApps = { ...prev };
        delete newApps[facturaId];
        return newApps;
      });
    } else {
      setAplicaciones(prev => ({
        ...prev,
        [facturaId]: numericMonto.toFixed(2)
      }));
    }
  };

  const generarMovimientosDesdeAplicaciones = (aplicacionesActualizadas) => {
    if (!cuentasConfiguradas.creditoId || !cuentasConfiguradas.debitoId) {
      setError("Las cuentas de débito/crédito para la transacción no están configuradas en el tipo de documento.");
      return;
    }

    const cuentaCredito = maestros.cuentas.find(c => c.id === cuentasConfiguradas.creditoId);
    const cuentaDebito = maestros.cuentas.find(c => c.id === cuentasConfiguradas.debitoId);

    if (!cuentaCredito || !cuentaDebito) {
      setError("No se pudieron encontrar las cuentas configuradas en el plan de cuentas.");
      return;
    }

    const facturasAbonadas = facturasPendientes.filter(f => aplicacionesActualizadas[f.id] && parseFloat(aplicacionesActualizadas[f.id]) > 0);
    if (facturasAbonadas.length === 0) {
      setMovimientos([
        { rowId: Date.now(), cuentaId: '', concepto: '', debito: '', credito: '', cuentaInput: '' },
        { rowId: Date.now() + 1, cuentaId: '', concepto: '', debito: '', credito: '', cuentaInput: '' },
      ]);
      return;
    }

    const esPagoProveedores = tipoDocSeleccionado?.funcion_especial === FuncionEspecial.PAGO_PROVEEDOR;
    const prefijoConcepto = esPagoProveedores ? "Abona FC-" : "Abona FV-";
    const conceptoBase = prefijoConcepto + facturasAbonadas.map(f => f.numero).join(`, ${prefijoConcepto}`);
    let conceptoFinal = conceptoBase.substring(0, 100);
    const totalAplicadoNum = Object.values(aplicacionesActualizadas).reduce((sum, val) => sum + (parseFloat(val) || 0), 0);

    const nuevosMovimientos = [
      {
        rowId: Date.now(),
        cuentaId: cuentaCredito.id,
        cuentaInput: `${cuentaCredito.codigo} - ${cuentaCredito.nombre}`,
        concepto: conceptoFinal,
        debito: '',
        credito: totalAplicadoNum.toFixed(2)
      },
      {
        rowId: Date.now() + 1,
        cuentaId: cuentaDebito.id,
        cuentaInput: `${cuentaDebito.codigo} - ${cuentaDebito.nombre}`,
        concepto: conceptoFinal,
        debito: totalAplicadoNum.toFixed(2),
        credito: ''
      }
    ];
    setMovimientos(nuevosMovimientos);
  };

  const handlePlantillaChange = async (plantillaId) => {
    if (!plantillaId) {
      setBeneficiarioId('');
      setCentroCostoId('');
      setTipoDocumentoId('');
      setMovimientos([
        { rowId: Date.now(), cuentaId: '', concepto: '', debito: '', credito: '', cuentaInput: '' },
        { rowId: Date.now() + 1, cuentaId: '', concepto: '', debito: '', credito: '', cuentaInput: '' },
      ]);
      setError('');
      setMensaje('');
      setFechaVencimiento(null);
      return;
    }

    setError('');
    setMensaje('Cargando plantilla...');
    try {
      const res = await apiService.get(`/plantillas/${plantillaId}`);
      const plantilla = res.data;

      if (plantilla.tipo_documento_id_sugerido) {
        await handleTipoDocumentoChange(String(plantilla.tipo_documento_id_sugerido));
      }

      setBeneficiarioId(String(plantilla.beneficiario_id_sugerido || ''));
      setCentroCostoId(String(plantilla.centro_costo_id_sugerido || ''));

      const nuevosMovimientos = plantilla.detalles.map((d, i) => {
        const cuentaCompleta = maestros.cuentas.find(c => c.id === d.cuenta_id);
        if (!cuentaCompleta || !cuentaCompleta.permite_movimiento) {
          console.warn(`ADVERTENCIA: La cuenta de la plantilla no es válida o no permite movimientos. Se omitirá.`);
          return null;
        }
        return {
          rowId: Date.now() + i,
          cuentaId: d.cuenta_id,
          concepto: d.concepto || '',
          debito: d.debito ? parseFloat(d.debito).toFixed(2) : '',
          credito: d.credito ? parseFloat(d.credito).toFixed(2) : '',
          cuentaInput: `${cuentaCompleta.codigo} - ${cuentaCompleta.nombre}`
        };
      }).filter(Boolean);

      if (nuevosMovimientos.length > 0) {
        setMovimientos(nuevosMovimientos);
      } else if (plantilla.detalles.length > 0) {
        setError("No se pudieron cargar movimientos de la plantilla porque las cuentas no son válidas.");
      }

      setMensaje(`Plantilla "${plantilla.nombre_plantilla}" cargada exitosamente.`);

    } catch (err) {
      setError(err.response?.data?.detail || 'Error al cargar la plantilla.');
      setMensaje('');
    }
  };

  const handleAddNewConcept = async (movimientoIndex) => {
    const conceptoValue = movimientos[movimientoIndex].concepto.trim();
    if (!conceptoValue) {
      setError("El campo de concepto está vacío.");
      return;
    }

    if (maestros.conceptos.some(c => c.descripcion.toLowerCase() === conceptoValue.toLowerCase())) {
      setError("Este concepto ya existe en la librería.");
      return;
    }

    setMensaje("Guardando nuevo concepto...");
    setError('');
    try {
      const payload = { descripcion: conceptoValue };
      const response = await apiService.post('/conceptos-favoritos/', payload);
      const nuevoConcepto = response.data;

      setMaestros(prev => ({ ...prev, conceptos: [...prev.conceptos, nuevoConcepto].sort((a, b) => a.descripcion.localeCompare(b.descripcion)) }));
      setMensaje(`Concepto "${nuevoConcepto.descripcion}" añadido a la librería.`);

    } catch (err) {
      setError(err.response?.data?.detail?.[0]?.msg || err.response?.data?.detail || 'Error al guardar el nuevo concepto.');
      setMensaje('');
    }
  };

  const handleSaveAsTemplate = async () => {
    const nombrePlantilla = window.prompt("Por favor, ingresa un nombre para la nueva plantilla:");
    if (!nombrePlantilla || nombrePlantilla.trim() === '') return;

    if (maestros.plantillas.some(p => p.nombre_plantilla.toLowerCase() === nombrePlantilla.trim().toLowerCase())) {
      setError("Ya existe una plantilla con ese nombre.");
      return;
    }

    setIsSubmitting(true);
    setMensaje("Guardando como plantilla...");
    setError('');

    try {
      const payload = {
        nombre_plantilla: nombrePlantilla.trim(),
        empresa_id: user.empresaId,
        tipo_documento_id_sugerido: tipoDocumentoId ? parseInt(tipoDocumentoId, 10) : null,
        beneficiario_id_sugerido: beneficiarioId ? parseInt(beneficiarioId, 10) : null,
        centro_costo_id_sugerido: centroCostoId ? parseInt(centroCostoId, 10) : null,
        detalles: movimientos
          .filter(m => m.cuentaId)
          .map(m => ({
            cuenta_id: parseInt(m.cuentaId, 10),
            concepto: m.concepto || '',
            debito: parseFloat(m.debito) || 0,
            credito: parseFloat(m.credito) || 0,
          }))
      };

      const response = await apiService.post('/plantillas/', payload);
      const nuevaPlantilla = response.data;
      setMaestros(prev => ({ ...prev, plantillas: [...prev.plantillas, nuevaPlantilla].sort((a, b) => a.nombre_plantilla.localeCompare(b.nombre_plantilla)) }));
      setMensaje(`Plantilla "${nuevaPlantilla.nombre_plantilla}" guardada exitosamente.`);

    } catch (err) {
      setError(err.response?.data?.detail || 'Error al guardar la plantilla.');
      setMensaje('');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleImprimirDocumento = async (docId) => {
    setMensaje("Generando URL de impresión segura...");
    setError('');
    setIsSubmitting(true);
    try {
      const response = await apiService.post(`/documentos/${docId}/solicitar-impresion`);
      const { signed_url } = response.data;

      if (signed_url) {
        window.open(signed_url, '_blank');
        setMensaje("Documento listo para imprimir.");
      } else {
        setError("No se recibió una URL de impresión válida.");
      }

    } catch (err) {
      setError(err.response?.data?.detail || "Error al solicitar la impresión del documento.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // --- NUEVO: HANDLER TERCERO CREADO ---
  const handleTerceroCreado = (nuevoTercero) => {
    // 1. Agregarlo a la lista de maestros
    setMaestros(prev => ({
      ...prev,
      terceros: [...prev.terceros, nuevoTercero].sort((a, b) => a.razon_social.localeCompare(b.razon_social))
    }));
    // 2. Seleccionarlo automáticamente
    setBeneficiarioId(String(nuevoTercero.id));
    // 3. Mostrar mensaje éxito
    setMensaje(`Tercero "${nuevoTercero.razon_social}" creado y seleccionado.`);
    // 4. Reset para limpiar cualquier data de facturas anterior (que no tendría sentido porque es nuevo)
    setFacturasPendientes([]);
    setAplicaciones({});
    setValorAAbonar('');
  };

  const handleSubmit = async () => {
    if (!user || !user.empresaId) {
      setError("No se pudo identificar la empresa del usuario. Por favor, recargue la página.");
      return;
    }
    if (!tipoDocumentoId || !numero || !beneficiarioId) {
      setError('Debe completar los campos de la cabecera (Tipo, Número, Beneficiario).');
      return;
    }
    const numeroParsed = parseInt(numero, 10);
    if (isNaN(numeroParsed) || numeroParsed <= 0) {
      setError('El número del documento es inválido. Debe ser un número mayor que cero.');
      return;
    }
    if (movimientos.filter(m => m.cuentaId).length === 0) {
      setError("Debe agregar al menos un movimiento contable.");
      return;
    }
    if (!estaBalanceado) {
      setError('El documento no está balanceado. Las sumas de débito y crédito deben ser iguales.');
      return;
    }

    const esPagoCartera = tipoDocSeleccionado?.funcion_especial === FuncionEspecial.RC_CLIENTE;
    const esPagoProveedores = tipoDocSeleccionado?.funcion_especial === FuncionEspecial.PAGO_PROVEEDOR;
    if (esPagoCartera || esPagoProveedores) {
      const diffAbonoAplicado = Math.abs(totalAbono - totalAplicado);
      if (diffAbonoAplicado > 0.01) {
        setError(`El valor a abonar (${totalAbono.toFixed(2)}) no coincide con el total aplicado a facturas (${totalAplicado.toFixed(2)}). Diferencia: ${diffAbonoAplicado.toFixed(2)}`);
        return;
      }
    }

    for (const mov of movimientos) {
      if (mov.cuentaId) {
        const cuenta = maestros.cuentas.find(c => c.id === mov.cuentaId);
        if (!cuenta || !cuenta.permite_movimiento) {
          setError(`La cuenta ${cuenta?.codigo || mov.cuentaInput} no permite movimientos o no es válida.`);
          return;
        }
      }
    }

    setIsSubmitting(true);
    setError('');
    setMensaje('');
    setDocumentoRecienCreadoId(null);

    const movimientosParaPayload = movimientos
      .filter(m => m.cuentaId)
      .map(m => ({
        cuenta_id: parseInt(m.cuentaId, 10),
        concepto: m.concepto || '',
        debito: parseFloat(m.debito) || 0,
        credito: parseFloat(m.credito) || 0,
      }));

    try {
      const aplicacionesPayload = Object.entries(aplicaciones)
        .filter(([_, value]) => parseFloat(value) > 0)
        .map(([key, value]) => ({
          documento_factura_id: parseInt(key, 10),
          valor_aplicado: parseFloat(value)
        }));

      const esFacturaCliente = tipoDocSeleccionado?.funcion_especial === FuncionEspecial.CARTERA_CLIENTE;
      const esFacturaProveedor = tipoDocSeleccionado?.funcion_especial === FuncionEspecial.CXP_PROVEEDOR;

      const payload = {
        fecha: fecha.toISOString().split('T')[0],
        tipo_documento_id: parseInt(tipoDocumentoId, 10),
        numero: numeroParsed,
        beneficiario_id: beneficiarioId ? parseInt(beneficiarioId, 10) : null,
        centro_costo_id: centroCostoId ? parseInt(centroCostoId, 10) : null,
        fecha_vencimiento: (esFacturaCliente || esFacturaProveedor) && fechaVencimiento ? fechaVencimiento.toISOString().split('T')[0] : null,
        empresa_id: user.empresaId,
        movimientos: movimientosParaPayload,
        aplicaciones: aplicacionesPayload.length > 0 ? aplicacionesPayload : null
      };

      const response = await apiService.post('/documentos/', payload);
      setMensaje(`¡Éxito! Documento ${response.data.numero} creado.`);
      setDocumentoRecienCreadoId(response.data.id);

      // --- CAMBIOS DE PERSISTENCIA (Request Usuario) ---
      // setTipoDocumentoId(''); // MANTENER TIPO DE DOCUMENTO
      // setBeneficiarioId(''); // MANTENER TERCERO
      // setCentroCostoId(''); // MANTENER CENTRO DE COSTO

      // Actualizar consecutivo (Número) automáticamente si se mantiene el tipo
      if (tipoDocumentoId) {
        try {
          // Pequeño delay para asegurar que el backend haya procesado el anterior (aunque ya respondió ok)
          const resNum = await apiService.get(`/tipos-documento/${tipoDocumentoId}/siguiente-numero`);
          if (!resNum.data.es_manual) {
            setNumero(String(resNum.data.siguiente_numero).padStart(7, '0'));
          } else {
            setNumero(''); // Si es manual, limpiar para que ingrese el nuevo
          }
        } catch (e) {
          console.error("Error al actualizar consecutivo:", e);
          setNumero('');
        }
      } else {
        setNumero('');
      }

      setMovimientos([
        { rowId: Date.now(), cuentaId: '', concepto: '', debito: '', credito: '', cuentaInput: '' },
        { rowId: Date.now() + 1, cuentaId: '', concepto: '', debito: '', credito: '', cuentaInput: '' },
      ]);
      // setFechaVencimiento(null); // MANTENER FECHA VENCIMIENTO SI APLICA

      // Limpiar estados dependientes que deberían regenerarse
      setFacturasPendientes([]);
      setAplicaciones({});
      setValorAAbonar('');

      // setNumeroEditable(false); // Mantener estado de editabilidad
      // setTipoDocSeleccionado(null); // NO LIMPIAR SELECCIÓN
      // setCuentasConfiguradas({ debitoId: null, creditoId: null }); // NO LIMPIAR CONFIG

    } catch (err) {
      const errorDetail = err.response?.data?.detail;
      if (typeof errorDetail === 'string') {
        setError(errorDetail);
      } else if (Array.isArray(errorDetail)) {
        const firstError = errorDetail[0];
        const errorPath = firstError.loc?.slice(1)?.join(' -> ');
        setError(`Error de validación en '${errorPath || "campos"}': ${firstError.msg}`);
      } else {
        setError('Ocurrió un error desconocido al guardar.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const agregarFila = () => {
    setMovimientos(prevMovimientos => {
      const newMovimientos = [...prevMovimientos, { rowId: Date.now(), cuentaId: '', concepto: '', debito: '', credito: '', cuentaInput: '' }];
      setTimeout(() => {
        const newCuentaInputName = `mov-${newMovimientos.length - 1}-cuenta`;
        if (formRefs.current[newCuentaInputName]) {
          formRefs.current[newCuentaInputName].focus();
        }
      }, 100);
      return newMovimientos;
    });
  };

  const eliminarFila = (index) => {
    if (movimientos.length > 1) {
      setMovimientos(movimientos.filter((_, i) => i !== index));
    }
  };

  const handleKeyDown = (e, currentRefName) => {
    const targetName = e.target.name || currentRefName;

    const esDebitoCreditoField = targetName && (targetName.startsWith('mov-') && (targetName.endsWith('-debito') || targetName.endsWith('-credito')));
    if (esDebitoCreditoField) {
      const parts = targetName.split('-');
      const index = parseInt(parts[1], 10);
      const fieldType = parts[2];
      let currentValue = parseFloat(movimientos[index][fieldType]) || 0;

      if (e.key === '+') {
        e.preventDefault();
        handleMovimientoChange(index, fieldType, (currentValue * 1000).toFixed(2));
      } else if (e.key === '-') {
        e.preventDefault();
        handleMovimientoChange(index, fieldType, (currentValue * 100).toFixed(2));
      }
    }

    const esPago = tipoDocSeleccionado?.funcion_especial === FuncionEspecial.RC_CLIENTE || tipoDocSeleccionado?.funcion_especial === FuncionEspecial.PAGO_PROVEEDOR;
    if (esPago) {
      if (currentRefName === 'valorAAbonar' && e.key === 'Enter') {
        e.preventDefault();
        if (facturasPendientes.length > 0) {
          formRefs.current[`aplicacion-${facturasPendientes[0].id}`]?.focus();
        } else {
          formRefs.current[`mov-0-cuenta`]?.focus();
        }
        return;
      }

      if (currentRefName.startsWith('aplicacion-') && e.key === 'Tab') {
        e.preventDefault();
        const facturaId = parseInt(currentRefName.split('-')[1], 10);
        const currentIndex = facturasPendientes.findIndex(f => f.id === facturaId);

        const valorAbonarNum = parseFloat(valorAAbonar) || 0;
        const nuevasAplicaciones = { ...aplicaciones };
        const totalAplicadoSinActual = Object.entries(nuevasAplicaciones)
          .reduce((sum, [key, val]) => (parseInt(key) !== facturaId ? sum + (parseFloat(val) || 0) : sum), 0);

        let saldoDisponible = valorAbonarNum - totalAplicadoSinActual;
        const facturaActual = facturasPendientes[currentIndex];
        const montoAAplicar = Math.max(0, Math.min(saldoDisponible, facturaActual.saldo_pendiente));

        if (montoAAplicar > 0) {
          nuevasAplicaciones[facturaId] = montoAAplicar.toFixed(2);
        } else {
          delete nuevasAplicaciones[facturaId];
        }

        setAplicaciones(nuevasAplicaciones);

        if (currentIndex + 1 < facturasPendientes.length) {
          const proximaFacturaId = facturasPendientes[currentIndex + 1].id;
          formRefs.current[`aplicacion-${proximaFacturaId}`]?.focus();
        } else {
          generarMovimientosDesdeAplicaciones(nuevasAplicaciones);
          setTimeout(() => {
            formRefs.current[`mov-0-cuenta`]?.focus();
          }, 100);
        }
        return;
      }
    }

    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      const currentIndex = order.current.indexOf(currentRefName);
      if (['guardar-doc', 'guardar-plantilla', 'imprimir-doc'].includes(currentRefName)) {
        const buttonElement = formRefs.current[currentRefName];
        if (buttonElement && !buttonElement.disabled) {
          buttonElement.click();
        }
        return;
      }

      let nextElementToFocus = null;
      for (let i = currentIndex + 1; i < order.current.length; i++) {
        const candidateRefName = order.current[i];
        const candidateElement = formRefs.current[candidateRefName];

        if (candidateElement && typeof candidateElement.closest === 'function') {
          if (!candidateElement.disabled && candidateElement.offsetParent !== null && !candidateElement.closest('tbody button')) {
            nextElementToFocus = candidateElement;
            break;
          }
        }
      }

      if (nextElementToFocus) {
        nextElementToFocus.focus();
      } else {
        formRefs.current['guardar-doc']?.focus();
      }
    }

    if (e.key === 'Tab' && !e.shiftKey) {
      const lastMovimientoIndex = movimientos.length - 1;
      const currentTargetName = e.target.name || currentRefName;
      const esUltimaFilaDebito = currentTargetName === `mov-${lastMovimientoIndex}-debito`;
      const esUltimaFilaCredito = currentTargetName === `mov-${lastMovimientoIndex}-credito`;

      if ((esUltimaFilaDebito || esUltimaFilaCredito) && movimientos.length > 1) {
        const totalDebitoOtrasFilas = totales.debito - (parseFloat(movimientos[lastMovimientoIndex].debito) || 0);
        const totalCreditoOtrasFilas = totales.credito - (parseFloat(movimientos[lastMovimientoIndex].credito) || 0);
        const diferenciaOtrasFilas = totalDebitoOtrasFilas - totalCreditoOtrasFilas;

        if (diferenciaOtrasFilas > 0.001) {
          e.preventDefault();
          handleMovimientoChange(lastMovimientoIndex, 'debito', '');
          handleMovimientoChange(lastMovimientoIndex, 'credito', diferenciaOtrasFilas.toFixed(2));
          setTimeout(() => formRefs.current['guardar-doc']?.focus(), 50);
        }
        else if (diferenciaOtrasFilas < -0.001) {
          e.preventDefault();
          handleMovimientoChange(lastMovimientoIndex, 'credito', '');
          handleMovimientoChange(lastMovimientoIndex, 'debito', Math.abs(diferenciaOtrasFilas).toFixed(2));
          setTimeout(() => formRefs.current['guardar-doc']?.focus(), 50);
        }
      }
    }
  };

  const shouldFetchFacturasTrigger = useRef(false);

  const handleConceptoKeyDown = (e, index) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      if (index > 0) {
        const conceptoAnterior = movimientos[index - 1].concepto;
        setMovimientos(currentMovimientos => {
          const newMovimientos = [...currentMovimientos];
          newMovimientos[index] = { ...newMovimientos[index], concepto: conceptoAnterior };
          return newMovimientos;
        });
      }
    }

    // --- NUEVO: AUTO-COMPLETAR CON TAB SI ESTÁ VACÍO ---
    if (e.key === 'Tab' && !e.shiftKey) {
      const currentMov = movimientos[index];
      // Si el concepto está vacío y hay una cuenta seleccionada
      if ((!currentMov.concepto || currentMov.concepto.trim() === '') && currentMov.cuentaId) {
        const cuenta = maestros.cuentas.find(c => c.id === parseInt(currentMov.cuentaId));
        if (cuenta) {
          handleMovimientoChange(index, 'concepto', cuenta.nombre);
        }
      }
    }

    handleKeyDown(e, `mov-${index}-concepto`);
  };

  useEffect(() => {
    setFacturasPendientes([]);
    setAplicaciones({});
    setValorAAbonar('');
    shouldFetchFacturasTrigger.current = false;
  }, [beneficiarioId, tipoDocumentoId]);

  useEffect(() => {
    const esPago = tipoDocSeleccionado?.funcion_especial === FuncionEspecial.RC_CLIENTE || tipoDocSeleccionado?.funcion_especial === FuncionEspecial.PAGO_PROVEEDOR;

    if (user?.empresaId && beneficiarioId && esPago) {
      shouldFetchFacturasTrigger.current = true;
    } else {
      shouldFetchFacturasTrigger.current = false;
    }
  }, [beneficiarioId, tipoDocSeleccionado?.funcion_especial, user?.empresaId]);

  useEffect(() => {
    if (shouldFetchFacturasTrigger.current) {
      shouldFetchFacturasTrigger.current = false;
      fetchFacturasPendientes(beneficiarioId);
    }
  }, [beneficiarioId, fetchFacturasPendientes]);

  useEffect(() => {
    const baseOrder = ['fecha', 'tipoDocumento', 'numero', 'beneficiario', 'centroCosto'];

    const esPago = tipoDocSeleccionado?.funcion_especial === FuncionEspecial.RC_CLIENTE || tipoDocSeleccionado?.funcion_especial === FuncionEspecial.PAGO_PROVEEDOR;
    const esFactura = tipoDocSeleccionado?.funcion_especial === FuncionEspecial.CARTERA_CLIENTE || tipoDocSeleccionado?.funcion_especial === FuncionEspecial.CXP_PROVEEDOR;

    if (esPago) {
      baseOrder.push('valorAAbonar');
    }
    if (esFactura) {
      baseOrder.push('fechaVencimiento');
    }
    baseOrder.push('plantilla');

    let currentOrder = [...baseOrder];

    movimientos.forEach((mov, index) => {
      currentOrder.push(`mov-${index}-cuenta`);
      currentOrder.push(`mov-${index}-concepto`);
      currentOrder.push(`mov-${index}-debito`);
      currentOrder.push(`mov-${index}-credito`);
    });

    if (esPago && beneficiarioId && facturasPendientes.length > 0 && parseFloat(valorAAbonar) > 0) {
      facturasPendientes.forEach(factura => {
        currentOrder.push(`aplicacion-${factura.id}`);
      });
    }

    currentOrder.push('guardar-doc', 'guardar-plantilla');
    if (documentoRecienCreadoId) {
      currentOrder.push('imprimir-doc');
    }
    order.current = currentOrder;
  }, [movimientos, facturasPendientes, tipoDocSeleccionado, beneficiarioId, valorAAbonar, documentoRecienCreadoId]);

  useEffect(() => {
    if (authLoading) return;

    if (!user || !user.empresaId) {
      router.push('/login');
      return;
    }

    if (maestros.cuentas.length > 0) {
      setPageIsLoading(false);
      return;
    }

    const fetchMaestros = async () => {
      setPageIsLoading(true);
      setError('');
      try {
        const [cuentasRes, tercerosRes, ccostoRes, tiposDocRes, plantillasRes, conceptosRes] = await Promise.all([
          apiService.get('/plan-cuentas/list-flat/'),
          apiService.get('/terceros/'),
          apiService.get('/centros-costo/get-flat'),
          apiService.get('/tipos-documento/'),
          apiService.get('/plantillas/'),
          apiService.get('/conceptos-favoritos/')
        ]);

        const aplanarCuentas = (cuentas) => {
          let listaPlana = [];
          const recorrer = (cuenta) => {
            if (cuenta.permite_movimiento) {
              listaPlana.push(cuenta);
            }
            if (cuenta.children) {
              cuenta.children.forEach(recorrer);
            }
          };
          cuentas.forEach(recorrer);
          return listaPlana;
        };

        setMaestros({
          cuentas: aplanarCuentas(cuentasRes.data),
          terceros: tercerosRes.data,
          centrosCosto: ccostoRes.data.filter(c => c.permite_movimiento),
          tiposDocumento: tiposDocRes.data,
          plantillas: plantillasRes.data,
          conceptos: conceptosRes.data || [],
        });

      } catch (err) {
        setError(err.response?.data?.detail || 'Error fatal al cargar los datos maestros.');
        setPageIsLoading(false);
      } finally {
        setPageIsLoading(false);
      }
    };
    fetchMaestros();


  }, [user, authLoading, router, maestros.cuentas.length]);

  if (pageIsLoading || authLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
        <FaFileAlt className="text-indigo-300 text-6xl mb-4 animate-pulse" />
        <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando contabilidad...</p>
      </div>
    );
  }

  if (error && (maestros.cuentas.length === 0)) {
    return (
      <div className="min-h-screen bg-gray-50 p-6 flex items-center justify-center">
        <div className="bg-white p-8 rounded-xl shadow-lg border border-red-100 max-w-2xl text-center">
          <FaExclamationTriangle className="text-4xl text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Error de Carga</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <div className="flex justify-center">
            <button onClick={() => router.push('/')} className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700">Ir al Inicio</button>
          </div>
        </div>
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
                <FaFileAlt className="text-2xl" />
              </div>
              <div>
                <div className="flex items-center gap-4">
                  <h1 className="text-3xl font-bold text-gray-800">Documento Contable</h1>
                  <button
                    onClick={() => window.open('/manual/capitulo_24_nuevo_documento.html', '_blank')}
                    className="text-indigo-600 hover:bg-indigo-50 px-2 py-1 rounded-md flex items-center gap-2 transition-colors"
                    title="Ver Manual de Usuario"
                  >
                    <span className="text-lg">📖</span> <span className="font-bold text-sm hidden md:inline">Manual</span>
                  </button>
                </div>
                <p className="text-gray-500 text-sm">Registro manual de asientos, notas y comprobantes.</p>
              </div>
            </div>
          </div>
        </div>

        {/* NOTIFICACIONES */}
        {mensaje && (
          <div className="mb-6 p-4 bg-green-50 border-l-4 border-green-500 text-green-700 rounded-r-lg animate-fadeIn flex items-center gap-3">
            <FaCheckCircle className="text-xl" />
            <p className="font-bold">{mensaje}</p>
          </div>
        )}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded-r-lg animate-pulse flex items-center gap-3">
            <FaExclamationTriangle className="text-xl" />
            <p className="font-bold">{error}</p>
          </div>
        )}

        <form className="space-y-6">

          {/* CARD 1: CABECERA DEL DOCUMENTO */}
          <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 animate-fadeIn">
            <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2 border-b border-gray-100 pb-2">
              <span className="bg-indigo-100 text-indigo-600 w-6 h-6 flex items-center justify-center rounded-full text-xs">1</span>
              Información General
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* FECHA */}
              <div>
                <label htmlFor="fecha" className={labelClass}>Fecha Contable</label>
                <div className="relative">
                  <DatePicker
                    selected={fecha}
                    onChange={(date) => setFecha(date || new Date())}
                    dateFormat="dd/MM/yyyy"
                    className={inputClass}
                    ref={(el) => addRef('fecha', el)}
                    onKeyDown={(e) => handleKeyDown(e, 'fecha')}
                    id="fecha"
                  />
                  <FaCalendarAlt className="absolute right-3 top-3 text-gray-400 pointer-events-none" />
                </div>
              </div>

              {/* TIPO DOCUMENTO */}
              <div>
                <label htmlFor="tipoDocumento" className={labelClass}>Tipo de Documento</label>
                <div className="relative">
                  <select
                    id="tipoDocumento"
                    value={tipoDocumentoId}
                    onChange={e => handleTipoDocumentoChange(e.target.value)}
                    className={selectClass}
                    ref={(el) => addRef('tipoDocumento', el)}
                    onKeyDown={(e) => handleKeyDown(e, 'tipoDocumento')}
                  >
                    <option value="">Seleccione...</option>
                    {maestros.tiposDocumento.map(t => <option key={t.id} value={t.id}>{t.nombre}</option>)}
                  </select>
                  <FaList className="absolute right-8 top-3 text-gray-400 pointer-events-none" />
                </div>
              </div>

              {/* NÚMERO */}
              <div>
                <label htmlFor="numero" className={labelClass}>Número / Consecutivo</label>
                <div className="relative">
                  <input
                    type="number"
                    id="numero"
                    value={numero}
                    onChange={e => { setNumero(e.target.value); setError(''); }}
                    disabled={!numeroEditable}
                    className={`${inputClass} disabled:bg-gray-50 disabled:text-gray-500`}
                    ref={(el) => addRef('numero', el)}
                    onKeyDown={(e) => handleKeyDown(e, 'numero')}
                  />
                  <FaHashtag className="absolute right-3 top-3 text-gray-400 pointer-events-none" />
                </div>
              </div>

              {/* BENEFICIARIO */}
              <div>
                <label htmlFor="beneficiario" className={labelClass}>
                  Tercero / Beneficiario
                  <button
                    type="button"
                    onClick={() => setShowTerceroModal(true)}
                    className="ml-2 text-indigo-600 hover:text-indigo-800 text-[10px] font-bold bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200 transition-colors inline-flex items-center gap-1"
                    title="Crear nuevo tercero rápidamente"
                  >
                    <FaPlus size={8} /> CREAR
                  </button>
                </label>
                <div className="relative">
                  <select
                    id="beneficiario"
                    value={beneficiarioId}
                    onChange={e => handleBeneficiarioChange(e.target.value)}
                    className={selectClass}
                    ref={(el) => addRef('beneficiario', el)}
                    onKeyDown={(e) => handleKeyDown(e, 'beneficiario')}
                  >
                    <option value="">Seleccione...</option>
                    {maestros.terceros.map(t => <option key={t.id} value={t.id}>{t.razon_social}</option>)}
                  </select>
                  <FaUserTag className="absolute right-8 top-3 text-gray-400 pointer-events-none" />
                </div>
              </div>

              {/* CENTRO DE COSTO */}
              <div>
                <label htmlFor="centroCosto" className={labelClass}>Centro de Costo</label>
                <div className="relative">
                  <select
                    id="centroCosto"
                    value={centroCostoId}
                    onChange={e => setCentroCostoId(e.target.value)}
                    className={selectClass}
                    ref={(el) => addRef('centroCosto', el)}
                    onKeyDown={(e) => handleKeyDown(e, 'centroCosto')}
                  >
                    <option value="">Ninguno</option>
                    {maestros.centrosCosto.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
                  </select>
                  <FaBuilding className="absolute right-8 top-3 text-gray-400 pointer-events-none" />
                </div>
              </div>

              {/* VALOR A ABONAR (CONDICIONAL) */}
              {(tipoDocSeleccionado?.funcion_especial === FuncionEspecial.RC_CLIENTE || tipoDocSeleccionado?.funcion_especial === FuncionEspecial.PAGO_PROVEEDOR) && (
                <div className="animate-fadeIn">
                  <label htmlFor="valorAAbonar" className="block text-xs font-bold text-green-600 uppercase mb-1 tracking-wide">Valor Total a Abonar</label>
                  <div className="relative">
                    <input
                      type="number"
                      id="valorAAbonar"
                      value={valorAAbonar}
                      onChange={e => setValorAAbonar(e.target.value)}
                      placeholder="0.00"
                      className={`${inputClass} border-green-300 focus:ring-green-200 font-bold text-green-700`}
                      ref={(el) => addRef('valorAAbonar', el)}
                      onKeyDown={(e) => handleKeyDown(e, 'valorAAbonar')}
                    />
                    <FaMoneyBillWave className="absolute right-3 top-3 text-green-500 pointer-events-none" />
                  </div>
                </div>
              )}

              {/* VENCIMIENTO (CONDICIONAL) */}
              {(tipoDocSeleccionado?.funcion_especial === FuncionEspecial.CARTERA_CLIENTE || tipoDocSeleccionado?.funcion_especial === FuncionEspecial.CXP_PROVEEDOR) && (
                <div className="animate-fadeIn">
                  <label htmlFor="fechaVencimiento" className={labelClass}>Fecha Vencimiento</label>
                  <div className="relative">
                    <DatePicker
                      id="fechaVencimiento"
                      selected={fechaVencimiento}
                      onChange={(date) => setFechaVencimiento(date)}
                      dateFormat="dd/MM/yyyy"
                      className={inputClass}
                      placeholderText="Opcional"
                      ref={(el) => addRef('fechaVencimiento', el)}
                      onKeyDown={(e) => handleKeyDown(e, 'fechaVencimiento')}
                    />
                    <FaCalendarAlt className="absolute right-3 top-3 text-gray-400 pointer-events-none" />
                  </div>
                </div>
              )}

              {/* PLANTILLA */}
              <div>
                <label htmlFor="plantilla" className={labelClass}>Cargar Plantilla (Opcional)</label>
                <select
                  id="plantilla"
                  onChange={e => handlePlantillaChange(e.target.value)}
                  className={`${selectClass} bg-slate-50`}
                  ref={(el) => addRef('plantilla', el)}
                  onKeyDown={(e) => handleKeyDown(e, 'plantilla')}
                  defaultValue=""
                >
                  <option value="">Ninguna</option>
                  {maestros.plantillas.map(p => <option key={p.id} value={p.id}>{p.nombre_plantilla}</option>)}
                </select>
              </div>
            </div>
          </div >

          {/* SECCIÓN DE CARTERA (CONDICIONAL) */}
          {
            (tipoDocSeleccionado?.funcion_especial === FuncionEspecial.RC_CLIENTE || tipoDocSeleccionado?.funcion_especial === FuncionEspecial.PAGO_PROVEEDOR) && beneficiarioId && (
              <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 animate-slideDown mb-6">
                <h2 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2">
                  <FaMoneyBillWave className="text-green-500" /> Aplicación de Pagos
                </h2>

                {isCarteraLoading && <p className="text-indigo-500 animate-pulse">Cargando facturas pendientes...</p>}

                {!isCarteraLoading && facturasPendientes.length === 0 && (
                  <p className="text-center text-gray-400 italic py-4">Este tercero no tiene facturas con saldo pendiente.</p>
                )}

                {!isCarteraLoading && facturasPendientes.length > 0 && (
                  <div className="overflow-hidden rounded-lg border border-gray-200">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-slate-100">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase">Factura</th>
                          <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase">Fecha</th>
                          <th className="px-6 py-3 text-right text-xs font-bold text-gray-500 uppercase">Saldo Pendiente</th>
                          <th className="px-6 py-3 text-right text-xs font-bold text-gray-500 uppercase w-48">Abono</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-100">
                        {facturasPendientes.map((factura) => (
                          <tr key={factura.id} className="hover:bg-gray-50">
                            <td className="px-6 py-3 text-sm font-mono text-gray-700">{factura.numero}</td>
                            <td className="px-6 py-3 text-sm text-gray-600">{new Date(factura.fecha + 'T00:00:00').toLocaleDateString('es-CO')}</td>
                            <td className="px-6 py-3 text-right text-sm font-mono font-bold text-gray-800">${factura.saldo_pendiente.toLocaleString('es-CO', { minimumFractionDigits: 2 })}</td>
                            <td className="px-6 py-2">
                              <input
                                type="number"
                                placeholder="0.00"
                                value={aplicaciones[factura.id] || ''}
                                onChange={(e) => handleAplicacionChange(factura.id, e.target.value)}
                                max={factura.saldo_pendiente}
                                className={`${tableInputClass} text-right font-bold text-green-700 bg-green-50 border-green-200`}
                                ref={(el) => addRef(`aplicacion-${factura.id}`, el)}
                                onKeyDown={(e) => handleKeyDown(e, `aplicacion-${factura.id}`)}
                              />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    <div className="bg-slate-50 px-6 py-4 flex justify-end gap-8 border-t border-gray-200">
                      <div className="text-right">
                        <p className="text-xs font-bold text-gray-500 uppercase">Total a Abonar</p>
                        <p className="font-mono text-xl font-bold text-gray-800">${totalAbono.toLocaleString('es-CO', { minimumFractionDigits: 2 })}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs font-bold text-gray-500 uppercase">Total Aplicado</p>
                        <p className={`font-mono text-xl font-bold ${Math.abs(totalAbono - totalAplicado) > 0.01 ? 'text-red-600' : 'text-green-600'}`}>
                          ${totalAplicado.toLocaleString('es-CO', { minimumFractionDigits: 2 })}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )
          }

          {/* CARD 2: MOVIMIENTOS */}
          <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 animate-slideDown">
            <div className="flex justify-between items-center mb-4 border-b border-gray-100 pb-2">
              <h3 className="text-lg font-bold text-gray-700 flex items-center gap-2">
                <span className="bg-indigo-100 text-indigo-600 w-6 h-6 flex items-center justify-center rounded-full text-xs">2</span>
                Detalle Contable
              </h3>
              <button
                type="button"
                onClick={agregarFila}
                className="px-3 py-1.5 bg-gray-100 text-gray-700 hover:bg-gray-200 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
              >
                <FaPlus className="text-indigo-500" /> Agregar Fila
              </button>
            </div>

            <div className="overflow-hidden rounded-lg border border-gray-200">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-slate-100">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider w-1/4">Cuenta Contable</th>
                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider w-1/4">Concepto / Detalle</th>
                    <th className="px-4 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider">Saldo</th>
                    <th className="px-4 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider">Débito</th>
                    <th className="px-4 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider">Crédito</th>
                    <th className="px-2 py-3"></th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-100">
                  {movimientos.map((mov, index) => (
                    <tr key={mov.rowId} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-2">
                        <input
                          list="cuentas-list"
                          placeholder="Código o nombre..."
                          value={mov.cuentaInput}
                          onChange={e => handleMovimientoChange(index, 'cuentaInput', e.target.value)}
                          onBlur={e => mov.cuentaId === '' && handleCuentaBlur(index, e.target.value)}
                          className={tableInputClass}
                          ref={(el) => addRef(`mov-${index}-cuenta`, el)}
                          onKeyDown={(e) => handleKeyDown(e, `mov-${index}-cuenta`)}
                        />
                        <datalist id="cuentas-list">
                          {maestros.cuentas.map(c => <option key={c.id} value={c.codigo}>{`${c.codigo} - ${c.nombre}`}</option>)}
                        </datalist>
                      </td>
                      <td className="px-4 py-2">
                        <div className="flex items-center gap-1">
                          <input
                            list="conceptos-list"
                            type="text"
                            placeholder="Descripción..."
                            value={mov.concepto || ''}
                            onChange={e => handleMovimientoChange(index, 'concepto', e.target.value)}
                            className={tableInputClass}
                            name={`concepto-${index}`}
                            ref={(el) => addRef(`mov-${index}-concepto`, el)}
                            onKeyDown={(e) => handleConceptoKeyDown(e, index)}
                          />
                          <datalist id="conceptos-list">
                            {maestros.conceptos.map(c => <option key={c.id} value={c.descripcion} />)}
                          </datalist>
                          <button
                            type="button"
                            onClick={() => handleAddNewConcept(index)}
                            className="p-1.5 bg-green-100 text-green-700 rounded hover:bg-green-200 text-xs font-bold border border-green-200 transition-colors"
                            title="Guardar concepto"
                          >+</button>
                        </div>
                      </td>
                      <td className="px-4 py-2 text-right">
                        <span className={`text-xs font-mono font-bold ${(() => {
                          const c = maestros.cuentas.find(x => x.id === parseInt(mov.cuentaId));
                          const s = c ? (c.saldo || 0) : 0;
                          return s < 0 ? 'text-red-500' : 'text-gray-600';
                        })()
                          }`}>
                          {(() => {
                            const c = maestros.cuentas.find(x => x.id === parseInt(mov.cuentaId));
                            const saldo = c ? (c.saldo || 0) : 0;
                            return c ? `$${saldo.toLocaleString('es-CO', { minimumFractionDigits: 2 })}` : '-';
                          })()}
                        </span>
                      </td>
                      <td className="px-4 py-2">
                        <input
                          type="number"
                          placeholder="0.00"
                          name={`mov-${index}-debito`}
                          value={mov.debito || ''}
                          onChange={e => handleMovimientoChange(index, 'debito', e.target.value)}
                          className={`${tableInputClass} text-right font-mono`}
                          ref={(el) => addRef(`mov-${index}-debito`, el)}
                          onKeyDown={(e) => handleKeyDown(e, `mov-${index}-debito`)}
                        />
                      </td>
                      <td className="px-4 py-2">
                        <input
                          type="number"
                          placeholder="0.00"
                          name={`mov-${index}-credito`}
                          value={mov.credito || ''}
                          onChange={e => handleMovimientoChange(index, 'credito', e.target.value)}
                          className={`${tableInputClass} text-right font-mono`}
                          ref={(el) => addRef(`mov-${index}-credito`, el)}
                          onKeyDown={(e) => handleKeyDown(e, `mov-${index}-credito`)}
                        />
                      </td>
                      <td className="px-2 py-2 text-center">
                        <button
                          type="button"
                          onClick={() => eliminarFila(index)}
                          className="text-red-400 hover:text-red-600 p-1.5 rounded-full hover:bg-red-50 transition-colors"
                        ><FaTrash /></button>
                      </td>
                    </tr>
                  ))}
                </tbody>
                {/* FOOTER DE TOTALES */}
                <tfoot className="bg-slate-50 border-t-2 border-slate-200">
                  <tr>
                    <td colSpan="3" className="px-4 py-3 text-right text-xs font-bold text-gray-500 uppercase">Sumas Iguales:</td>
                    <td className={`px-4 py-3 text-right text-lg font-bold font-mono ${estaBalanceado ? 'text-green-600' : 'text-red-600'}`}>
                      ${totales.debito.toLocaleString('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className={`px-4 py-3 text-right text-lg font-bold font-mono ${estaBalanceado ? 'text-green-600' : 'text-red-600'}`}>
                      ${totales.credito.toLocaleString('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td></td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>

          {/* BOTONES DE ACCIÓN */}
          <div className="flex justify-center items-center mt-8 gap-4 flex-wrap">
            <button
              type="button"
              onClick={handleSubmit}
              name="guardar-doc"
              disabled={isSubmitting || !estaBalanceado || movimientos.filter(m => m.cuentaId).length === 0}
              className={`
                    w-full md:w-auto px-8 py-3 rounded-xl shadow-lg font-bold text-white text-lg transition-all transform hover:-translate-y-1 flex items-center gap-2
                    ${isSubmitting || !estaBalanceado
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-green-600 hover:bg-green-700 hover:shadow-green-200'}
                `}
              ref={(el) => addRef('guardar-doc', el)}
              onKeyDown={(e) => handleKeyDown(e, 'guardar-doc')}
            >
              {isSubmitting ? 'Guardando...' : <><FaSave /> Guardar Documento</>}
            </button>

            <button
              type="button"
              onClick={handleSaveAsTemplate}
              name="guardar-plantilla"
              disabled={isSubmitting || movimientos.length === 0 || !movimientos[0].cuentaId}
              className="w-full md:w-auto px-6 py-3 rounded-xl shadow border border-indigo-200 text-indigo-700 bg-white hover:bg-indigo-50 font-semibold transition-colors flex items-center gap-2"
              ref={(el) => addRef('guardar-plantilla', el)}
              onKeyDown={(e) => handleKeyDown(e, 'guardar-plantilla')}
            >
              <FaBook /> Guardar Plantilla
            </button>

            {documentoRecienCreadoId && (
              <button
                type="button"
                onClick={() => handleImprimirDocumento(documentoRecienCreadoId)}
                name="imprimir-doc"
                disabled={isSubmitting}
                className="w-full md:w-auto px-6 py-3 rounded-xl shadow bg-gray-700 text-white hover:bg-gray-800 font-semibold transition-colors flex items-center gap-2 animate-pulse"
                ref={(el) => addRef('imprimir-doc', el)}
                onKeyDown={(e) => handleKeyDown(e, 'imprimir-doc')}
              >
                <FaPrint /> Imprimir Doc. #{documentoRecienCreadoId}
              </button>
            )}
          </div>
        </form >
      </div >

      {/* MODAL CREAR TERCERO */}
      <ModalCrearTercero
        isOpen={showTerceroModal}
        onClose={() => setShowTerceroModal(false)}
        onSuccess={handleTerceroCreado}
      />
    </div >
  );
}