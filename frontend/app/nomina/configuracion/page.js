"use client";
import React, { useState, useEffect } from 'react';
import { getConfig, saveConfig } from '../../../lib/nominaService';
import { getPlanCuentasFlat } from '../../../lib/planCuentasService';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { FaCog, FaSave } from 'react-icons/fa';

// ... (imports)
import { apiService } from '../../../lib/apiService'; // Ensure apiService is imported

export default function NominaConfiguracion() {
    const [cuentas, setCuentas] = useState([]);
    const [tiposDoc, setTiposDoc] = useState([]); // Nuevo estado
    const [config, setConfig] = useState({
        tipo_documento_id: '', // Nuevo campo
        cuenta_sueldo_id: '',
        cuenta_auxilio_transporte_id: '',
        cuenta_horas_extras_id: '',
        cuenta_comisiones_id: '',
        cuenta_salarios_por_pagar_id: '',
        cuenta_aporte_salud_id: '',
        cuenta_aporte_pension_id: '',
        cuenta_fondo_solidaridad_id: ''
    });
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const load = async () => {
            try {
                toast.info("Cargando cuentas contables...", { autoClose: 2000 });
                // Cargar TODAS las cuentas (sin filtrar por movimiento)
                const resCuentas = await getPlanCuentasFlat();

                // Cargar Tipos de Documento
                try {
                    const resTipos = await apiService.get('/tipos-documento'); // Verificar ruta
                    setTiposDoc(resTipos.data || []);
                } catch (e) {
                    console.error("Error cargando tipos documento", e);
                }

                // ... (existing logic for accounts)
                const dataArray = Array.isArray(resCuentas.data) ? resCuentas.data : [];
                setCuentas(dataArray);

                // Cargar config actual
                const resConfig = await getConfig();
                if (resConfig) {
                    // Mapear nulls a string vacÃo para inputs
                    const mapped = {};
                    Object.keys(resConfig).forEach(k => mapped[k] = resConfig[k] || '');
                    setConfig(mapped);
                }
            } catch (err) {
                toast.error("Error cargando datos iniciales");
            }
        };
        load();
    }, []);

    const handleChange = (e) => {
        setConfig({ ...config, [e.target.name]: e.target.value });
    };

    const handleSave = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            // Convertir vacíos a null
            const payload = {};
            Object.keys(config).forEach(k => payload[k] = config[k] === '' ? null : parseInt(config[k]));

            await saveConfig(payload);
            toast.success("Configuración Contable Guardada");
        } catch (err) {
            toast.error("Error al guardar configuración");
        } finally {
            setLoading(false);
        }
    };

    // Render helper
    const renderSelect = (label, name, help) => (
        // ... (same as before)
        <div className="mb-4">
            <label className="block text-sm font-bold text-gray-700 mb-1">{label}</label>
            <select name={name} value={config[name]} onChange={handleChange}
                className="w-full border p-2 rounded focus:ring-2 focus:ring-blue-500 bg-white">
                <option value="">-- Seleccionar Cuenta PUC --</option>
                {cuentas.map(cta => (
                    <option key={cta.id} value={cta.id}>
                        {cta.codigo} - {cta.nombre}
                    </option>
                ))}
            </select>
            {help && <p className="text-xs text-gray-400 mt-1">{help}</p>}
        </div>
    );

    return (
        <div className="p-8 max-w-4xl mx-auto">
            <ToastContainer />
            <h1 className="text-2xl font-light text-gray-800 mb-6 flex items-center border-b pb-4">
                <FaCog className="mr-3 text-gray-500" /> Configuración Contable de Nómina
            </h1>

            <form onSubmit={handleSave} className="space-y-8">

                {/* CONFIGURACIÓN GENERAL */}
                <div className="bg-white p-6 rounded shadow border-l-4 border-gray-500">
                    <h3 className="text-lg font-bold text-gray-800 mb-4">Parámetros Generales</h3>
                    <div>
                        <label className="block text-sm font-bold text-gray-700 mb-1">Tipo de Documento (Contabilización)</label>
                        <select name="tipo_documento_id" value={config.tipo_documento_id} onChange={handleChange}
                            className="w-full border p-2 rounded focus:ring-2 focus:ring-blue-500 bg-white">
                            <option value="">-- Seleccionar Tipo de Documento --</option>
                            {tiposDoc.map(td => (
                                <option key={td.id} value={td.id}>
                                    {td.codigo} - {td.nombre}
                                </option>
                            ))}
                        </select>
                        <p className="text-xs text-gray-400 mt-1">Este tipo de documento se usará para generar el comprobante contable.</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {/* DEVENGADOS (GASTOS) */}
                    <div className="bg-white p-6 rounded shadow border-l-4 border-blue-500">
                        <h3 className="text-lg font-bold text-blue-800 mb-4">Cuentas de Gasto (Débito)</h3>
                        {renderSelect("Sueldos (Salario Base)", "cuenta_sueldo_id", "Clase 51 o 52. Ej: 510506")}
                        {renderSelect("Auxilio de Transporte", "cuenta_auxilio_transporte_id", "Clase 51 o 52. Ej: 510527")}
                        {renderSelect("Horas Extras y Recargos", "cuenta_horas_extras_id", "Clase 51 o 52. Ej: 510555")}
                        {renderSelect("Comisiones", "cuenta_comisiones_id", "Clase 51 o 52. Ej: 510518")}
                    </div>

                    {/* DEDUCCIONES / PASIVOS */}
                    <div className="bg-white p-6 rounded shadow border-l-4 border-red-500">
                        <h3 className="text-lg font-bold text-red-800 mb-4">Cuentas de Pasivo (Crédito)</h3>
                        {renderSelect("Saldos por Pagar (Neto)", "cuenta_salarios_por_pagar_id", "Cuenta del empleado. Ej: 250501")}
                        {renderSelect("Aporte Salud (Total)", "cuenta_aporte_salud_id", "Pasivo EPS. Ej: 237005")}
                        {renderSelect("Aporte Pensión (Total)", "cuenta_aporte_pension_id", "Pasivo Fondo Pensiones. Ej: 238030")}
                        {renderSelect("Fondo Solidaridad Pensional", "cuenta_fondo_solidaridad_id", "Pasivo FSP. Ej: 238030")}
                    </div>
                </div>

                <div className="md:col-span-2">
                    <button type="submit" disabled={loading}
                        className="bg-gray-800 text-white font-bold py-3 px-8 rounded shadow hover:bg-black transition w-full flex justify-center items-center">
                        <FaSave className="mr-2" />
                        {loading ? "Guardando..." : "Guardar Mapeo Contable"}
                    </button>
                    <p className="text-center text-xs text-gray-500 mt-4">
                        Estos códigos PUC se usarán para generar automáticamente el comprobante contable al aprobar la nómina.
                    </p>
                </div>
            </form>
        </div>
    );
}
