'use client';

import React, { useState, useEffect, useRef } from 'react';
import { FaChevronDown, FaTimes } from 'react-icons/fa';

export default function AutocompleteInput({ items, value, onChange, placeholder, searchKey, displayKey, renderOption }) {
    const [inputValue, setInputValue] = useState('');
    const [filteredItems, setFilteredItems] = useState([]);
    const [isOpen, setIsOpen] = useState(false);
    const [highlightedIndex, setHighlightedIndex] = useState(-1);
    const wrapperRef = useRef(null);
    const inputRef = useRef(null);

    useEffect(() => {
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
                setHighlightedIndex(-1);
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
        setHighlightedIndex(0);

        if (val.trim() === '') {
            setFilteredItems(items.slice(0, 50));
            return;
        }

        const filtered = items.filter(item => {
            const itemValue = item[searchKey] || item[displayKey];
            return itemValue.toString().toLowerCase().includes(val.toLowerCase());
        });
        setFilteredItems(filtered);
    };

    const handleSelectItem = (item) => {
        if (!item) return;
        const displayVal = item[displayKey];
        setInputValue(displayVal);
        setFilteredItems([]);
        onChange(item);
        setIsOpen(false);
        setHighlightedIndex(-1);
    };

    const clearSelection = () => {
        setInputValue('');
        onChange(null);
        setIsOpen(false);
        setHighlightedIndex(-1);
    };

    const currentItems = filteredItems.length > 0 ? filteredItems : items.slice(0, 50);

    const handleKeyDown = (e) => {
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (!isOpen) {
                setIsOpen(true);
                setHighlightedIndex(0);
            } else {
                setHighlightedIndex(prev => prev < currentItems.length - 1 ? prev + 1 : prev);
            }
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            setHighlightedIndex(prev => prev > 0 ? prev - 1 : 0);
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (isOpen && currentItems.length > 0) {
                const indexToSelect = highlightedIndex >= 0 ? highlightedIndex : 0;
                handleSelectItem(currentItems[indexToSelect]);
            }
            // SIEMPRE saltamos al siguiente campo con Enter (como pidiÃ³ el usuario)
            setTimeout(() => {
                const nextInput = inputRef.current?.closest('td')?.nextElementSibling?.querySelector('input');
                if (nextInput) nextInput.focus();
            }, 50);
        } else if (e.key === 'Tab') {
            if (isOpen && currentItems.length > 0) {
                const indexToSelect = highlightedIndex >= 0 ? highlightedIndex : 0;
                handleSelectItem(currentItems[indexToSelect]);
            }
        } else if (e.key === 'Escape') {
            setIsOpen(false);
            setHighlightedIndex(-1);
        }
    };

    return (
        <div ref={wrapperRef} className="relative w-full">
            <div className="relative">
                <input
                    ref={inputRef}
                    type="text"
                    className="w-full border rounded-lg p-2 pr-8 focus:ring-2 focus:ring-blue-100 outline-none transition-all text-gray-900"
                    placeholder={placeholder}
                    value={inputValue}
                    onChange={handleInputChange}
                    onKeyDown={handleKeyDown}
                    onFocus={() => {
                        if (inputValue === '') {
                            setFilteredItems(items.slice(0, 50));
                        }
                        setIsOpen(true);
                        setHighlightedIndex(0);
                    }}
                />

                {inputValue && (
                    <button
                        type="button"
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

            {isOpen && (currentItems.length > 0) && (
                <ul className="absolute z-50 w-full bg-white border border-gray-100 rounded-lg shadow-lg max-h-60 overflow-y-auto mt-1">
                    {currentItems.map((item, index) => (
                        <li
                            key={index}
                            className={`p-2 cursor-pointer text-gray-900 text-sm border-b border-gray-50 last:border-0 ${
                                highlightedIndex === index ? 'bg-blue-100' : 'hover:bg-blue-50'
                            }`}
                            onClick={() => handleSelectItem(item)}
                            onMouseEnter={() => setHighlightedIndex(index)}
                        >
                            {renderOption ? renderOption(item) : item[displayKey]}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}
