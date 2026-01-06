import React, { useState, useEffect, useRef } from 'react';
import { FaChevronDown, FaTimes, FaSearch, FaCheck } from 'react-icons/fa';

/**
 * Componente MultiSelect Reutilizable
 * @param {Array} options - Array de objetos { value, label }
 * @param {Array} value - Array de values seleccionados [1, 2, 3]
 * @param {Function} onChange - Callback que recibe el nuevo array de values seleccionados
 * @param {String} placeholder - Texto a mostrar cuando no hay nada seleccionado
 * @param {String} label - Label del campo (opcional)
 */
export default function MultiSelect({ options = [], value = [], onChange, placeholder = "Seleccionar...", label, getDependentValues }) {
    const [isOpen, setIsOpen] = useState(false);
    const [searchTerm, setSearchTerm] = useState("");
    const dropdownRef = useRef(null);

    // Cerrar al hacer clic fuera
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    // Filtrar opciones
    const filteredOptions = options.filter(opt =>
        opt.label.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const handleToggleOption = (optionValue) => {
        const isSelected = value.includes(optionValue);
        let newValue;
        
        // Lógica de Dependencias (Jerarquía)
        let dependentValues = [];
        if (getDependentValues) {
            dependentValues = getDependentValues(optionValue, options);
        }

        if (isSelected) {
            // Deseleccionar: Remover el valor Y sus dependientes
            newValue = value.filter(v => v !== optionValue && !dependentValues.includes(v));
        } else {
            // Seleccionar: Agregar el valor Y sus dependientes (evitando duplicados)
            const toAdd = [optionValue, ...dependentValues];
            const uniqueToAdd = toAdd.filter(v => !value.includes(v));
            newValue = [...value, ...uniqueToAdd];
        }
        onChange(newValue);
    };

    const handleRemoveItem = (e, valToRemove) => {
        e.stopPropagation();
        const newValue = value.filter(v => v !== valToRemove);
        onChange(newValue);
    };

    const handleSelectAll = () => {
        if (value.length === options.length) {
            onChange([]); // Deseleccionar todo
        } else {
            onChange(options.map(o => o.value)); // Seleccionar todo
        }
    };

    // Renderizar etiquetas seleccionadas (Limitado a 2 para no romper diseño)
    const renderTags = () => {
        if (value.length === 0) return <span className="text-gray-400">{placeholder}</span>;

        if (value.length > 2) {
            return (
                <span className="bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-md text-xs font-bold">
                    {value.length} seleccionados
                </span>
            );
        }

        return value.map(val => {
            const option = options.find(o => o.value === val);
            if (!option) return null;
            return (
                <span key={val} className="flex items-center gap-1 bg-indigo-50 text-indigo-700 border border-indigo-100 px-2 py-0.5 rounded text-xs">
                    <span className="truncate max-w-[80px]">{option.label}</span>
                    <button onClick={(e) => handleRemoveItem(e, val)} className="hover:text-red-500"><FaTimes /></button>
                </span>
            );
        });
    };

    return (
        <div className="w-full relative" ref={dropdownRef}>
            {label && <label className="block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide">{label}</label>}

            {/* Trigger Box */}
            <div
                className={`w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm bg-white cursor-pointer min-h-[38px] flex items-center justify-between transition-all ${isOpen ? 'ring-2 ring-indigo-500 border-indigo-500' : 'hover:border-indigo-300'}`}
                onClick={() => setIsOpen(!isOpen)}
            >
                <div className="flex flex-wrap gap-1 items-center overflow-hidden">
                    {renderTags()}
                </div>
                <FaChevronDown className={`text-gray-400 text-xs transition-transform ${isOpen ? 'rotate-180' : ''}`} />
            </div>

            {isOpen && (
                <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-xl max-h-60 overflow-hidden flex flex-col animate-fadeIn">
                    {/* Search Bar */}
                    <div className="p-2 border-b border-gray-100 bg-gray-50">
                        <div className="relative">
                            <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 text-xs" />
                            <input
                                autoFocus
                                type="text"
                                placeholder="Buscar..."
                                className="w-full pl-8 pr-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                            />
                        </div>
                        <button onClick={handleSelectAll} className="text-xs text-indigo-600 font-bold mt-2 hover:underline ml-1">
                            {value.length === options.length ? 'Deseleccionar todos' : 'Seleccionar todos'}
                        </button>
                    </div>

                    {/* Options List */}
                    <div className="overflow-y-auto flex-1 max-h-48 p-1">
                        {filteredOptions.length === 0 ? (
                            <div className="text-center py-4 text-gray-400 text-xs">No hay resultados</div>
                        ) : (
                            filteredOptions.map(opt => {
                                const isSelected = value.includes(opt.value);
                                return (
                                    <div
                                        key={opt.value}
                                        onClick={() => handleToggleOption(opt.value)}
                                        className={`flex items-center px-3 py-2 text-sm cursor-pointer rounded-md transition-colors ${isSelected ? 'bg-indigo-50 text-indigo-700 font-medium' : 'hover:bg-gray-100 text-gray-700'}`}
                                    >
                                        <div className={`w-4 h-4 border rounded mr-2 flex items-center justify-center transition-colors ${isSelected ? 'bg-indigo-600 border-indigo-600' : 'border-gray-400 bg-white'}`}>
                                            {isSelected && <FaCheck className="text-white text-[10px]" />}
                                        </div>
                                        <span className="truncate">{opt.label}</span>
                                    </div>
                                );
                            })
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
