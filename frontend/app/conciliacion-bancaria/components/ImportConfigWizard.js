'use client';

import { useState, useEffect } from 'react';
import { apiService } from '@/lib/apiService';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import {
    ArrowRight,
    ArrowLeft,
    Save,
    Building2,
    FileSpreadsheet,
    TableProperties,
    CheckCircle,
    AlertCircle
} from 'lucide-react';

export default function ImportConfigWizard({ onCancel, onSaveSuccess }) {
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);
    const [banks, setBanks] = useState([]);
    const [error, setError] = useState(null);

    // Estado del formulario
    const [formData, setFormData] = useState({
        name: '',
        bank_id: '',
        file_format: 'CSV',
        delimiter: ',',
        encoding: 'utf-8',
        date_format: 'YYYY-MM-DD',
        amount_format: 'decimal',
        header_rows: 1,
        field_mapping: {
            date: '',
            description: '',
            amount: '',
            reference: '',
            balance: ''
        }
    });

    // Cargar bancos al iniciar
    useEffect(() => {
        loadBanks();
    }, []);

    const loadBanks = async () => {
        try {
            // Usamos el endpoint real que creamos anteriormente
            const response = await apiService.get('/conciliacion-bancaria/bank-accounts');
            setBanks(response.data);
        } catch (err) {
            console.error("Error cargando bancos:", err);
            setError("No se pudieron cargar los bancos. Verifica tu conexión.");
        }
    };

    const handleInputChange = (field, value) => {
        setFormData(prev => ({
            ...prev,
            [field]: value
        }));
        setError(null);
    };

    const handleMappingChange = (field, value) => {
        setFormData(prev => ({
            ...prev,
            field_mapping: {
                ...prev.field_mapping,
                [field]: value.toUpperCase() // Forzamos mayúscula visualmente
            }
        }));
    };

    // Convertir letra A->0, B->1
    const letterToIndex = (letter) => {
        if (!letter) return null;
        if (!isNaN(letter)) return parseInt(letter); // Si ya es número
        const clean = letter.trim().toUpperCase();
        if (clean.length === 1 && clean.match(/[A-Z]/)) {
            return clean.charCodeAt(0) - 65;
        }
        return null; // Inválido
    };

    const validateStep1 = () => {
        if (!formData.name.trim()) return "El nombre de la configuración es obligatorio.";
        if (!formData.bank_id) return "Debes seleccionar un banco.";
        return null;
    };

    const validateStep2 = () => {
        // Validaciones de formato si fueran necesarias (por ahora son selects seguros)
        return null;
    };

    const validateStep3 = () => {
        const { date, description, amount } = formData.field_mapping;
        if (!date || !description || !amount) {
            return "Fecha, Descripción y Monto son columnas obligatorias.";
        }
        return null;
    };

    const handleNext = () => {
        let err = null;
        if (step === 1) err = validateStep1();
        if (step === 2) err = validateStep2();

        if (err) {
            setError(err);
        } else {
            setError(null);
            setStep(step + 1);
        }
    };

    const handleBack = () => {
        setError(null);
        setStep(step - 1);
    };

    const handleSave = async () => {
        const err = validateStep3();
        if (err) {
            setError(err);
            return;
        }

        setLoading(true);
        try {
            // Construir payload limpio
            const payload = {
                name: formData.name,
                bank_id: parseInt(formData.bank_id), // Asegurar int
                file_format: formData.file_format, // Ya es mayúscula por default
                delimiter: formData.delimiter,
                encoding: formData.encoding,
                date_format: formData.date_format,
                header_rows: parseInt(formData.header_rows) || 0,
                amount_format: formData.amount_format,
                field_mapping: {}
            };

            // Procesar mapping: convertir letras a números y limpiar vacíos
            Object.entries(formData.field_mapping).forEach(([key, val]) => {
                const index = letterToIndex(val);
                if (index !== null) {
                    payload.field_mapping[key] = index;
                }
            });

            console.log("💾 Enviando payload Wizard:", payload);

            await apiService.post('/conciliacion-bancaria/import-configs', payload);

            if (onSaveSuccess) onSaveSuccess();

        } catch (err) {
            console.error("Error guardando:", err);
            setError(err.response?.data?.detail || "Error al guardar la configuración.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <Card className="w-full max-w-4xl mx-auto shadow-lg">
            <CardHeader className="border-b bg-gray-50">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-xl text-blue-800 flex items-center gap-2">
                        <Building2 className="w-6 h-6" />
                        Asistente de Configuración
                    </CardTitle>
                    <div className="flex gap-2">
                        {[1, 2, 3].map(s => (
                            <div key={s} className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold 
                        ${step === s ? 'bg-blue-600 text-white' :
                                    step > s ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-500'}`}>
                                {step > s ? <CheckCircle className="w-5 h-5" /> : s}
                            </div>
                        ))}
                    </div>
                </div>
            </CardHeader>

            <CardContent className="p-6 min-h-[400px]">
                {error && (
                    <Alert variant="destructive" className="mb-6 animate-pulse">
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                )}

                {/* STEP 1: DATOS BÁSICOS */}
                {step === 1 && (
                    <div className="space-y-6 animate-in fade-in slide-in-from-right-4">
                        <div className="grid gap-4">
                            <Label className="text-lg">1. ¿Cómo llamaremos a esta configuración?</Label>
                            <Input
                                value={formData.name}
                                onChange={e => handleInputChange('name', e.target.value)}
                                placeholder="Ej: Bancolombia Cuenta Ahorros"
                                className="text-lg p-6 bg-blue-50/30"
                                autoFocus
                            />
                        </div>

                        <div className="grid gap-4">
                            <Label className="text-lg">2. ¿A qué banco pertenece?</Label>
                            <select
                                className="w-full p-3 border rounded-lg bg-white shadow-sm focus:ring-2 focus:ring-blue-500"
                                value={formData.bank_id}
                                onChange={e => handleInputChange('bank_id', e.target.value)}
                            >
                                <option value="">-- Selecciona un banco --</option>
                                {banks.map(bank => (
                                    <option key={bank.id} value={bank.id}>
                                        {bank.codigo} - {bank.nombre}
                                    </option>
                                ))}
                            </select>
                            <p className="text-sm text-gray-500">
                                * Mostrando cuentas contables 1110/1120.
                            </p>
                        </div>

                        <div className="grid gap-4">
                            <Label className="text-lg">3. ¿Qué tipo de archivo te entrega el banco?</Label>
                            <div className="grid grid-cols-3 gap-4">
                                {['CSV', 'TXT', 'EXCEL'].map(fmt => (
                                    <div
                                        key={fmt}
                                        onClick={() => handleInputChange('file_format', fmt)}
                                        className={`cursor-pointer p-4 border rounded-xl flex flex-col items-center justify-center gap-2 transition-all
                                    ${formData.file_format === fmt
                                                ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                                                : 'border-gray-200 hover:border-blue-300'}`}
                                    >
                                        <FileSpreadsheet className={`w-8 h-8 ${formData.file_format === fmt ? 'text-blue-600' : 'text-gray-400'}`} />
                                        <span className="font-bold">{fmt}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {/* STEP 2: FORMATO */}
                {step === 2 && (
                    <div className="space-y-6 animate-in fade-in slide-in-from-right-4">
                        <div className="bg-blue-50 p-4 rounded-lg flex items-center gap-3">
                            <TableProperties className="text-blue-600" />
                            <div>
                                <h3 className="font-bold text-blue-900">Detalles del Archivo</h3>
                                <p className="text-sm text-blue-700">Asegúrate de que coincida con tu extracto</p>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-6">
                            <div>
                                <Label>Delimitador (para CSV/TXT)</Label>
                                <select
                                    className="w-full p-3 mt-2 border rounded-md"
                                    value={formData.delimiter}
                                    onChange={e => handleInputChange('delimiter', e.target.value)}
                                >
                                    <option value=",">Coma (,)</option>
                                    <option value=";">Punto y coma (;)</option>
                                    <option value="|">Barra vertical (|)</option>
                                    <option value="\t">Tabulación</option>
                                </select>
                            </div>
                            <div>
                                <Label>Filas de encabezado</Label>
                                <select
                                    className="w-full p-3 mt-2 border rounded-md"
                                    value={formData.header_rows}
                                    onChange={e => handleInputChange('header_rows', e.target.value)}
                                >
                                    <option value="0">Sin encabezado</option>
                                    <option value="1">1 Fila (Lo normal)</option>
                                    <option value="2">2 Filas</option>
                                </select>
                            </div>
                            <div>
                                <Label>Formato de Fecha</Label>
                                <select
                                    className="w-full p-3 mt-2 border rounded-md"
                                    value={formData.date_format}
                                    onChange={e => handleInputChange('date_format', e.target.value)}
                                >
                                    <option value="YYYY-MM-DD">2023-12-31</option>
                                    <option value="DD/MM/YYYY">31/12/2023</option>
                                    <option value="MM/DD/YYYY">12/31/2023</option>
                                    <option value="DD-MM-YYYY">31-12-2023</option>
                                </select>
                            </div>
                            <div>
                                <Label>Separador de Decimales</Label>
                                <select
                                    className="w-full p-3 mt-2 border rounded-md"
                                    value={formData.amount_format}
                                    onChange={e => handleInputChange('amount_format', e.target.value)}
                                >
                                    <option value="decimal">Punto (1000.00)</option>
                                    <option value="comma">Coma (1000,00)</option>
                                </select>
                            </div>
                        </div>
                    </div>
                )}

                {/* STEP 3: MAPEO */}
                {step === 3 && (
                    <div className="space-y-6 animate-in fade-in slide-in-from-right-4">
                        <Alert className="bg-green-50 border-green-200">
                            <CheckCircle className="h-4 w-4 text-green-600" />
                            <AlertDescription className="text-green-800 font-medium">
                                ¡Casi listo! Indica en qué columna (Letra) está cada dato.
                            </AlertDescription>
                        </Alert>

                        <div className="grid gap-6">
                            {['date', 'description', 'amount', 'reference', 'balance'].map((field) => (
                                <div key={field} className="flex items-center gap-4 p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                                    <div className="w-1/3">
                                        <Label className="text-base font-bold capitalize">
                                            {field === 'date' ? 'Fecha *' :
                                                field === 'description' ? 'Descripción *' :
                                                    field === 'amount' ? 'Monto *' :
                                                        field === 'reference' ? 'Referencia (Opcional)' :
                                                            'Saldo (Opcional)'}
                                        </Label>
                                        <p className="text-xs text-gray-500 mt-1">Columna en Excel</p>
                                    </div>
                                    <div className="flex-1 flex items-center gap-3">
                                        <Input
                                            value={formData.field_mapping[field]}
                                            onChange={e => handleMappingChange(field, e.target.value)}
                                            placeholder="Ej: A"
                                            className="w-24 text-center font-bold text-lg uppercase"
                                            maxLength={2}
                                        />
                                        <ArrowRight className="text-gray-300" />
                                        <Badge variant="secondary" className="px-3 py-1 font-mono">
                                            Columna: {letterToIndex(formData.field_mapping[field]) ?? '?'}
                                        </Badge>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

            </CardContent>

            <CardFooter className="flex justify-between border-t p-6 bg-gray-50">
                <Button variant="ghost" onClick={step === 1 ? onCancel : handleBack} disabled={loading}>
                    {step === 1 ? 'Cancelar' : 'Atrás'}
                </Button>

                {step < 3 ? (
                    <Button onClick={handleNext} className="gap-2">
                        Siguiente <ArrowRight className="w-4 h-4" />
                    </Button>
                ) : (
                    <Button onClick={handleSave} disabled={loading} className="gap-2 bg-green-600 hover:bg-green-700">
                        {loading ? 'Guardando...' : 'Finalizar y Guardar'}
                        {!loading && <Save className="w-4 h-4" />}
                    </Button>
                )}
            </CardFooter>
        </Card>
    );
}
