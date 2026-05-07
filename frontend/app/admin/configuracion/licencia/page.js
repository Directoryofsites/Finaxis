'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/app/context/AuthContext';
import { apiService } from '@/lib/apiService';
import { toast } from 'react-toastify';
import {
    FaKey, FaCheckCircle, FaTimesCircle, FaLock, FaUnlock,
    FaSpinner, FaShieldAlt, FaInfoCircle, FaCalendarAlt,
    FaBuilding, FaChartBar, FaCopy
} from 'react-icons/fa';

// ─── Helpers ────────────────────────────────────────────────────────────────

function BadgeEstado({ version }) {
    if (version === 'FULL') {
        return (
            <span className="inline-flex items-center gap-1.5 bg-emerald-100 text-emerald-700 text-xs font-bold px-3 py-1 rounded-full border border-emerald-200">
                <FaUnlock className="text-xs" /> VERSIÓN COMPLETA
            </span>
        );
    }
    return (
        <span className="inline-flex items-center gap-1.5 bg-amber-100 text-amber-700 text-xs font-bold px-3 py-1 rounded-full border border-amber-200">
            <FaLock className="text-xs" /> MODO DEMO
        </span>
    );
}

function StatCard({ icon: Icon, label, value, color = 'indigo' }) {
    const colors = {
        indigo: 'bg-indigo-50 text-indigo-600 border-indigo-100',
        emerald: 'bg-emerald-50 text-emerald-600 border-emerald-100',
        amber: 'bg-amber-50 text-amber-600 border-amber-100',
    };
    return (
        <div className={`flex items-center gap-4 p-4 rounded-xl border ${colors[color]}`}>
            <div className="text-2xl">
                <Icon />
            </div>
            <div>
                <p className="text-xs font-semibold uppercase tracking-wide opacity-70">{label}</p>
                <p className="text-base font-bold">{value}</p>
            </div>
        </div>
    );
}

// ─── Página Principal ────────────────────────────────────────────────────────

export default function LicenciaPage() {
    const { user } = useAuth();

    // Estado de la licencia actual
    const [estado, setEstado] = useState(null);
    const [loadingEstado, setLoadingEstado] = useState(true);

    // Formulario de activación
    const [llave, setLlave] = useState('');
    const [activando, setActivando] = useState(false);
    const [mostrarFormulario, setMostrarFormulario] = useState(false);

    // ── Cargar estado al montar ──────────────────────────────────────────────
    useEffect(() => {
        if (user?.empresaId) {
            cargarEstado();
        }
    }, [user]);

    const cargarEstado = async () => {
        setLoadingEstado(true);
        try {
            const res = await apiService.get(`/licencia/estado/${user.empresaId}`);
            setEstado(res.data);
        } catch (error) {
            console.error('Error cargando estado de licencia:', error);
            toast.error('No se pudo cargar el estado de la licencia.');
        } finally {
            setLoadingEstado(false);
        }
    };

    // ── Activar licencia ─────────────────────────────────────────────────────
    const handleActivar = async (e) => {
        e.preventDefault();
        const llaveClean = llave.trim();
        if (!llaveClean) {
            return toast.warning('Por favor ingrese la llave de activación.');
        }

        setActivando(true);
        try {
            const res = await apiService.post('/licencia/activar', {
                empresa_id: user.empresaId,
                llave: llaveClean,
            });
            toast.success('¡Licencia activada correctamente! El programa está ahora en versión completa.');
            setLlave('');
            setMostrarFormulario(false);
            await cargarEstado(); // Refrescar estado
        } catch (error) {
            const msg = error.response?.data?.detail || 'Llave inválida o ya utilizada. Verifique e intente nuevamente.';
            toast.error(msg);
        } finally {
            setActivando(false);
        }
    };

    const handleCopiarLlave = () => {
        if (estado?.licencia_key) {
            navigator.clipboard.writeText(estado.licencia_key);
            toast.info('Llave copiada al portapapeles.');
        }
    };

    // ── Render ───────────────────────────────────────────────────────────────
    if (loadingEstado) {
        return (
            <div className="p-6 flex items-center justify-center min-h-[400px]">
                <div className="text-center text-gray-500">
                    <FaSpinner className="animate-spin text-4xl mx-auto mb-3 text-indigo-400" />
                    <p className="font-medium">Verificando estado de licencia...</p>
                </div>
            </div>
        );
    }

    const esCompleta = estado?.version === 'FULL';

    return (
        <div className="p-6 max-w-3xl mx-auto space-y-6">

            {/* ── Header ── */}
            <header className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                <div className="flex items-center justify-between flex-wrap gap-3">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-3">
                            <FaShieldAlt className="text-indigo-500" />
                            Licencia del Programa
                        </h1>
                        <p className="text-gray-500 mt-1 text-sm">
                            Gestione la activación y el estado de su licencia de Finaxis.
                        </p>
                    </div>
                    {estado && <BadgeEstado version={estado.version} />}
                </div>
            </header>

            {/* ── Panel de Estado Actual ── */}
            {estado && (
                <div className={`bg-white rounded-xl shadow-sm border p-6 space-y-5 ${esCompleta ? 'border-emerald-200' : 'border-amber-200'}`}>
                    <h2 className="text-base font-bold text-gray-700 border-b pb-3 flex items-center gap-2">
                        <FaInfoCircle className={esCompleta ? 'text-emerald-500' : 'text-amber-500'} />
                        Estado Actual de la Licencia
                    </h2>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        <StatCard
                            icon={esCompleta ? FaUnlock : FaLock}
                            label="Modalidad"
                            value={esCompleta ? 'Completa' : 'Demo'}
                            color={esCompleta ? 'emerald' : 'amber'}
                        />
                        <StatCard
                            icon={FaChartBar}
                            label="Límite mensual"
                            value={estado.limite === 'Ilimitado' ? '∞ Ilimitado' : `${estado.limite} registros`}
                            color={esCompleta ? 'emerald' : 'indigo'}
                        />
                        <StatCard
                            icon={FaCalendarAlt}
                            label="Activada el"
                            value={estado.activada_en
                                ? new Date(estado.activada_en).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
                                : 'No activada'}
                            color="indigo"
                        />
                    </div>

                    {/* Cliente registrado */}
                    {estado.cliente && (
                        <div className="flex items-center gap-3 bg-gray-50 rounded-lg px-4 py-3 border border-gray-100">
                            <FaBuilding className="text-gray-400" />
                            <div>
                                <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">Licencia registrada a</p>
                                <p className="text-sm font-bold text-gray-700">{estado.cliente}</p>
                            </div>
                        </div>
                    )}

                    {/* Llave activa (parcial) */}
                    {estado.licencia_key && (
                        <div className="flex items-center justify-between gap-3 bg-gray-50 rounded-lg px-4 py-3 border border-gray-100">
                            <div className="flex items-center gap-3 min-w-0">
                                <FaKey className="text-gray-400 flex-shrink-0" />
                                <div className="min-w-0">
                                    <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">Llave de activación</p>
                                    <code className="text-xs font-mono text-gray-600 break-all">
                                        {estado.licencia_key.substring(0, 30)}...
                                    </code>
                                </div>
                            </div>
                            <button
                                onClick={handleCopiarLlave}
                                title="Copiar llave completa"
                                className="text-gray-400 hover:text-indigo-500 transition-colors p-2 rounded-lg hover:bg-indigo-50 flex-shrink-0"
                            >
                                <FaCopy />
                            </button>
                        </div>
                    )}
                </div>
            )}

            {/* ── SECCIÓN DE IDENTIFICACIÓN DE EQUIPO (MACHINE ID) ── */}
            <div className="bg-white rounded-xl shadow-sm border border-indigo-100 p-6">
                <div className="flex items-start gap-4">
                    <div className="bg-indigo-50 rounded-full p-3 flex-shrink-0">
                        <FaShieldAlt className="text-indigo-600 text-xl" />
                    </div>
                    <div className="flex-1">
                        <h3 className="font-bold text-gray-800 text-base">Identificación de este Equipo</h3>
                        <p className="text-sm text-gray-500 mt-1 leading-relaxed">
                            Para activar su licencia, proporcione este código a su proveedor de software. 
                            Este código es único para este computador.
                        </p>
                        
                        <div className="mt-4 flex items-center gap-3">
                            <div className="bg-gray-100 border border-gray-200 rounded-lg px-4 py-2 font-mono font-bold text-indigo-700 text-lg tracking-wider">
                                {estado?.machine_id_actual || '---'}
                            </div>
                            <button
                                onClick={() => {
                                    navigator.clipboard.writeText(estado?.machine_id_actual || '');
                                    toast.info('ID de equipo copiado al portapapeles.');
                                }}
                                className="bg-white border border-gray-300 hover:border-indigo-500 hover:text-indigo-600 text-gray-600 px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2 transition-all shadow-sm"
                            >
                                <FaCopy /> Copiar ID
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* ── MODO BLOQUEADO (Cambio de Máquina) ── */}
            {estado?.modo === 'BLOQUEADO' && (
                <div className="bg-red-50 border border-red-200 rounded-xl p-5">
                    <div className="flex items-start gap-4">
                        <div className="bg-red-100 rounded-full p-3 flex-shrink-0">
                            <FaLock className="text-red-600 text-xl" />
                        </div>
                        <div className="flex-1">
                            <h3 className="font-bold text-red-800 text-base">Acceso Bloqueado: Cambio de Hardware</h3>
                            <p className="text-sm text-red-700 mt-1 leading-relaxed">
                                {estado.error || 'Esta licencia pertenece a otro computador. No puede operar el sistema en este equipo con esa llave.'}
                            </p>
                            <button
                                onClick={() => setMostrarFormulario(true)}
                                className="mt-4 bg-red-600 hover:bg-red-700 text-white font-bold px-5 py-2.5 rounded-lg text-sm flex items-center gap-2 transition-colors shadow-sm"
                            >
                                <FaKey /> Ingresar Nueva Llave para este PC
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* ── Banner Demo (solo si está en demo y no bloqueado) ── */}
            {!esCompleta && estado?.modo !== 'BLOQUEADO' && (
                <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-xl p-5">
                    <div className="flex items-start gap-4">
                        <div className="bg-amber-100 rounded-full p-3 flex-shrink-0">
                            <FaLock className="text-amber-600 text-xl" />
                        </div>
                        <div className="flex-1">
                            <h3 className="font-bold text-amber-800 text-base">Programa en Modo Demo</h3>
                            <p className="text-sm text-amber-700 mt-1 leading-relaxed">
                                Está usando la versión de demostración con un límite de <strong>{estado?.limite ?? 200} registros por mes</strong>.
                                Para trabajar sin restricciones, ingrese su llave de activación suministrada por Finaxis.
                            </p>
                            {!mostrarFormulario && (
                                <button
                                    onClick={() => setMostrarFormulario(true)}
                                    className="mt-4 bg-amber-600 hover:bg-amber-700 text-white font-bold px-5 py-2.5 rounded-lg text-sm flex items-center gap-2 transition-colors shadow-sm"
                                >
                                    <FaKey /> Ingresar Llave de Activación
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* ── Formulario de Activación ── */}
            {(mostrarFormulario || esCompleta) && (
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                    <h2 className="text-base font-bold text-gray-700 border-b pb-3 mb-5 flex items-center gap-2">
                        <FaKey className="text-indigo-500" />
                        {esCompleta ? 'Actualizar / Reemplazar Llave' : 'Activar Licencia Completa'}
                    </h2>

                    <form onSubmit={handleActivar} className="space-y-4">
                        <div>
                            <label className="block text-sm font-bold text-gray-700 mb-2">
                                Llave de Activación
                            </label>
                            <p className="text-xs text-gray-500 mb-3">
                                Ingrese exactamente la llave que le fue enviada por correo electrónico.
                                La llave distingue mayúsculas y minúsculas.
                            </p>
                            <textarea
                                id="llave-activacion"
                                value={llave}
                                onChange={(e) => setLlave(e.target.value)}
                                rows={3}
                                placeholder="eyJ... (pegue aquí su llave de activación)"
                                className="w-full border-2 border-gray-200 rounded-xl px-4 py-3 font-mono text-sm text-gray-700 focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 outline-none transition-all resize-none placeholder:text-gray-300"
                                disabled={activando}
                            />
                        </div>

                        <div className="bg-blue-50 border border-blue-100 rounded-lg px-4 py-3 text-xs text-blue-700 flex items-start gap-2">
                            <FaInfoCircle className="flex-shrink-0 mt-0.5" />
                            <span>
                                La llave está ligada a esta empresa. Una vez activada, el programa pasará
                                inmediatamente a modo completo sin necesidad de reiniciar.
                            </span>
                        </div>

                        <div className="flex items-center gap-3 pt-2">
                            <button
                                type="submit"
                                disabled={activando || !llave.trim()}
                                className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white font-bold px-7 py-2.5 rounded-lg flex items-center gap-2 transition-colors shadow-sm disabled:cursor-not-allowed"
                            >
                                {activando ? (
                                    <><FaSpinner className="animate-spin" /> Activando...</>
                                ) : (
                                    <><FaCheckCircle /> Activar Licencia</>
                                )}
                            </button>

                            {!esCompleta && mostrarFormulario && (
                                <button
                                    type="button"
                                    onClick={() => { setMostrarFormulario(false); setLlave(''); }}
                                    className="text-gray-500 hover:text-gray-700 font-medium px-4 py-2.5 rounded-lg hover:bg-gray-50 transition-colors text-sm"
                                >
                                    Cancelar
                                </button>
                            )}
                        </div>
                    </form>
                </div>
            )}

            {/* ── Versión Completa: Confirmación ── */}
            {esCompleta && !mostrarFormulario && (
                <div className="bg-white rounded-xl shadow-sm border border-emerald-200 p-6">
                    <div className="flex items-start gap-4">
                        <div className="bg-emerald-100 rounded-full p-3 flex-shrink-0">
                            <FaCheckCircle className="text-emerald-600 text-xl" />
                        </div>
                        <div className="flex-1">
                            <h3 className="font-bold text-emerald-800 text-base">Licencia Activa y Válida</h3>
                            <p className="text-sm text-emerald-700 mt-1">
                                Su programa está operando en <strong>versión completa</strong> sin restricciones de registros.
                                Si necesita reactivar con una nueva llave, use el botón de abajo.
                            </p>
                            <button
                                onClick={() => setMostrarFormulario(true)}
                                className="mt-4 text-indigo-600 border border-indigo-200 hover:bg-indigo-50 font-semibold px-4 py-2 rounded-lg text-sm flex items-center gap-2 transition-colors"
                            >
                                <FaKey /> Ingresar nueva llave
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* ── Footer Ayuda ── */}
            <div className="text-center text-xs text-gray-400 pb-4">
                ¿Problemas con su llave? Contáctenos al correo de soporte de <strong>Finaxis</strong>.
            </div>
        </div>
    );
}
