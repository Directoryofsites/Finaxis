'use client';
import React, { useState, useEffect, useCallback } from 'react';
import { FaBook } from 'react-icons/fa';
import BotonRegresar from '@/app/components/BotonRegresar';

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
    deleteUser
} from '@/lib/soporteApiService';

import ConteoRegistros from './components/ConteoRegistros';
import BuscadorPorLlaveNatural from './components/BuscadorPorLlaveNatural';
import InspectorMaestros from './components/InspectorMaestros';
import ErradicadorUniversal from './components/ErradicadorUniversal';
import CrearEmpresaPanel from './components/CrearEmpresaPanel';
import InspectorUniversal from './components/InspectorUniversal';
import UltimasOperaciones from './components/UltimasOperaciones';
import AuditoriaConsecutivosSoporte from './components/AuditoriaConsecutivosSoporte';


// ... (Aquí van todos los componentes hijos que ya tienes en tu archivo, 
//      FormularioEditarEmpresa, PanelGestionUsuarios, etc. No cambian.)
function FormularioEditarEmpresa({ empresa, onFinished, onCancel }) {
    const [formData, setFormData] = useState({
        razon_social: '',
        nit: '',
        fecha_inicio_operaciones: ''
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
                fecha_inicio_operaciones: fechaFormateada
            });
        }
    }, [empresa]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
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
            <div>
                <label className="block text-sm font-medium text-gray-700">Razón Social</label>
                <input type="text" name="razon_social" value={formData.razon_social} onChange={handleChange} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm" />
            </div>
            <div>
                <label className="block text-sm font-medium text-gray-700">NIT</label>
                <input type="text" name="nit" value={formData.nit} onChange={handleChange} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm" />
            </div>
            <div>
                <label className="block text-sm font-medium text-gray-700">Fecha Inicio de Operaciones</label>
                <input type="date" name="fecha_inicio_operaciones" value={formData.fecha_inicio_operaciones} onChange={handleChange} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm" />
            </div>
            <div className="flex justify-end space-x-2">
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

    useEffect(() => {
        const fetchRoles = async () => {
            setIsLoadingRoles(true);
            try {
                const response = await getRoles();
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
            password: newUser.password,
            nombre_completo: newUser.nombre_completo,
            roles_ids: [parseInt(newUser.rolId, 10)]
        };
        try {
            await createUserForCompany(empresa.id, payload);
            setMensaje({ texto: 'Usuario creado con éxito. Actualizando...', tipo: 'success' });
            onDataChange();
            setNewUser({ email: '', password: '', nombre_completo: '', rolId: roles.length > 0 ? roles[0].id : '' });
        } catch (error) {
            const errorMsg = error.response?.data?.detail || 'Error al crear el usuario.';
            setMensaje({ texto: errorMsg, tipo: 'error' });
        } finally {
            setIsProcessing(false);
        }
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
                <h4 className="text-md font-semibold text-gray-800">Crear Nuevo Usuario</h4>
                <input type="email" name="email" value={newUser.email} onChange={handleNewUserChange} placeholder="Email" required className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm" />
                <input type="password" name="password" value={newUser.password} onChange={handleNewUserChange} placeholder="Contraseña (mín 6 caracteres)" required className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm" />
                <input type="text" name="nombre_completo" value={newUser.nombre_completo} onChange={handleNewUserChange} placeholder="Nombre Completo (Opcional)" className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm" />
                <select name="rolId" value={newUser.rolId} onChange={handleNewUserChange} disabled={isLoadingRoles} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm">
                    {isLoadingRoles ? <option>Cargando roles...</option> : roles.map(rol => <option key={rol.id} value={rol.id}>{rol.nombre}</option>)}
                </select>
                <button type="submit" disabled={isProcessing || isLoadingRoles} className="w-full px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 disabled:bg-gray-400">
                    {isProcessing ? 'Creando...' : 'Crear Usuario'}
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

function GestionEmpresasPanel({ empresas, onDataChange, onOpenModal }) {
    const [mensaje, setMensaje] = useState({ texto: '', tipo: '' });
    const [procesandoId, setProcesandoId] = useState(null);

    const handleDelete = async (empresaId, razonSocial) => {
        setMensaje({ texto: '', tipo: '' });
        if (!window.confirm(`¿Seguro que quieres eliminar "${razonSocial}"?`)) return;
        setProcesandoId(empresaId);
        try {
            const response = await deleteEmpresa(empresaId);
            setMensaje({ texto: response.data.message || 'Empresa eliminada. Actualizando...', tipo: 'success' });
            onDataChange();
        } catch (error) {
            const errorMsg = error.response?.data?.detail || 'Error al eliminar la empresa.';
            setMensaje({ texto: errorMsg, tipo: 'error' });
        } finally {
            setProcesandoId(null);
        }
    };

    return (
        <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold text-gray-800">Gestión de Empresas Registradas</h2>
                <button
                    onClick={() => window.open('/manual/capitulo_16_gestion_empresas.html', '_blank')}
                    className="text-indigo-600 hover:bg-indigo-50 px-3 py-1 rounded-md flex items-center gap-2 transition-colors"
                    title="Ver Manual de Usuario"
                >
                    <FaBook className="text-lg" /> <span className="font-bold text-sm">Manual</span>
                </button>
            </div>
            {mensaje.texto && <div className={`p-4 mb-4 rounded-md ${mensaje.tipo === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>{mensaje.texto}</div>}
            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">NIT</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Razón Social</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Acciones</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {empresas.map((empresa) => (
                            <tr key={empresa.id}>
                                <td className="px-6 py-4 whitespace-nowrap text-sm">{empresa.nit}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm">{empresa.razon_social}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-4">
                                    <button onClick={() => onOpenModal(empresa)} className="text-indigo-600 hover:text-indigo-900">Gestionar</button>
                                    <button onClick={() => handleDelete(empresa.id, empresa.razon_social)} disabled={procesandoId === empresa.id} className="text-red-600 hover:text-red-900 disabled:text-gray-400">
                                        {procesandoId === empresa.id ? 'Eliminando...' : 'Eliminar'}
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
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
                        {soporteUsers.map(user => (
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

export default function SoporteUtilPage() {
    const [soporteIsLoggedIn, setSoporteIsLoggedIn] = useState(false);
    const [loginError, setLoginError] = useState('');
    const [isLoading, setIsLoading] = useState(true);
    const [isDataLoading, setIsDataLoading] = useState(true);

    const [dashboardData, setDashboardData] = useState({ empresas: [], usuarios_soporte: [] });
    const [soporteEmail, setSoporteEmail] = useState('');
    const [soportePassword, setSoportePassword] = useState('');

    const [activeTab, setActiveTab] = useState('gestionSoporte');
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedEmpresa, setSelectedEmpresa] = useState(null);

    const fetchDashboardData = useCallback(async () => {
        setIsDataLoading(true);
        try {
            const response = await getDashboardData();
            setDashboardData(response.data);
        } catch (error) {
            console.error("Error cargando datos del dashboard", error);
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

    const openModal = (empresa) => {
        setSelectedEmpresa(empresa);
        setIsModalOpen(true);
    };
    const closeModal = () => {
        setIsModalOpen(false);
        setSelectedEmpresa(null);
    };

    const handleDataUpdatedInModal = () => {
        fetchDashboardData();
    };

    if (isLoading) return <p className="text-center mt-10">Cargando...</p>;

    if (!soporteIsLoggedIn) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-gray-100">
                <div className="p-8 max-w-md w-full bg-white rounded-lg shadow-md">
                    <h2 className="text-2xl font-bold text-center text-gray-800 mb-6">Acceso de Soporte</h2>
                    <form onSubmit={handleSoporteLogin}>
                        <div className="mb-4">
                            <label className="block text-gray-700 text-sm font-bold mb-2">Usuario</label>
                            <input type="text" value={soporteEmail} onChange={(e) => setSoporteEmail(e.target.value)} className="shadow appearance-none border rounded w-full py-2 px-3" required />
                        </div>
                        <div className="mb-6">
                            <label className="block text-gray-700 text-sm font-bold mb-2">Contraseña</label>
                            <input type="password" value={soportePassword} onChange={(e) => setSoportePassword(e.target.value)} className="shadow appearance-none border rounded w-full py-2 px-3" required />
                        </div>
                        {loginError && <p className="text-red-500 text-xs italic mb-4">{loginError}</p>}
                        <button type="submit" className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded w-full">Ingresar</button>
                    </form>
                </div>
            </div>
        );
    }

    return (
        <div className="container mx-auto p-4 max-w-screen-2xl space-y-8 bg-gray-50 min-h-screen">
            <div className="flex justify-between items-center">
                <h1 className="text-3xl font-extrabold text-gray-900">Panel de Herramientas de Soporte</h1>
                <div>
                    <button onClick={handleLogout} className="text-sm text-red-600 hover:underline mr-4">Cerrar Sesión</button>
                    <BotonRegresar />
                </div>
            </div>
            <div className="flex border-b mb-6 overflow-x-auto">
                <button onClick={() => setActiveTab('gestionSoporte')} className={`py-2 px-4 whitespace-nowrap ${activeTab === 'gestionSoporte' ? 'border-b-2 border-pink-600 font-semibold text-pink-600' : 'text-gray-500'}`}>Gestión Soporte</button>
                <button onClick={() => setActiveTab('crearEmpresa')} className={`py-2 px-4 whitespace-nowrap ${activeTab === 'crearEmpresa' ? 'border-b-2 border-green-600 font-semibold text-green-600' : 'text-gray-500'}`}>Crear Empresa</button>
                <button onClick={() => setActiveTab('gestionEmpresas')} className={`py-2 px-4 whitespace-nowrap ${activeTab === 'gestionEmpresas' ? 'border-b-2 border-yellow-600 font-semibold text-yellow-600' : 'text-gray-500'}`}>Gestión Empresas</button>
                <button onClick={() => setActiveTab('auditoriaConsecutivos')} className={`py-2 px-4 whitespace-nowrap ${activeTab === 'auditoriaConsecutivos' ? 'border-b-2 border-cyan-600 font-semibold text-cyan-600' : 'text-gray-500'}`}>Auditoría Consecutivos</button>
                <button onClick={() => setActiveTab('inspectorMaestros')} className={`py-2 px-4 whitespace-nowrap ${activeTab === 'inspectorMaestros' ? 'border-b-2 border-indigo-600 font-semibold text-indigo-600' : 'text-gray-500'}`}>Inspector Maestros</button>
                <button onClick={() => setActiveTab('buscadorLlaveNatural')} className={`py-2 px-4 whitespace-nowrap ${activeTab === 'buscadorLlaveNatural' ? 'border-b-2 border-teal-600 font-semibold text-teal-600' : 'text-gray-500'}`}>Buscador</button>
                <button onClick={() => setActiveTab('inspectorUniversal')} className={`py-2 px-4 whitespace-nowrap ${activeTab === 'inspectorUniversal' ? 'border-b-2 border-purple-600 font-semibold text-purple-600' : 'text-gray-500'}`}>Inspector (ID)</button>
                <button onClick={() => setActiveTab('operaciones')} className={`py-2 px-4 whitespace-nowrap ${activeTab === 'operaciones' ? 'border-b-2 border-blue-600 font-semibold text-blue-600' : 'text-gray-500'}`}>Últimas Operaciones</button>
                <button onClick={() => setActiveTab('conteo')} className={`py-2 px-4 whitespace-nowrap ${activeTab === 'conteo' ? 'border-b-2 border-blue-600 font-semibold text-blue-600' : 'text-gray-500'}`}>Conteo</button>
                <button onClick={() => setActiveTab('erradicadorUniversal')} className={`py-2 px-4 whitespace-nowrap ${activeTab === 'erradicadorUniversal' ? 'border-b-2 border-red-600 font-semibold text-red-600' : 'text-gray-500'}`}>Erradicador</button>
            </div>
            <div>
                {isDataLoading ? (
                    <p className="text-center mt-10">Cargando datos del panel...</p>
                ) : (
                    <>
                        {activeTab === 'gestionSoporte' && <GestionSoportePanel soporteUsers={dashboardData.usuarios_soporte} onDataChange={fetchDashboardData} />}
                        {activeTab === 'crearEmpresa' && <CrearEmpresaPanel onEmpresaCreada={fetchDashboardData} />}
                        {activeTab === 'gestionEmpresas' && <GestionEmpresasPanel empresas={dashboardData.empresas} onDataChange={fetchDashboardData} onOpenModal={openModal} />}
                        {activeTab === 'auditoriaConsecutivos' && <AuditoriaConsecutivosSoporte todasLasEmpresas={dashboardData.empresas} />}
                        {activeTab === 'inspectorMaestros' && <InspectorMaestros todasLasEmpresas={dashboardData.empresas} />}
                        {activeTab === 'buscadorLlaveNatural' && <BuscadorPorLlaveNatural todasLasEmpresas={dashboardData.empresas} />}
                        {activeTab === 'inspectorUniversal' && <InspectorUniversal />}
                        {activeTab === 'operaciones' && <UltimasOperaciones todasLasEmpresas={dashboardData.empresas} />}
                        {activeTab === 'conteo' && <ConteoRegistros />}
                        {activeTab === 'erradicadorUniversal' && <ErradicadorUniversal todasLasEmpresas={dashboardData.empresas} />}
                    </>
                )}
            </div>
            {isModalOpen && selectedEmpresa && (
                <ModalGestionarEmpresa
                    empresa={selectedEmpresa}
                    onClose={closeModal}
                    onDataChange={handleDataUpdatedInModal}
                />
            )}
        </div>
    );
}