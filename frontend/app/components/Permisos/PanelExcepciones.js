'use client';
import React, { useState, useEffect, useMemo } from 'react';
import { FaTimes, FaSpinner, FaShieldAlt, FaCheck, FaBan, FaUndo, FaTrash, FaSave, FaSearch } from 'react-icons/fa';
import { getPermisosConEstado, upsertExcepciones, resetExcepciones } from '@/lib/rolesApiService';

/**
 * Drawer lateral para gestionar las excepciones de permisos de un usuario específico.
 * Muestra cada permiso con 3 estados: heredado del rol, concedido manualmente, revocado manualmente.
 * 
 * Props:
 *   usuario    — objeto del usuario { id, nombre_completo, email, roles }
 *   onClose    — función para cerrar el drawer
 */
export default function PanelExcepciones({ usuario, onClose }) {
    const [permisos, setPermisos] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [busqueda, setBusqueda] = useState('');
    // pendientes: mapa { permiso_id -> true(conceder)|false(revocar)|null(limpiar) }
    const [pendientes, setPendientes] = useState({});
    const [toast, setToast] = useState(null);

    const showToast = (msg, tipo = 'ok') => {
        setToast({ msg, tipo });
        setTimeout(() => setToast(null), 3000);
    };

    const cargar = async () => {
        setIsLoading(true);
        try {
            const data = await getPermisosConEstado(usuario.id);
            setPermisos(data);
        } catch {
            showToast('Error cargando permisos', 'error');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => { cargar(); }, [usuario.id]);

    // Permisos filtrados por búsqueda
    const permisosFiltrados = useMemo(() => {
        if (!busqueda.trim()) return permisos;
        const q = busqueda.toLowerCase();
        return permisos.filter(p =>
            p.nombre.toLowerCase().includes(q) ||
            (p.descripcion || '').toLowerCase().includes(q)
        );
    }, [permisos, busqueda]);

    // Agrupar por módulo (prefijo antes de ":")
    const grupos = useMemo(() => {
        const map = {};
        permisosFiltrados.forEach(p => {
            const modulo = p.nombre.split(':')[0];
            if (!map[modulo]) map[modulo] = [];
            map[modulo].push(p);
        });
        return map;
    }, [permisosFiltrados]);

    // Calcular el estado visual efectivo considerando cambios pendientes
    const getEstadoEfectivo = (p) => {
        if (p.id in pendientes) {
            const val = pendientes[p.id];
            if (val === null) return p.tiene_por_rol; // removiendo excepción
            return val;
        }
        return p.estado_efectivo;
    };

    const getTipoPendiente = (p) => {
        if (!(p.id in pendientes)) return null;
        return pendientes[p.id]; // true, false, o null (quitar excepción)
    };

    const handleConceder = (p) => {
        setPendientes(prev => ({ ...prev, [p.id]: true }));
    };

    const handleRevocar = (p) => {
        setPendientes(prev => ({ ...prev, [p.id]: false }));
    };

    const handleRestaurar = (p) => {
        // Quitar del mapa de pendientes → hereda rol
        setPendientes(prev => {
            const next = { ...prev };
            delete next[p.id];
            return next;
        });
    };

    const hayPendientes = Object.keys(pendientes).length > 0;

    const guardar = async () => {
        setIsSaving(true);
        try {
            const excepciones = Object.entries(pendientes)
                .filter(([, val]) => val !== null)
                .map(([permiso_id, permitido]) => ({ permiso_id: parseInt(permiso_id), permitido }));

            if (excepciones.length > 0) {
                await upsertExcepciones(usuario.id, excepciones);
            }

            // Los que quedaron en null deben eliminarse (volver al rol)
            const aEliminar = Object.entries(pendientes)
                .filter(([, val]) => val === null)
                .map(([permiso_id]) => parseInt(permiso_id));

            // Si hay excepciones a eliminar individualmente, hacemos reset total
            // y re-aplicamos las que sí queremos (más simple y seguro)
            if (aEliminar.length > 0 && excepciones.length === 0) {
                await resetExcepciones(usuario.id);
            } else if (aEliminar.length > 0) {
                // Reset total y re-aplicar solo las que queremos mantener
                await resetExcepciones(usuario.id);
                // Re-obtener todas las excepciones vigentes del estado actual + nuevas
                const todasLasExcepciones = permisos
                    .filter(p => p.tiene_excepcion && !aEliminar.includes(p.id))
                    .map(p => ({ permiso_id: p.id, permitido: p.excepcion_permitido }));
                const combinadas = [...todasLasExcepciones, ...excepciones];
                if (combinadas.length > 0) {
                    await upsertExcepciones(usuario.id, combinadas);
                }
            }

            setPendientes({});
            showToast('Permisos guardados correctamente');
            cargar();
        } catch {
            showToast('Error al guardar los cambios', 'error');
        } finally {
            setIsSaving(false);
        }
    };

    const MODULO_LABELS = {
        contabilidad: 'Contabilidad',
        empresa: 'Empresa y Admin',
        utilidades: 'Utilidades',
        inventario: 'Inventario',
        nomina: 'Nómina',
        soporte: 'Soporte',
        plantilla: 'Plantillas',
    };

    return (
        <div className="fixed inset-0 z-50 flex justify-end">
            {/* Overlay */}
            <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />

            {/* Drawer */}
            <div className="relative w-full max-w-2xl bg-white h-full flex flex-col shadow-2xl animate-slideInRight">

                {/* Header */}
                <div className="bg-gradient-to-r from-indigo-700 to-indigo-900 text-white px-6 py-5 shrink-0">
                    <div className="flex justify-between items-start">
                        <div className="flex items-center gap-3">
                            <div className="bg-white/20 p-2.5 rounded-lg">
                                <FaShieldAlt className="text-xl" />
                            </div>
                            <div>
                                <h2 className="font-bold text-lg leading-tight">Permisos Personalizados</h2>
                                <p className="text-indigo-200 text-sm mt-0.5">{usuario.nombre_completo || usuario.email}</p>
                                <p className="text-indigo-300 text-xs mt-0.5">
                                    Rol: <span className="font-semibold text-white">{usuario.roles?.[0]?.nombre || 'Sin rol'}</span>
                                </p>
                            </div>
                        </div>
                        <button onClick={onClose} className="text-white/70 hover:text-white hover:bg-white/10 p-2 rounded-lg transition-colors">
                            <FaTimes />
                        </button>
                    </div>

                    {/* Leyenda */}
                    <div className="flex gap-4 mt-4 text-xs">
                        <span className="flex items-center gap-1.5 bg-white/10 px-2 py-1 rounded">
                            <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block" /> Activo por rol
                        </span>
                        <span className="flex items-center gap-1.5 bg-white/10 px-2 py-1 rounded">
                            <span className="w-2 h-2 rounded-full bg-blue-400 inline-block" /> Concedido manual
                        </span>
                        <span className="flex items-center gap-1.5 bg-white/10 px-2 py-1 rounded">
                            <span className="w-2 h-2 rounded-full bg-red-400 inline-block" /> Revocado manual
                        </span>
                    </div>
                </div>

                {/* Barra de búsqueda */}
                <div className="px-6 py-3 border-b border-gray-100 bg-gray-50 shrink-0">
                    <div className="relative">
                        <FaSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm" />
                        <input
                            type="text"
                            value={busqueda}
                            onChange={e => setBusqueda(e.target.value)}
                            placeholder="Buscar permiso..."
                            className="w-full pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none bg-white"
                        />
                    </div>
                </div>

                {/* Lista de permisos */}
                <div className="flex-1 overflow-y-auto px-6 py-4 space-y-5">
                    {isLoading ? (
                        <div className="flex flex-col items-center justify-center h-40 gap-3 text-gray-400">
                            <FaSpinner className="animate-spin text-3xl text-indigo-400" />
                            <p className="text-sm">Cargando permisos...</p>
                        </div>
                    ) : Object.keys(grupos).length === 0 ? (
                        <div className="text-center py-12 text-gray-400 text-sm">
                            No se encontraron permisos.
                        </div>
                    ) : (
                        Object.entries(grupos).map(([modulo, items]) => (
                            <div key={modulo}>
                                <h3 className="text-xs font-bold uppercase tracking-widest text-indigo-600 mb-2 pb-1 border-b border-indigo-50">
                                    {MODULO_LABELS[modulo] || modulo}
                                </h3>
                                <div className="space-y-1.5">
                                    {items.map(p => {
                                        const efectivo = getEstadoEfectivo(p);
                                        const tipoPend = getTipoPendiente(p);
                                        const esPendiente = p.id in pendientes;

                                        // Determinar color de fila
                                        let rowClass = 'bg-white border-gray-100';
                                        if (esPendiente && tipoPend === true) rowClass = 'bg-blue-50 border-blue-200';
                                        else if (esPendiente && tipoPend === false) rowClass = 'bg-red-50 border-red-200';
                                        else if (esPendiente && tipoPend === null) rowClass = 'bg-amber-50 border-amber-200';
                                        else if (p.tiene_excepcion && p.excepcion_permitido === true) rowClass = 'bg-blue-50 border-blue-200';
                                        else if (p.tiene_excepcion && p.excepcion_permitido === false) rowClass = 'bg-red-50 border-red-200';

                                        return (
                                            <div key={p.id} className={`flex items-center justify-between px-3 py-2.5 rounded-lg border ${rowClass} transition-colors`}>
                                                <div className="flex items-center gap-2.5 min-w-0">
                                                    {/* Semáforo */}
                                                    <span className={`shrink-0 w-2.5 h-2.5 rounded-full ${
                                                        efectivo
                                                            ? (esPendiente && tipoPend === true) || (p.tiene_excepcion && p.excepcion_permitido === true && !esPendiente)
                                                                ? 'bg-blue-500'
                                                                : 'bg-emerald-500'
                                                            : 'bg-red-400'
                                                    }`} />
                                                    <div className="min-w-0">
                                                        <p className="text-xs font-semibold text-gray-800 truncate">{p.nombre.split(':')[1] || p.nombre}</p>
                                                        {p.descripcion && <p className="text-[10px] text-gray-400 truncate">{p.descripcion}</p>}
                                                    </div>
                                                </div>

                                                {/* Acciones */}
                                                <div className="flex items-center gap-1 shrink-0 ml-2">
                                                    {/* Badge de estado */}
                                                    {(esPendiente || p.tiene_excepcion) && (
                                                        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded mr-1 ${
                                                            (esPendiente ? tipoPend === true : p.excepcion_permitido === true)
                                                                ? 'bg-blue-100 text-blue-700'
                                                                : esPendiente && tipoPend === null
                                                                    ? 'bg-amber-100 text-amber-700'
                                                                    : 'bg-red-100 text-red-700'
                                                        }`}>
                                                            {esPendiente && tipoPend === null ? 'RESTAURANDO' : esPendiente
                                                                ? tipoPend ? 'CONCEDER' : 'REVOCAR'
                                                                : p.excepcion_permitido ? 'MANUAL ✓' : 'REVOCADO'}
                                                        </span>
                                                    )}

                                                    {/* Botón Conceder */}
                                                    <button
                                                        title="Conceder manualmente"
                                                        onClick={() => handleConceder(p)}
                                                        disabled={esPendiente && tipoPend === true}
                                                        className={`p-1.5 rounded text-xs transition-colors ${
                                                            (esPendiente && tipoPend === true) || (!esPendiente && p.tiene_excepcion && p.excepcion_permitido === true)
                                                                ? 'bg-blue-500 text-white'
                                                                : 'text-gray-400 hover:bg-blue-50 hover:text-blue-600'
                                                        }`}
                                                    >
                                                        <FaCheck />
                                                    </button>

                                                    {/* Botón Revocar */}
                                                    <button
                                                        title="Revocar manualmente"
                                                        onClick={() => handleRevocar(p)}
                                                        disabled={esPendiente && tipoPend === false}
                                                        className={`p-1.5 rounded text-xs transition-colors ${
                                                            (esPendiente && tipoPend === false) || (!esPendiente && p.tiene_excepcion && p.excepcion_permitido === false)
                                                                ? 'bg-red-500 text-white'
                                                                : 'text-gray-400 hover:bg-red-50 hover:text-red-600'
                                                        }`}
                                                    >
                                                        <FaBan />
                                                    </button>

                                                    {/* Botón Restaurar (solo si tiene excepción o pendiente) */}
                                                    {(p.tiene_excepcion || esPendiente) && (
                                                        <button
                                                            title="Volver al rol base"
                                                            onClick={() => handleRestaurar(p)}
                                                            className="p-1.5 rounded text-xs text-gray-400 hover:bg-amber-50 hover:text-amber-600 transition-colors"
                                                        >
                                                            <FaUndo />
                                                        </button>
                                                    )}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        ))
                    )}
                </div>

                {/* Footer con acciones */}
                <div className="px-6 py-4 border-t border-gray-100 bg-gray-50 shrink-0">
                    {hayPendientes && (
                        <div className="mb-3 bg-amber-50 border border-amber-200 text-amber-800 text-xs px-3 py-2 rounded-lg flex items-center gap-2">
                            <span className="font-bold">{Object.keys(pendientes).length}</span> cambio(s) sin guardar
                        </div>
                    )}
                    <div className="flex gap-3">
                        <button
                            onClick={onClose}
                            className="flex-1 py-2.5 text-sm font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                        >
                            Cerrar
                        </button>
                        <button
                            onClick={guardar}
                            disabled={!hayPendientes || isSaving}
                            className="flex-1 py-2.5 text-sm font-bold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:bg-gray-200 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
                        >
                            {isSaving ? <><FaSpinner className="animate-spin" /> Guardando...</> : <><FaSave /> Guardar Cambios</>}
                        </button>
                    </div>
                </div>
            </div>

            {/* Toast */}
            {toast && (
                <div className={`fixed bottom-6 right-6 z-[60] px-4 py-3 rounded-xl shadow-lg text-sm font-medium text-white transition-all ${toast.tipo === 'error' ? 'bg-red-500' : 'bg-emerald-500'}`}>
                    {toast.msg}
                </div>
            )}
        </div>
    );
}
