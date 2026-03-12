'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { Card, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Upload,
  Settings,
  GitMerge,
  Eye,
  BarChart3,
  AlertCircle,
  CheckCircle,
  Clock,
  Zap
} from 'lucide-react';

import ImportConfigManager from './components/ImportConfigManager';
import FileImportInterface from './components/FileImportInterface';
import ManualReconciliationInterface from './components/ManualReconciliationInterface';
import ReconciliationDashboard from './components/ReconciliationDashboard';
import ReconciliationReports from './components/ReconciliationReports';
import AutomaticAdjustments from './components/AutomaticAdjustments';
import AccountingConfiguration from './components/AccountingConfiguration';
import BreadcrumbNavigation from './components/BreadcrumbNavigation';
import ConnectionStatus from './components/ConnectionStatus';
import TestForm from './components/TestForm';
import { apiService } from '@/lib/apiService';

// Importar estilos específicos
import './conciliacion-bancaria.css';

function ConciliacionBancariaContent() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedBankAccount, setSelectedBankAccount] = useState(null);
  const [reconciliationSummary, setReconciliationSummary] = useState(null);
  const searchParams = useSearchParams();

  // Leer parámetro tab de la URL al cargar la página
  useEffect(() => {
    console.log('🚀 [PAGE LOAD] Cargando página de conciliación bancaria...');
    console.log('🚀 [PAGE LOAD] URL:', window.location.href);
    console.log('🚀 [PAGE LOAD] User Agent:', navigator.userAgent);

    const tabParam = searchParams.get('tab');
    console.log('🚀 [PAGE LOAD] Tab parameter:', tabParam);

    if (tabParam) {
      // Validar que el tab existe
      const validTabs = ['dashboard', 'import', 'manual', 'adjustments', 'reports', 'config', 'test'];
      if (validTabs.includes(tabParam)) {
        console.log('🚀 [PAGE LOAD] Setting active tab to:', tabParam);
        setActiveTab(tabParam);
      } else {
        console.log('❌ [PAGE LOAD] Invalid tab parameter:', tabParam);
      }
    }
  }, [searchParams]);

  // Cargar resumen inicial
  useEffect(() => {
    if (selectedBankAccount) {
      loadReconciliationSummary();
    }
  }, [selectedBankAccount]);

  const loadReconciliationSummary = async () => {
    if (!selectedBankAccount) return;

    try {
      const response = await apiService.get(`/conciliacion-bancaria/reconcile/summary/${selectedBankAccount.id}`);
      setReconciliationSummary(response.data);
    } catch (error) {
      console.error('Error cargando resumen:', error);
    }
  };

  const handleBankAccountChange = (account) => {
    setSelectedBankAccount(account);
  };

  const handleReconciliationUpdate = () => {
    // Recargar resumen cuando se actualice una conciliación
    loadReconciliationSummary();
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Breadcrumb Navigation */}
      <BreadcrumbNavigation activeTab={activeTab} selectedBankAccount={selectedBankAccount} />

      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Conciliación Bancaria</h1>
          <p className="text-gray-600 mt-1">
            Gestión integral de conciliaciones bancarias automatizadas y manuales
          </p>
        </div>

        {selectedBankAccount && (
          <div className="text-right">
            <div className="text-sm text-gray-500">Cuenta seleccionada</div>
            <div className="font-semibold text-lg">{selectedBankAccount.nombre}</div>
            <div className="text-sm text-gray-600">{selectedBankAccount.codigo}</div>
          </div>
        )}
      </div>

      {/* Resumen rápido */}
      {reconciliationSummary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
                <div>
                  <div className="text-2xl font-bold text-green-600">
                    {reconciliationSummary.bank_movements?.matched || 0}
                  </div>
                  <div className="text-sm text-gray-600">Conciliados</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <Clock className="h-5 w-5 text-yellow-500" />
                <div>
                  <div className="text-2xl font-bold text-yellow-600">
                    {reconciliationSummary.bank_movements?.pending || 0}
                  </div>
                  <div className="text-sm text-gray-600">Pendientes</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <BarChart3 className="h-5 w-5 text-blue-500" />
                <div>
                  <div className="text-2xl font-bold text-blue-600">
                    {reconciliationSummary.reconciliation_rate || 0}%
                  </div>
                  <div className="text-sm text-gray-600">Tasa de conciliación</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <GitMerge className="h-5 w-5 text-purple-500" />
                <div>
                  <div className="text-2xl font-bold text-purple-600">
                    {(reconciliationSummary.reconciliations?.automatic || 0) +
                      (reconciliationSummary.reconciliations?.manual || 0)}
                  </div>
                  <div className="text-sm text-gray-600">Total conciliaciones</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Navegación principal */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-7">
          <TabsTrigger value="dashboard" className="flex items-center space-x-2">
            <BarChart3 className="h-4 w-4" />
            <span>Dashboard</span>
          </TabsTrigger>
          <TabsTrigger value="import" className="flex items-center space-x-2">
            <Upload className="h-4 w-4" />
            <span>Importar</span>
          </TabsTrigger>
          <TabsTrigger value="manual" className="flex items-center space-x-2">
            <GitMerge className="h-4 w-4" />
            <span>Conciliar</span>
          </TabsTrigger>
          <TabsTrigger value="adjustments" className="flex items-center space-x-2">
            <Zap className="h-4 w-4" />
            <span>Ajustes</span>
          </TabsTrigger>
          <TabsTrigger value="reports" className="flex items-center space-x-2">
            <Eye className="h-4 w-4" />
            <span>Reportes</span>
          </TabsTrigger>
          <TabsTrigger value="config" className="flex items-center space-x-2">
            <Settings className="h-4 w-4" />
            <span>Configuración</span>
          </TabsTrigger>
          <TabsTrigger value="test" className="flex items-center space-x-2">
            <AlertCircle className="h-4 w-4" />
            <span>Test</span>
          </TabsTrigger>
        </TabsList>

        {/* Dashboard */}
        <TabsContent value="dashboard" className="space-y-6">
          <ReconciliationDashboard
            selectedBankAccount={selectedBankAccount}
            onBankAccountChange={handleBankAccountChange}
            reconciliationSummary={reconciliationSummary}
            onSummaryUpdate={loadReconciliationSummary}
            onNavigate={setActiveTab}
          />
        </TabsContent>
        {/* Importación */}
        <TabsContent value="import" className="space-y-6">
          <FileImportInterface
            selectedBankAccount={selectedBankAccount}
            onBankAccountChange={handleBankAccountChange}
            onImportComplete={handleReconciliationUpdate}
          />
        </TabsContent>

        {/* Conciliación Manual */}
        <TabsContent value="manual" className="space-y-6">
          {selectedBankAccount ? (
            <ManualReconciliationInterface
              bankAccount={selectedBankAccount}
              onReconciliationUpdate={handleReconciliationUpdate}
            />
          ) : (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Selecciona una cuenta bancaria para comenzar la conciliación manual.
              </AlertDescription>
            </Alert>
          )}
        </TabsContent>

        {/* Ajustes Automáticos */}
        <TabsContent value="adjustments" className="space-y-6">
          <AutomaticAdjustments
            bankAccount={selectedBankAccount}
            onAdjustmentComplete={handleReconciliationUpdate}
          />
        </TabsContent>

        {/* Reportes */}
        <TabsContent value="reports" className="space-y-6">
          <ReconciliationReports
            selectedBankAccount={selectedBankAccount}
            onBankAccountChange={handleBankAccountChange}
          />
        </TabsContent>

        {/* Configuración */}
        <TabsContent value="config" className="space-y-6">
          <div className="grid grid-cols-1 gap-6">
            <ImportConfigManager />
            {selectedBankAccount && (
              <AccountingConfiguration
                bankAccount={selectedBankAccount}
                onConfigurationSaved={handleReconciliationUpdate}
              />
            )}
          </div>
        </TabsContent>

        {/* Test */}
        <TabsContent value="test" className="space-y-6">
          <div className="max-w-2xl mx-auto">
            <h2 className="text-2xl font-bold mb-4">Formulario de Prueba</h2>
            <p className="text-gray-600 mb-6">
              Use este formulario para probar que los inputs funcionen correctamente.
              Si puede escribir normalmente aquí, el problema está en los otros componentes.
            </p>
            <TestForm />
          </div>
        </TabsContent>
      </Tabs>

      {/* Componentes flotantes */}
      <ConnectionStatus />
    </div>
  );
}

export default function ConciliacionBancariaPage() {
  return (
    <Suspense fallback={
      <div className="container mx-auto p-6 space-y-6 flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Cargando módulo de conciliación...</p>
        </div>
      </div>
    }>
      <ConciliacionBancariaContent />
    </Suspense>
  );
}