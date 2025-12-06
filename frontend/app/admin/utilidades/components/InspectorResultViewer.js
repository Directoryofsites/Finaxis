// frontend/app/admin/utilidades/components/InspectorResultViewer.js

import React from 'react';

// Componente para renderizar un valor. Si es un ID, lo hace clickeable.
const ValueRenderer = ({ fieldKey, value, onIdClick }) => {
    if (value === null || typeof value === 'undefined') {
        return <span className="text-gray-400">N/A</span>;
    }

    const isIdField = fieldKey.endsWith('_id') && value !== null;

    if (isIdField) {
        return (
            <button 
                onClick={() => onIdClick(value)} 
                className="text-blue-600 hover:text-blue-800 hover:underline font-semibold"
                title={`Inspeccionar ID ${value}`}
            >
                {String(value)}
            </button>
        );
    }
    if (typeof value === 'string' && value.match(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/)) {
        return new Date(value).toLocaleString('es-CO', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    }
    if (typeof value === 'boolean') {
        return value ? <span className="font-bold text-green-600">Verdadero</span> : <span className="font-bold text-red-600">Falso</span>;
    }
    return String(value);
};


export default function InspectorResultViewer({ results, onIdClick }) {
    if (!results || results.length === 0) {
        return null;
    }

    return (
        <div className="space-y-6">
            {results.map((result, index) => {
                // --- INICIO DE LA MEJORA ---
                // Función de detección más robusta
                const isObjectField = (key, value) => {
                    // Lo trata como objeto si su tipo es 'object' O si su nombre termina en '_json' o es 'documentos_eliminados'
                    return (typeof value === 'object' && value !== null) || key.endsWith('_json') || key === 'documentos_eliminados';
                };

                const simpleFields = Object.entries(result.datos).filter(([key, value]) => !isObjectField(key, value));
                const objectFields = Object.entries(result.datos).filter(([key, value]) => isObjectField(key, value));
                // --- FIN DE LA MEJORA ---

                return (
                    <div key={index} className="bg-white p-4 rounded-lg shadow-md border border-gray-200">
                        <h4 className="text-md font-bold text-gray-800 mb-3 border-b pb-2">
                            Registro encontrado en la tabla: <span className="font-mono bg-gray-200 text-purple-700 px-2 py-1 rounded">{result.tabla_origen}</span>
                        </h4>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-2 text-sm">
                            {simpleFields.map(([key, value]) => (
                                <div key={key} className="flex border-t py-2">
                                    <strong className="w-1/3 text-gray-600 font-medium">{key}:</strong>
                                    <span className="w-2/3 text-gray-800 font-mono break-words">
                                       <ValueRenderer fieldKey={key} value={value} onIdClick={onIdClick} />
                                    </span>
                                </div>
                            ))}
                        </div>

                        {objectFields.length > 0 && (
                            <div className="mt-4 space-y-3">
                                {objectFields.map(([key, value]) => (
                                    <div key={key} className="border-t pt-3">
                                        <strong className="text-gray-600 font-medium">{key}:</strong>
                                        <pre className="mt-1 bg-gray-900 text-green-400 text-xs p-4 rounded-md overflow-auto shadow-inner">
                                            <code>
                                                {/* Se asegura de que si el valor es un string, intente parsearlo */}
                                                {typeof value === 'string' ? JSON.stringify(JSON.parse(value), null, 2) : JSON.stringify(value, null, 2)}
                                            </code>
                                        </pre>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                );
            })}
        </div>
    );
}