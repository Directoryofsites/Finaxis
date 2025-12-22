
import {
    FaBox,
    FaFileInvoiceDollar,
    FaUserPlus,
    FaBalanceScale,
    FaFileContract,
    FaMoneyBillWave,
    FaBuilding,
    FaLayerGroup,
    FaCog,
    FaBook
} from 'react-icons/fa';

/**
 * Diccionario de Comandos Inteligentes
 * 
 * triggers: Array de frases que activan el comando (lowercase).
 * name: Título mostrado en el resultado.
 * description: Subtítulo.
 * path: Ruta de destino.
 * queryParam: Parámetro opcional para activar acciones (ej: 'trigger=new_item').
 * icon: Icono de React-Icons.
 * category: Etiqueta clasificadora.
 */
export const commandDictionary = [
    // --- INVENTARIO ---
    {
        triggers: ['nuevo item', 'nuevo producto', 'crear item', 'crear producto'],
        aliases: ['ni', 'npr'],
        name: 'Crear Nuevo Ítem',
        description: 'Abrir modal de creación en Inventario',
        path: '/admin/inventario',
        queryParam: 'trigger=new_item',
        icon: FaBox,
        category: 'Inventario'
    },

    // --- FACTURACIÓN ---
    // Nota: Facturación es una página entera, no requiere trigger, pero el alias es útil.
    {
        triggers: ['nueva factura', 'crear factura', 'facturar'],
        aliases: ['nf', 'fac'],
        name: 'Nueva Factura de Venta',
        description: 'Ir a la pantalla de creación de factura',
        path: '/contabilidad/facturacion',
        icon: FaFileInvoiceDollar,
        category: 'Ventas'
    },

    // --- COMPRAS (Gasto) ---
    {
        triggers: ['nueva compra', 'nuevo gasto', 'registrar compra'],
        aliases: ['nc', 'ng'],
        name: 'Nueva Compra / Gasto',
        description: 'Abrir modal de registro de compras',
        path: '/contabilidad/compras',
        queryParam: 'trigger=new_purchase',
        icon: FaMoneyBillWave,
        category: 'Compras'
    },

    // --- TRASLADOS ---
    {
        triggers: ['nuevo traslado', 'crear traslado', 'mover inventario'],
        aliases: ['nt', 'tras'],
        name: 'Nuevo Traslado',
        description: 'Abrir modal de traslado de bodega',
        path: '/contabilidad/traslados',
        queryParam: 'trigger=new_transfer',
        icon: FaBox,
        category: 'Inventario'
    },

    // --- CENTROS DE COSTO ---
    {
        triggers: ['nuevo centro costo', 'crear centro costo'],
        aliases: ['ncc'],
        name: 'Nuevo Centro de Costo',
        description: 'Abrir modal de creación',
        path: '/admin/centros-costo',
        queryParam: 'trigger=new_cc',
        icon: FaBuilding, // Update icon import if needed
        category: 'Administración'
    },

    // --- TERCEROS ---
    {
        triggers: ['nuevo tercero', 'crear tercero', 'nuevo cliente', 'crear cliente', 'nuevo proveedor', 'nuevo empleado', 'nuevo propietario'],
        aliases: ['nter', 'ncl', 'npro', 'nemp'], // npro added
        name: 'Nuevo Tercero',
        description: 'Registrar Cliente, Proveedor o Empleado',
        path: '/admin/terceros/crear',
        icon: FaUserPlus,
        category: 'Administración'
    },

    // --- PH (PROPIEDAD HORIZONTAL) ---
    {
        triggers: ['nueva unidad', 'crear unidad', 'nuevo apartamento'],
        aliases: ['nu', 'nuni'],
        name: 'Nueva Unidad Privada',
        description: 'Crear apartamento, casa o local',
        path: '/ph/unidades/crear',
        icon: FaBuilding,
        category: 'PH'
    },

    // --- PRODUCCIÓN ---
    {
        triggers: ['nueva receta', 'crear receta', 'fichas tecnicas'],
        aliases: ['nr', 'rec'],
        name: 'Nueva Receta de Producción',
        description: 'Crear ficha técnica de producto',
        path: '/produccion/recetas',
        queryParam: 'trigger=new_recipe',
        icon: FaFileContract,
        category: 'Producción'
    },

    // --- CONFIGURACIÓN INVENTARIO ---
    {
        triggers: ['nuevo grupo', 'crear grupo inventario'],
        aliases: ['ng', 'ngrp'],
        name: 'Nuevo Grupo de Inventario',
        description: 'Configurar agrupación contable',
        path: '/admin/inventario/parametros',
        queryParam: 'trigger=tab_groups',
        icon: FaLayerGroup,
        category: 'Configuración'
    },
    {
        triggers: ['nueva bodega', 'crear bodega'],
        aliases: ['nb', 'nbod'],
        name: 'Nueva Bodega',
        description: 'Registrar lugar de almacenamiento',
        path: '/admin/inventario/parametros',
        queryParam: 'trigger=tab_warehouses',
        icon: FaBuilding,
        category: 'Configuración'
    },

    // --- ADMINISTRACIÓN / UTILIDADES ---
    {
        triggers: ['nuevo tipo documento', 'crear tipo documento'],
        aliases: ['ntd'],
        name: 'Nuevo Tipo de Documento',
        description: 'Configurar consecutivo (Fac, RC, CE...)',
        path: '/admin/tipos-documento/crear',
        icon: FaFileContract,
        category: 'Configuración'
    },
    {
        triggers: ['nueva plantilla', 'crear plantilla'],
        aliases: ['npl'],
        name: 'Nueva Plantilla Contable',
        description: 'Modelo de asiento recurrente',
        path: '/admin/plantillas/crear',
        icon: FaFileContract,
        category: 'Configuración'
    },
    {
        triggers: ['nueva empresa', 'crear empresa'],
        aliases: ['nempresa'],
        name: 'Nueva Empresa (Soporte)',
        description: 'Registrar nueva compañía en el sistema',
        path: '/admin/utilidades/soporte-util',
        queryParam: 'trigger=tab_create_company',
        icon: FaBuilding,
        category: 'Soporte'
    },
    // --- NÓMINA ---
    {
        triggers: ['nuevo tipo nomina', 'crear tipo nomina'],
        aliases: ['ntn', 'ntnom'],
        name: 'Nuevo Tipo de Nómina',
        description: 'Crear configuración de nómina',
        path: '/nomina/configuracion',
        queryParam: 'trigger=new_payroll_type',
        icon: FaCog, // FaCog imported? Need to check imports
        category: 'Nómina'
    },
    // --- PH ---
    {
        triggers: ['nuevo concepto ph', 'crear concepto ph'],
        aliases: ['ncph'],
        name: 'Nuevo Concepto PH',
        description: 'Crear concepto de facturación PH',
        path: '/ph/conceptos',
        queryParam: 'trigger=new_ph_concept',
        icon: FaFileInvoiceDollar,
        category: 'Propiedad Horizontal'
    },
    // --- UTILIDADES ---
    {
        triggers: ['nuevo concepto', 'crear concepto'],
        aliases: ['nc', 'ncon'],
        name: 'Nuevo Concepto (Favorito)',
        description: 'Librería de conceptos favoritos',
        path: '/admin/utilidades/gestionar-conceptos',
        queryParam: 'trigger=new_fav_concept',
        icon: FaBook,
        category: 'Configuración'
    }
];
