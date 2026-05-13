import React from 'react';
import AsyncSelect from 'react-select/async';
import { getTerceros } from '../../../lib/terceroService';
import { useTheme } from '../../context/ThemeContext';

/**
 * Componente de selección de terceros con búsqueda asíncrona.
 * Permite buscar por nombre o NIT sin cargar todos los registros al inicio.
 * 
 * @param {object} value - Objeto seleccionado { value: id, label: string }
 * @param {function} onChange - Función que recibe el nuevo objeto seleccionado
 * @param {boolean} isDisabled - Si está deshabilitado
 */
const TerceroSelect = ({ value, onChange, isDisabled = false, placeholder = "Buscar por Nombre, Razón Social o NIT...", filterVendedores = false }) => {
    const { isDarkMode } = useTheme();
    const loadOptions = async (inputValue) => {
        try {
            // Buscamos con filtro (nombre o NIT) y límite de 20 para rapidez
            const params = { filtro: inputValue, limit: 20 };
            if (filterVendedores) {
                params.es_vendedor = true;
            }
            const terceros = await getTerceros(params);
            return terceros.map(t => ({
                value: t.id,
                label: `(${t.nit}) ${t.razon_social}`
            }));
        } catch (error) {
            console.error("Error cargando terceros:", error);
            return [];
        }
    };

    // Estilos personalizados para integrar con Tailwind
    const customStyles = {
        control: (provided, state) => ({
            ...provided,
            borderRadius: '0.5rem', // rounded-lg
            borderColor: state.isFocused ? '#3b82f6' : (isDarkMode ? '#333333' : '#d1d5db'),
            boxShadow: state.isFocused ? '0 0 0 1px #3b82f6' : 'none',
            minHeight: '42px',
            fontSize: '0.875rem', // text-sm
            backgroundColor: state.isDisabled ? (isDarkMode ? '#111111' : '#f3f4f6') : (isDarkMode ? '#000000' : 'white'),
            color: isDarkMode ? 'white' : '#111827',
        }),
        menu: (provided) => ({
            ...provided,
            zIndex: 9999,
            backgroundColor: isDarkMode ? '#000000' : 'white',
            border: isDarkMode ? '1px solid #333333' : '1px solid #d1d5db',
            minWidth: '500px', // Los nombres de terceros suelen ser largos
            width: 'max-content',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.2)',
            borderRadius: '0.5rem',
        }),
        menuList: (provided) => ({
            ...provided,
            maxHeight: '350px',
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
            fontWeight: '700'
        }),
        input: (provided) => ({
            ...provided,
            color: isDarkMode ? 'white' : 'black',
        }),
        placeholder: (provided) => ({
            ...provided,
            color: isDarkMode ? '#666666' : '#9ca3af'
        })
    };

    return (
        <AsyncSelect
            value={value}
            onChange={onChange}
            loadOptions={loadOptions}
            cacheOptions
            defaultOptions
            isDisabled={isDisabled}
            placeholder={placeholder}
            noOptionsMessage={({ inputValue }) => inputValue ? "No se encontraron resultados" : "Escribe para buscar..."}
            loadingMessage={() => "Buscando..."}
            isClearable
            styles={customStyles}
            required
            menuPortalTarget={typeof document !== 'undefined' ? document.body : null}
            menuPlacement="auto"
        />
    );
};

export default TerceroSelect;
