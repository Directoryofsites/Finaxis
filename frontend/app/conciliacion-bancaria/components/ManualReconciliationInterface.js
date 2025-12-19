'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Search, 
  Filter, 
  RefreshCw, 
  GitMerge, 
  Eye, 
  AlertCircle,
  CheckCircle,
  X,
  Calendar,
  DollarSign,
  FileText,
  ArrowRight,
  Undo2
} from 'lucide-react';

import UnmatchedMovementsList from './UnmatchedMovementsList';
import ReconciliationPreview from './ReconciliationPreview';
import ReconciliationHistory from './ReconciliationHistory';

export default function ManualReconciliationInterface({ bankAccount, onReconciliationUpdate }) {
  const [activeTab, setActiveTab] = useState('unmatched');
  const [unmatchedData, setUnmatchedData] = useState(null);
  const [selectedBankMovements, setSelectedBankMovements] = useState([]);
  const [selectedAccountingMovements, setSelectedAccountingMovements] = useState([]);
  const [matchPreview, setMatchPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    dateFrom: '',
    dateTo: '',
    searchQuery: '',
    amountMin: '',
    amountMax: ''
  });

  // Cargar movimientos no conciliados
  const loadUnmatchedMovements = useCallback(async () => {
    if (!bankAccount) return;

    setLoading(true);
    try {
      const params = new URLSearchParams({
        bank_account_id: bankAccount.id,
        limit: 50,
        offset: 0
      });

      if (filters.dateFrom) params.append('date_from', filters.dateFrom);
      if (filters.dateTo) params.append('date_to', filters.dateTo);

      const response = await fetch(`/api/conciliacion-bancaria/manual-reconciliation/unmatched-movements?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setUnmatchedData(data);
      } else {
        console.error('Error cargando movimientos no conciliados');
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  }, [bankAccount, filters.dateFrom, filters.dateTo]);

  // Cargar datos iniciales
  useEffect(() => {
    loadUnmatchedMovements();
  }, [loadUnmatchedMovements]);

  // Generar vista previa de conciliación
  const generateMatchPreview = async () => {
    if (selectedBankMovements.length !== 1 || selectedAccountingMovements.length === 0) {
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('bank_movement_id', selectedBankMovements[0].id);
      formData.append('accounting_movement_ids', selectedAccountingMovements.map(m => m.id).join(','));

      const response = await fetch('/api/conciliacion-bancaria/manual-reconciliation/match-preview', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: formData
      });

      if (response.ok) {
        const preview = await response.json();
        setMatchPreview(preview);
      } else {
        console.error('Error generando vista previa');
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Aplicar conciliación manual
  const applyManualReconciliation = async (notes = '') => {
    if (!matchPreview) return;

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('bank_movement_id', selectedBankMovements[0].id);
      formData.append('accounting_movement_ids', selectedAccountingMovements.map(m => m.id).join(','));
      if (notes) formData.append('notes', notes);

      const response = await fetch('/api/conciliacion-bancaria/reconcile/manual', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        
        // Limpiar selecciones
        setSelectedBankMovements([]);
        setSelectedAccountingMovements([]);
        setMatchPreview(null);
        
        // Recargar datos
        await loadUnmatchedMovements();
        onReconciliationUpdate?.();
        
        // Mostrar mensaje de éxito
        alert('Conciliación aplicada exitosamente');
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Error aplicando conciliación');
    } finally {
      setLoading(false);
    }
  };

  // Obtener sugerencias automáticas
  const getSuggestions = async (bankMovementId) => {
    try {
      const response = await fetch(`/api/conciliacion-bancaria/reconcile/suggestions/${bankMovementId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        return data.suggestions || [];
      }
    } catch (error) {
      console.error('Error obteniendo sugerencias:', error);
    }
    return [];
  };

  // Manejar selección de movimientos bancarios
  const handleBankMovementSelect = (movement, isSelected) => {
    if (isSelected) {
      setSelectedBankMovements([movement]); // Solo uno a la vez
      setSelectedAccountingMovements([]); // Limpiar selección contable
      setMatchPreview(null);
    } else {
      setSelectedBankMovements([]);
      setMatchPreview(null);
    }
  };

  // Manejar selección de movimientos contables
  const handleAccountingMovementSelect = (movement, isSelected) => {
    if (isSelected) {
      setSelectedAccountingMovements(prev => [...prev, movement]);
    } else {
      setSelectedAccountingMovements(prev => prev.filter(m => m.id !== movement.id));
    }
    setMatchPreview(null); // Limpiar preview cuando cambie la selección
  };

  // Aplicar filtros
  const applyFilters = () => {
    loadUnmatchedMovements();
  };

  // Limpiar filtros
  const clearFilters = () => {
    setFilters({
      dateFrom: '',
      dateTo: '',
      searchQuery: '',
      amountMin: '',
      amountMax: ''
    });
  };

  // Generar preview automáticamente cuando cambien las selecciones
  useEffect(() => {
    if (selectedBankMovements.length === 1 && selectedAccountingMovements.length > 0) {
      generateMatchPreview();
    } else {
      setMatchPreview(null);
    }
  }, [selectedBankMovements, selectedAccountingMovements]);

  return (
    <div className="space-y-6">
      {/* Header con información de la cuenta */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <GitMerge className="h-5 w-5" />
              <span>Conciliación Manual - {bankAccount.nombre}</span>
            </div>
            <Button 
              onClick={loadUnmatchedMovements} 
              disabled={loading}
              variant="outline"
              size="sm"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Actualizar
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* Filtros */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-4">
            <div>
              <Label htmlFor="dateFrom">Fecha desde</Label>
              <Input
                id="dateFrom"
                type="date"
                value={filters.dateFrom}
                onChange={(e) => setFilters(prev => ({ ...prev, dateFrom: e.target.value }))}
              />
            </div>
            <div>
              <Label htmlFor="dateTo">Fecha hasta</Label>
              <Input
                id="dateTo"
                type="date"
                value={filters.dateTo}
                onChange={(e) => setFilters(prev => ({ ...prev, dateTo: e.target.value }))}
              />
            </div>
            <div>
              <Label htmlFor="searchQuery">Buscar</Label>
              <Input
                id="searchQuery"
                placeholder="Descripción, referencia..."
                value={filters.searchQuery}
                onChange={(e) => setFilters(prev => ({ ...prev, searchQuery: e.target.value }))}
              />
            </div>
            <div className="flex space-x-2">
              <Button onClick={applyFilters} size="sm" className="mt-6">
                <Filter className="h-4 w-4 mr-2" />
                Filtrar
              </Button>
              <Button onClick={clearFilters} variant="outline" size="sm" className="mt-6">
                <X className="h-4 w-4 mr-2" />
                Limpiar
              </Button>
            </div>
          </div>

          {/* Estadísticas rápidas */}
          {unmatchedData && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-50 p-3 rounded-lg">
                <div className="text-sm text-blue-600">Movimientos Bancarios</div>
                <div className="text-2xl font-bold text-blue-800">
                  {unmatchedData.bank_movements?.length || 0}
                </div>
              </div>
              <div className="bg-green-50 p-3 rounded-lg">
                <div className="text-sm text-green-600">Movimientos Contables</div>
                <div className="text-2xl font-bold text-green-800">
                  {unmatchedData.accounting_movements?.length || 0}
                </div>
              </div>
              <div className="bg-purple-50 p-3 rounded-lg">
                <div className="text-sm text-purple-600">Seleccionados</div>
                <div className="text-2xl font-bold text-purple-800">
                  {selectedBankMovements.length + selectedAccountingMovements.length}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Navegación de pestañas */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="unmatched">Movimientos Pendientes</TabsTrigger>
          <TabsTrigger value="matching">Interfaz de Conciliación</TabsTrigger>
          <TabsTrigger value="history">Historial</TabsTrigger>
        </TabsList>

        {/* Movimientos no conciliados */}
        <TabsContent value="unmatched" className="space-y-4">
          <UnmatchedMovementsList
            unmatchedData={unmatchedData}
            selectedBankMovements={selectedBankMovements}
            selectedAccountingMovements={selectedAccountingMovements}
            onBankMovementSelect={handleBankMovementSelect}
            onAccountingMovementSelect={handleAccountingMovementSelect}
            onGetSuggestions={getSuggestions}
            loading={loading}
          />
        </TabsContent>

        {/* Interfaz de conciliación */}
        <TabsContent value="matching" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Panel de selección */}
            <Card>
              <CardHeader>
                <CardTitle>Selección Actual</CardTitle>
              </CardHeader>
              <CardContent>
                {selectedBankMovements.length === 0 && selectedAccountingMovements.length === 0 ? (
                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      Selecciona movimientos de la pestaña "Movimientos Pendientes" para comenzar la conciliación.
                    </AlertDescription>
                  </Alert>
                ) : (
                  <div className="space-y-4">
                    {/* Movimiento bancario seleccionado */}
                    {selectedBankMovements.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-sm text-blue-600 mb-2">Movimiento Bancario</h4>
                        {selectedBankMovements.map(movement => (
                          <div key={movement.id} className="border rounded p-3 bg-blue-50">
                            <div className="flex justify-between items-start">
                              <div>
                                <div className="font-medium">{movement.description}</div>
                                <div className="text-sm text-gray-600">
                                  {movement.transaction_date} • {movement.reference}
                                </div>
                              </div>
                              <div className="text-right">
                                <div className="font-bold text-lg">
                                  ${parseFloat(movement.amount).toLocaleString()}
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Movimientos contables seleccionados */}
                    {selectedAccountingMovements.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-sm text-green-600 mb-2">
                          Movimientos Contables ({selectedAccountingMovements.length})
                        </h4>
                        <div className="space-y-2">
                          {selectedAccountingMovements.map(movement => (
                            <div key={movement.id} className="border rounded p-3 bg-green-50">
                              <div className="flex justify-between items-start">
                                <div>
                                  <div className="font-medium">{movement.concepto}</div>
                                  <div className="text-sm text-gray-600">
                                    {movement.fecha} • Doc: {movement.documento_numero}
                                  </div>
                                </div>
                                <div className="text-right">
                                  <div className="font-bold">
                                    ${parseFloat(movement.valor).toLocaleString()}
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Vista previa de conciliación */}
            <Card>
              <CardHeader>
                <CardTitle>Vista Previa</CardTitle>
              </CardHeader>
              <CardContent>
                {matchPreview ? (
                  <ReconciliationPreview
                    preview={matchPreview}
                    onApply={applyManualReconciliation}
                    loading={loading}
                  />
                ) : (
                  <Alert>
                    <Eye className="h-4 w-4" />
                    <AlertDescription>
                      Selecciona un movimiento bancario y uno o más movimientos contables para ver la vista previa.
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Historial de conciliaciones */}
        <TabsContent value="history" className="space-y-4">
          <ReconciliationHistory
            bankAccount={bankAccount}
            onReconciliationUpdate={onReconciliationUpdate}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}