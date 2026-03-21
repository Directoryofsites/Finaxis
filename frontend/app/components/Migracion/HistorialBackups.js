'use client';
import React, { useState, useEffect } from 'react';
import { FaDownload, FaHistory, FaSpinner, FaArchive } from 'react-icons/fa';
import { apiService, API_URL } from '../../../lib/apiService';

export default function HistorialBackups() {
    const [backups, setBackups] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [downloadingFile, setDownloadingFile] = useState(null);

    const fetchBackups = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const res = await apiService.get('/utilidades/backups');
            setBackups(res.data);
        } catch (err) {
            setError(err.response?.data?.detail || 'Error al cargar el historial de copias de seguridad.');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchBackups();
    }, []);

    const handleDownload = async (filename) => {
        setDownloadingFile(filename);
        try {
            // Se utiliza blob para poder forzar la descarga en el navegador con el stream
            const response = await apiService.get(`/utilidades/backups/${filename}/download`, {
                responseType: 'blob'
            });
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', filename);
            document.body.appendChild(link);
            link.click();
            link.parentNode.removeChild(link);
            window.URL.revokeObjectURL(url);
        } catch (err) {
            alert('Error al descargar el archivo. Es posible que esté corrupto o ya no exista.');
            console.error(err);
        } finally {
            setDownloadingFile(null);
        }
    };

    return (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 mt-6 relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
                <FaArchive className="text-8xl" />
            </div>
            
            <div className="flex items-center gap-3 mb-6 relative z-10">
                <div className="p-3 bg-indigo-100 rounded-lg text-indigo-600">
                    <FaHistory className="text-xl" />
                </div>
                <div>
                    <h2 className="text-xl font-bold text-gray-800">Historial de Copias Automáticas</h2>
                    <p className="text-sm text-gray-500">
                        Visualiza y descarga tus copias de seguridad generadas automáticamente por el sistema.
                    </p>
                </div>
            </div>

            {error && (
                <div className="mb-4 bg-red-50 text-red-600 p-3 rounded border border-red-200 text-sm">
                    {error}
                </div>
            )}

            <div className="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden relative z-10">
                {isLoading ? (
                    <div className="flex flex-col items-center justify-center p-8 text-gray-500">
                        <FaSpinner className="animate-spin text-3xl mb-3 text-indigo-500" />
                        <p>Buscando copias de seguridad de la empresa...</p>
                    </div>
                ) : backups.length === 0 ? (
                    <div className="text-center p-8">
                        <FaArchive className="text-gray-300 text-4xl mx-auto mb-3" />
                        <p className="text-gray-500 font-medium">No hay copias de seguridad almacenadas aún.</p>
                        <p className="text-xs text-gray-400 mt-1">El servidor automático generará la primera copia durante la próxima madrugada.</p>
                    </div>
                ) : (
                    <ul className="divide-y divide-gray-200">
                        {backups.map((backup, index) => (
                            <li key={index} className="p-4 hover:bg-gray-100 transition flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <div className="bg-white p-2 border border-gray-200 rounded shadow-sm text-indigo-400">
                                        <FaArchive />
                                    </div>
                                    <div>
                                        <p className="font-mono text-sm font-bold text-gray-800">{backup.filename}</p>
                                        <p className="text-xs text-gray-500">
                                            Fecha: {new Date(backup.created_at).toLocaleString()} | Peso: {(backup.size_mb).toFixed(2)} MB
                                        </p>
                                    </div>
                                </div>
                                <div>
                                    <button 
                                        onClick={() => handleDownload(backup.filename)}
                                        disabled={downloadingFile === backup.filename}
                                        className="flex items-center gap-2 px-3 py-1.5 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200 rounded text-sm font-medium transition disabled:bg-gray-100 disabled:text-gray-400 disabled:border-gray-200 cursor-pointer"
                                    >
                                        {downloadingFile === backup.filename ? (
                                            <><FaSpinner className="animate-spin" /> Descargando...</>
                                        ) : (
                                            <><FaDownload /> Descargar</>
                                        )}
                                    </button>
                                </div>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
}
