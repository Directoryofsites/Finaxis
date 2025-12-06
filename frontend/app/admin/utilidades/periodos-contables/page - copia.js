'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../../context/AuthContext';
import Link from 'next/link';
// PASO 1: Importamos nuestro apiService estándar
import { apiService } from '../../../../lib/apiService'; 

export default function PeriodosContablesPage() {

    const { user, authLoading } = useAuth();
    const [empresas, setEmpresas] = useState([]);
    const [selectedEmpresa, setSelectedEmpresa] = useState('');
    const [periodosCerrados, setPeriodosCerrados] = useState([]);
    const [year, setYear] = useState(new Date().getFullYear());
    const [month, setMonth] = useState(new Date().getMonth() + 1);
    const [isLoading, setIsLoading] = useState(true);
    const [isProcessing, setIsProcessing] = useState(false);
    const [error, setError] = useState(null);
    const [message, setMessage] = useState('');

    useEffect(() => {
    const fetchEmpresas = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await apiService.get('/utilidades/soporte/maestros');
            const data = response.data;

            setEmpresas(data.empresas);

            if (user && user.rol === 'superadmin' && data.empresas.length > 0) {
                 setSelectedEmpresa(user.empresaId || data.empresas[0].id);
            } else if (user && data.empresas.length > 0) {
                 setSelectedEmpresa(user.empresaId);
            }
        } catch (err) {
            setError(err.response?.data?.detail || 'No se pudieron cargar las empresas.');
        } finally {
            setIsLoading(false);
        }
    };

    // LA CONDICIÓN CLAVE: Solo se ejecuta si hay usuario Y la autenticación NO está cargando.
    if (user && !authLoading) {
        fetchEmpresas();
    }
}, [user, authLoading]); // Se añade authLoading a las dependencias

    // PASO 3: Refactorizamos fetchPeriodos para usar apiService y useCallback para optimización
    const fetchPeriodos = useCallback(async () => {
        if (!selectedEmpresa) {
            setPeriodosCerrados([]);
            return;
        }

        setIsLoading(true);
        setError(null);
        try {
            const response = await apiService.get(`/periodos?empresa_id=${selectedEmpresa}`);
            setPeriodosCerrados(response.data);
        } catch (err) {
            setError(err.response?.data?.detail || 'No se pudieron cargar los períodos cerrados.');
            setPeriodosCerrados([]); // Limpiar en caso de error
        } finally {
            setIsLoading(false);
        }
    }, [selectedEmpresa]);

    useEffect(() => {
        fetchPeriodos();
    }, [fetchPeriodos]);

    // PASO 4: Refactorizamos el resto de manejadores para usar apiService
    const handleCerrarPeriodo = async () => {
        // ... (validaciones se mantienen)
        if (!selectedEmpresa || !year || !month) {
            alert('Por favor, seleccione una empresa, año y mes.');
            return;
        }
        setIsProcessing(true);
        setError(null);
        setMessage('');
        try {
            const response = await apiService.post('/periodos', {
                empresa_id: parseInt(selectedEmpresa), // Aseguramos que sea número
                ano: year,
                mes: month,
                usuario_id: user.id
            });
            setMessage(response.data.message);
            await fetchPeriodos();
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al cerrar el período.');
        } finally {
            setIsProcessing(false);
        }
    };

    const handleReabrirPeriodo = async (ano, mes) => {
        // ... (confirmación se mantiene)
        if (!window.confirm(`¿Estás seguro de que deseas reabrir el período ${mes}/${ano}?`)) {
            return;
        }
        setIsProcessing(true);
        setError(null);
        setMessage('');
        try {
            // En axios (base de apiService), el body de DELETE va en la propiedad 'data'
            const response = await apiService.delete('/periodos', {
                data: {
                    empresa_id: parseInt(selectedEmpresa),
                    ano: ano,
                    mes: mes,
                }
            });
            setMessage(response.data.message);
            await fetchPeriodos();
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al reabrir el período.');
        } finally {
            setIsProcessing(false);
        }
    };

    const monthNames = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"];
    
    // El JSX se mantiene casi idéntico, solo ajustamos el selector de empresa

    if (authLoading) {
    return <div className="container mx-auto p-8"><p className="text-center">Cargando autenticación...</p></div>;
}
    return (
        <div className="container mx-auto p-8">
            <div className="flex justify-between items-center mb-8">
                <h1 className="text-3xl font-bold text-gray-800">Gestión de Períodos Contables</h1>
                <Link href="/" className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600">&larr; Regresar al Inicio</Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="bg-white p-6 rounded-lg shadow-md">
                    <h2 className="text-xl font-semibold mb-4 border-b pb-2">1. Cerrar un Nuevo Período</h2>
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Empresa</label>
                            <select 
                                value={selectedEmpresa} 
                                onChange={(e) => setSelectedEmpresa(e.target.value)} 
                                className="mt-1 block w-full py-2 px-3 border border-gray-300 rounded-md"
                                // El superadmin es el único que puede cambiar de empresa en esta vista
                                disabled={user?.rol !== 'superadmin' || empresas.length === 0}>
                                <option value="">{user?.rol === 'superadmin' ? 'Seleccione una empresa...' : 'Cargando...'}</option>
                                {empresas.map(e => <option key={e.id} value={e.id}>{e.razon_social}</option>)}
                            </select>
                        </div>
                        <div className="flex gap-4">
                            <div className="w-1/2">
                                <label className="block text-sm font-medium text-gray-700">Año</label>
                                <input type="number" value={year} onChange={e => setYear(e.target.value)} className="mt-1 block w-full py-2 px-3 border border-gray-300 rounded-md" />
                            </div>
                            <div className="w-1/2">
                                <label className="block text-sm font-medium text-gray-700">Mes</label>
                                <select value={month} onChange={e => setMonth(e.target.value)} className="mt-1 block w-full py-2 px-3 border border-gray-300 rounded-md">
                                    {monthNames.map((name, index) => (
                                        <option key={index + 1} value={index + 1}>{name}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                        <div className="pt-2">
                            <button onClick={handleCerrarPeriodo} disabled={isProcessing || !selectedEmpresa} className="w-full bg-blue-700 hover:bg-blue-900 text-white font-bold py-2 px-6 rounded-lg shadow-md disabled:bg-gray-400">
                                {isProcessing ? 'Procesando...' : `Cerrar Período ${monthNames[month-1]} ${year}`}
                            </button>
                        </div>
                        {error && <p className="text-red-600 text-center mt-4">{error}</p>}
                        {message && <p className="text-green-600 text-center mt-4">{message}</p>}
                    </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow-md">
                    <h2 className="text-xl font-semibold mb-4 border-b pb-2">2. Períodos Ya Cerrados</h2>
                    {isLoading ? <p>Cargando...</p> : 
                    periodosCerrados.length > 0 ? (
                        <ul className="space-y-2 max-h-80 overflow-y-auto">
                            {periodosCerrados.map(p => (
                                <li key={`${p.ano}-${p.mes}`} className="flex justify-between items-center bg-gray-100 p-3 rounded-md">
                                    <span className="font-medium">{monthNames[p.mes - 1]} de {p.ano}</span>
                                    <button 
                                        onClick={() => handleReabrirPeriodo(p.ano, p.mes)}
                                        disabled={isProcessing}
                                        className="px-3 py-1 bg-red-600 text-white text-xs font-bold rounded-md hover:bg-red-800 disabled:bg-gray-400"
                                        title="Reabrir este período"
                                    >
                                        Reabrir 🔓
                                    </button>
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <p className="text-gray-500 text-center pt-8">No hay períodos cerrados para la empresa seleccionada.</p>
                    )}
                </div>
            </div>
        </div>
    );
}