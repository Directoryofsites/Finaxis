"use client";
import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { FaFileInvoiceDollar, FaFileContract, FaWallet, FaSync, FaCheckCircle, FaExclamationCircle, FaClock, FaEye } from 'react-icons/fa';
import { apiService } from '../lib/apiService';

/**
 * CleanHomePage - Dashboard Adaptativo
 * 
 * - Si is_lite_mode = True: Muestra Dashboard Express (Botones Grandes + Wallet + Historial)
 * - Si is_lite_mode = False: Muestra Logo Branding (Comportamiento Original)
 */
export default function CleanHomePage({ user }) {
    const router = useRouter();
    const [facturas, setFacturas] = useState([]);
    const [loadingFacturas, setLoadingFacturas] = useState(false);
    const [saldoFacturas, setSaldoFacturas] = useState(user?.empresa?.saldo_facturas_venta || 0);

    // --- LÓGICA MODO EXPRESS ---
    const isLiteMode = user?.empresa?.is_lite_mode || false;
    const saldoDocsSoporte = user?.empresa?.saldo_documentos_soporte || 0;

    // Efecto para cargar historial y refrescar saldo al montar
    useEffect(() => {
        if (isLiteMode) {
            fetchFacturas();
            refreshSaldo();
        }
    }, [isLiteMode]);

    const refreshSaldo = async () => {
        try {
            // Recargar datos del usuario/empresa para asegurar saldo actualizado
            // NOTA: Esto asume que hay un endpoint O que recargamos la página completa.
            // Por ahora, confiamos en router.refresh() si el backend soporta revalidación,
            // o hacemos un fetch manual si tenemos endpoint de "me" o "empresa".
            // Para simplicidad en este paso, usaremos router.refresh() de Next.js
            router.refresh();

            // Si router.refresh() no actualiza el prop 'user' in-place inmediatamente (que no suele hacerlo sin server actions),
            // lo ideal sería hacer un fetch a /api/v1/usuarios/me o /api/v1/empresas/me.
            // Implementación temporal robusta:
            const response = await apiService.get('/usuarios/me');
            if (response.data && response.data.empresa) {
                setSaldoFacturas(response.data.empresa.saldo_facturas_venta);
            }

        } catch (error) {
            console.error("Error refrescando saldo:", error);
        }
    };

    const fetchFacturas = async () => {
        setLoadingFacturas(true);
        try {
            const response = await apiService.get('/documentos', {
                params: {
                    limit: 5,
                    sort: 'fecha_creacion:desc', // Ajustar según backend
                    // tipo_documento_id: 1 // Asumiendo 1 = Factura Venta, ajustar si es dinámico
                }
            });
            // El backend devuelve { data: [...], total: ... } o directamente [...]
            const data = response.data.data || response.data;
            setFacturas(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error("Error cargando historial:", error);
        } finally {
            setLoadingFacturas(false);
        }
    };

    if (isLiteMode) {
        return (
            <div className="h-full w-full flex flex-col bg-gray-50 p-6 md:p-12 overflow-y-auto">
                {/* Header Bienvenida */}
                <div className="mb-8 flex justify-between items-center">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-800">Hola, {user?.nombre || 'Emprendedor'}</h1>
                        <p className="text-slate-500">Todo listo para facturar hoy.</p>
                    </div>
                    <button onClick={refreshSaldo} className="p-2 text-blue-600 hover:bg-blue-50 rounded-full transition-colors" title="Actualizar Saldo">
                        <FaSync />
                    </button>
                </div>

                {/* Widget Wallet (Saldo) */}
                <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 mb-8 flex flex-col md:flex-row items-center justify-between">
                    <div className="flex items-center mb-4 md:mb-0">
                        <div className={`p-4 rounded-full ${saldoFacturas > 5 ? 'bg-green-100 text-green-600' : 'bg-orange-100 text-orange-600'} mr-4`}>
                            <FaWallet size={24} />
                        </div>
                        <div>
                            <h2 className="text-lg font-semibold text-slate-700">Tu Plan Actual</h2>
                            {saldoFacturas > 0 ? (
                                <p className="text-slate-500 text-sm">Tienes saldo disponible para operar.</p>
                            ) : (
                                <p className="text-red-500 text-sm font-bold">¡Saldo Agotado! Recarga para facturar.</p>
                            )}
                        </div>
                    </div>

                    <div className="flex space-x-8 text-center">
                        <div>
                            <span className={`block text-3xl font-bold ${saldoFacturas > 5 ? 'text-slate-800' : 'text-red-600'}`}>
                                {saldoFacturas}
                            </span>
                            <span className="text-xs text-slate-400 uppercase tracking-wider">Facturas</span>
                        </div>
                        <div className="border-l border-slate-100 pl-8">
                            <span className="block text-3xl font-bold text-slate-800">{saldoDocsSoporte}</span>
                            <span className="text-xs text-slate-400 uppercase tracking-wider">Doc. Soporte</span>
                        </div>
                    </div>
                </div>

                {/* Grid de Acciones Principales */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto w-full mb-10">
                    {/* Botón Factura Venta */}
                    <button
                        onClick={() => router.push('/contabilidad/facturacion')}
                        className={`group relative flex flex-col items-center justify-center p-8 bg-white border-2 border-slate-100 rounded-2xl shadow-sm hover:shadow-lg hover:border-blue-500 transition-all duration-200
                        ${saldoFacturas <= 0 ? 'opacity-50 cursor-not-allowed grayscale' : ''}`}
                        disabled={saldoFacturas <= 0}
                    >
                        <div className="p-5 bg-blue-50 text-blue-600 rounded-full mb-4 group-hover:bg-blue-600 group-hover:text-white transition-colors duration-200">
                            <FaFileInvoiceDollar size={40} />
                        </div>
                        <h3 className="text-xl font-bold text-slate-800 mb-2">Crear Factura</h3>
                        <p className="text-center text-slate-500 text-sm">
                            Venta de Bienes o Servicios
                        </p>
                        {saldoFacturas <= 0 && (
                            <span className="absolute top-4 right-4 bg-red-100 text-red-600 text-xs font-bold px-2 py-1 rounded">
                                SIN SALDO
                            </span>
                        )}
                    </button>

                    {/* Botón Documento Soporte */}
                    <button
                        onClick={() => router.push('/contabilidad/documentos?tipo=DS')} // Asumiendo ruta, ajustar si es necesario
                        className="group flex flex-col items-center justify-center p-8 bg-white border-2 border-slate-100 rounded-2xl shadow-sm hover:shadow-lg hover:border-purple-500 transition-all duration-200"
                    >
                        <div className="p-5 bg-purple-50 text-purple-600 rounded-full mb-4 group-hover:bg-purple-600 group-hover:text-white transition-colors duration-200">
                            <FaFileContract size={40} />
                        </div>
                        <h3 className="text-xl font-bold text-slate-800 mb-2">Documento Soporte</h3>
                        <p className="text-center text-slate-500 text-sm">
                            Compras a no obligados a facturar
                        </p>
                    </button>
                </div>

                {/* Tabla de Historial Reciente */}
                <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden max-w-4xl mx-auto w-full">
                    <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
                        <h3 className="font-bold text-slate-700">Últimas Facturas</h3>
                        <button onClick={fetchFacturas} className="text-xs text-blue-600 hover:underline">Refrescar</button>
                    </div>

                    {loadingFacturas ? (
                        <div className="p-8 text-center text-gray-400">Cargando historial...</div>
                    ) : facturas.length === 0 ? (
                        <div className="p-8 text-center text-gray-400">Aún no has creado facturas.</div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm text-left">
                                <thead className="text-xs text-gray-500 uppercase bg-gray-50">
                                    <tr>
                                        <th className="px-6 py-3">Número</th>
                                        <th className="px-6 py-3">Fecha</th>
                                        <th className="px-6 py-3">Cliente</th>
                                        <th className="px-6 py-3 text-right">Total</th>
                                        <th className="px-6 py-3 text-center">Estado</th>
                                        <th className="px-6 py-3"></th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {facturas.map((factura) => (
                                        <tr key={factura.id} className="border-b border-gray-100 hover:bg-gray-50">
                                            <td className="px-6 py-4 font-medium text-gray-900">
                                                {factura.numero || `ID: ${factura.id}`}
                                            </td>
                                            <td className="px-6 py-4 text-gray-500">
                                                {factura.fecha ? factura.fecha.split('T')[0] : ''}
                                            </td>
                                            <td className="px-6 py-4 text-gray-500 truncate max-w-[150px]">
                                                {factura.tercero?.razon_social || factura.tercero?.nombre_comercial || 'Consumidor Final'}
                                            </td>
                                            <td className="px-6 py-4 text-gray-900 font-bold text-right">
                                                ${parseFloat(factura.total_factura || 0).toLocaleString()}
                                            </td>
                                            <td className="px-6 py-4 text-center">
                                                {factura.estado_dian === 'EXITOSO' ? (
                                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                                        <FaCheckCircle className="mr-1" /> Emitida
                                                    </span>
                                                ) : factura.estado_dian === 'ERROR' || factura.estado_dian === 'FALLIDO' ? (
                                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                                        <FaExclamationCircle className="mr-1" /> Error
                                                    </span>
                                                ) : (
                                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                                                        <FaClock className="mr-1" /> Pendiente
                                                    </span>
                                                )}
                                            </td>
                                            <td className="px-6 py-4 text-right">
                                                <button
                                                    onClick={() => window.open(`/api/v1/documentos/${factura.id}/pdf`, '_blank')}
                                                    className="text-blue-600 hover:text-blue-800"
                                                    title="Ver PDF"
                                                >
                                                    <FaEye />
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                    <div className="bg-gray-50 px-6 py-3 text-right">
                        <button onClick={() => router.push('/contabilidad/explorador')} className="text-xs font-medium text-blue-600 hover:text-blue-800">Ver Todo el Historial &rarr;</button>
                    </div>
                </div>

                {/* Footer simple */}
                <div className="mt-auto pt-10 text-center text-slate-400 text-sm">
                    <p>Modo Express Activo • Finaxis ERP</p>
                </div>
            </div>
        );
    }

    // --- RENDERIZADO ORIGINAL (Logo Branding) ---
    return (
        <div className="h-full w-full flex flex-col items-center justify-center bg-gray-50 select-none overflow-hidden relative">

            {/* Branding Central (Marca de Agua) */}
            <div className="flex flex-col items-center justify-center opacity-30 transform scale-125 pointer-events-none filter saturate-0">
                <img
                    src="/logo_finaxis_real.png"
                    alt="Finaxis ERP"
                    className="w-auto h-48 object-contain mb-8 mix-blend-multiply contrast-[1.2] brightness-[1.1]"
                />
            </div>

            {/* Pista de Uso (Sutil, abajo) */}
            <div className="absolute bottom-10 text-slate-400 text-sm font-medium animate-pulse flex items-center">
                <span className="mr-2">Presione</span>
                <kbd className="px-2 py-0.5 bg-white border border-gray-300 rounded shadow-[0_2px_0_rgba(0,0,0,0.1)] text-slate-600 font-bold font-mono text-xs">Alt</kbd>
                <span className="ml-2">para Menú Principal</span>
            </div>

            {/* Decoración de Fondo (Patrón de Puntos) */}
            <div className="absolute inset-0 z-[-1] opacity-[0.03]"
                style={{
                    backgroundImage: 'radial-gradient(#000000 1px, transparent 1px)',
                    backgroundSize: '24px 24px'
                }}
            ></div>
        </div>
    );
}
