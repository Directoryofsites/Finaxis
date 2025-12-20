// frontend/app/admin/tipos-documento/disenar/[id]/page.js
'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAuth } from '../../../../context/AuthContext';
import { apiService } from '../../../../../lib/apiService';


import {
    FaPalette, FaCode, FaSave, FaEye, FaMagic,
    FaSyncAlt
} from 'react-icons/fa';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// =============================================================================
// 🧠 GENERADOR DE PLANTILLA BASE (Tu diseño personalizado por defecto)
// =============================================================================
const generarPlantillaBase = (config) => {
    // NOTA: Usamos tu diseño de CC/Factura como base limpia
    return `<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: 'Helvetica', sans-serif; font-size: 11px; color: #333; margin: 0; padding: 20px; }
        .header-table { width: 100%; border-bottom: 2px solid ${config.colorPrincipal || '#333'}; padding-bottom: 10px; margin-bottom: 20px; }
        .company-name { font-size: 16px; font-weight: bold; text-transform: uppercase; }
        .doc-type-box { background: #eee; padding: 8px; border: 1px solid #ccc; text-align: right; font-weight: bold; font-size: 14px; text-transform: uppercase; width: 100%; box-sizing: border-box; }
        .doc-number { color: #d32f2f; font-size: 16px; font-weight: bold; text-align: right; margin-top: 5px; }
        .info-box { background: #f9f9f9; padding: 10px; border: 1px solid #ddd; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        th { background: ${config.colorPrincipal || '#333'}; color: white; padding: 5px; text-align: left; font-size: 10px; }
        td { padding: 5px; border-bottom: 1px solid #eee; }
        .text-right { text-align: right; }
        .font-mono { font-family: 'Courier New', monospace; }
        .footer-totals { background: #f0f0f0; font-weight: bold; }
        .footer-totals td { border-top: 2px solid #333; }
        .letras-row td { background: #fff; padding-top: 10px; font-style: italic; border: none; }
        .signatures { margin-top: 50px; width: 100%; display: table; }
        .sig-col { display: table-cell; width: 25%; text-align: center; vertical-align: bottom; height: 40px; }
        .sig-line { border-top: 1px solid #333; margin: 0 10px; padding-top: 5px; font-size: 10px; font-weight: bold; }
    </style>
</head>
<body>
    <table class="header-table">
        <tr>
            <td width="60%" valign="top">
                {% if empresa.logo_url %}
                    <img src="{{empresa.logo_url}}" style="max-height: 60px; margin-bottom: 5px;"><br>
                {% endif %}
                <div class="company-name">{{empresa.razon_social}}</div>
                <div>NIT: {{empresa.nit}}</div>
                <div>{{empresa.direccion}}</div>
                <div>{{empresa.telefono}}</div>
            </td>
            <td width="40%" valign="top" align="right">
                <div class="doc-type-box">{{documento.tipo_nombre}}</div>
                <div class="doc-number">N° {{documento.consecutivo}}</div>
                <div style="text-align: right; margin-top: 5px;">Fecha: <strong>{{documento.fecha_emision}}</strong></div>
            </td>
        </tr>
    </table>

    <div class="info-box">
        <table style="width: 100%; margin: 0;">
            <tr>
                <td width="15%"><strong>Tercero:</strong></td>
                <td width="45%">{{tercero.razon_social}}</td>
                <td width="15%"><strong>NIT/CC:</strong></td>
                <td width="25%">{{tercero.nit}}</td>
            </tr>
            {% if documento.observaciones %}
            <tr>
                <td colspan="4" style="border-top: 1px dashed #ccc; padding-top: 5px;">
                    <strong>Notas:</strong> {{documento.observaciones}}
                </td>
            </tr>
            {% endif %}
        </table>
    </div>

    <table>
        <thead>
            <tr>
                <th width="15%">Cuenta</th>
                <th width="45%">Descripción</th>
                <th width="20%" class="text-right">Débito</th>
                <th width="20%" class="text-right">Crédito</th>
            </tr>
        </thead>
        <tbody>
            {% for item in items %}
            <tr>
                <td class="font-mono">{{item.producto_codigo}}</td>
                <td>{{item.producto_nombre}}</td>
                <td class="text-right font-mono">{{item.debito_fmt}}</td>
                <td class="text-right font-mono">{{item.credito_fmt}}</td>
            </tr>
            {% endfor %}
            <tr class="footer-totals">
                <td colspan="2" class="text-right">SUMAS IGUALES:</td>
                <td class="text-right font-mono">{{totales.total_debito}}</td>
                <td class="text-right font-mono">{{totales.total_credito}}</td>
            </tr>
            <tr class="letras-row">
                <td colspan="4"><strong>SON:</strong> {{totales.valor_letras}}</td>
            </tr>
        </tbody>
    </table>

    <div class="signatures">
        <div class="sig-col"><div class="sig-line">Elaboró</div></div>
        <div class="sig-col"><div class="sig-line">Revisó</div></div>
        <div class="sig-col"><div class="sig-line">Aprobó</div></div>
        <div class="sig-col"><div class="sig-line">Contabilizó</div></div>
    </div>

    <div style="text-align: center; font-size: 9px; color: #aaa; margin-top: 20px;">
        ${config.notaPie || 'Impreso por Sistema ContaPY'}
    </div>
</body>
</html>`;
};

export default function DisenarFormatoHibridoPage() {
    const router = useRouter();
    const params = useParams();
    const tipoDocumentoId = params.id;
    const { user, loading: authLoading } = useAuth();

    // Estados
    const [mode, setMode] = useState('visual');
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [formatoId, setFormatoId] = useState(null);
    const [tipoDocNombre, setTipoDocNombre] = useState(''); // Nuevo estado para el nombre real

    // Estado Visual
    const [visualConfig, setVisualConfig] = useState({
        colorPrincipal: '#333333',
        tituloDocumento: 'DOCUMENTO',
        logoUrl: '',
        notaPie: 'Gracias por su confianza.'
    });

    // Estado Código
    const [htmlCode, setHtmlCode] = useState('');
    const [previewHtml, setPreviewHtml] = useState('');

    // --- CARGA INICIAL INTELIGENTE ---
    useEffect(() => {
        if (tipoDocumentoId && user && !authLoading) {
            const cargarDatos = async () => {
                try {
                    // 1. Cargar Info del Tipo de Documento (Para saber cómo se llama realmente)
                    const resTipoDoc = await apiService.get(`/tipos-documento/${tipoDocumentoId}`);
                    const nombreReal = resTipoDoc.data.nombre || 'DOCUMENTO';
                    setTipoDocNombre(nombreReal);

                    // 2. Cargar Formato existente (si hay)
                    const resFormato = await apiService.get(`/formatos-impresion?tipo_documento_id=${tipoDocumentoId}`);

                    if (resFormato.data && resFormato.data.length > 0) {
                        const formato = resFormato.data[0];
                        setFormatoId(formato.id);

                        if (formato.variables_ejemplo_json && formato.variables_ejemplo_json.visualConfig) {
                            setVisualConfig(formato.variables_ejemplo_json.visualConfig);
                        }
                        setHtmlCode(formato.contenido_html);
                    } else {
                        // 3. Si es NUEVO, usamos el nombre real en la config inicial
                        const configInicial = {
                            ...visualConfig,
                            tituloDocumento: nombreReal.toUpperCase()
                        };
                        setVisualConfig(configInicial);
                        const baseHtml = generarPlantillaBase(configInicial);
                        setHtmlCode(baseHtml);
                    }
                } catch (error) {
                    console.error(error);
                    toast.error("Error cargando datos.");
                } finally {
                    setIsLoading(false);
                }
            };
            cargarDatos();
        }
    }, [tipoDocumentoId, user, authLoading]);

    // --- PREVIEW ---
    useEffect(() => {
        actualizarPreview(htmlCode);
    }, [htmlCode]);

    const actualizarPreview = (html) => {
        // Datos Dummy para previsualizar
        let dummy = html
            .replace(/{{empresa.razon_social}}/g, "MI EMPRESA S.A.S")
            .replace(/{{empresa.nit}}/g, "900.123.456-7")
            .replace(/{{empresa.direccion}}/g, "Calle 123 # 45-67")
            .replace(/{{empresa.telefono}}/g, "(601) 555-5555")
            .replace(/{{empresa.logo_url}}/g, "/logo.png")
            .replace(/{{documento.tipo_nombre}}/g, visualConfig.tituloDocumento || "COMPROBANTE")
            .replace(/{{documento.consecutivo}}/g, "1045")
            .replace(/{{documento.fecha_emision}}/g, "24/11/2025")
            .replace(/{{tercero.razon_social}}/g, "CLIENTE EJEMPLO LTDA")
            .replace(/{{tercero.nit}}/g, "800.987.654-3")
            .replace(/{{documento.observaciones}}/g, "Pago correspondiente a servicios del mes.")
            .replace(/{{totales.total_debito}}/g, "$ 500,000")
            .replace(/{{totales.total_credito}}/g, "$ 500,000")
            .replace(/{{totales.valor_letras}}/g, "QUINIENTOS MIL PESOS M/CTE");

        const filas = `
            <tr><td class="font-mono">110505</td><td>Caja General</td><td class="text-right font-mono">$ 250,000</td><td class="text-right font-mono">0</td></tr>
            <tr><td class="font-mono">130505</td><td>Clientes Nacionales</td><td class="text-right font-mono">0</td><td class="text-right font-mono">$ 250,000</td></tr>
        `;
        dummy = dummy.replace(/{% for item in items %}[\s\S]*?{% endfor %}/, filas);
        setPreviewHtml(dummy);
    };

    // --- HANDLERS ---
    const handleVisualChange = (e) => {
        const { name, value } = e.target;
        setVisualConfig(prev => ({ ...prev, [name]: value }));
    };

    const aplicarCambiosVisuales = () => {
        if (window.confirm("⚠️ Esto sobrescribirá tu código HTML con la plantilla base. ¿Continuar?")) {
            const nuevoHtml = generarPlantillaBase(visualConfig);
            setHtmlCode(nuevoHtml);
            toast.info("Plantilla regenerada.");
        }
    };

    const handleSave = async () => {
        setIsSaving(true);
        try {
            // CORRECCIÓN CRÍTICA: NOMBRE ÚNICO PARA EVITAR ERROR DE BD
            // Agregamos el ID del tipo de documento al nombre para que sea único por empresa/tipo.
            const nombreUnicoDB = `Formato ${visualConfig.tituloDocumento} (${tipoDocumentoId})`;

            const payload = {
                tipo_documento_id: parseInt(tipoDocumentoId),
                empresa_id: user.empresaId,
                nombre: nombreUnicoDB, // <--- AQUÍ ESTÁ LA SOLUCIÓN AL ERROR DE DUPLICADO
                contenido_html: htmlCode,
                variables_ejemplo_json: { visualConfig }
            };

            if (formatoId) {
                await apiService.put(`/formatos-impresion/${formatoId}`, payload);
            } else {
                const res = await apiService.post('/formatos-impresion/', payload);
                setFormatoId(res.data.id);
            }
            toast.success("Diseño guardado exitosamente.");
        } catch (error) {
            console.error(error);
            // Mostrar error legible si es duplicado
            if (error.response?.data?.detail?.includes("UniqueViolation")) {
                toast.error("Error: Ya existe un formato con este nombre. Intenta cambiar el título.");
            } else {
                toast.error("Error al guardar el diseño.");
            }
        } finally {
            setIsSaving(false);
        }
    };

    if (authLoading || isLoading) return <div className="h-screen flex items-center justify-center"><span className="loading loading-spinner text-indigo-600"></span></div>;

    return (
        <div className="min-h-screen bg-gray-50 p-4 font-sans pb-20">
            <ToastContainer />

            <div className="max-w-7xl mx-auto flex justify-between items-center mb-6">
                <div className="flex items-center gap-3">
                    <div className="p-3 bg-indigo-100 text-indigo-600 rounded-xl shadow-sm">
                        <FaMagic className="text-2xl" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-gray-800">Diseñador: {tipoDocNombre}</h1>
                        <p className="text-gray-500 text-sm">Personaliza la apariencia de tus documentos.</p>
                    </div>
                </div>
                <div className="flex gap-2">

                    <button onClick={handleSave} disabled={isSaving} className="btn btn-primary bg-indigo-600 text-white gap-2 shadow-lg">
                        <FaSave /> {isSaving ? 'Guardando...' : 'Guardar Diseño'}
                    </button>
                </div>
            </div>

            <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-6 h-[85vh]">

                {/* EDITOR */}
                <div className="flex flex-col bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
                    <div className="flex border-b border-gray-200 bg-gray-50">
                        <button onClick={() => setMode('visual')} className={`flex-1 py-3 text-sm font-bold flex items-center justify-center gap-2 ${mode === 'visual' ? 'bg-white text-indigo-600 border-t-2 border-indigo-600' : 'text-gray-500 hover:bg-gray-100'}`}>
                            <FaPalette /> Visual
                        </button>
                        <button onClick={() => setMode('code')} className={`flex-1 py-3 text-sm font-bold flex items-center justify-center gap-2 ${mode === 'code' ? 'bg-white text-indigo-600 border-t-2 border-indigo-600' : 'text-gray-500 hover:bg-gray-100'}`}>
                            <FaCode /> HTML (Avanzado)
                        </button>
                    </div>

                    <div className="flex-1 overflow-y-auto p-6">
                        {mode === 'visual' ? (
                            <div className="space-y-6">
                                <div className="alert alert-info text-xs shadow-sm">
                                    <FaSyncAlt /> Define colores y textos. Luego pulsa <strong>"Aplicar al HTML"</strong>.
                                </div>
                                <div>
                                    <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Título Visible</label>
                                    <input type="text" name="tituloDocumento" value={visualConfig.tituloDocumento} onChange={handleVisualChange} className="input input-bordered w-full input-sm" />
                                </div>
                                <div>
                                    <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Color Principal</label>
                                    <div className="flex gap-2">
                                        <input type="color" name="colorPrincipal" value={visualConfig.colorPrincipal} onChange={handleVisualChange} className="h-8 w-12 p-0 border-0 cursor-pointer" />
                                        <input type="text" name="colorPrincipal" value={visualConfig.colorPrincipal} onChange={handleVisualChange} className="input input-bordered w-full input-sm" />
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Pie de Página</label>
                                    <textarea name="notaPie" value={visualConfig.notaPie} onChange={handleVisualChange} className="textarea textarea-bordered w-full" rows="2"></textarea>
                                </div>
                                <button onClick={aplicarCambiosVisuales} className="btn btn-outline btn-indigo w-full gap-2 mt-4 btn-sm">
                                    <FaSyncAlt /> Aplicar Configuración Visual
                                </button>
                            </div>
                        ) : (
                            <div className="h-full flex flex-col">
                                <textarea
                                    className="flex-1 w-full font-mono text-xs p-4 bg-slate-900 text-green-400 rounded-lg focus:outline-none resize-none leading-relaxed"
                                    value={htmlCode}
                                    onChange={(e) => setHtmlCode(e.target.value)}
                                    spellCheck="false"
                                ></textarea>
                            </div>
                        )}
                    </div>
                </div>

                {/* PREVIEW */}
                <div className="bg-gray-200 rounded-xl p-8 flex justify-center overflow-y-auto shadow-inner relative">
                    <div className="absolute top-4 right-4 bg-white/90 px-3 py-1 rounded-full text-xs font-bold text-gray-500 shadow-sm flex items-center gap-2 z-10">
                        <FaEye /> Vista Previa
                    </div>
                    <div
                        className="bg-white shadow-2xl origin-top transform scale-90 lg:scale-100"
                        style={{ width: '210mm', minHeight: '297mm', padding: '15mm' }}
                        dangerouslySetInnerHTML={{ __html: previewHtml }}
                    />
                </div>
            </div>
        </div>
    );
}