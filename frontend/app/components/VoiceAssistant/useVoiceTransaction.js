import { useState, useCallback } from 'react';
import { apiService } from '@/lib/apiService';
import { toast } from 'react-toastify';

export const useVoiceTransaction = () => {
    // Estado del documento en construcción
    const [docState, setDocState] = useState({
        step: 'IDLE', // IDLE, LISTENING, PROCESSING, REVIEW, SAVING
        tipo_documento: '', // 'Recibo de Caja', 'Factura de Venta', etc.
        tercero: null, // Objeto { id, nombre, ... }
        fecha: new Date().toISOString().split('T')[0],
        movimientos: [], // Array de { cuenta, concepto, debito, credito }
        total_debito: 0,
        total_credito: 0
    });

    const [assistantMessage, setAssistantMessage] = useState("¿Qué deseas hacer hoy? (Ej: 'Crear Recibo')");

    // Reiniciar estado
    const resetTransaction = useCallback(() => {
        setDocState({
            step: 'IDLE',
            tipo_documento: '',
            tercero: null,
            fecha: new Date().toISOString().split('T')[0],
            movimientos: [],
            total_debito: 0,
            total_credito: 0
        });
        setAssistantMessage("¿Qué deseas hacer hoy?");
    }, []);

    // Procesar comando de voz con contexto
    const processVoiceCommand = useCallback(async (text) => {
        if (!text.trim()) return;

        setDocState(prev => ({ ...prev, step: 'PROCESSING' }));

        try {
            // Construimos el contexto para enviar a la IA
            const context = {
                current_step: docState.step,
                current_doc_type: docState.tipo_documento,
                has_tercero: !!docState.tercero,
                lines_count: docState.movimientos.length,
                total_gap: docState.total_debito - docState.total_credito
            };

            const response = await apiService.post('/ai/process-command', {
                command: text,
                context: context
            });

            const toolCall = response?.tool_calls?.[0]; // Asumimos estructura de Gemini/OpenAI wrapper

            if (toolCall) {
                const args = toolCall.args || {};

                // CASO 1: La IA decide correctamente usar el extractor
                if (toolCall.name === 'extraer_datos_documento') {
                    handleExtraction(args);
                }
                // CASO 2: La IA usa 'crear_recurso' (Fallback)
                else if (toolCall.name === 'crear_recurso') {
                    const docTypes = ['factura', 'compra', 'traslado', 'recibo', 'comprobante', 'documento'];
                    if (docTypes.some(t => args.tipo && args.tipo.toLowerCase().includes(t))) {
                        handleExtraction({
                            accion: 'DEFINIR_CABECERA',
                            tipo_documento: args.tipo
                        });
                    } else {
                        setAssistantMessage(`Entendido. Te llevaré a crear ${args.tipo}.`);
                    }
                }
                // CASO 3: La IA usa 'navegar_a_pagina' para crear algo (Fallback)
                else if (toolCall.name === 'navegar_a_pagina') {
                    if (args.accion && ['crear', 'nuevo', 'alta'].some(a => args.accion.toLowerCase().includes(a))) {
                        handleExtraction({
                            accion: 'DEFINIR_CABECERA',
                            tipo_documento: args.modulo // Usamos el módulo como proxy del tipo
                        });
                    } else {
                        setAssistantMessage(`Navegando a ${args.modulo}...`);
                        // Aquí podríamos cerrar el overlay automágicamente
                    }
                }
                // CASO 4: Otra herramienta no soportada en modo asistente
                else {
                    setAssistantMessage(`Intenté usar '${toolCall.name}', pero no sé cómo manejarlo aquí.`);
                }
            } else {
                // No tool call
                setAssistantMessage("No entendí tu solicitud. Intenta decir: 'Crear recibo de caja'.");
                setDocState(prev => ({ ...prev, step: 'IDLE' }));
            }

        } catch (error) {
            console.error("Error processing voice command:", error);
            setAssistantMessage("Tuve un error procesando eso. ¿Puedes repetir?");
            setDocState(prev => ({ ...prev, step: 'IDLE' }));
            // En un caso real, 'IDLE' podría ser 'ACTIVE_SESSION' para no cerrar el chat
        }
    }, [docState]);

    // Lógica pura de actualización de estado basada en la respuesta de la IA
    const handleExtraction = (data) => {
        setDocState(prev => {
            const newState = { ...prev, step: 'REVIEW' }; // Por defecto volvemos a modo revisión/espera
            let message = "Actualizado.";

            // 1. Cabecera
            if (data.tipo_documento) {
                newState.tipo_documento = data.tipo_documento;
                message = `Iniciando ${data.tipo_documento}. ¿Quién es el tercero?`;
            }
            if (data.tercero) {
                // TODO: En un sistema real, esto buscaría el ID en el backend.
                // Por ahora simulamos que "lo encontró"
                newState.tercero = { id: 0, nombre: data.tercero };
                message = `Asignado a ${data.tercero}. ¿Qué agregamos?`;
            }
            if (data.fecha) newState.fecha = data.fecha;

            // 2. Líneas
            if (data.accion === 'AGREGAR_LINEA' || (data.debito || data.credito)) {
                // Validar si es una línea válida
                if (data.cuenta && (data.debito || data.credito)) {
                    newState.movimientos = [
                        ...prev.movimientos,
                        {
                            cuenta_nombre: data.cuenta, // En backend se resolvería ID
                            concepto: data.concepto || prev.tipo_documento,
                            debito: data.debito || 0,
                            credito: data.credito || 0
                        }
                    ];
                    message = `Agregada línea: ${data.cuenta} por ${data.debito || data.credito}.`;
                }
            }

            // 3. Recálculo de totales
            newState.total_debito = newState.movimientos.reduce((sum, m) => sum + m.debito, 0);
            newState.total_credito = newState.movimientos.reduce((sum, m) => sum + m.credito, 0);
            const diff = newState.total_debito - newState.total_credito;

            if (diff === 0 && newState.movimientos.length > 0) {
                message += " Documento cuadrado. ¿Deseas guardar?";
            } else if (Math.abs(diff) > 0) {
                message += ` Diferencia de ${Math.abs(diff)}.`;
            }

            // 4. Acción de finalización
            if (data.accion === 'FINALIZAR') {
                if (diff === 0) {
                    newState.step = 'SAVING';
                    // Aquí se dispararía saveDocument(newState)
                    message = "Guardando documento...";
                } else {
                    message = "No puedo guardar, el documento está descuadrado.";
                }
            } else if (data.accion === 'CANCELAR') {
                resetTransaction();
                return { ...prev, step: 'IDLE' }; // Short circuit
            }

            setAssistantMessage(message);
            return newState;
        });
    };

    return {
        docState,
        assistantMessage,
        processVoiceCommand,
        resetTransaction,
        // Helper para inyectar manualmente si se desea
        updateStateManual: setDocState
    };
};
