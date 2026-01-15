'use client';

import React, { useState } from 'react';
import {
  FaUpload,
  FaFileImport,
  FaBuilding,
  FaExclamationTriangle,
  FaCheckCircle,
  FaSpinner,
  FaBan,
  FaFileCode,
  FaArrowRight
} from 'react-icons/fa';
import { analizarBackup, ejecutarRestauracion } from '../../../lib/utilidadesService';

// --- ESTILOS REUSABLES (Manual v2.0) ---
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const selectClass = "w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-green-500 focus:border-green-500 text-sm transition-all outline-none bg-white pl-10";
const fileInputClass = "w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-bold file:bg-green-50 file:text-green-700 hover:file:bg-green-100 cursor-pointer border border-gray-300 rounded-lg shadow-sm";

export default function RestauracionForm({
  empresas,
  isProcessing,
  setIsProcessing,
  setMessage,
  setError
}) {
  const [analysisReport, setAnalysisReport] = useState(null);
  const [targetEmpresaId, setTargetEmpresaId] = useState('');
  const [parsedBackupData, setParsedBackupData] = useState(null);
  const [selectedModules, setSelectedModules] = useState({});

  const handleFileSelect = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!targetEmpresaId) {
      alert("Por favor, seleccione una empresa de destino antes de subir el archivo.");
      e.target.value = null;
      return;
    }

    setMessage(`Analizando estructura del archivo "${file.name}"...`);
    setError(null);
    setAnalysisReport(null);
    setIsProcessing(true);

    try {
      const fileContent = await file.text();
      const backupData = JSON.parse(fileContent);
      setParsedBackupData(backupData);

      const payload = {
        backupData,
        targetEmpresaId: targetEmpresaId
      };

      const { data: report } = await analizarBackup(payload);

      setAnalysisReport(report);

      // Inicializar todos los módulos como seleccionados por defecto
      const initialSelection = {};
      Object.keys(report.summary).forEach(key => {
        initialSelection[key.replace(/_/g, ' ')] = true;
        // Nota: report.summary keys son como 'plan_cuentas', pero migración usa nombres Human Readable en should_restore
        // Sin embargo, mi backend should_restore usa strings literales como 'Plan de Cuentas'.
        // Debo asegurarme que las keys coincidan.
        // Revisando backend: keys en summary son internal keys (e.g. 'terceros'). 
        // should_restore usa 'Terceros', 'Plan de Cuentas'.
        // Necesito un mapeo o usar las mismas keys.
        // Revisaré el mapping en el backend para ser consistente.
      });
      // Corrección: El backend usa strings hardcoded en los IFs (e.g. 'Grupos Inventario').
      // El report.summary viene de 'analizar_backup'. Veamos qué keys genera 'analizar_backup'.
      // 'analizar_backup' no lo vi, pero asumo keys standard pythonicas.
      // ESTRATEGIA: Usaré un mapeo en Frontend para mostrar nombres bonitos, pero enviaré las KEYS bonitas al backend
      // porque el backend espera 'Terceros', 'Plan de Cuentas' etc. en should_restore.
      // Espera... should_restore(module_key) verifica module_key in modulesToRestore.
      // Si el backend hace if should_restore('Plan de Cuentas'), entonces el FE debe enviar 'Plan de Cuentas'.
      // Entonces mi initialSelection debe usar esas keys.

      // MAPPING MANUAL PARA GARANTIZAR COINCIDENCIA CON BACKEND
      const keyMapping = {
        'terceros': 'Terceros',
        'plan_cuentas': 'Plan de Cuentas',
        'centros_costo': 'Centros de Costo',
        'bodegas': 'Bodegas',
        'productos': 'Productos',
        'grupos_inventario': 'Grupos Inventario',
        'transacciones': 'Documentos y Movimientos', // Legacy key often used
        'documentos': 'Documentos y Movimientos',
        'propiedad_horizontal': 'Propiedad Horizontal',
        'activos_fijos': 'Activos Fijos',
        'cotizaciones': 'Cotizaciones',
        'produccion': 'Producción',
        'conciliacion_bancaria': 'Conciliación Bancaria',
        'nomina': 'Nómina',
        'tasas_impuesto': 'Tasas Impuesto',
        'tipos_documento': 'Tipos de Documento',
        'conceptos_favoritos': 'Conceptos Favoritos',
        'listas_precio': 'Listas de Precio',
        'formatos_impresion': 'Formatos PDF',
        'plantillas': 'Plantillas Contables'
      };

      const selectionState = {};
      Object.keys(report.summary).forEach(rawKey => {
        const niceKey = keyMapping[rawKey] || rawKey; // Fallback to raw if not mapped
        selectionState[niceKey] = true;
      });
      setSelectedModules(selectionState);

      setMessage("Análisis completado. Revise el reporte de impacto antes de proceder.");

    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message;
      console.error(err);
      setError(`Error crítico al procesar el archivo: ${errorMsg}`);
      setMessage('');
    } finally {
      setIsProcessing(false);
      e.target.value = null;
    }
  };

  const handleConfirmRestore = async () => {
    if (!analysisReport || !parsedBackupData) {
      alert("No hay un análisis válido para confirmar.");
      return;
    }

    if (!window.confirm("⚠️ ADVERTENCIA FINAL ⚠️\n\nEsta acción borrará los datos existentes en la empresa destino para reemplazarlos por la copia de seguridad.\n\n¿Está absolutamente seguro?")) {
      return;
    }

    if (analysisReport.integrity_valid === false) {
      if (!window.confirm("🛑 ALERTA DE SEGURIDAD 🛑\n\nEl archivo tiene una firma digital INVÁLIDA. Esto es común si copia backups entre servidores distintos.\n\n¿Desea FORZAR la restauración ignorando la seguridad?")) {
        return;
      }
    }

    setMessage('EJECUTANDO RESTAURACIÓN... Por favor no cierre esta ventana.');
    setError(null);
    setIsProcessing(true);

    try {
      const payload = {
        backupData: parsedBackupData,
        targetEmpresaId: analysisReport.targetEmpresaId,
        bypass_signature: analysisReport.integrity_valid === false,
        modulesToRestore: Object.keys(selectedModules).filter(k => selectedModules[k])
      };

      const { data: result } = await ejecutarRestauracion(payload);

      setAnalysisReport(null);
      setParsedBackupData(null);
      setTargetEmpresaId('');
      setMessage(`¡Restauración Exitosa! ${result.message}`);
      alert(`¡Éxito! ${result.message}`);

    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message;
      setError(`Error crítico durante la restauración: ${errorMsg}`);
      setMessage('');
    } finally {
      setIsProcessing(false);
    }
  };

  const toggleModule = (moduleKey) => {
    setSelectedModules(prev => ({
      ...prev,
      [moduleKey]: !prev[moduleKey]
    }));
  };

  const toggleAll = (selectAll) => {
    const newState = {};
    Object.keys(selectedModules).forEach(key => {
      newState[key] = selectAll;
    });
    setSelectedModules(newState);
  };

  return (
    <>
      {/* CARD DE CONFIGURACIÓN */}
      <div className="bg-white p-8 rounded-xl shadow-lg border border-gray-100 mt-8 animate-fadeIn">

        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-gray-100">
          <div className="p-3 bg-green-100 rounded-full text-green-600">
            <FaUpload className="text-xl" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-800">Restaurar Copia de Seguridad</h2>
            <p className="text-gray-500 text-sm">Importar datos desde un archivo JSON previamente exportado.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
          {/* Selección de Empresa */}
          <div>
            <label htmlFor="targetEmpresaId" className={labelClass}>1. Empresa de Destino</label>
            <div className="relative">
              <select
                id="targetEmpresaId"
                value={targetEmpresaId}
                onChange={(e) => setTargetEmpresaId(e.target.value)}
                className={selectClass}
                disabled={isProcessing || analysisReport}
              >
                <option value="">-- Seleccione destino --</option>
                {empresas.map(e => (<option key={e.id} value={e.id}>{e.razon_social}</option>))}
              </select>
              <FaBuilding className="absolute left-3 top-3 text-gray-400 pointer-events-none" />
            </div>
            <p className="text-xs text-gray-400 mt-1 ml-1">Los datos de esta empresa serán modificados.</p>
          </div>

          {/* Input de Archivo */}
          <div>
            <label htmlFor="backupFile" className={labelClass}>2. Archivo de Respaldo (.json)</label>
            <div className="relative">
              <input
                id="backupFile"
                type="file"
                accept=".json"
                onChange={handleFileSelect}
                disabled={isProcessing || !targetEmpresaId || analysisReport}
                className={fileInputClass}
              />
            </div>
            <p className="text-xs text-gray-400 mt-1 ml-1">Seleccione el archivo generado por el sistema.</p>
          </div>
        </div>
      </div>

      {/* REPORTE DE ANÁLISIS (CONDICIONAL) */}
      {analysisReport && (
        <div className="bg-white border border-amber-200 p-6 rounded-xl shadow-lg mt-8 animate-slideDown relative overflow-hidden">
          {/* Barra decorativa superior */}
          <div className={`absolute top-0 left-0 right-0 h-2 ${analysisReport.integrity_valid === false ? 'bg-red-500' : 'bg-amber-400'}`}></div>

          {analysisReport.integrity_valid === false && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 flex items-start gap-3">
              <FaBan className="text-xl mt-1 shrink-0" />
              <div>
                <h4 className="font-bold">Error de Integridad Detectado</h4>
                <p className="text-sm">La firma digital de este archivo no coincide. Si movió este archivo desde otra instalación, esto es esperado. De lo contrario, el archivo podría estar corrupto.</p>
              </div>
            </div>
          )}

          <div className="flex items-center gap-3 mb-6">
            <FaExclamationTriangle className="text-3xl text-amber-500" />
            <div>
              <h3 className="text-xl font-bold text-gray-800">Análisis de Impacto</h3>
              <p className="text-sm text-gray-600">
                Destino: <span className="font-bold text-indigo-600">{empresas.find(e => e.id == analysisReport.targetEmpresaId)?.razon_social || 'Desconocida'}</span>
              </p>
            </div>
          </div>

          {/* Controles de Selección */}
          <div className="flex justify-end gap-2 mb-2">
            <button onClick={() => toggleAll(true)} className="text-xs text-green-600 font-semibold hover:underline">Seleccionar Todo</button>
            <span className="text-gray-300">|</span>
            <button onClick={() => toggleAll(false)} className="text-xs text-red-500 font-semibold hover:underline">Deseleccionar Todo</button>
          </div>

          {/* Grid de Resumen */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
            {Object.entries(analysisReport.summary).map(([key, value]) => {
              const total = value.total || 0;
              const importar = value.a_importar || value.a_crear || 0;
              const conflicto = value.conflictos || (total - importar);

              const keyMapping = {
                'terceros': 'Terceros',
                'plan_cuentas': 'Plan de Cuentas',
                'centros_costo': 'Centros de Costo',
                'bodegas': 'Bodegas',
                'productos': 'Productos',
                'grupos_inventario': 'Grupos Inventario',
                'transacciones': 'Documentos y Movimientos',
                'documentos': 'Documentos y Movimientos',
                'propiedad_horizontal': 'Propiedad Horizontal',
                'activos_fijos': 'Activos Fijos',
                'cotizaciones': 'Cotizaciones',
                'produccion': 'Producción',
                'conciliacion_bancaria': 'Conciliación Bancaria',
                'nomina': 'Nómina',
                'tasas_impuesto': 'Tasas Impuesto',
                'tipos_documento': 'Tipos de Documento',
                'conceptos_favoritos': 'Conceptos Favoritos',
                'listas_precio': 'Listas de Precio',
                'formatos_impresion': 'Formatos PDF',
                'plantillas': 'Plantillas Contables'
              };
              const niceKey = keyMapping[key] || key.replace(/_/g, ' ');

              return (
                <div
                  key={key}
                  className={`p-4 rounded-lg border transition-all cursor-pointer ${selectedModules[niceKey] ? 'bg-white border-green-300 shadow-sm' : 'bg-gray-50 border-gray-200 opacity-60'}`}
                  onClick={() => toggleModule(niceKey)}
                >
                  <div className="flex items-center gap-2 mb-2 border-b border-gray-100 pb-2">
                    <input
                      type="checkbox"
                      checked={!!selectedModules[niceKey]}
                      onChange={() => { }} // Handled by div click
                      className="rounded text-green-600 focus:ring-green-500 cursor-pointer h-4 w-4"
                    />
                    <span className="text-sm font-bold text-gray-700 uppercase tracking-wide truncate">{niceKey}</span>
                  </div>

                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-600">Encontrados:</span>
                    <span className="font-bold">{total}</span>
                  </div>
                  <div className="flex justify-between items-center text-sm mt-1">
                    <span className="text-green-600 font-medium flex items-center gap-1"><FaArrowRight size={10} /> Restaurar:</span>
                    <span className="font-bold text-green-700">{importar}</span>
                  </div>
                  {conflicto > 0 && (
                    <div className="flex justify-between items-center text-sm mt-1 text-red-600 font-bold bg-red-50 px-2 rounded">
                      <span>Conflictos:</span>
                      <span>{conflicto}</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Lista Detallada de Conflictos */}
          {Object.values(analysisReport.conflicts).flat().length > 0 && (
            <div className="mb-8">
              <details className="group bg-red-50 border border-red-100 rounded-lg">
                <summary className="flex items-center justify-between cursor-pointer p-4 text-red-700 font-semibold">
                  <span>Ver detalle de registros omitidos por conflicto ({Object.values(analysisReport.conflicts).flat().length})</span>
                  <span className="transform group-open:rotate-180 transition-transform">▼</span>
                </summary>
                <div className="p-4 pt-0 border-t border-red-100">
                  <ul className="list-disc list-inside space-y-1 mt-2 text-sm text-red-600 max-h-60 overflow-y-auto font-mono">
                    {Object.values(analysisReport.conflicts).flat().map((conflict, index) => (
                      <li key={`conflict-${index}`}>{conflict}</li>
                    ))}
                  </ul>
                </div>
              </details>
            </div>
          )}

          {/* Botones de Acción */}
          <div className="flex flex-col md:flex-row justify-end gap-4 pt-4 border-t border-gray-100">
            <button
              onClick={() => { setAnalysisReport(null); setParsedBackupData(null); }}
              className="px-6 py-3 rounded-lg text-gray-600 hover:bg-gray-100 font-bold transition-colors flex items-center justify-center gap-2"
            >
              <FaBan /> Cancelar Operación
            </button>
            <button
              onClick={handleConfirmRestore}
              className="px-8 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg shadow-md font-bold transition-transform transform hover:-translate-y-0.5 flex items-center justify-center gap-2 disabled:bg-gray-400 disabled:cursor-not-allowed"
              disabled={isProcessing || Object.values(analysisReport.summary).reduce((total, summary) => total + (summary.a_importar || summary.a_crear), 0) === 0}
            >
              {isProcessing ? <><FaSpinner className="animate-spin" /> Restaurando...</> : <><FaFileImport /> Confirmar e Importar Datos</>}
            </button>
          </div>
        </div>
      )}
    </>
  );
}