// frontend/app/admin/utilidades/configuracion-favoritos/page.js (REEMPLAZO COMPLETO - LÍMITE 16)
'use client';

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { FaTrash, FaCheck, FaExclamationTriangle, FaPlus } from 'react-icons/fa';
import { toast, ToastContainer } from 'react-toastify';
// La importación de CSS debe estar en globals.css
// import 'react-toastify/dist/react-toastify.css';

// --- Servicios ---
import { getFavoritos, createFavorito, deleteFavorito } from '@/lib/favoritosService';
// Importamos la estructura del menú desde la librería centralizada
import { menuStructure } from '@/lib/menuData';
import BotonRegresar from '@/app/components/BotonRegresar'; // Asumiendo esta ruta

// ====================================================================
// CONSTANTE DE CAPACIDAD CENTRALIZADA (FIX CRÍTICO)
// El límite anterior de 12 se amplía a 16.
// ====================================================================
const MAX_FAVORITES_CAPACITY = 16;


const mapMenuToOptions = (menu) => {
    const options = [];
    menu.forEach(module => {
        // Módulos con enlaces directos
        if (module.links) {
            module.links.forEach(link => {
                options.push({
                    value: link.href,
                    label: `${module.name} > ${link.name}`
                });
            });
        }
        // Módulos con subgrupos (ej. Administración)
        if (module.subgroups) {
            module.subgroups.forEach(subgroup => {
                subgroup.links.forEach(link => {
                    options.push({
                        value: link.href,
                        label: `${module.name} > ${subgroup.title} > ${link.name}`
                    });
                });
            });
        }
    });
    return options;
};

// ====================================================================
// COMPONENTE PRINCIPAL
// ====================================================================

export default function ConfiguracionFavoritosPage() {
    const router = useRouter();
    const [favoritos, setFavoritos] = useState([]);
    const [maestros, setMaestros] = useState({ availableRoutes: [], nextOrder: 1 });
    const [loading, setLoading] = useState(true);
    const [newFavorite, setNewFavorite] = useState({ ruta_enlace: '', nombre_personalizado: '', orden: 1 });
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Lista plana de todas las rutas válidas
    const allRoutes = useMemo(() => mapMenuToOptions(menuStructure), []);

    // Generación dinámica de todas las posiciones posibles (1 a 16)
    const ALL_ORDERS = useMemo(() => Array.from({ length: MAX_FAVORITES_CAPACITY }, (_, i) => i + 1), []);


    const fetchFavoritos = useCallback(async () => {
        setLoading(true);
        try {
            const currentFavs = await getFavoritos();

            // 1. Determinar las posiciones ocupadas
            const occupiedOrders = currentFavs.map(f => f.orden);
            let nextOrder = 1;
            // FIX: El bucle ahora respeta el nuevo límite de 16
            while (occupiedOrders.includes(nextOrder) && nextOrder <= MAX_FAVORITES_CAPACITY) {
                nextOrder++;
            }

            // 2. Mapear las rutas para saber cuáles están disponibles
            const occupiedRoutes = new Set(currentFavs.map(f => f.ruta_enlace));
            const availableRoutes = allRoutes.filter(route => !occupiedRoutes.has(route.value));

            setFavoritos(currentFavs.sort((a, b) => a.orden - b.orden));
            setMaestros({ availableRoutes, nextOrder });
            setNewFavorite(prev => ({ ...prev, orden: nextOrder })); // Preseleccionar la próxima posición disponible

        } catch (error) {
            toast.error("Error al cargar la configuración de favoritos.");
            console.error(error);
        } finally {
            setLoading(false);
        }
    }, [allRoutes]);

    useEffect(() => {
        fetchFavoritos();
    }, [fetchFavoritos]);




    const handleCreate = async (e) => {
        e.preventDefault();

        if (favoritos.length >= MAX_FAVORITES_CAPACITY) {
            toast.warning(`Ya has alcanzado el límite de ${MAX_FAVORITES_CAPACITY} accesos rápidos.`);
            return;
        }

        setIsSubmitting(true);
        try {
            const suggestedRoute = allRoutes.find(r => r.value === newFavorite.ruta_enlace);

            const payload = {
                ruta_enlace: newFavorite.ruta_enlace,
                nombre_personalizado: newFavorite.nombre_personalizado.trim() || suggestedRoute.label.split(' > ').pop(),
                orden: newFavorite.orden,
            };

            // SONDA 1: Muestra el payload antes de enviarlo
            console.log("SONDA DE ENVÍO - Payload:", payload);

            await createFavorito(payload);
            toast.success("Acceso rápido creado y guardado.");
            setNewFavorite({ ruta_enlace: '', nombre_personalizado: '', orden: maestros.nextOrder });
            fetchFavoritos();

        } catch (error) {
            // SONDA 2: Captura y muestra el cuerpo de la respuesta del error 422
            const backendDetail = error.response?.data?.detail;
            console.error("SONDA DE ERROR - Respuesta del Backend 422:", backendDetail);

            let errorMsg = "Error desconocido al crear el favorito.";

            if (Array.isArray(backendDetail)) {
                // Falla de Pydantic (ej. orden > 16 o campo incorrecto)
                errorMsg = `Error de Validación en campo '${backendDetail[0]?.loc[1]}': ${backendDetail[0]?.msg}`;
            } else if (typeof backendDetail === 'string') {
                // Falla del Servicio (ej. el límite de 12 sigue activo en el Backend)
                errorMsg = backendDetail;
            }

            toast.error(`Fallo: ${errorMsg}`);
            console.error(error);

        } finally {
            setIsSubmitting(false);
        }
    };





    const handleDelete = async (id, nombre) => {
        if (!confirm(`¿Está seguro de eliminar el acceso rápido: ${nombre}?`)) return;

        try {
            await deleteFavorito(id);
            toast.success("Acceso rápido eliminado.");
            fetchFavoritos();
        } catch (error) {
            toast.error("Error al eliminar el favorito.");
        }
    };

    if (loading) return <div className="text-center mt-10"><span className="loading loading-spinner loading-lg text-primary"></span></div>;


    // Obtener las posiciones disponibles para el selector de orden
    const occupiedOrders = favoritos.map(f => f.orden);

    // Filtramos las posiciones no ocupadas (de 1 a 16)
    const availableOrders = ALL_ORDERS.filter(n => !occupiedOrders.includes(n));

    // Si la orden actual es válida o es una orden existente, la incluimos
    if (newFavorite.orden > 0 && newFavorite.orden <= MAX_FAVORITES_CAPACITY && !availableOrders.includes(newFavorite.orden)) {
        availableOrders.push(newFavorite.orden);
    }
    availableOrders.sort((a, b) => a - b);


    return (
        <div className="container mx-auto p-4 md:p-8">
            <ToastContainer position="top-right" autoClose={5000} hideProgressBar={false} newestOnTop={false} closeOnClick rtl={false} pauseOnFocusLoss draggable pauseOnHover />
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl md:text-3xl font-bold">🛠️ Configuración de Accesos Rápidos</h1>
                <Link href="/" className="btn btn-sm btn-outline">
                    Regresar al Panel Principal
                </Link>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-lg border border-gray-200">
                {/* FIX VISUAL: El mensaje ahora refleja la capacidad de 16 */}
                <h2 className="text-xl font-semibold mb-4">Favoritos Actuales ({favoritos.length} de {MAX_FAVORITES_CAPACITY})</h2>

                {/* Tabla de Favoritos Existentes */}
                <div className="overflow-x-auto mb-8">
                    <table className="min-w-full table table-zebra">
                        <thead className="bg-slate-100">
                            <tr>
                                <th className="px-4 py-2 w-1/12">Orden</th>
                                <th className="px-4 py-2 w-4/12">Nombre Personalizado</th>
                                <th className="px-4 py-2 w-5/12">Ruta de Origen</th>
                                <th className="px-4 py-2 w-1/12 text-center">Acción</th>
                            </tr>
                        </thead>
                        <tbody>
                            {favoritos.map((fav) => (
                                <tr key={fav.id}>
                                    <td className="px-4 py-2 text-center font-bold text-lg">{fav.orden}</td>
                                    <td className="px-4 py-2">{fav.nombre_personalizado}</td>
                                    <td className="px-4 py-2 font-mono text-sm">{fav.ruta_enlace}</td>
                                    <td className="px-4 py-2 text-center">
                                        <button onClick={() => handleDelete(fav.id, fav.nombre_personalizado)} className="btn btn-ghost btn-xs text-red-500 hover:text-red-700">
                                            <FaTrash />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                        {favoritos.length === 0 && (
                            <tfoot><tr><td colSpan="4" className="text-center text-gray-500 py-4 italic">No hay accesos rápidos configurados.</td></tr></tfoot>
                        )}
                    </table>
                </div>

                {/* Formulario para Añadir Nuevo Favorito */}
                {/* FIX: La visibilidad del formulario ahora se basa en MAX_FAVORITES_CAPACITY */}
                {favoritos.length < MAX_FAVORITES_CAPACITY && (
                    <form onSubmit={handleCreate} className="space-y-4 border p-4 rounded-lg bg-blue-50">


                        <h3 className="text-lg font-semibold text-gray-800">Añadir Nuevo Acceso Rápido</h3>

                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                            {/* Selector de Ruta de Origen */}
                            <div className="md:col-span-2">
                                <label className="block text-sm font-medium text-gray-700">Ruta del Menú <span className="text-red-500">*</span></label>
                                <select
                                    required
                                    value={newFavorite.ruta_enlace}
                                    onChange={(e) => setNewFavorite(prev => ({ ...prev, ruta_enlace: e.target.value }))}
                                    className="select select-bordered w-full mt-1"
                                >
                                    <option value="">Seleccione una ruta...</option>
                                    {maestros.availableRoutes.map(route => (
                                        <option key={route.value} value={route.value}>{route.label}</option>
                                    ))}
                                </select>
                            </div>

                            {/* Nombre Personalizado */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Nombre Personalizado (Opcional)</label>
                                <input
                                    type="text"
                                    value={newFavorite.nombre_personalizado}
                                    onChange={(e) => setNewFavorite(prev => ({ ...prev, nombre_personalizado: e.target.value }))}
                                    placeholder={
                                        allRoutes.find(r => r.value === newFavorite.ruta_enlace)?.label.split(' > ').pop() || "Ej: Facturar Rápido"
                                    }
                                    className="input input-bordered w-full mt-1"
                                    maxLength="100"
                                />
                            </div>

                            {/* Selector de Orden */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Posición <span className="text-red-500">*</span></label>
                                <select
                                    required
                                    value={newFavorite.orden}
                                    onChange={(e) => setNewFavorite(prev => ({ ...prev, orden: parseInt(e.target.value) }))}
                                    className="select select-bordered w-full mt-1"
                                >
                                    {availableOrders.map(order => (
                                        <option key={order} value={order}>Posición {order}</option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        <button
                            type="submit"
                            className="btn btn-success mt-4 w-full md:w-auto"
                            disabled={isSubmitting || !newFavorite.ruta_enlace}
                        >
                            {isSubmitting ? <FaCheck className="animate-spin" /> : <FaPlus />}
                            {isSubmitting ? 'Guardando...' : 'Añadir Acceso Rápido'}
                        </button>
                    </form>
                )}

                {/* Mensaje de límite alcanzado */}
                {favoritos.length >= MAX_FAVORITES_CAPACITY && (
                    <div className="alert alert-warning mt-4">
                        <FaExclamationTriangle className="text-xl" />
                        <span>¡Límite alcanzado! Has configurado el máximo de {MAX_FAVORITES_CAPACITY} accesos rápidos.</span>
                    </div>
                )}
            </div>
        </div>
    );
}