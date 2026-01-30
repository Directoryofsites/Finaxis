'use client';

import React, { useState, useEffect, useRef } from 'react';
import { FaChevronDown, FaTimes } from 'react-icons/fa';

export default function AutocompleteInput({ items, value, onChange, placeholder, searchKey, displayKey }) {
    const [inputValue, setInputValue] = useState('');
    const [filteredItems, setFilteredItems] = useState([]);
    const [isOpen, setIsOpen] = useState(false);
    const wrapperRef = useRef(null);

    useEffect(() => {
        // Sync internal input with prop value if it changes externally
        if (value) {
            setInputValue(value);
        } else {
            setInputValue('');
        }
    }, [value]);

    useEffect(() => {
        function handleClickOutside(event) {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [wrapperRef]);

    const handleInputChange = (e) => {
        const val = e.target.value;
        setInputValue(val);
        setIsOpen(true);

        if (val.trim() === '') {
            setFilteredItems([]);
            // onChange(null); // Optional: clear selection if typed text is cleared
            return;
        }

        const filtered = items.filter(item => {
            const itemValue = item[searchKey] || item[displayKey];
            return itemValue.toString().toLowerCase().includes(val.toLowerCase());
        });
        setFilteredItems(filtered);
    };

    const handleSelectItem = (item) => {
        const displayVal = item[displayKey];
        setInputValue(displayVal);
        onChange(item);
        setIsOpen(false);
    };

    const clearSelection = () => {
        setInputValue('');
        onChange(null);
        setIsOpen(false);
    };

    return (
        <div ref={wrapperRef} className="relative w-full">
            <div className="relative">
                <input
                    type="text"
                    className="w-full border rounded-lg p-2 pr-8 focus:ring-2 focus:ring-blue-100 outline-none transition-all text-gray-900"
                    placeholder={placeholder}
                    value={inputValue}
                    onChange={handleInputChange}
                    onFocus={() => {
                        if (inputValue === '') {
                            setFilteredItems(items.slice(0, 50)); // Show some initial items if empty
                        }
                        setIsOpen(true);
                    }}
                />

                {inputValue && (
                    <button
                        onClick={clearSelection}
                        className="absolute right-8 top-3 text-gray-400 hover:text-gray-600"
                    >
                        <FaTimes size={12} />
                    </button>
                )}

                <div className="absolute right-3 top-3 text-gray-400 pointer-events-none">
                    <FaChevronDown size={12} />
                </div>
            </div>

            {isOpen && (filteredItems.length > 0 || items.length > 0) && (
                <ul className="absolute z-50 w-full bg-white border border-gray-100 rounded-lg shadow-lg max-h-60 overflow-y-auto mt-1">
                    {filteredItems.length > 0 ? (
                        filteredItems.map((item, index) => (
                            <li
                                key={index}
                                className="p-2 hover:bg-blue-50 cursor-pointer text-gray-900 text-sm border-b border-gray-50 last:border-0"
                                onClick={() => handleSelectItem(item)}
                            >
                                {item[displayKey]}
                            </li>
                        ))
                    ) : (
                        inputValue === '' ? (
                            items.slice(0, 50).map((item, index) => (
                                <li
                                    key={index}
                                    className="p-2 hover:bg-blue-50 cursor-pointer text-gray-900 text-sm border-b border-gray-50 last:border-0"
                                    onClick={() => handleSelectItem(item)}
                                >
                                    {item[displayKey]}
                                </li>
                            ))
                        ) : (
                            <li className="p-4 text-center text-gray-400 text-sm">No se encontraron resultados</li>
                        )
                    )}
                </ul>
            )}
        </div>
    );
}
