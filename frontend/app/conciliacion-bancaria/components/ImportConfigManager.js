'use client';

import { useState, useEffect } from 'react';
import { apiService } from '@/lib/apiService';
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

import DebugPanel from './DebugPanel';
import ImportConfigWizard from './ImportConfigWizard'; // [NEW] Wizard Component

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
      const response = await apiService.get('/conciliacion-bancaria/import-configs');
      setConfigs(response.data);
    } catch (error) {
      console.error('Error cargando configuraciones:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNew = () => {
    console.log(`🆕 [CREATE NEW] Iniciando creación de nueva configuración`);
    setIsCreating(true);
    setIsEditing(false);
    setSelectedConfig(null);

    const initialFormData = {
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
    };

    console.log(`🆕 [CREATE NEW] FormData inicial:`, initialFormData);
    setFormData(initialFormData);
  };

  const handleEdit = (config) => {
    setSelectedConfig(config);
    setIsEditing(true);
    setIsCreating(false);

    // [PARCHE] Normalizar field_mapping (API) -> field_mappings (Frontend)
    const normalizedData = { ...config };
    if (normalizedData.field_mapping && !normalizedData.field_mappings) {
      normalizedData.field_mappings = { ...normalizedData.field_mapping };
    }
    // Asegurar que exista
    if (!normalizedData.field_mappings) {
      normalizedData.field_mappings = {
        date: '', description: '', amount: '', reference: '', balance: ''
      };
    }

    // [PARCHE] Normalizar header_rows (API) -> skip_rows (Frontend)
    if (normalizedData.header_rows !== undefined) {
      normalizedData.skip_rows = normalizedData.header_rows;
      normalizedData.has_header = normalizedData.header_rows > 0;
    }

    // [PARCHE] Normalizar formato de archivo (TXT -> txt) para que coincida con el select
    if (normalizedData.file_format) {
      normalizedData.file_format = normalizedData.file_format.toLowerCase();
    }

    // [PARCHE] Convertir índices numéricos a Letras (0->A, 1->B) para mejor UX
    if (normalizedData.field_mappings) {
      const mapping = { ...normalizedData.field_mappings };
      Object.keys(mapping).forEach(key => {
        const val = mapping[key];
        if (typeof val === 'number') {
          // Convertir 0 -> A, 1 -> B, etc.
          mapping[key] = String.fromCharCode(65 + val);
        }
      });
      normalizedData.field_mappings = mapping;
    }

    setFormData(normalizedData);
  };

  const handleSave = async () => {
    console.log(`💾 [SAVE] Iniciando guardado...`);
    console.log(`💾 [SAVE] FormData a guardar:`, formData);

    // Validaciones básicas
    if (!formData.name?.trim()) {
      console.log(`❌ [SAVE] Error: Nombre vacío`);
      alert('El nombre de la configuración es obligatorio');
      return;
    }

    if (!formData.bank_name?.trim()) {
      // Si estamos editando y ya tiene un bank_id válido, permitimos continuar
      // aunque el nombre visual no esté cargado (para evitar bloqueo).
      // Si es creación, sí exigimos el nombre.
      if (isCreating) {
        console.log(`❌ [SAVE] Error: Nombre del banco vacío`);
        alert('El nombre del banco es obligatorio');
        return;
      }
      // Si es edición, logueamos warning pero seguimos
      console.warn(`⚠️ [SAVE] Nombre de banco vacío en edición. Se asume bank_id existente: ${formData.bank_id}`);
    }

    // [PARCHE] Validar campos del mapeo obligatorios (Safe Check)
    const mappings = formData.field_mappings || {};
    const hasValue = (val) => val !== undefined && val !== null && val !== '';

    if (!hasValue(mappings.date) || !hasValue(mappings.amount) || !hasValue(mappings.description)) {
      alert('Por favor, indica la columna para Fecha, Monto y Descripción (Ej: A, B, C). Son obligatorios.');
      return;
    }

    console.log(`💾 [SAVE] Validaciones pasadas, enviando a API...`);
    setLoading(true);

    try {
      const url = isCreating
        ? '/conciliacion-bancaria/import-configs'
        : `/conciliacion-bancaria/import-configs/${selectedConfig.id}`;

      const method = isCreating ? 'post' : 'put';

      console.log(`💾 [SAVE] URL: ${url}, Método: ${method}`);

      // [PARCHE MEJORADO] Transformar field_mappings a field_mapping y convertir letras a números
      const payload = { ...formData };

      // [CRITICO] Fix 422: Enviar bank_id = 0 para pasar validación Pydantic
      if (!payload.bank_id) {
        payload.bank_id = 0;
      }

      // [CRITICO] Fix 422: Validaciones de Schema (Uppercase y Mapeo)
      if (payload.file_format) {
        payload.file_format = payload.file_format.toUpperCase(); // Schema exige MAYÚSCULAS
      }
      if (payload.skip_rows !== undefined) {
        payload.header_rows = parseInt(payload.skip_rows) || 1; // Default a 1 si no hay nada
      }

      if (payload.field_mappings) {
        const mapping = { ...payload.field_mappings };

        // Convertir valores (A->0, B->1, "0"->0)
        Object.keys(mapping).forEach(key => {
          const val = mapping[key];

          // Si está vacío, borrar la clave para que no falle la validación de tipo (int)
          if (val === '' || val === null || val === undefined) {
            delete mapping[key];
            return;
          }

          // Si es número directo "0", "1"
          if (!isNaN(val) && val.toString().trim() !== '') {
            mapping[key] = parseInt(val, 10);
          }
          // Si es letra única A, B, C...
          else if (typeof val === 'string' && val.trim().length === 1 && val.trim().match(/[a-zA-Z]/)) {
            mapping[key] = val.trim().toUpperCase().charCodeAt(0) - 65;
          }
          // Caso borde: alguien escribe "Columna A" -> No lo soportamos aun, fallará validación de tipo int
        });

        payload.field_mapping = mapping;
        delete payload.field_mappings; // Eliminar la clave antigua
      }

      // Asegurarse de quitar bank_name si estorba (aunque backend lo usa para fallback)
      // No quitar bank_name, el backend lo usa.

      console.log(`💾 [SAVE] Payload procesado:`, JSON.stringify(payload, null, 2));

      const response = await apiService[method](url, payload);

      console.log(`✅ [SAVE] Guardado exitoso:`, response.data);

      await loadConfigurations();
      setIsCreating(false);
      setIsEditing(false);
      setSelectedConfig(null);
      alert('Configuración guardada exitosamente');

    } catch (error) {
      console.error('💥 [SAVE] Error:', error);
      const errorMessage = error.response?.data?.detail || 'Error desconocido al guardar';
      console.log(`❌ [SAVE] Error del servidor:`, errorMessage);
      alert(`Error al guardar: ${errorMessage}`);
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
      await apiService.delete(`/conciliacion-bancaria/import-configs/${configId}`);
      await loadConfigurations();
    } catch (error) {
      console.error('Error eliminando configuración:', error);
      alert('Error al eliminar la configuración');
    } finally {
      setLoading(false);
    }
  };

  const handleTestConfig = async () => {
    setLoading(true);
    try {
      // Nota: Si test requiere archivo, apiService necesita Content-Type multipart/form-data si enviamos FormData.
      // Pero aquí parece que enviamos JSON (config_data) según la ruta /import-configs/test (sin file)
      // Si es /test con file, sería diferente. Revisando routes.py:
      // /import-configs/test -> test_configuration_without_file (recibe config_data: dict)

      const response = await apiService.post('/conciliacion-bancaria/import-configs/test', formData);
      setTestResult(response.data);
    } catch (error) {
      console.error('Error probando configuración:', error);
      setTestResult({ success: false, error: 'Error de conexión o validación' });
    } finally {
      setLoading(false);
    }
  };

  const handleFieldMappingChange = (field, value) => {
    console.log(`🗺️ [FIELD MAPPING] Campo: ${field}, Valor: "${value}"`);
    console.log(`🗺️ [FIELD MAPPING] Mappings anteriores:`, formData.field_mappings);

    setFormData(prev => {
      const newState = {
        ...prev,
        field_mappings: {
          ...prev.field_mappings,
          [field]: value
        }
      };
      console.log(`🗺️ [FIELD MAPPING] Nuevos mappings:`, newState.field_mappings);
      return newState;
    });
  };

  const handleInputChange = (field, value) => {
    console.log(`🔍 [INPUT CHANGE] Campo: ${field}, Valor: "${value}", Tipo: ${typeof value}`);
    console.log(`🔍 [INPUT CHANGE] Estado anterior:`, formData[field]);

    setFormData(prev => {
      const newState = {
        ...prev,
        [field]: value
      };
      console.log(`🔍 [INPUT CHANGE] Nuevo estado para ${field}:`, newState[field]);
      console.log(`🔍 [INPUT CHANGE] Estado completo:`, newState);
      return newState;
    });
  };

  const ConfigurationForm = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>{isCreating ? 'Nueva Configuración' : 'Editar Configuración'}</span>
          <div className="flex gap-2">
            <Button onClick={handleTestConfig} variant="outline" size="sm" disabled={loading}>
              <TestTube className="h-4 w-4 mr-2" />
              Probar
            </Button>
            <Button onClick={handleSave} size="sm" disabled={loading}>
              <Save className="h-4 w-4 mr-2" />
              {loading ? 'Guardando...' : 'Guardar'}
            </Button>
            <Button
              onClick={() => {
                setIsCreating(false);
                setIsEditing(false);
                setSelectedConfig(null);
              }}
              variant="outline"
              size="sm"
            >
              Cancelar
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
              onChange={(e) => handleInputChange('name', e.target.value)}
              placeholder="Ej: Banco Nacional CSV"
              className="conciliacion-input"
            />
          </div>
          <div>
            <Label htmlFor="bank_name">Nombre del banco</Label>
            <Input
              id="bank_name"
              value={formData.bank_name || 'Asignado en creación'}
              disabled={true}
              title="El banco no se puede modificar una vez creada la configuración."
              className="conciliacion-input bg-gray-100 text-gray-500 cursor-not-allowed"
            />
          </div>
        </div>

        {/* Configuración de archivo */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <Label htmlFor="file_format">Formato de archivo</Label>
            <div className="conciliacion-select">
              <select
                id="file_format"
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white conciliacion-input"
                value={formData.file_format}
                onChange={(e) => handleInputChange('file_format', e.target.value)}
              >
                <option value="csv">CSV</option>
                <option value="txt">TXT</option>
                <option value="excel">Excel</option>
                <option value="pdf">PDF</option>
                <option value="texto">Texto</option>
              </select>
            </div>
          </div>
          <div>
            <Label htmlFor="delimiter">Delimitador</Label>
            <Input
              id="delimiter"
              value={formData.delimiter}
              onChange={(e) => handleInputChange('delimiter', e.target.value)}
              placeholder=","
            />
          </div>
          <div>
            <Label htmlFor="encoding">Codificación</Label>
            <select
              id="encoding"
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
              value={formData.encoding}
              onChange={(e) => handleInputChange('encoding', e.target.value)}
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
            {Object.entries(formData.field_mappings || {}).map(([field, value]) => (
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
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
              value={formData.date_format}
              onChange={(e) => handleInputChange('date_format', e.target.value)}
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
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
              value={formData.amount_format}
              onChange={(e) => handleInputChange('amount_format', e.target.value)}
            >
              <option value="decimal">Decimal (1234.56)</option>
              <option value="comma">Coma europea (1234,56)</option>
              <option value="accounting">Contable ((1234.56))</option>
            </select>
          </div>
          <div>
            <Label htmlFor="skip_rows">Filas a omitir (Encabezados)</Label>
            <div className="flex items-center gap-2 mt-2">
              <input
                type="checkbox"
                id="has_header"
                checked={formData.skip_rows > 0}
                onChange={(e) => {
                  const hasHeader = e.target.checked;
                  handleInputChange('skip_rows', hasHeader ? 1 : 0);
                }}
                className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
              />
              <Label htmlFor="has_header" className="font-normal text-gray-700">Tiene encabezados?</Label>
            </div>
            <Input
              id="skip_rows"
              type="number"
              value={formData.skip_rows}
              onChange={(e) => handleInputChange('skip_rows', parseInt(e.target.value) || 0)}
              min="0"
              className="mt-2"
              placeholder="0"
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
      {/* CREACIÓN: Wizard (Reemplazo total del formulario antiguo) */}
      {isCreating && (
        <ImportConfigWizard
          onCancel={() => setIsCreating(false)}
          onSaveSuccess={() => {
            setIsCreating(false);
            loadConfigurations();
            alert("¡Configuración creada exitosamente!");
          }}
        />
      )}

      {/* EDICIÓN: Formulario Legacy (Solo para editar existentes) */}
      {isEditing && ConfigurationForm()}

      {/* Panel de Debug */}
      <DebugPanel formData={formData} />
    </div>
  );
}