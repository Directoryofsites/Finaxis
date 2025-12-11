'use client';

import React, { useState } from 'react';
import { FaBook } from 'react-icons/fa';
// --- INICIO: CORRECCIÓN DE IMPORTACIÓN ---
// Nos aseguramos de importar la función desde el servicio de SOPORTE.
import { crearEmpresaConUsuarios } from '@/lib/soporteApiService';
// --- FIN: CORRECCIÓN DE IMPORTACIÓN ---

export default function CrearEmpresaPanel() {
  const [empresaData, setEmpresaData] = useState({
    razon_social: '',
    nit: '',
    fecha_inicio_operaciones: '',
  });

  const [usuarios, setUsuarios] = useState([
    { email: '', password: '' }
  ]);

  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleEmpresaChange = (e) => {
    setEmpresaData({ ...empresaData, [e.target.name]: e.target.value });
  };

  const handleUsuarioChange = (index, e) => {
    const newUsuarios = [...usuarios];
    newUsuarios[index][e.target.name] = e.target.value;
    setUsuarios(newUsuarios);
  };

  const addUsuario = () => {
    setUsuarios([...usuarios, { email: '', password: '' }]);
  };

  const removeUsuario = (index) => {
    const newUsuarios = usuarios.filter((_, i) => i !== index);
    setUsuarios(newUsuarios);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsProcessing(true);
    setError('');
    setSuccess('');

    if (!empresaData.razon_social || !empresaData.nit || !empresaData.fecha_inicio_operaciones) {
      setError('Por favor, complete todos los datos de la empresa.');
      setIsProcessing(false);
      return;
    }

    if (usuarios.some(u => !u.email || !u.password || u.password.length < 6)) {
      setError('Por favor, complete todos los campos para cada usuario. La contraseña debe tener al menos 6 caracteres.');
      setIsProcessing(false);
      return;
    }

    const payload = { ...empresaData, usuarios };

    try {
      const response = await crearEmpresaConUsuarios(payload);

      setSuccess(`¡Empresa "${response.data.razon_social}" y sus usuarios creados exitosamente!`);
      setEmpresaData({ razon_social: '', nit: '', fecha_inicio_operaciones: '' });
      setUsuarios([{ email: '', password: '' }]);

    } catch (err) {
      setError(err.response?.data?.detail || 'Ocurrió un error al crear la empresa.');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-gray-800">Crear Nueva Empresa y Usuarios</h2>
        <button
          onClick={() => window.open('/manual/capitulo_15_crear_empresa.html', '_blank')}
          className="text-indigo-600 hover:bg-indigo-50 px-3 py-1 rounded-md flex items-center gap-2 transition-colors"
          title="Ver Manual de Usuario"
        >
          <FaBook className="text-lg" /> <span className="font-bold text-sm">Manual</span>
        </button>
      </div>
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* El JSX del formulario se mantiene igual */}
        <div className="p-4 border rounded-md space-y-4">
          <h3 className="font-medium text-gray-700">Datos de la Empresa</h3>
          <div>
            <label className="block text-sm font-medium text-gray-600">Razón Social</label>
            <input type="text" name="razon_social" value={empresaData.razon_social} onChange={handleEmpresaChange} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm" required />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-600">NIT</label>
              <input type="text" name="nit" value={empresaData.nit} onChange={handleEmpresaChange} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-600">Fecha Inicio de Operaciones</label>
              <input type="date" name="fecha_inicio_operaciones" value={empresaData.fecha_inicio_operaciones} onChange={handleEmpresaChange} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm" required />
            </div>
          </div>
        </div>

        {usuarios.map((usuario, index) => (
          <div key={index} className="p-4 border rounded-md relative space-y-4">
            <h3 className="font-medium text-gray-700">Usuario Administrador #{index + 1}</h3>
            {usuarios.length > 1 && (
              <button type="button" onClick={() => removeUsuario(index)} className="absolute top-2 right-2 text-red-500 hover:text-red-700 font-bold text-lg">
                &times;
              </button>
            )}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-600">Email</label>
                <input type="email" name="email" value={usuario.email} onChange={(e) => handleUsuarioChange(index, e)} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm" required />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-600">Contraseña (mínimo 6 caracteres)</label>
                <input type="password" name="password" value={usuario.password} onChange={(e) => handleUsuarioChange(index, e)} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm" required />
              </div>
            </div>
          </div>
        ))}

        <button type="button" onClick={addUsuario} className="text-sm text-indigo-600 hover:text-indigo-800 font-medium">
          + Añadir otro usuario
        </button>

        <div className="pt-4">
          {error && <p className="text-red-600 bg-red-100 p-3 rounded-md mb-4">{error}</p>}
          {success && <p className="text-green-600 bg-green-100 p-3 rounded-md mb-4">{success}</p>}
          <button type="submit" disabled={isProcessing} className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400">
            {isProcessing ? 'Creando empresa...' : 'Crear Empresa y Usuarios'}
          </button>
        </div>
      </form>
    </div>
  );
}