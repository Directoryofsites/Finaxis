'use client';

import React from 'react';
import CreatableSelect from 'react-select/creatable';
import { useTheme } from '../../context/ThemeContext';

const ConceptoSelect = ({ options, value, onChange, onKeyDown, placeholder = "DescripciÃ³n...", isDisabled = false }) => {
    const { isDarkMode } = useTheme();

    const selectOptions = options.map(c => ({
        value: c.id || c.descripcion,
        label: c.descripcion
    }));

    const selectedOption = value ? { value, label: value } : null;

    const customStyles = {
        control: (base) => ({
            ...base,
            backgroundColor: isDarkMode ? '#1f2937' : '#ffffff',
            borderColor: isDarkMode ? '#374151' : '#e5e7eb',
            color: isDarkMode ? '#ffffff' : '#000000',
            minHeight: '38px',
            fontSize: '14px',
            borderRadius: '0.5rem',
            '&:hover': {
                borderColor: '#3b82f6'
            }
        }),
        menu: (base) => ({
            ...base,
            backgroundColor: isDarkMode ? '#1f2937' : '#ffffff',
            zIndex: 9999
        }),
        option: (base, { isFocused, isSelected }) => ({
            ...base,
            backgroundColor: isSelected 
                ? '#3b82f6' 
                : isFocused 
                    ? (isDarkMode ? '#374151' : '#eff6ff') 
                    : 'transparent',
            color: isSelected ? '#ffffff' : (isDarkMode ? '#ffffff' : '#000000'),
            cursor: 'pointer',
            fontSize: '14px'
        }),
        singleValue: (base) => ({
            ...base,
            color: isDarkMode ? '#ffffff' : '#000000'
        }),
        input: (base) => ({
            ...base,
            color: isDarkMode ? '#ffffff' : '#000000'
        })
    };

    return (
        <CreatableSelect
            options={selectOptions}
            value={selectedOption}
            onChange={(opt) => onChange(opt ? opt.label : '')}
            onKeyDown={onKeyDown}
            onCreateOption={(inputValue) => onChange(inputValue)}
            placeholder={placeholder}
            isDisabled={isDisabled}
            styles={customStyles}
            formatCreateLabel={(inputValue) => `Usar "${inputValue}"`}
            isClearable
            menuPortalTarget={typeof document !== 'undefined' ? document.body : null}
            menuPlacement="auto"
        />
    );
};

export default ConceptoSelect;
