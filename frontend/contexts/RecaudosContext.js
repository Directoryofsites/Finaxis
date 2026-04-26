import React, { createContext, useContext, useState, useEffect } from 'react';
import { phService } from '../lib/phService';

const RecaudosContext = createContext();

// Diccionario de Términos por Sector
const SECTOR_LABELS = {
    'PH_RESIDENCIAL': {
        module: 'Propiedad Horizontal',
        unidad: 'Unidad Privada',
        unidad_plural: 'Unidades Privadas',
        propietario: 'Propietario',
        propietario_plural: 'Propietarios',
        coeficiente: 'Coeficiente',
        concepto: 'Expensa/Concepto',
        torre: 'Torre',
        torre_plural: 'Torres',
        maestro: 'Maestro de Unidades',
        descripcion: 'Gestión de saldos por unidad, torre y concepto.',
        modulo: 'Módulo'
    },
    'PH_COMERCIAL': {
        module: 'Centro Comercial',
        unidad: 'Local Comercial',
        unidad_plural: 'Locales Comerciales',
        propietario: 'Arrendatario/Dueño',
        propietario_plural: 'Arrendatarios',
        coeficiente: 'Área/Coeficiente',
        concepto: 'Cuota Admin',
        torre: 'Zona',
        torre_plural: 'Zonas',
        maestro: 'Maestro de Locales',
        descripcion: 'Saldos detallados por local, zona y concepto comercial.',
        modulo: 'Sección'
    },
    'TRANSPORTE': {
        module: 'Parque Automotor',
        unidad: 'Vehículo/Móvil',
        unidad_plural: 'Vehículos',
        propietario: 'Asociado/Propietario',
        propietario_plural: 'Asociados',
        coeficiente: 'Cupo',
        concepto: 'Rodamiento',
        torre: 'Ruta',
        torre_plural: 'Rutas',
        maestro: 'Control de Parque Automotor',
        descripcion: 'Saldos de rodamiento y aportes por vehículo y ruta.',
        modulo: 'Línea/Ruta'
    },
    'EDUCATIVO': {
        module: 'Gestión Educativa',
        unidad: 'Estudiante',
        unidad_plural: 'Estudiantes',
        propietario: 'Acudiente',
        propietario_plural: 'Acudientes',
        coeficiente: 'Grado',
        concepto: 'Pensión',
        torre: 'Grado',
        torre_plural: 'Grados',
        maestro: 'Maestro de Estudiantes',
        descripcion: 'Saldos de pensiones y servicios por estudiante y grado.',
        modulo: 'Grado/Curso'
    },
    'PARQUEADERO': {
        module: 'Alquiler de Espacios',
        unidad: 'Sitio/Plaza',
        unidad_plural: 'Plazas',
        propietario: 'Cliente',
        propietario_plural: 'Clientes',
        coeficiente: 'Área',
        concepto: 'Mensualidad',
        torre: 'Zona',
        torre_plural: 'Zonas',
        maestro: 'Control de Espacios',
        descripcion: 'Saldos por plaza de parqueo y zona de ubicación.',
        modulo: 'Zona/Sección'
    },
    'CREDITO': {
        module: 'Cartera Financiera',
        unidad: 'Préstamo',
        unidad_plural: 'Préstamos',
        propietario: 'Deudor',
        propietario_plural: 'Deudores',
        coeficiente: 'Tasa Interés',
        concepto: 'Cuota',
        torre: 'Línea',
        torre_plural: 'Líneas',
        maestro: 'Gestión de Cartera de Crédito',
        descripcion: 'Seguimiento de cuotas pendientes por préstamo y línea.',
        modulo: 'Producto'
    },
    'GENERICO': {
        module: 'Gestión de Recaudos',
        unidad: 'Activo/Contrato',
        unidad_plural: 'Activos',
        propietario: 'Cliente',
        propietario_plural: 'Clientes',
        coeficiente: 'Factor',
        concepto: 'Concepto',
        torre: 'Grupo',
        torre_plural: 'Grupos',
        maestro: 'Maestro de Activos',
        descripcion: 'Saldos generales por concepto y grupo de gestión.',
        modulo: 'Módulo'
    }
};

// Tipos de Unidades por Sector (Sembrados)
const SECTOR_TYPES = {
    'PH_RESIDENCIAL': ['Residencial', 'Comercial', 'Parqueadero', 'Depósito', 'Lote'],
    'PH_COMERCIAL': ['Local', 'Isla', 'Oficina', 'Consultorio', 'Bodega', 'Parqueadero'],
    'TRANSPORTE': ['Bus', 'Buseta', 'Microbús', 'Taxi', 'Van', 'Campero', 'Particular'],
    'EDUCATIVO': ['Estudiante Regular', 'Becado', 'Hijo de Docente', 'Convenio'],
    'PARQUEADERO': ['Automóvil', 'Motocicleta', 'Bicicleta', 'Pesado'],
    'CREDITO': ['Libre Inversión', 'Hipotecario', 'Vehículo', 'Microcrédito'],
    'GENERICO': ['Estándar', 'Premium', 'Básico']
};

export function RecaudosProvider({ children }) {
    const [config, setConfig] = useState(null);
    const [labels, setLabels] = useState(SECTOR_LABELS['PH_RESIDENCIAL']);
    const [loading, setLoading] = useState(true);

    const refreshConfig = async () => {
        try {
            const data = await phService.getConfiguracion();
            setConfig(data);
            if (data && data.tipo_negocio && SECTOR_LABELS[data.tipo_negocio]) {
                setLabels(SECTOR_LABELS[data.tipo_negocio]);
            } else {
                setLabels(SECTOR_LABELS['PH_RESIDENCIAL']); // Fallback
            }
        } catch (error) {
            console.error("Error cargando configuración Recaudos:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        refreshConfig();
    }, []);

    return (
        <RecaudosContext.Provider value={{ config, labels, loading, refreshConfig, SECTOR_LABELS, SECTOR_TYPES }}>
            {children}
        </RecaudosContext.Provider>
    );
}

export function useRecaudos() {
    return useContext(RecaudosContext);
}
