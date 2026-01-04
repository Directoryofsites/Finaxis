
'use client';

import React, { useState } from 'react';
import {
    FaFileUpload,
    FaSave,
    FaCalendarAlt,
    FaBuilding,
    FaUserFriends,
    FaPlayCircle,
    FaSpinner,
    FaCheck
} from 'react-icons/fa';
import { importarLegacy } from '../../../lib/utilidadesService';

// Styles
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white pl-10";
const inputClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none bg-white pl-10";
const fileInputClass = "w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-bold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 cursor-pointer border border-gray-300 rounded-lg shadow-sm";

export default function LegacyImportForm({
    maestros,
    empresaActual,
    isProcessing,
    setIsProcessing,
    setMessage,
    setError
}) {
    const [targetEmpresaId, setTargetEmpresaId] = useState('');
    const [defaultTerceroId, setDefaultTerceroId] = useState('');
    const [periodoFecha, setPeriodoFecha] = useState('');

    const [fileComa, setFileComa] = useState(null);
    const [fileConi, setFileConi] = useState(null);
    const [fileCotr, setFileCotr] = useState(null);
    const [fileTxt, setFileTxt] = useState(null); // Nuevo soporte TXT

    const handleImport = async () => {
        if (!targetEmpresaId || !periodoFecha) {
            alert("Por favor complete todos los campos obligatorios (Empresa, Fecha).");
            return;
        }

        if (!fileComa && !fileConi && !fileCotr && !fileTxt) {
            alert("Seleccione al menos un archivo para importar (Reporte TXT o Archivos Legacy).");
            return;
        }

        if (!window.confirm("¿Está seguro de iniciar la importación? Esto creará registros en la empresa seleccionada.")) {
            return;
        }

        setIsProcessing(true);
        setMessage("Importando datos del sistema DOS... Esto puede tardar unos minutos.");
        setError(null);

        try {
            const formData = new FormData();
            formData.append('empresa_id', targetEmpresaId);
            formData.append('periodo_fecha', periodoFecha);
            if (defaultTerceroId) {
                formData.append('default_tercero_id', defaultTerceroId);
            }

            if (fileComa) formData.append('file_coma', fileComa);
            if (fileConi) formData.append('file_coni', fileConi);
            if (fileCotr) formData.append('file_cotr', fileCotr);
            if (fileTxt) formData.append('file_txt', fileTxt);

            const { data } = await importarLegacy(formData);

            setMessage(`¡Importación Completa! Cuentas: ${data.accounts}, Terceros: ${data.third_parties}, Documentos: ${data.transactions}`);

            // Reset files
            setFileComa(null);
            setFileConi(null);
            setFileCotr(null);
            setFileTxt(null);

        } catch (err) {
            const msg = err.response?.data?.detail || err.message;
            setError(`Error en importación: ${msg}`);
            setMessage('');
        } finally {
            setIsProcessing(false);
        }
    };

    return (
        <div className="bg-white p-8 rounded-xl shadow-lg border border-gray-100 mt-8 animate-fadeIn">

            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-gray-100">
                <div className="p-3 bg-indigo-100 rounded-full text-indigo-600">
                    <FaSave className="text-xl" />
                </div>
                <div>
                    <h2 className="text-xl font-bold text-gray-800">Importador Legacy (DOS)</h2>
                    <p className="text-gray-500 text-sm">Importar desde Reporte Unificado (TXT) o Archivos Separados (.XXX)</p>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                {/* Empresa */}
                <div>
                    <label className={labelClass}>Empresa Destino</label>
                    <div className="relative">
                        <select
                            value={targetEmpresaId}
                            onChange={e => setTargetEmpresaId(e.target.value)}
                            disabled={isProcessing}
                            className={selectClass}
                        >
                            <option value="">-- Seleccionar --</option>
                            {maestros.empresas.map(e => <option key={e.id} value={e.id}>{e.razon_social}</option>)}
                        </select>
                        <FaBuilding className="absolute left-3 top-3 text-gray-400" />
                    </div>
                </div>

                {/* Fecha Periodo */}
                <div>
                    <label className={labelClass}>Fecha de Corte / Periodo</label>
                    <div className="relative">
                        <input
                            type="date"
                            value={periodoFecha}
                            onChange={e => setPeriodoFecha(e.target.value)}
                            disabled={isProcessing}
                            className={inputClass}
                        />
                        <FaCalendarAlt className="absolute left-3 top-3 text-gray-400" />
                    </div>
                </div>

                {/* Tercero Defecto (Opcional/Oculto si no se usa) */}
                <div className="hidden">
                    <label className={labelClass}>Tercero por Defecto (Opcional)</label>
                    <div className="relative">
                        <select
                            value={defaultTerceroId}
                            onChange={e => setDefaultTerceroId(e.target.value)}
                            disabled={isProcessing}
                            className={selectClass}
                        >
                            <option value="">-- Seleccionar --</option>
                            {maestros.terceros.map(t => <option key={t.id} value={t.id}>{t.razon_social} ({t.nit})</option>)}
                        </select>
                        <FaUserFriends className="absolute left-3 top-3 text-gray-400" />
                    </div>
                </div>
            </div>

            <h3 className="font-bold text-gray-700 mb-3 text-sm border-b pb-1">Método A: Reporte Unificado (Recomendado)</h3>
            <div className="mb-6 grid grid-cols-1 md:grid-cols-1 gap-6">
                <div>
                    <label className={labelClass}>REPORTE TXT (Ej: AA99.TXT)</label>
                    <input type="file" accept=".txt" onChange={e => setFileTxt(e.target.files[0])} className={fileInputClass} disabled={isProcessing} />
                    <p className="text-xs text-gray-400 mt-1">Importa Cuentas, Terceros y Documentos desde un solo reporte columnar.</p>
                </div>
            </div>

            <h3 className="font-bold text-gray-700 mb-3 text-sm border-b pb-1">Método B: Archivos Separados (Antiguo)</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                <div>
                    <label className={labelClass}>1. CONI (Terceros)</label>
                    <input type="file" accept="*" onChange={e => setFileConi(e.target.files[0])} className={fileInputClass} disabled={isProcessing} />
                </div>
                <div>
                    <label className={labelClass}>2. COMA (Cuentas)</label>
                    <input type="file" accept="*" onChange={e => setFileComa(e.target.files[0])} className={fileInputClass} disabled={isProcessing} />
                </div>
                <div>
                    <label className={labelClass}>3. COTR (Transacciones)</label>
                    <input type="file" accept="*" onChange={e => setFileCotr(e.target.files[0])} className={fileInputClass} disabled={isProcessing} />
                </div>
            </div>

            <div className="flex justify-end pt-4 border-t border-gray-100">
                <button
                    onClick={handleImport}
                    disabled={isProcessing}
                    className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg shadow-md font-bold transition-all flex items-center gap-2 disabled:bg-gray-400"
                >
                    {isProcessing ? <><FaSpinner className="animate-spin" /> Procesando...</> : <><FaPlayCircle /> Iniciar Importación</>}
                </button>
            </div>

        </div>
    );
}
