"use client";
import { useState, useEffect } from 'react';
import { apiService } from '../../lib/apiService';
import { toast } from 'react-toastify';

export function useTutorAI() {
    const [messages, setMessages] = useState([]);
    const [isThinking, setIsThinking] = useState(false);

    // Cargar historial desde el Servidor (Persistencia Real)
    useEffect(() => {
        const fetchHistory = async () => {
            try {
                const response = await apiService.get('/ai/tutor/history');
                if (response.data && response.data.length > 0) {
                    setMessages(response.data);
                } else {
                    // Mensaje de bienvenida inicial si no hay historial
                    setMessages([
                        {
                            role: "assistant",
                            content: "👋 ¡Hola! Soy **Finaxis Tutor**. Estoy aquí para ayudarte a entender la plataforma y tus finanzas. ¿En qué puedo apoyarte hoy?"
                        }
                    ]);
                }
            } catch (e) {
                console.error("Error cargando historial de tutor", e);
                // Fallback a bienvenida
                setMessages([{ role: "assistant", content: "Error cargando historial. ¿En qué puedo apoyarte hoy?" }]);
            }
        };
        
        fetchHistory();
    }, []);

    const sendMessage = async (query) => {
        if (!query.trim()) return;

        const userMessage = { role: "user", content: query };
        const historyForContext = messages.slice(-10); // Enviamos contexto para la respuesta inmediata
        
        setMessages(prev => [...prev, userMessage]);
        setIsThinking(true);

        try {
            const response = await apiService.post('/ai/tutor', {
                query: query,
                history: historyForContext
            });

            const data = response.data;
            setIsThinking(false);

            if (data.error) {
                toast.error(`Tutor: ${data.error}`);
                return;
            }

            if (data.type === 'text') {
                setMessages(prev => [...prev, { role: "assistant", content: data.text }]);
            } else if (data.type === 'tool') {
                const cmdDesc = data.suggested_command || data.name;
                setMessages(prev => [...prev, { 
                    role: "assistant", 
                    content: `🔍 Entendido. Voy a procesar una consulta sobre: **${cmdDesc}**.`,
                    toolCall: data 
                }]);
            }

        } catch (error) {
            console.error(error);
            setIsThinking(false);
            toast.error("Error conectando con Finaxis Tutor.");
            setMessages(prev => [...prev, { role: "assistant", content: "❌ Lo siento, tuve un problema técnico. ¿Puedes repetir la pregunta?" }]);
        }
    };

    const clearChat = async () => {
        if (confirm("¿Quieres borrar permanentemente la conversación con el tutor?")) {
            try {
                await apiService.delete('/ai/tutor/history');
                setMessages([{ role: "assistant", content: "Chat reiniciado. ¿En qué puedo ayudarte?" }]);
                toast.success("Historial borrado.");
            } catch (e) {
                toast.error("No se pudo borrar el historial.");
            }
        }
    };

    return {
        messages,
        sendMessage,
        isThinking,
        clearChat
    };
}
