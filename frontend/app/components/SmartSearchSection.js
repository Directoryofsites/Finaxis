"use client";
import React, { useState, useMemo, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { FaSearch, FaMagic, FaMicrophone, FaArrowRight, FaExternalLinkAlt } from 'react-icons/fa';
import { toast } from 'react-toastify';
import { menuStructure } from '../../lib/menuData'; // Importamos la estructura real

export default function SmartSearchSection() {
    const router = useRouter();
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [isThinking, setIsThinking] = useState(false);
    const [selectedIndex, setSelectedIndex] = useState(0);

    // 1. Aplanar la estructura del menú para búsqueda
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

    // 2. Lógica de Búsqueda en Tiempo Real
    useEffect(() => {
        if (!query.trim()) {
            setResults([]);
            return;
        }

        const lowerQuery = query.toLowerCase();
        const terms = lowerQuery.split(' ').filter(t => t.length > 0);

        // Algoritmo de coincidencia simple pero efectivo
        const matches = searchableItems.filter(item => {
            // Todos los términos deben coincidir parcialmente con algo en las keywords
            return terms.every(term => item.keywords.includes(term));
        });

        // Ordenar: Prioridad a coincidencia en el Nombre sobre la Descripción
        matches.sort((a, b) => {
            const aNameMatch = a.name.toLowerCase().includes(lowerQuery);
            const bNameMatch = b.name.toLowerCase().includes(lowerQuery);
            if (aNameMatch && !bNameMatch) return -1;
            if (!aNameMatch && bNameMatch) return 1;
            return 0;
        });

        setResults(matches.slice(0, 5)); // Top 5 resultados
        setSelectedIndex(0); // Reset selección
    }, [query, searchableItems]);


    const handleSearch = (e) => {
        e.preventDefault();
        if (results.length > 0) {
            handleSelectResult(results[selectedIndex]);
        } else {
            setIsThinking(true);
            setTimeout(() => {
                setIsThinking(false);
                toast.info("No encontré una coincidencia exacta en el menú. Intenta con palabras clave como 'Factura', 'Balance', 'Tercero'.");
            }, 800);
        }
    };

    const handleSelectResult = (item) => {
        if (!item) return;
        setIsThinking(true);
        // Simular pequeño delay para efecto "Thinking"
        setTimeout(() => {
            router.push(item.href);
            setIsThinking(false);
        }, 300);
    };

    // Navegación con teclado en resultados
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

            {/* Logo Section (REDUCIDO) */}
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
                    <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-full blur opacity-30 group-hover:opacity-75 transition duration-1000 group-hover:duration-200 animate-pulse-slow"></div>

                    <div className={`relative flex items-center bg-white shadow-2xl border border-gray-100 transition-all duration-300 transform 
                        ${results.length > 0 ? 'rounded-t-3xl rounded-b-none' : 'rounded-full group-hover:-translate-y-1'}
                    `}>
                        <div className="pl-6 text-gray-400">
                            {isThinking ? (
                                <FaMagic className="text-purple-500 animate-spin-slow text-xl" />
                            ) : (
                                <FaSearch className="text-gray-400 text-lg group-hover:text-blue-500 transition-colors" />
                            )}
                        </div>

                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Describe qué deseas hacer... (ej: 'Ver facturas', 'Crear cliente')"
                            className="w-full py-4 px-4 text-lg text-gray-700 bg-transparent border-none outline-none placeholder-gray-400 font-light"
                            autoFocus
                        />

                        {/* Botón enviar */}
                        <div className="pr-2 flex items-center gap-2">
                            {query.trim() && (
                                <button
                                    type="submit"
                                    className="p-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-full hover:shadow-lg transform transition hover:scale-105 active:scale-95"
                                >
                                    <FaArrowRight />
                                </button>
                            )}
                        </div>
                    </div>
                </form>

                {/* Live Search Results Dropdown */}
                {results.length > 0 && (
                    <div className="absolute top-full left-0 right-0 bg-white border border-gray-100 rounded-b-3xl shadow-xl overflow-hidden animate-in fade-in slide-in-from-top-2">
                        <ul>
                            {results.map((item, index) => (
                                <li
                                    key={index}
                                    onClick={() => handleSelectResult(item)}
                                    className={`px-6 py-3 cursor-pointer border-b border-gray-50 last:border-0 flex items-center gap-3 transition-colors
                                        ${index === selectedIndex ? 'bg-blue-50' : 'hover:bg-gray-50'}
                                    `}
                                >
                                    <span className={`p-2 rounded-lg ${index === selectedIndex ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-500'}`}>
                                        {item.icon ? <item.icon /> : <FaExternalLinkAlt />}
                                    </span>
                                    <div className="flex-1">
                                        <div className="font-medium text-gray-800 text-base">{item.name}</div>
                                        <div className="text-xs text-gray-400">{item.category} • {item.description}</div>
                                    </div>
                                    {index === selectedIndex && <FaArrowRight className="text-blue-400 text-sm" />}
                                </li>
                            ))}
                        </ul>
                        <div className="px-4 py-2 bg-gray-50 text-xs text-center text-gray-400 border-t border-gray-100">
                            Presiona <strong>Enter</strong> para ir al primer resultado
                        </div>
                    </div>
                )}
            </div>

            {/* AI Status Text Only (No buttons) */}
            <div className="mt-8 h-6 text-center">
                {isThinking && (
                    <p className="text-sm text-purple-600 font-semibold animate-pulse flex items-center gap-2 justify-center">
                        <FaMagic /> Buscando la mejor opción para ti...
                    </p>
                )}
            </div>

        </div>
    );
}
