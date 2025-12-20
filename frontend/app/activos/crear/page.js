'use client';
import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiService } from '../../../lib/apiService';
import { FaSave, FaBarcode, FaMapMarkerAlt, FaCalendarAlt, FaDollarSign } from 'react-icons/fa';


export default function CrearActivoPage() {
    const router = useRouter();
    const [loading, setLoading] = useState(false);

    // Listas para selects
    const [categorias, setCategorias] = useState([]);
    const [terceros, setTerceros] = useState([]);

    const [formData, setFormData] = useState({
        codigo: '',
        nombre: '',
        descripcion: '',
        serial: '',
        modelo: '',
        marca: '',
        categoria_id: '',
        ubicacion: '',
        responsable_id: '',
        fecha_compra: new Date().toISOString().split('T')[0],
        costo_adquisicion: 0,
        valor_residual: 0,
        estado: 'ACTIVO'
    });

    useEffect(() => {
        loadMaestros();
    }, []);

    const loadMaestros = async () => {
        try {
            const [resCat, resTer] = await Promise.all([
                apiService.get('/activos/categorias'),
                apiService.get('/terceros/')
            ]);
            setCategorias(resCat.data);
            setTerceros(resTer.data);
        } catch (error) {
            console.error("Error cargando maestros:", error);
        }
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            // ARREGLO: Convertir strings vacíos a null para campos opcionales
            const dataToSend = { ...formData };

            // Validar campo requerido
            if (!dataToSend.categoria_id || dataToSend.categoria_id === '') {
                alert('Por favor selecciona una categoría de activo.');
                return;
            }

            // Convertir campos de ID a enteros
            dataToSend.categoria_id = parseInt(dataToSend.categoria_id);
            if (dataToSend.responsable_id === '' || !dataToSend.responsable_id) {
                dataToSend.responsable_id = null;
            } else {
                dataToSend.responsable_id = parseInt(dataToSend.responsable_id);
            }

            // Convertir números
            dataToSend.costo_adquisicion = parseFloat(dataToSend.costo_adquisicion) || 0;
            dataToSend.valor_residual = parseFloat(dataToSend.valor_residual) || 0;

            await apiService.post('/activos/', dataToSend);
            alert('Activo Fijo creado exitosamente.');
            router.push('/activos');
        } catch (error) {
            console.error(error);
            alert('Error al guardar el activo: ' + (error.response?.data?.detail || error.message));
        } finally {
            setLoading(false);
        }
    };

    const inputClass = "w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2";
    const labelClass = "block text-sm font-medium text-gray-700 mb-1";

    return (
        <div className="p-6 max-w-4xl mx-auto">
            <div className="flex items-center gap-4 mb-6">
                <h1 className="text-2xl font-bold text-gray-800">Registrar Nuevo Activo Fijo</h1>
            </div>

            <form onSubmit={handleSubmit} className="bg-white shadow-lg rounded-xl p-8 border border-gray-200">

                {/* SECCIÓN 1: IDENTIFICACIÓN */}
                <div className="mb-8">
                    <h2 className="text-lg font-bold text-blue-600 mb-4 border-b pb-2 flex items-center gap-2">
                        <FaBarcode /> Identificación del Bien
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label className={labelClass}>Placa / Código Interno *</label>
                            <input
                                type="text" name="codigo" required
                                className={inputClass}
                                value={formData.codigo} onChange={handleChange}
                                placeholder="Ej: AF-001"
                            />
                        </div>
                        <div>
                            <label className={labelClass}>Nombre del Activo *</label>
                            <input
                                type="text" name="nombre" required
                                className={inputClass}
                                value={formData.nombre} onChange={handleChange}
                                placeholder="Ej: Computador Portátil Dell XPS"
                            />
                        </div>
                        <div>
                            <label className={labelClass}>Categoría *</label>
                            <select
                                name="categoria_id" required
                                className={inputClass}
                                value={formData.categoria_id} onChange={handleChange}
                            >
                                <option value="">Seleccione...</option>
                                {categorias.map(c => (
                                    <option key={c.id} value={c.id}>{c.nombre}</option>
                                ))}
                            </select>
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                            <div>
                                <label className={labelClass}>Marca</label>
                                <input type="text" name="marca" className={inputClass} value={formData.marca} onChange={handleChange} />
                            </div>
                            <div>
                                <label className={labelClass}>Modelo</label>
                                <input type="text" name="modelo" className={inputClass} value={formData.modelo} onChange={handleChange} />
                            </div>
                        </div>
                        <div className="md:col-span-2">
                            <label className={labelClass}>Serial / No. Serie</label>
                            <input type="text" name="serial" className={inputClass} value={formData.serial} onChange={handleChange} />
                        </div>
                    </div>
                </div>

                {/* SECCIÓN 2: UBICACIÓN Y RESPONSABLE */}
                <div className="mb-8">
                    <h2 className="text-lg font-bold text-blue-600 mb-4 border-b pb-2 flex items-center gap-2">
                        <FaMapMarkerAlt /> Control de Custodia
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label className={labelClass}>Ubicación Física</label>
                            <input
                                type="text" name="ubicacion"
                                className={inputClass}
                                value={formData.ubicacion} onChange={handleChange}
                                placeholder="Ej: Sede Norte - Oficina Gerencia"
                            />
                        </div>
                        <div>
                            <label className={labelClass}>Responsable (Custodio)</label>
                            <select
                                name="responsable_id"
                                className={inputClass}
                                value={formData.responsable_id} onChange={handleChange}
                            >
                                <option value="">Sin asignar</option>
                                {terceros.map(t => (
                                    <option key={t.id} value={t.id}>{t.razon_social} ({t.numero_identificacion})</option>
                                ))}
                            </select>
                        </div>
                    </div>
                </div>

                {/* SECCIÓN 3: VALORES */}
                <div className="mb-8">
                    <h2 className="text-lg font-bold text-blue-600 mb-4 border-b pb-2 flex items-center gap-2">
                        <FaDollarSign /> Valores y Adquisición
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div>
                            <label className={labelClass}><FaCalendarAlt className="inline mr-1" /> Fecha de Compra</label>
                            <input
                                type="date" name="fecha_compra" required
                                className={inputClass}
                                value={formData.fecha_compra} onChange={handleChange}
                            />
                        </div>
                        <div>
                            <label className={labelClass}>Costo de Adquisición</label>
                            <input
                                type="number" name="costo_adquisicion" required
                                className={inputClass}
                                value={formData.costo_adquisicion} onChange={handleChange}
                            />
                        </div>
                        <div>
                            <label className={labelClass}>Valor Residual (Salvamento)</label>
                            <input
                                type="number" name="valor_residual"
                                className={inputClass}
                                value={formData.valor_residual} onChange={handleChange}
                            />
                            <p className="text-xs text-gray-500 mt-1">Valor estimado al final de la vida útil.</p>
                        </div>
                    </div>
                </div>

                <div className="flex justify-end gap-4 pt-4 border-t">
                    <button
                        type="button"
                        onClick={() => router.back()}
                        className="px-6 py-2 text-gray-600 font-semibold hover:bg-gray-100 rounded-lg transition"
                    >
                        Cancelar
                    </button>
                    <button
                        type="submit"
                        disabled={loading}
                        className="bg-blue-600 text-white px-8 py-2 rounded-lg font-bold shadow-md hover:bg-blue-700 transition flex items-center gap-2"
                    >
                        {loading ? 'Guardando...' : <><FaSave /> Guardar Activo</>}
                    </button>
                </div>
            </form>
        </div>
    );
}
