"use client";
import React, { useState, useEffect } from 'react';
import { getEmpleados, createEmpleado, updateEmpleado, getTiposNomina } from '../../../lib/nominaService';
import { getTerceros } from '../../../lib/terceroService';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { FaUserPlus, FaSearch, FaEdit, FaCheck, FaTimes } from 'react-icons/fa';

export default function EmpleadosPage() {
    const [empleados, setEmpleados] = useState([]);
    const [tiposNomina, setTiposNomina] = useState([]);
    const [loading, setLoading] = useState(false);
    const [showForm, setShowForm] = useState(false);
    const [editingId, setEditingId] = useState(null);

    // Form State
    const [formData, setFormData] = useState({
        nombres: '', apellidos: '', numero_documento: '',
        salario_base: '', fecha_ingreso: '', tiene_auxilio: true,
        tercero_id: null, tipo_nomina_id: ''
    });

    // Search State
    const [searchTerm, setSearchTerm] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [searching, setSearching] = useState(false);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [emps, tipos] = await Promise.all([
                getEmpleados(),
                getTiposNomina()
            ]);
            setEmpleados(emps);
            setTiposNomina(tipos);
        } catch (error) {
            toast.error("Error al cargar datos");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

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
        const rawName = tercero.nombre_razon_social || '';
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

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            // Prepare payload
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
            fetchData();
        } catch (error) {
            toast.error("Error al guardar empleado");
        }
    };

    const startEdit = (emp) => {
        setEditingId(emp.id);
        setFormData({
            nombres: emp.nombres,
            apellidos: emp.apellidos,
            numero_documento: emp.numero_documento,
            salario_base: emp.salario_base,
            fecha_ingreso: emp.fecha_ingreso,
            tiene_auxilio: emp.auxilio_transporte,
            tercero_id: emp.tercero_id,
            tipo_nomina_id: emp.tipo_nomina_id || ''
        });
        setShowForm(true);
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

    return (
        <div className="p-8">
            <ToastContainer />
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-light text-gray-800">Gestión de Empleados</h1>
                <button
                    onClick={() => { resetForm(); setShowForm(true); }}
                    className="bg-blue-600 text-white px-4 py-2 rounded shadow hover:bg-blue-700 flex items-center"
                >
                    <FaUserPlus className="mr-2" /> Nuevo Empleado
                </button>
            </div>

            {showForm && (
                <div className="bg-white p-6 rounded shadow mb-6 border-l-4 border-blue-500 animate-fadeIn relative">
                    <button onClick={resetForm} className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"><FaTimes /></button>
                    <h3 className="font-bold mb-4 text-gray-700">{editingId ? 'Editar Empleado' : 'Registrar Nuevo Colaborador'}</h3>

                    {!editingId && (
                        <div className="mb-6 relative">
                            <label className="block text-xs text-gray-500 mb-1">Buscar Tercero Existente (Opcional)</label>
                            <div className="flex">
                                <input
                                    type="text"
                                    placeholder="Buscar por Nombre o NIT..."
                                    className="border p-2 rounded-l w-full focus:outline-none focus:ring-2 focus:ring-blue-300"
                                    value={searchTerm}
                                    onChange={(e) => handleSearchTercero(e.target.value)}
                                />
                                <div className="bg-gray-100 p-2 rounded-r border border-l-0 text-gray-500">
                                    <FaSearch />
                                </div>
                            </div>
                            {searchResults.length > 0 && (
                                <ul className="absolute z-10 w-full bg-white border rounded shadow-lg max-h-48 overflow-y-auto mt-1">
                                    {searchResults.map(t => (
                                        <li key={t.id}
                                            onClick={() => selectTercero(t)}
                                            className="p-2 hover:bg-blue-50 cursor-pointer border-b last:border-b-0 text-sm"
                                        >
                                            <span className="font-bold">{t.nombre_razon_social}</span>
                                            <span className="text-gray-500 ml-2">({t.nit})</span>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <input name="nombres" placeholder="Nombres" className="border p-2 rounded" required
                            value={formData.nombres} onChange={e => setFormData({ ...formData, nombres: e.target.value })} />
                        <input name="apellidos" placeholder="Apellidos" className="border p-2 rounded" required
                            value={formData.apellidos} onChange={e => setFormData({ ...formData, apellidos: e.target.value })} />
                        <input name="numero_documento" placeholder="No. Documento" className="border p-2 rounded" required
                            value={formData.numero_documento} onChange={e => setFormData({ ...formData, numero_documento: e.target.value })} />
                        <input type="number" name="salario_base" placeholder="Salario Base" className="border p-2 rounded" required
                            value={formData.salario_base} onChange={e => setFormData({ ...formData, salario_base: e.target.value })} />

                        <div>
                            <label className="block text-xs text-gray-500">Fecha Ingreso</label>
                            <input type="date" className="border p-2 rounded w-full" required
                                value={formData.fecha_ingreso} onChange={e => setFormData({ ...formData, fecha_ingreso: e.target.value })} />
                        </div>

                        <div>
                            <label className="block text-xs text-gray-500">Tipo de Nómina</label>
                            <select
                                className="border p-2 rounded w-full bg-white"
                                value={formData.tipo_nomina_id}
                                onChange={e => setFormData({ ...formData, tipo_nomina_id: e.target.value })}
                            >
                                <option value="">-- Sin Clasificar --</option>
                                {tiposNomina.map(tipo => (
                                    <option key={tipo.id} value={tipo.id}>{tipo.nombre} ({tipo.periodo_pago})</option>
                                ))}
                            </select>
                        </div>

                        <div className="flex items-center md:col-span-2">
                            <input type="checkbox" id="aux" checked={formData.tiene_auxilio}
                                onChange={e => setFormData({ ...formData, tiene_auxilio: e.target.checked })} className="mr-2 h-5 w-5" />
                            <label htmlFor="aux" className="text-gray-700">Aplica Auxilio de Transporte</label>
                        </div>

                        <div className="md:col-span-2 flex gap-3">
                            <button type="submit" className="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700 w-full font-bold flex justify-center items-center">
                                <FaCheck className="mr-2" /> {editingId ? 'Actualizar Empleado' : 'Guardar Empleado'}
                            </button>
                            {editingId && (
                                <button type="button" onClick={resetForm} className="bg-gray-400 text-white px-4 py-2 rounded hover:bg-gray-500">
                                    Cancelar
                                </button>
                            )}
                        </div>
                    </form>
                </div>
            )}

            <div className="bg-white rounded shadow overflow-hidden">
                <table className="w-full text-left">
                    <thead className="bg-gray-100 text-gray-600 uppercase text-xs">
                        <tr>
                            <th className="p-4">Documento</th>
                            <th className="p-4">Nombre Completo</th>
                            <th className="p-4">Tipo Nómina</th>
                            <th className="p-4">Salario Base</th>
                            <th className="p-4">Fecha Ingreso</th>
                            <th className="p-4 text-right">Acciones</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {empleados.map(emp => (
                            <tr key={emp.id} className="hover:bg-gray-50">
                                <td className="p-4 font-mono text-sm">{emp.numero_documento}</td>
                                <td className="p-4 font-medium text-gray-800">{emp.nombres} {emp.apellidos}</td>
                                <td className="p-4 text-sm text-gray-600">
                                    {tiposNomina.find(t => t.id === emp.tipo_nomina_id)?.nombre || <span className="text-gray-400 italic">No Asignado</span>}
                                </td>
                                <td className="p-4 text-green-600 font-bold">
                                    {new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(emp.salario_base)}
                                </td>
                                <td className="p-4 text-gray-500 text-sm">{emp.fecha_ingreso}</td>
                                <td className="p-4 text-right">
                                    <button
                                        onClick={() => startEdit(emp)}
                                        className="text-blue-500 hover:text-blue-700 bg-blue-50 p-2 rounded transition"
                                    >
                                        <FaEdit />
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
