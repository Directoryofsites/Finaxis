import { useCallback, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { toast } from 'react-toastify';
// import { apiService } from '@/lib/apiService'; // Uncomment if API calls are needed

/**
 * Hook para manejar automatizaciones de reportes basadas en URL parameters via AI assistant.
 * @param {string} reportName - Identificador del reporte (ej. 'super_informe_inventarios')
 * @param {Function} onGeneratePDF - Callback para generar el PDF/Exportar cuando la accion sea 'pdf' o 'download'
 */
export const useAutoReport = (reportName, onGeneratePDF) => {
    const searchParams = useSearchParams();

    const triggerAutoDispatch = useCallback((currentFilters) => {
        const action = searchParams.get('ai_action'); // 'pdf', 'email', 'download'
        const email = searchParams.get('ai_email');
        const trigger = searchParams.get('trigger');

        if (!trigger || trigger !== 'ai_search') return;

        // Auto PDF Generation / Download
        if (action === 'pdf' || action === 'download') {
            if (onGeneratePDF) {
                console.log(`[AutoReport] Triggering PDF generation for ${reportName}`);
                onGeneratePDF();
            }
        }

        // Future: Handle Email sending automatically
        if (action === 'email' && email) {
            console.log(`[AutoReport] Would send email to ${email} for ${reportName}`);
            // Logic to send email would go here
            // apiService.post('/reports/send-email', { ...currentFilters, email, reportName })
        }

    }, [searchParams, reportName, onGeneratePDF]);

    return { triggerAutoDispatch };
};
