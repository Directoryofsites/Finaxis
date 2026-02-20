// frontend/app/admin/empresas/[id]/page.js
'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';

import { useAuth } from '../../../context/AuthContext';
import { apiService } from '../../../../lib/apiService';
import { FaBuilding, FaSave, FaUsers, FaExclamationTriangle, FaFileInvoiceDollar, FaLandmark, FaListOl, FaIdCard, FaMapMarkerAlt, FaPhoneAlt, FaEnvelope, FaImage } from 'react-icons/fa';

export default function DetalleEmpresaPage() {
    const params = useParams();
    const { id } = params;
    const { user } = useAuth();

    // Estado para el formulario de la empresa
    const [formData, setFormData] = useState({
        razon_social: '',
        nit: '',
        direccion: '',
        telefono: '',
        email: '',
        logo_url: '', // Para el logo en el PDF
        limite_registros: 0
    });

    // NUEVO: Estado para la configuración de FE
    const [feConfig, setFeConfig] = useState({
        ambiente: 'PRUEBAS',
        resolucion_numero: '',
        resolucion_fecha: '',
        prefijo: '',
        rango_desde: '',
        rango_hasta: '',
        factura_rango_id: '',
        nc_rango_id: '',
        nd_rango_id: '',
        ds_rango_id: '',
        api_token: '',
        habilitado: false
    });

    const [usuarios, setUsuarios] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState(null);
    const [errorUsuarios, setErrorUsuarios] = useState(null); // Error específico para usuarios (403)
    const [success, setSuccess] = useState('');

    useEffect(() => {
        if (id && user) {
            const fetchData = async () => {
                setIsLoading(true);
                try {
                    // 1. Cargar Datos de la Empresa
                    const resEmpresa = await apiService.get(`/empresas/${id}`);
                    const emp = resEmpresa.data;

                    // Pre-llenar formulario (usamos || '' para evitar warnings de React)
                    setFormData({
                        razon_social: emp.razon_social || '',
                        nit: emp.nit || '',
                        direccion: emp.direccion || '',
                        telefono: emp.telefono || '',
                        email: emp.email || '',
                        logo_url: emp.logo_url || '',
                        limite_registros: emp.limite_registros || 0
                    });

                    // 2. Intentar Cargar Usuarios (Puede fallar por permisos 403)
                    try {
                        const resUsuarios = await apiService.get(`/empresas/${id}/usuarios`);
                        setUsuarios(resUsuarios.data);
                    } catch (errUsers) {
                        console.warn("No se pudieron cargar usuarios:", errUsers);
                        setErrorUsuarios("No tienes permisos para ver o gestionar los usuarios de esta empresa.");
                    }

                    // 3. Cargar Configuración FE
                    try {
                        const resFE = await apiService.get(`/fe/config/${id}`);
                        setFeConfig({
                            ambiente: resFE.data.ambiente || 'PRUEBAS',
                            resolucion_numero: resFE.data.resolucion_numero || '',
                            resolucion_fecha: resFE.data.resolucion_fecha || '',
                            prefijo: resFE.data.prefijo || '',
                            rango_desde: resFE.data.rango_desde || '',
                            rango_hasta: resFE.data.rango_hasta || '',
                            factura_rango_id: resFE.data.factura_rango_id || '',
                            nc_rango_id: resFE.data.nc_rango_id || '',
                            nd_rango_id: resFE.data.nd_rango_id || '',
                            ds_rango_id: resFE.data.ds_rango_id || '',
                            api_token: resFE.data.api_token || '',
                            habilitado: resFE.data.habilitado || false
                        });
                    } catch (errFE) {
                        console.warn("No se pudo cargar config FE:", errFE);
                    }

                } catch (err) {
                    setError(err.response?.data?.detail || 'Error cargando la empresa.');
                } finally {
                    setIsLoading(false);
                }
            };
            fetchData();
        }
    }, [id, user]);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleFEInputChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFeConfig(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleUpdateEmpresa = async (e) => {
        e.preventDefault();
        setIsSaving(true);
        setError(null);
        setSuccess('');

        try {
            // Enviamos PUT para actualizar
            await apiService.put(`/empresas/${id}`, formData);

            // Enviamos PUT para la configuración de FE (si se editó algo)
            await apiService.put(`/fe/config/${id}`, {
                ...feConfig,
                rango_desde: feConfig.rango_desde ? parseInt(feConfig.rango_desde) : null,
                rango_hasta: feConfig.rango_hasta ? parseInt(feConfig.rango_hasta) : null,
                factura_rango_id: feConfig.factura_rango_id ? parseInt(feConfig.factura_rango_id) : null,
                nc_rango_id: feConfig.nc_rango_id ? parseInt(feConfig.nc_rango_id) : null,
                nd_rango_id: feConfig.nd_rango_id ? parseInt(feConfig.nd_rango_id) : null,
                ds_rango_id: feConfig.ds_rango_id ? parseInt(feConfig.ds_rango_id) : null
            });

            setSuccess('¡Datos de la empresa y configuración de FE actualizados correctamente!');
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al guardar los cambios.');
        } finally {
            setIsSaving(false);
        }
    };

    if (isLoading) return <div className="p-10 text-center"><span className="loading loading-spinner text-indigo-600"></span></div>;

    return (
        <div className="container mx-auto p-4 md:p-8 max-w-7xl font-sans pb-28 min-h-screen bg-slate-50/50">
            {/* Header de la página */}
            <div className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-extrabold text-slate-800 tracking-tight flex items-center gap-3">
                        <div className="p-3 bg-indigo-100 text-indigo-600 rounded-2xl shadow-sm">
                            <FaBuilding size={24} />
                        </div>
                        Configuración de Empresa
                    </h1>
                    <p className="text-slate-500 mt-2 ml-1">Administra los datos fiscales, facturación electrónica y usuarios de la organización.</p>
                </div>
            </div>

            {/* Mensajes globales */}
            {success && (
                <div className="alert alert-success bg-emerald-50 border-emerald-200 text-emerald-800 mb-6 rounded-2xl shadow-sm">
                    <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                    <span>{success}</span>
                </div>
            )}
            {error && (
                <div className="alert alert-error bg-red-50 border-red-200 text-red-800 mb-6 rounded-2xl shadow-sm">
                    <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                    <span>{error}</span>
                </div>
            )}

            <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">

                {/* COLUMNA IZQUIERDA: DATOS GENERALES */}
                <div className="xl:col-span-1 space-y-8">
                    <div className="bg-white p-6 md:p-8 rounded-[2rem] shadow-sm border border-slate-100 transition-all hover:shadow-md">
                        <h2 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">
                            Datos Fiscales
                        </h2>

                        <form id="form-empresa" onSubmit={handleUpdateEmpresa} className="space-y-5">
                            <div>
                                <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-2 flex items-center gap-2"><FaBuilding className="text-slate-400" /> Razón Social</label>
                                <input type="text" name="razon_social" value={formData.razon_social} onChange={handleInputChange} className="input input-bordered w-full focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors bg-slate-50 focus:bg-white" required />
                            </div>
                            <div>
                                <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-2 flex items-center gap-2"><FaIdCard className="text-slate-400" /> NIT / Identificación</label>
                                <input type="text" name="nit" value={formData.nit} onChange={handleInputChange} className="input input-bordered w-full font-mono text-sm bg-slate-50 focus:bg-white focus:border-indigo-500" required />
                            </div>
                            <div>
                                <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-2 flex items-center gap-2"><FaMapMarkerAlt className="text-slate-400" /> Dirección</label>
                                <input type="text" name="direccion" value={formData.direccion} onChange={handleInputChange} className="input input-bordered w-full bg-slate-50 focus:bg-white focus:border-indigo-500" placeholder="Ej: Calle 123 # ... " />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-2 flex items-center gap-2"><FaPhoneAlt className="text-slate-400" /> Teléfono</label>
                                    <input type="text" name="telefono" value={formData.telefono} onChange={handleInputChange} className="input input-bordered w-full bg-slate-50 focus:bg-white focus:border-indigo-500" placeholder="300 123 4567" />
                                </div>
                                <div>
                                    <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-2 flex items-center gap-2"><FaEnvelope className="text-slate-400" /> Email</label>
                                    <input type="email" name="email" value={formData.email} onChange={handleInputChange} className="input input-bordered w-full bg-slate-50 focus:bg-white focus:border-indigo-500" />
                                </div>
                            </div>
                            <div>
                                <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-2 flex items-center gap-2"><FaImage className="text-slate-400" /> URL del Logo</label>
                                <input type="text" name="logo_url" value={formData.logo_url} onChange={handleInputChange} className="input input-bordered w-full text-xs font-mono bg-slate-50 focus:bg-white focus:border-indigo-500" placeholder="https://mi-sitio.com/logo.png" />
                                {formData.logo_url && (
                                    <div className="mt-4 p-4 bg-slate-50 rounded-2xl border border-slate-100 flex justify-center items-center shadow-inner">
                                        <img src={formData.logo_url} alt="Logo Previsto" className="max-h-16 object-contain" />
                                    </div>
                                )}
                            </div>
                        </form>
                    </div>

                    <div className="bg-white p-6 md:p-8 rounded-[2rem] shadow-sm border border-slate-100">
                        <h3 className="text-lg font-bold text-slate-800 mb-5 flex items-center gap-2 pb-4 border-b border-slate-50">
                            <FaUsers className="text-indigo-500" /> Usuarios Autorizados
                        </h3>
                        {errorUsuarios ? (
                            <div className="text-sm text-rose-700 bg-rose-50 p-4 rounded-xl border border-rose-200">
                                <FaExclamationTriangle className="inline mr-2" />
                                {errorUsuarios}
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {usuarios.map(u => (
                                    <div key={u.id} className="flex items-center justify-between p-3.5 bg-slate-50 hover:bg-slate-100 transition-colors rounded-[1rem] border border-slate-100/80">
                                        <div className="truncate flex-1 pr-3">
                                            <p className="text-sm font-semibold text-slate-700 truncate">{u.email}</p>
                                        </div>
                                        <span className="badge border-0 bg-indigo-100 text-indigo-700 badge-sm font-bold tracking-wider px-3 py-2.5 rounded-lg">{u.rol}</span>
                                    </div>
                                ))}
                                {usuarios.length === 0 && <p className="text-sm text-slate-400 text-center py-6">No hay usuarios visibles.</p>}
                            </div>
                        )}
                    </div>
                </div>

                {/* COLUMNA DERECHA: FACTURACIÓN ELECTRÓNICA */}
                <div className="xl:col-span-2 space-y-8">
                    <div className="bg-white p-6 md:p-10 rounded-[2.5rem] shadow-sm border border-slate-100 transition-all hover:shadow-md relative overflow-hidden">
                        {/* Adorno de fondo esquinero */}
                        <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-50 rounded-bl-[100px] -z-0 opacity-50"></div>

                        <div className="relative z-10 flex flex-col md:flex-row md:items-start justify-between mb-8 pb-6 border-b border-slate-100 gap-4">
                            <div>
                                <h2 className="text-2xl font-black text-slate-800 flex items-center gap-3 tracking-tight">
                                    <div className="p-3 bg-emerald-100 text-emerald-600 rounded-2xl shadow-sm">
                                        <FaFileInvoiceDollar size={24} />
                                    </div>
                                    Facturación Electrónica
                                </h2>
                                <p className="text-slate-500 mt-2 ml-1 text-sm font-medium">Conexión oficial e integración con Proveedor Tecnológico DIAN.</p>
                            </div>

                            {/* Toggle habilitar tipo Pill */}
                            <div className="flex flex-col items-end gap-2 bg-white/50 backdrop-blur px-5 py-4 rounded-3xl border border-slate-200/60 shadow-sm">
                                <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Estado Emisión</span>
                                <div className="flex items-center gap-3">
                                    <span className={`text-xs font-bold px-3 py-1.5 rounded-full uppercase tracking-wider shadow-sm transition-colors ${feConfig.habilitado ? 'bg-emerald-500 text-white' : 'bg-slate-100 text-slate-400'}`}>
                                        {feConfig.habilitado ? 'ACTIVA' : 'INACTIVO'}
                                    </span>
                                    <input type="checkbox" name="habilitado" checked={feConfig.habilitado} onChange={handleFEInputChange} className="toggle toggle-success toggle-lg" />
                                </div>
                            </div>
                        </div>

                        <form id="form-fe" onSubmit={handleUpdateEmpresa} className="relative z-10">
                            <div className="space-y-10">

                                {/* Bloque 1: Entorno */}
                                <div className="p-7 bg-slate-50/80 rounded-[2rem] border border-slate-100/80">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                        <div>
                                            <h3 className="text-sm font-bold text-slate-800 mb-1 flex items-center gap-2">Ambiente de Trabajo</h3>
                                            <p className="text-xs text-slate-500 mb-4">Servidor destino para los XML y validaciones.</p>
                                            <select name="ambiente" value={feConfig.ambiente} onChange={handleFEInputChange} className="select select-bordered w-full bg-white border-transparent focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200/50 font-bold text-slate-700 shadow-sm rounded-xl">
                                                <option value="PRUEBAS">Habilitación (Sandbox Pruebas)</option>
                                                <option value="PRODUCCION">Producción (Emisión Real)</option>
                                            </select>
                                        </div>
                                        <div>
                                            <h3 className="text-sm font-bold text-slate-800 mb-1">API Token (Factus)</h3>
                                            <p className="text-xs text-slate-500 mb-4">Credenciales de autenticación en formato JSON.</p>
                                            <textarea name="api_token" value={feConfig.api_token} onChange={handleFEInputChange} className="textarea textarea-bordered w-full h-16 font-mono text-[11px] bg-white border-transparent focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200/50 shadow-sm rounded-xl" placeholder='{"client_id": "...", "client_secret": "..."}'></textarea>
                                        </div>
                                    </div>
                                </div>

                                {/* Bloque 2: Resolución DIAN */}
                                <div>
                                    <h3 className="text-base font-bold text-slate-800 mb-6 flex items-center gap-3">
                                        <div className="p-2 bg-emerald-50 rounded-lg text-emerald-500"><FaLandmark /></div>
                                        Datos de Resolución DIAN Autorizada
                                    </h3>
                                    <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
                                        <div className="md:col-span-2">
                                            <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-2 ml-1">Número Resolución</label>
                                            <input type="text" name="resolucion_numero" value={feConfig.resolucion_numero} onChange={handleFEInputChange} className="input input-bordered w-full bg-slate-50 focus:bg-white focus:border-emerald-500 rounded-xl font-medium" placeholder="Ej: 18760000001" />
                                        </div>
                                        <div>
                                            <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-2 ml-1">Fecha</label>
                                            <input type="date" name="resolucion_fecha" value={feConfig.resolucion_fecha} onChange={handleFEInputChange} className="input input-bordered w-full bg-slate-50 focus:bg-white focus:border-emerald-500 rounded-xl font-medium text-sm text-slate-600" />
                                        </div>
                                        <div>
                                            <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-2 ml-1">Prefijo</label>
                                            <input type="text" name="prefijo" value={feConfig.prefijo} onChange={handleFEInputChange} className="input input-bordered w-full font-mono text-center font-bold text-lg text-emerald-700 bg-emerald-50 focus:bg-white focus:border-emerald-500 rounded-xl border-emerald-100" placeholder="Ej: FV" />
                                        </div>
                                    </div>
                                </div>

                                {/* Bloque 3: Rangos */}
                                <div>
                                    <h3 className="text-base font-bold text-slate-800 mb-6 flex items-center gap-3">
                                        <div className="p-2 bg-emerald-50 rounded-lg text-emerald-500"><FaListOl /></div>
                                        Numeración y Rangos del Proveedor
                                    </h3>
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                        {/* Rango Autorizado */}
                                        <div className="p-6 bg-gradient-to-br from-emerald-50 to-green-50/30 rounded-3xl border border-emerald-100/50 flex flex-col justify-center shadow-sm">
                                            <label className="block text-[10px] font-black text-emerald-700 mb-5 text-center uppercase tracking-[0.2em]">Rango Autorizado DIAN</label>
                                            <div className="flex items-center gap-3">
                                                <input type="number" name="rango_desde" value={feConfig.rango_desde} onChange={handleFEInputChange} className="input shadow-inner w-full text-center font-mono font-bold text-emerald-800 bg-white border-0 focus:ring-2 focus:ring-emerald-400 rounded-xl" placeholder="Desde" />
                                                <span className="text-emerald-300 font-black text-xl">-</span>
                                                <input type="number" name="rango_hasta" value={feConfig.rango_hasta} onChange={handleFEInputChange} className="input shadow-inner w-full text-center font-mono font-bold text-emerald-800 bg-white border-0 focus:ring-2 focus:ring-emerald-400 rounded-xl" placeholder="Hasta" />
                                            </div>
                                        </div>

                                        {/* IDs Factus */}
                                        <div className="md:col-span-2 grid grid-cols-2 gap-x-6 gap-y-5 p-6 bg-white border border-slate-100 shadow-sm rounded-3xl">
                                            <div>
                                                <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">ID Rango Factura</label>
                                                <input type="number" name="factura_rango_id" value={feConfig.factura_rango_id} onChange={handleFEInputChange} className="input input-bordered input-sm w-full font-mono text-slate-600 bg-slate-50 focus:bg-white rounded-lg h-10" placeholder="Ej: 8" />
                                            </div>
                                            <div>
                                                <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">ID Rango Doc. Soporte</label>
                                                <input type="number" name="ds_rango_id" value={feConfig.ds_rango_id || ''} onChange={handleFEInputChange} className="input input-bordered input-sm w-full font-mono text-slate-600 bg-slate-50 focus:bg-white rounded-lg h-10" placeholder="Ej: 148" />
                                            </div>
                                            <div>
                                                <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">ID Rango Nota Crédito</label>
                                                <input type="number" name="nc_rango_id" value={feConfig.nc_rango_id || ''} onChange={handleFEInputChange} className="input input-bordered input-sm w-full font-mono text-slate-600 bg-slate-50 focus:bg-white rounded-lg h-10" placeholder="Ej: 9" />
                                            </div>
                                            <div>
                                                <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">ID Rango Nota Débito</label>
                                                <input type="number" name="nd_rango_id" value={feConfig.nd_rango_id || ''} onChange={handleFEInputChange} className="input input-bordered input-sm w-full font-mono text-slate-600 bg-slate-50 focus:bg-white rounded-lg h-10" placeholder="Ej: 10" />
                                            </div>
                                            <div className="col-span-2 mt-2 pt-4 border-t border-slate-50">
                                                <p className="text-[10px] text-slate-400 text-center uppercase tracking-wider font-semibold">(*) Identificadores de Numeración Interna del Proveedor Tecnológico</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </form>
                    </div>
                </div>

            </div>

            {/* BARRA INFERIOR FLOTANTE ESTILO MAC PARA GUARDAR TODO */}
            <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 bg-white/80 backdrop-blur-xl border border-slate-200/50 shadow-2xl rounded-full pl-8 pr-3 py-3 flex items-center justify-between gap-8 z-50 min-w-[320px] max-w-[800px] w-11/12 md:w-auto transition-transform hover:-translate-y-1 duration-300">
                <div className="hidden md:block">
                    <p className="text-sm font-black text-slate-800 tracking-tight">Menú de Guardado</p>
                    <p className="text-[11px] uppercase tracking-widest font-bold text-slate-400 mt-0.5">La configuración aplica a ambos formularios</p>
                </div>
                <button
                    type="button"
                    disabled={isSaving}
                    onClick={handleUpdateEmpresa}
                    className="btn bg-indigo-600 hover:bg-indigo-700 text-white border-0 shadow-lg shadow-indigo-200 hover:shadow-indigo-300 transition-all gap-3 px-8 rounded-full font-bold w-full md:w-auto tracking-wide text-sm h-12"
                >
                    {isSaving ? <span className="loading loading-spinner loading-sm"></span> : <FaSave size={18} />}
                    APLICAR Y GUARDAR CAMBIOS
                </button>
            </div>

        </div>
    );
}