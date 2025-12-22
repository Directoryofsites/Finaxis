'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Bug, Eye, EyeOff, Trash2, Download } from 'lucide-react';

export default function DebugPanel({ formData, config, accounts }) {
  const [isVisible, setIsVisible] = useState(false);
  const [logs, setLogs] = useState([]);

  // Interceptar console.log para capturar logs
  useEffect(() => {
    const originalLog = console.log;
    const originalError = console.error;

    console.log = (...args) => {
      // Solo capturar logs que empiecen con emojis (nuestros logs)
      const message = args.join(' ');
      if (message.match(/^[🔍🗺️🆕💾❌✅💥🏦📊]/)) {
        setLogs(prev => [...prev.slice(-19), {
          timestamp: new Date().toLocaleTimeString(),
          type: 'log',
          message: message
        }]);
      }
      originalLog.apply(console, args);
    };

    console.error = (...args) => {
      const message = args.join(' ');
      if (message.match(/^[🔍🗺️🆕💾❌✅💥🏦📊]/)) {
        setLogs(prev => [...prev.slice(-19), {
          timestamp: new Date().toLocaleTimeString(),
          type: 'error',
          message: message
        }]);
      }
      originalError.apply(console, args);
    };

    return () => {
      console.log = originalLog;
      console.error = originalError;
    };
  }, []);

  const clearLogs = () => {
    setLogs([]);
  };

  const downloadLogs = () => {
    const logText = logs.map(log => `[${log.timestamp}] ${log.message}`).join('\n');
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `conciliacion-debug-${new Date().toISOString().slice(0, 19)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!isVisible) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <Button
          onClick={() => setIsVisible(true)}
          variant="outline"
          size="sm"
          className="bg-yellow-50 border-yellow-200 text-yellow-800 hover:bg-yellow-100"
        >
          <Bug className="h-4 w-4 mr-2" />
          Debug {logs.length > 0 && `(${logs.length})`}
        </Button>
      </div>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 w-96 max-h-96 overflow-auto">
      <Card className="bg-yellow-50 border-yellow-200">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-2">
              <Bug className="h-4 w-4 text-yellow-600" />
              <span>Panel de Debug</span>
            </div>
            <div className="flex gap-1">
              <Button
                onClick={downloadLogs}
                variant="ghost"
                size="sm"
                title="Descargar logs"
              >
                <Download className="h-4 w-4" />
              </Button>
              <Button
                onClick={clearLogs}
                variant="ghost"
                size="sm"
                title="Limpiar logs"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
              <Button
                onClick={() => setIsVisible(false)}
                variant="ghost"
                size="sm"
              >
                <EyeOff className="h-4 w-4" />
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Logs en tiempo real */}
          {logs.length > 0 && (
            <div>
              <h4 className="font-semibold text-xs text-yellow-800">Logs Recientes:</h4>
              <div className="text-xs bg-white p-2 rounded border max-h-32 overflow-auto font-mono">
                {logs.slice(-10).map((log, index) => (
                  <div key={index} className={`${log.type === 'error' ? 'text-red-600' : 'text-gray-800'}`}>
                    <span className="text-gray-500">[{log.timestamp}]</span> {log.message}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Estado del formulario */}
          {formData && (
            <div>
              <h4 className="font-semibold text-xs text-yellow-800">Form Data:</h4>
              <pre className="text-xs bg-white p-2 rounded border overflow-auto max-h-32">
                {JSON.stringify(formData, null, 2)}
              </pre>
            </div>
          )}

          {/* Estado de configuración */}
          {config && (
            <div>
              <h4 className="font-semibold text-xs text-yellow-800">Config:</h4>
              <pre className="text-xs bg-white p-2 rounded border overflow-auto max-h-32">
                {JSON.stringify(config, null, 2)}
              </pre>
            </div>
          )}

          {/* Cuentas disponibles */}
          {accounts && (
            <div>
              <h4 className="font-semibold text-xs text-yellow-800">
                Cuentas ({accounts.length}):
              </h4>
              <div className="text-xs bg-white p-2 rounded border max-h-32 overflow-auto">
                {accounts.slice(0, 5).map(account => (
                  <div key={account.id}>
                    {account.codigo} - {account.nombre}
                  </div>
                ))}
                {accounts.length > 5 && (
                  <div className="text-gray-500">
                    ... y {accounts.length - 5} más
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Información del navegador */}
          <div>
            <h4 className="font-semibold text-xs text-yellow-800">Browser Info:</h4>
            <div className="text-xs bg-white p-2 rounded border">
              <div>User Agent: {navigator.userAgent.substring(0, 50)}...</div>
              <div>URL: {window.location.href}</div>
              <div>Timestamp: {new Date().toISOString()}</div>
            </div>
          </div>

          {/* Test de conectividad */}
          <div className="space-y-2">
            <Button
              onClick={async () => {
                console.log('🧪 [API TEST] Probando conexión a /api/plan-cuentas...');
                try {
                  // Obtener token de autenticación
                  const token = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
                  console.log('🧪 [API TEST] Token encontrado:', token ? 'Sí' : 'No');
                  
                  const headers = {
                    'Content-Type': 'application/json'
                  };
                  
                  if (token) {
                    headers['Authorization'] = `Bearer ${token}`;
                  }
                  
                  const response = await fetch('/api/plan-cuentas/', {
                    method: 'GET',
                    headers: headers
                  });
                  
                  console.log(`🧪 [API TEST] Respuesta: ${response.status} - ${response.ok ? 'OK' : 'Error'}`);
                  if (response.ok) {
                    const data = await response.json();
                    console.log(`🧪 [API TEST] Datos recibidos: ${data.length} cuentas`);
                    console.log(`🧪 [API TEST] Primeras 5 cuentas:`, data.slice(0, 5));
                    alert(`✅ API Plan Cuentas OK: ${data.length} cuentas encontradas`);
                  } else {
                    const errorText = await response.text();
                    console.log(`🧪 [API TEST] Error response:`, errorText);
                    
                    if (response.status === 401) {
                      alert(`🔐 Error de Autenticación: Token inválido o expirado\nStatus: ${response.status}`);
                    } else {
                      alert(`❌ API Plan Cuentas Error: ${response.status} - ${errorText}`);
                    }
                  }
                } catch (error) {
                  console.error('💥 [API TEST] Error:', error);
                  alert(`💥 API Test Error: ${error.message}`);
                }
              }}
              variant="outline"
              size="sm"
              className="w-full text-xs"
            >
              🧪 Test API Plan Cuentas
            </Button>

            <Button
              onClick={async () => {
                console.log('🧪 [TEST ENDPOINT] Probando endpoint de cuentas bancarias...');
                try {
                  const token = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
                  const response = await fetch('/api/conciliacion-bancaria/test-bank-accounts', {
                    headers: token ? { 'Authorization': `Bearer ${token}` } : {}
                  });
                  
                  if (response.ok) {
                    const data = await response.json();
                    console.log('🧪 [TEST ENDPOINT] Respuesta:', data);
                    alert(`✅ Test OK!\nEmpresa: ${data.empresa_id}\nCuentas bancarias: ${data.total_cuentas}\n\nPrimeras cuentas:\n${data.cuentas.slice(0, 3).map(c => `${c.codigo} - ${c.nombre} (ID: ${c.id})`).join('\n')}`);
                  } else {
                    const errorText = await response.text();
                    alert(`❌ Error: ${response.status} - ${errorText}`);
                  }
                } catch (error) {
                  console.error('💥 [TEST ENDPOINT] Error:', error);
                  alert(`💥 Error: ${error.message}`);
                }
              }}
              variant="outline"
              size="sm"
              className="w-full text-xs bg-purple-50"
            >
              🧪 Test Cuentas Bancarias
            </Button>

            <Button
              onClick={async () => {
                console.log('🔍 [FORCE RELOAD] Forzando recarga de cuentas...');
                try {
                  // Simular la función loadAccounts del componente AccountingConfiguration
                  const response = await fetch('/api/plan-cuentas');
                  console.log(`🔍 [FORCE RELOAD] Status: ${response.status}`);
                  
                  if (response.ok) {
                    const data = await response.json();
                    console.log(`🔍 [FORCE RELOAD] Cuentas obtenidas:`, data.length);
                    console.log(`🔍 [FORCE RELOAD] Estructura de cuenta:`, data[0]);
                    
                    // Verificar filtros por tipo
                    const expenseAccounts = data.filter(account => account.codigo?.startsWith('5'));
                    const incomeAccounts = data.filter(account => account.codigo?.startsWith('4'));
                    
                    console.log(`🔍 [FORCE RELOAD] Cuentas de gasto (5xxx): ${expenseAccounts.length}`);
                    console.log(`🔍 [FORCE RELOAD] Cuentas de ingreso (4xxx): ${incomeAccounts.length}`);
                    
                    alert(`🔍 Recarga forzada: ${data.length} cuentas total\n- Gastos (5xxx): ${expenseAccounts.length}\n- Ingresos (4xxx): ${incomeAccounts.length}`);
                  } else {
                    alert(`❌ Error en recarga: ${response.status}`);
                  }
                } catch (error) {
                  console.error('💥 [FORCE RELOAD] Error:', error);
                  alert(`💥 Error en recarga: ${error.message}`);
                }
              }}
              variant="outline"
              size="sm"
              className="w-full text-xs bg-blue-50"
            >
              🔍 Forzar Recarga Cuentas
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}