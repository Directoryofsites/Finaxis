import React from 'react';
import Select from 'react-select';
import { useTheme } from '../../context/ThemeContext';

const CuentaSelect = ({ options, value, onChange, onKeyDown, placeholder = "Código o nombre...", isDisabled = false }) => {
    const { isDarkMode } = useTheme();

    // Transformar las cuentas de Finaxis al formato de react-select
    const selectOptions = options.map(c => ({
        value: c.id,
        label: `${c.codigo} - ${c.nombre}`,
        codigo: c.codigo,
        nombre: c.nombre
    }));

    // Encontrar la opción actual basada en el ID
    const selectedOption = selectOptions.find(opt => opt.value === value) || null;

    const customStyles = {
        control: (provided, state) => ({
            ...provided,
            borderRadius: '0.375rem',
            borderColor: state.isFocused ? '#3b82f6' : (isDarkMode ? '#333333' : '#d1d5db'),
            boxShadow: state.isFocused ? '0 0 0 1px #3b82f6' : 'none',
            minHeight: '34px',
            fontSize: '0.875rem',
            backgroundColor: state.isDisabled ? (isDarkMode ? '#111111' : '#f3f4f6') : (isDarkMode ? '#000000' : 'white'),
            color: isDarkMode ? 'white' : '#111827',
        }),
        menu: (provided) => ({
            ...provided,
            zIndex: 9999,
            backgroundColor: isDarkMode ? '#000000' : 'white',
            border: isDarkMode ? '1px solid #333333' : '1px solid #d1d5db',
            minWidth: '450px', // Se expande hacia la derecha
            width: 'max-content',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.2), 0 10px 10px -5px rgba(0, 0, 0, 0.1)',
            borderRadius: '0.5rem',
        }),
        menuList: (provided) => ({
            ...provided,
            maxHeight: '300px', // Mostrar más resultados
        }),
        menuPortal: base => ({ ...base, zIndex: 9999 }),
        option: (provided, state) => ({
            ...provided,
            fontSize: '0.875rem',
            color: state.isSelected ? 'white' : (isDarkMode ? '#ffffff' : '#111827'),
            backgroundColor: state.isSelected ? '#3b82f6' : state.isFocused ? (isDarkMode ? '#222222' : '#eff6ff') : (isDarkMode ? '#000000' : 'white'),
            fontWeight: '600',
            cursor: 'pointer'
        }),
        singleValue: (provided) => ({
            ...provided,
            color: isDarkMode ? 'white' : '#111827',
            fontWeight: '600'
        }),
        input: (provided) => ({
            ...provided,
            color: isDarkMode ? 'white' : 'black',
        }),
        placeholder: (provided) => ({
            ...provided,
            color: isDarkMode ? '#666666' : '#9ca3af'
        }),
        valueContainer: (provided) => ({
            ...provided,
            padding: '0 8px'
        }),
        indicatorsContainer: (provided) => ({
            ...provided,
            height: '32px'
        })
    };

    return (
        <Select
            options={selectOptions}
            value={selectedOption}
            onChange={(opt) => onChange(opt)}
            onKeyDown={onKeyDown}
            placeholder={placeholder}
            isDisabled={isDisabled}
            styles={customStyles}
            noOptionsMessage={() => "No se encontró la cuenta"}
            isClearable
            menuPortalTarget={typeof document !== 'undefined' ? document.body : null}
            menuPlacement="auto"
        />
    );
};

export default CuentaSelect;
