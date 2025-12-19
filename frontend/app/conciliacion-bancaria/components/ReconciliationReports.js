'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { 
  BarChart3, 
  Download,
  FileText,
  Eye,
  Printer,
  AlertCircle,
  CheckCircle,
  Clock,
  TrendingUp,
  DollarSign,
  Loader2
} from 'lucide-react';

export default function ReconciliationReports({ selectedBankAccount, onBankAccountChange }) {
  const [reportType, setReportType] = useState('summary');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [loading, setLoading] = useState(false);
  const [reportData, setReportData] = useState(null);
  const [bankAccounts, setBankAccounts] = useState([]);

  // Cargar cuentas bancarias disponibles
  useEffect(() => {
    loadBankAccounts();
  }, []);

  // Establecer fechas por defecto (último mes)
  useEffect(() => {
    const today = new Date();
    const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
    const endOfLastMonth = new Date(today.getFullYear(), today.getMonth(), 0);
    
    setDateFrom(lastMonth.toISOString().split('T')[0]);
    setDateTo(endOfLastMonth.toISOString().split('T')[0]);
  }, []);

  const loadBankAccounts = async () => {
    try {
      const response = await fetch('/api/plan-cuentas?tipo=banco');
      if (response.ok) {
        const data = await response.json();
        setBankAccounts(data);
      }
    } catch (error) {
      console.error('Error cargando cuentas bancarias:', error);
    }
  };

  const generateReport = async () => {
    if (!selectedBankAccount) {
      alert('Selecciona una cuenta bancaria');
      return;
    }

    setLoading(true);
    try {
      const params = new URLSearchParams({
        bank_account_id: selectedBankAccount.id,
        report_type: reportType,
        date_from: dateFrom,
        date_to: dateTo
      });

      const response = await fetch(`/api/conciliacion-bancaria/reports/generate?${params}`);
      
      if (response.ok) {
        const data = await response.json();
        setReportData(data);
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error generando reporte:', error);
      alert('Error generando reporte');
    } finally {
      setLoading(false);
    }
  };

  const exportReport = async (format) => {
    if (!reportData) {
      alert('Genera un reporte primero');
      return;
    }

    try {
      const params = new URLSearchParams({
        bank_account_id: selectedBankAccount.id,
        report_type: reportType,
        date_from: dateFrom,
        date_to: dateTo,
        format: format
      });

      const response = await fetch(`/api/conciliacion-bancaria/reports/export?${params}`);
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `conciliacion_${reportType}_${dateFrom}_${dateTo}.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
      } else {
        alert('Error exportando reporte');
      }
    } catch (error) {
      console.error('Error exportando:', error);
      alert('Error exportando reporte');
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

  const SummaryReport = ({ data }) => (
    <div className="space-y-6">
      {/* Estadísticas generales */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <div>
                <div className="text-2xl font-bold text-green-600">
                  {data.summary?.reconciled_movements || 0}
                </div>
                <div className="text-sm text-gray-600">Conciliados</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Clock className="h-5 w-5 text-yellow-500" />
              <div>
                <div className="text-2xl font-bold text-yellow-600">
                  {data.summary?.pending_movements || 0}
                </div>
                <div className="text-sm text-gray-600">Pendientes</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <TrendingUp className="h-5 w-5 text-blue-500" />
              <div>
                <div className="text-2xl font-bold text-blue-600">
                  {data.summary?.reconciliation_rate || 0}%
                </div>
                <div className="text-sm text-gray-600">Tasa conciliación</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <DollarSign className="h-5 w-5 text-purple-500" />
              <div>
                <div className="text-2xl font-bold text-purple-600">
                  {formatCurrency(data.summary?.total_amount || 0)}
                </div>
                <div className="text-sm text-gray-600">Monto total</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Resumen por tipo de conciliación */}
      <Card>
        <CardHeader>
          <CardTitle>Resumen por Tipo de Conciliación</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {data.by_type?.map((item, index) => (
              <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Badge variant={item.type === 'AUTO' ? 'success' : 'secondary'}>
                    {item.type === 'AUTO' ? 'Automática' : 'Manual'}
                  </Badge>
                  <span className="font-medium">{item.count} movimientos</span>
                </div>
                <div className="text-right">
                  <div className="font-semibold">{formatCurrency(item.amount)}</div>
                  <div className="text-sm text-gray-600">{item.percentage}%</div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Movimientos pendientes */}
      {data.pending_movements && data.pending_movements.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Movimientos Pendientes de Conciliación</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {data.pending_movements.slice(0, 10).map((movement, index) => (
                <div key={index} className="flex justify-between items-center p-2 border-b">
                  <div>
                    <div className="font-medium">{movement.description}</div>
                    <div className="text-sm text-gray-600">
                      {formatDate(movement.transaction_date)} - {movement.reference}
                    </div>
                  </div>
                  <div className={`font-semibold ${movement.amount >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatCurrency(Math.abs(movement.amount))}
                  </div>
                </div>
              ))}
              {data.pending_movements.length > 10 && (
                <div className="text-center text-gray-600 text-sm pt-2">
                  ... y {data.pending_movements.length - 10} movimientos más
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const DetailedReport = ({ data }) => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Reporte Detallado de Conciliaciones</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse border border-gray-300">
              <thead>
                <tr className="bg-gray-50">
                  <th className="border border-gray-300 p-2 text-left">Fecha</th>
                  <th className="border border-gray-300 p-2 text-left">Descripción</th>
                  <th className="border border-gray-300 p-2 text-left">Referencia</th>
                  <th className="border border-gray-300 p-2 text-right">Monto</th>
                  <th className="border border-gray-300 p-2 text-center">Estado</th>
                  <th className="border border-gray-300 p-2 text-center">Tipo</th>
                </tr>
              </thead>
              <tbody>
                {data.detailed_movements?.map((movement, index) => (
                  <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="border border-gray-300 p-2">
                      {formatDate(movement.transaction_date)}
                    </td>
                    <td className="border border-gray-300 p-2">{movement.description}</td>
                    <td className="border border-gray-300 p-2">{movement.reference || '-'}</td>
                    <td className={`border border-gray-300 p-2 text-right font-medium ${
                      movement.amount >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {formatCurrency(Math.abs(movement.amount))}
                    </td>
                    <td className="border border-gray-300 p-2 text-center">
                      <Badge variant={movement.status === 'MATCHED' ? 'success' : 'warning'}>
                        {movement.status === 'MATCHED' ? 'Conciliado' : 'Pendiente'}
                      </Badge>
                    </td>
                    <td className="border border-gray-300 p-2 text-center">
                      {movement.reconciliation_type ? (
                        <Badge variant={movement.reconciliation_type === 'AUTO' ? 'default' : 'secondary'}>
                          {movement.reconciliation_type === 'AUTO' ? 'Auto' : 'Manual'}
                        </Badge>
                      ) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header y controles */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <BarChart3 className="h-5 w-5" />
            <span>Reportes de Conciliación</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Selección de cuenta bancaria */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
              >
                <option value="">Seleccionar cuenta...</option>
                {bankAccounts.map(account => (
                  <option key={account.id} value={account.id}>
                    {account.codigo} - {account.nombre}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <Label htmlFor="report_type">Tipo de Reporte</Label>
              <select
                id="report_type"
                className="w-full p-2 border border-gray-300 rounded-md"
                value={reportType}
                onChange={(e) => setReportType(e.target.value)}
              >
                <option value="summary">Resumen Ejecutivo</option>
                <option value="detailed">Reporte Detallado</option>
                <option value="adjustments">Ajustes Automáticos</option>
                <option value="unmatched">Movimientos Pendientes</option>
              </select>
            </div>
          </div>

          {/* Filtros de fecha */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="date_from">Fecha Desde</Label>
              <Input
                id="date_from"
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="date_to">Fecha Hasta</Label>
              <Input
                id="date_to"
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
              />
            </div>
          </div>

          {/* Botones de acción */}
          <div className="flex flex-wrap gap-2">
            <Button onClick={generateReport} disabled={loading || !selectedBankAccount}>
              {loading && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
              <Eye className="h-4 w-4 mr-2" />
              Generar Reporte
            </Button>

            {reportData && (
              <>
                <Button onClick={() => exportReport('pdf')} variant="outline">
                  <FileText className="h-4 w-4 mr-2" />
                  Exportar PDF
                </Button>
                <Button onClick={() => exportReport('excel')} variant="outline">
                  <Download className="h-4 w-4 mr-2" />
                  Exportar Excel
                </Button>
                <Button onClick={() => window.print()} variant="outline">
                  <Printer className="h-4 w-4 mr-2" />
                  Imprimir
                </Button>
              </>
            )}
          </div>

          {!selectedBankAccount && (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Selecciona una cuenta bancaria para generar reportes.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Contenido del reporte */}
      {reportData && (
        <div className="print:shadow-none">
          {/* Header del reporte para impresión */}
          <div className="hidden print:block mb-6">
            <h1 className="text-2xl font-bold text-center">Reporte de Conciliación Bancaria</h1>
            <div className="text-center text-gray-600 mt-2">
              <div>Cuenta: {selectedBankAccount?.codigo} - {selectedBankAccount?.nombre}</div>
              <div>Período: {formatDate(dateFrom)} - {formatDate(dateTo)}</div>
              <div>Generado: {new Date().toLocaleString('es-CO')}</div>
            </div>
          </div>

          {reportType === 'summary' && <SummaryReport data={reportData} />}
          {reportType === 'detailed' && <DetailedReport data={reportData} />}
          
          {reportType === 'adjustments' && (
            <Card>
              <CardHeader>
                <CardTitle>Ajustes Automáticos Generados</CardTitle>
              </CardHeader>
              <CardContent>
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    Reporte de ajustes automáticos en desarrollo.
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
          )}

          {reportType === 'unmatched' && (
            <Card>
              <CardHeader>
                <CardTitle>Movimientos Pendientes de Conciliación</CardTitle>
              </CardHeader>
              <CardContent>
                {reportData.pending_movements?.length > 0 ? (
                  <div className="space-y-2">
                    {reportData.pending_movements.map((movement, index) => (
                      <div key={index} className="flex justify-between items-center p-3 border rounded-lg">
                        <div>
                          <div className="font-medium">{movement.description}</div>
                          <div className="text-sm text-gray-600">
                            {formatDate(movement.transaction_date)} - {movement.reference || 'Sin referencia'}
                          </div>
                        </div>
                        <div className={`font-semibold ${movement.amount >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {formatCurrency(Math.abs(movement.amount))}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <Alert>
                    <CheckCircle className="h-4 w-4" />
                    <AlertDescription>
                      ¡Excelente! No hay movimientos pendientes de conciliación en el período seleccionado.
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}