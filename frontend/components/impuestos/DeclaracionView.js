"use client";
import React, { useState, useEffect } from 'react';
import { FaFilePdf, FaDownload, FaCheckCircle, FaHistory, FaPrint } from 'react-icons/fa';
import { toast } from 'react-toastify';

import { apiService } from '../../lib/apiService';

export default function DeclaracionView({ impuesto }) {
    const [historial, setHistorial] = useState([]);
    const [loading, setLoading] = useState(false);
    const [datosCalculados, setDatosCalculados] = useState(null);

    // Selectors State
    const [anio, setAnio] = useState(new Date().getFullYear());
    const [periodo, setPeriodo] = useState('01');
    const [periodoConfig, setPeriodoConfig] = useState('Bimestral');

    // Load Period Config
    useEffect(() => {
        if (impuesto) {
            const savedPeriod = localStorage.getItem(`impuestos_periodicidad_${impuesto}`);
            if (savedPeriod) {
                setPeriodoConfig(savedPeriod);
            }
        }
    }, [impuesto]);

    // Load history from localStorage
    useEffect(() => {
        if (typeof window !== 'undefined' && impuesto) {
            const saved = localStorage.getItem(`impuestos_historial_${impuesto}`);
            if (saved) {
                setHistorial(JSON.parse(saved));
            }
        }
    }, [impuesto]);

    // Auto-select Annual period for Renta
    useEffect(() => {
        if (impuesto === 'renta') {
            setPeriodo('00');
        } else {
            setPeriodo('01');
        }
    }, [impuesto]);

    const handleCalcular = async () => {
        setLoading(true);
        try {
            const res = await apiService.get(`/impuestos/declaracion/${impuesto.toUpperCase()}`, {
                params: { anio, periodo }
            });
            setDatosCalculados(res.data);
            toast.success("Cálculo realizado exitosamente.");
        } catch (error) {
            console.error(error);
            toast.error("Error al calcular la declaración.");
        } finally {
            setLoading(false);
        }
    };

    const handleGenerate = async (tipo) => {
        if (!datosCalculados) {
            toast.warn("Primero debe calcular la declaración.");
            return;
        }

        setLoading(true);
        toast.info(`Generando ${tipo} definitivo...`);

        const rows = datosCalculados.renglones;
        const empresa = "EMPRESA DE PRUEBA S.A.S"; // Context
        const nit = "900.123.456-7"; // Context
        const periodoTexto = impuesto === 'renta' ? `${anio} - Anual` :
            impuesto === 'iva' ? `${anio} - Bimestre ${periodo}` :
                `${anio} - Mes ${periodo}`;

        try {
            if (tipo === 'PDF') {
                const jsPDF = (await import('jspdf')).default;
                const autoTable = (await import('jspdf-autotable')).default;

                const doc = new jsPDF();
                // ... (PDF Generation Logic - Same as before but using rows from API)
                doc.setFontSize(16);
                doc.text(`Declaración de ${impuesto}`, 105, 15, { align: 'center' });
                doc.setFontSize(10);
                doc.text(`Contribuyente: ${empresa}`, 14, 25);
                doc.text(`NIT: ${nit}`, 14, 30);
                doc.text(`Periodo: ${periodoTexto}`, 14, 35);
                doc.text(`Desde: ${datosCalculados.fecha_inicio} Hasta: ${datosCalculados.fecha_fin}`, 14, 40);

                const tableBody = rows.map(r => {
                    if (r.is_header) {
                        return [{ content: r.c, colSpan: 3, styles: { fontStyle: 'bold', fillColor: [240, 240, 240], halign: 'left' } }];
                    }
                    return [r.r, r.c, `$ ${r.v.toLocaleString('es-CO')}`];
                });

                autoTable(doc, {
                    startY: 45,
                    head: [['Renglón', 'Concepto', 'Valor']],
                    body: tableBody,
                    theme: 'grid',
                    headStyles: { fillColor: [22, 163, 74] },
                });

                // Footer lines - Ajustadas firmas (Línea más arriba)
                const finalY = doc.lastAutoTable.finalY + 10;

                // Líneas de firma (Subidas 2 filas visuales, aprox 15-20 pts)
                doc.line(14, finalY + 15, 80, finalY + 15); // Antes +19
                doc.text("Firma del Declarante", 14, finalY + 22); // Antes +20 (Texto un poco más abajo de la línea)

                doc.line(110, finalY + 15, 180, finalY + 15);
                doc.text("Firma del Contador/Revisor Fiscal", 110, finalY + 22);

                doc.save(`Declaracion_${impuesto}_${anio}_${periodo}.pdf`);

            } else if (tipo === 'XML') {
                // ... (XML Logic)
                let xmlContent = `<?xml version="1.0" encoding="UTF-8"?>\n<Declaracion tipo="${impuesto}">\n`;
                // ... Add header ...
                xmlContent += `  <Detalle>\n`;
                rows.forEach(r => {
                    if (!r.is_header) { // Skip headers in XML usually? Or keep them? Keeping simple for now, maybe skip headers to avoid validation errors if strictly numeric.
                        xmlContent += `    <Renglon id="${r.r}"><Concepto>${r.c}</Concepto><Valor>${r.v}</Valor></Renglon>\n`;
                    }
                });
                xmlContent += `  </Detalle>\n</Declaracion>`;

                // Download blob...
                const blob = new Blob([xmlContent], { type: 'application/xml' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `Declaracion_${impuesto}_${anio}_${periodo}.xml`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }

            // Update History
            const nuevoRegistro = {
                id: Date.now(),
                periodo: periodoTexto,
                fecha: new Date().toISOString().split('T')[0],
                numero: Math.floor(Math.random() * 9000000000000) + 1000000000000,
                tipo: tipo
            };
            const nuevoHistorial = [nuevoRegistro, ...historial];
            setHistorial(nuevoHistorial);
            localStorage.setItem(`impuestos_historial_${impuesto}`, JSON.stringify(nuevoHistorial));

            toast.success(`Archivo ${tipo} generado exitosamente.`);

        } catch (error) {
            console.error(error);
            toast.error(`Error al generar ${tipo}.`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            {/* Panel de Cálculo */}
            <div className="bg-white p-6 rounded-lg shadow-md mb-6">
                <h2 className="text-xl font-semibold text-gray-800 mb-4">Generación de Declaración</h2>
                <div className="flex gap-4 items-end">
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Año Gravable</label>
                        <input type="number" value={anio} onChange={(e) => setAnio(e.target.value)} className="mt-1 block w-32 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border" />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">
                            {impuesto === 'renta' ? 'Periodo (Anual)' :
                                periodoConfig === 'Mensual' ? 'Periodo (Mes)' : 'Periodo (Bimestre)'}
                        </label>
                        <select value={periodo} onChange={(e) => setPeriodo(e.target.value)} className="mt-1 block w-48 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border">
                            {impuesto === 'renta' ? (
                                <option value="00">Anual (Ene - Dic)</option>
                            ) : periodoConfig === 'Mensual' ? (
                                <>
                                    <option value="01">01. Enero</option>
                                    <option value="02">02. Febrero</option>
                                    <option value="03">03. Marzo</option>
                                    <option value="04">04. Abril</option>
                                    <option value="05">05. Mayo</option>
                                    <option value="06">06. Junio</option>
                                    <option value="07">07. Julio</option>
                                    <option value="08">08. Agosto</option>
                                    <option value="09">09. Septiembre</option>
                                    <option value="10">10. Octubre</option>
                                    <option value="11">11. Noviembre</option>
                                    <option value="12">12. Diciembre</option>
                                </>
                            ) : (
                                <>
                                    <option value="01">01. Ene - Feb</option>
                                    <option value="02">02. Mar - Abr</option>
                                    <option value="03">03. May - Jun</option>
                                    <option value="04">04. Jul - Ago</option>
                                    <option value="05">05. Sep - Oct</option>
                                    <option value="06">06. Nov - Dic</option>
                                </>
                            )}
                        </select>
                    </div>
                    <button onClick={handleCalcular} disabled={loading} className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 font-semibold h-10 mb-0.5">
                        {loading ? 'Calculando...' : 'Calcular Valores'}
                    </button>
                </div>
            </div>

            {/* Resultado del Cálculo */}
            {datosCalculados && (
                <div className="bg-white p-6 rounded-lg shadow-md animate-fadeIn">
                    <h3 className="text-lg font-bold text-gray-700 mb-4 border-b pb-2">Valores Calculados (PUC)</h3>
                    <div className="overflow-x-auto mb-6">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-4 py-2 text-left text-xs font-bold text-gray-500 uppercase">Renglón</th>
                                    <th className="px-4 py-2 text-left text-xs font-bold text-gray-500 uppercase">Concepto</th>
                                    <th className="px-4 py-2 text-right text-xs font-bold text-gray-500 uppercase">Valor Calculado</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {datosCalculados.renglones.map((r, i) => {
                                    if (r.is_header) {
                                        return (
                                            <tr key={i} className="bg-gray-100">
                                                <td colSpan="3" className="px-4 py-3 font-bold text-gray-800 uppercase text-xs tracking-wider border-t border-b border-gray-200">
                                                    {r.c}
                                                </td>
                                            </tr>
                                        )
                                    }
                                    return (
                                        <tr key={i} className="hover:bg-gray-50">
                                            <td className="px-4 py-2 font-mono text-sm font-bold text-green-700 text-center">{r.r}</td>
                                            <td className="px-4 py-2 text-sm text-gray-700">{r.c}</td>
                                            <td className="px-4 py-2 text-right font-mono text-sm font-bold text-gray-900">
                                                $ {r.v.toLocaleString('es-CO')}
                                            </td>
                                        </tr>
                                    )
                                })}
                            </tbody>
                        </table>
                    </div>

                    <div className="flex space-x-4">
                        <button onClick={() => handleGenerate('PDF')} disabled={loading} className="flex-1 bg-green-600 text-white py-3 rounded-md hover:bg-green-700 font-semibold flex justify-center items-center">
                            <FaFilePdf className="mr-2" /> Generar PDF Definitivo
                        </button>
                        <button onClick={() => handleGenerate('XML')} disabled={loading} className="flex-1 bg-indigo-600 text-white py-3 rounded-md hover:bg-indigo-700 font-semibold flex justify-center items-center">
                            <FaDownload className="mr-2" /> Descargar XML DIAN
                        </button>
                    </div>
                </div>
            )}

            {/* Historial */}
            <div className="bg-white p-6 rounded-lg shadow-md">
                <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                    <FaHistory className="mr-2 text-blue-500" /> Historial de Presentaciones
                </h3>
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Periodo</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fecha Presentación</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Número Adhesivo</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo</th>
                                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Comprobante</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {historial.length === 0 ? (
                                <tr>
                                    <td colSpan="5" className="px-6 py-4 text-center text-gray-500 text-sm">No hay presentaciones registradas.</td>
                                </tr>
                            ) : (
                                historial.map((h) => (
                                    <tr key={h.id} className="hover:bg-gray-50">
                                        <td className="px-6 py-4 text-sm text-gray-900">{h.periodo}</td>
                                        <td className="px-6 py-4 text-sm text-gray-500">{h.fecha}</td>
                                        <td className="px-6 py-4 text-sm font-mono text-gray-600">{h.numero}</td>
                                        <td className="px-6 py-4 text-sm text-gray-500">{h.tipo}</td>
                                        <td className="px-6 py-4 text-right text-sm">
                                            <button
                                                onClick={() => toast.success(`Descargando comprobante ${h.numero}...`)}
                                                className="text-blue-600 hover:text-blue-900 font-semibold"
                                            >
                                                Descargar
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
