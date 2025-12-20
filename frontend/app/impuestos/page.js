"use client";
import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '../context/AuthContext';
import { FaFileInvoiceDollar, FaChartLine, FaUniversity, FaStamp, FaShoppingCart, FaBuilding, FaMoneyBillWave, FaCalendarAlt, FaFileAlt } from 'react-icons/fa';
import { menuStructure } from '../../lib/menuData';

// Reusable ModuleTile component (Matching Global Style with Colors)
const ModuleTile = ({ title, description, icon, onClick, href, index = 0 }) => {
    const IconComponent = icon || FaFileAlt;

    // Paleta de colores vibrantes estilo PH
    const palette = [
        { border: 'border-blue-200 hover:border-blue-500', shadow: 'hover:shadow-blue-100', icon: 'text-blue-500', bgIcon: 'bg-blue-50' },     // 0: Azul
        { border: 'border-green-200 hover:border-green-500', shadow: 'hover:shadow-green-100', icon: 'text-green-500', bgIcon: 'bg-green-50' },  // 1: Verde
        { border: 'border-purple-200 hover:border-purple-500', shadow: 'hover:shadow-purple-100', icon: 'text-purple-500', bgIcon: 'bg-purple-50' }, // 2: Morado
        { border: 'border-orange-200 hover:border-orange-500', shadow: 'hover:shadow-orange-100', icon: 'text-orange-500', bgIcon: 'bg-orange-50' }, // 3: Naranja
        { border: 'border-indigo-200 hover:border-indigo-500', shadow: 'hover:shadow-indigo-100', icon: 'text-indigo-500', bgIcon: 'bg-indigo-50' }, // 4: Indigo
        { border: 'border-teal-200 hover:border-teal-500', shadow: 'hover:shadow-teal-100', icon: 'text-teal-500', bgIcon: 'bg-teal-50' },       // 5: Teal
        { border: 'border-pink-200 hover:border-pink-500', shadow: 'hover:shadow-pink-100', icon: 'text-pink-500', bgIcon: 'bg-pink-50' },       // 6: Rosa
        { border: 'border-cyan-200 hover:border-cyan-500', shadow: 'hover:shadow-cyan-100', icon: 'text-cyan-500', bgIcon: 'bg-cyan-50' },       // 7: Cyan
        { border: 'border-emerald-200 hover:border-emerald-500', shadow: 'hover:shadow-emerald-100', icon: 'text-emerald-500', bgIcon: 'bg-emerald-50' }, // 8: Esmeralda
        { border: 'border-red-200 hover:border-red-500', shadow: 'hover:shadow-red-100', icon: 'text-red-500', bgIcon: 'bg-red-50' },           // 9: Rojo
    ];

    // Selección cíclica del tema basada en el índice
    const theme = palette[index % palette.length];

    const containerClasses = `bg-white p-6 rounded-xl border-2 ${theme.border} shadow-sm ${theme.shadow} transition-all duration-300 transform hover:-translate-y-1 cursor-pointer h-full flex flex-col items-center text-center gap-2 group w-full`;
    const iconContainerClasses = `p-4 rounded-full mb-2 transition-colors ${theme.bgIcon} group-hover:bg-opacity-80`;
    const iconClasses = `text-4xl ${theme.icon} transition-colors`;
    const titleClasses = "text-lg font-bold text-gray-800 leading-tight";
    const descClasses = "text-sm text-gray-500";

    const Content = () => (
        <div className={containerClasses}>
            <div className={iconContainerClasses}>
                <IconComponent className={iconClasses} />
            </div>
            <h3 className={titleClasses}>{title}</h3>
            {description && <p className={descClasses}>{description}</p>}
        </div>
    );

    if (href) {
        return <Link href={href} className="w-full"><Content /></Link>;
    }

    return <div onClick={onClick} className="w-full"><Content /></div>;
};

export default function ImpuestosDashboard() {
    const { user } = useAuth();
    // const router = useRouter(); // NO LONGER NEEDED IF ModuleTile uses Link directly

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

    return (
        <div className="flex h-screen bg-gray-100">
            {/* Contenido Principal Full Width */}
            <div className="flex-1 flex flex-col overflow-hidden">
                <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-start px-6 shadow-sm">
                    <div className="text-2xl font-light text-slate-800 flex items-center">
                        <FaFileInvoiceDollar className="w-6 h-6 mr-3 text-blue-500" />
                        Explorador de Módulos: <strong className="font-semibold ml-2">Impuestos</strong>
                    </div>
                </header>


                <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50 p-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {impuestos.map((imp, index) => (
                            <ModuleTile
                                key={imp.id}
                                index={index}
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
