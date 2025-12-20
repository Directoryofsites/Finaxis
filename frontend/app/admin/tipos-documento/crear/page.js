// frontend/app/admin/tipos-documento/crear/page.js
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../../context/AuthContext';
import { apiService } from '../../../../lib/apiService';


// --- Iconos Estándar v2.0 ---
import { FaFileInvoice, FaSave, FaBarcode, FaTag, FaCogs, FaExclamationCircle } from 'react-icons/fa';

const funcionesDocumento = [
    { value: '', label: 'Ninguna (Documento estándar)' },
    { value: 'EGRESO_BANCARIO', label: 'Egreso Bancario (Pide # Cheque)' },
    { value: 'FACTURA_VENTA', label: 'Factura de Venta (Activa CxC)' },
    { value: 'RECIBO_CAJA', label: 'Recibo de Caja (Activa CxC)' },
    { value: 'FACTURA_COMPRA', label: 'Factura de Compra (Activa CxP)' },
    { value: 'NOTA_CREDITO', label: 'Nota de Crédito' },
    { value: 'CIERRE_ANUAL', label: 'Cierre Anual (Proceso automático)' },
];

export default function CrearTipoDocumentoPage() {
    const router = useRouter();
    const { user, authLoading } = useAuth();

    const [formData, setFormData] = useState({
        codigo: '',
        nombre: '',
        numeracion_manual: false,
        funcion_especial: '',
        afecta_inventario: false,
    });

    const [error, setError] = useState(null);
    const [isLoading, setIsLoading] = useState(false);

    // --- Clases Estándar v2.0 ---
    const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
    const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white";
    const checkboxContainerClass = "flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer";

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prevState => ({
            ...prevState,
            [name]: type === 'checkbox' ? checked : value,
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        if (!user?.empresaId) {
            setError("No se pudo identificar la empresa del usuario. Por favor, inicie sesión de nuevo.");
            setIsLoading(false);
            return;
        }

        try {
            const payload = {
                ...formData,
                funcion_especial: formData.funcion_especial || null,
                empresa_id: user.empresaId,
            };

            await apiService.post('/tipos-documento/', payload);
            router.push('/admin/tipos-documento');

        } catch (err) {
            let errorMessage = 'Ocurrió un error al crear el tipo de documento.';
            if (Array.isArray(err.response?.data?.detail) && err.response.data.detail.length > 0) {
                errorMessage = err.response.data.detail[0].msg;
            } else if (err.response?.data?.detail) {
                errorMessage = err.response.data.detail;
            }
            setError(errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

    if (authLoading) {
        return (
            <div className="min-h-screen bg-gray-50 flex justify-center items-center">
                <span className="loading loading-spinner loading-lg text-indigo-600"></span>
            </div>
        );
    }

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
                            <h1 className="text-3xl font-bold text-gray-800 tracking-tight">Crear Tipo Documento</h1>
                            <p className="text-gray-500 text-sm mt-1">Configure las reglas de negocio para este comprobante.</p>
                        </div>
                    </div>
                </div>

                {/* 2. FORMULARIO (CARD) */}
                <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-8 animate-fadeIn">
                    <form onSubmit={handleSubmit}>

                        {/* Sección Superior: Datos Básicos */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                            <div>
                                <label htmlFor="codigo" className={labelClass}>
                                    <FaBarcode className="inline mr-1" /> Código (Prefijo)
                                </label>
                                <input
                                    type="text"
                                    name="codigo"
                                    id="codigo"
                                    required
                                    maxLength="5"
                                    value={formData.codigo}
                                    onChange={handleChange}
                                    className={`${inputClass} font-mono uppercase placeholder:normal-case`}
                                    placeholder="Ej: FV"
                                />
                                <p className="text-xs text-gray-400 mt-1">Máximo 5 caracteres. Ej: RC, CE, FV.</p>
                            </div>

                            <div>
                                <label htmlFor="nombre" className={labelClass}>
                                    <FaTag className="inline mr-1" /> Nombre del Documento
                                </label>
                                <input
                                    type="text"
                                    name="nombre"
                                    id="nombre"
                                    required
                                    value={formData.nombre}
                                    onChange={handleChange}
                                    className={inputClass}
                                    placeholder="Ej: Factura de Venta Nacional"
                                />
                            </div>
                        </div>

                        {/* Sección Media: Configuración Avanzada */}
                        <div className="mb-8">
                            <label htmlFor="funcion_especial" className={labelClass}>
                                <FaCogs className="inline mr-1" /> Función Especial (Comportamiento)
                            </label>
                            <select
                                name="funcion_especial"
                                id="funcion_especial"
                                value={formData.funcion_especial}
                                onChange={handleChange}
                                className={inputClass}
                            >
                                {funcionesDocumento.map(func => (
                                    <option key={func.value} value={func.value}>{func.label}</option>
                                ))}
                            </select>
                        </div>

                        {/* Sección Inferior: Interruptores (Checkboxes) */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
                            <label className={checkboxContainerClass}>
                                <input
                                    type="checkbox"
                                    name="numeracion_manual"
                                    id="numeracion_manual"
                                    checked={formData.numeracion_manual}
                                    onChange={handleChange}
                                    className="checkbox checkbox-primary mr-3"
                                />
                                <div>
                                    <span className="block text-sm font-bold text-gray-700">Numeración Manual</span>
                                    <span className="text-xs text-gray-500">Permite editar el consecutivo al crear.</span>
                                </div>
                            </label>

                            <label className={checkboxContainerClass}>
                                <input
                                    type="checkbox"
                                    name="afecta_inventario"
                                    id="afecta_inventario"
                                    checked={formData.afecta_inventario}
                                    onChange={handleChange}
                                    className="checkbox checkbox-primary mr-3"
                                />
                                <div>
                                    <span className="block text-sm font-bold text-gray-700">Afecta Inventario</span>
                                    <span className="text-xs text-gray-500">Habilita movimientos de entrada/salida de stock.</span>
                                </div>
                            </label>
                        </div>

                        {/* Mensajes de Error */}
                        {error && (
                            <div className="alert alert-error shadow-lg mb-6 rounded-xl text-white">
                                <FaExclamationCircle className="text-xl" />
                                <span>{error}</span>
                            </div>
                        )}

                        {/* Footer de Acciones */}
                        <div className="flex justify-end pt-6 border-t border-gray-100">
                            <button
                                type="submit"
                                disabled={isLoading || !user?.empresaId}
                                className="btn btn-primary bg-indigo-600 hover:bg-indigo-700 text-white shadow-md rounded-lg font-bold px-8"
                            >
                                {isLoading ? (
                                    <>
                                        <span className="loading loading-spinner loading-xs mr-2"></span> Guardando...
                                    </>
                                ) : (
                                    <>
                                        <FaSave className="mr-2" /> Guardar Configuración
                                    </>
                                )}
                            </button>
                        </div>

                    </form>
                </div>
            </div>
        </div>
    );
}