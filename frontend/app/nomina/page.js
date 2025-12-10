"use client";
import React from 'react';
import { FaUsers, FaCalculator, FaFileAlt, FaChartLine } from 'react-icons/fa';
import Link from 'next/link';

export default function NominaDashboard() {
    const cards = [
        { title: 'Gestión de Empleados', desc: 'Crear, editar y listar empleados.', icon: FaUsers, href: '/nomina/empleados', color: 'bg-blue-500' },
        { title: 'Liquidar Nómina', desc: 'Calcular nómina quincenal/mensual.', icon: FaCalculator, href: '/nomina/liquidar', color: 'bg-green-500' },
        { title: 'Histórico y Desprendibles', desc: 'Ver pagos anteriores y PDFs.', icon: FaFileAlt, href: '/nomina/desprendibles', color: 'bg-purple-500' },
        { title: 'Reportes Legales', desc: 'PILA y provisiones.', icon: FaChartLine, href: '/nomina/reportes', color: 'bg-orange-500' },
    ];

    return (
        <div className="p-8">
            <h1 className="text-3xl font-light text-gray-800 mb-8 border-b pb-4">
                Módulo de Nómina <span className="text-sm bg-blue-100 text-blue-800 py-1 px-3 rounded-full ml-4 font-bold">Colombia 2025</span>
            </h1>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {cards.map((card, idx) => (
                    <Link key={idx} href={card.href} className="group">
                        <div className="bg-white rounded-xl shadow-md p-6 hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 border border-gray-100 h-full flex flex-col items-center text-center cursor-pointer">
                            <div className={`${card.color} text-white p-4 rounded-full mb-4 shadow-lg group-hover:scale-110 transition-transform`}>
                                <card.icon size={30} />
                            </div>
                            <h3 className="text-xl font-semibold text-gray-700 mb-2 group-hover:text-blue-600">{card.title}</h3>
                            <p className="text-gray-500 text-sm">{card.desc}</p>
                        </div>
                    </Link>
                ))}
            </div>

            <div className="mt-12 bg-blue-50 p-6 rounded-lg border border-blue-100">
                <h3 className="text-lg font-bold text-blue-800 mb-2">Parámetros Vigentes (2025)</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-blue-900">
                    <div className="bg-white p-3 rounded shadow-sm">
                        <span className="block text-gray-500 text-xs">Salario Mínimo</span>
                        <span className="font-bold text-lg">$ 1.423.500</span>
                    </div>
                    <div className="bg-white p-3 rounded shadow-sm">
                        <span className="block text-gray-500 text-xs">Auxilio Transporte</span>
                        <span className="font-bold text-lg">$ 200.000</span>
                    </div>
                    <div className="bg-white p-3 rounded shadow-sm">
                        <span className="block text-gray-500 text-xs">Aporte Salud/Pensión</span>
                        <span className="font-bold text-lg">4% / 4%</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
