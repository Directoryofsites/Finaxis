import React, { createContext, useContext, useState, useEffect } from 'react';
import { phService } from '../lib/phService';

const RecaudosContext = createContext();

// Diccionario de Términos por Sector
const SECTOR_LABELS = {
    'PH_RESIDENCIAL': {
        module: 'Propiedad Horizontal',
        unidad: 'Unidad Privada',
        propietario: 'Propietario',
        coeficiente: 'Coeficiente',
        concepto: 'Expensa/Concepto',
        torre: 'Torre',
        torre_plural: 'Torres'
    },
    'PH_COMERCIAL': {
        module: 'Centro Comercial',
        unidad: 'Local Comercial',
        propietario: 'Arrendatario/Dueño',
        coeficiente: 'Área/Coeficiente',
        concepto: 'Cuota Admin',
        torre: 'Zona',
        torre_plural: 'Zonas'
    },
    'TRANSPORTE': {
        module: 'Parque Automotor',
        unidad: 'Vehículo/Móvil',
        propietario: 'Asociado/Propietario',
        coeficiente: 'Cupo',
        concepto: 'Rodamiento',
        torre: 'Ruta',
        torre_plural: 'Rutas'
    },
    'EDUCATIVO': {
        module: 'Gestión Educativa',
        unidad: 'Estudiante',
        propietario: 'Acudiente',
        coeficiente: 'Grado',
        concepto: 'Pensión',
        torre: 'Grado',
        torre_plural: 'Grados'
    },
    'PARQUEADERO': {
        module: 'Alquiler de Espacios',
        unidad: 'Sitio/Plaza',
        propietario: 'Cliente',
        coeficiente: 'Área',
        concepto: 'Mensualidad',
        torre: 'Zona',
        torre_plural: 'Zonas'
    },
    'CREDITO': {
        module: 'Cartera Financiera',
        unidad: 'Préstamo',
        propietario: 'Deudor',
        coeficiente: 'Tasa Interés',
        concepto: 'Cuota',
        torre: 'Línea',
        torre_plural: 'Líneas'
    },
    'GENERICO': {
        module: 'Gestión de Recaudos',
        unidad: 'Activo/Contrato',
        propietario: 'Cliente',
        coeficiente: 'Factor',
        concepto: 'Concepto',
        torre: 'Grupo',
        torre_plural: 'Grupos'
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
