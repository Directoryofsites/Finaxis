import React, { useState } from 'react';
import {
    User, CreditCard, MessageSquare, LogOut,
    AlertCircle, CheckCircle2, Clock, Send, Loader2
} from 'lucide-react';
import { handleLogin, fetchAccountStatus, submitPQR } from '../lib/api';

const CustomerPortalWidget = () => {
    // Auth State
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(null);

    // Navigation State (login, dashboard, pqr)
    const [currentView, setCurrentView] = useState('login');

    // Data State
    const [accountData, setAccountData] = useState({ total_adeudado: 0, facturas: [] });
    const [isLoading, setIsLoading] = useState(false);
    const [errorMsg, setErrorMsg] = useState('');

    const loadDashboardData = async (userId) => {
        setIsLoading(true);
        setErrorMsg('');
        try {
            const data = await fetchAccountStatus(userId);
            setAccountData(data);
        } catch (err) {
            setErrorMsg("Error cargando el estado de cartera");
        } finally {
            setIsLoading(false);
        }
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
            <header className="bg-brand-900 text-white shadow-md relative z-10 w-full py-4 px-6 md:px-12 flex justify-between items-center">
                <div>
                    <h2 className="text-2xl md:text-3xl font-extrabold tracking-wider">FINAXIS</h2>
                    <p className="text-brand-100 text-xs md:text-sm font-medium tracking-wide">Portal de Autogestión de Clientes</p>
                </div>
                {user && (
                    <button
                        onClick={onLogout}
                        className="flex items-center gap-2 bg-brand-800 hover:bg-red-600 text-white px-4 py-2 rounded-xl transition-all shadow-sm text-sm font-semibold"
                    >
                        <LogOut size={16} />
                        <span className="hidden sm:inline">Cerrar Sesión</span>
                    </button>
                )}
            </header>

            {/* Main Content Area */}
            <main className="flex-1 w-full max-w-4xl mx-auto p-4 sm:p-6 md:p-8">

                {/* Banner de Mensajes de Error Generales */}
                {errorMsg && (
                    <div className="bg-red-50 text-red-700 border border-red-200 rounded-xl p-4 mb-6 flex items-start space-x-3 shadow-sm animate-in fade-in slide-in-from-top-4">
                        <AlertCircle className="flex-shrink-0 w-5 h-5 mt-0.5" />
                        <p className="text-sm font-medium">{errorMsg}</p>
                    </div>
                )}

                {/* View Routing */}
                <div className="bg-white rounded-3xl shadow-xl shadow-brand-900/5 border border-gray-100 overflow-hidden min-h-[500px] flex flex-col relative">

                    <div className="flex-1 p-6 sm:p-10">
                        {currentView === 'login' && (
                            <LoginView
                                setUser={setUser}
                                setToken={setToken}
                                setCurrentView={setCurrentView}
                                setErrorMsg={setErrorMsg}
                                loadDashboardData={loadDashboardData}
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
                <p>© 2026 Plataforma FINAXIS. Sistema seguro de verificación vía Documento.</p>
            </footer>
        </div>
    );
};

// --- SUBVIEWS ---

// 1. Login View (Refactorizado para NIT/Cédula)
const LoginView = ({ setUser, setToken, setCurrentView, setErrorMsg, loadDashboardData }) => {
    const [email, setEmail] = useState('');
    const [documento, setDocumento] = useState('');
    const [loading, setLoading] = useState(false);

    const onSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setErrorMsg('');
        try {
            const resp = await handleLogin(email, documento);
            setUser(resp.usuario);
            setToken(resp.token);
            setCurrentView('dashboard');
            loadDashboardData(resp.usuario.id);
        } catch (err) {
            setErrorMsg(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full items-center justify-center animate-in fade-in zoom-in-95 duration-500">
            <div className="w-full max-w-md">
                <div className="w-20 h-20 bg-brand-50 rounded-[2rem] flex items-center justify-center mx-auto mb-8 text-brand-600 shadow-inner">
                    <User size={40} />
                </div>
                <h3 className="text-2xl font-bold text-center text-gray-900 mb-2">Acceso a Clientes</h3>
                <p className="text-gray-500 text-center text-sm md:text-base mb-10">
                    Ingresa con tu correo y Número de Cédula o NIT para consultar tu estado de cuenta.
                </p>

                <form onSubmit={onSubmit} className="space-y-6">
                    <div>
                        <label className="block text-sm font-bold text-gray-700 mb-2">Correo Electrónico</label>
                        <input
                            type="email"
                            required
                            className="w-full px-5 py-4 rounded-xl border border-gray-200 focus:ring-4 focus:ring-brand-500/20 focus:border-brand-500 outline-none transition-all text-base bg-gray-50 focus:bg-white"
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
                            className="w-full px-5 py-4 rounded-xl border border-gray-200 focus:ring-4 focus:ring-brand-500/20 focus:border-brand-500 outline-none transition-all text-base bg-gray-50 focus:bg-white tracking-widest"
                            placeholder="Ej: 900123456"
                            value={documento}
                            onChange={e => setDocumento(e.target.value)}
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-brand-600 hover:bg-brand-700 text-white font-bold py-4 rounded-xl transition-all shadow-lg hover:shadow-brand-500/30 flex justify-center items-center mt-6 text-lg disabled:opacity-70"
                    >
                        {loading ? <Loader2 className="animate-spin w-6 h-6" /> : 'Ver mi Estado de Cuenta'}
                    </button>
                </form>

                <div className="mt-10 pt-8 border-t border-gray-100 text-xs text-center">
                    <p className="text-gray-400 mb-2">Terceros de Prueba (Sandbox):</p>
                    <div className="flex flex-col gap-2 mx-auto max-w-xs">
                        <span className="bg-gray-50 px-3 py-2 rounded-lg text-gray-600 font-mono">comercial@test.com / NIT: 123456789</span>
                        <span className="bg-gray-50 px-3 py-2 rounded-lg text-gray-600 font-mono">apto500@test.com / CC: 987654321</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

// 2. Dashboard View
const DashboardView = ({ user, accountData, isLoading }) => {
    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center h-full space-y-4">
                <Loader2 className="w-12 h-12 text-brand-500 animate-spin" />
                <p className="text-gray-500 font-medium text-lg">Sincronizando con ERP...</p>
            </div>
        );
    }

    const formatMoney = (amount) => {
        return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(amount);
    };

    const getStatusBadge = (status) => {
        switch (status) {
            case 'al_dia':
                return <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-sm"><CheckCircle2 size={14} /> Al día</span>;
            case 'vence_pronto':
                return <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider bg-amber-50 text-amber-700 border border-amber-200 shadow-sm"><Clock size={14} /> Vence Pronto</span>;
            case 'vencido':
                return <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider bg-rose-50 text-rose-700 border border-rose-200 shadow-sm"><AlertCircle size={14} /> Vencido</span>;
            default:
                return null;
        }
    };

    return (
        <div className="animate-in slide-in-from-bottom-8 duration-500 h-full flex flex-col">
            <div className="mb-8 flex justify-between items-end">
                <div>
                    <h3 className="text-2xl md:text-3xl font-bold text-gray-900 mb-1">Hola, {user.nombre}</h3>
                    <p className="text-base text-gray-500">Has accedido como: <span className="font-semibold">{user.perfil}</span></p>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                {/* Tarjeta Resumen Gigante */}
                <div className="md:col-span-1 bg-gradient-to-br from-brand-600 to-brand-900 rounded-3xl shadow-xl p-8 text-white relative overflow-hidden flex flex-col justify-center min-h-[200px]">
                    {/* Decoración gráfica */}
                    <div className="absolute -right-10 -top-10 w-40 h-40 bg-white/10 rounded-full blur-2xl"></div>
                    <div className="absolute -left-10 -bottom-10 w-32 h-32 bg-brand-400/20 rounded-full blur-xl"></div>

                    <p className="text-brand-100 text-base font-medium mb-2 relative z-10 flex items-center gap-2">
                        <CreditCard className="w-5 h-5 opacity-80" /> Total Adeudado
                    </p>
                    <h4 className="text-4xl lg:text-5xl font-extrabold tracking-tight relative z-10">{formatMoney(accountData.total_adeudado || 0)}</h4>
                </div>

                {/* Lista de Facturas */}
                <div className="md:col-span-2 flex flex-col">
                    <h4 className="font-bold text-gray-800 text-lg mb-5 flex items-center justify-between border-b border-gray-100 pb-3">
                        <span>Detalle de Obligaciones</span>
                        <span className="text-sm bg-gray-100 px-3 py-1 rounded-full text-gray-600 font-bold">{accountData.facturas?.length || 0} recibos</span>
                    </h4>

                    <div className="space-y-4 flex-1 overflow-y-auto pr-2 custom-scrollbar">
                        {(!accountData.facturas || accountData.facturas.length === 0) ? (
                            <div className="flex flex-col items-center justify-center p-12 bg-gray-50 rounded-2xl border border-gray-100 border-dashed h-full">
                                <CheckCircle2 className="w-16 h-16 text-gray-300 mb-4" />
                                <p className="text-gray-500 font-medium">Usted se encuentra a paz y salvo.</p>
                            </div>
                        ) : (
                            accountData.facturas.map((factura) => (
                                <div key={factura.id} className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 hover:shadow-md hover:border-brand-200 transition-all group flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                                    <div className="flex-1">
                                        <span className="block text-base font-bold text-gray-900 mb-1 group-hover:text-brand-600 transition-colors">{factura.concepto}</span>
                                        <div className="text-sm text-gray-500 flex items-center gap-1.5 font-medium">
                                            <Clock size={14} className="text-gray-400" />
                                            Vence: <span className="text-gray-700">{factura.fecha_vencimiento}</span>
                                        </div>
                                    </div>
                                    <div className="flex sm:flex-col items-center sm:items-end justify-between sm:justify-center gap-2">
                                        <span className="text-xl font-extrabold text-gray-900">{formatMoney(factura.monto)}</span>
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

// 3. PQR / Soporte View
const PQRView = ({ setCurrentView, setErrorMsg }) => {
    const [formData, setFormData] = useState({ asunto: '', tipo: 'peticion', mensaje: '' });
    const [loading, setLoading] = useState(false);
    const [successMsg, setSuccessMsg] = useState('');

    const onSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setErrorMsg('');
        setSuccessMsg('');

        try {
            const resp = await submitPQR(formData);
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
                                className="w-full px-4 py-3.5 rounded-xl border border-gray-200 focus:ring-4 focus:ring-brand-500/20 outline-none text-base bg-gray-50 focus:bg-white cursor-pointer"
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
                                className="w-full px-4 py-3.5 rounded-xl border border-gray-200 focus:ring-4 focus:ring-brand-500/20 outline-none text-base bg-gray-50 focus:bg-white transition-colors"
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
                            className="w-full px-4 py-3.5 rounded-xl border border-gray-200 focus:ring-4 focus:ring-brand-500/20 outline-none text-base bg-gray-50 focus:bg-white transition-colors resize-none"
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

// UI Helper
const NavButton = ({ icon, label, active, onClick }) => {
    return (
        <button
            onClick={onClick}
            className={`flex items-center gap-2.5 px-6 py-3 rounded-xl transition-all duration-300 font-bold text-sm
        ${active
                    ? 'text-brand-700 bg-brand-100 shadow-sm'
                    : 'text-gray-500 hover:bg-gray-100 hover:text-gray-800'
                }
      `}
        >
            <div className={`transition-transform ${active ? 'scale-110' : ''}`}>{icon}</div>
            <span>{label}</span>
        </button>
    );
};

export default CustomerPortalWidget;
