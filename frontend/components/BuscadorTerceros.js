import React, { useState, useEffect, useRef } from 'react';
import { getTerceros } from '../lib/terceroService'; // Importación correcta
import { FaSearch, FaUser, FaTimes, FaSpinner } from 'react-icons/fa';

/**
 * Componente para buscar y seleccionar Terceros.
 * @param {Function} onSelect - Retorna el objeto tercero seleccionado (o null).
 * @param {Object} selected - Objeto tercero pre-seleccionado (opcional).
 * @param {String} label - Etiqueta del campo.
 */
export default function BuscadorTerceros({ onSelect, selected, label = "Buscar Tercero" }) {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [showResults, setShowResults] = useState(false);
    const wrapperRef = useRef(null);

    // Efecto para cerrar resultados al hacer click fuera
    useEffect(() => {
        function handleClickOutside(event) {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
                setShowResults(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [wrapperRef]);

    // Handle Search
    const handleSearch = async (val) => {
        setQuery(val);
        if (val.length < 2) {
            setResults([]);
            return;
        }

        setLoading(true);
        setShowResults(true);
        try {
            // Asumimos que el backend acepta ?filtro=... o ?search=...
            const data = await getTerceros({ filtro: val, limit: 10 });
            setResults(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error("Error buscando terceros:", error);
            setResults([]);
        } finally {
            setLoading(false);
        }
    };

    const handleSelect = (tercero) => {
        onSelect(tercero);
        // Deferimos la limpieza para evitar conflictos de "removeChild" 
        // cuando React intenta desmontar el nodo que disparó el evento click.
        setTimeout(() => {
            setQuery('');
            setResults([]);
            setShowResults(false);
        }, 0);
    };

    const handleClear = () => {
        onSelect(null);
        setQuery('');
    };

    return (
        <div className="relative w-full" ref={wrapperRef}>
            <label className="block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide">{label}</label>

            {selected ? (
                <div className="flex items-center justify-between p-2 pl-3 bg-indigo-50 border border-indigo-200 rounded-lg text-indigo-900 shadow-sm">
                    <div className="flex items-center gap-2 overflow-hidden">
                        <FaUser className="text-indigo-500 shrink-0" />
                        <div className="flex flex-col truncate">
                            <span className="font-bold text-sm truncate">{selected.razon_social || selected.nombre_comercial}</span>
                            <span className="text-xs text-indigo-400">{selected.nit ? `NIT: ${selected.nit}` : 'Sin ID'}</span>
                        </div>
                    </div>
                    <button
                        type="button"
                        onClick={handleClear}
                        className="p-2 text-indigo-400 hover:text-red-500 hover:bg-white rounded-full transition-all"
                        title="Quitar selección"
                    >
                        <FaTimes />
                    </button>
                </div>
            ) : (
                <div className="relative">
                    <input
                        type="text"
                        className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm outline-none transition-all"
                        placeholder="Nombre, NIT o Razón Social..."
                        value={query}
                        onChange={(e) => handleSearch(e.target.value)}
                        onFocus={() => { if (query.length >= 2) setShowResults(true); }}
                    />
                    <div className="absolute left-3 top-2.5 text-gray-400">
                        {loading ? <FaSpinner className="animate-spin text-indigo-500" /> : <FaSearch />}
                    </div>

                    {/* Resultados Dropdown */}
                    {showResults && (
                        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-100 rounded-lg shadow-xl max-h-60 overflow-y-auto animate-fadeIn">
                            {results.length > 0 ? (
                                results.map((t) => (
                                    <button
                                        key={t.id}
                                        type="button"
                                        onClick={() => handleSelect(t)}
                                        className="w-full text-left px-4 py-3 hover:bg-indigo-50 border-b border-gray-50 last:border-0 transition-colors flex flex-col group"
                                    >
                                        <span className="font-bold text-sm text-gray-700 group-hover:text-indigo-700">
                                            {t.razon_social || t.nombre_comercial}
                                        </span>
                                        <div className="flex justify-between items-center mt-1">
                                            <span className="text-xs text-gray-400">NIT: {t.nit}</span>
                                            <span className="text-[10px] uppercase bg-gray-100 px-2 py-0.5 rounded-full text-gray-500">{t.tipo_tercero || 'Tercero'}</span>
                                        </div>
                                    </button>
                                ))
                            ) : (
                                <div className="p-4 text-center text-gray-400 text-sm italic">
                                    {loading ? 'Buscando...' : 'No se encontraron resultados.'}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
