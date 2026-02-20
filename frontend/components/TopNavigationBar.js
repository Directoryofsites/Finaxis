"use client";
import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { useRouter, usePathname, useSearchParams } from 'next/navigation';
import {
    FaUserCircle, FaSignOutAlt, FaSearch, FaTimes, FaArrowLeft,
    FaCog, FaBuilding, FaBars, FaTh, FaMicrophone, FaHome,
    FaMagic, FaTerminal, FaExternalLinkAlt, FaArrowRight, FaHistory, FaSave, FaBolt, FaStop, FaClock
} from 'react-icons/fa';
import { menuStructure } from '../lib/menuData';
import { useAuth } from '../app/context/AuthContext';
import { useSmartSearch } from '../app/hooks/useSmartSearch';
import AssistantOverlay from '../app/components/VoiceAssistant/AssistantOverlay';

// Mapa de colores vibrantes inspirados en Google Workspace (Docs = Azul, Sheets = Verde, YouTube = Rojo, etc.)
const MODULE_COLORS = {
    'contabilidad': 'bg-blue-50 text-blue-600 border-blue-100 group-hover:bg-blue-600 group-hover:text-white group-hover:shadow-blue-300',
    'nomina': 'bg-red-50 text-red-600 border-red-100 group-hover:bg-red-600 group-hover:text-white group-hover:shadow-red-300',
    'facturacion': 'bg-green-50 text-green-600 border-green-100 group-hover:bg-green-600 group-hover:text-white group-hover:shadow-green-300',
    'inventarios': 'bg-yellow-50 text-yellow-600 border-yellow-100 group-hover:bg-yellow-500 group-hover:text-white group-hover:shadow-yellow-300',
    'terceros': 'bg-purple-50 text-purple-600 border-purple-100 group-hover:bg-purple-600 group-hover:text-white group-hover:shadow-purple-300',
    'analisis_financiero': 'bg-cyan-50 text-cyan-600 border-cyan-100 group-hover:bg-cyan-600 group-hover:text-white group-hover:shadow-cyan-300',
    'centros_costo': 'bg-indigo-50 text-indigo-600 border-indigo-100 group-hover:bg-indigo-600 group-hover:text-white group-hover:shadow-indigo-300',
    'impuestos': 'bg-pink-50 text-pink-600 border-pink-100 group-hover:bg-pink-600 group-hover:text-white group-hover:shadow-pink-300',
    'activos': 'bg-slate-50 text-slate-600 border-slate-100 group-hover:bg-slate-600 group-hover:text-white group-hover:shadow-slate-300',
    'ph': 'bg-teal-50 text-teal-600 border-teal-100 group-hover:bg-teal-600 group-hover:text-white group-hover:shadow-teal-300',
    'produccion': 'bg-orange-50 text-orange-600 border-orange-100 group-hover:bg-orange-600 group-hover:text-white group-hover:shadow-orange-300',
    'conciliacion_bancaria': 'bg-emerald-50 text-emerald-600 border-emerald-100 group-hover:bg-emerald-600 group-hover:text-white group-hover:shadow-emerald-300',
    'administracion': 'bg-gray-50 text-gray-600 border-gray-100 group-hover:bg-gray-600 group-hover:text-white group-hover:shadow-gray-300',
    'default': 'bg-indigo-50 text-indigo-600 border-indigo-100 group-hover:bg-indigo-600 group-hover:text-white group-hover:shadow-indigo-300'
};

/**
 * TopNavigationBar - Premium App Launcher & Smart AI Search
 */
export default function TopNavigationBar() {
    const { user, logout } = useAuth();
    const router = useRouter();

    // Hooks para el buscador global de IA extraídos del SmartSearch viejo
    const {
        query, setQuery, results, isListening, isThinking, isCommandMode,
        commandHistory, library, selectedIndex, setSelectedIndex,
        toggleListening, processVoiceCommand, handleSelectResult, addToLibrary, showHistory
    } = useSmartSearch();

    const [showAssistant, setShowAssistant] = useState(false);
    const [isSearchFocused, setIsSearchFocused] = useState(false);

    // Estados del Waffle Launcher
    const [isWaffleOpen, setIsWaffleOpen] = useState(false);
    const [waffleActiveModule, setWaffleActiveModule] = useState(null);
    const [userMenuOpen, setUserMenuOpen] = useState(false);
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    // Cerrar clickeando afuera (Menús y Dropdowns)
    const waffleRef = useRef(null);
    const userRef = useRef(null);
    const searchRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (e) => {
            if (waffleRef.current && !waffleRef.current.contains(e.target)) {
                setIsWaffleOpen(false);
                setWaffleActiveModule(null);
            }
            if (userRef.current && !userRef.current.contains(e.target)) {
                setUserMenuOpen(false);
            }
            if (searchRef.current && !searchRef.current.contains(e.target)) {
                // Pequeño delay para permitir que el click en una opción funcione
                setTimeout(() => setIsSearchFocused(false), 200);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const closeAll = () => {
        setIsWaffleOpen(false);
        setUserMenuOpen(false);
        setWaffleActiveModule(null);
        setIsMobileMenuOpen(false);
        setIsSearchFocused(false);
    };

    const handleSearchSubmit = (e) => {
        if (e) e.preventDefault();

        // Evitar accionar si el usuario selecciona una ruta con teclado
        if (results.length > 0 && selectedIndex >= 0) {
            handleSelectResult(results[selectedIndex]);
            closeAll();
            return;
        }

        // Enviar a la Inferencia IA
        if (query.trim()) {
            processVoiceCommand(query);
            setIsSearchFocused(false);
            document.getElementById('finaxis-global-search')?.blur();
        }
    };

    const handleCommandClick = (text) => {
        setQuery(text);
        document.getElementById('finaxis-global-search')?.focus();
    };

    const handleKeyDown = (e) => {
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            setSelectedIndex(prev => Math.min(prev + 1, results.length - 1));
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            setSelectedIndex(prev => Math.max(0, prev - 1));
        } else if (e.key === 'Enter') {
            handleSearchSubmit(e);
        }
    };

    if (!user) return null;

    return (
        <>
            {/* BARRA SUPERIOR ULTRA LIMPIA */}
            <header className="fixed top-0 left-0 right-0 z-[99999] bg-[#ffffff] backdrop-blur-md text-gray-800 shadow-sm h-14 flex items-center justify-between px-4 select-none transition-all duration-300">

                {/* Lado Izquierdo: Botón Inicio Restaurado */}
                <div className="flex items-center h-full min-w-max">
                    {/* Hamburguesa Móvil */}
                    <button onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)} className="md:hidden p-2 text-gray-600 hover:bg-gray-100 rounded-full transition-colors mr-2">
                        <FaBars size={20} />
                    </button>

                    {/* Botón clásico Inicio (Home) */}
                    <button
                        onClick={() => router.push('/')}
                        className="hidden md:flex items-center px-4 py-2 font-bold text-gray-700 hover:bg-blue-50 hover:text-blue-600 rounded-full transition-colors group"
                        title="Ir a Inicio"
                    >
                        <FaHome size={20} className="mr-2 text-gray-400 group-hover:text-blue-600 transition-colors" />
                        <span className="text-sm">Inicio</span>
                    </button>
                </div>

                {/* CENTRO: BUSCADOR IA / ASISTENTE VIRTUAL CENTRAL (REF: PANTALLAZO DEL CLIENTE) */}
                <div className="hidden lg:flex items-center justify-center flex-1 max-w-[800px] mx-6 relative" ref={searchRef}>

                    {/* Asistente Flotante Voz */}
                    {showAssistant && (
                        <AssistantOverlay onClose={() => setShowAssistant(false)} />
                    )}

                    <form onSubmit={handleSearchSubmit} className="w-[500px] xl:w-[650px] relative group h-[44px]">

                        {/* Glow de la IA */}
                        <div className={`absolute -inset-[1px] blur opacity-40 rounded-[28px] transition duration-1000 group-hover:duration-200 pointer-events-none 
                            ${isListening ? 'bg-gradient-to-r from-red-500 to-orange-500 animate-pulse' :
                                isCommandMode ? 'bg-gradient-to-r from-green-400 to-emerald-600' : 'bg-gradient-to-r from-blue-300 via-purple-300 to-pink-300'}
                        `}></div>

                        <div className={`relative flex items-center w-full h-full bg-white shadow-[0_4px_15px_rgba(200,100,200,0.1)] transition-all duration-300 transform border
                            ${(showHistory && isSearchFocused && (results.length > 0 || (commandHistory.length > 0 && !query))) ? 'rounded-t-[20px] rounded-b-none border-gray-100 shadow-xl' : 'rounded-full group-hover:shadow-[0_6px_25px_rgba(200,100,200,0.15)] border-transparent'}
                            ${isCommandMode ? 'ring-2 ring-emerald-200 border-emerald-400' : ''}
                        `}>
                            {/* Icono izquierdo estricto */}
                            <div className="pl-4 pr-3 text-gray-400">
                                {isThinking ? (
                                    <FaMagic className="text-purple-500 animate-spin-slow text-[16px]" />
                                ) : isCommandMode ? (
                                    <FaTerminal className="text-green-500 text-[16px] animate-pulse" />
                                ) : (
                                    <FaSearch className="text-[#a0aabf] text-[16px]" />
                                )}
                            </div>

                            {/* Input exacto ref: "Describe qué deseas hacer..." */}
                            <input
                                id="finaxis-global-search"
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                onKeyDown={handleKeyDown}
                                onFocus={() => setIsSearchFocused(true)}
                                placeholder={isListening ? "Te escucho..." : (isCommandMode ? "Escribe un comando IA..." : "Describe qué deseas hacer...")}
                                className={`block w-full h-full bg-transparent focus:outline-none sm:text-[15px] font-medium transition-colors border-none pt-[1px]
                                    ${isCommandMode ? 'text-green-800 placeholder-green-700/50 font-mono' : 'text-gray-700 placeholder-[#a0aabf]'}
                                `}
                                autoComplete="off"
                            />

                            <div className="pr-3 pl-2 flex items-center h-full">
                                <button
                                    type="button"
                                    onClick={toggleListening}
                                    className={`p-1.5 rounded-full transition-colors flex items-center justify-center
                                        ${isListening ? 'bg-red-500 text-white animate-pulse' : 'text-[#a0aabf] hover:text-blue-500 hover:bg-gray-100'}
                                    `}
                                    title="Modo Voz Finaxis"
                                >
                                    {isListening ? <FaStop size={14} /> : <FaMicrophone size={16} />}
                                </button>

                                {query.trim() && !isCommandMode && (
                                    <button
                                        type="submit"
                                        className="ml-1 flex items-center justify-center p-1.5 w-7 h-7 bg-blue-600 text-white rounded-full hover:bg-blue-700 transform transition-transform hover:scale-105 active:scale-95"
                                    >
                                        <FaArrowRight size={11} />
                                    </button>
                                )}
                                {query.trim() && isCommandMode && (
                                    <button
                                        type="submit"
                                        className="ml-1 flex items-center justify-center p-1.5 w-7 h-7 bg-emerald-500 text-white rounded-full hover:bg-emerald-600 transition-transform"
                                    >
                                        <FaBolt size={11} />
                                    </button>
                                )}
                            </div>
                        </div>

                        {/* DESPLEGABLE DE RESULTADOS / INTENCIONES IA */}
                        {showHistory && isSearchFocused && (
                            <div className="absolute top-[100%] left-0 right-0 bg-white border border-t-0 border-gray-100 rounded-b-[20px] shadow-2xl max-h-[60vh] overflow-y-auto animate-in fade-in slide-in-from-top-1 scrollbar-thin scrollbar-thumb-gray-200 scrollbar-track-transparent z-[100020]">
                                {results.length > 0 ? (
                                    <>
                                        <ul>
                                            {results.map((item, index) => (
                                                <li
                                                    key={index}
                                                    onClick={() => { handleSelectResult(item); closeAll(); }}
                                                    className={`px-5 py-3 cursor-pointer border-b border-gray-50 last:border-0 flex items-center gap-3 transition-colors
                                                        ${index === selectedIndex ? (isCommandMode ? 'bg-green-50' : 'bg-blue-50') : 'hover:bg-gray-50'}
                                                    `}
                                                >
                                                    <span className={`p-2 rounded-lg ${item.isCommand ? (index === selectedIndex ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-green-500') : (index === selectedIndex ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-500')}`}>
                                                        {item.icon ? <item.icon /> : <FaExternalLinkAlt />}
                                                    </span>
                                                    <div className="flex-1 overflow-hidden">
                                                        <div className={`font-semibold text-[14px] truncate flex items-center gap-2 ${isCommandMode ? 'text-green-800 font-mono' : 'text-gray-800'}`}>
                                                            {item.name}
                                                        </div>
                                                        <div className="text-[11px] text-gray-400 truncate uppercase tracking-wider font-semibold mt-0.5">{item.category} • {item.description}</div>
                                                    </div>
                                                </li>
                                            ))}
                                        </ul>
                                    </>
                                ) : !query && commandHistory.length > 0 && (
                                    <div className="py-2">
                                        <div className="px-5 py-2 text-[10px] font-bold text-gray-400 uppercase tracking-widest flex items-center gap-2">
                                            <FaHistory /> Búsquedas Recientes
                                        </div>
                                        <ul>
                                            {commandHistory.slice(0, 5).map((cmd, idx) => (
                                                <li
                                                    key={idx}
                                                    className="px-5 py-2.5 cursor-pointer hover:bg-gray-50 flex items-center gap-3 group transition-colors"
                                                >
                                                    <FaClock className="text-gray-300 text-xs" />
                                                    <span className="text-gray-600 text-[14px] group-hover:text-blue-600 flex-1 font-medium truncate" onClick={() => handleCommandClick(cmd)}>{cmd}</span>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        )}
                    </form>
                </div>

                {/* Lado Derecho: Waffle y Perfil (Con padding extra mr-12 para evitar cruce con RightSidebar) */}
                <div className="flex items-center space-x-3 relative h-full mr-2 md:mr-10 py-2">

                    {/* El Waffle Button (App Launcher) */}
                    <div className="relative flex items-center h-full" ref={waffleRef}>
                        <button
                            onClick={() => {
                                setIsWaffleOpen(!isWaffleOpen);
                                setWaffleActiveModule(null);
                                setUserMenuOpen(false);
                            }}
                            className={`p-2 rounded-full transition-all duration-200 cursor-pointer 
                                ${isWaffleOpen ? 'bg-gray-100 text-gray-800 ring-4 ring-gray-100' : 'text-gray-500 hover:bg-gray-100 hover:text-gray-800'}`}
                            title="Aplicaciones Finaxis"
                        >
                            <FaTh size={20} className={isWaffleOpen ? "scale-105 transition-transform" : ""} />
                        </button>

                        {/* EL POPOVER DEL WAFFLE (APP LAUNCHER) */}
                        {isWaffleOpen && (
                            <div className="absolute top-[48px] right-0 w-[420px] max-h-[85vh] bg-[#fdfdfd] border border-gray-200/60 shadow-[0_12px_40px_rgba(0,0,0,0.15)] rounded-3xl z-[100010] flex flex-col overflow-hidden animate-in fade-in slide-in-from-top-4 duration-200">

                                {/* Header del Waffle */}
                                <div className={`px-4 h-14 border-b border-gray-100 flex items-center bg-white sticky top-0 z-10 transition-all ${waffleActiveModule ? 'justify-between' : 'justify-center'}`}>
                                    {waffleActiveModule ? (
                                        <button
                                            onClick={() => setWaffleActiveModule(null)}
                                            className="flex items-center text-sm font-semibold text-gray-500 hover:text-blue-600 transition-colors group px-2 py-1 rounded-lg hover:bg-blue-50"
                                        >
                                            <FaArrowLeft className="mr-2 group-hover:-translate-x-1 transition-transform" />
                                            Atrás
                                        </button>
                                    ) : (
                                        <div className="flex flex-col items-center select-none pt-1">
                                            <span className="font-extrabold text-gray-800 text-base">Finaxis Apps Suite</span>
                                        </div>
                                    )}
                                </div>

                                {/* Contenido del Waffle (Scrollable) */}
                                <div className="p-5 overflow-y-auto scrollbar-hide flex-1 bg-[#fcfcfc]">
                                    {!waffleActiveModule ? (
                                        // VISTA 1: GRID DE APLICACIONES PRINCIPALES (Iconos VIBRANTES)
                                        <div className="grid grid-cols-3 gap-y-7 gap-x-2">
                                            {menuStructure.map((module) => {
                                                if (module.permission) {
                                                    const userPermissions = user?.roles?.flatMap(r => r.permisos?.map(p => p.nombre)) || [];
                                                    if (!userPermissions.includes(module.permission)) return null;
                                                }

                                                // Asignar color temático al botón (tipo Google)
                                                const colorClasses = MODULE_COLORS[module.id] || MODULE_COLORS['default'];

                                                return (
                                                    <div
                                                        key={module.id}
                                                        onClick={() => {
                                                            if (module.route) {
                                                                router.push(module.route);
                                                                closeAll();
                                                            } else {
                                                                setWaffleActiveModule(module);
                                                            }
                                                        }}
                                                        className="flex flex-col items-center justify-start cursor-pointer group p-2 rounded-2xl hover:bg-white hover:shadow-[0_4px_20px_rgba(0,0,0,0.06)] border border-transparent transition-all duration-300"
                                                    >
                                                        {/* CONTENEDOR DE ICONO MÁS GRANDE Y COLORIDO */}
                                                        <div className={`w-[72px] h-[72px] rounded-[1.3rem] border flex items-center justify-center transition-all duration-300 group-hover:scale-[1.08] group-hover:shadow-lg ${colorClasses}`}>
                                                            {module.icon && <module.icon size={36} />}
                                                        </div>
                                                        <span className="mt-3 text-[13px] font-bold text-gray-700 group-hover:text-black text-center leading-tight">
                                                            {module.name}
                                                        </span>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    ) : (
                                        // VISTA 2: ENLACES DENTRO DEL MÓDULO SELECCIONADO
                                        <div className="flex flex-col space-y-2 animate-in slide-in-from-right-8 fade-in duration-300">

                                            <div className="flex items-center mb-4 select-none pb-2 border-b border-gray-100">
                                                <div className={`w-12 h-12 rounded-xl border flex items-center justify-center mr-4 ${MODULE_COLORS[waffleActiveModule.id]?.replace(/group-hover:[^\s]+/g, '') || MODULE_COLORS['default'].replace(/group-hover:[^\s]+/g, '')}`}>
                                                    {waffleActiveModule.icon && <waffleActiveModule.icon size={26} />}
                                                </div>
                                                <div className="flex flex-col">
                                                    <h3 className="font-extrabold text-gray-800 text-[1.35rem] tracking-tight leading-none">{waffleActiveModule.name}</h3>
                                                    <span className="text-[11px] text-gray-400 font-medium mt-1 uppercase tracking-wider">Módulo Activo</span>
                                                </div>
                                            </div>

                                            <div className="space-y-1">
                                                {waffleActiveModule.links?.map(link => {
                                                    const restrictedSafeHrefs = ['/contabilidad/documentos', '/contabilidad/captura-rapida', '/contabilidad/facturacion', '/contabilidad/compras', '/contabilidad/traslados'];
                                                    if (user?.empresa?.modo_operacion === 'AUDITORIA_READONLY' && restrictedSafeHrefs.includes(link.href)) return null;

                                                    return (
                                                        <Link
                                                            key={link.href}
                                                            href={link.href}
                                                            onClick={closeAll}
                                                            className="flex flex-col p-3 rounded-2xl hover:bg-gray-50 hover:shadow-sm border border-transparent hover:border-gray-200 transition-all group"
                                                        >
                                                            <div className="flex items-center">
                                                                <span className="w-8 h-8 rounded-full bg-gray-100 text-gray-500 flex items-center justify-center mr-3 group-hover:bg-blue-500 group-hover:text-white transition-all duration-300">
                                                                    {link.icon && <link.icon size={14} />}
                                                                </span>
                                                                <span className="text-[14px] font-bold text-gray-700 group-hover:text-blue-700 transition-colors">{link.name}</span>
                                                            </div>
                                                            {link.description && (
                                                                <p className="text-[12px] text-gray-400 pl-11 mt-1 leading-tight font-medium">{link.description}</p>
                                                            )}
                                                        </Link>
                                                    );
                                                })}
                                            </div>

                                            {waffleActiveModule.subgroups?.filter(s => s.links?.length > 0).map(sub => (
                                                <div key={sub.title} className="mt-6 pt-4 border-t border-gray-100">
                                                    <div className="px-3 mb-3 flex flex-col">
                                                        <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">{sub.title}</span>
                                                    </div>
                                                    <div className="grid grid-cols-2 gap-2 px-1">
                                                        {sub.links.map(link => (
                                                            <Link
                                                                key={link.href}
                                                                href={link.href}
                                                                onClick={closeAll}
                                                                className="flex items-center px-3 py-3 bg-gray-50 rounded-xl hover:bg-blue-50 hover:shadow-sm border border-transparent text-gray-600 hover:text-blue-700 transition-all group"
                                                            >
                                                                <span className="mr-2 opacity-60 group-hover:opacity-100 transition-opacity text-blue-500">
                                                                    {link.icon && <link.icon size={14} />}
                                                                </span>
                                                                <span className="text-[13px] font-bold truncate">{link.name}</span>
                                                            </Link>
                                                        ))}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Perfil de Usuario */}
                    <div className="relative flex items-center h-full" ref={userRef}>
                        <div
                            className="flex items-center space-x-2 p-1.5 rounded-full hover:bg-gray-100 transition-colors group cursor-pointer border border-transparent"
                            onClick={() => {
                                setUserMenuOpen(!userMenuOpen);
                                setIsWaffleOpen(false);
                            }}
                        >
                            <div className="w-[34px] h-[34px] rounded-full bg-gradient-to-tr from-gray-300 to-gray-400 flex items-center justify-center text-white group-hover:from-blue-500 group-hover:to-indigo-600 shadow-sm transition-all">
                                <FaUserCircle size={22} />
                            </div>
                        </div>

                        {userMenuOpen && (
                            <div className="absolute top-[48px] right-0 w-64 bg-white border border-gray-200 shadow-xl rounded-2xl z-[100010] py-2 animate-in fade-in slide-in-from-top-2 duration-150">
                                <div className="px-5 py-3 border-b border-gray-100 bg-gray-50/50 rounded-t-2xl">
                                    <p className="text-sm font-bold text-gray-800 truncate">{user?.nombre || 'Usuario'}</p>
                                    <p className="text-xs font-medium text-gray-500 mt-0.5 truncate">{user?.role || 'Administrador'}</p>
                                </div>
                                <div className="py-2">
                                    <button onClick={() => { router.push('/portal'); closeAll(); }} className="w-full text-left px-5 py-2.5 text-sm text-gray-600 font-medium hover:bg-gray-50 hover:text-gray-900 flex items-center transition-colors">
                                        <FaBuilding className="mr-3 text-gray-400" /> Mis Empresas
                                    </button>
                                    <button onClick={() => { router.push('/admin/configuracion/perfil'); closeAll(); }} className="w-full text-left px-5 py-2.5 text-sm text-gray-600 font-medium hover:bg-gray-50 hover:text-gray-900 flex items-center transition-colors">
                                        <FaCog className="mr-3 text-gray-400" /> Configuración
                                    </button>
                                </div>
                                <div className="border-t border-gray-100 py-2">
                                    <button onClick={() => { logout(); closeAll(); }} className="w-full text-left px-5 py-2.5 text-sm font-bold text-red-500 hover:bg-red-50 hover:text-red-700 flex items-center transition-colors">
                                        <FaSignOutAlt className="mr-3" /> Cerrar Sesión
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </header>

            {/* Overlay para móvil clásico */}
            {isMobileMenuOpen && (
                <div className="fixed inset-0 bg-gray-900/40 z-[100005] md:hidden backdrop-blur-sm" onClick={() => setIsMobileMenuOpen(false)}>
                    {/* Contenido omitido de móvil en pro de visibilidad del App Launcher */}
                </div>
            )}
        </>
    );
}
