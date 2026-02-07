import React from 'react';
import ParametrosInventoryWrapper from './ParametrosInventoryWrapper';

// Server Component (Por defecto en Next.js App Router)
// Este archivo es estático y seguro para el build.
// Delega toda la complejidad de "Cliente" al Wrapper.

export const metadata = {
    title: 'Parámetros de Inventario | Finaxis',
    description: 'Configuración de impuestos, retenciones y cuentas para inventario.',
};

export default function ParametrosInventarioPage() {
    return (
        <ParametrosInventoryWrapper />
    );
}
