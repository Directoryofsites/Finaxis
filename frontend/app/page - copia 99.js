'use client';

import { useAuth } from './context/AuthContext';
import Link from 'next/link';

export default function HomePage() {
  const { user, logout } = useAuth();

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gray-50">
      <div className="w-full max-w-3xl text-center"> {/* Aumenté un poco el ancho máximo */}
        {user ? (
          <div>
            <h1 className="text-4xl font-bold text-gray-800">
              Bienvenido al Sistema Contable
            </h1>
            <p className="mt-4 text-xl text-gray-600">
              Sesión iniciada como: <strong>{user.email}</strong>
            </p>
            <div className="mt-8 space-y-6">

              {/* --- Grupo de Botones de Operación Contable --- */}
              <div className="p-4 border rounded-lg">
                <h3 className="text-lg font-medium text-gray-700 mb-3 text-left">Operaciones y Reportes</h3>
                <div className="flex flex-wrap justify-center gap-4">
                  <Link href="/contabilidad/documentos" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700">
                    Crear Documento
                  </Link>
                 
                  <Link href="/contabilidad/reportes/libro-diario" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700">
                    Libro Diario
                  </Link>
                  <Link href="/contabilidad/reportes/auxiliar-cuenta" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-cyan-600 hover:bg-cyan-700">
                    Reporte Auxiliar
                  </Link>
                  <Link href="/contabilidad/reportes/tercero-cuenta" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-purple-600 hover:bg-purple-700">
                    Auxiliar por Tercero
                  </Link>
                  {/* --- BOTÓN NUEVO AÑADIDO --- */}
                  <Link href="/contabilidad/reportes/estado-resultados" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-orange-600 hover:bg-orange-700">
                    Estado de Resultados
                  </Link>
                  <Link href="/contabilidad/reportes/balance-general" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-700 hover:bg-blue-800">
                    Balance General
                  </Link>
                  <Link href="/contabilidad/reportes/auxiliar-cc-cuenta" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-teal-600 hover:bg-teal-700">
                    Auxiliar por CC y Cuenta
                  </Link>
                 
                  <Link href="/contabilidad/reportes/estado-resultados-cc-detallado" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-slate-600 hover:bg-slate-700">
                    Estado de Resultados por CC
                  </Link>

                  <Link href="/contabilidad/reportes/balance-general-cc" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-purple-600 hover:bg-purple-700">
                    Balance general por CC
                  </Link>

                  <Link href="/contabilidad/reportes/estado-cuenta-cliente" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700">
                    Cartera
                  </Link>
                  
                  <Link href="/contabilidad/reportes/auxiliar-cartera" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-orange-600 hover:bg-orange-700">
                    Auxiliar de Cartera
                  </Link>

                  <Link href="/contabilidad/reportes/estado-cuenta-proveedor" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-700 hover:bg-blue-800">
                    Proveedores
                  </Link>

                  <Link href="/contabilidad/reportes/auxiliar-proveedores" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700">
                    Auxiliar Proveedores
                  </Link>

                  <Link href="/contabilidad/reportes/super-informe" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-purple-600 hover:bg-purple-700">
                    Auditoria Avanzada
                  </Link>

                  <Link href="/contabilidad/captura-rapida" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700">
                    Captura Rápida de Documentos
                  </Link>

                  <Link href="/contabilidad/reportes/balance-de-prueba" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700">
                    Balance de Prueba
                  </Link>

                    <Link href="/contabilidad/reportes/balance-de-prueba-cc" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-purple-600 hover:bg-purple-700">
                    Balance de Prueba por Centro
                     </Link>

                  <Link href="/admin/utilidades/libros-oficiales" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700">
                    Libros Oficiales
                  </Link>

                  <Link href="/contabilidad/facturacion" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700">
                    Facturacion
                  </Link>

                  <Link href="/admin/inventario" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700">
                    Gestión de Inventario
                  </Link>

                       <Link href="/contabilidad/compras" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-purple-600 hover:bg-purple-700">
                    Gestión Compras
                  </Link>

                  <Link href="/contabilidad/reportes/estado-inventarios" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700">
                    Estado Inventarios
                  </Link>

                  <Link href="/contabilidad/reportes/rentabilidad-producto" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700">
                    Rentabilidad Producto
                  </Link>

                   <Link href="/contabilidad/reportes/gestion-ventas" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700">
                    Gestion Ventas
                  </Link>

                  <Link href="/contabilidad/reportes/explorador-transacciones-facturacion" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700">
                    Informes Facturacion
                  </Link>

                  <Link href="/admin/inventario/ajuste-inventario" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700">
                    Ajustes Inventario
                  </Link>
                 
                  <Link href="/contabilidad/reportes/movimiento-analitico" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700">
                    Estado General y Movimientos de Inventario
                  </Link>

                  <Link href="/contabilidad/reportes/super-informe-inventarios" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700">
                    Super Informe Inventarios
                  </Link>

               
                <Link href="/contabilidad/traslados" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700">
                    Traslado Inventarios
                  </Link>



                  
                </div>
              </div>
              
              {/* --- Grupo de Botones de Administración --- */}
              <div className="p-4 border rounded-lg">
                 <h3 className="text-lg font-medium text-gray-700 mb-3 text-left">Administración y Parametrización</h3>
                <div className="flex flex-wrap justify-center gap-4">
                  <Link href="/admin/plan-de-cuentas" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-gray-600 hover:bg-gray-700">
                    Gestionar PUC
                  </Link>
                  <Link href="/admin/tipos-documento" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-gray-600 hover:bg-gray-700">
                    Gestionar Tipos de Doc.
                  </Link>

                  <Link href="/admin/terceros" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-gray-600 hover:bg-gray-700">
                    Gestionar Terceros
                  </Link>
                  <Link href="/admin/plantillas" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-gray-600 hover:bg-gray-700">
                    Gestionar Plantillas
                  
                  </Link>

                  <Link href="/admin/utilidades/eliminacion-masiva" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-700 hover:bg-red-800">
                    Edición de Documentos
                    </Link>

                    <Link href="/admin/utilidades/erradicar-documento" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-700 hover:bg-red-800">
                    Erradicador de Documentos
                    </Link>

                    <Link href="/admin/utilidades/soporte-util" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-700 hover:bg-red-800">
                    Gestion Avanzada y Utilitarios
                    </Link>



                  <Link href="/admin/utilidades/recodificacion-masiva" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-amber-600 hover:bg-amber-700">
                Recodificación Masiva
              </Link>

              <Link href="/admin/centros-costo" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-gray-600 hover:bg-gray-700">
              Gestionar C. de Costo
              </Link>             
              
              <Link href="/admin/utilidades/gestionar-conceptos" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-gray-600 hover:bg-gray-700">
              Gestionar Conceptos
              </Link>

              <Link href="/admin/utilidades/migracion-datos" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-purple-600 hover:bg-purple-700">
              Copias y Restauración
              </Link>

              <Link href="/admin/utilidades/periodos-contables" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-gray-600 hover:bg-gray-700">
              Cerrar Periodos Contables
              </Link>

              <Link href="/admin/utilidades/papelera" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-gray-600 hover:bg-gray-700">
              Papelera de Reciclaje
              </Link>

               
              <Link href="/admin/utilidades/gestion-anulados" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-gray-600 hover:bg-gray-700">
              Gestion Anulados
              </Link>

              <Link href="/admin/utilidades/auditoria-consecutivos" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-gray-600 hover:bg-gray-700">
              Consecutivos
              </Link>

              <Link href="/admin/empresas" className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-gray-600 hover:bg-gray-700">
              Empresas
              </Link>

            


                </div>
              </div>
            </div>

            <div className="mt-12">
                <button
                  onClick={logout}
                  className="px-5 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700"
                >
                  Cerrar Sesión
                </button>
            </div>
          </div>
        ) : (
          <div>
            <h1 className="text-4xl font-bold text-gray-800">
              Bienvenido al Sistema Contable
            </h1>
            <p className="mt-4 text-xl text-gray-600">
              Por favor, inicia sesión o crea una cuenta para continuar.
            </p>
            <div className="mt-8 flex justify-center gap-4">
              <Link 
                href="/login"
                className="px-6 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700"
              >
                Iniciar Sesión
              </Link>
             <Link 
                href="/register" 
                className="px-6 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                Registrarse
              </Link>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}