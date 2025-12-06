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
    FaBook
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

// --- Componentes ---
import BotonRegresar from '../../components/BotonRegresar';
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

    const [maestros, setMaestros] = useState({
        terceros: [],
        tiposDocumento: [],
        centrosCosto: [],
    });

    // Cálculo Memoizado
    const totalCompra = useMemo(() => {
        return items.reduce((acc, item) => acc + ((parseFloat(item.cantidad) || 0) * (parseFloat(item.costo_unitario) || 0)), 0);
    }, [items]);

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
                    tiposDocumento: tiposDocRes.filter(td => td.funcion_especial === 'cxp_proveedor'),
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
                        costo_unitario: newItem.costo_unitario
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
                    costo_unitario: costoNum
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
            items: itemsValidados
        };

        try {
            const response = await comprasService.createCompra(payload);
            toast.success(`¡Éxito! Compra #${response.numero} creada correctamente.`);
            setItems([]);
            setBeneficiarioId('');
            setNumeroManual('');
            setCentroCostoId('');
            setFechaVencimiento(null);
        } catch (err) {
            console.error("Error al guardar compra:", err);
            const errorMsg = err.response?.data?.detail || "Ocurrió un error inesperado al guardar la compra.";
            toast.error(`Error: ${errorMsg}`);
        } finally {
            setIsSubmitting(false);
        }
    };

    if (pageIsLoading || authLoading) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
                <FaShoppingCart className="text-green-300 text-6xl mb-4 animate-pulse" />
                <p className="text-green-600 font-semibold text-lg animate-pulse">Cargando módulo de compras...</p>
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
                        <BotonRegresar />
                        <div className="flex items-center gap-3 mt-3">
                            <div className="p-2 bg-green-100 rounded-lg text-green-600">
                                <FaShoppingCart className="text-2xl" />
                            </div>
                            <div>
                                <h1 className="text-3xl font-bold text-gray-800">Nueva Compra</h1>
                                <p className="text-gray-500 text-sm">Registro de facturas de proveedores e ingreso de inventario.</p>
                            </div>
                        </div>
                    </div>
                    <button
                        onClick={() => window.open('/manual?file=capitulo_40_compras.md', '_blank')}
                        className="btn btn-ghost btn-sm gap-2 text-green-600"
                    >
                        <FaBook /> Manual
                    </button>
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
                                            <td className="px-4 py-2 text-right font-mono text-sm font-bold text-gray-700">
                                                ${((parseFloat(item.cantidad) || 0) * (parseFloat(item.costo_unitario) || 0)).toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
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
                                        <td colSpan="4" className="px-4 py-3 text-right text-sm font-bold text-gray-600 uppercase">Total Compra:</td>
                                        <td className="px-4 py-3 text-right text-lg font-bold font-mono text-green-600">
                                            ${totalCompra.toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                                        </td>
                                        <td></td>
                                    </tr>
                                </tfoot>
                            )}
                        </table>
                    </div>
                </div>

                <div className="flex justify-end mt-8">
                    <button
                        type="button"
                        onClick={handleSubmit}
                        disabled={isSubmitting || items.length === 0 || !beneficiarioId || !tipoDocumentoId || !selectedBodegaId}
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
                            <> <FaSave className="text-xl" /> Guardar Compra </>
                        )}
                    </button>
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