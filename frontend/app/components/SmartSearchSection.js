"use client";
import React, { useState, useMemo, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { FaSearch, FaMagic, FaMicrophone, FaArrowRight, FaExternalLinkAlt, FaTerminal, FaBolt } from 'react-icons/fa';
import { toast } from 'react-toastify';
import { menuStructure } from '../../lib/menuData'; // Importamos la estructura real
import { commandDictionary } from '../../lib/commandDictionary';

export default function SmartSearchSection() {
    const router = useRouter();
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [isThinking, setIsThinking] = useState(false);
    const [selectedIndex, setSelectedIndex] = useState(0);
    const [isCommandMode, setIsCommandMode] = useState(false); // Nuevo estado para Modo Comando

    // 1. Aplanar la estructura del menú para búsqueda (Normal)
    const searchableItems = useMemo(() => {
        const items = [];
        const processLinks = (links, category) => {
            links.forEach(link => {
                items.push({
                    name: link.name,
                    description: link.description || '',
                    href: link.href,
                    icon: link.icon,
                    category: category,
                    keywords: `${link.name} ${link.description || ''} ${category}`.toLowerCase()
                });
            });
        };

        menuStructure.forEach(module => {
            if (module.links) processLinks(module.links, module.name);
            if (module.subgroups) {
                module.subgroups.forEach(sub => processLinks(sub.links, `${module.name} - ${sub.title}`));
            }
        });
        return items;
    }, []);

    // 2. Lógica de Búsqueda y Detección de Comandos
    const searchParams = useSearchParams();

    useEffect(() => {
        const trigger = searchParams.get('trigger');
        if (trigger === 'focus_search') {
            const input = document.getElementById('smart-search-input');
            if (input) {
                // Small delay to ensure render
                setTimeout(() => {
                    input.focus();
                    input.select();
                }, 100);
            }
            // Clean URL
            const newUrl = window.location.pathname;
            window.history.replaceState({}, '', newUrl);
        }
    }, [searchParams]);

    useEffect(() => {
        if (!query.trim()) {
            setResults([]);
            setIsCommandMode(false);
            return;
        }

        // --- DETECCION DE MODO COMANDO (Starts with :) ---
        if (query.startsWith(':')) {
            setIsCommandMode(true);
            const commandQuery = query.substring(1).toLowerCase().trim();

            // Búsqueda en Diccionario
            const matchedCommands = commandDictionary.filter(cmd =>
                cmd.triggers.some(trigger => trigger.includes(commandQuery)) ||
                (cmd.aliases && cmd.aliases.some(alias => alias.startsWith(commandQuery)))
            );

            if (matchedCommands.length > 0) {
                setResults(matchedCommands.map(cmd => ({
                    name: cmd.name,
                    description: cmd.description,
                    href: cmd.queryParam ? `${cmd.path}?${cmd.queryParam}` : cmd.path,
                    icon: cmd.icon,
                    category: cmd.category || 'Comando',
                    isCommand: true,
                    aliases: cmd.aliases
                })));
            } else {
                setResults([]);
            }
            return;
        }

        setIsCommandMode(false);

        // --- BÚSQUEDA NORMAL ---
        const lowerQuery = query.toLowerCase();
        const terms = lowerQuery.split(' ').filter(t => t.length > 0);

        const matches = searchableItems.filter(item => {
            return terms.every(term => item.keywords.includes(term));
        });

        matches.sort((a, b) => {
            const aNameMatch = a.name.toLowerCase().includes(lowerQuery);
            const bNameMatch = b.name.toLowerCase().includes(lowerQuery);
            if (aNameMatch && !bNameMatch) return -1;
            if (!aNameMatch && bNameMatch) return 1;
            return 0;
        });

        setResults(matches.slice(0, 5));
        setSelectedIndex(0);

    }, [query, searchableItems]);


    const handleSearch = (e) => {
        e.preventDefault();

        // Ejecución prioritaria si hay resultados (Comando o Búsqueda)
        if (results.length > 0) {
            handleSelectResult(results[selectedIndex]);
            return;
        }

        // Feedback si no hay nada
        setIsThinking(true);
        setTimeout(() => {
            setIsThinking(false);
            if (isCommandMode) {
                toast.warning("Comando no reconocido. Intenta con ':nuevo item'");
            } else {
                toast.info("No encontré una coincidencia exacta.");
            }
        }, 800);
    };

    const handleSelectResult = (item) => {
        if (!item) return;
        setIsThinking(true);
        setTimeout(() => {
            router.push(item.href);
            setIsThinking(false);
        }, 300);
    };

    const handleKeyDown = (e) => {
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            setSelectedIndex(prev => Math.min(prev + 1, results.length - 1));
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            setSelectedIndex(prev => Math.max(0, prev - 1));
        }
    };

    return (
        <div className="flex flex-col items-center justify-center min-h-[80vh] w-full px-4 animate-in fade-in zoom-in duration-500">

            {/* Logo Section */}
            <div className="mb-8 text-center relative group">
                <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
                <img
                    src="/logo_finaxis_real.png"
                    alt="Finaxis AI"
                    className="relative h-20 object-contain drop-shadow-2xl transform transition-transform duration-500 hover:scale-105"
                />
            </div>

            {/* Search Bar Section */}
            <div className="relative w-full max-w-2xl z-50">
                <form onSubmit={handleSearch} className="relative group">
                    <div className={`absolute -inset-0.5 rounded-full blur opacity-30 group-hover:opacity-75 transition duration-1000 group-hover:duration-200 animate-pulse-slow
                        ${isCommandMode ? 'bg-gradient-to-r from-green-400 to-emerald-600' : 'bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500'}
                    `}></div>

                    <div className={`relative flex items-center bg-white shadow-2xl border transition-all duration-300 transform 
                        ${results.length > 0 ? 'rounded-t-3xl rounded-b-none' : 'rounded-full group-hover:-translate-y-1'}
                        ${isCommandMode ? 'border-green-400 ring-2 ring-green-100' : 'border-gray-100'}
                    `}>
                        <div className="pl-6 text-gray-400">
                            {isThinking ? (
                                <FaMagic className="text-purple-500 animate-spin-slow text-xl" />
                            ) : isCommandMode ? (
                                <FaTerminal className="text-green-500 text-lg animate-pulse" />
                            ) : (
                                <FaSearch className="text-gray-400 text-lg group-hover:text-blue-500 transition-colors" />
                            )}
                        </div>

                        <input
                            id="smart-search-input"
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder={isCommandMode ? "Escribe el comando... (ej: 'nuevo item')" : "Describe qué deseas hacer..."}
                            className={`w-full py-4 px-4 text-lg bg-transparent border-none outline-none font-light transition-colors
                                ${isCommandMode ? 'text-green-800 placeholder-green-700/50 font-mono' : 'text-gray-700 placeholder-gray-400'}
                            `}
                            autoFocus
                        />

                        {/* Botón enviar */}
                        <div className="pr-2 flex items-center gap-2">
                            {query.trim() && (
                                <button
                                    type="submit"
                                    className={`p-2 text-white rounded-full hover:shadow-lg transform transition hover:scale-105 active:scale-95
                                        ${isCommandMode ? 'bg-gradient-to-r from-green-500 to-emerald-600' : 'bg-gradient-to-r from-blue-600 to-purple-600'}
                                    `}
                                >
                                    {isCommandMode ? <FaBolt /> : <FaArrowRight />}
                                </button>
                            )}
                        </div>
                    </div>
                </form>

                {/* Live Search Results Dropdown */}
                {results.length > 0 && (
                    <div className="absolute top-full left-0 right-0 bg-white border border-gray-100 rounded-b-3xl shadow-xl max-h-96 overflow-y-auto animate-in fade-in slide-in-from-top-2 scrollbar-thin scrollbar-thumb-gray-200 scrollbar-track-transparent">
                        <ul>
                            {results.map((item, index) => (
                                <li
                                    key={index}
                                    onClick={() => handleSelectResult(item)}
                                    className={`px-6 py-3 cursor-pointer border-b border-gray-50 last:border-0 flex items-center gap-3 transition-colors
                                        ${index === selectedIndex ? (isCommandMode ? 'bg-green-50' : 'bg-blue-50') : 'hover:bg-gray-50'}
                                    `}
                                >
                                    <span className={`p-2 rounded-lg 
                                        ${item.isCommand
                                            ? (index === selectedIndex ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-green-500')
                                            : (index === selectedIndex ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-500')
                                        }
                                    `}>
                                        {item.icon ? <item.icon /> : <FaExternalLinkAlt />}
                                    </span>
                                    <div className="flex-1">
                                        <div className={`font-medium text-base flex items-center gap-2 ${isCommandMode ? 'text-green-800 font-mono' : 'text-gray-800'}`}>
                                            {item.name}
                                            {item.aliases && item.aliases.length > 0 && (
                                                <span className="text-[10px] bg-green-200 text-green-900 border border-green-300 px-1.5 py-0.5 rounded font-bold tracking-wide">
                                                    :{item.aliases[0].toUpperCase()}
                                                </span>
                                            )}
                                        </div>
                                        <div className="text-xs text-gray-400">{item.category} • {item.description}</div>
                                    </div>
                                    {index === selectedIndex && <FaArrowRight className="text-gray-400 text-sm" />}
                                </li>
                            ))}
                        </ul>
                        <div className="px-4 py-2 bg-gray-50 text-xs text-center text-gray-400 border-t border-gray-100">
                            Presiona <strong>Enter</strong> para ejecutar
                        </div>
                    </div>
                )}
            </div>

            {/* AI Status Text Only (No buttons) */}
            <div className="mt-8 h-6 text-center">
                {isThinking && (
                    <p className="text-sm text-purple-600 font-semibold animate-pulse flex items-center gap-2 justify-center">
                        <FaMagic /> Procesando solicitud...
                    </p>
                )}
            </div>

        </div>
    );
}
