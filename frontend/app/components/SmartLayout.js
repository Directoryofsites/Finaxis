'use client';
import React, { useState, useEffect } from 'react';
import SidebarFavorites from './SidebarFavorites';
import TopNavigationBar from '../../components/TopNavigationBar';
import RightSidebar from './RightSidebar';
import { usePathname } from 'next/navigation';

export default function SmartLayout({ children }) {
    // Estado del Sidebar Derecho
    // 'pinned' = fijo y empuja el contenido.
    // 'open' = flotante sobre el contenido.
    // 'closed' = solo pestañas visibles.

    // Iniciar cerrado para mobile first/limpieza, o leer de localStorage si quieres persistencia.
    const [rightState, setRightState] = useState('closed'); // 'closed', 'open', 'pinned'
    const pathname = usePathname();

    // Resetear a closed o open (unpin) al navegar? 
    // UX Decision: Si es 'pinned', se mantiene pinned. Si es 'open' (flotante), se cierra al navegar.
    useEffect(() => {
        if (rightState === 'open') {
            setRightState('closed');
        }
    }, [pathname]);


    // Handlers
    const handleToggle = (shouldOpen) => {
        if (shouldOpen) setRightState('open');
        else if (rightState === 'open') setRightState('closed');
        // Si es pinned, toggle a closed? O a open?
        // Vamos a asumir toggle button en barra cerrada -> Open.
        // Botón cerrar en barra abierta -> Closed.
    };

    const handlePin = () => {
        if (rightState === 'pinned') setRightState('open'); // Desanclar (vuelve a flotante)
        else setRightState('pinned'); // Anclar
    };

    const handleClose = () => {
        setRightState('closed');
    };

    // Calculamos margenes
    // El sidebar izquierdo es fixed w-2 -> hover w-64. No empuja contenido (es overlay o pequeño).
    // El sidebar derecho SI queremos que empuje cuando es PINNED.

    // Ancho del Sidebar Derecho cuando está pinned
    const rightSidebarWidth = 350; // Debe coincidir con el w-[350px] de tailwind

    // Estilo para el contenedor principal
    const isPortal = pathname?.startsWith('/portal');

    const mainContentStyle = {
        transition: 'margin-right 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        // FIX: Empujar contenido siempre que esté visible (Open o Pinned) para evitar solapamiento
        // En portal no hay sidebar derecho ni izquierdo ocupando espacio
        marginRight: (!isPortal && (rightState === 'pinned' || rightState === 'open')) ? `${rightSidebarWidth}px` : (!isPortal ? '48px' : '0px'),
        marginLeft: isPortal ? '0px' : '48px' // Ajuste para el sidebar izquierdo
    };

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col">

            {/* 1. Left Sidebar (Fixed, High Z-Index) - Hide in Portal */}
            {!isPortal && (
                <React.Suspense fallback={<div className="w-12 bg-white h-screen border-r border-gray-200"></div>}>
                    <SidebarFavorites />
                </React.Suspense>
            )}

            {/* 2. Top Navigation (Fixed Top, adjusted margin?) */}
            {/* TopNav suele ser fixed. Si queremos que se ajuste con el Pin, debemos pasare props o envolverlo */}
            {/* Por simplicidad actual, TopNav está fixed w-full. Puede que el RightSidebar la tape. Idealmente RightSidebar tiene z-index mayor. */}
            <div className="z-50">
                <React.Suspense fallback={<div className="h-16 w-full bg-gray-100"></div>}>
                    <TopNavigationBar />
                </React.Suspense>
            </div>

            {/* 3. Main Content Wrapper */}
            {/* TopNav tiene altura h-16 (64px) aprox. Añadimos pad-top */}
            <main
                className="flex-1 pt-20 px-4 pb-4 md:px-8 transition-all duration-300"
                style={mainContentStyle}
            >
                {children}
            </main>

            {/* 4. Right Sidebar (Smart Hub) */}
            <RightSidebar
                isOpen={rightState === 'open'}
                isPinned={rightState === 'pinned'}
                onToggle={handleToggle}
                onPin={handlePin}
                onClose={handleClose}
            />

            {/* Overlay para cerrar modo 'Open' (Flotante) al hacer click fuera */}
            {rightState === 'open' && (
                <div
                    className="fixed inset-0 bg-black/5 z-50 md:hidden"
                    onClick={handleClose}
                    aria-hidden="true"
                />
            )}
        </div>
    );
}
