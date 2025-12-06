"use client";
import React, { useState, useEffect } from 'react';
import { FaSave, FaPlus, FaTrash, FaBook, FaTimes, FaListOl } from 'react-icons/fa';
import { toast } from 'react-toastify';

export default function ParametrosView({ impuesto }) {
    // State for tariffs
    const [tarifas, setTarifas] = useState([
        { id: 1, concepto: 'General', valor: 19, unidad: '%' },
        { id: 2, concepto: 'Especial', valor: 5, unidad: '%' },
    ]);
    const [periodicidad, setPeriodicidad] = useState('Bimestral');

    // State for PUC Mapping
    // We initialize with the standard rows for the form
    const defaultMapping = [
        { r: 27, c: 'Ingresos Brutos', cuentas: '' },
        { r: 28, c: 'Devoluciones en ventas', cuentas: '' },
        { r: 40, c: 'Compras de bienes gravados', cuentas: '' },
        { r: 57, c: 'Impuesto Generado', cuentas: '' },
        { r: 65, c: 'Impuesto Descontable', cuentas: '' },
    ];
    const [mapping, setMapping] = useState(defaultMapping);

    // Modal state
    const [showModal, setShowModal] = useState(false);
    const [newTarifa, setNewTarifa] = useState({ concepto: '', valor: '', unidad: '%' });

    // LOAD from localStorage
    useEffect(() => {
        if (impuesto) {
            try {
                const savedTarifas = localStorage.getItem(`impuestos_tarifas_${impuesto}`);
                const savedPeriod = localStorage.getItem(`impuestos_periodicidad_${impuesto}`);
                const savedMapping = localStorage.getItem(`impuestos_mapping_${impuesto}`);

                if (savedTarifas) setTarifas(JSON.parse(savedTarifas));
                if (savedPeriod) setPeriodicidad(savedPeriod);
                if (savedMapping) setMapping(JSON.parse(savedMapping));

            } catch (error) {
                console.error("Error loading from localStorage:", error);
            }
        }
    }, [impuesto]);

    // Handlers
    const handleDelete = (id) => {
        if (window.confirm('¿Está seguro de eliminar esta tarifa?')) {
            setTarifas(prev => prev.filter(t => t.id !== id));
            toast.success('Tarifa eliminada correctamente');
        }
    };

    const handleAdd = () => {
        if (!newTarifa.concepto || !newTarifa.valor) {
            toast.warning('Complete todos los campos');
            return;
        }
        const nueva = {
            id: Date.now(),
            concepto: newTarifa.concepto,
            valor: parseFloat(newTarifa.valor),
            unidad: newTarifa.unidad
        };
        setTarifas(prev => [...prev, nueva]);
        setShowModal(false);
        setNewTarifa({ concepto: '', valor: '', unidad: '%' });
        toast.success('Tarifa agregada correctamente');
    };

    const handleMappingChange = (index, value) => {
        setMapping(prev => prev.map((row, i) =>
            i === index ? { ...row, cuentas: value } : row
        ));
    };

    const handleSave = () => {
        try {
            localStorage.setItem(`impuestos_tarifas_${impuesto}`, JSON.stringify(tarifas));
            localStorage.setItem(`impuestos_periodicidad_${impuesto}`, periodicidad);
            localStorage.setItem(`impuestos_mapping_${impuesto}`, JSON.stringify(mapping));

            toast.success(`Configuración de ${impuesto} guardada exitosamente.`);
        } catch (error) {
            console.error("Error al guardar:", error);
            toast.error("Error al guardar la configuración.");
        }
    };

    const openManual = () => {
        window.open('/manual?file=capitulo_impuestos_parametros.md', '_blank');
    };

    return (
        <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow-md">
                <div className="flex justify-between items-start mb-6">
                    <div>
                        <h2 className="text-xl font-semibold text-gray-800">Configuración de {impuesto}</h2>
                        <p className="text-gray-600 mt-1">Administre las tarifas, periodicidades y reglas de contabilización.</p>
                    </div>
                    <div className="flex space-x-3">
                        <button
                            onClick={handleSave}
                            className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 flex items-center font-semibold shadow-sm"
                        >
                            <FaSave className="mr-2" /> Guardar
                        </button>
                        <button
                            onClick={openManual}
                            className="text-blue-600 hover:text-blue-800 flex items-center text-sm font-medium"
                        >
                            <FaBook className="mr-2" /> Manual
                        </button>
                    </div>
                </div>

                {/* Subpanel: Tarifas */}
                <div className="border rounded-lg overflow-hidden mb-6">
                    <div className="bg-gray-50 px-4 py-2 border-b flex justify-between items-center">
                        <h3 className="font-medium text-gray-700">Tabla de Tarifas</h3>
                        <button
                            onClick={() => setShowModal(true)}
                            className="text-sm bg-blue-100 text-blue-700 px-3 py-1 rounded hover:bg-blue-200 flex items-center"
                        >
                            <FaPlus className="mr-1" /> Agregar
                        </button>
                    </div>
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-white">
                            <tr>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Concepto</th>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Valor</th>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Unidad</th>
                                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {tarifas.length === 0 ? (
                                <tr>
                                    <td colSpan="4" className="px-4 py-4 text-center text-gray-500 text-sm">No hay tarifas registradas.</td>
                                </tr>
                            ) : (
                                tarifas.map((t) => (
                                    <tr key={t.id}>
                                        <td className="px-4 py-2 text-sm text-gray-900">{t.concepto}</td>
                                        <td className="px-4 py-2 text-sm text-gray-900">{t.valor}</td>
                                        <td className="px-4 py-2 text-sm text-gray-500">{t.unidad}</td>
                                        <td className="px-4 py-2 text-right text-sm">
                                            <button
                                                onClick={() => handleDelete(t.id)}
                                                className="text-red-600 hover:text-red-800"
                                                title="Eliminar"
                                            >
                                                <FaTrash />
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Subpanel: Mapeo de Cuentas (NUEVO) */}
                <div className="border rounded-lg overflow-hidden mb-6">
                    <div className="bg-blue-50 px-4 py-2 border-b flex justify-between items-center">
                        <h3 className="font-medium text-blue-800 flex items-center">
                            <FaListOl className="mr-2" /> Mapeo de Cuentas Contables (PUC)
                        </h3>
                        <span className="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded">Integración Contable</span>
                    </div>
                    <div className="p-4 bg-gray-50 text-sm text-gray-600 mb-0 border-b">
                        Defina qué cuentas del PUC alimentan cada renglón del formulario. Separe las cuentas con comas (ej: 4135, 4140).
                    </div>
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-white">
                            <tr>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase w-16">Renglón</th>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Concepto del Formulario</th>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Cuentas PUC (Separadas por coma)</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {mapping.map((row, idx) => (
                                <tr key={idx}>
                                    <td className="px-4 py-2 text-sm font-bold text-gray-600 text-center">{row.r}</td>
                                    <td className="px-4 py-2 text-sm text-gray-900">{row.c}</td>
                                    <td className="px-4 py-2">
                                        <input
                                            type="text"
                                            value={row.cuentas}
                                            onChange={(e) => handleMappingChange(idx, e.target.value)}
                                            placeholder="Ej: 413505, 413510"
                                            className="w-full border rounded px-2 py-1 focus:ring-blue-500 focus:border-blue-500 text-sm font-mono"
                                        />
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {/* Subpanel: Periodicidad */}
                <div className="border rounded-lg p-4">
                    <h3 className="font-medium text-gray-700 mb-2">Periodicidad</h3>
                    <div className="flex space-x-4">
                        {['Bimestral', 'Cuatrimestral', 'Anual'].map((p) => (
                            <label key={p} className="flex items-center space-x-2 cursor-pointer">
                                <input
                                    type="radio"
                                    name="periodicidad"
                                    checked={periodicidad === p}
                                    onChange={() => setPeriodicidad(p)}
                                    className="text-blue-600 focus:ring-blue-500"
                                />
                                <span className="text-gray-700">{p}</span>
                            </label>
                        ))}
                    </div>
                </div>

                <div className="mt-6 flex justify-end">
                    <button
                        onClick={handleSave}
                        className="bg-green-600 text-white px-6 py-2 rounded-md hover:bg-green-700 flex items-center font-semibold shadow-sm"
                    >
                        <FaSave className="mr-2" /> Guardar Cambios
                    </button>
                </div>
            </div>

            {/* Modal Agregar Tarifa */}
            {showModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 w-96 shadow-xl">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-bold text-gray-800">Nueva Tarifa</h3>
                            <button onClick={() => setShowModal(false)} className="text-gray-500 hover:text-gray-700">
                                <FaTimes />
                            </button>
                        </div>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Concepto</label>
                                <input
                                    type="text"
                                    className="w-full border rounded p-2 focus:ring-blue-500 focus:border-blue-500"
                                    placeholder="Ej: Tarifa General"
                                    value={newTarifa.concepto}
                                    onChange={(e) => setNewTarifa({ ...newTarifa, concepto: e.target.value })}
                                />
                            </div>
                            <div className="flex gap-4">
                                <div className="flex-1">
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Valor</label>
                                    <input
                                        type="number"
                                        className="w-full border rounded p-2 focus:ring-blue-500 focus:border-blue-500"
                                        placeholder="19"
                                        value={newTarifa.valor}
                                        onChange={(e) => setNewTarifa({ ...newTarifa, valor: e.target.value })}
                                    />
                                </div>
                                <div className="w-24">
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Unidad</label>
                                    <select
                                        className="w-full border rounded p-2 focus:ring-blue-500 focus:border-blue-500"
                                        value={newTarifa.unidad}
                                        onChange={(e) => setNewTarifa({ ...newTarifa, unidad: e.target.value })}
                                    >
                                        <option value="%">%</option>
                                        <option value="UVT">UVT</option>
                                        <option value="COP">COP</option>
                                    </select>
                                </div>
                            </div>
                            <button
                                onClick={handleAdd}
                                className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 font-semibold mt-2"
                            >
                                Agregar
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
