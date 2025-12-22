'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { TestTube } from 'lucide-react';

export default function TestForm() {
  const [testData, setTestData] = useState({
    name: '',
    email: '',
    bank: '',
    amount: ''
  });

  const handleChange = (field, value) => {
    console.log(`Changing ${field} to:`, value);
    setTestData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmit = () => {
    console.log('Submitting:', testData);
    alert(`Datos: ${JSON.stringify(testData, null, 2)}`);
  };

  return (
    <Card className="max-w-md mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <TestTube className="h-5 w-5" />
          <span>Formulario de Prueba</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label htmlFor="test_name">Nombre</Label>
          <Input
            id="test_name"
            value={testData.name}
            onChange={(e) => handleChange('name', e.target.value)}
            placeholder="Escribe tu nombre"
          />
          <div className="text-xs text-gray-500 mt-1">
            Valor actual: "{testData.name}"
          </div>
        </div>

        <div>
          <Label htmlFor="test_email">Email</Label>
          <Input
            id="test_email"
            type="email"
            value={testData.email}
            onChange={(e) => handleChange('email', e.target.value)}
            placeholder="tu@email.com"
          />
          <div className="text-xs text-gray-500 mt-1">
            Valor actual: "{testData.email}"
          </div>
        </div>

        <div>
          <Label htmlFor="test_bank">Banco</Label>
          <select
            id="test_bank"
            className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
            value={testData.bank}
            onChange={(e) => handleChange('bank', e.target.value)}
          >
            <option value="">Seleccionar banco...</option>
            <option value="bancolombia">Bancolombia</option>
            <option value="davivienda">Davivienda</option>
            <option value="bbva">BBVA</option>
            <option value="banco_bogota">Banco de Bogotá</option>
          </select>
          <div className="text-xs text-gray-500 mt-1">
            Valor actual: "{testData.bank}"
          </div>
        </div>

        <div>
          <Label htmlFor="test_amount">Monto</Label>
          <Input
            id="test_amount"
            type="number"
            value={testData.amount}
            onChange={(e) => handleChange('amount', e.target.value)}
            placeholder="0.00"
          />
          <div className="text-xs text-gray-500 mt-1">
            Valor actual: "{testData.amount}"
          </div>
        </div>

        <Button onClick={handleSubmit} className="w-full">
          Probar Envío
        </Button>

        <div className="bg-gray-50 p-3 rounded text-xs">
          <strong>Estado completo:</strong>
          <pre>{JSON.stringify(testData, null, 2)}</pre>
        </div>
      </CardContent>
    </Card>
  );
}