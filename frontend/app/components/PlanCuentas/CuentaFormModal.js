'use client';

import React, { useState, useEffect } from 'react';
import { 
  FaSave, 
  FaTimes, 
  FaHashtag, 
  FaTag, 
  FaFolderOpen, 
  FaCheckCircle, 
  FaSpinner, 
  FaExclamationTriangle,
  FaEdit,
  FaPlus
} from 'react-icons/fa';

// --- ESTILOS REUSABLES (Manual v2.0) ---
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none pl-10";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white pl-10";

export default function CuentaFormModal({
  isOpen,
  onClose,
  onSubmit,
  initialData = {},
  planCuentasFlat,
  title
}) {
  const [formData, setFormData] = useState({
    codigo: '',
    nombre: '',
    permite_movimiento: false,
    cuenta_padre_id: null,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      // Lógica original preservada con Optional Chaining
      setFormData({
        codigo: initialData?.codigo || '',
        nombre: initialData?.nombre || '',
        permite_movimiento: initialData?.permite_movimiento || false,
        cuenta_padre_id: initialData?.cuenta_padre_id || null,
      });
      setError('');
    }
  }, [isOpen, initialData]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    
    const dataToSubmit = {
        ...formData,
        cuenta_padre_id: formData.cuenta_padre_id ? parseInt(formData.cuenta_padre_id, 10) : null,
        nivel: 0 // El backend recalculará el nivel real
    };

    try {
      await onSubmit(dataToSubmit);
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Ocurrió un error al guardar la cuenta.');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  const isEdit = !!initialData?.id;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex justify-center items-center p-4 animate-fadeIn">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md border border-gray-100 transform transition-all scale-100">
        
        {/* HEADER */}
        <div className="flex justify-between items-center p-6 border-b border-gray-100">
            <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                {isEdit ? <FaEdit className="text-indigo-500"/> : <FaPlus className="text-green-500"/>}
                {title || (isEdit ? 'Editar Cuenta' : 'Nueva Cuenta')}
            </h2>
            <button 
                onClick={onClose} 
                className="text-gray-400 hover:text-gray-600 transition-colors text-xl p-1 rounded-full hover:bg-gray-100"
            >
                <FaTimes />
            </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          
          {/* SELECCIÓN DE PADRE */}
          <div>
            <label htmlFor="cuenta_padre_id" className={labelClass}>Cuenta Padre (Ubicación)</label>
            <div className="relative">
                <select 
                    name="cuenta_padre_id" 
                    id="cuenta_padre_id" 
                    value={formData.cuenta_padre_id || ''} 
                    onChange={handleChange} 
                    className={selectClass}
                >
                    <option value="">-- Ninguna (Raíz) --</option>
                    {planCuentasFlat.map(cuenta => (
                    <option key={cuenta.id} value={cuenta.id}>
                        {cuenta.codigo} - {cuenta.nombre}
                    </option>
                    ))}
                </select>
                <FaFolderOpen className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
              {/* CÓDIGO */}
              <div className="col-span-1">
                <label htmlFor="codigo" className={labelClass}>Código <span className="text-red-500">*</span></label>
                <div className="relative">
                    <input 
                        type="text" 
                        name="codigo" 
                        id="codigo" 
                        value={formData.codigo} 
                        onChange={handleChange} 
                        required 
                        className={`${inputClass} font-mono font-bold text-gray-700`}
                        placeholder="Ej: 1105"
                        autoFocus
                    />
                    <FaHashtag className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                </div>
              </div>

              {/* NOMBRE */}
              <div className="col-span-2">
                <label htmlFor="nombre" className={labelClass}>Nombre <span className="text-red-500">*</span></label>
                <div className="relative">
                    <input 
                        type="text" 
                        name="nombre" 
                        id="nombre" 
                        value={formData.nombre} 
                        onChange={handleChange} 
                        required 
                        className={inputClass}
                        placeholder="Ej: Caja General"
                    />
                    <FaTag className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                </div>
              </div>
          </div>

          {/* TIPO DE CUENTA (CHECKBOX CARD) */}
          <div className={`p-4 rounded-lg border flex items-center transition-colors ${formData.permite_movimiento ? 'bg-blue-50 border-blue-200' : 'bg-gray-50 border-gray-200'}`}>
            <input 
                type="checkbox" 
                name="permite_movimiento" 
                id="permite_movimiento" 
                checked={formData.permite_movimiento} 
                onChange={handleChange} 
                className="h-5 w-5 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded cursor-pointer" 
            />
            <div className="ml-3">
                <label htmlFor="permite_movimiento" className="block text-sm font-bold text-gray-900 cursor-pointer">
                    Permite Movimientos (Auxiliar)
                </label>
                <p className="text-xs text-gray-500 mt-0.5">
                    {formData.permite_movimiento 
                        ? "Esta cuenta podrá ser seleccionada en documentos contables." 
                        : "Esta cuenta será un título agrupador (Carpeta)."}
                </p>
            </div>
          </div>

          {/* ERROR */}
          {error && (
              <div className="p-3 bg-red-50 border border-red-100 rounded-lg flex items-center gap-2 text-red-600 text-sm animate-pulse">
                  <FaExclamationTriangle /> {error}
              </div>
          )}

          {/* BOTONES */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
            <button 
                type="button" 
                onClick={onClose} 
                disabled={isLoading} 
                className="px-5 py-2 text-gray-600 hover:bg-gray-100 rounded-lg font-medium transition-colors"
            >
              Cancelar
            </button>
            <button 
                type="submit" 
                disabled={isLoading} 
                className={`
                    px-6 py-2 rounded-lg shadow-md font-bold text-white flex items-center gap-2 transition-transform transform hover:-translate-y-0.5
                    ${isLoading ? 'bg-gray-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'}
                `}
            >
              {isLoading ? <><FaSpinner className="animate-spin"/> Guardando...</> : <><FaSave /> Guardar</>}
            </button>
          </div>

        </form>
      </div>
    </div>
  );
}