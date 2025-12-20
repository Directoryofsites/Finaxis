'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { FaSave, FaPlus, FaTrash, FaCalendarAlt, FaUserTag, FaBoxOpen, FaWarehouse } from 'react-icons/fa';

import { useAuth } from '../../context/AuthContext';
import { apiService } from '../../../lib/apiService';


const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 text-sm outline-none";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 text-sm outline-none bg-white";

export default function CreateRemisionPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const curRemisionId = searchParams.get('remision_id');

    const { user } = useAuth();

    // Estados Header
    const [fecha, setFecha] = useState(new Date());
    const [fechaVencimiento, setFechaVencimiento] = useState(null);
    const [terceroId, setTerceroId] = useState('');
    const [bodegaId, setBodegaId] = useState('');
    const [observaciones, setObservaciones] = useState('');

    // Estados Detalle
    const [detalles, setDetalles] = useState([
        { rowId: Date.now(), productoId: '', cantidad: 1, precio: 0, productoInput: '', stockDisponible: null, stockTexto: '' }
    ]);

    // Maestros
    const [maestros, setMaestros] = useState({
        terceros: [],
        bodegas: [],
        productos: []
    });
    const [loading, setLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState('');
    const [mensaje, setMensaje] = useState('');

    useEffect(() => {
        if (!user?.empresaId) return;
        fetchMaestros();
    }, [user]);

    // Load Remission Data if Editing
    useEffect(() => {
        if (curRemisionId && maestros.productos.length > 0) {
            fetchRemisionData(curRemisionId);
        }
    }, [curRemisionId, maestros]); // Depend on maestros to correctly map products

    const fetchRemisionData = async (id) => {
        try {
            setLoading(true);
            const res = await apiService.get(`/remisiones/${id}`);
            const data = res.data;
            console.log("Remision Data Fetched:", data);

            // Populate Fields
            setFecha(new Date(data.fecha + 'T00:00:00'));
            setFechaVencimiento(data.fecha_vencimiento ? new Date(data.fecha_vencimiento + 'T00:00:00') : null);
            setTerceroId(data.tercero_id);
            setBodegaId(data.bodega_id);
            setObservaciones(data.observaciones || '');

            // Populate Detalles & Fetch Stocks Parallelly
            const mappedDetalles = await Promise.all(data.detalles.map(async (d) => {
                const prod = maestros.productos.find(p => p.id == d.producto_id);

                let stockInfo = { stockDisponible: null, stockTexto: '' };

                try {
                    // Fetch Stock inline
                    const stockRes = await apiService.get(`/inventario/productos/${d.producto_id}`);
                    const productoFull = stockRes.data;
                    const stockEntry = productoFull.stocks_bodega.find(sb => sb.bodega_id === Number(data.bodega_id));
                    const stockFisico = stockEntry ? stockEntry.stock_actual : 0;
                    const stockComprometido = stockEntry ? stockEntry.stock_comprometido || 0 : 0;
                    const stockDisponible = stockFisico - stockComprometido;

                    stockInfo = {
                        stockDisponible: stockDisponible,
                        stockTexto: `Disp: ${stockDisponible} (Fís: ${stockFisico} - Res: ${stockComprometido})`
                    };
                } catch (err) {
                    console.warn("Could not fetch stock for edit load", d.producto_id);
                }

                return {
                    rowId: Date.now() + Math.random(),
                    productoId: d.producto_id,
                    cantidad: d.cantidad_solicitada,
                    precio: d.precio_unitario,
                    productoInput: prod ? `${prod.codigo} - ${prod.nombre}` : `Producto ID ${d.producto_id}`,
                    ...stockInfo
                };
            }));

            // ONE State Update
            setDetalles(mappedDetalles);

        } catch (err) {
            console.error("Error loading remission", err);
            setError("No se pudo cargar la remisión para editar.");
        } finally {
            setLoading(false);
        }
    };

    const fetchMaestros = async () => {
        // ... existing fetchMaestros logic

        try {
            const [tercerosRes, bodegasRes, productosRes] = await Promise.all([
                apiService.get('/terceros/'),
                apiService.get('/bodegas/'),
                apiService.get('/inventario/productos/list-flat')
            ]);
            setMaestros({
                terceros: tercerosRes.data,
                bodegas: bodegasRes.data,
                productos: productosRes.data
            });
            // Set default bodega if user has access or first one
            if (bodegasRes.data.length > 0) setBodegaId(bodegasRes.data[0].id);
        } catch (err) {
            console.error("Error cargando maestros remisión", err);
            setError("Error cargando listas desplegables.");
        } finally {
            setLoading(false);
        }
    };

    const handleDetalleChange = (index, field, value) => {
        const newDetalles = [...detalles];
        newDetalles[index][field] = value;
        setDetalles(newDetalles);
    };

    const checkStock = async (index, productoId, currentBodegaId) => {
        if (!productoId || !currentBodegaId) return;
        try {
            // Fetch remote stock
            // We use the detail endpoint which returns stocks_bodega list
            const res = await apiService.get(`/inventario/productos/${productoId}`);
            const productoFull = res.data;

            const stockEntry = productoFull.stocks_bodega.find(sb => sb.bodega_id === Number(currentBodegaId));
            const stockFisico = stockEntry ? stockEntry.stock_actual : 0;
            const stockComprometido = stockEntry ? stockEntry.stock_comprometido || 0 : 0; // Assuming backend returns this now
            const stockDisponible = stockFisico - stockComprometido;

            setDetalles(prev => {
                const newDetalles = [...prev];
                // Safety: check if index exists (user might have deleted row while fetching)
                if (newDetalles[index]) {
                    newDetalles[index] = {
                        ...newDetalles[index],
                        stockDisponible: stockDisponible,
                        stockTexto: `Disp: ${stockDisponible} (Fís: ${stockFisico} - Res: ${stockComprometido})`
                    };
                }
                return newDetalles;
            });

        } catch (err) {
            console.error("Error fetching stock", err);
        }
    };

    const handleProductoBlur = (index, value) => {
        if (!value) return;
        const productoFound = maestros.productos.find(p =>
            p.codigo.toLowerCase() === value.toLowerCase() ||
            p.nombre.toLowerCase().includes(value.toLowerCase())
        );

        if (productoFound) {
            handleDetalleChange(index, 'productoId', productoFound.id);
            handleDetalleChange(index, 'productoInput', `${productoFound.codigo} - ${productoFound.nombre}`);
            handleDetalleChange(index, 'precio', productoFound.costo_promedio || 0);

            // Check Stock
            checkStock(index, productoFound.id, bodegaId);

        } else {
            handleDetalleChange(index, 'productoId', '');
        }
    };

    // Refresh stocks if Bodega changes
    useEffect(() => {
        if (!bodegaId) return;
        detalles.forEach((d, index) => {
            if (d.productoId) {
                checkStock(index, d.productoId, bodegaId);
            }
        });
    }, [bodegaId]);


    const agregarFila = () => {
        setDetalles([...detalles, { rowId: Date.now(), productoId: '', cantidad: 1, precio: 0, productoInput: '', stockDisponible: null, stockTexto: '' }]);
    };

    const eliminarFila = (index) => {
        if (detalles.length > 1) {
            setDetalles(detalles.filter((_, i) => i !== index));
        } else {
            // Reset last row instead of empty
            setDetalles([{ rowId: Date.now(), productoId: '', cantidad: 1, precio: 0, productoInput: '', stockDisponible: null, stockTexto: '' }]);
        }
    };

    const handleSubmit = async () => {
        if (!terceroId || !bodegaId) {
            setError("Debe seleccionar Cliente y Bodega.");
            return;
        }
        if (detalles.some(d => !d.productoId || d.cantidad <= 0)) {
            setError("Revise los productos. Todos deben ser válidos y tener cantidad > 0.");
            return;
        }

        setIsSubmitting(true);
        setError('');

        const payload = {
            fecha: fecha.toISOString().split('T')[0],
            fecha_vencimiento: fechaVencimiento ? fechaVencimiento.toISOString().split('T')[0] : null,
            tercero_id: parseInt(terceroId),
            bodega_id: parseInt(bodegaId),
            observaciones: observaciones,
            detalles: detalles.map(d => ({
                producto_id: parseInt(d.productoId),
                cantidad_solicitada: parseFloat(d.cantidad),
                precio_unitario: parseFloat(d.precio)
            }))
        };

        try {
            if (curRemisionId) {
                await apiService.put(`/remisiones/${curRemisionId}`, payload);
                setMensaje("Remisión actualizada exitosamente.");
            } else {
                await apiService.post('/remisiones/', payload);
                setMensaje("Remisión creada exitosamente.");
            }
            setTimeout(() => router.push('/remisiones'), 1500);
        } catch (err) {
            setError(err.response?.data?.detail || "Error al guardar la remisión.");
            setIsSubmitting(false);
        }
    };

    if (loading) return <div className="p-8">Cargando maestro de datos...</div>;

    return (
        <div className="p-6 max-w-7xl mx-auto">
            <div className="flex justify-between items-center mb-6">
                <div className="flex items-center gap-4">
                    <h1 className="text-2xl font-bold text-gray-800">{curRemisionId ? `Editar Remisión #${curRemisionId}` : 'Nueva Remisión'}</h1>
                </div>
                <button
                    onClick={handleSubmit}
                    disabled={isSubmitting}
                    className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 flex items-center gap-2 disabled:opacity-50 shadow-md"
                >
                    <FaSave /> Guardar Remisión
                </button>
            </div>

            {error && <div className="bg-red-100 text-red-700 p-4 rounded-lg mb-4 flex items-center"><span className="font-bold mr-2">Error:</span> {error}</div>}
            {mensaje && <div className="bg-green-100 text-green-700 p-4 rounded-lg mb-4 flex items-center"><span className="font-bold mr-2">Éxito:</span> {mensaje}</div>}

            {/* CABECERA */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div>
                        <label className="block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide">Fecha Emisión</label>
                        <div className="relative">
                            <DatePicker
                                selected={fecha}
                                onChange={(date) => setFecha(date)}
                                className={inputClass}
                                dateFormat="dd/MM/yyyy"
                            />
                            <FaCalendarAlt className="absolute right-3 top-3 text-gray-400" />
                        </div>
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide">Vencimiento (Opcional)</label>
                        <div className="relative">
                            <DatePicker
                                selected={fechaVencimiento}
                                onChange={(date) => setFechaVencimiento(date)}
                                className={inputClass}
                                dateFormat="dd/MM/yyyy"
                                placeholderText="Sin vencimiento"
                            />
                            <FaCalendarAlt className="absolute right-3 top-3 text-gray-400" />
                        </div>
                    </div>
                    <div className="col-span-2">
                        <label className="block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide">Cliente / Tercero</label>
                        <div className="relative">
                            <select
                                value={terceroId}
                                onChange={(e) => setTerceroId(e.target.value)}
                                className={selectClass}
                            >
                                <option value="">Seleccione un cliente...</option>
                                {maestros.terceros.map(t => (
                                    <option key={t.id} value={t.id}>{t.numero_identificacion} - {t.razon_social}</option>
                                ))}
                            </select>
                            <FaUserTag className="absolute right-8 top-3 text-gray-400 pointer-events-none" />
                        </div>
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide">Bodega Origen</label>
                        <div className="relative">
                            <select
                                value={bodegaId}
                                onChange={(e) => setBodegaId(e.target.value)}
                                className={selectClass}
                            >
                                <option value="">Seleccione Bodega...</option>
                                {maestros.bodegas.map(b => (
                                    <option key={b.id} value={b.id}>{b.codigo} - {b.nombre}</option>
                                ))}
                            </select>
                            <FaWarehouse className="absolute right-8 top-3 text-gray-400 pointer-events-none" />
                        </div>
                    </div>
                    <div className="col-span-3">
                        <label className="block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide">Observaciones</label>
                        <input
                            type="text"
                            className={inputClass}
                            placeholder="Notas internas sobre esta remisión..."
                            value={observaciones}
                            onChange={(e) => setObservaciones(e.target.value)}
                        />
                    </div>
                </div>
            </div>

            {/* DETALLES */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="p-4 bg-gray-50 border-b border-gray-200 flex justify-between items-center">
                    <h3 className="font-bold text-gray-700 flex items-center gap-2">
                        <FaBoxOpen /> Productos a Comprometer
                    </h3>
                    <button onClick={agregarFila} className="text-indigo-600 hover:text-indigo-800 text-sm font-semibold flex items-center gap-1">
                        <FaPlus /> Agregar Producto
                    </button>
                </div>

                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/2">Producto</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-24">Cant.</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">Precio Unit.</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">Total</th>
                            <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-16"></th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {detalles.map((det, index) => (
                            <tr key={det.rowId}>
                                <td className="px-4 py-2">
                                    <input
                                        list="productos-list"
                                        className="w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                                        value={det.productoInput}
                                        onChange={(e) => handleDetalleChange(index, 'productoInput', e.target.value)}
                                        onBlur={(e) => handleProductoBlur(index, e.target.value)}
                                        placeholder="Buscar código o nombre..."
                                    />
                                    {det.stockTexto && (
                                        <div className={`text-xs mt-1 ${det.stockDisponible < det.cantidad ? 'text-red-500 font-bold' : 'text-green-600'}`}>
                                            {det.stockTexto}
                                        </div>
                                    )}
                                </td>
                                <td className="px-4 py-2">
                                    <input
                                        type="number"
                                        min="0.01"
                                        step="0.01"
                                        className="w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm text-right"
                                        value={det.cantidad}
                                        onChange={(e) => handleDetalleChange(index, 'cantidad', e.target.value)}
                                    />
                                </td>
                                <td className="px-4 py-2">
                                    <input
                                        type="number"
                                        className="w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm text-right"
                                        value={det.precio}
                                        onChange={(e) => handleDetalleChange(index, 'precio', e.target.value)}
                                    />
                                </td>
                                <td className="px-4 py-2 text-right font-medium text-gray-700">
                                    {((parseFloat(det.cantidad) || 0) * (parseFloat(det.precio) || 0)).toLocaleString('es-CO', { style: 'currency', currency: 'COP' })}
                                </td>
                                <td className="px-4 py-2 text-center">
                                    <button onClick={() => eliminarFila(index)} className="text-red-500 hover:text-red-700">
                                        <FaTrash />
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                <datalist id="productos-list">
                    {maestros.productos.map(p => (
                        <option key={p.id} value={p.codigo}>{`${p.codigo} - ${p.nombre}`}</option>
                    ))}
                </datalist>
            </div>
        </div>
    );
}
