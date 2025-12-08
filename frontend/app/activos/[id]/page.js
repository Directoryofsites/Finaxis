'use client';
import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiService } from '../../../lib/apiService'; // Ajustar path relativo ../../../
import { FaArrowLeft, FaPrint, FaHistory, FaCalculator } from 'react-icons/fa';

export default function FichaActivoPage({ params }) {
    const { id } = params;
    const router = useRouter();
    const [activo, setActivo] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (id) fetchActivo();
    }, [id]);

    const fetchActivo = async () => {
        try {
            const res = await apiService.get(`/activos/${id}`);
            setActivo(res.data);
        } catch (error) {
            console.error("Error:", error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="p-10 text-center">Cargando Ficha Técnica...</div>;
    if (!activo) return <div className="p-10 text-center text-red-600">Activo no encontrado.</div>;

    // Cálculos Visuales
    const costo = parseFloat(activo.costo_adquisicion);
    const depAcum = parseFloat(activo.depreciacion_acumulada_niif);
    const valorNeto = costo - depAcum;
    const porcentajeDep = (depAcum / costo) * 100;

    return (
        <div className="p-6 max-w-6xl mx-auto">
            {/* HERRAMIENTAS SUPERIORES */}
            <div className="flex justify-between items-center mb-6 no-print">
                <button
                    onClick={() => router.back()}
                    className="flex items-center gap-2 text-gray-600 hover:text-blue-600 font-medium"
                >
                    <FaArrowLeft /> Regresar
                </button>
                <button className="bg-gray-800 text-white px-4 py-2 rounded flex items-center gap-2 hover:bg-gray-700">
                    <FaPrint /> Imprimir Ficha
                </button>
            </div>

            <div className="bg-white shadow-2xl rounded-xl overflow-hidden border border-gray-200">
                {/* ENCABEZADO */}
                <div className="bg-gradient-to-r from-blue-700 to-blue-900 text-white p-6">
                    <div className="flex justify-between items-start">
                        <div>
                            <h1 className="text-3xl font-bold">{activo.nombre}</h1>
                            <p className="text-blue-200 mt-1 text-lg font-mono">PLACA: {activo.codigo}</p>
                        </div>
                        <div className="text-right">
                            <span className={`px-3 py-1 rounded-full text-sm font-bold bg-white text-blue-900`}>
                                {activo.estado}
                            </span>
                            <p className="text-sm mt-2 opacity-80">ID Sistema: {activo.id}</p>
                        </div>
                    </div>
                </div>

                {/* CUERPO DE LA FICHA */}
                <div className="p-8 grid grid-cols-1 md:grid-cols-3 gap-8">

                    {/* COLUMNA 1: DETALLES FÍSICOS */}
                    <div className="space-y-4">
                        <h3 className="text-gray-500 font-bold uppercase text-xs tracking-wider border-b pb-1">Identificación</h3>
                        <div>
                            <label className="text-sm text-gray-500 block">Serial / Serie</label>
                            <span className="font-semibold text-gray-800">{activo.serial || 'N/A'}</span>
                        </div>
                        <div>
                            <label className="text-sm text-gray-500 block">Marca / Modelo</label>
                            <span className="text-gray-800">{activo.marca} {activo.modelo}</span>
                        </div>
                        <div>
                            <label className="text-sm text-gray-500 block">Ubicación Actual</label>
                            <span className="text-gray-800 font-medium bg-gray-100 px-2 py-1 rounded">{activo.ubicacion}</span>
                        </div>
                        <div>
                            <label className="text-sm text-gray-500 block">Custodio (Responsable)</label>
                            <span className="text-gray-800">{activo.responsable ? activo.responsable.razon_social : 'Sin asignar'}</span>
                        </div>
                    </div>

                    {/* COLUMNA 2: INFORMACIÓN CONTABLE */}
                    <div className="space-y-4">
                        <h3 className="text-gray-500 font-bold uppercase text-xs tracking-wider border-b pb-1">Datos Contables</h3>
                        <div className="flex justify-between">
                            <label className="text-sm text-gray-500">Fecha Compra</label>
                            <span className="font-mono text-gray-800">{activo.fecha_compra}</span>
                        </div>
                        <div className="flex justify-between">
                            <label className="text-sm text-gray-500">Costo Histórico</label>
                            <span className="font-mono font-bold text-gray-900">$ {costo.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between text-red-600">
                            <label className="text-sm">Depreciación Acum.</label>
                            <span className="font-mono font-bold">- $ {depAcum.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between border-t border-gray-300 pt-2 mt-2">
                            <label className="text-base font-bold text-blue-900">VALOR NETO (Libros)</label>
                            <span className="font-mono font-bold text-xl text-blue-700">$ {valorNeto.toLocaleString()}</span>
                        </div>
                    </div>

                    {/* COLUMNA 3: ESTADO VISUAL */}
                    <div className="bg-gray-50 p-4 rounded-lg text-center flex flex-col justify-center items-center">
                        <div className="w-32 h-32 rounded-full border-8 border-gray-200 relative flex items-center justify-center">
                            {/* Simulación Gráfica Circular */}
                            <div className="absolute inset-0 rounded-full border-8 border-blue-500 transition-all duration-1000"
                                style={{ clipPath: `polygon(0 0, 100% 0, 100% ${porcentajeDep}%, 0 ${porcentajeDep}%)` }}>
                                {/* Nota: Esto es un hack visual simple. En prod usar chart.js */}
                            </div>
                            <span className="text-2xl font-bold text-gray-700 z-10">{Math.round(100 - porcentajeDep)}%</span>
                        </div>
                        <p className="text-sm font-medium text-gray-500 mt-2">Vida Útil Restante Estimada</p>
                    </div>

                </div>

                {/* HISTORIAL (NOVEDADES) */}
                <div className="border-t border-gray-200">
                    <div className="p-4 bg-gray-50 border-b border-gray-200">
                        <h3 className="font-bold flex items-center gap-2 text-gray-700">
                            <FaHistory /> Historial de Movimientos (Kardex del Activo)
                        </h3>
                    </div>
                    {/* Aquí iría la tabla de Novedades si tuviéramos el endpoint de novedades por activo. Por ahora placeholder. */}
                    <div className="p-8 text-center text-gray-400 italic">
                        El historial detallado se cargará en la próxima actualización.
                    </div>
                </div>
            </div>
        </div>
    );
}
