/*
 * functions.js
 * Lógica detrás de las fórmulas nativas de Excel (Ej. =FINAXIS.SALDO)
 */

console.log("Finaxis Functions: Iniciando carga de funciones.js...");
function debugFuncLog(msg) {
    console.log("FUNC_DEBUG: " + msg);
}

var API_BASE_URL = "https://finaxis.onrender.com"; // Usar var en Shared Runtime

/**
 * Obtiene el saldo de una cuenta contable desde Finaxis.
 * @customfunction
 * @param {string} cuenta El código de la cuenta contable (ej. '110505').
 * @param {string} [periodo] El periodo hasta el cual calcular en formato AAAA-MM.
 * @returns {Promise<number>} El saldo calculado.
 */
async function saldo(cuenta, periodo) {
    // 1. Obtener Token y Empresa Activa desde el Storage Compartido con el panel
    let token = null;
    let empresaId = null;

    try {
        token = await OfficeRuntime.storage.getItem("finaxis_token");
        empresaId = await OfficeRuntime.storage.getItem("finaxis_active_empresa_id");
    } catch (e) {
        throw new CustomFunctions.Error(CustomFunctions.ErrorCode.notAvailable, "Error leyendo Storage");
    }

    if (!token) {
        // En Excel, si lanzamos este error, la celda mostrará #BUSY! o #VALUE!
        throw new CustomFunctions.Error(CustomFunctions.ErrorCode.notAvailable, "Inicie sesión en el Panel lateral de Finaxis primero.");
    }

    // 2. Construir la URL de consulta
    let url = `${API_BASE_URL}/api/excel/saldo?cuenta=${encodeURIComponent(cuenta)}`;
    if (periodo) {
        url += `&periodo=${encodeURIComponent(periodo)}`;
    }

    // 3. Consultar al Backend de Finaxis
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30s timeout para fórmulas
    let response;

    try {
        response = await fetch(url, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            },
            signal: controller.signal
        });
        clearTimeout(timeoutId);

        if (!response.ok) {
            if (response.status === 401) {
                // Token expirado o inválido
                throw new CustomFunctions.Error(CustomFunctions.ErrorCode.notAvailable, "La sesión expiró. Vuelva a conectarse en el panel.");
            }
            throw new CustomFunctions.Error(CustomFunctions.ErrorCode.invalidValue, "Error consultando saldo (HTTP " + response.status + ").");
        }

        const data = await response.json();

        // 4. Retornamos limpiamente el número a Excel
        return data.saldo;

    } catch (error) {
        clearTimeout(timeoutId);
        // Si el fetch falla por red (Render dormido, sin internet, etc)
        if (error instanceof CustomFunctions.Error) {
            throw error;
        }
        if (error.name === 'AbortError') {
            throw new CustomFunctions.Error(CustomFunctions.ErrorCode.notAvailable, "Timeout: El servidor Finaxis tardó demasiado.");
        }
        throw new CustomFunctions.Error(CustomFunctions.ErrorCode.notAvailable, "Error de red conectando a Finaxis.");
    }
}

// Registro global de la función para el entorno de Excel MS
try {
    CustomFunctions.associate("SALDO", saldo);
    console.log("Asociación de funciones 'SALDO' completada con éxito.");
} catch (e) {
    console.error("ERROR FATAL asociando funciones: " + e.message);
}
