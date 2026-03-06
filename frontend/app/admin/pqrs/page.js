'use client';
import React, { useState, useEffect } from 'react';
import { apiService } from '@/lib/apiService';
import { FaEnvelope, FaClock, FaCheckCircle, FaExclamationCircle, FaUser, FaReply, FaSearch } from 'react-icons/fa';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import { toast } from 'react-toastify';
import { useAuth } from '@/app/context/AuthContext';

export default function PQRInboxPage() {
    const { user } = useAuth();
    const [tickets, setTickets] = useState([]);
    const [filteredTickets, setFilteredTickets] = useState([]);
    const [selectedTicket, setSelectedTicket] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [filterStatus, setFilterStatus] = useState('ALL');
    const [responseText, setResponseText] = useState('');
    const [isSending, setIsSending] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        fetchTickets();
    }, []);

    useEffect(() => {
        let result = tickets;
        if (filterStatus !== 'ALL') {
            result = result.filter(t => t.estado === filterStatus);
        }
        if (searchTerm) {
            const lowSearch = searchTerm.toLowerCase();
            result = result.filter(t =>
                t.asunto.toLowerCase().includes(lowSearch) ||
                t.tercero_nombre.toLowerCase().includes(lowSearch) ||
                t.mensaje.toLowerCase().includes(lowSearch)
            );
        }
        setFilteredTickets(result);
    }, [tickets, filterStatus, searchTerm]);

    const fetchTickets = async () => {
        setIsLoading(true);
        try {
            const response = await apiService.get('/soporte/tickets/admin');
            setTickets(response.data);
            if (response.data.length > 0 && !selectedTicket) {
                // No seleccionamos automáticamente para dejar la vista limpia
            }
        } catch (error) {
            console.error("Error fetching tickets:", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleUpdateStatus = async (ticketId, newStatus) => {
        try {
            await apiService.patch(`/soporte/tickets/admin/${ticketId}`, { estado: newStatus });
            fetchTickets();
            if (selectedTicket?.id === ticketId) {
                setSelectedTicket(prev => ({ ...prev, estado: newStatus }));
            }
        } catch (error) {
            alert("Error al actualizar el estado");
        }
    };

    const handleSendResponse = async () => {
        if (!responseText.trim()) return;
        setIsSending(true);
        try {
            await apiService.patch(`/soporte/tickets/admin/${selectedTicket.id}`, {
                respuesta_soporte: responseText,
                estado: 'PROCESO'
            });
            setResponseText('');
            fetchTickets();
            toast.success("Respuesta guardada con éxito");
        } catch (error) {
            alert("Error al enviar respuesta");
        } finally {
            setIsSending(false);
        }
    };

    const getStatusBadge = (status) => {
        switch (status) {
            case 'ABIERTO': return <span className="bg-red-100 text-red-700 px-2 py-1 rounded-full text-xs font-bold ring-1 ring-red-200">Abierto</span>;
            case 'PROCESO': return <span className="bg-amber-100 text-amber-700 px-2 py-1 rounded-full text-xs font-bold ring-1 ring-amber-200">En Proceso</span>;
            case 'CERRADO': return <span className="bg-emerald-100 text-emerald-700 px-2 py-1 rounded-full text-xs font-bold ring-1 ring-emerald-200">Cerrado</span>;
            default: return <span className="bg-gray-100 text-gray-700 px-2 py-1 rounded-full text-xs font-bold">{status}</span>;
        }
    };

    return (
        <div className="flex flex-col h-[calc(100vh-120px)] bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100">
            {/* HEADER */}
            <div className="mb-8 p-4 bg-gray-50 border-b border-gray-200">
                <div className="flex items-center gap-3 mb-2">
                    <div className="bg-indigo-600 p-2.5 rounded-xl shadow-lg shadow-indigo-200">
                        <FaEnvelope className="text-white text-xl" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-black text-gray-900 tracking-tight">Buzón de PQRs</h1>
                        <p className="text-gray-500 font-medium">Gestión de tickets de soporte de clientes</p>
                    </div>
                </div>

                {/* DEPURACIÓN TEMPORAL */}
                <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-xl text-xs font-mono text-blue-700 flex flex-wrap gap-4">
                    <span>DEBUG: API_URL={apiService.defaults.baseURL}</span>
                    <span>TICKETS_RAW: {tickets?.length || 0}</span>
                    <span>FILTERED: {filteredTickets?.length || 0}</span>
                    <span>STATUS: {filterStatus}</span>
                    <span>USER_COMPANY: {user?.empresa_id || user?.empresaId || 'None'}</span>
                </div>
            </div>
            <div className="flex items-center gap-3 w-full md:w-auto p-4 pt-0">
                <div className="relative flex-1 md:w-64">
                    <FaSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm" />
                    <input
                        type="text"
                        placeholder="Buscar ticket..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-9 pr-4 py-2 bg-white border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                    />
                </div>
                <select
                    value={filterStatus}
                    onChange={(e) => setFilterStatus(e.target.value)}
                    className="bg-white border border-gray-200 rounded-xl px-3 py-2 text-sm font-bold text-gray-700 outline-none focus:ring-2 focus:ring-indigo-500"
                >
                    <option value="ALL">Todos los Estados</option>
                    <option value="ABIERTO">Solo Abiertos</option>
                    <option value="PROCESO">En Proceso</option>
                    <option value="CERRADO">Cerrados</option>
                </select>
            </div>

            <div className="flex flex-1 overflow-hidden">
                {/* Listado de Tickets */}
                <div className="w-full md:w-1/3 border-r border-gray-100 overflow-y-auto bg-gray-50/30">
                    {isLoading ? (
                        <div className="p-10 text-center text-gray-400">
                            <div className="animate-spin mb-4 inline-block"><FaClock size={24} /></div>
                            <p className="text-sm">Cargando tickets...</p>
                        </div>
                    ) : filteredTickets.length === 0 ? (
                        <div className="p-10 text-center text-gray-400">
                            <FaCheckCircle size={40} className="mx-auto mb-4 opacity-20" />
                            <p className="text-sm font-medium">No hay tickets pendientes</p>
                        </div>
                    ) : (
                        <div className="divide-y divide-gray-100">
                            {filteredTickets.map(ticket => (
                                <div
                                    key={ticket.id}
                                    onClick={() => setSelectedTicket(ticket)}
                                    className={`p-4 cursor-pointer transition-all hover:bg-white relative border-l-4 ${selectedTicket?.id === ticket.id ? 'bg-white border-indigo-600 shadow-md z-10' : 'border-transparent'}`}
                                >
                                    <div className="flex justify-between items-start mb-1">
                                        <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">#{ticket.id}</span>
                                        {getStatusBadge(ticket.estado)}
                                    </div>
                                    <h3 className={`text-sm font-bold truncate ${selectedTicket?.id === ticket.id ? 'text-indigo-700' : 'text-gray-800'}`}>
                                        {ticket.asunto}
                                    </h3>
                                    <p className="text-xs text-gray-500 truncate mt-1 flex items-center gap-1">
                                        <FaUser className="text-[10px]" /> {ticket.tercero_nombre}
                                    </p>
                                    <div className="mt-2 text-[10px] text-gray-400 font-bold flex items-center gap-1">
                                        <FaClock /> {format(new Date(ticket.fecha_creacion), 'dd MMM, HH:mm', { locale: es })}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Detalle del Ticket */}
                <div className="flex-1 overflow-y-auto bg-white p-6">
                    {selectedTicket ? (
                        <div className="max-w-3xl mx-auto animate-in fade-in slide-in-from-right-4 duration-300">
                            <div className="flex justify-between items-start mb-6">
                                <div>
                                    <div className="flex items-center gap-2 mb-2">
                                        <span className="bg-indigo-50 text-indigo-700 px-3 py-1 rounded-lg text-xs font-black">TIPO: {selectedTicket.tipo?.toUpperCase() || 'GENERAL'}</span>
                                        {getStatusBadge(selectedTicket.estado)}
                                    </div>
                                    <h2 className="text-2xl font-black text-gray-900 tracking-tight leading-tight">{selectedTicket.asunto}</h2>
                                    <p className="text-sm text-gray-500 mt-2 flex items-center gap-2 font-medium">
                                        <span className="bg-gray-100 p-1.5 rounded-full"><FaUser size={12} className="text-gray-400" /></span>
                                        Enviado por: <span className="font-bold text-gray-700">{selectedTicket.tercero_nombre}</span>
                                        <span className="text-gray-300 mx-1">|</span>
                                        <span>{format(new Date(selectedTicket.fecha_creacion), "EEEE d 'de' MMMM, HH:mm", { locale: es })}</span>
                                    </p>
                                </div>
                                <div className="flex gap-2">
                                    {selectedTicket.estado !== 'CERRADO' ? (
                                        <button
                                            onClick={() => handleUpdateStatus(selectedTicket.id, 'CERRADO')}
                                            className="px-4 py-2 bg-emerald-600 text-white rounded-xl text-sm font-bold hover:bg-emerald-700 shadow-lg shadow-emerald-100 transition-all flex items-center gap-2"
                                        >
                                            <FaCheckCircle /> Cerrar Caso
                                        </button>
                                    ) : (
                                        <button
                                            onClick={() => handleUpdateStatus(selectedTicket.id, 'ABIERTO')}
                                            className="px-4 py-2 border border-red-200 text-red-600 rounded-xl text-sm font-bold hover:bg-red-50 transition-all"
                                        >
                                            Reabrir
                                        </button>
                                    )}
                                </div>
                            </div>

                            <div className="bg-gray-50 rounded-2xl p-6 border border-gray-100 mb-8 relative">
                                <div className="absolute -top-3 left-6 bg-white px-2 text-[10px] font-black text-gray-400 uppercase tracking-widest border border-gray-100 rounded-md">Mensaje del Cliente</div>
                                <p className="text-gray-800 leading-relaxed whitespace-pre-wrap font-medium">
                                    {selectedTicket.mensaje}
                                </p>
                            </div>

                            {/* Responder Section */}
                            <div className="border-t border-gray-100 pt-8">
                                <h4 className="text-sm font-black text-gray-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                                    <FaReply className="text-indigo-400" /> Gestionar Respuesta
                                </h4>
                                <textarea
                                    className="w-full h-40 p-4 bg-white border-2 border-gray-100 rounded-2xl focus:border-indigo-500 outline-none transition-all text-sm font-medium placeholder-gray-300"
                                    placeholder="Escribe aquí la respuesta interna o para el cliente..."
                                    value={responseText}
                                    onChange={(e) => setResponseText(e.target.value)}
                                ></textarea>
                                <div className="flex justify-end mt-4">
                                    <button
                                        disabled={isSending || !responseText.trim()}
                                        onClick={handleSendResponse}
                                        className="px-6 py-3 bg-indigo-600 text-white rounded-xl text-sm font-black hover:bg-indigo-700 disabled:bg-gray-200 shadow-xl shadow-indigo-100 transition-all"
                                    >
                                        {isSending ? 'Enviando...' : 'Guardar y Marcar en Proceso'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="h-full flex flex-col items-center justify-center text-gray-400 animate-pulse">
                            <div className="bg-gray-50 p-8 rounded-full mb-6">
                                <FaEnvelope size={60} className="opacity-10" />
                            </div>
                            <p className="text-lg font-black tracking-tight">Selecciona un ticket para ver los detalles</p>
                            <p className="text-sm font-medium mt-1">Aquí aparecerán las solicitudes reales de tus clientes</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
