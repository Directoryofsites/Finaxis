'use client';

import { useEffect } from 'react';
import { useSearchParams } from 'next/navigation';

export default function DeepLinkingHandler({ onTrigger }) {
    const searchParams = useSearchParams();

    useEffect(() => {
        const trigger = searchParams.get('trigger');
        if (trigger) {
            // Limpiamos el parámetro de la URL
            const newUrl = window.location.pathname;
            window.history.replaceState({}, '', newUrl);

            // Ejecutamos la acción
            onTrigger(trigger);
        }
    }, [searchParams, onTrigger]);

    return null;
}
