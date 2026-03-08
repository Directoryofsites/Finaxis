"use client";
import React, { useState } from 'react';
import {
    User, CreditCard, MessageSquare, LogOut,
    AlertCircle, CheckCircle2, Clock, Send, Loader2
} from 'lucide-react';
import { apiService } from '../../lib/apiService';

const CustomerPortalFull = ({ empresaSlug }) => {
    // Auth State
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(null);

    // Navigation State (login, dashboard, pqr)
    const [currentView, setCurrentView] = useState('login');

    // Data State
    const [accountData, setAccountData] = useState({ total_adeudado: 0, facturas: [] });
    const [isLoading, setIsLoading] = useState(false);
    const [errorMsg, setErrorMsg] = useState('');

    const loadDashboardData = async (userToken) => {
        setIsLoading(true);
        setErrorMsg('');
        try {
            // Usando token propio del portal (tercero) en vez del de FINAXIS admin
            const headers = {
                'Authorization': `Bearer ${userToken}`,
                'Content-Type': 'application/json'
            };
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';
            const response = await fetch(`${apiUrl}/api/soporte/cuenta/estado`, { headers });
            if (!response.ok) throw new Error("Error cargando el estado de cartera");
            const data = await response.json();
            setAccountData(data);
        } catch (err) {
            setErrorMsg(err.message || "Error cargando el estado de cartera");
        } finally {
            setIsLoading(false);
        }
    };

    const handleLogin = async (email, documento) => {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';
        const response = await fetch(`${apiUrl}/api/soporte/portal-login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, documento, empresa_slug: empresaSlug }),
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Error en credenciales");
        }
        return await response.json();
    };

    const submitPQR = async (formData, userToken) => {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';
        const response = await fetch(`${apiUrl}/api/soporte/pqr`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${userToken}`
            },
            body: JSON.stringify(formData),
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Error enviando PQR");
        }
        return await response.json();
    };

    const onLogout = () => {
        setUser(null);
        setToken(null);
        setAccountData({ total_adeudado: 0, facturas: [] });
        setCurrentView('login');
    };

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col w-full">
            {/* Header Corporativo Global */}
            <header className="bg-indigo-900 text-white shadow-md relative z-10 w-full py-4 px-6 md:px-12 flex justify-between items-center">
                <div>
                    <h2 className="text-2xl md:text-3xl font-extrabold tracking-wider">FINAXIS</h2>
                    <p className="text-indigo-100 text-xs md:text-sm font-medium tracking-wide">Portal de Autogestión de Clientes</p>
                </div>
                {user && (
                    <button
                        onClick={onLogout}
                        className="flex items-center gap-2 bg-indigo-800 hover:bg-red-600 text-white px-4 py-2 rounded-xl transition-all shadow-sm text-sm font-semibold"
                    >
                        <LogOut size={16} />
                        <span className="hidden sm:inline">Cerrar Sesión</span>
                    </button>
                )}
            </header>

            {/* Main Content Area */}
            <main className="flex-1 w-full max-w-4xl mx-auto p-4 sm:p-6 md:p-8 flex flex-col justify-center">

                {/* Banner de Mensajes de Error Generales */}
                {errorMsg && (
                    <div className="bg-red-50 text-red-700 border border-red-200 rounded-xl p-4 mb-6 flex items-start space-x-3 shadow-sm animate-in fade-in slide-in-from-top-4">
                        <AlertCircle className="flex-shrink-0 w-5 h-5 mt-0.5" />
                        <p className="text-sm font-medium">{errorMsg}</p>
                    </div>
                )}

                {/* View Routing */}
                <div className="bg-white rounded-3xl shadow-xl shadow-indigo-900/5 border border-gray-100 overflow-hidden min-h-[500px] flex flex-col relative w-full">

                    <div className="flex-1 p-6 sm:p-10 flex flex-col justify-center">
                        {currentView === 'login' && (
                            <LoginView
                                setUser={setUser}
                                setToken={setToken}
                                setCurrentView={setCurrentView}
                                setErrorMsg={setErrorMsg}
                                loadDashboardData={loadDashboardData}
                                apiLogin={handleLogin}
                            />
                        )}

                        {currentView === 'dashboard' && user && (
                            <DashboardView
                                user={user}
                                accountData={accountData}
                                isLoading={isLoading}
                                setCurrentView={setCurrentView}
                            />
                        )}

                        {currentView === 'pqr' && user && (
                            <PQRView
                                setCurrentView={setCurrentView}
                                setErrorMsg={setErrorMsg}
                                apiSubmitPQR={(data) => submitPQR(data, token)}
                            />
                        )}
                    </div>

                    {/* Footer Navigation (Solo si está logueado) */}
                    {user && (
                        <div className="bg-gray-50/80 backdrop-blur-md border-t border-gray-100 p-4 shrink-0 flex justify-center gap-4 sm:gap-8">
                            <NavButton
                                icon={<CreditCard size={20} />}
                                label="Estado de Cartera"
                                active={currentView === 'dashboard'}
                                onClick={() => setCurrentView('dashboard')}
                            />
                            <NavButton
                                icon={<MessageSquare size={20} />}
                                label="Buzón de Soporte"
                                active={currentView === 'pqr'}
                                onClick={() => setCurrentView('pqr')}
                            />
                        </div>
                    )}
                </div>

            </main>

            {/* Footer Legal */}
            <footer className="w-full text-center py-6 text-gray-400 text-xs">
                <p>© {new Date().getFullYear()} Plataforma FINAXIS. Sistema seguro de verificación vía Documento.</p>
            </footer>
        </div>
    );
};

// --- SUBVIEWS ---

const LoginView = ({ setUser, setToken, setCurrentView, setErrorMsg, loadDashboardData, apiLogin }) => {
    const [email, setEmail] = useState('');
    const [documento, setDocumento] = useState('');
    const [loading, setLoading] = useState(false);

    const onSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setErrorMsg('');
        try {
            const resp = await apiLogin(email, documento);
            setUser(resp.usuario);
            setToken(resp.access_token);
            setCurrentView('dashboard');
            loadDashboardData(resp.access_token);
        } catch (err) {
            setErrorMsg(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full items-center justify-center animate-in fade-in zoom-in-95 duration-500 w-full max-w-md mx-auto">
            <div className="w-20 h-20 bg-indigo-50 rounded-[2rem] flex items-center justify-center mb-8 text-indigo-600 shadow-inner">
                <User size={40} />
            </div>
            <h3 className="text-2xl font-bold text-center text-gray-900 mb-2">Acceso a Clientes</h3>
            <p className="text-gray-500 text-center text-sm md:text-base mb-10">
                Ingresa con tu correo y Número de Cédula o NIT para consultar tu estado de cuenta.
            </p>

            <form onSubmit={onSubmit} className="space-y-6 w-full">
                <div>
                    <label className="block text-sm font-bold text-gray-700 mb-2">Correo Electrónico</label>
                    <input
                        type="email"
                        required
                        className="w-full px-5 py-4 rounded-xl border border-gray-200 focus:ring-4 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none transition-all text-base bg-gray-50 focus:bg-white"
                        placeholder="correo@empresa.com"
                        value={email}
                        onChange={e => setEmail(e.target.value)}
                    />
                </div>
                <div>
                    <label className="block text-sm font-bold text-gray-700 mb-2">Documento de Identidad (NIT/Cédula)</label>
                    <input
                        type="text"
                        required
                        className="w-full px-5 py-4 rounded-xl border border-gray-200 focus:ring-4 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none transition-all text-base bg-gray-50 focus:bg-white tracking-widest"
                        placeholder="Ej: 900123456"
                        value={documento}
                        onChange={e => setDocumento(e.target.value)}
                    />
                </div>
                <button
                    type="submit"
                    disabled={loading}
                    className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-4 rounded-xl transition-all shadow-lg hover:shadow-indigo-500/30 flex justify-center items-center mt-6 text-lg disabled:opacity-70"
                >
                    {loading ? <Loader2 className="animate-spin w-6 h-6" /> : 'Ver mi Estado de Cuenta'}
                </button>
            </form>
        </div>
    );
};

const DashboardView = ({ user, accountData, isLoading }) => {
    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center h-full space-y-4">
                <Loader2 className="w-12 h-12 text-indigo-500 animate-spin" />
                <p className="text-gray-500 font-medium text-lg">Sincronizando con ERP...</p>
            </div>
        );
    }

    const formatMoney = (amount) => {
        return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(amount);
    };

    const getStatusBadge = (status) => {
        switch (status) {
            case 'Pagada':
                return <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-sm"><CheckCircle2 size={14} /> Pagada</span>;
            case 'vence_pronto':
                return <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider bg-amber-50 text-amber-700 border border-amber-200 shadow-sm"><Clock size={14} /> Vence Pronto</span>;
            case 'Pendiente':
                return <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider bg-rose-50 text-rose-700 border border-rose-200 shadow-sm"><AlertCircle size={14} /> Pendiente</span>;
            default:
                return null;
        }
    };

    return (
        <div className="animate-in slide-in-from-bottom-8 duration-500 h-full flex flex-col">
            <div className="mb-8 flex justify-between items-end">
                <div>
                    <h3 className="text-2xl md:text-3xl font-bold text-gray-900 mb-1">Hola, {user.nombre}</h3>
                    <p className="text-base text-gray-500">Has accedido como: <span className="font-semibold">{user.rol}</span></p>
                </div>
            </div>

            <div className="flex flex-col gap-8 mb-8 flex-1">
                {/* Tarjeta Resumen Horizontal (Banner) */}
                <div className="w-full bg-gradient-to-r from-indigo-800 via-indigo-900 to-black rounded-[2.5rem] shadow-2xl p-8 md:p-12 text-white relative overflow-hidden flex flex-col md:flex-row md:items-center justify-between border-4 border-white/10">
                    <div className="absolute -right-10 -top-10 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl"></div>
                    <div className="absolute left-1/4 -bottom-10 w-48 h-48 bg-indigo-400/5 rounded-full blur-2xl"></div>

                    <div className="relative z-10 flex flex-col mb-6 md:mb-0">
                        <div className="flex items-center gap-3 mb-3">
                            <div className="bg-white/10 p-2 rounded-lg backdrop-blur-sm">
                                <CreditCard className="w-6 h-6 text-indigo-300" />
                            </div>
                            <p className="text-indigo-200 text-sm font-black tracking-widest uppercase">
                                Estado de Cartera
                            </p>
                        </div>
                        <h4 className="text-indigo-100/70 text-base font-medium">Total pendiente por pagar:</h4>
                    </div>

                    <div className="relative z-10 flex flex-col items-start md:items-end">
                        <h4 className="text-4xl md:text-6xl font-black tracking-tighter text-white drop-shadow-2xl">
                            {formatMoney(accountData.total_adeudado || 0)}
                        </h4>
                        <div className="mt-2 text-indigo-300 text-xs font-bold bg-white/5 py-1 px-3 rounded-full border border-white/10">
                            Actualizado en tiempo real
                        </div>
                    </div>
                </div>

                {/* Lista de Facturas */}
                <div className="flex flex-col h-full bg-white rounded-[2rem] p-6 shadow-sm border border-gray-100">
                    <h4 className="font-black text-gray-900 text-xl mb-6 flex items-center justify-between border-b border-gray-50 pb-5">
                        <span>Detalle de Obligaciones</span>
                        <div className="flex items-center gap-2">
                            <span className="text-xs bg-indigo-50 text-indigo-600 px-3 py-1.5 rounded-full font-black uppercase tracking-tighter">
                                {accountData.ultimas_facturas?.length || 0} Documentos
                            </span>
                        </div>
                    </h4>

                    <div className="space-y-4 flex-1 overflow-y-auto pr-2 custom-scrollbar max-h-[600px]">
                        {(!accountData.ultimas_facturas || accountData.ultimas_facturas.length === 0) ? (
                            <div className="flex flex-col items-center justify-center p-20 bg-gray-50/50 rounded-3xl border border-gray-100 border-dashed h-full">
                                <CheckCircle2 className="w-16 h-16 text-emerald-400 mb-4 opacity-50" />
                                <p className="text-gray-400 font-bold text-lg text-center">No tienes deudas pendientes. <br /><span className="text-sm font-medium opacity-70">¡Gracias por ser un cliente cumplido!</span></p>
                            </div>
                        ) : (
                            accountData.ultimas_facturas.map((factura) => (
                                <div key={factura.id} className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-xl hover:border-indigo-100 transition-all duration-300 group flex flex-col sm:flex-row sm:items-center justify-between gap-6">
                                    <div className="flex items-center gap-5">
                                        <div className="w-12 h-12 bg-gray-50 rounded-2xl flex items-center justify-center text-gray-400 group-hover:bg-indigo-50 group-hover:text-indigo-600 transition-colors">
                                            <CreditCard size={24} />
                                        </div>
                                        <div>
                                            <span className="block text-lg font-black text-gray-900 mb-1 group-hover:text-indigo-700 transition-colors tracking-tight">
                                                Factura {factura.referencia}
                                            </span>
                                            <div className="text-sm text-gray-400 flex items-center gap-2 font-bold">
                                                <Clock size={14} />
                                                Emitida el <span className="text-gray-600">{factura.fecha}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="flex sm:flex-col items-center sm:items-end justify-between sm:justify-center gap-3">
                                        <span className="text-2xl font-black text-gray-900 tabular-nums">{formatMoney(factura.monto)}</span>
                                        {getStatusBadge(factura.estado)}
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

const PQRView = ({ setCurrentView, setErrorMsg, apiSubmitPQR }) => {
    const [formData, setFormData] = useState({ asunto: '', tipo: 'peticion', mensaje: '' });
    const [loading, setLoading] = useState(false);
    const [successMsg, setSuccessMsg] = useState('');

    const onSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setErrorMsg('');
        setSuccessMsg('');

        try {
            const resp = await apiSubmitPQR(formData);
            setSuccessMsg(resp.mensaje);
            setFormData({ asunto: '', tipo: 'peticion', mensaje: '' });
            setTimeout(() => setCurrentView('dashboard'), 4000);
        } catch (err) {
            setErrorMsg(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-2xl mx-auto animate-in fade-in zoom-in-95 duration-500 h-full flex flex-col justify-center">
            <div className="mb-8 text-center">
                <h3 className="text-2xl md:text-3xl font-extrabold text-gray-900 mb-2">Centro de Soporte</h3>
                <p className="text-base text-gray-500">Radica tus Peticiones, Quejas o Reclamos asociados a tu cuenta.</p>
            </div>

            {successMsg ? (
                <div className="bg-emerald-50 text-emerald-800 p-8 sm:p-12 rounded-3xl border border-emerald-100 text-center shadow-lg shadow-emerald-900/5 animate-in slide-in-from-bottom-4">
                    <div className="w-20 h-20 bg-emerald-100 rounded-[2rem] flex items-center justify-center mx-auto mb-6 text-emerald-600 shadow-inner">
                        <CheckCircle2 size={40} />
                    </div>
                    <h4 className="text-2xl font-extrabold mb-3">¡Ticket Radicado con Éxito!</h4>
                    <p className="text-base text-emerald-700/80 mb-8 max-w-sm mx-auto">{successMsg}</p>
                    <button
                        onClick={() => setCurrentView('dashboard')}
                        className="w-full sm:w-auto px-8 bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-4 rounded-xl transition-all shadow-md"
                    >
                        Regresar a Detalles de Facturas
                    </button>
                </div>
            ) : (
                <form onSubmit={onSubmit} className="bg-white rounded-3xl shadow-sm border border-gray-100 p-6 sm:p-8 space-y-6">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                        <div className="sm:col-span-1">
                            <label className="block text-sm font-bold text-gray-700 mb-2">Tipo de Solicitud</label>
                            <select
                                value={formData.tipo}
                                onChange={e => setFormData({ ...formData, tipo: e.target.value })}
                                className="w-full px-4 py-3.5 rounded-xl border border-gray-200 focus:ring-4 focus:ring-indigo-500/20 outline-none text-base bg-gray-50 focus:bg-white cursor-pointer"
                            >
                                <option value="peticion">Petición Formal</option>
                                <option value="queja">Queja sobre el Servicio</option>
                                <option value="reclamo">Reclamo de Facturación</option>
                            </select>
                        </div>

                        <div className="sm:col-span-1">
                            <label className="block text-sm font-bold text-gray-700 mb-2">Asunto Principal</label>
                            <input
                                type="text"
                                required
                                className="w-full px-4 py-3.5 rounded-xl border border-gray-200 focus:ring-4 focus:ring-indigo-500/20 outline-none text-base bg-gray-50 focus:bg-white transition-colors"
                                placeholder="Ej. Cobro doble en factura"
                                value={formData.asunto}
                                onChange={e => setFormData({ ...formData, asunto: e.target.value })}
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-bold text-gray-700 mb-2">Detalles del Caso</label>
                        <textarea
                            required
                            rows="5"
                            className="w-full px-4 py-3.5 rounded-xl border border-gray-200 focus:ring-4 focus:ring-indigo-500/20 outline-none text-base bg-gray-50 focus:bg-white transition-colors resize-none"
                            placeholder="Describe detalladamente los motivos de tu solicitud para que nuestro equipo pueda ayudarte rápidamente..."
                            value={formData.mensaje}
                            onChange={e => setFormData({ ...formData, mensaje: e.target.value })}
                        ></textarea>
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-gray-900 hover:bg-black text-white font-bold py-4 rounded-xl transition-all shadow hover:shadow-lg flex justify-center items-center gap-3 text-lg"
                    >
                        {loading ? <Loader2 className="animate-spin w-5 h-5" /> : <Send className="w-5 h-5" />}
                        <span>Radicar Solicitud Oficial</span>
                    </button>
                </form>
            )}
        </div>
    );
};

const NavButton = ({ icon, label, active, onClick }) => {
    return (
        <button
            onClick={onClick}
            className={`flex items-center gap-2.5 px-6 py-3 rounded-xl transition-all duration-300 font-bold text-sm
        ${active
                    ? 'text-indigo-700 bg-indigo-100 shadow-sm'
                    : 'text-gray-500 hover:bg-gray-100 hover:text-gray-800'
                }
      `}
        >
            <div className={`transition-transform ${active ? 'scale-110' : ''}`}>{icon}</div>
            <span>{label}</span>
        </button>
    );
};

export default CustomerPortalFull;
