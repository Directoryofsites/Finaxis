'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/app/context/AuthContext';
import { apiService } from '@/lib/apiService';
import { toast } from 'react-toastify';
import {
    FaBuilding, FaUserLock, FaSave, FaExclamationTriangle, FaUser, FaShieldAlt, FaQrcode, FaCheckCircle, FaTimesCircle
} from 'react-icons/fa';

export default function PerfilConfigPage() {
    const { user } = useAuth();
    const [activeTab, setActiveTab] = useState('empresa');
    const [isLoading, setIsLoading] = useState(false);

    // Estado Empresa
    const [empresaData, setEmpresaData] = useState({
        razon_social: '',
        nit: '',
        direccion: '',
        telefono: '',
        email: '',
        logo_url: ''
    });

    // Estado Password
    const [passData, setPassData] = useState({
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
    });

    // Estado Usuario
    const [usuarioData, setUsuarioData] = useState({
        whatsapp_number: ''
    });

    // Estado Template
    const [templateModalOpen, setTemplateModalOpen] = useState(false);
    const [newTemplateName, setNewTemplateName] = useState('');

    // --- Estado 2FA ---
    const [twoFAStatus, setTwoFAStatus] = useState(null);   // null = desconocido, true/false
    const [twoFASetup, setTwoFASetup] = useState(null);     // { secret, qr_uri } cuando se inicia setup
    const [twoFACode, setTwoFACode] = useState('');          // Código de confirmación
    const [is2FALoading, setIs2FALoading] = useState(false);

    const handleExtractTemplate = async () => {
        if (!newTemplateName.trim()) return toast.warning("Ingrese un nombre para la plantilla");

        setIsLoading(true);
        try {
            await apiService.post(`/empresas/${user.empresaId}/extract-template`, {
                name: newTemplateName,
                category: "PERSONALIZADO"
            });
            toast.success("Plantilla creada exitosamente. Ya puede usarla al crear nuevas empresas.");
            setTemplateModalOpen(false);
            setNewTemplateName('');
        } catch (error) {
            console.error(error);
            toast.error(error.response?.data?.detail || "Error al crear plantilla");
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        if (user?.empresaId) {
            loadEmpresa();
        }
        if (user?.id) {
            loadUsuario();
        }
    }, [user]);

    const loadUsuario = async () => {
        try {
            const res = await apiService.get('/usuarios/me');
            setUsuarioData({
                whatsapp_number: res.data.whatsapp_number || ''
            });
            // Cargar estado 2FA del usuario actual
            setTwoFAStatus(res.data.totp_enabled || false);
        } catch (error) {
            console.error("Error loading usuario:", error);
        }
    };

    const loadEmpresa = async () => {
        try {
            const res = await apiService.get(`/empresas/${user.empresaId}`);
            setEmpresaData({
                razon_social: res.data.razon_social,
                nit: res.data.nit,
                direccion: res.data.direccion || '',
                telefono: res.data.telefono || '',
                email: res.data.email || '',
                logo_url: res.data.logo_url || ''
            });
        } catch (error) {
            console.error("Error loading empresa:", error);
            toast.error("Error al cargar datos de empresa");
        }
    };

    const handleSaveUsuario = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        try {
            await apiService.put(`/usuarios/${user.id}`, {
                whatsapp_number: usuarioData.whatsapp_number
            });
            toast.success("Perfil personal actualizado correctamente");
        } catch (error) {
            console.error(error);
            toast.error("Error al actualizar perfil personal");
        } finally {
            setIsLoading(false);
        }
    };

    const handleSaveEmpresa = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        try {
            // Solo enviamos los campos editables
            const payload = {
                direccion: empresaData.direccion,
                telefono: empresaData.telefono,
                email: empresaData.email,
                logo_url: empresaData.logo_url
            };

            await apiService.put(`/empresas/${user.empresaId}`, payload);
            toast.success("Información de empresa actualizada");
        } catch (error) {
            console.error(error);
            toast.error("Error al guardar cambios");
        } finally {
            setIsLoading(false);
        }
    };

    const handleChangePassword = async (e) => {
        e.preventDefault();
        if (passData.newPassword !== passData.confirmPassword) {
            return toast.warning("Las nuevas contraseñas no coinciden");
        }
        if (passData.newPassword.length < 6) {
            return toast.warning("La contraseña debe tener al menos 6 caracteres");
        }

        setIsLoading(true);
        try {
            // Usamos endpoint de usuario. Si no existe uno específico de "change-password",
            // intentamos actualizar el usuario actual enviando el password.
            // NOTA: Dependiendo de la implementación del backend, esto puede variar.
            // Asumimos un endpoint standard o autoservicio.
            // Si el backend requiere currentPassword para validación, se enviaría.
            // Por ahora intentaremos PUT /usuarios/{id} con password.

            const payload = {
                password: passData.newPassword
            };

            // Verificamos si update_user en backend soporta password directo
            await apiService.put(`/usuarios/${user.id}`, payload);

            toast.success("Contraseña actualizada correctamente");
            setPassData({ currentPassword: '', newPassword: '', confirmPassword: '' });
        } catch (error) {
            console.error(error);
            toast.error(error.response?.data?.detail || "Error al cambiar contraseña");
        } finally {
            setIsLoading(false);
        }
    };

    // --- Handlers 2FA ---
    const handleStart2FASetup = async () => {
        setIs2FALoading(true);
        try {
            const res = await apiService.get('/auth/setup-2fa');
            setTwoFASetup(res.data);  // { secret, qr_uri }
            setTwoFACode('');
            toast.info('Escanea el código QR con tu app autenticadora.');
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Error al iniciar configuración 2FA');
        } finally {
            setIs2FALoading(false);
        }
    };

    const handleActivate2FA = async (e) => {
        e.preventDefault();
        if (twoFACode.length !== 6) return toast.warning('El código debe tener 6 dígitos.');
        setIs2FALoading(true);
        try {
            await apiService.post('/auth/activate-2fa', { totp_code: twoFACode });
            setTwoFAStatus(true);
            setTwoFASetup(null);
            setTwoFACode('');
            toast.success('✅ Autenticación de dos factores activada correctamente.');
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Código incorrecto. Intenta nuevamente.');
            setTwoFACode('');
        } finally {
            setIs2FALoading(false);
        }
    };

    const handleDisable2FA = async () => {
        if (!confirm('¿Estás seguro de que deseas desactivar el 2FA? Tu cuenta quedará protegida solo con contraseña.')) return;
        setIs2FALoading(true);
        try {
            await apiService.delete('/auth/disable-2fa');
            setTwoFAStatus(false);
            setTwoFASetup(null);
            toast.success('2FA desactivado.');
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Error al desactivar 2FA.');
        } finally {
            setIs2FALoading(false);
        }
    };

    return (
        <div className="p-6 max-w-4xl mx-auto space-y-6">
            <header className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 mb-6">
                <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-3">
                    Configuración General
                </h1>
                <p className="text-gray-500 mt-1">Gestione los datos de su empresa y seguridad de su cuenta.</p>
            </header>

            <div className="flex flex-col md:flex-row gap-6">
                {/* Sidebar Tabs */}
                <div className="md:w-64 flex flex-col gap-2">
                    <button
                        onClick={() => setActiveTab('empresa')}
                        className={`text-left px-4 py-3 rounded-lg font-medium flex items-center gap-3 transition-colors ${activeTab === 'empresa' ? 'bg-indigo-50 text-indigo-700' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
                    >
                        <FaBuilding /> Datos Empresa
                    </button>
                    <button
                        onClick={() => setActiveTab('usuario')}
                        className={`text-left px-4 py-3 rounded-lg font-medium flex items-center gap-3 transition-colors ${activeTab === 'usuario' ? 'bg-indigo-50 text-indigo-700' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
                    >
                        <FaUser /> Perfil Personal
                    </button>
                    <button
                        onClick={() => setActiveTab('seguridad')}
                        className={`text-left px-4 py-3 rounded-lg font-medium flex items-center gap-3 transition-colors ${activeTab === 'seguridad' ? 'bg-indigo-50 text-indigo-700' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
                    >
                        <FaUserLock /> Seguridad
                    </button>
                </div>

                {/* Content Area */}
                <div className="flex-1 bg-white rounded-xl shadow-sm border border-gray-100 p-6 min-h-[400px]">

                    {activeTab === 'empresa' && (
                        <form onSubmit={handleSaveEmpresa} className="space-y-6 animate-fadeIn">
                            <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-4">
                                <div className="flex">
                                    <div className="flex-shrink-0">
                                        <FaExclamationTriangle className="h-5 w-5 text-blue-400" />
                                    </div>
                                    <div className="ml-3">
                                        <p className="text-sm text-blue-700">
                                            La Razón Social y el NIT son datos fiscales que no pueden ser modificados. Contacte a soporte si requiere cambios legales.
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <label className="block text-sm font-bold text-gray-700 mb-1">Razón Social</label>
                                    <input
                                        type="text"
                                        value={empresaData.razon_social}
                                        disabled
                                        className="w-full bg-gray-100 border border-gray-300 rounded-lg px-3 py-2 text-gray-500 cursor-not-allowed"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-bold text-gray-700 mb-1">NIT</label>
                                    <input
                                        type="text"
                                        value={empresaData.nit}
                                        disabled
                                        className="w-full bg-gray-100 border border-gray-300 rounded-lg px-3 py-2 text-gray-500 cursor-not-allowed"
                                    />
                                </div>

                                <div className="col-span-2 border-t pt-4 mt-2">
                                    <label className="block text-sm font-bold text-gray-700 mb-1">Dirección Física</label>
                                    <input
                                        type="text"
                                        value={empresaData.direccion}
                                        onChange={e => setEmpresaData({ ...empresaData, direccion: e.target.value })}
                                        className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                                        placeholder="Ej: Calle 123 # 45 - 67, Of 301"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-bold text-gray-700 mb-1">Teléfono / Celular</label>
                                    <input
                                        type="text"
                                        value={empresaData.telefono}
                                        onChange={e => setEmpresaData({ ...empresaData, telefono: e.target.value })}
                                        className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                                        placeholder="Ej: 300 123 4567"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-bold text-gray-700 mb-1">Correo Electrónico (Contacto)</label>
                                    <input
                                        type="email"
                                        value={empresaData.email}
                                        onChange={e => setEmpresaData({ ...empresaData, email: e.target.value })}
                                        className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                                        placeholder="contacto@suempresa.com"
                                    />
                                </div>
                            </div>

                            <div className="flex justify-between pt-4 border-t">
                                {/* Left Side: Template Action */}
                                <button
                                    type="button"
                                    onClick={() => setTemplateModalOpen(true)}
                                    className="text-indigo-600 hover:text-indigo-800 font-medium text-sm flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-indigo-50 transition-colors"
                                >
                                    <FaBuilding className="text-xs" /> Guardar como Plantilla
                                </button>

                                <button
                                    type="submit"
                                    disabled={isLoading}
                                    className="bg-indigo-600 text-white px-6 py-2 rounded-lg font-bold hover:bg-indigo-700 transition-colors flex items-center gap-2 shadow-sm"
                                >
                                    {isLoading ? 'Guardando...' : <><FaSave /> Guardar Cambios</>}
                                </button>
                            </div>
                        </form>
                    )}

                    {/* Template Name Modal */}
                    {templateModalOpen && (
                        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
                            <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 animate-fadeIn">
                                <h3 className="text-lg font-bold text-gray-800 mb-2">Crear Plantilla Personalizada</h3>
                                <p className="text-sm text-gray-500 mb-4">
                                    Se creará una copia de la configuración de esta empresa (PUC, Impuestos, Tipos de Documento) para usarla en futuras creaciones.
                                </p>

                                <div className="mb-4">
                                    <label className="block text-sm font-bold text-gray-700 mb-1">Nombre de la Plantilla</label>
                                    <input
                                        type="text"
                                        autoFocus
                                        value={newTemplateName}
                                        onChange={(e) => setNewTemplateName(e.target.value)}
                                        placeholder={`Plantilla de ${empresaData.razon_social}`}
                                        className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 outline-none"
                                    />
                                </div>

                                <div className="flex justify-end gap-3">
                                    <button
                                        onClick={() => setTemplateModalOpen(false)}
                                        className="text-gray-500 hover:text-gray-800 font-medium px-4 py-2"
                                    >
                                        Cancelar
                                    </button>
                                    <button
                                        onClick={handleExtractTemplate}
                                        disabled={isLoading}
                                        className="bg-indigo-600 text-white px-4 py-2 rounded-lg font-bold hover:bg-indigo-700 transition-colors"
                                    >
                                        {isLoading ? 'Creando...' : 'Crear Plantilla'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === 'usuario' && (
                        <form onSubmit={handleSaveUsuario} className="space-y-6 max-w-xl animate-fadeIn">
                            <h3 className="text-lg font-bold text-gray-800 border-b pb-2">Perfil Personal y Enlace IA</h3>

                            <div className="bg-indigo-50 border-l-4 border-indigo-500 p-4 mb-4 rounded-r-lg">
                                <p className="text-sm text-indigo-700">
                                    Ingrese su número de celular personal con código de país (Ej: <strong>573001234567</strong>) para autorizar este número a realizar consultas mediante <strong>Inteligencia Artificial por WhatsApp</strong>. Sólo los números almacenados en perfiles activos tendrán acceso al bot de la empresa.
                                </p>
                            </div>

                            <div>
                                <label className="block text-sm font-bold text-gray-700 mb-1 flex justify-between">
                                    <span>Celular Autorizado de WhatsApp</span>
                                    <span className="text-xs font-normal text-gray-500 mt-1">(Sin el símbolo +)</span>
                                </label>
                                <input
                                    type="text"
                                    value={usuarioData.whatsapp_number}
                                    onChange={e => setUsuarioData({ ...usuarioData, whatsapp_number: e.target.value })}
                                    className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-shadow text-gray-800"
                                    placeholder="Ejemplo: 573234259925"
                                />
                                <p className="text-xs text-gray-400 mt-1 pl-1">Asegúrese de agregar el código de área (57 para Colombia).</p>
                            </div>

                            <div className="flex justify-start pt-4 border-t mt-4">
                                <button
                                    type="submit"
                                    disabled={isLoading}
                                    className="bg-indigo-600 text-white px-6 py-2.5 rounded-lg font-bold hover:bg-indigo-700 focus:ring-4 focus:ring-indigo-100 transition-all flex items-center gap-2 shadow hover:shadow-md"
                                >
                                    {isLoading ? 'Guardando...' : <><FaSave /> Guardar Cambios</>}
                                </button>
                            </div>
                        </form>
                    )}

                    {activeTab === 'seguridad' && (
                        <div className="space-y-8 max-w-md animate-fadeIn">

                            {/* ===== SECCIÓN: Cambiar Contraseña ===== */}
                            <form onSubmit={handleChangePassword} className="space-y-4">
                                <h3 className="text-lg font-bold text-gray-800 border-b pb-2">Cambiar Contraseña</h3>

                                <div>
                                    <label className="block text-sm font-bold text-gray-700 mb-1">Nueva Contraseña</label>
                                    <input
                                        type="password"
                                        value={passData.newPassword}
                                        onChange={e => setPassData({ ...passData, newPassword: e.target.value })}
                                        className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 outline-none"
                                        required minLength={6}
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-bold text-gray-700 mb-1">Confirmar Nueva Contraseña</label>
                                    <input
                                        type="password"
                                        value={passData.confirmPassword}
                                        onChange={e => setPassData({ ...passData, confirmPassword: e.target.value })}
                                        className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 outline-none"
                                        required minLength={6}
                                    />
                                </div>

                                <div className="text-sm text-gray-500 bg-gray-50 p-3 rounded">
                                    Nota: Al cambiar su contraseña, es posible que deba iniciar sesión nuevamente en otros dispositivos.
                                </div>

                                <div className="flex justify-start pt-2">
                                    <button
                                        type="submit" disabled={isLoading}
                                        className="bg-gray-800 text-white px-6 py-2 rounded-lg font-bold hover:bg-black transition-colors flex items-center gap-2"
                                    >
                                        {isLoading ? 'Actualizando...' : 'Actualizar Contraseña'}
                                    </button>
                                </div>
                            </form>

                            {/* ===== SECCIÓN: Autenticación de Dos Factores (2FA) ===== */}
                            <div className="border-t pt-6">
                                <h3 className="text-lg font-bold text-gray-800 pb-2 flex items-center gap-2">
                                    <FaShieldAlt className="text-indigo-500" />
                                    Autenticación de Dos Factores (2FA)
                                </h3>

                                {/* Estado: 2FA YA ACTIVO */}
                                {twoFAStatus === true && !twoFASetup && (
                                    <div className="space-y-4">
                                        <div className="flex items-center gap-3 bg-green-50 border border-green-200 rounded-xl p-4">
                                            <FaCheckCircle className="text-green-500 text-xl flex-shrink-0" />
                                            <div>
                                                <p className="font-semibold text-green-800">2FA Activado</p>
                                                <p className="text-sm text-green-600">Tu cuenta requiere el código del autenticador al iniciar sesión.</p>
                                            </div>
                                        </div>
                                        <button
                                            onClick={handleDisable2FA}
                                            disabled={is2FALoading}
                                            className="text-red-600 border border-red-200 hover:bg-red-50 px-4 py-2 rounded-lg text-sm font-semibold flex items-center gap-2 transition-colors"
                                        >
                                            <FaTimesCircle /> {is2FALoading ? 'Desactivando...' : 'Desactivar 2FA'}
                                        </button>
                                    </div>
                                )}

                                {/* Estado: 2FA NO CONFIGURADO */}
                                {twoFAStatus === false && !twoFASetup && (
                                    <div className="space-y-4">
                                        <div className="flex items-center gap-3 bg-amber-50 border border-amber-200 rounded-xl p-4">
                                            <FaShieldAlt className="text-amber-500 text-xl flex-shrink-0" />
                                            <div>
                                                <p className="font-semibold text-amber-800">2FA No configurado</p>
                                                <p className="text-sm text-amber-600">Tu cuenta solo está protegida por contraseña. Se recomienda activar el 2FA.</p>
                                            </div>
                                        </div>
                                        <button
                                            onClick={handleStart2FASetup}
                                            disabled={is2FALoading}
                                            className="bg-indigo-600 text-white px-5 py-2.5 rounded-lg font-bold hover:bg-indigo-700 transition-colors flex items-center gap-2 shadow-sm"
                                        >
                                            <FaQrcode /> {is2FALoading ? 'Generando...' : 'Activar Autenticador'}
                                        </button>
                                    </div>
                                )}

                                {/* Estado: SETUP EN PROCESO — mostrar QR */}
                                {twoFASetup && (
                                    <div className="space-y-5">
                                        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm text-blue-800">
                                            <strong>Instrucciones:</strong>
                                            <ol className="list-decimal list-inside mt-2 space-y-1">
                                                <li>Abre <strong>Google Authenticator</strong>, <strong>Authy</strong> o cualquier app TOTP.</li>
                                                <li>Toca «Añadir cuenta» → «Escanear código QR».</li>
                                                <li>Escanea el código de abajo.</li>
                                                <li>Ingresa el código de 6 dígitos para confirmar.</li>
                                            </ol>
                                        </div>

                                        {/* QR generado con Google Charts API */}
                                        <div className="flex flex-col items-center gap-3">
                                            <div className="bg-white p-3 rounded-xl border-2 border-indigo-200 shadow-sm">
                                                <img
                                                    src={`https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(twoFASetup.qr_uri)}`}
                                                    alt="QR Code para autenticador"
                                                    width={180} height={180}
                                                    className="rounded"
                                                />
                                            </div>
                                            <div className="text-center">
                                                <p className="text-xs text-gray-500 mb-1">¿No puedes escanear? Ingresa este código manualmente:</p>
                                                <code className="text-xs font-mono bg-gray-100 px-3 py-1.5 rounded-lg text-gray-700 break-all select-all">
                                                    {twoFASetup.secret}
                                                </code>
                                            </div>
                                        </div>

                                        {/* Confirmación con código */}
                                        <form onSubmit={handleActivate2FA} className="space-y-3">
                                            <label className="block text-sm font-bold text-gray-700">Confirmar con el código de 6 dígitos</label>
                                            <input
                                                type="text"
                                                inputMode="numeric"
                                                maxLength={6}
                                                autoComplete="one-time-code"
                                                value={twoFACode}
                                                onChange={e => setTwoFACode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                                                className="w-full border-2 border-indigo-300 rounded-xl px-4 py-3 text-center text-2xl font-mono tracking-[0.4em] focus:ring-2 focus:ring-indigo-500 outline-none"
                                                placeholder="000000"
                                            />
                                            <div className="flex gap-3">
                                                <button
                                                    type="button"
                                                    onClick={() => { setTwoFASetup(null); setTwoFACode(''); }}
                                                    className="flex-1 py-2 border border-gray-300 rounded-lg text-sm font-semibold text-gray-600 hover:bg-gray-50 transition-colors"
                                                >
                                                    Cancelar
                                                </button>
                                                <button
                                                    type="submit"
                                                    disabled={is2FALoading || twoFACode.length !== 6}
                                                    className="flex-1 py-2 bg-indigo-600 text-white rounded-lg text-sm font-bold hover:bg-indigo-700 transition-colors disabled:opacity-50"
                                                >
                                                    {is2FALoading ? 'Activando...' : '✓ Activar 2FA'}
                                                </button>
                                            </div>
                                        </form>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}


                </div>
            </div>
        </div>
    );
}
