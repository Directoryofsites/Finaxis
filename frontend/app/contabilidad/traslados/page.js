'use client';

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { 
  FaTruckMoving, 
  FaSave, 
  FaPlus, 
  FaCalendarAlt, 
  FaExchangeAlt, 
  FaTrash,
  FaBook, 
  FaWarehouse,
  FaArrowRight,
  FaCommentDots
} from 'react-icons/fa';

import { useAuth } from '../../context/AuthContext';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// --- Servicios ---
import { getBodegas } from '../../../lib/bodegaService'; // Ajuste de importación correcto
import { getTiposDocumento } from '../../../lib/tiposDocumentoService';
import trasladoService from '../../../lib/trasladoInventarioService'; 
import BotonRegresar from '../../components/BotonRegresar';
import ProductSelectionModal from '../../components/Facturacion/ProductSelectionModal';

// Estilos Reusables (Manual v2.0)
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none pl-10";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white pl-10";

export default function NuevoTrasladoPage() {
    const router = useRouter();
    const { user, loading: authLoading } = useAuth();

    // Estados del Formulario
    const [fecha, setFecha] = useState(new Date());
    const [tipoDocumentoId, setTipoDocumentoId] = useState('');
    const [bodegaOrigenId, setBodegaOrigenId] = useState('');
    const [bodegaDestinoId, setBodegaDestinoId] = useState('');
    const [observaciones, setObservaciones] = useState('');
    const [items, setItems] = useState([]);

    const [pageIsLoading, setPageIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isModalOpen, setIsModalOpen] = useState(false);

    const [maestros, setMaestros] = useState({
        tiposDocumento: [],
        bodegas: [],
    });

    const totalCantidad = useMemo(() => {
        return items.reduce((acc, item) => acc + (parseFloat(item.cantidad) || 0), 0);
    }, [items]);
    
    const TR_DOC_ID = useMemo(() => {
        const trasladoDoc = maestros.tiposDocumento.find(td => td.funcion_especial === 'traslado_inventario');
        return trasladoDoc ? String(trasladoDoc.id) : '';
    }, [maestros.tiposDocumento]);

    useEffect(() => {
        if (TR_DOC_ID && tipoDocumentoId === '') {
            setTipoDocumentoId(TR_DOC_ID);
        }
    }, [TR_DOC_ID, tipoDocumentoId]);

    const fetchMaestros = useCallback(async () => {
        try {
            const [tiposDocRes, bodegasRes] = await Promise.all([
                getTiposDocumento(),
                getBodegas()
            ]);

            setMaestros({
                tiposDocumento: tiposDocRes.filter(td => td.funcion_especial === 'traslado_inventario'), 
                bodegas: bodegasRes,
            });

            if (bodegasRes.length > 0 && bodegaOrigenId === '') {
                setBodegaOrigenId(String(bodegasRes[0].id));
            }
        } catch (err) {
            const errorMsg = err.response?.data?.detail || 'Error al cargar datos maestros.';
            toast.error(errorMsg);
        } finally {
            setPageIsLoading(false);
        }
    }, [bodegaOrigenId]);

    useEffect(() => {
        if (authLoading) return;
        if (!user) {
            router.push('/login');
            return;
        }
        fetchMaestros();
    }, [user, authLoading, router, fetchMaestros]);


    const handleAddProducts = (newItems) => {
        setItems(prevItems => {
            const updatedItems = [...prevItems];
            newItems.forEach(newItem => {
                const existingIndex = updatedItems.findIndex(i => i.producto_id === newItem.producto_id);
                if (existingIndex > -1) {
                    updatedItems[existingIndex] = {
                        ...updatedItems[existingIndex],
                        cantidad: updatedItems[existingIndex].cantidad + newItem.cantidad,
                    };
                } else {
                    updatedItems.push({
                        producto_id: newItem.id || newItem.producto_id,
                        codigo: newItem.codigo,
                        nombre: newItem.nombre,
                        cantidad: newItem.cantidad || 1,
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
            item.producto_id === productId ? { ...item, [field]: numericValue } : item
        ));
    };

    const handleRemoveItem = (productId) => {
        setItems(prev => prev.filter(item => item.producto_id !== productId));
    };

    const handleSwapBodegas = () => {
        const temp = bodegaOrigenId;
        setBodegaOrigenId(bodegaDestinoId);
        setBodegaDestinoId(temp);
    };

    const handleSubmit = async () => {
        if (!TR_DOC_ID) return toast.error("Documento de Traslado (TR) no encontrado.");
        if (!bodegaOrigenId) return toast.error("Seleccione la Bodega de Origen.");
        if (!bodegaDestinoId) return toast.error("Seleccione la Bodega de Destino.");
        if (bodegaOrigenId === bodegaDestinoId) return toast.error("Origen y Destino no pueden ser iguales.");
        if (items.length === 0) return toast.error("Añada al menos un producto.");

        const itemsValidados = items.map(item => ({
            producto_id: parseInt(item.producto_id),
            cantidad: parseFloat(item.cantidad) || 0
        }));

        if (itemsValidados.some(item => item.cantidad <= 0)) {
            return toast.error("Las cantidades deben ser mayores a 0.");
        }

        setIsSubmitting(true);

        const payload = {
            tipo_documento_id: parseInt(TR_DOC_ID),
            bodega_origen_id: parseInt(bodegaOrigenId),
            bodega_destino_id: parseInt(bodegaDestinoId),
            fecha: fecha.toISOString().split('T')[0],
            observaciones: observaciones || null,
            items: itemsValidados
        };

        try {
            const response = await trasladoService.createTraslado(payload);
            toast.success(`¡Éxito! Traslado #${response.numero} registrado.`);
            setItems([]);
            setObservaciones('');
        } catch (err) {
            console.error("Error al guardar traslado:", err);
            const errorMsg = err.response?.data?.detail || "Error al registrar el traslado.";
            toast.error(`Error: ${errorMsg}`);
        } finally {
            setIsSubmitting(false);
        }
    };

    if (pageIsLoading || authLoading) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
                <FaTruckMoving className="text-indigo-300 text-6xl mb-4 animate-pulse" />
                <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando logística...</p>
            </div>
        );
    }
    
    const bodegasOtras = maestros.bodegas.filter(b => String(b.id) !== bodegaOrigenId);

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
            <div className="max-w-5xl mx-auto">
                <ToastContainer position="top-right" autoClose={5000} />

                
                {/* ENCABEZADO */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                    <div>

                        <div className="flex items-center gap-3 mb-3">
                            
                            {/* 1. Botón Regresar (Izquierda) */}
                            <BotonRegresar />

                            {/* 2. Botón Manual (Derecha) */}
                            <button
                                onClick={() => window.open('/manual?file=capitulo_42_traslados.md', '_blank')}
                                className="text-indigo-600 hover:bg-indigo-50 px-3 py-1 rounded-md flex items-center gap-2 transition-colors font-bold text-sm"
                                type="button"
                            >
                                <FaBook className="text-lg" /> Manual
                            </button>

                        </div>


                        <div className="flex items-center gap-3 mt-3">
                            <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                                <FaTruckMoving className="text-2xl" />
                            </div>
                            <div>
                                <h1 className="text-3xl font-bold text-gray-800">Traslado de Inventario</h1>
                                <p className="text-gray-500 text-sm">Movimiento de mercancía entre bodegas.</p>
                            </div>
                        </div>
                    </div>
                </div>


                {/* CARD 1: LOGÍSTICA */}
                <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 animate-fadeIn mb-8">
                    
                    {/* Fecha */}
                    <div className="mb-6 w-full md:w-1/3">
                        <label htmlFor="fecha" className={labelClass}>Fecha Traslado</label>
                        <div className="relative">
                            <DatePicker
                                selected={fecha}
                                onChange={(date) => setFecha(date || new Date())}
                                dateFormat="dd/MM/yyyy"
                                className={inputClass}
                            />
                            <FaCalendarAlt className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                        </div>
                    </div>

                    {/* ZONA DE INTERCAMBIO */}
                    <div className="flex flex-col md:flex-row items-center justify-between gap-4 bg-slate-50 p-6 rounded-xl border border-slate-200 relative">
                        
                        {/* Origen */}
                        <div className="w-full md:w-5/12">
                            <label className="block text-xs font-bold text-red-600 uppercase mb-1 tracking-wide">Bodega Origen (Salida)</label>
                            <div className="relative">
                                <select
                                    value={bodegaOrigenId} 
                                    onChange={e => setBodegaOrigenId(e.target.value)}
                                    className={`${selectClass} border-red-200 bg-red-50 text-red-800 font-medium`}
                                >
                                    <option value="">Seleccione Origen...</option>
                                    {maestros.bodegas.map(b => <option key={b.id} value={String(b.id)}>{b.nombre}</option>)}
                                </select>
                                <FaWarehouse className="absolute left-3 top-3 text-red-400 pointer-events-none" />
                            </div>
                        </div>

                        {/* Flecha / Swap */}
                        <div className="flex items-center justify-center w-full md:w-2/12 py-2 md:py-0">
                            <button 
                                onClick={handleSwapBodegas} 
                                className="p-3 bg-white border border-gray-300 rounded-full shadow-sm hover:shadow-md hover:bg-indigo-50 text-indigo-600 transition-all transform hover:rotate-180"
                                title="Intercambiar Bodegas"
                                disabled={!bodegaOrigenId && !bodegaDestinoId}
                            >
                                <FaExchangeAlt />
                            </button>
                        </div>

                        {/* Destino */}
                        <div className="w-full md:w-5/12">
                            <label className="block text-xs font-bold text-green-600 uppercase mb-1 tracking-wide">Bodega Destino (Entrada)</label>
                            <div className="relative">
                                <select
                                    value={bodegaDestinoId} 
                                    onChange={e => setBodegaDestinoId(e.target.value)}
                                    className={`${selectClass} border-green-200 bg-green-50 text-green-800 font-medium`}
                                >
                                    <option value="">Seleccione Destino...</option>
                                    {bodegasOtras.map(b => <option key={b.id} value={String(b.id)}>{b.nombre}</option>)}
                                </select>
                                <FaWarehouse className="absolute left-3 top-3 text-green-400 pointer-events-none" />
                            </div>
                        </div>
                    </div>

                    {/* Observaciones */}
                    <div className="mt-6">
                        <label htmlFor="observaciones" className={labelClass}>Observaciones</label>
                        <div className="relative">
                            <input
                                type="text" id="observaciones" value={observaciones} onChange={e => setObservaciones(e.target.value)}
                                className={inputClass}
                                maxLength="255" 
                                placeholder="Motivo del traslado..."
                            />
                            <FaCommentDots className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                        </div>
                    </div>
                </div>

                {/* CARD 2: ITEMS */}
                <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 animate-slideDown">
                    <div className="flex justify-between items-center mb-4 border-b border-gray-100 pb-2">
                        <h2 className="text-lg font-bold text-gray-700 flex items-center gap-2">
                            <span className="bg-indigo-100 text-indigo-600 w-6 h-6 flex items-center justify-center rounded-full text-xs">2</span> 
                            Mercancía a Mover
                        </h2>
                        <button
                            type="button" onClick={() => setIsModalOpen(true)}
                            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 shadow-md flex items-center gap-2 transition-colors disabled:bg-gray-300"
                            disabled={!bodegaOrigenId || !bodegaDestinoId} 
                        >
                            <FaPlus /> Añadir Productos
                        </button>
                    </div>

                    <div className="overflow-hidden rounded-lg border border-gray-200">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-slate-100">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Código</th>
                                    <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Producto</th>
                                    <th className="px-6 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider w-40">Cantidad</th>
                                    <th className="px-6 py-3 text-center"></th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-100">
                                {items.length === 0 ? (
                                    <tr><td colSpan="4" className="text-center text-gray-400 py-8 italic">Seleccione la bodega de origen para cargar el inventario disponible.</td></tr>
                                ) : (
                                    items.map((item) => (
                                        <tr key={item.producto_id} className="hover:bg-gray-50 transition-colors">
                                            <td className="px-6 py-3 text-sm font-mono text-gray-600">{item.codigo}</td>
                                            <td className="px-6 py-3 text-sm font-medium text-gray-800">{item.nombre}</td>
                                            <td className="px-6 py-3 text-right">
                                                <input
                                                    type="number" value={item.cantidad}
                                                    onChange={e => handleItemChange(item.producto_id, 'cantidad', e.target.value)}
                                                    className="w-full px-2 py-1 border border-gray-300 rounded text-right focus:ring-2 focus:ring-indigo-200 outline-none font-bold text-indigo-700"
                                                    min="0.01" step="any" 
                                                />
                                            </td>
                                            <td className="px-6 py-3 text-center">
                                                <button onClick={() => handleRemoveItem(item.producto_id)} className="text-red-400 hover:text-red-600 p-1.5 rounded-full hover:bg-red-50 transition-colors"><FaTrash /></button>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                            {items.length > 0 && (
                                <tfoot className="bg-slate-50 border-t-2 border-slate-200">
                                    <tr>
                                        <td colSpan="2" className="px-6 py-3 text-right text-sm font-bold text-gray-600 uppercase">Total Unidades:</td>
                                        <td className="px-6 py-3 text-right text-lg font-mono font-bold text-indigo-600">
                                            {totalCantidad.toLocaleString('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                        </td>
                                        <td></td>
                                    </tr>
                                </tfoot>
                            )}
                        </table>
                    </div>
                </div>

                {/* BOTÓN FINAL */}
                <div className="flex justify-end mt-8">
                    <button
                        type="button" onClick={handleSubmit}
                        disabled={isSubmitting || items.length === 0 || !bodegaOrigenId || !bodegaDestinoId}
                        className={`
                            px-10 py-4 rounded-xl shadow-lg font-bold text-white text-lg transition-all transform hover:-translate-y-1 flex items-center gap-3
                            ${isSubmitting || items.length === 0 
                                ? 'bg-gray-400 cursor-not-allowed' 
                                : 'bg-green-600 hover:bg-green-700 hover:shadow-green-200'}
                        `}
                    >
                        {isSubmitting ? (
                            <> <span className="loading loading-spinner"></span> Procesando... </>
                        ) : (
                            <> <FaSave className="text-xl" /> Confirmar Traslado </>
                        )}
                    </button>
                </div>

                <ProductSelectionModal
                    isOpen={isModalOpen}
                    onClose={() => setIsModalOpen(false)}
                    onAddProducts={handleAddProducts}
                    mode="traslado" 
                    bodegaIdSeleccionada={parseInt(bodegaOrigenId) || null} 
                />
            </div>
        </div>
    );
}