'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Lightbulb, 
  Eye, 
  Calendar, 
  DollarSign, 
  FileText,
  ArrowRight,
  Loader2,
  AlertCircle,
  TrendingUp,
  TrendingDown
} from 'lucide-react';

export default function UnmatchedMovementsList({
  unmatchedData,
  selectedBankMovements,
  selectedAccountingMovements,
  onBankMovementSelect,
  onAccountingMovementSelect,
  onGetSuggestions,
  loading
}) {
  const [suggestions, setSuggestions] = useState({});
  const [loadingSuggestions, setLoadingSuggestions] = useState({});

  // Obtener sugerencias para un movimiento bancario
  const handleGetSuggestions = async (bankMovement) => {
    setLoadingSuggestions(prev => ({ ...prev, [bankMovement.id]: true }));
    
    try {
      const suggestions = await onGetSuggestions(bankMovement.id);
      setSuggestions(prev => ({ ...prev, [bankMovement.id]: suggestions }));
    } catch (error) {
      console.error('Error obteniendo sugerencias:', error);
    } finally {
      setLoadingSuggestions(prev => ({ ...prev, [bankMovement.id]: false }));
    }
  };

  // Verificar si un movimiento está seleccionado
  const isBankMovementSelected = (movement) => {
    return selectedBankMovements.some(m => m.id === movement.id);
  };

  const isAccountingMovementSelected = (movement) => {
    return selectedAccountingMovements.some(m => m.id === movement.id);
  };

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

  if (!unmatchedData) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Cargando movimientos...</span>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Movimientos Bancarios */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
              <span>Movimientos Bancarios</span>
              <Badge variant="secondary">{unmatchedData.bank_movements?.length || 0}</Badge>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {unmatchedData.bank_movements?.length === 0 ? (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                No hay movimientos bancarios pendientes de conciliación.
              </AlertDescription>
            </Alert>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {unmatchedData.bank_movements?.map((movement) => (
                <div
                  key={movement.id}
                  className={`border rounded-lg p-4 transition-all cursor-pointer ${
                    isBankMovementSelected(movement)
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => onBankMovementSelect(movement, !isBankMovementSelected(movement))}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3">
                      <Checkbox
                        checked={isBankMovementSelected(movement)}
                        onChange={() => {}}
                        className="mt-1"
                      />
                      <div className="flex-1">
                        <div className="font-medium text-gray-900 mb-1">
                          {movement.description}
                        </div>
                        <div className="flex items-center space-x-4 text-sm text-gray-600">
                          <div className="flex items-center space-x-1">
                            <Calendar className="h-3 w-3" />
                            <span>{formatDate(movement.transaction_date)}</span>
                          </div>
                          {movement.reference && (
                            <div className="flex items-center space-x-1">
                              <FileText className="h-3 w-3" />
                              <span>{movement.reference}</span>
                            </div>
                          )}
                        </div>
                        {movement.transaction_type && (
                          <Badge variant="outline" className="mt-2 text-xs">
                            {movement.transaction_type}
                          </Badge>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`font-bold text-lg flex items-center ${
                        parseFloat(movement.amount) >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {parseFloat(movement.amount) >= 0 ? (
                          <TrendingUp className="h-4 w-4 mr-1" />
                        ) : (
                          <TrendingDown className="h-4 w-4 mr-1" />
                        )}
                        {formatCurrency(Math.abs(parseFloat(movement.amount)))}
                      </div>
                      {movement.balance && (
                        <div className="text-sm text-gray-500">
                          Saldo: {formatCurrency(parseFloat(movement.balance))}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Botón de sugerencias */}
                  <div className="mt-3 flex justify-between items-center">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleGetSuggestions(movement);
                      }}
                      disabled={loadingSuggestions[movement.id]}
                    >
                      {loadingSuggestions[movement.id] ? (
                        <Loader2 className="h-3 w-3 animate-spin mr-1" />
                      ) : (
                        <Lightbulb className="h-3 w-3 mr-1" />
                      )}
                      Sugerencias
                    </Button>

                    {suggestions[movement.id] && suggestions[movement.id].length > 0 && (
                      <Badge variant="secondary">
                        {suggestions[movement.id].length} sugerencias
                      </Badge>
                    )}
                  </div>

                  {/* Mostrar sugerencias */}
                  {suggestions[movement.id] && suggestions[movement.id].length > 0 && (
                    <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded">
                      <div className="text-sm font-medium text-yellow-800 mb-2">
                        Sugerencias automáticas:
                      </div>
                      <div className="space-y-2">
                        {suggestions[movement.id].slice(0, 3).map((suggestion, index) => (
                          <div
                            key={index}
                            className="flex items-center justify-between text-sm p-2 bg-white rounded border"
                          >
                            <div>
                              <div className="font-medium">
                                {suggestion.accounting_movement.concepto}
                              </div>
                              <div className="text-gray-600">
                                {formatDate(suggestion.accounting_movement.fecha)} • 
                                Doc: {suggestion.accounting_movement.documento_numero}
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="font-medium">
                                {formatCurrency(Math.abs(parseFloat(suggestion.accounting_movement.valor)))}
                              </div>
                              <Badge 
                                variant={suggestion.confidence_score > 0.8 ? "default" : "secondary"}
                                className="text-xs"
                              >
                                {Math.round(suggestion.confidence_score * 100)}% confianza
                              </Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Movimientos Contables */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span>Movimientos Contables</span>
              <Badge variant="secondary">{unmatchedData.accounting_movements?.length || 0}</Badge>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {unmatchedData.accounting_movements?.length === 0 ? (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                No hay movimientos contables pendientes de conciliación.
              </AlertDescription>
            </Alert>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {unmatchedData.accounting_movements?.map((movement) => (
                <div
                  key={movement.id}
                  className={`border rounded-lg p-4 transition-all cursor-pointer ${
                    isAccountingMovementSelected(movement)
                      ? 'border-green-500 bg-green-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => onAccountingMovementSelect(movement, !isAccountingMovementSelected(movement))}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3">
                      <Checkbox
                        checked={isAccountingMovementSelected(movement)}
                        onChange={() => {}}
                        className="mt-1"
                      />
                      <div className="flex-1">
                        <div className="font-medium text-gray-900 mb-1">
                          {movement.concepto}
                        </div>
                        <div className="flex items-center space-x-4 text-sm text-gray-600">
                          <div className="flex items-center space-x-1">
                            <Calendar className="h-3 w-3" />
                            <span>{formatDate(movement.fecha)}</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <FileText className="h-3 w-3" />
                            <span>Doc: {movement.documento_numero}</span>
                          </div>
                        </div>
                        {movement.referencia && (
                          <div className="text-sm text-gray-600 mt-1">
                            Ref: {movement.referencia}
                          </div>
                        )}
                        {movement.documento_tipo && (
                          <Badge variant="outline" className="mt-2 text-xs">
                            {movement.documento_tipo}
                          </Badge>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`font-bold text-lg flex items-center ${
                        parseFloat(movement.valor) >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {parseFloat(movement.valor) >= 0 ? (
                          <TrendingUp className="h-4 w-4 mr-1" />
                        ) : (
                          <TrendingDown className="h-4 w-4 mr-1" />
                        )}
                        {formatCurrency(Math.abs(parseFloat(movement.valor)))}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        D: {formatCurrency(parseFloat(movement.debito))} | 
                        C: {formatCurrency(parseFloat(movement.credito))}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}