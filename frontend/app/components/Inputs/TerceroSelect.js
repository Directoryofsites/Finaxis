import React from 'react';
import AsyncSelect from 'react-select/async';
import { getTerceros } from '../../../lib/terceroService';

/**
 * Componente de selección de terceros con búsqueda asíncrona.
 * Permite buscar por nombre o NIT sin cargar todos los registros al inicio.
 * 
 * @param {object} value - Objeto seleccionado { value: id, label: string }
 * @param {function} onChange - Función que recibe el nuevo objeto seleccionado
 * @param {boolean} isDisabled - Si está deshabilitado
 */
const TerceroSelect = ({ value, onChange, isDisabled = false }) => {

    const loadOptions = async (inputValue) => {
        try {
            // Buscamos con filtro (nombre o NIT) y límite de 20 para rapidez
            const terceros = await getTerceros({ filtro: inputValue, limit: 20 });
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
            borderColor: state.isFocused ? '#3b82f6' : '#d1d5db', // ring-blue-500 : gray-300
            boxShadow: state.isFocused ? '0 0 0 1px #3b82f6' : 'none',
            minHeight: '42px',
            fontSize: '0.875rem', // text-sm
            backgroundColor: state.isDisabled ? '#f3f4f6' : 'white',
        }),
        menu: (provided) => ({
            ...provided,
            zIndex: 9999, // Flotar sobre otros elementos
        }),
        option: (provided, state) => ({
            ...provided,
            fontSize: '0.875rem',
            color: state.isSelected ? 'white' : '#111827', // text-gray-900 (Oscuro y legible siempre)
            backgroundColor: state.isSelected ? '#3b82f6' : state.isFocused ? '#eff6ff' : 'white',
            fontWeight: '600', // Bien negrito como pidió el usuario
            cursor: 'pointer'
        }),
        singleValue: (provided) => ({
            ...provided,
            color: '#111827',
            fontWeight: '700'
        }),
        placeholder: (provided) => ({
            ...provided,
            color: '#9ca3af' // text-gray-400
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
            placeholder="Buscar por Nombre, Razón Social o NIT..."
            noOptionsMessage={({ inputValue }) => inputValue ? "No se encontraron resultados" : "Escribe para buscar..."}
            loadingMessage={() => "Buscando..."}
            isClearable
            styles={customStyles}
            required // Nota: AsyncSelect no soporta 'required' nativamente del todo bien en forms HTML5, validación manual recomendada
        />
    );
};

export default TerceroSelect;
