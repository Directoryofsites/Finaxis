'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Select, { components } from 'react-select';
import {
    FaEdit,
    FaTrashAlt,
    FaPlus,
    FaTimes,
    FaFilePdf,
    FaSearch,
    FaBoxOpen,
    FaCubes,
    FaBook
} from 'react-icons/fa';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import debounce from 'lodash/debounce';

import { useAuth } from '../../context/AuthContext';
import {
    getProductosFiltrados,
    deleteProducto,
    getGruposInventario,
    generarPdfListaProductos
} from '../../../lib/inventarioService';

import InventarioFormModal from '../../components/Inventario/InventarioFormModal';


// --- ESTILOS REUSABLES (Manual v2.0) ---
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";

// --- COMPONENTE "ANTI-CHORRERO" ---
const CustomValueContainer = ({ children, ...props }) => {
    const selectedCount = props.getValue().length;
    if (selectedCount > 1) {
        return (
            <components.ValueContainer {...props}>
                <div className="text-sm font-semibold text-indigo-600 px-2 flex items-center">
                    <span className="bg-indigo-50 px-2 py-0.5 rounded-md border border-indigo-100">
                        ✅ {selectedCount} Grupos Seleccionados
                    </span>
                </div>
                {React.Children.map(children, child =>
                    child && child.type && child.type.name === 'Input' ? child : null
                )}
            </components.ValueContainer>
        );
    }
    return <components.ValueContainer {...props}>{children}</components.ValueContainer>;
};

const SELECT_ALL_OPTION = { label: "Seleccionar Todos", value: "all" };

export default function GestionInventarioPage() {
    const { user, loading: authLoading } = useAuth();
    const router = useRouter();
    const searchParams = useSearchParams();

    // Estados
    const [productos, setProductos] = useState([]);
    // ... rest of state

    useEffect(() => {
        // Listening for Deep Linking triggers
        const trigger = searchParams.get('trigger');

        if (trigger === 'new_item') {
            // Limpiamos el param de la URL para evitar re-aperturas no deseadas al recargar
            const newUrl = window.location.pathname;
            window.history.replaceState({}, '', newUrl);

            // Forzamos apertura del modal
            // Necesitamos esperar un tick para asegurar que todo el componente montó
            setTimeout(() => {
                handleOpenModal();
            }, 500);
        }
    }, [searchParams]);


    const [gruposOptions, setGruposOptions] = useState([]);
    const [selectedGroups, setSelectedGroups] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');

    const [isLoading, setIsLoading] = useState(true);
    const [isSearching, setIsSearching] = useState(false);
    const [isExportingPdf, setIsExportingPdf] = useState(false);
    const [error, setError] = useState('');

    const [isModalOpen, setIsModalOpen] = useState(false);
    const [productoAEditar, setProductoAEditar] = useState(null);

    const isMounted = useRef(false);

    // 1. Carga de Grupos
    useEffect(() => {
        if (authLoading) return;
        if (!user) { router.push('/login'); return; }

        const fetchGrupos = async () => {
            try {
                const data = await getGruposInventario();
                const options = data.map(g => ({ value: g.id, label: g.nombre }));
                setGruposOptions([SELECT_ALL_OPTION, ...options]);
            } catch (err) {
                toast.error("Error al cargar grupos.");
            }
        };
        fetchGrupos();
    }, [user, authLoading, router]);

    // 2. Búsqueda Centralizada
    const fetchProductos = useCallback(async (groups = [], term = '') => {
        setIsSearching(true);
        setError('');
        try {
            let grupoIdsParaApi = null;

            // Lógica inteligente de filtrado
            const isSelectAll = groups.some(g => g.value === 'all');
            if (!isSelectAll && groups.length > 0) {
                grupoIdsParaApi = groups.map(g => g.value);
            }

            const filtrosParaApi = {
                grupo_ids: grupoIdsParaApi,
                search_term: term === '' ? null : term,
            };

            const data = await getProductosFiltrados(filtrosParaApi);
            setProductos(data || []);
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al cargar productos.');
            setProductos([]);
        } finally {
            setIsLoading(false);
            setIsSearching(false);
        }
    }, []);

    // 3. Debounce para texto
    const debouncedSearch = useCallback(
        debounce((groups, term) => {
            fetchProductos(groups, term);
        }, 500),
        [fetchProductos]
    );

    // 4. Carga inicial
    useEffect(() => {
        if (user && !isMounted.current) {
            isMounted.current = true;
            fetchProductos([], '');
        }
    }, [user, fetchProductos]);

    // Handlers
    const handleGroupChange = (selected) => {
        let newSelection = selected || [];
        // Si se selecciona "Todos", limpiamos los demás o viceversa
        if (newSelection.some(opt => opt.value === 'all')) {
            if (selectedGroups.some(g => g.value === 'all')) {
                newSelection = []; // Deseleccionar si ya estaba
            } else {
                newSelection = [SELECT_ALL_OPTION];
            }
        } else {
            newSelection = newSelection.filter(opt => opt.value !== 'all');
        }

        setSelectedGroups(newSelection);

        // Si es "ALL", pasamos array vacío al fetch
        const groupsToFetch = newSelection.some(g => g.value === 'all') ? [] : newSelection;
        fetchProductos(groupsToFetch, searchTerm);
    };

    const handleSearchChange = (e) => {
        const val = e.target.value;
        setSearchTerm(val);
        const groupsToFetch = selectedGroups.some(g => g.value === 'all') ? [] : selectedGroups;
        debouncedSearch(groupsToFetch, val);
    };

    const clearSearch = () => {
        setSearchTerm('');
        const groupsToFetch = selectedGroups.some(g => g.value === 'all') ? [] : selectedGroups;
        fetchProductos(groupsToFetch, '');
    };

    const handleExportPDF = async () => {
        setIsExportingPdf(true);
        try {
            let grupoIdsParaApi = null;
            const isSelectAll = selectedGroups.some(g => g.value === 'all');
            if (!isSelectAll && selectedGroups.length > 0) {
                grupoIdsParaApi = selectedGroups.map(g => g.value);
            }

            const filtrosActuales = {
                grupo_ids: grupoIdsParaApi,
                search_term: searchTerm === '' ? null : searchTerm,
            };

            await generarPdfListaProductos(filtrosActuales);
            toast.success('Generando PDF...');
        } catch (err) {
            toast.error("Error al generar PDF.");
        } finally {
            setIsExportingPdf(false);
        }
    };

    const handleOpenModal = (producto = null) => {
        setProductoAEditar(producto);
        setIsModalOpen(true);
    };

    const handleSaveSuccess = () => {
        setIsModalOpen(false);
        setProductoAEditar(null);
        toast.success(productoAEditar ? 'Producto actualizado.' : 'Producto creado.');
        const groupsToFetch = selectedGroups.some(g => g.value === 'all') ? [] : selectedGroups;
        fetchProductos(groupsToFetch, searchTerm);
    };

    const handleDeleteProducto = async (productoId) => {
        if (!window.confirm('¿Está seguro de eliminar este producto?')) return;
        try {
            await deleteProducto(productoId);
            toast.success('Producto eliminado.');
            const groupsToFetch = selectedGroups.some(g => g.value === 'all') ? [] : selectedGroups;
            fetchProductos(groupsToFetch, searchTerm);
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Error al eliminar.');
        }
    };

    if (isLoading || authLoading) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
                <FaCubes className="text-indigo-300 text-6xl mb-4 animate-pulse" />
                <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando Inventario...</p>
            </div>
        );
    }

    return (
        <div className="container mx-auto p-6 md:p-8 bg-gray-50 min-h-screen font-sans pb-20">
            <ToastContainer position="top-right" autoClose={3000} />

            {/* HEADER */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                <div>
                    <div className="flex items-center gap-3 mt-3">
                        <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                            <FaCubes className="text-2xl" />
                        </div>
                        <div>
                            <div className="flex items-center gap-3">
                                <h1 className="text-3xl font-bold text-gray-800">Catálogo de Productos</h1>
                                <button
                                    onClick={() => window.open('/manual/capitulo_38_gestion_inventario.html', '_blank')}
                                    className="flex items-center gap-2 px-2 py-1 bg-white border border-indigo-200 text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors font-medium shadow-sm"
                                    title="Ver Manual"
                                >
                                    <FaBook /> <span className="hidden md:inline">Manual</span>
                                </button>
                            </div>
                            <p className="text-gray-500 text-sm">Administración de bienes y servicios.</p>
                        </div>
                    </div>
                </div>
                <div className="flex gap-3">
                    <button onClick={handleExportPDF} className="btn btn-outline btn-sm gap-2" disabled={isExportingPdf || isSearching}>
                        {isExportingPdf ? <span className="loading loading-spinner loading-xs"></span> : <FaFilePdf className="text-red-500" />}
                        PDF
                    </button>
                    <button onClick={() => handleOpenModal()} className="btn btn-primary btn-sm gap-2 shadow-md">
                        <FaPlus /> Nuevo Item
                    </button>
                </div>
            </div>

            {/* CARD DE FILTROS */}
            <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 mb-8 animate-fadeIn">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-end">

                    {/* Filtro Grupos */}
                    <div>
                        <label className={labelClass}>Filtrar por Grupo</label>
                        <Select
                            isMulti
                            options={gruposOptions}
                            value={selectedGroups}
                            onChange={handleGroupChange}
                            placeholder="Seleccionar grupos..."
                            components={{ ValueContainer: CustomValueContainer }}
                            styles={{
                                control: (base) => ({
                                    ...base,
                                    minHeight: '42px',
                                    borderRadius: '0.5rem',
                                    borderColor: '#D1D5DB',
                                    boxShadow: 'none',
                                    '&:hover': { borderColor: '#6366F1' }
                                }),
                                multiValue: (base) => ({ ...base, backgroundColor: '#E0E7FF' }),
                                multiValueLabel: (base) => ({ ...base, color: '#3730A3', fontWeight: '600' }),
                            }}
                            className="text-sm"
                        />
                    </div>

                    {/* Buscador */}
                    <div>
                        <label className={labelClass}>Buscar Artículo</label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <FaSearch className="text-gray-400" />
                            </div>
                            <input
                                type="text"
                                placeholder="Código, nombre o referencia..."
                                value={searchTerm}
                                onChange={handleSearchChange}
                                className="w-full pl-10 pr-10 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all outline-none"
                            />
                            {searchTerm && (
                                <button onClick={clearSearch} className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600">
                                    <FaTimes />
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {error && (
                <div className="alert alert-error shadow-sm mb-6 rounded-lg">
                    <span>{error}</span>
                </div>
            )}

            {/* CARD DE RESULTADOS */}
            <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden animate-slideDown">
                {/* Cabecera Tabla */}
                <div className="p-4 bg-gray-50 border-b border-gray-200 flex justify-between items-center">
                    <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                        Resultados
                        <span className="bg-gray-200 text-gray-700 px-2 py-0.5 rounded-md text-xs font-mono">
                            {productos.length} items
                        </span>
                    </h2>
                </div>

                {isSearching ? (
                    <div className="flex flex-col items-center justify-center p-12 text-gray-500">
                        <span className="loading loading-spinner loading-lg text-indigo-500 mb-2"></span>
                        <p>Buscando...</p>
                    </div>
                ) : !productos || productos.length === 0 ? (
                    <div className="flex flex-col items-center justify-center p-12 text-gray-400">
                        <FaBoxOpen className="text-4xl mb-2 opacity-30" />
                        <p className="italic">No se encontraron productos.</p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="table w-full">
                            <thead className="bg-slate-100 text-gray-600 text-xs uppercase font-bold">
                                <tr>
                                    <th className="py-3 pl-6">Código</th>
                                    <th className="py-3">Nombre</th>
                                    <th className="py-3">Grupo</th>
                                    <th className="py-3 text-right">Stock Total</th>
                                    <th className="py-3 text-right">Costo Prom.</th>
                                    <th className="py-3 text-right">Precio Base</th>
                                    <th className="py-3 text-center">Tipo</th>
                                    <th className="py-3 text-center pr-6">Acciones</th>
                                </tr>
                            </thead>
                            <tbody className="text-sm divide-y divide-gray-100">
                                {productos.map(producto => (
                                    <tr key={producto.id} className="hover:bg-indigo-50/20 transition-colors">
                                        <td className="pl-6 font-mono font-semibold text-indigo-900">{producto.codigo}</td>
                                        <td className="font-medium text-gray-700">{producto.nombre}</td>
                                        <td className="text-gray-500 text-xs">
                                            <span className="bg-gray-100 px-2 py-1 rounded-md border border-gray-200 text-gray-600 font-medium">
                                                {producto.grupo_inventario?.nombre || 'N/A'}
                                            </span>
                                        </td>

                                        <td className="text-right font-mono">
                                            {producto.es_servicio ? (
                                                <span className="text-gray-300">-</span>
                                            ) : (
                                                <span className={`font-bold ${producto.stock_total_calculado < 0 ? 'text-red-600' : 'text-gray-800'}`}>
                                                    {producto.stock_total_calculado?.toFixed(2)}
                                                </span>
                                            )}
                                        </td>

                                        <td className="text-right font-mono text-gray-600">
                                            {(!producto.es_servicio && producto.costo_promedio)
                                                ? `$ ${producto.costo_promedio.toLocaleString('es-CO', { minimumFractionDigits: 2 })}`
                                                : '-'}
                                        </td>

                                        <td className="text-right font-mono font-bold text-green-700">
                                            {(producto.precio_base_manual)
                                                ? `$ ${producto.precio_base_manual.toLocaleString('es-CO', { minimumFractionDigits: 0 })}`
                                                : '-'}
                                        </td>

                                        <td className="text-center">
                                            {producto.es_servicio
                                                ? <span className="px-2 py-1 rounded-full text-xs font-bold bg-blue-50 text-blue-600 border border-blue-100">Servicio</span>
                                                : <span className="px-2 py-1 rounded-full text-xs font-bold bg-green-50 text-green-600 border border-green-100">Bien</span>
                                            }
                                        </td>

                                        <td className="text-center pr-6">
                                            <div className="flex items-center justify-center gap-2">
                                                <button onClick={() => handleOpenModal(producto)} className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" title="Editar">
                                                    <FaEdit />
                                                </button>
                                                <button onClick={() => handleDeleteProducto(producto.id)} className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="Eliminar">
                                                    <FaTrashAlt />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Modal */}
            {isModalOpen && (
                <InventarioFormModal
                    isOpen={isModalOpen}
                    onClose={() => setIsModalOpen(false)}
                    onSaveSuccess={handleSaveSuccess}
                    onSaveError={(err) => toast.error(err.message || 'Error al guardar')}
                    productoAEditar={productoAEditar}
                />
            )}
        </div>
    );
}