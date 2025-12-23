"use client";
import React, { useState, useMemo, useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { FaSearch, FaMagic, FaMicrophone, FaArrowRight, FaExternalLinkAlt, FaTerminal, FaBolt, FaStop } from 'react-icons/fa';
import { toast } from 'react-toastify';
import { menuStructure } from '../../lib/menuData'; // Importamos la estructura real
import { commandDictionary } from '../../lib/commandDictionary';
import { apiService } from '@/lib/apiService';
import AssistantOverlay from './VoiceAssistant/AssistantOverlay';

export default function SmartSearchSection() {
    const router = useRouter();
    const [commandHistory, setCommandHistory] = useState([]);
    const [showHistory, setShowHistory] = useState(false);
    const [showAssistant, setShowAssistant] = useState(false);

    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [isListening, setIsListening] = useState(false);
    const [isThinking, setIsThinking] = useState(false);
    const [selectedIndex, setSelectedIndex] = useState(-1);
    const recognitionRef = useRef(null);

    const isCommandMode = query.startsWith(':') || (results.length > 0 && results[0].isCommand);

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
        if (!query) {
            setResults([]);
            setSelectedIndex(-1);
            return;
        }

        // --- DETECCION DE MODO COMANDO (Starts with :) ---
        if (query.startsWith(':')) {
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
            setSelectedIndex(0);
            return;
        }

        // --- BÚSQUEDA NORMAL ---
        const lowerQuery = query.toLowerCase();
        const terms = lowerQuery.split(' ').filter(term => term.length > 0);

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
        setSelectedIndex(matches.length > 0 ? 0 : -1);

    }, [query, searchableItems]);

    useEffect(() => {
        try {
            const saved = localStorage.getItem('voice_history');
            if (saved) {
                const parsed = JSON.parse(saved);
                if (Array.isArray(parsed)) {
                    // Ensure all items are strings to prevent React object render error
                    const safeHistory = parsed.filter(item => typeof item === 'string' && item.trim().length > 0);
                    setCommandHistory(safeHistory);
                }
            }
        } catch (e) {
            console.error("Error parsing history", e);
            // Si hay error, limpiamos para evitar loop
            localStorage.removeItem('voice_history');
        }
    }, []);

    const addToHistory = (text) => {
        if (!text || !text.trim()) return;
        const cleanText = text.trim();

        setCommandHistory(prev => {
            // Remove exact duplicate if exists to bump it to top
            const filtered = prev.filter(item => item !== cleanText);
            const newHistory = [cleanText, ...filtered].slice(0, 6); // Keep last 6
            localStorage.setItem('voice_history', JSON.stringify(newHistory));
            return newHistory;
        });
    };

    const handleSearch = (e) => {
        e.preventDefault();

        // Ejecución prioritaria si hay resultados (Comando o Búsqueda)
        if (results.length > 0) {
            handleSelectResult(results[selectedIndex]);
            return;
        }

        // Si no hay resultados locales, intentamos enviar a AI
        if (query.trim()) {
            processVoiceCommand(query);
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

    const handleHistoryClick = (text) => {
        setQuery(text);
        document.getElementById('smart-search-input')?.focus();
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

    // --- VOICE LOGIC ---
    useEffect(() => {
        // Voice recognition setup code...
        if (typeof window !== 'undefined' && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognitionRef.current = new SpeechRecognition();
            recognitionRef.current.continuous = true;
            recognitionRef.current.lang = 'es-CO';
            recognitionRef.current.interimResults = true;
            recognitionRef.current.maxAlternatives = 1;

            let silenceTimer = null;

            recognitionRef.current.onresult = (event) => {
                let finalTranscript = '';
                // Helper to concat current results
                const currentText = Array.from(event.results)
                    .map(result => result[0].transcript)
                    .join('');

                setQuery(currentText);

                if (silenceTimer) clearTimeout(silenceTimer);
                silenceTimer = setTimeout(() => {
                    recognitionRef.current.stop();
                    setIsListening(false);
                    processVoiceCommand(currentText);
                }, 2000);
            };

            recognitionRef.current.onerror = (event) => {
                if (event.error !== 'no-speech') {
                    console.error("Speech error", event.error);
                }
            };
        }
    }, [isListening]);

    const toggleListening = () => {
        if (isListening) {
            recognitionRef.current?.stop();
            setIsListening(false);
        } else {
            setQuery('');
            setIsListening(true);
            try {
                recognitionRef.current?.start();
            } catch (e) {
                console.error("Error starting speech recognition:", e);
                setIsListening(false);
            }
        }
    };

    const processVoiceCommand = async (text) => {
        if (!text || !text.trim()) return;

        addToHistory(text);

        setIsThinking(true);
        try {
            const token = localStorage.getItem('authToken');
            if (!token) {
                toast.error("Sesión no válida.");
                setIsThinking(false);
                return;
            }

            const baseUrl = process.env.NEXT_PUBLIC_API_URL || (typeof window !== 'undefined' ? `http://${window.location.hostname}:8000` : 'http://localhost:8000');

            let response = await fetch(`${baseUrl}/api/ai/process-command`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ command: text })
            });

            if (response.status === 401) {
                response = await fetch(`${baseUrl}/api/ai/process-command-debug`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command: text })
                });
            }

            const data = await response.json();
            setIsThinking(false);

            if (data.error) {
                toast.error(`IA: ${data.error}`);
                return;
            }

            // --- AI ACTION HANDLER ---
            const actionName = data.name || data.function_name;

            if (actionName === 'navegar_a_pagina') {
                const modulo = data.parameters.modulo.toLowerCase();
                if (modulo.includes('contabil')) router.push('/contabilidad/documentos');
                else if (modulo.includes('factur')) router.push('/facturacion/crear');
                else if (modulo.includes('inventar')) router.push('/admin/inventario');
                else if (modulo.includes('nomin')) router.push('/nomina/liquidar');
                else toast.success(`IA: Navegando a ${data.parameters.modulo}`);

            } else if (actionName === 'generar_reporte_movimientos') {
                const params = new URLSearchParams();
                const p = data.parameters;
                if (p.tercero || p.tercero_nombre) params.set('tercero', p.tercero || p.tercero_nombre);
                if (p.cuenta || p.cuenta_nombre) params.set('cuenta', p.cuenta || p.cuenta_nombre);
                if (p.fecha_inicio) params.set('fecha_inicio', p.fecha_inicio);
                if (p.fecha_fin) params.set('fecha_fin', p.fecha_fin);
                router.push(`/contabilidad/reportes/tercero-cuenta?${params.toString()}`);
                toast.success('IA: Configurando Auxiliar por Tercero...');

            } else if (actionName === 'generar_balance_prueba') {
                const params = new URLSearchParams();
                const p = data.parameters;
                if (p.fecha_inicio) params.set('fecha_inicio', p.fecha_inicio);
                if (p.fecha_fin) params.set('fecha_fin', p.fecha_fin);
                router.push(`/contabilidad/reportes/balance-de-prueba?${params.toString()}`);
                toast.success('IA: Configurando Balance de Prueba...');

            } else if (actionName === 'generar_balance_general') {
                const params = new URLSearchParams();
                const p = data.parameters;
                if (p.fecha_corte) params.set('fecha_corte', p.fecha_corte);
                if (p.comparativo) params.set('comparativo', 'true');
                router.push(`/contabilidad/reportes/balance-general?${params.toString()}`);
                toast.success('IA: Configurando Balance General...');

            } else if (actionName === 'generar_estado_resultados') {
                const params = new URLSearchParams();
                const p = data.parameters;
                if (p.fecha_inicio) params.set('fecha_inicio', p.fecha_inicio);
                if (p.fecha_fin) params.set('fecha_fin', p.fecha_fin);
                router.push(`/contabilidad/reportes/estado-resultados?${params.toString()}`);
                toast.success('IA: Configurando Estado de Resultados...');

            } else if (actionName === 'crear_recurso') {
                const tipo = data.parameters.tipo || data.parameters.type;
                const creationMap = {
                    'factura': { path: '/contabilidad/facturacion', param: '' },
                    'compra': { path: '/contabilidad/compras', param: 'trigger=new_purchase' },
                    'item': { path: '/admin/inventario', param: 'trigger=new_item' },
                    'tercero': { path: '/admin/terceros/crear', param: '' },
                    'traslado': { path: '/contabilidad/traslados', param: 'trigger=new_transfer' },
                    'centro_costo': { path: '/admin/centros-costo', param: 'trigger=new_cc' },
                    'unidad_ph': { path: '/ph/unidades/crear', param: '' },
                    'bodega': { path: '/admin/inventario/parametros', param: 'trigger=tab_warehouses' },
                    'receta': { path: '/produccion/recetas', param: 'trigger=new_recipe' },
                    'nomina': { path: '/nomina/configuracion', param: 'trigger=new_payroll_type' },
                    'plantilla': { path: '/admin/plantillas/crear', param: '' },
                    'empresa': { path: '/admin/utilidades/soporte-util', param: 'trigger=tab_create_company' },
                    'cuenta': { path: '/admin/plan-de-cuentas', param: 'trigger=new_account' },
                    'tipo_documento': { path: '/admin/tipos-documento/crear', param: '' }
                };
                const target = creationMap[tipo];
                if (target) {
                    const finalUrl = target.param ? `${target.path}?${target.param}` : target.path;
                    router.push(finalUrl);
                    toast.success(`IA: Abriendo creación de ${tipo}...`);
                } else {
                    toast.warning(`IA: No sé cómo crear '${tipo}' aún.`);
                }

            } else if (actionName === 'consultar_documento') {
                const p = data.parameters;
                const params = new URLSearchParams();
                params.set('trigger', 'ai_search');
                if (p.tipo_documento) params.set('ai_tipo_doc', p.tipo_documento);
                if (p.numero_documento) params.set('numero', p.numero_documento);
                if (p.tercero) params.set('ai_tercero', p.tercero);
                if (p.cuenta) params.set('ai_cuenta', p.cuenta);
                if (p.fecha_inicio) params.set('fecha_inicio', p.fecha_inicio);
                if (p.fecha_fin) params.set('fecha_fin', p.fecha_fin);
                if (p.concepto) params.set('conceptoKeyword', p.concepto);
                router.push(`/contabilidad/reportes/super-informe?${params.toString()}`);
                toast.success('IA: Buscando documentos...');

            } else if (actionName === 'generar_backup') {
                toast.loading('IA: Generando respaldo completo de la base de datos...', { id: 'backup-toast' });
                try {
                    const response = await apiService.post('/utilidades/backup-rapido', {});
                    // Convertir la respuesta JSON a Blob y descargar
                    const jsonString = JSON.stringify(response, null, 2);
                    const blob = new Blob([jsonString], { type: "application/json" });
                    const url = window.URL.createObjectURL(blob);
                    const link = document.createElement("a");
                    link.href = url;
                    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
                    link.download = `backup_completo_finaxis_${timestamp}.json`;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);

                    toast.success("¡Respaldo generado y descargado exitosamente!", { id: 'backup-toast' });
                } catch (err) {
                    console.error(err);
                    toast.error("Error generando el respaldo.", { id: 'backup-toast' });
                }

            } else {
                toast.info(`IA sugiere acción desconocida: ${actionName}`);
            }

        } catch (error) {
            console.error(error);
            setIsThinking(false);
            toast.error("Error conectando con el cerebro AI.");
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

            {/* Assistant Trigger Button */}
            <button
                onClick={() => setShowAssistant(true)}
                className="mb-8 flex items-center gap-2 px-6 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-full font-medium shadow-lg hover:shadow-xl hover:scale-105 transition-all transform animate-in fade-in slide-in-from-bottom-4 duration-700 delay-200"
            >
                <FaMicrophone className="animate-pulse" />
                <span>Modo Asistente Interactivo</span>
            </button>

            {/* Assistant Overlay Portal */}
            {showAssistant && (
                <AssistantOverlay onClose={() => setShowAssistant(false)} />
            )}

            {/* Search Bar Section */}
            <div className="relative w-full max-w-2xl z-50">
                <form onSubmit={handleSearch} className="relative group">
                    {/* ... (Existing Input Styles) ... */}
                    <div className={`absolute -inset-0.5 rounded-full blur opacity-30 group-hover:opacity-75 transition duration-1000 group-hover:duration-200 animate-pulse-slow
                        ${isListening ? 'bg-gradient-to-r from-red-500 to-orange-500 animate-ping' :
                            isCommandMode ? 'bg-gradient-to-r from-green-400 to-emerald-600' : 'bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500'}
                    `}></div>

                    <div className={`relative flex items-center bg-white shadow-2xl border transition-all duration-300 transform 
                        ${results.length > 0 || (showHistory && !query && commandHistory.length > 0) ? 'rounded-t-3xl rounded-b-none' : 'rounded-full group-hover:-translate-y-1'}
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
                            onFocus={() => setShowHistory(true)}
                            onBlur={() => setTimeout(() => setShowHistory(false), 200)} // Delay for click
                            placeholder={isListening ? "Te escucho..." : (isCommandMode ? "Escribe el comando..." : "Describe qué deseas hacer...")}
                            className={`w-full py-4 px-4 text-lg bg-transparent border-none outline-none font-light transition-colors
                                ${isCommandMode ? 'text-green-800 placeholder-green-700/50 font-mono' : 'text-gray-700 placeholder-gray-400'}
                            `}
                            autoFocus
                            autoComplete="off"
                        />

                        {/* Botones Derecha */}
                        <div className="pr-2 flex items-center gap-2">
                            <button
                                type="button"
                                onClick={toggleListening}
                                className={`p-3 rounded-full transition-all duration-300 ${isListening ? 'bg-red-500 text-white animate-pulse shadow-red-300 shadow-lg' : 'text-gray-400 hover:text-blue-500 hover:bg-blue-50'}`}
                                title="Hablar con AI"
                            >
                                {isListening ? <FaStop /> : <FaMicrophone />}
                            </button>

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
                {(results.length > 0 || (showHistory && !query && commandHistory.length > 0)) && (
                    <div className="absolute top-full left-0 right-0 bg-white border border-gray-100 rounded-b-3xl shadow-xl max-h-96 overflow-y-auto animate-in fade-in slide-in-from-top-2 scrollbar-thin scrollbar-thumb-gray-200 scrollbar-track-transparent z-40">
                        {/* CASE 1: SEARCH RESULTS */}
                        {results.length > 0 ? (
                            <>
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
                            </>
                        ) : (
                            /* CASE 2: COMMAND HISTORY */
                            <div className="py-2">
                                <div className="px-6 py-2 text-xs font-bold text-gray-400 uppercase tracking-wider flex justify-between items-center">
                                    <span>Últimos Comandos (Historial)</span>
                                </div>
                                <ul>
                                    {commandHistory.map((cmd, idx) => (
                                        <li
                                            key={idx}
                                            onClick={() => handleHistoryClick(cmd)}
                                            className="px-6 py-3 cursor-pointer hover:bg-purple-50 flex items-center gap-3 group transition-colors border-b border-gray-50 last:border-0"
                                        >
                                            <div className="p-2 bg-purple-100 text-purple-600 rounded-full group-hover:bg-purple-200 transition-colors">
                                                <FaMicrophone className="text-xs" />
                                            </div>
                                            <span className="text-gray-600 group-hover:text-purple-700 flex-1 font-medium">{cmd}</span>
                                            <span className="text-xs text-purple-400 opacity-0 group-hover:opacity-100">Editar</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                )}

                {/* AI Status Text */}
                <div className="mt-8 h-6 text-center">
                    {isThinking && (
                        <p className="text-sm text-purple-600 font-semibold animate-pulse flex items-center gap-2 justify-center">
                            <FaMagic /> Procesando solicitud...
                        </p>
                    )}
                    {isListening && (
                        <p className="text-sm text-red-600 font-semibold animate-pulse flex items-center gap-2 justify-center">
                            <FaMicrophone /> Escuchando...
                        </p>
                    )}
                </div>
            </div>
        </div>
    );
}
