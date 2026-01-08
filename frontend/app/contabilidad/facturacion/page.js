'use client';

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import {
    FaFileInvoiceDollar,
    FaBook,
    FaListOl,
    FaCalendarAlt,
    FaWarehouse,
    FaUserTag,
    FaMoneyBillWave,
    FaBuilding,
    FaPlus,
    FaTrash,
    FaSave,
    FaTag
} from 'react-icons/fa';

import { useAuth } from '../../context/AuthContext';
import ProductSelectionModal from '../../components/Facturacion/ProductSelectionModal';
import TerceroSelect from '../../components/Inputs/TerceroSelect';

import { getBodegas } from '../../../lib/bodegaService';
import { getTiposDocumento } from '../../../lib/tiposDocumentoService';
import { getCentrosCosto } from '../../../lib/centrosCostoService';
import { getTerceroById } from '../../../lib/terceroService';
import facturacionService from '../../../lib/facturacionService';
import { apiService } from '../../../lib/apiService';

// Estilos reusables
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

    // --- CAMBIO: Manejo de Beneficiario con Objeto ---
    const [beneficiarioId, setBeneficiarioId] = useState('');
    const [beneficiarioOption, setBeneficiarioOption] = useState(null); // {value: id, label: string}
    // ------------------------------------------------

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

    // --- NUEVO: ESTADOS PARA COTIZACIÓN ---
    const [cotizacionId, setCotizacionId] = useState(null);
    const [isCotizacionModalOpen, setIsCotizacionModalOpen] = useState(false);
    const [cotizacionesDisponibles, setCotizacionesDisponibles] = useState([]);
    // -------------------------------------

    const [clienteListaPrecioId, setClienteListaPrecioId] = useState(null);

    const [pageIsLoading, setPageIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isModalOpen, setIsModalOpen] = useState(false);

    const [maestros, setMaestros] = useState({
        // terceros: [], // YA NO CARGAMOS TODOS LOS TERCEROS AL INICIO
        tiposDocumento: [],
        centrosCosto: [],
        productos: [],
    });

    const { subtotalGeneral, ivaGeneral, totalGeneral } = useMemo(() => {
        const result = items.reduce((acc, item) => {
            const cantidad = parseFloat(item.cantidad) || 0;
            const precio = parseFloat(item.precio_unitario) || 0;
            const subtotalItem = cantidad * precio;
            const ivaItem = subtotalItem * (item.porcentaje_iva || 0);

            acc.subtotal += subtotalItem;
            acc.iva += ivaItem;
            return acc;
        }, { subtotal: 0, iva: 0 });

        return {
            subtotalGeneral: result.subtotal,
            ivaGeneral: result.iva,
            totalGeneral: result.subtotal + result.iva
        };
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
                // YA NO LLAMAMOS A getTerceros() AQUÍ PARA OPTIMIZAR
                const [tiposDocRes, centrosCostoRes, bodegasRes, productosRes] = await Promise.all([
                    getTiposDocumento(),
                    getCentrosCosto(),
                    getBodegas(),
                    apiService.get('/inventario/productos/list-flat')
                ]);

                // --- FILTRO ESTRUCTURAL: SOLO HIJOS ---
                const centrosCostoFiltrados = centrosCostoRes.filter(c => c.permite_movimiento);

                setMaestros({
                    // terceros: tercerosRes,
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


    // --- CAMBIO: Handler para el AsyncSelect ---
    const handleBeneficiarioChange = useCallback(async (selectedOption) => {
        setBeneficiarioOption(selectedOption);
        const selectedId = selectedOption ? selectedOption.value : '';
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
    // -------------------------------------------


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
        }

        // 2. Cargar Datos Cabecera
        // ACTUALIZACIÓN PARA ASYNC SELECT
        setBeneficiarioId(rem.tercero_id);
        setBeneficiarioOption({ value: rem.tercero_id, label: rem.tercero_nombre }); // Construimos la opción visual

        setSelectedBodegaId(String(rem.bodega_id));
        setRemisionId(rem.id);
        setCotizacionId(null);

        // 3. Cargar Detalles
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
                    precio_unitario: d.precio_unitario,
                    porcentaje_iva: producto ? (producto.porcentaje_iva || 0) : 0
                };
            });

        setItems(nuevosItems);
        setIsRemisionModalOpen(false);
        // Disparar carga de lista de precios si es necesario (el useEffect lo haría si dependiera de beneficiarioId, 
        // pero handleBeneficiarioChange lo hace manual. Aquí deberíamos quizás llamar logicamente o confiar en que el usuario ya tiene precio)
        // Por seguridad, llamamos al check de lista de precios simulando el cambio
        handleBeneficiarioChange({ value: rem.tercero_id, label: rem.tercero_nombre });

        toast.success(`Remisión #${rem.numero} cargada.`);
    };

    // --- LÓGICA DE COTIZACIONES ---
    const handleOpenCotizacionModal = useCallback(async () => {
        try {
            setCotizacionesDisponibles([]);
            const res = await apiService.get('/cotizaciones/', {
                params: { estado: 'APROBADA' }
            });
            setCotizacionesDisponibles(res.data.cotizaciones);
            setIsCotizacionModalOpen(true);
        } catch (error) {
            console.error("Error fetching cotizaciones:", error);
            toast.error("No se pudieron cargar las cotizaciones disponibles.");
        }
    }, []);

    const cargarCotizacion = (cot) => {
        // 1. Validar Bodega (si aplica)
        if (cot.bodega_id) {
            const bodegaExiste = bodegas.some(b => b.id === cot.bodega_id);
            if (bodegaExiste) setSelectedBodegaId(String(cot.bodega_id));
        }

        // 2. Cargar Datos
        // ACTUALIZACIÓN PARA ASYNC SELECT
        setBeneficiarioId(cot.tercero_id);
        setBeneficiarioOption({ value: cot.tercero_id, label: cot.tercero_nombre });

        setCotizacionId(cot.id);
        setRemisionId(null);
        setCondicionPago('Crédito')

        // 3. Items
        const nuevosItems = cot.detalles.map(d => {
            const producto = maestros.productos.find(p => p.id === d.producto_id);
            return {
                producto_id: d.producto_id,
                codigo: producto ? producto.codigo : d.producto_id,
                nombre: producto ? producto.nombre : `Producto ID ${d.producto_id}`,
                cantidad: d.cantidad,
                precio_unitario: d.precio_unitario,
                porcentaje_iva: producto ? (producto.porcentaje_iva || 0) : 0
            };
        });

        setItems(nuevosItems);
        setIsCotizacionModalOpen(false);
        // Validar lista de precios logicamente
        handleBeneficiarioChange({ value: cot.tercero_id, label: cot.tercero_nombre });

        toast.success(`Cotización #${cot.numero} cargada.`);
    };
    // ------------------------------------
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
            cotizacion_id: cotizacionId ? parseInt(cotizacionId) : null,
            items: itemsValidados
        };

        try {
            const response = await facturacionService.createFactura(payload);
            toast.success(`¡Éxito! Factura #${response.numero} creada.`);
            setItems([]);
            // setBeneficiarioId(''); // MANTENER CLIENTE SELECCIONADO PARA FACTURACIÓN RÁPIDA
            // setCentroCostoId(''); // MANTENER CENTRO DE COSTO SELECCIONADO (Request usuario)
            // setClienteListaPrecioId(null); // MANTENER LISTA DE PRECIOS
            // setFecha(new Date()); // MANTENER FECHA SELECCIONADA (Request usuario: desatraso de contabilidad)
            // setFechaVencimiento(new Date()); // MANTENER FECHA VENCIMIENTO

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
                {/* ENCABEZADO */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                    <div>
                        {/* 2. TÍTULO E ICONO */}
                        <div className="flex items-center gap-3 mt-3">
                            <div className="p-2 bg-blue-100 rounded-lg text-blue-600">
                                <FaFileInvoiceDollar className="text-2xl" />
                            </div>
                            <div>
                                <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-3">
                                    Nueva Factura
                                    <button
                                        onClick={() => window.open('/manual/capitulo_41_facturacion.html', '_blank')}
                                        className="text-indigo-600 hover:bg-indigo-50 px-2 py-1 rounded-md flex items-center gap-2 transition-colors font-bold text-sm border border-indigo-100 shadow-sm"
                                        type="button"
                                    >
                                        <FaBook className="text-lg" /> <span className="hidden md:inline">Manual</span>
                                    </button>
                                </h1>
                                <p className="text-gray-500 text-sm">Gestión de ventas y salida de inventario.</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* BOTÓN CARGAR REMISIÓN Y COTIZACIÓN */}
                <div className="flex justify-end mb-4 gap-2">
                    <button
                        onClick={handleOpenCotizacionModal}
                        className="bg-blue-600 text-white px-4 py-2 rounded-lg shadow hover:bg-blue-700 flex items-center gap-2 font-bold transition-colors"
                    >
                        <FaListOl /> Cargar Cotización
                    </button>
                    <button
                        onClick={handleOpenRemisionModal}
                        className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg shadow-sm hover:bg-gray-300 flex items-center gap-2 font-bold transition-colors"
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

                        {/* Cliente - Async Search */}
                        <div className="lg:col-span-1">
                            <label htmlFor="beneficiario" className={labelClass}>Cliente <span className="text-red-500">*</span></label>
                            <div className="relative z-50">
                                <TerceroSelect
                                    value={beneficiarioOption}
                                    onChange={handleBeneficiarioChange}
                                />
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

                                        <td colSpan="4" className="px-4 py-2 text-right text-sm font-bold text-gray-500 uppercase">Subtotal:</td>
                                        <td className="px-4 py-2 text-right text-base font-medium text-gray-700">
                                            ${subtotalGeneral.toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                                        </td>
                                        <td></td>
                                    </tr>
                                    <tr>
                                        <td colSpan="4" className="px-4 py-2 text-right text-sm font-bold text-gray-500 uppercase">IVA:</td>
                                        <td className="px-4 py-2 text-right text-base font-medium text-gray-700">
                                            ${ivaGeneral.toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                                        </td>
                                        <td></td>
                                    </tr>
                                    <tr className="bg-blue-50">
                                        <td colSpan="4" className="px-4 py-3 text-right text-sm font-bold text-gray-800 uppercase border-t border-blue-200">Total Factura:</td>
                                        <td className="px-4 py-3 text-right text-xl font-bold font-mono text-blue-700 border-t border-blue-200">
                                            ${totalGeneral.toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
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
                        <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto p-6">
                            <div className="flex justify-between items-center mb-6 border-b pb-2">
                                <h3 className="text-xl font-bold text-gray-800">Seleccionar Remisión</h3>
                                <button onClick={() => setIsRemisionModalOpen(false)} className="text-gray-500 hover:text-gray-700"><FaTrash className="transform rotate-45" /></button>
                            </div>

                            <div className="overflow-x-auto">
                                <table className="min-w-full divide-y divide-gray-200">
                                    <thead className="bg-gray-50">
                                        <tr>
                                            <th className="px-4 py-2 text-left text-xs font-bold text-gray-500 uppercase">Número</th>
                                            <th className="px-4 py-2 text-left text-xs font-bold text-gray-500 uppercase">Fecha</th>
                                            <th className="px-4 py-2 text-left text-xs font-bold text-gray-500 uppercase">Cliente</th>
                                            <th className="px-4 py-2 text-left text-xs font-bold text-gray-500 uppercase">Bodega</th>
                                            <th className="px-4 py-2 text-center text-xs font-bold text-gray-500 uppercase">Acción</th>
                                        </tr>
                                    </thead>
                                    <tbody className="bg-white divide-y divide-gray-200">
                                        {remisionesDisponibles.length === 0 ? (
                                            <tr><td colSpan="5" className="text-center py-4">No hay remisiones disponibles.</td></tr>
                                        ) : (
                                            remisionesDisponibles.map(rem => (
                                                <tr key={rem.id} className="hover:bg-gray-50">
                                                    <td className="px-4 py-2 font-bold">#{rem.numero}</td>
                                                    <td className="px-4 py-2">{rem.fecha}</td>
                                                    <td className="px-4 py-2">{rem.tercero_nombre}</td>
                                                    <td className="px-4 py-2">{rem.bodega_nombre}</td>
                                                    <td className="px-4 py-2 text-center">
                                                        <button onClick={() => cargarRemision(rem)} className="bg-blue-100 text-blue-700 px-3 py-1 rounded hover:bg-blue-200 text-sm font-bold">
                                                            Cargar
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                )}

                {/* MODAL SELECCION COTIZACION */}
                {isCotizacionModalOpen && (
                    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
                        <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto p-6">
                            <div className="flex justify-between items-center mb-6 border-b pb-2">
                                <h3 className="text-xl font-bold text-gray-800">Seleccionar Cotización</h3>
                                <button onClick={() => setIsCotizacionModalOpen(false)} className="text-gray-500 hover:text-gray-700"><FaTrash className="transform rotate-45" /></button>
                            </div>

                            <div className="overflow-x-auto">
                                <table className="min-w-full divide-y divide-gray-200">
                                    <thead className="bg-gray-50">
                                        <tr>
                                            <th className="px-4 py-2 text-left text-xs font-bold text-gray-500 uppercase">Número</th>
                                            <th className="px-4 py-2 text-left text-xs font-bold text-gray-500 uppercase">Fecha</th>
                                            <th className="px-4 py-2 text-left text-xs font-bold text-gray-500 uppercase">Cliente</th>
                                            <th className="px-4 py-2 text-right text-xs font-bold text-gray-500 uppercase">Total</th>
                                            <th className="px-4 py-2 text-center text-xs font-bold text-gray-500 uppercase">Acción</th>
                                        </tr>
                                    </thead>
                                    <tbody className="bg-white divide-y divide-gray-200">
                                        {cotizacionesDisponibles.length === 0 ? (
                                            <tr><td colSpan="5" className="text-center py-4">No hay cotizaciones aprobadas disponibles.</td></tr>
                                        ) : (
                                            cotizacionesDisponibles.map(cot => (
                                                <tr key={cot.id} className="hover:bg-gray-50">
                                                    <td className="px-4 py-2 font-bold">#{cot.numero}</td>
                                                    <td className="px-4 py-2">{cot.fecha}</td>
                                                    <td className="px-4 py-2">{cot.tercero_nombre}</td>
                                                    <td className="px-4 py-2 text-right">{(cot.total_estimado || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP' })}</td>
                                                    <td className="px-4 py-2 text-center">
                                                        <button onClick={() => cargarCotizacion(cot)} className="bg-blue-100 text-blue-700 px-3 py-1 rounded hover:bg-blue-200 text-sm font-bold">
                                                            Cargar
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
