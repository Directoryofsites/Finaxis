"use client";
import React from 'react';
import { FaTimes, FaSignOutAlt } from 'react-icons/fa';
import { menuStructure } from '../lib/menuData';

export default function Sidebar({
    activeModuleId,
    onMenuClick,
    isMenuOpen,
    setIsMenuOpen,
    user,
    logout
}) {
    return (
        <aside
            className={`fixed inset-y-0 left-0 z-30 transform ${isMenuOpen ? 'translate-x-0' : '-translate-x-full'} 
               md:relative md:translate-x-0 transition duration-200 ease-in-out 
               w-64 bg-slate-900 flex flex-col shadow-2xl md:shadow-none`}
        >
            {/* Encabezado del Sidebar (Logo y Versión) */}
            <div className="p-4 flex items-center justify-between h-16 bg-slate-900 border-b border-slate-700">
                <h2 className="text-xl font-bold text-white">
                    Finaxis <span className="text-sm font-light text-blue-400">v1.0</span>
                </h2>
                <button
                    className="md:hidden text-slate-400 hover:text-white"
                    onClick={() => setIsMenuOpen(false)}
                >
                    <FaTimes size={20} />
                </button>
            </div>

            {/* Contenedor de Items del Menú (Nivel 1: El Árbol Principal) */}
            <div className="flex-1 overflow-y-auto pt-4 space-y-1">
                {menuStructure.map((module) => {
                    // Verificar permisos
                    if (module.permission) {
                        const userPermissions = user?.roles?.flatMap(r => r.permisos?.map(p => p.nombre)) || [];
                        if (!userPermissions.includes(module.permission)) {
                            // Si no tiene el permiso del módulo, verificar si tiene AL MENOS UN permiso de los sub-items (fallback inteligente)
                            // Esto es opcional, pero ayuda si el permiso padre no está asignado explícitamente pero sí uno hijo.
                            // Para simplificar: Estricto. Si requiere permiso de módulo y no lo tiene, chao.
                            return null;
                        }
                    }

                    return (
                        <button
                            key={module.id}
                            type="button"
                            onClick={(e) => {
                                e.preventDefault();
                                onMenuClick(module.id);
                            }}
                            className={`flex items-center p-3 transition duration-150 rounded-lg mx-2 text-sm font-semibold w-[90%]
                            ${activeModuleId === module.id ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-300 hover:bg-slate-700 hover:text-white'}`}
                            title={module.name}
                        >
                            <module.icon className="w-5 h-5 mr-3" />
                            <span>{module.name}</span>
                        </button>
                    );
                })}
            </div>

            {/* Pie de página del Sidebar (Cerrar Sesión) */}
            <div className="p-4 border-t border-slate-700 bg-slate-900">
                <div className="flex flex-col space-y-2 text-white">
                    <p className="text-sm font-medium text-blue-300 truncate">Sesión: {user?.email}</p>
                    <button
                        onClick={logout}
                        className="flex items-center justify-center p-2 rounded-lg bg-red-600 hover:bg-red-700 transition duration-150 text-sm font-semibold"
                    >
                        <FaSignOutAlt className="mr-2" />
                        Cerrar Sesión
                    </button>
                </div>
            </div>
        </aside>
    );
}
