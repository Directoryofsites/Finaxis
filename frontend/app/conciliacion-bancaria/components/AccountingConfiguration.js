'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Settings, 
  Save, 
  AlertCircle, 
  CheckCircle,
  DollarSign,
  TrendingUp,
  TrendingDown,
  FileText,
  Loader2
} from 'lucide-react';

import DebugPanel from './DebugPanel';

export default function AccountingConfiguration({ bankAccount, onConfigurationSaved }) {
  const [config, setConfig] = useState({
    commission_account_id: '',
    interest_income_account_id: '',
    bank_charges_account_id: '',
    adjustment_account_id: '',
    default_cost_center_id: ''
  });
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [accounts, setAccounts] = useState([]);
  const [costCenters, setCostCenters] = useState([]);

  // Función para manejar cambios en los campos
  const handleConfigChange = (field, value) => {
    console.log(`🏦 [CONFIG CHANGE] Campo: ${field}, Valor: "${value}", Tipo: ${typeof value}`);
    console.log(`🏦 [CONFIG CHANGE] Estado anterior:`, config[field]);
    
    setConfig(prev => {
      const newState = {
        ...prev,
        [field]: value
      };
      console.log(`🏦 [CONFIG CHANGE] Nuevo estado para ${field}:`, newState[field]);
      console.log(`🏦 [CONFIG CHANGE] Estado completo:`, newState);
      return newState;
    });
  };

  // Cargar configuración existente
  const loadConfiguration = async () => {
    if (!bankAccount) return;

    setLoading(true);
    try {
      // Obtener el token de autenticación
      const token = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
      
      const headers = {
        'Content-Type': 'application/json'
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch(`/api/conciliacion-bancaria/accounting-config/${bankAccount.id}`, {
        headers: headers
      });
      
      if (response.ok) {
        const data = await response.json();
        setConfig(data);
      } else if (response.status === 404) {
        // No hay configuración existente, usar valores por defecto
        setConfig({
          commission_account_id: '',
          interest_income_account_id: '',
          bank_charges_account_id: '',
          adjustment_account_id: '',
          default_cost_center_id: ''
        });
      }
    } catch (error) {
      console.error('Error cargando configuración:', error);
    } finally {
      setLoading(false);
    }
  };

  // Cargar cuentas contables disponibles
  const loadAccounts = async () => {
    console.log(`📊 [LOAD ACCOUNTS] Iniciando carga de cuentas...`);
    try {
      // Usar exactamente el mismo código que funciona en la prueba de emergencia
      const token = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
      console.log(`📊 [LOAD ACCOUNTS] Token encontrado:`, token ? 'Sí' : 'No');
      
      // Probar endpoint list-flat que sabemos que funciona
      const response = await fetch('/api/plan-cuentas/list-flat', {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      
      console.log(`📊 [LOAD ACCOUNTS] Respuesta:`, response.status, response.statusText);
      
      if (response.ok) {
        const data = await response.json();
        console.log(`📊 [LOAD ACCOUNTS] Cuentas cargadas:`, data.length, 'cuentas');
        console.log(`📊 [LOAD ACCOUNTS] Primeras 3 cuentas:`, data.slice(0, 3));
        console.log(`📊 [LOAD ACCOUNTS] Estructura de cuenta ejemplo:`, data[0]);
        
        // Verificar que las cuentas tienen la estructura esperada
        const validAccounts = data.filter(account => account.codigo && account.nombre);
        console.log(`📊 [LOAD ACCOUNTS] Cuentas válidas:`, validAccounts.length);
        
        if (validAccounts.length === 0) {
          console.log(`⚠️ [LOAD ACCOUNTS] No se encontraron cuentas válidas con código y nombre`);
        }
        
        setAccounts(data);
      } else {
        console.log(`❌ [LOAD ACCOUNTS] Error en respuesta:`, response.status);
        const errorText = await response.text();
        console.log(`❌ [LOAD ACCOUNTS] Error text:`, errorText);
        
        // Si es error de autenticación, mostrar mensaje específico
        if (response.status === 401) {
          console.log(`🔐 [LOAD ACCOUNTS] Error de autenticación - token inválido o expirado`);
        }
      }
    } catch (error) {
      console.error('💥 [LOAD ACCOUNTS] Error:', error);
    }
  };

  // Guardar configuración
  const saveConfiguration = async () => {
    console.log(`💾 [SAVE CONFIG] Iniciando guardado de configuración contable...`);
    console.log(`💾 [SAVE CONFIG] Cuenta bancaria:`, bankAccount);
    console.log(`💾 [SAVE CONFIG] Configuración a guardar:`, config);
    
    if (!bankAccount) {
      console.log(`❌ [SAVE CONFIG] Error: No hay cuenta bancaria seleccionada`);
      alert('No hay cuenta bancaria seleccionada');
      return;
    }

    setSaving(true);
    try {
      // Obtener el token de autenticación
      const token = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
      console.log(`💾 [SAVE CONFIG] Token encontrado:`, token ? 'Sí' : 'No');
      
      // Limpiar los datos: convertir strings vacíos a null para campos integer
      const cleanConfig = {
        commission_account_id: config.commission_account_id || null,
        interest_income_account_id: config.interest_income_account_id || null,
        bank_charges_account_id: config.bank_charges_account_id || null,
        adjustment_account_id: config.adjustment_account_id || null,
        default_cost_center_id: config.default_cost_center_id || null
      };
      
      console.log(`💾 [SAVE CONFIG] Configuración limpia:`, cleanConfig);
      
      const headers = {
        'Content-Type': 'application/json'
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const url = `/api/conciliacion-bancaria/accounting-config/${bankAccount.id}`;
      console.log(`💾 [SAVE CONFIG] URL:`, url);
      console.log(`💾 [SAVE CONFIG] Payload:`, JSON.stringify(cleanConfig, null, 2));
      
      const response = await fetch(url, {
        method: 'PUT',
        headers: headers,
        body: JSON.stringify(cleanConfig)
      });

      console.log(`💾 [SAVE CONFIG] Respuesta:`, response.status, response.statusText);

      if (response.ok) {
        const responseData = await response.json();
        console.log(`✅ [SAVE CONFIG] Guardado exitoso:`, responseData);
        alert('✅ Configuración guardada exitosamente');
        onConfigurationSaved?.();
      } else {
        const error = await response.json();
        console.log(`❌ [SAVE CONFIG] Error del servidor:`, error);
        
        if (response.status === 401) {
          alert('🔐 Error de autenticación: Tu sesión ha expirado. Por favor, inicia sesión nuevamente.');
        } else {
          alert(`❌ Error: ${error.detail || 'Error desconocido'}`);
        }
      }
    } catch (error) {
      console.error('💥 [SAVE CONFIG] Error de conexión:', error);
      alert('💥 Error de conexión al guardar la configuración');
    } finally {
      setSaving(false);
    }
  };

  // Cargar datos iniciales
  useEffect(() => {
    if (bankAccount) {
      loadConfiguration();
      loadAccounts();
    }
  }, [bankAccount]);

  // Filtrar cuentas por tipo
  const getAccountsByType = (type) => {
    return accounts.filter(account => {
      const code = account.codigo || '';
      switch (type) {
        case 'expense': // Cuentas de gasto (5xxx)
          return code.startsWith('5');
        case 'income': // Cuentas de ingreso (4xxx)
          return code.startsWith('4');
        case 'asset': // Cuentas de activo (1xxx)
          return code.startsWith('1');
        default:
          return true;
      }
    });
  };

  if (!bankAccount) {
    return (
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Selecciona una cuenta bancaria para configurar las cuentas contables.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Settings className="h-5 w-5" />
              <span>Configuración Contable - {bankAccount.nombre}</span>
            </div>
            <div className="flex gap-2">
              <Button
                onClick={loadAccounts}
                variant="outline"
                size="sm"
                disabled={loading}
              >
                🔄 Recargar Cuentas ({accounts.length})
              </Button>
              <Button
                onClick={async () => {
                  console.log('🔧 [EMERGENCY TEST] Prueba de emergencia...');
                  try {
                    // Probar sin autenticación primero
                    const response1 = await fetch('/api/plan-cuentas/');
                    console.log('🔧 [EMERGENCY TEST] Sin auth:', response1.status);
                    
                    // Probar con autenticación
                    const token = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
                    const response2 = await fetch('/api/plan-cuentas/', {
                      headers: token ? { 'Authorization': `Bearer ${token}` } : {}
                    });
                    console.log('🔧 [EMERGENCY TEST] Con auth:', response2.status);
                    
                    // Probar endpoint alternativo
                    const response3 = await fetch('/api/plan-cuentas/list-flat', {
                      headers: token ? { 'Authorization': `Bearer ${token}` } : {}
                    });
                    console.log('🔧 [EMERGENCY TEST] List-flat:', response3.status);
                    
                    if (response3.ok) {
                      const data = await response3.json();
                      console.log('🔧 [EMERGENCY TEST] Datos obtenidos:', data.length);
                      alert(`✅ ÉXITO: ${data.length} cuentas encontradas con list-flat`);
                      setAccounts(data);
                    } else {
                      alert(`❌ Todos los endpoints fallaron\nSin auth: ${response1.status}\nCon auth: ${response2.status}\nList-flat: ${response3.status}`);
                    }
                  } catch (error) {
                    console.error('🔧 [EMERGENCY TEST] Error:', error);
                    alert(`💥 Error: ${error.message}`);
                  }
                }}
                variant="outline"
                size="sm"
                className="bg-red-50 text-red-700"
              >
                🚨 Prueba Emergencia
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className={`p-3 rounded border ${accounts.length === 0 ? 'bg-red-50 border-red-200' : 'bg-blue-50 border-blue-200'}`}>
            <div className="text-sm">
              {accounts.length === 0 ? (
                <>
                  ⚠️ <strong>No se han cargado cuentas contables.</strong> Configure las cuentas contables que se utilizarán para generar automáticamente 
                  los asientos de ajuste para diferentes tipos de movimientos bancarios.
                </>
              ) : (
                <>
                  ✅ <strong>{accounts.length} cuentas cargadas.</strong> Configure las cuentas contables que se utilizarán para generar automáticamente 
                  los asientos de ajuste para diferentes tipos de movimientos bancarios.
                </>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {loading ? (
        <div className="flex items-center justify-center p-8">
          <Loader2 className="h-8 w-8 animate-spin" />
          <span className="ml-2">Cargando configuración...</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Cuentas de Gastos */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-red-600">
                <TrendingDown className="h-5 w-5" />
                <span>Cuentas de Gastos</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Comisiones */}
              <div>
                <Label htmlFor="commission_account">Cuenta de Comisiones Bancarias</Label>
                <select
                  id="commission_account"
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                  value={config.commission_account_id}
                  onChange={(e) => handleConfigChange('commission_account_id', e.target.value)}
                >
                  <option value="">
                    {accounts.length === 0 ? 'Cargando cuentas...' : 'Seleccionar cuenta...'}
                  </option>
                  {getAccountsByType('expense').map(account => (
                    <option key={account.id} value={account.id}>
                      {account.codigo} - {account.nombre}
                    </option>
                  ))}
                  {accounts.length === 0 && (
                    <option value="" disabled>No hay cuentas disponibles</option>
                  )}
                </select>
                <div className="text-sm text-gray-600 mt-1">
                  Para registrar comisiones cobradas por el banco
                  {accounts.length === 0 && (
                    <div className="text-red-600 text-xs mt-1">
                      ⚠️ No se pudieron cargar las cuentas. Verifica la conexión con la API.
                    </div>
                  )}
                </div>
              </div>

              {/* Cargos bancarios */}
              <div>
                <Label htmlFor="bank_charges_account">Cuenta de Cargos Bancarios</Label>
                <select
                  id="bank_charges_account"
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                  value={config.bank_charges_account_id}
                  onChange={(e) => handleConfigChange('bank_charges_account_id', e.target.value)}
                >
                  <option value="">Seleccionar cuenta...</option>
                  {getAccountsByType('expense').map(account => (
                    <option key={account.id} value={account.id}>
                      {account.codigo} - {account.nombre}
                    </option>
                  ))}
                </select>
                <div className="text-sm text-gray-600 mt-1">
                  Para registrar notas débito y otros cargos
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Cuentas de Ingresos */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-green-600">
                <TrendingUp className="h-5 w-5" />
                <span>Cuentas de Ingresos</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Intereses */}
              <div>
                <Label htmlFor="interest_account">Cuenta de Intereses Ganados</Label>
                <select
                  id="interest_account"
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                  value={config.interest_income_account_id}
                  onChange={(e) => handleConfigChange('interest_income_account_id', e.target.value)}
                >
                  <option value="">Seleccionar cuenta...</option>
                  {getAccountsByType('income').map(account => (
                    <option key={account.id} value={account.id}>
                      {account.codigo} - {account.nombre}
                    </option>
                  ))}
                </select>
                <div className="text-sm text-gray-600 mt-1">
                  Para registrar intereses pagados por el banco
                </div>
              </div>

              {/* Ajustes */}
              <div>
                <Label htmlFor="adjustment_account">Cuenta de Ajustes</Label>
                <select
                  id="adjustment_account"
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                  value={config.adjustment_account_id}
                  onChange={(e) => handleConfigChange('adjustment_account_id', e.target.value)}
                >
                  <option value="">Seleccionar cuenta...</option>
                  {getAccountsByType('income').map(account => (
                    <option key={account.id} value={account.id}>
                      {account.codigo} - {account.nombre}
                    </option>
                  ))}
                </select>
                <div className="text-sm text-gray-600 mt-1">
                  Para registrar notas crédito y otros ajustes
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Centro de costo por defecto */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <FileText className="h-5 w-5" />
            <span>Configuración Adicional</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div>
            <Label htmlFor="cost_center">Centro de Costo por Defecto (Opcional)</Label>
            <Input
              id="cost_center"
              type="number"
              placeholder="ID del centro de costo"
              value={config.default_cost_center_id}
              onChange={(e) => handleConfigChange('default_cost_center_id', e.target.value)}
            />
            <div className="text-sm text-gray-600 mt-1">
              Centro de costo que se asignará automáticamente a los ajustes
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Vista previa de configuración */}
      <Card>
        <CardHeader>
          <CardTitle>Vista Previa de Configuración</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-semibold text-red-600 mb-2">Cuentas de Gastos:</h4>
              <div className="space-y-1 text-sm">
                <div>
                  <strong>Comisiones:</strong> {
                    config.commission_account_id ? 
                    accounts.find(a => a.id == config.commission_account_id)?.codigo + ' - ' + 
                    accounts.find(a => a.id == config.commission_account_id)?.nombre : 
                    'No configurada'
                  }
                </div>
                <div>
                  <strong>Cargos:</strong> {
                    config.bank_charges_account_id ? 
                    accounts.find(a => a.id == config.bank_charges_account_id)?.codigo + ' - ' + 
                    accounts.find(a => a.id == config.bank_charges_account_id)?.nombre : 
                    'No configurada'
                  }
                </div>
              </div>
            </div>
            
            <div>
              <h4 className="font-semibold text-green-600 mb-2">Cuentas de Ingresos:</h4>
              <div className="space-y-1 text-sm">
                <div>
                  <strong>Intereses:</strong> {
                    config.interest_income_account_id ? 
                    accounts.find(a => a.id == config.interest_income_account_id)?.codigo + ' - ' + 
                    accounts.find(a => a.id == config.interest_income_account_id)?.nombre : 
                    'No configurada'
                  }
                </div>
                <div>
                  <strong>Ajustes:</strong> {
                    config.adjustment_account_id ? 
                    accounts.find(a => a.id == config.adjustment_account_id)?.codigo + ' - ' + 
                    accounts.find(a => a.id == config.adjustment_account_id)?.nombre : 
                    'No configurada'
                  }
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Botón de guardar */}
      <div className="flex justify-end">
        <Button 
          onClick={saveConfiguration}
          disabled={saving}
        >
          {saving && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
          <Save className="h-4 w-4 mr-2" />
          Guardar Configuración
        </Button>
      </div>

      {/* Panel de Debug */}
      <DebugPanel config={config} accounts={accounts} />
    </div>
  );
}