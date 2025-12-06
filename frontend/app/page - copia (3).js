// frontend/app/page.js (REEMPLAZO COMPLETO FINAL - MARGEN BRUTO DE UTILIDAD)
'use client';

import { useAuth } from './context/AuthContext';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import React, { useState, useMemo, useEffect, useCallback } from 'react';

// Importamos TODOS los íconos necesarios 
import { 
    FaBars, FaTimes, FaHome, FaCalculator, FaChartLine, FaBoxes, FaCog, 
    FaUsers, FaSignOutAlt, FaPercentage, FaFileAlt, FaChartBar, FaWrench, 
    FaFileContract, FaBook, FaListUl, FaPlus, FaClipboardList, FaHandshake, 
    FaUniversity, FaReceipt, FaTruckMoving, FaMoneyBill, FaTools, 
    FaGg, FaRedoAlt, FaBalanceScale, FaChartPie, FaChartArea, FaDollarSign, FaMoneyCheckAlt,
    FaExclamationTriangle, FaCheckCircle, FaExclamationCircle, FaSkullCrossbones, FaArrowUp, FaMoneyBillWave // Nuevo ícono para Margen Bruto
} from 'react-icons/fa';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css'; 

// --- Importación de Componentes CRÍTICOS ---
import QuickAccessGrid from './components/QuickAccessGrid'; 

// --- Servicios Frontend ---
import { getFinancialRatios } from '../lib/dashboardService'; 
import { getFavoritos } from '../lib/favoritosService';       

// =============================================================
// I. DATA: Estructura Jerárquica del Menú (Mantenido)
// =============================================================

export const menuStructure = [ 
  // [CÓDIGO DE menuStructure] (Se mantiene sin cambios)
    {
    name: "Contabilidad General",
    icon: FaCalculator,
    links: [
      { name: "Crear Documento", href: "/contabilidad/documentos" },
      { name: "Captura Rápida", href: "/contabilidad/captura-rapida" },
      { name: "Explorador de Documentos", href: "/contabilidad/explorador" },
      { name: "Libro Diario", href: "/contabilidad/reportes/libro-diario" },
      { name: "Balance General", href: "/contabilidad/reportes/balance-general" },
      { name: "Estado de Resultados", href: "/contabilidad/reportes/estado-resultados" },
      { name: "Balance de Prueba", href: "/contabilidad/reportes/balance-de-prueba" },
      { name: "Reporte Auxiliar", href: "/contabilidad/reportes/auxiliar-cuenta" },
      { name: "Libros Oficiales (PDF)", href: "/admin/utilidades/libros-oficiales" },
      { name: "Auditoría Avanzada (Super Informe)", href: "/contabilidad/reportes/super-informe" },
    ]
  },
  {
    name: "Centros de Costo",
    icon: FaChartBar,
    links: [
      { name: "Gestionar C. de Costo", href: "/admin/centros-costo" },
      { name: "Auxiliar por CC y Cuenta", href: "/contabilidad/reportes/auxiliar-cc-cuenta" },
      { name: "Balance General por CC", href: "/contabilidad/reportes/balance-general-cc" },
      { name: "Estado Resultados por CC", href: "/contabilidad/reportes/estado-resultados-cc-detallado" },
      { name: "Balance de Prueba por CC", href: "/contabilidad/reportes/balance-de-prueba-cc" },
    ]
  },
  {
    name: "Terceros",
    icon: FaUsers,
    links: [
      { name: "Gestionar Terceros", href: "/admin/terceros" },
      { name: "Auxiliar por Tercero", href: "/contabilidad/reportes/tercero-cuenta" },
      { name: "Cartera", href: "/contabilidad/reportes/estado-cuenta-cliente" },
      { name: "Auxiliar de Cartera", href: "/contabilidad/reportes/auxiliar-cartera" },
      { name: "Proveedores", href: "/contabilidad/reportes/estado-cuenta-proveedor" },
      { name: "Auxiliar Proveedores", href: "/contabilidad/reportes/auxiliar-proveedores" },
      { name: "Gestión Ventas (Cartera)", href: "/contabilidad/reportes/gestion-ventas" },
    ]
  },
  {
    name: "Inventario y Logística",
    icon: FaBoxes,
    links: [
      { name: "Gestión de Inventario (Productos)", href: "/admin/inventario" },
      { name: "Parámetros Inventario", href: "/admin/inventario/parametros" },
      { name: "Gestión Compras", href: "/contabilidad/compras" },
      { name: "Facturación", href: "/contabilidad/facturacion" },
      { name: "Traslado Inventarios", href: "/contabilidad/traslados" },
      { name: "Ajustes Inventario", href: "/admin/inventario/ajuste-inventario" },
      { name: "Estado Inventarios", href: "/contabilidad/reportes/estado-inventarios" },
      { name: "Rentabilidad Producto", href: "/contabilidad/reportes/rentabilidad-producto" },
      { name: "Estado General y Movimientos", href: "/contabilidad/reportes/movimiento-analitico" },
      { name: "Super Informe Inventarios", href: "/contabilidad/reportes/super-informe-inventarios" },

      { name: "Gestión Topes", href: "/contabilidad/reportes/gestion-topes" },
      

    ]
  },
  {
    name: "Administración y Configuración",
    icon: FaCog,
    subgroups: [
      { 
        title: "Parametrización Maestra", 
        icon: FaFileContract, 
        links: [
          { name: "Gestionar PUC", href: "/admin/plan-de-cuentas" },
          { name: "Gestionar Tipos de Doc.", href: "/admin/tipos-documento" },
          { name: "Gestionar Plantillas", href: "/admin/plantillas" },
          { name: "Gestionar Conceptos", href: "/admin/utilidades/gestionar-conceptos" },
          { name: "Gestionar Empresas", href: "/admin/empresas" },
        ]
      },
      { 
        title: "Control y Cierre", 
        icon: FaBook, 
        links: [
          { name: "Copias y Restauración", href: "/admin/utilidades/migracion-datos" },
          { name: "Cerrar Periodos Contables", href: "/admin/utilidades/periodos-contables" },
          { name: "Auditoría Consecutivos", href: "/admin/utilidades/auditoria-consecutivos" },
        ]
      },
      { 
        title: "Herramientas Avanzadas", 
        icon: FaWrench, 
        links: [
          { name: "Gestión Avanzada y Utilitarios", href: "/admin/utilidades/soporte-util" },
          { name: "Edición de Documentos", href: "/admin/utilidades/eliminacion-masiva" },
          { name: "Erradicador de Documentos", href: "/admin/utilidades/erradicar-documento" },
          { name: "Recodificación Masiva", href: "/admin/utilidades/recodificacion-masiva" },
          { name: "Papelera de Reciclaje", href: "/admin/utilidades/papelera" },
        ]
      },
    ]
  }
];

// =============================================================
// II. COMPONENTES: Sidebar y Dashboard
// =============================================================

/**
 * Componente funcional que muestra el menú lateral jerárquico. (Mantenido)
 */
const SidebarMenu = ({ menuItems, isMenuOpen, setIsMenuOpen }) => {
  const [openModule, setOpenModule] = useState(null);
  const [openSubGroup, setOpenSubGroup] = useState(null); 
  const router = useRouter();

  const toggleModule = (name) => {
    setOpenModule(openModule === name ? null : name);
    setOpenSubGroup(null); 
  };

  const toggleSubGroup = (title) => {
    setOpenSubGroup(openSubGroup === title ? null : title);
  };

  const handleLinkClick = (href) => {
    router.push(href);
    setIsMenuOpen(false);
  };

  return (
    <>
      <button 
        className="text-white absolute top-4 right-4 z-50 md:hidden" 
        onClick={() => setIsMenuOpen(false)}
      >
        <FaTimes size={20} />
      </button>

      <nav className="flex flex-col space-y-1 p-4 w-full">
        <h2 className="text-sm font-bold uppercase tracking-wider text-blue-400 mb-4">MENÚ SAP-LIKE</h2>
        
        <button 
          onClick={() => handleLinkClick('/')}
          className="flex items-center space-x-3 p-2 rounded-lg text-white hover:bg-blue-600 transition duration-150 bg-blue-500 font-semibold"
        >
          <FaHome size={16} />
          <span>Inicio / Dashboard</span>
        </button>

        {menuItems.map((module) => (
          <div key={module.name} className="mt-2">
            <button
              onClick={() => toggleModule(module.name)}
              className="flex items-center w-full p-2 rounded-lg text-blue-100 font-medium hover:bg-blue-700 transition duration-150 space-x-3 text-left"
            >
              <module.icon size={16} />
              <span>{module.name}</span>
              <span className="ml-auto">
                {openModule === module.name ? '▲' : '▼'}
              </span>
            </button>

            {openModule === module.name && (
              <div className="pt-1 flex flex-col space-y-1 bg-slate-700 rounded-b-lg">
                
                {module.subgroups && module.subgroups.map((subgroup) => (
                  <div key={subgroup.title} className="w-full">
                    <button
                      onClick={() => toggleSubGroup(subgroup.title)}
                      className="flex items-center w-full p-2 text-sm text-yellow-300 font-semibold hover:bg-slate-600 transition duration-150 space-x-2 text-left border-b border-slate-600"
                    >
                      <subgroup.icon size={14} className="opacity-70"/>
                      <span>{subgroup.title}</span>
                      <span className="ml-auto">
                        {openSubGroup === subgroup.title ? '−' : '+'}
                      </span>
                    </button>
                    
                    {openSubGroup === subgroup.title && (
                      <div className="flex flex-col space-y-1 bg-slate-600">
                        {subgroup.links.map((link) => (
                          <button
                            key={link.href}
                            onClick={() => handleLinkClick(link.href)}
                            className="flex items-center p-2 pl-8 text-sm rounded-none text-white hover:bg-blue-600 transition duration-150 text-left w-full"
                          >
                            {link.name}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                ))}

                {module.links && module.links.map((link) => (
                  <button
                    key={link.href}
                    onClick={() => handleLinkClick(link.href)}
                    className="flex items-center p-2 pl-6 text-sm rounded-none text-white hover:bg-blue-600 transition duration-150 text-left w-full"
                  >
                    {link.name}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </nav>
    </>
  );
};

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

    // Usamos 'Azul' para la zona neutra y se reemplaza 'orange-500' (en el colorLogic) por 'blue-500'
    const colorStyle = colorClass.replace('text-red-600', 'text-red-600').replace('text-green-600', 'text-green-600').replace('text-orange-500', 'text-blue-500');

    return (
        <div className="bg-white p-5 rounded-xl shadow-lg border-l-4 border-gray-200 transition duration-300 hover:shadow-xl">
            
            {/* Cabecera del Indicador */}
            <div className="flex items-center justify-between mb-3">
                <p className="text-sm font-semibold uppercase tracking-wider text-gray-500">
                    {title}
                </p>
                <Icon className={`w-6 h-6 ${colorStyle}`} />
            </div>

            {/* Valor Principal (Razón/Ratio) */}
            <div className="flex items-baseline mb-2">
                <p className={`text-4xl font-extrabold ${colorStyle}`}>
                    {ratioDisplay}
                </p>
                <span className={`ml-2 text-base font-semibold ${colorStyle}`}>
                    {unit === '%' ? '' : unit} 
                </span>
            </div>

            {/* Valores Monetarios y Semáforo */}
            <div className="mt-4 border-t pt-3 border-gray-100">
                {/* LÍNEA DE SOPORTE SUPERIOR (NUMERADOR) */}
                <div className="flex justify-between text-sm font-medium text-gray-700">
                    <span>{mainLabel}:</span>
                    <span className="text-gray-800 font-bold">{mainDisplay}</span>
                </div>
                {/* LÍNEA DE SOPORTE INFERIOR (DENOMINADOR) */}
                <div className="flex justify-between text-sm text-gray-600">
                    <span>{secondaryLabel}:</span>
                    <span className="text-gray-800 font-bold">{secondaryDisplay}</span>
                </div>
                
                {/* Meta y Semáforo (Nuevo Estilo) */}
                <p className={`mt-2 text-xs font-semibold ${colorStyle}`}>
                    Desempeño: {goodRange}
                </p>
            </div>
        </div>
    );
};


/**
 * NUEVO Componente para mostrar el análisis textual cualitativo.
 * REFATORIZADO para mostrar el Diagnóstico SEEE (Escenario General)
 */
const TextualAnalysis = ({ analysisData, escenario, interpretacion, recomendaciones }) => {
    if (!escenario) return null;

    // 1. Configuración de Iconos y Estilos para el Escenario General (1 a 5)
    const escenarioConfig = {
        1: { name: 'ÓPTIMO (Sólido y eficiente)', icon: FaArrowUp, color: 'border-green-600 text-green-600', iconColor: 'text-green-600' }, // FIX: Usando FaArrowUp
        2: { name: 'ESTABLE (Sano, pero con márgenes ajustados)', icon: FaCheckCircle, color: 'border-blue-500 text-blue-500', iconColor: 'text-blue-500' },
        3: { name: 'VIGILANCIA (Equilibrio frágil)', icon: FaExclamationTriangle, color: 'border-yellow-500 text-yellow-500', iconColor: 'text-yellow-500' },
        4: { name: 'RIESGO (Desequilibrio financiero)', icon: FaExclamationCircle, color: 'border-orange-500 text-orange-500', iconColor: 'text-orange-500' },
        5: { name: 'CRÍTICO (Insolvencia o pérdida de capital)', icon: FaSkullCrossbones, color: 'border-red-600 text-red-600', iconColor: 'text-red-600' },
    };
    
    const config = escenarioConfig[escenario] || escenarioConfig[3]; // Fallback a Vigilancia

    // Mapeo de Emojis/Iconos para el análisis individual
    const analysisIcons = {
        'razon_corriente': '💧 Liquidez',
        'prueba_acida': '⚡ Liquidez Inmediata',
        'capital_trabajo_neto': '💼 Capital de Trabajo',
        'nivel_endeudamiento': '💣 Endeudamiento',
        'apalancamiento_financiero': '⚙️ Apalancamiento',
        'margen_neto_utilidad': '💵 Margen Neto',
        'margen_bruto_utilidad': '💰 Margen Bruto', // NUEVO ÍCONO
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

            {/* INTERPRETACIÓN NARRATIVA CRUZADA */}
            <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-700 mb-2">Análisis Narrativo del SEEE:</h3>
                <p className="text-gray-600 italic whitespace-pre-wrap">{interpretacion}</p>
            </div>

            {/* RECOMENDACIONES AUTOMÁTICAS */}
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

            {/* ANÁLISIS INDIVIDUAL (Detalle de cada ratio) */}
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


// =============================================================
// LÓGICA DEL MOTOR DE ANÁLISIS AFAM 
// =============================================================

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
    { "indicador": "capital_trabajo_neto", "rango_condicional": { "min": 50000000, "max": Infinity }, "comentario": "Exceso de capital de trabajo. Recursos ociosos; se recomienda evaluar inversión productiva en proyectos rentables." },

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
    
    // NUEVO: MARGEN BRUTO DE UTILIDAD (Valores en porcentaje decimal: 5% = 0.05)
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
    // Caso especial: convertimos de porcentaje a decimal para la búsqueda en el rango
    let search_value = ratioId === 'margen_neto_utilidad' || ratioId === 'margen_bruto_utilidad' || ratioId.startsWith('rentabilidad') || ratioId.startsWith('nivel') 
                       ? value / 100 
                       : value;
    
    // Tratamos valores que causan división por cero o infinitos
    if (isNaN(value) || value === Infinity || value === -Infinity) {
        // Fallback de anomalía contable
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

    // Formatear el valor del ratio para el display
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
 */
const RatiosDisplay = ({ kpisData }) => { 
    if (!kpisData) {
        return (
            <div className="text-gray-500 p-4 bg-white rounded-lg shadow-inner">
                Seleccione un rango de fechas y presione "Ejecutar" para ver el Tablero de Control Financiero.
            </div>
        );
    }

    // Obtener valores brutos para cálculos derivados en el Frontend
    const activoCorriente = parseFloat(kpisData.activo_corriente) || 0;
    const pasivoCorriente = parseFloat(kpisData.pasivo_corriente) || 0;
    const inventariosTotal = parseFloat(kpisData.inventarios_total) || 0;
    
    // --- FIX CRÍTICO 1: Capital de Trabajo Neto ---
    const capitalTrabajoNetoValue = activoCorriente - pasivoCorriente;

    // --- FIX CRÍTICO 2: Prueba Ácida (Valor de Soporte Monetario - Numerador) ---
    const numeradorPruebaAcida = activoCorriente - inventariosTotal;


    // Configuración y lógica Tricolor para los 9 Ratios
    // El 9no ratio (ROTACIÓN DE ACTIVOS) ha sido reemplazado por MARGEN BRUTO DE UTILIDAD en el Schema/Backend
    const ratiosConfig = [
        // 1. Razón Corriente (Liquidez)
        { id: 'razon_corriente', title: "Razón Corriente (Liquidez)", max: 3.0, unit: 'x', goodRange: 'Meta: > 1.5x', icon: FaBalanceScale, format: 'ratio', 
          mainData: 'activo_corriente', secondaryData: 'pasivo_corriente',
          mainLabel: 'Activo Corriente', secondaryLabel: 'Pasivo Corriente',
          colorLogic: (val) => val > 1.5 ? "text-green-600" : (val > 1.0 ? "text-blue-500" : "text-red-600") },
        
        // 2. Prueba Ácida (Liquidez Pura)
        { id: 'prueba_acida', title: "Prueba Ácida (Liquidez Inmediata)", max: 2.0, unit: 'x', goodRange: 'Meta: > 1.0x', icon: FaChartPie, format: 'ratio', 
          mainData: 'prueba_acida', secondaryData: 'pasivo_corriente', 
          mainLabel: 'Act. Corriente (sin Inv.)', secondaryLabel: 'Pasivo Corriente',
          colorLogic: (val) => val > 1.0 ? "text-green-600" : (val > 0.7 ? "text-blue-500" : "text-red-600") },
        
        // 3. Capital de Trabajo Neto (Valor Absoluto)
        { id: 'capital_trabajo_neto', title: "Capital de Trabajo Neto", format: 'currency', goodRange: 'Meta: > $0 (Positivo)', icon: FaMoneyCheckAlt, format: 'currency', 
          mainData: 'activo_corriente', secondaryData: 'pasivo_corriente', 
          mainLabel: 'Activo Corriente', secondaryLabel: 'Pasivo Corriente',
          colorLogic: (val) => val > 0 ? "text-green-600" : "text-red-600" },
        
        // 4. Nivel de Endeudamiento (Solvencia)
        { id: 'nivel_endeudamiento', title: "Nivel de Endeudamiento", max: 1.0, unit: '%', goodRange: 'Meta: < 50%', icon: FaPercentage, format: 'percent', 
          mainData: 'pasivos_total', secondaryData: 'activos_total',
          mainLabel: 'Pasivo Total', secondaryLabel: 'Activo Total',
          colorLogic: (val) => val < 0.50 ? "text-green-600" : (val < 0.70 ? "text-blue-500" : "text-red-600") },
        
        // 5. Apalancamiento Financiero (Solvencia)
        { id: 'apalancamiento_financiero', title: "Apalancamiento (Deuda/Patrimonio)", max: 5.0, unit: 'x', goodRange: 'Meta: < 3.0x', icon: FaRedoAlt, format: 'ratio', 
          mainData: 'pasivos_total', secondaryData: 'patrimonio_total',
          mainLabel: 'Pasivo Total', secondaryLabel: 'Patrimonio Total',
          colorLogic: (val) => val < 3.0 ? "text-green-600" : (val < 4.0 ? "text-blue-500" : "text-red-600") },
          
        // 6. Margen Neto Utilidad (Rentabilidad)
        { id: 'margen_neto_utilidad', title: "Margen Neto de Utilidad", max: 30, unit: '%', goodRange: 'Meta: > 5%', icon: FaChartArea, format: 'percent', 
          mainData: 'utilidad_neta', secondaryData: 'ingresos_anuales',
          mainLabel: 'Utilidad Neta', secondaryLabel: 'Ingresos Anuales',
          colorLogic: (val) => val > 5 ? "text-green-600" : (val > 0 ? "text-blue-500" : "text-red-600") },
        
        // 7. Rentabilidad Patrimonio (ROE)
        { id: 'rentabilidad_patrimonio', title: "Rentabilidad Patrimonio (ROE)", max: 20, unit: '%', goodRange: 'Meta: > 10%', icon: FaChartLine, format: 'percent', 
          mainData: 'utilidad_neta', secondaryData: 'patrimonio_total',
          mainLabel: 'Utilidad Neta', secondaryLabel: 'Patrimonio Total',
          colorLogic: (val) => val > 10 ? "text-green-600" : (val > 5 ? "text-blue-500" : "text-red-600") },
        
        // 8. Rentabilidad Activo (ROA)
        { id: 'rentabilidad_activo', title: "Rentabilidad Activo (ROA)", max: 15, unit: '%', goodRange: 'Meta: > 5%', icon: FaDollarSign, format: 'percent', 
          mainData: 'utilidad_neta', secondaryData: 'activos_total',
          mainLabel: 'Utilidad Neta', secondaryLabel: 'Activo Total',
          colorLogic: (val) => val > 5 ? "text-green-600" : (val > 2 ? "text-blue-500" : "text-red-600") },
        
        // 9. MARGEN BRUTO DE UTILIDAD (REEMPLAZO DE ROTACIÓN DE ACTIVOS)
        { id: 'margen_bruto_utilidad', title: "Margen Bruto de Utilidad", max: 60, unit: '%', goodRange: 'Meta: > 20%', icon: FaMoneyBillWave, format: 'percent', 
          mainData: 'ingresos_anuales', secondaryData: 'costo_ventas_total', // El backend envía costo_ventas_total ampliado
          mainLabel: 'Utilidad Bruta', secondaryLabel: 'Ingresos Anuales',
          colorLogic: (val) => val > 40 ? "text-green-600" : (val > 20 ? "text-blue-500" : "text-red-600") },
    ];

// --- GENERACIÓN DEL ANÁLISIS TEXTUAL ---
    const analysisData = [];
    
    ratiosConfig.forEach((ratio) => {
        let value = parseFloat(kpisData[ratio.id]) || 0;
        
        // FIX CRÍTICO: Si el indicador es Capital de Trabajo Neto,
        // aseguramos que el "value" para el análisis sea el valor monetario absoluto
        if (ratio.id === 'capital_trabajo_neto') {
            value = capitalTrabajoNetoValue; 
        }

        // Excluir Apalancamiento y Rentabilidad Patrimonio si el denominador es cero (Lógica de Apalancamiento)
        if ((ratio.id === 'apalancamiento_financiero' || ratio.id === 'rentabilidad_patrimonio') && parseFloat(kpisData.patrimonio_total) === 0) {
            // Se utiliza el valor que viene del Backend para evitar error de NaN en findAnalysis
            const analysis = findAnalysis(ratio.id, value, ratiosConfig, kpisData);
            analysisData.push({
                indicador: ratio.id,
                title: ratio.title,
                // Mensaje de anomalía contable (ya no es parte de las reglas, se maneja aquí)
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

    // NUEVO: Obtener los campos del SEEE
    const escenarioGeneral = kpisData.escenario_general;
    const textoInterpretativo = kpisData.texto_interpretativo;
    const recomendacionesBreves = kpisData.recomendaciones_breves;
    
    
    return (
        <>
            {/* Grid de 3 columnas para las nuevas tarjetas de indicadores */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-3 gap-6 mb-8">
                {ratiosConfig.map((ratio) => {
                    // Obtener el valor principal del Ratio (el que se muestra grande)
                    let value = parseFloat(kpisData[ratio.id]) || 0; 
                    
                    // --- MANEJO DE VALORES DERIVADOS DE SOPORTE ---
                    let mainValue, secondaryValue;

                    if (ratio.id === 'prueba_acida') {
                        mainValue = numeradorPruebaAcida;
                        secondaryValue = pasivoCorriente;
                    } else if (ratio.id === 'capital_trabajo_neto') {
                        value = capitalTrabajoNetoValue;
                        mainValue = activoCorriente;
                        secondaryValue = pasivoCorriente;
                    } else if (ratio.id === 'margen_bruto_utilidad') { // NUEVA LÓGICA DE SOPORTE
                        // Calcular utilidad bruta para mostrar en soporte: Utilidad Neta + Gastos (Clase 5, 7)
                        // NOTA: Esto se hace en el Backend. Aquí mostramos Ingresos - Costo Total Ampliado
                        const ingresos = parseFloat(kpisData.ingresos_anuales) || 0;
                        const utilidadBrutaCalculada = ingresos - (parseFloat(kpisData.costo_ventas_total) || 0); // Asumiendo que costo_ventas_total es el costo ampliado
                        mainValue = utilidadBrutaCalculada;
                        secondaryValue = ingresos;
                        ratio.mainLabel = 'Utilidad Bruta';
                        ratio.secondaryLabel = 'Ingresos Anuales';
                    } else {
                        // Caso General: Los valores de soporte son atómicos (directos del Backend)
                        mainValue = parseFloat(kpisData[ratio.mainData]) || 0;
                        secondaryValue = parseFloat(kpisData[ratio.secondaryData]) || 0;
                    }

                    // Ejecutamos la función colorLogic
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
            
            {/* NUEVO: Muestra el análisis textual del SEEE y el detalle individual */}
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
 * Componente que muestra los KPIs y accesos directos principales.
 */
const DashboardArea = ({ user }) => {
  
  // --- ESTADOS CRÍTICOS (FECHAS Y DATOS) ---
  const today = new Date();
  const firstDayOfYear = new Date(today.getFullYear(), 0, 1);

  // NOTA: EL BACKEND ES QUIEN DEBE DAR LA FECHA MÁXIMA PARA EL CORTE
  const [fechaInicio, setFechaInicio] = useState(firstDayOfYear.toISOString().split('T')[0]);
  const [fechaFin, setFechaFin] = useState(today.toISOString().split('T')[0]);
  
  // kpisData AHORA ALOJA LAS 9 RAZONES
  const [kpisData, setKpisData] = useState(null); 
  const [favoritos, setFavoritos] = useState([]);
  const [loading, setLoading] = useState(false); 
  const router = useRouter();

  
  // --- LÓGICA DE FORMATO DE VALORES ---
  const formatValue = (value, format) => {
    if (value === null || value === undefined) return format === 'percent' ? '0.00 %' : (format === 'currency' ? '$ 0.00' : '0.00');
    
    // Si el valor es una cadena (puede ser el caso si el backend no pudo calcularlo), mostramos 0
    if (typeof value === 'string' && (value === '' || isNaN(parseFloat(value)))) value = 0;

    if (format === 'currency') {
      // Formateo que muestra el signo de pesos y separadores de miles
      const formatted = new Intl.NumberFormat('es-CO', {
        style: 'currency',
        currency: 'USD', 
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      }).format(value);
      // Ajuste para el signo negativo en color
      const isNegative = parseFloat(value) < 0;
      // Corregimos el formato para eliminar 'US' y manejar el signo correctamente
      const cleanFormatted = formatted.replace('-', '').replace('US', '').replace('$', '').trim();
      return (isNegative ? '- ' : '') + '$ ' + cleanFormatted;
    }
    
    if (format === 'percent') {
      return `${(value).toFixed(2)} %`;
    }
    
    if (format === 'ratio') {
        return parseFloat(value).toFixed(2);
    }
    
    return value.toLocaleString('es-CO');
  };

  // --- FUNCIÓN PRINCIPAL DE CARGA DE DATOS (AHORA RECIBE FECHAS) ---
  const fetchData = useCallback(async (start, end) => {
    setLoading(true);
    try {
        
        // 1. CARGA DE RAZONES FINANCIERAS (NUEVO MOTOR)
        let ratiosRes = null;
        if (start && end) {
            // FIX CRÍTICO: Llamada correcta con fechas
            ratiosRes = await getFinancialRatios(start, end); 
        }
        
        // 2. CARGA DE FAVORITOS (Se mantiene para la parte inferior)
        const favoritosRes = await getFavoritos(); 
        
        // Actualizar estados
        setKpisData(ratiosRes);
        setFavoritos(favoritosRes);
        
        // SONDA DE DIAGNÓSTICO CRÍTICO
        console.log("--- SONDA BACKEND DATA RECIBIDA ---");
        console.log("Margen Bruto:", ratiosRes ? ratiosRes.margen_bruto_utilidad : "Nulo/Vacio"); // Nueva Sonda
        console.log("Escenario SEEE:", ratiosRes ? ratiosRes.escenario_general : "Nulo/Vacio");
        console.log("Capital de Trabajo:", ratiosRes ? ratiosRes.capital_trabajo_neto : "Nulo/Vacio");
        console.log("-------------------------------------");

    } catch (err) {
        console.error("Error al cargar datos del dashboard:", err);
        const errorMsg = err.response?.data?.detail || err.message || "Verifique la conexión con el backend.";
        toast.error(`Fallo al cargar datos: ${errorMsg}`);
        
        // Si hay fallo, establecemos datos en cero para evitar que la UI crashee
        setKpisData(null); 
        setFavoritos([]);
        
    } finally {
        setLoading(false);
    }
  }, []);

  // --- FUNCIÓN DEL BOTÓN EJECUTAR ---
  const handleExecuteRatios = (e) => {
      e.preventDefault();
      // Validar fechas antes de ejecutar
      if (!fechaInicio || !fechaFin) {
          toast.warning("Por favor, seleccione un rango de fechas válido.");
          return;
      }
      if (new Date(fechaInicio) > new Date(fechaFin)) {
          toast.error("La fecha de inicio no puede ser posterior a la fecha final.");
          return;
      }
      fetchData(fechaInicio, fechaFin);
  };
  
  // --- CARGA INICIAL (Solo favoritos) ---
  useEffect(() => {
    if (user) {
      // Cargamos solo los favoritos al inicio para que no se vea vacío
      setLoading(true);
      getFavoritos().then(res => {
          setFavoritos(res);
          setLoading(false);
      }).catch(err => {
          console.error("Error al cargar favoritos:", err);
          setLoading(false);
      });
    }
  }, [user]); 

  

  if (!user) {
    // Esto debería ser manejado por el HomePage, pero se mantiene como guardia
    return null;
  }


  return (
    <div className="p-6 w-full h-full overflow-y-auto">
      <ToastContainer position="top-right" autoClose={5000} hideProgressBar={false} newestOnTop={false} closeOnClick rtl={false} pauseOnFocusLoss draggable pauseOnHover />
      <h1 className="text-3xl font-light text-gray-700 mb-6">
        Dashboard de Gestión, Bienvenido(a) <strong className="font-semibold">{user.email}</strong>
      </h1>
      
      {/* --- NUEVA SECCIÓN: FORMULARIO DE CONTROL FINANCIERO --- */}
      <div className="bg-white p-6 rounded-xl shadow-lg mb-8 border-t-4 border-blue-500">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
             
             <FaGg className="mr-3 text-blue-500" /> Tablero de Control Financiero
        </h2>
        
        <form onSubmit={handleExecuteRatios} className="flex flex-col md:flex-row items-end space-y-3 md:space-y-0 md:space-x-4">
          <div className="flex-1 w-full md:w-auto">
            <label htmlFor="fechaInicio" className="block text-sm font-medium text-gray-700">Desde (Fecha de Inicio Balance)</label>
            <input 
              type="date" 
              id="fechaInicio"
              value={fechaInicio}
              onChange={(e) => setFechaInicio(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border focus:border-blue-500 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
              required
            />
          </div>
          
          <div className="flex-1 w-full md:w-auto">
            <label htmlFor="fechaFin" className="block text-sm font-medium text-gray-700">Hasta (Fecha de Corte Balance)</label>
            <input 
              type="date" 
              id="fechaFin"
              value={fechaFin}
              onChange={(e) => setFechaFin(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border focus:border-blue-500 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
              required
            />
          </div>
          
          <button 
            type="submit"
            className="w-full md:w-auto px-6 py-2 bg-blue-600 text-white font-semibold rounded-lg shadow-md hover:bg-blue-700 transition duration-150 flex items-center justify-center disabled:bg-gray-400"
            disabled={loading}
          >
            {loading ? (
                <>
                    <span className="loading loading-spinner mr-2"></span>
                    Calculando...
                </>
            ) : (
                <>
                    <FaChartLine className="mr-2" />
                    Ejecutar Análisis
                </>
            )}
          </button>
          
          {/* ELIMINACIÓN CRÍTICA: Se remueve el enlace "Ver Balance de Prueba" */}
          
        </form>
      </div>

      {/* --- CONTENEDOR DE LAS 9 RAZONES FINANCIERAS (NUEVO DISEÑO DE TARJETAS) --- */}
      <RatiosDisplay kpisData={kpisData} />

      {/* --- Sección de Botones Dinámicos y Configuración --- */}
      <QuickAccessGrid favoritos={favoritos} router={router} />
      
    </div>
  );
};


// =============================================================
// III. PÁGINA PRINCIPAL (Index) (Mantenido)
// =============================================================

/**
 * La página principal de la aplicación.
 * Implementa el layout con Sidebar y el contenido central.
 */
export default function HomePage() {
  const { user, logout, loading: authLoading } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const router = useRouter();

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
          <h1 className="text-4xl font-extrabold text-blue-600 mb-4">
            ContaPY
          </h1>
          <p className="mt-4 text-lg text-gray-600">
            Tu Sistema Contable ERP. Por favor, inicia sesión para acceder.
          </p>
          <div className="mt-8 flex justify-center gap-4">
            <Link 
              href="/login"
              className="btn btn-primary btn-lg shadow-lg"
            >
              Iniciar Sesión
            </Link>
            <Link 
              href="/register" 
              className="btn btn-outline btn-lg"
            >
              Registrarse
            </Link>
          </div>
        </div>
      </main>
    );
  }

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

      {/* --- Sidebar (Menú Principal) --- */}
      <aside 
        className={`fixed inset-y-0 left-0 z-30 transform ${isMenuOpen ? 'translate-x-0' : '-translate-x-full'} 
                   md:relative md:translate-x-0 transition duration-200 ease-in-out 
                   w-64 bg-slate-800 flex flex-col shadow-2xl md:shadow-none`}
      >
        <div className="p-4 flex items-center justify-between h-16 bg-slate-900">
          <h2 className="text-xl font-bold text-white">
            ContaPY <span className="text-sm font-light text-blue-400">v1.0</span>
          </h2>
        </div>
        <div className="flex-1 overflow-y-auto">
          <SidebarMenu 
            menuItems={menuStructure} 
            isMenuOpen={isMenuOpen}
            setIsMenuOpen={setIsMenuOpen}
          />
        </div>
        
        {/* Pie de página del Sidebar (Cerrar Sesión) */}
        <div className="p-4 border-t border-slate-700 bg-slate-900">
          <div className="flex flex-col space-y-2 text-white">
            <p className="text-sm font-medium text-blue-300">Sesión: {user.email}</p>
            <button 
              onClick={logout}
              className="flex items-center justify-center p-2 rounded-lg bg-red-600 hover:bg-red-700 transition duration-150 text-sm font-semibold"
            >
              <FaSignOutAlt className="mr-2" />
              Cerrar Sesión
            </button>
          </div>
        </div>
      </aside>

      {/* --- Contenido Principal (Dashboard) --- */}
      <main className="flex-1 overflow-x-hidden overflow-y-auto">
        <DashboardArea user={user} />
      </main>
    </div>
  );
}