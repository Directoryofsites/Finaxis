"use client";
import { useEffect, useState, useCallback } from 'react';

/**
 * Hook personalizado para manejar la navegación por teclado.
 * 
 * Funcionalidades:
 * 1. Detectar pulsación de tecla ALT para revelar mnemónicos (subrayados).
 * 2. Detectar combos Alt + [Letra] para abrir menús.
 * 3. Manejar tecla ESC para cerrar menús.
 */
export function useKeyboardNavigation({
    setAltPressed,
    handleMenuToggle, // Función para abrir/cerrar un menú por ID
    visibleMenuIds,   // Array de IDs de menús disponibles
    menuMap           // Mapa de Letra -> MenuID (ej: 'c' -> 'contabilidad')
}) {

    // Handler para eventos keydown
    const handleKeyDown = useCallback((e) => {
        // 1. Detectar si se presiona ALT
        if (e.key === 'Alt') {
            setAltPressed(true);
            return; // No bloqueamos el comportamiento nativo todavía
        }

        // 2. Detectar ESC para cerrar todo
        if (e.key === 'Escape') {
            handleMenuToggle(null); // Cerrar todo
            return;
        }

        // 3. Detectar Alt + Letra
        if (e.altKey) {
            const key = e.key.toLowerCase();

            // Verificamos si la tecla corresponde a un menú mapeado
            const targetMenuId = menuMap[key];

            if (targetMenuId) {
                e.preventDefault(); // Prevenir comportamiento del navegador (ej: Alt+A seleccionar todo)
                handleMenuToggle(targetMenuId);
            }
        }
    }, [setAltPressed, handleMenuToggle, menuMap]);

    // Handler para keyup (solo para soltar Alt)
    const handleKeyUp = useCallback((e) => {
        if (e.key === 'Alt') {
            setAltPressed(false);
        }
    }, [setAltPressed]);

    // Registrar event listeners
    useEffect(() => {
        window.addEventListener('keydown', handleKeyDown);
        window.addEventListener('keyup', handleKeyUp);

        return () => {
            window.removeEventListener('keydown', handleKeyDown);
            window.removeEventListener('keyup', handleKeyUp);
        };
    }, [handleKeyDown, handleKeyUp]);
}
