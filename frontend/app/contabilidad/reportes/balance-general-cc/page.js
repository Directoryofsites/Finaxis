'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  FaBalanceScale, 
  FaCalendarAlt, 
  FaSearch, 
  FaFilePdf, 
  FaBuilding, 
  FaMoneyBillWave, 
  FaLandmark, 
  FaChartPie,
  FaExclamationTriangle,
  FaCheckCircle,
  FaLayerGroup
} from 'react-icons/fa';

import { 
FaBook,
} from 'react-icons/fa';

import BotonRegresar from '../../../components/BotonRegresar';
import { useAuth } from '../../../context/AuthContext';
import { apiService } from '../../../../lib/apiService';

// Estilos Reusables (Manual v2.0)
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none pl-10";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white pl-10";

export default function BalanceGeneralCCPage() {
    const { user, authLoading } = useAuth();
    const router = useRouter();

    const [reporte, setReporte] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [fechaCorte, setFechaCorte] = useState('');
    const [centrosCosto, setCentrosCosto] = useState([]);
    const [centroCostoId, setCentroCostoId] = useState('');
    const [isPageReady, setPageReady] = useState(false);

    // Efecto de Autenticación y Carga de Maestros
    useEffect(() => {
        if (!authLoading) {
            if (user && user.empresaId) {
                const fetchCentrosCosto = async () => {
                    try {
                        const res = await apiService.get('/centros-costo/get-flat');
                        // Aplicamos el filtro de seguridad para mostrar solo los que permiten movimiento (o todos si se desea consolidar)
                        // Usualmente en reportes se quiere ver todo, pero para filtrar mejor usamos la lógica de 'permite_movimiento' si aplica
                        // En este caso, dejaremos que el usuario elija cualquiera, pero es mejor si el backend soporta consolidación.
                        setCentrosCosto(res.data); 
                        setPageReady(true);
                    } catch (err) {
                        setError("No se pudieron cargar los centros de costo: " + (err.response?.data?.detail || err.message));
                        setPageReady(true);
                    }
                };
                fetchCentrosCosto();
            } else {
                router.push('/login');
            }
        }
    }, [user, authLoading, router]);

    const handleGenerateReport = async () => {
        if (!fechaCorte) {
            setError("Por favor, seleccione una fecha de corte.");
            return;
        }
        setIsLoading(true);
        setError('');
        setReporte(null);
        try {
            const params = {
                fecha_corte: fechaCorte,
                centro_costo_id: centroCostoId || null
            };
            const res = await apiService.get('/reports/balance-sheet-cc', { params });
            setReporte(res.data);
        } catch (err) {
            setError(err.response?.data?.detail || "Error al generar el reporte.");
        } finally {
            setIsLoading(false);
        }
    };

    const handleExportPDF = async () => {
        if (!reporte) {
            setError("Primero debe generar un reporte para poder exportarlo.");
            return;
        }
        setIsLoading(true);
        setError('');
        try {
            const params = {
                fecha_corte: fechaCorte,
                centro_costo_id: centroCostoId || null
            };
            const res = await apiService.get('/reports/balance-sheet-cc/get-signed-url', { params });
            const signedToken = res.data.signed_url_token;
            
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const pdfDownloadUrl = `${baseUrl}/api/reports/balance-sheet-cc/imprimir?signed_token=${signedToken}`;
            
            const link = document.createElement('a');
            link.href = pdfDownloadUrl;
            link.setAttribute('download', `Balance_CC_${fechaCorte}.pdf`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (err) {
            setError(err.response?.data?.detail || "Error al generar el PDF del reporte.");
        } finally {
            setIsLoading(false);
        }
    };

    const formatCurrency = (value) => {
        const num = parseFloat(value);
        if (isNaN(num)) return '$ 0.00';
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }).format(num);
    };

    const getSelectedCcName = () => {
        if (!centroCostoId) return 'Todos (Consolidado)';
        const seleccionado = centrosCosto.find(cc => cc.id == centroCostoId);
        return seleccionado ? `${seleccionado.codigo} - ${seleccionado.nombre}` : 'Todos (Consolidado)';
    };

    if (!isPageReady) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
                <FaBalanceScale className="text-indigo-300 text-6xl mb-4 animate-pulse" />
                <p className="text-indigo-600 font-semibold text-lg animate-pulse">Cargando Balance por Centro de Costo...</p>
            </div>
        );
    }

    // Componente de Fila de Cuenta
    const AccountRow = ({ codigo, nombre, saldo, colorClass = "text-gray-700" }) => (
        <div className="flex justify-between items-center py-2 border-b border-gray-50 hover:bg-gray-50 transition-colors px-2 rounded">
            <div className="flex flex-col md:flex-row md:items-center gap-1 md:gap-3">
                <span className={`font-mono text-xs font-bold px-2 py-0.5 rounded-md bg-gray-100 ${colorClass}`}>{codigo}</span>
                <span className="text-sm text-gray-700 font-medium">{nombre}</span>
            </div>
            <span className={`font-mono text-sm font-bold ${colorClass}`}>
                {formatCurrency(saldo)}
            </span>
        </div>
    );

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
            <div className="max-w-5xl mx-auto">
                
                {/* ENCABEZADO */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                    <div>


                       <div className="flex items-center gap-3 mb-3">
                            
                            {/* 1. Botón Regresar (Izquierda) */}
                            <BotonRegresar />

                            {/* 2. Botón Manual (Derecha) */}
                            <button
                                onClick={() => window.open('/manual/capitulo_52_balance_general_cc.html', '_blank')}
                                className="text-indigo-600 hover:bg-indigo-50 px-3 py-1 rounded-md flex items-center gap-2 transition-colors font-bold text-sm"
                                type="button"
                            >
                                <FaBook className="text-lg" /> Manual
                            </button>

                        </div>


                        <div className="flex items-center gap-3 mt-3">
                            <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                                <FaBuilding className="text-2xl" />
                            </div>
                            <div>
                                <h1 className="text-3xl font-bold text-gray-800">Balance por Centro de Costo</h1>
                                <p className="text-gray-500 text-sm">Análisis financiero segmentado por unidad de negocio.</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* CARD 1: FILTROS */}
                <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 animate-fadeIn mb-8">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-end">
                        {/* Selector Centro Costo */}
                        <div className="md:col-span-1">
                            <label htmlFor="centroCosto" className={labelClass}>Centro de Costo</label>
                            <div className="relative">
                                <select 
                                    id="centroCosto" 
                                    value={centroCostoId} 
                                    onChange={(e) => setCentroCostoId(e.target.value)} 
                                    className={selectClass}
                                >
                                    <option value="">-- Todos (Consolidado) --</option>
                                    {centrosCosto.map(cc => (
                                        <option key={cc.id} value={cc.id}>
                                            {cc.codigo} - {cc.nombre}
                                        </option>
                                    ))}
                                </select>
                                <FaLayerGroup className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                            </div>
                        </div>

                        {/* Fecha Corte */}
                        <div className="md:col-span-1">
                            <label htmlFor="fechaCorte" className={labelClass}>Fecha de Corte</label>
                            <div className="relative">
                                <input 
                                    type="date" 
                                    id="fechaCorte" 
                                    value={fechaCorte} 
                                    onChange={(e) => setFechaCorte(e.target.value)} 
                                    className={inputClass} 
                                />
                                <FaCalendarAlt className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
                            </div>
                        </div>
                        
                        {/* Botones */}
                        <div className="md:col-span-1 flex flex-col md:flex-row justify-end gap-3">
                            <button 
                                onClick={handleGenerateReport} 
                                disabled={isLoading} 
                                className={`
                                    w-full px-6 py-2 rounded-lg shadow-md font-bold text-white transition-all transform hover:-translate-y-0.5 flex items-center justify-center gap-2
                                    ${isLoading ? 'bg-gray-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'}
                                `}
                            >
                                {isLoading ? <span className="loading loading-spinner loading-sm"></span> : <><FaSearch /> Generar</>}
                            </button>
                            
                            <button 
                                onClick={handleExportPDF} 
                                disabled={!reporte || isLoading} 
                                className={`
                                    w-full md:w-auto px-4 py-2 rounded-lg shadow-md font-bold border transition-all transform hover:-translate-y-0.5 flex items-center justify-center gap-2
                                    ${!reporte || isLoading 
                                        ? 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed' 
                                        : 'bg-white text-red-600 border-red-100 hover:bg-red-50'}
                                `}
                            >
                                <FaFilePdf /> PDF
                            </button>
                        </div>
                    </div>
                    
                    {error && (
                        <div className="mt-4 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded-r-lg flex items-center gap-3 animate-pulse">
                            <FaExclamationTriangle className="text-xl" />
                            <p className="font-bold">{error}</p>
                        </div>
                    )}
                </div>

                {/* CARD 2: REPORTE */}
                {reporte && (
                    <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden animate-slideDown">
                        {/* Cabecera Reporte */}
                        <div className="bg-slate-50 p-6 border-b border-gray-200 text-center">
                            <h2 className="text-xl font-bold text-gray-800">{user?.nombre_empresa}</h2>
                            <p className="text-sm text-gray-500 font-medium mt-1">{getSelectedCcName()}</p>
                            <p className="text-indigo-600 font-bold mt-2 flex items-center justify-center gap-2">
                                <FaCalendarAlt /> Corte a: {new Date(fechaCorte).toLocaleDateString('es-CO', {timeZone: 'UTC', year: 'numeric', month: 'long', day: 'numeric'})}
                            </p>
                        </div>

                        <div className="p-6 space-y-8">
                            
                            {/* ACTIVOS */}
                            <section>
                                <div className="flex items-center gap-2 mb-4 pb-2 border-b-2 border-emerald-100">
                                    <div className="p-2 bg-emerald-100 text-emerald-600 rounded-lg"><FaMoneyBillWave /></div>
                                    <h3 className="text-xl font-bold text-gray-700">Activos</h3>
                                </div>
                                <div className="pl-2 md:pl-4 space-y-1">
                                    {reporte.activos.length === 0 ? <p className="text-gray-400 italic text-sm">Sin registros.</p> : 
                                        reporte.activos.map((item, index) => <AccountRow key={`act-${index}`} {...item} saldo={item.saldo} colorClass="text-emerald-700"/>)
                                    }
                                </div>
                                <div className="flex justify-between items-center mt-3 pt-3 border-t border-gray-200 bg-emerald-50/50 p-3 rounded-lg">
                                    <span className="font-bold text-gray-700 uppercase text-sm">Total Activos</span>
                                    <span className="font-mono text-lg font-bold text-emerald-700">{formatCurrency(reporte.total_activos)}</span>
                                </div>
                            </section>

                            {/* PASIVOS */}
                            <section>
                                <div className="flex items-center gap-2 mb-4 pb-2 border-b-2 border-rose-100">
                                    <div className="p-2 bg-rose-100 text-rose-600 rounded-lg"><FaBuilding /></div>
                                    <h3 className="text-xl font-bold text-gray-700">Pasivos</h3>
                                </div>
                                <div className="pl-2 md:pl-4 space-y-1">
                                    {reporte.pasivos.length === 0 ? <p className="text-gray-400 italic text-sm">Sin registros.</p> : 
                                        reporte.pasivos.map((item, index) => <AccountRow key={`pas-${index}`} {...item} saldo={item.saldo} colorClass="text-rose-700"/>)
                                    }
                                </div>
                                <div className="flex justify-between items-center mt-3 pt-3 border-t border-gray-200 bg-rose-50/50 p-3 rounded-lg">
                                    <span className="font-bold text-gray-700 uppercase text-sm">Total Pasivos</span>
                                    <span className="font-mono text-lg font-bold text-rose-700">{formatCurrency(reporte.total_pasivos)}</span>
                                </div>
                            </section>

                            {/* PATRIMONIO */}
                            <section>
                                <div className="flex items-center gap-2 mb-4 pb-2 border-b-2 border-blue-100">
                                    <div className="p-2 bg-blue-100 text-blue-600 rounded-lg"><FaLandmark /></div>
                                    <h3 className="text-xl font-bold text-gray-700">Patrimonio</h3>
                                </div>
                                <div className="pl-2 md:pl-4 space-y-1">
                                    {reporte.patrimonio.map((item, index) => <AccountRow key={`pat-${index}`} {...item} saldo={item.saldo} colorClass="text-blue-700"/>)}
                                    
                                    {/* Utilidad Ejercicio */}
                                    <div className="flex justify-between items-center py-2 px-2 bg-blue-50 rounded border border-blue-100 mt-2">
                                        <div className="flex gap-3 items-center">
                                            <span className="font-mono text-xs font-bold px-2 py-0.5 rounded-md bg-white text-blue-600 border border-blue-100">3605</span>
                                            <span className="text-sm text-blue-900 font-bold">Utilidad (Pérdida) del Ejercicio</span>
                                        </div>
                                        <span className={`font-mono text-sm font-bold ${reporte.utilidad_ejercicio >= 0 ? 'text-blue-700' : 'text-red-600'}`}>
                                            {formatCurrency(reporte.utilidad_ejercicio)}
                                        </span>
                                    </div>
                                </div>
                                <div className="flex justify-between items-center mt-3 pt-3 border-t border-gray-200 bg-blue-50/50 p-3 rounded-lg">
                                    <span className="font-bold text-gray-700 uppercase text-sm">Total Patrimonio</span>
                                    <span className="font-mono text-lg font-bold text-blue-700">{formatCurrency(reporte.total_patrimonio)}</span>
                                </div>
                            </section>

                            {/* ECUACIÓN PATRIMONIAL */}
                            <div className="mt-8 pt-6 border-t-4 border-gray-200">
                                <div className="flex flex-col md:flex-row justify-between items-center bg-slate-800 text-white p-6 rounded-xl shadow-lg">
                                    <div className="flex items-center gap-3 mb-4 md:mb-0">
                                        <FaChartPie className="text-3xl text-yellow-400" />
                                        <div>
                                            <p className="text-sm text-slate-300 uppercase tracking-wider font-bold">Ecuación Patrimonial</p>
                                            <p className="text-xs text-slate-400">Total Pasivo + Total Patrimonio</p>
                                        </div>
                                    </div>
                                    <div className="text-3xl font-mono font-bold text-yellow-400">
                                        {formatCurrency(reporte.total_pasivo_patrimonio)}
                                    </div>
                                </div>
                                
                                {/* Verificación Visual */}
                                {Math.abs(reporte.total_activos - reporte.total_pasivo_patrimonio) < 1 ? (
                                    <p className="text-center text-green-600 font-bold mt-3 flex justify-center items-center gap-2">
                                        <FaCheckCircle /> El balance está cuadrado.
                                    </p>
                                ) : (
                                    <p className="text-center text-red-500 font-bold mt-3 flex justify-center items-center gap-2 animate-pulse">
                                        <FaExclamationTriangle /> El balance presenta descuadres.
                                    </p>
                                )}
                            </div>

                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}