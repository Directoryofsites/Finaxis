'use client';
import React, { useState, useEffect } from 'react';
import { getConteoRegistros, updateLimiteRegistros, setCupoAdicional, getConsumoEmpresa } from '../../../../../lib/soporteApiService';
import { FaCalendarAlt, FaSave, FaSync, FaChartBar, FaBook } from 'react-icons/fa';

export default function ConteoRegistros() {
    const [conteoData, setConteoData] = useState([]);
    const [loading, setLoading] = useState(false);

    // Modal
    const [modalOpen, setModalOpen] = useState(false);
    const [selectedEmpresa, setSelectedEmpresa] = useState(null);

    // Datos Modal
    const [mesGestion, setMesGestion] = useState(new Date().getMonth() + 1);
    const [anioGestion, setAnioGestion] = useState(new Date().getFullYear());
    const [limiteMensualInput, setLimiteMensualInput] = useState('');

    // Estado de Datos en Tiempo Real
    const [datosRealesMes, setDatosRealesMes] = useState(null);
    const [cargandoDatosMes, setCargandoDatosMes] = useState(false);

    const fetchData = async () => {
        setLoading(true);
        try {
            const res = await getConteoRegistros();
            setConteoData(res.data);
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    };

    useEffect(() => { fetchData(); }, []);

    // --- EFECTO: Consultar datos reales al cambiar fecha ---
    useEffect(() => {
        if (modalOpen && selectedEmpresa) {
            consultarDatosReales();
        }
    }, [mesGestion, anioGestion, selectedEmpresa]);

    const consultarDatosReales = async () => {
        setCargandoDatosMes(true);
        try {
            // Llamamos al nuevo endpoint que conecta con la lógica maestra
            const res = await getConsumoEmpresa(selectedEmpresa.empresa_id, mesGestion, anioGestion);
            setDatosRealesMes(res.data);

            // MAGIA: Pre-llenamos el input con el límite REAL que está aplicando el sistema
            // Si el sistema dice que el límite es 500, mostramos 500.
            setLimiteMensualInput(res.data.limite_registros);
        } catch (error) {
            console.error("Error consultando detalle mes", error);
        } finally {
            setCargandoDatosMes(false);
        }
    };

    const handleOpenGestion = (empresa) => {
        setSelectedEmpresa(empresa);
        setMesGestion(new Date().getMonth() + 1);
        setAnioGestion(new Date().getFullYear());
        setDatosRealesMes(null); // Limpiar datos previos
        setModalOpen(true);
    };

    const handleGuardarMensual = async () => {
        if (!selectedEmpresa) return;
        try {
            await setCupoAdicional(selectedEmpresa.empresa_id, anioGestion, mesGestion, limiteMensualInput);
            alert(`✅ Actualizado: Límite de ${limiteMensualInput} registros para el periodo ${mesGestion}/${anioGestion}.`);
            consultarDatosReales(); // Recargar para ver el cambio reflejado inmediatamente
            fetchData(); // Actualizar lista de fondo
        } catch (error) {
            alert('Error al guardar.');
        }
    };

    const handleUpdateBase = async (empresaId, nuevoValor) => {
        if (!confirm("¿Cambiar el PLAN BASE?")) return;
        try { await updateLimiteRegistros(empresaId, nuevoValor); fetchData(); }
        catch (e) { alert("Error"); }
    };

    return (
        <section className="bg-white p-6 rounded-xl shadow-lg border border-gray-100 font-sans">
            <div className="flex justify-between items-center mb-6 border-b pb-4">
                <div>
                    <h2 className="text-xl font-bold text-gray-800">Control de Límites por Empresa</h2>
                    <p className="text-sm text-gray-500">Gestión de planes mensuales y excepciones temporales.</p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={() => window.open('/manual/capitulo_22_conteo_registros.html', '_blank')}
                        className="btn btn-sm btn-outline btn-info gap-2"
                        title="Ver Manual de Usuario"
                    >
                        <FaBook /> Manual
                    </button>
                    <button onClick={fetchData} className="btn btn-sm btn-ghost"><FaSync /> Actualizar Lista</button>
                </div>
            </div>

            <div className="overflow-x-auto">
                <table className="table table-sm w-full">
                    <thead className="bg-slate-100 text-gray-600 uppercase">
                        <tr>
                            <th>Empresa</th>
                            <th className="text-center">Consumo (Mes Actual)</th>
                            <th className="text-center">Plan Base (Defecto)</th>
                            <th className="text-center">Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {conteoData.map((row) => {
                            if (row.nombre_empresa === 'TOTAL GENERAL') return null;
                            return (
                                <tr key={row.empresa_id} className="hover:bg-gray-50">
                                    <td className="font-bold text-gray-700">{row.nombre_empresa}</td>
                                    <td className="text-center font-mono text-lg">{row.total_registros}</td>
                                    <td className="text-center">
                                        <input
                                            type="number"
                                            className="input input-bordered input-sm w-24 text-center bg-gray-50"
                                            defaultValue={row.limite_registros}
                                            onBlur={(e) => {
                                                if (e.target.value != row.limite_registros) handleUpdateBase(row.empresa_id, e.target.value)
                                            }}
                                        />
                                    </td>
                                    <td className="text-center">
                                        <button onClick={() => handleOpenGestion(row)} className="btn btn-sm btn-outline btn-indigo gap-2">
                                            <FaCalendarAlt /> Gestionar Meses
                                        </button>
                                    </td>
                                </tr>
                            )
                        })}
                    </tbody>
                </table>
            </div>

            {/* --- MODAL SINCRONIZADO --- */}
            {modalOpen && selectedEmpresa && (
                <div className="modal modal-open">
                    <div className="modal-box border-t-4 border-indigo-600">
                        <h3 className="font-bold text-lg text-gray-800">Gestión de Periodo Específico</h3>
                        <p className="text-sm text-gray-500 mb-6">Empresa: <strong>{selectedEmpresa.nombre_empresa}</strong></p>

                        <div className="bg-gray-50 p-5 rounded-xl border border-gray-200">
                            {/* SELECTORES DE FECHA */}
                            <div className="flex gap-4 mb-6">
                                <div className="w-1/2">
                                    <label className="label-text text-xs font-bold text-gray-500 uppercase mb-1 block">Mes</label>
                                    <select value={mesGestion} onChange={e => setMesGestion(e.target.value)} className="select select-bordered select-sm w-full">
                                        {[...Array(12)].map((_, i) => <option key={i + 1} value={i + 1}>{new Date(0, i).toLocaleString('es', { month: 'long' }).toUpperCase()}</option>)}
                                    </select>
                                </div>
                                <div className="w-1/2">
                                    <label className="label-text text-xs font-bold text-gray-500 uppercase mb-1 block">Año</label>
                                    <input type="number" value={anioGestion} onChange={e => setAnioGestion(e.target.value)} className="input input-bordered input-sm w-full" />
                                </div>
                            </div>

                            {/* INDICADOR DE ESTADO REAL (SYNC) */}
                            <div className="mb-6 p-4 bg-white rounded-lg shadow-sm border border-gray-100 flex justify-between items-center">
                                <div>
                                    <p className="text-xs font-bold text-gray-400 uppercase">Consumo Real</p>
                                    <div className="flex items-baseline gap-1">
                                        {cargandoDatosMes ? <span className="loading loading-spinner loading-xs"></span> :
                                            <span className="text-2xl font-mono font-bold text-gray-800">{datosRealesMes?.total_registros || 0}</span>
                                        }
                                        <span className="text-xs text-gray-500">registros</span>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <p className="text-xs font-bold text-gray-400 uppercase">Uso del Cupo</p>
                                    {cargandoDatosMes ? <span className="loading loading-dots loading-xs"></span> :
                                        <span className={`text-lg font-bold ${datosRealesMes?.estado === 'CRITICO' ? 'text-red-600' : 'text-green-600'}`}>
                                            {datosRealesMes?.porcentaje || 0}%
                                        </span>
                                    }
                                </div>
                            </div>

                            {/* INPUT DE EDICIÓN */}
                            <div className="form-control">
                                <label className="label">
                                    <span className="label-text font-bold text-indigo-900">Definir Límite para este Mes:</span>
                                </label>
                                <div className="flex gap-2">
                                    <input
                                        type="number"
                                        value={limiteMensualInput}
                                        onChange={e => setLimiteMensualInput(e.target.value)}
                                        className="input input-bordered w-full font-mono text-lg font-bold text-indigo-600"
                                        placeholder="Ej: 600"
                                    />
                                    <button onClick={handleGuardarMensual} className="btn btn-primary">
                                        <FaSave /> Guardar
                                    </button>
                                </div>
                                <p className="text-xs text-gray-400 mt-2 italic">
                                    * Escribe <strong>0</strong> para eliminar la excepción y volver al Plan Base.
                                </p>
                            </div>
                        </div>

                        <div className="modal-action">
                            <button onClick={() => setModalOpen(false)} className="btn btn-ghost btn-sm">Cerrar</button>
                        </div>
                    </div>
                </div>
            )}
        </section>
    );
}