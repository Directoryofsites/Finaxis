'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAuth } from '../../../../context/AuthContext';
import BotonRegresar from '../../../../components/BotonRegresar';
import BuscadorTerceros from '../../../../../components/BuscadorTerceros';
import { phService } from '../../../../../lib/phService';
import { getTerceroById } from '../../../../../lib/terceroService';
import { FaSave, FaBuilding, FaCar, FaPaw, FaTrash, FaPlus, FaPen, FaLayerGroup } from 'react-icons/fa';

// Estilos
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none";
const sectionTitleClass = "text-lg font-bold text-gray-700 flex items-center gap-2 border-b pb-2 mb-4";

export default function EditarUnidadPage() {
    const router = useRouter();
    const { id } = useParams();
    const { user, loading: authLoading } = useAuth();
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);

    // Estado del Formulario Principal
    const [formData, setFormData] = useState({
        codigo: '',
        tipo: 'RESIDENCIAL',
        torre_id: '',
        matricula_inmobiliaria: '',
        area_privada: 0,
        coeficiente: 0,
        observaciones: '',
        propietario_principal_id: null,
        modulos_ids: []
    });

    const [selectedPropietario, setSelectedPropietario] = useState(null);
    const [availableModulos, setAvailableModulos] = useState([]);

    // Estado para Listas Anidadas
    const [vehiculos, setVehiculos] = useState([]);
    const [mascotas, setMascotas] = useState([]);

    // Cargar Datos
    useEffect(() => {
        if (!authLoading && user) {
            const fetchData = async () => {
                try {
                    setLoading(true);

                    // Cargar Unidad y Módulos en paralelo
                    const [data, mods] = await Promise.all([
                        phService.getUnidadById(id),
                        phService.getModulos()
                    ]);

                    setAvailableModulos(mods);

                    setFormData({
                        codigo: data.codigo,
                        tipo: data.tipo,
                        torre_id: data.torre_id || '',
                        matricula_inmobiliaria: data.matricula_inmobiliaria || '',
                        area_privada: data.area_privada || 0,
                        coeficiente: data.coeficiente || 0,
                        observaciones: data.observaciones || '',
                        propietario_principal_id: data.propietario_principal_id || null,
                        modulos_ids: data.modulos_contribucion ? data.modulos_contribucion.map(m => m.id) : []
                    });
                    setVehiculos(data.vehiculos || []);
                    setMascotas(data.mascotas || []);

                    // Cargar Propietario si existe
                    if (data.propietario_principal_id) {
                        try {
                            const terceroData = await getTerceroById(data.propietario_principal_id);
                            setSelectedPropietario(terceroData);
                        } catch (err) {
                            console.error("Error cargando propietario:", err);
                        }
                    }

                } catch (err) {
                    setError("No se pudo cargar la unidad.");
                    console.error(err);
                } finally {
                    setLoading(false);
                }
            };
            fetchData();
        }
    }, [id, user, authLoading]);

    const handlePropietarioSelect = (tercero) => {
        setSelectedPropietario(tercero);
        setFormData(prev => ({ ...prev, propietario_principal_id: tercero ? tercero.id : null }));
    };

    // Handler Módulos
    const toggleModulo = (id) => {
        setFormData(prev => {
            const current = prev.modulos_ids || [];
            if (current.includes(id)) {
                return { ...prev, modulos_ids: current.filter(x => x !== id) };
            } else {
                return { ...prev, modulos_ids: [...current, id] };
            }
        });
    };


    // Handlers para Formulario Principal
    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    // Handlers para Vehiculos
    const addVehiculo = () => {
        setVehiculos([...vehiculos, { placa: '', tipo: 'Carro', marca: '', color: '' }]);
    };
    const updateVehiculo = (idx, field, val) => {
        const updated = [...vehiculos];
        updated[idx][field] = val;
        setVehiculos(updated);
    };
    const removeVehiculo = (idx) => {
        setVehiculos(vehiculos.filter((_, i) => i !== idx));
    };

    // Handlers para Mascotas
    const addMascota = () => {
        setMascotas([...mascotas, { nombre: '', especie: 'Perro', raza: '' }]);
    };
    const updateMascota = (idx, field, val) => {
        const updated = [...mascotas];
        updated[idx][field] = val;
        setMascotas(updated);
    };
    const removeMascota = (idx) => {
        setMascotas(mascotas.filter((_, i) => i !== idx));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError(null);
        try {
            // Preparar payload
            const payload = {
                ...formData,
                torre_id: formData.torre_id === '' ? null : parseInt(formData.torre_id),
                vehiculos: vehiculos,
                mascotas: mascotas
            };

            await phService.updateUnidad(id, payload);
            alert('Unidad actualizada exitosamente');
            router.push('/ph/unidades');
        } catch (err) {
            const detail = err.response?.data?.detail;
            if (typeof detail === 'string') {
                setError(detail);
            } else if (Array.isArray(detail)) {
                const msg = detail.map(e => `${e.loc[1] || 'Campo'}: ${e.msg}`).join(', ');
                setError(msg);
            } else if (typeof detail === 'object') {
                setError(JSON.stringify(detail));
            } else {
                setError('Error al actualizar la unidad.');
            }
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <div className="p-10 text-center text-gray-500">Cargando datos...</div>;

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
            <div className="max-w-4xl mx-auto">
                {/* HEADER */}
                <div className="flex justify-between items-center mb-6">
                    <div className="flex items-center gap-4">
                        <BotonRegresar />
                        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                            <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600"><FaPen /></div>
                            Editar Unidad {formData.codigo}
                        </h1>
                    </div>
                </div>

                {error && (
                    <div className="mb-6 p-4 bg-red-100 border-l-4 border-red-500 text-red-700 rounded-r-lg">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Reutilización de campos (Mismo diseño que Crear) */}
                    {/* DATOS BÁSICOS */}
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                        <h2 className={sectionTitleClass}>Datos Generales</h2>

                        {/* BUSCADOR PROPIETARIO */}
                        <div className="mb-4 bg-indigo-50/50 p-4 rounded-lg border border-indigo-100">
                            <BuscadorTerceros
                                label="Propietario Principal *"
                                onSelect={handlePropietarioSelect}
                                selected={selectedPropietario}
                            />
                            <p className="text-[10px] text-indigo-400 mt-1 flex items-center gap-1">
                                <FaBuilding /> La factura se generará a nombre de este tercero.
                            </p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className={labelClass}>Código / Número *</label>
                                <input name="codigo" required className={inputClass} placeholder="Ej: 501, LC-101" value={formData.codigo} onChange={handleChange} />
                            </div>
                            <div>
                                <label className={labelClass}>Tipo de Unidad *</label>
                                <select name="tipo" className={inputClass} value={formData.tipo} onChange={handleChange}>
                                    <option value="RESIDENCIAL">Residencial</option>
                                    <option value="COMERCIAL">Comercial</option>
                                    <option value="PARQUEADERO">Parqueadero</option>
                                    <option value="DEPOSITO">Depósito</option>
                                </select>
                            </div>
                            <div>
                                <label className={labelClass}>Coeficiente (%) *</label>
                                <input type="number" step="0.000001" name="coeficiente" required className={inputClass} placeholder="0.00" value={formData.coeficiente} onChange={handleChange} />
                            </div>
                            <div>
                                <label className={labelClass}>Área Privada (m²)</label>
                                <input type="number" step="0.01" name="area_privada" className={inputClass} value={formData.area_privada} onChange={handleChange} />
                            </div>
                            <div>
                                <label className={labelClass}>Matrícula Inmobiliaria</label>
                                <input name="matricula_inmobiliaria" className={inputClass} value={formData.matricula_inmobiliaria} onChange={handleChange} />
                            </div>
                        </div>
                    </div>

                    {/* MÓDULOS DE CONTRIBUCIÓN (PH MIXTA) */}
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                        <h2 className={sectionTitleClass}><FaLayerGroup /> Módulos de Contribución (PH Mixta)</h2>
                        <p className="text-xs text-gray-400 mb-3">
                            Selecciona los sectores a los que pertenece esta unidad. Esto determinará qué gastos debe pagar.
                        </p>

                        {availableModulos.length === 0 ? (
                            <div className="bg-yellow-50 p-3 rounded-lg text-yellow-700 text-sm">
                                No hay módulos creados aún. Ve a Configuración &gt; Módulos.
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                                {availableModulos.map(mod => (
                                    <div
                                        key={mod.id}
                                        onClick={() => toggleModulo(mod.id)}
                                        className={`cursor-pointer p-3 rounded-lg border flex items-center gap-3 transition-all ${formData.modulos_ids.includes(mod.id)
                                                ? 'bg-indigo-50 border-indigo-500 ring-1 ring-indigo-500'
                                                : 'bg-white border-gray-200 hover:border-indigo-300'
                                            }`}
                                    >
                                        <div className={`w-5 h-5 rounded border flex items-center justify-center ${formData.modulos_ids.includes(mod.id) ? 'bg-indigo-600 border-indigo-600' : 'border-gray-300'
                                            }`}>
                                            {formData.modulos_ids.includes(mod.id) && <span className="text-white text-xs font-bold">✓</span>}
                                        </div>
                                        <div>
                                            <p className="font-bold text-gray-700 text-sm">{mod.nombre}</p>
                                            <p className="text-xs text-gray-400">{mod.tipo_distribucion}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* VEHÍCULOS */}
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                        <div className="flex justify-between items-center border-b pb-2 mb-4">
                            <h2 className="text-lg font-bold text-gray-700 flex items-center gap-2"><FaCar /> Vehículos</h2>
                            <button type="button" onClick={addVehiculo} className="px-3 py-1 bg-green-50 text-green-600 rounded-lg hover:bg-green-100 text-sm font-medium flex items-center gap-1">
                                <FaPlus /> Agregar
                            </button>
                        </div>
                        {vehiculos.length === 0 && <p className="text-gray-400 italic text-sm">No hay vehículos registrados.</p>}

                        <div className="space-y-3">
                            {vehiculos.map((v, i) => (
                                <div key={i} className="flex gap-2 items-end bg-gray-50 p-3 rounded-lg">
                                    <div className="flex-1">
                                        <label className="text-xs font-bold text-gray-500">Placa</label>
                                        <input className={inputClass} value={v.placa} onChange={(e) => updateVehiculo(i, 'placa', e.target.value)} placeholder="XXX-123" />
                                    </div>
                                    <div className="w-32">
                                        <label className="text-xs font-bold text-gray-500">Tipo</label>
                                        <select className={inputClass} value={v.tipo} onChange={(e) => updateVehiculo(i, 'tipo', e.target.value)}>
                                            <option>Carro</option>
                                            <option>Moto</option>
                                        </select>
                                    </div>
                                    <div className="flex-1">
                                        <label className="text-xs font-bold text-gray-500">Marca/Color</label>
                                        <input className={inputClass} value={v.marca} onChange={(e) => updateVehiculo(i, 'marca', e.target.value)} placeholder="Mazda Rojo" />
                                    </div>
                                    <button type="button" onClick={() => removeVehiculo(i)} className="p-2 text-red-500 hover:bg-red-100 rounded-lg mb-1"><FaTrash /></button>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* MASCOTAS */}
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                        <div className="flex justify-between items-center border-b pb-2 mb-4">
                            <h2 className="text-lg font-bold text-gray-700 flex items-center gap-2"><FaPaw /> Mascotas</h2>
                            <button type="button" onClick={addMascota} className="px-3 py-1 bg-amber-50 text-amber-600 rounded-lg hover:bg-amber-100 text-sm font-medium flex items-center gap-1">
                                <FaPlus /> Agregar
                            </button>
                        </div>
                        {mascotas.length === 0 && <p className="text-gray-400 italic text-sm">No hay mascotas registradas.</p>}

                        <div className="space-y-3">
                            {mascotas.map((m, i) => (
                                <div key={i} className="flex gap-2 items-end bg-gray-50 p-3 rounded-lg">
                                    <div className="flex-1">
                                        <label className="text-xs font-bold text-gray-500">Nombre</label>
                                        <input className={inputClass} value={m.nombre} onChange={(e) => updateMascota(i, 'nombre', e.target.value)} />
                                    </div>
                                    <div className="w-32">
                                        <label className="text-xs font-bold text-gray-500">Especie</label>
                                        <select className={inputClass} value={m.especie} onChange={(e) => updateMascota(i, 'especie', e.target.value)}>
                                            <option>Perro</option>
                                            <option>Gato</option>
                                            <option>Otro</option>
                                        </select>
                                    </div>
                                    <button type="button" onClick={() => removeMascota(i)} className="p-2 text-red-500 hover:bg-red-100 rounded-lg mb-1"><FaTrash /></button>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* BOTÓN GUARDAR */}
                    <div className="flex justify-end pt-4">
                        <button
                            type="submit"
                            disabled={saving}
                            className="flex items-center gap-2 px-8 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 shadow-md transform hover:-translate-y-1 transition-all font-bold disabled:opacity-50"
                        >
                            {saving ? 'Guardando...' : <><FaSave /> Actualizar Unidad</>}
                        </button>
                    </div>

                </form>
            </div>
        </div>
    );
}
