'use client';

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import {
    FaFileInvoiceDollar,
    FaSave,
    FaPlus,
    FaCalendarAlt,
    FaUserTag,
    FaBuilding,
    FaWarehouse,
    FaMoneyBillWave,
    FaTrash,
    FaTag,
    FaListOl,
    FaBook,
    FaCheckCircle,
    FaExclamationTriangle
} from 'react-icons/fa';



import { useAuth } from '../../context/AuthContext';
// --- Servicios ---
import { getBodegas } from '../../../lib/bodegaService';
import { getTerceros, getTerceroById } from '../../../lib/terceroService';
import { getTiposDocumento } from '../../../lib/tiposDocumentoService';
import { getCentrosCosto } from '../../../lib/centrosCostoService';
import facturacionService from '../../../lib/facturacionService';
import { apiService } from '../../../lib/apiService';
// --- Componentes ---
import BotonRegresar from '../../components/BotonRegresar';
import ProductSelectionModal from '../../components/Facturacion/ProductSelectionModal';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// Estilos reusables (Manual v2.0)
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm transition-all outline-none";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm transition-all outline-none bg-white";

export default function NuevaFacturaPage() {
    const router = useRouter();
    const { user, loading: authLoading } = useAuth();

    // Estados del Formulario
    const [fecha, setFecha] = useState(new Date());
    const [fechaVencimiento, setFechaVencimiento] = useState(new Date());

    const [tipoDocumentoId, setTipoDocumentoId] = useState('');
    const [beneficiarioId, setBeneficiarioId] = useState('');
    const [centroCostoId, setCentroCostoId] = useState('');
    const [items, setItems] = useState([]);
    const [condicionPago, setCondicionPago] = useState('Crédito');
    const [bodegas, setBodegas] = useState([]);
    const [selectedBodegaId, setSelectedBodegaId] = useState('');

    // --- NUEVO: ESTADOS PARA REMISIÓN ---
    const [remisionId, setRemisionId] = useState(null);
    const [isRemisionModalOpen, setIsRemisionModalOpen] = useState(false);
    const [remisionesDisponibles, setRemisionesDisponibles] = useState([]);
    // ------------------------------------

    const [clienteListaPrecioId, setClienteListaPrecioId] = useState(null);

    const [pageIsLoading, setPageIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isModalOpen, setIsModalOpen] = useState(false);

    const [maestros, setMaestros] = useState({
        terceros: [],
        tiposDocumento: [],
        centrosCosto: [],
        productos: [],
    });

    const totalFactura = useMemo(() => {
        return items.reduce((acc, item) => acc + (item.cantidad * item.precio_unitario), 0);
    }, [items]);

    const tipoDocSeleccionado = useMemo(() =>
        maestros.tiposDocumento.find(td => td.id === parseInt(tipoDocumentoId))
        , [maestros.tiposDocumento, tipoDocumentoId]);

    const bodegaRequerida = useMemo(() =>
        tipoDocSeleccionado?.afecta_inventario ?? false
        , [tipoDocSeleccionado]);

    useEffect(() => {
        if (authLoading) return;
        if (!user) {
            router.push('/login');
            return;
        }

        const fetchMaestros = async () => {
            try {
                setPageIsLoading(true);
                const [tercerosRes, tiposDocRes, centrosCostoRes, bodegasRes, productosRes] = await Promise.all([
                    getTerceros(),
                    getTiposDocumento(),
                    getCentrosCosto(),
                    getBodegas(),
                    apiService.get('/inventario/productos/list-flat')
                ]);

                // --- FILTRO ESTRUCTURAL: SOLO HIJOS ---
                const centrosCostoFiltrados = centrosCostoRes.filter(c => c.permite_movimiento);

                setMaestros({
                    terceros: tercerosRes,
                    tiposDocumento: tiposDocRes.filter(td => td.afecta_inventario && td.funcion_especial === 'cartera_cliente'),
                    centrosCosto: centrosCostoFiltrados,
                    productos: productosRes.data
                });

                setBodegas(bodegasRes);
                if (bodegasRes.length > 0 && selectedBodegaId === '') {
                    setSelectedBodegaId(String(bodegasRes[0].id));
                } else if (bodegasRes.length === 0) {
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
    }, [user, authLoading, router]);

    // Efecto para manejar la selección automática de bodega
    useEffect(() => {
        if (!pageIsLoading && bodegaRequerida && bodegas.length === 0) {
            toast.warning("No se encontraron bodegas. No podrá facturar inventario.");
        }
        if (!bodegaRequerida) {
            if (selectedBodegaId !== '') setSelectedBodegaId('');
        } else if (bodegaRequerida && selectedBodegaId === '' && bodegas.length > 0) {
            setSelectedBodegaId(String(bodegas[0].id));
        }
    }, [bodegaRequerida, bodegas, pageIsLoading, selectedBodegaId]);

    useEffect(() => {
        if (fecha > fechaVencimiento) {
            setFechaVencimiento(fecha);
        }
    }, [fecha]);


    const handleBeneficiarioChange = useCallback(async (selectedId) => {
        setBeneficiarioId(selectedId);
        setClienteListaPrecioId(null);
        if (!selectedId) return;

        try {
            const tercero = await getTerceroById(parseInt(selectedId));
            const listaId = tercero.lista_precio_id > 0 ? tercero.lista_precio_id : null;
            setClienteListaPrecioId(listaId);
            if (!listaId) toast.warning("El cliente seleccionado no tiene asignada una Lista de Precios.");
        } catch (error) {
            console.error("Error al obtener lista de precios:", error);
        }
    }, []);


    const handleAddProducts = useCallback(async (newItems) => {
        if (!beneficiarioId) {
            toast.error("Debe seleccionar un cliente antes de añadir productos.");
            return;
        }
        setIsSubmitting(true);
        const itemsWithCalculatedPrice = [];
        try {
            await Promise.all(newItems.map(async (item) => {
                let precioUnitarioCalculado = item.precio_unitario;
                if (clienteListaPrecioId) {
                    try {
                        const precioCalculado = await facturacionService.getPrecioVenta(item.producto_id, clienteListaPrecioId);
                        if (precioCalculado > 0) precioUnitarioCalculado = precioCalculado;
                        else toast.warning(`Lista de Precios inválida para ${item.nombre}. Usando precio base.`);
                    } catch (error) {
                        console.error(`[FALLO CÁLCULO] ${item.producto_id}:`, error);
                    }
                }
                itemsWithCalculatedPrice.push({ ...item, precio_unitario: precioUnitarioCalculado });
            }));

            setItems(prevItems => {
                const updatedItems = [...prevItems];
                itemsWithCalculatedPrice.forEach(newItem => {
                    const existingIndex = updatedItems.findIndex(i => i.producto_id === newItem.producto_id);
                    if (existingIndex > -1) {
                        updatedItems[existingIndex] = {
                            ...updatedItems[existingIndex],
                            cantidad: updatedItems[existingIndex].cantidad + newItem.cantidad,
                        };
                    } else {
                        updatedItems.push(newItem);
                    }
                });
                return updatedItems;
            });
        } catch (error) {
            console.error("Error handleAddProducts:", error);
            toast.error("Error al añadir productos.");
        } finally {
            setIsSubmitting(false);
        }
    }, [beneficiarioId, clienteListaPrecioId]);


    // --- LÓGICA DE REMISIONES ---
    const fetchRemisiones = async () => {
        try {
            const res = await apiService.get('/remisiones/');
            // Filtramos solo las que se pueden facturar
            const disponibles = res.data.remisiones.filter(r =>
                r.estado === 'APROBADA' || r.estado === 'FACTURADA_PARCIAL' || r.estado === 'BORRADOR'
            );
            setRemisionesDisponibles(disponibles);
        } catch (error) {
            console.error(error);
            toast.error("Error al cargar remisiones.");
        }
    };

    const handleOpenRemisionModal = () => {
        fetchRemisiones();
        setIsRemisionModalOpen(true);
    };

    const cargarRemision = (rem) => {
        // 1. Validar Bodega
        const bodegaExiste = bodegas.some(b => b.id === rem.bodega_id);
        if (!bodegaExiste && bodegas.length > 0) {
            toast.warning(`La bodega de la remisión (${rem.bodega_nombre}) no está disponible para su usuario.`);
            // Aún así permitimos cargar, o bloqueamos? Mejor permitimos y que el backend o selector validen.
        }

        // 2. Cargar Datos Cabecera
        setBeneficiarioId(rem.tercero_id);
        setSelectedBodegaId(String(rem.bodega_id));
        setRemisionId(rem.id);

        // 3. Cargar Detalles
        // Necesitamos mapear los detalles de la remisión a items de factura
        // IMPORTANTE: Solo cargamos lo PENDIENTE
        const nuevosItems = rem.detalles
            .filter(d => d.cantidad_pendiente > 0)
            .filter(d => d.cantidad_pendiente > 0)
            .map(d => {
                const producto = maestros.productos.find(p => p.id === d.producto_id);
                return {
                    producto_id: d.producto_id,
                    codigo: producto ? producto.codigo : d.producto_id,
                    nombre: producto ? producto.nombre : `Producto ID ${d.producto_id} (Desde Remisión)`,
                    cantidad: d.cantidad_pendiente,
                    precio_unitario: d.precio_unitario
                };
            });

        setItems(nuevosItems);
        setIsRemisionModalOpen(false);
        toast.success(`Remisión #${rem.numero} cargada.`);
    };
    // ------------------------------------





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
        if (!beneficiarioId) return toast.error("Seleccione un cliente.");
        if (bodegaRequerida && !selectedBodegaId) return toast.error("Seleccione una bodega.");
        if (items.length === 0) return toast.error("Añada al menos un producto.");

        if (condicionPago === 'Crédito') {
            if (!fechaVencimiento) return toast.error("La Fecha de Vencimiento es obligatoria para Crédito.");
            if (fechaVencimiento < fecha) return toast.error("La fecha de vencimiento no puede ser menor a la fecha de la factura.");
        }

        const itemsValidados = items.map(item => ({
            ...item,
            cantidad: parseFloat(item.cantidad) || 0,
            precio_unitario: parseFloat(item.precio_unitario) || 0
        }));

        if (itemsValidados.some(item => item.cantidad <= 0 || item.precio_unitario < 0)) {
            return toast.error("Cantidades deben ser mayores a 0 y precios no negativos.");
        }

        setIsSubmitting(true);

        const payload = {
            tipo_documento_id: parseInt(tipoDocumentoId),
            beneficiario_id: parseInt(beneficiarioId),
            centro_costo_id: centroCostoId ? parseInt(centroCostoId) : null,
            fecha: fecha.toISOString().split('T')[0],
            fecha_vencimiento: condicionPago === 'Crédito' ? fechaVencimiento.toISOString().split('T')[0] : null,
            condicion_pago: condicionPago,
            bodega_id: bodegaRequerida ? parseInt(selectedBodegaId) : null,
            remision_id: remisionId ? parseInt(remisionId) : null,
            items: itemsValidados
        };

        try {
            const response = await facturacionService.createFactura(payload);
            toast.success(`¡Éxito! Factura #${response.numero} creada.`);
            setItems([]);
            setBeneficiarioId('');
            setCentroCostoId('');
            setClienteListaPrecioId(null);
            setFecha(new Date());
            setFechaVencimiento(new Date());

        } catch (err) {
            console.error("Error al guardar factura:", err);
            const errorMsg = err.response?.data?.detail || "Error inesperado al guardar.";
            toast.error(`Error: ${errorMsg}`);
        } finally {
            setIsSubmitting(false);
        }
    };

    if (pageIsLoading || authLoading) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
                <FaFileInvoiceDollar className="text-blue-300 text-6xl mb-4 animate-pulse" />
                <p className="text-blue-600 font-semibold text-lg animate-pulse">Cargando módulo de facturación...</p>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
            <div className="max-w-7xl mx-auto">
                <ToastContainer position="top-right" autoClose={5000} />

                {/* ENCABEZADO */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                    <div>
                        {/* 1. BLOQUE DE BOTONES DE NAVEGACIÓN (En Fila) */}
                        <div className="flex items-center gap-3 mb-2">
                            <BotonRegresar />

                            <button
                                onClick={() => window.open('/manual?file=capitulo_41_facturacion.md', '_blank')}
                                className="text-indigo-600 hover:bg-indigo-50 px-3 py-1 rounded-md flex items-center gap-2 transition-colors font-bold text-sm"
                                type="button"
                            >
                                <FaBook className="text-lg" /> Manual
                            </button>
                        </div>

                        {/* 2. TÍTULO E ICONO */}
                        <div className="flex items-center gap-3 mt-3">
                            <div className="p-2 bg-blue-100 rounded-lg text-blue-600">
                                <FaFileInvoiceDollar className="text-2xl" />
                            </div>
                            <div>
                                <h1 className="text-3xl font-bold text-gray-800">Nueva Factura</h1>
                                <p className="text-gray-500 text-sm">Gestión de ventas y salida de inventario.</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* BOTÓN CARGAR REMISIÓN */}
                <div className="flex justify-end mb-4">
                    <button
                        onClick={handleOpenRemisionModal}
                        className="bg-orange-600 text-white px-4 py-2 rounded-lg shadow hover:bg-orange-700 flex items-center gap-2 font-bold transition-colors"
                    >
                        <FaListOl /> Cargar Remisión
                    </button>
                </div>

                {/* CARD 1: DATOS GENERALES */}
                <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 animate-fadeIn mb-6">
                    <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2 border-b border-gray-100 pb-2">
                        <span className="bg-blue-100 text-blue-600 w-6 h-6 flex items-center justify-center rounded-full text-xs">1</span>
                        Información de la Venta
                    </h3>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {/* Fecha */}
                        <div>
                            <label htmlFor="fecha" className={labelClass}>Fecha Emisión</label>
                            <div className="relative">
                                <DatePicker
                                    selected={fecha}
                                    onChange={(date) => setFecha(date || new Date())}
                                    dateFormat="dd/MM/yyyy"
                                    className={inputClass}
                                />
                                <FaCalendarAlt className="absolute right-3 top-3 text-gray-400 pointer-events-none" />
                            </div>
                        </div>

                        {/* Tipo Doc */}
                        <div>
                            <label htmlFor="tipoDocumento" className={labelClass}>Tipo Documento <span className="text-red-500">*</span></label>
                            <div className="relative">
                                <select id="tipoDocumento" value={tipoDocumentoId} onChange={e => setTipoDocumentoId(e.target.value)} className={selectClass} required >
                                    <option value="">Seleccione...</option>
                                    {maestros.tiposDocumento.map(t => <option key={t.id} value={t.id}>{`(${t.codigo}) ${t.nombre}`}</option>)}
                                </select>
                                <FaListOl className="absolute right-8 top-3 text-gray-400 pointer-events-none" />
                            </div>
                        </div>

                        {/* Bodega */}
                        <div className={bodegaRequerida ? '' : 'opacity-50 pointer-events-none grayscale'}>
                            <label htmlFor="bodega" className={labelClass}>Bodega <span className="text-red-500">*</span></label>
                            <div className="relative">
                                <select
                                    id="bodega" value={selectedBodegaId} onChange={e => setSelectedBodegaId(e.target.value)}
                                    className={`${selectClass} ${bodegaRequerida ? 'bg-yellow-50 border-yellow-300' : 'bg-gray-100'}`}
                                    disabled={!bodegaRequerida || bodegas.length === 0} required={bodegaRequerida}
                                >
                                    {!bodegaRequerida ? <option value="">(No aplica)</option> :
                                        bodegas.length === 0 ? <option value="">No hay bodegas</option> :
                                            <> <option value="">Seleccione...</option> {bodegas.map(b => <option key={b.id} value={String(b.id)}>{b.nombre}</option>)} </>}
                                </select>
                                <FaWarehouse className="absolute right-8 top-3 text-gray-400 pointer-events-none" />
                            </div>
                        </div>

                        {/* Cliente */}
                        <div className="lg:col-span-1">
                            <label htmlFor="beneficiario" className={labelClass}>Cliente <span className="text-red-500">*</span></label>
                            <div className="relative">
                                <select id="beneficiario" value={beneficiarioId} onChange={e => handleBeneficiarioChange(e.target.value)} className={selectClass} required >
                                    <option value="">Seleccione...</option>
                                    {maestros.terceros.map(t => <option key={t.id} value={t.id}>{`(${t.nit}) ${t.razon_social}`}</option>)}
                                </select>
                                <FaUserTag className="absolute right-8 top-3 text-gray-400 pointer-events-none" />
                            </div>
                            {clienteListaPrecioId && <p className="mt-1 text-xs text-green-600 font-bold flex items-center"><FaTag className="mr-1" /> Lista Precios ID: {clienteListaPrecioId}</p>}
                        </div>

                        {/* Condición Pago */}
                        <div>
                            <label htmlFor="condicionPago" className={labelClass}>Condición Pago</label>
                            <div className="relative">
                                <select id="condicionPago" value={condicionPago} onChange={e => setCondicionPago(e.target.value)} className={selectClass}>
                                    <option value="Crédito">Crédito</option>
                                    <option value="Contado">Contado</option>
                                </select>
                                <FaMoneyBillWave className="absolute right-8 top-3 text-gray-400 pointer-events-none" />
                            </div>
                        </div>

                        {/* Fecha Vencimiento */}
                        {condicionPago === 'Crédito' && (
                            <div className="animate-fadeIn">
                                <label htmlFor="fechaVencimiento" className="block text-xs font-bold text-red-500 uppercase mb-1 tracking-wide">Vencimiento <span className="text-red-500">*</span></label>
                                <div className="relative">
                                    <DatePicker
                                        selected={fechaVencimiento}
                                        onChange={(date) => setFechaVencimiento(date)}
                                        dateFormat="dd/MM/yyyy"
                                        minDate={fecha}
                                        className={`${inputClass} border-red-300 focus:border-red-500 focus:ring-red-200`}
                                    />
                                    <FaCalendarAlt className="absolute right-3 top-3 text-red-400 pointer-events-none" />
                                </div>
                            </div>
                        )}

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
                            <span className="bg-blue-100 text-blue-600 w-6 h-6 flex items-center justify-center rounded-full text-xs">2</span>
                            Detalle de Productos
                        </h3>
                        <button
                            type="button" onClick={() => setIsModalOpen(true)}
                            disabled={isSubmitting || (bodegaRequerida && !selectedBodegaId)}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 shadow-md flex items-center gap-2 transition-colors disabled:bg-gray-300" >
                            <FaPlus /> Añadir Items
                        </button>
                    </div>

                    <div className="overflow-hidden rounded-xl border border-gray-200">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-slate-100">
                                <tr>
                                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Código</th>
                                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Producto</th>
                                    <th className="px-4 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider w-32">Cantidad</th>
                                    <th className="px-4 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider w-40">Precio Unit.</th>
                                    <th className="px-4 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider">Subtotal</th>
                                    <th className="px-4 py-3 text-center"></th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-100">
                                {items.length === 0 ? (
                                    <tr><td colSpan="6" className="text-center text-gray-400 py-8 italic">No hay productos seleccionados.</td></tr>
                                ) : (
                                    items.map((item) => (
                                        <tr key={item.producto_id} className="hover:bg-gray-50 transition-colors">
                                            <td className="px-4 py-2 font-mono text-sm text-gray-600">{item.codigo}</td>
                                            <td className="px-4 py-2 text-sm font-medium text-gray-800">{item.nombre}</td>
                                            <td className="px-4 py-2 text-right">
                                                <input type="number" value={item.cantidad} onChange={e => handleItemChange(item.producto_id, 'cantidad', e.target.value)} className="w-full px-2 py-1 border border-gray-300 rounded text-right focus:ring-2 focus:ring-blue-200 outline-none" min="0.01" step="any" />
                                            </td>
                                            <td className="px-4 py-2 text-right">
                                                <input type="number" step="0.01" value={item.precio_unitario} onChange={e => handleItemChange(item.producto_id, 'precio_unitario', e.target.value)} className="w-full px-2 py-1 border border-gray-300 rounded text-right focus:ring-2 focus:ring-blue-200 outline-none" min="0" />
                                            </td>
                                            <td className="px-4 py-2 text-right font-mono text-sm font-bold text-gray-700">
                                                ${((parseFloat(item.cantidad) || 0) * (parseFloat(item.precio_unitario) || 0)).toLocaleString('es-CO')}
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
                                    <tr>
                                        <td colSpan="4" className="px-4 py-3 text-right text-sm font-bold text-gray-600 uppercase">Total Factura:</td>
                                        <td className="px-4 py-3 text-right text-lg font-bold font-mono text-blue-600">
                                            ${totalFactura.toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                                        </td>
                                        <td></td>
                                    </tr>
                                </tfoot>
                            )}
                        </table>
                    </div>
                </div>

                {/* BOTÓN FINAL */}
                <div className="mt-8 flex justify-end">
                    <button
                        type="button" onClick={handleSubmit}
                        disabled={isSubmitting || items.length === 0 || !beneficiarioId || !tipoDocumentoId || (bodegaRequerida && !selectedBodegaId)}
                        className={`
                            px-10 py-4 rounded-xl shadow-lg font-bold text-white text-lg transition-all transform hover:-translate-y-1 flex items-center gap-3
                            ${isSubmitting || items.length === 0
                                ? 'bg-gray-400 cursor-not-allowed'
                                : 'bg-green-600 hover:bg-green-700 hover:shadow-green-200'}
                        `}
                    >
                        {isSubmitting ? (
                            <> <span className="loading loading-spinner"></span> Guardando... </>
                        ) : (
                            <> <FaSave className="text-xl" /> Crear Factura </>
                        )}
                    </button>
                </div>

                <ProductSelectionModal
                    isOpen={isModalOpen}
                    onClose={() => setIsModalOpen(false)}
                    onAddProducts={handleAddProducts}
                    mode="venta"
                    bodegaIdSeleccionada={bodegaRequerida ? (selectedBodegaId ? parseInt(selectedBodegaId) : null) : null}
                />

                {/* MODAL SELECCION REMISION */}
                {isRemisionModalOpen && (
                    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
                        <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
                            <div className="p-4 border-b flex justify-between items-center bg-gray-50">
                                <h3 className="text-xl font-bold text-gray-800">Seleccionar Remisión</h3>
                                <button onClick={() => setIsRemisionModalOpen(false)} className="text-gray-500 hover:text-red-500">
                                    <FaTrash className="transform rotate-45" /> Cerrar
                                </button>
                            </div>
                            <div className="p-4">
                                {remisionesDisponibles.length === 0 ? (
                                    <p className="text-center text-gray-500 py-8">No hay remisiones pendientes de facturar.</p>
                                ) : (
                                    <table className="min-w-full divide-y divide-gray-200">
                                        <thead className="bg-gray-100">
                                            <tr>
                                                <th className="px-4 py-2 text-left">Número</th>
                                                <th className="px-4 py-2 text-left">Fecha</th>
                                                <th className="px-4 py-2 text-left">Cliente</th>
                                                <th className="px-4 py-2 text-left">Bodega</th>
                                                <th className="px-4 py-2 text-center">Acción</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {remisionesDisponibles.map(r => (
                                                <tr key={r.id} className="hover:bg-blue-50">
                                                    <td className="px-4 py-2 font-bold">#{r.numero}</td>
                                                    <td className="px-4 py-2">{r.fecha}</td>
                                                    <td className="px-4 py-2">{r.tercero_nombre}</td>
                                                    <td className="px-4 py-2">{r.bodega_nombre}</td>
                                                    <td className="px-4 py-2 text-center">
                                                        <button
                                                            onClick={() => cargarRemision(r)}
                                                            className="bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-800 text-sm"
                                                        >
                                                            Cargar
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}