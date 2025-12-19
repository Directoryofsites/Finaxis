'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { 
  CheckCircle, 
  AlertTriangle, 
  DollarSign, 
  Calendar, 
  FileText,
  ArrowRight,
  Loader2,
  TrendingUp,
  TrendingDown,
  Equal,
  X
} from 'lucide-react';

export default function ReconciliationPreview({ preview, onApply, loading }) {
  const [notes, setNotes] = useState('');
  const [showConfirmation, setShowConfirmation] = useState(false);

  if (!preview) {
    return null;
  }

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

  // Determinar el color del badge de confianza
  const getConfidenceBadgeVariant = (score) => {
    if (score >= 0.9) return 'default'; // Verde
    if (score >= 0.7) return 'secondary'; // Amarillo
    return 'destructive'; // Rojo
  };

  // Determinar el texto del badge de confianza
  const getConfidenceText = (score) => {
    if (score >= 0.9) return 'Alta confianza';
    if (score >= 0.7) return 'Confianza media';
    return 'Baja confianza';
  };

  const handleApply = () => {
    if (preview.totals.is_balanced || showConfirmation) {
      onApply(notes);
      setShowConfirmation(false);
      setNotes('');
    } else {
      setShowConfirmation(true);
    }
  };

  const handleCancel = () => {
    setShowConfirmation(false);
  };

  return (
    <div className="space-y-4">
      {/* Resumen de la conciliación */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-gray-900">Resumen de Conciliación</h3>
          <Badge variant={getConfidenceBadgeVariant(preview.confidence_score)}>
            {getConfidenceText(preview.confidence_score)} ({Math.round(preview.confidence_score * 100)}%)
          </Badge>
        </div>

        {/* Comparación de montos */}
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="text-center">
            <div className="text-sm text-gray-600">Movimiento Bancario</div>
            <div className={`text-lg font-bold ${
              parseFloat(preview.totals.bank_amount) >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {formatCurrency(Math.abs(parseFloat(preview.totals.bank_amount)))}
            </div>
          </div>
          
          <div className="flex items-center justify-center">
            {preview.totals.is_balanced ? (
              <Equal className="h-6 w-6 text-green-500" />
            ) : (
              <X className="h-6 w-6 text-red-500" />
            )}
          </div>
          
          <div className="text-center">
            <div className="text-sm text-gray-600">Total Contable</div>
            <div className={`text-lg font-bold ${
              parseFloat(preview.totals.accounting_total) >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {formatCurrency(Math.abs(parseFloat(preview.totals.accounting_total)))}
            </div>
          </div>
        </div>

        {/* Diferencia */}
        {!preview.totals.is_balanced && (
          <div className="text-center p-3 bg-yellow-50 border border-yellow-200 rounded">
            <div className="text-sm text-yellow-700">Diferencia</div>
            <div className="text-lg font-bold text-yellow-800">
              {formatCurrency(parseFloat(preview.totals.difference))}
            </div>
          </div>
        )}
      </div>

      {/* Detalle del movimiento bancario */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm text-blue-600">Movimiento Bancario</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Descripción:</span>
              <span className="font-medium">{preview.bank_movement.description}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Fecha:</span>
              <span>{formatDate(preview.bank_movement.transaction_date)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Referencia:</span>
              <span>{preview.bank_movement.reference || 'N/A'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Monto:</span>
              <span className="font-bold">
                {formatCurrency(parseFloat(preview.bank_movement.amount))}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Detalle de movimientos contables */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm text-green-600">
            Movimientos Contables ({preview.accounting_movements.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {preview.accounting_movements.map((movement, index) => (
              <div key={movement.id} className="border-l-4 border-green-500 pl-3 py-2">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="font-medium">{movement.concepto}</div>
                    <div className="text-sm text-gray-600">
                      {formatDate(movement.fecha)} • Doc: {movement.documento_numero}
                    </div>
                    {movement.referencia && (
                      <div className="text-sm text-gray-500">
                        Ref: {movement.referencia}
                      </div>
                    )}
                  </div>
                  <div className="text-right">
                    <div className="font-bold">
                      {formatCurrency(parseFloat(movement.valor))}
                    </div>
                    <div className="text-xs text-gray-500">
                      D: {formatCurrency(parseFloat(movement.debito))} | 
                      C: {formatCurrency(parseFloat(movement.credito))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Advertencias */}
      {preview.warnings && preview.warnings.length > 0 && (
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            <div className="space-y-1">
              {preview.warnings.map((warning, index) => (
                <div key={index}>{warning}</div>
              ))}
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Notas */}
      <div>
        <Label htmlFor="notes">Notas de conciliación (opcional)</Label>
        <Textarea
          id="notes"
          placeholder="Agregar comentarios sobre esta conciliación..."
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={3}
        />
      </div>

      {/* Confirmación para diferencias */}
      {showConfirmation && !preview.totals.is_balanced && (
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            <div className="space-y-2">
              <div className="font-medium">¿Confirmar conciliación con diferencia?</div>
              <div>
                Existe una diferencia de {formatCurrency(parseFloat(preview.totals.difference))} 
                entre el movimiento bancario y los movimientos contables. 
                ¿Deseas proceder con la conciliación?
              </div>
              <div className="flex space-x-2 mt-3">
                <Button 
                  onClick={handleApply} 
                  disabled={loading}
                  variant="destructive"
                  size="sm"
                >
                  {loading && <Loader2 className="h-3 w-3 animate-spin mr-1" />}
                  Sí, conciliar con diferencia
                </Button>
                <Button 
                  onClick={handleCancel} 
                  variant="outline"
                  size="sm"
                >
                  Cancelar
                </Button>
              </div>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Botones de acción */}
      {!showConfirmation && (
        <div className="flex justify-end space-x-2">
          <Button 
            onClick={handleApply} 
            disabled={loading}
            className={preview.totals.is_balanced ? '' : 'bg-yellow-600 hover:bg-yellow-700'}
          >
            {loading && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
            <CheckCircle className="h-4 w-4 mr-2" />
            {preview.totals.is_balanced ? 'Aplicar Conciliación' : 'Conciliar con Diferencia'}
          </Button>
        </div>
      )}
    </div>
  );
}