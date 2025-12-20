// frontend/app/admin/tipos-documento/editar/[id]/page.js
'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';

import { useAuth } from '../../../../context/AuthContext';
import { apiService } from '../../../../../lib/apiService';

// --- Iconos Estándar v2.0 ---
import {
    FaFileInvoice, FaSave, FaBarcode, FaTag, FaCogs,
    FaExclamationCircle, FaLock, FaUnlock, FaBook,
    FaMoneyBillWave, FaExchangeAlt
} from 'react-icons/fa';

const funcionesDocumento = [
    { value: '', label: 'Ninguna (Documento estándar)' },
    { value: 'cartera_cliente', label: 'Factura de Venta (Activa CxC)' },
    { value: 'rc_cliente', label: 'Recibo de Caja (Activa CxC)' },
    { value: 'cxp_proveedor', label: 'Factura de Compra (Activa CxP)' },
    { value: 'pago_proveedor', label: 'Comprobante de Egreso (Activa CxP)' },
    { value: 'EGRESO_BANCARIO', label: 'Egreso Bancario (Pide # Cheque)' },
    { value: 'NOTA_CREDITO', label: 'Nota de Crédito' },
    { value: 'CIERRE_ANUAL', label: 'Cierre Anual (Proceso automático)' },
];

export default function EditarTipoDocumento() {
    const router = useRouter();
    const params = useParams();
    const { id } = params; // Obtener ID de la URL
    const { user, loading: authLoading } = useAuth();

    const [formData, setFormData] = useState({
        codigo: '',
        nombre: '',
        consecutivo_actual: 0,
        numeracion_manual: false,
        funcion_especial: '',
        afecta_inventario: false,
        cuenta_caja_id: null,
        cuenta_debito_cxc_id: null,
        cuenta_credito_cxc_id: null,
        cuenta_debito_cxp_id: null,
        cuenta_credito_cxp_id: null,
    });

    const [forzarEdicion, setForzarEdicion] = useState(false);
    const [error, setError] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [cuentas, setCuentas] = useState([]);

    // --- Estilos Estándar v2.0 ---
    const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
    const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white disabled:bg-gray-100 disabled:text-gray-500";
    const checkboxContainerClass = "flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer bg-white";
    const sectionTitleClass = "text-sm font-bold text-indigo-700 uppercase tracking-wide border-b border-indigo-100 pb-2 mb-4 flex items-center gap-2";

    useEffect(() => {
        if (id && user && !authLoading) {
            const fetchData = async () => {
                setIsLoading(true);
                try {
                    const [resTipoDoc, resCuentas] = await Promise.all([
                        apiService.get(`/tipos-documento/${id}`),
                        apiService.get('/plan-cuentas/list-flat/')
                    ]);

                    setFormData({
                        codigo: resTipoDoc.data.codigo,
                        nombre: resTipoDoc.data.nombre,
                        consecutivo_actual: resTipoDoc.data.consecutivo_actual,
                        numeracion_manual: resTipoDoc.data.numeracion_manual,
                        funcion_especial: resTipoDoc.data.funcion_especial || '',
                        afecta_inventario: resTipoDoc.data.afecta_inventario || false,
                        cuenta_caja_id: resTipoDoc.data.cuenta_caja_id || '',
                        cuenta_debito_cxc_id: resTipoDoc.data.cuenta_debito_cxc_id || '',
                        cuenta_credito_cxc_id: resTipoDoc.data.cuenta_credito_cxc_id || '',
                        cuenta_debito_cxp_id: resTipoDoc.data.cuenta_debito_cxp_id || '',
                        cuenta_credito_cxp_id: resTipoDoc.data.cuenta_credito_cxp_id || '',
                    });

                    setCuentas(resCuentas.data);

                } catch (err) {
                    setError(err.response?.data?.detail || 'Error al cargar los datos necesarios para la edición.');
                } finally {
                    setIsLoading(false);
                }
            };
            fetchData();
        }
    }, [id, user, authLoading]);

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        const finalValue = type === 'checkbox' ? checked : (value === '' ? null : value);
        setFormData(prevState => ({
            ...prevState,
            [name]: finalValue
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        try {
            const payload = {
                ...formData,
                cuenta_caja_id: formData.cuenta_caja_id ? parseInt(formData.cuenta_caja_id, 10) : null,
                cuenta_debito_cxc_id: formData.cuenta_debito_cxc_id ? parseInt(formData.cuenta_debito_cxc_id, 10) : null,
                cuenta_credito_cxc_id: formData.cuenta_credito_cxc_id ? parseInt(formData.cuenta_credito_cxc_id, 10) : null,
                cuenta_debito_cxp_id: formData.cuenta_debito_cxp_id ? parseInt(formData.cuenta_debito_cxp_id, 10) : null,
                cuenta_credito_cxp_id: formData.cuenta_credito_cxp_id ? parseInt(formData.cuenta_credito_cxp_id, 10) : null,
            };

            await apiService.put(`/tipos-documento/${id}`, payload);
            router.push('/admin/tipos-documento');

        } catch (err) {
            let errorMessage = 'Ocurrió un error al actualizar.';
            if (Array.isArray(err.response?.data?.detail) && err.response.data.detail.length > 0) {
                const errorDetail = err.response.data.detail[0];
                const fieldName = errorDetail.loc && errorDetail.loc.length > 1 ? errorDetail.loc[1] : 'Campo desconocido';
                errorMessage = `Error en el campo '${fieldName}': ${errorDetail.msg}`;
            } else if (err.response?.data?.detail) {
                errorMessage = err.response.data.detail;
            }
            setError(errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

    if (authLoading || isLoading) {
        return (
            <div className="min-h-screen bg-gray-50 flex justify-center items-center">
                <span className="loading loading-spinner loading-lg text-indigo-600"></span>
            </div>
        );
    }

    // --- LÓGICA DE CUENTAS: LIBERACIÓN TOTAL ---
    const cuentasAuxiliares = cuentas.filter(c => c.permite_movimiento);

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
            <div className="max-w-7xl mx-auto">

                {/* 1. ENCABEZADO */}
                <div className="flex justify-between items-center mb-8">
                    <div className="flex items-center gap-3">
                        <div className="p-3 bg-indigo-100 text-indigo-600 rounded-xl shadow-sm">
                            <FaFileInvoice className="text-2xl" />
                        </div>
                        <div>
                            <div className="flex items-center gap-3">
                                <h1 className="text-3xl font-bold text-gray-800 tracking-tight">Editar Tipo Documento</h1>
                                <button
                                    onClick={() => window.open('/manual/capitulo_9_consecutivos.html', '_blank')}
                                    className="flex items-center gap-2 px-2 py-1 bg-white border border-indigo-200 text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors font-medium shadow-sm"
                                    type="button"
                                >
                                    <FaBook /> <span className="hidden md:inline">Manual</span>
                                </button>
                            </div>
                            <p className="text-gray-500 text-sm mt-1">Ajuste la configuración contable y operativa.</p>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        {/* Actions consolidated */}
                    </div>
                </div>

                {/* 2. FORMULARIO PRINCIPAL */}
                <form onSubmit={handleSubmit} className="animate-fadeIn">

                    {/* TARJETA 1: DATOS BÁSICOS */}
                    <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-8 mb-8">
                        <h3 className={sectionTitleClass}><FaTag /> Información General</h3>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                            {/* Código */}
                            <div>
                                <label htmlFor="codigo" className={labelClass}><FaBarcode className="inline mr-1" /> Código</label>
                                <input type="text" name="codigo" id="codigo" disabled value={formData.codigo} className={`${inputClass} font-mono font-bold bg-gray-100 cursor-not-allowed`} />
                            </div>

                            {/* Nombre */}
                            <div>
                                <label htmlFor="nombre" className={labelClass}>Nombre</label>
                                <input type="text" name="nombre" id="nombre" required value={formData.nombre} onChange={handleChange} className={inputClass} />
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* Consecutivo con Candado de Seguridad */}
                            <div>
                                <div className="flex justify-between items-center mb-1">
                                    <label htmlFor="consecutivo_actual" className={labelClass}>Último Consecutivo</label>
                                    {!formData.numeracion_manual && (
                                        <button type="button" onClick={() => setForzarEdicion(!forzarEdicion)} className="text-xs text-indigo-600 hover:text-indigo-800 flex items-center gap-1 font-semibold transition-colors">
                                            {forzarEdicion ? <FaUnlock /> : <FaLock />} {forzarEdicion ? 'Bloquear Edición' : 'Forzar Edición'}
                                        </button>
                                    )}
                                </div>
                                <input
                                    type="number" name="consecutivo_actual" id="consecutivo_actual" required
                                    value={formData.consecutivo_actual} onChange={handleChange}
                                    className={`${inputClass} font-mono`}
                                    disabled={!formData.numeracion_manual && !forzarEdicion}
                                />
                            </div>

                            {/* Función Especial */}
                            <div>
                                <label htmlFor="funcion_especial" className={labelClass}><FaCogs className="inline mr-1" /> Función Especial</label>
                                <select name="funcion_especial" value={formData.funcion_especial || ''} onChange={handleChange} className={inputClass}>
                                    {funcionesDocumento.map(f => <option key={f.value} value={f.value}>{f.label}</option>)}
                                </select>
                            </div>
                        </div>

                        {/* Toggles / Checkboxes */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8 pt-6 border-t border-gray-100">
                            <label className={checkboxContainerClass}>
                                <input type="checkbox" name="numeracion_manual" id="numeracion_manual" checked={formData.numeracion_manual} onChange={handleChange} className="checkbox checkbox-primary mr-3" />
                                <div>
                                    <span className="block text-sm font-bold text-gray-700">Numeración Manual</span>
                                    <span className="text-xs text-gray-500">Permite editar el consecutivo al crear documento.</span>
                                </div>
                            </label>
                            <label className={checkboxContainerClass}>
                                <input type="checkbox" name="afecta_inventario" id="afecta_inventario" checked={formData.afecta_inventario} onChange={handleChange} className="checkbox checkbox-primary mr-3" />
                                <div>
                                    <span className="block text-sm font-bold text-gray-700">Afecta Inventario</span>
                                    <span className="text-xs text-gray-500">Habilita movimientos de entrada/salida de stock.</span>
                                </div>
                            </label>
                        </div>
                    </div>

                    {/* TARJETA 2: CONFIGURACIÓN CONTABLE */}
                    <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-8 mb-8">
                        <h3 className={sectionTitleClass}><FaBook /> Mapeo Contable Automático</h3>
                        <p className="text-sm text-gray-500 mb-6">Seleccione las cuentas auxiliares que el sistema usará automáticamente al generar asientos.</p>

                        {/* Sección 1: Tesorería */}
                        <div className="mb-6 p-4 bg-gray-50 rounded-xl border border-gray-100">
                            <h4 className="text-xs font-bold text-gray-600 uppercase mb-3 flex items-center gap-2">
                                <FaMoneyBillWave className="text-green-600" /> Tesorería / Caja / Bancos
                            </h4>
                            <div>
                                <label htmlFor="cuenta_caja_id" className={labelClass}>Cuenta de Dinero (Débito)</label>
                                <select name="cuenta_caja_id" value={formData.cuenta_caja_id || ''} onChange={handleChange} className={inputClass}>
                                    <option value="">-- No aplica --</option>
                                    {cuentasAuxiliares.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
                                </select>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* Sección 2: Cartera */}
                            <div className="p-4 bg-blue-50/50 rounded-xl border border-blue-100">
                                <h4 className="text-xs font-bold text-blue-700 uppercase mb-3 flex items-center gap-2">
                                    <FaExchangeAlt /> Cuentas por Cobrar (Clientes)
                                </h4>
                                <div className="space-y-4">
                                    <div>
                                        <label htmlFor="cuenta_debito_cxc_id" className={labelClass}>Cuenta Débito (Cartera)</label>
                                        <select name="cuenta_debito_cxc_id" value={formData.cuenta_debito_cxc_id || ''} onChange={handleChange} className={inputClass}>
                                            <option value="">-- No aplica --</option>
                                            {cuentasAuxiliares.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
                                        </select>
                                    </div>
                                    <div>
                                        <label htmlFor="cuenta_credito_cxc_id" className={labelClass}>Cuenta Crédito (Abono)</label>
                                        <select name="cuenta_credito_cxc_id" value={formData.cuenta_credito_cxc_id || ''} onChange={handleChange} className={inputClass}>
                                            <option value="">-- No aplica --</option>
                                            {cuentasAuxiliares.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
                                        </select>
                                    </div>
                                </div>
                            </div>

                            {/* Sección 3: Proveedores */}
                            <div className="p-4 bg-orange-50/50 rounded-xl border border-orange-100">
                                <h4 className="text-xs font-bold text-orange-700 uppercase mb-3 flex items-center gap-2">
                                    <FaExchangeAlt /> Cuentas por Pagar (Proveedores)
                                </h4>
                                <div className="space-y-4">
                                    <div>
                                        <label htmlFor="cuenta_debito_cxp_id" className={labelClass}>Cuenta Débito (Abono)</label>
                                        <select name="cuenta_debito_cxp_id" value={formData.cuenta_debito_cxp_id || ''} onChange={handleChange} className={inputClass}>
                                            <option value="">-- No aplica --</option>
                                            {cuentasAuxiliares.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
                                        </select>
                                    </div>
                                    <div>
                                        <label htmlFor="cuenta_credito_cxp_id" className={labelClass}>Cuenta Crédito (Deuda)</label>
                                        <select name="cuenta_credito_cxp_id" value={formData.cuenta_credito_cxp_id || ''} onChange={handleChange} className={inputClass}>
                                            <option value="">-- No aplica --</option>
                                            {cuentasAuxiliares.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
                                        </select>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* ALERTAS DE ERROR */}
                    {error && (
                        <div className="alert alert-error shadow-lg mb-6 rounded-xl text-white">
                            <FaExclamationCircle className="text-xl" />
                            <span>{error}</span>
                        </div>
                    )}

                    {/* BOTÓN GUARDAR FLOTANTE/FIJO */}
                    <div className="flex justify-end pt-4">
                        <button type="submit" disabled={isLoading} className="btn btn-primary bg-indigo-600 hover:bg-indigo-700 text-white shadow-md rounded-lg font-bold px-8 py-3 text-lg flex items-center gap-2">
                            {isLoading ? (
                                <><span className="loading loading-spinner loading-sm"></span> Guardando...</>
                            ) : (
                                <><FaSave /> Guardar Cambios</>
                            )}
                        </button>
                    </div>

                </form>
            </div>
        </div>
    );
}