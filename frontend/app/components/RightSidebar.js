'use client';
import React, { useState, useEffect, useRef } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import {
    FaRobot, FaCalculator, FaStickyNote, FaBell,
    FaThumbtack, FaTimes, FaExpandAlt, FaMagic, FaPaperPlane,
    FaBackspace, FaTrash, FaMicrophone, FaStop, FaPlus, FaSave, FaList, FaShareSquare, FaHistory, FaClock
} from 'react-icons/fa';
import { CONTEXT_CONFIG } from '../config/rightSidebarConfig';
import { toast } from 'react-toastify';
import { apiService } from '@/lib/apiService';

// --- HELPER: FORMAT NUMBERS ---
const formatNumber = (numStr) => {
    if (!numStr || numStr === 'Error') return numStr;
    const parts = numStr.split('.');
    const integerPart = parts[0];
    const decimalPart = parts.length > 1 ? '.' + parts[1] : '';
    const formattedInt = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return formattedInt + decimalPart;
};

// --- HOOK: CALCULADORA (STANDARD LOGIC) ---
const useCalculator = () => {
    const [display, setDisplay] = useState('0');
    const [firstOperand, setFirstOperand] = useState(null);
    const [operator, setOperator] = useState(null);
    const [waitingForSecondOperand, setWaitingForSecondOperand] = useState(false);
    const [expression, setExpression] = useState(''); // To show invalidation state or history

    const calculate = (first, second, op) => {
        const a = parseFloat(first);
        const b = parseFloat(second);
        if (isNaN(a) || isNaN(b)) return 0;
        switch (op) {
            case '+': return a + b;
            case '-': return a - b;
            case '*': return a * b;
            case '/': return b === 0 ? 'Error' : a / b;
            default: return second;
        }
    };

    const handleInput = (val) => {
        try {
            // RESET
            if (val === 'C') {
                setDisplay('0');
                setFirstOperand(null);
                setOperator(null);
                setWaitingForSecondOperand(false);
                setExpression('');
                return;
            }

            // BACKSPACE
            if (val === 'DEL') {
                if (waitingForSecondOperand) return;
                setDisplay(prev => {
                    if (prev.length > 1) return prev.slice(0, -1);
                    return '0';
                });
                return;
            }

            // NUMBERS & DOT (Fixed: Accepts string digits for keyboard support)
            const isDigit = (v) => (typeof v === 'number') || (typeof v === 'string' && /^[0-9]$/.test(v));
            if (isDigit(val) || val === '.') {
                if (waitingForSecondOperand) {
                    setDisplay(String(val));
                    setWaitingForSecondOperand(false);
                } else {
                    if (val === '.') {
                        if (!display.includes('.')) setDisplay(prev => prev + '.');
                    } else {
                        setDisplay(prev => prev === '0' ? String(val) : prev + val);
                    }
                }
                return;
            }

            // OPERATORS
            if (['+', '-', '*', '/'].includes(val)) {
                setExpression(prev => {
                    if (waitingForSecondOperand) return prev.slice(0, -1) + val;
                    return prev + display + val;
                });

                if (firstOperand === null) {
                    setFirstOperand(display);
                } else if (operator) {
                    if (!waitingForSecondOperand) {
                        const result = calculate(firstOperand, display, operator);
                        setDisplay(String(result));
                        setFirstOperand(String(result));
                    }
                }
                setWaitingForSecondOperand(true);
                setOperator(val);
                return;
            }

            // EQUALS
            if (val === '=') {
                if (!operator || firstOperand === null) return;
                const result = calculate(firstOperand, display, operator);
                setExpression('');
                setDisplay(String(result));
                setFirstOperand(String(result));
                setOperator(null);
                setWaitingForSecondOperand(true);
            }
        } catch (err) {
            console.error("Calculator Error:", err);
            setDisplay('Error');
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
    const pathname = usePathname();
    const router = useRouter();
    const [activeTab, setActiveTab] = useState('ai');

    // Hooks
    const { display, expression, handleInput } = useCalculator();
    const { notes, activeNoteId, currentText, setCurrentText, createNote, deleteNote, selectNote } = useNotesManager();
    const [showNoteList, setShowNoteList] = useState(false);

    // AI & Voice State
    const [aiQuery, setAiQuery] = useState('');
    const [aiResponse, setAiResponse] = useState(null);
    const [isThinking, setIsThinking] = useState(false);

    // Voice Control
    const [listeningMode, setListeningMode] = useState(null);
    const listeningModeRef = useRef(null);
    const recognitionRef = useRef(null);

    // HISTORY STATE
    const [commandHistory, setCommandHistory] = useState([]);
    const [showHistory, setShowHistory] = useState(false);
    const [showLibraryTabInModal, setShowLibraryTabInModal] = useState(false); // <--- FIXED: Missing state


    // --- SAVED SEARCHES STATE ---
    const [savedSearches, setSavedSearches] = useState([]);
    const [isSavedSearchesLoading, setIsSavedSearchesLoading] = useState(false);
    const [editingSearchId, setEditingSearchId] = useState(null); // ID being edited
    const [editSearchTitle, setEditSearchTitle] = useState('');   // Title being edited

    const fetchSavedSearches = async () => {
        setIsSavedSearchesLoading(true);
        try {
            const token = localStorage.getItem('authToken');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/usuarios/busquedas/`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setSavedSearches(data);
            }
        } catch (err) {
            console.error("Error fetching saved searches", err);
        } finally {
            setIsSavedSearchesLoading(false);
        }
    };

    const saveSearch = async (cmd) => {
        const title = prompt("Nombre para esta búsqueda:", cmd.substring(0, 30));
        if (!title) return;

        try {
            const token = localStorage.getItem('authToken');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/usuarios/busquedas/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ titulo: title, comando: cmd })
            });
            if (res.ok) {
                toast.success("Búsqueda guardada en Biblioteca");
                fetchSavedSearches(); // Refresh list
            } else {
                toast.error("Error al guardar");
            }
        } catch (err) {
            console.error(err);
            toast.error("Error de conexión");
        }
    };

    const deleteSavedSearch = async (id) => {
        if (!confirm("¿Eliminar de la biblioteca?")) return;
        try {
            const token = localStorage.getItem('authToken');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/usuarios/busquedas/${id}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                toast.success("Eliminado");
                fetchSavedSearches();
            } else {
                toast.error("Error al eliminar");
            }
        } catch (err) {
            console.error(err);
            toast.error("Error de conexión");
        }
    };

    const updateSavedSearch = async (id, newTitle) => {
        try {
            const token = localStorage.getItem('authToken');
            const search = savedSearches.find(s => s.id === id);
            if (!search) return;

            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/usuarios/busquedas/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ titulo: newTitle, comando: search.comando })
            });
            if (res.ok) {
                toast.success("Actualizado");
                setEditingSearchId(null);
                fetchSavedSearches();
            } else {
                toast.error("Error al actualizar");
            }
        } catch (err) {
            console.error(err);
            toast.error("Error de conexión");
        }
    };

    // Load History & Saved Searches
    useEffect(() => {
        try {
            const saved = localStorage.getItem('voice_history');
            if (saved) {
                const parsed = JSON.parse(saved);
                if (Array.isArray(parsed)) setCommandHistory(parsed);
            }
            // Fetch saved searches on mount
            fetchSavedSearches();
        } catch (e) {
            console.error("History parse error", e);
        }
    }, []);

    const addToHistory = (text) => {
        if (!text || !text.trim()) return;
        const clean = text.trim();
        setCommandHistory(prev => {
            const filtered = prev.filter(t => t !== clean);
            const next = [clean, ...filtered].slice(0, 8); // Keep last 8
            localStorage.setItem('voice_history', JSON.stringify(next));
            return next;
        });
    };

    const handleHistoryClick = (cmd) => {
        setAiQuery(cmd);
        setShowHistory(false);
        // Optional: Auto submit or just fill?
        // User asked "traerle y cambiarle a algo", so just fill.
    };

    const handleSavedSearchClick = (cmd) => {
        setAiQuery(cmd);
        // Close modal? Maybe not yet, let user hit send
        // Or auto-send? Let's just fill for now to be safe
    };

    useEffect(() => {
        listeningModeRef.current = listeningMode;
    }, [listeningMode]);

    const currentContext = CONTEXT_CONFIG.find(ctx =>
        ctx.match.some(pathTrigger => pathname.toLowerCase().includes(pathTrigger.toLowerCase()))
    );

    // --- EXECUTE CLIENT ACTION (Ported from SmartSearchSection) ---
    const executeClientAction = async (data) => {
        const actionName = data.name || data.function_name;

        // --- INTERCEPTOR: ESTADO DE CUENTA CARTERA ---
        // Si el usuario pide "estado de cuenta", "cartera" o "cuanto debe" de un tercero, priorizar el módulo especializado
        // incluso si la IA clasificó la acción como 'generar_reporte_movimientos' o 'consultar_documento'.
        const queryLower = aiQuery.toLowerCase();
        const isCarteraIntent = queryLower.includes('estado de cuenta') || queryLower.includes('cartera') || queryLower.includes('cuanto debe') || queryLower.includes('saldo de');

        if (isCarteraIntent && (actionName === 'generar_reporte_movimientos' || actionName === 'consultar_documento')) {
            const p = data.parameters;
            const terceroIdentified = p.tercero || p.tercero_nombre || p.ai_tercero;

            if (terceroIdentified) {
                const params = new URLSearchParams();
                params.set('tercero', terceroIdentified);
                // Usar fecha fin o corte si existe, sino hoy
                if (p.fecha_corte || p.fecha_fin) params.set('fecha_corte', p.fecha_corte || p.fecha_fin);

                // AUTOMATION PARAMS
                const wantsPdf = p.formato === 'PDF' || (typeof p.formato === 'string' && p.formato.toLowerCase().includes('pdf'));
                if (wantsPdf) params.set('auto_pdf', 'true');
                if (p.whatsapp_destino) { params.set('wpp', p.whatsapp_destino); params.set('auto_pdf', 'true'); }
                if (p.email_destino) { params.set('email', p.email_destino); params.set('auto_pdf', 'true'); }

                router.push(`/contabilidad/reportes/estado-cuenta-cliente?${params.toString()}`);
                toast.success('IA: Abriendo Estado de Cuenta (Cartera)...');
                return;
            }
        }

        // --- INTERCEPTOR: MOVIMIENTOS INVENTARIO ---
        const isInventarioIntent = queryLower.includes('inventario') || queryLower.includes('kardex') || queryLower.includes('stock') || queryLower.includes('existencias');

        if (isInventarioIntent && (actionName === 'generar_reporte_movimientos' || actionName === 'consultar_documento')) {
            const p = data.parameters;
            const params = new URLSearchParams();
            if (p.fecha_inicio) params.set('fecha_inicio', p.fecha_inicio);
            if (p.fecha_fin) params.set('fecha_fin', p.fecha_fin);

            // Product variants
            console.log("AI INVENTORY DEBUG Params:", p);
            let prod = p.producto || p.producto_nombre || p.nombre_producto || p.articulo || p.referencia || p.search_term_prod || p.concepto || p.descripcion;

            // --- SAFETY NET: BLOCK GENERIC COMMAND PHRASES ---
            const invalidPhrases = [
                'movimientos detallados de inventario', 'movimientos de inventario',
                'reporte de inventario', 'informe de inventario',
                'inventario', 'kardex', 'stock', 'existencias',
                'movimientos detallados', 'movimientos'
            ];
            if (prod && invalidPhrases.some(phrase => prod.toLowerCase().trim() === phrase || prod.toLowerCase().includes('movimientos detallados'))) {
                console.warn("AI hallucinated command name as product. Ignoring:", prod);
                prod = null;
            }

            if (prod) params.set('search_term_prod', prod);

            if (p.tercero || p.tercero_nombre || p.ai_tercero) params.set('ai_tercero', p.tercero || p.tercero_nombre || p.ai_tercero);
            if (p.bodega || p.bodega_nombre) params.set('ai_bodega', p.bodega || p.bodega_nombre);
            if (p.grupo || p.grupo_nombre) params.set('ai_grupo', p.grupo || p.grupo_nombre);

            // Document Filtering (New) - Combine into search_term_doc which the page expects
            let docFilter = '';

            // Helper to clean hallucinations
            const cleanDocParam = (val) => {
                if (!val) return '';
                const v = val.toString().trim();
                const forbidden = ['inventario', 'movimientos', 'reporte', 'informe', 'kardex', 'stock', 'detallados', 'filtrar', 'documento', 'ref'];
                if (forbidden.some(f => v.toLowerCase().includes(f) && v.length < 15)) return ''; // Block typical hallucinations
                return v;
            };

            const rawTipo = p.tipo_documento || p.tipo || p.ai_tipo_doc;
            const rawNum = p.numero_documento || p.numero;

            const cleanTipo = cleanDocParam(rawTipo);
            const cleanNum = cleanDocParam(rawNum);

            // Smart combination to avoid "FV-FV-8"
            if (cleanNum) {
                // Format normalization: replace spaces/underscores with dashes for better matching
                const normalizedNum = cleanNum.replace(/[\s_]+/g, '-');

                // If number already contains the type (e.g. "FV-8" includes "FV"), don't prepend type
                if (cleanTipo && normalizedNum.toLowerCase().startsWith(cleanTipo.toLowerCase())) {
                    docFilter = normalizedNum;
                }
                else if (cleanTipo) {
                    docFilter = `${cleanTipo}-${normalizedNum}`;
                }
                else {
                    docFilter = normalizedNum;
                }
            } else if (cleanTipo) {
                docFilter = cleanTipo;
            }

            if (docFilter) params.set('search_term_doc', docFilter);

            params.set('trigger', 'ai_search');
            params.set('requestId', Date.now().toString()); // FORCE EFFECT RE-EXECUTION

            router.push(`/contabilidad/reportes/super-informe-inventarios?${params.toString()}`);
            toast.success('IA: Abriendo Movimientos de Inventario...');
            return;
        }

        if (actionName === 'navegar_a_pagina') {
            const modulo = data.parameters.modulo.toLowerCase();
            if (modulo.includes('contabil')) router.push('/contabilidad/documentos');
            else if (modulo.includes('factur')) router.push('/facturacion/crear');
            else if (modulo.includes('inventar')) router.push('/admin/inventario');
            else if (modulo.includes('nomin')) router.push('/nomina/liquidar');
            else {
                toast.success(`IA: Navegando a ${data.parameters.modulo}`);
                // Basic fallback if exact route not found, though backend usually helps
            }

        } else if (actionName === 'generar_reporte_movimientos') {
            const params = new URLSearchParams();
            const p = data.parameters;
            if (p.fecha_inicio) params.set('fecha_inicio', p.fecha_inicio);
            if (p.fecha_fin) params.set('fecha_fin', p.fecha_fin);
            if (p.cuenta || p.cuenta_nombre) params.set('cuenta', p.cuenta || p.cuenta_nombre);

            const wantsPdf = p.formato === 'PDF' || (typeof p.formato === 'string' && p.formato.toLowerCase().includes('pdf'));
            if (wantsPdf) params.set('auto_pdf', 'true');
            if (p.whatsapp_destino) { params.set('wpp', p.whatsapp_destino); params.set('auto_pdf', 'true'); }
            if (p.email_destino) { params.set('email', p.email_destino); params.set('auto_pdf', 'true'); }

            if (p.tercero || p.tercero_nombre) {
                params.set('tercero', p.tercero || p.tercero_nombre);
                router.push(`/contabilidad/reportes/tercero-cuenta?${params.toString()}`);
                toast.success('IA: Procesando Auxiliar por Tercero...');
            } else {
                router.push(`/contabilidad/reportes/auxiliar-cuenta?${params.toString()}`);
                toast.success('IA: Procesando Auxiliar por Cuenta...');
            }

        } else if (actionName === 'generar_balance_prueba') {
            const params = new URLSearchParams();
            const p = data.parameters;
            if (p.fecha_inicio) params.set('fecha_inicio', p.fecha_inicio);
            if (p.fecha_fin) params.set('fecha_fin', p.fecha_fin);
            if (p.nivel) params.set('nivel', p.nivel);

            const wantsPdf = p.formato === 'PDF' || (typeof p.formato === 'string' && p.formato.toLowerCase().includes('pdf'));
            if (wantsPdf) params.set('auto_pdf', 'true');
            if (p.whatsapp_destino) { params.set('wpp', p.whatsapp_destino); params.set('auto_pdf', 'true'); }

            router.push(`/contabilidad/reportes/balance-de-prueba?${params.toString()}`);
            toast.success('IA: Configurando Balance de Prueba...');

        } else if (actionName === 'generar_balance_general') {
            const params = new URLSearchParams();
            const p = data.parameters;
            if (p.fecha_corte) params.set('fecha_corte', p.fecha_corte);
            if (p.comparativo) params.set('comparativo', 'true');

            const wantsPdf = p.formato === 'PDF' || (typeof p.formato === 'string' && p.formato.toLowerCase().includes('pdf'));
            if (wantsPdf) params.set('auto_pdf', 'true');
            if (p.whatsapp_destino) { params.set('wpp', p.whatsapp_destino); params.set('auto_pdf', 'true'); }

            router.push(`/contabilidad/reportes/balance-general?${params.toString()}`);
            toast.success('IA: Configurando Balance General...');

        } else if (actionName === 'generar_estado_resultados') {
            const params = new URLSearchParams();
            const p = data.parameters;
            if (p.fecha_inicio) params.set('fecha_inicio', p.fecha_inicio);
            if (p.fecha_fin) params.set('fecha_fin', p.fecha_fin);

            const wantsPdf = p.formato === 'PDF' || (typeof p.formato === 'string' && p.formato.toLowerCase().includes('pdf'));
            if (wantsPdf) params.set('auto_pdf', 'true');
            if (p.whatsapp_destino) { params.set('wpp', p.whatsapp_destino); params.set('auto_pdf', 'true'); }

            router.push(`/contabilidad/reportes/estado-resultados?${params.toString()}`);
            toast.success('IA: Configurando Estado de Resultados...');

        } else if (actionName === 'crear_recurso') {
            const tipo = data.parameters.tipo || data.parameters.type;
            const creationMap = {
                'factura': { path: '/contabilidad/facturacion', param: '' },
                'compra': { path: '/contabilidad/compras', param: 'trigger=new_purchase' },
                'item': { path: '/admin/inventario', param: 'trigger=new_item' },
                'tercero': { path: '/admin/terceros/crear', param: '' },
                'traslado': { path: '/contabilidad/traslados', param: 'trigger=new_transfer' },
                'centro_costo': { path: '/admin/centros-costo', param: 'trigger=new_cc' },
                'unidad_ph': { path: '/ph/unidades/crear', param: '' },
                'bodega': { path: '/admin/inventario/parametros', param: 'trigger=tab_warehouses' },
                'receta': { path: '/produccion/recetas', param: 'trigger=new_recipe' },
                'nomina': { path: '/nomina/configuracion', param: 'trigger=new_payroll_type' },
                'plantilla': { path: '/admin/plantillas/crear', param: '' },
                'empresa': { path: '/admin/utilidades/soporte-util', param: 'trigger=tab_create_company' },
                'cuenta': { path: '/admin/plan-de-cuentas', param: 'trigger=new_account' },
                'tipo_documento': { path: '/admin/tipos-documento/crear', param: '' }
            };
            const target = creationMap[tipo];
            if (target) {
                const finalUrl = target.param ? `${target.path}?${target.param}` : target.path;
                router.push(finalUrl);
                toast.success(`IA: Abriendo creación de ${tipo}...`);
            } else {
                toast.warning(`IA: No sé cómo crear '${tipo}' aún.`);
            }

        } else if (actionName === 'consultar_documento') {
            const p = data.parameters;
            const params = new URLSearchParams();
            params.set('trigger', 'ai_search');
            // Improved robustness for parameter names
            if (p.tipo_documento || p.tipo || p.ai_tipo_doc) params.set('ai_tipo_doc', p.tipo_documento || p.tipo || p.ai_tipo_doc);
            if (p.numero_documento || p.numero) params.set('numero', p.numero_documento || p.numero);
            if (p.tercero || p.tercero_nombre || p.ai_tercero) params.set('ai_tercero', p.tercero || p.tercero_nombre || p.ai_tercero);
            if (p.cuenta || p.cuenta_nombre || p.ai_cuenta) params.set('ai_cuenta', p.cuenta || p.cuenta_nombre || p.ai_cuenta);
            if (p.fecha_inicio) params.set('fecha_inicio', p.fecha_inicio);
            if (p.fecha_fin) params.set('fecha_fin', p.fecha_fin);
            if (p.concepto || p.conceptoKeyword) params.set('conceptoKeyword', p.concepto || p.conceptoKeyword);

            router.push(`/contabilidad/reportes/super-informe?${params.toString()}`);
            toast.success('IA: Buscando documentos...');

        } else if (actionName === 'generar_backup') {
            toast.loading('IA: Generando respaldo completo...', { id: 'backup-toast' });
            try {
                const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/utilidades/backup-rapido`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` }
                });
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const link = document.createElement("a");
                    link.href = url;
                    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
                    link.download = `backup_completo_finaxis_${timestamp}.json`;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    toast.success("¡Respaldo descargado!", { id: 'backup-toast' });
                } else {
                    throw new Error("Failed to backup");
                }
            } catch (err) {
                console.error(err);
                toast.error("Error generando el respaldo.", { id: 'backup-toast' });
            }
        }
    };

    // --- SUBMIT LOGIC ---
    const handleAiSubmit = async (e, forcedQuery = null) => {
        if (e) e.preventDefault();
        const commandToRun = forcedQuery || aiQuery;
        if (!commandToRun || !commandToRun.trim()) return;

        // SAVE HISTOY
        addToHistory(commandToRun);

        setIsThinking(true);
        setAiResponse(null);
        try {
            const token = localStorage.getItem('authToken');
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const response = await fetch(`${baseUrl}/api/ai/process-command`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ command: commandToRun })
            });

            // Fallback for demo debug
            if (response.status === 401) {
                // Try debug endpoint if auth fails
            }

            const data = await response.json();

            if (data.error) {
                setAiResponse({ type: 'error', text: data.error });
            } else {
                setAiResponse({ type: 'success', text: data.message || `Acción procesada con éxito` });
                // EXECUTE THE ACTION
                await executeClientAction(data);
            }

        } catch (error) {
            setAiResponse({ type: 'error', text: 'Error conectando con el cerebro.' });
        } finally {
            setIsThinking(false);
            if (!forcedQuery) setAiQuery('');
        }
    };

    // --- VOICE SETUP ---
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
                    console.error("Speech error", e);
                    setListeningMode(null);
                    if (e.error !== 'no-speech') toast.error("Error de microfono.");
                };

                recognitionRef.current = recognition;
            }
        }
        return () => { if (recognitionRef.current) recognitionRef.current.abort(); };
    }, []);

    const toggleVoice = (mode) => {
        if (!recognitionRef.current) { toast.warning("Usa Chrome para voz."); return; }
        if (listeningMode === mode) {
            recognitionRef.current.stop();
            if (mode === 'ai' && aiQuery.trim()) {
                handleAiSubmit(null, aiQuery);
            }
            setListeningMode(null);
        } else {
            if (listeningMode) recognitionRef.current.abort();
            setListeningMode(mode);
            try {
                recognitionRef.current.start();
                toast.info(mode === 'ai' ? "Escuchando comando..." : "Dictando nota...");
            } catch (e) { console.error(e); }
        }
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
    // --- CALCULATOR ACTION ---
    const sendCalcToNote = () => {
        const val = formatNumber(display);
        const line = `\nCálculo: ${val}`;
        if (activeNoteId) {
            setCurrentText(prev => prev + line);
            toast.success("Agregado a nota activa");
        } else {
            createNote(`Nota de Cálculo${line}`);
            toast.success("Nueva nota creada");
        }
        setActiveTab('notes');
    };

    const handleTabClick = (tab) => { if (!isOpen && !isPinned) onToggle(true); setActiveTab(tab); };

    return (
        <div className={`fixed right-0 top-0 bottom-0 z-[60] transition-all duration-300 ease-spring ${widthClass} ${glassClass} flex`}>
            {/* ICONS */}
            <div className="w-12 flex flex-col items-center py-4 bg-gray-50/50 border-r border-gray-200 h-full flex-shrink-0">
                <button onClick={() => handleTabClick('ai')} className={`nav-item mb-6 p-2 rounded-xl transition-all ${activeTab === 'ai' && (isOpen || isPinned) ? 'bg-indigo-100 text-indigo-600' : 'text-gray-400 hover:text-indigo-500 hover:bg-indigo-50'}`}><FaRobot className="text-xl" /></button>
                <div className="w-6 h-[1px] bg-gray-200 mb-4"></div>
                <button onClick={() => handleTabClick('calc')} className={`nav-item p-2 mb-2 rounded-lg ${activeTab === 'calc' && (isOpen || isPinned) ? 'bg-blue-100 text-blue-600' : 'text-gray-400 hover:bg-blue-50'}`}><FaCalculator /></button>
                <button onClick={() => handleTabClick('notes')} className={`nav-item p-2 mb-2 rounded-lg ${activeTab === 'notes' && (isOpen || isPinned) ? 'bg-yellow-100 text-yellow-600' : 'text-gray-400 hover:bg-yellow-50'}`}><FaStickyNote /></button>
                <button onClick={() => handleTabClick('notif')} className={`nav-item p-2 rounded-lg ${activeTab === 'notif' && (isOpen || isPinned) ? 'bg-red-100 text-red-600' : 'text-gray-400 hover:text-red-500 hover:bg-red-50'}`}><FaBell /><span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full border border-white"></span></button>
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
                                    <div className="absolute top-2 right-2 flex gap-1">
                                        <button type="button" onClick={() => { setShowHistory(true); fetchSavedSearches(); }} className="text-gray-400 hover:text-indigo-600 p-1" title="Historial y Biblioteca"><FaHistory /></button>
                                        <button type="button" onClick={toggleVoice.bind(null, 'ai')} className={`p-2 rounded-full transition-all ${listeningMode === 'ai' ? 'bg-red-500 text-white animate-pulse' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}>{listeningMode === 'ai' ? <FaStop /> : <FaMicrophone />}</button>
                                        <button type="submit" disabled={isThinking} className="bg-indigo-600 text-white p-2 rounded-full hover:bg-indigo-700 transition-all disabled:opacity-50"><FaPaperPlane /></button>
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
                                    {!showLibraryTabInModal ? (
                                        // RECENT HISTORY
                                        <div className="flex-1 overflow-y-auto p-2">
                                            {commandHistory.length === 0 ? <p className="text-center text-gray-400 text-xs mt-4">Sin historial reciente.</p> : (
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
                                            )}
                                        </div>
                                    ) : (
                                        // SAVED LIBRARY
                                        <div className="flex-1 overflow-y-auto p-2">
                                            {isSavedSearchesLoading ? <p className="text-center text-xs text-gray-400 mt-4">Cargando...</p> :
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
                                                                    <div className="flex gap-1">
                                                                        <button onClick={() => deleteSavedSearch(item.id)} className="text-gray-300 hover:text-red-500 p-1"><FaTrash className="text-xs" /></button>
                                                                    </div>
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
                                                )}
                                        </div>
                                    )}
                                </div>
                            )}

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
                                {/* NEW BUTTON TO SEND TO NOTES */}
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
        </div>
    );
}
