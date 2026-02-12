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

    useEffect(() => {
        if (rightState === 'open') {
            setRightState('closed');
        }
    }, [pathname]);

    // Escuchar evento de guardado en biblioteca para abrir sidebar
    useEffect(() => {
        const handleShowLibrary = () => {
            if (rightState === 'closed') {
                setRightState('open');
            }
        };
        window.addEventListener('show-ai-library', handleShowLibrary);
        return () => window.removeEventListener('show-ai-library', handleShowLibrary);
    }, [rightState]);


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

    // Detectar si es móvil (para evitar márgenes fijos)
    const [isMobile, setIsMobile] = useState(false);

    useEffect(() => {
        const checkMobile = () => setIsMobile(window.innerWidth < 768);
        checkMobile();
        window.addEventListener('resize', checkMobile);
        return () => window.removeEventListener('resize', checkMobile);
    }, []);

    // Calculamos margenes
    const rightSidebarWidth = 350;
    const isPortal = pathname?.startsWith('/portal');

    const mainContentStyle = {
        transition: 'margin-right 0.3s cubic-bezier(0.4, 0, 0.2, 1), margin-left 0.3s',
        // En móvil, NUNCA empujamos contenido (los sidebars son overlays)
        marginRight: (!isPortal && !isMobile && (rightState === 'pinned' || rightState === 'open')) ? `${rightSidebarWidth}px` : (!isPortal && !isMobile ? '48px' : '0px'),
        marginLeft: (isPortal || isMobile) ? '0px' : '48px'
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
