"use client";
import React, { useState, useEffect } from 'react';
import { toast, ToastContainer } from 'react-toastify';
import { FaPlus, FaList, FaSave, FaSearch, FaTimes, FaFlask } from 'react-icons/fa';
import { useAuth } from '../../context/AuthContext';
import { getRecetas, createReceta } from '../../../lib/produccionService';
import { getProductosByEmpresa as getProductos } from '../../../lib/productosService'; // Necesitamos buscar productos (MP y PT)

export default function GestionRecetasPage() {
    const { user } = useAuth();
    const [activeTab, setActiveTab] = useState('list'); // 'list' | 'create'
    const [recetas, setRecetas] = useState([]);
    const [loading, setLoading] = useState(false);

    // Estado para Crear Receta
    const [productos, setProductos] = useState([]); // Catálogo global para selección
    const [productoPT, setProductoPT] = useState(null); // Producto Terminado seleccionado

    const [nombreReceta, setNombreReceta] = useState('');
    const [cantidadBase, setCantidadBase] = useState(1);
    const [detalles, setDetalles] = useState([]); // Lista de ingredientes { insumo_id, cantidad, producto_nombre }

    // Estado auxiliar para agregar ingrediente
    const [selectedIngrediente, setSelectedIngrediente] = useState(null);
    const [cantidadIngrediente, setCantidadIngrediente] = useState(1);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        loadRecetas();
        loadProductos();
    }, []);

    const loadRecetas = async () => {
        setLoading(true);
        try {
            const data = await getRecetas();
            setRecetas(data);
        } catch (error) {
            console.error("Error cargando recetas", error);
            // toast.error("Error al cargar recetas."); // Silenciado si no hay endpoint de lista aún
        } finally {
            setLoading(false);
        }
    };

    const loadProductos = async () => {
        try {
            // Cargamos todos para poder elegir PT e Insumos SIMPLE
            // Idealmente usar un endpoint de búsqueda o paginado si son muchos
            const res = await getProductos();
            setProductos(res.productos || []);
        } catch (error) {
            console.error("Error cargando productos", error);
        }
    };

    const handleAddIngrediente = () => {
        if (!selectedIngrediente) {
            toast.warning("Seleccione un insumo.");
            return;
        }
        if (cantidadIngrediente <= 0) {
            toast.warning("Cantidad debe ser mayor a 0.");
            return;
        }

        const existe = detalles.find(d => d.insumo_id === selectedIngrediente.id);
        if (existe) {
            toast.error("Este insumo ya está en la receta.");
            return;
        }

        setDetalles([
            ...detalles,
            {
                insumo_id: selectedIngrediente.id,
                producto_nombre: selectedIngrediente.nombre,
                cantidad: parseFloat(cantidadIngrediente)
            }
        ]);
        setSelectedIngrediente(null);
        setCantidadIngrediente(1);
        setSearchTerm('');
    };

    const handleRemoveIngrediente = (id) => {
        setDetalles(detalles.filter(d => d.insumo_id !== id));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!productoPT) return toast.warning("Seleccione el Producto Terminado.");
        if (!nombreReceta) return toast.warning("Asigne un nombre a la receta.");
        if (detalles.length === 0) return toast.warning("Agregue al menos un insumo.");

        try {
            setLoading(true);
            const payload = {
                producto_id: productoPT.id,
                nombre: nombreReceta,
                descripcion: `Receta para ${productoPT.nombre}`,
                cantidad_base: parseFloat(cantidadBase),
                activa: true,
                detalles: detalles.map(d => ({
                    insumo_id: d.insumo_id,
                    cantidad: d.cantidad
                }))
            };

            await createReceta(payload);
            toast.success("Receta creada exitosamente.");
            setActiveTab('list');
            loadRecetas();
            // Reset form
            setProductoPT(null);
            setNombreReceta('');
            setDetalles([]);
        } catch (error) {
            console.error(error);
            toast.error("Error al guardar receta.");
        } finally {
            setLoading(false);
        }
    };

    // Filtrar productos para autocompletar
    const productosFiltrados = productos.filter(p =>
        p.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.codigo.toLowerCase().includes(searchTerm.toLowerCase())
    ).slice(0, 10); // Top 10

    return (
        <div className="p-6 bg-slate-50 min-h-screen">
            <ToastContainer />

            <header className="mb-6 flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-slate-800 flex items-center">
                        <FaFlask className="mr-3 text-blue-600" />
                        Gestión de Recetas (Fórmulas)
                    </h1>
                    <p className="text-slate-500">Defina los materiales necesarios para producir sus productos.</p>
                </div>
                <button
                    onClick={() => setActiveTab(activeTab === 'list' ? 'create' : 'list')}
                    className={`px-4 py-2 rounded-lg font-semibold shadow-md transition ${activeTab === 'list' ? 'bg-blue-600 text-white hover:bg-blue-700' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}`}
                >
                    {activeTab === 'list' ? <><FaPlus className="inline mr-2" /> Nueva Receta</> : <><FaList className="inline mr-2" /> Ver Lista</>}
                </button>
            </header>

            {activeTab === 'list' && (
                <div className="bg-white rounded-xl shadow p-6">
                    <h2 className="text-lg font-bold mb-4">Recetas Registradas</h2>
                    {loading ? <p>Cargando...</p> : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-left border-collapse">
                                <thead>
                                    <tr className="bg-slate-100 text-slate-600 uppercase text-sm">
                                        <th className="p-3">ID</th>
                                        <th className="p-3">Nombre Receta</th>
                                        <th className="p-3">Producto Terminado</th>
                                        <th className="p-3">Base</th>
                                        <th className="p-3">Estado</th>
                                    </tr>
                                </thead>
                                <tbody className="text-sm">
                                    {recetas.length === 0 ? (
                                        <tr><td colSpan="5" className="p-4 text-center text-gray-500">No hay recetas registradas.</td></tr>
                                    ) : recetas.map(r => (
                                        <tr key={r.id} className="border-b hover:bg-slate-50">
                                            <td className="p-3 font-mono">{r.id}</td>
                                            <td className="p-3 font-semibold text-blue-600">{r.nombre}</td>
                                            <td className="p-3">{r.producto ? r.producto.nombre : 'N/A'}</td>
                                            <td className="p-3">{r.cantidad_base} UND</td>
                                            <td className="p-3">
                                                <span className={`px-2 py-1 rounded-full text-xs font-bold ${r.activa ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                                    {r.activa ? 'ACTIVA' : 'INACTIVA'}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}

            {activeTab === 'create' && (
                <div className="bg-white rounded-xl shadow p-6 max-w-4xl mx-auto">
                    <h2 className="text-xl font-bold mb-6 text-slate-700 border-b pb-2">Crear Nueva Fórmula Maestra</h2>

                    <form onSubmit={handleSubmit}>
                        {/* SECCIÓN 1: CABECERA */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6 bg-slate-50 p-4 rounded-lg">
                            <div>
                                <label className="block text-sm font-semibold text-gray-700 mb-1">Nombre de la Receta</label>
                                <input
                                    type="text"
                                    className="w-full border rounded p-2 focus:ring-2 focus:ring-blue-500 outline-none"
                                    placeholder="Ej: Camisa Slim Fit Talla M"
                                    value={nombreReceta}
                                    onChange={e => setNombreReceta(e.target.value)}
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-semibold text-gray-700 mb-1">Producto a Producir (PT)</label>
                                <select
                                    className="w-full border rounded p-2 focus:ring-2 focus:ring-blue-500 outline-none"
                                    onChange={e => {
                                        const prod = productos.find(p => p.id === parseInt(e.target.value));
                                        setProductoPT(prod);
                                        if (prod && !nombreReceta) setNombreReceta(`Fórmula estándar para ${prod.nombre}`);
                                    }}
                                    value={productoPT ? productoPT.id : ''}
                                >
                                    <option value="">-- Seleccione Producto Terminado --</option>
                                    {productos.filter(p => !p.es_servicio).map(p => (
                                        <option key={p.id} value={p.id}>{p.codigo} - {p.nombre}</option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-semibold text-gray-700 mb-1">Cantidad Base (Rendimiento)</label>
                                <input
                                    type="number"
                                    className="w-full border rounded p-2 focus:ring-2 focus:ring-blue-500 outline-none"
                                    min="0.01" step="0.01"
                                    value={cantidadBase}
                                    onChange={e => setCantidadBase(e.target.value)}
                                />
                                <span className="text-xs text-gray-500">Cantidad de PT que resulta de esta receta.</span>
                            </div>
                        </div>

                        {/* SECCIÓN 2: INGREDIENTES */}
                        <div className="mb-6">
                            <h3 className="font-bold text-gray-700 mb-2">Ingredientes / Materia Prima (MP)</h3>

                            <div className="flex gap-2 mb-4 items-end bg-blue-50 p-3 rounded-lg border border-blue-100">
                                <div className="flex-1 relative">
                                    <label className="block text-xs font-bold text-blue-700 mb-1">Buscar Insumo</label>
                                    <div className="flex items-center bg-white border rounded">
                                        <FaSearch className="ml-2 text-gray-400" />
                                        <input
                                            type="text"
                                            className="w-full p-2 outline-none"
                                            placeholder="Escriba nombre o código..."
                                            value={searchTerm}
                                            onChange={e => {
                                                setSearchTerm(e.target.value);
                                                setSelectedIngrediente(null); // Reset al escribir
                                            }}
                                        />
                                    </div>
                                    {/* Autocomplete Dropdown */}
                                    {searchTerm && !selectedIngrediente && (
                                        <div className="absolute z-10 bg-white border shadow-lg w-full mt-1 max-h-40 overflow-y-auto rounded-md">
                                            {productosFiltrados.map(p => (
                                                <div
                                                    key={p.id}
                                                    className="p-2 hover:bg-blue-50 cursor-pointer text-sm"
                                                    onClick={() => {
                                                        setSelectedIngrediente(p);
                                                        setSearchTerm(p.nombre);
                                                    }}
                                                >
                                                    <span className="font-bold text-gray-700">{p.codigo}</span> - {p.nombre}
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>

                                <div className="w-32">
                                    <label className="block text-xs font-bold text-blue-700 mb-1">Cantidad</label>
                                    <input
                                        type="number"
                                        className="w-full border rounded p-2 text-center"
                                        min="0.0001" step="any"
                                        value={cantidadIngrediente}
                                        onChange={e => setCantidadIngrediente(e.target.value)}
                                    />
                                </div>

                                <button
                                    type="button"
                                    onClick={handleAddIngrediente}
                                    className="bg-blue-600 text-white p-2 rounded hover:bg-blue-700 shadow h-10 w-10 flex items-center justify-center"
                                    title="Agregar Insumo"
                                >
                                    <FaPlus />
                                </button>
                            </div>

                            {/* Lista de Detalles Agregados */}
                            <div className="border rounded-lg overflow-hidden">
                                <table className="w-full text-sm">
                                    <thead className="bg-gray-100 text-gray-600 font-semibold">
                                        <tr>
                                            <th className="p-2 text-left">Insumo</th>
                                            <th className="p-2 text-center">Cantidad Requerida</th>
                                            <th className="p-2 text-center">Acción</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {detalles.length === 0 ? (
                                            <tr><td colSpan="3" className="p-4 text-center text-gray-400 bg-white">Sin ingredientes agregados.</td></tr>
                                        ) : detalles.map((d, idx) => (
                                            <tr key={idx} className="border-t">
                                                <td className="p-2 font-medium">{d.producto_nombre}</td>
                                                <td className="p-2 text-center">{d.cantidad}</td>
                                                <td className="p-2 text-center">
                                                    <button
                                                        type="button"
                                                        onClick={() => handleRemoveIngrediente(d.insumo_id)}
                                                        className="text-red-500 hover:text-red-700 transition"
                                                    >
                                                        <FaTimes />
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        <div className="flex justify-end gap-4 mt-8">
                            <button
                                type="button"
                                onClick={() => setActiveTab('list')}
                                className="px-6 py-2 border rounded-lg hover:bg-gray-50 text-gray-700"
                            >
                                Cancelar
                            </button>
                            <button
                                type="submit"
                                disabled={loading}
                                className="px-6 py-2 bg-green-600 text-white font-bold rounded-lg shadow hover:bg-green-700 flex items-center"
                            >
                                <FaSave className="mr-2" />
                                {loading ? 'Guardando...' : 'Guardar Receta'}
                            </button>
                        </div>
                    </form>
                </div>
            )}
        </div>
    );
}
