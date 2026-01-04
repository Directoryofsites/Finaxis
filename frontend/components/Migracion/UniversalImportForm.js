import React, { useState } from 'react';
import { FaFileExcel, FaUpload, FaChevronDown, FaChevronUp, FaInfoCircle, FaDownload } from 'react-icons/fa';
import { apiService } from '../../lib/apiService';

export default function UniversalImportForm({ maestros, empresaActual, isProcessing, setIsProcessing, setMessage, setError }) {
    const [isOpen, setIsOpen] = useState(false); // Collapsible
    const [file, setFile] = useState(null);
    const [defaultTerceroId, setDefaultTerceroId] = useState('');
    const [result, setResult] = useState(null);

    const handleFileChange = (e) => {
        setFile(e.target.files[0]);
    };

    const downloadTemplate = () => {
        // Generar un CSV simple on-the-fly y descargar
        const headers = "Fecha (DD/MM/YYYY),Cod Tipo Doc,Numero,Cod Cuenta,NIT Tercero,Nombre Tercero,Detalle,Debito,Credito";
        const example = "01/01/2023,CB,1,110505,88888888,EMPRESA EJEMPLO,SALDO INICIAL,1000000,0";
        const content = `\uFEFF${headers}\n${example}`; // BOM for Excel
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
        if (defaultTerceroId) {
            formData.append('default_tercero_id', defaultTerceroId);
        }

        try {
            const response = await apiService.post('/utilidades/importar-universal', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            setResult(response.data);
            setMessage('Importación Universal completada exitosamente.');
        } catch (err) {
            console.error(err);
            const msg = err.response?.data?.detail || 'Error en la importación.';
            setError(msg);
        } finally {
            setIsProcessing(false);
        }
    };

    return (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div
                className="p-6 bg-gradient-to-r from-green-50 to-white cursor-pointer flex justify-between items-center"
                onClick={() => setIsOpen(!isOpen)}
            >
                <div className="flex items-center gap-3">
                    <div className="p-3 bg-green-100 rounded-lg text-green-600">
                        <FaFileExcel className="text-xl" />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold text-gray-800">Importación Universal (Excel)</h2>
                        <p className="text-sm text-gray-500">Migre datos desde cualquier software usando nuestra "Plantilla Maestra".</p>
                    </div>
                </div>
                {isOpen ? <FaChevronUp className="text-gray-400" /> : <FaChevronDown className="text-gray-400" />}
            </div>

            {isOpen && (
                <div className="p-6 border-t border-gray-100 animate-fadeIn">

                    <div className="mb-6 bg-blue-50 p-4 rounded-lg flex items-start gap-3">
                        <FaInfoCircle className="text-blue-500 mt-1" />
                        <div className="text-sm text-blue-800">
                            <p className="font-bold mb-1">Instrucciones:</p>
                            <ul className="list-disc ml-4 space-y-1">
                                <li>Descargue la Plantilla Maestra.</li>
                                <li>Copie y pegue sus datos (Fecha, Doc, Cuenta, Tercero, Valor).</li>
                                <li>El sistema creará automáticamente las Cuentas, Terceros y Documentos que no existan.</li>
                            </ul>
                        </div>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-6">

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* File Upload */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">Archivo Excel / CSV (.xlsx, .csv)</label>
                                <input
                                    type="file"
                                    accept=".xlsx, .xls, .csv"
                                    onChange={handleFileChange}
                                    required
                                    className="file-input file-input-bordered file-input-primary w-full"
                                />
                            </div>

                            {/* Default Tercero */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">Tercero por Defecto (Opcional)</label>
                                <select
                                    value={defaultTerceroId}
                                    onChange={(e) => setDefaultTerceroId(e.target.value)}
                                    className="select select-bordered w-full"
                                >
                                    <option value="">-- El sistema lo creará si falta --</option>
                                    {maestros.terceros.map(t => (
                                        <option key={t.id} value={t.id}>{t.nit} - {t.razon_social}</option>
                                    ))}
                                </select>
                                <p className="text-xs text-gray-500 mt-1">Si una línea no tiene NIT, se usará este tercero.</p>
                            </div>
                        </div>

                        <div className="flex gap-4 pt-4">
                            <button
                                type="button"
                                onClick={downloadTemplate}
                                className="btn btn-outline btn-success gap-2"
                            >
                                <FaDownload /> Plantilla
                            </button>

                            <button
                                type="submit"
                                disabled={!file || isProcessing}
                                className={`btn btn-primary flex-1 gap-2 ${isProcessing ? 'loading' : ''}`}
                            >
                                <FaUpload /> {isProcessing ? 'Importando...' : 'Subir y Procesar'}
                            </button>
                        </div>

                    </form>

                    {result && (
                        <div className="mt-8 p-4 bg-gray-50 rounded-lg border border-gray-200">
                            <h3 className="font-bold text-gray-800 mb-2">Resumen de Importación:</h3>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                                <div className="bg-white p-3 rounded shadow-sm">
                                    <p className="text-2xl font-bold text-indigo-600">{result.documents}</p>
                                    <p className="text-xs text-gray-500 uppercase">Documentos</p>
                                </div>
                                <div className="bg-white p-3 rounded shadow-sm">
                                    <p className="text-2xl font-bold text-green-600">{result.transactions}</p>
                                    <p className="text-xs text-gray-500 uppercase">Movimientos</p>
                                </div>
                                <div className="bg-white p-3 rounded shadow-sm">
                                    <p className="text-2xl font-bold text-blue-600">{result.accounts}</p>
                                    <p className="text-xs text-gray-500 uppercase">Cuentas Nuevas</p>
                                </div>
                                <div className="bg-white p-3 rounded shadow-sm">
                                    <p className="text-2xl font-bold text-orange-600">{result.third_parties}</p>
                                    <p className="text-xs text-gray-500 uppercase">Terceros Nuevos</p>
                                </div>
                            </div>

                            {result.errors && result.errors.length > 0 && (
                                <div className="mt-4">
                                    <p className="text-red-600 font-bold mb-2">Errores / Advertencias:</p>
                                    <div className="max-h-40 overflow-y-auto text-xs bg-red-50 p-2 rounded text-red-700 font-mono">
                                        {result.errors.map((e, i) => <div key={i}>{e}</div>)}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
