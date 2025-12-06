"use client";
import React, { useState } from 'react';
import { FaCalendarAlt, FaPlus, FaArrowLeft, FaTrash, FaSave } from 'react-icons/fa';
import Link from 'next/link';

export default function CalendarioTributario() {
    // Estado para la lista de obligaciones (Manual)
    const [obligaciones, setObligaciones] = useState([
        { id: 1, impuesto: 'IVA', periodo: 'Bimestre 1 2025', vencimiento: '2025-03-10', estado: 'Pendiente' },
        { id: 2, impuesto: 'Retención en la Fuente', periodo: 'Enero 2025', vencimiento: '2025-02-14', estado: 'Borrador' },
    ]);

    // Estado para el formulario de nueva obligación
    const [nuevaObligacion, setNuevaObligacion] = useState({
        impuesto: 'IVA',
        periodo: '',
        vencimiento: '',
        estado: 'Pendiente'
    });

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setNuevaObligacion(prev => ({ ...prev, [name]: value }));
    };

    const agregarObligacion = (e) => {
        e.preventDefault();
        if (!nuevaObligacion.periodo || !nuevaObligacion.vencimiento) return;

        const nueva = {
            id: Date.now(),
            ...nuevaObligacion
        };

        setObligaciones([...obligaciones, nueva]);
        setNuevaObligacion({ impuesto: 'IVA', periodo: '', vencimiento: '', estado: 'Pendiente' }); // Reset form
    };

    const eliminarObligacion = (id) => {
        setObligaciones(obligaciones.filter(o => o.id !== id));
    };

    const getDiasRestantes = (fecha) => {
        const diff = new Date(fecha) - new Date();
        return Math.ceil(diff / (1000 * 60 * 60 * 24));
    };

    return (
        <div className="p-6 space-y-8">
            {/* Header */}
            <div className="flex items-center space-x-4 mb-6">
                <Link href="/impuestos" className="text-gray-500 hover:text-gray-700">
                    <FaArrowLeft className="text-xl" />
                </Link>
                <h1 className="text-2xl font-bold text-gray-800 flex items-center">
                    <FaCalendarAlt className="mr-3 text-blue-600" /> Calendario y Obligaciones
                </h1>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                {/* COLUMNA 1: Formulario de Registro Manual */}
                <div className="bg-white p-6 rounded-lg shadow-md h-fit">
                    <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                        <FaPlus className="mr-2 text-green-600" /> Registrar Nuevo Vencimiento
                    </h2>
                    <p className="text-sm text-gray-500 mb-4">
                        Consulte su fecha límite según su NIT y regístrela aquí manualmente.
                    </p>

                    <form onSubmit={agregarObligacion} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Impuesto</label>
                            <select
                                name="impuesto"
                                value={nuevaObligacion.impuesto}
                                onChange={handleInputChange}
                                className="w-full border rounded-md p-2 focus:ring-blue-500 focus:border-blue-500"
                            >
                                <option value="IVA">IVA</option>
                                <option value="Retención en la Fuente">Retención en la Fuente</option>
                                <option value="Renta">Renta</option>
                                <option value="ICA">Industria y Comercio (ICA)</option>
                                <option value="ReteICA">ReteICA</option>
                                <option value="Impuesto al Consumo">Impuesto al Consumo</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Periodo (Ej: Ene-Feb 2025)</label>
                            <input
                                type="text"
                                name="periodo"
                                value={nuevaObligacion.periodo}
                                onChange={handleInputChange}
                                placeholder="Descripción del periodo"
                                className="w-full border rounded-md p-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Fecha de Vencimiento</label>
                            <input
                                type="date"
                                name="vencimiento"
                                value={nuevaObligacion.vencimiento}
                                onChange={handleInputChange}
                                className="w-full border rounded-md p-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                        </div>

                        <button type="submit" className="w-full bg-green-600 text-white py-2 rounded-md hover:bg-green-700 flex justify-center items-center font-semibold">
                            <FaSave className="mr-2" /> Guardar Obligación
                        </button>
                    </form>
                </div>

                {/* COLUMNA 2: Tabla de Obligaciones (Ancha) */}
                <div className="lg:col-span-2 bg-white rounded-lg shadow-md overflow-hidden">
                    <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
                        <h2 className="text-lg font-semibold text-gray-800">Mis Obligaciones Tributarias</h2>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-white">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Impuesto / Periodo</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Vencimiento</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acción</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {obligaciones.length === 0 ? (
                                    <tr>
                                        <td colSpan="4" className="px-6 py-8 text-center text-gray-500">
                                            No hay obligaciones registradas. Utilice el formulario para agregar una.
                                        </td>
                                    </tr>
                                ) : (
                                    obligaciones.map((obl) => {
                                        const dias = getDiasRestantes(obl.vencimiento);
                                        return (
                                            <tr key={obl.id} className="hover:bg-gray-50">
                                                <td className="px-6 py-4">
                                                    <div className="text-sm font-medium text-gray-900">{obl.impuesto}</div>
                                                    <div className="text-sm text-gray-500">{obl.periodo}</div>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <div className="text-sm text-gray-900">{obl.vencimiento}</div>
                                                    <div className={`text-xs font-bold ${dias < 0 ? 'text-red-600' : dias < 5 ? 'text-orange-600' : 'text-green-600'}`}>
                                                        {dias < 0 ? `Vencido hace ${Math.abs(dias)} días` : `Faltan ${dias} días`}
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                            ${obl.estado === 'Presentado' ? 'bg-green-100 text-green-800' :
                                                            obl.estado === 'Pendiente' ? 'bg-red-100 text-red-800' :
                                                                'bg-yellow-100 text-yellow-800'}`}>
                                                        {obl.estado}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                    <button
                                                        onClick={() => eliminarObligacion(obl.id)}
                                                        className="text-red-600 hover:text-red-900"
                                                        title="Eliminar"
                                                    >
                                                        <FaTrash />
                                                    </button>
                                                </td>
                                            </tr>
                                        );
                                    })
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

            </div>
        </div>
    );
}
