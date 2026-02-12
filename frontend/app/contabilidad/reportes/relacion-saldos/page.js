'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import {
    FaBalanceScale,
    FaSearch,
    FaFileCsv,
    FaFilePdf,
    FaFilter,
    FaCalendarAlt,
    FaUserTag,
    FaBook,
    FaExclamationTriangle
} from 'react-icons/fa';
import { toast } from 'react-toastify';
import { useAuth } from '../../../context/AuthContext';
import { apiService } from '../../../../lib/apiService';

// --- ESTILOS REUSABLES ---
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none pl-10";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white pl-10 text-gray-900";
const multiSelectClass = "w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white h-32";

const CheckboxMultiSelect = ({ options, selected, onChange, placeholder = "Seleccionar..." }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [searchTerm, setSearchTerm] = useState("");
    const dropdownRef = useRef(null);

    // Cerrar al hacer clic fuera
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const filteredOptions = options.filter(opt =>
        (opt.label || opt.nombre || opt.razon_social || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
        (opt.codigo || "").toLowerCase().includes(searchTerm.toLowerCase())
    );

    const isAllSelected = selected.includes('all');

    // Calcular texto a mostrar
    let displayLabel = placeholder;
    if (isAllSelected) {
        displayLabel = "Todos Seleccionados";
    } else if (selected.length > 0) {
        displayLabel = `${selected.length} Seleccionado(s)`;
    }

    const toggleOption = (value) => {
        if (value === 'all') {
            // Toggle 'Select All'
            onChange(isAllSelected ? [] : ['all']);
        } else {
            let newSelected = [...selected];

            if (isAllSelected) {
                // If 'all' was selected, switch to manual mode starting with ONLY this item clicked
                // This is intuitive: "I was selecting everything, but now I specifically want THIS one"
                newSelected = [value];
            } else {
                // Manual toggle
                if (newSelected.includes(value)) {
                    newSelected = newSelected.filter(id => id !== value);
                } else {
                    newSelected.push(value);
                }
            }
            onChange(newSelected);
        }
    };

    return (
        <div className="relative" ref={dropdownRef}>
            <div
                className="w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm bg-white text-sm cursor-pointer flex justify-between items-center"
                onClick={() => setIsOpen(!isOpen)}
            >
                <div className="flex flex-col items-start overflow-hidden">
                    <span className={`truncate font-bold ${selected.length === 0 ? 'text-gray-400' : 'text-indigo-700'}`}>
                        {displayLabel}
                    </span>
                    {isAllSelected && <span className="text-xs text-gray-500 font-normal">Se incluirán todos los registros</span>}
                </div>
                <span className="text-gray-400">▼</span>
            </div>

            {isOpen && (
                <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-xl max-h-60 flex flex-col">
                    <div className="p-2 border-b border-gray-100">
                        <input
                            type="text"
                            className="w-full px-2 py-1 border border-gray-200 rounded text-xs focus:outline-none focus:border-indigo-500"
                            placeholder="Buscar..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            autoFocus
                        />
                    </div>
                    <div className="overflow-y-auto flex-1 p-2 space-y-1">
                        <label className="flex items-center gap-2 px-2 py-1.5 hover:bg-indigo-50 rounded cursor-pointer border-b border-gray-100 mb-1">
                            <input
                                type="checkbox"
                                className="rounded text-indigo-600 focus:ring-indigo-500 transform scale-110"
                                checked={isAllSelected}
                                onChange={() => toggleOption('all')}
                            />
                            <span className="text-sm font-bold text-gray-800">-- TODOS --</span>
                        </label>
                        {filteredOptions.map(option => {
                            const isSelected = selected.includes(option.id);
                            // VISUALMENTE: Si está en 'all', mostramos los individuales vacíos para indicar que 
                            // al clicarlos pasará a selección manual específica (UX Patrón común)
                            return (
                                <label key={option.id} className={`flex items-center gap-2 px-2 py-1.5 rounded cursor-pointer transition-colors ${isSelected ? 'bg-indigo-50' : 'hover:bg-gray-50'}`}>
                                    <input
                                        type="checkbox"
                                        className="rounded text-indigo-600 focus:ring-indigo-500"
                                        checked={isSelected}
                                        onChange={() => toggleOption(option.id)}
                                    // YA NO ESTÁ DISABLED
                                    />
                                    <div className="flex flex-col overflow-hidden">
                                        <span className="text-sm text-gray-700 font-medium truncate">
                                            {option.codigo ? `${option.codigo} - ` : ''}{option.label || option.nombre || option.razon_social}
                                        </span>
                                        {option.nit && <span className="text-xs text-gray-400">NIT: {option.nit}</span>}
                                    </div>
                                </label>
                            );
                        })}
                        {filteredOptions.length === 0 && (
                            <div className="text-center text-xs text-gray-400 py-2">No hay resultados</div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

import { useSearchParams } from 'next/navigation';

export default function RelacionSaldosPage() {
    const { user, loading: authLoading } = useAuth();
    const router = useRouter();
    const searchParams = useSearchParams();

    // Estados de Filtros
    const [cuentas, setCuentas] = useState([]);
    const [terceros, setTerceros] = useState([]);

    const [selectedCuentas, setSelectedCuentas] = useState(['all']);
    const [selectedTerceros, setSelectedTerceros] = useState(['all']);

    const [fechas, setFechas] = useState({
        inicio: searchParams.get('fecha_inicio') || new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0],
        fin: searchParams.get('fecha_fin') || new Date().toISOString().split('T')[0]
    });

    // Estados de UI
    const [reportData, setReportData] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [isPageReady, setPageReady] = useState(false);

    // --- AUTENTICACIÓN Y CARGA INICIAL ---
    useEffect(() => {
        if (!authLoading) {
            if (user && user.empresaId) {
                setPageReady(true);
                fetchMaestros();
            } else {
                router.push('/login');
            }
        }
    }, [user, authLoading, router]);

    const fetchMaestros = async () => {
        try {
            const [resCuentas, resTerceros] = await Promise.all([
                apiService.get('/plan-cuentas/list-flat?permite_movimiento=true'),
                apiService.get('/terceros')
            ]);
            setCuentas(resCuentas.data);
            setTerceros(resTerceros.data);

            // LOGICA AI: Resolver nombres/códigos desde la URL a IDs
            const urlCuenta = searchParams.get('cuenta');
            const urlTercero = searchParams.get('tercero');

            if (urlCuenta || urlTercero) {
                let resolveCuentas = ['all'];
                let resolveTerceros = ['all'];

                if (urlCuenta) {
                    const term = urlCuenta.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
                    const matched = resCuentas.data.find(c =>
                        c.codigo === urlCuenta ||
                        c.nombre.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").includes(term)
                    );
                    if (matched) resolveCuentas = [matched.id];
                }

                if (urlTercero) {
                    const term = urlTercero.toLowerCase().trim().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
                    const terms = term.split(' ').filter(t => t.length > 2);

                    const matched = resTerceros.data.find(t => {
                        const nitVal = (t.nit || '').toLowerCase();
                        const razon = (t.razon_social || '').toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
                        const comercial = (t.nombre_comercial || '').toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
                        const fullText = `${nitVal} ${razon} ${comercial}`;

                        if (nitVal === term) return true;
                        if (terms.length > 0 && terms.every(word => fullText.includes(word))) return true;
                        const matchesCount = terms.filter(word => fullText.includes(word)).length;
                        return matchesCount >= 2;
                    });
                    if (matched) resolveTerceros = [matched.id];
                }

                setSelectedCuentas(resolveCuentas);
                setSelectedTerceros(resolveTerceros);

                // DISPARAR EJECUCIÓN INMEDIATA CON FILTROS REALES
                const isAuto = searchParams.get('trigger') === 'ai';
                const isAutoPdf = searchParams.get('auto_pdf') === 'true';

                if (isAuto || urlCuenta || urlTercero) {
                    setTimeout(() => {
                        handleGenerateReport(resolveCuentas, resolveTerceros).then(success => {
                            if (success && isAutoPdf) {
                                handleExportPDF(resolveCuentas, resolveTerceros);
                            }
                        });
                    }, 300);
                }
            }

        } catch (err) {
            console.error(err);
            setError("Error cargando maestros.");
        }
    };

    // Ya no necesitamos este efecto duplicado, la lógica está en fetchMaestros

    // --- GENERACIÓN DE REPORTE ---
    const handleGenerateReport = async (overrideCuentas = null, overrideTerceros = null) => {
        // Corrección de Evento: Si el primer argumento es un evento de React, ignoramos overrides
        const actualCuentas = (Array.isArray(overrideCuentas)) ? overrideCuentas : selectedCuentas;
        const actualTerceros = (Array.isArray(overrideTerceros)) ? overrideTerceros : selectedTerceros;

        if (!fechas.inicio || !fechas.fin) {
            setError("Por favor seleccione un rango de fechas.");
            return false;
        }

        setIsLoading(true);
        setError(null);
        setReportData(null);

        const params = {
            fecha_inicio: fechas.inicio,
            fecha_fin: fechas.fin,
        };

        if (actualCuentas.length > 0 && !actualCuentas.includes('all')) {
            params.cuenta_ids = actualCuentas.join(',');
        }
        if (actualTerceros.length > 0 && !actualTerceros.includes('all')) {
            params.tercero_ids = actualTerceros.join(',');
        }

        try {
            const res = await apiService.get('/reports/relacion-saldos', { params });
            setReportData(res.data);
            return true;
        } catch (err) {
            setError(err.response?.data?.detail || "Error generando el reporte.");
            return false;
        } finally {
            setIsLoading(false);
        }
    };

    // --- EXPORTACIÓN ---
    const handleExportPDF = async (overrideCuentas = null, overrideTerceros = null) => {
        setIsLoading(true);
        setError(null);
        try {
            const actualCuentas = (Array.isArray(overrideCuentas)) ? overrideCuentas : selectedCuentas;
            const actualTerceros = (Array.isArray(overrideTerceros)) ? overrideTerceros : selectedTerceros;

            const params = {
                fecha_inicio: fechas.inicio,
                fecha_fin: fechas.fin,
            };

            if (actualCuentas.length > 0 && !actualCuentas.includes('all')) {
                params.cuenta_ids = actualCuentas.join(',');
            }
            if (actualTerceros.length > 0 && !actualTerceros.includes('all')) {
                params.tercero_ids = actualTerceros.join(',');
            }

            const res = await apiService.get('/reports/relacion-saldos/get-signed-url', { params });
            const token = res.data.signed_url_token;
            const pdfUrl = `${process.env.NEXT_PUBLIC_API_URL}/api/reports/relacion-saldos/imprimir?signed_token=${token}`;

            // Trigger download/view
            window.open(pdfUrl, '_blank');

        } catch (err) {
            console.error(err);
            setError(err.response?.data?.detail || "Error al generar el PDF.");
        } finally {
            setIsLoading(false);
        }
    };

    const handleExportCSV = () => {
        if (!reportData || reportData.length === 0) return;

        // Headers
        const headers = ["Cuenta Código", "Cuenta Nombre", "NIT Tercero", "Nombre Tercero", "Saldo Anterior", "Débito", "Crédito", "Saldo Final"];

        // Rows
        const rows = reportData.map(row => [
            `"${row.cuenta_codigo}"`,
            `"${row.cuenta_nombre}"`,
            `"${row.tercero_nit}"`,
            `"${row.tercero_nombre}"`,
            row.saldo_anterior,
            row.debito,
            row.credito,
            row.saldo_final
        ]);

        // Combine
        const csvContent = [
            headers.join(','),
            ...rows.map(r => r.join(','))
        ].join('\n');

        // Download
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.setAttribute("href", url);
        link.setAttribute("download", `Relacion_Saldos_${fechas.inicio}_${fechas.fin}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const formatCurrency = (val) => {
        return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 2 }).format(val || 0);
    };

    if (!isPageReady) return null;

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
            <div className="max-w-7xl mx-auto">

                {/* HEADER */}
                <div className="flex items-center gap-3 mb-8">
                    <div className="p-3 bg-indigo-100 rounded-xl text-indigo-600">
                        <FaBalanceScale className="text-2xl" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold text-gray-800">Relación de Saldos</h1>
                        <p className="text-gray-500 text-sm">Informe de saldos netos por Cuenta y Tercero.</p>
                    </div>
                </div>

                {/* FILTROS */}
                <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 animate-fadeIn mb-8">
                    <div className="flex items-center gap-2 mb-4 border-b pb-2">
                        <FaFilter className="text-indigo-500" />
                        <h2 className="text-lg font-bold text-gray-700">Filtros</h2>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                        {/* Fechas */}
                        <div>
                            <label className={labelClass}>Desde</label>
                            <div className="relative">
                                <input type="date" value={fechas.inicio} onChange={(e) => setFechas({ ...fechas, inicio: e.target.value })} className={inputClass} />
                                <FaCalendarAlt className="absolute left-3 top-3 text-gray-400" />
                            </div>
                        </div>
                        <div>
                            <label className={labelClass}>Hasta</label>
                            <div className="relative">
                                <input type="date" value={fechas.fin} onChange={(e) => setFechas({ ...fechas, fin: e.target.value })} className={inputClass} />
                                <FaCalendarAlt className="absolute left-3 top-3 text-gray-400" />
                            </div>
                        </div>

                        {/* MultiSelects con Checkboxes (Nueva UI) */}
                        <div className="md:col-span-2 row-span-2 grid grid-cols-2 gap-4">
                            <div>
                                <label className={labelClass}>Cuentas</label>
                                <CheckboxMultiSelect
                                    options={cuentas}
                                    selected={selectedCuentas}
                                    onChange={setSelectedCuentas}
                                    placeholder="Seleccionar Cuentas..."
                                />
                                <p className="text-xs text-gray-400 mt-1">Marque 'Todos' o seleccione individualmente.</p>
                            </div>
                            <div>
                                <label className={labelClass}>Terceros</label>
                                <CheckboxMultiSelect
                                    options={terceros.map(t => ({ id: t.id, label: t.razon_social, nit: t.numero_identificacion }))}
                                    selected={selectedTerceros}
                                    onChange={setSelectedTerceros}
                                    placeholder="Seleccionar Terceros..."
                                />
                                <p className="text-xs text-gray-400 mt-1">Busque por nombre o NIT.</p>
                            </div>
                        </div>
                    </div>

                    <div className="flex justify-end mt-4">
                        <button
                            onClick={handleGenerateReport}
                            disabled={isLoading}
                            className="btn btn-primary bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-8 shadow-md"
                        >
                            {isLoading ? <span className="loading loading-spinner"></span> : <><FaSearch className="mr-2" /> Consultar Saldos</>}
                        </button>
                    </div>
                </div>

                {/* ERROR */}
                {error && (
                    <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded-r-lg flex items-center gap-3">
                        <FaExclamationTriangle className="text-xl" />
                        <p>{error}</p>
                    </div>
                )}

                {/* RESULTADOS */}
                {reportData && (
                    <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden animate-slideDown">
                        <div className="p-4 bg-gray-50 border-b flex justify-between items-center">
                            <h2 className="font-bold text-gray-700">Resultados</h2>
                            <div className="flex gap-2">
                                <button onClick={handleExportCSV} className="btn btn-sm btn-ghost text-green-600"><FaFileCsv className="mr-1" /> CSV</button>
                                <button onClick={handleExportPDF} className="btn btn-sm btn-ghost text-red-600"><FaFilePdf className="mr-1" /> PDF</button>
                            </div>
                        </div>

                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-slate-100">
                                    <tr>
                                        <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase">Cuenta</th>
                                        <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase">Tercero</th>
                                        <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase">Saldo Anterior</th>
                                        <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase">Débito</th>
                                        <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase">Crédito</th>
                                        <th className="px-4 py-3 text-right text-xs font-bold text-gray-600 uppercase">Saldo Final</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-100">
                                    {reportData.map((row, idx) => (
                                        <tr key={idx} className="hover:bg-gray-50">
                                            <td className="px-4 py-2 text-sm text-gray-800 font-medium">{row.cuenta_codigo}</td>
                                            <td className="px-4 py-2 text-sm text-gray-600 truncate max-w-xs">{row.tercero_nombre}</td>
                                            <td className="px-4 py-2 text-right text-sm text-gray-600 font-mono">{formatCurrency(row.saldo_anterior)}</td>
                                            <td className="px-4 py-2 text-right text-sm text-gray-600 font-mono">{formatCurrency(row.debito)}</td>
                                            <td className="px-4 py-2 text-right text-sm text-gray-600 font-mono">{formatCurrency(row.credito)}</td>
                                            <td className={`px-4 py-2 text-right text-sm font-mono font-bold ${row.saldo_final < 0 ? 'text-red-600' : 'text-gray-800'}`}>
                                                {formatCurrency(row.saldo_final)}
                                            </td>
                                        </tr>
                                    ))}
                                    {reportData.length === 0 && (
                                        <tr>
                                            <td colSpan="6" className="text-center py-8 text-gray-400 font-medium">No se encontraron saldos para los filtros seleccionados.</td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}