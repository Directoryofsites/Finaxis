import React, { useState, useEffect } from 'react';
import { FaPlus, FaTrash, FaEdit, FaSave, FaArrowLeft, FaFileExcel, FaExchangeAlt } from 'react-icons/fa';
import { apiService } from '../../../lib/apiService';
import Swal from 'sweetalert2';

export default function TemplateManager({ onSelectTemplate, onClose }) {
    const [view, setView] = useState('list'); // list, create, edit
    const [templates, setTemplates] = useState([]);
    const [loading, setLoading] = useState(false);

    // Form State
    const [currentTemplate, setCurrentTemplate] = useState({ nombre: '', descripcion: '', mapping_config: {} });
    const [previewHeaders, setPreviewHeaders] = useState([]);
    const [uploadingPreview, setUploadingPreview] = useState(false);

    useEffect(() => {
        fetchTemplates();
    }, []);

    const fetchTemplates = async () => {
        setLoading(true);
        try {
            const res = await apiService.get('/import-templates/');
            setTemplates(res.data);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleUploadPreview = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setUploadingPreview(true);
        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await apiService.post('/import-templates/preview-headers', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setPreviewHeaders(res.data);
            // Auto-map if headers match our keys exactly? 
            // Optional enhancement.
        } catch (error) {
            Swal.fire('Error', 'No se pudieron leer los encabezados del archivo', 'error');
        } finally {
            setUploadingPreview(false);
        }
    };

    const handleSave = async (e) => {
        e.preventDefault();

        // Basic Validation
        // Basic Validation
        const mapping = currentTemplate.mapping_config;
        const requiredFields = ['fecha', 'cuenta', 'debito', 'credito'];
        const missing = requiredFields.filter(f => mapping[f] === undefined || mapping[f] === null || mapping[f] === '');

        if (missing.length > 0) {
            Swal.fire('Error', 'Debes mapear al menos: Fecha, Cuenta, Débito y Crédito', 'warning');
            return;
        }

        try {
            if (currentTemplate.id) {
                await apiService.put(`/import-templates/${currentTemplate.id}`, currentTemplate);
                Swal.fire('Actualizado', 'Plantilla actualizada', 'success');
                if (onSelectTemplate) onSelectTemplate(currentTemplate.id);
            } else {
                const res = await apiService.post('/import-templates/', currentTemplate);
                Swal.fire('Creado', 'Plantilla creada correctamente', 'success');
                if (onSelectTemplate) onSelectTemplate(res.data.id);
            }
            setView('list');
            fetchTemplates();
        } catch (error) {
            Swal.fire('Error', 'Error al guardar la plantilla', 'error');
        }
    };

    const handleDelete = async (id) => {
        const result = await Swal.fire({
            title: '¿Eliminar plantilla?',
            text: "No podrás revertir esto",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Sí, eliminar'
        });

        if (result.isConfirmed) {
            try {
                await apiService.delete(`/import-templates/${id}`);
                fetchTemplates();
                Swal.fire('Eliminado', '', 'success');
            } catch (error) {
                Swal.fire('Error', 'No se pudo eliminar', 'error');
            }
        }
    };

    const openCreate = () => {
        setCurrentTemplate({ nombre: '', descripcion: '', mapping_config: {} });
        setPreviewHeaders([]);
        setView('create');
    };

    const openEdit = (tpl) => {
        setCurrentTemplate(tpl);
        // If editing, user might verify mapping manually or upload file again.
        // We set previewHeaders to empty initially or we could try to show indices?
        // Actually, without the file, we just show the Indices (0, 1, 2). 
        // If they want to remap visually, they should upload a file.
        setPreviewHeaders([]);
        setView('edit');
    };

    // Helper to convert 0-based index to Excel column (0->A, 1->B... 26->AA)
    const getExcelLetter = (index) => {
        let letter = '';
        let temp = index;
        while (temp >= 0) {
            letter = String.fromCharCode((temp % 26) + 65) + letter;
            temp = Math.floor(temp / 26) - 1;
        }
        return letter;
    };

    const MappingRow = ({ label, fieldKey }) => {
        const val = currentTemplate.mapping_config[fieldKey];
        return (
            <div className="grid grid-cols-2 gap-4 items-center p-3 border-b hover:bg-gray-50">
                <div className="font-semibold text-gray-700">{label}</div>
                <div>
                    <select
                        className="select select-sm select-bordered w-full"
                        value={val !== undefined ? val : ''}
                        onChange={(e) => setCurrentTemplate({
                            ...currentTemplate,
                            mapping_config: { ...currentTemplate.mapping_config, [fieldKey]: parseInt(e.target.value) }
                        })}
                    >
                        <option value="">-- Sin Asignar --</option>
                        {previewHeaders.length > 0 ? (
                            previewHeaders.map((h, idx) => (
                                <option key={idx} value={idx}>{idx + 1} ({getExcelLetter(idx)}) - {h}</option>
                            ))
                        ) : (
                            // Fallback if no file uploaded: Just numbers with Excel letters
                            [...Array(50)].map((_, idx) => (
                                <option key={idx} value={idx}>Columna {idx + 1} ({getExcelLetter(idx)})</option>
                            ))
                        )}
                    </select>
                </div>
            </div>
        );
    };

    // --- VIEWS ---

    if (view === 'list') {
        return (
            <div className="p-4 bg-white rounded-lg animate-fadeIn">
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-lg font-bold">Mis Plantillas de Importación</h3>
                    <button onClick={openCreate} className="btn btn-sm btn-primary gap-2">
                        <FaPlus /> Nueva Plantilla
                    </button>
                </div>

                {loading ? <p>Cargando...</p> : (
                    <div className="overflow-x-auto">
                        <table className="table w-full">
                            <thead>
                                <tr>
                                    <th>Nombre</th>
                                    <th>Descripción</th>
                                    <th>Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                {templates.map(tpl => (
                                    <tr key={tpl.id}>
                                        <td className="font-bold">{tpl.nombre}</td>
                                        <td>{tpl.descripcion || '-'}</td>
                                        <td className="flex gap-2">
                                            <button
                                                onClick={() => onSelectTemplate && onSelectTemplate(tpl.id)}
                                                className="btn btn-xs btn-outline btn-success"
                                                title="Usar esta plantilla">
                                                Seleccionar
                                            </button>
                                            <button onClick={() => openEdit(tpl)} className="btn btn-xs btn-ghost text-blue-600"><FaEdit /></button>
                                            <button onClick={() => handleDelete(tpl.id)} className="btn btn-xs btn-ghost text-red-600"><FaTrash /></button>
                                        </td>
                                    </tr>
                                ))}
                                {templates.length === 0 && (
                                    <tr>
                                        <td colSpan="3" className="text-center text-gray-400 py-4">No tienes plantillas creadas.</td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                )}
                {onClose && (
                    <div className="mt-4 border-t pt-4">
                        <button onClick={onClose} className="btn btn-sm btn-ghost">Cerrar Gestor</button>
                    </div>
                )}
            </div>
        );
    }

    // Create/Edit View
    return (
        <div className="p-4 bg-white rounded-lg animate-fadeIn">
            <div className="flex items-center gap-2 mb-6">
                <button onClick={() => setView('list')} className="btn btn-sm btn-circle btn-ghost"><FaArrowLeft /></button>
                <h3 className="text-lg font-bold">{view === 'create' ? 'Nueva Plantilla' : 'Editar Plantilla'}</h3>
            </div>

            <form onSubmit={handleSave} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="form-control">
                        <label className="label">Nombre de la Plantilla</label>
                        <input
                            type="text"
                            className="input input-bordered w-full"
                            placeholder="Ej: Reporte Banco X"
                            value={currentTemplate.nombre}
                            onChange={e => setCurrentTemplate({ ...currentTemplate, nombre: e.target.value })}
                            required
                        />
                    </div>
                    <div className="form-control">
                        <label className="label">Descripción (Opcional)</label>
                        <input
                            type="text"
                            className="input input-bordered w-full"
                            placeholder="Ej: Para importaciones de nómina mensual"
                            value={currentTemplate.descripcion || ''}
                            onChange={e => setCurrentTemplate({ ...currentTemplate, descripcion: e.target.value })}
                        />
                    </div>
                </div>

                {/* Upload Sample */}
                <div className="bg-blue-50 p-4 rounded-xl border border-blue-100 mb-6">
                    <h4 className="font-bold text-blue-800 flex items-center gap-2 mb-2">
                        <FaFileExcel /> Paso 1. Sube un archivo de ejemplo
                    </h4>
                    <p className="text-sm text-blue-600 mb-3">Para facilitar el mapeo, sube un Excel con los encabezados que usas.</p>
                    <input
                        type="file"
                        accept=".xlsx,.csv"
                        className="file-input file-input-sm file-input-bordered w-full max-w-xs"
                        onChange={handleUploadPreview}
                    />
                    {uploadingPreview && <span className="loading loading-spinner loading-sm ml-2"></span>}
                </div>

                {/* Mapping Area */}
                <div className="border rounded-xl overflow-hidden">
                    <div className="bg-gray-100 p-3 font-bold border-b flex justify-between">
                        <span>Campo en Sistema (Finaxis)</span>
                        <span>Columna en tu Archivo</span>
                    </div>

                    <div className="bg-gray-50 p-2 text-xs text-gray-500 text-center uppercase font-bold tracking-wide">Obligatorios</div>
                    <MappingRow label="Fecha" fieldKey="fecha" />
                    <MappingRow label="Cuenta (Código)" fieldKey="cuenta" />
                    <MappingRow label="Nombre de Cuenta (Descripción)" fieldKey="nombre_cuenta" />
                    <MappingRow label="Débito (Valor)" fieldKey="debito" />
                    <MappingRow label="Crédito (Valor)" fieldKey="credito" />

                    <div className="bg-gray-50 p-2 text-xs text-gray-500 text-center uppercase font-bold tracking-wide border-t">Identificación del Documento</div>
                    <MappingRow label="Código Tipo Documento (ej: RC, CE)" fieldKey="tipo_doc" />
                    <MappingRow label="Nombre Tipo Documento (ej: Recibo de Caja)" fieldKey="nombre_tipo_doc" />
                    <MappingRow label="Número del Documento" fieldKey="numero" />

                    <div className="bg-gray-50 p-2 text-xs text-gray-500 text-center uppercase font-bold tracking-wide border-t">Terceros y Detalles</div>
                    <MappingRow label="NIT Tercero" fieldKey="nit" />
                    <MappingRow label="Nombre Tercero" fieldKey="nombre_tercero" />
                    <MappingRow label="Detalle / Concepto" fieldKey="detalle" />
                </div>

                <div className="flex justify-end pt-4">
                    <button type="submit" className="btn btn-primary gap-2">
                        <FaSave /> Guardar Plantilla
                    </button>
                </div>
            </form>
        </div>
    );
}
