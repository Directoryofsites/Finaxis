import { FaExclamationTriangle } from 'react-icons/fa';

// --- DEFINICIÓN DE WIDGETS ---
// Aquí el usuario puede definir qué widgets aparecen en qué ruta.
// Pro-Tip: Puedes crear nuevos componentes de Widgets en 'frontend/app/components/widgets' e importarlos aquí.

export const CONTEXT_CONFIG = [
    {
        // 1. FACTURACIÓN
        // Si la URL contiene 'facturacion' o 'ventas'
        match: ['/facturacion', '/ventas'],
        title: 'Facturación Rápida',
        widgets: [
            {
                type: 'stat',
                title: 'Ventas Hoy',
                value: '$2.4M',
                change: '+12%',
                color: 'blue'
            },
            {
                type: 'action',
                label: '💰 Calculadora de Descuentos',
                action: 'open_calc_discount', // ID de acción que manejará el Sidebar
                color: 'blue'
            }
        ]
    },
    {
        // 2. NÓMINA
        match: ['/nomina'],
        title: 'Gestión de Talento',
        widgets: [
            {
                type: 'progress',
                title: 'Nómina Quincenal',
                subtitle: 'Diciembre - Q2',
                progress: 70,
                color: 'purple'
            },
            {
                type: 'info',
                icon: '🎂',
                title: 'Cumpleaños',
                text: 'María (Mañana)',
                color: 'yellow'
            }
        ]
    },
    {
        // 3. INVENTARIO
        match: ['/inventario', '/productos'],
        title: 'Control de Stock',
        widgets: [
            {
                type: 'alert',
                title: 'Stock Crítico',
                items: [
                    { label: 'Tornillo 3x4', value: '4 und' },
                    { label: 'Aceite 1L', value: '2 und' }
                ],
                color: 'red'
            }
        ]
    },
    {
        // 4. CARTERA (Ejemplo solicitado por usuario)
        // 4. CARTERA (Ejemplo solicitado por usuario)
        match: ['/cartera', '/reportes/tercero', 'auxiliar-cartera', 'cliente', 'estado'],
        title: 'Recaudo y Cartera',
        widgets: [
            {
                type: 'stat',
                title: 'Cartera Vencida',
                value: '$15.2M',
                change: '-5%',
                color: 'orange'
            },
            {
                type: 'action', // Botón de acción
                label: '📧 Enviar Cobro Masivo',
                action: 'trigger_email_blast',
                color: 'orange'
            }
        ]
    }
];
