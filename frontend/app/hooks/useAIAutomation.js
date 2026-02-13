import { useEffect, useState, useRef } from 'react';
import { useSearchParams } from 'next/navigation';

/**
 * useAIAutomation
 * Hook universal para que cualquier página de reporte de Finaxis 
 * responda automáticamente a comandos de la IA.
 * 
 * @param {boolean} isPageReady - Indica si el componente ya tiene sesión/empresa.
 * @param {Object} filtros - El estado actual de los filtros en la página.
 * @param {Function} setFiltros - Función setter del estado de filtros.
 * @param {Function} onExecute - Función que genera el reporte (handleGenerate).
 */
export function useAIAutomation(isPageReady, filtros, setFiltros, onExecute) {
    const searchParams = useSearchParams();
    const [shouldRun, setShouldRun] = useState(false);
    const lastSignature = useRef('');

    useEffect(() => {
        if (!isPageReady || !searchParams) return;

        // Si es una búsqueda de la IA, debe tener al menos trigger=ai o algún parámetro de fecha
        const isAI = searchParams.get('trigger') === 'ai_search' || searchParams.get('trigger') === 'ai' || searchParams.get('fecha_inicio') || searchParams.get('fecha_corte');
        if (!isAI) return;

        // Crear una firma de los parámetros para evitar ejecuciones duplicadas por re-renders
        const paramsString = searchParams.toString();
        if (lastSignature.current === paramsString) return;
        lastSignature.current = paramsString;

        // 1. Mapear parámetros a los filtros de la página
        setFiltros(prev => {
            const nuevos = { ...prev };

            searchParams.forEach((value, key) => {
                // Mapeos inteligentes de alias comunes
                if (key === 'nivel') {
                    if ('nivel_maximo' in prev) nuevos.nivel_maximo = value;
                    if ('nivel' in prev) nuevos.nivel = value;
                    if ('presentationMode' in prev) nuevos.presentationMode = value;
                } else if (key === 'cuenta') {
                    if ('cuenta' in prev) nuevos.cuenta = value;
                    if ('codigo_cuenta' in prev) nuevos.codigo_cuenta = value;
                } else if (key === 'tercero') {
                    if ('tercero' in prev) nuevos.tercero = value;
                    if ('nombre_tercero' in prev) nuevos.nombre_tercero = value;
                }
                // Si el nombre coincide exacto, lo ponemos
                else if (key in prev) {
                    nuevos[key] = value;
                }
            });

            return nuevos;
        });

        // 2. Dar una pequeña espera para que React actualice el estado de los filtros antes de ejecutar
        setShouldRun(true);
    }, [isPageReady, searchParams]);

    useEffect(() => {
        if (shouldRun) {
            // Verificamos si los filtros requeridos están presentes
            // (La página misma debería manejar la validación final)
            onExecute();
            setShouldRun(false);

            // Limpiar la URL para no re-ejecutar en F5
            if (typeof window !== 'undefined') {
                window.history.replaceState(null, '', window.location.pathname);
            }
        }
    }, [shouldRun]);
}
