
import React, { useState, useRef, useEffect } from 'react';
import {
    FaFileExcel, FaUpload, FaChevronDown, FaChevronUp, FaInfoCircle,
    FaDownload, FaCheckCircle, FaCloudUploadAlt, FaFileAlt, FaSearch
} from 'react-icons/fa';
import { apiService } from '../../../lib/apiService';
import TemplateManager from './TemplateManager';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

// Format currency helper
const formatCurrency = (val) => {
    return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(val);
};

export default function UniversalImportForm({ maestros, empresaActual, isProcessing, setIsProcessing, setMessage, setError }) {
    const [isOpen, setIsOpen] = useState(true);
    const [file, setFile] = useState(null);
    const [dragActive, setDragActive] = useState(false);
    const [result, setResult] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const fileInputRef = useRef(null);

    // Template State
    const [showTemplateManager, setShowTemplateManager] = useState(false);
    const [templates, setTemplates] = useState([]);
    const [selectedTemplateId, setSelectedTemplateId] = useState(null);

    useEffect(() => {
        loadTemplates();
    }, []);

    const loadTemplates = async () => {
        try {
            const res = await apiService.get('/import-templates/');
            setTemplates(res.data);
        } catch (error) {
            console.error("Error loading templates", error);
        }
    };

    // --- File Handling ---
    const handleFileChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    const handleDrag = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            setFile(e.dataTransfer.files[0]);
        }
    };

    const downloadTemplate = () => {
        const headers = "Fecha (DD/MM/YYYY),Cod Tipo Doc,Numero,Cod Cuenta,NIT Tercero,Nombre Tercero,Detalle,Debito,Credito";
        const example = "01/01/2023,CB,1,110505,88888888,EMPRESA EJEMPLO,SALDO INICIAL,1000000,0";
        const content = `\uFEFF${headers}\n${example}`;
        const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = "Plantilla_Universal_ContaPY.csv";
        link.click();
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!file || !empresaActual) return;

        setIsProcessing(true);
        setMessage('');
        setError(null);
        setResult(null);

        const formData = new FormData();
        formData.append('empresa_id', empresaActual.id);
        formData.append('file_excel', file);
        if (selectedTemplateId) formData.append('template_id', selectedTemplateId);

        try {
            const response = await apiService.post('/utilidades/importar-universal', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            setResult(response.data);
            setMessage('Importación completada con éxito.');
        } catch (err) {
            console.error(err);
            const msg = err.response?.data?.detail || 'Error en la importación.';
            setError(msg);
        } finally {
            setIsProcessing(false);
        }
    };

    // Filter results for summary table
    const filteredDocs = result?.created_documents?.filter(doc =>
        doc.numero.toString().includes(searchTerm) ||
        doc.beneficiario.toLowerCase().includes(searchTerm.toLowerCase()) ||
        doc.concepto.toLowerCase().includes(searchTerm.toLowerCase())
    ) || [];

    // --- UI Components ---

    return (
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden transition-all duration-300">
            {/* Header */}
            <div
                className="p-6 bg-gradient-to-r from-indigo-600 to-violet-600 text-white flex justify-between items-center cursor-pointer"
                onClick={() => setIsOpen(!isOpen)}
            >
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-white/20 backdrop-blur-sm rounded-xl">
                        <FaCloudUploadAlt className="text-2xl text-white" />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold">Importación Universal Inteligente</h2>
                        <p className="text-sm text-indigo-100 opacity-90">Sube tus Excel o CSV y nosotros hacemos el resto.</p>
                    </div>
                </div>
                {isOpen ? <FaChevronUp /> : <FaChevronDown />}
            </div>

            {isOpen && (
                <div className="p-8">

                    {!result ? (
                        /* SEARCH & UPLOAD STATE */
                        <form onSubmit={handleSubmit} onDragEnter={handleDrag} className="space-y-8">

                            {/* Stats / Instructions Banner */}
                            <div className="bg-indigo-50 rounded-xl p-5 border border-indigo-100 flex items-start gap-4">
                                <FaInfoCircle className="text-indigo-500 text-xl mt-1" />
                                <div>
                                    <h3 className="font-bold text-indigo-900">¿Cómo funciona?</h3>
                                    <p className="text-sm text-indigo-700 mt-1">
                                        El sistema detecta automáticamente columnas, delimitadores (CSV) y crea Cuentas o Terceros que falten.
                                        Solo asegúrate de tener columnas para: <span className="font-semibold">Fecha, Documento, Cuenta, Tercero y Valor</span>.
                                    </p>
                                    <button onClick={downloadTemplate} type="button" className="mt-3 text-xs font-bold text-indigo-600 hover:text-indigo-800 underline flex items-center gap-1">
                                        <FaDownload /> Descargar Plantilla Ejemplo
                                    </button>
                                </div>
                            </div>

                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                                {/* Configuration */}
                                <div className="space-y-6">
                                    {/* Template Selection - Modern Design */}
                                    <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow group">
                                        <div className="flex justify-between items-center mb-3">
                                            <label className="text-sm font-bold text-gray-700 flex items-center gap-2">
                                                <FaFileExcel className="text-indigo-500" /> Plantilla de Lectura
                                            </label>
                                            <button
                                                type="button"
                                                onClick={() => setShowTemplateManager(true)}
                                                className="text-xs font-semibold text-indigo-600 bg-indigo-50 px-3 py-1.5 rounded-full hover:bg-indigo-100 transition-colors"
                                            >
                                                Gestionar / Crear
                                            </button>
                                        </div>

                                        <div className="relative">
                                            <select
                                                className="w-full pl-4 pr-10 py-3 bg-gray-50 border-0 rounded-xl text-gray-700 font-medium focus:ring-2 focus:ring-indigo-500 transition-all text-sm appearance-none cursor-pointer"
                                                value={selectedTemplateId || ''}
                                                onChange={(e) => setSelectedTemplateId(e.target.value ? parseInt(e.target.value) : null)}
                                            >
                                                <option value="">✨ Detección Automática (Inteligente)</option>
                                                {templates.map(t => (
                                                    <option key={t.id} value={t.id}>📄 {t.nombre}</option>
                                                ))}
                                            </select>
                                            <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-gray-400">
                                                <FaChevronDown />
                                            </div>
                                        </div>

                                        <p className="text-xs text-gray-400 mt-3 pl-1 leading-relaxed">
                                            {selectedTemplateId
                                                ? "El sistema leerá las columnas basándose estrictamente en tu plantilla personalizada."
                                                : "ContaPY analizará el archivo e intentará descubrir las columnas automáticamente."}
                                        </p>
                                    </div>

                                </div>

                                {/* Drag & Drop Zone */}
                                <div className="lg:col-span-2">
                                    <label
                                        className={`
                                            flex flex-col items-center justify-center w-full h-48 
                                            border-2 border-dashed rounded-2xl cursor-pointer 
                                            transition-all duration-300 group
                                            ${dragActive
                                                ? 'border-indigo-500 bg-indigo-50 scale-[1.01]'
                                                : 'border-gray-300 bg-gray-50 hover:bg-gray-100 hover:border-gray-400'
                                            }
                                            ${file ? 'border-green-500 bg-green-50' : ''}
                                        `}
                                        onDragEnter={handleDrag}
                                        onDragLeave={handleDrag}
                                        onDragOver={handleDrag}
                                        onDrop={handleDrop}
                                    >
                                        <div className="flex flex-col items-center justify-center pt-5 pb-6 text-center">
                                            {file ? (
                                                <>
                                                    <div className="p-3 bg-green-100 rounded-full text-green-600 mb-3 animate-pulse">
                                                        <FaFileExcel className="text-3xl" />
                                                    </div>
                                                    <p className="text-lg font-bold text-gray-700">{file.name}</p>
                                                    <p className="text-xs text-gray-500">{(file.size / 1024).toFixed(1)} KB listos para procesar</p>
                                                </>
                                            ) : (
                                                <>
                                                    <FaCloudUploadAlt className={`text-4xl mb-3 ${dragActive ? 'text-indigo-600' : 'text-gray-400 group-hover:text-gray-600'}`} />
                                                    <p className="mb-2 text-sm text-gray-500"><span className="font-semibold text-indigo-600">Haz clic para cargar</span> o arrastra y suelta</p>
                                                    <p className="text-xs text-gray-400">Soporta Excel (.xlsx) y CSV</p>
                                                </>
                                            )}
                                        </div>
                                        <input
                                            ref={fileInputRef}
                                            type="file"
                                            className="hidden"
                                            accept=".xlsx,.xls,.csv"
                                            onChange={handleFileChange}
                                        />
                                    </label>
                                </div>
                            </div>

                            {/* Action Button */}
                            <div className="flex justify-end pt-4">
                                <button
                                    type="submit"
                                    disabled={!file || isProcessing}
                                    className={`
                                        btn btn-lg rounded-xl shadow-lg border-0 gap-3 text-white px-8
                                        ${isProcessing
                                            ? 'bg-gray-400 cursor-not-allowed'
                                            : 'bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 hover:shadow-indigo-200/50'
                                        }
                                    `}
                                >
                                    {isProcessing ? (
                                        <> <span className="loading loading-spinner"></span> Procesando Archivo... </>
                                    ) : (
                                        <> <FaUpload /> Iniciar Importación </>
                                    )}
                                </button>
                            </div>
                        </form>

                    ) : (

                        /* RESULTS DASHBOARD */
                        <div className="animate-fadeIn">
                            {/* Summary Cards */}
                            <div className="flex justify-between items-center mb-6 p-4 bg-white rounded-lg shadow-sm border border-gray-100">
                                <h3 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                                    <FaCheckCircle className="text-green-500" /> Resumen de Importación
                                </h3>
                                <button
                                    onClick={() => {
                                        console.log("Generando PDF...");
                                        const doc = new jsPDF('l', 'mm', 'a4');
                                        doc.text("Reporte de Importación", 14, 15);
                                        doc.setFontSize(10);
                                        doc.text(`Fecha: ${new Date().toLocaleString()}`, 14, 22);

                                        autoTable(doc, {
                                            startY: 25,
                                            head: [['Fecha', 'Tipo', 'Nombre Doc', 'Número', 'Cuenta', 'Nombre Cuenta', 'NIT', 'Tercero', 'Débito', 'Crédito']],
                                            body: result.created_documents.map(d => [
                                                d.fecha, d.tipo_doc, d.nombre_tipo_doc, d.numero, d.cuenta_codigo, d.cuenta_nombre, d.nit, d.tercero_nombre,
                                                formatCurrency(d.debito), formatCurrency(d.credito)
                                            ]),
                                            styles: { fontSize: 8 },
                                        });
                                        doc.save("Reporte_Importacion.pdf");
                                    }}
                                    style={{ backgroundColor: '#2563EB', color: 'white', padding: '10px 20px', borderRadius: '5px', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}
                                >
                                    <FaFileAlt /> DESCARGAR PDF AHORA
                                </button>
                            </div>

                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                                <StatCard
                                    icon={<FaCheckCircle />} color="text-emerald-600" bg="bg-emerald-100"
                                    value={result.transactions} label="Registros Importados"
                                />
                                <StatCard
                                    icon={<FaUpload />} color="text-blue-600" bg="bg-blue-100"
                                    value={result.accounts} label="Cuentas Nuevas"
                                />
                                <StatCard
                                    icon={<FaCheckCircle />} color="text-orange-600" bg="bg-orange-100"
                                    value={result.third_parties} label="Terceros Nuevos"
                                />
                            </div>

                            {/* Error Alert */}
                            {result.errors && result.errors.length > 0 && (
                                <div className="mb-8 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700">
                                    <strong className="block mb-2 text-red-800 flex items-center gap-2">
                                        <span className="badge badge-error badge-xs">!</span> Atencion: Hubo algunos problemas
                                    </strong>
                                    <ul className="list-disc ml-5 space-y-1 max-h-32 overflow-y-auto">
                                        {result.errors.map((e, i) => <li key={i}>{e}</li>)}
                                    </ul>
                                </div>
                            )}

                            {/* Detailed List */}
                            <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden text-xs">
                                <div className="overflow-x-auto max-h-[600px]">
                                    <table className="table table-pin-rows w-full">
                                        <thead>
                                            <tr className="bg-gray-50 text-gray-700 font-bold">
                                                <th>Fecha</th>
                                                <th>Tipo</th>
                                                <th>Nombre Doc</th>
                                                <th>Número</th>
                                                <th>Cta Cod</th>
                                                <th>Cta Nombre</th>
                                                <th>NIT</th>
                                                <th>Tercero</th>
                                                <th className="text-right">Débito</th>
                                                <th className="text-right">Crédito</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {result.created_documents.map((row, i) => (
                                                <tr key={i} className="hover:bg-gray-50 border-b border-gray-100">
                                                    <td className="whitespace-nowrap">{row.fecha}</td>
                                                    <td className="font-mono">{row.tipo_doc}</td>
                                                    <td className="truncate max-w-[150px]" title={row.nombre_tipo_doc}>{row.nombre_tipo_doc}</td>
                                                    <td className="font-bold">{row.numero}</td>
                                                    <td className="font-mono text-indigo-600">{row.cuenta_codigo}</td>
                                                    <td className="truncate max-w-[150px]" title={row.cuenta_nombre}>{row.cuenta_nombre}</td>
                                                    <td className="font-mono">{row.nit}</td>
                                                    <td className="truncate max-w-[150px]" title={row.tercero_nombre}>{row.tercero_nombre}</td>
                                                    <td className="text-right font-mono">{row.debito > 0 ? formatCurrency(row.debito) : '-'}</td>
                                                    <td className="text-right font-mono">{row.credito > 0 ? formatCurrency(row.credito) : '-'}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            <div className="flex justify-center mt-8">
                                <button
                                    onClick={() => { setFile(null); setResult(null); }}
                                    className="btn btn-outline text-gray-500 hover:bg-gray-100 gap-2 px-8"
                                >
                                    Subir Otro Archivo
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {showTemplateManager && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50 backdrop-blur-sm">
                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
                        <TemplateManager
                            onClose={() => { setShowTemplateManager(false); loadTemplates(); }}
                            onSelectTemplate={(id) => {
                                loadTemplates();
                                setSelectedTemplateId(id);
                                setShowTemplateManager(false);
                            }}
                        />
                    </div>
                </div>
            )}
        </div>
    );
}

function StatCard({ icon, color, bg, value, label }) {
    return (
        <div className="bg-white p-4 rounded-xl border border-gray-100 flex items-center gap-4 hover:shadow-md transition-shadow">
            <div className={`p-3 rounded-lg ${bg} ${color} text-xl`}>
                {icon}
            </div>
            <div>
                <p className={`text-2xl font-bold ${color}`}>{value}</p>
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide">{label}</p>
            </div>
        </div>
    );
}
