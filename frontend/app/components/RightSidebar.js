'use client';
import React, { useState, useEffect, useRef } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import {
    FaRobot, FaCalculator, FaStickyNote, FaBell,
    FaThumbtack, FaTimes, FaExpandAlt, FaMagic, FaPaperPlane,
    FaBackspace, FaTrash, FaMicrophone, FaStop, FaPlus, FaSave, FaList, FaShareSquare, FaHistory, FaClock,
    FaBuilding, FaChartLine, FaBolt, FaSync, FaFilePdf, FaEdit, FaSearch, FaPrint
} from 'react-icons/fa';
import { CONTEXT_CONFIG } from '../config/rightSidebarConfig';
import { toast } from 'react-toastify';
import { apiService } from '@/lib/apiService';
import { useAuth } from '@/app/context/AuthContext';
import EconomicIndicatorsPanel from './EconomicIndicatorsPanel';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { useSmartSearch } from '@/app/hooks/useSmartSearch';

// --- HELPER: FORMAT NUMBERS ---
const formatNumber = (numStr) => {
    if (!numStr || numStr === 'Error') return numStr;
    const parts = numStr.split('.');
    const integerPart = parts[0];
    const decimalPart = parts.length > 1 ? '.' + parts[1] : '';
    const formattedInt = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return formattedInt + decimalPart;
};

// --- HOOK: CALCULADORA ---
const useCalculator = () => {
    const [display, setDisplay] = useState('0');
    const [expression, setExpression] = useState('');
    const [waitingForOperand, setWaitingForOperand] = useState(false);

    const handleInput = (val) => {
        if (val === 'C') {
            setDisplay('0');
            setExpression('');
            return;
        }
        if (val === 'DEL') {
            if (waitingForOperand) return;
            setDisplay(prev => {
                if (prev === 'Error') return '0';
                return prev.length > 1 ? prev.slice(0, -1) : '0';
            });
            return;
        }
        if (val === '=') {
            try {
                if (!expression) return;
                const safeExpr = expression + display;
                // eslint-disable-next-line
                const result = new Function('return ' + safeExpr)();
                if (!isFinite(result)) throw new Error("Math Error");
                setDisplay(String(result));
                setExpression('');
                setWaitingForOperand(true);
            } catch (e) {
                setDisplay('Error');
            }
            return;
        }
        if (['+', '-', '*', '/'].includes(val)) {
            setExpression(prev => {
                if (waitingForOperand) {
                    return prev.slice(0, -1) + val;
                }
                return prev + display + val;
            });
            setWaitingForOperand(true);
            return;
        }

        if (waitingForOperand) {
            setDisplay(val);
            setWaitingForOperand(false);
        } else {
            setDisplay(display === '0' ? val : display + val);
        }
    };

    return { display, expression, handleInput };
};

// --- HOOK: NOTES MANAGER ---
const useNotesManager = () => {
    const [notes, setNotes] = useState([]);
    const [activeNoteId, setActiveNoteId] = useState(null);
    const [currentText, setCurrentText] = useState('');

    useEffect(() => {
        try {
            const saved = localStorage.getItem('smart_hub_notes');
            if (saved) {
                const parsed = JSON.parse(saved);
                setNotes(parsed);
                if (parsed.length > 0) {
                    setActiveNoteId(parsed[0].id);
                    setCurrentText(parsed[0].text);
                }
            } else {
                const initial = [{ id: Date.now(), text: '', date: new Date().toISOString() }];
                setNotes(initial);
                setActiveNoteId(initial[0].id);
            }
        } catch (e) { console.error("Loading notes error", e); }
    }, []);

    useEffect(() => {
        if (!activeNoteId) return;
        const timeout = setTimeout(() => {
            const updated = notes.map(n => n.id === activeNoteId ? { ...n, text: currentText, date: new Date().toISOString() } : n);
            localStorage.setItem('smart_hub_notes', JSON.stringify(updated));
            setNotes(updated);
        }, 500);
        return () => clearTimeout(timeout);
    }, [currentText, activeNoteId]);

    const createNote = (initialText = '') => {
        const content = typeof initialText === 'string' ? initialText : '';
        const newNote = { id: Date.now(), text: content, date: new Date().toISOString() };
        const newNotes = [newNote, ...notes];
        setNotes(newNotes);
        setActiveNoteId(newNote.id);
        setCurrentText(content);
        localStorage.setItem('smart_hub_notes', JSON.stringify(newNotes));
    };

    const deleteNote = (id) => {
        const remaining = notes.filter(n => n.id !== id);
        if (remaining.length === 0) {
            const fresh = [{ id: Date.now(), text: '', date: new Date().toISOString() }];
            setNotes(fresh);
            setActiveNoteId(fresh[0].id);
            setCurrentText('');
            localStorage.setItem('smart_hub_notes', JSON.stringify(fresh));
        } else {
            setNotes(remaining);
            localStorage.setItem('smart_hub_notes', JSON.stringify(remaining));
            if (id === activeNoteId) {
                setActiveNoteId(remaining[0].id);
                setCurrentText(remaining[0].text);
            }
        }
    };

    const selectNote = (id) => {
        const target = notes.find(n => n.id === id);
        if (target) {
            setActiveNoteId(id);
            setCurrentText(target.text);
        }
    };

    return { notes, activeNoteId, currentText, setCurrentText, createNote, deleteNote, selectNote };
};

// --- COMPONENTE: WIDGET RENDERER ---
const WidgetRenderer = ({ config }) => {
    if (!config || !config.widgets) return null;
    return (
        <div className="space-y-4 animate-fadeIn">
            <div className={`p-4 rounded-xl border bg-${config.widgets[0].color || 'gray'}-50 border-${config.widgets[0].color || 'gray'}-100`}>
                <h4 className={`text-xs font-bold text-${config.widgets[0].color || 'gray'}-800 uppercase mb-3`}>
                    {config.title}
                </h4>
                <div className="space-y-3">
                    {config.widgets.map((widget, idx) => (
                        <div key={idx}>
                            {widget.type === 'stat' && (
                                <div className="flex justify-between items-end bg-white/50 p-2 rounded-lg">
                                    <div>
                                        <p className={`text-xs text-${widget.color}-600`}>{widget.title}</p>
                                        <p className={`text-xl font-bold text-${widget.color}-900`}>{widget.value}</p>
                                    </div>
                                    {widget.change && <span className="text-xs text-green-600 bg-green-100 px-2 py-1 rounded-full">{widget.change}</span>}
                                </div>
                            )}
                            {widget.type === 'action' && (
                                <button className={`w-full mt-2 py-2 bg-white border border-${widget.color}-200 text-${widget.color}-700 text-sm rounded-lg shadow-sm hover:bg-${widget.color}-50 transition-all font-medium`}>
                                    {widget.label}
                                </button>
                            )}
                            {widget.type === 'alert' && (
                                <ul className="text-xs text-gray-700 space-y-1">
                                    {widget.items.map((item, i) => (
                                        <li key={i} className="flex justify-between">
                                            <span>{item.label}</span>
                                            <span className="font-bold text-red-600">{item.value}</span>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default function RightSidebar({ isOpen, isPinned, onToggle, onPin, onClose }) {
    const { user } = useAuth();
    const pathname = usePathname();
    const router = useRouter();
    const [activeTab, setActiveTab] = useState('ai');
    const [showIndicators, setShowIndicators] = useState(false);

    // Escuchar evento para mostrar biblioteca
    useEffect(() => {
        const handleShowLibrary = () => {
            setActiveTab('ai');
            setShowLibraryTabInModal(true);
        };
        window.addEventListener('show-ai-library', handleShowLibrary);
        return () => window.removeEventListener('show-ai-library', handleShowLibrary);
    }, []);

    // --- MONITOR STATE ---
    const [monitorData, setMonitorData] = useState([]);
    const [monitorLoading, setMonitorLoading] = useState(false);
    const [monitorFilters, setMonitorFilters] = useState({
        fechaInicio: new Date(new Date().getFullYear(), new Date().getMonth(), 1),
        fechaFin: new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0),
        tipo: '',
        numero: '',
        beneficiario: '',
        concepto: ''
    });

    const fetchMonitorData = async () => {
        setMonitorLoading(true);
        try {
            const inicio = monitorFilters.fechaInicio.toISOString().split('T')[0];
            const fin = monitorFilters.fechaFin.toISOString().split('T')[0];

            const res = await apiService.get('/reports/journal', {
                params: {
                    fecha_inicio: inicio,
                    fecha_fin: fin
                }
            });

            const sorted = Array.isArray(res.data) ? res.data.sort((a, b) => b.id - a.id) : [];
            setMonitorData(sorted);
        } catch (err) {
            console.error("Error fetching monitor data", err);
        } finally {
            setMonitorLoading(false);
        }
    };

    useEffect(() => {
        if (activeTab === 'monitor') {
            fetchMonitorData();
        }
    }, [activeTab, monitorFilters.fechaInicio, monitorFilters.fechaFin]);

    const handlePrintDoc = async (id) => {
        if (!id) return;
        toast.info("Generando PDF... ⏳", { autoClose: 2000 });
        try {
            const response = await apiService.get(`/documentos/${id}/pdf`, {
                responseType: 'blob'
            });
            const file = new Blob([response.data], { type: 'application/pdf' });
            const fileURL = URL.createObjectURL(file);
            window.open(fileURL, '_blank');
        } catch (err) {
            console.error("Error generating PDF", err);
            toast.error("No se pudo generar el PDF del documento.");
        }
    };

    const handleEditDoc = (id) => {
        if (!id) return;
        window.open(`/contabilidad/documentos/${id}?edit=true`, '_blank');
    };

    const handleViewAuxiliar = (codigo) => {
        if (!codigo) return;
        const inicio = monitorFilters.fechaInicio.toISOString().split('T')[0];
        const fin = monitorFilters.fechaFin.toISOString().split('T')[0];
        window.open(`/contabilidad/reportes/auxiliar-cuenta?cuenta=${codigo}&fecha_inicio=${inicio}&fecha_fin=${fin}`, '_blank');
    };

    const handleExportMonitorPDF = async () => {
        try {
            const inicio = monitorFilters.fechaInicio.toISOString().split('T')[0];
            const fin = monitorFilters.fechaFin.toISOString().split('T')[0];

            const res = await apiService.get('/reports/journal/get-signed-url', {
                params: {
                    fecha_inicio: inicio,
                    fecha_fin: fin,
                    numero_documento: monitorFilters.numero || '',
                    beneficiario_filtro: monitorFilters.beneficiario || '',
                    concepto_filtro: monitorFilters.concepto || ''
                }
            });

            const data = res.data;
            if (data.signed_url_token) {
                // Obtenemos la URL de la API desde la configuración global o fallback
                const baseUrl = process.env.NEXT_PUBLIC_API_URL || '';
                window.open(`${baseUrl}/api/reports/journal/imprimir?signed_token=${data.signed_url_token}`, '_blank');
            }
        } catch (error) {
            console.error("Error al exportar monitor:", error);
            toast.error("Error al exportar monitor");
        }
    };

    const monitorFiltrado = monitorData.filter(mov => {
        if (monitorFilters.tipo && mov.tipo_documento_codigo !== monitorFilters.tipo) return false;
        if (monitorFilters.numero && !String(mov.numero_documento).includes(monitorFilters.numero)) return false;
        if (monitorFilters.beneficiario && monitorFilters.beneficiario.length >= 2) {
            const term = monitorFilters.beneficiario.toLowerCase();
            const nombre = (mov.beneficiario_nombre || '').toLowerCase();
            const nit = (mov.beneficiario_nit || '').toLowerCase();
            if (!nombre.includes(term) && !nit.includes(term)) return false;
        }
        if (monitorFilters.concepto && monitorFilters.concepto.length >= 3) {
            const term = monitorFilters.concepto.toLowerCase();
            const concepto = (mov.concepto || '').toLowerCase();
            if (!concepto.includes(term)) return false;
        }
        return true;
    });

    const tiposMonitor = Array.from(new Set(monitorData.map(m => m.tipo_documento_codigo).filter(Boolean))).sort();


    // Hooks
    const { display, expression, handleInput } = useCalculator();
    const { notes, activeNoteId, currentText, setCurrentText, createNote, deleteNote, selectNote } = useNotesManager();
    const [showNoteList, setShowNoteList] = useState(false);

    // --- AI & Voice Logic (Unified via hook) ---
    const {
        query: aiQuery,
        setQuery: setAiQuery,
        isThinking,
        toggleListening,
        processVoiceCommand,
        commandHistory,
        library: savedSearches,
        isLibraryLoading: isSavedSearchesLoading,
        addToLibrary: saveSearch,
        deleteFromLibrary: deleteSavedSearch,
        updateLibraryTitle: updateSavedSearch,
        loadLibraryData: fetchLibrary,
        loadCommandHistory: fetchSavedSearches,
        isListening
    } = useSmartSearch();

    const [aiResponse, setAiResponse] = useState(null);
    const [listeningMode, setListeningMode] = useState(null); // 'ai' or 'notes'
    const recognitionRef = useRef(null);
    const listeningModeRef = useRef(null);

    const [showHistory, setShowHistory] = useState(false);
    const [showLibraryTabInModal, setShowLibraryTabInModal] = useState(false);

    // --- SAVED SEARCHES STATE HANDLED BY HOOK ---

    const [editingSearchId, setEditingSearchId] = useState(null);
    const [editSearchTitle, setEditSearchTitle] = useState('');

    const sendCalcToNote = () => {
        const val = display === 'Error' ? '0' : display;
        const line = `\nCálculo: ${formatNumber(val)}`;
        if (activeNoteId) {
            setCurrentText(prev => prev + line);
            toast.success("Agregado a nota activa");
        } else {
            createNote(`Nota de Cálculo${line}`);
            toast.success("Nueva nota creada");
        }
        setActiveTab('notes');
    };

    // History handled by hook

    const addToHistory = (text) => {
        // Handled by hook
    };

    const handleHistoryClick = (cmd) => {
        setAiQuery(cmd);
        setShowHistory(false);
    };

    // --- VOICE SETUP (SHARED/LOCAL) ---
    useEffect(() => {
        listeningModeRef.current = listeningMode;
    }, [listeningMode]);

    useEffect(() => {
        if (typeof window !== 'undefined') {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (SpeechRecognition) {
                const recognition = new SpeechRecognition();
                recognition.continuous = false;
                recognition.lang = 'es-CO';
                recognition.interimResults = true;

                recognition.onresult = (event) => {
                    const transcript = Array.from(event.results).map(r => r[0].transcript).join('');
                    const mode = listeningModeRef.current;

                    if (mode === 'ai') {
                        setAiQuery(transcript);
                    } else if (mode === 'notes') {
                        if (event.results[0].isFinal) {
                            setCurrentText(prev => prev + (prev ? ' ' : '') + transcript);
                        }
                    }
                };

                recognition.onend = () => {
                    setListeningMode(null);
                };

                recognition.onerror = (e) => {
                    setListeningMode(null);
                    if (e.error !== 'no-speech') toast.error("Error de micrófono.");
                };

                recognitionRef.current = recognition;
            }
        }
    }, []);

    const toggleVoice = (mode) => {
        if (mode === 'ai') {
            toggleListening();
            setListeningMode(prev => prev === 'ai' ? null : 'ai');
            return;
        }

        // Local handling for notes
        if (!recognitionRef.current) { toast.warning("Usa Chrome para voz."); return; }
        if (listeningMode === mode) {
            recognitionRef.current.stop();
            setListeningMode(null);
        } else {
            if (listeningMode) recognitionRef.current.abort();
            setListeningMode(mode);
            try {
                recognitionRef.current.start();
                toast.info("Dictando nota...");
            } catch (e) { console.error(e); }
        }
    };

    // Sync hook state with local listeningMode for AI
    useEffect(() => {
        if (isListening) setListeningMode('ai');
        else if (listeningMode === 'ai') setListeningMode(null);
    }, [isListening]);

    const handleSavedSearchClick = (cmd) => {
        setAiQuery(cmd);
    };

    const currentContext = CONTEXT_CONFIG ? CONTEXT_CONFIG.find(ctx =>
        ctx.match.some(pathTrigger => pathname && pathname.toLowerCase().includes(pathTrigger.toLowerCase()))
    ) : null;


    // AI action execution is now handled by the useSmartSearch hook

    // --- SUBMIT LOGIC ---
    const handleAiSubmit = async (e, forcedQuery = null) => {
        if (e) e.preventDefault();
        const commandToRun = forcedQuery || aiQuery;
        if (!commandToRun || !commandToRun.trim()) return;

        setAiResponse(null);
        await processVoiceCommand(commandToRun);
        if (!forcedQuery) setAiQuery('');
    };

    // Keyboard support
    useEffect(() => {
        if (activeTab === 'calc' && (isOpen || isPinned)) {
            const handleKeyDown = (e) => {
                const key = e.key;
                if (/[0-9]/.test(key)) handleInput(key);
                if (['+', '-', '*', '/'].includes(key)) handleInput(key);
                if (key === 'Enter' || key === '=') handleInput('=');
                if (key === 'Escape' || key === 'c' || key === 'C') handleInput('C');
                if (key === 'Backspace') handleInput('DEL');
            };
            window.addEventListener('keydown', handleKeyDown);
            return () => window.removeEventListener('keydown', handleKeyDown);
        }
    }, [activeTab, isOpen, isPinned, display, expression]);

    // UI Helpers
    const widthClass = (isOpen || isPinned) ? 'w-[350px]' : 'w-12';
    const glassClass = "backdrop-blur-xl bg-white/90 border-l border-gray-200 shadow-2xl";
    const handleTabClick = (tab) => { if (!isOpen && !isPinned) onToggle(true); setActiveTab(tab); };

    return (
        <div className={`fixed right-0 top-0 bottom-0 z-[60] transition-all duration-300 ease-spring ${widthClass} ${glassClass} flex`}>
            {/* ICONS */}
            <div className="w-12 flex flex-col items-center py-4 bg-gray-50/50 border-r border-gray-200 h-full flex-shrink-0">
                <button onClick={() => handleTabClick('ai')} className={`nav-item mb-2 p-2 rounded-xl transition-all ${activeTab === 'ai' && (isOpen || isPinned) ? 'bg-indigo-100 text-indigo-600' : 'text-gray-400 hover:text-indigo-500 hover:bg-indigo-50'}`}><FaRobot className="text-xl" /></button>
                <button onClick={() => handleTabClick('monitor')} className={`nav-item mb-6 p-2 rounded-xl transition-all ${activeTab === 'monitor' && (isOpen || isPinned) ? 'bg-purple-100 text-purple-600' : 'text-gray-400 hover:text-purple-500 hover:bg-purple-50'}`} title="Monitor de Asientos"><FaBolt className="text-xl" /></button>
                <div className="w-6 h-[1px] bg-gray-200 mb-4"></div>
                <button onClick={() => handleTabClick('calc')} className={`nav-item p-2 mb-2 rounded-lg ${activeTab === 'calc' && (isOpen || isPinned) ? 'bg-blue-100 text-blue-600' : 'text-gray-400 hover:bg-blue-50'}`}><FaCalculator /></button>
                <button onClick={() => handleTabClick('notes')} className={`nav-item p-2 mb-2 rounded-lg ${activeTab === 'notes' && (isOpen || isPinned) ? 'bg-yellow-100 text-yellow-600' : 'text-gray-400 hover:bg-yellow-50'}`}><FaStickyNote /></button>
                <button onClick={() => handleTabClick('notif')} className={`nav-item p-2 rounded-lg ${activeTab === 'notif' && (isOpen || isPinned) ? 'bg-red-100 text-red-600' : 'text-gray-400 hover:text-red-500 hover:bg-red-50'}`}><FaBell /><span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full border border-white"></span></button>

                {/* BOTÓN IDENTIFICADOR DE EMPRESA */}
                <button
                    onClick={() => toast.info(
                        <div>
                            <p className="font-bold">🏢 Empresa Actual:</p>
                            <p className="text-lg text-indigo-700">{user?.empresa?.razon_social || 'Sin Empresa'}</p>
                            <p className="text-xs text-gray-500">NIT: {user?.empresa?.nit}</p>
                            <p className="text-xs text-gray-400 mt-1">Usuario: {user?.email}</p>
                        </div>,
                        { position: "bottom-left", autoClose: 5000 }
                    )}
                    className="nav-item p-2 mt-2 rounded-lg text-gray-400 hover:text-purple-600 hover:bg-purple-50 transition-colors"
                    title="Ver Empresa Actual"
                >
                    <FaBuilding />
                </button>

                {/* BOTÓN INDICADORES ECONÓMICOS */}
                <button
                    onClick={() => setShowIndicators(!showIndicators)}
                    className={`nav-item p-2 mt-2 rounded-lg transition-colors ${showIndicators ? 'bg-green-100 text-green-600' : 'text-gray-400 hover:text-green-600 hover:bg-green-50'}`}
                    title="Indicadores Económicos (Dólar, UVT, Nómina)"
                >
                    <span className="font-bold text-lg">$</span>
                </button>

                <div className="flex-grow"></div>
                {(isOpen || isPinned) ? (
                    <div className="flex flex-col gap-2 mb-2">
                        <button onClick={onPin} className={`p-2 rounded-lg hover:bg-gray-200 ${isPinned ? 'text-indigo-600' : 'text-gray-400'}`}><FaThumbtack className={`text-sm ${!isPinned && '-rotate-45'}`} /></button>
                        <button onClick={onClose} className="p-2 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50"><FaTimes /></button>
                    </div>
                ) : (
                    <button onClick={() => onToggle(true)} className="p-2 text-gray-400"><FaExpandAlt /></button>
                )}
            </div>

            {/* CONTENT */}
            <div className={`flex-1 flex flex-col h-full overflow-hidden transition-opacity duration-300 ${(isOpen || isPinned) ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}>
                <div className="h-14 border-b border-gray-100 flex items-center px-6 bg-white/50 justify-between">
                    <h2 className="font-bold text-gray-700">
                        {activeTab === 'ai' && 'Finaxis Copilot'}
                        {activeTab === 'monitor' && 'Monitor de Asientos'}
                        {activeTab === 'calc' && 'Calculadora'}
                        {activeTab === 'notes' && 'Mis Notas'}
                        {activeTab === 'notif' && 'Notificaciones'}
                    </h2>
                    {currentContext && <span className="text-[10px] bg-gray-100 text-gray-500 px-2 py-1 rounded-full uppercase font-bold tracking-wider">{currentContext.title}</span>}
                </div>
                <div className="flex-1 overflow-y-auto p-6 scrollbar-thin">

                    {/* AI */}
                    {activeTab === 'ai' && (
                        <div className="flex flex-col h-full">
                            {currentContext ? <WidgetRenderer config={currentContext} /> : <div className="p-4 text-center text-gray-400 text-xs mb-4 border border-dashed border-gray-200 rounded-lg">No hay contexto activo.</div>}
                            <div className="flex-grow"></div>
                            {aiResponse && <div className={`mb-4 p-3 rounded-lg text-sm ${aiResponse.type === 'error' ? 'bg-red-50 text-red-700' : 'bg-indigo-50 text-indigo-800'}`}><strong>Respuesta:</strong><p>{aiResponse.text}</p></div>}

                            <form onSubmit={(e) => handleAiSubmit(e)} className="bg-white p-2 rounded-2xl shadow-sm border border-gray-200 mt-4 relative">
                                <div className="flex gap-2 items-end">
                                    <textarea
                                        autoFocus
                                        rows={4}
                                        value={aiQuery}
                                        onChange={(e) => setAiQuery(e.target.value)}
                                        onKeyDown={(e) => {
                                            if (e.key === 'Enter' && !e.shiftKey) {
                                                e.preventDefault();
                                                handleAiSubmit(e);
                                            }
                                        }}
                                        placeholder={listeningMode === 'ai' ? "Escuchando..." : "¿Qué deseas hacer? (Shift+Enter para saltar línea)"}
                                        className="flex-1 text-sm bg-transparent border-none focus:ring-0 p-2 resize-none custom-scrollbar"
                                        disabled={isThinking}
                                    />
                                    <div className="flex flex-col gap-1 pb-1">
                                        <button type="button" onClick={() => { setShowHistory(true); fetchSavedSearches(); }} className="text-gray-400 hover:text-indigo-600 p-2" title="Historial y Biblioteca"><FaHistory /></button>
                                        <button type="button" onClick={() => toggleVoice('ai')} className={`p-2 rounded-full transition-colors ${listeningMode === 'ai' ? 'bg-red-100 text-red-600 animate-pulse' : 'text-gray-400 hover:text-red-500'}`}>
                                            {listeningMode === 'ai' ? <FaStop /> : <FaMicrophone />}
                                        </button>
                                        <button type="submit" className="p-2 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition shadow-md" disabled={isThinking}>
                                            {isThinking ? <FaMagic className="animate-spin" /> : <FaPaperPlane />}
                                        </button>
                                    </div>
                                </div>
                            </form>

                            {/* HISTORY & LIBRARY MODAL */}
                            {showHistory && (
                                <div className="absolute inset-0 bg-white z-50 flex flex-col animate-fadeIn">
                                    <div className="flex items-center justify-between p-4 border-b">
                                        <h3 className="font-bold text-gray-700 flex items-center gap-2"><FaHistory /> Historial</h3>
                                        <button onClick={() => setShowHistory(false)} className="text-gray-400 hover:text-red-500"><FaTimes /></button>
                                    </div>

                                    {/* TABS HEADERS */}
                                    <div className="flex border-b">
                                        <button
                                            className={`flex-1 py-2 text-sm font-medium ${!showLibraryTabInModal ? 'text-indigo-600 border-b-2 border-indigo-600' : 'text-gray-500 hover:text-gray-700'}`}
                                            onClick={() => setShowLibraryTabInModal(false)}
                                        >
                                            Recientes
                                        </button>
                                        <button
                                            className={`flex-1 py-2 text-sm font-medium ${showLibraryTabInModal ? 'text-indigo-600 border-b-2 border-indigo-600' : 'text-gray-500 hover:text-gray-700'}`}
                                            onClick={() => setShowLibraryTabInModal(true)}
                                        >
                                            <span className="flex items-center justify-center gap-2"><FaSave /> Biblioteca</span>
                                        </button>
                                    </div>

                                    {/* TABS CONTENT */}
                                    <div className="flex-1 overflow-y-auto p-2">
                                        {!showLibraryTabInModal ? (
                                            commandHistory.length === 0 ? <p className="text-center text-gray-400 text-xs mt-4">Sin historial reciente.</p> : (
                                                <ul className="space-y-2">
                                                    {commandHistory.map((cmd, i) => (
                                                        <li key={i} className="group p-3 bg-gray-50 rounded-lg hover:bg-indigo-50 transition-colors flex justify-between items-center cursor-pointer">
                                                            <div onClick={() => handleHistoryClick(cmd)} className="flex-1 cursor-pointer">
                                                                <p className="text-sm text-gray-700">{cmd}</p>
                                                                <span className="text-[10px] text-gray-400"><FaClock className="inline mr-1" />Reciente</span>
                                                            </div>
                                                            <button
                                                                onClick={(e) => { e.stopPropagation(); saveSearch(cmd); }}
                                                                className="text-gray-300 hover:text-indigo-600 p-2 opacity-0 group-hover:opacity-100 transition-opacity"
                                                                title="Guardar en Biblioteca"
                                                            >
                                                                <FaSave />
                                                            </button>
                                                        </li>
                                                    ))}
                                                </ul>
                                            )
                                        ) : (
                                            isSavedSearchesLoading ? <p className="text-center text-xs text-gray-400 mt-4">Cargando...</p> :
                                                savedSearches.length === 0 ? <p className="text-center text-gray-400 text-xs mt-4">No hay búsquedas guardadas.</p> : (
                                                    <ul className="space-y-2">
                                                        {savedSearches.map((item) => (
                                                            <li key={item.id} className="group p-3 bg-white border border-gray-100 rounded-lg hover:border-indigo-200 hover:shadow-sm transition-all">
                                                                <div className="flex justify-between items-start mb-1">
                                                                    {editingSearchId === item.id ? (
                                                                        <input
                                                                            type="text"
                                                                            className="flex-1 border-b border-indigo-300 outline-none text-sm font-bold text-indigo-700 bg-transparent"
                                                                            autoFocus
                                                                            value={editSearchTitle}
                                                                            onChange={(e) => setEditSearchTitle(e.target.value)}
                                                                            onBlur={() => updateSavedSearch(item.id, editSearchTitle)}
                                                                            onKeyDown={(e) => { if (e.key === 'Enter') updateSavedSearch(item.id, editSearchTitle); }}
                                                                        />
                                                                    ) : (
                                                                        <h4
                                                                            className="font-bold text-gray-700 text-sm cursor-pointer hover:text-indigo-600"
                                                                            onClick={() => { setEditingSearchId(item.id); setEditSearchTitle(item.titulo); }}
                                                                            title="Clic para editar nombre"
                                                                        >
                                                                            {item.titulo}
                                                                        </h4>
                                                                    )}
                                                                    <button onClick={() => deleteSavedSearch(item.id)} className="text-gray-300 hover:text-red-500 p-1"><FaTrash className="text-xs" /></button>
                                                                </div>
                                                                <p className="text-xs text-gray-500 line-clamp-2 italic mb-2">"{item.comando}"</p>
                                                                <button
                                                                    onClick={() => { handleSavedSearchClick(item.comando); setShowHistory(false); }}
                                                                    className="w-full py-1.5 bg-indigo-50 text-indigo-600 text-xs font-bold rounded hover:bg-indigo-100 flex items-center justify-center gap-2"
                                                                >
                                                                    <FaPaperPlane /> Ejecutar
                                                                </button>
                                                            </li>
                                                        ))}
                                                    </ul>
                                                )
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* MONITOR DE ASIENTOS */}
                    {activeTab === 'monitor' && (
                        <div className="flex flex-col h-full space-y-4 animate-fadeIn">
                            {/* BARRA DE ACCIONES Y FILTROS RÁPIDOS */}
                            <div className="flex flex-col gap-3 bg-gray-50 p-3 rounded-xl border border-gray-100 shadow-sm transition-all">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2 bg-white px-2 py-1 rounded-lg border border-gray-200 shadow-inner">
                                        <DatePicker
                                            selected={monitorFilters.fechaInicio}
                                            onChange={date => setMonitorFilters(prev => ({ ...prev, fechaInicio: date }))}
                                            dateFormat="dd/MM"
                                            className="w-12 bg-transparent text-center text-xs font-bold focus:outline-none cursor-pointer text-gray-700"
                                        />
                                        <span className="text-gray-400">-</span>
                                        <DatePicker
                                            selected={monitorFilters.fechaFin}
                                            onChange={date => setMonitorFilters(prev => ({ ...prev, fechaFin: date }))}
                                            dateFormat="dd/MM"
                                            className="w-12 bg-transparent text-center text-xs font-bold focus:outline-none cursor-pointer text-gray-700"
                                        />
                                    </div>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={fetchMonitorData}
                                            disabled={monitorLoading}
                                            className={`p-2 rounded-lg transition-all ${monitorLoading ? 'bg-gray-100 text-gray-400' : 'bg-indigo-50 text-indigo-600 hover:bg-indigo-100 border border-indigo-200'}`}
                                            title="Actualizar"
                                        >
                                            <FaSync className={monitorLoading ? 'animate-spin' : ''} />
                                        </button>
                                        <button
                                            onClick={handleExportMonitorPDF}
                                            disabled={monitorLoading || monitorFiltrado.length === 0}
                                            className={`p-2 rounded-lg transition-all ${monitorLoading || monitorFiltrado.length === 0 ? 'bg-gray-100 text-gray-400' : 'bg-red-50 text-red-600 hover:bg-red-100 border border-red-200'}`}
                                            title="Exportar PDF General"
                                        >
                                            <FaFilePdf />
                                        </button>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-2">
                                    <select
                                        value={monitorFilters.tipo}
                                        onChange={(e) => setMonitorFilters(prev => ({ ...prev, tipo: e.target.value }))}
                                        className="text-xs p-2 border border-gray-200 rounded-lg bg-white outline-none focus:ring-1 focus:ring-purple-400 transition-all"
                                    >
                                        <option value="">Todos Tipos</option>
                                        {tiposMonitor.map(t => <option key={t} value={t}>{t}</option>)}
                                    </select>
                                    <input
                                        type="text"
                                        placeholder="Número..."
                                        value={monitorFilters.numero}
                                        onChange={(e) => setMonitorFilters(prev => ({ ...prev, numero: e.target.value }))}
                                        className="text-xs p-2 border border-gray-200 rounded-lg bg-white outline-none focus:ring-1 focus:ring-purple-400 transition-all"
                                    />
                                </div>
                                <div className="relative">
                                    <input
                                        type="text"
                                        placeholder="Beneficiario o Concepto..."
                                        value={monitorFilters.beneficiario}
                                        onChange={(e) => setMonitorFilters(prev => ({ ...prev, beneficiario: e.target.value }))}
                                        className="text-xs p-2 pl-8 border border-gray-200 rounded-lg bg-white outline-none focus:ring-1 focus:ring-purple-400 w-full transition-all"
                                    />
                                    <FaSearch className="absolute left-2.5 top-2.5 text-gray-300 text-xs" />
                                </div>
                            </div>

                            {/* LISTA DE MOVIMIENTOS */}
                            <div className="flex-grow space-y-2 pb-10">
                                {monitorLoading && monitorData.length === 0 ? (
                                    <div className="flex flex-col items-center justify-center py-20 text-gray-400 animate-pulse">
                                        <FaBolt className="text-4xl mb-2" />
                                        <p className="text-xs">Cargando monitor...</p>
                                    </div>
                                ) : monitorFiltrado.length === 0 ? (
                                    <div className="text-center py-20 text-gray-400 italic text-xs">
                                        No se encontraron movimientos.
                                    </div>
                                ) : (
                                    <div className="space-y-3">
                                        <p className="text-[10px] font-bold text-gray-400 uppercase flex justify-between">
                                            <span>{monitorFiltrado.length} Registros</span>
                                            <span>Desliza para ver más</span>
                                        </p>
                                        {monitorFiltrado.map((mov, idx) => (
                                            <div key={idx} className="bg-white p-3 rounded-xl border border-gray-100 shadow-sm hover:border-purple-300 hover:shadow-md transition-all group">
                                                <div className="flex justify-between items-start mb-2">
                                                    <div className="flex flex-col">
                                                        <button
                                                            onClick={() => handleEditDoc(mov.documento_id)}
                                                            className="text-xs font-bold text-indigo-700 hover:text-purple-600 hover:underline transition-colors flex items-center gap-1"
                                                            title="Editar Documento"
                                                        >
                                                            {mov.tipo_documento_codigo} {mov.numero_documento}
                                                            <FaEdit className="text-[9px] opacity-0 group-hover:opacity-100 transition-opacity" />
                                                        </button>
                                                        <span className="text-[10px] text-gray-400">{new Date(mov.fecha).toLocaleDateString()}</span>
                                                    </div>
                                                    <div className="flex gap-1">
                                                        <button
                                                            onClick={() => handlePrintDoc(mov.documento_id)}
                                                            className="p-1.5 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-all"
                                                            title="Ver PDF"
                                                        >
                                                            <FaPrint className="text-sm" />
                                                        </button>
                                                    </div>
                                                </div>

                                                <div className="space-y-1 mb-2">
                                                    <p className="text-[11px] text-gray-800 font-semibold truncate" title={mov.beneficiario_nombre}>
                                                        {mov.beneficiario_nombre || 'Sin Beneficiario'}
                                                    </p>
                                                    <p className="text-[10px] text-gray-500 italic line-clamp-1" title={mov.concepto}>
                                                        {mov.concepto}
                                                    </p>
                                                </div>

                                                <div className="flex justify-between items-center border-t border-gray-50 pt-2 mt-1">
                                                    <button
                                                        onClick={() => handleViewAuxiliar(mov.cuenta_codigo)}
                                                        className="text-[10px] font-mono bg-slate-50 px-2 py-0.5 rounded border border-gray-100 text-gray-600 hover:bg-indigo-50 hover:text-indigo-700 hover:border-indigo-200 transition-all"
                                                        title="Ver Auxiliar de Cuenta"
                                                    >
                                                        {mov.cuenta_codigo}
                                                    </button>
                                                    <div className="text-[11px] font-bold text-gray-900 bg-gray-50/50 px-2 py-0.5 rounded-lg border border-gray-50">
                                                        {mov.debito > 0 ? `$${parseFloat(mov.debito).toLocaleString('es-CO')}` : `$${parseFloat(mov.credito).toLocaleString('es-CO')}`}
                                                        <span className={`ml-1 text-[8px] font-bold ${mov.debito > 0 ? 'text-blue-600' : 'text-red-500'}`}>
                                                            {mov.debito > 0 ? 'DB' : 'CR'}
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* CALCULATOR */}
                    {activeTab === 'calc' && (
                        <div className="flex flex-col items-center justify-center h-full">
                            <div className="w-full bg-gray-100 p-4 rounded-xl mb-4 text-right shadow-inner">
                                <div className="text-gray-400 text-xs h-4">{expression || '0'}</div>
                                <div className="text-3xl font-mono text-gray-800 font-bold truncate tracking-wider">{formatNumber(display)}</div>
                            </div>
                            <div className="grid grid-cols-4 gap-3 w-full">
                                {['C', '/', '*', '-'].map(op => (<button key={op} onClick={() => handleInput(op)} className="aspect-square bg-indigo-50 text-indigo-600 font-bold rounded-lg hover:bg-indigo-100">{op}</button>))}
                                {[7, 8, 9, '+'].map(val => (<button key={val} onClick={() => handleInput(val)} className={`aspect-square rounded-lg font-bold hover:bg-gray-50 shadow-sm ${val === '+' ? 'bg-indigo-50 text-indigo-600' : 'bg-white text-gray-700'}`}>{val}</button>))}
                                {[4, 5, 6].map(val => (<button key={val} onClick={() => handleInput(val)} className="aspect-square bg-white text-gray-700 font-bold rounded-lg hover:bg-gray-50 shadow-sm">{val}</button>))}
                                <button onClick={() => handleInput('=')} className="row-span-2 bg-indigo-600 text-white font-bold rounded-lg hover:bg-indigo-700 shadow-md flex items-center justify-center">=</button>
                                {[1, 2, 3].map(val => (<button key={val} onClick={() => handleInput(val)} className="aspect-square bg-white text-gray-700 font-bold rounded-lg hover:bg-gray-50 shadow-sm">{val}</button>))}
                                <button onClick={() => handleInput(0)} className="bg-white text-gray-700 font-bold rounded-lg hover:bg-gray-50 shadow-sm">0</button>
                                <button onClick={() => handleInput('.')} className="bg-white text-gray-700 font-bold rounded-lg hover:bg-gray-50 shadow-sm">.</button>
                                <button onClick={sendCalcToNote} className="col-span-1 bg-yellow-100 text-yellow-700 font-bold rounded-lg hover:bg-yellow-200 shadow-sm flex items-center justify-center" title="Enviar a Notas">
                                    <FaShareSquare />
                                </button>
                            </div>
                        </div>
                    )}

                    {/* NOTES */}
                    {activeTab === 'notes' && (
                        <div className="flex flex-col h-full space-y-2">
                            <div className="flex gap-2 pb-2 border-b border-gray-100">
                                <button onClick={() => setShowNoteList(!showNoteList)} className="px-3 py-1 bg-gray-100 text-gray-600 rounded-lg text-xs hover:bg-gray-200 flex items-center gap-2"><FaList /> Lista</button>
                                <button onClick={() => createNote()} className="px-3 py-1 bg-yellow-100 text-yellow-700 rounded-lg text-xs hover:bg-yellow-200 flex items-center gap-2"><FaPlus /> Nueva</button>
                                <button onClick={() => toggleVoice('notes')} className={`px-3 py-1 rounded-lg text-xs flex items-center gap-2 ${listeningMode === 'notes' ? 'bg-red-500 text-white animate-pulse' : 'bg-gray-100 text-gray-600 hover:bg-red-50 hover:text-red-500'}`}>
                                    {listeningMode === 'notes' ? <FaStop /> : <FaMicrophone />} {listeningMode === 'notes' ? 'Grabando...' : 'Dictar'}
                                </button>
                                <div className="flex-grow"></div>
                                <button onClick={() => activeNoteId && deleteNote(activeNoteId)} className="px-3 py-1 bg-red-50 text-red-500 rounded-lg text-xs hover:bg-red-100 flex items-center gap-2" disabled={!activeNoteId}><FaTrash /></button>
                            </div>
                            {showNoteList && (
                                <div className="bg-gray-50 rounded-lg p-2 max-h-40 overflow-y-auto border border-gray-200 shadow-inner">
                                    {notes.map(n => (
                                        <div key={n.id} onClick={() => { selectNote(n.id); setShowNoteList(false); }} className={`p-2 rounded cursor-pointer text-xs mb-1 ${activeNoteId === n.id ? 'bg-yellow-200 text-yellow-900 border border-yellow-300' : 'bg-white text-gray-600 hover:bg-gray-100'}`}>
                                            {n.text.substring(0, 30) || 'Nota vacía...'}<span className="block text-[10px] text-gray-400">{new Date(n.date).toLocaleDateString()}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                            <textarea
                                value={currentText}
                                onChange={(e) => setCurrentText(e.target.value)}
                                className="flex-1 bg-yellow-50/50 p-4 rounded-xl resize-none text-gray-700 leading-relaxed focus:outline-none focus:ring-2 focus:ring-yellow-200 border-none shadow-sm"
                                placeholder="Escribe aquí..."
                            ></textarea>
                            <p className="text-[10px] text-gray-400 text-right">Guardado automático</p>
                        </div>
                    )}

                    {/* NOTIF */}
                    {activeTab === 'notif' && (
                        <div className="space-y-3">
                            <p className="text-xs text-gray-400 font-bold uppercase mb-4">Centro de Notificaciones</p>
                            <div className="p-4 bg-blue-50 text-blue-800 rounded-lg text-xs leading-relaxed">
                                🔔 <strong>¡Hola!</strong> Este espacio es para tus <strong>alertas importantes</strong>: vencimientos de impuestos, clientes en mora, stock crítico, tareas pendientes o mensajes del equipo.
                            </div>
                            <div className="p-3 bg-white border-l-4 border-yellow-400 shadow-sm rounded-r-lg">
                                <p className="text-sm font-bold text-gray-700">Declaración de Renta</p>
                                <p className="text-xs text-gray-500">Recuerda preparar los informes para el cierre.</p>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* INDICATORS PANEL */}
            <EconomicIndicatorsPanel
                isOpen={showIndicators}
                onClose={() => setShowIndicators(false)}
                sidebarExpanded={isOpen || isPinned}
            />
        </div>
    );
}
