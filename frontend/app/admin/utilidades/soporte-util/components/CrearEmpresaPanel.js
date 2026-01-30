'use client';

import React, { useState } from 'react';
import { FaBook, FaCopy } from 'react-icons/fa';
// --- INICIO: CORRECCIÓN DE IMPORTACIÓN ---
// Nos aseguramos de importar la función desde el servicio de SOPORTE.
import { crearEmpresaConUsuarios, getRoles, searchEmpresas, createEmpresaFromTemplate } from '@/lib/soporteApiService';
// --- FIN: CORRECCIÓN DE IMPORTACIÓN ---

export default function CrearEmpresaPanel() {
  const [empresaData, setEmpresaData] = useState({
    razon_social: '',
    nit: '',
    fecha_inicio_operaciones: '',
    // Nuevo estado para el Modo Clon
    modo_operacion: 'STANDARD',
    rol_inicial_id: '', // Nuevo campo para selección manual de rol
  });

  // --- NUEVO ESTADO: PLANTILLAS ---
  const [plantillas, setPlantillas] = useState([]);
  const [selectedTemplateCategory, setSelectedTemplateCategory] = useState(''); // Si tiene valor, usamos creación por plantilla

  const [rolesDisponibles, setRolesDisponibles] = useState([]);

  // Cargar roles y plantillas al montar el componente
  React.useEffect(() => {
    const cargarDatos = async () => {
      try {
        // 1. Obtener roles globales
        const responseRoles = await getRoles(null);
        setRolesDisponibles(responseRoles.data);

        // 2. Obtener Plantillas Disponibles
        // Usamos el servicio de búsqueda filtrando por type_filter='PLANTILLA'
        const responseTemplates = await searchEmpresas({ type_filter: 'PLANTILLA', size: 100 }); // Traemos todas (limit 100)
        setPlantillas(responseTemplates.data.items);
      } catch (error) {
        console.error("Error al cargar datos iniciales:", error);
      }
    };
    cargarDatos();
  }, []);

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

    try {
      let response;
      const basePayload = { ...empresaData, usuarios };

      if (selectedTemplateCategory) {
        // --- FLUJO: CREACIÓN DESDE PLANTILLA ---
        const templatePayload = {
          empresa_data: basePayload,
          template_category: selectedTemplateCategory,
          owner_id: null // Por ahora null, o podríamos asignar el usuario actual si fuera contador
        };
        response = await createEmpresaFromTemplate(templatePayload);
        setSuccess(`¡Empresa "${response.data.razon_social}" creada desde PLANTILLA exitosamente! (PUC y Documentos copiados)`);
      } else {
        // --- FLUJO: CREACIÓN STANDARD ---
        response = await crearEmpresaConUsuarios(basePayload);
        setSuccess(`¡Empresa "${response.data.razon_social}" creada exitosamente!`);
      }

      setEmpresaData({ razon_social: '', nit: '', fecha_inicio_operaciones: '', modo_operacion: 'STANDARD', rol_inicial_id: '' });
      setUsuarios([{ email: '', password: '' }]);
      setSelectedTemplateCategory(''); // Reset selector

    } catch (err) {
      setError(err.response?.data?.detail || 'Ocurrió un error al crear la empresa.');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-gray-800">Crear Nueva Empresa</h2>
        <button
          onClick={() => window.open('/manual/capitulo_15_crear_empresa.html', '_blank')}
          className="text-indigo-600 hover:bg-indigo-50 px-3 py-1 rounded-md flex items-center gap-2 transition-colors"
          title="Ver Manual de Usuario"
        >
          <FaBook className="text-lg" /> <span className="font-bold text-sm">Manual</span>
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">

        {/* --- NUEVO: SELECTOR DE PLANTILLA --- */}
        <div className={`p-4 border-2 rounded-md transition-colors ${selectedTemplateCategory ? 'border-purple-300 bg-purple-50' : 'border-gray-200 bg-gray-50'}`}>
          <div className="flex items-start gap-3">
            <FaCopy className={`text-2xl mt-1 ${selectedTemplateCategory ? 'text-purple-600' : 'text-gray-400'}`} />
            <div className="flex-1">
              <label className="block text-sm font-bold text-gray-700 mb-1">
                ¿Basar en una Plantilla? (Recomendado)
              </label>
              <p className="text-xs text-gray-500 mb-3">
                Si seleccionas una plantilla, la nueva empresa copiará automáticamen el Plan de Cuentas (PUC),
                Tipos de Documento e Impuestos de la plantilla seleccionada.
              </p>
              <select
                value={selectedTemplateCategory}
                onChange={(e) => setSelectedTemplateCategory(e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-purple-500 focus:border-purple-500"
              >
                <option value="">-- No usar plantilla (Empresa en Blanco) --</option>
                {plantillas.map(t => (
                  <option key={t.id} value={t.template_category || 'DEFAULT'}>
                    📂 {t.razon_social} ({t.template_category || 'Sin Categoría'})
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>


        <div className="p-4 border rounded-md space-y-4">
          <h3 className="font-medium text-gray-700">Datos Básicos</h3>
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

        {/* Nuevo Control para Modo Auditoría */}
        <div className="flex items-center mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
          <div className="flex items-center h-5">
            <input
              id="modo_operacion"
              name="modo_operacion"
              type="checkbox"
              checked={empresaData.modo_operacion === 'AUDITORIA_READONLY'}
              onChange={(e) => setEmpresaData({ ...empresaData, modo_operacion: e.target.checked ? 'AUDITORIA_READONLY' : 'STANDARD' })}
              className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded cursor-pointer"
            />
          </div>
          <div className="ml-3 text-sm">
            <label htmlFor="modo_operacion" className="font-medium text-gray-700 cursor-pointer select-none">
              Activar Modo Auditoría / Clon (Restringido)
            </label>
            <p className="text-gray-500 text-xs mt-1">
              Si se activa, esta empresa <strong>NO podrá crear nuevos documentos</strong>. Solo permitirá importar datos históricos para análisis y simulación. Ideal para NIIF o proyecciones.
            </p>
          </div>
        </div>
        {/* Fin Control */}

        {/* --- NUEVO: Selector de Rol Inicial --- */}
        <div className="p-4 border border-blue-200 rounded-md bg-blue-50">
          <h3 className="font-medium text-blue-800 mb-2">Asignación de Rol Inicial</h3>
          <p className="text-sm text-blue-600 mb-2">
            Selecciona el rol que tendrá el usuario administrador inicial.
            Si seleccionas una opción, esta <strong>prevalecerá</strong> sobre cualquier configuración automática del "Modo Auditoría".
          </p>
          <label className="block text-sm font-medium text-gray-700">Rol del Usuario Admin</label>
          <select
            name="rol_inicial_id"
            value={empresaData.rol_inicial_id}
            onChange={handleEmpresaChange}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-white"
          >
            <option value="">-- Automático (Según Modo Operación) --</option>
            {rolesDisponibles.map(rol => (
              <option key={rol.id} value={rol.id}>
                {rol.nombre} {rol.descripcion ? `(${rol.descripcion})` : ''}
              </option>
            ))}
          </select>
        </div>
        {/* --- Fin Selector --- */}

        {
          usuarios.map((usuario, index) => (
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
          ))
        }

        <button type="button" onClick={addUsuario} className="text-sm text-indigo-600 hover:text-indigo-800 font-medium">
          + Añadir otro usuario
        </button>

        <div className="pt-4">
          {error && <p className="text-red-600 bg-red-100 p-3 rounded-md mb-4">{error}</p>}
          {success && <p className="text-green-600 bg-green-100 p-3 rounded-md mb-4">{success}</p>}
          <button type="submit" disabled={isProcessing} className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400">
            {isProcessing ? 'Creando empresa...' : (
              selectedTemplateCategory ? 'Crear desde Plantilla' : 'Crear Empresa y Usuarios'
            )}
          </button>
        </div>
      </form >
    </div >
  );
}