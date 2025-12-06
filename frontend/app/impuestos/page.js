"use client";
import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '../context/AuthContext'; // Assuming AuthContext is in frontend/app/context
import { FaFileInvoiceDollar, FaChartLine, FaUniversity, FaStamp, FaShoppingCart, FaBuilding, FaMoneyBillWave, FaCalendarAlt, FaFileAlt, FaBars } from 'react-icons/fa';
import Sidebar from '../../components/Sidebar';
import { menuStructure } from '../../lib/menuData';

// Reusable ModuleTile component (Matching Inventario/Global Style)
const ModuleTile = ({ title, description, icon, onClick, href }) => {
    const IconComponent = icon || FaFileAlt;
    // Style matching "Inventario" (Green icons, white card)
    // Removed 'isFolder' logic to enforce consistency
    const colorClass = 'text-green-600';

    const Content = () => (
        <div className="flex flex-col items-start justify-start p-4 h-24 text-left bg-white border border-gray-200 rounded-lg shadow-sm hover:border-blue-500 hover:shadow-md transition duration-200 group transform hover:scale-[1.01] w-full cursor-pointer">
            <div className="flex items-center space-x-3">
                <IconComponent size={24} className={`mb-1 ${colorClass} group-hover:text-blue-700`} />
                <span className="text-sm font-semibold truncate text-gray-800">{title}</span>
            </div>
            <span className="text-xs text-gray-500 mt-1 truncate max-w-full">{description}</span>
        </div>
    );

    if (href) {
        return <Link href={href} className="w-full"><Content /></Link>;
    }

    return <button onClick={onClick} className="w-full"><Content /></button>;
};

export default function ImpuestosDashboard() {
    const { user, logout } = useAuth();
    const router = useRouter();
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    const impuestos = [
        { id: 'iva', nombre: 'IVA', icon: FaFileInvoiceDollar, desc: 'Gestión de Impuesto al Valor Agregado' },
        { id: 'renta', nombre: 'Renta', icon: FaChartLine, desc: 'Impuesto sobre la Renta y Complementarios' },
        { id: 'retefuente', nombre: 'Retención en la Fuente', icon: FaMoneyBillWave, desc: 'Gestión de Retenciones Mensuales' },
        { id: 'reteica', nombre: 'ReteICA', icon: FaUniversity, desc: 'Retención de Industria y Comercio' },
        { id: 'ica', nombre: 'Industria y Comercio', icon: FaBuilding, desc: 'Impuesto Municipal ICA' },
        { id: 'timbre', nombre: 'Timbre', icon: FaStamp, desc: 'Impuesto de Timbre Nacional' },
        { id: 'consumo', nombre: 'Impuesto al Consumo', icon: FaShoppingCart, desc: 'Impuesto Nacional al Consumo' },
        { id: 'calendario', nombre: 'Calendario y Obligaciones', icon: FaCalendarAlt, desc: 'Vencimientos, Plazos y Estado de Obligaciones' },
    ];

    const handleMenuClick = (moduleId) => {
        const module = menuStructure.find(m => m.id === moduleId);
        if (module && module.route) {
            router.push(module.route);
        } else {
            // Redirect to home with module query param to activate the correct view
            router.push(`/?module=${moduleId}`);
        }
    };

    return (
        <div className="flex h-screen bg-gray-100">
            {/* Botón de Menú para móvil */}
            <button
                className="p-4 text-blue-600 fixed top-0 left-0 z-40 md:hidden"
                onClick={() => setIsMenuOpen(true)}
            >
                <FaBars size={24} />
            </button>

            {/* Sidebar Reutilizable */}
            <Sidebar
                activeModuleId="impuestos"
                onMenuClick={handleMenuClick}
                isMenuOpen={isMenuOpen}
                setIsMenuOpen={setIsMenuOpen}
                user={user}
                logout={logout}
            />

            {/* Contenido Principal */}
            <div className="flex-1 flex flex-col overflow-hidden">
                <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-start px-6 shadow-sm">
                    <div className="text-2xl font-light text-slate-800 flex items-center">
                        <FaFileInvoiceDollar className="w-6 h-6 mr-3 text-blue-500" />
                        Explorador de Módulos: <strong className="font-semibold ml-2">Impuestos</strong>
                    </div>
                </header>

                <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50 p-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {impuestos.map((imp) => (
                            <ModuleTile
                                key={imp.id}
                                title={imp.nombre}
                                description={imp.desc}
                                icon={imp.icon}
                                href={imp.id === 'calendario' ? '/impuestos/calendario' : `/impuestos/${imp.id}`}
                            />
                        ))}
                    </div>
                </main>
            </div>
        </div>
    );
}
