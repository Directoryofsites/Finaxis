"use client";
import React, { useState, useEffect } from 'react';
import { toast, ToastContainer } from 'react-toastify';
import { FaPlus, FaList, FaSave, FaSearch, FaCogs, FaCheckCircle, FaArrowRight, FaIndustry, FaBoxOpen } from 'react-icons/fa';
import { useAuth } from '../../context/AuthContext';
import { getOrdenes, createOrden, getRecetas, registrarConsumo, cerrarOrden } from '../../../lib/produccionService';
import { getBodegas } from '../../../lib/bodegaService';
import Link from 'next/link';

export default function GestionOrdenesPage() {
    const { user } = useAuth();
    const [activeTab, setActiveTab] = useState('list'); // 'list' | 'create'
    const [ordenes, setOrdenes] = useState([]);
    const [recetas, setRecetas] = useState([]);
    const [bodegas, setBodegas] = useState([]);
    const [loading, setLoading] = useState(false);

    // Formulario Crear Orden
    const [selectedReceta, setSelectedReceta] = useState(null);
    const [cantidadPlaneada, setCantidadPlaneada] = useState(1);
    const [bodegaDestino, setBodegaDestino] = useState(null);
    const [observaciones, setObservaciones] = useState('');

    // Estado para Acciones (Consumo / Cierre)
    const [selectedOrden, setSelectedOrden] = useState(null); // Si no es null, muestra detalle/acciones
    const [consumoItems, setConsumoItems] = useState([]); // Items a consumir
    const [bodegaOrigenConsumo, setBodegaOrigenConsumo] = useState('');
    const [cantidadCierre, setCantidadCierre] = useState(0);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        setLoading(true);
        try {
            const [ords, recs, bods] = await Promise.all([
                getOrdenes(),
                getRecetas(),
                getBodegas()
            ]);
            setOrdenes(ords);
            setRecetas(recs.filter(r => r.activa)); // Solo activas
            setBodegas(bods);
        } catch (error) {
            console.error(error);
            toast.error("Error cargando datos de producción.");
        } finally {
            setLoading(false);
        }
    };

    const handleCreateOrden = async (e) => {
        e.preventDefault();
        if (!selectedReceta) return toast.warning("Seleccione una receta.");
        if (!bodegaDestino) return toast.warning("Seleccione bodega destino.");

        try {
            setLoading(true);
            const payload = {
                producto_id: selectedReceta.producto_id,
                receta_id: selectedReceta.id,
                bodega_destino_id: bodegaDestino,
                cantidad_planeada: parseFloat(cantidadPlaneada),
                observaciones: observaciones,
                fecha_inicio: new Date().toISOString().split('T')[0]
            };
            await createOrden(payload);
            toast.success("Orden de producción creada.");
            await loadData();
            setActiveTab('list');
            // Reset
            setSelectedReceta(null);
            setCantidadPlaneada(1);
            setObservaciones('');
        } catch (error) {
            console.error(error);
            toast.error("Error creando orden.");
        } finally {
            setLoading(false);
        }
    };

    const handleOpenConsumo = (orden) => {
        setSelectedOrden(orden);
        // Pre-cargar items necesarios según receta restante (simple lógica)
        // En un sistema real, se calcula lo pendiente. Aquí cargamos todo lo de la receta base * cantidad orden
        // Ajustado a la proporción
        const factor = orden.cantidad_planeada / orden.receta.cantidad_base;
        const itemsSugeridos = orden.receta.detalles.map(d => ({
            insumo_id: d.insumo_id,
            producto_nombre: d.insumo ? d.insumo.nombre : `Insumo #${d.insumo_id}`, // Fallback si no viene populado
            cantidad: d.cantidad * factor
        }));
        setConsumoItems(itemsSugeridos);
        setCantidadCierre(orden.cantidad_planeada); // Sugerir planeado
        // Abrir modal o cambiar vista
        document.getElementById('modal_acciones').showModal();
    };

    const handleRegistrarConsumo = async () => {
        if (!bodegaOrigenConsumo) return toast.warning("Seleccione bodega de origen de la materia prima.");
        try {
            setLoading(true);
            await registrarConsumo(selectedOrden.id, consumoItems, bodegaOrigenConsumo);
            toast.success("Consumo registrado y descargado de inventario.");
            document.getElementById('modal_acciones').close();
            loadData();
        } catch (error) {
            console.error(error);
            toast.error("Error al registrar consumo: " + (error.response?.data?.detail || error.message));
        } finally {
            setLoading(false);
        }
    };

    const handleCerrarOrden = async () => {
        if (cantidadCierre <= 0) return toast.warning("Cantidad real debe ser mayor a 0.");
        if (!window.confirm("¿Está seguro de cerrar la orden? Esto generará la entrada de producto terminado y asientos contables finales.")) return;

        try {
            setLoading(true);
            await cerrarOrden(selectedOrden.id, cantidadCierre);
            toast.success("Orden CERRADA exitosamente.");
            document.getElementById('modal_acciones').close();
            loadData();
        } catch (error) {
            console.error(error);
            toast.error("Error al cerrar orden: " + (error.response?.data?.detail || error.message));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-6 bg-slate-50 min-h-screen">
            <ToastContainer />

            <header className="mb-6 flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-slate-800 flex items-center">
                        <FaIndustry className="mr-3 text-blue-600" />
                        Órdenes de Producción
                    </h1>
                    <p className="text-slate-500">Planifique, ejecute y cierre sus órdenes de fabricación.</p>
                </div>
                <button
                    onClick={() => setActiveTab(activeTab === 'list' ? 'create' : 'list')}
                    className={`px-4 py-2 rounded-lg font-semibold shadow-md transition ${activeTab === 'list' ? 'bg-blue-600 text-white hover:bg-blue-700' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}`}
                >
                    {activeTab === 'list' ? <><FaPlus className="inline mr-2" /> Nueva Orden</> : <><FaList className="inline mr-2" /> Ver Lista</>}
                </button>
            </header>

            {activeTab === 'list' && (
                <div className="bg-white rounded-xl shadow p-6">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-slate-100 text-slate-600 uppercase text-sm">
                                    <th className="p-3">Num Orden</th>
                                    <th className="p-3">Producto</th>
                                    <th className="p-3 text-center">Cant. Planeada</th>
                                    <th className="p-3 text-center">Cant. Real</th>
                                    <th className="p-3 text-right">Costo Total</th>
                                    <th className="p-3 text-center">Estado</th>
                                    <th className="p-3 text-center">Acciones</th>
                                </tr>
                            </thead>
                            <tbody className="text-sm">
                                {ordenes.length === 0 ? (
                                    <tr><td colSpan="7" className="p-4 text-center text-gray-500">No hay órdenes registradas.</td></tr>
                                ) : ordenes.map(o => (
                                    <tr key={o.id} className="border-b hover:bg-slate-50">
                                        <td className="p-3 font-mono font-bold text-blue-600">{o.numero_orden}</td>
                                        <td className="p-3">{o.producto?.nombre}</td>
                                        <td className="p-3 text-center font-bold">{o.cantidad_planeada}</td>
                                        <td className="p-3 text-center">{o.cantidad_real}</td>
                                        <td className="p-3 text-right font-mono">
                                            $ {((o.costo_total_mp + o.costo_total_mod + o.costo_total_cif) || 0).toLocaleString()}
                                        </td>
                                        <td className="p-3 text-center">
                                            <span className={`px-2 py-1 rounded-full text-xs font-bold 
                                                ${o.estado === 'CERRADA' ? 'bg-gray-200 text-gray-600' :
                                                    o.estado === 'EN_PROCESO' ? 'bg-yellow-100 text-yellow-700' :
                                                        'bg-blue-100 text-blue-700'}`}>
                                                {o.estado}
                                            </span>
                                        </td>
                                        <td className="p-3 text-center">
                                            {o.estado !== 'CERRADA' && (
                                                <button
                                                    onClick={() => handleOpenConsumo(o)}
                                                    className="text-blue-600 hover:text-blue-800 underline text-xs font-bold"
                                                >
                                                    Gestionar
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {activeTab === 'create' && (
                <div className="bg-white rounded-xl shadow p-6 max-w-2xl mx-auto">
                    <h2 className="text-xl font-bold mb-6 text-slate-700 border-b pb-2">Planificar Nueva Producción</h2>
                    <form onSubmit={handleCreateOrden}>
                        <div className="mb-4">
                            <label className="block text-sm font-semibold text-gray-700 mb-1">Receta / Fórmula</label>
                            <select
                                className="w-full border rounded p-2 outline-none focus:ring-2 focus:ring-blue-500"
                                onChange={e => setSelectedReceta(recetas.find(r => r.id === parseInt(e.target.value)))}
                                required
                            >
                                <option value="">-- Seleccione Receta --</option>
                                {recetas.map(r => (
                                    <option key={r.id} value={r.id}>
                                        {r.nombre} (Prod: {r.producto?.nombre})
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div className="mb-4">
                            <label className="block text-sm font-semibold text-gray-700 mb-1">Bodega Destino (Producto Terminado)</label>
                            <select
                                className="w-full border rounded p-2 outline-none focus:ring-2 focus:ring-blue-500"
                                onChange={e => setBodegaDestino(e.target.value)}
                                required
                            >
                                <option value="">-- Seleccione Bodega --</option>
                                {bodegas.map(b => (
                                    <option key={b.id} value={b.id}>{b.nombre}</option>
                                ))}
                            </select>
                        </div>

                        <div className="mb-4">
                            <label className="block text-sm font-semibold text-gray-700 mb-1">Cantidad a Producir</label>
                            <input
                                type="number"
                                className="w-full border rounded p-2 outline-none focus:ring-2 focus:ring-blue-500"
                                min="1" step="any"
                                value={cantidadPlaneada}
                                onChange={e => setCantidadPlaneada(e.target.value)}
                                required
                            />
                        </div>

                        <div className="mb-6">
                            <label className="block text-sm font-semibold text-gray-700 mb-1">Observaciones</label>
                            <textarea
                                className="w-full border rounded p-2 outline-none focus:ring-2 focus:ring-blue-500"
                                rows="3"
                                value={observaciones}
                                onChange={e => setObservaciones(e.target.value)}
                            ></textarea>
                        </div>

                        <div className="flex justify-end gap-3">
                            <button type="button" onClick={() => setActiveTab('list')} className="px-4 py-2 border rounded hover:bg-gray-50">Cancelar</button>
                            <button type="submit" disabled={loading} className="px-6 py-2 bg-blue-600 text-white font-bold rounded hover:bg-blue-700">
                                Crear Orden
                            </button>
                        </div>
                    </form>
                </div>
            )}

            {/* MODAL DE ACCIONES (CONSUMO / CIERRE) */}
            <dialog id="modal_acciones" className="modal modal-bottom sm:modal-middle">
                {selectedOrden && (
                    <div className="modal-box w-11/12 max-w-3xl">
                        <h3 className="font-bold text-lg flex items-center mb-4">
                            <FaCogs className="mr-2 text-slate-500" />
                            Gestionar Orden #{selectedOrden.numero_orden}
                        </h3>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* PANEL IZQUIERDO: CONSUMO DE MATERIALES */}
                            <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
                                <h4 className="font-bold text-blue-800 mb-2 border-b border-blue-200 pb-1">1. Registrar Consumo (Salida MP)</h4>
                                <p className="text-xs text-blue-600 mb-3">Descarga materiales del inventario y carga costo a la orden.</p>

                                <div className="mb-3">
                                    <label className="block text-xs font-bold text-gray-600 mb-1">Bodega Origen Materia Prima</label>
                                    <select
                                        className="w-full border rounded p-1 text-sm bg-white"
                                        onChange={e => setBodegaOrigenConsumo(e.target.value)}
                                        value={bodegaOrigenConsumo}
                                    >
                                        <option value="">-- Seleccione Bodega --</option>
                                        {bodegas.map(b => (
                                            <option key={b.id} value={b.id}>{b.nombre}</option>
                                        ))}
                                    </select>
                                </div>

                                <div className="max-h-40 overflow-y-auto mb-3 bg-white border rounded">
                                    <table className="w-full text-xs">
                                        <thead>
                                            <tr className="bg-gray-100"><th className="p-1">Material</th><th className="p-1">Cant.</th></tr>
                                        </thead>
                                        <tbody>
                                            {consumoItems.map((item, idx) => (
                                                <tr key={idx} className="border-t">
                                                    <td className="p-1">{item.producto_nombre || 'Item ' + item.insumo_id}</td>
                                                    <td className="p-1 text-center">{item.cantidad.toFixed(2)}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>

                                <button
                                    onClick={handleRegistrarConsumo}
                                    className="w-full py-2 bg-blue-600 text-white rounded text-sm font-bold hover:bg-blue-700"
                                >
                                    Registrar Consumo
                                </button>
                            </div>

                            {/* PANEL DERECHO: CIERRE DE ORDEN */}
                            <div className="bg-green-50 p-4 rounded-lg border border-green-100">
                                <h4 className="font-bold text-green-800 mb-2 border-b border-green-200 pb-1">2. Cerrar Orden (Entrada PT)</h4>
                                <p className="text-xs text-green-600 mb-3">Finaliza la producción, calcula costo unitario real e ingresa producto terminado.</p>

                                <div className="mb-3">
                                    <label className="block text-xs font-bold text-gray-600 mb-1">Cantidad Real Producida</label>
                                    <input
                                        type="number"
                                        className="w-full border rounded p-1 text-sm text-center font-mono font-bold"
                                        value={cantidadCierre}
                                        onChange={e => setCantidadCierre(e.target.value)}
                                    />
                                </div>

                                <div className="text-xs text-gray-600 mb-4 bg-white p-2 rounded border">
                                    <p><strong>Costos Acumulados:</strong></p>
                                    <p>MP: ${selectedOrden.costo_total_mp.toLocaleString()}</p>
                                    <p>MOD: ${selectedOrden.costo_total_mod.toLocaleString()}</p>
                                    <p>CIF: ${selectedOrden.costo_total_cif.toLocaleString()}</p>
                                    <p className="mt-1 border-t pt-1 font-bold text-green-700">Total: ${(selectedOrden.costo_total_mp + selectedOrden.costo_total_mod + selectedOrden.costo_total_cif).toLocaleString()}</p>
                                </div>

                                <button
                                    onClick={handleCerrarOrden}
                                    className="w-full py-2 bg-green-600 text-white rounded text-sm font-bold hover:bg-green-700"
                                >
                                    <FaCheckCircle className="inline mr-1" /> Cerrar Orden
                                </button>
                            </div>
                        </div>

                        <div className="modal-action">
                            <form method="dialog">
                                <button className="btn btn-sm btn-circle btn-ghost absolute right-2 top-2">✕</button>
                                <button className="btn btn-sm">Cancelar</button>
                            </form>
                        </div>
                    </div>
                )}
            </dialog>
        </div>
    );
}
