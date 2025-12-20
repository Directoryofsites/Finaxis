'use client';

import React, { useState, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import { getFinancialRatios } from '../../../lib/dashboardService';
import {
    FaChartLine, FaBalanceScale, FaChartPie, FaMoneyCheckAlt, FaPercentage,
    FaRedoAlt, FaChartArea, FaDollarSign, FaMoneyBillWave, FaArrowUp,
    FaCheckCircle, FaExclamationTriangle, FaExclamationCircle, FaSkullCrossbones, FaClipboardList
} from 'react-icons/fa';

// --- COMPONENTES AUXILIARES (Internalizados para este módulo) ---

const FinancialIndicatorCard = ({ id, title, value, max, unit, goodRange, colorClass, format, mainValue, secondaryValue, icon, mainLabel, secondaryLabel }) => {

    const Icon = icon || FaChartLine;

    // --- Lógica de Formato ---
    const formatValue = (val, fmt) => {
        if (val === null || val === undefined) return fmt === 'percent' ? '0.00 %' : (fmt === 'currency' ? '$ 0.00' : '0.00');

        if (typeof val === 'string' && (val === '' || isNaN(parseFloat(val)))) val = 0;
        val = parseFloat(val);

        if (fmt === 'currency') {
            const formatted = new Intl.NumberFormat('es-CO', {
                style: 'currency',
                currency: 'USD',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            }).format(val);
            const isNegative = val < 0;
            const cleanFormatted = formatted.replace('-', '').replace('US', '').replace('$', '').trim();
            return (isNegative ? '- ' : '') + '$ ' + cleanFormatted;
        }
        if (fmt === 'percent') {
            return `${(val).toFixed(2)} %`;
        }
        if (fmt === 'ratio') {
            return val.toFixed(2) + ' ' + unit;
        }
        return val.toLocaleString('es-CO');
    };

    const ratioDisplay = formatValue(value, format);
    const mainDisplay = formatValue(mainValue, 'currency');
    const secondaryDisplay = formatValue(secondaryValue, 'currency');
    const colorStyle = colorClass.replace('text-orange-500', 'text-blue-500'); // Uniformidad de color azul para rango medio

    return (
        <div className="bg-white p-5 rounded-xl shadow-lg border-l-4 border-gray-200 transition duration-300 hover:shadow-xl">
            <div className="flex items-center justify-between mb-3">
                <p className="text-sm font-semibold uppercase tracking-wider text-gray-500">{title}</p>
                <Icon className={`w-6 h-6 ${colorStyle}`} />
            </div>
            <div className="flex items-baseline mb-2">
                <p className={`text-4xl font-extrabold ${colorStyle}`}>{ratioDisplay}</p>
                <span className={`ml-2 text-base font-semibold ${colorStyle}`}>{unit === '%' ? '' : unit}</span>
            </div>
            <div className="mt-4 border-t pt-3 border-gray-100">
                <div className="flex justify-between text-sm font-medium text-gray-700">
                    <span>{mainLabel}:</span>
                    <span className="text-gray-800 font-bold">{mainDisplay}</span>
                </div>
                <div className="flex justify-between text-sm text-gray-600">
                    <span>{secondaryLabel}:</span>
                    <span className="text-gray-800 font-bold">{secondaryDisplay}</span>
                </div>
                <p className={`mt-2 text-xs font-semibold ${colorStyle}`}>Desempeño: {goodRange}</p>
            </div>
        </div>
    );
};

const TextualAnalysis = ({ analysisData, escenario, interpretacion, recomendaciones }) => {
    if (!escenario) return null;

    const escenarioConfig = {
        1: { name: 'ÓPTIMO (Sólido y eficiente)', icon: FaArrowUp, color: 'border-green-600 text-green-600', iconColor: 'text-green-600' },
        2: { name: 'ESTABLE (Sano, pero con márgenes ajustados)', icon: FaCheckCircle, color: 'border-blue-500 text-blue-500', iconColor: 'text-blue-500' },
        3: { name: 'VIGILANCIA (Equilibrio frágil)', icon: FaExclamationTriangle, color: 'border-yellow-500 text-yellow-500', iconColor: 'text-yellow-500' },
        4: { name: 'RIESGO (Desequilibrio financiero)', icon: FaExclamationCircle, color: 'border-orange-500 text-orange-500', iconColor: 'text-orange-500' },
        5: { name: 'CRÍTICO (Insolvencia o pérdida de capital)', icon: FaSkullCrossbones, color: 'border-red-600 text-red-600', iconColor: 'text-red-600' },
    };

    const config = escenarioConfig[escenario] || escenarioConfig[3];
    const EscenarioIcon = config.icon;

    const analysisIcons = {
        'razon_corriente': '💧 Liquidez',
        'prueba_acida': '⚡ Liquidez Inmediata',
        'capital_trabajo_neto': '💼 Capital de Trabajo',
        'nivel_endeudamiento': '💣 Endeudamiento',
        'apalancamiento_financiero': '⚙️ Apalancamiento',
        'margen_neto_utilidad': '💵 Margen Neto',
        'margen_bruto_utilidad': '💰 Margen Bruto',
        'rentabilidad_patrimonio': '📊 Rentab. Patrimonio',
        'rentabilidad_activo': '📈 Rentab. Activo',
    };

    return (
        <div className={`bg-white p-6 rounded-xl shadow-lg mb-8 border-t-4 ${config.color}`}>
            <h2 className={`text-xl font-bold mb-4 flex items-center ${config.iconColor}`}>
                <EscenarioIcon className="mr-3" />
                Diagnóstico Estratégico General: Escenario {escenario} - {config.name}
            </h2>
            <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-700 mb-2">Análisis Narrativo del SEEE:</h3>
                <p className="text-gray-600 italic whitespace-pre-wrap">{interpretacion}</p>
            </div>
            {recomendaciones && recomendaciones.length > 0 && (
                <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-700 mb-2 flex items-center">
                        <FaClipboardList className="mr-2 text-blue-500" />
                        Recomendaciones Automáticas:
                    </h3>
                    <ul className="list-disc ml-6 space-y-1 text-gray-600">
                        {recomendaciones.map((rec, index) => (
                            <li key={index} className="text-sm">{rec}</li>
                        ))}
                    </ul>
                </div>
            )}
            <div className="mt-6 border-t pt-4">
                <h3 className="text-lg font-semibold text-gray-700 mb-2">Detalle de Ratios Individuales:</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {analysisData.map((item, index) => (
                        <div key={index} className="p-3 bg-white rounded-md border border-gray-100 shadow-sm">
                            <p className="text-sm font-bold text-gray-800 mb-1">
                                {analysisIcons[item.indicador] || item.title} <span className="font-normal text-blue-600">({item.ratioValue})</span>
                            </p>
                            <p className="text-xs text-gray-500 italic">{item.comentario}</p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

// --- LÓGICA DE ANÁLISIS ---

const analysisRules = [
    // RAZÓN CORRIENTE
    { "indicador": "razon_corriente", "rango_condicional": { "min": 0, "max": 1 }, "comentario": "Liquidez crítica. Los activos corrientes no alcanzan a cubrir las deudas inmediatas." },
    { "indicador": "razon_corriente", "rango_condicional": { "min": 1, "max": 1.5 }, "comentario": "Liquidez débil. Margen estrecho." },
    { "indicador": "razon_corriente", "rango_condicional": { "min": 1.5, "max": 2.5 }, "comentario": "Liquidez saludable. Equilibrio adecuado." },
    { "indicador": "razon_corriente", "rango_condicional": { "min": 2.5, "max": 4 }, "comentario": "Liquidez alta. Buena capacidad de pago." },
    { "indicador": "razon_corriente", "rango_condicional": { "min": 4, "max": Infinity }, "comentario": "Exceso de liquidez. Posible ineficiencia de recursos." },
    // PRUEBA ÁCIDA
    { "indicador": "prueba_acida", "rango_condicional": { "min": 0, "max": 0.8 }, "comentario": "Liquidez inmediata insuficiente." },
    { "indicador": "prueba_acida", "rango_condicional": { "min": 0.8, "max": 1.2 }, "comentario": "Liquidez ajustada." },
    { "indicador": "prueba_acida", "rango_condicional": { "min": 1.2, "max": 2 }, "comentario": "Liquidez sólida." },
    { "indicador": "prueba_acida", "rango_condicional": { "min": 2, "max": 3 }, "comentario": "Liquidez fuerte." },
    { "indicador": "prueba_acida", "rango_condicional": { "min": 3, "max": Infinity }, "comentario": "Liquidez extraordinaria." },
    // CAPITAL TRABAJO
    { "indicador": "capital_trabajo_neto", "rango_condicional": { "min": -Infinity, "max": 0 }, "comentario": "Capital negativo. Riesgo de insolvencia." },
    { "indicador": "capital_trabajo_neto", "rango_condicional": { "min": 0, "max": 5000000 }, "comentario": "Capital ajustado." },
    { "indicador": "capital_trabajo_neto", "rango_condicional": { "min": 5000000, "max": 20000000 }, "comentario": "Capital adecuado." },
    { "indicador": "capital_trabajo_neto", "rango_condicional": { "min": 20000000, "max": Infinity }, "comentario": "Capital robusto." },
    // ENDEUDAMIENTO
    { "indicador": "nivel_endeudamiento", "rango_condicional": { "min": 0, "max": 0.4 }, "comentario": "Endeudamiento bajo/moderado." },
    { "indicador": "nivel_endeudamiento", "rango_condicional": { "min": 0.4, "max": 0.6 }, "comentario": "Endeudamiento óptimo." },
    { "indicador": "nivel_endeudamiento", "rango_condicional": { "min": 0.6, "max": 0.8 }, "comentario": "Alto endeudamiento." },
    { "indicador": "nivel_endeudamiento", "rango_condicional": { "min": 0.8, "max": 1 }, "comentario": "Sobreendeudamiento crítico." },
    // APALANCAMIENTO
    { "indicador": "apalancamiento_financiero", "rango_condicional": { "min": 0, "max": 2 }, "comentario": "Apalancamiento bajo/moderado." },
    { "indicador": "apalancamiento_financiero", "rango_condicional": { "min": 2, "max": 3 }, "comentario": "Apalancamiento óptimo." },
    { "indicador": "apalancamiento_financiero", "rango_condicional": { "min": 3, "max": Infinity }, "comentario": "Apalancamiento alto." },
    // MÁRGENES
    { "indicador": "margen_neto_utilidad", "rango_condicional": { "min": -Infinity, "max": 0 }, "comentario": "Pérdidas netas." },
    { "indicador": "margen_neto_utilidad", "rango_condicional": { "min": 0, "max": 0.05 }, "comentario": "Margen bajo." },
    { "indicador": "margen_neto_utilidad", "rango_condicional": { "min": 0.05, "max": 0.15 }, "comentario": "Margen moderado." },
    { "indicador": "margen_neto_utilidad", "rango_condicional": { "min": 0.15, "max": Infinity }, "comentario": "Margen excelente." },
    { "indicador": "margen_bruto_utilidad", "rango_condicional": { "min": -Infinity, "max": 0.2 }, "comentario": "Margen bruto crítico." },
    { "indicador": "margen_bruto_utilidad", "rango_condicional": { "min": 0.2, "max": 0.4 }, "comentario": "Margen bruto saludable." },
    { "indicador": "margen_bruto_utilidad", "rango_condicional": { "min": 0.4, "max": Infinity }, "comentario": "Margen bruto fuerte." },
    // RENTABILIDAD
    { "indicador": "rentabilidad_patrimonio", "rango_condicional": { "min": -Infinity, "max": 0.05 }, "comentario": "ROE Bajo o Negativo." },
    { "indicador": "rentabilidad_patrimonio", "rango_condicional": { "min": 0.05, "max": Infinity }, "comentario": "ROE Positivo." },
    { "indicador": "rentabilidad_activo", "rango_condicional": { "min": -Infinity, "max": 0.05 }, "comentario": "ROA Bajo o Negativo." },
    { "indicador": "rentabilidad_activo", "rango_condicional": { "min": 0.05, "max": Infinity }, "comentario": "ROA Positivo." },
];

const findAnalysis = (ratioId, value, ratiosConfig, kpisData) => {
    let search_value = ratioId === 'margen_neto_utilidad' || ratioId === 'margen_bruto_utilidad' || ratioId.startsWith('rentabilidad') || ratioId.startsWith('nivel')
        ? value / 100
        : value;

    if (isNaN(value) || value === Infinity || value === -Infinity) {
        return { comentario: "Anomalía de Datos.", ratioValue: 'N/A' };
    }

    const analysis = analysisRules.find(rule =>
        rule.indicador === ratioId &&
        search_value >= rule.rango_condicional.min &&
        search_value < rule.rango_condicional.max
    );

    const ratioConfig = ratiosConfig.find(r => r.id === ratioId);
    let ratioValue = ratioConfig && ratioConfig.format === 'percent' ? `${value.toFixed(2)} %` : (ratioConfig && ratioConfig.format === 'ratio' ? `${value.toFixed(2)} ${ratioConfig.unit}` : value.toFixed(2));

    return {
        comentario: analysis ? analysis.comentario : "N/A",
        ratioValue: ratioValue
    };
};

const RatiosDisplay = ({ kpisData }) => {
    if (!kpisData) return null;

    const activoCorriente = parseFloat(kpisData.activo_corriente) || 0;
    const pasivoCorriente = parseFloat(kpisData.pasivo_corriente) || 0;
    const inventariosTotal = parseFloat(kpisData.inventarios_total) || 0;

    const capitalTrabajoNetoValue = activoCorriente - pasivoCorriente;
    const numeradorPruebaAcida = activoCorriente - inventariosTotal;

    const ratiosConfig = [
        {
            id: 'razon_corriente', title: "Razón Corriente", max: 3.0, unit: 'x', goodRange: '> 1.5x', icon: FaBalanceScale, format: 'ratio',
            mainData: 'activo_corriente', secondaryData: 'pasivo_corriente', mainLabel: 'Activo C.', secondaryLabel: 'Pasivo C.',
            colorLogic: (val) => val > 1.5 ? "text-green-600" : (val > 1.0 ? "text-blue-500" : "text-red-600")
        },
        {
            id: 'prueba_acida', title: "Prueba Ácida", max: 2.0, unit: 'x', goodRange: '> 1.0x', icon: FaChartPie, format: 'ratio',
            mainData: 'prueba_acida', secondaryData: 'pasivo_corriente', mainLabel: 'AC - Inv', secondaryLabel: 'Pasivo C.',
            colorLogic: (val) => val > 1.0 ? "text-green-600" : (val > 0.7 ? "text-blue-500" : "text-red-600")
        },
        {
            id: 'capital_trabajo_neto', title: "Capital de Trabajo", format: 'currency', goodRange: '> $0', icon: FaMoneyCheckAlt, format: 'currency',
            mainData: 'activo_corriente', secondaryData: 'pasivo_corriente', mainLabel: 'Activo C.', secondaryLabel: 'Pasivo C.',
            colorLogic: (val) => val > 0 ? "text-green-600" : "text-red-600"
        },
        {
            id: 'nivel_endeudamiento', title: "Endeudamiento", max: 1.0, unit: '%', goodRange: '< 50%', icon: FaPercentage, format: 'percent',
            mainData: 'pasivos_total', secondaryData: 'activos_total', mainLabel: 'Pasivo Total', secondaryLabel: 'Activo Total',
            colorLogic: (val) => val < 0.50 ? "text-green-600" : (val < 0.70 ? "text-blue-500" : "text-red-600")
        },
        {
            id: 'apalancamiento_financiero', title: "Apalancamiento", max: 5.0, unit: 'x', goodRange: '< 3.0x', icon: FaRedoAlt, format: 'ratio',
            mainData: 'pasivos_total', secondaryData: 'patrimonio_total', mainLabel: 'Pasivo Total', secondaryLabel: 'Patrimonio',
            colorLogic: (val) => val < 3.0 ? "text-green-600" : (val < 4.0 ? "text-blue-500" : "text-red-600")
        },
        {
            id: 'margen_neto_utilidad', title: "Margen Neto", max: 30, unit: '%', goodRange: '> 5%', icon: FaChartArea, format: 'percent',
            mainData: 'utilidad_neta', secondaryData: 'ingresos_anuales', mainLabel: 'Utilidad Neta', secondaryLabel: 'Ingresos',
            colorLogic: (val) => val > 5 ? "text-green-600" : (val > 0 ? "text-blue-500" : "text-red-600")
        },
        {
            id: 'rentabilidad_patrimonio', title: "ROE", max: 20, unit: '%', goodRange: '> 10%', icon: FaChartLine, format: 'percent',
            mainData: 'utilidad_neta', secondaryData: 'patrimonio_total', mainLabel: 'Utilidad Neta', secondaryLabel: 'Patrimonio',
            colorLogic: (val) => val > 10 ? "text-green-600" : (val > 5 ? "text-blue-500" : "text-red-600")
        },
        {
            id: 'rentabilidad_activo', title: "ROA", max: 15, unit: '%', goodRange: '> 5%', icon: FaDollarSign, format: 'percent',
            mainData: 'utilidad_neta', secondaryData: 'activos_total', mainLabel: 'Utilidad Neta', secondaryLabel: 'Activo Total',
            colorLogic: (val) => val > 5 ? "text-green-600" : (val > 2 ? "text-blue-500" : "text-red-600")
        },
        {
            id: 'margen_bruto_utilidad', title: "Margen Bruto", max: 60, unit: '%', goodRange: '> 20%', icon: FaMoneyBillWave, format: 'percent',
            mainData: 'ingresos_anuales', secondaryData: 'costo_ventas_total', mainLabel: 'Ingresos', secondaryLabel: 'Costos',
            colorLogic: (val) => val > 40 ? "text-green-600" : (val > 20 ? "text-blue-500" : "text-red-600")
        },
    ];

    const analysisData = [];
    ratiosConfig.forEach((ratio) => {
        let value = parseFloat(kpisData[ratio.id]) || 0;
        if (ratio.id === 'capital_trabajo_neto') value = capitalTrabajoNetoValue;

        let mainValue, secondaryValue;
        if (ratio.id === 'prueba_acida') {
            mainValue = numeradorPruebaAcida;
            secondaryValue = pasivoCorriente;
        } else if (ratio.id === 'capital_trabajo_neto') {
            mainValue = activoCorriente;
            secondaryValue = pasivoCorriente;
        } else if (ratio.id === 'margen_bruto_utilidad') {
            const ingresos = parseFloat(kpisData.ingresos_anuales) || 0;
            const utilidadBruta = ingresos - (parseFloat(kpisData.costo_ventas_total) || 0);
            mainValue = utilidadBruta;
            secondaryValue = ingresos;
            ratio.mainLabel = 'U. Bruta';
        } else {
            mainValue = parseFloat(kpisData[ratio.mainData]) || 0;
            secondaryValue = parseFloat(kpisData[ratio.secondaryData]) || 0;
        }

        const analysis = findAnalysis(ratio.id, value, ratiosConfig, kpisData);
        analysisData.push({ indicador: ratio.id, title: ratio.title, comentario: analysis.comentario, ratioValue: analysis.ratioValue });

        ratio.value = value;
        ratio.mainValue = mainValue;
        ratio.secondaryValue = secondaryValue;
        ratio.colorClass = ratio.colorLogic(value);
    });

    return (
        <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                {ratiosConfig.map((ratio) => (
                    <FinancialIndicatorCard key={ratio.id} {...ratio} />
                ))}
            </div>
            <TextualAnalysis
                analysisData={analysisData}
                escenario={kpisData.escenario_general}
                interpretacion={kpisData.texto_interpretativo}
                recomendaciones={kpisData.recomendaciones_breves}
            />
        </>
    );
};

// --- PÁGINA PRINCIPAL ---

export default function AnalysisDashboardPage() {
    const { user } = useAuth();
    const [fechaInicio, setFechaInicio] = useState(new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0]);
    const [fechaFin, setFechaFin] = useState(new Date().toISOString().split('T')[0]);
    const [kpisData, setKpisData] = useState(null);
    const [loading, setLoading] = useState(false);

    const fetchData = useCallback(async () => {
        setLoading(true);
        try {
            const data = await getFinancialRatios(fechaInicio, fechaFin);
            setKpisData(data);
        } catch (error) {
            console.error("Error fetching ratios:", error);
        } finally {
            setLoading(false);
        }
    }, [fechaInicio, fechaFin]);

    return (
        <div className="p-6 max-w-7xl mx-auto">
            <h1 className="text-3xl font-bold text-gray-800 mb-6">Tablero de Control Financiero</h1>

            <div className="bg-white p-6 rounded-xl shadow-md mb-8 flex flex-col md:flex-row gap-4 items-end">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Fecha Inicio</label>
                    <input type="date" value={fechaInicio} onChange={(e) => setFechaInicio(e.target.value)} className="border rounded-lg px-4 py-2" />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Fecha Corte</label>
                    <input type="date" value={fechaFin} onChange={(e) => setFechaFin(e.target.value)} className="border rounded-lg px-4 py-2" />
                </div>
                <button
                    onClick={fetchData}
                    disabled={loading}
                    className="bg-blue-600 text-white px-6 py-2 rounded-lg font-bold hover:bg-blue-700 transition disabled:opacity-50"
                >
                    {loading ? 'Analizando...' : 'Ejecutar Análisis'}
                </button>
            </div>

            <RatiosDisplay kpisData={kpisData} />

            {!kpisData && !loading && (
                <div className="p-8 text-center text-gray-500 bg-gray-50 rounded-xl border border-dashed border-gray-300">
                    Seleccione un rango de fechas y presione "Ejecutar Análisis" para generar el informe.
                </div>
            )}
        </div>
    );
}
