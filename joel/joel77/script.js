import React, { useState, useEffect } from 'react';
import {
    X, Menu, User, CreditCard, MessageSquare, LogOut,
    AlertCircle, CheckCircle2, Clock, Send, Loader2
} from 'lucide-react';

// =========================================================================
// CAPA DE DATOS (SERVICIOS Y CONEXIONES API)
// =========================================================================
// IMPORTANTE: Para la integración real con el software FINAXIS del tío, 
// reemplazar esta URL con la ruta de su servidor real de Base de Datos.
const API_BASE_URL = "http://127.0.0.1:8000";

export async function handleLogin(email, password) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password }),
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Error de autenticación");
        }
        return await response.json();
    } catch (error) {
        console.error("Error en handleLogin:", error);
        throw error;
    }
}

export async function fetchAccountStatus(userId) {
    try {
        const response = await fetch(`${API_BASE_URL}/cuenta/estado/${userId}`);
        if (!response.ok) throw new Error("Error obteniendo el estado de cuenta");
        return await response.json();
    } catch (error) {
        console.error("Error en fetchAccountStatus:", error);
        throw error;
    }
}

export async function submitPQR(pqrData) {
    try {
        const response = await fetch(`${API_BASE_URL}/solicitudes/nueva`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(pqrData),
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Error enviando la solicitud");
        }
        return await response.json();
    } catch (error) {
        console.error("Error en submitPQR:", error);
        throw error;
    }
}

// =========================================================================
// CAPA VISUAL (INTERFAZ DE USUARIO Y LÓGICA DEL PORTAL)
// =========================================================================

export const CustomerPortalWidget = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [isAnimating, setIsAnimating] = useState(false);

    // Auth State
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(null);

    // Navigation State (login, dashboard, pqr)
    const [currentView, setCurrentView] = useState('login');

    // Data State
    const [accountData, setAccountData] = useState({ total_adeudado: 0, facturas: [] });
    const [isLoading, setIsLoading] = useState(false);
    const [errorMsg, setErrorMsg] = useState('');

    // Handle Drawer Open/Close with Animation
    const toggleDrawer = () => {
        if (isOpen) {
            setIsAnimating(true);
            setTimeout(() => {
                setIsOpen(false);
                setIsAnimating(false);
            }, 300); // match transition duration
        } else {
            setIsOpen(true);
            // Reset view to dashboard if logged in
            if (user) {
                setCurrentView('dashboard');
                loadDashboardData(user.id);
            } else {
                setCurrentView('login');
            }
        }
    };

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
        <>
            {/* Botón Flotante (Launcher) */}
            <button
                onClick={toggleDrawer}
                className={`fixed bottom-6 right-6 z-50 rounded-full p-4 shadow-xl transition-all duration-300 transform hover:scale-105 hover:shadow-2xl flex items-center justify-center
            ${isOpen ? 'bg-gray-800 text-white rotate-90' : 'bg-brand-600 text-white'}`}
            >
                {isOpen ? <X size={28} /> : <MessageSquare size={28} className="animate-pulse" />}
            </button>

            {/* Backdrop (Blur) */}
            {(isOpen || isAnimating) && (
                <div
                    className={`fixed inset-0 bg-gray-900/30 backdrop-blur-sm z-40 transition-opacity duration-300 
              ${isOpen && !isAnimating ? 'opacity-100' : 'opacity-0'}`}
                    onClick={toggleDrawer}
                />
            )}

            {/* Drawer */}
            <div
                className={`fixed inset-y-0 right-0 z-50 w-full sm:w-[450px] bg-white shadow-2xl flex flex-col transition-transform duration-300 ease-in-out transform 
            ${isOpen && !isAnimating ? 'translate-x-0' : 'translate-x-full'}`}
            >
                {/* Header */}
                <div className="bg-brand-900 text-white p-6 rounded-bl-3xl shadow-md z-10">
                    <div className="flex justify-between items-center mb-2">
                        <h2 className="text-2xl font-bold tracking-wider">FINAXIS</h2>
                        <button onClick={toggleDrawer} className="text-white/80 hover:text-white transition-colors">
                            <X size={24} />
                        </button>
                    </div>
                    <p className="text-brand-100 text-sm font-medium">Portal de Autogestión</p>
                </div>

                {/* Content Area */}
                <div className="flex-1 overflow-y-auto bg-gray-50/50 p-6">
                    {errorMsg && (
                        <div className="bg-red-50 text-red-700 border border-red-200 rounded-xl p-4 mb-6 flex items-start space-x-3 shadow-sm animate-in fade-in slide-in-from-top-4">
                            <AlertCircle className="flex-shrink-0 w-5 h-5 mt-0.5" />
                            <p className="text-sm font-medium">{errorMsg}</p>
                        </div>
                    )}

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
                    <div className="bg-white border-t border-gray-100 p-4 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)] z-10 flex justify-around">
                        <NavButton
                            icon={<CreditCard />}
                            label="Cartera"
                            active={currentView === 'dashboard'}
                            onClick={() => setCurrentView('dashboard')}
                        />
                        <NavButton
                            icon={<MessageSquare />}
                            label="Soporte"
                            active={currentView === 'pqr'}
                            onClick={() => setCurrentView('pqr')}
                        />
                        <NavButton
                            icon={<LogOut />}
                            label="Salir"
                            active={false}
                            onClick={onLogout}
                            danger
                        />
                    </div>
                )}
            </div>
        </>
    );
};

// -------------------------------------------------------------------------
// FUNCIONES Y SUB-VISTAS INTERNAS (DEPENDENCIAS DEL PORTAL)
// -------------------------------------------------------------------------

const LoginView = ({ setUser, setToken, setCurrentView, setErrorMsg, loadDashboardData }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);

    const onSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setErrorMsg('');
        try {
            const resp = await handleLogin(email, password);
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
        <div className="flex flex-col h-full justify-center pb-12 animate-in fade-in zoom-in-95 duration-300">
            <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
                <div className="w-16 h-16 bg-brand-50 rounded-full flex items-center justify-center mx-auto mb-6 text-brand-600">
                    <User size={32} />
                </div>
                <h3 className="text-xl font-bold text-center text-gray-800 mb-2">Bienvenido de nuevo</h3>
                <p className="text-gray-500 text-center text-sm mb-8">Ingresa tus credenciales para acceder</p>

                <form onSubmit={onSubmit} className="space-y-5">
                    <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-1.5">Correo Electrónico</label>
                        <input
                            type="email"
                            required
                            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition-all text-sm bg-gray-50 focus:bg-white"
                            placeholder="usuario@ejemplo.com"
                            value={email}
                            onChange={e => setEmail(e.target.value)}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-1.5">Contraseña</label>
                        <input
                            type="password"
                            required
                            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition-all text-sm bg-gray-50 focus:bg-white"
                            placeholder="••••••••"
                            value={password}
                            onChange={e => setPassword(e.target.value)}
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-brand-600 hover:bg-brand-700 text-white font-medium py-3 rounded-xl transition-all shadow-md hover:shadow-lg flex justify-center items-center mt-4 disabled:opacity-70"
                    >
                        {loading ? <Loader2 className="animate-spin w-5 h-5" /> : 'Ingresar al Portal'}
                    </button>
                </form>
            </div>
        </div>
    );
};

const DashboardView = ({ user, accountData, isLoading }) => {
    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center h-48 space-y-4">
                <Loader2 className="w-10 h-10 text-brand-500 animate-spin" />
                <p className="text-gray-500 font-medium">Sincronizando sus datos...</p>
            </div>
        );
    }

    const formatMoney = (amount) => {
        return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(amount);
    };

    const getStatusBadge = (status) => {
        switch (status) {
            case 'al_dia':
                return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200"><CheckCircle2 size={12} /> Al día</span>;
            case 'vence_pronto':
                return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200"><Clock size={12} /> Vence Pronto</span>;
            case 'vencido':
                return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200"><AlertCircle size={12} /> Vencido</span>;
            default:
                return null;
        }
    };

    return (
        <div className="animate-in slide-in-from-right-8 duration-300">
            <div className="mb-6">
                <h3 className="text-lg font-bold text-gray-800">Hola, {user.nombre}</h3>
                <p className="text-sm text-gray-500">Perfil: {user.perfil}</p>
            </div>

            {/* Tarjeta Resumen */}
            <div className="bg-gradient-to-br from-brand-600 to-brand-800 rounded-2xl shadow-lg p-6 mb-8 text-white relative overflow-hidden">
                <div className="absolute -right-6 -top-6 w-32 h-32 bg-white/10 rounded-full blur-2xl"></div>
                <div className="absolute -left-6 -bottom-6 w-24 h-24 bg-brand-400/20 rounded-full blur-xl"></div>

                <p className="text-brand-100 text-sm font-medium mb-1 relative z-10">Total Adeudado</p>
                <h4 className="text-3xl font-bold tracking-tight relative z-10">{formatMoney(accountData.total_adeudado || 0)}</h4>
            </div>

            {/* Lista de Facturas */}
            <div>
                <h4 className="font-bold text-gray-800 mb-4 flex items-center justify-between">
                    <span>Detalle de Facturas</span>
                    <span className="text-xs bg-gray-200 px-2 py-1 rounded-full text-gray-600 font-medium">{accountData.facturas?.length || 0}</span>
                </h4>

                <div className="space-y-4">
                    {(!accountData.facturas || accountData.facturas.length === 0) ? (
                        <div className="text-center py-8 bg-white rounded-xl border border-gray-100 border-dashed">
                            <CheckCircle2 className="mx-auto w-10 h-10 text-gray-300 mb-2" />
                            <p className="text-gray-500 text-sm">No tienes facturas pendientes.</p>
                        </div>
                    ) : (
                        accountData.facturas.map((factura) => (
                            <div key={factura.id} className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 hover:shadow-md transition-shadow group">
                                <div className="flex justify-between items-start mb-2">
                                    <span className="text-sm font-semibold text-gray-800 group-hover:text-brand-600 transition-colors line-clamp-1">{factura.concepto}</span>
                                    {getStatusBadge(factura.estado)}
                                </div>
                                <div className="flex justify-between items-end mt-3">
                                    <div className="text-xs text-gray-500 flex items-center gap-1">
                                        <Clock size={12} />
                                        Vence: {factura.fecha_vencimiento}
                                    </div>
                                    <span className="font-bold text-gray-900">{formatMoney(factura.monto)}</span>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};

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
            setTimeout(() => setCurrentView('dashboard'), 3000);
        } catch (err) {
            setErrorMsg(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="animate-in slide-in-from-right-8 duration-300">
            <div className="mb-6">
                <h3 className="text-lg font-bold text-gray-800">Centro de Soporte</h3>
                <p className="text-sm text-gray-500">Envíanos tu Petición, Queja o Reclamo</p>
            </div>

            {successMsg ? (
                <div className="bg-emerald-50 text-emerald-800 p-6 rounded-2xl border border-emerald-100 text-center animate-in zoom-in-95">
                    <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4 text-emerald-600">
                        <CheckCircle2 size={32} />
                    </div>
                    <h4 className="font-bold mb-2">¡Caso Enviado!</h4>
                    <p className="text-sm text-emerald-600 mb-6">{successMsg}</p>
                    <button
                        onClick={() => setCurrentView('dashboard')}
                        className="text-sm font-semibold text-brand-600 hover:text-brand-800 transition-colors"
                    >
                        Volver a Cartera &rarr;
                    </button>
                </div>
            ) : (
                <form onSubmit={onSubmit} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 space-y-4">
                    <div>
                        <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">Tipo de Solicitud</label>
                        <select
                            value={formData.tipo}
                            onChange={e => setFormData({ ...formData, tipo: e.target.value })}
                            className="w-full px-3 py-2.5 rounded-lg border border-gray-200 focus:ring-2 focus:ring-brand-500 outline-none text-sm bg-gray-50 bg-white"
                        >
                            <option value="peticion">Petición</option>
                            <option value="queja">Queja</option>
                            <option value="reclamo">Reclamo</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">Asunto</label>
                        <input
                            type="text"
                            required
                            className="w-full px-3 py-2.5 rounded-lg border border-gray-200 focus:ring-2 focus:ring-brand-500 outline-none text-sm bg-gray-50 focus:bg-white transition-colors"
                            placeholder="Ej. Error en cobro"
                            value={formData.asunto}
                            onChange={e => setFormData({ ...formData, asunto: e.target.value })}
                        />
                    </div>

                    <div>
                        <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">Mensaje</label>
                        <textarea
                            required
                            rows="4"
                            className="w-full px-3 py-2.5 rounded-lg border border-gray-200 focus:ring-2 focus:ring-brand-500 outline-none text-sm bg-gray-50 focus:bg-white transition-colors resize-none"
                            placeholder="Describe detalladamente tu caso..."
                            value={formData.mensaje}
                            onChange={e => setFormData({ ...formData, mensaje: e.target.value })}
                        ></textarea>
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-gray-900 hover:bg-black text-white font-medium py-3 rounded-xl transition-all shadow hover:shadow-md flex justify-center items-center gap-2 mt-4"
                    >
                        {loading ? <Loader2 className="animate-spin w-4 h-4" /> : <Send className="w-4 h-4" />}
                        <span>Enviar Solicitud</span>
                    </button>
                </form>
            )}
        </div>
    );
};

const NavButton = ({ icon, label, active, onClick, danger }) => {
    return (
        <button
            onClick={onClick}
            className={`flex flex-col items-center justify-center p-2 min-w-[64px] rounded-lg transition-all duration-200
          ${active ? 'text-brand-600 bg-brand-50' : 'text-gray-500 hover:bg-gray-50'}
          ${danger ? 'hover:text-red-600 hover:bg-red-50' : ''}
        `}
        >
            <div className={`mb-1 transition-transform ${active ? 'scale-110' : ''}`}>{icon}</div>
            <span className="text-[10px] uppercase tracking-wider font-semibold">{label}</span>
        </button>
    );
};

export default CustomerPortalWidget;
