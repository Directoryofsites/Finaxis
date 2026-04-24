'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../../context/AuthContext';
import { phService } from '../../../lib/phService';
import { reportesFacturacionService } from '../../../lib/reportesFacturacionService'; // para cuentas
import BatchPreviewTable from '../../components/ph/BatchPreviewTable';
import { FaUpload, FaCheck, FaSpinner, FaFileExcel, FaFileCsv } from 'react-icons/fa';

export default function RecaudoMasivoPage() {
    const router = useRouter();
    const { user, loading: authLoading } = useAuth();
    
    const [file, setFile] = useState(null);
    const [cuentasBancarias, setCuentasBancarias] = useState([]);
    const [cuentaSeleccionada, setCuentaSeleccionada] = useState('');
    const [fechaConsignacion, setFechaConsignacion] = useState(new Date().toISOString().split('T')[0]);
    
    const [previewData, setPreviewData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [processing, setProcessing] = useState(false);
    const [error, setError] = useState(null);
    const [successMessage, setSuccessMessage] = useState(null);

    useEffect(() => {
        if (!authLoading && user) {
            cargarCuentas();
        }
    }, [user, authLoading]);

    const cargarCuentas = async () => {
        try {
            // Reutilizando el servicio de cuentas que lista cajas y bancos
            const data = await reportesFacturacionService.getCuentasBancarias();
            setCuentasBancarias(data);
            if (data && data.length > 0) {
                setCuentaSeleccionada(data[0].id.toString());
            }
        } catch (err) {
            console.error("Error cargando cuentas", err);
        }
    };

    const handleFileChange = (e) => {
        if (e.target.files && e.target.files.length > 0) {
            setFile(e.target.files[0]);
            setPreviewData(null);
            setError(null);
            setSuccessMessage(null);
        }
    };

    const handleUpload = async () => {
        if (!file) {
            setError("Por favor selecciona un archivo.");
            return;
        }

        setLoading(true);
        setError(null);
        setSuccessMessage(null);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const data = await phService.uploadRecaudoMasivo(formData);
            setPreviewData(data);
        } catch (err) {
            setError(err.message || "Error procesando el archivo. Verifica el formato.");
        } finally {
            setLoading(false);
        }
    };

    const handleProcess = async () => {
        if (!cuentaSeleccionada) {
            setError("Selecciona una cuenta bancaria de destino.");
            return;
        }
        
        if (!previewData || previewData.filas_validas === 0) {
            setError("No hay filas válidas para procesar.");
            return;
        }

        setProcessing(true);
        setError(null);

        const requestBody = {
            cuenta_bancaria_id: parseInt(cuentaSeleccionada),
            fecha_consignacion: fechaConsignacion,
            filas: previewData.detalles
        };

        try {
            const result = await phService.processRecaudoMasivo(requestBody);
            setSuccessMessage(result.mensaje);
            setPreviewData(null);
            setFile(null);
            // Reset input file
            const fileInput = document.getElementById('file-upload');
            if(fileInput) fileInput.value = '';
        } catch (err) {
            setError(err.message || "Error registrando los pagos en lote.");
        } finally {
            setProcessing(false);
        }
    };

    if (authLoading) return <div className="p-10 text-center">Cargando...</div>;

    return (
        <div className="min-h-screen bg-gray-50 p-6 font-sans pb-20">
            <div className="max-w-6xl mx-auto">
                <div className="flex justify-between items-center mb-6">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                            <div className="p-2 bg-green-100 rounded-lg text-green-600"><FaUpload /></div>
                            Recaudo Masivo (Extractos Bancarios)
                        </h1>
                        <p className="text-sm text-gray-500 mt-1">Sube el archivo Excel/CSV del banco para conciliar automáticamente los pagos.</p>
                    </div>
                </div>

                {error && (
                    <div className="mb-6 p-4 bg-red-100 border-l-4 border-red-500 text-red-700 rounded-r-lg">
                        {error}
                    </div>
                )}
                
                {successMessage && (
                    <div className="mb-6 p-4 bg-green-100 border-l-4 border-green-500 text-green-700 rounded-r-lg font-bold">
                        {successMessage}
                    </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* COLUMNA IZQUIERDA: FORMULARIO */}
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 h-fit">
                        <h2 className="text-lg font-bold text-gray-700 border-b pb-2 mb-4">Configuración del Lote</h2>
                        
                        <div className="space-y-4">
                            <div>
                                <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Archivo del Banco (.csv, .xlsx)</label>
                                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 flex flex-col items-center justify-center bg-gray-50 hover:bg-indigo-50 transition-colors">
                                    <input 
                                        id="file-upload"
                                        type="file" 
                                        accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel" 
                                        onChange={handleFileChange}
                                        className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
                                    />
                                    {file && <p className="text-xs font-bold text-indigo-600 mt-2">Seleccionado: {file.name}</p>}
                                </div>
                            </div>

                            <div>
                                <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Cuenta Bancaria Destino</label>
                                <select 
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm text-sm outline-none"
                                    value={cuentaSeleccionada}
                                    onChange={(e) => setCuentaSeleccionada(e.target.value)}
                                >
                                    <option value="">-- Seleccione Cuenta --</option>
                                    {cuentasBancarias.map(c => (
                                        <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Fecha de Consignación</label>
                                <input 
                                    type="date" 
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm text-sm outline-none"
                                    value={fechaConsignacion}
                                    onChange={(e) => setFechaConsignacion(e.target.value)}
                                />
                            </div>

                            <button 
                                onClick={handleUpload}
                                disabled={!file || loading || processing}
                                className="w-full mt-4 bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
                            >
                                {loading ? <FaSpinner className="animate-spin" /> : <FaUpload />}
                                Previsualizar Cruce
                            </button>
                        </div>
                    </div>

                    {/* COLUMNA DERECHA: PREVIEW Y PROCESAR */}
                    <div className="md:col-span-2">
                        {previewData ? (
                            <div className="space-y-4">
                                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex justify-between items-center">
                                    <div>
                                        <h2 className="text-lg font-bold text-gray-800">Cruce Exitoso</h2>
                                        <p className="text-sm text-gray-500">Revisa los resultados antes de aplicar los pagos definitivamente.</p>
                                    </div>
                                    <button 
                                        onClick={handleProcess}
                                        disabled={processing || previewData.filas_validas === 0}
                                        className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-6 rounded-lg shadow-lg flex items-center gap-2 transition-transform active:scale-95 disabled:opacity-50"
                                    >
                                        {processing ? <FaSpinner className="animate-spin" /> : <FaCheck />}
                                        {processing ? 'Generando Recibos...' : `Registrar ${previewData.filas_validas} Pagos`}
                                    </button>
                                </div>

                                <BatchPreviewTable previewData={previewData} />
                            </div>
                        ) : (
                            <div className="bg-white p-10 rounded-xl shadow-sm border border-gray-100 h-full flex flex-col items-center justify-center text-gray-400">
                                <div className="flex gap-4 mb-4 text-4xl text-gray-300">
                                    <FaFileExcel />
                                    <FaFileCsv />
                                </div>
                                <p className="font-medium text-lg">Sube un archivo para previsualizar los pagos</p>
                                <p className="text-sm mt-2 text-center max-w-sm">
                                    El archivo debe contener columnas con la palabra "Ref", "Fecha" y "Valor".
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
