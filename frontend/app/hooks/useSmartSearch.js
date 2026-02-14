"use client";
import { useState, useEffect, useRef, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'react-toastify';
import { menuStructure } from '../../lib/menuData';
import { commandDictionary } from '../../lib/commandDictionary';
import { apiService } from '../../lib/apiService';

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
            const res = await apiService.get('/usuarios/busquedas/');
            setLibrary(res.data);
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
            await apiService.post('/usuarios/busquedas/', {
                titulo: title,
                comando: cmd
            });
            toast.success("Guardado en biblioteca");
            loadLibraryData();
            // Notificar a otros componentes (como la barra lateral)
            window.dispatchEvent(new CustomEvent('show-ai-library'));
        } catch (err) {
            console.error(err);
            toast.error("Error al guardar en biblioteca");
        }
    };

    const deleteFromLibrary = async (id) => {
        if (!confirm("¿Eliminar de la biblioteca?")) return;
        try {
            await apiService.delete(`/usuarios/busquedas/${id}`);
            toast.success("Eliminado de la biblioteca");
            loadLibraryData();
        } catch (err) {
            console.error(err);
            toast.error("Error al eliminar");
        }
    };

    const updateLibraryTitle = async (id, newTitle) => {
        if (!newTitle || !newTitle.trim()) return;
        try {
            const search = library.find(s => s.id === id);
            if (!search) return;

            await apiService.put(`/usuarios/busquedas/${id}`, {
                titulo: newTitle,
                comando: search.comando
            });
            toast.success("Nombre actualizado");
            loadLibraryData();
        } catch (err) {
            console.error(err);
            toast.error("Error al actualizar");
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

    const queryRef = useRef('');

    useEffect(() => {
        if (typeof window !== 'undefined' && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognitionRef.current = new SpeechRecognition();
            recognitionRef.current.continuous = false;
            recognitionRef.current.lang = 'es-CO';
            recognitionRef.current.interimResults = true;

            recognitionRef.current.onresult = (event) => {
                let finalTranscript = '';
                let interimTranscript = '';

                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    if (event.results[i].isFinal) {
                        finalTranscript += event.results[i][0].transcript;
                    } else {
                        interimTranscript += event.results[i][0].transcript;
                    }
                }

                const currentText = finalTranscript || interimTranscript;
                if (currentText) {
                    setQuery(currentText);
                    queryRef.current = currentText;
                }
            };

            recognitionRef.current.onend = () => {
                setIsListening(false);
                const finalQuery = queryRef.current;
                if (finalQuery && finalQuery.trim().length > 2) {
                    processVoiceCommand(finalQuery);
                }
                queryRef.current = '';
            };

            recognitionRef.current.onerror = (event) => {
                if (event.error !== 'no-speech') {
                    console.error("Speech error", event.error);
                    toast.error("Error de micrófono: " + event.error);
                }
                setIsListening(false);
            };
        }

        return () => {
            if (recognitionRef.current) {
                recognitionRef.current.stop();
            }
        };
    }, []);

    const toggleListening = () => {
        if (isListening) {
            recognitionRef.current?.stop();
            setIsListening(false);
        } else {
            setQuery('');
            queryRef.current = '';
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
            const cleanCommand = text.startsWith(':') ? text.substring(1).trim() : text;

            const response = await apiService.post('/ai/process-command', { command: cleanCommand });
            const data = response.data;
            setIsThinking(false);

            if (data.error) {
                toast.error(`IA: ${data.error}`);
                return;
            }

            console.log("--- IA RAW RESULT ---", data);
            await handleAIAction(data, text); // Pasar text para contexto extra
        } catch (error) {
            console.error(error);
            setIsThinking(false);
            toast.error("Error conectando con el cerebro AI.");
        }
    };

    const handleAIAction = async (data, text = null) => {
        const actionName = data.name || data.function_name;
        const p = data.parameters || {};
        const queryLower = (text || query || '').toLowerCase();

        // --- INTELLIGENCE: GASTOS / INGRESOS ---
        const isGastos = queryLower.includes('gasto') || queryLower.includes('egreso') || queryLower.includes('pago a');
        const isIngresos = queryLower.includes('ingreso') || queryLower.includes('venta') || queryLower.includes('recuperacion');

        // --- INTERCEPTOR: ESTADO DE CUENTA CARTERA / SALDOS ---
        const isSaldosIntent = queryLower.includes('saldo') || queryLower.includes('cuanto debe') || queryLower.includes('deuda') || isGastos || isIngresos;
        const isMovimientosIntent = queryLower.includes('movimiento') || queryLower.includes('detalle') || queryLower.includes('auxiliar');

        if ((isSaldosIntent || isMovimientosIntent) && (actionName === 'generar_reporte_movimientos' || actionName === 'consultar_documento' || actionName === 'generar_relacion_saldos')) {
            const terceroIdentified = p.tercero || p.tercero_nombre || p.ai_tercero || p.nombre_tercero;
            const params = new URLSearchParams();

            if (terceroIdentified) params.set('tercero', terceroIdentified);
            if (isGastos) params.set('cuenta', '5');
            else if (isIngresos) params.set('cuenta', '4');
            else if (p.cuenta || p.ai_cuenta) params.set('cuenta', p.cuenta || p.ai_cuenta);

            if (p.fecha_inicio) params.set('fecha_inicio', p.fecha_inicio);
            if (p.fecha_fin || p.fecha_corte) params.set('fecha_fin', p.fecha_fin || p.fecha_corte);

            params.set('trigger', 'ai');
            const wantsPdf = p.formato === 'PDF' || (typeof p.formato === 'string' && p.formato.toLowerCase().includes('pdf'));
            if (wantsPdf) params.set('auto_pdf', 'true');

            if (isMovimientosIntent) {
                router.push(`/contabilidad/reportes/tercero-cuenta?${params.toString()}`);
                toast.success(`IA: Consultando Movimientos (${isGastos ? 'Gastos' : isIngresos ? 'Ingresos' : 'Detallados'})...`);
            } else {
                router.push(`/contabilidad/reportes/relacion-saldos?${params.toString()}`);
                toast.success(`IA: Consultando Saldos (${isGastos ? 'Gastos' : isIngresos ? 'Ingresos' : 'General'})...`);
            }
            return;
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
        } else if (actionName === 'generar_reporte_movimientos' || actionName === 'generar_auxiliar_cuenta') {
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
            const includesTerceroIntent = queryLower.includes('tercero');

            if (terceroVal || includesTerceroIntent) {
                if (terceroVal) params.set('tercero', terceroVal);

                // Si tenemos cuenta pero no un tercero específico, es probable que quiera "Por Cuenta (Inverso)"
                if ((p.cuenta || p.ai_cuenta) && !terceroVal) {
                    params.set('mode', 'cuenta_first');
                }

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

            // JUEZ: Divorcio del Nivel 1. Si no viene nivel o si es 1, forzamos a 7.
            const forcedNivel = (p.nivel && parseInt(p.nivel) > 1) ? p.nivel : '7';
            params.set('nivel', forcedNivel);
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
        } else if (actionName === 'generar_balance_general' || actionName === 'generar_estado_situacion_financiera') {
            const params = new URLSearchParams();
            // Fallback: Si no viene fecha_corte, intenta usar fecha_fin o fecha_inicio (o hoy)
            const fCorte = p.fecha_corte || p.fecha_fin || p.fecha_inicio || new Date().toISOString().split('T')[0];
            params.set('fecha_corte', fCorte);

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
        } else if (actionName === 'consultar_documento' || actionName === 'consultar_comprobante_diario') {
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

            // Filtro por valor/monto
            const val = p.valor || p.monto || p.importe || p.total;
            if (val) params.set('ai_valor', val);

            router.push(`/contabilidad/reportes/super-informe?${params.toString()}`);
            toast.success('IA: Buscando documentos...');
        } else if (actionName === 'buscar_recurso_o_reporte') {
            const termino = p.termino_busqueda;
            if (!termino) {
                toast.error("IA: No se proporcionó un reporte específico.");
                return;
            }

            // Fuzzy resolution: Busca en el menú el nombre más parecido
            const match = searchableItems
                .map(item => {
                    const lowName = item.name.toLowerCase();
                    const lowTerm = termino.toLowerCase();
                    let score = 0;
                    if (lowName === lowTerm) score = 100;
                    else if (lowName.startsWith(lowTerm)) score = 50;
                    else if (lowName.includes(lowTerm)) score = 30;
                    return { item, score };
                })
                .filter(m => m.score > 0)
                .sort((a, b) => b.score - a.score)[0]?.item;

            if (match) {
                const params = new URLSearchParams();
                // Parámetros universales
                if (p.fecha_inicio) params.set('fecha_inicio', p.fecha_inicio);
                if (p.fecha_fin) params.set('fecha_fin', p.fecha_fin);
                if (p.fecha_corte) params.set('fecha_corte', p.fecha_corte);
                if (p.nivel) params.set('nivel', p.nivel);

                // Otros filtros específicos
                if (p.filtros && typeof p.filtros === 'object') {
                    Object.entries(p.filtros).forEach(([k, v]) => params.set(k, v));
                }

                // PDF Automation
                const wantsPdf = p.formato === 'PDF' || (typeof p.formato === 'string' && p.formato.toLowerCase().includes('pdf'));
                if (wantsPdf) params.set('auto_pdf', 'true');

                const connector = match.href.includes('?') ? '&' : '?';
                router.push(`${match.href}${connector}${params.toString()}`);
                toast.success(`IA: Navegando a '${match.name}'...`);
            } else {
                toast.warning(`IA: No encontré ningún reporte que coincida con '${termino}'.`);
            }
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
                const response = await apiService.post('/utilidades/backup-rapido', {}, {
                    responseType: 'blob'
                });

                const url = window.URL.createObjectURL(new Blob([response.data]));
                const link = document.createElement("a");
                link.href = url;
                const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
                link.download = `backup_completo_finaxis_${timestamp}.json`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                toast.success('Respaldo generado con éxito', { id: 'backup-toast' });
            } catch (err) {
                console.error(err);
                toast.error('Error al generar respaldo', { id: 'backup-toast' });
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
