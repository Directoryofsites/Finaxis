"use client";
import React, { useState, useEffect } from 'react';
import { FaFilePdf, FaDownload, FaCheckCircle, FaHistory, FaPrint } from 'react-icons/fa';
import { toast } from 'react-toastify';

export default function DeclaracionView({ impuesto }) {
    const [historial, setHistorial] = useState([]);
    const [loading, setLoading] = useState(false);

    // Load history from localStorage
    useEffect(() => {
        if (typeof window !== 'undefined' && impuesto) {
            const saved = localStorage.getItem(`impuestos_historial_${impuesto}`);
            if (saved) {
                setHistorial(JSON.parse(saved));
            }
        }
    }, [impuesto]);

    const handleGenerate = async (tipo) => {
        setLoading(true);
        toast.info(`Generando ${tipo} definitivo...`);

        // 1. Get Data
        const savedBorrador = localStorage.getItem(`impuestos_borrador_${impuesto}`);
        const rows = savedBorrador ? JSON.parse(savedBorrador) : [];
        const empresa = "EMPRESA DE PRUEBA S.A.S"; // Should come from context
        const nit = "900.123.456-7";
        const periodo = "2025 - Bimestre 1";

        if (rows.length === 0) {
            toast.error("No hay datos en el borrador para generar la declaración.");
            setLoading(false);
            return;
        }

        try {
            if (tipo === 'PDF') {
                // Dynamic import to avoid SSR issues
                const jsPDF = (await import('jspdf')).default;
                const autoTable = (await import('jspdf-autotable')).default;

                const doc = new jsPDF();

                // Header
                doc.setFontSize(16);
                doc.text(`Declaración de ${impuesto}`, 105, 15, { align: 'center' });
                doc.setFontSize(10);
                doc.text(`Contribuyente: ${empresa}`, 14, 25);
                doc.text(`NIT: ${nit}`, 14, 30);
                doc.text(`Periodo: ${periodo}`, 14, 35);
                doc.text(`Fecha Generación: ${new Date().toLocaleDateString()}`, 14, 40);

                // Table
                const tableBody = rows.map(r => [r.r, r.c, `$ ${r.v.toLocaleString('es-CO')}`]);

                autoTable(doc, {
                    startY: 45,
                    head: [['Renglón', 'Concepto', 'Valor']],
                    body: tableBody,
                    theme: 'grid',
                    headStyles: { fillColor: [22, 163, 74] }, // Green header
                });

                // Footer
                const finalY = doc.lastAutoTable.finalY + 10;
                doc.text("Firma del Declarante:", 14, finalY + 20);
                doc.line(14, finalY + 19, 80, finalY + 19);

                doc.text("Firma del Contador/Revisor Fiscal:", 110, finalY + 20);
                doc.line(110, finalY + 19, 180, finalY + 19);

                doc.save(`Declaracion_${impuesto}_${Date.now()}.pdf`);

            } else if (tipo === 'XML') {
                // Simple XML construction
                let xmlContent = `<?xml version="1.0" encoding="UTF-8"?>\n`;
                xmlContent += `<Declaracion tipo="${impuesto}">\n`;
                xmlContent += `  <Encabezado>\n`;
                xmlContent += `    <Empresa>${empresa}</Empresa>\n`;
                xmlContent += `    <NIT>${nit}</NIT>\n`;
                xmlContent += `    <Periodo>${periodo}</Periodo>\n`;
                xmlContent += `    <Fecha>${new Date().toISOString()}</Fecha>\n`;
                xmlContent += `  </Encabezado>\n`;
                xmlContent += `  <Detalle>\n`;

                rows.forEach(r => {
                    xmlContent += `    <Renglon id="${r.r}">\n`;
                    xmlContent += `      <Concepto>${r.c}</Concepto>\n`;
                    xmlContent += `      <Valor>${r.v}</Valor>\n`;
                    xmlContent += `    </Renglon>\n`;
                });

                xmlContent += `  </Detalle>\n`;
                xmlContent += `</Declaracion>`;

                const blob = new Blob([xmlContent], { type: 'application/xml' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `Declaracion_${impuesto}_${Date.now()}.xml`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }

            // Register in History
            const nuevoRegistro = {
                id: Date.now(),
                periodo: periodo,
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
            {/* Estado Actual */}
            <div className="bg-white p-6 rounded-lg shadow-md">
                <h2 className="text-xl font-semibold text-gray-800 mb-4">Declaración y Presentación - {impuesto}</h2>

                <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
                    <div className="flex">
                        <div className="flex-shrink-0">
                            <FaCheckCircle className="h-5 w-5 text-yellow-400" />
                        </div>
                        <div className="ml-3">
                            <p className="text-sm text-yellow-700">
                                El formulario está listo para presentación. Por favor verifique los valores antes de generar el archivo definitivo.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Formulario Final (Read Only Placeholder) */}
                <div className="border rounded-lg p-8 bg-gray-50 mb-6 flex flex-col items-center justify-center text-gray-400 border-dashed border-2 border-gray-300">
                    <FaPrint size={48} className="mb-2" />
                    <p className="text-lg font-medium">Vista Previa del Formulario DIAN</p>
                    <p className="text-sm">(Los valores se toman del Borrador aprobado)</p>
                </div>

                <div className="flex space-x-4">
                    <button
                        onClick={() => handleGenerate('PDF')}
                        disabled={loading}
                        className={`flex-1 bg-green-600 text-white py-3 rounded-md hover:bg-green-700 font-semibold flex justify-center items-center ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                        <FaFilePdf className="mr-2" /> {loading ? 'Procesando...' : 'Generar PDF Definitivo'}
                    </button>
                    <button
                        onClick={() => handleGenerate('XML')}
                        disabled={loading}
                        className={`flex-1 bg-indigo-600 text-white py-3 rounded-md hover:bg-indigo-700 font-semibold flex justify-center items-center ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                        <FaDownload className="mr-2" /> {loading ? 'Procesando...' : 'Descargar XML / Archivo DIAN'}
                    </button>
                </div>
            </div>

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
