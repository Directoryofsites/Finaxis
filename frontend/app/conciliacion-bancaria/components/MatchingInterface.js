'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  CheckCircle, 
  XCircle, 
  ArrowRight,
  DollarSign,
  Calendar,
  FileText
} from 'lucide-react';

const MatchingInterface = ({ 
  bankMovements = [], 
  accountingMovements = [], 
  onMatch,
  onReject 
}) => {
  const [selectedBank, setSelectedBank] = useState(null);
  const [selectedAccounting, setSelectedAccounting] = useState(null);

  const handleMatch = () => {
    if (selectedBank && selectedAccounting && onMatch) {
      onMatch(selectedBank, selectedAccounting);
      setSelectedBank(null);
      setSelectedAccounting(null);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP'
    }).format(amount);
  };

  const formatDate = (date) => {
    return new Date(date).toLocaleDateString('es-CO');
  };

  const MovementCard = ({ movement, type, isSelected, onSelect }) => (
    <Card 
      className={`cursor-pointer transition-all ${
        isSelected ? 'ring-2 ring-blue-500 bg-blue-50' : 'hover:shadow-md'
      }`}
      onClick={() => onSelect(movement)}
    >
      <CardContent className="p-4">
        <div className="flex justify-between items-start mb-2">
          <div className="flex items-center gap-2">
            <Badge variant={type === 'bank' ? 'default' : 'secondary'}>
              {type === 'bank' ? 'Banco' : 'Contable'}
            </Badge>
            <span className="text-sm text-gray-500">
              <Calendar className="w-4 h-4 inline mr-1" />
              {formatDate(movement.fecha)}
            </span>
          </div>
          <div className={`font-semibold ${
            movement.monto >= 0 ? 'text-green-600' : 'text-red-600'
          }`}>
            {formatCurrency(Math.abs(movement.monto))}
          </div>
        </div>
        
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-gray-400" />
            <span className="text-sm font-medium">{movement.descripcion}</span>
          </div>
          
          {movement.referencia && (
            <div className="text-xs text-gray-500">
              Ref: {movement.referencia}
            </div>
          )}
          
          {movement.tercero && (
            <div className="text-xs text-gray-600">
              {movement.tercero}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Conciliación Manual</h3>
        <div className="flex gap-2">
          <Button
            onClick={handleMatch}
            disabled={!selectedBank || !selectedAccounting}
            className="flex items-center gap-2"
          >
            <CheckCircle className="w-4 h-4" />
            Conciliar Seleccionados
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Movimientos Bancarios */}
        <div className="space-y-4">
          <h4 className="font-medium text-gray-700 flex items-center gap-2">
            <DollarSign className="w-4 h-4" />
            Movimientos Bancarios ({bankMovements.length})
          </h4>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {bankMovements.map((movement) => (
              <MovementCard
                key={movement.id}
                movement={movement}
                type="bank"
                isSelected={selectedBank?.id === movement.id}
                onSelect={setSelectedBank}
              />
            ))}
            {bankMovements.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                No hay movimientos bancarios pendientes
              </div>
            )}
          </div>
        </div>

        {/* Indicador de Conciliación */}
        <div className="flex items-center justify-center">
          <div className="text-center space-y-4">
            <div className={`w-16 h-16 rounded-full border-2 border-dashed flex items-center justify-center ${
              selectedBank && selectedAccounting 
                ? 'border-green-500 bg-green-50' 
                : 'border-gray-300'
            }`}>
              <ArrowRight className={`w-8 h-8 ${
                selectedBank && selectedAccounting 
                  ? 'text-green-500' 
                  : 'text-gray-400'
              }`} />
            </div>
            
            {selectedBank && selectedAccounting && (
              <div className="space-y-2">
                <div className="text-sm font-medium text-green-600">
                  Listos para conciliar
                </div>
                <div className="text-xs text-gray-500">
                  Diferencia: {formatCurrency(
                    Math.abs(selectedBank.monto - selectedAccounting.monto)
                  )}
                </div>
              </div>
            )}
            
            {(!selectedBank || !selectedAccounting) && (
              <div className="text-sm text-gray-500">
                Selecciona un movimiento de cada lado
              </div>
            )}
          </div>
        </div>

        {/* Movimientos Contables */}
        <div className="space-y-4">
          <h4 className="font-medium text-gray-700 flex items-center gap-2">
            <FileText className="w-4 h-4" />
            Movimientos Contables ({accountingMovements.length})
          </h4>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {accountingMovements.map((movement) => (
              <MovementCard
                key={movement.id}
                movement={movement}
                type="accounting"
                isSelected={selectedAccounting?.id === movement.id}
                onSelect={setSelectedAccounting}
              />
            ))}
            {accountingMovements.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                No hay movimientos contables pendientes
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Información de ayuda */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <div className="w-5 h-5 rounded-full bg-blue-500 text-white flex items-center justify-center text-xs font-bold mt-0.5">
            i
          </div>
          <div className="text-sm text-blue-700">
            <p className="font-medium mb-1">Instrucciones:</p>
            <ul className="space-y-1 text-xs">
              <li>• Selecciona un movimiento bancario y uno contable que correspondan</li>
              <li>• Verifica que las fechas y montos sean coherentes</li>
              <li>• Haz clic en "Conciliar Seleccionados" para crear la conciliación</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MatchingInterface;