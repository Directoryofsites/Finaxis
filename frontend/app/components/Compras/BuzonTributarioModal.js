import React, { useState, useEffect } from 'react';
import { FaInbox, FaSpinner, FaTimes, FaCheckCircle, FaLock, FaEnvelope } from 'react-icons/fa';
import { apiService } from '../../../lib/apiService';
import { toast } from 'react-toastify';

export default function BuzonTributarioModal({ isOpen, onClose }) {
    const [email, setEmail] = useState('iglesiaibgv5@gmail.com');
    const [password, setPassword] = useState('');
    const [tipoDocumentoId, setTipoDocumentoId] = useState('');
    const [cuentaGastoId, setCuentaGastoId] = useState('');
    const [cuentaCajaId, setCuentaCajaId] = useState('');

    const [tiposDocumentos, setTiposDocumentos] = useState([]);
    const [cuentasGasto, setCuentasGasto] = useState([]);
    const [cuentasCaja, setCuentasCaja] = useState([]);

    const [isLoading, setIsLoading] = useState(false);
    const [loadingData, setLoadingData] = useState(false);

    useEffect(() => {
        if (isOpen) {
            fetchData();
        }
    }, [isOpen]);

    const fetchData = async () => {
        setLoadingData(true);
        try {
            const [tdRes, cRes] = await Promise.all([
                apiService.get('/tipos-documento'),
                apiService.get('/plan-cuentas/list-flat?permite_movimiento=true')
            ]);

            // Tipos de Documento: Solo Compras / Documento Soporte
            const filtrados = (tdRes.data || []).filter(t => t.funcion_especial === 'cxp_proveedor' || t.funcion_especial === 'documento_soporte');
            setTiposDocumentos(filtrados);
            if (filtrados.length > 0) setTipoDocumentoId(String(filtrados[0].id));

            // Cuentas: Gasto (5) / Caja (11)
            const fl = cRes.data || [];
            setCuentasGasto(fl.filter(c => c.codigo.startsWith('5') || c.codigo.startsWith('6') || c.codigo.startsWith('7')));
            setCuentasCaja(fl.filter(c => c.codigo.startsWith('11') || c.codigo.startsWith('23'))); // Bancos o pasivos de pago

        } catch (error) {
            console.error(error);
            toast.error("Error al cargar configuración para buzón.");
        } finally {
            setLoadingData(false);
        }
    };

    const handleSync = async (e) => {
        e.preventDefault();
        if (!email || !password || !tipoDocumentoId || !cuentaGastoId || !cuentaCajaId) {
            return toast.warning("Debe llenar todos los campos.");
        }

        setIsLoading(true);
        try {
            const payload = {
                email_addr: email,
                password: password,
                tipo_documento_id: parseInt(tipoDocumentoId),
                cuenta_gasto_id: parseInt(cuentaGastoId),
                cuenta_caja_id: parseInt(cuentaCajaId)
            };

            const res = await apiService.post('/buzon-tributario/sincronizar', payload);

            toast.success(`¡Sincronización Exitosa! ${res.data.procesadas} facturas importadas.`);

            // Clean pass for security (if needed) but keep email
            setPassword('');
            onClose();

        } catch (error) {
            console.error("Error al sincronizar buzón:", error);
            const msg = error.response?.data?.detail || "Error en el servidor al leer el correo.";
            toast.error(msg);
        } finally {
            setIsLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[9999] flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg overflow-hidden animate-zoomIn flex flex-col">
                <div className="bg-indigo-600 px-6 py-4 flex justify-between items-center text-white shrink-0">
                    <h2 className="text-xl font-bold flex items-center gap-3">
                        <FaInbox className="text-2xl opacity-80" />
                        Escanear Buzón Tributario
                    </h2>
                    <button onClick={onClose} className="text-white hover:text-indigo-200 focus:outline-none transition-colors">
                        <FaTimes className="text-xl" />
                    </button>
                </div>

                <div className="p-6 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 120px)' }}>
                    {loadingData ? (
                        <div className="flex justify-center p-8 text-indigo-500">
                            <FaSpinner className="animate-spin text-4xl" />
                        </div>
                    ) : (
                        <form id="buzonForm" onSubmit={handleSync} className="space-y-4">
                            <p className="text-sm text-gray-500 mb-4 bg-indigo-50 p-3 rounded-lg border border-indigo-100">
                                Finaxis leerá tu correo en busca de XML de facturas electrónicas (.zip o .xml) de proveedores y las contabilizará como Borrador Automáticamente.
                            </p>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="col-span-2">
                                    <label className="block text-xs font-bold text-gray-600 uppercase mb-1">Correo de Recepción</label>
                                    <div className="relative">
                                        <FaEnvelope className="absolute left-3 top-3 text-gray-400" />
                                        <input type="email" value={email} onChange={e => setEmail(e.target.value)} required className="w-full pl-10 pr-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500" />
                                    </div>
                                </div>
                                <div className="col-span-2">
                                    <label className="block text-xs font-bold text-gray-600 uppercase mb-1">Clave de Aplicación (Gmail)</label>
                                    <div className="relative">
                                        <FaLock className="absolute left-3 top-3 text-gray-400" />
                                        <input type="password" value={password} onChange={e => setPassword(e.target.value)} required placeholder="ej: dscq zies jsrh oxiy" className="w-full pl-10 pr-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500" />
                                    </div>
                                </div>

                                <div className="col-span-2 mt-4 border-t pt-4">
                                    <h4 className="font-bold text-gray-700 mb-2">Configuración Contable por Defecto</h4>
                                </div>

                                <div className="col-span-2">
                                    <label className="block text-xs font-bold text-gray-600 uppercase mb-1">Tipo de Documento</label>
                                    <select value={tipoDocumentoId} onChange={e => setTipoDocumentoId(e.target.value)} required className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 bg-white">
                                        <option value="">Seleccione...</option>
                                        {tiposDocumentos.map(t => <option key={t.id} value={t.id}>{t.nombre}</option>)}
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-xs font-bold text-gray-600 uppercase mb-1" title="Se usará si el proveedor no tiene una paramatrizada">Cuenta Gasto Base</label>
                                    <select value={cuentaGastoId} onChange={e => setCuentaGastoId(e.target.value)} required className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 bg-white text-sm">
                                        <option value="">Seleccione Gasto...</option>
                                        {cuentasGasto.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-xs font-bold text-gray-600 uppercase mb-1">Cuenta de Pago (Caja/Banco)</label>
                                    <select value={cuentaCajaId} onChange={e => setCuentaCajaId(e.target.value)} required className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 bg-white text-sm">
                                        <option value="">Seleccione Pago...</option>
                                        {cuentasCaja.map(c => <option key={c.id} value={c.id}>{c.codigo} - {c.nombre}</option>)}
                                    </select>
                                </div>
                            </div>
                        </form>
                    )}
                </div>

                <div className="bg-gray-50 px-6 py-4 flex justify-end gap-3 rounded-b-2xl border-t border-gray-100 shrink-0">
                    <button type="button" onClick={onClose} disabled={isLoading} className="px-5 py-2 text-gray-600 bg-white border border-gray-300 rounded-xl hover:bg-gray-50 focus:outline-none transition-colors font-medium">
                        Cancelar
                    </button>
                    <button type="submit" form="buzonForm" disabled={isLoading || loadingData} className="px-6 py-2 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 shadow-md flex items-center gap-2 transition-all font-bold disabled:bg-indigo-400">
                        {isLoading ? <><FaSpinner className="animate-spin" /> Conectando...</> : <><FaCheckCircle /> Escanear y Contabilizar</>}
                    </button>
                </div>
            </div>
        </div>
    );
}
