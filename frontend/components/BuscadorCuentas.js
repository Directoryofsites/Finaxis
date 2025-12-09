import React, { useState, useEffect, useRef } from 'react';
import { getPlanCuentasFlat } from '../lib/planCuentasService';
import { FaSearch, FaBook, FaTimes, FaSpinner } from 'react-icons/fa';

/**
 * Componente para buscar y seleccionar Cuentas Contables.
 * @param {Function} onSelect - Retorna el objeto cuenta seleccionado { id, codigo, nombre }.
 * @param {String} selectedCodigo - Código de la cuenta pre-seleccionada (opcional).
 * @param {String} label - Etiqueta del campo.
 */
export default function BuscadorCuentas({ onSelect, selectedCodigo, label = "Cuenta Contable" }) {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [filteredResults, setFilteredResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [showResults, setShowResults] = useState(false);
    const [selectedCuenta, setSelectedCuenta] = useState(null);
    const wrapperRef = useRef(null);

    // Cargar todas las cuentas al montar (o optimizar si son muchas)
    useEffect(() => {
        const fetchCuentas = async () => {
            try {
                setLoading(true);
                // Traemos cuentas que permiten movimiento
                const response = await getPlanCuentasFlat({ permite_movimiento: true });
                setResults(response.data);
            } catch (error) {
                console.error("Error cargando cuentas:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchCuentas();
    }, []);

    // Sincronizar selección inicial
    useEffect(() => {
        if (selectedCodigo && results.length > 0) {
            const found = results.find(c => c.codigo === selectedCodigo);
            if (found) setSelectedCuenta(found);
            else setSelectedCuenta({ codigo: selectedCodigo, nombre: 'Cuenta Desconocida' });
        } else if (!selectedCodigo) {
            setSelectedCuenta(null);
        }
    }, [selectedCodigo, results]);

    // Filtrado local
    useEffect(() => {
        if (query.trim() === '') {
            setFilteredResults([]);
        } else {
            const lowerQ = query.toLowerCase();
            const filtered = results.filter(c =>
                c.codigo.toLowerCase().includes(lowerQ) ||
                c.nombre.toLowerCase().includes(lowerQ)
            ).slice(0, 20); // Limitar a 20 resultados
            setFilteredResults(filtered);
        }
    }, [query, results]);

    // Cerrar al hacer click fuera
    useEffect(() => {
        function handleClickOutside(event) {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
                setShowResults(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [wrapperRef]);

    const handleSelect = (cuenta) => {
        setSelectedCuenta(cuenta);
        onSelect(cuenta); // Retornamos objeto completo
        setQuery('');
        setShowResults(false);
    };

    const handleClear = () => {
        setSelectedCuenta(null);
        onSelect(null);
        setQuery('');
    };

    return (
        <div className="relative w-full" ref={wrapperRef}>
            <label className="block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide">{label}</label>

            {selectedCuenta ? (
                <div className="flex items-center justify-between p-2 pl-3 bg-blue-50 border border-blue-200 rounded-lg text-blue-900 shadow-sm">
                    <div className="flex items-center gap-2 overflow-hidden">
                        <FaBook className="text-blue-500 shrink-0" />
                        <div className="flex flex-col truncate">
                            <span className="font-bold text-sm truncate">{selectedCuenta.codigo} - {selectedCuenta.nombre}</span>
                        </div>
                    </div>
                    <button
                        type="button"
                        onClick={handleClear}
                        className="p-2 text-blue-400 hover:text-red-500 hover:bg-white rounded-full transition-all"
                    >
                        <FaTimes />
                    </button>
                </div>
            ) : (
                <div className="relative">
                    <input
                        type="text"
                        className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm outline-none transition-all"
                        placeholder="Buscar por código o nombre..."
                        value={query}
                        onChange={(e) => { setQuery(e.target.value); setShowResults(true); }}
                        onFocus={() => setShowResults(true)}
                    />
                    <div className="absolute left-3 top-2.5 text-gray-400">
                        {loading ? <FaSpinner className="animate-spin text-indigo-500" /> : <FaSearch />}
                    </div>

                    {showResults && filteredResults.length > 0 && (
                        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-100 rounded-lg shadow-xl max-h-60 overflow-y-auto animate-fadeIn">
                            {filteredResults.map((c) => (
                                <button
                                    key={c.id}
                                    type="button"
                                    onClick={() => handleSelect(c)}
                                    className="w-full text-left px-4 py-3 hover:bg-blue-50 border-b border-gray-50 last:border-0 transition-colors flex flex-col group"
                                >
                                    <span className="font-bold text-sm text-gray-700 group-hover:text-blue-700">
                                        {c.codigo} - {c.nombre}
                                    </span>
                                </button>
                            ))}
                        </div>
                    )}
                    {showResults && filteredResults.length === 0 && query !== '' && (
                        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-100 rounded-lg shadow-xl p-4 text-center text-gray-400 text-sm italic">
                            No se encontraron cuentas.
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
