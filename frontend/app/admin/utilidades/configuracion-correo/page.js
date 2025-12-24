
"use client";
import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'react-toastify';
import { FaEnvelope, FaKey, FaPlug, FaSave, FaCheckCircle, FaExclamationTriangle, FaBook } from 'react-icons/fa';

import { useAuth } from '../../../context/AuthContext';
import { apiService } from '../../../../lib/apiService';

export default function ConfiguracionCorreoPage() {
    const { user, loading: authLoading } = useAuth();
    const router = useRouter();

    const [email, setEmail] = useState('');
    const [password, setPassword] = useState(''); // Plain text input, encrypted by backend
    const [isLoading, setIsLoading] = useState(false);
    const [isTesting, setIsTesting] = useState(false);
    const [isConfigured, setIsConfigured] = useState(false);

    useEffect(() => {
        if (!authLoading && user) {
            fetchConfig();
        }
    }, [user, authLoading]);

    const fetchConfig = async () => {
        try {
            const res = await apiService.get('/config/email/');
            if (res.data.is_configured) {
                setEmail(res.data.smtp_user);
                setIsConfigured(true);
                setPassword('********'); // Dummy mask
            }
        } catch (err) {
            console.error(err);
        }
    };

    const handleTestConnection = async () => {
        if (!email || !password || password === '********') {
            toast.warn("Ingrese un correo y contraseña válidos para probar.");
            return;
        }
        setIsTesting(true);
        {/* Usamos toast.promise para feedback visual */ }
        const promise = apiService.post('/config/email/test', {
            smtp_user: email,
            smtp_password: password
        });

        toast.promise(promise, {
            pending: '🔌 Conectando con Gmail (SMTP)...',
            success: '✅ ¡Conexión Exitosa! Credenciales válidas.',
            error: {
                render({ data }) {
                    // Extract error detail
                    return `❌ Falló: ${data.response?.data?.detail || 'Error desconocido'}`;
                }
            }
        });

        try {
            await promise;
        } catch (e) {
            // Handled by toast
        } finally {
            setIsTesting(false);
        }
    };

    const handleSave = async () => {
        if (!email || !password) return;
        if (password === '********') {
            // User didn't change password, maybe only email? 
            // For security, require re-entry if changing.
            // But typical flow: just re-save user if only updating user? 
            // Backend expects password to encrypt. If masked, we can't send '********'.
            toast.info("Si desea actualizar, por favor reingrese la Contraseña de Aplicación.");
            setPassword('');
            return;
        }

        setIsLoading(true);
        try {
            await apiService.post('/config/email/', {
                smtp_user: email,
                smtp_password: password
            });
            toast.success("💾 Configuración guardada exitosamente.");
            setIsConfigured(true);
            setPassword('********');
        } catch (err) {
            toast.error("Error al guardar configuración.");
        } finally {
            setIsLoading(false);
        }
    };

    if (authLoading) return <p className="p-10">Cargando...</p>;

    return (
        <div className="container mx-auto">
            <div className="p-6 max-w-4xl mx-auto">
                <h1 className="text-3xl font-bold text-gray-800 mb-2 flex items-center gap-2">
                    <FaEnvelope className="text-indigo-600" />
                    Configuración de Correo (SMTP)
                </h1>
                <p className="text-gray-600 mb-8">
                    Configure la cuenta de Gmail desde la cual se enviarán los reportes, facturas y alertas de su empresa.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {/* FORMULARIO */}
                    <div className="bg-white p-6 rounded-xl shadow-lg border border-gray-100">
                        <div className="mb-6">
                            <label className="block text-sm font-bold text-gray-700 mb-2">
                                Correo Electrónico (Gmail)
                            </label>
                            <div className="relative">
                                <FaEnvelope className="absolute left-3 top-3 text-gray-400" />
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                    placeholder="ej: gerencia@miempresa.com"
                                />
                            </div>
                        </div>

                        <div className="mb-6">
                            <label className="block text-sm font-bold text-gray-700 mb-2">
                                Contraseña de Aplicación
                            </label>
                            <div className="relative">
                                <FaKey className="absolute left-3 top-3 text-gray-400" />
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                    placeholder="Ingrese el código de 16 caracteres"
                                />
                            </div>
                            <p className="text-xs text-gray-500 mt-1">
                                No use su clave normal. Use una "App Password" de Google.
                            </p>
                        </div>

                        <div className="flex gap-4">
                            <button
                                onClick={handleTestConnection}
                                disabled={isTesting || !password || password === '********'}
                                className={`flex-1 py-2 px-4 rounded-lg font-bold text-white flex items-center justify-center gap-2 transition-all
                                    ${isTesting ? 'bg-gray-400 cursor-not-allowed' : 'bg-yellow-500 hover:bg-yellow-600 shadow-md'}`}
                            >
                                <FaPlug /> {isTesting ? 'Probando...' : 'Probar Conexión'}
                            </button>

                            <button
                                onClick={handleSave}
                                disabled={isLoading || isTesting}
                                className="flex-1 py-2 px-4 rounded-lg font-bold text-white bg-indigo-600 hover:bg-indigo-700 shadow-md flex items-center justify-center gap-2"
                            >
                                {isLoading ? 'Guardando...' : <><FaSave /> Guardar Configuración</>}
                            </button>
                        </div>
                    </div>

                    {/* ESTADO E INSTRUCCIONES */}
                    <div className="space-y-6">
                        {/* Status Card */}
                        <div className={`p-6 rounded-xl border ${isConfigured ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'}`}>
                            <h3 className="font-bold text-lg mb-2 flex items-center gap-2">
                                {isConfigured ? <FaCheckCircle className="text-green-600" /> : <FaExclamationTriangle className="text-gray-400" />}
                                Estado del Servicio
                            </h3>
                            {isConfigured ? (
                                <p className="text-green-800 text-sm">
                                    Su correo <strong>{email}</strong> está configurado y listo para enviar reportes automatizados.
                                </p>
                            ) : (
                                <p className="text-gray-600 text-sm">
                                    El servicio no está configurado. El sistema usará la configuración por defecto o fallará si no hay una global.
                                </p>
                            )}
                        </div>

                        {/* Instructions */}
                        <div className="bg-blue-50 p-6 rounded-xl border border-blue-200 text-sm text-blue-900">
                            <h4 className="font-bold mb-2">¿Cómo obtener la contraseña?</h4>
                            <ol className="list-decimal list-inside space-y-2">
                                <li>Vaya a su Cuenta de Google {'>'} Seguridad.</li>
                                <li>Busque <strong>Verificación en 2 pasos</strong> (Actívela si no lo está).</li>
                                <li>Busque la opción <strong>Contraseñas de aplicaciones</strong>.</li>
                                <li>Genere una nueva para "Otra (ContaPY2)".</li>
                                <li>Copie el código de 16 letras y péguelo aquí.</li>
                            </ol>
                            <div className="flex flex-col gap-2 mt-4">
                                <a
                                    href="/manual/guia_gmail_app_password.html"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="flex items-center justify-center gap-2 py-2 px-4 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 shadow-sm transition-all"
                                >
                                    <FaBook /> Ver Guía Paso a Paso (Recomendado)
                                </a>
                                <a
                                    href="https://myaccount.google.com/apppasswords"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-center text-xs text-blue-600 hover:underline"
                                >
                                    Ir directo a Google &rarr;
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
