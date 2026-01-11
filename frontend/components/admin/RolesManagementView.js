
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { FaPlus, FaEdit, FaTrash, FaSave, FaTimes, FaTags } from 'react-icons/fa';
import Swal from 'sweetalert2';
import { menuStructure } from '@/lib/menuData';

// NOTE: Ensure your API client sends credentials/tokens
// Usamos el servicio de soporte que ya tiene el token configurado
import { soporteApiService as api } from '@/lib/soporteApiService';

export default function RolesManagementView() {
    const [roles, setRoles] = useState([]);
    const [allPermisos, setAllPermisos] = useState([]);
    const [loading, setLoading] = useState(false);

    // Configuración del editor
    const [isEditing, setIsEditing] = useState(false);
    const [editingRol, setEditingRol] = useState(null); // Objeto completo del rol

    // Filtros de permisos
    const [permisoSearch, setPermisoSearch] = useState('');

    useEffect(() => {
        fetchRoles();
        fetchPermisos();
    }, []);

    const fetchRoles = async () => {
        setLoading(true);
        try {
            // Pasamos empresa_id=null implícitamente al ser rol de sistema si el usuario es soporte
            const response = await api.get('/roles/');
            setRoles(response.data);
        } catch (error) {
            console.error(error);
            Swal.fire('Error', 'No se pudieron cargar los roles', 'error');
        } finally {
            setLoading(false);
        }
    };

    const fetchPermisos = async () => {
        try {
            const response = await api.get('/roles/permisos');
            setAllPermisos(response.data);
        } catch (error) {
            console.error("Error cargando permisos", error);
        }
    };

    const handleCreateClick = () => {
        setEditingRol({
            id: null,
            nombre: '',
            descripcion: '',
            permisos: [] // Lista de objetos o IDs? El backend suele esperar IDs o lista de objetos en update
        });
        setIsEditing(true);
    };

    const handleEditClick = (rol) => {
        // Clonar para no mutar estado directo y facilitar edición
        setEditingRol({ ...rol });
        setIsEditing(true);
    };

    const handleDeleteClick = async (rolId) => {
        const result = await Swal.fire({
            title: '¿Estás seguro?',
            text: "Esta acción no se puede deshacer.",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Sí, eliminar'
        });

        if (result.isConfirmed) {
            try {
                await api.delete(`/roles/${rolId}`);
                Swal.fire('Eliminado', 'El rol ha sido eliminado.', 'success');
                fetchRoles();
            } catch (error) {
                console.error(error);
                Swal.fire('Error', 'No se pudo eliminar el rol. Tal vez esté asignado a usuarios.', 'error');
            }
        }
    };

    const handleSave = async () => {
        if (!editingRol.nombre.trim()) {
            Swal.fire('Error', 'El nombre del rol es obligatorio', 'warning');
            return;
        }

        try {
            const payload = {
                nombre: editingRol.nombre,
                descripcion: editingRol.descripcion,
                permisos_ids: editingRol.permisos.map(p => p.id) // Enviamos solo IDs al backend
            };

            if (editingRol.id) {
                // Update
                await api.put(`/roles/${editingRol.id}`, payload);
            } else {
                // Create
                await api.post('/roles/', payload);
            }

            Swal.fire('Éxito', 'Rol guardado correctamente', 'success');
            setIsEditing(false);
            setEditingRol(null);
            fetchRoles();
        } catch (error) {
            console.error(error);
            Swal.fire('Error', 'Hubo un error al guardar el rol', 'error');
        }
    };

    const togglePermiso = (permisoItem) => {
        if (!editingRol) return;

        const hasPermiso = editingRol.permisos.some(p => p.id === permisoItem.id);
        let newPermisos = [];

        if (hasPermiso) {
            newPermisos = editingRol.permisos.filter(p => p.id !== permisoItem.id);
        } else {
            newPermisos = [...editingRol.permisos, permisoItem];
        }

        setEditingRol({ ...editingRol, permisos: newPermisos });
    };

    // Agrupar permisos por modulo (prefix antes de :)
    const groupedPermisos = allPermisos.reduce((acc, p) => {
        const prefix = p.nombre.split(':')[0] || 'Otros';
        if (!acc[prefix]) acc[prefix] = [];
        acc[prefix].push(p);
        return acc;
    }, {});

    // Filtrar grupos/permisos si hay búsqueda
    const filteredGroups = Object.keys(groupedPermisos).filter(group => {
        if (!permisoSearch) return true;
        // Si el grupo empiza con el search
        if (group.toLowerCase().includes(permisoSearch.toLowerCase())) return true;
        // O si alguno de sus permisos lo incluye
        return groupedPermisos[group].some(p => p.nombre.toLowerCase().includes(permisoSearch.toLowerCase()));
    });

    return (
        <div className="p-4 bg-white rounded shadow-md h-full flex flex-col">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold flex items-center text-slate-700">
                    <FaTags className="mr-2" /> Gestión de Roles y Perfiles
                </h2>
                {!isEditing && (
                    <button onClick={handleCreateClick} className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 flex items-center">
                        <FaPlus className="mr-2" /> Crear Nuevo Rol
                    </button>
                )}
            </div>

            {isEditing ? (
                // --- VISTA DE EDICIÓN ---
                <div className="flex flex-col flex-1 overflow-hidden">
                    <div className="mb-4 grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-slate-600">Nombre del Rol</label>
                            <input
                                type="text"
                                className="w-full border p-2 rounded"
                                placeholder="Ej: Auditor Externo, Gerente..."
                                value={editingRol.nombre}
                                onChange={e => setEditingRol({ ...editingRol, nombre: e.target.value })}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-600">Descripción</label>
                            <input
                                type="text"
                                className="w-full border p-2 rounded"
                                placeholder="Descripción corta..."
                                value={editingRol.descripcion || ''}
                                onChange={e => setEditingRol({ ...editingRol, descripcion: e.target.value })}
                            />
                        </div>
                    </div>

                    <div className="flex-1 overflow-y-auto border rounded p-4 bg-slate-50">
                        <div className="flex justify-between items-center mb-2 sticky top-0 bg-slate-50 pb-2 border-b z-10">
                            <h3 className="font-semibold">Asignar Permisos (Basado en Menú)</h3>
                            <div className="space-x-2">
                                <button
                                    onClick={() => setEditingRol({ ...editingRol, permisos: [...allPermisos] })}
                                    className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded hover:bg-blue-200 font-medium"
                                >
                                    Seleccionar Todo
                                </button>
                                <button
                                    onClick={() => setEditingRol({ ...editingRol, permisos: [] })}
                                    className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded hover:bg-gray-200 font-medium"
                                >
                                    Deseleccionar Todo
                                </button>
                            </div>
                        </div>

                        <div className="flex overflow-x-auto gap-4 pb-4">
                            {menuStructure.map(module => {
                                // Excluir módulo Favoritos si no tiene permisos relevantes o es de frontend puro
                                if (module.id === 'favoritos') return null;

                                return (
                                    <div key={module.id} className="min-w-[300px] w-[300px] bg-white p-3 rounded shadow-sm border flex-shrink-0 flex flex-col">
                                        <div className="flex items-center gap-2 border-b pb-2 mb-2 bg-slate-100 p-2 rounded-t -mx-3 -mt-3">
                                            {module.icon && <module.icon className="text-gray-500" />}
                                            <div className="flex-1">
                                                <h4 className="font-bold text-slate-700 uppercase text-xs">{module.name}</h4>
                                            </div>
                                            {/* Checkbox para el permiso del Módulo (Padre) */}
                                            {module.permission && (() => {
                                                const permissionObj = allPermisos.find(p => p.nombre === module.permission);
                                                if (permissionObj) {
                                                    const isSelected = editingRol.permisos.some(p => p.id === permissionObj.id);
                                                    return (
                                                        <label className="flex items-center space-x-1 cursor-pointer" title="Habilitar Módulo Completo">
                                                            <input
                                                                type="checkbox"
                                                                checked={isSelected}
                                                                onChange={() => togglePermiso(permissionObj)}
                                                                className="form-checkbox h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                                                            />
                                                            <span className="text-[10px] font-semibold text-blue-800 uppercase">Acceso</span>
                                                        </label>
                                                    );
                                                }
                                                return null;
                                            })()}
                                        </div>

                                        <div className="space-y-3 overflow-y-auto max-h-[400px]">
                                            {/* Render Links Standard */}
                                            {module.links && module.links.map(link => {
                                                // Buscar el permiso en allPermisos por nombre
                                                const permissionObj = allPermisos.find(p => p.nombre === link.permission);
                                                if (!permissionObj) return null; // Si no existe en BD, no mostramos (o mostraremos deshabilitado)

                                                const isSelected = editingRol.permisos.some(p => p.id === permissionObj.id);

                                                return (
                                                    <label key={link.href} className="flex items-start space-x-2 text-sm cursor-pointer hover:bg-slate-100 p-2 rounded transition-colors">
                                                        <input
                                                            type="checkbox"
                                                            checked={isSelected}
                                                            onChange={() => togglePermiso(permissionObj)}
                                                            className="form-checkbox h-4 w-4 text-blue-600 mt-1"
                                                        />
                                                        <div>
                                                            <div className="font-medium text-gray-800">{link.name}</div>
                                                            {link.description && <div className="text-xs text-gray-500 leading-tight">{link.description}</div>}
                                                            <div className="text-[10px] text-gray-400 font-mono mt-0.5">{link.permission}</div>
                                                        </div>
                                                    </label>
                                                );
                                            })}

                                            {/* Render Subgroups (Admin) */}
                                            {module.subgroups && module.subgroups.map(subgroup => (
                                                <div key={subgroup.title} className="mt-2 text-xs">
                                                    <h5 className="font-semibold text-slate-500 mb-1 ml-1 flex items-center gap-1">
                                                        {subgroup.icon && <subgroup.icon size={10} />}
                                                        {subgroup.title}
                                                    </h5>
                                                    <div className="pl-2 border-l-2 border-gray-100 space-y-2">
                                                        {subgroup.links.map(link => {
                                                            const permissionObj = allPermisos.find(p => p.nombre === link.permission);
                                                            if (!permissionObj) return null;

                                                            const isSelected = editingRol.permisos.some(p => p.id === permissionObj.id);

                                                            return (
                                                                <label key={link.href} className="flex items-start space-x-2 text-sm cursor-pointer hover:bg-slate-100 p-2 rounded transition-colors">
                                                                    <input
                                                                        type="checkbox"
                                                                        checked={isSelected}
                                                                        onChange={() => togglePermiso(permissionObj)}
                                                                        className="form-checkbox h-4 w-4 text-blue-600 mt-1"
                                                                    />
                                                                    <div>
                                                                        <div className="font-medium text-gray-800">{link.name}</div>
                                                                        {link.description && <div className="text-xs text-gray-500 leading-tight">{link.description}</div>}
                                                                        <div className="text-[10px] text-gray-400 font-mono mt-0.5">{link.permission}</div>
                                                                    </div>
                                                                </label>
                                                            );
                                                        })}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>

                    <div className="mt-4 flex justify-end space-x-2">
                        <button onClick={() => setIsEditing(false)} className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600">
                            <FaTimes className="mr-1 inline" /> Cancelar
                        </button>
                        <button onClick={handleSave} className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
                            <FaSave className="mr-1 inline" /> Guardar Rol
                        </button>
                    </div>
                </div>
            ) : (
                // --- VISTA DE LISTA ---
                <div className="flex-1 overflow-y-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Descripción</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Alcance</th>
                                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {roles.map((rol) => (
                                <tr key={rol.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{rol.nombre}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{rol.descripcion}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {rol.empresa_id ? <span className="bg-blue-100 text-blue-800 px-2 rounded-full text-xs">Empresa</span> : <span className="bg-purple-100 text-purple-800 px-2 rounded-full text-xs">Global / Sistema</span>}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                        <button onClick={() => handleEditClick(rol)} className="text-indigo-600 hover:text-indigo-900 mr-4">
                                            <FaEdit size={16} />
                                        </button>
                                        <button onClick={() => handleDeleteClick(rol.id)} className="text-red-600 hover:text-red-900">
                                            <FaTrash size={16} />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    {roles.length === 0 && !loading && (
                        <p className="text-center text-gray-500 mt-4">No hay roles definidos.</p>
                    )}
                </div>
            )}
        </div>
    );
}
