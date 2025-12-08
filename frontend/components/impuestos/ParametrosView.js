"use client";
import React, { useState, useEffect } from 'react';
import { FaSave, FaPlus, FaTrash, FaBook, FaTimes, FaListOl, FaHistory } from 'react-icons/fa';
import { toast } from 'react-toastify';

import { apiService } from '../../lib/apiService';

export default function ParametrosView({ impuesto }) {
    // State for tariffs
    const [tarifas, setTarifas] = useState([
        { id: 1, concepto: 'General', valor: 19, unidad: '%' },
        { id: 2, concepto: 'Especial', valor: 5, unidad: '%' },
    ]);
    const [periodicidad, setPeriodicidad] = useState('Bimestral');

    // -------------------------------------------------------------------------
    // DEFAULT CONFIGURATIONS
    // -------------------------------------------------------------------------

    // IVA
    const defaultIVA = [
        { isHeader: true, c: 'Ingresos' },
        { r: '27', c: 'Ingresos Operaciones 5%', cuentas: '' },
        { r: '28', c: 'Ingresos Operaciones General (19%)', cuentas: '' },
        { r: '35', c: 'Ingresos Exentos', cuentas: '' },
        { r: '39', c: 'Operaciones excluidas', cuentas: '' },
        { r: '40', c: 'Ingresos No Gravados', cuentas: '' },
        { r: '41', c: 'Total Ingresos Brutos', cuentas: '[27]+[28]+[35]+[39]+[40]' },
        { r: '42', c: 'Devoluciones en ventas anuladas, rescindidas o resueltas', cuentas: '' },
        { r: '43', c: 'Total Ingresos Netos', cuentas: '[41]-[42]' },

        { isHeader: true, c: 'Compras' },
        { r: '50', c: 'Bienes gravados a la tarifa del 5%', cuentas: '' },
        { r: '51', c: 'Bienes gravados a la tarifa general', cuentas: '' },
        { r: '52', c: 'Servicios gravados a la tarifa del 5%', cuentas: '' },
        { r: '53', c: 'Servicios gravados a la tarifa general', cuentas: '' },
        { r: '54', c: 'Bienes y servicios excluidos, exentos y no gravados', cuentas: '' },
        { r: '55', c: 'Total compras e importaciones brutas', cuentas: '[50]+[51]+[52]+[53]+[54]' },
        { r: '56', c: 'Devoluciones en compras anuladas, rescindidas o resueltas', cuentas: '' },
        { r: '57', c: 'Total compras netas', cuentas: '[55]-[56]' },

        { isHeader: true, c: 'Impuesto Generado' },
        { r: '58', c: 'IVA Generado 5%', cuentas: '' },
        { r: '59', c: 'IVA Generado 19%', cuentas: '' },
        { r: '66', c: 'IVA recuperado en devoluciones en compras', cuentas: '' },
        { r: '67', c: 'Total impuesto generado', cuentas: '[58]+[59]+[66]' },

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

        { isHeader: true, c: 'Control de Saldos' },
        { r: '82', c: 'Saldo a pagar', cuentas: 'max(0, [67]-[81])' },
        { r: '83', c: 'Saldo a favor', cuentas: 'max(0, [81]-[67])' },
        { r: '85', c: 'Retenciones por IVA practicadas', cuentas: '' },
        { r: '86', c: 'Saldo a pagar final', cuentas: '[82]-[85]' },
    ];

    // RETEFUENTE (Form 350)
    const defaultRete = [
        { isHeader: true, c: 'Rentas de Trabajo y Pensiones' },
        { r: '27', c: 'Rentas de trabajo (Salarios)', cuentas: '236505' },
        { r: '28', c: 'Contribuciones a E.P.S.', cuentas: '' },
        { r: '29', c: 'Rentas de pensiones', cuentas: '' },

        { isHeader: true, c: 'Retenciones Renta (Personas Jurídicas)' },
        { r: '30', c: 'Honorarios (Personas Jurídicas)', cuentas: '236515' },
        { r: '31', c: 'Comisiones (Personas Jurídicas)', cuentas: '' },
        { r: '32', c: 'Servicios (Personas Jurídicas)', cuentas: '236525' },
        { r: '33', c: 'Arrendamientos (Personas Jurídicas)', cuentas: '236530' },
        { r: '34', c: 'Rendimientos Financieros (PJ)', cuentas: '' },
        { r: '35', c: 'Regalías y Propiedad Intelectual (PJ)', cuentas: '' },
        { r: '36', c: 'Dividendos y Participaciones (PJ)', cuentas: '' },

        { isHeader: true, c: 'Retenciones Renta (Personas Naturales)' },
        { r: '40', c: 'Honorarios (Personas Naturales)', cuentas: '' },
        { r: '41', c: 'Comisiones (Personas Naturales)', cuentas: '' },
        { r: '42', c: 'Servicios (Personas Naturales)', cuentas: '' },
        { r: '43', c: 'Arrendamientos (Personas Naturales)', cuentas: '' },
        { r: '44', c: 'Rendimientos Financieros (PN)', cuentas: '' },
        { r: '45', c: 'Enajenación Activos Fijos (PN)', cuentas: '' },
        { r: '46', c: 'Loterías, rifas y apuestas', cuentas: '' },

        { isHeader: true, c: 'Compras y Otros' },
        { r: '50', c: 'Compras General', cuentas: '236540' },
        { r: '51', c: 'Compras Hidrocarburos/Carbón (NUEVO)', cuentas: '' },
        { r: '52', c: 'Pagos al Exterior (General)', cuentas: '' },
        { r: '53', c: 'Pagos al Exterior (Con PES)', cuentas: '' },
        { r: '54', c: 'Otros pagos sujetos a retención', cuentas: '' },

        { isHeader: true, c: 'IVA y Timbre Nacional' },
        { r: '60', c: 'Retenciones a título de IVA', cuentas: '2367' },
        { r: '61', c: 'Retenciones Impuesto de Timbre', cuentas: '' },

        { isHeader: true, c: 'Autorretenciones' },
        { r: '70', c: 'Autorretención Ventas (General)', cuentas: '' },
        { r: '71', c: 'Autorretención Hidrocarburos/Minería', cuentas: '' },
        { r: '72', c: 'Otras Autorretenciones', cuentas: '' },

        { isHeader: true, c: 'Total' },
        { r: '99', c: 'Total Retenciones', cuentas: '[27]+[28]+[29]+[30]+[31]+[32]+[33]+[34]+[35]+[36]+[40]+[41]+[42]+[43]+[44]+[45]+[46]+[50]+[51]+[52]+[53]+[54]+[60]+[61]+[70]+[71]+[72]' }
    ];

    // RENTA (Form 110 - Personas Jurídicas)
    const defaultRenta110 = [
        { isHeader: true, c: 'Patrimonio (Form 110)' },
        { r: '36', c: 'Efectivo y equivalentes', cuentas: '11' },
        { r: '37', c: 'Inversiones', cuentas: '12' },
        { r: '38', c: 'Cuentas por cobrar', cuentas: '13' },
        { r: '39', c: 'Inventarios', cuentas: '14' },
        { r: '40', c: 'Activos Intangibles', cuentas: '16' },
        { r: '41', c: 'Activos Biológicos', cuentas: '' },
        { r: '42', c: 'Propiedades, planta y equipo', cuentas: '15' },
        { r: '43', c: 'Otros activos', cuentas: '17, 18, 19' },
        { r: '44', c: 'Total Patrimonio Bruto', cuentas: '[36]+[37]+[38]+[39]+[40]+[41]+[42]+[43]' },
        { r: '45', c: 'Pasivos', cuentas: '2' },
        { r: '46', c: 'Total Patrimonio Líquido', cuentas: '[44]-[45]' },

        { isHeader: true, c: 'Ingresos' },
        { r: '47', c: 'Ingresos Brutos Act. Ordinarias', cuentas: '41' },
        { r: '48', c: 'Ingresos Financieros', cuentas: '4210' },
        { r: '49', c: 'Dividendos y participaciones', cuentas: '4215' },
        { r: '50', c: 'Otros Ingresos', cuentas: '42' },
        { r: '51', c: 'Total Ingresos Brutos', cuentas: '[47]+[48]+[49]+[50]' },
        { r: '52', c: 'Devoluciones, rebajas y descuentos', cuentas: '' },
        { r: '53', c: 'Ingresos Netos', cuentas: '[51]-[52]' },

        { isHeader: true, c: 'Costos y Deducciones' },
        { r: '54', c: 'Costo de Ventas', cuentas: '61, 71' },
        { r: '55', c: 'Gastos de Administración', cuentas: '51' },
        { r: '56', c: 'Gastos de Distribución y Ventas', cuentas: '52' },
        { r: '57', c: 'Gastos Financieros', cuentas: '53' },
        { r: '58', c: 'Otros Gastos', cuentas: '' },
        { r: '59', c: 'Total Costos y Gastos', cuentas: '[54]+[55]+[56]+[57]+[58]' },

        { isHeader: true, c: 'Renta' },
        { r: '64', c: 'Renta Líquida Ordinaria del Ejercicio', cuentas: 'max(0, [53]-[59])' },
        { r: '65', c: 'Pérdida Líquida del Ejercicio', cuentas: 'max(0, [59]-[53])' },

        { isHeader: true, c: 'Ganancias Ocasionales' },
        { r: '80', c: 'Ingresos por ganancias ocasionales', cuentas: '4240' },
        { r: '81', c: 'Costos por ganancias ocasionales', cuentas: '' },
        { r: '82', c: 'Ganancias ocasionales netas', cuentas: 'max(0, [80]-[81])' },

        { isHeader: true, c: 'Liquidación Privada' },
        { r: '96', c: 'Impuesto sobre la renta líquida', cuentas: '' },
        { r: '104', c: 'Total Impuesto a Cargo', cuentas: '' },
        { r: '110', c: 'Total Saldo a Pagar', cuentas: '' },
    ];

    // RENTA (Form 210 - Personas Naturales)
    const defaultRenta210 = [
        { isHeader: true, c: 'Patrimonio (Form 210)' },
        { r: '28', c: 'Total Patrimonio Bruto', cuentas: '1' },
        { r: '29', c: 'Deudas', cuentas: '2' },
        { r: '30', c: 'Total Patrimonio Líquido', cuentas: '[28]-[29]' },

        { isHeader: true, c: 'Rentas de Trabajo' },
        { r: '32', c: 'Ingresos brutos rentas de trabajo', cuentas: '42' },
        { r: '33', c: 'Ingresos no constitutivos de renta', cuentas: '' },
        { r: '34', c: 'Costos y deducciones procedentes', cuentas: '51' },
        { r: '35', c: 'Renta líquida ordinaria trabajo', cuentas: '[32]-[33]-[34]' },

        { isHeader: true, c: 'Rentas de Capital' },
        { r: '50', c: 'Ingresos brutos por intereses y rendimientos fin.', cuentas: '4210' },
        { r: '51', c: 'Otros ingresos rentas de capital', cuentas: '' },
        { r: '52', c: 'Ingresos no constitutivos de renta (Capital)', cuentas: '' },
        { r: '53', c: 'Costos y gastos procedentes (Capital)', cuentas: '53' },
        { r: '54', c: 'Renta líquida ordinaria capital', cuentas: '[50]+[51]-[52]-[53]' },

        { isHeader: true, c: 'Rentas No Laborales' },
        { r: '70', c: 'Ingresos brutos rentas no laborales', cuentas: '' },
        { r: '71', c: 'Costos y gastos procedentes (No Laborales)', cuentas: '' },

        { isHeader: true, c: 'Cédula de Pensiones' },
        { r: '90', c: 'Ingresos brutos por pensiones', cuentas: '' },
        { r: '91', c: 'Ingresos no constitutivos de renta (Pensiones)', cuentas: '' },

        { isHeader: true, c: 'Dividendos y Participaciones' },
        { r: '100', c: 'Dividendos y participaciones 2017 y siguientes', cuentas: '4215' },

        { isHeader: true, c: 'Ganancias Ocasionales' },
        { r: '110', c: 'Ingresos por ganancias ocasionales', cuentas: '4240' },
        { r: '111', c: 'Costos por ganancias ocasionales', cuentas: '' },

        { isHeader: true, c: 'Liquidación Privada' },
        { r: '120', c: 'Impuesto sobre la renta líquida', cuentas: '' },
        { r: '130', c: 'Total Saldo a Pagar', cuentas: '' },
        { r: '131', c: 'Total Saldo a Favor', cuentas: '' },
    ];

    // State for Config Logic
    const [mapping, setMapping] = useState([]);
    const [templateRenta, setTemplateRenta] = useState('210'); // '110' or '210'
    const [showModal, setShowModal] = useState(false);
    const [newTarifa, setNewTarifa] = useState({ concepto: '', valor: '', unidad: '%' });

    // -------------------------------------------------------------------------
    // EFFECTS
    // -------------------------------------------------------------------------
    useEffect(() => {
        if (impuesto) {
            // Set defaults initially to avoid empty tables
            let initialMap = [];
            if (impuesto.toLowerCase() === 'iva') initialMap = defaultIVA;
            else if (impuesto.toLowerCase() === 'retefuente') initialMap = defaultRete;
            else if (impuesto.toLowerCase() === 'renta') initialMap = defaultRenta210;

            setMapping(initialMap);

            // Load LocalStorage for Tarifas/Period
            const savedTarifas = localStorage.getItem(`impuestos_tarifas_${impuesto}`);
            const savedPeriod = localStorage.getItem(`impuestos_periodicidad_${impuesto}`);
            if (savedTarifas) setTarifas(JSON.parse(savedTarifas));
            if (savedPeriod) setPeriodicidad(savedPeriod);

            // Load Configuration from Backend
            apiService.get(`/impuestos/configuracion/${impuesto.toUpperCase()}`)
                .then(res => {
                    if (res.data && res.data.length > 0) {
                        const backendRows = res.data.map(b => ({
                            r: b.renglon,
                            c: b.concepto,
                            cuentas: b.cuentas_ids ? b.cuentas_ids.join(', ') : '',
                            isHeader: b.is_header || false
                        }));

                        // Sort by Renglon number if needed
                        backendRows.sort((a, b) => parseInt(a.r) - parseInt(b.r));
                        setMapping(backendRows);

                        // Heuristic detection: 
                        // If it has 'Rentas de Trabajo' -> 210 PN
                        // If it has 'Pasivos' directly after Patrimonio Bruto or specific 110 fields -> 110 PJ
                        if (impuesto.toLowerCase() === 'renta') {
                            const hasCedulas = backendRows.some(r => r.c && r.c.includes('Rentras de Trabajo') || r.c.includes('Cedula'));
                            const has110Specific = backendRows.some(r => r.c && r.c.includes('Gastos de Distribución'));
                            if (has110Specific && !hasCedulas) {
                                setTemplateRenta('110');
                            } else {
                                setTemplateRenta('210');
                            }
                        }
                    }
                })
                .catch(err => console.error("Error loading config", err));
        }
    }, [impuesto]);

    // -------------------------------------------------------------------------
    // HANDLERS
    // -------------------------------------------------------------------------
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

    const handleTemplateChange = (e) => {
        setTemplateRenta(e.target.value);
        toast.info("Plantilla cambiada. Presione 'Restaurar' para cargar la estructura.");
    };

    const handleRestoreDefaults = () => {
        if (window.confirm(`¿Está seguro? Esto sobrescribirá la configuración con la plantilla actual (${impuesto === 'Renta' ? templateRenta : 'Default'}).`)) {
            if (impuesto.toLowerCase() === 'iva') setMapping(defaultIVA);
            else if (impuesto.toLowerCase() === 'retefuente') setMapping(defaultRete);
            else if (impuesto.toLowerCase() === 'renta') {
                if (templateRenta === '110') setMapping(defaultRenta110);
                else setMapping(defaultRenta210);
            }
            toast.info("Configuración restaurada. Recuerde Guardar.");
        }
    };

    // -------------------------------------------------------------------------
    // RENDER
    // -------------------------------------------------------------------------
    return (
        <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow-md">

                {/* HEADERS & ACTIONS */}
                <div className="flex justify-between items-start mb-6">
                    <div>
                        <h2 className="text-xl font-semibold text-gray-800">Configuración de {impuesto}</h2>
                        <p className="text-gray-600 mt-1">Administre las tarifas, periodicidades y reglas de contabilización.</p>

                        {/* TEMPLATE SELECTOR (ONLY RENTA) */}
                        {impuesto.toLowerCase() === 'renta' && (
                            <div className="mt-4 flex items-center space-x-2 bg-yellow-50 p-2 rounded border border-yellow-200 w-fit">
                                <span className="text-sm font-semibold text-yellow-800">Plantilla de Formulario:</span>
                                <select
                                    value={templateRenta}
                                    onChange={handleTemplateChange}
                                    className="text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 cursor-pointer"
                                >
                                    <option value="210">Formulario 210 (Personas Naturales)</option>
                                    <option value="110">Formulario 110 (Personas Jurídicas)</option>
                                </select>
                            </div>
                        )}
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

                {/* TARIFAS PANEL */}
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

                {/* MAPEO CUENTAS PANEL */}
                <div className="border rounded-lg overflow-hidden mb-6">
                    <div className="bg-blue-50 px-4 py-2 border-b flex justify-between items-center">
                        <h3 className="font-medium text-blue-800 flex items-center">
                            <FaListOl className="mr-2" /> Mapeo de Cuentas Contables (PUC)
                        </h3>
                        <span className="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded">Integración Contable</span>
                    </div>
                    <div className="p-4 bg-gray-50 text-sm text-gray-600 mb-0 border-b">
                        Defina qué cuentas del PUC alimentan cada renglón del formulario. Separe las cuentas con comas (ej: 4135, 4140) o use fórmulas (ej: [27]+[28]).
                    </div>
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-white">
                            <tr>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase w-16">Renglón</th>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Concepto del Formulario</th>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Cuentas PUC / Fórmula</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {mapping.map((row, idx) => {
                                if (row.isHeader) {
                                    return (
                                        <tr key={idx} className="bg-gray-100">
                                            <td colSpan="3" className="px-4 py-3 font-bold text-gray-800 uppercase text-xs tracking-wider border-t border-b border-gray-200">
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
                                                placeholder="Ej: 4135 o [27]+[28]"
                                                className="w-full border rounded px-2 py-1 focus:ring-blue-500 focus:border-blue-500 text-sm font-mono"
                                            />
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>

                {/* PERIODICIDAD PANEL */}
                <div className="border rounded-lg p-4">
                    <h3 className="font-medium text-gray-700 mb-2">Periodicidad</h3>
                    <div className="flex space-x-4">
                        {['Mensual', 'Bimestral', 'Cuatrimestral', 'Anual'].map((p) => (
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

            {/* MODAL - AGREGAR TARIFA */}
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
