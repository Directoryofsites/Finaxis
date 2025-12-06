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
    FaUniversity, FaReceipt, FaTruckMoving, FaMoneyBill, FaDollarSign, FaTools 
} from 'react-icons/fa';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// --- Importación del Nuevo Componente ---
import QuickAccessGrid from './components/QuickAccessGrid'; // Importamos la nueva cuadrícula moderna

// --- Servicios Frontend ---
import { getFinancialKPIs } from '../lib/dashboardService'; // Misión 2: KPIs
import { getFavoritos } from '../lib/favoritosService';       // Misión 1: Favoritos

// =============================================================
// I. DATA: Estructura Jerárquica del Menú (EXPORTADA PARA ELIMINAR BUILD ERROR)
// =============================================================

export const menuStructure = [ // <--- CORRECCIÓN CLAVE: Exportamos menuStructure
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
 * Componente funcional que muestra el menú lateral jerárquico.
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
  
  // Definición de la estructura de las tarjetas y los íconos (mapeados a los nombres del backend)
  const kpiDefinitions = useMemo(() => ([
    // --- Rendimiento (PYG) ---
    { id: 'ingresos_anuales', title: "Ingresos del Año (2025)", color: "text-green-600", icon: FaChartLine, format: 'currency', widthClass: "lg:col-span-1" },
    { id: 'costo_ventas_total', title: "Total Costo de Ventas", color: "text-red-600", icon: FaDollarSign, format: 'currency', widthClass: "lg:col-span-1" },
    { id: 'utilidad_bruta', title: "Utilidad Bruta", color: "text-purple-600", icon: FaPercentage, format: 'currency', widthClass: "lg:col-span-1" },
    { id: 'utilidad_neta', title: "Utilidad Neta", color: "text-cyan-600", icon: FaChartBar, format: 'currency', widthClass: "lg:col-span-1" },
    { id: 'rentabilidad_porcentaje', title: "Rentabilidad Neta (%)", color: "text-blue-700", icon: FaPercentage, format: 'percent', widthClass: "lg:col-span-2 md:col-span-2" },

    // --- Balance General y Liquidez ---
    { id: 'activos_total', title: "Total Activos", color: "text-green-700", icon: FaClipboardList, format: 'currency', widthClass: "lg:col-span-1" },
    { id: 'pasivos_total', title: "Total Pasivos", color: "text-red-700", icon: FaHandshake, format: 'currency', widthClass: "lg:col-span-1" },
    { id: 'patrimonio_total', title: "Total Patrimonio", color: "text-blue-700", icon: FaUniversity, format: 'currency', widthClass: "lg:col-span-1" },
    
    // --- Detalle ---
    { id: 'cartera_total', title: "Total Cartera (CxC)", color: "text-orange-600", icon: FaReceipt, format: 'currency', widthClass: "lg:col-span-1" },
    { id: 'proveedores_total', title: "Total Proveedores (CxP)", color: "text-red-500", icon: FaTruckMoving, format: 'currency', widthClass: "lg:col-span-1" },
    { id: 'disponible_total', title: "Total Disponible", color: "text-teal-600", icon: FaMoneyBill, format: 'currency', widthClass: "lg:col-span-1" },
    
  ]), []);
  
  const [kpisData, setKpisData] = useState(null);
  const [favoritos, setFavoritos] = useState([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  // Lógica para formatear números
  const formatValue = (value, format) => {
    if (value === null || value === undefined) return format === 'percent' ? '0.00 %' : '$ 0.00';
    
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
      const cleanFormatted = formatted.replace('-', '').replace('US', '').trim();
      return (isNegative ? '- ' : '') + cleanFormatted;
    }
    
    if (format === 'percent') {
      return `${(value).toFixed(2)} %`;
    }
    
    return value.toLocaleString('es-CO');
  };

  // Se eliminó la función getIconForRoute de este archivo, ahora reside en QuickAccessGrid.js

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
        const [kpisRes, favoritosRes] = await Promise.all([
            getFinancialKPIs(), // Llama a la API de KPIs
            getFavoritos()      // Llama a la API de Favoritos
        ]);
        
        setKpisData(kpisRes);
        setFavoritos(favoritosRes);

    } catch (err) {
        console.error("Error al cargar datos del dashboard:", err);
        const errorMsg = err.message || "Verifique la conexión con el backend.";
        toast.error(`Fallo al cargar datos: ${errorMsg}`);
        
        // Si hay fallo, establecemos datos en cero para evitar que la UI crashee
        setKpisData({
            ingresos_anuales: 0, costo_ventas_total: 0, utilidad_bruta: 0, utilidad_neta: 0, 
            rentabilidad_porcentaje: 0, activos_total: 0, pasivos_total: 0, patrimonio_total: 0, 
            cartera_total: 0, proveedores_total: 0, disponible_total: 0
        });
        setFavoritos([]);
        
    } finally {
        setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (user) {
      fetchData();
    }
  }, [user, fetchData]);

  if (loading) {
      return (
          <div className="flex h-full items-center justify-center">
              <span className="loading loading-spinner loading-lg text-primary"></span>
          </div>
      );
  }

  return (
    <div className="p-6 w-full h-full overflow-y-auto">
      <ToastContainer position="top-right" autoClose={5000} hideProgressBar={false} newestOnTop={false} closeOnClick rtl={false} pauseOnFocusLoss draggable pauseOnHover />
      <h1 className="text-3xl font-light text-gray-700 mb-6">
        Dashboard de Gestión, Bienvenido(a) <strong className="font-semibold">{user.email}</strong>
      </h1>
      
      {/* --- Cards de KPIs Financieros Reales (12 KPIs) --- */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-8">
        {kpiDefinitions.map((kpi) => {
          const value = kpisData ? kpisData[kpi.id] : null; 
          const formattedValue = formatValue(value, kpi.format);
          
          return (
            <div key={kpi.id} className={`bg-white p-4 rounded-xl shadow-md border border-gray-200 lg:col-span-1 ${kpi.widthClass} transform hover:scale-105 transition duration-300`}>
              <kpi.icon size={20} className={`${kpi.color} mb-1`} />
              <p className="text-xs font-medium text-gray-500 truncate">{kpi.title}</p>
              <p className={`text-xl font-bold mt-1 ${kpi.color}`}>{formattedValue}</p>
            </div>
          );
        })}
      </div>

      {/* --- Sección de Botones Dinámicos y Configuración (NUEVA CUADRÍCULA) --- */}
      <QuickAccessGrid favoritos={favoritos} router={router} />
      
    </div>
  );
};


// =============================================================
// III. PÁGINA PRINCIPAL (Index)
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