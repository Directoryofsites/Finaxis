var API_BASE_URL = "https://finaxis.onrender.com"; // Usar var para no chocar con functions.js

function log(msg) {
    const debug = document.getElementById("debug-log");
    if (debug) {
        debug.innerText += "\n> " + msg;
    }
    console.log(msg);
}

window.onerror = function (message, source, lineno, colno, error) {
    log("ERROR JS: " + message + " en " + lineno);
};

Office.onReady((info) => {
    log("Office.onReady disparado. Host: " + info.host);
    const loginBtn = document.getElementById("login-btn");

    // Indicador visual crítico para confirmar que el JS cargó
    loginBtn.innerText = "Conectar a Finaxis (Listo)";
    loginBtn.onclick = attemptLogin;

    document.getElementById("logout-btn").onclick = logout;
    document.getElementById("empresa-select").onchange = updateActiveCompany;

    checkExistingSession();
});

async function attemptLogin() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const errorMsg = document.getElementById("login-error");
    const btn = document.getElementById("login-btn");

    if (!email || !password) {
        errorMsg.innerText = "Por favor ingrese ambos campos.";
        return;
    }

    try {
        errorMsg.innerText = "";
        btn.innerText = "Conectando (Despertando servidor, puede tardar 1 min)...";
        btn.disabled = true;

        const formData = new URLSearchParams();
        formData.append("username", email);
        formData.append("password", password);

        // Controlador de Timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 segundos de timeout

        let response;
        try {
            // Usamos la API Optimizada de Excel
            response = await fetch(`${API_BASE_URL}/api/excel/auth`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                body: formData,
                signal: controller.signal
            });
            clearTimeout(timeoutId);
        } catch (fetchError) {
            clearTimeout(timeoutId);
            if (fetchError.name === 'AbortError') {
                throw new Error("El servidor tardó demasiado en responder (Timeout). Es posible que esté 'dormido'. Por favor, intente conectar de nuevo en unos segundos.");
            }
            throw new Error("Error de red: No se pudo conectar con el servidor Finaxis. Compruebe su conexión.");
        }

        if (!response.ok) {
            let serverError = "Credenciales incorrectas o error en el servidor";
            try {
                const errorData = await response.json();
                serverError = errorData.detail || serverError;
            } catch (e) { }
            throw new Error(serverError);
        }

        const data = await response.json();

        // Guardamos el Session State en OfficeRuntime.storage (SharedRuntime seguro)
        await OfficeRuntime.storage.setItem("finaxis_token", data.access_token);
        await OfficeRuntime.storage.setItem("finaxis_empresas", JSON.stringify(data.empresas));

        // Predeterminamos la primera empresa
        if (data.empresas && data.empresas.length > 0) {
            await OfficeRuntime.storage.setItem("finaxis_active_empresa_id", data.empresas[0].id.toString());
        }

        showDashboard(data.usuario, data.empresas);

    } catch (error) {
        log("Login Error: " + error.message);
        errorMsg.innerText = error.message;
    } finally {
        btn.innerText = "Conectar";
        btn.disabled = false;
    }
}

async function checkExistingSession() {
    try {
        const token = await OfficeRuntime.storage.getItem("finaxis_token");
        const empresasStr = await OfficeRuntime.storage.getItem("finaxis_empresas");

        if (token && empresasStr) {
            const empresas = JSON.parse(empresasStr);
            // Por simplicidad, si hay token asumimos que está activo. 
            // Si la API falla después, la fórmula devolverá ERROR y el usuario deberá volver a loguearse.
            showDashboard("Usuario Contable", empresas);
        }
    } catch (e) {
        log("No hay sesión guardada o error leyendo storage: " + e.message);
    }
}

function showDashboard(nombre, empresas) {
    document.getElementById("login-container").classList.remove("active");
    document.getElementById("dashboard-container").classList.add("active");

    document.getElementById("user-display").innerText = nombre || "Usuario(a)";

    // Poblar Selector de Empresas
    const select = document.getElementById("empresa-select");
    select.innerHTML = "";
    empresas.forEach(emp => {
        let opt = document.createElement("option");
        opt.value = emp.id;
        opt.innerText = emp.razon_social;
        select.appendChild(opt);
    });
}

async function updateActiveCompany() {
    const select = document.getElementById("empresa-select");
    const selectedId = select.value;
    await OfficeRuntime.storage.setItem("finaxis_active_empresa_id", selectedId);
}

async function logout() {
    await OfficeRuntime.storage.removeItem("finaxis_token");
    await OfficeRuntime.storage.removeItem("finaxis_empresas");
    await OfficeRuntime.storage.removeItem("finaxis_active_empresa_id");

    document.getElementById("dashboard-container").classList.remove("active");
    document.getElementById("login-container").classList.add("active");
    document.getElementById("password").value = "";
}
