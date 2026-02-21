
// Datos Tributarios Colombia 2026 (Ajustado a requerimientos visuales del usuario)
// Nota: El usuario indicó específicamente que para NIT terminado en 9, la retención vence el 21 de febrero.
// Esto corresponde al calendario 2025, pero se ajusta aquí para cumplir con la validación del usuario.

export const TAX_CONSTANTS_2026 = {
    UVT: 52374,
    SANCION_MINIMA_UVT: 10,
    BASE_RET_COMPRAS_UVT: 27, // Mantenemos constante general, aunque conceptos especificos varian
    BASE_RET_SERVICIOS_UVT: 4,
    TOPE_PATRIMONIO_RENTA_UVT: 4500,
    TOPE_INGRESOS_RENTA_UVT: 1400
};

// --- CALENDARIOS COMPLETOS 2026 (BASE SIMULADA 2025/2026 DIAN) ---
// Retencion en la Fuente - Día de Vencimiento mensual por último dígito de NIT
const DIAS_RETENCION = {
    '1': 11, '2': 12, '3': 13, '4': 14, '5': 17,
    '6': 18, '7': 19, '8': 20, '9': 21, '0': 24
};

// IVA Bimestral - Meses de Vencimiento: Marzo, Mayo, Julio, Septiembre, Noviembre, Enero
const MESES_IVA_BIMESTRAL = [2, 4, 6, 8, 10, 0]; // (Mar, May, Jul, Sep, Nov, Ene del prox año)
const DIAS_IVA = DIAS_RETENCION; // Usan los mismos días típicamente

// IVA Cuatrimestral - Meses de Vencimiento: Mayo, Septiembre, Enero
const MESES_IVA_CUATRIMESTRAL = [4, 8, 0];

// Renta PJ - Vencimientos en Abril / Mayo (Simplificado al primer vencimiento)
const DIAS_RENTA_PJ_C1 = {
    '1': 7, '2': 8, '3': 9, '4': 10, '5': 11,
    '6': 14, '7': 15, '8': 16, '9': 17, '0': 21
};

const NOMBRES_MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];

export const getTaxDeadlines = (nit, tipoPersona, periodicidadIva) => {
    if (!nit) return null;

    const lastDigit = nit.slice(-1);
    const currentDate = new Date();
    const currentMonth = currentDate.getMonth(); // 0-11

    // --- 1. RENTA ---
    let renta = "";
    if (tipoPersona === 'natural') {
        renta = `Vencimiento: Ago-Oct (${lastDigit})`;
    } else {
        const diaRenta = DIAS_RENTA_PJ_C1[lastDigit] || 15;
        renta = `Cuota 1: Abril ${diaRenta}`;
    }

    // --- 2. RETENCIÓN (Mensual) ---
    // La retención se declara al mes SIGUIENTE. Si estoy en Febrero, declaro la de Enero.
    const diaRetencion = DIAS_RETENCION[lastDigit] || 15;
    const mesVencimientoRet = NOMBRES_MESES[currentMonth];
    const mesPeriodoRet = currentMonth === 0 ? 'Diciembre' : NOMBRES_MESES[currentMonth - 1];
    const retencion = `${mesVencimientoRet} ${diaRetencion} (Mes ${mesPeriodoRet})`;

    // --- 3. IVA ---
    let iva = "";
    const diaIva = DIAS_IVA[lastDigit] || 15;

    if (periodicidadIva === 'bimestral') {
        // Encontrar el mes bimestral más cercano hacia o desde el actual
        const proximoMesIvaIndex = MESES_IVA_BIMESTRAL.find(m => m >= currentMonth) ?? 0;
        const nombreMesIva = NOMBRES_MESES[proximoMesIvaIndex];

        // Calcular los bimestres a los que obedece
        let periodoIvaDesc = "";
        if (proximoMesIvaIndex === 2) periodoIvaDesc = "(Ene-Feb)";
        else if (proximoMesIvaIndex === 4) periodoIvaDesc = "(Mar-Abr)";
        else if (proximoMesIvaIndex === 6) periodoIvaDesc = "(May-Jun)";
        else if (proximoMesIvaIndex === 8) periodoIvaDesc = "(Jul-Ago)";
        else if (proximoMesIvaIndex === 10) periodoIvaDesc = "(Sep-Oct)";
        else periodoIvaDesc = "(Nov-Dic)";

        iva = `${nombreMesIva} ${diaIva} ${periodoIvaDesc}`;
    } else {
        // Cuatrimestral
        const proximoMesCuatIndex = MESES_IVA_CUATRIMESTRAL.find(m => m >= currentMonth) ?? 0;
        const nombreMesIva = NOMBRES_MESES[proximoMesCuatIndex];

        let periodoIvaDesc = "";
        if (proximoMesCuatIndex === 4) periodoIvaDesc = "(Ene-Abr)";
        else if (proximoMesCuatIndex === 8) periodoIvaDesc = "(May-Ago)";
        else periodoIvaDesc = "(Sep-Dic)";

        iva = `${nombreMesIva} ${diaIva} ${periodoIvaDesc}`;
    }

    return { renta, iva, retencion };
};

// CONCEPTOS ACTUALIZADOS SEGÚN TABLA DE USUARIO
// Fuente: Usuario (Tabla personalizada)
export const RETENTION_CONCEPTS_2026 = [
    { concepto: 'Compras generales (bienes) - Declarantes', base_uvt: 10, tarifa: 2.5 },
    { concepto: 'Compras generales (bienes) - No Declarantes', base_uvt: 10, tarifa: 3.5 },

    { concepto: 'Servicios generales - Declarantes', base_uvt: 2, tarifa: 4.0 },
    { concepto: 'Servicios generales - No Declarantes', base_uvt: 2, tarifa: 6.0 },

    { concepto: 'Honorarios PN (Naturales) - Declarante', base_uvt: 0, tarifa: 10.0 },
    { concepto: 'Honorarios PN (Naturales) - No Declarante', base_uvt: 0, tarifa: 11.0 },

    { concepto: 'Honorarios PJ (Jurídicas)', base_uvt: 0, tarifa: 11.0 },

    { concepto: 'Arrendamiento Inmuebles', base_uvt: 10, tarifa: 3.5 }, // User table specified 10 UVT
    { concepto: 'Arrendamiento Muebles', base_uvt: 0, tarifa: 4.0 },

    { concepto: 'Transporte Carga Terrestre', base_uvt: 2, tarifa: 1.0 }, // User table specified 2 UVT

    { concepto: 'Licenciamiento Software', base_uvt: 0, tarifa: 3.5 },

    { concepto: 'Intereses Financieros', base_uvt: 0, tarifa: 7.0 },

    { concepto: 'Productos Agrícolas Sin Procesar', base_uvt: 70, tarifa: 1.5 },
    { concepto: 'Café Pergamino/Cereza', base_uvt: 70, tarifa: 0.5 },

    { concepto: 'Combustibles Petróleo', base_uvt: 0, tarifa: 0.1 }
];


// RETEICA ARMENIA (Acuerdo 229 de 2021)
// Conceptos Principales Simplificados
export const RETEICA_ARMENIA_CONCEPTS = [
    { concepto: 'Compras (Bienes Gravados)', base_uvt: 27, tarifa_porcentaje: 0.50, tarifa_x_mil: 5.0 },
    { concepto: 'Servicios Generales', base_uvt: 4, tarifa_porcentaje: 1.00, tarifa_x_mil: 10.0 },
    { concepto: 'Honorarios Profesionales', base_uvt: 0, tarifa_porcentaje: 1.00, tarifa_x_mil: 10.0 },
    { concepto: 'Construcción / Obra Civil', base_uvt: 4, tarifa_porcentaje: 1.40, tarifa_x_mil: 14.0 },
    { concepto: 'Publicidad / Comunicación', base_uvt: 4, tarifa_porcentaje: 1.00, tarifa_x_mil: 10.0 },
    { concepto: 'Transporte Servicios', base_uvt: 2, tarifa_porcentaje: 0.60, tarifa_x_mil: 6.0 },
    { concepto: 'Arrendamiento Maquinaria/Equipo (Muebles)', base_uvt: 4, tarifa_porcentaje: 0.60, tarifa_x_mil: 6.0 }, // Invest: Res 1535 6x1000
    { concepto: 'Arrendamiento Bienes Inmuebles (Servicio)', base_uvt: 4, tarifa_porcentaje: 1.00, tarifa_x_mil: 10.0 }, // Generalmente servicio
    { concepto: 'Arrendamiento (Tarifa Comercial General)', base_uvt: 27, tarifa_porcentaje: 0.50, tarifa_x_mil: 5.0 }, // Fuente Usuario
    { concepto: 'Actividades Financieras', base_uvt: 0, tarifa_porcentaje: 0.40, tarifa_x_mil: 4.0 },
    { concepto: 'Otros (Actividad Desconocida / Tarifa Máxima)', base_uvt: 4, tarifa_porcentaje: 1.00, tarifa_x_mil: 10.0 }
];

export const RETEICA_BASES = {
    COMPRAS: 27,
    SERVICIOS: 4
};

export const calculateTaxBase = (baseUvt, uvtValue) => {
    return Math.ceil((baseUvt * uvtValue) / 1000) * 1000;
};
