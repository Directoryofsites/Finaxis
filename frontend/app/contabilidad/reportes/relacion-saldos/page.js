export const dynamic = 'force-dynamic';

import React, { Suspense } from 'react';
import RelacionSaldosClient from './RelacionSaldosClient';

export default function RelacionSaldosPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-6 text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
                <p className="mt-4 text-gray-600 font-semibold">Cargando Relación de Saldos...</p>
            </div>
        }>
            <RelacionSaldosClient />
        </Suspense>
    );
}