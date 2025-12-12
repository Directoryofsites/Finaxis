'use client';
import React, { useState, useEffect } from 'react';
import { apiService } from '../../../lib/apiService';
import { FaPlus, FaCog, FaEdit, FaFileDownload, FaCalculator } from 'react-icons/fa';
import BotonRegresar from '../../components/BotonRegresar';

export default function CategoriasActivosPage() {
    const [categorias, setCategorias] = useState([]);
    const [cuentas, setCuentas] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [editingCategoria, setEditingCategoria] = useState(null);

    const [formData, setFormData] = useState({
        nombre: '',
        vida_util_niif_meses: 60,
        vida_util_fiscal_meses: 60,
        metodo_depreciacion: 'LINEA_RECTA',
        cuenta_activo_id: '',
        cuenta_gasto_depreciacion_id: '',
        cuenta_depreciacion_acumulada_id: ''
    });

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [resCat, resCuentas] = await Promise.all([
                apiService.get('/activos/categorias'),
                apiService.get('/plan-cuentas/')
            ]);
            setCategorias(resCat.data);
            setCuentas(resCuentas.data);
        } catch (error) {
            console.error("Error cargando datos:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const dataToSend = { ...formData };
            
            // Convertir campos vacíos a null
            ['cuenta_activo_id', 'cuenta_gasto_depreciacion_id', 'cuenta_depreciacion_acumulada_id'].forEach(field => {
                if (dataToSend[field] === '') dataToSend[field] = null;
                else if (dataToSend[field]) dataToSend[field] = parseInt(dataToSend[field]);
            });
            
            dataToSend.vida_util_niif_meses = parseInt(dataToSend.vida_util_niif_meses);
            dataToSend.vida_util_fiscal_meses = parseInt(dataToSend.vida_util_fiscal_meses);

            if (editingCategoria) {
                await apiService.put(`/activos/categorias/${editingCategoria.id}`, dataToSend);
            } else {
                await apiService.post('/activos/categorias', dataToSend);
            }
            
            setShowModal(false);
            setEditingCategoria(null);
            resetForm();
            loadData();
            alert('Categoría guardada exitosamente.');
        } catch (error) {
            console.error(error);
            alert('Error al guardar: ' + (error.response?.data?.detail || error.message));
        }
    };

    const resetForm = () => {
        setFormData({
            nombre: '',
            vida_util_niif_meses: 60,
            vida_util_fiscal_meses: 60,
            metodo_depreciacion: 'LINEA_RECTA',
            cuenta_activo_id: '',
            cuenta_gasto_depreciacion_id: '',
            cuenta_depreciacion_acumulada_id: ''
        });
    };

    const handleEdit = (categoria) => {
        setEditingCategoria(categoria);
        setFormData({
            nombre: categoria.nombre,
            vida_util_niif_meses: categoria.vida_util_niif_meses,
            vida_util_fiscal_meses: categoria.vida_util_fiscal_meses,
            metodo_depreciacion: categoria.metodo_depreciacion,
            cuenta_activo_id: categoria.cuenta_activo_id || '',
            cuenta_gasto_depreciacion_id: categoria.cuenta_gasto_depreciacion_id || '',
            cuenta_depreciacion_acumulada_id: categoria.cuenta_depreciacion_acumulada_id || ''
        });
        setShowModal(true);
    };

    const ejecutarDepreciacion = async () => {
        const anio = new Date().getFullYear();
        const mes = new Date().getMonth() + 1;
        
        const tipoDocId = prompt('Ingrese el ID del tipo de documento para depreciación:');
        if (!tipoDocId) return;
        
        try {
            const response = await apiService.post('/activos/depreciar', {
                anio: anio,
                mes: mes,
                tipo_documento_id: parseInt(tipoDocId)
            });
            
            alert(`Depreciación ejecutada exitosamente. Documento: ${response.data.numero}`);
            
            // Descargar PDF automáticamente
            window.open(`/api/activos/reportes/depreciacion-pdf?anio=${anio}&mes=${mes}`, '_blank');
        } catch (error) {
            console.error(error);
            alert('Error en depreciación: ' + (error.response?.data?.detail || error.message));
        }
    };

    const descargarReporteMaestro = () => {
        window.open('/api/activos/reportes/maestro-pdf', '_blank');
    };

    const inputClass = "w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2";
    const labelClass = "block text-sm font-medium text-gray-700 mb-1";

    if (loading) return <div className="p-6">Cargando...</div>;

    return (
        <div className="p-6">
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-4">
                    <BotonRegresar href="/activos" />
                    <h1 className="text-2xl font-bold text-gray-800">Categorías de Activos Fijos</h1>
                </div>
                
                <div className="flex gap-2">
                    <button
                        onClick={descargarReporteMaestro}
                        className="bg-green-600 text-white px-4 py-2 rounded-lg font-semibold shadow-md hover:bg-green-700 transition flex items-center gap-2"
                    >
                        <FaFileDownload /> Reporte PDF
                    </button>
                    <button
                        onClick={ejecutarDepreciacion}
                        className="bg-orange-600 text-white px-4 py-2 rounded-lg font-semibold shadow-md hover:bg-orange-700 transition flex items-center gap-2"
                    >
                        <FaCalculator /> Ejecutar Depreciación
                    </button>
                    <button
                        onClick={() => setShowModal(true)}
                        className="bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold shadow-md hover:bg-blue-700 transition flex items-center gap-2"
                    >
                        <FaPlus /> Nueva Categoría
                    </button>
                </div>
            </div>

            {/* Tabla de categorías */}
            <div className="bg-white shadow-lg rounded-xl overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Vida Útil (Meses)</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Método</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Configuración Contable</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {categorias.map((categoria) => {
                            const configuracionCompleta = categoria.cuenta_activo_id && 
                                                        categoria.cuenta_gasto_depreciacion_id && 
                                                        categoria.cuenta_depreciacion_acumulada_id;
                            
                            return (
                                <tr key={categoria.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                        {categoria.nombre}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        NIIF: {categoria.vida_util_niif_meses} | Fiscal: {categoria.vida_util_fiscal_meses}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {categoria.metodo_depreciacion.replace('_', ' ')}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                            configuracionCompleta 
                                                ? 'bg-green-100 text-green-800' 
                                                : 'bg-red-100 text-red-800'
                                        }`}>
                                            {configuracionCompleta ? 'Completa' : 'Incompleta'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                        <button
                                            onClick={() => handleEdit(categoria)}
                                            className="text-blue-600 hover:text-blue-900 flex items-center gap-1"
                                        >
                                            <FaEdit /> Editar
                                        </button>
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>

            {/* Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
                    <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-2xl shadow-lg rounded-md bg-white">
                        <h3 className="text-lg font-bold text-gray-900 mb-4">
                            {editingCategoria ? 'Editar Categoría' : 'Nueva Categoría'}
                        </h3>
                        
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className={labelClass}>Nombre de la Categoría *</label>
                                <input
                                    type="text"
                                    required
                                    className={inputClass}
                                    value={formData.nombre}
                                    onChange={(e) => setFormData({...formData, nombre: e.target.value})}
                                    placeholder="Ej: Equipos de Oficina"
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className={labelClass}>Vida Útil NIIF (Meses) *</label>
                                    <input
                                        type="number"
                                        required
                                        min="1"
                                        className={inputClass}
                                        value={formData.vida_util_niif_meses}
                                        onChange={(e) => setFormData({...formData, vida_util_niif_meses: e.target.value})}
                                    />
                                </div>
                                <div>
                                    <label className={labelClass}>Vida Útil Fiscal (Meses) *</label>
                                    <input
                                        type="number"
                                        required
                                        min="1"
                                        className={inputClass}
                                        value={formData.vida_util_fiscal_meses}
                                        onChange={(e) => setFormData({...formData, vida_util_fiscal_meses: e.target.value})}
                                    />
                                </div>
                            </div>

                            <div>
                                <label className={labelClass}>Método de Depreciación *</label>
                                <select
                                    required
                                    className={inputClass}
                                    value={formData.metodo_depreciacion}
                                    onChange={(e) => setFormData({...formData, metodo_depreciacion: e.target.value})}
                                >
                                    <option value="LINEA_RECTA">Línea Recta</option>
                                    <option value="REDUCCION_SALDOS">Reducción de Saldos</option>
                                    <option value="UNIDADES_PRODUCCION">Unidades de Producción</option>
                                    <option value="NO_DEPRECIAR">No Depreciar</option>
                                </select>
                            </div>

                            <div className="border-t pt-4">
                                <h4 className="font-semibold text-gray-700 mb-3">Configuración Contable</h4>
                                
                                <div className="space-y-3">
                                    <div>
                                        <label className={labelClass}>Cuenta del Activo (15xx)</label>
                                        <select
                                            className={inputClass}
                                            value={formData.cuenta_activo_id}
                                            onChange={(e) => setFormData({...formData, cuenta_activo_id: e.target.value})}
                                        >
                                            <option value="">Seleccione...</option>
                                            {cuentas.filter(c => c.codigo.startsWith('15')).map(cuenta => (
                                                <option key={cuenta.id} value={cuenta.id}>
                                                    {cuenta.codigo} - {cuenta.nombre}
                                                </option>
                                            ))}
                                        </select>
                                    </div>

                                    <div>
                                        <label className={labelClass}>Cuenta Gasto Depreciación (51xx)</label>
                                        <select
                                            className={inputClass}
                                            value={formData.cuenta_gasto_depreciacion_id}
                                            onChange={(e) => setFormData({...formData, cuenta_gasto_depreciacion_id: e.target.value})}
                                        >
                                            <option value="">Seleccione...</option>
                                            {cuentas.filter(c => c.codigo.startsWith('51')).map(cuenta => (
                                                <option key={cuenta.id} value={cuenta.id}>
                                                    {cuenta.codigo} - {cuenta.nombre}
                                                </option>
                                            ))}
                                        </select>
                                    </div>

                                    <div>
                                        <label className={labelClass}>Cuenta Depreciación Acumulada (1592xx)</label>
                                        <select
                                            className={inputClass}
                                            value={formData.cuenta_depreciacion_acumulada_id}
                                            onChange={(e) => setFormData({...formData, cuenta_depreciacion_acumulada_id: e.target.value})}
                                        >
                                            <option value="">Seleccione...</option>
                                            {cuentas.filter(c => c.codigo.startsWith('159')).map(cuenta => (
                                                <option key={cuenta.id} value={cuenta.id}>
                                                    {cuenta.codigo} - {cuenta.nombre}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                </div>
                            </div>

                            <div className="flex justify-end gap-3 pt-4 border-t">
                                <button
                                    type="button"
                                    onClick={() => {
                                        setShowModal(false);
                                        setEditingCategoria(null);
                                        resetForm();
                                    }}
                                    className="px-4 py-2 text-gray-600 font-semibold hover:bg-gray-100 rounded-lg transition"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    className="bg-blue-600 text-white px-6 py-2 rounded-lg font-bold shadow-md hover:bg-blue-700 transition"
                                >
                                    Guardar
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}