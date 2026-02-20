"use client";
import React, { useState } from 'react';
import { FaSearch, FaMagic, FaMicrophone, FaArrowRight, FaExternalLinkAlt, FaTerminal, FaBolt, FaStop, FaSave, FaTrash, FaHistory, FaClock, FaStar } from 'react-icons/fa';
import { useSmartSearch } from '../hooks/useSmartSearch';
import AssistantOverlay from './VoiceAssistant/AssistantOverlay';

export default function SmartSearchSection() {
    const {
        query,
        setQuery,
        results,
        isListening,
        isThinking,
        isCommandMode,
        commandHistory,
        library,
        isLibraryLoading,
        selectedIndex,
        setSelectedIndex,
        toggleListening,
        processVoiceCommand,
        handleSelectResult,
        addToLibrary,
        deleteFromLibrary,
        showHistory
    } = useSmartSearch();

    const [showAssistant, setShowAssistant] = useState(false);
    const [isFocused, setIsFocused] = useState(false);

    const handleSearch = (e) => {
        if (e) e.preventDefault();

        // Si hay resultados de menú y uno seleccionado, navegar a él
        if (results.length > 0 && selectedIndex >= 0) {
            handleSelectResult(results[selectedIndex]);
            return;
        }

        // Si no hay resultado de menú, enviar a la IA (Cerebro)
        if (query.trim()) {
            processVoiceCommand(query);
            setIsFocused(false);
            document.getElementById('smart-search-input')?.blur();
        }
    };

    const handleCommandClick = (text, execute = false) => {
        setQuery(text);
        if (execute) {
            processVoiceCommand(text);
        } else {
            document.getElementById('smart-search-input')?.focus();
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            setSelectedIndex(prev => Math.min(prev + 1, results.length - 1));
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            setSelectedIndex(prev => Math.max(0, prev - 1));
        } else if (e.key === 'Enter') {
            handleSearch(e);
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

            {/* Assistant Overlay Portal */}
            {showAssistant && (
                <AssistantOverlay onClose={() => setShowAssistant(false)} />
            )}

            {/* Search Bar Section */}
            <div className="relative w-full max-w-2xl z-20">
                <form onSubmit={handleSearch} className="relative group">
                    <div className={`absolute -inset-0.5 rounded-full blur opacity-30 group-hover:opacity-75 transition duration-1000 group-hover:duration-200 animate-pulse-slow
                        ${isListening ? 'bg-gradient-to-r from-red-500 to-orange-500 animate-ping' :
                            isCommandMode ? 'bg-gradient-to-r from-green-400 to-emerald-600' : 'bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500'}
                    `}></div>

                    <div className={`relative flex items-center bg-white shadow-2xl border transition-all duration-300 transform 
                        ${showHistory ? 'rounded-t-3xl rounded-b-none' : 'rounded-full group-hover:-translate-y-1'}
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
                            placeholder={isListening ? "Te escucho..." : (isCommandMode ? "Escribe el comando..." : "Describe qué deseas hacer...")}
                            className={`w-full py-4 px-4 text-lg bg-transparent border-none outline-none font-light transition-colors
                                ${isCommandMode ? 'text-green-800 placeholder-green-700/50 font-mono' : 'text-gray-700 placeholder-gray-400'}
                            `}
                            autoFocus
                            autoComplete="off"
                            onFocus={() => setIsFocused(true)}
                            onBlur={() => setTimeout(() => setIsFocused(false), 200)}
                        />

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
                                <>
                                    <button
                                        type="button"
                                        onClick={() => addToLibrary(query)}
                                        className="p-3 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-full transition-all duration-300"
                                        title="Guardar en Biblioteca"
                                    >
                                        <FaSave />
                                    </button>
                                    <button
                                        type="submit"
                                        className={`p-2 text-white rounded-full hover:shadow-lg transform transition hover:scale-105 active:scale-95
                                            ${isCommandMode ? 'bg-gradient-to-r from-green-500 to-emerald-600' : 'bg-gradient-to-r from-blue-600 to-purple-600'}
                                        `}
                                    >
                                        {isCommandMode ? <FaBolt /> : <FaArrowRight />}
                                    </button>
                                </>
                            )}
                        </div>
                    </div>
                </form>

                {/* Results Dropdown */}
                {showHistory && isFocused && (
                    <div className="absolute top-full left-0 right-0 bg-white border border-gray-100 rounded-b-3xl shadow-xl max-h-96 overflow-y-auto animate-in fade-in slide-in-from-top-2 scrollbar-thin scrollbar-thumb-gray-200 scrollbar-track-transparent z-40">
                        {results.length > 0 ? (
                            <>
                                <ul>
                                    {results.map((item, index) => (
                                        <li
                                            key={index}
                                            onClick={() => {
                                                handleSelectResult(item);
                                                setIsFocused(false);
                                            }}
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
                        ) : !query && (commandHistory.length > 0 || library.length > 0) && (
                            <div className="py-2">
                                {(() => {
                                    // Filtrar historial para no mostrar comandos que ya están en la biblioteca
                                    const filteredHistory = commandHistory.filter(cmd =>
                                        !library.some(libItem => libItem.comando === cmd)
                                    );

                                    if (filteredHistory.length === 0) return null;

                                    return (
                                        <>
                                            <div className="px-6 py-2 text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-2">
                                                <FaHistory className="text-[10px]" /> Historial Reciente
                                            </div>
                                            <ul>
                                                {filteredHistory.map((cmd, idx) => (
                                                    <li
                                                        key={idx}
                                                        className="px-6 py-3 cursor-pointer hover:bg-purple-50 flex items-center gap-3 group transition-colors border-b border-gray-50 last:border-0"
                                                    >
                                                        <div className="p-2 bg-purple-100 text-purple-600 rounded-full group-hover:bg-purple-200 transition-colors" onClick={() => { handleCommandClick(cmd); setIsFocused(false); }}>
                                                            <FaMicrophone className="text-xs" />
                                                        </div>
                                                        <span className="text-gray-600 group-hover:text-purple-700 flex-1 font-medium" onClick={() => { handleCommandClick(cmd); setIsFocused(false); }}>{cmd}</span>
                                                        <button
                                                            onClick={(e) => { e.stopPropagation(); addToLibrary(cmd); }}
                                                            className="p-2 text-gray-300 hover:text-indigo-600 opacity-0 group-hover:opacity-100 transition-opacity"
                                                            title="Guardar en biblioteca"
                                                        >
                                                            <FaSave className="text-xs" />
                                                        </button>
                                                    </li>
                                                ))}
                                            </ul>
                                        </>
                                    );
                                })()}
                            </div>
                        )}
                    </div>
                )}
            </div>

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
    );
}
