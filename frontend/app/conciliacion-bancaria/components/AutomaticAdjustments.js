'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { 
  Zap, 
  Eye, 
  CheckCircle, 
  AlertTriangle, 
  DollarSign, 
  Calendar, 
  FileText,
  RefreshCw,
  Loader2,
  TrendingUp,
  TrendingDown,
  Settings,
  History
} from 'lucide-react';

export default function AutomaticAdjustments({ bankAccount, onAdjustmentComplete }) {
  const [adjustmentPreview, setAdjustmentPreview] = useState(null);
  const [selectedAdjustments, setSelectedAdjustments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [notes, setNotes] = useState('');
  const [filters, setFilters] = useState({
    dateFrom: '',
    dateTo: ''
  });
  const [adjustmentHistory, setAdjustmentHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);

  // Cargar vista previa de ajustes
  const loadAdjustmentPreview = async () => {
    if (!bankAccount) {
      console.warn('No hay cuenta bancaria seleccionada para cargar ajustes');
      return;
    }

    setLoading(true);
    try {
      const params = new URLSearchParams({
        bank_account_id: bankAccount.id
      });

      if (filters.dateFrom) params.append('date_from', filters.dateFrom);
      if (filters.dateTo) params.append('date_to', filters.dateTo);

      const response = await fetch(`/api/conciliacion-bancaria/adjustments/preview/${bankAccount.id}?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.status === 'success') {
          setAdjustmentPreview(result.data || result);
          setSelectedAdjustments([]); // Limpiar selección
        } else {
          console.error('Error en respuesta del servidor:', result.message || 'Error desconocido');
          setAdjustmentPreview({ adjustments: [], summary: { total: 0, amount: 0 } });
        }
      } else {
        const errorText = await response.text();
        console.error('Error HTTP cargando vista previa de ajustes:', response.status, errorText);
        setAdjustmentPreview({ adjustments: [], summary: { total: 0, amount: 0 } });
      }
    } catch (error) {
      console.error('Error de red cargando vista previa de ajustes:', error);
      setAdjustmentPreview({ adjustments: [], summary: { total: 0, amount: 0 } });
    } finally {
      setLoading(false);
    }
  };

  // Cargar historial de ajustes
  const loadAdjustmentHistory = async () => {
    if (!bankAccount) return;

    try {
      const params = new URLSearchParams({
        bank_account_id: bankAccount.id,
        limit: 20
      });

      const response = await fetch(`/api/conciliacion-bancaria/adjustments/history?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setAdjustmentHistory(data.adjustments || []);
      }
    } catch (error) {
      console.error('Error cargando historial:', error);
    }
  };

  // Aplicar ajustes seleccionados
  const applySelectedAdjustments = async () => {
    if (selectedAdjustments.length === 0) {
      alert('Selecciona al menos un ajuste para aplicar');
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('bank_movement_ids', selectedAdjustments.join(','));
      if (notes) formData.append('notes', notes);

      const response = await fetch('/api/conciliacion-bancaria/adjustments/apply', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        
        alert(`Ajustes aplicados: ${result.total_successful} exitosos, ${result.total_failed} fallidos`);
        
        // Limpiar estado y recargar
        setSelectedAdjustments([]);
        setNotes('');
        await loadAdjustmentPreview();
        await loadAdjustmentHistory();
        onAdjustmentComplete?.();
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Error aplicando ajustes');
    } finally {
      setLoading(false);
    }
  };

  // Manejar selección de ajustes
  const handleAdjustmentSelect = (bankMovementId, isSelected) => {
    if (isSelected) {
      setSelectedAdjustments(prev => [...prev, bankMovementId]);
    } else {
      setSelectedAdjustments(prev => prev.filter(id => id !== bankMovementId));
    }
  };

  // Seleccionar todos los ajustes
  const selectAllAdjustments = () => {
    if (!adjustmentPreview?.adjustments) return;
    
    const allIds = adjustmentPreview.adjustments.map(adj => adj.bank_movement_id);
    setSelectedAdjustments(allIds);
  };

  // Deseleccionar todos los ajustes
  const deselectAllAdjustments = () => {
    setSelectedAdjustments([]);
  };

  // Cargar datos iniciales
  useEffect(() => {
    if (bankAccount) {
      loadAdjustmentPreview();
      loadAdjustmentHistory();
    }
  }, [bankAccount]);

  // Formatear moneda
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0
    }).format(amount);
  };

  // Formatear fecha
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('es-CO');
  };

  // Obtener color del badge según el tipo de ajuste
  const getAdjustmentTypeColor = (type) => {
    switch (type) {
      case 'COMMISSION': return 'destructive';
      case 'INTEREST': return 'default';
      case 'DEBIT_NOTE': return 'secondary';
      case 'CREDIT_NOTE': return 'outline';
      default: return 'secondary';
    }
  };

  // Obtener icono según el tipo de ajuste
  const getAdjustmentIcon = (type) => {
    switch (type) {
      case 'COMMISSION': return <TrendingDown className="h-4 w-4" />;
      case 'INTEREST': return <TrendingUp className="h-4 w-4" />;
      case 'DEBIT_NOTE': return <TrendingDown className="h-4 w-4" />;
      case 'CREDIT_NOTE': return <TrendingUp className="h-4 w-4" />;
      default: return <FileText className="h-4 w-4" />;
    }
  };

  if (!bankAccount) {
    return (
      <Alert>
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          Selecciona una cuenta bancaria para detectar ajustes automáticos.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header con controles */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Zap className="h-5 w-5" />
              <span>Ajustes Automáticos - {bankAccount.nombre}</span>
            </div>
            <div className="flex space-x-2">
              <Button
                onClick={() => setShowHistory(!showHistory)}
                variant="outline"
                size="sm"
              >
                <History className="h-4 w-4 mr-2" />
                {showHistory ? 'Ocultar' : 'Ver'} Historial
              </Button>
              <Button 
                onClick={loadAdjustmentPreview} 
                disabled={loading}
                variant="outline"
                size="sm"
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Actualizar
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* Filtros */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
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
            <div className="flex items-end">
              <Button onClick={loadAdjustmentPreview} disabled={loading}>
                <Eye className="h-4 w-4 mr-2" />
                Detectar Ajustes
              </Button>
            </div>
          </div>

          {/* Resumen */}
          {adjustmentPreview && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-blue-50 p-3 rounded-lg">
                <div className="text-sm text-blue-600">Movimientos Analizados</div>
                <div className="text-2xl font-bold text-blue-800">
                  {adjustmentPreview.summary.total_movements_analyzed}
                </div>
              </div>
              <div className="bg-green-50 p-3 rounded-lg">
                <div className="text-sm text-green-600">Ajustes Detectados</div>
                <div className="text-2xl font-bold text-green-800">
                  {adjustmentPreview.summary.total_adjustments_detected}
                </div>
              </div>
              <div className="bg-purple-50 p-3 rounded-lg">
                <div className="text-sm text-purple-600">Monto Total</div>
                <div className="text-2xl font-bold text-purple-800">
                  {formatCurrency(adjustmentPreview.summary.total_amount)}
                </div>
              </div>
              <div className="bg-yellow-50 p-3 rounded-lg">
                <div className="text-sm text-yellow-600">Seleccionados</div>
                <div className="text-2xl font-bold text-yellow-800">
                  {selectedAdjustments.length}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Lista de ajustes detectados */}
      {adjustmentPreview && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Ajustes Detectados ({adjustmentPreview.adjustments.length})</span>
              <div className="flex space-x-2">
                <Button
                  onClick={selectAllAdjustments}
                  variant="outline"
                  size="sm"
                  disabled={adjustmentPreview.adjustments.length === 0}
                >
                  Seleccionar Todos
                </Button>
                <Button
                  onClick={deselectAllAdjustments}
                  variant="outline"
                  size="sm"
                  disabled={selectedAdjustments.length === 0}
                >
                  Deseleccionar Todos
                </Button>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {adjustmentPreview.adjustments.length === 0 ? (
              <Alert>
                <CheckCircle className="h-4 w-4" />
                <AlertDescription>
                  No se detectaron ajustes automáticos para el período seleccionado.
                </AlertDescription>
              </Alert>
            ) : (
              <div className="space-y-4">
                {adjustmentPreview.adjustments.map((adjustment) => (
                  <div
                    key={adjustment.bank_movement_id}
                    className={`border rounded-lg p-4 transition-all ${
                      selectedAdjustments.includes(adjustment.bank_movement_id)
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3">
                        <Checkbox
                          checked={selectedAdjustments.includes(adjustment.bank_movement_id)}
                          onChange={(e) => handleAdjustmentSelect(
                            adjustment.bank_movement_id, 
                            e.target.checked
                          )}
                          className="mt-1"
                        />
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <Badge variant={getAdjustmentTypeColor(adjustment.adjustment_type)}>
                              <div className="flex items-center space-x-1">
                                {getAdjustmentIcon(adjustment.adjustment_type)}
                                <span>{adjustment.adjustment_description}</span>
                              </div>
                            </Badge>
                            {adjustment.requires_approval && (
                              <Badge variant="outline">
                                <AlertTriangle className="h-3 w-3 mr-1" />
                                Requiere Aprobación
                              </Badge>
                            )}
                          </div>
                          
                          <div className="font-medium text-gray-900 mb-1">
                            {adjustment.bank_movement.description}
                          </div>
                          
                          <div className="flex items-center space-x-4 text-sm text-gray-600">
                            <div className="flex items-center space-x-1">
                              <Calendar className="h-3 w-3" />
                              <span>{formatDate(adjustment.bank_movement.transaction_date)}</span>
                            </div>
                            {adjustment.bank_movement.reference && (
                              <div className="flex items-center space-x-1">
                                <FileText className="h-3 w-3" />
                                <span>{adjustment.bank_movement.reference}</span>
                              </div>
                            )}
                          </div>

                          {/* Detalle de asientos */}
                          <div className="mt-3 p-3 bg-gray-50 rounded border">
                            <div className="text-sm font-medium text-gray-700 mb-2">
                              Asientos propuestos:
                            </div>
                            <div className="space-y-1">
                              {adjustment.entries.map((entry, index) => (
                                <div key={index} className="flex justify-between text-sm">
                                  <span>{entry.account_code} - {entry.account_name}</span>
                                  <span>
                                    {entry.debit > 0 ? (
                                      <span className="text-red-600">
                                        Débito: {formatCurrency(entry.debit)}
                                      </span>
                                    ) : (
                                      <span className="text-green-600">
                                        Crédito: {formatCurrency(entry.credit)}
                                      </span>
                                    )}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <div className="text-right">
                        <div className="font-bold text-lg">
                          {formatCurrency(adjustment.total_amount)}
                        </div>
                        <div className="text-sm text-gray-500">
                          {adjustment.bank_movement.amount < 0 ? 'Débito' : 'Crédito'}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Panel de aplicación */}
      {selectedAdjustments.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Aplicar Ajustes Seleccionados</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <Label htmlFor="notes">Notas adicionales (opcional)</Label>
                <Textarea
                  id="notes"
                  placeholder="Agregar comentarios sobre estos ajustes..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={3}
                />
              </div>

              <div className="flex justify-between items-center">
                <div className="text-sm text-gray-600">
                  {selectedAdjustments.length} ajuste(s) seleccionado(s)
                </div>
                <Button 
                  onClick={applySelectedAdjustments}
                  disabled={loading}
                >
                  {loading && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Aplicar Ajustes
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Historial de ajustes */}
      {showHistory && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <History className="h-5 w-5" />
              <span>Historial de Ajustes Aplicados</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {adjustmentHistory.length === 0 ? (
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  No hay ajustes aplicados en el historial.
                </AlertDescription>
              </Alert>
            ) : (
              <div className="space-y-3">
                {adjustmentHistory.map((adjustment) => (
                  <div key={adjustment.id} className="border rounded-lg p-3">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="font-medium">{adjustment.description}</div>
                        <div className="text-sm text-gray-600">
                          {formatDate(adjustment.transaction_date)} • 
                          Ref: {adjustment.reference || 'N/A'}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-bold">
                          {formatCurrency(Math.abs(adjustment.amount))}
                        </div>
                        <Badge variant="default" className="text-xs">
                          Aplicado
                        </Badge>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}