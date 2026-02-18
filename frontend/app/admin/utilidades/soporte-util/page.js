'use client';
import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'next/navigation';
import { FaBook } from 'react-icons/fa';


import {
    soporteApiService,
    setSoporteAuthToken,
    getDashboardData,
    deleteEmpresa,
    updateEmpresa,
    createUserForCompany,
    createSoporteUser,
    updateSoporteUserPassword,
    getRoles,
    deleteUser,
    updateUser,
    convertirEnPlantilla,
    searchEmpresas,
    getAccountants
} from '@/lib/soporteApiService';

import ConteoRegistros from './components/ConteoRegistros';
import BuscadorPorLlaveNatural from './components/BuscadorPorLlaveNatural';
import InspectorMaestros from './components/InspectorMaestros';
import ErradicadorUniversal from './components/ErradicadorUniversal';
import CrearEmpresaPanel from './components/CrearEmpresaPanel';
import InspectorUniversal from './components/InspectorUniversal';
import UltimasOperaciones from './components/UltimasOperaciones';
import AuditoriaConsecutivosSoporte from './components/AuditoriaConsecutivosSoporte';
import ResetConsumoPanel from './components/ResetConsumoPanel';
import RolesManagementView from '../../../../components/admin/RolesManagementView';


// ... (Aquí van todos los componentes hijos que ya tienes en tu archivo, 
//      FormularioEditarEmpresa, PanelGestionUsuarios, etc. No cambian.)
function FormularioEditarEmpresa({ empresa, onFinished, onCancel }) {
    const [formData, setFormData] = useState({
        razon_social: '',
        nit: '',
        fecha_inicio_operaciones: '',
        is_lite_mode: false,
        saldo_facturas_venta: 0,
        saldo_documentos_soporte: 0,
        saldo_notas_credito: 0
    });
    const [mensaje, setMensaje] = useState({ texto: '', tipo: '' });
    const [isProcessing, setIsProcessing] = useState(false);

    useEffect(() => {
        if (empresa) {
            const fechaFormateada = empresa.fecha_inicio_operaciones
                ? empresa.fecha_inicio_operaciones.split('T')[0]
                : '';
            setFormData({
                razon_social: empresa.razon_social || '',
                nit: empresa.nit || '',
                fecha_inicio_operaciones: fechaFormateada,
                is_lite_mode: empresa.is_lite_mode || false,
                saldo_facturas_venta: empresa.saldo_facturas_venta || 0,
                saldo_documentos_soporte: empresa.saldo_documentos_soporte || 0,
                saldo_notas_credito: empresa.saldo_notas_credito || 0
            });
        }
    }, [empresa]);

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsProcessing(true);
        setMensaje({ texto: '', tipo: '' });
        try {
            const empresaActualizada = await updateEmpresa(empresa.id, formData);
            setMensaje({ texto: 'Empresa actualizada con éxito.', tipo: 'success' });
            onFinished(empresaActualizada.data);
        } catch (error) {
            const errorMsg = error.response?.data?.detail || 'Error al actualizar la empresa.';
            setMensaje({ texto: errorMsg, tipo: 'error' });
        } finally {
            setIsProcessing(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            {mensaje.texto && <p className={`p-2 rounded-md text-sm ${mensaje.tipo === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>{mensaje.texto}</p>}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700">Razón Social</label>
                    <input type="text" name="razon_social" value={formData.razon_social} onChange={handleChange} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm" />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700">NIT</label>
                    <input type="text" name="nit" value={formData.nit} onChange={handleChange} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm" />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700">Fecha Inicio Ops</label>
                    <input type="date" name="fecha_inicio_operaciones" value={formData.fecha_inicio_operaciones} onChange={handleChange} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm" />
                </div>
            </div>

            {/* --- SECCIÓN MODO LITE / PAQUETES --- */}
            <div className="bg-blue-50 p-4 rounded-md border border-blue-100">
                <h4 className="text-sm font-bold text-blue-800 mb-3 border-b border-blue-200 pb-1">Configuración Modo Lite (Paquetes)</h4>

                <div className="flex items-center mb-4">
                    <input
                        type="checkbox"
                        name="is_lite_mode"
                        checked={formData.is_lite_mode}
                        onChange={handleChange}
                        id="is_lite_mode"
                        className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                    />
                    <label htmlFor="is_lite_mode" className="ml-2 block text-sm text-gray-900 font-medium">Activar Modo Lite (Interfaz Simplificada)</label>
                </div>

                <div className="grid grid-cols-3 gap-4">
                    <div>
                        <label className="block text-xs font-medium text-gray-500 uppercase">Saldo Facturas</label>
                        <input type="number" name="saldo_facturas_venta" value={formData.saldo_facturas_venta} onChange={handleChange} className="mt-1 block w-full px-3 py-2 border border-blue-300 rounded-md shadow-sm bg-white" />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-gray-500 uppercase">Saldo Doc. Soporte</label>
                        <input type="number" name="saldo_documentos_soporte" value={formData.saldo_documentos_soporte} onChange={handleChange} className="mt-1 block w-full px-3 py-2 border border-blue-300 rounded-md shadow-sm bg-white" />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-gray-500 uppercase">Saldo Notas Crédito</label>
                        <input type="number" name="saldo_notas_credito" value={formData.saldo_notas_credito} onChange={handleChange} className="mt-1 block w-full px-3 py-2 border border-blue-300 rounded-md shadow-sm bg-white" />
                    </div>
                </div>
            </div>

            <div className="flex justify-end space-x-2 pt-4 border-t">
                <button type="button" onClick={onCancel} className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200">Cancelar</button>
                <button type="submit" disabled={isProcessing} className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:bg-gray-400">
                    {isProcessing ? 'Guardando...' : 'Guardar Cambios'}
                </button>
            </div>
        </form>
    );
}

function PanelGestionUsuarios({ empresa, onDataChange }) {
    const [roles, setRoles] = useState([]);
    const [isLoadingRoles, setIsLoadingRoles] = useState(true);
    const [newUser, setNewUser] = useState({ email: '', password: '', nombre_completo: '', rolId: '' });
    const [mensaje, setMensaje] = useState({ texto: '', tipo: '' });
    const [isProcessing, setIsProcessing] = useState(false);
    const [processingDeleteId, setProcessingDeleteId] = useState(null);
    const [isEditing, setIsEditing] = useState(false);
    const [editUserId, setEditUserId] = useState(null);

    useEffect(() => {
        const fetchRoles = async () => {
            setIsLoadingRoles(true);
            try {
                const response = await getRoles(empresa.id);
                setRoles(response.data);
                if (response.data.length > 0) {
                    setNewUser(prev => ({ ...prev, rolId: response.data[0].id }));
                }
            } catch (error) {
                setMensaje({ texto: 'Error al cargar la lista de roles.', tipo: 'error' });
            } finally {
                setIsLoadingRoles(false);
            }
        };
        fetchRoles();
    }, []);

    const handleNewUserChange = (e) => {
        const { name, value } = e.target;
        setNewUser(prev => ({ ...prev, [name]: value }));
    };

    const handleCreateUser = async (e) => {
        e.preventDefault();
        if (!newUser.rolId) {
            setMensaje({ texto: 'Por favor, selecciona un rol.', tipo: 'error' });
            return;
        }
        setIsProcessing(true);
        setMensaje({ texto: '', tipo: '' });

        const payload = {
            email: newUser.email,
            password: newUser.password, // Puede estar vacío en edit mode
            nombre_completo: newUser.nombre_completo,
            roles_ids: [parseInt(newUser.rolId, 10)]
        };

        try {
            if (isEditing) {
                // Lógica de Actualización
                // Solo enviamos password si el usuario escribió algo
                if (!payload.password) delete payload.password;

                await updateUser(editUserId, payload);
                setMensaje({ texto: 'Usuario actualizado con éxito. Actualizando...', tipo: 'success' });
            } else {
                // Lógica de Creación
                await createUserForCompany(empresa.id, payload);
                setMensaje({ texto: 'Usuario creado con éxito. Actualizando...', tipo: 'success' });
            }
            onDataChange();
            resetForm();
        } catch (error) {
            const errorMsg = error.response?.data?.detail || (isEditing ? 'Error al actualizar usuario.' : 'Error al crear usuario.');
            setMensaje({ texto: errorMsg, tipo: 'error' });
        } finally {
            setIsProcessing(false);
        }
    };

    const resetForm = () => {
        setNewUser({ email: '', password: '', nombre_completo: '', rolId: roles.length > 0 ? roles[0].id : '' });
        setIsEditing(false);
        setEditUserId(null);
    };

    const handleEditUser = (user) => {
        setNewUser({
            email: user.email,
            password: '', // No mostramos la contraseña
            nombre_completo: user.nombre_completo || '',
            rolId: user.roles && user.roles.length > 0 ? user.roles[0].id : (roles.length > 0 ? roles[0].id : '')
        });
        setIsEditing(true);
        setEditUserId(user.id);
        setMensaje({ texto: 'Modo Edición Activado', tipo: 'info' });
    };

    const handleDeleteUser = async (userId, userEmail) => {
        if (!window.confirm(`¿Estás seguro de que quieres eliminar al usuario "${userEmail}"?`)) return;
        setProcessingDeleteId(userId);
        setMensaje({ texto: '', tipo: '' });
        try {
            await deleteUser(userId);
            setMensaje({ texto: `Usuario "${userEmail}" eliminado. Actualizando...`, tipo: 'success' });
            onDataChange();
        } catch (error) {
            const errorMsg = error.response?.data?.detail || 'Error al eliminar el usuario.';
            setMensaje({ texto: errorMsg, tipo: 'error' });
        } finally {
            setProcessingDeleteId(null);
        }
    };

    return (
        <div className="space-y-6">
            <div>
                <h4 className="text-md font-semibold text-gray-800 mb-2">Usuarios Actuales</h4>
                {mensaje.texto && <p className={`p-2 my-2 rounded-md text-sm ${mensaje.tipo === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>{mensaje.texto}</p>}
                <ul className="bg-gray-50 p-3 rounded-md divide-y divide-gray-200">
                    {(empresa.usuarios || []).map(user => (
                        <li key={user.id} className="text-sm py-2 flex justify-between items-center">
                            <span>
                                {user.email} ({user.roles?.map(r => r.nombre).join(', ') || 'Sin rol'})
                            </span>
                            <button
                                onClick={() => handleEditUser(user)}
                                disabled={isProcessing}
                                className="text-xs text-indigo-600 hover:text-indigo-800 disabled:text-gray-400 mr-3">
                                Editar
                            </button>
                            <button
                                onClick={() => handleDeleteUser(user.id, user.email)}
                                disabled={processingDeleteId === user.id}
                                className="text-xs text-red-600 hover:text-red-800 disabled:text-gray-400">
                                {processingDeleteId === user.id ? 'Eliminando...' : 'Eliminar'}
                            </button>
                        </li>
                    ))}
                </ul>
            </div>
            <form onSubmit={handleCreateUser} className="space-y-4 border-t pt-4">
                <div className="flex justify-between items-center">
                    <h4 className="text-md font-semibold text-gray-800">
                        {isEditing ? 'Editar Usuario' : 'Crear Nuevo Usuario'}
                    </h4>
                    {isEditing && (
                        <button type="button" onClick={resetForm} className="text-xs text-gray-500 hover:text-gray-700 underline">
                            Cancelar Edición
                        </button>
                    )}
                </div>
                <input type="email" name="email" value={newUser.email} onChange={handleNewUserChange} placeholder="Email" required className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm" />
                <input type="password" name="password" value={newUser.password} onChange={handleNewUserChange} placeholder={isEditing ? "Dejar en blanco para mantener contraseña" : "Contraseña (mín 6 caracteres)"} required={!isEditing} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm" />
                <input type="text" name="nombre_completo" value={newUser.nombre_completo} onChange={handleNewUserChange} placeholder="Nombre Completo (Opcional)" className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm" />
                <select name="rolId" value={newUser.rolId} onChange={handleNewUserChange} disabled={isLoadingRoles} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm">
                    {isLoadingRoles ? <option>Cargando roles...</option> : (roles || []).map(rol => <option key={rol.id} value={rol.id}>{rol.nombre}</option>)}
                </select>
                <button type="submit" disabled={isProcessing || isLoadingRoles} className={`w-full px-4 py-2 text-sm font-medium text-white rounded-md hover:opacity-90 disabled:bg-gray-400 ${isEditing ? 'bg-indigo-600' : 'bg-green-600'}`}>
                    {isProcessing ? 'Procesando...' : (isEditing ? 'Actualizar Usuario' : 'Crear Usuario')}
                </button>
            </form>
        </div>
    );
}

function ModalGestionarEmpresa({ empresa, onClose, onDataChange }) {
    const [activeTab, setActiveTab] = useState('datos');
    return (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
            <div className="relative mx-auto p-5 border w-full max-w-lg shadow-lg rounded-md bg-white">
                <div className="flex justify-between items-start mb-4">
                    <h3 className="text-lg font-medium text-gray-900">Gestionando: <span className="font-bold">{empresa.razon_social}</span></h3>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600">&times;</button>
                </div>
                <div className="border-b border-gray-200">
                    <nav className="-mb-px flex space-x-4" aria-label="Tabs">
                        <button onClick={() => setActiveTab('datos')} className={`py-2 px-3 whitespace-nowrap text-sm font-medium ${activeTab === 'datos' ? 'border-b-2 border-indigo-500 text-indigo-600' : 'text-gray-500 hover:text-gray-700'}`}>Datos</button>
                        <button onClick={() => setActiveTab('usuarios')} className={`py-2 px-3 whitespace-nowrap text-sm font-medium ${activeTab === 'usuarios' ? 'border-b-2 border-indigo-500 text-indigo-600' : 'text-gray-500 hover:text-gray-700'}`}>Usuarios</button>
                    </nav>
                </div>
                <div className="mt-4">
                    {activeTab === 'datos' && <FormularioEditarEmpresa empresa={empresa} onFinished={onDataChange} onCancel={onClose} />}
                    {activeTab === 'usuarios' && <PanelGestionUsuarios empresa={empresa} onDataChange={onDataChange} />}
                </div>
            </div>
        </div>
    );
}

function GestionEmpresasPanel({ onDataChange, onOpenModal }) {
    // --- ESTADO LOCAL PARA BÚSQUEDA Y PAGINACIÓN ---
    const [empresas, setEmpresas] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [totalItems, setTotalItems] = useState(0);

    // Filtros
    const [searchText, setSearchText] = useState('');
    const [roleFilter, setRoleFilter] = useState('ADMIN'); // 'ADMIN' | 'CONTADOR'
    const [showTemplates, setShowTemplates] = useState(false); // Solo para ADMIN

    // NUEVO: Filtro por Contador Específico
    const [accountants, setAccountants] = useState([]);
    const [selectedAccountant, setSelectedAccountant] = useState('');
    const [isLoadingAccountants, setIsLoadingAccountants] = useState(false);

    // Acciones y mensajes
    const [mensaje, setMensaje] = useState({ texto: '', tipo: '' });
    const [procesandoId, setProcesandoId] = useState(null);

    // DEBOUNCE: Esperar que el usuario termine de escribir
    useEffect(() => {
        const timer = setTimeout(() => {
            fetchEmpresas();
        }, 500);
        return () => clearTimeout(timer);
    }, [searchText, roleFilter, showTemplates, page, selectedAccountant]);

    // NUEVO: Cargar lista de contadores cuando se cambia a la pestaña CONTADOR
    useEffect(() => {
        if (roleFilter === 'CONTADOR' && accountants.length === 0) {
            fetchAccountants();
        }
    }, [roleFilter]);

    const fetchAccountants = async () => {
        setIsLoadingAccountants(true);
        try {
            const response = await getAccountants();
            setAccountants(response.data);
        } catch (error) {
            console.error('Error fetching accountants:', error);
            setMensaje({ texto: 'Error al cargar lista de contadores.', tipo: 'error' });
        } finally {
            setIsLoadingAccountants(false);
        }
    };

    const fetchEmpresas = async () => {
        setIsLoading(true);
        try {
            const params = {
                q: searchText,
                role_filter: roleFilter,
                type_filter: showTemplates ? 'PLANTILLA' : 'REAL',
                page: page,
                size: 20,
                owner_id: selectedAccountant || null
            };
            // Llamamos a la nueva función de búsqueda
            const response = await searchEmpresas(params);

            setEmpresas(response.data.items);
            setTotalPages(response.data.pages);
            setTotalItems(response.data.total);
        } catch (error) {
            console.error(error);
            setMensaje({ texto: 'Error al cargar empresas. Intente recargar.', tipo: 'error' });
        } finally {
            setIsLoading(false);
        }
    };

    const handleDelete = async (empresaId, razonSocial) => {
        setMensaje({ texto: '', tipo: '' });
        if (!window.confirm(`¿Seguro que quieres eliminar "${razonSocial}"?`)) return;
        setProcesandoId(empresaId);
        try {
            const response = await deleteEmpresa(empresaId);
            setMensaje({ texto: response.data.message || 'Empresa eliminada.', tipo: 'success' });
            fetchEmpresas(); // Recargar lista actual
            if (onDataChange) onDataChange(); // Notificar al padre si es necesario
        } catch (error) {
            const errorMsg = error.response?.data?.detail || 'Error al eliminar la empresa.';
            setMensaje({ texto: errorMsg, tipo: 'error' });
        } finally {
            setProcesandoId(null);
        }
    };

    // --- MANEJADORES DE UI ---
    const handleTabChange = (newRole) => {
        setRoleFilter(newRole);
        setPage(1); // Resetear a página 1 al cambiar pestaña
        setSearchText(''); // Opcional: limpiar búsqueda
        if (newRole === 'CONTADOR') {
            setShowTemplates(false); // Contadores no ven plantillas aquí
            setSelectedAccountant('');
        }
        if (newRole === 'ADMIN') {
            setSelectedAccountant('');
        }
    };

    return (
        <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h2 className="text-xl font-bold text-gray-800">Gestión de Empresas</h2>
                    <p className="text-sm text-gray-500">Administra el acceso y ciclo de vida de las organizaciones.</p>
                </div>
                <button
                    onClick={() => window.open('/manual/capitulo_16_gestion_empresas.html', '_blank')}
                    className="text-indigo-600 hover:bg-indigo-50 px-3 py-1 rounded-md flex items-center gap-2 transition-colors"
                    title="Ver Manual de Usuario"
                >
                    <FaBook className="text-lg" /> <span className="font-bold text-sm">Manual</span>
                </button>
            </div>

            {mensaje.texto && <div className={`p-4 mb-4 rounded-md ${mensaje.tipo === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>{mensaje.texto}</div>}

            {/* --- CONTROLES DE FILTRO --- */}
            <div className="flex flex-col md:flex-row justify-between items-end md:items-center gap-4 mb-6 border-b pb-4">

                {/* PESTAÑAS */}
                <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
                    <button
                        onClick={() => handleTabChange('ADMIN')}
                        className={`px-4 py-2 text-sm font-medium rounded-md transition-shadow ${roleFilter === 'ADMIN' ? 'bg-white text-indigo-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                    >
                        🏢 Mis Empresas
                    </button>
                    <button
                        onClick={() => handleTabChange('CONTADOR')}
                        className={`px-4 py-2 text-sm font-medium rounded-md transition-shadow ${roleFilter === 'CONTADOR' ? 'bg-white text-emerald-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                    >
                        💼 De Contadores
                    </button>
                </div>

                {/* BUSCADOR Y TOGGLES */}
                <div className="flex flex-1 items-center gap-4 w-full md:w-auto">
                    {roleFilter === 'ADMIN' && (
                        <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer bg-gray-50 px-3 py-2 rounded border hover:bg-gray-100">
                            <input
                                type="checkbox"
                                checked={showTemplates}
                                onChange={(e) => { setShowTemplates(e.target.checked); setPage(1); }}
                                className="rounded text-indigo-600 focus:ring-indigo-500 border-gray-300"
                            />
                            Ver Plantillas
                        </label>
                    )}

                    {/* Filtro: Selección de Contador (Solo Contadores) */}
                    {roleFilter === 'CONTADOR' && (
                        <select
                            value={selectedAccountant}
                            onChange={(e) => { setSelectedAccountant(e.target.value); setPage(1); }}
                            disabled={isLoadingAccountants}
                            className="text-sm border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                        >
                            <option value="">Todos los Contadores</option>
                            {isLoadingAccountants ? <option disabled>Cargando...</option> :
                                (accountants || []).map(acc => (
                                    <option key={acc.id} value={acc.id}>
                                        {acc.nombre_completo || acc.email}
                                    </option>
                                ))
                            }
                        </select>
                    )}

                    <div className="relative flex-1 max-w-md">
                        <input
                            type="text"
                            placeholder="Buscar por Nombre o NIT..."
                            value={searchText}
                            onChange={(e) => setSearchText(e.target.value)}
                            className="w-full pl-4 pr-10 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                        />
                        {/* Spinner de carga mini si está buscando */}
                        {isLoading && (
                            <div className="absolute right-3 top-2.5">
                                <span className="flex h-5 w-5 relative">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-5 w-5 bg-indigo-500 opacity-20"></span>
                                </span>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* --- TABLA --- */}
            <div className="overflow-x-auto min-h-[300px]">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">NIT</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Razón Social</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Estado / Rol</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Acciones</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {isLoading && empresas.length === 0 ? (
                            <tr><td colSpan="4" className="text-center py-10 text-gray-400">Buscando empresas...</td></tr>
                        ) : empresas.length === 0 ? (
                            <tr><td colSpan="4" className="text-center py-10 text-gray-500 bg-gray-50">No se encontraron empresas con estos filtros.</td></tr>
                        ) : (
                            (empresas || []).map((empresa) => (
                                <tr key={empresa.id} className="hover:bg-gray-50 transition-colors">
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-600">{empresa.nit}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-800 flex items-center gap-2">
                                        {empresa.razon_social}
                                        {empresa.is_template && <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full border border-purple-200">Plantilla</span>}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {roleFilter === 'ADMIN' ? 'Sistema' : 'Creada por Contador'}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                                        <button onClick={() => onOpenModal(empresa)} className="px-3 py-1 bg-indigo-50 text-indigo-700 rounded hover:bg-indigo-100 border border-indigo-200">
                                            Gestionar
                                        </button>

                                        {!empresa.is_template && roleFilter === 'ADMIN' && (
                                            <button
                                                onClick={async () => {
                                                    const category = prompt('Escribe la CATEGORÍA para esta nueva plantilla (ej: PH, RETAIL, SALUD):');
                                                    if (!category) return;
                                                    setProcesandoId(empresa.id);
                                                    try {
                                                        await convertirEnPlantilla(empresa.id, category.toUpperCase());
                                                        setMensaje({ texto: `¡Empresa convertida en Plantilla (${category}) exitosamente!`, tipo: 'success' });
                                                        fetchEmpresas();
                                                    } catch (error) {
                                                        setMensaje({ texto: 'Error al convertir en plantilla.', tipo: 'error' });
                                                    } finally {
                                                        setProcesandoId(null);
                                                    }
                                                }}
                                                disabled={procesandoId === empresa.id}
                                                className="px-3 py-1 bg-purple-50 text-purple-700 rounded hover:bg-purple-100 border border-purple-200"
                                            >
                                                Convertir en Plantilla
                                            </button>
                                        )}

                                        <button
                                            onClick={() => handleDelete(empresa.id, empresa.razon_social)}
                                            disabled={procesandoId === empresa.id}
                                            className="px-3 py-1 bg-red-50 text-red-700 rounded hover:bg-red-100 border border-red-200 disabled:opacity-50"
                                        >
                                            {procesandoId === empresa.id ? '...' : 'Eliminar'}
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* --- PAGINACIÓN --- */}
            {
                totalPages > 1 && (
                    <div className="flex justify-between items-center mt-6 pt-4 border-t border-gray-100">
                        <span className="text-sm text-gray-500">
                            Mostrando {empresas.length} de {totalItems} resultados
                        </span>
                        <div className="flex gap-2">
                            <button
                                onClick={() => setPage(p => Math.max(1, p - 1))}
                                disabled={page === 1}
                                className="px-4 py-2 text-sm border rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Anterior
                            </button>
                            <span className="px-4 py-2 text-sm bg-indigo-50 text-indigo-700 font-medium rounded border border-indigo-100">
                                Página {page} de {totalPages}
                            </span>
                            <button
                                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                disabled={page === totalPages}
                                className="px-4 py-2 text-sm border rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Siguiente
                            </button>
                        </div>
                    </div>
                )
            }
        </div >
    );
}

// ##################################################################
// ########### INICIO DE LA MODIFICACIÓN ###########
// ##################################################################
function GestionSoportePanel({ soporteUsers, onDataChange }) {
    const [mensaje, setMensaje] = useState({ texto: '', tipo: '' });
    const [newUser, setNewUser] = useState({ email: '', password: '', nombre_completo: '' });
    const [isCreating, setIsCreating] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    // --- NUEVO: Estado para controlar el proceso de borrado de un usuario específico ---
    const [processingDeleteId, setProcessingDeleteId] = useState(null);

    const handleNewUserChange = (e) => {
        const { name, value } = e.target;
        setNewUser(prev => ({ ...prev, [name]: value }));
    };

    const handleCreateUser = async (e) => {
        e.preventDefault();
        setIsCreating(true);
        setMensaje({ texto: '', tipo: '' });
        try {
            await createSoporteUser(newUser);
            setMensaje({ texto: 'Usuario de soporte creado con éxito. Actualizando...', tipo: 'success' });
            setNewUser({ email: '', password: '', nombre_completo: '' });
            onDataChange();
        } catch (error) {
            const errorMsg = error.response?.data?.detail || 'Error al crear el usuario de soporte.';
            setMensaje({ texto: errorMsg, tipo: 'error' });
        } finally {
            setIsCreating(false);
        }
    };

    const handleChangePassword = async (userId, userEmail) => {
        const newPassword = prompt(`Introduce la nueva contraseña para ${userEmail}:`);
        if (newPassword && newPassword.length >= 6) {
            setIsProcessing(true);
            try {
                await updateSoporteUserPassword(userId, { nuevaPassword: newPassword });
                setMensaje({ texto: `Contraseña para ${userEmail} actualizada.`, tipo: 'success' });
            } catch (error) {
                const errorMsg = error.response?.data?.detail || 'Error al cambiar la contraseña.';
                setMensaje({ texto: errorMsg, tipo: 'error' });
            } finally {
                setIsProcessing(false);
            }
        } else if (newPassword) {
            alert('La contraseña debe tener al menos 6 caracteres.');
        }
    };

    // --- NUEVO: Función para manejar la eliminación de usuarios de soporte ---
    const handleDeleteSoporteUser = async (userId, userEmail) => {
        if (!window.confirm(`¿Estás seguro de que quieres eliminar al usuario de soporte "${userEmail}"? Esta acción no se puede deshacer.`)) return;
        setProcessingDeleteId(userId);
        setMensaje({ texto: '', tipo: '' });
        try {
            // Reutilizamos la función 'deleteUser' que ya es segura
            await deleteUser(userId);
            setMensaje({ texto: `Usuario de soporte "${userEmail}" eliminado. Actualizando...`, tipo: 'success' });
            onDataChange(); // Provocamos la recarga de datos en el panel principal
        } catch (error) {
            const errorMsg = error.response?.data?.detail || 'Error al eliminar el usuario de soporte.';
            setMensaje({ texto: errorMsg, tipo: 'error' });
        } finally {
            setProcessingDeleteId(null);
        }
    };

    return (
        <div className="space-y-8">
            <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-xl font-bold text-gray-800">Usuarios de Soporte Actuales</h2>
                    <button
                        onClick={() => window.open('/manual/capitulo_14_soporte_gestion.html', '_blank')}
                        className="text-indigo-600 hover:bg-indigo-50 px-3 py-1 rounded-md flex items-center gap-2 transition-colors"
                        title="Ver Manual de Usuario"
                    >
                        <FaBook className="text-lg" /> <span className="font-bold text-sm">Manual</span>
                    </button>
                </div>
                {mensaje.texto && <div className={`p-4 mb-4 rounded-md ${mensaje.tipo === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>{mensaje.texto}</div>}
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nombre</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Acciones</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {(soporteUsers || []).map(user => (
                            <tr key={user.id}>
                                <td className="px-6 py-4 text-sm">{user.email}</td>
                                <td className="px-6 py-4 text-sm">{user.nombre_completo || 'N/A'}</td>
                                {/* --- NUEVO: Se añade el botón de Eliminar y se ajusta la lógica de 'disabled' --- */}
                                <td className="px-6 py-4 text-sm font-medium space-x-4">
                                    <button
                                        onClick={() => handleChangePassword(user.id, user.email)}
                                        disabled={isProcessing || processingDeleteId}
                                        className="text-indigo-600 hover:text-indigo-900 disabled:text-gray-400">
                                        {isProcessing ? '...' : 'Cambiar Contraseña'}
                                    </button>
                                    <button
                                        onClick={() => handleDeleteSoporteUser(user.id, user.email)}
                                        disabled={processingDeleteId === user.id || isProcessing}
                                        className="text-red-600 hover:text-red-900 disabled:text-gray-400">
                                        {processingDeleteId === user.id ? 'Eliminando...' : 'Eliminar'}
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            <form onSubmit={handleCreateUser} className="bg-white p-6 rounded-lg shadow-md border border-gray-200 space-y-4">
                <h2 className="text-xl font-bold text-gray-800">Crear Usuario de Soporte</h2>
                <input type="email" name="email" value={newUser.email} onChange={handleNewUserChange} placeholder="Email" required className="block w-full border-gray-300 rounded-md" />
                <input type="text" name="nombre_completo" value={newUser.nombre_completo} onChange={handleNewUserChange} placeholder="Nombre Completo" className="block w-full border-gray-300 rounded-md" />
                <input type="password" name="password" value={newUser.password} onChange={handleNewUserChange} placeholder="Contraseña (mín 6)" required className="block w-full border-gray-300 rounded-md" />
                <button type="submit" disabled={isCreating} className="w-full bg-green-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-green-700 disabled:bg-gray-400">
                    {isCreating ? 'Creando...' : 'Crear Usuario'}
                </button>
            </form>
        </div>
    );
}
// ##################################################################
// ########### FIN DE LA MODIFICACIÓN ###########
// ##################################################################

function SoporteUtilContent() {
    const [soporteIsLoggedIn, setSoporteIsLoggedIn] = useState(false);
    const [loginError, setLoginError] = useState('');
    const [isLoading, setIsLoading] = useState(true);
    const [isDataLoading, setIsDataLoading] = useState(true);

    const [dashboardData, setDashboardData] = useState({ empresas: [], usuarios_soporte: [] });
    const [soporteEmail, setSoporteEmail] = useState('');
    const [soportePassword, setSoportePassword] = useState('');

    const [activeTab, setActiveTab] = useState('gestionSoporte');
    const [isModalOpen, setIsModalOpen] = useState(false);
    // CHANGE: Store the full object directly to avoid lookup issues if dashboardData is stale/incomplete
    const [selectedEmpresa, setSelectedEmpresa] = useState(null);

    const fetchDashboardData = useCallback(async () => {
        setIsDataLoading(true);
        try {
            const response = await getDashboardData();
            setDashboardData(response.data);
        } catch (error) {
            console.error("Error cargando datos del dashboard", error);
            if (error.response && error.response.status === 401) {
                handleLogout();
            }
        } finally {
            setIsDataLoading(false);
        }
    }, []);

    useEffect(() => {
        const token = localStorage.getItem('soporteAuthToken');
        if (token) {
            setSoporteAuthToken(token);
            setSoporteIsLoggedIn(true);
        }
        setIsLoading(false);
    }, []);

    const searchParams = useSearchParams();
    useEffect(() => {
        const trigger = searchParams.get('trigger');
        if (trigger === 'tab_create_company') {
            const newUrl = window.location.pathname;
            window.history.replaceState({}, '', newUrl);
            setActiveTab('crearEmpresa');
        }
    }, [searchParams]);

    useEffect(() => {
        if (soporteIsLoggedIn) {
            fetchDashboardData();
        }
    }, [soporteIsLoggedIn, fetchDashboardData]);

    const handleSoporteLogin = async (e) => {
        e.preventDefault();
        setLoginError('');
        try {
            const formData = new URLSearchParams();
            formData.append('username', soporteEmail);
            formData.append('password', soportePassword);
            const response = await soporteApiService.post('/auth/soporte/login', formData, {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
            });
            const { access_token } = response.data;
            setSoporteAuthToken(access_token);
            setSoporteIsLoggedIn(true);
        } catch (err) {
            setSoporteAuthToken(null);
            setLoginError(err.response?.data?.detail || 'Credenciales de soporte incorrectas.');
        }
    };

    const handleLogout = () => {
        setSoporteAuthToken(null);
        setSoporteIsLoggedIn(false);
        setDashboardData({ empresas: [], usuarios_soporte: [] });
        setActiveTab('gestionSoporte');
    };

    if (isLoading) return <div className="p-10 text-center">Cargando panel de soporte...</div>;

    if (!soporteIsLoggedIn) {
        return (
            <div className="flex h-screen items-center justify-center bg-gray-100">
                <div className="bg-white p-8 rounded-lg shadow-lg max-w-sm w-full border border-gray-200">
                    <h2 className="text-2xl font-bold mb-6 text-center text-gray-800">Acceso Soporte</h2>
                    {loginError && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert"><strong className="font-bold">Error:</strong> <span className="block sm:inline">{loginError}</span></div>}
                    <form onSubmit={handleSoporteLogin} className="space-y-4">
                        <div>
                            <label className="block text-gray-700 text-sm font-bold mb-2">Email Soporte</label>
                            <input type="email" value={soporteEmail} onChange={(e) => setSoporteEmail(e.target.value)} className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline focus:ring-2 focus:ring-indigo-500" required />
                        </div>
                        <div>
                            <label className="block text-gray-700 text-sm font-bold mb-2">Contraseña</label>
                            <input type="password" value={soportePassword} onChange={(e) => setSoportePassword(e.target.value)} className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline focus:ring-2 focus:ring-indigo-500" required />
                        </div>
                        <button type="submit" className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline transition-colors">
                            Ingresar
                        </button>
                    </form>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 pb-20">
            {/* Header */}
            <header className="bg-white shadow-sm border-b sticky top-0 z-30">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
                    <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                        🛡️ Panel de Soporte
                    </h1>
                    <button onClick={handleLogout} className="text-red-600 hover:text-red-800 font-medium text-sm border border-red-200 px-3 py-1 rounded bg-red-50 hover:bg-red-100 transition-colors">
                        Cerrar Sesión
                    </button>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Tabs de Navegación */}
                <div className="mb-8 border-b border-gray-200">
                    <nav className="-mb-px flex space-x-8 overflow-x-auto" aria-label="Tabs">
                        {['gestionSoporte', 'gestionEmpresas', 'crearEmpresa', 'conteo', 'roles', 'auditoria', 'utilidades', 'erradicador', 'maestros'].map((tab) => {
                            const labels = {
                                gestionSoporte: 'Usuarios Soporte',
                                gestionEmpresas: 'Gestión Empresas',
                                crearEmpresa: 'Crear Empresa',
                                conteo: 'Conteo Registros 📊',
                                roles: 'Roles Globales',
                                auditoria: 'Auditoría',
                                utilidades: 'Utilidades',
                                erradicador: 'Erradicador',
                                maestros: 'Inspector Maestros'
                            };
                            return (
                                <button
                                    key={tab}
                                    onClick={() => setActiveTab(tab)}
                                    className={`
                                        whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors
                                        ${activeTab === tab
                                            ? 'border-indigo-500 text-indigo-600'
                                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
                                    `}
                                >
                                    {labels[tab]}
                                </button>
                            );
                        })}
                    </nav>
                </div>

                {/* Contenido de Tabs */}
                <div className="animate-fadeIn">
                    {activeTab === 'gestionSoporte' && (
                        <div className="grid grid-cols-1 gap-6">
                            <GestionSoportePanel soporteUsers={dashboardData.usuarios_soporte} onDataChange={fetchDashboardData} />
                            <UltimasOperaciones todasLasEmpresas={dashboardData.empresas || []} limit={5} />
                        </div>
                    )}

                    {activeTab === 'gestionEmpresas' && (
                        <GestionEmpresasPanel
                            onDataChange={fetchDashboardData}
                            onOpenModal={(empresa) => {
                                setSelectedEmpresa(empresa);
                                setIsModalOpen(true);
                            }}
                        />
                    )}

                    {activeTab === 'crearEmpresa' && (
                        <CrearEmpresaPanel
                            onEmpresaCreated={(newEmpresa) => {
                                setActiveTab('gestionEmpresas');
                                fetchDashboardData();
                            }}
                        />
                    )}

                    {activeTab === 'conteo' && (
                        <ConteoRegistros />
                    )}

                    {activeTab === 'roles' && (
                        <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
                            <div className="flex justify-between items-center mb-6">
                                <h2 className="text-xl font-bold text-gray-800">Gestión Global de Roles</h2>
                                <p className="text-sm text-gray-500">Configuración de plantillas de permisos para nuevas empresas.</p>
                            </div>
                            <RolesManagementView isGlobalMode={true} />
                        </div>
                    )}

                    {activeTab === 'auditoria' && (
                        <div className="space-y-8">
                            <AuditoriaConsecutivosSoporte todasLasEmpresas={dashboardData.empresas || []} />
                            <InspectorUniversal />
                        </div>
                    )}

                    {activeTab === 'utilidades' && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <ResetConsumoPanel />
                            <BuscadorPorLlaveNatural />
                        </div>
                    )}

                    {activeTab === 'erradicador' && (
                        <ErradicadorUniversal />
                    )}

                    {activeTab === 'maestros' && (
                        <InspectorMaestros />
                    )}
                </div>
            </main>

            {/* Modal Global */}
            {isModalOpen && selectedEmpresa && (
                <ModalGestionarEmpresa
                    empresa={selectedEmpresa}
                    onClose={() => {
                        setIsModalOpen(false);
                        setSelectedEmpresa(null);
                    }}
                    onDataChange={() => {
                        fetchDashboardData();
                        setIsModalOpen(false);
                        setSelectedEmpresa(null); // Force close to refresh potential stale data references
                    }}
                />
            )}
        </div>
    );
}

export default function SoporteUtilPage() {
    return (
        <React.Suspense fallback={<div className="h-screen flex items-center justify-center text-indigo-500">Cargando Soporte...</div>}>
            <SoporteUtilContent />
        </React.Suspense>
    );
}