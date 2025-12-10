"use client";

import { useAuth } from './context/AuthContext';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import React, { useState, useMemo, useEffect, useCallback, Suspense } from 'react';

// Importamos TODOS los íconos necesarios
import {
    FaBars, FaTimes, FaHome, FaCalculator, FaChartLine, FaBoxes, FaCog,
    FaUsers, FaSignOutAlt, FaPercentage, FaFileAlt, FaChartBar, FaWrench,
    FaFileContract, FaBook, FaListUl, FaPlus, FaClipboardList, FaHandshake,
    FaUniversity, FaReceipt, FaTruckMoving, FaMoneyBill, FaTools,
    FaGg, FaRedoAlt, FaBalanceScale, FaChartPie, FaChartArea, FaDollarSign, FaMoneyCheckAlt,
    FaExclamationTriangle, FaCheckCircle, FaExclamationCircle, FaSkullCrossbones, FaArrowUp, FaMoneyBillWave,
    FaStar, FaChevronRight, FaFolder, FaFile, FaCalendarAlt, FaPlayCircle, FaArrowLeft, FaLock,
    FaFileInvoiceDollar, FaBuilding, FaStamp, FaShoppingCart
} from 'react-icons/fa';
import { toast, ToastContainer } from 'react-toastify';

// --- Importación de Componentes CRÍTICOS ---
import QuickAccessGrid from './components/QuickAccessGrid';
import ConsumoWidget from './components/dashboard/ConsumoWidget';
import Sidebar from '../components/Sidebar'; // Usamos el nuevo componente Sidebar
import { menuStructure } from '../lib/menuData'; // Usamos la data centralizada

// --- Servicios Frontend ---
import { getFinancialRatios, getHorizontalAnalysis, getVerticalAnalysis } from '../lib/dashboardService';
import { getFavoritos } from '../lib/favoritosService';

// =============================================================
// II. COMPONENTES REUTILIZABLES: TILES Y LÓGICA DE EXPLORADOR
// =============================================================

/**
 * Componente que define el estilo de botón 'Tile' (Tarjeta de Favoritos)
 * para ser usado en el ExplorerView.
 */
const ModuleTile = ({ title, description, icon, onClick, isFolder = false }) => {
    const IconComponent = icon || FaFileAlt;
    const colorClass = isFolder ? 'text-blue-600' : 'text-green-600'; // Carpetas en azul, Archivos/Enlaces en verde/negro

    return (
        <button
            onClick={onClick}
            className="flex flex-col items-start justify-start p-4 h-24 text-left bg-white border border-gray-200 rounded-lg shadow-sm hover:border-blue-500 hover:shadow-md transition duration-200 group transform hover:scale-[1.01] w-full"
            title={title}
        >
            <div className="flex items-center space-x-3">
                <IconComponent size={24} className={`mb-1 ${colorClass} group-hover:text-blue-700`} />
                <span className="text-sm font-semibold truncate text-gray-800">{title}</span>
            </div>
            {/* Solo mostramos la descripción para los enlaces que son Nivel 3 */}
            {isFolder && <span className="text-xs text-gray-500 mt-1 truncate max-w-full">Explorar sub-opciones...</span>}
            {!isFolder && <span className="text-xs text-gray-500 mt-1 truncate max-w-full">Ejecutar función</span>}
        </button>
    );
};


// *** Se incluyen las definiciones de FinancialIndicatorCard, TextualAnalysis, RatiosDisplay, findAnalysis, analysisRules ***
// ----------------------------------------------------------------------------------------------------------------------
// Nota: Todo el código de las funciones y componentes de Dashboard debe ser incluido aquí.
// ----------------------------------------------------------------------------------------------------------------------


/**
 * Componente que muestra una tarjeta con el indicador financiero moderno.
 */
const FinancialIndicatorCard = ({ id, title, value, max, unit, goodRange, colorClass, format, mainValue, secondaryValue, icon, mainLabel, secondaryLabel }) => {

    const Icon = icon || FaChartLine;

    if (value === Infinity || isNaN(value)) value = 0;

    // --- Lógica de Formato (basada en DashboardArea) ---
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

    const colorStyle = colorClass.replace('text-red-600', 'text-red-600').replace('text-green-600', 'text-green-600').replace('text-orange-500', 'text-blue-500');

    return (
        <div className="bg-white p-5 rounded-xl shadow-lg border-l-4 border-gray-200 transition duration-300 hover:shadow-xl">

            <div className="flex items-center justify-between mb-3">
                <p className="text-sm font-semibold uppercase tracking-wider text-gray-500">
                    {title}
                </p>
                <Icon className={`w-6 h-6 ${colorStyle}`} />
            </div>

            <div className="flex items-baseline mb-2">
                <p className={`text-4xl font-extrabold ${colorStyle}`}>
                    {ratioDisplay}
                </p>
                <span className={`ml-2 text-base font-semibold ${colorStyle}`}>
                    {unit === '%' ? '' : unit}
                </span>
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

                <p className={`mt-2 text-xs font-semibold ${colorStyle}`}>
                    Desempeño: {goodRange}
                </p>
            </div>
        </div>
    );
};


/**
 * NUEVO Componente para mostrar el análisis textual cualitativo.
 */
const TextualAnalysis = ({ analysisData, escenario, interpretacion, recomendaciones }) => {
    if (!escenario) return null;

    // 1. Configuración de Iconos y Estilos para el Escenario General (1 a 5)
    const escenarioConfig = {
        1: { name: 'ÓPTIMO (Sólido y eficiente)', icon: FaArrowUp, color: 'border-green-600 text-green-600', iconColor: 'text-green-600' },
        2: { name: 'ESTABLE (Sano, pero con márgenes ajustados)', icon: FaCheckCircle, color: 'border-blue-500 text-blue-500', iconColor: 'text-blue-500' },
        3: { name: 'VIGILANCIA (Equilibrio frágil)', icon: FaExclamationTriangle, color: 'border-yellow-500 text-yellow-500', iconColor: 'text-yellow-500' },
        4: { name: 'RIESGO (Desequilibrio financiero)', icon: FaExclamationCircle, color: 'border-orange-500 text-orange-500', iconColor: 'text-orange-500' },
        5: { name: 'CRÍTICO (Insolvencia o pérdida de capital)', icon: FaSkullCrossbones, color: 'border-red-600 text-red-600', iconColor: 'text-red-600' },
    };

    const config = escenarioConfig[escenario] || escenarioConfig[3];

    // Mapeo de Emojis/Iconos para el análisis individual
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

    const EscenarioIcon = config.icon;

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

            <div className="mt-6 border-t pt-4">
                <h3 className="text-lg font-semibold text-gray-700 mb-2">Detalle de Ratios Individuales:</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {analysisData.map((item, index) => (
                        <div key={index} className="p-3 bg-white rounded-md border border-gray-100 shadow-sm">
                            <p className="text-sm font-bold text-gray-800 mb-1">
                                {analysisIcons[item.indicador] || item.title} <span className="font-normal text-blue-600">({item.ratioValue})</span>
                            </p>
                            <p className="text-xs text-gray-500 italic">
                                {item.comentario}
                            </p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};


// --- LÓGICA DEL MOTOR DE ANÁLISIS AFAM ---
const analysisRules = [
    // RAZÓN CORRIENTE (LIQUIDEZ)
    { "indicador": "razon_corriente", "rango_condicional": { "min": 0, "max": 1 }, "comentario": "Liquidez crítica. Los activos corrientes no alcanzan a cubrir las deudas inmediatas. Alto riesgo de iliquidez." },
    { "indicador": "razon_corriente", "rango_condicional": { "min": 1, "max": 1.5 }, "comentario": "Liquidez débil. Aunque los activos cubren el pasivo, el margen operativo es estrecho. Mejorar la gestión del efectivo." },
    { "indicador": "razon_corriente", "rango_condicional": { "min": 1.5, "max": 2.5 }, "comentario": "Liquidez saludable. La empresa mantiene equilibrio entre solvencia y eficiencia de recursos." },
    { "indicador": "razon_corriente", "rango_condicional": { "min": 2.5, "max": 4 }, "comentario": "Liquidez alta. Buena capacidad de pago, aunque podría existir capital ocioso no invertido." },
    { "indicador": "razon_corriente", "rango_condicional": { "min": 4, "max": Infinity }, "comentario": "Exceso de liquidez. Recursos inmovilizados sin rendimiento. Se recomienda evaluar inversión productiva o distribución de utilidades." },

    // PRUEBA ÁCIDA (LIQUIDEZ INMEDIATA)
    { "indicador": "prueba_acida", "rango_condicional": { "min": 0, "max": 0.8 }, "comentario": "Liquidez inmediata insuficiente. Alto riesgo de depender de inventarios para pagar obligaciones." },
    { "indicador": "prueba_acida", "rango_condicional": { "min": 0.8, "max": 1.2 }, "comentario": "Liquidez ajustada. Se cubren las deudas a corto plazo, pero sin margen de seguridad." },
    { "indicador": "prueba_acida", "rango_condicional": { "min": 1.2, "max": 2 }, "comentario": "Liquidez sólida. Los activos líquidos respaldan adecuadamente los pasivos inmediatos." },
    { "indicador": "prueba_acida", "rango_condicional": { "min": 2, "max": 3 }, "comentario": "Liquidez fuerte. Exceso de recursos líquidos; considerar reinversión o reducción de saldos improductivos." },
    { "indicador": "prueba_acida", "rango_condicional": { "min": 3, "max": Infinity }, "comentario": "Liquidez extraordinaria. Probable ineficiencia en la utilización de efectivo." },

    // CAPITAL DE TRABAJO NETO
    { "indicador": "capital_trabajo_neto", "rango_condicional": { "min": -Infinity, "max": 0 }, "comentario": "Capital negativo. Riesgo de insolvencia inmediata; revisar estructura de pasivos y liquidez." },
    { "indicador": "capital_trabajo_neto", "rango_condicional": { "min": 0, "max": 5000000 }, "comentario": "Capital ajustado. Se mantiene solvencia básica, pero sin holgura operativa." },
    { "indicador": "capital_trabajo_neto", "rango_condicional": { "min": 5000000, "max": 20000000 }, "comentario": "Capital adecuado. Flujo operativo saludable y margen financiero aceptable." },
    { "indicador": "capital_trabajo_neto", "rango_condicional": { "min": 20000000, "max": 50000000 }, "comentario": "Capital elevado. Excelente posición financiera, aunque podría existir ineficiencia por activos improductivos." },
    { "indicador": "capital_trabajo_neto", "rango_condicional": { "min": 50000000, "max": Infinity }, "comentario": "Exceso de capital de trabajo. Recursos ociosos; se recomienda evaluar inversión productiva o distribución de utilidades." },

    // NIVEL DE ENDEUDAMIENTO
    { "indicador": "nivel_endeudamiento", "rango_condicional": { "min": 0, "max": 0.2 }, "comentario": "Endeudamiento mínimo. Muy conservador; posible desaprovechamiento del apalancamiento financiero." },
    { "indicador": "nivel_endeudamiento", "rango_condicional": { "min": 0.2, "max": 0.4 }, "comentario": "Endeudamiento moderado. Buen equilibrio entre deuda y capital propio." },
    { "indicador": "nivel_endeudamiento", "rango_condicional": { "min": 0.4, "max": 0.6 }, "comentario": "Endeudamiento óptimo. La empresa aprovecha adecuadamente la financiación externa." },
    { "indicador": "nivel_endeudamiento", "rango_condicional": { "min": 0.6, "max": 0.8 }, "comentario": "Alto endeudamiento. Riesgo financiero relevante; se debe controlar el flujo de caja." },
    { "indicador": "nivel_endeudamiento", "rango_condicional": { "min": 0.8, "max": 1 }, "comentario": "Sobreendeudamiento. Pérdida de autonomía financiera. Urgente reducir pasivos o capitalizar la empresa." },

    // APALANCAMIENTO FINANCIERO (Pasivo Total / Patrimonio)
    { "indicador": "apalancamiento_financiero", "rango_condicional": { "min": 0, "max": 1 }, "comentario": "Bajo apalancamiento. La empresa depende principalmente del capital propio. Nivel de riesgo muy bajo." },
    { "indicador": "apalancamiento_financiero", "rango_condicional": { "min": 1, "max": 2 }, "comentario": "Apalancamiento equilibrado. La deuda es moderada y bien soportada por el patrimonio." },
    { "indicador": "apalancamiento_financiero", "rango_condicional": { "min": 2, "max": 3 }, "comentario": "Apalancamiento óptimo. Se maximiza el uso de deuda para generar rentabilidad, con riesgo controlado." },
    { "indicador": "apalancamiento_financiero", "rango_condicional": { "min": 3, "max": 5 }, "comentario": "Apalancamiento alto. Dependencia significativa de financiación externa. Revisar capacidad de servicio de la deuda." },
    { "indicador": "apalancamiento_financiero", "rango_condicional": { "min": 5, "max": Infinity }, "comentario": "Apalancamiento excesivo. Alto riesgo para los accionistas. Urgente reestructurar pasivos y capital." },

    // MARGEN NETO DE UTILIDAD (Valores en porcentaje decimal: 5% = 0.05)
    { "indicador": "margen_neto_utilidad", "rango_condicional": { "min": -Infinity, "max": 0 }, "comentario": "Pérdidas netas. La empresa no es rentable; analizar estructura de costos y ventas." },
    { "indicador": "margen_neto_utilidad", "rango_condicional": { "min": 0, "max": 0.05 }, "comentario": "Margen muy bajo. Rentabilidad mínima; revisar eficiencia operativa." },
    { "indicador": "margen_neto_utilidad", "rango_condicional": { "min": 0.05, "max": 0.15 }, "comentario": "Margen moderado. Rentabilidad aceptable y sostenible." },
    { "indicador": "margen_neto_utilidad", "rango_condicional": { "min": 0.15, "max": 0.3 }, "comentario": "Margen alto. Excelente control de gastos y estrategia comercial." },
    { "indicador": "margen_neto_utilidad", "rango_condicional": { "min": 0.3, "max": Infinity }, "comentario": "Margen extraordinario. Posible ingreso no recurrente o alta eficiencia estructural." },

    // NUEVO: MARGEN BRUTO DE UTILIDAD (REEMPLAZO DE ROTACIÓN DE ACTIVOS)
    { "indicador": "margen_bruto_utilidad", "rango_condicional": { "min": -Infinity, "max": 0.2 }, "comentario": "Margen bruto crítico. La estructura de costos directos (Mcia/Producción) es demasiado alta, amenazando la sostenibilidad." },
    { "indicador": "margen_bruto_utilidad", "rango_condicional": { "min": 0.2, "max": 0.4 }, "comentario": "Margen bruto saludable. Buena rentabilidad en la operación principal, cubriendo costos directos adecuadamente." },
    { "indicador": "margen_bruto_utilidad", "rango_condicional": { "min": 0.4, "max": 0.6 }, "comentario": "Margen bruto fuerte. Estructura de costos directos optimizada, generando una excelente utilidad en las ventas." },
    { "indicador": "margen_bruto_utilidad", "rango_condicional": { "min": 0.6, "max": Infinity }, "comentario": "Margen bruto excepcional. Dominio del mercado o costos directos muy bajos. Gran potencial de rentabilidad neta." },

    // RENTABILIDAD PATRIMONIO (ROE)
    { "indicador": "rentabilidad_patrimonio", "rango_condicional": { "min": -Infinity, "max": 0 }, "comentario": "Pérdidas sobre patrimonio. El capital propio no genera retornos. Revisión urgente de la rentabilidad." },
    { "indicador": "rentabilidad_patrimonio", "rango_condicional": { "min": 0, "max": 0.05 }, "comentario": "Rentabilidad del patrimonio muy baja. Capital con retornos insuficientes." },
    { "indicador": "rentabilidad_patrimonio", "rango_condicional": { "min": 0.05, "max": 0.15 }, "comentario": "Rentabilidad del patrimonio moderada. Generación de riqueza aceptable para los propietarios." },
    { "indicador": "rentabilidad_patrimonio", "rango_condicional": { "min": 0.15, "max": 0.3 }, "comentario": "Rentabilidad del patrimonio fuerte. Excelente generación de riqueza para los propietarios." },
    { "indicador": "rentabilidad_patrimonio", "rango_condicional": { "min": 0.3, "max": Infinity }, "comentario": "Rentabilidad del patrimonio sobresaliente. Excepcional creación de valor para el capital propio." },

    // RENTABILIDAD DEL ACTIVO (ROA)
    { "indicador": "rentabilidad_activo", "rango_condicional": { "min": -Infinity, "max": 0 }, "comentario": "Pérdidas sobre activos. Los recursos invertidos no generan retorno; urgente revisión operativa." },
    { "indicador": "rentabilidad_activo", "rango_condicional": { "min": 0, "max": 0.05 }, "comentario": "Rentabilidad baja. Los activos producen retornos limitados." },
    { "indicador": "rentabilidad_activo", "rango_condicional": { "min": 0.05, "max": 0.1 }, "comentario": "Rentabilidad moderada. Gestión adecuada de recursos." },
    { "indicador": "rentabilidad_activo", "rango_condicional": { "min": 0.1, "max": 0.2 }, "comentario": "Rentabilidad fuerte. Uso eficiente de activos productivos." },
    { "indicador": "rentabilidad_activo", "rango_condicional": { "min": 0.2, "max": Infinity }, "comentario": "Rentabilidad sobresaliente. Excelente retorno sobre activos." },
];



/**
 * Función para buscar el comentario de análisis basado en el valor del ratio.
 */
const findAnalysis = (ratioId, value, ratiosConfig, kpisData) => {
    let search_value = ratioId === 'margen_neto_utilidad' || ratioId === 'margen_bruto_utilidad' || ratioId.startsWith('rentabilidad') || ratioId.startsWith('nivel')
        ? value / 100
        : value;

    if (isNaN(value) || value === Infinity || value === -Infinity) {
        return {
            comentario: "Anomalía de Datos: La división por cero (ej. Patrimonio Total $0) impide el cálculo.",
            ratioValue: 'N/A'
        };
    }

    const analysis = analysisRules.find(rule =>
        rule.indicador === ratioId &&
        search_value >= rule.rango_condicional.min &&
        search_value < rule.rango_condicional.max
    );

    const ratioConfig = ratiosConfig.find(r => r.id === ratioId);
    let ratioValue;

    if (ratioConfig) {
        if (ratioConfig.format === 'percent') {
            ratioValue = `${(value).toFixed(2)} %`;
        } else if (ratioConfig.format === 'ratio') {
            ratioValue = `${(value).toFixed(2)} ${ratioConfig.unit}`;
        } else {
            ratioValue = value.toFixed(2);
        }
    } else {
        ratioValue = value.toFixed(2);
    }

    return {
        comentario: analysis ? analysis.comentario : "Análisis no disponible para este rango o valor.",
        ratioValue: ratioValue
    };
};




/**
 * Lógica que renderiza los 9 Ratios Financieros con el nuevo diseño de tarjeta.
 * Este componente es el núcleo del nuevo módulo 'Análisis Financiero'.
 */
const RatiosDisplay = ({ kpisData }) => {
    if (!kpisData) {
        return (
            <div className="text-gray-500 p-4 bg-white rounded-lg shadow-inner">
                Seleccione un rango de fechas y presione "Ejecutar Análisis" para cargar el Tablero de Control Financiero.
            </div>
        );
    }

    const activoCorriente = parseFloat(kpisData.activo_corriente) || 0;
    const pasivoCorriente = parseFloat(kpisData.pasivo_corriente) || 0;
    const inventariosTotal = parseFloat(kpisData.inventarios_total) || 0;

    const capitalTrabajoNetoValue = activoCorriente - pasivoCorriente;
    const numeradorPruebaAcida = activoCorriente - inventariosTotal;

    const ratiosConfig = [
        // 1. Razón Corriente (Liquidez)
        {
            id: 'razon_corriente', title: "Razón Corriente (Liquidez)", max: 3.0, unit: 'x', goodRange: 'Meta: > 1.5x', icon: FaBalanceScale, format: 'ratio',
            mainData: 'activo_corriente', secondaryData: 'pasivo_corriente',
            mainLabel: 'Activo Corriente', secondaryLabel: 'Pasivo Corriente',
            colorLogic: (val) => val > 1.5 ? "text-green-600" : (val > 1.0 ? "text-blue-500" : "text-red-600")
        },

        // 2. Prueba Ácida (Liquidez Pura)
        {
            id: 'prueba_acida', title: "Prueba Ácida (Liquidez Inmediata)", max: 2.0, unit: 'x', goodRange: 'Meta: > 1.0x', icon: FaChartPie, format: 'ratio',
            mainData: 'prueba_acida', secondaryData: 'pasivo_corriente',
            mainLabel: 'Act. Corriente (sin Inv.)', secondaryLabel: 'Pasivo Corriente',
            colorLogic: (val) => val > 1.0 ? "text-green-600" : (val > 0.7 ? "text-blue-500" : "text-red-600")
        },

        // 3. Capital de Trabajo Neto (Valor Absoluto)
        {
            id: 'capital_trabajo_neto', title: "Capital de Trabajo Neto", format: 'currency', goodRange: 'Meta: > $0 (Positivo)', icon: FaMoneyCheckAlt, format: 'currency',
            mainData: 'activo_corriente', secondaryData: 'pasivo_corriente',
            mainLabel: 'Activo Corriente', secondaryLabel: 'Pasivo Corriente',
            colorLogic: (val) => val > 0 ? "text-green-600" : "text-red-600"
        },

        // 4. Nivel de Endeudamiento (Solvencia)
        {
            id: 'nivel_endeudamiento', title: "Nivel de Endeudamiento", max: 1.0, unit: '%', goodRange: 'Meta: < 50%', icon: FaPercentage, format: 'percent',
            mainData: 'pasivos_total', secondaryData: 'activos_total',
            mainLabel: 'Pasivo Total', secondaryLabel: 'Activo Total',
            colorLogic: (val) => val < 0.50 ? "text-green-600" : (val < 0.70 ? "text-blue-500" : "text-red-600")
        },

        // 5. Apalancamiento Financiero (Solvencia)
        {
            id: 'apalancamiento_financiero', title: "Apalancamiento (Deuda/Patrimonio)", max: 5.0, unit: 'x', goodRange: 'Meta: < 3.0x', icon: FaRedoAlt, format: 'ratio',
            mainData: 'pasivos_total', secondaryData: 'patrimonio_total',
            mainLabel: 'Pasivo Total', secondaryLabel: 'Patrimonio Total',
            colorLogic: (val) => val < 3.0 ? "text-green-600" : (val < 4.0 ? "text-blue-500" : "text-red-600")
        },

        // 6. Margen Neto Utilidad (Rentabilidad)
        {
            id: 'margen_neto_utilidad', title: "Margen Neto de Utilidad", max: 30, unit: '%', goodRange: 'Meta: > 5%', icon: FaChartArea, format: 'percent',
            mainData: 'utilidad_neta', secondaryData: 'ingresos_anuales',
            mainLabel: 'Utilidad Neta', secondaryLabel: 'Ingresos Anuales',
            colorLogic: (val) => val > 5 ? "text-green-600" : (val > 0 ? "text-blue-500" : "text-red-600")
        },

        // 7. Rentabilidad Patrimonio (ROE)
        {
            id: 'rentabilidad_patrimonio', title: "Rentabilidad Patrimonio (ROE)", max: 20, unit: '%', goodRange: 'Meta: > 10%', icon: FaChartLine, format: 'percent',
            mainData: 'utilidad_neta', secondaryData: 'patrimonio_total',
            mainLabel: 'Utilidad Neta', secondaryLabel: 'Patrimonio Total',
            colorLogic: (val) => val > 10 ? "text-green-600" : (val > 5 ? "text-blue-500" : "text-red-600")
        },

        // 8. Rentabilidad Activo (ROA)
        {
            id: 'rentabilidad_activo', title: "Rentabilidad Activo (ROA)", max: 15, unit: '%', goodRange: 'Meta: > 5%', icon: FaDollarSign, format: 'percent',
            mainData: 'utilidad_neta', secondaryData: 'activos_total',
            mainLabel: 'Utilidad Neta', secondaryLabel: 'Activo Total',
            colorLogic: (val) => val > 5 ? "text-green-600" : (val > 2 ? "text-blue-500" : "text-red-600")
        },

        // 9. MARGEN BRUTO DE UTILIDAD (REEMPLAZO DE ROTACIÓN DE ACTIVOS)
        {
            id: 'margen_bruto_utilidad', title: "Margen Bruto de Utilidad", max: 60, unit: '%', goodRange: 'Meta: > 20%', icon: FaMoneyBillWave, format: 'percent',
            mainData: 'ingresos_anuales', secondaryData: 'costo_ventas_total',
            mainLabel: 'Utilidad Bruta', secondaryLabel: 'Ingresos Anuales',
            colorLogic: (val) => val > 40 ? "text-green-600" : (val > 20 ? "text-blue-500" : "text-red-600")
        },
    ];

    // --- GENERACIÓN DEL ANÁLISIS TEXTUAL ---
    const analysisData = [];

    ratiosConfig.forEach((ratio) => {
        let value = parseFloat(kpisData[ratio.id]) || 0;

        if (ratio.id === 'capital_trabajo_neto') {
            value = capitalTrabajoNetoValue;
        }

        if ((ratio.id === 'apalancamiento_financiero' || ratio.id === 'rentabilidad_patrimonio') && parseFloat(kpisData.patrimonio_total) === 0) {
            const analysis = findAnalysis(ratio.id, value, ratiosConfig, kpisData);
            analysisData.push({
                indicador: ratio.id,
                title: ratio.title,
                comentario: `Anomalía Contable: La división por cero (Patrimonio Total = $${kpisData.patrimonio_total}) impide el análisis. Ingrese el capital social.`,
                ratioValue: analysis.ratioValue,
            });
            return;
        }

        const analysis = findAnalysis(ratio.id, value, ratiosConfig, kpisData);
        analysisData.push({
            indicador: ratio.id,
            title: ratio.title,
            comentario: analysis.comentario,
            ratioValue: analysis.ratioValue,
        });
    });
    // ------------------------------------------

    const escenarioGeneral = kpisData.escenario_general;
    const textoInterpretativo = kpisData.texto_interpretativo;
    const recomendacionesBreves = kpisData.recomendaciones_breves;


    return (
        <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-3 gap-6 mb-8">
                {ratiosConfig.map((ratio) => {
                    let value = parseFloat(kpisData[ratio.id]) || 0;

                    let mainValue, secondaryValue;

                    if (ratio.id === 'prueba_acida') {
                        mainValue = numeradorPruebaAcida;
                        secondaryValue = pasivoCorriente;
                    } else if (ratio.id === 'capital_trabajo_neto') {
                        value = capitalTrabajoNetoValue;
                        mainValue = activoCorriente;
                        secondaryValue = pasivoCorriente;
                    } else if (ratio.id === 'margen_bruto_utilidad') {
                        const ingresos = parseFloat(kpisData.ingresos_anuales) || 0;
                        const utilidadBrutaCalculada = ingresos - (parseFloat(kpisData.costo_ventas_total) || 0);
                        mainValue = utilidadBrutaCalculada;
                        secondaryValue = ingresos;
                        ratio.mainLabel = 'Utilidad Bruta';
                        ratio.secondaryLabel = 'Ingresos Anuales';
                    } else {
                        mainValue = parseFloat(kpisData[ratio.mainData]) || 0;
                        secondaryValue = parseFloat(kpisData[ratio.secondaryData]) || 0;
                    }

                    const colorClass = ratio.colorLogic(value);

                    return (
                        <FinancialIndicatorCard
                            key={ratio.id}
                            id={ratio.id}
                            title={ratio.title}
                            value={value}
                            max={ratio.max}
                            unit={ratio.unit}
                            goodRange={ratio.goodRange}
                            colorClass={colorClass}
                            format={ratio.format}
                            mainValue={mainValue}
                            secondaryValue={secondaryValue}
                            icon={ratio.icon}
                            mainLabel={ratio.mainLabel}
                            secondaryLabel={ratio.secondaryLabel}
                        />
                    );
                })}
            </div>

            <TextualAnalysis
                analysisData={analysisData}
                escenario={escenarioGeneral}
                interpretacion={textoInterpretativo}
                recomendaciones={recomendacionesBreves}
            />

        </>
    );
};


/**
 * Vista para Análisis Horizontal (Comparativo).
 */
const HorizontalAnalysisView = ({ user }) => {
    // Estado fechas
    const [p1Start, setP1Start] = useState('');
    const [p1End, setP1End] = useState('');
    const [p2Start, setP2Start] = useState('');
    const [p2End, setP2End] = useState('');

    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);

    // Valores por defecto: P1 = Año anterior, P2 = Año actual
    useEffect(() => {
        const today = new Date();
        const year = today.getFullYear();
        setP2Start(`${year}-01-01`);
        setP2End(today.toISOString().split('T')[0]);
        setP1Start(`${year - 1}-01-01`);
        setP1End(`${year - 1}-12-31`);
    }, []);

    const handleExecute = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const res = await getHorizontalAnalysis(p1Start, p1End, p2Start, p2End);
            setData(res);
            toast.success("Análisis Horizontal generado.");
        } catch (err) {
            toast.error("Error al generar análisis horizontal.");
        } finally {
            setLoading(false);
        }
    };

    const formatMoney = (val) => new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(val);
    const formatPct = (val) => val.toFixed(2) + '%';

    return (
        <div>
            <form onSubmit={handleExecute} className="mb-6 bg-white p-4 rounded shadow flex flex-wrap gap-4 items-end border-l-4 border-green-500">
                <div>
                    <span className="block text-xs font-bold text-gray-500 mb-1">Periodo 1 (Base/Anterior)</span>
                    <div className="flex gap-2">
                        <input type="date" value={p1Start} onChange={e => setP1Start(e.target.value)} className="border rounded p-1 text-sm" required />
                        <input type="date" value={p1End} onChange={e => setP1End(e.target.value)} className="border rounded p-1 text-sm" required />
                    </div>
                </div>
                <div>
                    <span className="block text-xs font-bold text-gray-500 mb-1">Periodo 2 (Actual/Comparar)</span>
                    <div className="flex gap-2">
                        <input type="date" value={p2Start} onChange={e => setP2Start(e.target.value)} className="border rounded p-1 text-sm" required />
                        <input type="date" value={p2End} onChange={e => setP2End(e.target.value)} className="border rounded p-1 text-sm" required />
                    </div>
                </div>
                <button type="submit" disabled={loading} className="bg-green-600 text-white px-4 py-1.5 rounded hover:bg-green-700 text-sm font-semibold h-9">
                    {loading ? 'Analizando...' : 'Comparar Periodos'}
                </button>
            </form>

            {data && (
                <div className="overflow-x-auto bg-white shadow rounded">
                    <table className="w-full text-sm">
                        <thead className="bg-gray-100 text-gray-700">
                            <tr>
                                <th className="p-2 text-left">Cuenta</th>
                                <th className="p-2 text-right">{data.periodo_1_texto}</th>
                                <th className="p-2 text-right">{data.periodo_2_texto}</th>
                                <th className="p-2 text-right">Var. Absoluta</th>
                                <th className="p-2 text-right">Var. Relativa (%)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data.items.map((row) => (
                                <tr key={row.codigo_cuenta} className={`border-b hover:bg-gray-50 ${row.es_titulo ? 'font-bold bg-gray-50' : ''}`}>
                                    <td className="p-2">
                                        <span style={{ paddingLeft: `${(row.nivel - 1) * 10}px` }}>
                                            {row.codigo_cuenta} - {row.nombre_cuenta}
                                        </span>
                                    </td>
                                    <td className="p-2 text-right">{formatMoney(row.saldo_periodo_1)}</td>
                                    <td className="p-2 text-right">{formatMoney(row.saldo_periodo_2)}</td>
                                    <td className={`p-2 text-right ${row.variacion_absoluta < 0 ? 'text-red-600' : 'text-green-600'}`}>
                                        {formatMoney(row.variacion_absoluta)}
                                    </td>
                                    <td className={`p-2 text-right ${row.variacion_relativa < 0 ? 'text-red-600' : 'text-green-600'}`}>
                                        {formatPct(row.variacion_relativa)}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};

/**
 * Vista para Análisis Vertical (Estructural).
 */
const VerticalAnalysisView = ({ user }) => {
    const [start, setStart] = useState('');
    const [end, setEnd] = useState('');
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const today = new Date();
        setStart(`${today.getFullYear()}-01-01`);
        setEnd(today.toISOString().split('T')[0]);
    }, []);

    const handleExecute = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const res = await getVerticalAnalysis(start, end);
            setData(res);
            toast.success("Análisis Vertical generado.");
        } catch (err) {
            toast.error("Error al generar análisis vertical.");
        } finally {
            setLoading(false);
        }
    };

    const formatMoney = (val) => new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(val);

    return (
        <div>
            <form onSubmit={handleExecute} className="mb-6 bg-white p-4 rounded shadow flex items-end gap-4 border-l-4 border-purple-500">
                <div>
                    <span className="block text-xs font-bold text-gray-500 mb-1">Periodo de Análisis</span>
                    <div className="flex gap-2">
                        <input type="date" value={start} onChange={e => setStart(e.target.value)} className="border rounded p-1 text-sm" required />
                        <input type="date" value={end} onChange={e => setEnd(e.target.value)} className="border rounded p-1 text-sm" required />
                    </div>
                </div>
                <button type="submit" disabled={loading} className="bg-purple-600 text-white px-4 py-1.5 rounded hover:bg-purple-700 text-sm font-semibold h-9">
                    {loading ? 'Calculando...' : 'Ver Estructura (%)'}
                </button>
            </form>

            {data && (
                <div className="overflow-x-auto bg-white shadow rounded">
                    <table className="w-full text-sm">
                        <thead className="bg-gray-100 text-gray-700">
                            <tr>
                                <th className="p-2 text-left">Cuenta</th>
                                <th className="p-2 text-right">Saldo</th>
                                <th className="p-2 text-right">% Participación</th>
                                <th className="p-2 text-left w-1/3">Visualización</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data.items.map((row) => (
                                <tr key={row.codigo_cuenta} className={`border-b hover:bg-gray-50 ${row.es_titulo ? 'font-bold bg-gray-50' : ''}`}>
                                    <td className="p-2">
                                        <span style={{ paddingLeft: `${(row.nivel - 1) * 10}px` }}>
                                            {row.codigo_cuenta} - {row.nombre_cuenta}
                                        </span>
                                    </td>
                                    <td className="p-2 text-right">{formatMoney(row.saldo_periodo_1)}</td>
                                    <td className="p-2 text-right font-mono">{row.porcentaje_participacion.toFixed(2)}%</td>
                                    <td className="p-2 align-middle">
                                        <div className="w-full bg-gray-200 rounded-full h-2.5">
                                            <div className="bg-purple-600 h-2.5 rounded-full" style={{ width: `${Math.min(Math.abs(row.porcentaje_participacion), 100)}%` }}></div>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};


/**
 * Componente Principal del Módulo de Análisis Financiero.
 * Gestiona Pestañas y Vistas.
 */
const FinancialAnalysisModule = ({ user }) => {
    // --- LÓGICA DE PESTAÑAS ---
    const [activeTab, setActiveTab] = useState('ratios');

    // --- LÓGICA DE RATIOS (Original) ---
    const today = new Date();
    const firstDayOfYear = new Date(today.getFullYear(), 0, 1);
    const [fechaInicio, setFechaInicio] = useState(firstDayOfYear.toISOString().split('T')[0]);
    const [fechaFin, setFechaFin] = useState(today.toISOString().split('T')[0]);
    const [kpisData, setKpisData] = useState(null);
    const [loadingRatios, setLoadingRatios] = useState(false);

    const fetchRatios = useCallback(async (start, end) => {
        setLoadingRatios(true);
        try {
            if (start && end) {
                const res = await getFinancialRatios(start, end);
                setKpisData(res);
            }
        } catch (err) {
            toast.error("Error al cargar indicadores.");
        } finally {
            setLoadingRatios(false);
        }
    }, []);

    // Carga inicial de Ratios
    useEffect(() => {
        if (activeTab === 'ratios' && !kpisData) {
            fetchRatios(fechaInicio, fechaFin);
        }
    }, [activeTab, fetchRatios, fechaInicio, fechaFin, kpisData]);

    const handleExecuteRatios = (e) => {
        e.preventDefault();
        fetchRatios(fechaInicio, fechaFin);
    };

    return (
        <div className="p-6 w-full fade-in">
            <h1 className="text-2xl font-light text-slate-800 mb-6 flex items-center">
                <FaChartArea className="mr-3 text-blue-600" /> Análisis Financiero Integral
            </h1>

            {/* --- NAVEGACIÓN DE PESTAÑAS --- */}
            <div className="flex border-b border-gray-200 mb-6">
                <button
                    className={`px-6 py-3 font-medium text-sm focus:outline-none ${activeTab === 'ratios' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
                    onClick={() => setActiveTab('ratios')}
                >
                    Indicadores (Ratios)
                </button>
                <button
                    className={`px-6 py-3 font-medium text-sm focus:outline-none ${activeTab === 'horizontal' ? 'border-b-2 border-green-500 text-green-600' : 'text-gray-500 hover:text-gray-700'}`}
                    onClick={() => setActiveTab('horizontal')}
                >
                    Análisis Horizontal
                </button>
                <button
                    className={`px-6 py-3 font-medium text-sm focus:outline-none ${activeTab === 'vertical' ? 'border-b-2 border-purple-500 text-purple-600' : 'text-gray-500 hover:text-gray-700'}`}
                    onClick={() => setActiveTab('vertical')}
                >
                    Análisis Vertical
                </button>
            </div>

            {/* --- CONTENIDO DE PESTAÑAS --- */}

            {/* TAB 1: RATIOS (Código Original Optimizado) */}
            {activeTab === 'ratios' && (
                <div>
                    <form onSubmit={handleExecuteRatios} className="bg-white p-4 items-center rounded shadow-sm mb-6 flex gap-4 border-l-4 border-blue-500">
                        <span className="font-semibold text-sm text-gray-600">Periodo:</span>
                        <input type="date" value={fechaInicio} onChange={e => setFechaInicio(e.target.value)} className="border rounded p-1 text-sm" />
                        <span className="text-gray-400">-</span>
                        <input type="date" value={fechaFin} onChange={e => setFechaFin(e.target.value)} className="border rounded p-1 text-sm" />
                        <button type="submit" disabled={loadingRatios} className="bg-blue-600 text-white px-4 py-1 rounded hover:bg-blue-700 text-sm">
                            {loadingRatios ? '...' : 'Actualizar'}
                        </button>
                    </form>
                    <RatiosDisplay kpisData={kpisData} />
                </div>
            )}

            {/* TAB 2: HORIZONTAL */}
            {activeTab === 'horizontal' && <HorizontalAnalysisView user={user} />}

            {/* TAB 3: VERTICAL */}
            {activeTab === 'vertical' && <VerticalAnalysisView user={user} />}

        </div>
    );
};



/**
 * Componente que renderiza el contenido del Módulo 'Favoritos' (QuickAccessGrid reubicado).
 */
const FavoritesModule = ({ user, router }) => {
    const [favoritos, setFavoritos] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        setLoading(true);
        getFavoritos().then(res => {
            setFavoritos(res);
            setLoading(false);
        }).catch(err => {
            console.error("Error al cargar favoritos:", err);
            toast.error(`Fallo al cargar favoritos: ${err.message || "Verifique la conexión."}`);
            setLoading(false);
        });
    }, []);

    if (loading && favoritos.length === 0) {
        return (
            <div className="p-6 w-full h-full flex items-center justify-center">
                <span className="loading loading-spinner loading-lg text-blue-500"></span>
                <p className="text-gray-500 ml-3">Cargando accesos rápidos...</p>
            </div>
        );
    }

    return (
        <div className="p-6 w-full">
            {/* --- AQUÍ INSERTAMOS EL WIDGET DE CONSUMO --- */}
            <div className="mb-8">
                <ConsumoWidget />
            </div>
            {/* -------------------------------------------- */}

            <QuickAccessGrid favoritos={favoritos} router={router} />
        </div>
    );
};


// =============================================================
// III. NÚCLEO DEL EXPLORADOR: Vistas dinámicas y Layout principal
// =============================================================

/**
 * Componente que renderiza el contenido dinámico del módulo seleccionado.
 * Implementa la lógica de 2 Niveles para Administración y Configuración.
 */
const ExplorerView = ({ activeModuleId, router }) => {

    // 1. Encontrar la configuración del módulo activo
    const module = useMemo(() => menuStructure.find(m => m.id === activeModuleId), [activeModuleId]);

    // Estado local para manejar la exploración de subgrupos (Nivel 2)
    const [activeSubgroup, setActiveSubgroup] = useState(null);

    // Resetear el subgrupo cuando se cambia de módulo principal
    useEffect(() => {
        setActiveSubgroup(null);
    }, [activeModuleId]);


    if (!module) {
        return (
            <div className="p-8 text-center text-red-500">
                <FaExclamationTriangle size={40} className="mx-auto mb-4" />
                <h1 className="text-xl font-bold">Error de Navegación</h1>
                <p>El módulo seleccionado no se encuentra en la estructura de menú.</p>
            </div>
        );
    }

    // 2. Módulos con Vistas Especiales (Análisis Financiero / Favoritos)
    if (module.id === 'analisis_financiero') {
        return <FinancialAnalysisModule />;
    }

    if (module.id === 'favoritos') {
        return <FavoritesModule router={router} />;
    }

    // --- Lógica Especial para ADMINISTRACIÓN Y CONFIGURACIÓN ---
    if (module.id === 'administracion') {

        // Nivel de Exploración: Subgrupos (ej. Parametrización Maestra, Control y Cierre)
        if (!activeSubgroup) {

            return (
                <div className="p-6 w-full">
                    <h2 className="text-2xl font-light text-slate-800 mb-6">
                        Selecciona un Área de Configuración
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {module.subgroups.map(subgroup => (
                            <ModuleTile
                                key={subgroup.title}
                                title={subgroup.title}
                                description="Haz clic para ver las opciones de gestión."
                                icon={subgroup.icon || FaFolder}
                                isFolder={true}
                                onClick={() => setActiveSubgroup(subgroup)}
                            />
                        ))}
                    </div>
                </div>
            );
        }

        // Nivel de Exploración: Enlaces Finales (después de seleccionar un subgrupo)
        const currentSubgroup = activeSubgroup; // Usamos la copia del estado
        return (
            <div className="p-6 w-full">

                {/* Botón de regreso a la vista principal de Administración */}
                <button
                    onClick={() => setActiveSubgroup(null)}
                    className="flex items-center text-blue-600 hover:text-blue-800 font-semibold mb-6 transition duration-150"
                >
                    <FaArrowLeft className="mr-2" /> Volver a Administración
                </button>

                <h2 className="text-2xl font-light text-slate-800 mb-6 flex items-center">
                    <currentSubgroup.icon size={24} className="mr-3 text-blue-500" />
                    {currentSubgroup.title}
                </h2>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {currentSubgroup.links.map(link => (
                        <Link key={link.href} href={link.href} passHref>
                            <ModuleTile
                                title={link.name}
                                description={`Ir a: ${link.name}`}
                                icon={link.icon || FaFile}
                                onClick={() => router.push(link.href)}
                            />
                        </Link>
                    ))}
                </div>
            </div>
        );
    }

    // --- Lógica para el resto de módulos (Nivel Único de Enlaces) ---
    const explorerItems = module.links || [];

    return (
        <div className="p-6 w-full">
            <h1 className="text-2xl font-light text-slate-800 mb-6 flex items-center">
                <module.icon className="w-6 h-6 mr-3 text-blue-500" />
                Explorador de Módulos: <strong className="font-semibold ml-2">{module.name}</strong>
            </h1>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">

                {explorerItems.map((link) => (
                    <Link key={link.href} href={link.href} passHref>
                        <ModuleTile
                            title={link.name}
                            description={`Ir a: ${link.name}`}
                            icon={link.icon || FaFile}
                            onClick={() => router.push(link.href)}
                        />
                    </Link>
                ))}
            </div>
        </div>
    );
};


/**
 * El Componente Principal que define el Layout de la aplicación.
 */
function HomePageContent() {
    const { user, logout, loading: authLoading } = useAuth();
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [activeModuleId, setActiveModuleId] = useState('favoritos');
    const router = useRouter();
    const searchParams = useSearchParams();

    // --- LOGIC TO READ URL PARAMS ---
    useEffect(() => {
        const moduleParam = searchParams.get('module');
        if (moduleParam) {
            setActiveModuleId(moduleParam);
        }
    }, [searchParams]);

    if (authLoading) {
        return (
            <main className="flex min-h-screen items-center justify-center bg-gray-50">
                <div className="text-center">
                    <span className="loading loading-spinner loading-lg text-primary"></span>
                    <p className="text-gray-500 mt-2">Cargando sesión...</p>
                </div>
            </main>
        );
    }

    if (!user) {
        // Vista para usuarios no autenticados
        return (
            <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gray-100">
                <div className="w-full max-w-md text-center bg-white p-10 rounded-xl shadow-2xl">
                    <h1 className="text-4xl font-extrabold text-blue-600 mb-4">Finaxis</h1>
                    <p className="mt-4 text-lg text-gray-600">Tu Sistema Finaxis ERP. Por favor, inicia sesión para acceder.</p>
                    <div className="mt-8 flex justify-center gap-4">
                        <Link href="/login" className="btn btn-primary btn-lg shadow-lg">Iniciar Sesión</Link>
                        <Link href="/register" className="btn btn-outline btn-lg">Registrarse</Link>
                    </div>
                </div>
            </main>
        );
    }

    // Manejador de clics en el menú principal (Sidebar)
    const handleMenuClick = (moduleId) => {
        if (isMenuOpen) {
            setIsMenuOpen(false);
        }

        const module = menuStructure.find(m => m.id === moduleId);
        if (module && module.route) {
            router.push(module.route);
        } else {
            setActiveModuleId(moduleId);
            // Optional: Update URL without reloading to keep state shareable
            // router.replace(`/?module=${moduleId}`, undefined, { shallow: true });
        }
    };

    // Vista para usuarios autenticados
    return (
        <div className="flex h-screen bg-gray-100">
            {/* Botón de Menú para móvil */}
            <button
                className="p-4 text-blue-600 fixed top-0 left-0 z-40 md:hidden"
                onClick={() => setIsMenuOpen(true)}
            >
                <FaBars size={24} />
            </button>

            {/* --- Columna Izquierda: Sidebar (Menú Principal) --- */}
            <Sidebar
                activeModuleId={activeModuleId}
                onMenuClick={handleMenuClick}
                isMenuOpen={isMenuOpen}
                setIsMenuOpen={setIsMenuOpen}
                user={user}
                logout={logout}
            />

            {/* --- Columna Derecha: Contenido Principal (El Explorador Dinámico) --- */}
            <div className="flex-1 flex flex-col overflow-hidden">
                <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-start px-6 shadow-sm">
                    <div className="text-2xl font-light text-slate-800">
                        {menuStructure.find(m => m.id === activeModuleId)?.name || 'Explorador'}
                    </div>
                </header>

                <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50">
                    <ExplorerView
                        activeModuleId={activeModuleId}
                        router={router}
                    />
                </main>
            </div>

        </div>
    );
}

export default function HomePage() {
    return (
        <Suspense fallback={<div>Loading...</div>}>
            <HomePageContent />
        </Suspense>
    );
}