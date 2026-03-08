/*
 * functions.v108.js
 * Lógica detrás de las fórmulas nativas de Excel (Ej. =FINAXIS.SALDO)
 */

console.log("Finaxis Functions (v108): Iniciando carga...");
function debugFuncLog(msg) {
    console.log("FUNC_DEBUG (v108): " + msg);
}

var API_BASE_URL = "https://finaxis.onrender.com";

/**
 * Prueba de conexión.
 * @customfunction
 * @returns {string} Mensaje de saludo.
 */
function hola() {
    return "¡Hola desde Finaxis! Conexión Exitosa.";
}

/**
 * Obtiene el saldo de una cuenta contable desde Finaxis.
 * @customfunction
 * @param {string} cuenta El código de la cuenta contable (ej. '110505').
 * @param {string} [periodo] El periodo hasta el cual calcular en formato AAAA-MM.
 * @returns {Promise<number>} El saldo calculado.
 */
async function saldo(cuenta, periodo) {
    debugFuncLog("Consultando saldo para cuenta: " + cuenta);
    let token = null;
    try {
        token = await OfficeRuntime.storage.getItem("finaxis_token");
    } catch (e) {
        throw new CustomFunctions.Error(CustomFunctions.ErrorCode.notAvailable, "Error leyendo Storage");
    }

    if (!token) {
        throw new CustomFunctions.Error(CustomFunctions.ErrorCode.notAvailable, "Inicie sesión en el Panel lateral.");
    }

    let url = `${API_BASE_URL}/api/excel/saldo?cuenta=${encodeURIComponent(cuenta)}`;
    if (periodo) {
        url += `&periodo=${encodeURIComponent(periodo)}`;
    }

    try {
        const response = await fetch(url, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (!response.ok) {
            throw new CustomFunctions.Error(CustomFunctions.ErrorCode.invalidValue, "Error HTTP " + response.status);
        }

        const data = await response.json();
        return data.saldo;

    } catch (error) {
        if (error instanceof CustomFunctions.Error) throw error;
        throw new CustomFunctions.Error(CustomFunctions.ErrorCode.notAvailable, "Error de red.");
    }
}

// Registro global
try {
    CustomFunctions.associate("SALDO", saldo);
    CustomFunctions.associate("HOLA", hola);
    console.log("Asociación de funciones v108 (SALDO, HOLA) completada.");
} catch (e) {
    console.error("ERROR asociando funciones v108: " + e.message);
}
