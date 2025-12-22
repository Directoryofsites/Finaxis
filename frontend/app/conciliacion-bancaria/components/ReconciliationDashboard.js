'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  BarChart3,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
  Calendar,
  RefreshCw,
  Loader2,
  GitMerge,
  Target,
  Activity,
  Upload
} from 'lucide-react';

export default function ReconciliationDashboard({
  selectedBankAccount,
  onBankAccountChange,
  reconciliationSummary,
  onSummaryUpdate,
  onNavigate
}) {
  const [bankAccounts, setBankAccounts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [recentActivity, setRecentActivity] = useState([]);

  // Cargar cuentas bancarias disponibles
  const loadBankAccounts = async () => {
    try {
      // Importamos apiService si no está importado, pero asumimos que ya está o lo añadiremos
      // NOTA: Asegurarse de importar apiService arriba si no existe. 
      // Vemos que no está importado en el archivo original, así que usaré fetch con token o reemplazaré todo si es necesario.
      // Mejor: usar fetch directo con el token del localStorage para ser consistente con AuthContext si apiService no está accesible, 
      // PERO ya cambiamos ImportConfigManager a apiService. Deberíamos ser consistentes.
      // Sin embargo, para no romper imports, usaré apiService.get y aseguro de añadir el import si falta.

      const response = await fetch('/api/conciliacion-bancaria/bank-accounts', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      if (response.ok) {
        const accounts = await response.json();
        setBankAccounts(accounts);

        // Seleccionar la primera cuenta por defecto si no hay ninguna seleccionada
        if (!selectedBankAccount && accounts.length > 0) {
          onBankAccountChange(accounts[0]);
        }
      }
    } catch (error) {
      console.error('Error cargando cuentas bancarias:', error);
    }
  };

  // Cargar actividad reciente
  const loadRecentActivity = async () => {
    if (!selectedBankAccount) return;

    try {
      const response = await fetch(`/api/conciliacion-bancaria/reconciliations?bank_account_id=${selectedBankAccount.id}&limit=5`);
      if (response.ok) {
        const data = await response.json();
        setRecentActivity(data.reconciliations || []);
      }
    } catch (error) {
      console.error('Error cargando actividad reciente:', error);
    }
  };

  // Ejecutar conciliación automática
  const runAutoReconciliation = async () => {
    if (!selectedBankAccount) return;

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('bank_account_id', selectedBankAccount.id);

      const response = await fetch('/api/conciliacion-bancaria/reconcile/auto', {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        alert(`Conciliación automática completada: ${result.auto_applied} movimientos conciliados`);
        onSummaryUpdate();
        loadRecentActivity();
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Error ejecutando conciliación automática');
    } finally {
      setLoading(false);
    }
  };

  // Cargar datos iniciales
  useEffect(() => {
    loadBankAccounts();
  }, []);

  useEffect(() => {
    if (selectedBankAccount) {
      loadRecentActivity();
    }
  }, [selectedBankAccount]);

  // Formatear moneda
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0
    }).format(amount);
  };

  // Formatear fecha
  const formatDateTime = (dateString) => {
    return new Date(dateString).toLocaleString('es-CO');
  };

  // Calcular porcentaje de conciliación
  const getReconciliationPercentage = () => {
    if (!reconciliationSummary || !reconciliationSummary.bank_movements) return 0;
    const total = reconciliationSummary.bank_movements.total;
    const matched = reconciliationSummary.bank_movements.matched;
    return total > 0 ? Math.round((matched / total) * 100) : 0;
  };

  return (
    <div className="space-y-6">
      {/* Selector de cuenta bancaria */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Target className="h-5 w-5" />
            <span>Seleccionar Cuenta Bancaria</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {bankAccounts.map((account) => (
              <div
                key={account.id}
                className={`border rounded-lg p-4 cursor-pointer transition-all ${selectedBankAccount?.id === account.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                  }`}
                onClick={() => onBankAccountChange(account)}
              >
                <div className="font-medium">{account.nombre}</div>
                <div className="text-sm text-gray-600">{account.codigo}</div>
                <div className="text-lg font-bold text-green-600 mt-2">
                  {formatCurrency(account.saldo)}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {selectedBankAccount && (
        <>
          {/* Métricas principales */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-8 w-8 text-green-500" />
                  <div>
                    <div className="text-2xl font-bold text-green-600">
                      {reconciliationSummary?.bank_movements?.matched || 0}
                    </div>
                    <div className="text-sm text-gray-600">Movimientos Conciliados</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-2">
                  <Clock className="h-8 w-8 text-yellow-500" />
                  <div>
                    <div className="text-2xl font-bold text-yellow-600">
                      {reconciliationSummary?.bank_movements?.pending || 0}
                    </div>
                    <div className="text-sm text-gray-600">Pendientes</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-2">
                  <BarChart3 className="h-8 w-8 text-blue-500" />
                  <div>
                    <div className="text-2xl font-bold text-blue-600">
                      {getReconciliationPercentage()}%
                    </div>
                    <div className="text-sm text-gray-600">Tasa de Conciliación</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-2">
                  <GitMerge className="h-8 w-8 text-purple-500" />
                  <div>
                    <div className="text-2xl font-bold text-purple-600">
                      {(reconciliationSummary?.reconciliations?.automatic || 0) +
                        (reconciliationSummary?.reconciliations?.manual || 0)}
                    </div>
                    <div className="text-sm text-gray-600">Total Conciliaciones</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Acciones rápidas */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Acciones Rápidas</span>
                <Button
                  onClick={onSummaryUpdate}
                  variant="outline"
                  size="sm"
                  disabled={loading}
                >
                  <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                  Actualizar
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                <Button
                  variant="outline"
                  className="h-20 flex flex-col items-center justify-center"
                  onClick={() => onNavigate('import')}
                >
                  <Upload className="h-6 w-6 mb-2" />
                  <span className="text-xs text-center">Importar Extracto</span>
                </Button>

                <Button
                  onClick={runAutoReconciliation}
                  disabled={loading}
                  className="h-20 flex flex-col items-center justify-center"
                >
                  {loading ? (
                    <Loader2 className="h-6 w-6 animate-spin mb-2" />
                  ) : (
                    <GitMerge className="h-6 w-6 mb-2" />
                  )}
                  <span className="text-xs text-center">Conciliación Automática</span>
                </Button>

                <Button
                  variant="outline"
                  className="h-20 flex flex-col items-center justify-center"
                  onClick={() => onNavigate('manual')}
                >
                  <Activity className="h-6 w-6 mb-2" />
                  <span className="text-xs text-center">Conciliación Manual</span>
                </Button>

                <Button
                  variant="outline"
                  className="h-20 flex flex-col items-center justify-center"
                  onClick={() => onNavigate('adjustments')}
                >
                  <TrendingUp className="h-6 w-6 mb-2" />
                  <span className="text-xs text-center">Ajustes Automáticos</span>
                </Button>

                <Button
                  variant="outline"
                  className="h-20 flex flex-col items-center justify-center"
                  onClick={() => onNavigate('reports')}
                >
                  <BarChart3 className="h-6 w-6 mb-2" />
                  <span className="text-xs text-center">Ver Reportes</span>
                </Button>

                <Button
                  variant="outline"
                  className="h-20 flex flex-col items-center justify-center"
                  onClick={() => onNavigate('config')}
                >
                  <Calendar className="h-6 w-6 mb-2" />
                  <span className="text-xs text-center">Configuración</span>
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Resumen detallado */}
          {reconciliationSummary && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Movimientos bancarios */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-blue-600">Movimientos Bancarios</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span>Total de movimientos:</span>
                      <Badge variant="secondary">{reconciliationSummary.bank_movements.total}</Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Conciliados:</span>
                      <Badge variant="default">{reconciliationSummary.bank_movements.matched}</Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Pendientes:</span>
                      <Badge variant="outline">{reconciliationSummary.bank_movements.pending}</Badge>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${getReconciliationPercentage()}%` }}
                      ></div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Movimientos contables */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-green-600">Movimientos Contables</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span>Total de movimientos:</span>
                      <Badge variant="secondary">{reconciliationSummary.accounting_movements.total}</Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Conciliados:</span>
                      <Badge variant="default">{reconciliationSummary.accounting_movements.reconciled}</Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Sin conciliar:</span>
                      <Badge variant="outline">{reconciliationSummary.accounting_movements.unreconciled}</Badge>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-green-600 h-2 rounded-full"
                        style={{
                          width: `${reconciliationSummary.accounting_movements.total > 0 ?
                            Math.round((reconciliationSummary.accounting_movements.reconciled / reconciliationSummary.accounting_movements.total) * 100) : 0}%`
                        }}
                      ></div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Actividad reciente */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Activity className="h-5 w-5" />
                <span>Actividad Reciente</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {recentActivity.length === 0 ? (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    No hay actividad reciente para esta cuenta.
                  </AlertDescription>
                </Alert>
              ) : (
                <div className="space-y-3">
                  {recentActivity.map((activity) => (
                    <div key={activity.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className={`w-2 h-2 rounded-full ${activity.reconciliation_type === 'AUTO' ? 'bg-blue-500' : 'bg-green-500'
                          }`}></div>
                        <div>
                          <div className="font-medium">
                            {activity.bank_movement.description}
                          </div>
                          <div className="text-sm text-gray-600">
                            {formatDateTime(activity.reconciliation_date)} •
                            {activity.reconciliation_type === 'AUTO' ? 'Automática' : 'Manual'}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-bold">
                          {formatCurrency(parseFloat(activity.bank_movement.amount))}
                        </div>
                        <Badge variant={activity.status === 'ACTIVE' ? 'default' : 'destructive'} className="text-xs">
                          {activity.status === 'ACTIVE' ? 'Activa' : 'Revertida'}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}