'use client';

import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Stethoscope, X, Play, Pause } from 'lucide-react';

export default function InputDiagnostic() {
  const [isVisible, setIsVisible] = useState(false);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [diagnostics, setDiagnostics] = useState([]);
  const [inputStates, setInputStates] = useState({});
  const intervalRef = useRef(null);

  const addDiagnostic = (type, message, data = {}) => {
    const timestamp = new Date().toLocaleTimeString();
    setDiagnostics(prev => [...prev.slice(-19), {
      timestamp,
      type,
      message,
      data
    }]);
  };

  const startMonitoring = () => {
    setIsMonitoring(true);
    addDiagnostic('info', '🔍 Iniciando monitoreo de inputs...');

    // Monitorear cambios en inputs cada 100ms
    intervalRef.current = setInterval(() => {
      const inputs = document.querySelectorAll('input, select, textarea');
      const currentStates = {};

      inputs.forEach(input => {
        const id = input.id || input.name || `${input.tagName}-${Array.from(input.parentNode.children).indexOf(input)}`;
        const currentValue = input.value;
        const currentFocus = document.activeElement === input;

        currentStates[id] = {
          value: currentValue,
          focused: currentFocus,
          type: input.type || input.tagName,
          element: input
        };

        // Detectar cambios inesperados
        if (inputStates[id]) {
          const prevState = inputStates[id];
          
          // Detectar si el valor se resetea inesperadamente
          if (prevState.value !== currentValue && prevState.focused && currentValue === '') {
            addDiagnostic('error', `❌ Input ${id} se reseteo inesperadamente`, {
              previousValue: prevState.value,
              currentValue: currentValue,
              wasFocused: prevState.focused,
              isFocused: currentFocus,
              inputType: input.type || input.tagName
            });
          }

          // Detectar pérdida de foco inesperada
          if (prevState.focused && !currentFocus && prevState.value !== currentValue) {
            addDiagnostic('warning', `⚠️ Input ${id} perdió foco durante escritura`, {
              previousValue: prevState.value,
              currentValue: currentValue,
              inputType: input.type || input.tagName
            });
          }
        }
      });

      setInputStates(currentStates);
    }, 100);
  };

  const stopMonitoring = () => {
    setIsMonitoring(false);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    addDiagnostic('info', '⏹️ Monitoreo detenido');
  };

  useEffect(() => {
    if (isMonitoring) {
      startMonitoring();
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isMonitoring]);

  if (!isVisible) {
    return (
      <div className="fixed top-4 right-4 z-50">
        <Button
          onClick={() => setIsVisible(true)}
          variant="outline"
          size="sm"
          className="bg-purple-50 border-purple-200 text-purple-800 hover:bg-purple-100"
        >
          <Stethoscope className="h-4 w-4 mr-2" />
          Diagnóstico
        </Button>
      </div>
    );
  }

  return (
    <div className="fixed top-4 right-4 z-50 w-96 max-h-96 overflow-auto">
      <Card className="bg-purple-50 border-purple-200">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-2">
              <Stethoscope className="h-4 w-4 text-purple-600" />
              <span>Diagnóstico de Inputs</span>
            </div>
            <div className="flex gap-1">
              <Button
                onClick={() => isMonitoring ? stopMonitoring() : setIsMonitoring(true)}
                variant="ghost"
                size="sm"
                className={isMonitoring ? 'text-red-600' : 'text-green-600'}
              >
                {isMonitoring ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              </Button>
              <Button
                onClick={() => setDiagnostics([])}
                variant="ghost"
                size="sm"
                title="Limpiar diagnósticos"
              >
                🗑️
              </Button>
              <Button
                onClick={() => setIsVisible(false)}
                variant="ghost"
                size="sm"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Estado del monitoreo */}
          <div className={`p-3 rounded border ${isMonitoring ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'}`}>
            <div className="text-xs">
              {isMonitoring ? 
                '🟢 Monitoreando inputs en tiempo real...' : 
                '🔴 Monitoreo detenido. Haz clic en ▶️ para iniciar.'
              }
            </div>
          </div>

          {/* Inputs activos */}
          <div>
            <h4 className="font-semibold text-xs text-purple-800">
              Inputs Detectados ({Object.keys(inputStates).length}):
            </h4>
            <div className="text-xs bg-white p-2 rounded border max-h-24 overflow-auto">
              {Object.entries(inputStates).map(([id, state]) => (
                <div key={id} className={`${state.focused ? 'bg-yellow-100' : ''} p-1 rounded`}>
                  <strong>{id}</strong> ({state.type}): "{state.value}" 
                  {state.focused && <span className="text-blue-600"> [FOCUSED]</span>}
                </div>
              ))}
            </div>
          </div>

          {/* Diagnósticos */}
          <div>
            <h4 className="font-semibold text-xs text-purple-800">
              Diagnósticos ({diagnostics.length}):
            </h4>
            <div className="text-xs bg-white p-2 rounded border max-h-40 overflow-auto font-mono">
              {diagnostics.length === 0 ? (
                <div className="text-gray-500">No hay diagnósticos</div>
              ) : (
                diagnostics.slice(-10).map((diagnostic, index) => (
                  <div key={index} className={`mb-2 p-1 rounded ${
                    diagnostic.type === 'error' ? 'bg-red-50 text-red-800' :
                    diagnostic.type === 'warning' ? 'bg-yellow-50 text-yellow-800' :
                    diagnostic.type === 'info' ? 'bg-blue-50 text-blue-800' :
                    'bg-gray-50 text-gray-800'
                  }`}>
                    <div className="font-semibold">
                      [{diagnostic.timestamp}] {diagnostic.message}
                    </div>
                    {Object.keys(diagnostic.data).length > 0 && (
                      <div className="text-xs mt-1 opacity-75">
                        {JSON.stringify(diagnostic.data, null, 2)}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Acciones rápidas */}
          <div className="space-y-1">
            <Button
              onClick={() => {
                const inputs = document.querySelectorAll('input[value=""]');
                addDiagnostic('info', `🔍 Encontrados ${inputs.length} inputs vacíos`);
              }}
              variant="outline"
              size="sm"
              className="w-full text-xs"
            >
              Buscar Inputs Vacíos
            </Button>
            
            <Button
              onClick={() => {
                const focused = document.activeElement;
                if (focused && (focused.tagName === 'INPUT' || focused.tagName === 'SELECT')) {
                  addDiagnostic('info', `🎯 Input con foco: ${focused.id || focused.tagName}`, {
                    value: focused.value,
                    type: focused.type || focused.tagName
                  });
                } else {
                  addDiagnostic('info', '❌ No hay input con foco');
                }
              }}
              variant="outline"
              size="sm"
              className="w-full text-xs"
            >
              Verificar Foco Actual
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}