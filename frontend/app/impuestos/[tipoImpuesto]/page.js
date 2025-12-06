"use client";
import React, { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { FaArrowLeft, FaCog, FaEdit, FaCalculator, FaFileSignature } from 'react-icons/fa';

import ParametrosView from '../../../components/impuestos/ParametrosView';
import BorradorView from '../../../components/impuestos/BorradorView';
import SimulacionView from '../../../components/impuestos/SimulacionView';
import DeclaracionView from '../../../components/impuestos/DeclaracionView';

export default function ImpuestoDetalle() {
    const params = useParams();
    const router = useRouter();
    const tipoImpuesto = params.tipoImpuesto; // e.g., 'iva', 'renta'
    const [activeTab, setActiveTab] = useState('parametros');

    // Format title
    const formatTitle = (slug) => {
        if (!slug) return '';
        return slug.charAt(0).toUpperCase() + slug.slice(1).replace(/-/g, ' ');
    };

    const renderContent = () => {
        switch (activeTab) {
            case 'parametros': return <ParametrosView impuesto={tipoImpuesto} />;
            case 'borradores': return <BorradorView impuesto={tipoImpuesto} />;
            case 'simulaciones': return <SimulacionView impuesto={tipoImpuesto} />;
            case 'declaracion': return <DeclaracionView impuesto={tipoImpuesto} />;
            default: return <ParametrosView impuesto={tipoImpuesto} />;
        }
    };

    return (
        <div className="p-6 space-y-6">
            {/* Breadcrumbs & Header */}
            <div className="flex items-center space-x-4 mb-6">
                <Link href="/impuestos" className="text-gray-500 hover:text-gray-700">
                    <FaArrowLeft className="text-xl" />
                </Link>
                <div>
                    <div className="text-sm text-gray-500 breadcrumbs">
                        <Link href="/impuestos" className="hover:underline">Impuestos</Link> &gt; <span className="font-semibold text-gray-700">{formatTitle(tipoImpuesto)}</span>
                    </div>
                    <h1 className="text-3xl font-bold text-gray-800">{formatTitle(tipoImpuesto)}</h1>
                </div>
            </div>

            {/* 4-Level Navigation */}
            <div className="bg-white rounded-lg shadow-sm p-1 inline-flex space-x-1">
                <button
                    onClick={() => setActiveTab('parametros')}
                    className={`px-6 py-2 rounded-md flex items-center space-x-2 transition-colors ${activeTab === 'parametros' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
                >
                    <FaCog /> <span>Parámetros</span>
                </button>
                <button
                    onClick={() => setActiveTab('borradores')}
                    className={`px-6 py-2 rounded-md flex items-center space-x-2 transition-colors ${activeTab === 'borradores' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
                >
                    <FaEdit /> <span>Borradores</span>
                </button>
                <button
                    onClick={() => setActiveTab('simulaciones')}
                    className={`px-6 py-2 rounded-md flex items-center space-x-2 transition-colors ${activeTab === 'simulaciones' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
                >
                    <FaCalculator /> <span>Simulaciones</span>
                </button>
                <button
                    onClick={() => setActiveTab('declaracion')}
                    className={`px-6 py-2 rounded-md flex items-center space-x-2 transition-colors ${activeTab === 'declaracion' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
                >
                    <FaFileSignature /> <span>Declaración</span>
                </button>
            </div>

            {/* Content Area */}
            <div className="mt-6">
                {renderContent()}
            </div>
        </div>
    );
}
