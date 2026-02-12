export const dynamic = 'force-dynamic';

import React, { Suspense } from 'react';
import EstadoCuentaProveedorClient from './EstadoCuentaProveedorClient';

export default function EstadoCuentaProveedorPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
                <p className="mt-4 text-indigo-600 font-semibold animate-pulse">Cargando Reporte...</p>
            </div>
        }>
            <EstadoCuentaProveedorClient />
        </Suspense>
    );
}