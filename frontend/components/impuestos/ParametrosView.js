"use client";
import React, { useState, useEffect } from 'react';
import { FaSave, FaPlus, FaTrash, FaBook, FaTimes, FaListOl, FaHistory } from 'react-icons/fa';
import { toast } from 'react-toastify';

import { apiService } from '../../lib/apiService'; // Ensure this path is correct

export default function ParametrosView({ impuesto }) {
    // State for tariffs (Keep localStorage for tariffs for now as backend model only handles Report Config)
    const [tarifas, setTarifas] = useState([
        { id: 1, concepto: 'General', valor: 19, unidad: '%' },
        { id: 2, concepto: 'Especial', valor: 5, unidad: '%' },
    ]);
    const [periodicidad, setPeriodicidad] = useState('Bimestral');

    // State for PUC Mapping
    // State for PUC Mapping
    const defaultIVA = [
        // INGRESOS
        { isHeader: true, c: 'Ingresos' },
        { r: '27', c: 'Ingresos Operaciones 5%', cuentas: '' },
        { r: '28', c: 'Ingresos Operaciones General (19%)', cuentas: '' },
        { r: '35', c: 'Ingresos Exentos', cuentas: '' },
        { r: '39', c: 'Operaciones excluidas', cuentas: '' },
        { r: '40', c: 'Ingresos No Gravados', cuentas: '' },
        { r: '41', c: 'Total Ingresos Brutos', cuentas: '[27]+[28]+[35]+[39]+[40]' }, // Example Formula
        { r: '42', c: 'Devoluciones en ventas anuladas, rescindidas o resueltas', cuentas: '' },
        { r: '43', c: 'Total Ingresos Netos', cuentas: '[41]-[42]' },

        // COMPRAS
        { isHeader: true, c: 'Compras' },
        { r: '50', c: 'Bienes gravados a la tarifa del 5%', cuentas: '' },
        { r: '51', c: 'Bienes gravados a la tarifa general', cuentas: '' },
        { r: '52', c: 'Servicios gravados a la tarifa del 5%', cuentas: '' },
        { r: '53', c: 'Servicios gravados a la tarifa general', cuentas: '' },
        { r: '54', c: 'Bienes y servicios excluidos, exentos y no gravados', cuentas: '' },
        { r: '55', c: 'Total compras e importaciones brutas', cuentas: '[50]+[51]+[52]+[53]+[54]' },
        { r: '56', c: 'Devoluciones en compras anuladas, rescindidas o resueltas', cuentas: '' },
        { r: '57', c: 'Total compras netas', cuentas: '[55]-[56]' },

        // IMPUESTO GENERADO
        { isHeader: true, c: 'Impuesto Generado' },
        { r: '58', c: 'IVA Generado 5%', cuentas: '' },
        { r: '59', c: 'IVA Generado 19%', cuentas: '' },
        { r: '66', c: 'IVA recuperado en devoluciones en compras', cuentas: '' },
        { r: '67', c: 'Total impuesto generado', cuentas: '[58]+[59]+[66]' },

        // IMPUESTO DESCONTABLE
        { isHeader: true, c: 'Impuesto Descontable' },
        { r: '71', c: 'IVA Descontable Compras 5%', cuentas: '' },
        { r: '72', c: 'IVA Descontable Compras 19%', cuentas: '' },
        { r: '74', c: 'Servicios gravados a la tarifa del 5%', cuentas: '' },
        { r: '75', c: 'Servicios gravados a la tarifa general', cuentas: '' },
        { r: '77', c: 'Total impuesto pagado o facturado', cuentas: '[71]+[72]+[74]+[75]' },
        { r: '78', c: 'IVA Retenido por servicios no domiciliados', cuentas: '' },
        { r: '79', c: 'IVA por devoluciones en ventas', cuentas: '' },
        { r: '80', c: 'Ajuste impuestos descontables (Pérdidas/Hurto)', cuentas: '' },
        { r: '81', c: 'Total impuestos descontables', cuentas: '[77]+[78]+[79]-[80]' },

        // CONTROL DE SALDOS
        { isHeader: true, c: 'Control de Saldos' },
        { r: '82', c: 'Saldo a pagar', cuentas: 'max(0, [67]-[81])' }, // Python syntax for backend eval
        { r: '83', c: 'Saldo a favor', cuentas: 'max(0, [81]-[67])' },
        { r: '85', c: 'Retenciones por IVA practicadas', cuentas: '' },
        { r: '86', c: 'Saldo a pagar final', cuentas: '[82]-[85]' },
    ];

    const defaultRete = [
        { r: '27', c: 'Rentas de trabajo (Salarios)', cuentas: '' },
        { r: '29', c: 'Compras', cuentas: '' },
        { r: '30', c: 'Honorarios', cuentas: '' },
        { r: '31', c: 'Servicios', cuentas: '' },
        { r: '32', c: 'Arrendamientos', cuentas: '' },
        { r: '40', c: 'Total Retenciones', cuentas: '' },
    ];

    const defaultRenta = [
        { r: '36', c: 'Efectivo y equivalentes', cuentas: '11' },
        { r: '37', c: 'Inversiones', cuentas: '12' },
        { r: '38', c: 'Cuentas por cobrar', cuentas: '13' },
        { r: '39', c: 'Inventarios', cuentas: '14' },
        { r: '40', c: 'Activos Intangibles', cuentas: '16' },
        { r: '42', c: 'Propiedades, planta y equipo', cuentas: '15' },
        { r: '43', c: 'Otros activos', cuentas: '17, 18, 19' },
        { r: '45', c: 'Pasivos', cuentas: '2' },
        { r: '47', c: 'Ingresos Brutos Act. Ordinarias', cuentas: '41' },
        { r: '48', c: 'Ingresos Financieros', cuentas: '4210' },
        { r: '51', c: 'Otros Ingresos', cuentas: '42' },
        { r: '62', c: 'Costo de Ventas', cuentas: '61, 71' },
        { r: '63', c: 'Gastos de Administración', cuentas: '51' },
        { r: '64', c: 'Gastos de Distribución y Ventas', cuentas: '52' },
        { r: '65', c: 'Gastos Financieros', cuentas: '53' },
    ];

    const [mapping, setMapping] = useState([]);

    // Modal state
    const [showModal, setShowModal] = useState(false);
    const [newTarifa, setNewTarifa] = useState({ concepto: '', valor: '', unidad: '%' });

    // LOAD from Backend
    useEffect(() => {
        if (impuesto) {
            // Set initial defaults based on type to avoid flashing wrong rows
            // If backend has data, it will overwrite this.
            if (impuesto.toLowerCase() === 'iva') {
                setMapping(defaultIVA);
            } else if (impuesto.toLowerCase() === 'retefuente') {
                setMapping(defaultRete);
            } else if (impuesto.toLowerCase() === 'renta') {
                setMapping(defaultRenta);
            } else {
                setMapping([]);
            }

            // Load LocalStorage for Tarifas/Period
            const savedTarifas = localStorage.getItem(`impuestos_tarifas_${impuesto}`);
            const savedPeriod = localStorage.getItem(`impuestos_periodicidad_${impuesto}`);
            if (savedTarifas) setTarifas(JSON.parse(savedTarifas));
            if (savedPeriod) setPeriodicidad(savedPeriod);

            // Load Configuration from Backend
            apiService.get(`/impuestos/configuracion/${impuesto.toUpperCase()}`)
                .then(res => {
                    if (res.data && res.data.length > 0) {
                        // Backend is authority. Use its data.
                        const backendRows = res.data.map(b => ({
                            r: b.renglon,
                            c: b.concepto,
                            cuentas: b.cuentas_ids ? b.cuentas_ids.join(', ') : '',
                            isHeader: b.is_header || false
                        }));

                        // Optional: Sort by Renglon number if needed
                        backendRows.sort((a, b) => parseInt(a.r) - parseInt(b.r));

                        setMapping(backendRows);
                    }
                })
                .catch(err => console.error("Error loading config", err));
        }
    }, [impuesto]);

    // Handlers
    const handleDelete = (id) => {
        if (window.confirm('¿Está seguro de eliminar esta tarifa?')) {
            setTarifas(prev => prev.filter(t => t.id !== id));
            toast.success('Tarifa eliminada localmente');
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
        toast.success('Tarifa agregada localmente');
    };

    const handleMappingChange = (index, value) => {
        setMapping(prev => prev.map((row, i) =>
            i === index ? { ...row, cuentas: value } : row
        ));
    };

    const handleSave = async () => {
        try {
            // Save Local (Tarifas/Period)
            localStorage.setItem(`impuestos_tarifas_${impuesto}`, JSON.stringify(tarifas));
            localStorage.setItem(`impuestos_periodicidad_${impuesto}`, periodicidad);

            // Save Backend (Mapping)
            const payload = {
                configs: mapping.map(m => {
                    const cuentasStr = m.cuentas ? m.cuentas.trim() : '';
                    let ids = [];
                    // Detect Formula: Contains brackets [] or parenthesis ()
                    // If it's a formula, do NOT split by comma (because max(0, ...) uses comma)
                    if (cuentasStr && (cuentasStr.includes('[') || cuentasStr.includes('('))) {
                        ids = [cuentasStr];
                    } else {
                        ids = cuentasStr ? cuentasStr.split(',').map(s => s.trim()).filter(s => s !== '') : [];
                    }

                    return {
                        renglon: m.r || '',
                        concepto: m.c,
                        cuentas_ids: ids,
                        is_header: m.isHeader || false
                    };
                })
            };

            await apiService.post(`/impuestos/configuracion/${impuesto.toUpperCase()}`, payload);

            toast.success(`Configuración de ${impuesto} guardada exitosamente.`);
        } catch (error) {
            console.error("Error al guardar:", error);
            toast.error("Error al guardar la configuración.");
        }
    };

    const openManual = () => {
        window.open('/manual?file=capitulo_impuestos_parametros.md', '_blank');
    };

    const handleRestoreDefaults = () => {
        if (window.confirm("¿Está seguro? Esto sobrescribirá la configuración actual con la sugerida por el sistema.")) {
            if (impuesto.toLowerCase() === 'iva') {
                setMapping(defaultIVA);
            } else if (impuesto.toLowerCase() === 'retefuente') {
                setMapping(defaultRete);
            } else if (impuesto.toLowerCase() === 'renta') {
                setMapping(defaultRenta);
            } else {
                setMapping([]);
            }
            toast.info("Configuración restaurada. Recuerde Guardar.");
        }
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
                        <button
                            onClick={handleRestoreDefaults}
                            className="text-gray-600 hover:text-gray-800 flex items-center text-sm font-medium bg-gray-100 px-3 py-2 rounded-md ml-2"
                            title="Cargar configuración sugerida"
                        >
                            <FaHistory className="mr-2" /> Restaurar
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
                            {mapping.map((row, idx) => {
                                if (row.isHeader) {
                                    return (
                                        <tr key={idx} className="bg-gray-100">
                                            <td colSpan="3" className="px-4 py-2 font-bold text-gray-800 uppercase text-xs tracking-wider">
                                                {row.c}
                                            </td>
                                        </tr>
                                    );
                                }
                                return (
                                    <tr key={idx}>
                                        <td className="px-4 py-2 text-sm font-bold text-gray-600 text-center">{row.r}</td>
                                        <td className="px-4 py-2 text-sm text-gray-900">{row.c}</td>
                                        <td className="px-4 py-2">
                                            <input
                                                type="text"
                                                value={row.cuentas}
                                                onChange={(e) => handleMappingChange(idx, e.target.value)}
                                                placeholder="Ej: 4135 o Fórmula: [27]+[28]"
                                                className="w-full border rounded px-2 py-1 focus:ring-blue-500 focus:border-blue-500 text-sm font-mono"
                                            />
                                        </td>
                                    </tr>
                                );
                            })}
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
