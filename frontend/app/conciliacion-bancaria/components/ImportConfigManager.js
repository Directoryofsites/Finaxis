'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { 
  Settings, 
  Plus,
  Edit,
  Trash2,
  Save,
  TestTube,
  AlertCircle,
  CheckCircle,
  FileText,
  Download,
  Upload
} from 'lucide-react';

export default function ImportConfigManager() {
  const [configs, setConfigs] = useState([]);
  const [selectedConfig, setSelectedConfig] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [loading, setLoading] = useState(false);
  const [testResult, setTestResult] = useState(null);

  // Formulario para nueva configuración o edición
  const [formData, setFormData] = useState({
    name: '',
    bank_name: '',
    file_format: 'csv',
    delimiter: ',',
    encoding: 'utf-8',
    has_header: true,
    field_mappings: {
      date: '',
      description: '',
      amount: '',
      reference: '',
      balance: ''
    },
    date_format: 'DD/MM/YYYY',
    amount_format: 'decimal',
    skip_rows: 0,
    validation_rules: {
      required_fields: ['date', 'description', 'amount'],
      date_validation: true,
      amount_validation: true
    }
  });

  useEffect(() => {
    loadConfigurations();
  }, []);

  const loadConfigurations = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/conciliacion-bancaria/import-configs');
      if (response.ok) {
        const data = await response.json();
        setConfigs(data);
      }
    } catch (error) {
      console.error('Error cargando configuraciones:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNew = () => {
    setIsCreating(true);
    setIsEditing(false);
    setSelectedConfig(null);
    setFormData({
      name: '',
      bank_name: '',
      file_format: 'csv',
      delimiter: ',',
      encoding: 'utf-8',
      has_header: true,
      field_mappings: {
        date: '',
        description: '',
        amount: '',
        reference: '',
        balance: ''
      },
      date_format: 'DD/MM/YYYY',
      amount_format: 'decimal',
      skip_rows: 0,
      validation_rules: {
        required_fields: ['date', 'description', 'amount'],
        date_validation: true,
        amount_validation: true
      }
    });
  };

  const handleEdit = (config) => {
    setSelectedConfig(config);
    setIsEditing(true);
    setIsCreating(false);
    setFormData(config);
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      const url = isCreating 
        ? '/api/conciliacion-bancaria/import-configs'
        : `/api/conciliacion-bancaria/import-configs/${selectedConfig.id}`;
      
      const method = isCreating ? 'POST' : 'PUT';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        await loadConfigurations();
        setIsCreating(false);
        setIsEditing(false);
        setSelectedConfig(null);
      }
    } catch (error) {
      console.error('Error guardando configuración:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (configId) => {
    if (!confirm('¿Estás seguro de que quieres eliminar esta configuración?')) {
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`/api/conciliacion-bancaria/import-configs/${configId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        await loadConfigurations();
      }
    } catch (error) {
      console.error('Error eliminando configuración:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTestConfig = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/conciliacion-bancaria/import-configs/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        const result = await response.json();
        setTestResult(result);
      }
    } catch (error) {
      console.error('Error probando configuración:', error);
      setTestResult({ success: false, error: 'Error de conexión' });
    } finally {
      setLoading(false);
    }
  };

  const handleFieldMappingChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      field_mappings: {
        ...prev.field_mappings,
        [field]: value
      }
    }));
  };

  const ConfigurationForm = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>{isCreating ? 'Nueva Configuración' : 'Editar Configuración'}</span>
          <div className="flex gap-2">
            <Button onClick={handleTestConfig} variant="outline" size="sm">
              <TestTube className="h-4 w-4 mr-2" />
              Probar
            </Button>
            <Button onClick={handleSave} size="sm">
              <Save className="h-4 w-4 mr-2" />
              Guardar
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Información básica */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="name">Nombre de la configuración</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              placeholder="Ej: Banco Nacional CSV"
            />
          </div>
          <div>
            <Label htmlFor="bank_name">Nombre del banco</Label>
            <Input
              id="bank_name"
              value={formData.bank_name}
              onChange={(e) => setFormData(prev => ({ ...prev, bank_name: e.target.value }))}
              placeholder="Ej: Banco Nacional"
            />
          </div>
        </div>

        {/* Configuración de archivo */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <Label htmlFor="file_format">Formato de archivo</Label>
            <select
              id="file_format"
              className="w-full p-2 border rounded-md"
              value={formData.file_format}
              onChange={(e) => setFormData(prev => ({ ...prev, file_format: e.target.value }))}
            >
              <option value="csv">CSV</option>
              <option value="txt">TXT</option>
              <option value="excel">Excel</option>
            </select>
          </div>
          <div>
            <Label htmlFor="delimiter">Delimitador</Label>
            <Input
              id="delimiter"
              value={formData.delimiter}
              onChange={(e) => setFormData(prev => ({ ...prev, delimiter: e.target.value }))}
              placeholder=","
            />
          </div>
          <div>
            <Label htmlFor="encoding">Codificación</Label>
            <select
              id="encoding"
              className="w-full p-2 border rounded-md"
              value={formData.encoding}
              onChange={(e) => setFormData(prev => ({ ...prev, encoding: e.target.value }))}
            >
              <option value="utf-8">UTF-8</option>
              <option value="latin-1">Latin-1</option>
              <option value="cp1252">Windows-1252</option>
            </select>
          </div>
        </div>

        {/* Mapeo de campos */}
        <div>
          <Label className="text-base font-semibold">Mapeo de Campos</Label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
            {Object.entries(formData.field_mappings).map(([field, value]) => (
              <div key={field}>
                <Label htmlFor={`mapping_${field}`}>
                  {field === 'date' ? 'Fecha' :
                   field === 'description' ? 'Descripción' :
                   field === 'amount' ? 'Monto' :
                   field === 'reference' ? 'Referencia' :
                   field === 'balance' ? 'Saldo' : field}
                </Label>
                <Input
                  id={`mapping_${field}`}
                  value={value}
                  onChange={(e) => handleFieldMappingChange(field, e.target.value)}
                  placeholder="Nombre de la columna en el archivo"
                />
              </div>
            ))}
          </div>
        </div>

        {/* Configuración de formato */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <Label htmlFor="date_format">Formato de fecha</Label>
            <select
              id="date_format"
              className="w-full p-2 border rounded-md"
              value={formData.date_format}
              onChange={(e) => setFormData(prev => ({ ...prev, date_format: e.target.value }))}
            >
              <option value="DD/MM/YYYY">DD/MM/YYYY</option>
              <option value="MM/DD/YYYY">MM/DD/YYYY</option>
              <option value="YYYY-MM-DD">YYYY-MM-DD</option>
              <option value="DD-MM-YYYY">DD-MM-YYYY</option>
            </select>
          </div>
          <div>
            <Label htmlFor="amount_format">Formato de monto</Label>
            <select
              id="amount_format"
              className="w-full p-2 border rounded-md"
              value={formData.amount_format}
              onChange={(e) => setFormData(prev => ({ ...prev, amount_format: e.target.value }))}
            >
              <option value="decimal">Decimal (1234.56)</option>
              <option value="comma">Coma europea (1234,56)</option>
              <option value="accounting">Contable ((1234.56))</option>
            </select>
          </div>
          <div>
            <Label htmlFor="skip_rows">Filas a omitir</Label>
            <Input
              id="skip_rows"
              type="number"
              value={formData.skip_rows}
              onChange={(e) => setFormData(prev => ({ ...prev, skip_rows: parseInt(e.target.value) || 0 }))}
              min="0"
            />
          </div>
        </div>

        {/* Resultado de prueba */}
        {testResult && (
          <Alert variant={testResult.success ? 'success' : 'destructive'}>
            {testResult.success ? <CheckCircle className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
            <AlertDescription>
              {testResult.success 
                ? `Configuración válida. Se procesaron ${testResult.records_processed} registros.`
                : `Error en la configuración: ${testResult.error}`
              }
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Settings className="h-5 w-5" />
              <span>Configuraciones de Importación</span>
            </div>
            <Button onClick={handleCreateNew} size="sm">
              <Plus className="h-4 w-4 mr-2" />
              Nueva Configuración
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-600">
            Gestiona las configuraciones para importar archivos de diferentes bancos.
            Cada configuración define cómo interpretar los archivos de extractos bancarios.
          </p>
        </CardContent>
      </Card>

      {/* Lista de configuraciones */}
      {!isCreating && !isEditing && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {configs.map((config) => (
            <Card key={config.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg flex items-center justify-between">
                  <span>{config.name}</span>
                  <Badge variant="outline">{config.file_format.toUpperCase()}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <div className="text-sm text-gray-600">Banco: {config.bank_name}</div>
                  <div className="text-sm text-gray-600">
                    Formato: {config.date_format} | {config.amount_format}
                  </div>
                </div>
                
                <div className="flex justify-between items-center pt-2">
                  <div className="flex gap-2">
                    <Button onClick={() => handleEdit(config)} variant="outline" size="sm">
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button 
                      onClick={() => handleDelete(config.id)} 
                      variant="outline" 
                      size="sm"
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                  
                  <div className="text-xs text-gray-500">
                    {config.created_at && new Date(config.created_at).toLocaleDateString()}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
          
          {configs.length === 0 && !loading && (
            <div className="col-span-full">
              <Alert>
                <FileText className="h-4 w-4" />
                <AlertDescription>
                  No hay configuraciones creadas. Crea una nueva configuración para comenzar a importar archivos bancarios.
                </AlertDescription>
              </Alert>
            </div>
          )}
        </div>
      )}

      {/* Formulario de creación/edición */}
      {(isCreating || isEditing) && <ConfigurationForm />}
    </div>
  );
}