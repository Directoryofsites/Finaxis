'use client';

import React from 'react';
import dynamic from 'next/dynamic';

// Este componente actúa como un "puente" seguro para la carga diferida.
// Al ser 'use client', puede utilizar dynamic() con { ssr: false } sin problemas.
const ParametrosInventarioClient = dynamic(
    () => import('./ParametrosInventarioClient'),
    {
        ssr: false,
        loading: () => (
            <div className="flex items-center justify-center p-12">
                <div className="text-gray-500 font-medium">Cargando Parámetros...</div>
            </div>
        )
    }
);

export default function ParametrosInventoryWrapper() {
    return <ParametrosInventarioClient />;
}
