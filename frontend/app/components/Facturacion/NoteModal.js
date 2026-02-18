'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { FaTimes, FaSave, FaFileInvoiceDollar } from 'react-icons/fa';
import { apiService } from '../../../lib/apiService';

// Códigos de Concepto DIAN (Simplificados)
const CONCEPTOS_NOTA_CREDITO = [
    { code: '1', label: '1. Devolución parcial de los bienes y/o no aceptación parcial del servicio' },
    { code: '2', label: '2. Anulación de factura electrónica' },
    { code: '3', label: '3. Rebaja o descuento total o parcial' },
    { code: '4', label: '4. Ajuste de precio' },
    { code: '5', label: '5. Otros' },
    { code: '6', label: '6. Otros (Gastos, Intereses, etc.)' },
];

const CONCEPTOS_NOTA_DEBITO = [
    { code: '1', label: '1. Intereses' },
    { code: '2', label: '2. Gastos por cobrar' },
    { code: '3', label: '3. Cambio del valor' },
    { code: '4', label: '4. Otros' },
];

export default function NoteModal({
    isOpen,
    onClose,
    type = 'credit', // 'credit' | 'debit'
    sourceDocument, // Documento original (Factura)
    onSuccess
}) {
    const [items, setItems] = useState([]);
    const [concept, setConcept] = useState('1'); // Default to 1
    const [reason, setReason] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    // --- NUEVO: Selección de Tipo de Documento ---
    const [availableTypes, setAvailableTypes] = useState([]);
    const [selectedTipoDocId, setSelectedTipoDocId] = useState('');

    const isCredit = type === 'credit';
    const title = isCredit ? 'Generar Nota de Crédito' : 'Generar Nota de Débito';
    const conceptos = isCredit ? CONCEPTOS_NOTA_CREDITO : CONCEPTOS_NOTA_DEBITO;

    // Cargar items del documento original al abrir
    useEffect(() => {
        if (isOpen && sourceDocument) {
            // Intentar usar detalle_productos (vista comercial) si existe, sino fallback a movimientos
            // Pero para notas necesitamos productos reales.
            const sourceItems = sourceDocument.detalle_productos || [];

            // Mapear a estado local
            const initialItems = sourceItems.map(item => ({
                ...item,
                cantidad_nota: 0, // Iniciar en 0 para que el usuario seleccione
                valor_nota: 0,
                selected: false
            }));
            setItems(initialItems);
            setReason('');
            setConcept('1');
            setError('');
        }
    }, [isOpen, sourceDocument, type]);

    // Cargar Tipos de Documento Disponibles
    useEffect(() => {
        if (isOpen && sourceDocument) {
            const fetchTypes = async () => {
                try {
                    const res = await apiService.get('/tipos-documento', { params: { empresa_id: sourceDocument.empresa_id } });
                    const allTypes = res.data;
                    const filtered = allTypes.filter(t => {
                        const fe = t.funcion_especial ? t.funcion_especial.toLowerCase() : '';
                        const nombre = t.nombre ? t.nombre.toLowerCase() : '';
                        const codigo = t.codigo ? t.codigo.toUpperCase() : '';

                        if (isCredit) {
                            return fe === 'nota_credito' || fe === 'nota credito' ||
                                codigo === 'NC' || codigo === 'NCRE' || codigo.startsWith('NC') ||
                                nombre.includes('nota cré') || nombre.includes('nota cre');
                        } else {
                            // Nota Débito
                            return fe === 'nota_debito' || fe === 'nota debito' ||
                                codigo === 'ND' || codigo === 'NDEB' || codigo.startsWith('ND') ||
                                nombre.includes('nota dé') || nombre.includes('nota de');
                        }
                    });
                    setAvailableTypes(filtered);
                    if (filtered.length > 0) setSelectedTipoDocId(filtered[0].id);
                } catch (err) {
                    console.error("Error fetching note types", err);
                }
            };
            fetchTypes();
        }
    }, [isOpen, sourceDocument, isCredit]);


    const handleQuantityChange = (index, val) => {
        const newItems = [...items];
        const maxQty = newItems[index].cantidad;
        let newQty = parseFloat(val);

        if (isNaN(newQty)) newQty = 0;
        if (newQty < 0) newQty = 0;

        // Validación de cantidad máxima (solo si NO es nota débito pura por valor mayor)
        // En Nota Débito conceptualmente podríamas cobrar MÁS cantidad si fue error de facturación?
        // Por seguridad, mantenemos tope en cantidad original para referencias.
        if (newQty > maxQty) newQty = maxQty;

        newItems[index].cantidad_nota = newQty;
        newItems[index].valor_nota = newQty * newItems[index].vrUnitario; // Recalcular valor total
        newItems[index].selected = newQty > 0;
        setItems(newItems);
    };

    const handleValueChange = (index, val) => {
        const newItems = [...items];
        // El valor máximo es el total de la línea original
        // En Nota DÉBITO, el valor PUEDE ser mayor (Intereses, mayor valor).
        // En Nota CRÉDITO, no debería exceder el original.

        const maxVal = newItems[index].cantidad * newItems[index].vrUnitario;
        let newVal = parseFloat(val);

        if (isNaN(newVal)) newVal = 0;
        if (newVal < 0) newVal = 0;

        // Bloqueo solo para Crédito
        if (isCredit && newVal > maxVal) newVal = maxVal;

        newItems[index].valor_nota = newVal;
        // Para notas por valor, la cantidad visual puede ser irrelevante o fija en 1
        newItems[index].cantidad_nota = 1;
        newItems[index].selected = newVal > 0;
        setItems(newItems);
    };

    const toggleSelect = (index) => {
        const newItems = [...items];
        newItems[index].selected = !newItems[index].selected;

        // --- LÓGICA DE MODO VALOR VS MODO CANTIDAD ---
        // Nota Crédito: Solo concepto 3 es por valor (Rebaja).
        // Nota Débito: Casi todo es por valor (Intereses, Gastos, Cambio Valor).
        const isValueMode = (isCredit && concept === '3') || (!isCredit && ['1', '2', '3'].includes(concept));

        if (newItems[index].selected) {
            if (isValueMode) {
                // Modo Valor: Prellenar con el total de la línea
                newItems[index].cantidad_nota = 1;
                newItems[index].valor_nota = newItems[index].cantidad * newItems[index].vrUnitario;
            } else {
                // Modo Cantidad: Prellenar con cantidad máxima
                newItems[index].cantidad_nota = newItems[index].cantidad;
                newItems[index].valor_nota = newItems[index].cantidad * newItems[index].vrUnitario;
            }
        } else {
            newItems[index].cantidad_nota = 0;
            newItems[index].valor_nota = 0;
        }
        setItems(newItems);
    };

    const calculateTotal = useMemo(() => {
        return items.reduce((acc, item) => {
            if (!item.selected) return acc;
            return acc + (item.valor_nota !== undefined ? item.valor_nota : (item.cantidad_nota * item.vrUnitario));
        }, 0);
    }, [items, concept]);

    // Helper para saber si renderizar input de Valor o Cantidad
    const isValueModeRender = (isCredit && concept === '3') || (!isCredit && ['1', '2', '3'].includes(concept));

    const handleSubmit = async () => {
        const selectedItems = items.filter(i => i.selected && i.cantidad_nota > 0);

        if (selectedItems.length === 0 && concept !== '2') {
            // Nota: Concept 2 en NC es anulación, podría no llevar items si anula todo? No, siempre lleva items.
            // En ND Concept 2 es Gastos, lleva valor.
            setError("Debe seleccionar al menos un ítem y una cantidad válida.");
            return;
        }

        if (!reason.trim()) {
            setError("El motivo es obligatorio.");
            return;
        }

        if (!selectedTipoDocId) {
            setError("Debe seleccionar un Tipo de Documento para la nota.");
            return;
        }

        setIsLoading(true);
        setError('');

        try {
            // Construir Payload
            const payload = {
                tipo_documento_id: selectedTipoDocId,
                beneficiario_id: sourceDocument.beneficiario_id,
                fecha: new Date().toISOString().split('T')[0],
                fecha_vencimiento: new Date().toISOString().split('T')[0],
                condicion_pago: 'Contado',

                documento_referencia_id: sourceDocument.id,
                observaciones: `[${concept}] ${reason}`,
                bodega_id: sourceDocument.bodega_id,
                centro_costo_id: sourceDocument.centro_costo_id,

                items: selectedItems.map(item => ({
                    producto_id: item.producto_id,
                    cantidad: item.cantidad_nota,
                    // Si es modo valor, enviamos el valor como precio unitario (cantidad=1)
                    precio_unitario: isValueModeRender ? item.valor_nota : item.vrUnitario,
                    descuento_tasa: 0,
                }))
            };

            // Enviar
            const res = await apiService.post('/facturacion/', payload);

            onSuccess(res.data);
            onClose();

        } catch (err) {
            console.error(err);
            setError(err.response?.data?.detail || err.message || "Error al crear la nota.");
        } finally {
            setIsLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex justify-center items-center p-4 animate-fadeIn">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col border border-gray-100">

                {/* HEADER */}
                <div className={`p-6 border-b flex justify-between items-center text-white rounded-t-xl ${isCredit ? 'bg-orange-600' : 'bg-blue-600'}`}>
                    <div className="flex items-center gap-3">
                        <FaFileInvoiceDollar className="text-2xl" />
                        <div>
                            <h2 className="text-xl font-bold">{title}</h2>
                            <p className="text-xs opacity-90">Basado en Fac. {sourceDocument?.numero}</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="text-white/80 hover:text-white transition-colors">
                        <FaTimes className="text-xl" />
                    </button>
                </div>

                {/* BODY */}
                <div className="flex-grow overflow-y-auto p-6 bg-gray-50">

                    {error && (
                        <div className="mb-4 p-3 bg-red-100 border border-red-300 text-red-700 rounded-lg text-sm font-medium">
                            {error}
                        </div>
                    )}

                    {/* FORMULARIO SUPERIOR */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                        <div>
                            <label className="block text-sm font-bold text-gray-700 mb-2">Concepto DIAN</label>
                            <select
                                value={concept}
                                onChange={(e) => setConcept(e.target.value)}
                                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                            >
                                {conceptos.map(c => <option key={c.code} value={c.code}>{c.label}</option>)}
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-bold text-gray-700 mb-2">Tipo de Nota (Documento)</label>
                            <select
                                value={selectedTipoDocId}
                                onChange={(e) => setSelectedTipoDocId(e.target.value)}
                                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                            >
                                <option value="">Seleccione...</option>
                                {availableTypes.map(t => <option key={t.id} value={t.id}>{t.nombre}</option>)}
                            </select>
                        </div>
                        <div className="md:col-span-2">
                            <label className="block text-sm font-bold text-gray-700 mb-2">Motivo / Observaciones</label>
                            <textarea
                                value={reason}
                                onChange={(e) => setReason(e.target.value)}
                                placeholder="Explique la razón de esta nota..."
                                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 h-[42px] min-h-[42px]"
                            />
                        </div>
                    </div>

                    {/* TABLA DE ITEMS */}
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-100">
                                <tr>
                                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase w-10">
                                        <input type="checkbox" onChange={(e) => {
                                            const val = e.target.checked;
                                            setItems(items.map(i => {
                                                const baseVal = i.cantidad * i.vrUnitario;
                                                return {
                                                    ...i,
                                                    selected: val,
                                                    cantidad_nota: val ? (concept === '3' ? 1 : i.cantidad) : 0,
                                                    valor_nota: val ? baseVal : 0
                                                };
                                            }));
                                        }} />
                                    </th>
                                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase">Producto</th>
                                    <th className="px-4 py-3 text-right text-xs font-bold text-gray-500 uppercase">Cant. Orig.</th>
                                    <th className="px-4 py-3 text-right text-xs font-bold text-gray-500 uppercase w-32">
                                        {concept === '3' ? 'Valor Nota' : 'Cant. Nota'}
                                    </th>
                                    <th className="px-4 py-3 text-right text-xs font-bold text-gray-500 uppercase">Total</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                                {items.length === 0 ? (
                                    <tr><td colSpan="5" className="p-4 text-center text-gray-400">No hay productos disponibles.</td></tr>
                                ) : items.map((item, idx) => (
                                    <tr key={idx} className={item.selected ? 'bg-blue-50' : 'hover:bg-gray-50'}>
                                        <td className="px-4 py-3">
                                            <input
                                                type="checkbox"
                                                checked={item.selected}
                                                onChange={() => toggleSelect(idx)}
                                                className="rounded text-indigo-600 focus:ring-indigo-500"
                                            />
                                        </td>
                                        <td className="px-4 py-3 text-sm text-gray-800">{item.nombre_producto}</td>
                                        <td className="px-4 py-3 text-sm text-gray-600 text-right font-mono">{item.cantidad}</td>
                                        <td className="px-4 py-2 text-right">
                                            {isValueModeRender ? (
                                                <input
                                                    type="number"
                                                    min="0"
                                                    // En debito no hay maximo teorico para aumentos de valor
                                                    max={isCredit ? item.cantidad * item.vrUnitario : undefined}
                                                    step="100"
                                                    value={item.valor_nota}
                                                    onChange={(e) => handleValueChange(idx, e.target.value)}
                                                    disabled={!item.selected}
                                                    className="w-32 p-1 border border-gray-300 rounded text-right text-sm font-bold disabled:bg-gray-100 disabled:text-gray-400"
                                                />
                                            ) : (
                                                <input
                                                    type="number"
                                                    min="0"
                                                    max={item.cantidad}
                                                    step="0.01"
                                                    value={item.cantidad_nota}
                                                    onChange={(e) => handleQuantityChange(idx, e.target.value)}
                                                    disabled={!item.selected}
                                                    className="w-24 p-1 border border-gray-300 rounded text-right text-sm font-bold disabled:bg-gray-100 disabled:text-gray-400"
                                                />
                                            )}
                                        </td>
                                        <td className="px-4 py-3 text-sm text-gray-800 text-right font-bold font-mono">
                                            ${(item.valor_nota !== undefined ? item.valor_nota : (item.cantidad_nota * item.vrUnitario)).toLocaleString('es-CO')}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                </div>

                {/* FOOTER */}
                <div className="p-4 border-t bg-gray-50 rounded-b-xl flex justify-between items-center">
                    <div className="text-right flex-grow mr-6">
                        <span className="text-gray-500 text-sm mr-2">Total Estimado Nota:</span>
                        <span className="text-2xl font-bold text-gray-800">${calculateTotal.toLocaleString('es-CO')}</span>
                    </div>
                    <div className="flex gap-3">
                        <button
                            onClick={onClose}
                            className="px-4 py-2 text-gray-600 hover:bg-gray-200 rounded-lg font-medium transition-colors"
                            disabled={isLoading}
                        >
                            Cancelar
                        </button>
                        <button
                            onClick={handleSubmit}
                            className={`px-6 py-2 text-white rounded-lg font-bold shadow-lg transition-transform active:scale-95 flex items-center gap-2 ${isCredit ? 'bg-orange-600 hover:bg-orange-700' : 'bg-blue-600 hover:bg-blue-700'}`}
                            disabled={isLoading}
                        >
                            {isLoading ? 'Procesando...' : (
                                <>
                                    <FaSave /> Crear Nota
                                </>
                            )}
                        </button>
                    </div>
                </div>

            </div>
        </div>
    );
}

