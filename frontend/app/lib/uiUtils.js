/**
 * Genera estilos consistentes para react-select en modo oscuro y claro.
 * @param {boolean} isDarkMode - Indica si el modo oscuro está activo.
 * @returns {object} - Objeto de estilos para react-select.
 */
export const getSelectStyles = (isDarkMode) => ({
    control: (base, state) => ({
        ...base,
        minHeight: '2.6rem',
        borderRadius: '0.5rem',
        borderColor: state.isFocused ? '#6366f1' : (isDarkMode ? '#333333' : '#D1D5DB'),
        backgroundColor: isDarkMode ? '#000000' : '#ffffff',
        color: isDarkMode ? '#ffffff' : '#000000',
        boxShadow: state.isFocused ? '0 0 0 1px #6366f1' : 'none',
        '&:hover': {
            borderColor: '#6366f1'
        }
    }),
    menu: (base) => ({
        ...base,
        backgroundColor: isDarkMode ? '#000000' : '#ffffff',
        border: isDarkMode ? '1px solid #333333' : '1px solid #E5E7EB',
        zIndex: 9999
    }),
    option: (base, state) => ({
        ...base,
        backgroundColor: state.isSelected
            ? '#6366f1'
            : state.isFocused
                ? (isDarkMode ? '#1a1a1a' : '#f3f4f6')
                : 'transparent',
        color: state.isSelected
            ? '#ffffff'
            : (isDarkMode ? '#ffffff' : '#111827'),
        cursor: 'pointer',
        fontSize: '0.875rem'
    }),
    singleValue: (base) => ({
        ...base,
        color: isDarkMode ? '#ffffff' : '#111827'
    }),
    input: (base) => ({
        ...base,
        color: isDarkMode ? '#ffffff' : '#111827'
    }),
    placeholder: (base) => ({
        ...base,
        color: isDarkMode ? '#666666' : '#9CA3AF'
    })
});
