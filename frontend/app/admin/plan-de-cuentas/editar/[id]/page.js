'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
// 1. IMPORTACIONES CORREGIDAS Y AÑADIDAS


import { useAuth } from '../../../../context/AuthContext';
import { apiService } from '../../../../../lib/apiService';

const funcionesEspeciales = [
  { value: '', label: 'Ninguna (Cuenta estándar)' },
  { value: 'CUENTA_CARTERA', label: 'Cuenta de Cartera (Clientes)' },
  { value: 'CUENTA_PROVEEDORES', label: 'Cuenta de Proveedores' },
  { value: 'CUENTA_BANCARIA', label: 'Cuenta Bancaria (Tesorería)' },
  { value: 'CUENTA_IVA_GENERADO', label: 'IVA Generado' },
  { value: 'CUENTA_IVA_DESCONTABLE', label: 'IVA Descontable' },
  { value: 'CUENTA_RETENCION_FUENTE', label: 'Retención en la Fuente' },
  { value: 'CIERRE_EJERCICIO', label: 'Cierre del Ejercicio' },
  { value: 'CUENTA_INVENTARIO', label: 'Cuenta de Inventario' },
  { value: 'CUENTA_COSTO_VENTA', label: 'Costo de Venta' },
];

export default function EditarCuentaPage() {
  const router = useRouter();
  const params = useParams();
  const { id } = params;
  const { user } = useAuth(); // 2. Usamos el contexto de autenticación

  const [formData, setFormData] = useState({
    nombre: '',
    nivel: 1,
    permite_movimiento: false,
    funcion_especial: ''
  });
  const [codigo, setCodigo] = useState(''); // El código se maneja por separado
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // 3. useEffect ACTUALIZADO para usar apiService
  useEffect(() => {
    if (id && user) { // Solo se ejecuta si hay un ID y un usuario
      const fetchCuenta = async () => {
        setIsLoading(true);
        try {
          // Usamos apiService, la autenticación es automática
          const response = await apiService.get(`/plan-cuentas/${id}`);
          const data = response.data;
          setFormData({
            nombre: data.nombre,
            nivel: data.nivel,
            permite_movimiento: data.permite_movimiento,
            funcion_especial: data.funcion_especial || ''
          });
          setCodigo(data.codigo); // Guardamos el código para mostrarlo
        } catch (err) {
          setError(err.response?.data?.detail || 'No se pudo encontrar la cuenta para editar.');
        } finally {
          setIsLoading(false);
        }
      };
      fetchCuenta();
    }
  }, [id, user]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prevState => ({
      ...prevState,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  // 4. handleSubmit ACTUALIZADO para usar apiService
  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    // Creamos el payload con los tipos de datos correctos
    const updateData = {
      ...formData,
      nivel: parseInt(formData.nivel, 10),
      funcion_especial: formData.funcion_especial || null
    };

    try {
      // Usamos apiService para la petición PUT
      await apiService.put(`/plan-cuentas/${id}`, updateData);
      router.push('/admin/plan-de-cuentas');
    } catch (err) {
      setError(err.response?.data?.detail || 'Ocurrió un error al actualizar la cuenta.');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <div className="text-center mt-10">Cargando datos de la cuenta...</div>;
  }

  if (error) {
    return <div className="text-center mt-10 text-red-500">Error: {error}</div>;
  }

  return (
    <div className="container mx-auto p-4 max-w-2xl">
      <h1 className="text-2xl font-bold mb-4">Editar Cuenta Contable</h1>

      <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow-md space-y-4">
        <div>
          <label htmlFor="codigo" className="block text-sm font-medium text-gray-700">Código de la Cuenta (No editable)</label>
          <input
            type="text"
            name="codigo"
            id="codigo"
            disabled
            value={codigo} // Mostramos el código desde su propio estado
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-100"
          />
        </div>

        <div>
          <label htmlFor="nombre" className="block text-sm font-medium text-gray-700">Nombre de la Cuenta</label>
          <input
            type="text"
            name="nombre"
            id="nombre"
            required
            value={formData.nombre}
            onChange={handleChange}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>

        <div>
          <label htmlFor="nivel" className="block text-sm font-medium text-gray-700">Nivel</label>
          <input
            type="number"
            name="nivel"
            id="nivel"
            min="1"
            required
            value={formData.nivel}
            onChange={handleChange}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>

        <div>
          <label htmlFor="funcion_especial" className="block text-sm font-medium text-gray-700">Función Especial</label>
          <select
            name="funcion_especial"
            id="funcion_especial"
            value={formData.funcion_especial}
            onChange={handleChange}
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
          >
            {funcionesEspeciales.map(func => (
              <option key={func.value} value={func.value}>{func.label}</option>
            ))}
          </select>
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            name="permite_movimiento"
            id="permite_movimiento"
            checked={formData.permite_movimiento}
            onChange={handleChange}
            className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
          />
          <label htmlFor="permite_movimiento" className="ml-2 block text-sm text-gray-900">Permite Movimiento (Cuenta Auxiliar)</label>
        </div>

        {error && <p className="text-red-500 text-sm">{error}</p>}

        <div className="text-right">
          <button
            type="submit"
            disabled={isLoading}
            className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-indigo-300"
          >
            {isLoading ? 'Guardando Cambios...' : 'Guardar Cambios'}
          </button>
        </div>
      </form>
    </div>
  );
}