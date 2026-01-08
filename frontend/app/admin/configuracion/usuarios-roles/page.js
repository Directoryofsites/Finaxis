'use client';

import React, { useState, useEffect, useMemo } from 'react';
import {
    FaUsers, FaUserShield, FaEdit, FaTrash, FaPlus, FaCheck, FaTimes, FaShieldAlt
} from 'react-icons/fa';
import {
    getRoles, createRol, updateRol, deleteRol, getPermisos,
    getCompanyUsers, createCompanyUser, updateCompanyUser, deleteCompanyUser
} from '@/lib/rolesApiService';
import { useAuth } from '@/app/context/AuthContext';
import { menuStructure } from '@/lib/menuData';

export default function UsuariosRolesPage() {
    const { user } = useAuth();
    const [activeTab, setActiveTab] = useState('usuarios');
    const [isLoading, setIsLoading] = useState(false);

    // --- DATA STATE ---
    const [usuarios, setUsuarios] = useState([]);
    const [roles, setRoles] = useState([]); // Roles de la empresa + globales
    const [allPermisos, setAllPermisos] = useState([]);

    // --- MODAL STATE ---
    const [showUserModal, setShowUserModal] = useState(false);
    const [showRoleModal, setShowRoleModal] = useState(false);
    const [editingItem, setEditingItem] = useState(null); // User or Role object

    // --- FORM STATE ---
    const [userData, setUserData] = useState({ email: '', password: '', nombre_completo: '', rolId: '' });
    const [roleData, setRoleData] = useState({ nombre: '', descripcion: '', permisos_ids: [] });

    // --- FETCH DATA ---
    const fetchData = async () => {
        setIsLoading(true);
        try {
            const [usersRes, rolesRes, permisosRes] = await Promise.all([
                getCompanyUsers(),
                getRoles(),
                getPermisos()
            ]);
            setUsuarios(usersRes);
            setRoles(rolesRes);
            setAllPermisos(permisosRes);
        } catch (error) {
            console.error("Error fetching data:", error);
            alert("Error cargando datos. Ver consola.");
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    // --- HANDLERS: USER ---
    const handleSaveUser = async (e) => {
        e.preventDefault();
        try {
            const payload = {
                email: userData.email,
                nombre_completo: userData.nombre_completo,
                roles_ids: [parseInt(userData.rolId)]
            };
            if (userData.password) payload.password = userData.password;

            if (editingItem) {
                // Update
                if (!payload.password) delete payload.password;
                await updateCompanyUser(editingItem.id, payload);
            } else {
                // Create
                await createCompanyUser(payload);
            }
            setShowUserModal(false);
            fetchData();
        } catch (error) {
            alert(error.response?.data?.detail || "Error guardando usuario");
        }
    };

    const openUserModal = (userToEdit = null) => {
        if (userToEdit) {
            setEditingItem(userToEdit);
            setUserData({
                email: userToEdit.email,
                password: '',
                nombre_completo: userToEdit.nombre_completo || '',
                rolId: userToEdit.roles?.[0]?.id || ''
            });
        } else {
            setEditingItem(null);
            setUserData({ email: '', password: '', nombre_completo: '', rolId: roles[0]?.id || '' });
        }
        setShowUserModal(true);
    };

    // --- HANDLERS: ROLE ---
    const handleSaveRole = async (e) => {
        e.preventDefault();
        try {
            const payload = { ...roleData };

            if (editingItem) {
                await updateRol(editingItem.id, payload);
            } else {
                await createRol(payload);
            }
            setShowRoleModal(false);
            fetchData();
        } catch (error) {
            alert(error.response?.data?.detail || "Error guardando rol");
        }
    };

    const openRoleModal = (roleToEdit = null) => {
        if (roleToEdit) {
            setEditingItem(roleToEdit);
            setRoleData({
                nombre: roleToEdit.nombre,
                descripcion: roleToEdit.descripcion || '',
                permisos_ids: roleToEdit.permisos?.map(p => p.id) || []
            });
        } else {
            setEditingItem(null);
            setRoleData({ nombre: '', descripcion: '', permisos_ids: [] });
        }
        setShowRoleModal(true);
    };

    const togglePermiso = (permisoId) => {
        setRoleData(prev => {
            const ids = prev.permisos_ids;
            if (ids.includes(permisoId)) {
                return { ...prev, permisos_ids: ids.filter(id => id !== permisoId) };
            } else {
                return { ...prev, permisos_ids: [...ids, permisoId] };
            }
        });
    };

    const toggleGroup = (permisosGroup) => {
        const groupIds = permisosGroup.map(p => p.id);
        setRoleData(prev => {
            const allSelected = groupIds.every(id => prev.permisos_ids.includes(id));
            if (allSelected) {
                // Deselect all
                return { ...prev, permisos_ids: prev.permisos_ids.filter(id => !groupIds.includes(id)) };
            } else {
                // Select all (add missing ones)
                const newIds = [...prev.permisos_ids];
                groupIds.forEach(id => {
                    if (!newIds.includes(id)) newIds.push(id);
                });
                return { ...prev, permisos_ids: newIds };
            }
        });
    }

    // --- PERMISSION GROUPING ---
    // --- PERMISSION GROUPING (MENU BASED) ---
    const menuBasedPermissions = useMemo(() => {
        const sections = [];

        // Helper to find permission ID object
        const findPermId = (permName) => allPermisos.find(p => p.nombre === permName)?.id;

        menuStructure.forEach(module => {
            // Case 1: Module has direct links (e.g. Contabilida, Activos)
            if (module.links) {
                const items = module.links
                    .filter(link => link.permission) // Only links with permissions
                    .map(link => ({
                        id: findPermId(link.permission), // The DB ID of the permission
                        perm_name: link.permission,
                        label: link.name,
                        desc: link.description
                    }))
                    .filter(item => item.id); // Only if permission exists in DB

                if (items.length > 0) {
                    sections.push({ title: module.name, items });
                }
            }
            // Case 2: Module has subgroups (e.g. Admin)
            else if (module.subgroups) {
                module.subgroups.forEach(sub => {
                    const items = sub.links
                        .filter(link => link.permission)
                        .map(link => ({
                            id: findPermId(link.permission),
                            perm_name: link.permission,
                            label: link.name,
                            desc: link.description
                        }))
                        .filter(item => item.id);

                    if (items.length > 0) {
                        sections.push({ title: `${module.name} - ${sub.title}`, items });
                    }
                });
            }
        });
        return sections;
    }, [allPermisos]);


    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <header className="flex justify-between items-center bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                <div>
                    <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-3">
                        <FaUserShield className="text-indigo-600" />
                        Gestión de Usuarios y Roles
                    </h1>
                    <p className="text-gray-500 mt-1">Administre el acceso y funciones de su equipo.</p>
                </div>
            </header>

            {/* TABS */}
            <div className="flex border-b border-gray-200 bg-white rounded-t-xl px-6 pt-4 gap-6">
                <button
                    onClick={() => setActiveTab('usuarios')}
                    className={`pb-4 text-sm font-semibold flex items-center gap-2 border-b-2 transition-colors ${activeTab === 'usuarios' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
                >
                    <FaUsers /> Usuarios
                </button>
                <button
                    onClick={() => setActiveTab('roles')}
                    className={`pb-4 text-sm font-semibold flex items-center gap-2 border-b-2 transition-colors ${activeTab === 'roles' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
                >
                    <FaShieldAlt /> Roles y Permisos
                </button>
            </div>

            <div className="bg-white rounded-b-xl shadow-sm border border-t-0 p-6 min-h-[500px]">
                {/* TAB CONTENT: USUARIOS */}
                {activeTab === 'usuarios' && (
                    <div className="space-y-4">
                        <div className="flex justify-end">
                            <button onClick={() => openUserModal()} className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 flex items-center gap-2 font-medium shadow-sm transition-all hover:-translate-y-0.5">
                                <FaPlus /> Crear Usuario
                            </button>
                        </div>
                        <div className="overflow-hidden rounded-lg border border-gray-200">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50 text-gray-500 font-bold uppercase text-xs">
                                    <tr>
                                        <th className="px-6 py-3 text-left">Usuario</th>
                                        <th className="px-6 py-3 text-left">Email</th>
                                        <th className="px-6 py-3 text-left">Rol</th>
                                        <th className="px-6 py-3 text-center">Acciones</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100 bg-white">
                                    {usuarios.map(u => (
                                        <tr key={u.id} className="hover:bg-gray-50 transition-colors">
                                            <td className="px-6 py-4 font-medium text-gray-900">{u.nombre_completo || 'Sin nombre'}</td>
                                            <td className="px-6 py-4 text-gray-600">{u.email}</td>
                                            <td className="px-6 py-4">
                                                <span className="bg-indigo-50 text-indigo-700 text-xs font-bold px-2 py-1 rounded-full border border-indigo-100">
                                                    {u.roles?.[0]?.nombre || 'Sin Rol'}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 flex justify-center gap-3">
                                                <button onClick={() => openUserModal(u)} className="text-gray-400 hover:text-indigo-600"><FaEdit /></button>
                                                <button
                                                    onClick={async () => {
                                                        if (confirm('¿Eliminar usuario?')) {
                                                            await deleteCompanyUser(u.id);
                                                            fetchData();
                                                        }
                                                    }}
                                                    className="text-gray-400 hover:text-red-600"
                                                ><FaTrash /></button>
                                            </td>
                                        </tr>
                                    ))}
                                    {usuarios.length === 0 && <tr><td colSpan="4" className="text-center py-8 text-gray-400">No hay usuarios registrados.</td></tr>}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* TAB CONTENT: ROLES */}
                {activeTab === 'roles' && (
                    <div className="space-y-4">
                        <div className="flex justify-end">
                            <button onClick={() => openRoleModal()} className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 flex items-center gap-2 font-medium shadow-sm transition-all hover:-translate-y-0.5">
                                <FaPlus /> Crear Rol Personalizado
                            </button>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {roles.map(rol => {
                                const isGlobal = !rol.empresa_id;
                                return (
                                    <div key={rol.id} className={`border rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden ${isGlobal ? 'bg-gray-50 border-gray-200' : 'bg-white border-indigo-100'}`}>
                                        {isGlobal && <div className="absolute top-0 right-0 bg-gray-200 text-gray-600 text-[10px] font-bold px-2 py-0.5 rounded-bl">SISTEMA</div>}
                                        {!isGlobal && <div className="absolute top-0 right-0 bg-indigo-100 text-indigo-600 text-[10px] font-bold px-2 py-0.5 rounded-bl">PERSONALIZADO</div>}

                                        <h3 className="font-bold text-lg text-gray-800 mb-1">{rol.nombre}</h3>
                                        <p className="text-sm text-gray-500 mb-4 h-10 overflow-hidden">{rol.descripcion || 'Sin descripción'}</p>

                                        <div className="flex justify-between items-center border-t border-gray-100 pt-3">
                                            <span className="text-xs font-semibold text-gray-400">{rol.permisos?.length || 0} Permisos</span>
                                            {!isGlobal && (
                                                <div className="flex gap-2">
                                                    <button onClick={() => openRoleModal(rol)} className="text-indigo-600 hover:bg-indigo-50 p-1.5 rounded"><FaEdit /></button>
                                                    <button
                                                        onClick={async () => {
                                                            if (confirm('¿Eliminar rol?')) {
                                                                await deleteRol(rol.id);
                                                                fetchData();
                                                            }
                                                        }}
                                                        className="text-red-400 hover:bg-red-50 p-1.5 rounded"
                                                    ><FaTrash /></button>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}
            </div>

            {/* MODAL USUARIO */}
            {showUserModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
                    <div className="bg-white rounded-xl shadow-2xl w-full max-w-md p-6 animate-slideDown">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-xl font-bold text-gray-800">{editingItem ? 'Editar Usuario' : 'Nuevo Usuario'}</h2>
                            <button onClick={() => setShowUserModal(false)} className="text-gray-400 hover:text-gray-600"><FaTimes /></button>
                        </div>
                        <form onSubmit={handleSaveUser} className="space-y-4">
                            <div>
                                <label className="block text-sm font-bold text-gray-700 mb-1">Email</label>
                                <input
                                    type="email"
                                    value={userData.email}
                                    onChange={e => setUserData({ ...userData, email: e.target.value })}
                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-gray-900 focus:ring-2 focus:ring-indigo-500 outline-none"
                                    disabled={editingItem} // Email es difícil de cambiar a veces por integridad
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-bold text-gray-700 mb-1">Nombre Completo</label>
                                <input
                                    type="text"
                                    value={userData.nombre_completo}
                                    onChange={e => setUserData({ ...userData, nombre_completo: e.target.value })}
                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-gray-900 focus:ring-2 focus:ring-indigo-500 outline-none"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-bold text-gray-700 mb-1">Rol</label>
                                <select
                                    value={userData.rolId}
                                    onChange={e => setUserData({ ...userData, rolId: e.target.value })}
                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-gray-900 focus:ring-2 focus:ring-indigo-500 outline-none bg-white"
                                    required
                                >
                                    <option value="">Seleccione...</option>
                                    {roles.map(r => (
                                        <option key={r.id} value={r.id}>{r.nombre}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-bold text-gray-700 mb-1">Contraseña {editingItem && '(Opcional)'}</label>
                                <input
                                    type="password"
                                    value={userData.password}
                                    onChange={e => setUserData({ ...userData, password: e.target.value })}
                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-gray-900 focus:ring-2 focus:ring-indigo-500 outline-none"
                                    placeholder={editingItem ? "Dejar vacío para no cambiar" : "Mínimo 6 caracteres"}
                                    required={!editingItem}
                                />
                            </div>
                            <div className="flex justify-end gap-3 pt-4">
                                <button type="button" onClick={() => setShowUserModal(false)} className="px-4 py-2 text-gray-600 font-medium hover:bg-gray-100 rounded-lg">Cancelar</button>
                                <button type="submit" className="px-6 py-2 bg-indigo-600 text-white font-bold rounded-lg hover:bg-indigo-700">Guardar Usuario</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* MODAL ROL */}
            {showRoleModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
                    <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl p-6 h-[90vh] flex flex-col animate-slideDown">
                        <div className="flex justify-between items-center mb-6 shrink-0">
                            <h2 className="text-xl font-bold text-gray-800">{editingItem ? 'Editar Rol' : 'Nuevo Rol'}</h2>
                            <button onClick={() => setShowRoleModal(false)} className="text-gray-400 hover:text-gray-600"><FaTimes /></button>
                        </div>

                        <form onSubmit={handleSaveRole} className="flex flex-col flex-1 overflow-hidden">
                            <div className="grid grid-cols-2 gap-4 mb-6 shrink-0">
                                <div>
                                    <label className="block text-sm font-bold text-gray-700 mb-1">Nombre del Rol</label>
                                    <input
                                        type="text"
                                        value={roleData.nombre}
                                        onChange={e => setRoleData({ ...roleData, nombre: e.target.value })}
                                        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-gray-900 focus:ring-2 focus:ring-indigo-500 outline-none"
                                        placeholder="ej: Auxiliar de Facturación"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-bold text-gray-700 mb-1">Descripción</label>
                                    <input
                                        type="text"
                                        value={roleData.descripcion}
                                        onChange={e => setRoleData({ ...roleData, descripcion: e.target.value })}
                                        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-gray-900 focus:ring-2 focus:ring-indigo-500 outline-none"
                                        placeholder="Breve descripción del perfil"
                                    />
                                </div>
                            </div>

                            <div className="flex-1 overflow-y-auto border border-gray-200 rounded-lg p-4 bg-gray-50">
                                <label className="block text-sm font-bold text-gray-700 mb-4 uppercase tracking-wide border-b pb-2">Asignación de Permisos</label>
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                    {menuBasedPermissions.map((section) => {
                                        const allSelected = section.items.every(item => roleData.permisos_ids.includes(item.id));
                                        return (
                                            <div key={section.title} className="bg-white p-4 rounded-lg shadow-sm border border-gray-100 flex flex-col h-full">
                                                <div className="flex justify-between items-center border-b border-indigo-50 pb-2 mb-3">
                                                    <h4 className="font-bold text-indigo-600 uppercase text-xs">{section.title}</h4>
                                                    <button
                                                        type="button"
                                                        onClick={() => {
                                                            const ids = section.items.map(i => i.id);
                                                            setRoleData(prev => {
                                                                if (allSelected) {
                                                                    return { ...prev, permisos_ids: prev.permisos_ids.filter(id => !ids.includes(id)) };
                                                                } else {
                                                                    const newIds = [...prev.permisos_ids];
                                                                    ids.forEach(id => { if (!newIds.includes(id)) newIds.push(id); });
                                                                    return { ...prev, permisos_ids: newIds };
                                                                }
                                                            });
                                                        }}
                                                        className="text-[10px] text-blue-500 hover:text-blue-700 underline"
                                                    >
                                                        {allSelected ? 'Deseleccionar' : 'Todos'}
                                                    </button>
                                                </div>
                                                <div className="space-y-2 flex-1">
                                                    {section.items.map(item => (
                                                        <label key={item.id + item.label} className="flex items-start gap-2 cursor-pointer group hover:bg-gray-50 p-1 rounded -mx-1 transition-colors">
                                                            <div className={`mt-0.5 w-4 h-4 border rounded flex items-center justify-center transition-colors shrink-0 ${roleData.permisos_ids.includes(item.id) ? 'bg-indigo-600 border-indigo-600' : 'border-gray-300 group-hover:border-indigo-400'}`}>
                                                                {roleData.permisos_ids.includes(item.id) && <FaCheck className="text-white text-[10px]" />}
                                                            </div>
                                                            <input
                                                                type="checkbox"
                                                                className="hidden"
                                                                checked={roleData.permisos_ids.includes(item.id)}
                                                                onChange={() => togglePermiso(item.id)}
                                                            />
                                                            <div className="flex flex-col">
                                                                <span className="text-xs text-gray-800 font-medium group-hover:text-indigo-700 leading-tight select-none">
                                                                    {item.label}
                                                                </span>
                                                                <span className="text-[10px] text-gray-400">
                                                                    {item.desc || item.perm_name}
                                                                </span>
                                                            </div>
                                                        </label>
                                                    ))}
                                                </div>
                                            </div>
                                        )
                                    })}
                                </div>
                            </div>

                            <div className="flex justify-end gap-3 pt-6 shrink-0 border-t mt-4">
                                <button type="button" onClick={() => setShowRoleModal(false)} className="px-4 py-2 text-gray-600 font-medium hover:bg-gray-100 rounded-lg">Cancelar</button>
                                <button type="submit" className="px-6 py-2 bg-indigo-600 text-white font-bold rounded-lg hover:bg-indigo-700">Guardar Rol</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
