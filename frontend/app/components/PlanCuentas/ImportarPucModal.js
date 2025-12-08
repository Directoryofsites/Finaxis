import React, { useState, useMemo } from 'react';
import { FaFileUpload, FaSearch, FaCheckDouble, FaSpinner, FaExclamationTriangle } from 'react-icons/fa';
import * as planCuentasService from '@/lib/planCuentasService';

export default function ImportarPucModal({ isOpen, onClose, onImportComplete }) {
    const [step, setStep] = useState(1); // 1: Carga, 2: Selección
    const [fileData, setFileData] = useState(null);
    const [comprobando, setComprobando] = useState(false);
    const [analisis, setAnalisis] = useState(null); // { cuentas_analizadas: [] }
    const [importando, setImportando] = useState(false);

    // Estado de selección y Filtro
    const [seleccionados, setSeleccionados] = useState(new Set());
    const [filtro, setFiltro] = useState('');



    // --- LOGICA DE CARGA DE ARCHIVO ---
    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = async (e) => {
            try {
                const json = JSON.parse(e.target.result);
                let listaCuentas = [];

                // 1. Caso: Lista Directa ( [ {codigo...}, ... ] )
                if (Array.isArray(json)) {
                    listaCuentas = json;
                }
                // 2. Caso: Exportación del Sistema ( { data: { maestros: { plan_cuentas: [] } } } )
                else if (json.data?.maestros?.plan_cuentas && Array.isArray(json.data.maestros.plan_cuentas)) {
                    listaCuentas = json.data.maestros.plan_cuentas;
                }
                // 3. Caso: Exportación Parcial o sin firma ( { maestros: ... } )
                else if (json.maestros?.plan_cuentas && Array.isArray(json.maestros.plan_cuentas)) {
                    listaCuentas = json.maestros.plan_cuentas;
                }
                else {
                    throw new Error("El archivo no tiene un formato válido (No se encontró lista de cuentas ni estructura de respaldo).");
                }

                // Normalizar entrada (remover acentos de keys o mapear)
                const normalized = listaCuentas.map(c => ({
                    codigo: String(c.codigo || c.CODIGO || ''),
                    nombre: c.nombre || c.NOMBRE || '',
                    permite_movimiento: c.permite_movimiento || false
                })).filter(c => c.codigo); // Solo si tiene código

                if (normalized.length === 0) throw new Error("No se encontraron cuentas válidas en el archivo.");

                setFileData(normalized);
                await ejecutarAnalisis(normalized);

            } catch (err) {
                alert("Error al leer JSON: " + err.message);
            }
        };
        reader.readAsText(file);
    };

    const ejecutarAnalisis = async (data) => {
        setComprobando(true);
        try {
            const res = await planCuentasService.analizarImportacion(data);
            setAnalisis(res.data);

            // Pre-seleccionar SOLO las NUEVAS por defecto
            const nuevosIds = new Set();
            res.data.cuentas_analizadas.forEach(c => {
                if (c.es_nueva) nuevosIds.add(c.codigo);
            });
            setSeleccionados(nuevosIds);

            setStep(2);
        } catch (err) {
            console.error(err);
            alert("Error al analizar datos con el servidor.");
        } finally {
            setComprobando(false);
        }
    };

    // --- LOGICA DE SELECCION EN CASCADA ---
    const toggleSeleccion = (codigo) => {
        const newSet = new Set(seleccionados);
        const estabaMarcado = newSet.has(codigo);

        // Función auxiliar para buscar descendientes (Hacia abajo)
        const getDescendants = (parentCode) => {
            return analisis.cuentas_analizadas.filter(c =>
                c.es_nueva && c.codigo.startsWith(parentCode) && c.codigo !== parentCode
            );
        };

        // Función auxiliar para buscar ancestros (Hacia arriba)
        const getAncestors = (childCode) => {
            return analisis.cuentas_analizadas.filter(c =>
                c.es_nueva && childCode.startsWith(c.codigo) && c.codigo !== childCode
            );
        };

        if (estabaMarcado) {
            newSet.delete(codigo);
            // DESMARCAR en cascada descendente (Hijas)
            const descendants = getDescendants(codigo);
            descendants.forEach(d => newSet.delete(d.codigo));
        } else {
            newSet.add(codigo);
            // MARCAR en cascada descendente (Hijas)
            const descendants = getDescendants(codigo);
            descendants.forEach(d => newSet.add(d.codigo));

            // MARCAR en cascada ascendente (Padres/Ancestros)
            const ancestors = getAncestors(codigo);
            ancestors.forEach(a => newSet.add(a.codigo));
        }
        setSeleccionados(newSet);
    };

    const handleSelectAll = (seleccionar) => {
        if (!analisis) return;
        const newSet = new Set(seleccionados);
        cuentasVisibles.forEach(c => {
            if (c.es_nueva) {
                if (seleccionar) newSet.add(c.codigo);
                else newSet.delete(c.codigo);
            }
        });
        setSeleccionados(newSet);
    };

    // --- LOGICA DE FILTRADO ---
    const cuentasVisibles = useMemo(() => {
        if (!analisis) return [];
        let lista = analisis.cuentas_analizadas;
        if (filtro) {
            const f = filtro.toLowerCase();
            lista = lista.filter(c => c.codigo.includes(f) || c.nombre.toLowerCase().includes(f));
        }
        return lista;
    }, [analisis, filtro]);

    // --- EJECUTAR IMPORTACION ---
    const handleImportarDefinitivo = async () => {
        if (seleccionados.size === 0) return;
        setImportando(true);
        try {
            // Filtrar la lista original base usando los seleccionados
            // Pero ojo, necesitamos enviar el objeto completo que espera el backend
            // El AnalysisResponse tiene la info limpia
            const aEnviar = analisis.cuentas_analizadas
                .filter(c => seleccionados.has(c.codigo))
                .map(c => ({
                    codigo: c.codigo,
                    nombre: c.nombre,
                    permite_movimiento: c.permite_movimiento
                }));

            await planCuentasService.importarLote(aEnviar);

            alert(`¡Éxito! Se han creado ${aEnviar.length} cuentas.`);
            onImportComplete();
            onClose();
        } catch (err) {
            console.error(err);
            alert("Error al importar: " + (err.response?.data?.detail || err.message));
        } finally {
            setImportando(false);
        }
    };

    // --- RENDER ---
    if (!isOpen) return null;
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50 backdrop-blur-sm">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden">

                {/* Header */}
                <div className="bg-gradient-to-r from-indigo-600 to-blue-600 p-4 text-white flex justify-between items-center">
                    <h2 className="text-xl font-bold flex items-center gap-2">
                        <FaFileUpload /> Importador Inteligente de PUC
                    </h2>
                    <button onClick={onClose} className="text-white hover:text-gray-200 text-lg font-bold">✕</button>
                </div>

                {/* Body */}
                <div className="flex-1 overflow-auto p-6 bg-gray-50">

                    {step === 1 && (
                        <div className="flex flex-col items-center justify-center h-full space-y-6">
                            <div className="text-center max-w-lg">
                                <h3 className="text-xl font-bold text-gray-800 mb-2">Carga tu Archivo JSON</h3>
                                <p className="text-gray-500">Selecciona un archivo JSON con la estructura plana de cuentas. El sistema analizará cuáles son nuevas y te permitirá seleccionar.</p>
                            </div>

                            {comprobando ? (
                                <div className="flex flex-col items-center animate-pulse">
                                    <FaSpinner className="animate-spin text-4xl text-indigo-600 mb-2" />
                                    <span className="text-indigo-600 font-semibold">Analizando archivo contra base de datos...</span>
                                </div>
                            ) : (
                                <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-indigo-300 border-dashed rounded-lg cursor-pointer bg-white hover:bg-indigo-50 transition-colors">
                                    <div className="flex flex-col items-center justify-center pt-5 pb-6">
                                        <FaFileUpload className="w-10 h-10 mb-3 text-indigo-400" />
                                        <p className="mb-2 text-sm text-gray-500"><span className="font-semibold">Clic para subir</span> o arrastrar y soltar</p>
                                        <p className="text-xs text-gray-500">Formato .JSON (Array de objetos)</p>
                                    </div>
                                    <input type="file" accept=".json" className="hidden" onChange={handleFileChange} />
                                </label>
                            )}
                        </div>
                    )}

                    {step === 2 && analisis && (
                        <div className="flex flex-col h-full">
                            {/* Estadísticas */}
                            <div className="flex gap-4 mb-4 text-sm">
                                <div className="bg-green-100 text-green-800 px-3 py-2 rounded-lg font-semibold flex-1 text-center">
                                    {analisis.total_nuevas} Nuevas Detectadas
                                </div>
                                <div className="bg-orange-100 text-orange-800 px-3 py-2 rounded-lg font-semibold flex-1 text-center">
                                    {analisis.total_existentes} Ya Existen (Se ignorarán)
                                </div>
                                <div className="bg-indigo-100 text-indigo-800 px-3 py-2 rounded-lg font-semibold flex-1 text-center border border-indigo-200">
                                    {seleccionados.size} Seleccionadas para Importar
                                </div>
                            </div>

                            {/* Header de Acciones Masivas */}
                            <div className="flex gap-2 mb-2">
                                <button
                                    onClick={() => handleSelectAll(true)}
                                    className="px-3 py-1 text-xs font-semibold text-indigo-700 bg-indigo-50 rounded hover:bg-indigo-100 border border-indigo-200"
                                >
                                    Seleccionar Todo
                                </button>
                                <button
                                    onClick={() => handleSelectAll(false)}
                                    className="px-3 py-1 text-xs font-semibold text-gray-600 bg-white rounded hover:bg-gray-50 border border-gray-300"
                                >
                                    Ninguno
                                </button>
                            </div>

                            {/* Buscador */}
                            <div className="relative mb-4">
                                <FaSearch className="absolute left-3 top-3 text-gray-400" />
                                <input
                                    type="text"
                                    placeholder="Buscar cuenta por código o nombre para seleccionar..."
                                    className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                    value={filtro}
                                    onChange={(e) => setFiltro(e.target.value)}
                                />
                            </div>

                            {/* Tabla de Selección */}
                            <div className="flex-1 overflow-auto border rounded-lg bg-white shadow-inner">
                                <table className="w-full text-sm item-table">
                                    <thead className="bg-gray-100 sticky top-0 z-10">
                                        <tr>
                                            <th className="px-4 py-2 w-12 text-center">
                                                <input type="checkbox" disabled />
                                            </th>
                                            <th className="px-4 py-2 text-left">Código</th>
                                            <th className="px-4 py-2 text-left">Nombre</th>
                                            <th className="px-4 py-2 text-center">Estado</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-100">
                                        {cuentasVisibles.map((c) => (
                                            <tr key={c.codigo} className={!c.es_nueva ? 'bg-gray-50 opacity-60' : 'hover:bg-indigo-50'}>
                                                <td className="px-4 py-2 text-center">
                                                    {c.es_nueva ? (
                                                        <input
                                                            type="checkbox"
                                                            checked={seleccionados.has(c.codigo)}
                                                            onChange={() => toggleSeleccion(c.codigo)}
                                                            className="checkbox checkbox-xs checkbox-primary"
                                                        />
                                                    ) : (
                                                        <FaCheckDouble className="text-gray-400 inline" title="Ya existe" />
                                                    )}
                                                </td>
                                                <td className="px-4 py-2 font-mono font-bold text-gray-700">{c.codigo}</td>
                                                <td className="px-4 py-2">{c.nombre}</td>
                                                <td className="px-4 py-2 text-center">
                                                    {c.es_nueva ? (
                                                        <span className="text-green-600 font-bold text-xs bg-green-100 px-2 py-1 rounded">NUEVA</span>
                                                    ) : (
                                                        <span className="text-gray-500 font-bold text-xs">EXISTENTE</span>
                                                    )}
                                                </td>
                                            </tr>
                                        ))}
                                        {cuentasVisibles.length === 0 && (
                                            <tr><td colSpan="4" className="text-center py-10 text-gray-400">No se encontraron cuentas con ese filtro.</td></tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="bg-gray-100 p-4 border-t flex justify-between items-center">
                    <button
                        onClick={onClose}
                        className="btn btn-ghost text-gray-600"
                    >
                        Cancelar
                    </button>
                    {step === 2 && (
                        <button
                            onClick={handleImportarDefinitivo}
                            disabled={importando || seleccionados.size === 0}
                            className="btn bg-indigo-600 hover:bg-indigo-700 text-white border-none shadow-lg px-8"
                        >
                            {importando ? (
                                <><FaSpinner className="animate-spin mr-2" /> Importando...</>
                            ) : (
                                `Importar ${seleccionados.size} Cuentas`
                            )}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}
