'use client';

import React from 'react';
import { FaBook, FaQuestionCircle } from 'react-icons/fa';

/**
 * Componente reutilizable para botones de manual
 * @param {Object} props - Propiedades del componente
 * @param {string} props.manualPath - Ruta al archivo HTML del manual
 * @param {string} props.title - Título descriptivo del manual
 * @param {'header'|'sidebar'|'floating'} props.position - Posición del botón (default: 'header')
 * @param {string} props.className - Clases CSS adicionales
 * @param {boolean} props.showText - Mostrar texto junto al icono (default: true)
 */
const ManualButton = ({ 
    manualPath, 
    title = "Manual de Usuario", 
    position = 'header',
    className = '',
    showText = true 
}) => {
    const handleOpenManual = () => {
        if (!manualPath) {
            console.warn('ManualButton: No se especificó ruta del manual');
            alert('Manual no disponible en este momento.');
            return;
        }

        // Construir la ruta completa del manual
        const fullPath = manualPath.startsWith('/') ? manualPath : `/Manual/ph/${manualPath}`;
        
        // Abrir en nueva ventana
        const manualWindow = window.open(
            fullPath, 
            '_blank', 
            'width=1200,height=800,scrollbars=yes,resizable=yes,menubar=yes,toolbar=yes'
        );

        if (!manualWindow) {
            // Fallback si el popup fue bloqueado
            window.location.href = fullPath;
        }
    };

    // Estilos base según la posición
    const getBaseStyles = () => {
        const baseStyles = "inline-flex items-center gap-2 transition-all duration-300 font-medium rounded-lg shadow-sm hover:shadow-md transform hover:-translate-y-0.5";
        
        switch (position) {
            case 'header':
                return `${baseStyles} px-4 py-2 bg-indigo-600 text-white hover:bg-indigo-700 text-sm`;
            case 'sidebar':
                return `${baseStyles} px-3 py-2 bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-300 text-sm`;
            case 'floating':
                return `${baseStyles} px-3 py-3 bg-blue-500 text-white hover:bg-blue-600 rounded-full fixed bottom-6 right-6 z-50 shadow-lg`;
            default:
                return `${baseStyles} px-4 py-2 bg-indigo-600 text-white hover:bg-indigo-700 text-sm`;
        }
    };

    // Icono según la posición
    const getIcon = () => {
        const iconClass = position === 'floating' ? 'text-lg' : 'text-sm';
        return <FaBook className={iconClass} />;
    };

    return (
        <button
            onClick={handleOpenManual}
            className={`${getBaseStyles()} ${className}`}
            title={`Abrir ${title}`}
            aria-label={`Abrir manual: ${title}`}
        >
            {getIcon()}
            {showText && position !== 'floating' && (
                <span>Manual</span>
            )}
        </button>
    );
};

export default ManualButton;