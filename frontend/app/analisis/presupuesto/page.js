"use client";
import React, { useState } from 'react';
import EscenariosList from './EscenariosList';
import PresupuestoGrid from './PresupuestoGrid';
import { Toaster } from 'react-hot-toast';

export default function PresupuestoDashboardPage() {
    const [selectedEscenario, setSelectedEscenario] = useState(null);

    return (
        <div className="p-6 h-screen flex flex-col bg-gray-50">
            <Toaster position="top-right" />

            {!selectedEscenario ? (
                <>
                    <div className="mb-6">
                        <h1 className="text-2xl font-bold text-gray-800">Panel de Gestión Presupuestal</h1>
                        <p className="text-gray-600">Administra múltiples escenarios (Optimista, Realista, Público) y proyéctalos automáticamente.</p>
                    </div>
                    <EscenariosList onSelectEscenario={setSelectedEscenario} />
                </>
            ) : (
                <PresupuestoGrid
                    escenario={selectedEscenario}
                    onBack={() => setSelectedEscenario(null)}
                />
            )}
        </div>
    );
}
