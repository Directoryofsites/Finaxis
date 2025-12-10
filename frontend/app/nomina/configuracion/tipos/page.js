"use client";

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import {
    FaPlus, FaEdit, FaTrash, FaCheck, FaTimes, FaMoneyCheckAlt, FaArrowLeft
} from 'react-icons/fa';
import Link from 'next/link';
import { getTiposNomina, createTipoNomina, updateTipoNomina, deleteTipoNomina } from '@/lib/nominaService';

export default function GestionTiposNominaPage() {
    const [tipos, setTipos] = useState([]);
    const [loading, setLoading] = useState(true);
    const [editingTipo, setEditingTipo] = useState(null);
    const [isModalOpen, setIsModalOpen] = useState(false);

    const { register, handleSubmit, reset, setValue, formState: { errors } } = useForm();

    const fetchTipos = async () => {
        setLoading(true);
        try {
            const data = await getTiposNomina();
            setTipos(data);
        } catch (error) {
            toast.error("Error al cargar tipos de nómina");
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTipos();
    }, []);

    const onSubmit = async (data) => {
        try {
            if (editingTipo) {
                await updateTipoNomina(editingTipo.id, data);
                toast.success("Tipo de nómina actualizado");
            } else {
                await createTipoNomina(data);
                toast.success("Tipo de nómina creado");
            }
            setIsModalOpen(false);
            setEditingTipo(null);
            reset();
            fetchTipos();
        } catch (error) {
            toast.error("Error al guardar");
            console.error(error);
        }
    };

    const handleEdit = (tipo) => {
        setEditingTipo(tipo);
        setValue('nombre', tipo.nombre);
        setValue('descripcion', tipo.descripcion);
        setValue('periodo_pago', tipo.periodo_pago);
        setIsModalOpen(true);
    };

    const handleDelete = async (id) => {
        if (!confirm("¿Seguro que deseas eliminar este tipo de nómina?")) return;
        try {
            await deleteTipoNomina(id);
            toast.success("Eliminado correctamente");
            fetchTipos();
        } catch (error) {
            toast.error(error.response?.data?.detail || "Error al eliminar");
        }
    };

    const openNew = () => {
        setEditingTipo(null);
        reset();
        setValue('periodo_pago', 'Mensual');
        setIsModalOpen(true);
    };

    return (
        <div className="p-6 max-w-6xl mx-auto">
            <ToastContainer />
            {/* Header */}
            <div className="flex justify-between items-center mb-6">
                <div className="flex items-center gap-3">
                    <Link href="/nomina/configuracion" className="text-gray-500 hover:text-blue-600 transition-colors">
                        <FaArrowLeft size={20} />
                    </Link>
                    <div>
                        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                            <FaMoneyCheckAlt className="text-blue-600" /> Tipos de Nómina
                        </h1>
                        <p className="text-gray-500 text-sm">Gestiona las diferentes clasificaciones para tus empleados (Ej: Administrativa, Operativa)</p>
                    </div>
                </div>
                <button
                    onClick={openNew}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition flex items-center gap-2 shadow-sm font-medium"
                >
                    <FaPlus /> Nuevo Tipo
                </button>
            </div>

            {/* Content */}
            {loading ? (
                <div className="text-center py-10 text-gray-500">Cargando...</div>
            ) : (
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                    <table className="w-full text-left">
                        <thead className="bg-gray-50 text-gray-600 font-semibold text-sm uppercase tracking-wider border-b border-gray-200">
                            <tr>
                                <th className="px-6 py-4">Nombre</th>
                                <th className="px-6 py-4">Descripción</th>
                                <th className="px-6 py-4 text-center">Periodo Pago</th>
                                <th className="px-6 py-4 text-right">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {tipos.length === 0 ? (
                                <tr>
                                    <td colSpan="4" className="px-6 py-8 text-center text-gray-400 italic">
                                        No hay tipos de nómina configurados.
                                    </td>
                                </tr>
                            ) : tipos.map(tipo => (
                                <tr key={tipo.id} className="hover:bg-gray-50 transition-colors">
                                    <td className="px-6 py-4 font-medium text-gray-800">{tipo.nombre}</td>
                                    <td className="px-6 py-4 text-gray-500 text-sm">{tipo.descripcion || '-'}</td>
                                    <td className="px-6 py-4 text-center">
                                        <span className={`text-xs px-2 py-1 rounded-full font-bold ${tipo.periodo_pago === 'Mensual' ? 'bg-green-100 text-green-700' : 'bg-purple-100 text-purple-700'
                                            }`}>
                                            {tipo.periodo_pago}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-right space-x-2">
                                        <button
                                            onClick={() => handleEdit(tipo)}
                                            className="text-blue-500 hover:text-blue-700 p-1 rounded hover:bg-blue-50 transition"
                                            title="Editar"
                                        >
                                            <FaEdit />
                                        </button>
                                        <button
                                            onClick={() => handleDelete(tipo.id)}
                                            className="text-red-400 hover:text-red-600 p-1 rounded hover:bg-red-50 transition"
                                            title="Eliminar"
                                        >
                                            <FaTrash />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Modal Form */}
            {isModalOpen && (
                <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
                    <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden transform transition-all">
                        <form onSubmit={handleSubmit(onSubmit)}>
                            <div className="px-6 py-4 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
                                <h3 className="text-lg font-bold text-gray-800">
                                    {editingTipo ? 'Editar Tipo de Nómina' : 'Nuevo Tipo de Nómina'}
                                </h3>
                                <button type="button" onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                                    <FaTimes />
                                </button>
                            </div>

                            <div className="p-6 space-y-4">
                                <div>
                                    <label className="block text-sm font-bold text-gray-700 mb-1">Nombre <span className="text-red-500">*</span></label>
                                    <input
                                        {...register('nombre', { required: "El nombre es obligatorio" })}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition"
                                        placeholder="Ej: Administrativa"
                                    />
                                    {errors.nombre && <span className="text-red-500 text-xs">{errors.nombre.message}</span>}
                                </div>

                                <div>
                                    <label className="block text-sm font-bold text-gray-700 mb-1">Descripción</label>
                                    <textarea
                                        {...register('descripcion')}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition resize-none h-20"
                                        placeholder="Opcional..."
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-bold text-gray-700 mb-1">Periodo de Pago</label>
                                    <select
                                        {...register('periodo_pago')}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none bg-white"
                                    >
                                        <option value="Mensual">Mensual</option>
                                        <option value="Quincenal">Quincenal</option>
                                    </select>
                                </div>
                            </div>

                            <div className="px-6 py-4 border-t border-gray-100 bg-gray-50 flex justify-end gap-3">
                                <button
                                    type="button"
                                    onClick={() => setIsModalOpen(false)}
                                    className="px-4 py-2 text-gray-600 hover:bg-gray-200 rounded-lg font-medium transition"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-bold shadow-md transition flex items-center gap-2"
                                >
                                    <FaSave /> Guardar
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}

function FaSave(props) {
    return <FaCheck {...props} />
}
