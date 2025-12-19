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

  // Cargar configuración existente
  const loadConfiguration = async () => {
    if (!bankAccount) return;

    setLoading(true);
    try {
      const response = await fetch(`/api/conciliacion-bancaria/accounting-config/${bankAccount.id}`);
      
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
    try {
      const response = await fetch('/api/plan-cuentas');
      
      if (response.ok) {
        const data = await response.json();
        setAccounts(data);
      }
    } catch (error) {
      console.error('Error cargando cuentas:', error);
    }
  };

  // Guardar configuración
  const saveConfiguration = async () => {
    if (!bankAccount) return;

    setSaving(true);
    try {
      const response = await fetch(`/api/conciliacion-bancaria/accounting-config/${bankAccount.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
      });

      if (response.ok) {
        alert('Configuración guardada exitosamente');
        onConfigurationSaved?.();
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Error guardando configuración');
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
          <CardTitle className="flex items-center space-x-2">
            <Settings className="h-5 w-5" />
            <span>Configuración Contable - {bankAccount.nombre}</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Configure las cuentas contables que se utilizarán para generar automáticamente 
              los asientos de ajuste para diferentes tipos de movimientos bancarios.
            </AlertDescription>
          </Alert>
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
                  className="w-full p-2 border border-gray-300 rounded-md"
                  value={config.commission_account_id}
                  onChange={(e) => setConfig(prev => ({ ...prev, commission_account_id: e.target.value }))}
                >
                  <option value="">Seleccionar cuenta...</option>
                  {getAccountsByType('expense').map(account => (
                    <option key={account.id} value={account.id}>
                      {account.codigo} - {account.nombre}
                    </option>
                  ))}
                </select>
                <div className="text-sm text-gray-600 mt-1">
                  Para registrar comisiones cobradas por el banco
                </div>
              </div>

              {/* Cargos bancarios */}
              <div>
                <Label htmlFor="bank_charges_account">Cuenta de Cargos Bancarios</Label>
                <select
                  id="bank_charges_account"
                  className="w-full p-2 border border-gray-300 rounded-md"
                  value={config.bank_charges_account_id}
                  onChange={(e) => setConfig(prev => ({ ...prev, bank_charges_account_id: e.target.value }))}
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
                  className="w-full p-2 border border-gray-300 rounded-md"
                  value={config.interest_income_account_id}
                  onChange={(e) => setConfig(prev => ({ ...prev, interest_income_account_id: e.target.value }))}
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
                  className="w-full p-2 border border-gray-300 rounded-md"
                  value={config.adjustment_account_id}
                  onChange={(e) => setConfig(prev => ({ ...prev, adjustment_account_id: e.target.value }))}
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
              onChange={(e) => setConfig(prev => ({ ...prev, default_cost_center_id: e.target.value }))}
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
    </div>
  );
}