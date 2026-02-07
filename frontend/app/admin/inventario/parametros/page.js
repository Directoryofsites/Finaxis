import React from 'react';
import nextDynamic from 'next/dynamic';

// Carga Dinámica TOTAL: Evita que el servidor intente renderizar este componente cliente
const ParametrosInventarioContent = nextDynamic(
    // Importación dinámica del componente cliente
    () => import('./ParametrosInventarioClient'),
    {
        // 🛑 CRÍTICO: ssr: false deshabilita el renderizado en servidor.
        // Esto evita que next build falle por hooks de browser.
        ssr: false,
        loading: () => <div className="p-8 text-center text-gray-500">Cargando Configuración...</div>
    }
);

// Configuraciones de página: Dejamos valores por defecto para evitar conflictos con ssr: false

export default function ParametrosInventarioPage() {
    return (
        <ParametrosInventarioContent />
    );
}
