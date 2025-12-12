"use client";
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { toast, ToastContainer } from 'react-toastify';
import { FaPlus, FaList, FaSave, FaSearch, FaTimes, FaFlask, FaEdit, FaTrash, FaMoneyBillWave, FaFilePdf, FaIndustry } from 'react-icons/fa';
import { useAuth } from '../../context/AuthContext';
import { getRecetas, createReceta, updateReceta, deleteReceta, downloadRecetaPDF } from '../../../lib/produccionService';
import { getProductosByEmpresa as getProductos } from '../../../lib/productosService'; // Necesitamos buscar productos (MP y PT)

export default function GestionRecetasPage() {
    const { user } = useAuth();
    const [activeTab, setActiveTab] = useState('list'); // 'list' | 'create'
    const [recetas, setRecetas] = useState([]);
    const [loading, setLoading] = useState(false);
    const [searchTermList, setSearchTermList] = useState(''); // Estado para filtro de lista

    // Estado para Crear/Editar Receta
    const [editMode, setEditMode] = useState(false);
    const [editingId, setEditingId] = useState(null);

    const [productos, setProductos] = useState([]); // Catálogo global para selección
    const [productoPT, setProductoPT] = useState(null); // Producto Terminado seleccionado (objeto completo)

    const [nombreReceta, setNombreReceta] = useState('');
    const [descripcionReceta, setDescripcionReceta] = useState('');
    const [cantidadBase, setCantidadBase] = useState(1);

    // Lista de ingredientes { insumo_id, cantidad, producto_nombre }
    const [detalles, setDetalles] = useState([]);

    // Lista de recursos { descripcion, tipo (MOD/CIF), costo_estimado }
    const [recursos, setRecursos] = useState([]);

    // Estado auxiliar para agregar ingrediente
    const [selectedIngrediente, setSelectedIngrediente] = useState(null);
    const [cantidadIngrediente, setCantidadIngrediente] = useState(1);
    const [searchTerm, setSearchTerm] = useState('');

    // Estado auxiliar para agregar recurso
    const [newRecursoDesc, setNewRecursoDesc] = useState('');
    const [newRecursoTipo, setNewRecursoTipo] = useState('MANO_OBRA_DIRECTA'); // MOD o CIF
    const [newRecursoCosto, setNewRecursoCosto] = useState(0);

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

    const resetForm = () => {
        setEditMode(false);
        setEditingId(null);
        setNombreReceta('');
        setDescripcionReceta('');
        setCantidadBase(1);
        setProductoPT(null);
        setDetalles([]);
        setRecursos([]);
        setActiveTab('list');
    };

    const handleEdit = (receta) => {
        setEditMode(true);
        setEditingId(receta.id);

        setNombreReceta(receta.nombre);
        setDescripcionReceta(receta.descripcion || '');
        setCantidadBase(receta.cantidad_base);

        // Encontrar el producto PT en la lista cargada
        const pt = productos.find(p => p.id === receta.producto_id);
        setProductoPT(pt || { id: receta.producto_id, nombre: 'Producto Original (No encontrado en lista)' });

        // Mapear detalles
        const mappedDetalles = receta.detalles.map(d => ({
            insumo_id: d.insumo_id,
            cantidad: d.cantidad,
            producto_nombre: d.insumo ? d.insumo.nombre : `Insumo #${d.insumo_id}`
        }));
        setDetalles(mappedDetalles);

        // Mapear recursos (si existen en el objeto receta, verificar backend return)
        const mappedRecursos = receta.recursos ? receta.recursos.map(r => ({
            descripcion: r.descripcion,
            tipo: r.tipo === 'MANO_OBRA_DIRECTA' ? 'MANO_OBRA_DIRECTA' : 'COSTO_INDIRECTO_FABRICACION', // Normalizar si viene diferente
            costo_estimado: r.costo_estimado
        })) : [];
        setRecursos(mappedRecursos);

        setActiveTab('create');
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

    const handleAddRecurso = () => {
        if (!newRecursoDesc) return toast.warning("Ingrese una descripción para el recurso.");
        if (newRecursoCosto <= 0) return toast.warning("El costo debe ser mayor a 0.");

        setRecursos([
            ...recursos,
            {
                descripcion: newRecursoDesc,
                tipo: newRecursoTipo,
                costo_estimado: parseFloat(newRecursoCosto)
            }
        ]);
        setNewRecursoDesc('');
        setNewRecursoCosto(0);
    };

    const handleRemoveRecurso = (index) => {
        const newArr = [...recursos];
        newArr.splice(index, 1);
        setRecursos(newArr);
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
                descripcion: descripcionReceta,
                cantidad_base: parseFloat(cantidadBase),
                detalles: detalles.map(d => ({
                    insumo_id: d.insumo_id,
                    cantidad: d.cantidad
                })),
                recursos: recursos.map(r => ({
                    descripcion: r.descripcion,
                    tipo: r.tipo,
                    costo_estimado: r.costo_estimado
                }))
            };

            if (editMode) {
                // UPDATE
                await updateReceta(editingId, payload);
                toast.success("Receta actualizada correctamente.");
            } else {
                // CREATE
                await createReceta(payload);
                toast.success("Receta creada correctamente.");
            }

            resetForm();
            loadRecetas();
        } catch (error) {
            console.error("Error guardando receta", error);
            toast.error("Error al guardar la receta.");
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (receta) => {
        if (!window.confirm("¿Eliminar esta receta? Si tiene órdenes asociadas no se podrá eliminar.")) return;
        try {
            await deleteReceta(receta.id);
            toast.success("Receta eliminada.");
            loadRecetas();
        } catch (error) {
            console.error(error);
            toast.error("Error al eliminar receta.");
        }
    };

    // Filtros de búsqueda (simple)
    const filteredProductos = productos.filter(p =>
        p.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.codigo.toLowerCase().includes(searchTerm.toLowerCase())
    ).slice(0, 10); // Limitamos a 10 resultados para el dropdown

    return (
        <div className="p-6 bg-gray-50 min-h-screen font-sans text-gray-800">
            <ToastContainer />
            <div className="flex justify-between items-center mb-8">
                <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-3">
                    <FaFlask className="text-blue-600" />
                    Gestión de Recetas
                </h1>
                {activeTab === 'list' ? (
                    <button
                        onClick={() => { resetForm(); setActiveTab('create'); }}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2 rounded-lg shadow-md transition-all flex items-center gap-2"
                    >
                        <FaPlus /> Nueva Receta
                    </button>
                ) : (
                    <button
                        onClick={resetForm}
                        className="bg-gray-500 hover:bg-gray-600 text-white px-5 py-2 rounded-lg shadow-md transition-all flex items-center gap-2"
                    >
                        <FaList /> Volver al Listado
                    </button>
                )}
            </div>

            {activeTab === 'list' ? (
                // --- VISTA LISTADO ---
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">

                    {/* SEARCH BAR & FILTERS */}
                    <div className="flex flex-col md:flex-row gap-4 mb-6">
                        <div className="relative flex-1 group">
                            <FaSearch className="absolute left-3 top-3.5 text-gray-400 group-focus-within:text-blue-500 transition-colors" />
                            <input
                                type="text"
                                placeholder="Buscar por Nombre de Receta o Producto Terminado..."
                                className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 outline-none transition-all"
                                value={searchTermList}
                                onChange={(e) => setSearchTermList(e.target.value)}
                            />
                        </div>
                    </div>

                    {loading ? (
                        <p className="text-gray-500 text-center py-8">Cargando recetas...</p>
                    ) : (recetas.filter(r =>
                        (r.nombre?.toLowerCase() || '').includes(searchTermList.toLowerCase()) ||
                        (r.producto?.nombre?.toLowerCase() || '').includes(searchTermList.toLowerCase())
                    ).length === 0) ? (
                        <div className="text-center py-10 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200">
                            <p className="text-gray-500 mb-4">No se encontraron recetas.</p>
                            {recetas.length === 0 && <button onClick={() => setActiveTab('create')} className="text-blue-600 hover:underline">Crear la primera receta</button>}
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-left border-collapse">
                                <thead>
                                    <tr className="border-b border-gray-200 text-gray-600 text-xs uppercase tracking-wider bg-gray-50/50">
                                        <th className="px-3 py-3 font-bold">Producto Terminado</th>
                                        <th className="px-3 py-3 font-bold">Nombre Receta</th>
                                        <th className="px-3 py-3 font-bold text-center">Insumos</th>
                                        <th className="px-3 py-3 font-bold text-center">Estado</th>
                                        <th className="px-3 py-3 font-bold text-right">Acciones</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100">
                                    {recetas.filter(r =>
                                        (r.nombre?.toLowerCase() || '').includes(searchTermList.toLowerCase()) ||
                                        (r.producto?.nombre?.toLowerCase() || '').includes(searchTermList.toLowerCase())
                                    ).map(receta => (
                                        <tr key={receta.id} className="hover:bg-blue-50/50 transition-colors text-sm">
                                            <td className="px-3 py-2 text-gray-800 font-medium whitespace-nowrap">
                                                {receta.producto ? receta.producto.nombre : <span className="text-red-400 italic">Producto Eliminado</span>}
                                            </td>
                                            <td className="px-3 py-2 text-gray-600">
                                                {receta.nombre}
                                            </td>
                                            <td className="px-3 py-2 text-center">
                                                <span className="bg-gray-100 text-gray-700 text-xs px-2 py-0.5 rounded-full font-bold border border-gray-200">
                                                    {receta.detalles ? receta.detalles.length : 0} ítems
                                                </span>
                                            </td>
                                            <td className="px-3 py-2 text-center">
                                                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide ${receta.activa ? 'bg-green-100 text-green-700 border border-green-200' : 'bg-red-100 text-red-700 border border-red-200'}`}>
                                                    {receta.activa ? 'Activa' : 'Inactiva'}
                                                </span>
                                            </td>
                                            <td className="px-3 py-2 text-right whitespace-nowrap">
                                                <Link
                                                    href={`/produccion/ordenes?action=create&receta_id=${receta.id}`}
                                                    className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-green-50 text-green-600 hover:bg-green-100 hover:text-green-700 mx-1 transition-all"
                                                    title="Producir (Crear Orden)"
                                                >
                                                    <FaIndustry size={14} />
                                                </Link>
                                                <button onClick={() => downloadRecetaPDF(receta.id)} className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-gray-50 text-gray-500 hover:bg-gray-100 hover:text-gray-700 mx-1 transition-all" title="Imprimir">
                                                    <FaFilePdf size={14} />
                                                </button>
                                                <button
                                                    onClick={() => handleEdit(receta)}
                                                    className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-indigo-50 text-indigo-600 hover:bg-indigo-100 hover:text-indigo-700 mx-1 transition-all"
                                                    title="Editar"
                                                >
                                                    <FaEdit size={14} />
                                                </button>
                                                <button onClick={() => handleDelete(receta)} className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-red-50 text-red-500 hover:bg-red-100 hover:text-red-700 mx-1 transition-all" title="Eliminar">
                                                    <FaTrash size={14} />
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            ) : (
                // --- VISTA CREACIÓN / EDICIÓN ---
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* COLUMNA IZQUIERDA: DATOS GENERALES */}
                    <div className="lg:col-span-1 bg-white rounded-xl shadow-sm border border-gray-100 p-6 h-fit sticky top-6">
                        <h2 className="text-xl font-bold text-gray-800 mb-6 pb-2 border-b border-gray-100">
                            {editMode ? 'Editar Receta' : 'Datos Generales'}
                        </h2>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Producto a Fabricar (PT)</label>
                                {editMode ? (
                                    <div className="w-full border border-gray-300 rounded-lg px-3 py-2 bg-gray-100 text-gray-700 font-medium">
                                        {productoPT ? `${productoPT.nombre} (${productoPT.codigo})` : 'Cargando producto...'}
                                    </div>
                                ) : (
                                    productos.length > 0 ? (
                                        <select
                                            className="w-full border border-gray-300 rounded-lg px-3 py-2 bg-gray-50 focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                                            value={productoPT ? productoPT.id : ''}
                                            onChange={(e) => {
                                                const p = productos.find(prod => prod.id === parseInt(e.target.value));
                                                setProductoPT(p);
                                            }}
                                        >
                                            <option value="">-- Seleccionar --</option>
                                            {productos.filter(p => !p.es_servicio).map(p => ( // Mostrar todos, o filtrar por grupos PT si existiera flag
                                                <option key={p.id} value={p.id}>{p.nombre} ({p.codigo})</option>
                                            ))}
                                        </select>
                                    ) : (
                                        <p className="text-red-500 text-sm">No hay productos cargados.</p>
                                    )
                                )}
                                {editMode && <p className="text-xs text-gray-500 mt-1">El producto no se puede cambiar en edición.</p>}
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Nombre de la Receta</label>
                                <input
                                    type="text"
                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
                                    placeholder="Ej: Versión Estándar 2024"
                                    value={nombreReceta}
                                    onChange={e => setNombreReceta(e.target.value)}
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Descripción (Opcional)</label>
                                <textarea
                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
                                    rows="3"
                                    value={descripcionReceta}
                                    onChange={e => setDescripcionReceta(e.target.value)}
                                ></textarea>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Cantidad Base</label>
                                    <input
                                        type="number"
                                        className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
                                        min="1"
                                        value={cantidadBase}
                                        onChange={e => setCantidadBase(parseFloat(e.target.value))}
                                    />
                                    <span className="text-xs text-gray-500">Unidades que produce esta receta.</span>
                                </div>
                            </div>
                        </div>

                        <div className="mt-8 pt-6 border-t border-gray-100">
                            <button
                                onClick={handleSubmit}
                                disabled={loading}
                                className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 rounded-lg shadow-lg hover:shadow-xl transition-all flex justify-center items-center gap-2"
                            >
                                {loading ? 'Guardando...' : (
                                    <><FaSave /> {editMode ? 'Actualizar Receta' : 'Guardar Receta'}</>
                                )}
                            </button>
                        </div>
                    </div>

                    {/* COLUMNA DERECHA: INSUMOS Y RECURSOS */}
                    <div className="lg:col-span-2 space-y-6">

                        {/* SECCIÓN MATERIA PRIMA (INSUMOS) */}
                        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                            <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                                <FaFlask className="text-purple-600" /> Materia Prima e Insumos
                            </h3>

                            {/* Buscador y Agregador Small */}
                            <div className="flex flex-wrap items-end gap-3 mb-6 bg-purple-50 p-4 rounded-xl border border-purple-100">
                                <div className="flex-1 relative min-w-[200px]">
                                    <label className="text-xs font-bold text-gray-500 uppercase mb-1 block">Buscar Insumo</label>
                                    <div className="relative">
                                        <FaSearch className="absolute left-3 top-3 text-gray-400" />
                                        <input
                                            type="text"
                                            placeholder="Nombre o código..."
                                            className="w-full pl-9 pr-3 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-purple-500 outline-none"
                                            value={searchTerm}
                                            onChange={(e) => {
                                                setSearchTerm(e.target.value);
                                                setSelectedIngrediente(null); // Reset al escribir
                                            }}
                                        />
                                    </div>
                                    {/* Dropdown de resultados */}
                                    {searchTerm && !selectedIngrediente && (
                                        <div className="absolute z-10 w-full bg-white border border-gray-200 mt-1 rounded-lg shadow-xl max-h-48 overflow-y-auto">
                                            {filteredProductos.length > 0 ? filteredProductos.map(p => (
                                                <div
                                                    key={p.id}
                                                    className="px-4 py-2 hover:bg-purple-50 cursor-pointer text-sm border-b border-gray-50 last:border-0"
                                                    onClick={() => {
                                                        setSelectedIngrediente(p);
                                                        setSearchTerm(p.nombre);
                                                    }}
                                                >
                                                    <span className="font-bold text-gray-700">{p.nombre}</span>
                                                    <span className="text-gray-400 text-xs ml-2">({p.codigo})</span>
                                                </div>
                                            )) : (
                                                <div className="px-4 py-2 text-gray-400 text-sm">No se encontraron productos.</div>
                                            )}
                                        </div>
                                    )}
                                </div>

                                <div className="w-32">
                                    <label className="text-xs font-bold text-gray-500 uppercase mb-1 block">Cantidad</label>
                                    <input
                                        type="number"
                                        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-center font-bold focus:ring-2 focus:ring-purple-500 outline-none"
                                        value={cantidadIngrediente}
                                        onChange={e => setCantidadIngrediente(e.target.value)}
                                    />
                                </div>

                                <button
                                    onClick={handleAddIngrediente}
                                    className="bg-purple-600 hover:bg-purple-700 text-white p-2.5 rounded-lg shadow-md transition-colors"
                                    title="Agregar Insumo"
                                >
                                    <FaPlus />
                                </button>
                            </div>

                            {/* Tabla de Insumos Agregados */}
                            <div className="overflow-hidden rounded-lg border border-gray-200">
                                <table className="w-full text-sm">
                                    <thead className="bg-gray-50 text-gray-600 font-semibold">
                                        <tr>
                                            <td className="px-4 py-3">Insumo / Material</td>
                                            <td className="px-4 py-3 text-center">Cant. Req.</td>
                                            <td className="px-4 py-3 text-right"></td>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-100">
                                        {detalles.length === 0 ? (
                                            <tr>
                                                <td colSpan="3" className="px-4 py-6 text-center text-gray-400 italic">
                                                    No se han agregado insumos.
                                                </td>
                                            </tr>
                                        ) : detalles.map((det, idx) => (
                                            <tr key={idx} className="hover:bg-gray-50">
                                                <td className="px-4 py-3 font-medium text-gray-700">{det.producto_nombre}</td>
                                                <td className="px-4 py-3 text-center bg-gray-50 font-mono text-gray-800">{det.cantidad}</td>
                                                <td className="px-4 py-3 text-right">
                                                    <button
                                                        onClick={() => handleRemoveIngrediente(det.insumo_id)}
                                                        className="text-red-400 hover:text-red-600 p-1"
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

                        {/* SECCIÓN RECURSOS (MOD / CIF) */}
                        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                            <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                                <FaMoneyBillWave className="text-orange-600" /> Mano de Obra y Costos Indirectos
                            </h3>

                            {/* Agregador de Recursos */}
                            <div className="flex flex-wrap items-end gap-3 mb-6 bg-orange-50 p-4 rounded-xl border border-orange-100">
                                <div className="flex-1 min-w-[200px]">
                                    <label className="text-xs font-bold text-gray-500 uppercase mb-1 block">Descripción del Recurso</label>
                                    <input
                                        type="text"
                                        placeholder="Ej: Mano de Obra Operario, Energía, Agua..."
                                        className="w-full px-3 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-orange-500 outline-none"
                                        value={newRecursoDesc}
                                        onChange={(e) => setNewRecursoDesc(e.target.value)}
                                    />
                                </div>

                                <div className="w-48">
                                    <label className="text-xs font-bold text-gray-500 uppercase mb-1 block">Tipo de Costo</label>
                                    <select
                                        className="w-full border border-gray-300 rounded-lg px-3 py-2 bg-white focus:ring-2 focus:ring-orange-500 outline-none"
                                        value={newRecursoTipo}
                                        onChange={(e) => setNewRecursoTipo(e.target.value)}
                                    >
                                        <option value="MANO_OBRA_DIRECTA">Mano de Obra (MOD)</option>
                                        <option value="COSTO_INDIRECTO_FABRICACION">Costo Indirecto (CIF)</option>
                                    </select>
                                </div>

                                <div className="w-32">
                                    <label className="text-xs font-bold text-gray-500 uppercase mb-1 block">Costo Est. ($)</label>
                                    <input
                                        type="number"
                                        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-center font-bold focus:ring-2 focus:ring-orange-500 outline-none"
                                        value={newRecursoCosto}
                                        onChange={e => setNewRecursoCosto(e.target.value)}
                                    />
                                </div>

                                <button
                                    onClick={handleAddRecurso}
                                    className="bg-orange-600 hover:bg-orange-700 text-white p-2.5 rounded-lg shadow-md transition-colors"
                                    title="Agregar Recurso"
                                >
                                    <FaPlus />
                                </button>
                            </div>

                            {/* Tabla de Recursos Agregados */}
                            <div className="overflow-hidden rounded-lg border border-gray-200">
                                <table className="w-full text-sm">
                                    <thead className="bg-gray-50 text-gray-600 font-semibold">
                                        <tr>
                                            <td className="px-4 py-3">Concepto</td>
                                            <td className="px-4 py-3 text-center">Tipo</td>
                                            <td className="px-4 py-3 text-right">Costo Estimado</td>
                                            <td className="px-4 py-3 text-right"></td>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-100">
                                        {recursos.length === 0 ? (
                                            <tr>
                                                <td colSpan="4" className="px-4 py-6 text-center text-gray-400 italic">
                                                    No se han agregado recursos adicionales.
                                                </td>
                                            </tr>
                                        ) : recursos.map((rec, idx) => (
                                            <tr key={idx} className="hover:bg-gray-50">
                                                <td className="px-4 py-3 font-medium text-gray-700">{rec.descripcion}</td>
                                                <td className="px-4 py-3 text-center">
                                                    <span className={`text-xs px-2 py-1 rounded font-bold ${rec.tipo === 'MANO_OBRA_DIRECTA' ? 'bg-blue-100 text-blue-700' : 'bg-yellow-100 text-yellow-700'}`}>
                                                        {rec.tipo === 'MANO_OBRA_DIRECTA' ? 'MOD' : 'CIF'}
                                                    </span>
                                                </td>
                                                <td className="px-4 py-3 text-right font-mono text-gray-800">
                                                    ${rec.costo_estimado.toLocaleString()}
                                                </td>
                                                <td className="px-4 py-3 text-right">
                                                    <button
                                                        onClick={() => handleRemoveRecurso(idx)}
                                                        className="text-red-400 hover:text-red-600 p-1"
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

                    </div>
                </div>
            )}
        </div>
    );
}
