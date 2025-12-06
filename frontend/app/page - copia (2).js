// frontend/app/page.js (REEMPLAZO COMPLETO FINAL - FIX CSS y lógica visual)
'use client';

import { useAuth } from './context/AuthContext';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import React, { useState, useMemo, useEffect, useCallback } from 'react';


// Importamos TODOS los íconos necesarios 
import { 
    FaBars, FaTimes, FaHome, FaCalculator, FaChartLine, FaBoxes, FaCog, FaLock, 
    FaUsers, FaSignOutAlt, FaPercentage, FaFileAlt, FaChartBar, FaWrench, 
    FaFileContract, FaBook, FaListUl, FaPlus, FaClipboardList, FaHandshake, 
    FaUniversity, FaReceipt, FaTruckMoving, FaMoneyBill, FaDollarSign, FaTools,
    FaGg // Icono para el Tablero
} from 'react-icons/fa';
import { toast, ToastContainer } from 'react-toastify';
// FIX CRÍTICO: Usamos la ruta universal para el CSS de toastify
import 'react-toastify/dist/ReactToastify.css'; 

// --- Importación de Componentes CRÍTICOS ---
import QuickAccessGrid from './components/QuickAccessGrid'; 
import GaugeChart from './components/GaugeChart'; // Importa el componente del medidor

// --- Servicios Frontend ---
import { getFinancialRatios } from '../lib/dashboardService'; 
import { getFavoritos } from '../lib/favoritosService';       

// =============================================================
// I. DATA: Estructura Jerárquica del Menú (Mantenido)
// =============================================================

export const menuStructure = [ 
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
// II. COMPONENTES: Sidebar, Header y Dashboard (La Nueva UI)
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
        console.log("Datos PYG:", ratiosRes ? ratiosRes.ingresos_anuales : "Nulo/Vacio");
        console.log("Razón Corriente:", ratiosRes ? ratiosRes.razon_corriente : "Nulo/Vacio");
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

  

// --- COMPONENTE MEJORADO PARA LAS 9 RAZONES (CON MEDIDORES) ---
const RatiosDisplay = ({ kpisData }) => { 
  if (!kpisData) {
      return (
          <div className="text-gray-500 p-4 bg-white rounded-lg shadow-inner">
              Seleccione un rango de fechas y presione "Ejecutar" para ver el Tablero de Control Financiero.
          </div>
      );
  }
  
  // Mapeamos los campos de la respuesta del backend a propiedades para GaugeChart
  const ratiosConfig = [
    // FIX CRÍTICO: Todas las funciones de colorLogic están envueltas correctamente
    // 1. Razón Corriente (Liquidez)
    { id: 'razon_corriente', title: "1. Razón Corriente", max: 3.0, unit: 'x', goodRange: '> 1.5x', colorLogic: (val) => val > 1.5 ? "text-green-600" : (val > 1.0 ? "text-orange-500" : "text-red-600") },
    // 2. Prueba Ácida
    { id: 'prueba_acida', title: "2. Prueba Ácida", max: 2.0, unit: 'x', goodRange: '> 1.0x', colorLogic: (val) => val > 1.0 ? "text-green-600" : (val > 0.7 ? "text-orange-500" : "text-red-600") },
    // 3. Capital de Trabajo Neto (Indicador Especial de Valor)
    { id: 'capital_trabajo_neto', title: "3. Capital de Trabajo Neto", format: 'currency', goodRange: '> $0', colorLogic: (val) => val > 0 ? "text-green-600" : "text-red-600", isSpecial: true },
    
    // 4. Nivel de Endeudamiento
    { id: 'nivel_endeudamiento', title: "4. Nivel Endeudamiento", max: 1.0, unit: 'x', goodRange: '< 0.50x (50%)', colorLogic: (val) => val < 0.50 ? "text-green-600" : (val < 0.70 ? "text-orange-500" : "text-red-600") },
    // 5. Apalancamiento Financiero
    { id: 'apalancamiento_financiero', title: "5. Apalancamiento", max: 5.0, unit: 'x', goodRange: '< 3.0x', colorLogic: (val) => val < 3.0 ? "text-green-600" : (val < 4.0 ? "text-orange-500" : "text-red-600") },
    // 6. Margen Neto Utilidad
    { id: 'margen_neto_utilidad', title: "6. Margen Neto Utilidad", max: 30, unit: '%', goodRange: '> 5%', colorLogic: (val) => val > 5 ? "text-green-600" : (val > 0 ? "text-orange-500" : "text-red-600") },
    
    // 7. Rentabilidad Patrimonio (ROE)
    { id: 'rentabilidad_patrimonio', title: "7. Rentabilidad Patrimonio (ROE)", max: 20, unit: '%', goodRange: '> 10%', colorLogic: (val) => val > 10 ? "text-green-600" : (val > 5 ? "text-orange-500" : "text-red-600") },
    // 8. Rentabilidad Activo (ROA)
    { id: 'rentabilidad_activo', title: "8. Rentabilidad Activo (ROA)", max: 15, unit: '%', goodRange: '> 5%', colorLogic: (val) => val > 5 ? "text-green-600" : (val > 2 ? "text-orange-500" : "text-red-600") },
    // 9. Rotación de Activos
    { id: 'rotacion_activos', title: "9. Rotación Activos", max: 5.0, unit: 'x', goodRange: '> 2.0x', colorLogic: (val) => val > 2.0 ? "text-green-600" : (val > 1.0 ? "text-orange-500" : "text-red-600") },
  ];
  
  return (
      // Aquí el grid de 3 columnas para los medidores
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          {ratiosConfig.map((ratio) => {
              // Aseguramos que el valor sea float o 0 si es nulo
              const value = parseFloat(kpisData[ratio.id]) || 0; 
              // Ejecutamos la función colorLogic
              const colorClass = ratio.colorLogic(value);

              // 1. Caso Especial: Capital de Trabajo Neto (Valor Absoluto)
              if (ratio.isSpecial) {
                  const valDisplay = formatValue(value, 'currency');
                  const valColor = ratio.colorLogic(value);
                return (
                  <div key={ratio.id} className="bg-white p-4 rounded-xl shadow border border-gray-200 flex flex-col justify-center items-center h-full">
                      <p className="text-sm font-semibold text-gray-500">{ratio.title}</p>
                      <p className={`text-3xl font-extrabold mt-1 ${valColor}`}>{valDisplay}</p>
                      <p className="text-xs text-gray-500 mt-1">Meta Ideal: {ratio.goodRange}</p>
                  </div>
                );
              }
              
              // 2. Caso General: Medidor Circular (Ratio/Porcentaje)
              return (
                  <GaugeChart
                      key={ratio.id}
                      title={ratio.title}
                      value={value} 
                      max={ratio.max}
                      unit={ratio.unit}
                      goodRange={ratio.goodRange}
                      colorClass={colorClass}
                  />
              );
          })}
      </div>
  );
};


  if (!user || loading) {
      // ... (Código de carga y no autenticado)
      return (
          <main className="flex min-h-screen items-center justify-center bg-gray-50">
            <div className="text-center">
              <span className="loading loading-spinner loading-lg text-primary"></span>
              <p className="text-gray-500 mt-2">Cargando sesión...</p>
            </div>
          </main>
      );
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
          
          {/* Enlace al Balance de Prueba (Referencia) */}
           <Link 
              href="/contabilidad/reportes/balance-de-prueba" 
              target="_blank"
              className="w-full md:w-auto px-6 py-2 bg-gray-200 text-gray-700 font-semibold rounded-lg shadow-md hover:bg-gray-300 transition duration-150 flex items-center justify-center text-sm"
            >
              <FaFileAlt className="mr-2" />
              Ver Balance de Prueba
            </Link>
          
        </form>
      </div>

      {/* --- CONTENEDOR DE LAS 9 RAZONES FINANCIERAS (MEDIDORES) --- */}
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