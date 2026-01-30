'use client';

import React from 'react';
import Link from 'next/link';
import { useAuth } from '../context/AuthContext';
import ManualButton from '../components/ManualButton';

import {
    FaBuilding,
    FaUsers,
    FaFileInvoiceDollar,
    FaMoneyBillWave,
    FaChartLine,
    FaCogs,
    FaList,
    FaHome
} from 'react-icons/fa';

export default function DashboardPHPage() {
    const { user, loading } = useAuth();

    if (loading) return <p className="p-8 text-center text-gray-500">Cargando módulo PH...</p>;

    const menuItems = [
        {
            title: "Unidades Privadas",
            desc: "Administrar apartamentos, casas y locales.",
            icon: <FaBuilding className="text-4xl text-blue-500" />,
            href: "/ph/unidades",
            color: "border-blue-200 hover:border-blue-500 hover:shadow-blue-100"
        },
        {
            title: "Propietarios",
            desc: "Directorio de copropietarios y residentes.",
            icon: <FaUsers className="text-4xl text-green-500" />,
            href: "/ph/propietarios",
            color: "border-green-200 hover:border-green-500 hover:shadow-green-100"
        },
        {
            title: "Conceptos de Cobro",
            desc: "Definir cuotas de administración y extras.",
            icon: <FaList className="text-4xl text-purple-500" />,
            href: "/ph/conceptos",
            color: "border-purple-200 hover:border-purple-500 hover:shadow-purple-100"
        },
        {
            title: "Facturación Masiva",
            desc: "Generar cuentas de cobro mensuales.",
            icon: <FaFileInvoiceDollar className="text-4xl text-indigo-500" />,
            href: "/ph/facturacion",
            color: "border-indigo-200 hover:border-indigo-500 hover:shadow-indigo-100"
        },
        {
            title: "Estado de Cuenta",
            desc: "Consultar saldos y descargar paz y salvos.",
            icon: <FaHome className="text-4xl text-orange-500" />,
            href: "/ph/estado-cuenta",
            color: "border-orange-200 hover:border-orange-500 hover:shadow-orange-100"
        },
        {
            title: "Registro de Pagos",
            desc: "Asentar recaudos de administración.",
            icon: <FaMoneyBillWave className="text-4xl text-emerald-500" />,
            href: "/ph/pagos",
            color: "border-emerald-200 hover:border-emerald-500 hover:shadow-emerald-100"
        },
        {
            title: "Reportes",
            desc: "Informes financieros y de cartera.",
            icon: <FaChartLine className="text-4xl text-teal-500" />,
            href: "/ph/reportes",
            color: "border-teal-200 hover:border-teal-500 hover:shadow-teal-100"
        },
        {
            title: "Configuración PH",
            desc: "Parámetros generales del conjunto.",
            icon: <FaCogs className="text-4xl text-gray-500" />,
            href: "/ph/configuracion",
            color: "border-gray-200 hover:border-gray-500 hover:shadow-gray-100"
        },
    ];

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans">
            <div className="max-w-6xl mx-auto">
                <div className="mb-8">
                    <div className="flex justify-between items-start">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-800 mt-4 flex items-center gap-3">
                                <FaBuilding className="text-gray-400" />
                                Gestión de Propiedad Horizontal
                            </h1>
                            <p className="text-gray-500 mt-1">Administración centralizada de copropiedades.</p>
                        </div>
                        <div className="mt-4">
                            <ManualButton 
                                manualPath="dashboard.html"
                                title="Manual del Dashboard Principal"
                                position="header"
                            />
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {menuItems.map((item, index) => (
                        <Link key={index} href={item.href}>
                            <div className={`bg-white p-6 rounded-xl border-2 transition-all duration-300 transform hover:-translate-y-1 cursor-pointer h-full flex flex-col items-center text-center gap-4 shadow-sm ${item.color}`}>
                                <div className="p-4 bg-gray-50 rounded-full">
                                    {item.icon}
                                </div>
                                <div>
                                    <h3 className="text-xl font-bold text-gray-800">{item.title}</h3>
                                    <p className="text-sm text-gray-500 mt-2">{item.desc}</p>
                                </div>
                            </div>
                        </Link>
                    ))}
                </div>
            </div>
        </div>
    );
}
