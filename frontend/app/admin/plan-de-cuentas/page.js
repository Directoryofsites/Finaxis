// frontend/app/admin/plan-de-cuentas/page.js
'use client';

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/app/context/AuthContext';


// --- Iconos Estándar v2.0 ---
import {
  FaSitemap, FaPlus, FaSearch, FaEdit, FaTrashAlt,
  FaChevronRight, FaFolder, FaFolderOpen, FaLayerGroup, FaBook
} from 'react-icons/fa';

// --- RUTAS DE IMPORTACIÓN DEFINITIVAS ---
import * as planCuentasService from '@/lib/planCuentasService';
import CuentaFormModal from '@/app/components/PlanCuentas/CuentaFormModal';
import ConfirmacionDepuracionModal from '@/app/components/PlanCuentas/ConfirmacionDepuracionModal';
import ImportarPucModal from '@/app/components/PlanCuentas/ImportarPucModal';

// =============================================================================
// 🎨 COMPONENTE DE FILA RECURSIVA (Estilizado v2.0)
// =============================================================================
const RenderCuentaRow = ({ cuenta, nivel = 0, onCrear, onEditar, onEliminar, expandedNodes, onToggleNode }) => {
  const indentacion = { paddingLeft: `${nivel * 2}rem` }; // Mantenemos la lógica de indentación visual
  const esPadre = cuenta.children && cuenta.children.length > 0;
  const isExpanded = expandedNodes.has(cuenta.id);

  return (
    <>
      {/* ID ÚNICO PARA SCROLL AUTOMÁTICO */}
      <tr
        id={`cuenta-row-${cuenta.codigo}`}
        className={`group transition-colors border-b border-gray-100 last:border-0 ${isExpanded ? 'bg-indigo-50/30' : 'hover:bg-gray-50'}`}
      >
        {/* Columna: CÓDIGO (Jerarquía) */}
        <td className="px-4 py-3 whitespace-nowrap">
          <div style={indentacion} className="flex items-center space-x-2">
            {esPadre ? (
              <button
                onClick={() => onToggleNode(cuenta.id)}
                className="p-1 rounded text-indigo-500 hover:bg-indigo-100 focus:outline-none transition-colors"
              >
                <FaChevronRight className={`transform transition-transform duration-200 text-xs ${isExpanded ? 'rotate-90' : ''}`} />
              </button>
            ) : (
              <span className="w-5"></span> // Espaciador alineado
            )}

            {/* Icono de Carpeta Semántico */}
            <span className={`text-sm ${esPadre ? 'text-indigo-400' : 'text-gray-300'}`}>
              {esPadre ? (isExpanded ? <FaFolderOpen /> : <FaFolder />) : <div className="w-3 h-1 bg-gray-200 rounded-full"></div>}
            </span>

            <span
              className={`font-mono text-sm cursor-pointer select-none ${esPadre ? 'font-bold text-indigo-700' : 'text-gray-600 font-medium'}`}
              onClick={() => esPadre && onToggleNode(cuenta.id)}
            >
              {cuenta.codigo}
            </span>
          </div>
        </td>

        {/* Columna: NOMBRE */}
        <td className="px-4 py-3 whitespace-nowrap">
          <span className={`text-sm ${esPadre ? 'font-semibold text-gray-800' : 'text-gray-600'}`}>
            {cuenta.nombre}
          </span>
        </td>

        {/* Columna: NIVEL */}
        <td className="px-4 py-3 text-center">
          <span className="inline-flex items-center justify-center w-6 h-6 text-xs font-bold text-gray-500 bg-gray-100 rounded-full border border-gray-200">
            {cuenta.nivel}
          </span>
        </td>

        {/* Columna: MOVIMIENTO */}
        <td className="px-4 py-3 text-center">
          {cuenta.permite_movimiento ? (
            <span className="px-2 py-0.5 inline-flex text-xs font-bold rounded-md bg-green-50 text-green-700 border border-green-100 tracking-wide uppercase">
              Sí
            </span>
          ) : (
            <span className="px-2 py-0.5 inline-flex text-xs font-bold rounded-md bg-gray-50 text-gray-400 border border-gray-100 tracking-wide uppercase">
              No
            </span>
          )}
        </td>

        {/* Columna: ACCIONES */}
        <td className="px-4 py-3 text-right whitespace-nowrap">
          <div className="flex justify-end items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={() => onCrear(cuenta)}
              className="btn btn-xs btn-ghost text-green-600 hover:bg-green-50 hover:text-green-700 tooltip"
              title="Crear Subcuenta"
            >
              <FaPlus className="text-xs" /> <span className="hidden lg:inline ml-1 font-bold">Sub</span>
            </button>
            <div className="w-px h-4 bg-gray-200 mx-1"></div>
            <button
              onClick={() => onEditar(cuenta)}
              className="btn btn-xs btn-ghost text-indigo-600 hover:bg-indigo-50 hover:text-indigo-700"
              title="Editar"
            >
              <FaEdit />
            </button>
            <button
              onClick={() => onEliminar(cuenta)}
              className="btn btn-xs btn-ghost text-red-500 hover:bg-red-50 hover:text-red-600"
              title="Eliminar"
            >
              <FaTrashAlt />
            </button>
          </div>
        </td>
      </tr>

      {/* Renderizado Recursivo de Hijos */}
      {esPadre && isExpanded && cuenta.children.map(hijo => (
        <RenderCuentaRow
          key={hijo.id}
          cuenta={hijo}
          nivel={nivel + 1}
          onCrear={onCrear}
          onEditar={onEditar}
          onEliminar={onEliminar}
          expandedNodes={expandedNodes}
          onToggleNode={onToggleNode}
        />
      ))}
    </>
  );
};

// =============================================================================
// 📄 PÁGINA PRINCIPAL
// =============================================================================
export default function PlanDeCuentasPage() {
  const { user } = useAuth();

  // Estados de Datos
  const [cuentas, setCuentas] = useState([]);
  const [cuentasFlat, setCuentasFlat] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // Estados de UI y Lógica de Árbol
  const [expandedNodes, setExpandedNodes] = useState(new Set());
  const [searchTerm, setSearchTerm] = useState('');

  // Estados de Modales
  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
  const [cuentaActual, setCuentaActual] = useState(null);
  const [depuracionData, setDepuracionData] = useState(null);
  const [isActionLoading, setIsActionLoading] = useState(false);

  const [modalTitle, setModalTitle] = useState('');
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);

  // --- Carga Inicial ---
  const fetchCuentas = useCallback(async () => {
    if (user) {
      setIsLoading(true);
      setError('');
      try {
        const [resJerarquia, resFlat] = await Promise.all([
          planCuentasService.getPlanCuentas({ limit: 5000 }),
          planCuentasService.getPlanCuentasFlat()
        ]);
        setCuentas(resJerarquia.data);
        setCuentasFlat(resFlat.data);
      } catch (err) {
        console.error(err);
        setError(err.response?.data?.detail || 'No se pudo cargar el plan de cuentas.');
      } finally {
        setIsLoading(false);
      }
    }
  }, [user]);

  useEffect(() => {
    fetchCuentas();
  }, [fetchCuentas]);

  // --- LÓGICA DE BÚSQUEDA INTELIGENTE Y AUTO-EXPANSIÓN ---
  const handleSearchChange = (e) => {
    const term = e.target.value;
    setSearchTerm(term);

    if (term.length >= 4) {
      const cuentaEncontrada = cuentasFlat.find(c => c.codigo.startsWith(term));
      if (cuentaEncontrada) {
        expandirAncestros(cuentaEncontrada);
        setTimeout(() => {
          const element = document.getElementById(`cuenta-row-${cuentaEncontrada.codigo}`);
          if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'center' });
            element.classList.add('bg-yellow-100'); // Highlight temporal
            setTimeout(() => element.classList.remove('bg-yellow-100'), 2000);
          }
        }, 100);
      }
    }
  };

  const expandirAncestros = (cuentaObj) => {
    const nuevosExpandidos = new Set(expandedNodes);
    let currentId = cuentaObj.cuenta_padre_id;
    while (currentId) {
      nuevosExpandidos.add(currentId);
      const padre = cuentasFlat.find(c => c.id === currentId);
      currentId = padre ? padre.cuenta_padre_id : null;
    }
    nuevosExpandidos.add(cuentaObj.id);
    setExpandedNodes(nuevosExpandidos);
  };

  const toggleNode = (id) => {
    const newSet = new Set(expandedNodes);
    if (newSet.has(id)) newSet.delete(id);
    else newSet.add(id);
    setExpandedNodes(newSet);
  };

  // --- HANDLERS DE ACCIÓN ---
  const handleOpenCreateModal = (padre = null) => {
    setModalTitle('Crear Nueva Cuenta');
    if (padre) {
      setCuentaActual({
        initialData: {
          codigo: padre.codigo,
          nombre: '',
          cuenta_padre_id: padre.id,
          permite_movimiento: true
        },
        mode: 'create',
        padreContexto: padre
      });
    } else {
      setCuentaActual({ initialData: null, mode: 'create' });
    }
    setIsFormModalOpen(true);
  };

  const handleOpenEditModal = (cuenta) => {
    setModalTitle(`Editar Cuenta: ${cuenta.codigo}`);
    setCuentaActual({ initialData: cuenta, mode: 'edit' });
    setIsFormModalOpen(true);
  };

  const handleFormSubmit = async (formData) => {
    setError('');
    const { mode, initialData, padreContexto } = cuentaActual;
    try {
      if (mode === 'edit') {
        await planCuentasService.updateCuenta(initialData.id, formData);
      } else {
        await planCuentasService.createCuenta(formData);
        // UX: Mantener foco y expansión en el padre tras crear hijo
        if (padreContexto) {
          const newSet = new Set(expandedNodes);
          newSet.add(padreContexto.id);
          setExpandedNodes(newSet);
          setTimeout(() => {
            const element = document.getElementById(`cuenta-row-${padreContexto.codigo}`);
            if (element) element.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }, 500);
        }
      }
      setIsFormModalOpen(false);
      fetchCuentas();
    } catch (err) {
      throw err;
    }
  };

  const handleDeleteClick = async (cuenta) => {
    setIsActionLoading(true); setError('');
    try {
      const { data } = await planCuentasService.analizarDepuracion(cuenta.id);
      setDepuracionData(data);
      setIsConfirmModalOpen(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al analizar la cuenta.');
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleConfirmDepuracion = async () => {
    setIsActionLoading(true); setError('');
    try {
      const ids = depuracionData.cuentas_a_eliminar.map(c => c.id);
      await planCuentasService.ejecutarDepuracion(ids);
      setIsConfirmModalOpen(false);
      setDepuracionData(null);
      fetchCuentas();
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al ejecutar la depuración.');
    } finally {
      setIsActionLoading(false);
    }
  };

  // --- RENDERIZADO PRINCIPAL ---
  return (
    <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
      <div className="max-w-7xl mx-auto">

        {/* 1. Encabezado */}
        <div className="flex justify-between items-center mb-8">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-indigo-100 text-indigo-600 rounded-xl shadow-sm">
              <FaSitemap className="text-2xl" />
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-3xl font-bold text-gray-800 tracking-tight">Plan de Cuentas</h1>
                <button
                  onClick={() => window.open('/manual/capitulo_1_puc.html', '_blank')}
                  className="flex items-center gap-2 px-2 py-1 bg-white border border-indigo-200 text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors font-medium shadow-sm"
                  title="Ver Manual de Capacitación"
                  type="button"
                >
                  <FaBook /> <span className="hidden md:inline">Manual</span>
                </button>
              </div>
              <p className="text-gray-500 text-sm mt-1">Gestión jerárquica del Plan Único de Cuentas (PUC).</p>
            </div>
          </div>

          {/* Botones de Acción Superior */}
          <div className="flex gap-2">
            <button
              onClick={() => setIsImportModalOpen(true)}
              className="btn btn-ghost text-green-700 bg-green-50 hover:bg-green-100 gap-2 font-bold"
              title="Importar PUC desde JSON"
            >
              <FaPlus className="text-lg" /> Importar
            </button>
          </div>
        </div>

        {/* 2. Barra de Control (Filtro y Acción Principal) */}
        <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 mb-8 animate-fadeIn">
          <div className="flex flex-col md:flex-row gap-4 items-end justify-between">

            {/* Buscador Inteligente */}
            <div className="w-full md:w-96">
              <label htmlFor="search" className="block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide">
                Buscar por Código
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <FaSearch className="text-gray-400" />
                </div>
                <input
                  type="text" id="search"
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none"
                  placeholder="Ej: 1105..."
                  value={searchTerm}
                  onChange={handleSearchChange}
                  autoComplete="off"
                />
              </div>
            </div>

            {/* Botón Acción Principal */}
            <button
              onClick={() => handleOpenCreateModal()}
              className="w-full md:w-auto btn btn-primary bg-indigo-600 hover:bg-indigo-700 text-white shadow-md rounded-lg font-bold px-6 border-0"
            >
              <FaPlus className="mr-2" /> Cuenta Raíz
            </button>
          </div>
        </div>

        {/* 3. Alertas de Error */}
        {error && (
          <div className="alert alert-error shadow-lg mb-6 rounded-xl text-white">
            <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            <span>{error}</span>
          </div>
        )}

        {/* 4. Tabla Jerárquica */}
        <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden animate-slideDown">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-100 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider w-[35%]">
                    <div className="flex items-center gap-2"><FaLayerGroup /> Código Jerárquico</div>
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase tracking-wider w-[35%]">Nombre Cuenta</th>
                  <th className="px-4 py-3 text-center text-xs font-bold text-gray-600 uppercase tracking-wider w-[10%]">Nivel</th>
                  <th className="px-4 py-3 text-center text-xs font-bold text-gray-600 uppercase tracking-wider w-[10%]">Mov</th>
                  <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase tracking-wider w-[10%]">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50 bg-white">
                {isLoading ? (
                  <tr>
                    <td colSpan="5" className="py-20 text-center">
                      <div className="flex flex-col items-center justify-center text-indigo-500">
                        <span className="loading loading-spinner loading-lg mb-4"></span>
                        <span className="text-sm font-semibold text-gray-500">Construyendo árbol contable...</span>
                      </div>
                    </td>
                  </tr>
                ) : (
                  cuentas.map(cuenta => (
                    <RenderCuentaRow
                      key={cuenta.id}
                      cuenta={cuenta}
                      onCrear={handleOpenCreateModal}
                      onEditar={handleOpenEditModal}
                      onEliminar={handleDeleteClick}
                      expandedNodes={expandedNodes}
                      onToggleNode={toggleNode}
                    />
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Footer Informativo */}
          {!isLoading && cuentas.length > 0 && (
            <div className="bg-gray-50 px-6 py-3 border-t border-gray-200 text-xs text-gray-500 text-right">
              Mostrando {cuentasFlat.length} cuentas en total.
            </div>
          )}
        </div>
      </div>

      <CuentaFormModal
        isOpen={isFormModalOpen}
        onClose={() => setIsFormModalOpen(false)}
        onSubmit={handleFormSubmit}
        initialData={cuentaActual?.initialData}
        planCuentasFlat={cuentasFlat}
        title={modalTitle}
      />

      <ConfirmacionDepuracionModal
        isOpen={isConfirmModalOpen}
        onClose={() => setIsConfirmModalOpen(false)}
        onConfirm={handleConfirmDepuracion}
        analysisData={depuracionData}
        isLoading={isActionLoading}
      />

      {/* --- NUEVO IMPORTADOR INTELIGENTE (SOLICITUD ACTIVOS FIJOS/PUC) --- */}
      <ImportarPucModal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        onImportComplete={() => {
          fetchCuentas(); // Recargar tras importar
        }}
      />
    </div>
  );
}