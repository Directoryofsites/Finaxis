'use client';

import { useState, useEffect, useRef } from 'react';
import { apiService } from '@/lib/apiService'; // Using alias for consistency
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import {
  Upload,
  FileText,
  AlertCircle,
  CheckCircle,
  Loader2,
  Settings,
  Eye,
  Download,
  X,
  Plus
} from 'lucide-react';

export default function FileImportInterface({ selectedBankAccount, onBankAccountChange, onImportComplete }) {
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1); // 1: Selección, 2: Archivo, 3: Validación, 4: Importación
  const [configurations, setConfigurations] = useState([]);
  const [selectedConfig, setSelectedConfig] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [validationResult, setValidationResult] = useState(null);
  const [importResult, setImportResult] = useState(null);
  const [bankAccounts, setBankAccounts] = useState([]);
  const fileInputRef = useRef(null);

  // Cargar configuraciones y cuentas bancarias
  useEffect(() => {
    loadConfigurations();
    loadBankAccounts();
  }, []);

  const loadConfigurations = async () => {
    try {
      const response = await apiService.get('/conciliacion-bancaria/import-configs');
      setConfigurations(response.data);
    } catch (error) {
      console.error('Error cargando configuraciones:', error);
    }
  };

  const loadBankAccounts = async () => {
    try {
      // Usamos el endpoint específico que filtra bancos reales (1110/1120)
      const response = await apiService.get('/conciliacion-bancaria/bank-accounts');
      setBankAccounts(response.data);
    } catch (error) {
      console.error('Error cargando cuentas bancarias:', error);
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      setStep(3);
      validateFile(file);
    }
  };

  const validateFile = async (file) => {
    if (!selectedConfig) return;

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      // axios maneja el content-type multipart automáticamente cuando ve FormData
      // PERO si apiService tiene default 'application/json', hay que anularlo
      const response = await apiService.post(
        `/conciliacion-bancaria/import-configs/${selectedConfig.id}/validate`,
        formData,
        {
          headers: {
            'Content-Type': undefined
          }
        }
      );

      setValidationResult(response.data);
    } catch (error) {
      console.error('Error validando archivo:', error);
      let errorDetail = error.response?.data?.detail || 'Error de conexión al validar archivo';

      // [FIX] Handle Pydantic array of errors
      if (Array.isArray(errorDetail)) {
        errorDetail = errorDetail.map(e => typeof e === 'object' ? (e.msg || JSON.stringify(e)) : e);
      } else if (typeof errorDetail === 'object') {
        errorDetail = [JSON.stringify(errorDetail)];
      } else {
        errorDetail = [errorDetail];
      }

      setValidationResult({
        is_valid: false,
        errors: errorDetail
      });
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async () => {
    if (!selectedFile || !selectedConfig || !selectedBankAccount) return;

    setLoading(true);
    setStep(4);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('config_id', selectedConfig.id);
      formData.append('bank_account_id', selectedBankAccount.id);

      const response = await apiService.post('/conciliacion-bancaria/import', formData, {
        headers: {
          'Content-Type': undefined
        }
      });

      setImportResult(response.data);

      // Notificar al componente padre
      if (onImportComplete) {
        onImportComplete(response.data);
      }
    } catch (error) {
      console.error('Error importando archivo:', error);
      const errorDetail = error.response?.data?.detail || 'Error importando archivo';
      setImportResult({
        success: false,
        error: errorDetail
      });
    } finally {
      setLoading(false);
    }
  };

  const resetImport = () => {
    setStep(1);
    setSelectedFile(null);
    setValidationResult(null);
    setImportResult(null);
    setSelectedConfig(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-6">
      {/* Paso 1: Selección de configuración y cuenta */}
      {step >= 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Settings className="h-5 w-5" />
              <span>Configuración de Importación</span>
              {step > 1 && <CheckCircle className="h-5 w-5 text-green-500" />}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Selección de cuenta bancaria */}
            <div>
              <Label htmlFor="bank_account">Cuenta Bancaria</Label>
              <select
                id="bank_account"
                className="w-full p-2 border border-gray-300 rounded-md"
                value={selectedBankAccount?.id || ''}
                onChange={(e) => {
                  const account = bankAccounts.find(acc => acc.id == e.target.value);
                  onBankAccountChange?.(account);
                }}
                disabled={step > 2}
              >
                <option value="">Seleccionar cuenta bancaria...</option>
                {bankAccounts.map(account => (
                  <option key={account.id} value={account.id}>
                    {account.codigo} - {account.nombre}
                  </option>
                ))}
              </select>
            </div>

            {/* Selección de configuración */}
            <div>
              <Label htmlFor="config">Configuración de Importación</Label>
              <select
                id="config"
                className="w-full p-2 border border-gray-300 rounded-md"
                value={selectedConfig?.id || ''}
                onChange={(e) => {
                  const config = configurations.find(c => c.id == e.target.value);
                  setSelectedConfig(config);
                }}
                disabled={step > 2}
              >
                <option value="">Seleccionar configuración...</option>
                {configurations.map(config => (
                  <option key={config.id} value={config.id}>
                    {config.name} - {config.file_format}
                  </option>
                ))}
              </select>
            </div>

            {selectedConfig && (
              <div className="p-3 bg-blue-50 rounded-lg">
                <div className="text-sm">
                  <div><strong>Formato:</strong> {selectedConfig.file_format}</div>
                  <div><strong>Delimitador:</strong> {selectedConfig.delimiter}</div>
                  <div><strong>Formato de fecha:</strong> {selectedConfig.date_format}</div>
                </div>
              </div>
            )}

            {step === 1 && selectedConfig && selectedBankAccount && (
              <Button onClick={() => setStep(2)} className="w-full">
                <Upload className="h-4 w-4 mr-2" />
                Continuar con Archivo
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* Paso 2: Selección de archivo */}
      {step >= 2 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <FileText className="h-5 w-5" />
              <span>Selección de Archivo</span>
              {step > 2 && <CheckCircle className="h-5 w-5 text-green-500" />}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {step === 2 && (
              <div>
                <Label htmlFor="file">Archivo del Banco ({selectedConfig?.file_format})</Label>
                <Input
                  ref={fileInputRef}
                  id="file"
                  type="file"
                  accept={`.${selectedConfig?.file_format?.toLowerCase()}`}
                  onChange={handleFileSelect}
                  className="mt-1"
                />
                <div className="text-sm text-gray-600 mt-1">
                  Formatos soportados: {selectedConfig?.file_format}
                </div>
              </div>
            )}

            {selectedFile && (
              <div className="p-3 bg-green-50 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">{selectedFile.name}</div>
                    <div className="text-sm text-gray-600">
                      {formatFileSize(selectedFile.size)} - {selectedFile.type || 'Archivo de texto'}
                    </div>
                  </div>
                  {step === 2 && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setSelectedFile(null);
                        if (fileInputRef.current) {
                          fileInputRef.current.value = '';
                        }
                      }}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Paso 3: Validación */}
      {step >= 3 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Eye className="h-5 w-5" />
              <span>Validación del Archivo</span>
              {loading && step === 3 && <Loader2 className="h-4 w-4 animate-spin" />}
              {validationResult?.is_valid && <CheckCircle className="h-5 w-5 text-green-500" />}
              {validationResult && !validationResult.is_valid && <AlertCircle className="h-5 w-5 text-red-500" />}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {loading && step === 3 && (
              <Alert>
                <Loader2 className="h-4 w-4 animate-spin" />
                <AlertDescription>
                  Validando archivo, por favor espere...
                </AlertDescription>
              </Alert>
            )}

            {validationResult && (
              <div>
                {validationResult.is_valid ? (
                  <Alert className="border-green-200 bg-green-50">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <AlertDescription className="text-green-800">
                      ¡Archivo válido! Se encontraron {validationResult.total_rows || 0} filas de datos.
                    </AlertDescription>
                  </Alert>
                ) : (
                  <Alert className="border-red-200 bg-red-50">
                    <AlertCircle className="h-4 w-4 text-red-600" />
                    <AlertDescription className="text-red-800">
                      <div>Errores encontrados en el archivo:</div>
                      <ul className="list-disc list-inside mt-2">
                        {validationResult.errors?.map((error, index) => (
                          <li key={index} className="text-sm">{error}</li>
                        ))}
                      </ul>
                    </AlertDescription>
                  </Alert>
                )}

                {validationResult.warnings && validationResult.warnings.length > 0 && (
                  <Alert className="border-yellow-200 bg-yellow-50">
                    <AlertCircle className="h-4 w-4 text-yellow-600" />
                    <AlertDescription className="text-yellow-800">
                      <div>Advertencias:</div>
                      <ul className="list-disc list-inside mt-2">
                        {validationResult.warnings.map((warning, index) => (
                          <li key={index} className="text-sm">{warning}</li>
                        ))}
                      </ul>
                    </AlertDescription>
                  </Alert>
                )}

                {validationResult.sample_data && validationResult.sample_data.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Vista previa de datos:</h4>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm border border-gray-300">
                        <thead>
                          <tr className="bg-gray-50">
                            <th className="border border-gray-300 p-2">Fecha</th>
                            <th className="border border-gray-300 p-2">Descripción</th>
                            <th className="border border-gray-300 p-2">Monto</th>
                            <th className="border border-gray-300 p-2">Referencia</th>
                          </tr>
                        </thead>
                        <tbody>
                          {validationResult.sample_data.slice(0, 5).map((row, index) => (
                            <tr key={index}>
                              <td className="border border-gray-300 p-2">{row.date || '-'}</td>
                              <td className="border border-gray-300 p-2">{row.description || '-'}</td>
                              <td className="border border-gray-300 p-2">{row.amount || '-'}</td>
                              <td className="border border-gray-300 p-2">{row.reference || '-'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}

            {validationResult?.is_valid && step === 3 && (
              <div className="flex space-x-2">
                <Button onClick={handleImport} className="flex-1">
                  <Download className="h-4 w-4 mr-2" />
                  Importar Movimientos
                </Button>
                <Button variant="outline" onClick={resetImport}>
                  Cancelar
                </Button>
              </div>
            )}

            {validationResult && !validationResult.is_valid && (
              <div className="flex space-x-2">
                <Button variant="outline" onClick={() => setStep(2)}>
                  Seleccionar Otro Archivo
                </Button>
                <Button variant="outline" onClick={resetImport}>
                  Reiniciar
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Paso 4: Resultado de importación */}
      {step >= 4 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Download className="h-5 w-5" />
              <span>Resultado de Importación</span>
              {loading && step === 4 && <Loader2 className="h-4 w-4 animate-spin" />}
              {importResult?.success !== false && !loading && <CheckCircle className="h-5 w-5 text-green-500" />}
              {importResult?.success === false && <AlertCircle className="h-5 w-5 text-red-500" />}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {loading && step === 4 && (
              <Alert>
                <Loader2 className="h-4 w-4 animate-spin" />
                <AlertDescription>
                  Importando movimientos, por favor espere...
                </AlertDescription>
              </Alert>
            )}

            {importResult && (
              <div>
                {importResult.success !== false ? (
                  <div>
                    <Alert className="border-green-200 bg-green-50">
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <AlertDescription className="text-green-800">
                        ¡Importación completada exitosamente!
                      </AlertDescription>
                    </Alert>

                    <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                      <h4 className="font-medium mb-2">Resumen de importación:</h4>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="font-medium">Total de movimientos:</span> {importResult.total_movements || 0}
                        </div>
                        <div>
                          <span className="font-medium">Importados exitosamente:</span> {importResult.successful_imports || 0}
                        </div>
                        <div>
                          <span className="font-medium">Estado:</span>
                          <Badge variant={importResult.status === 'COMPLETED' ? 'success' : 'warning'} className="ml-2">
                            {importResult.status}
                          </Badge>
                        </div>
                        <div>
                          <span className="font-medium">Sesión ID:</span> {importResult.id}
                        </div>
                      </div>
                    </div>

                    {importResult.duplicate_report && importResult.duplicate_report.action_required && (
                      <Alert className="border-yellow-200 bg-yellow-50">
                        <AlertCircle className="h-4 w-4 text-yellow-600" />
                        <AlertDescription className="text-yellow-800">
                          Se encontraron {importResult.duplicate_report.total_duplicates} posibles duplicados.
                          Revise la importación antes de continuar.
                        </AlertDescription>
                      </Alert>
                    )}
                  </div>
                ) : (
                  <Alert className="border-red-200 bg-red-50">
                    <AlertCircle className="h-4 w-4 text-red-600" />
                    <AlertDescription className="text-red-800">
                      Error en la importación: {importResult.error}
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            )}

            {importResult && (
              <div className="flex space-x-2">
                <Button onClick={resetImport} className="flex-1">
                  <Plus className="h-4 w-4 mr-2" />
                  Nueva Importación
                </Button>
                {importResult.success !== false && (
                  <Button variant="outline" onClick={() => window.location.reload()}>
                    Ver Movimientos
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Información de ayuda */}
      {step === 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-blue-500" />
              <span>¿Cómo funciona la importación?</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm text-gray-600">
              <p>1. <strong>Selecciona la cuenta bancaria</strong> donde se registrarán los movimientos</p>
              <p>2. <strong>Elige la configuración</strong> que corresponde al formato de tu banco</p>
              <p>3. <strong>Sube el archivo</strong> del extracto bancario (TXT, CSV, Excel)</p>
              <p>4. <strong>Valida los datos</strong> antes de importar</p>
              <p>5. <strong>Importa los movimientos</strong> para comenzar la conciliación</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}