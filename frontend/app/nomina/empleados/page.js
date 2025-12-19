"use client";
import React, { useState, useEffect } from 'react';
import { getEmpleados, createEmpleado, updateEmpleado, getTiposNomina, downloadEmpleadosPdf } from '../../../lib/nominaService';
import { getTerceros } from '../../../lib/terceroService';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { FaUserPlus, FaSearch, FaEdit, FaCheck, FaTimes, FaPrint, FaFilter, FaFilePdf } from 'react-icons/fa';

export default function EmpleadosPage() {
    const [empleados, setEmpleados] = useState([]);
    const [tiposNomina, setTiposNomina] = useState([]);
    const [loading, setLoading] = useState(false);
    const [showForm, setShowForm] = useState(false);
    const [editingId, setEditingId] = useState(null);

    // Filter State
    const [filterTipo, setFilterTipo] = useState(''); // '' = Todos
    const [textFilter, setTextFilter] = useState(''); // Text search client side

    // Form State
    const [formData, setFormData] = useState({
        nombres: '', apellidos: '', numero_documento: '',
        salario_base: '', fecha_ingreso: '', tiene_auxilio: true,
        tercero_id: null, tipo_nomina_id: ''
    });

    // Search State (Tercero)
    const [searchTerm, setSearchTerm] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [searching, setSearching] = useState(false);

    // Initial Load
    useEffect(() => {
        loadCatalogs();
    }, []);

    // Load employees when filters change
    useEffect(() => {
        loadEmpleados();
    }, [filterTipo]);

    const loadCatalogs = async () => {
        try {
            const tipos = await getTiposNomina();
            setTiposNomina(tipos);
        } catch (error) {
            console.error("Error loading catalogs", error);
        }
    };

    const loadEmpleados = async () => {
        setLoading(true);
        try {
            const params = {};
            if (filterTipo) params.tipo_nomina_id = filterTipo;

            // getEmpleados accepts params (updated in routes previously? YES, routes: Optional[int] = None)
            // But wait, does nominaService pass params?
            // Let's check getEmpleados in service.
            // ... Ah, getEmpleados logic might need update if it doesn't take params yet ...
            // Checking route: @router.get("/empleados") def get_empleados(tipo_nomina_id: Optional[int] = None ...
            // Checking service: export const getEmpleados = async (params = {}) => { ... await apiService.get('/nomina/empleados', { params }); ... }
            // Wait, I need to verify if getEmpleados in nominaService supports params.
            // If not, I should update it. (Previously I updated getHistorial, not getEmpleados). 
            // PROACTIVE FIX: Send params anyway, if service ignores it, filters won't work server side.
            // But I'll assume standard service pattern or fix it if I see it failing.

            // Actually, let's fix the service call here to pass params properly.
            // Assuming getEmpleados signature is getEmpleados(params) or similar.
            // Based on previous file read of getHistorial, likely getEmpleados is generic.

            // Re-reading service file previously showed:
            // export const getEmpleados = async (params = {}) => {
            //    try {
            //        const response = await apiService.get('/nomina/empleados', { params });
            //        return response.data;
            //    } ...

            // So it IS supported! Great.

            const data = await getEmpleados({ tipo_nomina_id: filterTipo || undefined });
            setEmpleados(data);
        } catch (error) {
            toast.error("Error al cargar empleados");
        } finally {
            setLoading(false);
        }
    };

    const handleSearchTercero = async (term) => {
        setSearchTerm(term);
        if (term.length < 3) {
            setSearchResults([]);
            return;
        }

        setSearching(true);
        try {
            const results = await getTerceros({ filtro: term });
            setSearchResults(Array.isArray(results) ? results : results.data || []);
        } catch (error) {
            console.error("Error buscando terceros", error);
        } finally {
            setSearching(false);
        }
    };

    const selectTercero = (tercero) => {
        const rawName = tercero.razon_social || tercero.nombre_razon_social || tercero.nombre || '';
        const parts = rawName.split(' ').filter(Boolean);
        let nombres = '', apellidos = '';

        if (parts.length > 2) {
            apellidos = parts.slice(-2).join(' ');
            nombres = parts.slice(0, -2).join(' ');
        } else if (parts.length === 2) {
            nombres = parts[0];
            apellidos = parts[1];
        } else {
            nombres = rawName;
            apellidos = '.';
        }

        setFormData({
            ...formData,
            nombres: nombres || '',
            apellidos: apellidos || '',
            numero_documento: tercero.nit || '',
            tercero_id: tercero.id
        });
        setSearchTerm('');
        setSearchResults([]);
    };

    const handleDocumentoBlur = async () => {
        const val = formData.numero_documento;
        if (!val || val.length < 5) return;

        try {
            const results = await getTerceros({ filtro: val });
            const lista = Array.isArray(results) ? results : results.data || [];

            const found = lista.find(t => t.nit === val);
            if (found) {
                selectTercero(found);
                toast.info("Datos completados desde Terceros");
            }
        } catch (error) {
            console.error(error);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const payload = { ...formData };
            if (payload.tipo_nomina_id === '') payload.tipo_nomina_id = null;
            else payload.tipo_nomina_id = parseInt(payload.tipo_nomina_id);

            if (editingId) {
                await updateEmpleado(editingId, payload);
                toast.success("Empleado actualizado");
            } else {
                await createEmpleado(payload);
                toast.success("Empleado creado");
            }

            resetForm();
            loadEmpleados();
        } catch (error) {
            toast.error("Error al guardar empleado");
        }
    };


    const handleSalarioChange = (e) => {
        const val = e.target.value;
        const numVal = parseFloat(val) || 0;
        // SMMLV 2025 aprox: 1,423,500 * 2 = 2,847,000
        const topeAuxilio = 2847000;

        setFormData(prev => ({
            ...prev,
            salario_base: val,
            tiene_auxilio: numVal <= topeAuxilio
        }));
    };

    const startEdit = (emp) => {
        setEditingId(emp.id);
        setFormData({
            nombres: emp.nombres,
            apellidos: emp.apellidos,
            numero_documento: emp.numero_documento,
            salario_base: emp.salario_base,
            fecha_ingreso: emp.fecha_ingreso,
            tiene_auxilio: emp.auxilio_transporte ?? false, // Fix uncontrolled input warning
            tercero_id: emp.tercero_id,
            tipo_nomina_id: emp.tipo_nomina_id || ''
        });
        setShowForm(true);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    const resetForm = () => {
        setShowForm(false);
        setEditingId(null);
        setFormData({
            nombres: '', apellidos: '', numero_documento: '',
            salario_base: '', fecha_ingreso: '', tiene_auxilio: true,
            tercero_id: null, tipo_nomina_id: ''
        });
    };

    // ... (rest of code) ...

    /* IN RENDER: Update Input to use handleSalarioChange */
    /*
    <input type="number" name="salario_base" placeholder="Salario Base" className="border p-2 rounded" required
           value={formData.salario_base} onChange={handleSalarioChange} />
    */

    const handlePrint = async () => {
        try {
            toast.info("Generando reporte...");
            await downloadEmpleadosPdf(filterTipo || undefined);
            toast.success("Reporte descargado");
        } catch (e) {
            toast.error("Error al generar PDF");
        }
    };

    // --- CLIENT SIDE FILTERING (Visual Search) ---
    const displayedEmpleados = empleados.filter(emp => {
        if (!textFilter) return true;
        const search = textFilter.toLowerCase();
        const fullName = `${emp.nombres} ${emp.apellidos}`.toLowerCase();
        const doc = emp.numero_documento.toLowerCase();
        return fullName.includes(search) || doc.includes(search);
    });

    return (
        <div className="p-8 max-w-7xl mx-auto">
            <ToastContainer />

            {/* HEADER & ACTIONS */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                <div>
                    <h1 className="text-3xl font-light text-gray-800 flex items-center gap-2">
                        <FaUserPlus className="text-gray-400" /> Gestión de Empleados
                    </h1>
                    <p className="text-gray-500 text-sm mt-1">Administre su planta de personal, contratos y asignación de nómina.</p>
                </div>

                <div className="flex gap-2">
                    <button
                        onClick={handlePrint}
                        className="bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 px-4 py-2 rounded shadow-sm flex items-center transition font-medium"
                    >
                        <FaFilePdf className="mr-2 text-red-500" /> Imprimir Lista
                    </button>
                    <button
                        onClick={() => { resetForm(); setShowForm(true); }}
                        className="bg-blue-600 text-white px-4 py-2 rounded shadow hover:bg-blue-700 flex items-center font-bold transition"
                    >
                        <FaUserPlus className="mr-2" /> Nuevo Empleado
                    </button>
                </div>
            </div>

            {/* FILTERS BAR */}
            <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100 mb-6 flex flex-col md:flex-row gap-4 items-center justify-between">

                {/* Payroll Type Filter */}
                <div className="flex items-center gap-3 w-full md:w-auto">
                    <FaFilter className="text-gray-400" />
                    <div className="flex flex-col">
                        <label className="text-[10px] uppercase font-bold text-gray-400">Filtrar por Nómina</label>
                        <select
                            value={filterTipo}
                            onChange={(e) => setFilterTipo(e.target.value)}
                            className="border-none bg-gray-50 rounded px-2 py-1 text-sm font-medium focus:ring-0 cursor-pointer hover:bg-gray-100 transition w-full md:w-48"
                        >
                            <option value="">-- Todas las Nóminas --</option>
                            {tiposNomina.map(t => (
                                <option key={t.id} value={t.id}>{t.nombre}</option>
                            ))}
                        </select>
                    </div>
                </div>

                {/* Instant Search */}
                <div className="relative w-full md:w-80">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <FaSearch className="text-gray-400" />
                    </div>
                    <input
                        type="text"
                        placeholder="Buscar por Nombre o Cédula..."
                        className="pl-10 pr-10 py-2 border border-gray-200 rounded-full w-full focus:ring-2 focus:ring-blue-100 outline-none transition text-sm"
                        value={textFilter}
                        onChange={(e) => setTextFilter(e.target.value)}
                    />
                    {textFilter && (
                        <button
                            onClick={() => setTextFilter('')}
                            className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
                        >
                            <FaTimes size={12} />
                        </button>
                    )}
                </div>
            </div>

            {/* FORMULARIO (MODAL O INLINE) - Mantenemos inline por ahora pero mejorado */}
            {showForm && (
                <div className="bg-white p-8 rounded-lg shadow-lg mb-8 border-t-4 border-blue-500 animate-fadeIn relative">
                    <button onClick={resetForm} className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition"><FaTimes size={20} /></button>
                    <h3 className="font-bold text-xl mb-6 text-gray-800 border-b pb-2">
                        {editingId ? 'Editar Información del Colaborador' : 'Registrar Nuevo Colaborador'}
                    </h3>


                    {!editingId && (
                        <div className="mb-6 bg-blue-50 p-4 rounded-lg flex flex-col gap-2 border border-blue-100 relative z-20">
                            <div className="flex items-center gap-2 mb-1">
                                <FaSearch className="text-blue-500" />
                                <span className="text-sm font-bold text-blue-800">Autocompletar Datos (Buscar Tercero)</span>
                            </div>

                            <div className="w-full relative">
                                <input
                                    type="text"
                                    placeholder="Escriba Nombre o NIT para buscar..."
                                    className="w-full p-2 border border-blue-300 rounded focus:ring-2 focus:ring-blue-400 outline-none bg-white"
                                    value={searchTerm}
                                    onChange={(e) => handleSearchTercero(e.target.value)}
                                    autoComplete="off"
                                />

                                {/* RESULTADOS AUTOCOMPLETE */}
                                {searchResults.length > 0 && (
                                    <ul className="absolute top-full left-0 w-full bg-white border border-gray-300 rounded-b shadow-2xl max-h-60 overflow-y-auto z-50 mt-1">
                                        {searchResults.map(t => (
                                            <li key={t.id}
                                                onMouseDown={() => selectTercero(t)} /* onMouseDown fires before onBlur */
                                                className="p-3 hover:bg-blue-100 cursor-pointer border-b last:border-b-0 text-sm flex justify-between items-center transition"
                                            >
                                                <span className="font-bold text-gray-800">{t.razon_social || t.nombre_razon_social}</span>
                                                <span className="text-gray-500 bg-gray-100 px-2 py-1 rounded text-xs">NIT: {t.nit}</span>
                                            </li>
                                        ))}
                                    </ul>
                                )}
                                {searchTerm.length > 2 && searchResults.length === 0 && searching === false && (
                                    <div className="absolute top-full left-0 w-full bg-white border border-gray-200 p-2 text-center text-gray-500 text-xs z-50 shadow-lg">
                                        No se encontraron resultados
                                    </div>
                                )}
                            </div>
                            <p className="text-[10px] text-blue-600 mt-1">
                                * Escriba para buscar en la base de datos de Terceros y rellenar el formulario.
                            </p>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Nombres</label>
                            <input name="nombres" className="w-full border p-2 rounded focus:ring-2 focus:ring-blue-200 outline-none" required
                                value={formData.nombres} onChange={e => setFormData({ ...formData, nombres: e.target.value })} />
                        </div>
                        <div>
                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Apellidos</label>
                            <input name="apellidos" className="w-full border p-2 rounded focus:ring-2 focus:ring-blue-200 outline-none" required
                                value={formData.apellidos} onChange={e => setFormData({ ...formData, apellidos: e.target.value })} />
                        </div>

                        <div>
                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">No. Documento</label>
                            <input name="numero_documento" className="w-full border p-2 rounded focus:ring-2 focus:ring-blue-200 outline-none font-mono" required
                                value={formData.numero_documento}
                                onChange={e => setFormData({ ...formData, numero_documento: e.target.value })}
                                onBlur={handleDocumentoBlur}
                            />
                        </div>

                        <div>
                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Salario Base</label>
                            <input type="number" className="w-full border p-2 rounded focus:ring-2 focus:ring-blue-200 outline-none font-mono text-right" required
                                value={formData.salario_base} onChange={handleSalarioChange} />
                        </div>

                        <div>
                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Fecha Ingreso</label>
                            <input type="date" className="w-full border p-2 rounded focus:ring-2 focus:ring-blue-200 outline-none" required
                                value={formData.fecha_ingreso} onChange={e => setFormData({ ...formData, fecha_ingreso: e.target.value })} />
                        </div>

                        <div>
                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Asignar a Nómina</label>
                            <select
                                className="w-full border p-2 rounded focus:ring-2 focus:ring-blue-200 outline-none bg-white"
                                value={formData.tipo_nomina_id}
                                onChange={e => setFormData({ ...formData, tipo_nomina_id: e.target.value })}
                            >
                                <option value="">-- Sin Clasificar --</option>
                                {tiposNomina.map(tipo => (
                                    <option key={tipo.id} value={tipo.id}>{tipo.nombre} ({tipo.periodo_pago})</option>
                                ))}
                            </select>
                        </div>

                        <div className="flex items-center md:col-span-2 bg-gray-50 p-3 rounded border border-gray-100">
                            <input type="checkbox" id="aux" checked={formData.tiene_auxilio}
                                onChange={e => setFormData({ ...formData, tiene_auxilio: e.target.checked })} className="mr-3 h-5 w-5 text-blue-600 rounded" />
                            <label htmlFor="aux" className="text-gray-700 font-medium">Aplica Auxilio de Transporte</label>
                        </div>

                        <div className="md:col-span-2 flex gap-3 pt-4 border-t">
                            <button type="submit" className="bg-green-600 text-white px-8 py-3 rounded hover:bg-green-700 font-bold flex justify-center items-center shadow-lg transform hover:-translate-y-0.5 transition">
                                <FaCheck className="mr-2" /> {editingId ? 'Guardar Cambios' : 'Registrar Empleado'}
                            </button>
                            {editingId && (
                                <button type="button" onClick={resetForm} className="bg-gray-200 text-gray-700 px-6 py-3 rounded hover:bg-gray-300 font-bold transition">
                                    Cancelar
                                </button>
                            )}
                        </div>
                    </form>
                </div>
            )}

            {/* TABLE */}
            <div className="bg-white rounded-lg shadow-md overflow-hidden border border-gray-100">
                <table className="w-full text-left">
                    <thead className="bg-gray-50 text-gray-600 uppercase text-xs font-bold tracking-wider">
                        <tr>
                            <th className="p-4 border-b">Documento</th>
                            <th className="p-4 border-b">Nombre Completo</th>
                            <th className="p-4 border-b">Tipo Nómina</th>
                            <th className="p-4 border-b text-right">Salario Base</th>
                            <th className="p-4 border-b">Ingreso</th>
                            <th className="p-4 border-b text-center">Editar</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {displayedEmpleados.map(emp => (
                            <tr key={emp.id} className="hover:bg-blue-50 transition duration-150 group">
                                <td className="p-4 font-mono text-sm text-gray-500">{emp.numero_documento}</td>
                                <td className="p-4">
                                    <div className="font-bold text-gray-800">{emp.nombres} {emp.apellidos}</div>
                                    <div className="text-[10px] text-gray-400">{emp.email || 'Sin email'}</div>
                                </td>
                                <td className="p-4 text-sm">
                                    {tiposNomina.find(t => t.id === emp.tipo_nomina_id) ? (
                                        <span className="bg-purple-100 text-purple-700 px-2 py-1 rounded text-xs font-bold">
                                            {tiposNomina.find(t => t.id === emp.tipo_nomina_id).nombre}
                                        </span>
                                    ) : (
                                        <span className="text-gray-400 italic text-xs">Sin Asignar</span>
                                    )}
                                </td>
                                <td className="p-4 text-right font-mono font-medium text-gray-700">
                                    {new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(emp.salario_base)}
                                </td>
                                <td className="p-4 text-gray-500 text-xs">{emp.fecha_ingreso}</td>
                                <td className="p-4 text-center">
                                    <button
                                        onClick={() => startEdit(emp)}
                                        className="text-gray-400 hover:text-blue-600 bg-transparent hover:bg-blue-100 p-2 rounded-full transition"
                                        title="Editar Empleado"
                                    >
                                        <FaEdit />
                                    </button>
                                </td>
                            </tr>
                        ))}
                        {displayedEmpleados.length === 0 && !loading && (
                            <tr>
                                <td colSpan="6" className="p-12 text-center text-gray-400 italic bg-gray-50">
                                    No se encontraron empleados con los filtros actuales.
                                </td>
                            </tr>
                        )}
                        {loading && (
                            <tr><td colSpan="6" className="p-8 text-center text-blue-500 animate-pulse">Cargando...</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
            <div className="mt-4 text-right text-xs text-gray-400">
                Mostrando {displayedEmpleados.length} registros
            </div>
        </div>
    );
}
