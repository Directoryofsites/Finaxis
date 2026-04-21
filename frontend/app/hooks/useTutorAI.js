"use client";
import { useState, useEffect } from 'react';
import { apiService } from '../../lib/apiService';
import { toast } from 'react-toastify';

export function useTutorAI() {
    const [messages, setMessages] = useState([]);
    const [isThinking, setIsThinking] = useState(false);

    // Cargar historial al iniciar
    useEffect(() => {
        const saved = localStorage.getItem('finaxis_tutor_chat');
        if (saved) {
            try {
                setMessages(JSON.parse(saved));
            } catch (e) {
                console.error("Error cargando historial de tutor", e);
            }
        } else {
            // Mensaje de bienvenida inicial
            const welcome = [
                {
                    role: "assistant",
                    content: "👋 ¡Hola! Soy **Finaxis Tutor**. Estoy aquí para ayudarte a entender la plataforma y tus finanzas. ¿En qué puedo apoyarte hoy?"
                }
            ];
            setMessages(welcome);
        }
    }, []);

    // Guardar historial cuando cambie
    useEffect(() => {
        if (messages.length > 0) {
            localStorage.setItem('finaxis_tutor_chat', JSON.stringify(messages));
        }
    }, [messages]);

    const sendMessage = async (query) => {
        if (!query.trim()) return;

        const userMessage = { role: "user", content: query };
        const newMessages = [...messages, userMessage];
        setMessages(newMessages);
        setIsThinking(true);

        try {
            const response = await apiService.post('/ai/tutor', {
                query: query,
                history: messages.slice(-10) // Enviamos los últimos 10 para contexto
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
                // Si la IA sugiere una herramienta, informamos al usuario y podríamos ejecutar acción
                setMessages(prev => [...prev, { 
                    role: "assistant", 
                    content: `🔍 Entendido. Voy a procesar una consulta sobre: **${data.name}**.`,
                    toolCall: data 
                }]);
                
                // Aquí podrías disparar el evento para navegar al reporte si fuera necesario
                // window.dispatchEvent(new CustomEvent('ai-tool-action', { detail: data }));
            }

        } catch (error) {
            console.error(error);
            setIsThinking(false);
            toast.error("Error conectando con Finaxis Tutor.");
            setMessages(prev => [...prev, { role: "assistant", content: "❌ Lo siento, tuve un problema técnico. ¿Puedes repetir la pregunta?" }]);
        }
    };

    const clearChat = () => {
        if (confirm("¿Quieres borrar la conversación con el tutor?")) {
            const welcome = [{ role: "assistant", content: "Chat reiniciado. ¿En qué puedo ayudarte?" }];
            setMessages(welcome);
            localStorage.removeItem('finaxis_tutor_chat');
        }
    };

    return {
        messages,
        sendMessage,
        isThinking,
        clearChat
    };
}
