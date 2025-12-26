import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'next/navigation';
import { toast } from 'react-toastify';
// FIXED: Use authenticated API service instead of raw axios
// import axios from 'axios'; 
import { apiService } from '@/lib/apiService';

/**
 * useAutoReport Hook
 * 
 * Encapsula la lógica de automatización de reportes impulsada por IA.
 * - Detecta filtros en URL
 * - Detecta acciones automáticas (PDF/Email)
 * - Gestiona el envío de correo con feedback al usuario
 * 
 * @param {string} reportKey - La clave única del reporte (debe coincidir con ReportingRegistry en backend)
 * @param {function} onExportPDF - Función para ejecutar la exportación a PDF (callback del componente)
 * @returns {object} { emailAddress, isAutoDispatching }
 */
export const useAutoReport = (reportKey, onExportPDF) => {
    const searchParams = useSearchParams();
    const [actionProcessed, setActionProcessed] = useState(false);
    const [emailAddress, setEmailAddress] = useState(null);

    // 1. Detección inicial de parámetros de correo
    useEffect(() => {
        const email = searchParams.get('ai_email');
        if (email) setEmailAddress(email);
    }, [searchParams]);

    // 2. Ejecutar Acción Automática (Solo una vez cuando hay datos listos)
    // Esta función debe ser llamada por el componente padre cuando los resultados de la búsqueda
    // se hayan cargado correctamente (ej. en el useEffect que setea resultados o valida length > 0).
    const triggerAutoDispatch = useCallback(async (currentFilters) => {
        // Evitar doble ejecución
        if (actionProcessed) return;

        const action = searchParams.get('ai_accion'); // 'pdf' | 'email'
        const email = searchParams.get('ai_email');

        if (!action && !email) return;

        // Marcar como procesado para evitar loops
        setActionProcessed(true);

        // Caso A: Descarga PDF Directa
        if (action === 'pdf' && !email) {
            toast.info("AI: Iniciando descarga automática de PDF...");
            if (onExportPDF) onExportPDF();
            return;
        }

        // Caso B: Envío de Correo
        if (email) {
            await handleSendEmail(email, currentFilters);
        }

    }, [actionProcessed, searchParams, onExportPDF, reportKey]);


    // Lógica Privada de Envío
    const handleSendEmail = async (targetEmail, filters) => {
        const toastId = toast.loading(`AI: Generando reporte y enviando a ${targetEmail}...`);

        try {
            const payload = {
                report_type: reportKey,
                email_to: targetEmail,
                filtros: sanitizeFilters(filters) // Limpieza básica
            };

            // USAR apiService PARA INCLUIR TOKEN DE AUTH AUTOMÁTICAMENTE
            await apiService.post('/reports/dispatch-email', payload);

            toast.update(toastId, {
                render: `¡Reporte enviado exitosamente a ${targetEmail}!`,
                type: "success",
                isLoading: false,
                autoClose: 4000
            });

        } catch (error) {
            console.error("Error useAutoReport dispatch:", error);
            const msg = error.response?.data?.detail || "Error desconocido";

            // Fallback inteligente: Bajar PDF
            toast.update(toastId, {
                render: `Fallo el envío (${msg}). Descargando PDF como respaldo...`,
                type: "warning",
                isLoading: false,
                autoClose: 5000
            });

            if (onExportPDF) onExportPDF();
        }
    };

    // Helper para asegurar que fechas sean strings y no objetos Date
    // Y que los campos vacíos se envíen como null para evitar errores de validación Pydantic
    const sanitizeFilters = (filters) => {
        const clean = { ...filters };
        Object.keys(clean).forEach(k => {
            const val = clean[k];

            // Caso 1: Fechas a ISO String (YYYY-MM-DD)
            if (val instanceof Date) {
                clean[k] = val.toISOString().split('T')[0];
            }

            // Caso 2: Strings vacíos a null (para campos numéricos opcionales como tercero_id)
            if (val === '') {
                clean[k] = null;
            }
        });
        return clean;
    };

    return {
        emailAddress,
        triggerAutoDispatch,
        hasAutoAction: !!(searchParams.get('ai_accion') || searchParams.get('ai_email'))
    };
};
