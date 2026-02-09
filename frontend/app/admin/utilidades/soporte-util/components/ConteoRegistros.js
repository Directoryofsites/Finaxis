import React, { useState, useEffect } from 'react';
import {
    FaSearch, FaBuilding, FaMoneyBillWave, FaChartLine, FaHistory,
    FaEdit, FaSave, FaTimes, FaArrowLeft, FaCheckCircle, FaExclamationTriangle, FaTrash, FaBolt
} from 'react-icons/fa';
import {
    getConteoRegistros,
    updateLimiteRegistros,
    getConsumoEmpresa,
    setCupoAdicional,
    getRecargasEmpresa,
    deleteRecargaEmpresa,
    markRecargaPaid,
    getPrecioEmpresa,
    setPrecioEmpresa,
    updatePlanMensualManual,
    getRecargasGlobales // Nuevo import
} from '@/lib/soporteApiService';
import { toast } from 'react-toastify';

// Helper Currency
const currency = (val) => {
    return new Intl.NumberFormat('es-CO', {
        style: 'currency',
        currency: 'COP',
        maximumFractionDigits: 0
    }).format(val || 0);
};

export default function ConteoRegistros() {
    // --- ESTADOS GLOBALES ---
    const [listaEmpresas, setListaEmpresas] = useState([]);
    const [loadingLista, setLoadingLista] = useState(false);
    const [busqueda, setBusqueda] = useState('');

    // --- ESTADO MODO GLOBAL (NUEVO) ---
    const [verModoGlobal, setVerModoGlobal] = useState(false);
    const [recargasGlobales, setRecargasGlobales] = useState([]);
    const [loadingGlobales, setLoadingGlobales] = useState(false);
    // Periodo global independiente
    const nowGlobal = new Date();
    const [mesGlobal, setMesGlobal] = useState(nowGlobal.getMonth() + 1);
    const [anioGlobal, setAnioGlobal] = useState(nowGlobal.getFullYear());

    // --- ESTADO SELECCIÓN EMPRESA ---
    const [empresaSelected, setEmpresaSelected] = useState(null);

    // --- DATOS EMPRESA SELECCIONADA ---
    const [loadingEmpresa, setLoadingEmpresa] = useState(false);
    const [configPrecio, setConfigPrecio] = useState({ personalizado: null, global: 0, efectivo: 0 });
    const [editandoPrecio, setEditandoPrecio] = useState(false);
    const [nuevoPrecio, setNuevoPrecio] = useState('');

    // --- ESTADO LIMITE GLOBAL ---
    const [editandoLimite, setEditandoLimite] = useState(false);
    const [limiteEditor, setLimiteEditor] = useState(0);

    // --- ESTADO LIMITE MES ESPECIFICO (MANUAL) ---
    const [editandoLimiteMes, setEditandoLimiteMes] = useState(false);
    const [limiteMesEditor, setLimiteMesEditor] = useState(0);

    // Sync limite editor
    useEffect(() => {
        if (empresaSelected) {
            setLimiteEditor(empresaSelected.limite_registros || 0);
        }
    }, [empresaSelected]);



    // Datos de Consumo y Recargas (Mes Actual por defecto en vista empresa)
    const now = new Date();
    const [mesView, setMesView] = useState(now.getMonth() + 1);
    const [anioView, setAnioView] = useState(now.getFullYear());

    const [consumoData, setConsumoData] = useState(null);
    const [recargasData, setRecargasData] = useState([]);
    const [loadingDetalle, setLoadingDetalle] = useState(false);

    // Sync limite mes editor cuando carga el consumo
    useEffect(() => {
        if (consumoData) {
            setLimiteMesEditor(consumoData.limite_registros || 0);
        }
    }, [consumoData]);

    // Cargar Lista Inicial (Para el buscador)
    useEffect(() => {
        cargarListaEmpresas();
    }, []);

    // Cargar Globales cuando se activa el modo o cambia fecha
    useEffect(() => {
        if (verModoGlobal) {
            cargarRecargasGlobales();
        }
    }, [verModoGlobal, mesGlobal, anioGlobal]);

    const cargarListaEmpresas = async () => {
        setLoadingLista(true);
        try {
            const res = await getConteoRegistros();
            // Mapeamos para tener una estructura limpia
            setListaEmpresas(res.data);
        } catch (error) {
            console.error(error);
            toast.error("Error cargando directorio de empresas.");
        } finally {
            setLoadingLista(false);
        }
    };

    const cargarRecargasGlobales = async () => {
        setLoadingGlobales(true);
        try {
            const res = await getRecargasGlobales(mesGlobal, anioGlobal);
            setRecargasGlobales(res.data);
        } catch (error) {
            console.error(error);
            toast.error("Error cargando reporte global.");
        } finally {
            setLoadingGlobales(false);
        }
    };

    // --- SELECCIONAR EMPRESA ---
    const handleSelectEmpresa = async (empresa) => {
        setEmpresaSelected(empresa);
        setBusqueda(''); // Limpiar busqueda al entrar
        await cargarDatosEmpresa(empresa.empresa_id);
    };

    const cargarDatosEmpresa = async (empresaId) => {
        setLoadingEmpresa(true);
        try {
            // 1. Cargar Configuración de Precios
            const resPrecio = await getPrecioEmpresa(empresaId);
            setConfigPrecio({
                personalizado: resPrecio.data.precio_personalizado,
                global: resPrecio.data.precio_global,
                efectivo: resPrecio.data.precio_efectivo
            });
            setNuevoPrecio(resPrecio.data.precio_personalizado || '');

            // 2. Cargar Consumo y Recargas del Mes Seleccionado
            await actualizarVistaMes(empresaId, mesView, anioView);

        } catch (error) {
            console.error("Error cargando datos empresa", error);
            toast.error("Error cargando detalles de la empresa.");
        } finally {
            setLoadingEmpresa(false);
        }
    };

    const actualizarVistaMes = async (empresaId, mes, anio) => {
        setLoadingDetalle(true);
        try {
            // Consumo
            const resConsumo = await getConsumoEmpresa(empresaId, mes, anio);
            setConsumoData(resConsumo.data);

            // Recargas
            const resRecargas = await getRecargasEmpresa(empresaId, mes, anio);
            setRecargasData(resRecargas.data);
        } catch (error) {
            console.error(error);
        } finally {
            setLoadingDetalle(false);
        }
    }

    // --- ACTIONS ---

    const handleGuardarPrecio = async () => {
        if (!empresaSelected) return;
        try {
            const val = nuevoPrecio === '' ? null : parseInt(nuevoPrecio);
            await setPrecioEmpresa(empresaSelected.empresa_id, val);
            toast.success("Precio actualizado correctamente.");
            setEditandoPrecio(false);
            // Recargar config
            const res = await getPrecioEmpresa(empresaSelected.empresa_id);
            setConfigPrecio({
                personalizado: res.data.precio_personalizado,
                global: res.data.precio_global,
                efectivo: res.data.precio_efectivo
            });
        } catch (error) {
            toast.error("Error guardando precio.");
        }
    };

    const handleMarcarPagado = async (recargaId, nuevoEstado, esGlobal = false) => {
        if (!confirm(nuevoEstado ? "¿Confirmar pago?" : "¿Deshacer pago?")) return;
        try {
            await markRecargaPaid(recargaId, nuevoEstado);
            toast.success(nuevoEstado ? "Pago registrado." : "Pago deshecho.");

            if (esGlobal) {
                cargarRecargasGlobales();
            } else {
                actualizarVistaMes(empresaSelected.empresa_id, mesView, anioView);
            }
        } catch (error) {
            toast.error("Error actualizando pago.");
        }
    };

    const handleEliminarRecarga = async (recargaId, esGlobal = false) => {
        if (!confirm("¿Eliminar esta recarga? Esto es irreversible.")) return;
        try {
            await deleteRecargaEmpresa(recargaId);
            toast.success("Recarga eliminada.");
            if (esGlobal) {
                cargarRecargasGlobales();
            } else {
                actualizarVistaMes(empresaSelected.empresa_id, mesView, anioView);
            }
        } catch (error) {
            toast.error("Error eliminando recarga.");
        }
    };

    // ... (Mantener handleGuardarLimite y handleGuardarLimiteMes igual)
    const handleGuardarLimite = async () => {
        try {
            await updateLimiteRegistros(empresaSelected.empresa_id, parseInt(limiteEditor));
            toast.success("Límite GLOBAL actualizado.");
            setEditandoLimite(false);
            // Actualizar estado local para reflejar cambio inmediato
            setEmpresaSelected(prev => ({ ...prev, limite_registros: parseInt(limiteEditor) }));
            // Recargar vista mes, por si afecta
            actualizarVistaMes(empresaSelected.empresa_id, mesView, anioView);
        } catch (err) {
            toast.error("Error actualizando límite global.");
        }
    };

    const handleGuardarLimiteMes = async () => {
        try {
            await updatePlanMensualManual(
                empresaSelected.empresa_id,
                anioView,
                mesView,
                parseInt(limiteMesEditor)
            );
            toast.success("Límite del MES actualizado.");
            setEditandoLimiteMes(false);
            actualizarVistaMes(empresaSelected.empresa_id, mesView, anioView);
        } catch (err) {
            toast.error("Error actualizando límite del mes.");
        }
    };


    // --- RENDER ---

    // 0. VISTA REPORTE GLOBAL
    if (verModoGlobal) {
        return (
            <div className="bg-white rounded-[2.5rem] shadow-xl shadow-slate-200/60 overflow-hidden min-h-[600px] flex flex-col">
                {/* TOOLBAR SUPERIOR */}
                <div className="bg-slate-900 text-white p-6 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => setVerModoGlobal(false)}
                            className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center hover:bg-white/20 transition-colors text-slate-200 hover:text-white"
                            title="Volver"
                        >
                            <FaArrowLeft />
                        </button>
                        <div>
                            <h2 className="text-2xl font-black tracking-tight text-white flex items-center gap-2">
                                <FaBolt className="text-amber-400" /> Reporte Global de Recargas
                            </h2>
                            <p className="text-slate-400 font-mono text-sm opacity-80">
                                Vista consolidada de compras extra realizadas por todas las empresas.
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center gap-6">
                        {/* Period Selector (Global) */}
                        <div className="flex items-center bg-slate-800 rounded-lg p-1">
                            <select
                                value={mesGlobal}
                                onChange={e => setMesGlobal(parseInt(e.target.value))}
                                className="bg-transparent text-sm font-bold border-none focus:ring-0 text-white cursor-pointer"
                            >
                                {Array.from({ length: 12 }, (_, i) => (
                                    <option key={i + 1} value={i + 1} className="text-black">{new Date(0, i).toLocaleString('es-CO', { month: 'long' }).toUpperCase()}</option>
                                ))}
                            </select>
                            <select
                                value={anioGlobal}
                                onChange={e => setAnioGlobal(parseInt(e.target.value))}
                                className="bg-transparent text-sm font-bold border-none focus:ring-0 text-white cursor-pointer border-l border-slate-600"
                            >
                                {Array.from({ length: 36 }, (_, i) => {
                                    const y = new Date().getFullYear() + 5 - i;
                                    return (
                                        <option key={y} value={y} className="text-black">{y}</option>
                                    );
                                })}
                            </select>
                        </div>
                    </div>
                </div>

                <div className="p-8 flex-1 bg-slate-50/50">
                    <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">

                        {/* HEADER STATS */}
                        <div className="p-6 border-b border-slate-100 flex justify-between items-end bg-slate-50">
                            <div>
                                <h4 className="font-bold text-slate-700 text-lg uppercase mb-1">Total Periodo</h4>
                                <div className="flex gap-4">
                                    <div className="badge badge-lg bg-indigo-100 text-indigo-700 font-bold border-0">
                                        {(recargasGlobales || []).length} Compras
                                    </div>
                                    <div className="badge badge-lg bg-amber-100 text-amber-700 font-bold border-0">
                                        Pendiente: {currency((recargasGlobales || []).filter(r => !r.facturado).reduce((acc, r) => acc + (r.valor_total || 0), 0))}
                                    </div>
                                </div>
                            </div>
                            <div className="text-right">
                                <span className="block text-xs uppercase font-bold text-slate-400">Total Facturado + Pendiente</span>
                                <span className="text-3xl font-black text-slate-900">
                                    {currency((recargasGlobales || []).reduce((acc, r) => acc + (r.valor_total || 0), 0))}
                                </span>
                            </div>
                        </div>

                        <div className="overflow-x-auto">
                            {loadingGlobales ? (
                                <div className="p-12 flex justify-center"><div className="loading loading-spinner loading-lg text-primary"></div></div>
                            ) : (
                                <table className="w-full text-sm text-left">
                                    <thead className="text-xs text-slate-400 uppercase bg-slate-50/50">
                                        <tr>
                                            <th className="px-6 py-3">Fecha</th>
                                            <th className="px-6 py-3">Empresa</th>
                                            <th className="px-6 py-3 text-center">Registros</th>
                                            <th className="px-6 py-3 text-right">Valor</th>
                                            <th className="px-6 py-3 text-center">Estado</th>
                                            <th className="px-6 py-3 text-right">Acción</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-100">
                                        {(recargasGlobales || []).length === 0 ? (
                                            <tr>
                                                <td colSpan="6" className="px-6 py-8 text-center text-slate-400 italic">
                                                    No se encontraron recargas en este periodo global.
                                                </td>
                                            </tr>
                                        ) : (
                                            (recargasGlobales || []).map(r => (
                                                <tr key={r.id} className="hover:bg-slate-50 transition-colors">
                                                    <td className="px-6 py-4 font-bold text-slate-700">
                                                        {new Date(r.fecha_compra).toLocaleDateString()}
                                                        <br />
                                                        <span className="text-[10px] font-normal text-slate-400">
                                                            {new Date(r.fecha_compra).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4">
                                                        <div className="font-bold text-slate-800">{r.nombre_empresa}</div>
                                                        <div className="text-xs font-mono text-slate-400">{r.nit}</div>
                                                    </td>
                                                    <td className="px-6 py-4 text-center">
                                                        <span className="bg-indigo-50 text-indigo-700 px-2 py-1 rounded font-bold">
                                                            +{r.cantidad_comprada}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 text-right font-mono font-bold text-slate-800">
                                                        {currency(r.valor_total)}
                                                    </td>
                                                    <td className="px-6 py-4 text-center">
                                                        {r.facturado ? (
                                                            <span className="inline-flex items-center gap-1 text-emerald-600 font-bold text-xs bg-emerald-50 px-2 py-1 rounded-full">
                                                                <FaCheckCircle /> PAGADO
                                                            </span>
                                                        ) : (
                                                            <span className="inline-flex items-center gap-1 text-amber-600 font-bold text-xs bg-amber-50 px-2 py-1 rounded-full">
                                                                <FaExclamationTriangle /> PENDIENTE
                                                            </span>
                                                        )}
                                                    </td>
                                                    <td className="px-6 py-4 text-right">
                                                        <div className="flex justify-end gap-2">
                                                            {!r.facturado ? (
                                                                <>
                                                                    <button
                                                                        onClick={() => handleMarcarPagado(r.id, true, true)}
                                                                        className="btn btn-xs bg-blue-600 hover:bg-blue-700 text-white border-blue-600 shadow-md flex items-center gap-2 px-3 py-1 font-bold tracking-wide"
                                                                        title="Registrar Pago"
                                                                    >
                                                                        <FaMoneyBillWave size={12} className="text-white" />
                                                                        PAGAR
                                                                    </button>
                                                                    <button
                                                                        onClick={() => handleEliminarRecarga(r.id, true)}
                                                                        className="btn btn-xs btn-ghost text-rose-300 hover:bg-rose-50 hover:text-rose-500"
                                                                        title="Eliminar"
                                                                    >
                                                                        <FaTrash />
                                                                    </button>
                                                                </>
                                                            ) : (
                                                                <button
                                                                    onClick={() => handleMarcarPagado(r.id, false, true)}
                                                                    className="text-[10px] font-bold text-slate-400 hover:text-amber-600 underline"
                                                                >
                                                                    DESHACER
                                                                </button>
                                                            )}
                                                        </div>
                                                    </td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                </table>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    // 1. VISTA BUSCADOR (Si no hay empresa seleccionada)
    if (!empresaSelected) {
        const filtradas = (listaEmpresas || []).filter(e =>
            (e.nombre_empresa && e.nombre_empresa.toLowerCase().includes(busqueda.toLowerCase())) ||
            (e.nit && e.nit.includes(busqueda))
        );

        return (
            <div className="min-h-[500px] flex flex-col items-center justify-start pt-12 space-y-8 animate-fade-in-up">
                <div className="text-center space-y-4">
                    <div className="bg-indigo-100 p-4 rounded-full inline-block text-indigo-600 mb-2">
                        <FaBuilding size={40} />
                    </div>
                    <h2 className="text-3xl font-black text-slate-800">Gestión de Clientes</h2>
                    <p className="text-slate-500 text-lg max-w-lg mx-auto">
                        Busca una empresa para administrar sus límites, precios y recargas.
                    </p>
                    {/* BOTÓN REPORTE GLOBAL - AGREGADO AQUÍ */}
                    <button
                        onClick={() => setVerModoGlobal(true)}
                        className="btn btn-outline btn-sm gap-2 border-slate-300 text-slate-600 hover:bg-indigo-50 hover:text-indigo-700 hover:border-indigo-200 normal-case"
                    >
                        <FaBolt className="text-amber-500" /> Reporte Global de Recargas
                    </button>
                </div>

                <div className="w-full max-w-2xl relative">
                    <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
                        <FaSearch className="text-slate-400 text-xl" />
                    </div>
                    <input
                        type="text"
                        className="w-full pl-12 pr-6 py-6 text-xl rounded-2xl border-slate-200 shadow-xl shadow-slate-200/50 focus:ring-4 focus:ring-indigo-100 focus:border-indigo-500 transition-all placeholder:text-slate-300 font-bold"
                        placeholder="Buscar por Nombre o NIT..."
                        value={busqueda}
                        onChange={e => setBusqueda(e.target.value)}
                        autoFocus
                    />
                </div>

                {busqueda && (
                    <div className="w-full max-w-2xl bg-white rounded-2xl shadow-lg border border-slate-100 overflow-hidden">
                        <div className="max-h-[400px] overflow-y-auto">
                            {filtradas.length === 0 ? (
                                <div className="p-8 text-center text-slate-400 italic">No se encontraron resultados.</div>
                            ) : (
                                (filtradas || []).map(empresa => (
                                    <button
                                        key={empresa.empresa_id}
                                        onClick={() => handleSelectEmpresa(empresa)}
                                        className="w-full text-left p-6 hover:bg-indigo-50 transition-colors border-b border-slate-50 last:border-0 flex justify-between items-center group"
                                    >
                                        <div>
                                            <h3 className="text-lg font-bold text-slate-800 group-hover:text-indigo-700">{empresa.nombre_empresa}</h3>
                                            <p className="text-slate-400 font-mono text-sm">NIT: {empresa.nit || 'S/N'}</p>
                                        </div>
                                        <div className="flex flex-col items-end">
                                            <span className="text-xs font-bold bg-slate-100 text-slate-500 px-2 py-1 rounded mb-1">
                                                Plan: {empresa.limite_registros ? empresa.limite_registros : 'N/A'}
                                            </span>
                                            <span className="text-indigo-600 text-sm font-bold flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                Gestionar <span className="text-lg">&rarr;</span>
                                            </span>
                                        </div>
                                    </button>
                                ))
                            )}
                        </div>
                    </div>
                )}
            </div>
        );
    }


    // 2. VISTA DASHBOARD (Empresa Seleccionada)
    return (
        <div className="bg-white rounded-[2.5rem] shadow-xl shadow-slate-200/60 overflow-hidden min-h-[600px] flex flex-col">

            {/* TOOLBAR SUPERIOR */}
            <div className="bg-slate-900 text-white p-6 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <button
                        onClick={() => setEmpresaSelected(null)}
                        className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center hover:bg-white/20 transition-colors text-slate-200 hover:text-white"
                        title="Volver al buscador"
                    >
                        <FaArrowLeft />
                    </button>
                    <div>
                        <h2 className="text-2xl font-black tracking-tight">{empresaSelected.nombre_empresa}</h2>
                        <p className="text-slate-400 font-mono text-sm opacity-80">NIT: {empresaSelected.nit}</p>
                    </div>
                </div>

                <div className="flex items-center gap-6">
                    {/* Period Selector (Simple) */}
                    <div className="flex items-center bg-slate-800 rounded-lg p-1">
                        <select
                            value={mesView}
                            onChange={e => { setMesView(parseInt(e.target.value)); actualizarVistaMes(empresaSelected.empresa_id, parseInt(e.target.value), anioView); }}
                            className="bg-transparent text-sm font-bold border-none focus:ring-0 text-white cursor-pointer"
                        >
                            {Array.from({ length: 12 }, (_, i) => (
                                <option key={i + 1} value={i + 1} className="text-black">{new Date(0, i).toLocaleString('es-CO', { month: 'long' }).toUpperCase()}</option>
                            ))}
                        </select>
                        <select
                            value={anioView}
                            onChange={e => { setAnioView(parseInt(e.target.value)); actualizarVistaMes(empresaSelected.empresa_id, mesView, parseInt(e.target.value)); }}
                            className="bg-transparent text-sm font-bold border-none focus:ring-0 text-white cursor-pointer border-l border-slate-600"
                        >
                            {Array.from({ length: 36 }, (_, i) => {
                                const y = new Date().getFullYear() + 5 - i;
                                return (
                                    <option key={y} value={y} className="text-black">{y}</option>
                                );
                            })}
                        </select>
                    </div>
                </div>
            </div>

            {/* CONTENIDO PRINCIPAL */}
            <div className="p-8 flex-1 bg-slate-50/50">

                {loadingEmpresa && (
                    <div className="flex justify-center p-12"><div className="loading loading-spinner loading-lg text-primary"></div></div>
                )}

                {!loadingEmpresa && (
                    <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">

                        {/* COLUMNA 1: CONFIGURACIÓN COMERCIAL */}
                        <div className="space-y-6">
                            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4">Configuración Comercial</h3>

                            {/* Card Precio */}
                            <div className="bg-white p-6 rounded-2xl shadow-lg border border-slate-100">
                                <div className="flex justify-between items-start mb-4">
                                    <div className="flex items-center gap-3 text-emerald-600 mb-1">
                                        <FaMoneyBillWave />
                                        <span className="font-bold text-sm uppercase">Precio por Registro</span>
                                    </div>
                                    {!editandoPrecio && (
                                        <button onClick={() => setEditandoPrecio(true)} className="text-indigo-600 hover:bg-indigo-50 p-2 rounded-lg transition-colors text-xs font-bold flex items-center gap-1">
                                            <FaEdit /> Editar
                                        </button>
                                    )}
                                </div>

                                {editandoPrecio ? (
                                    <div className="animate-fade-in space-y-3">
                                        <div>
                                            <label className="text-xs text-slate-400 font-bold block mb-1">Precio Personalizado (COP)</label>
                                            <input
                                                type="number"
                                                className="input input-sm input-bordered w-full font-bold text-slate-800"
                                                placeholder={`Global: ${configPrecio.global}`}
                                                value={nuevoPrecio}
                                                onChange={e => setNuevoPrecio(e.target.value)}
                                            />
                                            <p className="text-[10px] text-slate-400 mt-1">
                                                Dejar vacío para usar precio global ({currency(configPrecio.global)})
                                            </p>
                                        </div>
                                        <div className="flex gap-2 justify-end mt-2">
                                            <button
                                                onClick={() => setEditandoPrecio(false)}
                                                className="px-3 py-1.5 rounded-lg text-slate-500 hover:bg-slate-100 font-bold text-xs transition-colors"
                                            >
                                                Cancelar
                                            </button>
                                            <button
                                                onClick={handleGuardarPrecio}
                                                className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-1.5 rounded-lg font-bold text-xs flex items-center gap-2 shadow-md transition-all active:scale-95"
                                            >
                                                <FaSave /> Guardar
                                            </button>
                                        </div>
                                    </div>
                                ) : (
                                    <div>
                                        <p className="text-4xl font-black text-slate-800 tracking-tighter mb-1">
                                            {currency(configPrecio.efectivo)}
                                        </p>
                                        <p className="text-xs font-bold flex items-center gap-2">
                                            {configPrecio.personalizado ? (
                                                <span className="text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-md">Personalizado</span>
                                            ) : (
                                                <span className="text-slate-400 bg-slate-100 px-2 py-0.5 rounded-md">Por defecto (Global)</span>
                                            )}
                                        </p>
                                    </div>
                                )}
                            </div>

                            {/* Card Límite Base */}
                            <div className="bg-white p-6 rounded-2xl shadow-lg border border-slate-100">
                                <div className="flex justify-between items-center mb-2">
                                    <div className="flex items-center gap-3 text-indigo-600">
                                        <FaChartLine />
                                        <span className="font-bold text-sm uppercase">Config. Global (Predeterminada)</span>
                                    </div>
                                    {!editandoLimite && (
                                        <button onClick={() => setEditandoLimite(true)} className="text-indigo-600 hover:bg-indigo-50 p-2 rounded-lg transition-colors text-xs font-bold flex items-center gap-1">
                                            <FaEdit /> Editar
                                        </button>
                                    )}
                                </div>

                                {editandoLimite ? (
                                    <div className="animate-fade-in space-y-3">
                                        <div>
                                            <input
                                                type="number"
                                                className="input input-sm input-bordered w-full font-bold text-slate-800 text-2xl h-12"
                                                value={limiteEditor}
                                                onChange={(e) => setLimiteEditor(e.target.value)}
                                            />
                                            <span className="text-xs text-slate-400 mt-1 block">registros / mes</span>
                                        </div>
                                        <div className="flex gap-2 justify-end mt-2">
                                            <button
                                                onClick={() => setEditandoLimite(false)}
                                                className="px-3 py-1.5 rounded-lg text-slate-500 hover:bg-slate-100 font-bold text-xs transition-colors"
                                            >
                                                Cancelar
                                            </button>
                                            <button
                                                onClick={handleGuardarLimite}
                                                className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-1.5 rounded-lg font-bold text-xs flex items-center gap-2 shadow-md transition-all active:scale-95"
                                            >
                                                <FaSave /> Guardar
                                            </button>
                                        </div>
                                    </div>
                                ) : (
                                    <>
                                        <div className="flex items-center gap-2">
                                            <span className="font-black text-4xl text-slate-800 tracking-tighter">
                                                {empresaSelected.limite_registros || 0}
                                            </span>
                                            <span className="text-slate-400 font-bold text-sm">registros</span>
                                        </div>
                                        <p className="text-xs text-slate-400 mt-2">
                                            Se renueva automáticamente cada mes.
                                        </p>
                                    </>
                                )}
                            </div>
                        </div>

                        {/* COLUMNA 2: ESTADO DEL MES ACTUAL */}
                        <div className="xl:col-span-2 space-y-6">
                            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4">
                                Actividad de {new Date(0, mesView - 1).toLocaleString('es-CO', { month: 'long' })} {anioView}
                            </h3>

                            {loadingDetalle && <div className="skeleton h-48 w-full rounded-2xl"></div>}

                            {!loadingDetalle && consumoData && (
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                                    {/* Stats Consumo */}
                                    <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
                                        <h4 className="font-bold text-slate-700 mb-4 flex justify-between">
                                            Consumo Real
                                            <span className={`badge ${consumoData.porcentaje > 100 ? 'badge-error' : 'badge-success'} badge-sm font-bold text-white`}>
                                                {consumoData.porcentaje}% Uso
                                            </span>
                                        </h4>
                                        <div className="flex items-end gap-2 mb-2">
                                            <span className="text-5xl font-black text-slate-800">{consumoData.total_registros || 0}</span>

                                            {/* EDITOR DE LIMITE DEL MES */}
                                            <div className="flex flex-col items-end">
                                                {!editandoLimiteMes ? (
                                                    <div className="flex items-center gap-2 group cursor-pointer" onClick={() => { setLimiteMesEditor(consumoData.limite_registros); setEditandoLimiteMes(true); }}>
                                                        <span className="text-slate-400 font-bold text-lg mb-1 group-hover:text-indigo-600 transition-colors">
                                                            / {consumoData.limite_registros || 0}
                                                        </span>
                                                        <FaEdit className="text-slate-300 group-hover:text-indigo-500 text-xs" />
                                                    </div>
                                                ) : (
                                                    <div className="flex items-center gap-1 animate-fade-in">
                                                        <span className="text-slate-400 font-bold text-lg">/</span>
                                                        <input
                                                            autoFocus
                                                            type="number"
                                                            className="input input-xs input-bordered w-20 font-bold text-right"
                                                            value={limiteMesEditor}
                                                            onChange={e => setLimiteMesEditor(e.target.value)}
                                                            onKeyDown={e => e.key === 'Enter' && handleGuardarLimiteMes()}
                                                        />
                                                        <button onClick={handleGuardarLimiteMes} className="btn btn-xs btn-circle btn-primary text-white"><FaCheckCircle /></button>
                                                        <button onClick={() => setEditandoLimiteMes(false)} className="btn btn-xs btn-circle btn-ghost text-slate-400"><FaTimes /></button>
                                                    </div>
                                                )}
                                            </div>

                                        </div>
                                        <progress
                                            className={`progress ${consumoData.porcentaje > 90 ? 'progress-warning' : 'progress-primary'} w-full`}
                                            value={consumoData.total_registros || 0}
                                            max={consumoData.limite_registros || 100}
                                        ></progress>
                                    </div>

                                    {/* Stats Recargas */}
                                    <div className="bg-slate-800 text-white p-6 rounded-2xl shadow-lg relative overflow-hidden">
                                        <div className="absolute top-0 right-0 w-24 h-24 bg-white/5 rounded-bl-full -mr-8 -mt-8"></div>
                                        <h4 className="font-bold text-slate-400 mb-4 flex items-center gap-2">
                                            <FaBolt className="text-amber-400" /> Recargas Extra (Mes)
                                        </h4>
                                        <div className="flex flex-col gap-1">
                                            <span className="text-4xl font-black text-white">{recargasData.length}</span>
                                            <span className="text-xs text-slate-400 uppercase font-bold">Compras realizadas</span>
                                        </div>
                                        <div className="mt-4 pt-4 border-t border-white/10">
                                            <p className="text-[10px] text-amber-200 uppercase font-bold mb-1">Deuda Pendiente</p>
                                            <p className="text-2xl font-black text-amber-400">
                                                {currency((recargasData || []).filter(r => !r.facturado).reduce((acc, r) => acc + (r.valor_total || 0), 0))}
                                            </p>
                                        </div>
                                    </div>

                                </div>
                            )}

                            {/* TABLA DE RECARGAS DETALLADA */}
                            <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
                                <div className="p-4 border-b border-slate-100 bg-slate-50 flex justify-between items-center">
                                    <h4 className="font-bold text-slate-700 text-sm uppercase">Detalle de Recargas</h4>
                                    {/* Botón Accion Rapida Futura */}
                                </div>
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm text-left">
                                        <thead className="text-xs text-slate-400 uppercase bg-slate-50/50">
                                            <tr>
                                                <th className="px-6 py-3">Fecha</th>
                                                <th className="px-6 py-3 text-center">Registros</th>
                                                <th className="px-6 py-3 text-right">Valor</th>
                                                <th className="px-6 py-3 text-center">Estado</th>
                                                <th className="px-6 py-3 text-right">Acción</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-slate-100">
                                            {(recargasData || []).length === 0 ? (
                                                <tr>
                                                    <td colSpan="5" className="px-6 py-8 text-center text-slate-400 italic">
                                                        No hay recargas registradas en este periodo.
                                                    </td>
                                                </tr>
                                            ) : (
                                                recargasData.map(r => (
                                                    <tr key={r.id} className="hover:bg-slate-50 transition-colors">
                                                        <td className="px-6 py-4 font-bold text-slate-700">
                                                            {new Date(r.fecha_compra).toLocaleDateString()}
                                                            <br />
                                                            <span className="text-[10px] font-normal text-slate-400">
                                                                {new Date(r.fecha_compra).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                            </span>
                                                        </td>
                                                        <td className="px-6 py-4 text-center">
                                                            <span className="bg-indigo-50 text-indigo-700 px-2 py-1 rounded font-bold">
                                                                +{r.cantidad_comprada}
                                                            </span>
                                                        </td>
                                                        <td className="px-6 py-4 text-right font-mono font-bold text-slate-800">
                                                            {currency(r.valor_total)}
                                                        </td>
                                                        <td className="px-6 py-4 text-center">
                                                            {r.facturado ? (
                                                                <span className="inline-flex items-center gap-1 text-emerald-600 font-bold text-xs bg-emerald-50 px-2 py-1 rounded-full">
                                                                    <FaCheckCircle /> PAGADO
                                                                </span>
                                                            ) : (
                                                                <span className="inline-flex items-center gap-1 text-amber-600 font-bold text-xs bg-amber-50 px-2 py-1 rounded-full">
                                                                    <FaExclamationTriangle /> PENDIENTE
                                                                </span>
                                                            )}
                                                        </td>
                                                        <td className="px-6 py-4 text-right">
                                                            <div className="flex justify-end gap-2">
                                                                {!r.facturado ? (
                                                                    <>
                                                                        <button
                                                                            onClick={() => handleMarcarPagado(r.id, true)}
                                                                            className="btn btn-xs bg-blue-600 hover:bg-blue-700 text-white border-blue-600 shadow-md flex items-center gap-2 px-3 py-1 font-bold tracking-wide"
                                                                            title="Registrar Pago"
                                                                        >
                                                                            <FaMoneyBillWave size={12} className="text-white" />
                                                                            PAGAR
                                                                        </button>
                                                                        <button
                                                                            onClick={() => handleEliminarRecarga(r.id)}
                                                                            className="btn btn-xs btn-ghost text-rose-300 hover:bg-rose-50 hover:text-rose-500"
                                                                            title="Eliminar"
                                                                        >
                                                                            <FaTrash />
                                                                        </button>
                                                                    </>
                                                                ) : (
                                                                    <button
                                                                        onClick={() => handleMarcarPagado(r.id, false)}
                                                                        className="text-[10px] font-bold text-slate-400 hover:text-amber-600 underline"
                                                                    >
                                                                        DESHACER
                                                                    </button>
                                                                )}
                                                            </div>
                                                        </td>
                                                    </tr>
                                                ))
                                            )}
                                        </tbody>
                                        {/* Footer Totals */}
                                        {recargasData.length > 0 && (
                                            <tfoot className="bg-slate-50 border-t-2 border-slate-100">
                                                <tr>
                                                    <td colSpan="2" className="text-right px-6 py-4 font-bold text-slate-500 uppercase text-xs">Total Comprado (Mes)</td>
                                                    <td className="px-6 py-4 text-right font-black text-slate-900 border-t border-slate-200">
                                                        {currency((recargasData || []).reduce((acc, r) => acc + (r.valor_total || 0), 0))}
                                                    </td>
                                                    <td colSpan="2"></td>
                                                </tr>
                                            </tfoot>
                                        )}
                                    </table>
                                </div>
                            </div>

                        </div>
                    </div>
                )}

            </div>
        </div>
    );
}