"use client";
import React, { useState, useEffect, useMemo, useRef, useContext } from 'react';
import Link from 'next/link';
import { useRouter, usePathname, useSearchParams } from 'next/navigation';
import { FaUserCircle, FaSignOutAlt, FaSearch, FaTimes, FaKeyboard, FaArrowRight, FaCog } from 'react-icons/fa';
import { menuStructure } from '../lib/menuData';
import { useAuth } from '../app/context/AuthContext';

/**
 * TopNavigationBar - Versión 6.2 (ACCENT INSENSITIVE)
 * 
 * 1. FIXED: renderMnemonic now handles accents (Nómina -> 'm' or 'o').
 * 2. Mnemonic Logic: keys mapped to visual characters.
 */
export default function TopNavigationBar() {
    const { user, logout } = useAuth();
    const router = useRouter(); // Explicitly defining router here if not already defined
    const pathname = usePathname();
    const searchParams = useSearchParams();

    // ZEN MODE LOGIC:
    // Global Zen Mode: El menú siempre debe ocultarse automáticamente (replegarse) para maximizar espacio.
    const isZenMode = true;

    // Estados
    const [isVisible, setIsVisible] = useState(!isZenMode); // Inicialmente visible si NO es ZenMode
    const [isMenuOpen, setIsMenuOpen] = useState(null);
    const [activeDropdownLeft, setActiveDropdownLeft] = useState(0);
    const [altPressed, setAltPressed] = useState(false);
    const [focusedLinkIndex, setFocusedLinkIndex] = useState(-1);
    const [userMenuOpen, setUserMenuOpen] = useState(false);

    // Efecto para controlar la visibilidad basada en el modo
    useEffect(() => {
        if (!isZenMode) {
            setIsVisible(true);
        } else {
            setIsVisible(false);
        }
    }, [isZenMode]);

    // Referencias
    const buttonsRef = useRef({});
    const hoverTimeoutRef = useRef(null);

    // ... (rest of code) ...



    // ...


    const menuMap = useMemo(() => {
        const map = {};
        menuStructure.forEach(item => {
            if (item.mnemonic) {
                map[item.mnemonic.toLowerCase()] = item.id;
            }
        });
        return map;
    }, []);

    const closeAll = () => {
        setIsMenuOpen(null);
        setUserMenuOpen(false);
        // En ZenMode, ocultamos la barra al "cerrar todo" (mouseleave). 
        // En modo normal, la barra se queda visible.
        if (isZenMode) {
            setIsVisible(false);
        }
        setFocusedLinkIndex(-1);
    };

    // --- HOVER LOGIC ---
    const handleMouseEnter = (moduleId) => {
        if (hoverTimeoutRef.current) {
            clearTimeout(hoverTimeoutRef.current);
            hoverTimeoutRef.current = null;
        }

        // If it's a direct route module, don't open a menu, just keep bar visible
        const module = menuStructure.find(m => m.id === moduleId);
        if (module && !module.route) {
            openMenu(moduleId);
        }
        setIsVisible(true);
    };

    const handleMouseLeave = () => {
        const delay = isMenuOpen ? 300 : 50; // Cierre rápido si no hay menú desplagado
        hoverTimeoutRef.current = setTimeout(() => {
            closeAll();
        }, delay);
    };

    const handleDropdownEnter = () => {
        if (hoverTimeoutRef.current) {
            clearTimeout(hoverTimeoutRef.current);
            hoverTimeoutRef.current = null;
        }
    };

    // --- TECLADO GLOBAL ---
    useEffect(() => {
        const handleGlobalKeyDown = (e) => {
            // ALT Handling
            if (e.key === 'Alt') {
                e.preventDefault();
                setAltPressed(true);
                setIsVisible(true);
                return;
            }

            // ESCAPE
            if (e.key === 'Escape') {
                e.preventDefault();
                closeAll();
                setAltPressed(false);
                return;
            }

            // MENU ABIERTO: NAVEGACION COMPLETA
            if (isMenuOpen) {
                const currentModuleIndex = menuStructure.findIndex(m => m.id === isMenuOpen);
                const currentModule = menuStructure[currentModuleIndex];
                const allLinks = flattenLinks(currentModule);

                // --- 1. HORIZONTAL (CAMBIO DE MODULO) ---
                if (e.key === 'ArrowRight') {
                    e.preventDefault();
                    const nextIndex = (currentModuleIndex + 1) % menuStructure.length;
                    openMenu(menuStructure[nextIndex].id);
                    return;
                }
                if (e.key === 'ArrowLeft') {
                    e.preventDefault();
                    const prevIndex = (currentModuleIndex - 1 + menuStructure.length) % menuStructure.length;
                    openMenu(menuStructure[prevIndex].id);
                    return;
                }

                // --- 2. VERTICAL (LISTA) ---
                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    setFocusedLinkIndex(prev => Math.min(prev + 1, allLinks.length - 1));
                    return;
                }
                if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    setFocusedLinkIndex(prev => Math.max(0, prev - 1));
                    return;
                }
                if (e.key === 'Enter' && focusedLinkIndex >= 0) {
                    e.preventDefault();
                    if (allLinks[focusedLinkIndex]) {
                        router.push(allLinks[focusedLinkIndex].href);
                        closeAll();
                    }
                    return;
                }

                // --- 3. SUB-MNEMONICS (TECLAS DENTRO DEL MENU) ---
                if (!e.altKey && !e.ctrlKey && !e.metaKey && e.key.length === 1) {
                    const char = e.key.toLowerCase();
                    const linkMatch = allLinks.find(l => l.mnemonic && l.mnemonic.toLowerCase() === char);
                    if (linkMatch) {
                        e.preventDefault();
                        router.push(linkMatch.href);
                        closeAll();
                        return;
                    }
                }
            }

            // ACTIVACION CON ALT
            if (e.altKey && !e.ctrlKey && !e.metaKey) {
                const char = e.key.toLowerCase();

                if (char === 'm') {
                    e.preventDefault();
                    setIsVisible(prev => !prev);
                    return;
                }

                if (menuMap[char]) {
                    const moduleId = menuMap[char];
                    const module = menuStructure.find(m => m.id === moduleId);

                    if (module) {
                        e.preventDefault();
                        if (module.route) {
                            router.push(module.route);
                            closeAll();
                        } else {
                            setIsVisible(true);
                            openMenu(moduleId);
                        }
                    }
                    return;
                }
            }
        };

        const handleGlobalKeyUp = (e) => {
            if (e.key === 'Alt') {
                setAltPressed(false);
            }
        };

        window.addEventListener('keydown', handleGlobalKeyDown, { capture: true });
        window.addEventListener('keyup', handleGlobalKeyUp, { capture: true });

        return () => {
            window.removeEventListener('keydown', handleGlobalKeyDown, { capture: true });
            window.removeEventListener('keyup', handleGlobalKeyUp, { capture: true });
        };
    }, [menuMap, isMenuOpen, focusedLinkIndex]);

    const flattenLinks = (module) => {
        if (!module) return [];
        let links = [];
        if (module.links) links = [...module.links];
        if (module.subgroups) {
            module.subgroups.forEach(sub => {
                links = [...links, ...sub.links];
            });
        }
        return links;
    };

    const openMenu = (moduleId) => {
        setIsMenuOpen(moduleId);
        setFocusedLinkIndex(-1);
        setUserMenuOpen(false);

        const btn = buttonsRef.current[moduleId];
        if (btn) {
            const rect = btn.getBoundingClientRect();
            const left = Math.max(0, Math.min(rect.left, window.innerWidth - 280));
            setActiveDropdownLeft(left);
        }
    };

    const handleMouseMove = (e) => {
        if (e.clientY <= 10) setIsVisible(true);
    };

    useEffect(() => {
        window.addEventListener('mousemove', handleMouseMove);
        return () => window.removeEventListener('mousemove', handleMouseMove);
    }, []);

    const handleModuleClick = (e, module) => {
        e.stopPropagation();
        if (module.route) {
            router.push(module.route);
            closeAll();
        } else {
            // Click toggles if same menu, otherwise opens (handled by hover usually)
            if (isMenuOpen === module.id) {
                closeAll();
            } else {
                openMenu(module.id);
            }
        }
    };

    const handleUserClick = (e) => {
        e.stopPropagation();
        setUserMenuOpen(prev => !prev);
        setIsMenuOpen(null);
    };

    /**
     * Mnemonic Renderer with Normalization (Accent Insensitive)
     */
    const renderMnemonic = (text, targetKey) => {
        if (!altPressed || !targetKey) return text;

        // Normalize: 'Nómina' -> 'Nomina'
        const normalizedText = text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
        const normalizedKey = targetKey.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();

        const index = normalizedText.indexOf(normalizedKey);

        if (index === -1) return text;

        const charToHighlight = text.charAt(index);

        return (
            <span>
                {text.substring(0, index)}
                <span className="font-extrabold underline decoration-2 decoration-blue-500">{charToHighlight}</span>
                {text.substring(index + 1)}
            </span>
        );
    };

    const renderLinkContent = (link, idx) => {
        const text = link.name;
        const targetKey = link.mnemonic;

        if (!targetKey) return text;

        const normalizedText = text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
        const normalizedKey = targetKey.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();

        const index = normalizedText.indexOf(normalizedKey);
        if (index === -1) return text;

        return (
            <span>
                {text.substring(0, index)}
                <u className="decoration-2 decoration-blue-400 font-bold">{text.charAt(index)}</u>
                {text.substring(index + 1)}
            </span>
        );
    }

    if (!user) return null;

    return (
        <>
            {(!isVisible && isZenMode) && (
                <div
                    className="fixed top-0 left-0 right-0 h-6 z-[9900] bg-transparent hover:bg-blue-500/10 cursor-pointer transition-colors"
                    onClick={() => setIsVisible(true)}
                    title="Clic para mostrar Menú"
                />
            )}

            <header
                className={`fixed top-0 left-0 right-0 z-[99999] bg-[#f5f5f5] text-gray-800 shadow-xl h-9 flex items-center justify-between px-2 select-none transition-transform duration-200 ease-out border-b border-gray-300
                    ${isVisible ? 'translate-y-0' : '-translate-y-full'}
                `}
            // REMOVED HOVER HANDLERS
            >
                <nav className="flex items-center space-x-1 h-full overflow-visible pl-1 relative">
                    <button
                        onClick={() => router.push('/')}
                        className="px-3 py-1 text-gray-600 hover:bg-gray-200 rounded-sm transition-colors mr-2 text-lg"
                        title="Ir al Inicio"
                    >
                        🏠
                    </button>

                    {menuStructure.map((module) => {
                        const isOpen = isMenuOpen === module.id;
                        const mnemonicKey = module.mnemonic;

                        return (
                            <div key={module.id} className="relative h-full flex items-center group">
                                <button
                                    ref={el => buttonsRef.current[module.id] = el}
                                    className={`px-3 py-0.5 rounded-sm text-sm font-medium transition-colors whitespace-nowrap border border-transparent select-none relative z-[100001]
                                        ${isOpen ? 'bg-white border-b-0 border-gray-300 rounded-b-none shadow-none font-bold' : 'text-gray-700 hover:bg-gray-200'}
                                    `}
                                    onClick={(e) => handleModuleClick(e, module)}
                                // Removed onMouseEnter
                                >
                                    {renderMnemonic(module.name, mnemonicKey)}
                                </button>
                            </div>
                        );
                    })}
                </nav>

                <div className="flex items-center space-x-1 pl-2 border-l border-gray-300 h-5 my-auto relative">
                    {altPressed && <FaKeyboard className="text-blue-600 mr-2 animate-pulse" title="Teclado Activo" />}

                    <div
                        className="flex items-center space-x-2 ml-2 px-2 py-0.5 rounded hover:bg-gray-200 cursor-pointer text-sm transition-colors group relative"
                        onClick={handleUserClick}
                    >
                        <FaUserCircle className="text-gray-600 group-hover:text-black" size={16} />
                        <span className="font-semibold text-gray-700 group-hover:text-black hidden sm:block text-xs">{user?.nombre || 'Usuario'}</span>

                        {userMenuOpen && (
                            <div className="absolute top-[28px] right-0 w-48 bg-white border border-gray-300 shadow-xl rounded-md z-[100010] py-1 animate-in fade-in duration-75">
                                <div className="px-4 py-2 border-b border-gray-100 text-xs text-gray-500">
                                    Conectado como <strong>{user?.role || 'Admin'}</strong>
                                </div>
                                <button className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 flex items-center">
                                    <FaCog className="mr-2" /> Configuración
                                </button>
                                <button
                                    onClick={() => { logout(); closeAll(); }}
                                    className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center"
                                >
                                    <FaSignOutAlt className="mr-2" /> Cerrar Sesión
                                </button>
                            </div>
                        )}
                    </div>

                    <button
                        onClick={() => setIsVisible(false)}
                        className="p-1 px-3 bg-red-100 text-red-600 hover:bg-red-200 hover:text-red-700 ml-2 rounded font-bold text-xs flex items-center"
                        title="Ocultar Barra"
                    >
                        <FaTimes size={12} className="mr-1" /> Ocultar
                    </button>
                </div>
            </header>

            {/* DROPDOWN CONTAINER */}
            {isMenuOpen && (
                <div
                    className="fixed top-[35px] min-w-[280px] bg-white text-gray-800 border border-gray-400 shadow-[4px_4px_16px_rgba(0,0,0,0.3)] rounded-b-md rounded-tr-md overflow-hidden z-[100002]"
                    style={{ left: activeDropdownLeft }}
                    onMouseDown={(e) => e.stopPropagation()}
                    onMouseEnter={handleDropdownEnter}
                    onMouseLeave={handleMouseLeave}
                >
                    <div className="py-1 max-h-[80vh] overflow-y-auto">
                        {menuStructure.find(m => m.id === isMenuOpen)?.links?.map((link, idx) => (
                            <Link
                                key={link.href}
                                href={link.href}
                                className={`block px-4 py-2 text-sm flex items-center transition-colors border-l-4
                                    ${idx === focusedLinkIndex
                                        ? 'bg-blue-100 text-blue-900 border-blue-600'
                                        : 'text-gray-700 hover:bg-[#cce0ff] hover:text-black border-transparent'}
                                `}
                                onClick={closeAll}
                            >
                                <span className="w-5 mr-2 text-gray-500 flex justify-center">
                                    {link.icon && <link.icon size={12} />}
                                </span>
                                {renderLinkContent(link, idx)}
                                {idx === focusedLinkIndex && <FaArrowRight className="ml-auto text-blue-500 text-xs" />}
                            </Link>
                        ))}

                        {menuStructure.find(m => m.id === isMenuOpen)?.subgroups?.map(sub => (
                            <div key={sub.title} className="mt-1 border-t border-gray-200 pt-1 pb-1">
                                <div className="px-4 py-1 text-[10px] font-bold text-gray-400 uppercase tracking-wider bg-gray-50">{sub.title}</div>
                                {sub.links.map((link, subIdx) => {
                                    return (
                                        <Link
                                            key={link.href}
                                            href={link.href}
                                            className="block px-4 py-2 text-sm hover:bg-[#cce0ff] hover:text-black text-gray-700 pl-8 transition-colors"
                                            onClick={closeAll}
                                        >
                                            {renderLinkContent(link, subIdx)}
                                        </Link>
                                    )
                                })}
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </>
    );
}
