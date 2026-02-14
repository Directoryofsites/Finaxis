// frontend/app/contabilidad/compras/page.js (REDISEÑO VISUAL COMPLETO V2.0)
'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import {
    FaShoppingCart,
    FaSave,
    FaPlus,
    FaCalendarAlt,
    FaUserTag,
    FaBuilding,
    FaWarehouse,
    FaTrash,
    FaListOl,
    FaFileInvoice,
    FaBook,
    FaSatelliteDish
} from 'react-icons/fa';

import { useAuth } from '../../context/AuthContext';
// --- Librerías ---
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// --- Servicios ---
import { getBodegas } from '../../../lib/bodegaService';
import { getTerceros } from '../../../lib/terceroService';
import { getTiposDocumento } from '../../../lib/tiposDocumentoService';
import { getCentrosCosto } from '../../../lib/centrosCostoService';
import comprasService from '../../../lib/comprasService';
import { apiService } from '../../../lib/apiService'; // MODIFIED: Named Import

// --- Componentes ---

import ProductSelectionModal from '../../components/Facturacion/ProductSelectionModal';

// Estilos reusables (Manual v2.0)
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-green-500 focus:border-green-500 text-sm transition-all outline-none";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-green-500 focus:border-green-500 text-sm transition-all outline-none bg-white";

export default function NuevaCompraPage() {
    const router = useRouter();
    const { user, loading: authLoading } = useAuth();

    // Estados del Formulario
    const [fecha, setFecha] = useState(new Date());
    const [fechaVencimiento, setFechaVencimiento] = useState(null);
    const [tipoDocumentoId, setTipoDocumentoId] = useState('');
    const [beneficiarioId, setBeneficiarioId] = useState('');
    const [numeroManual, setNumeroManual] = useState('');
    const [esManual, setEsManual] = useState(false);
    const [items, setItems] = useState([]);
    const [centroCostoId, setCentroCostoId] = useState('');
    const [bodegas, setBodegas] = useState([]);
    const [selectedBodegaId, setSelectedBodegaId] = useState('');

    const [pageIsLoading, setPageIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isModalOpen, setIsModalOpen] = useState(false);

    // --- NUEVO: Descuentos y Cargos Globales ---
    const [descuentoGlobal, setDescuentoGlobal] = useState(0);
    const [tipoDescuentoGlobal, setTipoDescuentoGlobal] = useState('$'); // '$' o '%'
    const [cargoGlobal, setCargoGlobal] = useState(0);
    // ------------------------------------------

    const [maestros, setMaestros] = useState({
        terceros: [],
        tiposDocumento: [],
        centrosCosto: [],
    });

    // Cálculo Memoizado (Premium Version)
    const { subtotalGeneral, ivaGeneral, totalGeneral, totalDescuentoLineas, descuentoGlobalCalculado } = useMemo(() => {
        const result = items.reduce((acc, item) => {
            const cantidad = parseFloat(item.cantidad) || 0;
            const costo = parseFloat(item.costo_unitario) || 0;
            const descTasa = parseFloat(item.descuento_tasa) || 0;

            const bruto = cantidad * costo;
            const descuentoValor = bruto * (descTasa / 100);
            const baseImponible = bruto - descuentoValor;
            const ivaItem = baseImponible * (item.porcentaje_iva || 0);

            acc.subtotal += baseImponible;
            acc.iva += ivaItem;
            acc.descuentoLineas += descuentoValor;
            return acc;
        }, { subtotal: 0, iva: 0, descuentoLineas: 0 });

        let descGlobalVal = parseFloat(descuentoGlobal) || 0;

        // --- LÓGICA DE PORCENTAJE ---
        if (tipoDescuentoGlobal === '%') {
            descGlobalVal = result.subtotal * (descGlobalVal / 100.0);
        }

        // --- NUEVO: RECALCULO DE IVA VISUAL (PROPORCIONAL) ---
        // Si hay descuento global, la base gravable baja, por ende el IVA baja.
        let ratioBase = 1.0;
        if (result.subtotal > 0) {
            ratioBase = (result.subtotal - descGlobalVal) / result.subtotal;
            if (ratioBase < 0) ratioBase = 0;
        }

        const ivaAjustado = result.iva * ratioBase;
        const cargoGlobalVal = parseFloat(cargoGlobal) || 0;

        return {
            subtotalGeneral: result.subtotal,
            ivaGeneral: ivaAjustado,
            totalDescuentoLineas: result.descuentoLineas,
            descuentoGlobalCalculado: descGlobalVal,
            totalGeneral: result.subtotal + ivaAjustado - descGlobalVal + cargoGlobalVal
        };
    }, [items, descuentoGlobal, tipoDescuentoGlobal, cargoGlobal]);

    // Identificar si el tipo de documento seleccionado es Documento Soporte
    const isDS = useMemo(() => {
        const td = maestros.tiposDocumento.find(t => String(t.id) === tipoDocumentoId);
        return td?.funcion_especial === 'documento_soporte';
    }, [tipoDocumentoId, maestros.tiposDocumento]);

    // Carga de Datos Maestros
    useEffect(() => {
        if (authLoading) return;
        if (!user) { router.push('/login'); return; }

        const fetchMaestros = async () => {
            try {
                setPageIsLoading(true);
                const [tercerosRes, tiposDocRes, centrosCostoRes, bodegasRes] = await Promise.all([
                    getTerceros(),
                    getTiposDocumento(),
                    getCentrosCosto(),
                    getBodegas()
                ]);

                // Filtro Estructural: Solo hijos
                const centrosCostoFiltrados = centrosCostoRes.filter(c => c.permite_movimiento);

                setMaestros({
                    terceros: tercerosRes.filter(t => t.es_proveedor),
                    tiposDocumento: tiposDocRes.filter(td => td.funcion_especial === 'cxp_proveedor' || td.funcion_especial === 'documento_soporte'),
                    centrosCosto: centrosCostoFiltrados,
                });

                setBodegas(bodegasRes);
                if (bodegasRes.length > 0 && selectedBodegaId === '') {
                    setSelectedBodegaId(String(bodegasRes[0].id));
                } else if (bodegasRes.length === 0) {
                    toast.error("No se encontraron bodegas. No podrá registrar compras.");
                    setSelectedBodegaId('');
                }

            } catch (err) {
                const errorMsg = err.response?.data?.detail || 'Error al cargar datos maestros.';
                toast.error(errorMsg);
            } finally {
                setPageIsLoading(false);
            }
        };
        fetchMaestros();
    }, [user, authLoading, router, selectedBodegaId]);

    // Handlers
    const handleTipoDocChange = (e) => {
        const selectedId = e.target.value;
        setTipoDocumentoId(selectedId);
        const tipoDocSeleccionado = maestros.tiposDocumento.find(td => String(td.id) === selectedId);
        setEsManual(tipoDocSeleccionado ? tipoDocSeleccionado.numeracion_manual : false);
        setNumeroManual('');
    };

    const handleAddProducts = (newItemsFromModal) => {
        const newItems = newItemsFromModal.map(item => ({
            ...item,
            costo_unitario: parseFloat(item.costo_unitario) || 0
        }));

        setItems(prevItems => {
            const updatedItems = [...prevItems];
            newItems.forEach(newItem => {
                const existingIndex = updatedItems.findIndex(i => i.producto_id === newItem.producto_id);
                if (existingIndex > -1) {
                    updatedItems[existingIndex] = {
                        ...updatedItems[existingIndex],
                        cantidad: (parseFloat(updatedItems[existingIndex].cantidad) || 0) + (parseFloat(newItem.cantidad) || 0),
                        costo_unitario: newItem.costo_unitario
                    };
                } else {
                    updatedItems.push({
                        producto_id: newItem.producto_id,
                        codigo: newItem.codigo,
                        nombre: newItem.nombre,
                        cantidad: newItem.cantidad,
                        costo_unitario: newItem.costo_unitario,
                        porcentaje_iva: newItem.porcentaje_iva || 0
                    });
                }
            });
            return updatedItems;
        });
    };

    const handleItemChange = (productId, field, value) => {
        const numericValue = value === '' ? '' : parseFloat(value);
        if (value !== '' && isNaN(numericValue)) return;
        setItems(prevItems => prevItems.map(item =>
            item.producto_id === productId ? { ...item, [field]: value } : item
        ));
    };

    const handleRemoveItem = (productId) => {
        setItems(prev => prev.filter(item => item.producto_id !== productId));
    };

    const handleSubmit = async () => {
        if (!tipoDocumentoId) return toast.error("Seleccione un tipo de documento.");
        if (!beneficiarioId) return toast.error("Seleccione un proveedor.");
        if (!selectedBodegaId) return toast.error("Seleccione una bodega de destino.");
        if (items.length === 0) return toast.error("Añada al menos un producto.");
        if (esManual && !numeroManual.trim()) return toast.error("Ingrese el número de factura manual.");

        let itemsValidados;
        try {
            itemsValidados = items.map(item => {
                const cantidadNum = parseFloat(item.cantidad);
                const costoNum = parseFloat(item.costo_unitario);
                if (isNaN(cantidadNum) || cantidadNum <= 0 || isNaN(costoNum) || costoNum < 0) {
                    throw new Error(`Datos inválidos para ${item.nombre || `ID ${item.producto_id}`}. Cantidad debe ser > 0 y Costo >= 0.`);
                }
                return {
                    producto_id: item.producto_id,
                    cantidad: cantidadNum,
                    costo_unitario: costoNum,
                    descuento_tasa: parseFloat(item.descuento_tasa) || 0
                };
            });
        } catch (validationError) {
            return toast.error(validationError.message);
        }

        setIsSubmitting(true);

        const payload = {
            tipo_documento_id: parseInt(tipoDocumentoId),
            beneficiario_id: parseInt(beneficiarioId),
            fecha: fecha.toISOString().split('T')[0],
            fecha_vencimiento: fechaVencimiento ? fechaVencimiento.toISOString().split('T')[0] : null,
            numero: esManual ? numeroManual.trim() : null,
            centro_costo_id: centroCostoId ? parseInt(centroCostoId) : null,
            bodega_id: parseInt(selectedBodegaId),
            descuento_global_valor: parseFloat(descuentoGlobalCalculado) || 0,
            cargos_globales_valor: parseFloat(cargoGlobal) || 0,
            items: itemsValidados
        };

        // Función interna para emitir si se solicita
        const emitir = async (docId) => {
            try {
                toast.info("Transmitiendo Documento Soporte a la DIAN...");
                const res = await apiService.post(`/fe/emitir/${docId}`);
                toast.success("¡Documento Soporte emitido con éxito!");
                return res.data;
            } catch (err) {
                console.error("Error al emitir DS:", err);
                toast.error(`Error de emisión: ${err.response?.data?.detail || "Error desconocido"}`);
                return null;
            }
        };

        try {
            const response = await comprasService.createCompra(payload);
            toast.success(`¡Éxito! Compra #${response.numero} creada correctamente.`);

            // Si es DS y el usuario solicitó emitir (pasaremos un flag o usamos el botón específico)
            // Para simplicidad, agregamos un segundo argumento a handleSubmit o detectamos el botón.
            // Aquí, si isDS es true y fue llamado desde el botón de emitir, lanzamos la emisión.
            // Pero haremos que handleSubmit reciba un flag 'emitirDS'

            // Nota: He modificado la firma de handleSubmit para aceptar emitirDS
            return response; // Devolver response para el flujo de emisión
        } catch (err) {
            console.error("Error al guardar compra:", err);
            const errorMsg = err.response?.data?.detail || "Ocurrió un error inesperado al guardar la compra.";
            toast.error(`Error: ${errorMsg}`);
            throw err; // Propagar error para detener flujo
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleSaveAndEmit = async () => {
        setIsSubmitting(true);
        try {
            // 1. Guardar Compra (handleSubmit maneja su propio loading/error para la creación)
            // Pero como handleSubmit retorna el objeto creado, lo capturamos.
            const doc = await handleSubmit();

            if (doc && doc.id) {
                // 2. Emitir DS
                toast.info("Iniciando emisión a DIAN...");
                try {
                    const res = await apiService.post(`/fe/emitir/${doc.id}`);
                    const emitJson = res.data;

                    if (emitJson.success) {
                        toast.success(`¡Documento Soporte emitido con éxito! CUFE: ${emitJson.cufe}`);
                        // Limpiar formulario completo SOLO si todo fue éxito
                        setItems([]);
                        setBeneficiarioId('');
                        setNumeroManual('');
                        setCentroCostoId('');
                        setFechaVencimiento(null);
                        setDescuentoGlobal(0);
                        setCargoGlobal(0);
                        setTipoDescuentoGlobal('$');
                    } else {
                        console.error("Error FE:", emitJson);
                        toast.error(`Guardado OK, pero error al emitir: ${emitJson.error || "Error desconocido"}`);
                    }
                } catch (emitError) {
                    console.error("Error al emitir request:", emitError);
                    toast.error(`Error de conexión al emitir: ${emitError.message || "Sin respuesta del servidor"}`);
                }
            }
        } catch (e) {
            // Error ya manejado en handleSubmit (toast.error)
            console.error("Error en flujo Save/Emit:", e);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleSimpleSave = async () => {
        try {
            const doc = await handleSubmit();
            if (doc) {
                // Limpiar formulario completo
                setItems([]);
                setBeneficiarioId('');
                setNumeroManual('');
                setCentroCostoId('');
                setFechaVencimiento(null);
                setDescuentoGlobal(0);
                setCargoGlobal(0);
                setTipoDescuentoGlobal('$');
            }
        } catch (e) { }
    };

    if (pageIsLoading || authLoading) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
                <FaShoppingCart className="text-green-300 text-6xl mb-4 animate-pulse" />
                <p className="text-green-600 font-semibold text-lg animate-pulse">Cargando módulo de compras...</p>
            </div>
        );
    }

    // --- BLINDAJE AUDITORÍA/CLON ---
    if (user?.empresa?.modo_operacion === 'AUDITORIA_READONLY') {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-6 text-center">
                <div className="bg-white p-8 rounded-xl shadow-lg border border-yellow-200 max-w-lg">
                    <FaShoppingCart className="text-5xl text-yellow-500 mx-auto mb-4" />
                    <h2 className="text-2xl font-bold text-gray-800 mb-2">Restricción de Auditoría</h2>
                    <p className="text-gray-600 mb-6">
                        Esta empresa está en <strong>Modo Auditoría / Clon</strong>.
                        El registro de <strong>Facturas de Compra</strong> está deshabilitado.
                        No se permite afectar inventarios ni crear cuentas por pagar en este modo.
                    </p>
                    <button
                        onClick={() => router.push('/dashboard')}
                        className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-bold"
                    >
                        Volver al Dashboard
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
            <div className="max-w-7xl mx-auto">
                <ToastContainer position="top-right" autoClose={5000} />

                {/* ENCABEZADO */}
                {/* ENCABEZADO */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                    <div>
                        <div className="flex items-center gap-3 mt-3">
                            <div className="p-2 bg-green-100 rounded-lg text-green-600">
                                <FaShoppingCart className="text-2xl" />
                            </div>
                            <div>
                                <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-3">
                                    Nueva Compra
                                    <button
                                        onClick={() => window.open('/manual/capitulo_40_compras.html', '_blank')}
                                        className="text-indigo-600 hover:bg-indigo-50 px-2 py-1 rounded-md flex items-center gap-2 transition-colors font-bold text-sm border border-indigo-100 shadow-sm"
                                        type="button"
                                    >
                                        <FaBook className="text-lg" /> <span className="hidden md:inline">Manual</span>
                                    </button>
                                </h1>
                                <p className="text-gray-500 text-sm">Registro de facturas de proveedores e ingreso de inventario.</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* CARD 1: DATOS GENERALES */}
                <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 animate-fadeIn mb-6">
                    <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2 border-b border-gray-100 pb-2">
                        <span className="bg-green-100 text-green-600 w-6 h-6 flex items-center justify-center rounded-full text-xs">1</span>
                        Información del Proveedor
                    </h3>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {/* Fecha */}
                        <div>
                            <label htmlFor="fecha" className={labelClass}>Fecha Emisión</label>
                            <div className="relative">
                                <DatePicker selected={fecha} onChange={(date) => setFecha(date || new Date())} dateFormat="dd/MM/yyyy" className={inputClass} />
                                <FaCalendarAlt className="absolute right-3 top-3 text-gray-400 pointer-events-none" />
                            </div>
                        </div>

                        {/* Tipo Doc */}
                        <div>
                            <label htmlFor="tipoDocumento" className={labelClass}>Tipo Documento <span className="text-red-500">*</span></label>
                            <div className="relative">
                                <select id="tipoDocumento" value={tipoDocumentoId} onChange={handleTipoDocChange} className={selectClass} required>
                                    <option value="">Seleccione...</option>
                                    {maestros.tiposDocumento.map(t => <option key={t.id} value={t.id}>{`(${t.codigo}) ${t.nombre}`}</option>)}
                                </select>
                                <FaListOl className="absolute right-8 top-3 text-gray-400 pointer-events-none" />
                            </div>
                        </div>

                        {/* Bodega */}
                        <div>
                            <label htmlFor="bodega" className={labelClass}>Bodega Destino <span className="text-red-500">*</span></label>
                            <div className="relative">
                                <select
                                    id="bodega" value={selectedBodegaId} onChange={e => setSelectedBodegaId(e.target.value)}
                                    className={`${selectClass} bg-yellow-50 border-yellow-300`}
                                    disabled={bodegas.length === 0} required
                                >
                                    {bodegas.length === 0 ? (
                                        <option value="">No hay bodegas...</option>
                                    ) : (
                                        <>
                                            <option value="">Seleccione...</option>
                                            {bodegas.map(b => <option key={b.id} value={String(b.id)}>{b.nombre}</option>)}
                                        </>
                                    )}
                                </select>
                                <FaWarehouse className="absolute right-8 top-3 text-gray-400 pointer-events-none" />
                            </div>
                        </div>

                        {/* Proveedor */}
                        <div>
                            <label htmlFor="beneficiario" className={labelClass}>Proveedor <span className="text-red-500">*</span></label>
                            <div className="relative">
                                <select id="beneficiario" value={beneficiarioId} onChange={e => setBeneficiarioId(e.target.value)} className={selectClass} required>
                                    <option value="">Seleccione...</option>
                                    {maestros.terceros.map(t => <option key={t.id} value={t.id}>{`(${t.nit}) ${t.razon_social}`}</option>)}
                                </select>
                                <FaUserTag className="absolute right-8 top-3 text-gray-400 pointer-events-none" />
                            </div>
                        </div>

                        {/* Número Manual (Condicional) */}
                        {esManual && (
                            <div className="animate-fadeIn">
                                <label htmlFor="numeroManual" className={labelClass}># Factura Proveedor <span className="text-red-500">*</span></label>
                                <div className="relative">
                                    <input type="text" id="numeroManual" value={numeroManual} onChange={e => setNumeroManual(e.target.value)} required className={inputClass} placeholder="Ej: FE-1099" />
                                    <FaFileInvoice className="absolute right-3 top-3 text-gray-400 pointer-events-none" />
                                </div>
                            </div>
                        )}

                        {/* Fecha Vencimiento */}
                        <div>
                            <label htmlFor="fechaVencimiento" className={labelClass}>Fecha Vencimiento</label>
                            <div className="relative">
                                <DatePicker selected={fechaVencimiento} onChange={(date) => setFechaVencimiento(date)} dateFormat="dd/MM/yyyy" className={inputClass} isClearable placeholderText='(Opcional)' />
                                <FaCalendarAlt className="absolute right-8 top-3 text-gray-400 pointer-events-none" />
                            </div>
                        </div>

                        {/* Centro Costo */}
                        <div>
                            <label htmlFor="centroCostoId" className={labelClass}>Centro de Costo</label>
                            <div className="relative">
                                <select id="centroCostoId" value={centroCostoId} onChange={e => setCentroCostoId(e.target.value)} className={selectClass}>
                                    <option value="">(Opcional)</option>
                                    {maestros.centrosCosto.map(cc => <option key={cc.id} value={cc.id}>{cc.nombre}</option>)}
                                </select>
                                <FaBuilding className="absolute right-8 top-3 text-gray-400 pointer-events-none" />
                            </div>
                        </div>
                    </div>
                </div>

                {/* CARD 2: ITEMS */}
                <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 animate-slideDown">
                    <div className="flex justify-between items-center mb-4 border-b border-gray-100 pb-2">
                        <h3 className="text-lg font-bold text-gray-700 flex items-center gap-2">
                            <span className="bg-green-100 text-green-600 w-6 h-6 flex items-center justify-center rounded-full text-xs">2</span>
                            Productos a Comprar
                        </h3>
                        <button
                            type="button" onClick={() => setIsModalOpen(true)}
                            disabled={!selectedBodegaId}
                            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 shadow-md flex items-center gap-2 transition-colors disabled:bg-gray-300" >
                            <FaPlus /> Añadir Items
                        </button>
                    </div>

                    <div className="overflow-hidden rounded-xl border border-gray-200">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-slate-100">
                                <tr>
                                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Código</th>
                                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Producto/Servicio</th>
                                    <th className="px-4 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider w-32">Cantidad</th>
                                    <th className="px-4 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider w-40">Costo Unit.</th>
                                    <th className="px-4 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider w-24">Desc %</th>
                                    <th className="px-4 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider">Subtotal</th>
                                    <th className="px-4 py-3 text-center"></th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-100">
                                {items.length === 0 ? (
                                    <tr><td colSpan="6" className="text-center text-gray-400 py-8 italic">Añade productos a la compra...</td></tr>
                                ) : (
                                    items.map((item) => (
                                        <tr key={item.producto_id} className="hover:bg-gray-50 transition-colors">
                                            <td className="px-4 py-2 font-mono text-sm text-gray-600">{item.codigo}</td>
                                            <td className="px-4 py-2 text-sm font-medium text-gray-800">{item.nombre}</td>
                                            <td className="px-4 py-2 text-right">
                                                <input type="number" value={item.cantidad} onChange={e => handleItemChange(item.producto_id, 'cantidad', e.target.value)} className="w-full px-2 py-1 border border-gray-300 rounded text-right focus:ring-2 focus:ring-green-200 outline-none" min="0.01" step="any" required />
                                            </td>
                                            <td className="px-4 py-2 text-right">
                                                <input type="number" step="0.01" value={item.costo_unitario} onChange={e => handleItemChange(item.producto_id, 'costo_unitario', e.target.value)} className="w-full px-2 py-1 border border-gray-300 rounded text-right focus:ring-2 focus:ring-green-200 outline-none" min="0" required />
                                            </td>
                                            <td className="px-4 py-2 text-right">
                                                <input type="number" step="0.01" value={item.descuento_tasa || 0} onChange={e => handleItemChange(item.producto_id, 'descuento_tasa', e.target.value)} className="w-full px-2 py-1 border border-gray-300 rounded text-right focus:ring-2 focus:ring-green-200 outline-none" min="0" max="100" />
                                            </td>
                                            <td className="px-4 py-2 text-right font-mono text-sm font-bold text-gray-700">
                                                ${((parseFloat(item.cantidad) || 0) * (parseFloat(item.costo_unitario) || 0) * (1 - (parseFloat(item.descuento_tasa) || 0) / 100)).toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                                            </td>
                                            <td className="px-4 py-2 text-center">
                                                <button onClick={() => handleRemoveItem(item.producto_id)} className="text-red-400 hover:text-red-600 p-1 rounded transition-colors"><FaTrash /></button>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                            {items.length > 0 && (
                                <tfoot className="bg-slate-50 border-t-2 border-slate-200">
                                    {/* 1. SUBTOTAL BRUTO */}
                                    <tr>
                                        <td colSpan="5" className="px-4 py-2 text-right text-sm font-normal text-gray-500 uppercase">Subtotal Bruto:</td>
                                        <td className="px-4 py-2 text-right text-lg font-normal text-gray-700">
                                            ${(items.reduce((acc, item) => acc + (parseFloat(item.cantidad) || 0) * (parseFloat(item.costo_unitario) || 0), 0)).toLocaleString('es-CO')}
                                        </td>
                                        <td></td>
                                    </tr>

                                    {/* 2. DESCUENTOS */}
                                    <tr>
                                        <td colSpan="5" className="px-4 py-2 text-right text-sm font-normal text-gray-500 uppercase align-middle">
                                            <div className="flex justify-end items-center gap-2">
                                                <span>Desc. Global:</span>
                                                <div className="flex border rounded-md overflow-hidden bg-white shadow-sm">
                                                    <button
                                                        type="button"
                                                        onClick={() => setTipoDescuentoGlobal('$')}
                                                        className={`px-3 py-1 text-sm font-bold ${tipoDescuentoGlobal === '$' ? 'bg-green-600 text-white' : 'bg-gray-50 text-gray-600 hover:bg-gray-100'}`}
                                                    >
                                                        $
                                                    </button>
                                                    <button
                                                        type="button"
                                                        onClick={() => setTipoDescuentoGlobal('%')}
                                                        className={`px-3 py-1 text-sm font-bold ${tipoDescuentoGlobal === '%' ? 'bg-green-600 text-white' : 'bg-gray-50 text-gray-600 hover:bg-gray-100'}`}
                                                    >
                                                        %
                                                    </button>
                                                </div>
                                                <input
                                                    type="number"
                                                    value={descuentoGlobal}
                                                    onChange={e => setDescuentoGlobal(parseFloat(e.target.value) || 0)}
                                                    className="w-24 px-2 py-1 text-right border border-gray-300 rounded focus:ring-2 focus:ring-green-100 outline-none font-bold text-gray-700"
                                                    placeholder="0"
                                                    min="0"
                                                />
                                            </div>
                                        </td>
                                        <td className="px-4 py-2 text-right text-lg font-normal text-red-600 align-middle">
                                            -${(totalDescuentoLineas + (tipoDescuentoGlobal === '$' ? (parseFloat(descuentoGlobal) || 0) : (subtotalGeneral * (parseFloat(descuentoGlobal) || 0) / 100))).toLocaleString('es-CO')}
                                        </td>
                                        <td></td>
                                    </tr>

                                    {/* 3. OTROS CARGOS */}
                                    <tr>
                                        <td colSpan="5" className="px-4 py-2 text-right text-sm font-normal text-gray-500 uppercase align-middle">
                                            <div className="flex justify-end items-center gap-2">
                                                <span>Otros Cargos $:</span>
                                                <input
                                                    type="number"
                                                    value={cargoGlobal}
                                                    onChange={e => setCargoGlobal(parseFloat(e.target.value) || 0)}
                                                    className="w-32 px-2 py-1 text-right border border-gray-300 rounded focus:ring-2 focus:ring-green-100 outline-none font-bold text-gray-700"
                                                    placeholder="0"
                                                    min="0"
                                                />
                                            </div>
                                        </td>
                                        <td className="px-4 py-2 text-right text-lg font-normal text-green-600 align-middle">
                                            +${(parseFloat(cargoGlobal) || 0).toLocaleString('es-CO')}
                                        </td>
                                        <td></td>
                                    </tr>
                                    <tr className="bg-green-50/50">
                                        <td colSpan="5" className="px-4 py-2 text-right text-xs font-normal text-green-800 uppercase italic">Base Factura:</td>
                                        <td className="px-4 py-2 text-right text-lg font-normal text-green-900 border-y border-green-200">
                                            ${(subtotalGeneral - (descuentoGlobalCalculado || 0) + (parseFloat(cargoGlobal) || 0)).toLocaleString('es-CO')}
                                        </td>
                                        <td></td>
                                    </tr>
                                    <tr>
                                        <td colSpan="5" className="px-4 py-2 text-right text-sm font-normal text-gray-500 uppercase">IVA Total:</td>
                                        <td className="px-4 py-2 text-right text-lg font-normal text-gray-700">
                                            ${ivaGeneral.toLocaleString('es-CO')}
                                        </td>
                                        <td></td>
                                    </tr>
                                    <tr className="bg-slate-200">
                                        <td colSpan="5" className="px-4 py-4 text-right text-sm font-normal text-slate-700 uppercase italic">Total Compra:</td>
                                        <td className="px-4 py-4 text-right text-lg font-normal text-blue-700">
                                            {totalGeneral.toLocaleString('es-CO')}
                                        </td>
                                        <td className="bg-slate-200"></td>
                                    </tr>
                                </tfoot>
                            )}
                        </table>
                    </div>
                </div>

                <div className="flex justify-end mt-8 gap-4">
                    <button
                        type="button"
                        onClick={handleSimpleSave}
                        disabled={isSubmitting || items.length === 0 || !beneficiarioId || !tipoDocumentoId || !selectedBodegaId}
                        className={`
                            px-8 py-4 rounded-xl shadow-lg font-bold text-white text-lg transition-all transform hover:-translate-y-1 flex items-center gap-3
                            ${isSubmitting || items.length === 0
                                ? 'bg-gray-400 cursor-not-allowed'
                                : 'bg-slate-600 hover:bg-slate-700 hover:shadow-slate-200'}
                        `}
                    >
                        {isSubmitting ? (
                            <> <span className="loading loading-spinner"></span> Procesando... </>
                        ) : (
                            <> <FaSave className="text-xl" /> Guardar Compra </>
                        )}
                    </button>

                    {isDS && (
                        <button
                            type="button"
                            onClick={handleSaveAndEmit}
                            disabled={isSubmitting || items.length === 0 || !beneficiarioId || !tipoDocumentoId || !selectedBodegaId}
                            className={`
                                px-8 py-4 rounded-xl shadow-lg font-bold text-white text-lg transition-all transform hover:-translate-y-1 flex items-center gap-3
                                ${isSubmitting || items.length === 0
                                    ? 'bg-gray-400 cursor-not-allowed'
                                    : 'bg-green-600 hover:bg-green-700 hover:shadow-green-200'}
                            `}
                        >
                            {isSubmitting ? (
                                <> <span className="loading loading-spinner"></span> Emitiendo... </>
                            ) : (
                                <> <FaSatelliteDish className="text-xl" /> Guardar y Emitir DS </>
                            )}
                        </button>
                    )}
                </div>

                <ProductSelectionModal
                    isOpen={isModalOpen}
                    onClose={() => setIsModalOpen(false)}
                    onAddProducts={handleAddProducts}
                    mode="compra"
                    bodegaIdSeleccionada={selectedBodegaId ? parseInt(selectedBodegaId) : null}
                />
            </div>
        </div>
    );
}