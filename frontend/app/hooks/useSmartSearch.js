"use client";
import { useState, useEffect, useRef, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'react-toastify';
import { menuStructure } from '../../lib/menuData';
import { commandDictionary } from '../../lib/commandDictionary';

export function useSmartSearch() {
    const router = useRouter();
    const [commandHistory, setCommandHistory] = useState([]);
    const [library, setLibrary] = useState([]);
    const [isLibraryLoading, setIsLibraryLoading] = useState(false);

    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [isListening, setIsListening] = useState(false);
    const [isThinking, setIsThinking] = useState(false);
    const [selectedIndex, setSelectedIndex] = useState(-1);
    const recognitionRef = useRef(null);

    const isCommandMode = query.startsWith(':') || (results.length > 0 && results[0].isCommand);

    const searchableItems = useMemo(() => {
        const items = [];
        const processLinks = (links, category) => {
            links.forEach(link => {
                items.push({
                    name: link.name,
                    description: link.description || '',
                    href: link.href,
                    icon: link.icon,
                    category: category,
                    keywords: `${link.name} ${link.description || ''} ${category}`.toLowerCase()
                });
            });
        };

        menuStructure.forEach(module => {
            if (module.links) processLinks(module.links, module.name);
            if (module.subgroups) {
                module.subgroups.forEach(sub => processLinks(sub.links, `${module.name} - ${sub.title}`));
            }
        });
        return items;
    }, []);

    const loadCommandHistory = () => {
        try {
            const saved = localStorage.getItem('voice_history');
            if (saved) {
                const parsed = JSON.parse(saved);
                if (Array.isArray(parsed)) {
                    const safeHistory = parsed.filter(item => typeof item === 'string' && item.trim().length > 0);
                    setCommandHistory(safeHistory);
                }
            }
        } catch (e) {
            console.error("Error parsing history", e);
            localStorage.removeItem('voice_history');
        }
    };

    const loadLibraryData = async () => {
        setIsLibraryLoading(true);
        try {
            const token = localStorage.getItem('authToken');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/usuarios/busquedas/`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setLibrary(data);
            }
        } catch (err) {
            console.error("Error fetching library", err);
        } finally {
            setIsLibraryLoading(false);
        }
    };

    const addToHistory = (text) => {
        if (!text || !text.trim()) return;
        const cleanText = text.trim();
        setCommandHistory(prev => {
            const filtered = prev.filter(item => item !== cleanText);
            const newHistory = [cleanText, ...filtered].slice(0, 6);
            localStorage.setItem('voice_history', JSON.stringify(newHistory));
            return newHistory;
        });
    };

    const addToLibrary = async (cmd) => {
        if (!cmd || !cmd.trim()) return;
        const title = prompt("Nombre para guardar este comando:", cmd.substring(0, 30));
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
                toast.success("Comando guardado en Biblioteca");
                loadLibraryData();
                // Notificar a otros componentes (como la barra lateral)
                window.dispatchEvent(new CustomEvent('show-ai-library'));
            } else {
                toast.error("Error al guardar en biblioteca");
            }
        } catch (err) {
            console.error(err);
            toast.error("Error de conexión");
        }
    };

    const deleteFromLibrary = async (id) => {
        if (!confirm("¿Eliminar de la biblioteca?")) return;
        try {
            const token = localStorage.getItem('authToken');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/usuarios/busquedas/${id}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                toast.success("Eliminado de la biblioteca");
                loadLibraryData();
            } else {
                toast.error("Error al eliminar");
            }
        } catch (err) {
            console.error(err);
            toast.error("Error de conexión");
        }
    };

    const updateLibraryTitle = async (id, newTitle) => {
        if (!newTitle || !newTitle.trim()) return;
        try {
            const token = localStorage.getItem('authToken');
            const search = library.find(s => s.id === id);
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
                toast.success("Nombre actualizado");
                loadLibraryData();
            } else {
                toast.error("Error al actualizar");
            }
        } catch (err) {
            console.error(err);
            toast.error("Error de conexión");
        }
    };

    useEffect(() => {
        loadCommandHistory();
        loadLibraryData();
    }, []);

    useEffect(() => {
        if (!query) {
            setResults([]);
            setSelectedIndex(-1);
            return;
        }

        if (query.startsWith(':')) {
            const commandQuery = query.substring(1).toLowerCase().trim();
            const matchedCommands = commandDictionary.filter(cmd =>
                cmd.triggers.some(trigger => trigger.includes(commandQuery)) ||
                (cmd.aliases && cmd.aliases.some(alias => alias.startsWith(commandQuery)))
            );

            if (matchedCommands.length > 0) {
                setResults(matchedCommands.map(cmd => ({
                    name: cmd.name,
                    description: cmd.description,
                    href: cmd.queryParam ? `${cmd.path}?${cmd.queryParam}` : cmd.path,
                    icon: cmd.icon,
                    category: cmd.category || 'Comando',
                    isCommand: true,
                    aliases: cmd.aliases
                })));
            } else {
                setResults([]);
            }
            setSelectedIndex(0);
            return;
        }

        const lowerQuery = query.toLowerCase();
        const terms = lowerQuery.split(' ').filter(term => term.length > 0);
        const matches = searchableItems.filter(item => terms.every(term => item.keywords.includes(term)));
        matches.sort((a, b) => {
            const aNameMatch = a.name.toLowerCase().includes(lowerQuery);
            const bNameMatch = b.name.toLowerCase().includes(lowerQuery);
            if (aNameMatch && !bNameMatch) return -1;
            if (!aNameMatch && bNameMatch) return 1;
            return 0;
        });
        setResults(matches.slice(0, 5));
        setSelectedIndex(matches.length > 0 ? 0 : -1);
    }, [query, searchableItems]);

    useEffect(() => {
        if (typeof window !== 'undefined' && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognitionRef.current = new SpeechRecognition();
            recognitionRef.current.continuous = true;
            recognitionRef.current.lang = 'es-CO';
            recognitionRef.current.interimResults = true;
            recognitionRef.current.maxAlternatives = 1;

            let silenceTimer = null;
            recognitionRef.current.onresult = (event) => {
                const currentText = Array.from(event.results).map(result => result[0].transcript).join('');
                setQuery(currentText);
                if (silenceTimer) clearTimeout(silenceTimer);
                silenceTimer = setTimeout(() => {
                    recognitionRef.current.stop();
                    setIsListening(false);
                    processVoiceCommand(currentText);
                }, 2000);
            };
            recognitionRef.current.onerror = (event) => {
                if (event.error !== 'no-speech') console.error("Speech error", event.error);
            };
        }
    }, [isListening]);

    const toggleListening = () => {
        if (isListening) {
            recognitionRef.current?.stop();
            setIsListening(false);
        } else {
            setQuery('');
            setIsListening(true);
            try {
                recognitionRef.current?.start();
            } catch (e) {
                console.error("Error starting speech recognition:", e);
                setIsListening(false);
                toast.error("Error iniciando micrófono.");
            }
        }
    };

    const processVoiceCommand = async (text) => {
        if (!text || !text.trim()) return;
        addToHistory(text);
        setIsThinking(true);
        try {
            const token = localStorage.getItem('authToken');
            if (!token) {
                toast.error("Sesión no válida.");
                setIsThinking(false);
                return;
            }
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || (typeof window !== 'undefined' ? `http://${window.location.hostname}:8000` : 'http://localhost:8000');
            const cleanCommand = text.startsWith(':') ? text.substring(1).trim() : text;

            let response = await fetch(`${baseUrl}/api/ai/process-command`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ command: cleanCommand })
            });

            if (response.status === 401) {
                response = await fetch(`${baseUrl}/api/ai/process-command-debug`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command: cleanCommand })
                });
            }

            const data = await response.json();
            setIsThinking(false);

            if (data.error) {
                toast.error(`IA: ${data.error}`);
                return;
            }

            console.log("--- IA RAW RESULT ---", data);
            await handleAIAction(data);
        } catch (error) {
            console.error(error);
            setIsThinking(false);
            toast.error("Error conectando con el cerebro AI.");
        }
    };

    const handleAIAction = async (data) => {
        const actionName = data.name || data.function_name;
        const p = data.parameters || {};
        const queryLower = (query || '').toLowerCase();

        // --- INTERCEPTOR: ESTADO DE CUENTA CARTERA ---
        const isCarteraIntent = queryLower.includes('estado de cuenta') || queryLower.includes('cartera') || queryLower.includes('cuanto debe') || queryLower.includes('saldo de');
        if (isCarteraIntent && (actionName === 'generar_reporte_movimientos' || actionName === 'consultar_documento')) {
            const terceroIdentified = p.tercero || p.tercero_nombre || p.ai_tercero;
            if (terceroIdentified) {
                const params = new URLSearchParams();
                params.set('tercero', terceroIdentified);
                if (p.fecha_corte || p.fecha_fin) params.set('fecha_corte', p.fecha_corte || p.fecha_fin);
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
            const params = new URLSearchParams();
            if (p.fecha_inicio) params.set('fecha_inicio', p.fecha_inicio);
            if (p.fecha_fin) params.set('fecha_fin', p.fecha_fin);
            let prod = p.producto || p.producto_nombre || p.nombre_producto || p.articulo || p.referencia || p.search_term_prod || p.concepto || p.descripcion;
            const invalidPhrases = ['movimientos detallados de inventario', 'movimientos de inventario', 'reporte de inventario', 'informe de inventario', 'inventario', 'kardex', 'stock', 'existencias', 'movimientos detallados', 'movimientos'];
            if (prod && invalidPhrases.some(phrase => prod.toLowerCase().trim() === phrase)) prod = null;
            if (prod) params.set('search_term_prod', prod);
            if (p.tercero || p.tercero_nombre || p.ai_tercero) params.set('ai_tercero', p.tercero || p.tercero_nombre || p.ai_tercero);
            if (p.bodega || p.bodega_nombre) params.set('ai_bodega', p.bodega || p.bodega_nombre);
            if (p.grupo || p.grupo_nombre) params.set('ai_grupo', p.grupo || p.grupo_nombre);
            let docFilter = '';
            const cleanDocParam = (val) => {
                if (!val) return '';
                const v = val.toString().trim();
                const forbidden = ['inventario', 'movimientos', 'reporte', 'informe', 'kardex', 'stock', 'detallados', 'filtrar', 'documento', 'ref'];
                if (forbidden.some(f => v.toLowerCase().includes(f) && v.length < 15)) return '';
                return v;
            };
            const rawTipo = p.tipo_documento || p.tipo || p.ai_tipo_doc;
            const rawNum = p.numero_documento || p.numero;
            const cleanTipo = cleanDocParam(rawTipo);
            const cleanNum = cleanDocParam(rawNum);
            if (cleanNum) {
                const normalizedNum = cleanNum.replace(/[\s_]+/g, '-');
                if (cleanTipo && normalizedNum.toLowerCase().startsWith(cleanTipo.toLowerCase())) docFilter = normalizedNum;
                else if (cleanTipo) docFilter = `${cleanTipo}-${normalizedNum}`;
                else docFilter = normalizedNum;
            } else if (cleanTipo) docFilter = cleanTipo;
            if (docFilter) params.set('search_term_doc', docFilter);
            params.set('trigger', 'ai_search');
            params.set('requestId', Date.now().toString());
            router.push(`/contabilidad/reportes/super-informe-inventarios?${params.toString()}`);
            toast.success('IA: Abriendo Movimientos de Inventario...');
            return;
        }

        if (actionName === 'navegar_a_pagina') {
            const modulo = (p.modulo || '').toLowerCase();
            if (modulo.includes('contabil')) router.push('/contabilidad/documentos');
            else if (modulo.includes('factur')) router.push('/facturacion/crear');
            else if (modulo.includes('inventar')) router.push('/admin/inventario');
            else if (modulo.includes('nomin')) router.push('/nomina/liquidar');
            else toast.success(`IA: Navegando a ${p.modulo}`);
        } else if (actionName === 'generar_reporte_movimientos') {
            const params = new URLSearchParams();
            if (p.fecha_inicio) params.set('fecha_inicio', p.fecha_inicio);
            if (p.fecha_fin) params.set('fecha_fin', p.fecha_fin);

            // Extracción robusta de CUENTA
            const cuentaVal = p.cuenta || p.cuenta_nombre || p.ai_cuenta || p.concepto || p.cuenta_codigo;
            if (cuentaVal) params.set('cuenta', cuentaVal);

            const wantsPdf = p.formato === 'PDF' || (typeof p.formato === 'string' && p.formato.toLowerCase().includes('pdf'));
            if (wantsPdf) params.set('auto_pdf', 'true');
            if (p.whatsapp_destino) { params.set('wpp', p.whatsapp_destino); params.set('auto_pdf', 'true'); }
            if (p.email_destino) { params.set('email', p.email_destino); params.set('auto_pdf', 'true'); }

            // Extracción robusta de TERCERO
            const terceroVal = p.tercero || p.tercero_nombre || p.ai_tercero || p.nombre_tercero;
            if (terceroVal) {
                params.set('tercero', terceroVal);
                router.push(`/contabilidad/reportes/tercero-cuenta?${params.toString()}`);
                toast.success('IA: Procesando Auxiliar por Tercero...');
            } else {
                router.push(`/contabilidad/reportes/auxiliar-cuenta?${params.toString()}`);
                toast.success('IA: Procesando Auxiliar por Cuenta...');
            }
        } else if (actionName === 'generar_balance_prueba') {
            const params = new URLSearchParams();
            if (p.fecha_inicio) params.set('fecha_inicio', p.fecha_inicio);
            if (p.fecha_fin) params.set('fecha_fin', p.fecha_fin);
            if (p.nivel) params.set('nivel', p.nivel);
            const wantsPdf = p.formato === 'PDF' || (typeof p.formato === 'string' && p.formato.toLowerCase().includes('pdf'));
            if (wantsPdf) params.set('auto_pdf', 'true');
            if (p.whatsapp_destino) { params.set('wpp', p.whatsapp_destino); params.set('auto_pdf', 'true'); }
            router.push(`/contabilidad/reportes/balance-de-prueba?${params.toString()}`);
            toast.success('IA: Configurando Balance de Prueba...');
        } else if (actionName === 'generar_relacion_saldos') {
            const params = new URLSearchParams();
            if (p.fecha_inicio) params.set('fecha_inicio', p.fecha_inicio);
            if (p.fecha_fin) params.set('fecha_fin', p.fecha_fin);

            const cuentaVal = p.cuenta || p.cuenta_nombre || p.ai_cuenta || p.concepto || p.cuenta_codigo;
            if (cuentaVal) params.set('cuenta', cuentaVal);

            const terceroVal = p.tercero || p.tercero_nombre || p.ai_tercero || p.nombre_tercero;
            if (terceroVal) params.set('tercero', terceroVal);

            params.set('trigger', 'ai');

            const wantsPdf = p.formato === 'PDF' || (typeof p.formato === 'string' && p.formato.toLowerCase().includes('pdf'));
            if (wantsPdf) params.set('auto_pdf', 'true');

            router.push(`/contabilidad/reportes/relacion-saldos?${params.toString()}`);
            toast.success('IA: Consultando Relación de Saldos...');
        } else if (actionName === 'generar_balance_general') {
            const params = new URLSearchParams();
            if (p.fecha_corte) params.set('fecha_corte', p.fecha_corte);
            if (p.comparativo) params.set('comparativo', 'true');
            const wantsPdf = p.formato === 'PDF' || (typeof p.formato === 'string' && p.formato.toLowerCase().includes('pdf'));
            if (wantsPdf) params.set('auto_pdf', 'true');
            if (p.whatsapp_destino) { params.set('wpp', p.whatsapp_destino); params.set('auto_pdf', 'true'); }
            router.push(`/contabilidad/reportes/balance-general?${params.toString()}`);
            toast.success('IA: Configurando Balance General...');
        } else if (actionName === 'generar_estado_resultados') {
            const params = new URLSearchParams();
            if (p.fecha_inicio) params.set('fecha_inicio', p.fecha_inicio);
            if (p.fecha_fin) params.set('fecha_fin', p.fecha_fin);
            const wantsPdf = p.formato === 'PDF' || (typeof p.formato === 'string' && p.formato.toLowerCase().includes('pdf'));
            if (wantsPdf) params.set('auto_pdf', 'true');
            if (p.whatsapp_destino) { params.set('wpp', p.whatsapp_destino); params.set('auto_pdf', 'true'); }
            router.push(`/contabilidad/reportes/estado-resultados?${params.toString()}`);
            toast.success('IA: Configurando Estado de Resultados...');
        } else if (actionName === 'crear_recurso') {
            const tipo = p.tipo || p.type;
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
            } else toast.warning(`IA: No sé cómo crear '${tipo}' aún.`);
        } else if (actionName === 'consultar_documento') {
            const params = new URLSearchParams();
            params.set('trigger', 'ai_search');
            if (p.tipo_documento || p.tipo || p.ai_tipo_doc) params.set('ai_tipo_doc', p.tipo_documento || p.tipo || p.ai_tipo_doc);
            if (p.numero_documento || p.numero) params.set('numero', p.numero_documento || p.numero);

            const terceroVal = p.tercero || p.tercero_nombre || p.ai_tercero || p.nombre_tercero;
            if (terceroVal) params.set('ai_tercero', terceroVal);

            const cuentaVal = p.cuenta || p.cuenta_nombre || p.ai_cuenta || p.concepto || p.cuenta_codigo;
            if (cuentaVal) params.set('ai_cuenta', cuentaVal);

            if (p.fecha_inicio) params.set('fecha_inicio', p.fecha_inicio);
            if (p.fecha_fin) params.set('fecha_fin', p.fecha_fin);
            if (p.concepto || p.conceptoKeyword) params.set('conceptoKeyword', p.concepto || p.conceptoKeyword);
            router.push(`/contabilidad/reportes/super-informe?${params.toString()}`);
            toast.success('IA: Buscando documentos...');
        } else if (actionName === 'extraer_datos_documento' && p.plantilla) {
            const params = new URLSearchParams();
            params.set('ai_plantilla', p.plantilla);
            if (p.tercero) params.set('ai_tercero', p.tercero);
            const val = p.valor || p.monto || p.debito || p.credito || p.importe;
            if (val) params.set('ai_valor', val);
            params.set('ai_autosave', 'true');
            router.push(`/contabilidad/captura-rapida?${params.toString()}`);
            toast.success('IA: Abriendo Captura Rápida...');
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
                } else throw new Error("Failed to backup");
            } catch (err) {
                console.error(err);
                toast.error("Error generando el respaldo.", { id: 'backup-toast' });
            }
        } else toast.info(`IA sugiere acción desconocida o sin interceptor: ${actionName}`);
    };

    const handleSelectResult = (item) => {
        if (!item) return;
        setIsThinking(true);
        setTimeout(() => {
            router.push(item.href);
            setIsThinking(false);
        }, 300);
    };

    return {
        query, setQuery, results, isListening, isThinking, isCommandMode, commandHistory, library, isLibraryLoading, selectedIndex, setSelectedIndex,
        toggleListening, processVoiceCommand, handleSelectResult, addToLibrary, deleteFromLibrary, updateLibraryTitle,
        loadLibraryData, loadCommandHistory, addToHistory,
        showHistory: (results.length > 0 || (!query && (commandHistory.length > 0 || library.length > 0))),
    };
}
