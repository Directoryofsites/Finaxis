'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { FaSave, FaPlus, FaTrash, FaCalendarAlt, FaUserTag, FaBoxOpen, FaCheckCircle, FaPrint } from 'react-icons/fa';

import { useAuth } from '../../context/AuthContext';
import { apiService } from '../../../lib/apiService';

import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 text-sm outline-none";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 text-sm outline-none bg-white";

export default function CreateCotizacionPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const curCotizacionId = searchParams.get('cotizacion_id');

    const { user } = useAuth();

    // Estados Header
    const [fecha, setFecha] = useState(new Date());
    const [fechaVencimiento, setFechaVencimiento] = useState(null);
    const [terceroId, setTerceroId] = useState('');
    const [bodegaId, setBodegaId] = useState(''); // Opcional, pero útil si se quiere sugerir
    const [observaciones, setObservaciones] = useState('');
    const [estado, setEstado] = useState('BORRADOR');

    // Estados Detalle
    const [detalles, setDetalles] = useState([
        { rowId: Date.now(), productoId: '', cantidad: 1, precio: 0, productoInput: '' }
    ]);

    // Maestros
    const [maestros, setMaestros] = useState({
        terceros: [],
        bodegas: [], // Para referencial
        productos: []
    });
    const [loading, setLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        if (!user?.empresaId) return;
        fetchMaestros();
    }, [user]);

    // Load Cotizacion Data if Editing
    useEffect(() => {
        if (curCotizacionId && maestros.productos.length > 0) {
            fetchCotizacionData(curCotizacionId);
        }
    }, [curCotizacionId, maestros]);

    const fetchCotizacionData = async (id) => {
        try {
            setLoading(true);
            const res = await apiService.get(`/cotizaciones/${id}`);
            const data = res.data;

            setEstado(data.estado);
            setFecha(new Date(data.fecha + 'T00:00:00'));
            setFechaVencimiento(data.fecha_vencimiento ? new Date(data.fecha_vencimiento + 'T00:00:00') : null);
            setTerceroId(data.tercero_id);
            setBodegaId(data.bodega_id || '');
            setObservaciones(data.observaciones || '');

            const mappedDetalles = data.detalles.map((d) => {
                const prod = maestros.productos.find(p => p.id == d.producto_id);
                return {
                    rowId: Date.now() + Math.random(),
                    productoId: d.producto_id,
                    cantidad: d.cantidad,
                    precio: d.precio_unitario,
                    productoInput: prod ? `${prod.codigo} - ${prod.nombre}` : `Producto ID ${d.producto_id}`
                };
            });

            setDetalles(mappedDetalles);

        } catch (err) {
            console.error("Error loading cotización", err);
            toast.error("No se pudo cargar la cotización.");
        } finally {
            setLoading(false);
        }
    };

    const fetchMaestros = async () => {
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
        } catch (err) {
            console.error("Error cargando maestros", err);
            toast.error("Error cargando listas maestras.");
        } finally {
            setLoading(false);
        }
    };

    const handleDetalleChange = (index, field, value) => {
        const newDetalles = [...detalles];
        newDetalles[index][field] = value;
        setDetalles(newDetalles);
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
            // Sugerir precio de lista o base
            handleDetalleChange(index, 'precio', productoFound.precio_base_manual || productoFound.costo_promedio || 0);
        } else {
            // Si no encuentra exacto, limpiar ID pero dejar texto por si quiere corregir
            handleDetalleChange(index, 'productoId', '');
        }
    };

    const agregarFila = () => {
        setDetalles([...detalles, { rowId: Date.now(), productoId: '', cantidad: 1, precio: 0, productoInput: '' }]);
    };

    const eliminarFila = (index) => {
        if (detalles.length > 1) {
            setDetalles(detalles.filter((_, i) => i !== index));
        } else {
            setDetalles([{ rowId: Date.now(), productoId: '', cantidad: 1, precio: 0, productoInput: '' }]);
        }
    };

    const handleSubmit = async (accion = 'GUARDAR') => {
        if (!terceroId) {
            toast.warning("Debe seleccionar un Cliente.");
            return;
        }
        if (detalles.some(d => !d.productoId || d.cantidad <= 0)) {
            toast.warning("Revise los productos. Todos deben ser válidos y tener cantidad > 0.");
            return;
        }

        setIsSubmitting(true);

        const payload = {
            fecha: fecha.toISOString().split('T')[0],
            fecha_vencimiento: fechaVencimiento ? fechaVencimiento.toISOString().split('T')[0] : null,
            tercero_id: parseInt(terceroId),
            bodega_id: bodegaId ? parseInt(bodegaId) : null,
            observaciones: observaciones,
            detalles: detalles.map(d => ({
                producto_id: parseInt(d.productoId),
                cantidad: parseFloat(d.cantidad),
                precio_unitario: parseFloat(d.precio)
            }))
        };

        try {
            let res;
            if (curCotizacionId) {
                res = await apiService.put(`/cotizaciones/${curCotizacionId}`, payload);

                // Si la acción es APROBAR, hacemos el cambio de estado extra
                if (accion === 'APROBAR') {
                    await apiService.patch(`/cotizaciones/${curCotizacionId}/estado`, null, { params: { estado: 'APROBADA' } });
                    toast.success("¡Cotización aprobada y lista!");
                    setEstado('APROBADA');
                } else {
                    toast.success("Cotización actualizada.");
                }

            } else {
                res = await apiService.post('/cotizaciones/', payload);
                if (accion === 'APROBAR') {
                    await apiService.patch(`/cotizaciones/${res.data.id}/estado`, null, { params: { estado: 'APROBADA' } });
                    toast.success("¡Cotización creada y aprobada!");
                } else {
                    toast.success("Cotización creada.");
                }
                // Redirect on create
                setTimeout(() => router.push(`/cotizaciones/crear?cotizacion_id=${res.data.id}`), 1000);
            }

        } catch (err) {
            const msg = err.response?.data?.detail || "Error al guardar.";
            toast.error(msg);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleDownloadPDF = async () => {
        try {
            const response = await apiService.get(`/cotizaciones/${curCotizacionId}/pdf`, {
                responseType: 'blob',
            });
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `cotizacion_${curCotizacionId}.pdf`);
            document.body.appendChild(link);
            link.click();
            link.parentNode.removeChild(link);
        } catch (error) {
            console.error(error);
            toast.error("Error al descargar el PDF");
        }
    };

    if (loading) return <div className="p-8">Cargando...</div>;

    const totalEstimado = detalles.reduce((acc, d) => acc + ((parseFloat(d.cantidad) || 0) * (parseFloat(d.precio) || 0)), 0);
    const readOnly = estado === 'FACTURADA' || estado === 'ANULADA';

    return (
        <div className="p-6 max-w-7xl mx-auto">
            <ToastContainer />
            <div className="flex justify-between items-center mb-6">
                <div className="flex items-center gap-4">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-800">{curCotizacionId ? `Cotización #${curCotizacionId}` : 'Nueva Cotización'}</h1>
                        <span className={`text-xs font-bold px-2 py-1 rounded ${estado === 'BORRADOR' ? 'bg-gray-200' : 'bg-blue-200 text-blue-800'}`}>
                            {estado}
                        </span>
                    </div>
                </div>

                <div className="flex gap-2">
                    {!readOnly && (
                        <>
                            <button
                                onClick={() => handleSubmit('GUARDAR')}
                                disabled={isSubmitting}
                                className="bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50 flex items-center gap-2"
                            >
                                <FaSave /> Borrador
                            </button>
                            <button
                                onClick={() => handleSubmit('APROBAR')}
                                disabled={isSubmitting}
                                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2 shadow-md"
                            >
                                <FaCheckCircle /> Aprobar Oferta
                            </button>
                        </>
                    )}
                    {estado === 'APROBADA' && (
                        <button
                            className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 flex items-center gap-2 shadow-md"
                            onClick={handleDownloadPDF}
                        >
                            <FaPrint /> Imprimir PDF
                        </button>
                    )}
                </div>
            </div>

            {/* CABECERA */}
            <div className={`bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6 ${readOnly ? 'opacity-75 pointer-events-none' : ''}`}>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div>
                        <label className="block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide">Fecha Emisión</label>
                        <div className="relative">
                            <DatePicker selected={fecha} onChange={setFecha} className={inputClass} dateFormat="dd/MM/yyyy" readOnly={readOnly} />
                            <FaCalendarAlt className="absolute right-3 top-3 text-gray-400" />
                        </div>
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide">Vencimiento Oferta</label>
                        <div className="relative">
                            <DatePicker selected={fechaVencimiento} onChange={setFechaVencimiento} className={inputClass} dateFormat="dd/MM/yyyy" placeholderText="Opcional" readOnly={readOnly} />
                            <FaCalendarAlt className="absolute right-3 top-3 text-gray-400" />
                        </div>
                    </div>
                    <div className="col-span-2">
                        <label className="block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide">Cliente</label>
                        <select value={terceroId} onChange={(e) => setTerceroId(e.target.value)} className={selectClass} disabled={readOnly}>
                            <option value="">Seleccione...</option>
                            {maestros.terceros.map(t => (
                                <option key={t.id} value={t.id}>{t.numero_identificacion} - {t.razon_social}</option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide">Bodega (Ref)</label>
                        <select value={bodegaId} onChange={(e) => setBodegaId(e.target.value)} className={selectClass} disabled={readOnly}>
                            <option value="">Opcional...</option>
                            {maestros.bodegas.map(b => (
                                <option key={b.id} value={b.id}>{b.nombre}</option>
                            ))}
                        </select>
                    </div>
                    <div className="col-span-3">
                        <label className="block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide">Observaciones</label>
                        <input type="text" className={inputClass} value={observaciones} onChange={(e) => setObservaciones(e.target.value)} readOnly={readOnly} />
                    </div>
                </div>
            </div>

            {/* DETALLES */}
            <div className={`bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden ${readOnly ? 'opacity-90 pointer-events-none' : ''}`}>
                <div className="p-4 bg-blue-50 border-b border-blue-100 flex justify-between items-center">
                    <h3 className="font-bold text-blue-800 flex items-center gap-2">
                        <FaBoxOpen /> Items de la Cotización
                    </h3>
                    {!readOnly && (
                        <button onClick={agregarFila} className="text-blue-600 hover:text-blue-800 text-sm font-semibold flex items-center gap-1">
                            <FaPlus /> Agregar Producto
                        </button>
                    )}
                </div>

                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/2">Producto</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-24">Cant.</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">Precio Oferta</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider w-32">Subtotal</th>
                            <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-16"></th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {detalles.map((det, index) => (
                            <tr key={det.rowId}>
                                <td className="px-4 py-2">
                                    <input
                                        list="productos-list"
                                        className="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                                        value={det.productoInput}
                                        onChange={(e) => handleDetalleChange(index, 'productoInput', e.target.value)}
                                        onBlur={(e) => handleProductoBlur(index, e.target.value)}
                                        placeholder="Buscar..."
                                        readOnly={readOnly}
                                    />
                                </td>
                                <td className="px-4 py-2">
                                    <input
                                        type="number"
                                        className="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm text-right"
                                        value={det.cantidad}
                                        onChange={(e) => handleDetalleChange(index, 'cantidad', e.target.value)}
                                        readOnly={readOnly}
                                    />
                                </td>
                                <td className="px-4 py-2">
                                    <input
                                        type="number"
                                        className="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm text-right"
                                        value={det.precio}
                                        onChange={(e) => handleDetalleChange(index, 'precio', e.target.value)}
                                        readOnly={readOnly}
                                    />
                                </td>
                                <td className="px-4 py-2 text-right font-bold text-gray-700">
                                    {((parseFloat(det.cantidad) || 0) * (parseFloat(det.precio) || 0)).toLocaleString('es-CO', { style: 'currency', currency: 'COP' })}
                                </td>
                                <td className="px-4 py-2 text-center">
                                    {!readOnly && (
                                        <button onClick={() => eliminarFila(index)} className="text-red-500 hover:text-red-700">
                                            <FaTrash />
                                        </button>
                                    )}
                                </td>
                            </tr>
                        ))}
                        <tr className="bg-gray-50">
                            <td colSpan="3" className="px-4 py-3 text-right font-bold text-gray-800 uppercase text-xs">Total Estimado:</td>
                            <td className="px-4 py-3 text-right font-bold text-xl text-blue-900">
                                {totalEstimado.toLocaleString('es-CO', { style: 'currency', currency: 'COP' })}
                            </td>
                            <td></td>
                        </tr>
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
