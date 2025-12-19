'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  History, 
  Eye, 
  Undo2, 
  Calendar, 
  DollarSign, 
  FileText,
  User,
  Filter,
  RefreshCw,
  Loader2,
  AlertCircle,
  CheckCircle,
  Clock,
  GitMerge
} from 'lucide-react';

export default function ReconciliationHistory({ bankAccount, onReconciliationUpdate }) {
  const [reconciliations, setReconciliations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedReconciliation, setSelectedReconciliation] = useState(null);
  const [showDetail, setShowDetail] = useState(false);
  const [filters, setFilters] = useState({
    dateFrom: '',
    dateTo: '',
    reconciliationType: '',
    status: ''
  });
  const [pagination, setPagination] = useState({
    limit: 20,
    offset: 0,
    total: 0
  });

  // Cargar historial de conciliaciones
  const loadReconciliations = async () => {
    if (!bankAccount) return;

    setLoading(true);
    try {
      const params = new URLSearchParams({
        bank_account_id: bankAccount.id,
        limit: pagination.limit,
        offset: pagination.offset
      });

      if (filters.dateFrom) params.append('date_from', filters.dateFrom);
      if (filters.dateTo) params.append('date_to', filters.dateTo);
      if (filters.reconciliationType) params.append('reconciliation_type', filters.reconciliationType);
      if (filters.status) params.append('status', filters.status);

      const response = await fetch(`/api/conciliacion-bancaria/reconciliations?${params}`);
      
      if (response.ok) {
        const data = await response.json();
        setReconciliations(data.reconciliations || []);
        setPagination(prev => ({ ...prev, total: data.total || 0 }));
      } else {
        console.error('Error cargando historial');
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Cargar detalle de una conciliación
  const loadReconciliationDetail = async (reconciliationId) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/conciliacion-bancaria/reconciliations/${reconciliationId}`);
      
      if (response.ok) {
        const detail = await response.json();
        setSelectedReconciliation(detail);
        setShowDetail(true);
      } else {
        console.error('Error cargando detalle');
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Revertir conciliación
  const reverseReconciliation = async (reconciliationId, reason) => {
    if (!reason.trim()) {
      alert('Debe proporcionar una razón para la reversión');
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('reason', reason);

      const response = await fetch(`/api/conciliacion-bancaria/reconcile/reverse/${reconciliationId}`, {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        alert('Conciliación revertida exitosamente');
        setShowDetail(false);
        setSelectedReconciliation(null);
        await loadReconciliations();
        onReconciliationUpdate?.();
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Error revirtiendo conciliación');
    } finally {
      setLoading(false);
    }
  };

  // Cargar datos iniciales
  useEffect(() => {
    loadReconciliations();
  }, [bankAccount, pagination.offset, pagination.limit]);

  // Formatear moneda
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0
    }).format(amount);
  };

  // Formatear fecha y hora
  const formatDateTime = (dateString) => {
    return new Date(dateString).toLocaleString('es-CO');
  };

  // Obtener variante del badge según el tipo
  const getTypeVariant = (type) => {
    switch (type) {
      case 'AUTO': return 'default';
      case 'MANUAL': return 'secondary';
      case 'ADJUSTMENT': return 'outline';
      default: return 'secondary';
    }
  };

  // Obtener variante del badge según el estado
  const getStatusVariant = (status) => {
    switch (status) {
      case 'ACTIVE': return 'default';
      case 'REVERSED': return 'destructive';
      default: return 'secondary';
    }
  };

  // Aplicar filtros
  const applyFilters = () => {
    setPagination(prev => ({ ...prev, offset: 0 }));
    loadReconciliations();
  };

  // Limpiar filtros
  const clearFilters = () => {
    setFilters({
      dateFrom: '',
      dateTo: '',
      reconciliationType: '',
      status: ''
    });
    setPagination(prev => ({ ...prev, offset: 0 }));
  };

  // Cambiar página
  const changePage = (newOffset) => {
    setPagination(prev => ({ ...prev, offset: newOffset }));
  };

  return (
    <div className="space-y-6">
      {/* Filtros */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Filter className="h-5 w-5" />
            <span>Filtros</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
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
              <Label htmlFor="reconciliationType">Tipo</Label>
              <select
                id="reconciliationType"
                className="w-full p-2 border border-gray-300 rounded-md"
                value={filters.reconciliationType}
                onChange={(e) => setFilters(prev => ({ ...prev, reconciliationType: e.target.value }))}
              >
                <option value="">Todos</option>
                <option value="AUTO">Automática</option>
                <option value="MANUAL">Manual</option>
                <option value="ADJUSTMENT">Ajuste</option>
              </select>
            </div>
            <div>
              <Label htmlFor="status">Estado</Label>
              <select
                id="status"
                className="w-full p-2 border border-gray-300 rounded-md"
                value={filters.status}
                onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
              >
                <option value="">Todos</option>
                <option value="ACTIVE">Activa</option>
                <option value="REVERSED">Revertida</option>
              </select>
            </div>
          </div>
          <div className="flex space-x-2 mt-4">
            <Button onClick={applyFilters} size="sm">
              <Filter className="h-4 w-4 mr-2" />
              Aplicar Filtros
            </Button>
            <Button onClick={clearFilters} variant="outline" size="sm">
              Limpiar
            </Button>
            <Button onClick={loadReconciliations} variant="outline" size="sm" disabled={loading}>
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Actualizar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Lista de conciliaciones */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <History className="h-5 w-5" />
              <span>Historial de Conciliaciones</span>
              <Badge variant="secondary">{pagination.total}</Badge>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center p-8">
              <Loader2 className="h-8 w-8 animate-spin" />
              <span className="ml-2">Cargando historial...</span>
            </div>
          ) : reconciliations.length === 0 ? (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                No se encontraron conciliaciones para los filtros seleccionados.
              </AlertDescription>
            </Alert>
          ) : (
            <div className="space-y-3">
              {reconciliations.map((reconciliation) => (
                <div
                  key={reconciliation.id}
                  className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <Badge variant={getTypeVariant(reconciliation.reconciliation_type)}>
                          {reconciliation.reconciliation_type === 'AUTO' ? 'Automática' :
                           reconciliation.reconciliation_type === 'MANUAL' ? 'Manual' : 'Ajuste'}
                        </Badge>
                        <Badge variant={getStatusVariant(reconciliation.status)}>
                          {reconciliation.status === 'ACTIVE' ? 'Activa' : 'Revertida'}
                        </Badge>
                        {reconciliation.confidence_score && (
                          <Badge variant="outline">
                            {Math.round(reconciliation.confidence_score * 100)}% confianza
                          </Badge>
                        )}
                      </div>
                      
                      <div className="space-y-1">
                        <div className="font-medium">
                          {reconciliation.bank_movement.description}
                        </div>
                        <div className="text-sm text-gray-600">
                          Fecha: {formatDateTime(reconciliation.reconciliation_date)} • 
                          Movimientos contables: {reconciliation.accounting_movements_count}
                        </div>
                        {reconciliation.notes && (
                          <div className="text-sm text-gray-500 italic">
                            "{reconciliation.notes}"
                          </div>
                        )}
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <div className="font-bold text-lg mb-2">
                        {formatCurrency(parseFloat(reconciliation.bank_movement.amount))}
                      </div>
                      <div className="flex space-x-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => loadReconciliationDetail(reconciliation.id)}
                        >
                          <Eye className="h-3 w-3 mr-1" />
                          Ver
                        </Button>
                        {reconciliation.status === 'ACTIVE' && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              const reason = prompt('Ingrese la razón para revertir esta conciliación:');
                              if (reason) {
                                reverseReconciliation(reconciliation.id, reason);
                              }
                            }}
                          >
                            <Undo2 className="h-3 w-3 mr-1" />
                            Revertir
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Paginación */}
          {pagination.total > pagination.limit && (
            <div className="flex items-center justify-between mt-6">
              <div className="text-sm text-gray-600">
                Mostrando {pagination.offset + 1} - {Math.min(pagination.offset + pagination.limit, pagination.total)} de {pagination.total}
              </div>
              <div className="flex space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={pagination.offset === 0}
                  onClick={() => changePage(Math.max(0, pagination.offset - pagination.limit))}
                >
                  Anterior
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={pagination.offset + pagination.limit >= pagination.total}
                  onClick={() => changePage(pagination.offset + pagination.limit)}
                >
                  Siguiente
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal de detalle */}
      {showDetail && selectedReconciliation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">Detalle de Conciliación</h2>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowDetail(false)}
              >
                Cerrar
              </Button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Movimiento bancario */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-blue-600">Movimiento Bancario</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div><strong>Descripción:</strong> {selectedReconciliation.bank_movement.description}</div>
                    <div><strong>Fecha:</strong> {formatDateTime(selectedReconciliation.bank_movement.transaction_date)}</div>
                    <div><strong>Referencia:</strong> {selectedReconciliation.bank_movement.reference || 'N/A'}</div>
                    <div><strong>Monto:</strong> {formatCurrency(parseFloat(selectedReconciliation.bank_movement.amount))}</div>
                    <div><strong>Estado:</strong> 
                      <Badge variant={getStatusVariant(selectedReconciliation.bank_movement.status)} className="ml-2">
                        {selectedReconciliation.bank_movement.status}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Movimientos contables */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-green-600">
                    Movimientos Contables ({selectedReconciliation.accounting_movements.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {selectedReconciliation.accounting_movements.map((movement) => (
                      <div key={movement.id} className="border-l-4 border-green-500 pl-3 py-2">
                        <div className="font-medium">{movement.concepto}</div>
                        <div className="text-sm text-gray-600">
                          {formatDateTime(movement.fecha)} • Doc: {movement.documento_numero}
                        </div>
                        <div className="text-sm">
                          <strong>Valor:</strong> {formatCurrency(parseFloat(movement.valor))}
                        </div>
                        {movement.referencia && (
                          <div className="text-sm text-gray-500">
                            Ref: {movement.referencia}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Información de la conciliación */}
            <Card className="mt-6">
              <CardHeader>
                <CardTitle>Información de la Conciliación</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div><strong>Tipo:</strong> 
                    <Badge variant={getTypeVariant(selectedReconciliation.reconciliation_type)} className="ml-2">
                      {selectedReconciliation.reconciliation_type === 'AUTO' ? 'Automática' :
                       selectedReconciliation.reconciliation_type === 'MANUAL' ? 'Manual' : 'Ajuste'}
                    </Badge>
                  </div>
                  <div><strong>Estado:</strong> 
                    <Badge variant={getStatusVariant(selectedReconciliation.status)} className="ml-2">
                      {selectedReconciliation.status === 'ACTIVE' ? 'Activa' : 'Revertida'}
                    </Badge>
                  </div>
                  <div><strong>Fecha de conciliación:</strong> {formatDateTime(selectedReconciliation.reconciliation_date)}</div>
                  {selectedReconciliation.confidence_score && (
                    <div><strong>Confianza:</strong> {Math.round(selectedReconciliation.confidence_score * 100)}%</div>
                  )}
                  <div><strong>Usuario:</strong> ID {selectedReconciliation.user_id}</div>
                  {selectedReconciliation.notes && (
                    <div className="col-span-2">
                      <strong>Notas:</strong>
                      <div className="mt-1 p-2 bg-gray-50 rounded text-sm">
                        {selectedReconciliation.notes}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}