'use client';

import React, { useState } from 'react';
import { 
  FaMagic, 
  FaUpload, 
  FaCogs, 
  FaCalendarAlt, 
  FaSortNumericUp, 
  FaExchangeAlt, 
  FaDownload, 
  FaCode,
  FaCheckCircle,
  FaExclamationTriangle
} from 'react-icons/fa';

// --- ESTILOS REUSABLES (Manual v2.0) ---
const labelClass = "block text-xs font-bold text-gray-500 uppercase mb-1 tracking-wide";
const inputClass = "w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-purple-500 focus:border-purple-500 text-sm transition-all outline-none bg-white";
const selectClass = "w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-purple-500 focus:border-purple-500 text-sm transition-all outline-none bg-white";
const fileInputClass = "w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-bold file:bg-purple-50 file:text-purple-700 hover:file:bg-purple-100 cursor-pointer border border-gray-300 rounded-lg shadow-sm";

export default function TransformacionForm({ tiposDocumento }) {
  const [transformData, setTransformData] = useState(null);
  const [transformRules, setTransformRules] = useState({
    renumberStart: '',
    changeDayTo: '',
    changeMonthTo: '',
    changeYearTo: '',
    changeTypeFrom: '', // Guardará el ID del tipo seleccionado
    changeTypeTo: '',   // Guardará el ID del tipo seleccionado
    dateRangeFrom: '',
    dateRangeTo: '',
  });
  const [transformedJson, setTransformedJson] = useState(null);
  const [isTransforming, setIsTransforming] = useState(false);
  const [localMessage, setLocalMessage] = useState('');
  const [localError, setLocalError] = useState('');

  const handleTransformFileLoad = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setTransformData(null);
    setTransformedJson(null);
    setLocalMessage('');
    setLocalError('');

    try {
      const fileContent = await file.text();
      const jsonData = JSON.parse(fileContent);

      // --- Soporte Híbrido (Transacciones / Documentos) ---
      const rawDocs = jsonData.transacciones || jsonData.documentos;

      if (!rawDocs) {
        throw new Error("El archivo JSON no contiene la sección 'transacciones' ni 'documentos'.");
      }

      jsonData.documentos = rawDocs; // Normalizar para uso interno
      setTransformData(jsonData);
    } catch (err) {
      setLocalError(`Error al leer el archivo para transformar: ${err.message}`);
    } finally {
      e.target.value = null;
    }
  };

  const handleRuleChange = (e) => {
    const { name, value } = e.target;
    setTransformRules(prev => ({ ...prev, [name]: value }));
  };

  const handleApplyTransformations = () => {
    setIsTransforming(true);
    setTransformedJson(null);
    setLocalError('');
    setLocalMessage('');

    if (!transformData || !transformData.documentos || transformData.documentos.length === 0) {
      setLocalError("No hay datos de documentos cargados para transformar.");
      setIsTransforming(false);
      return;
    }
    if (transformRules.changeTypeFrom && transformRules.changeTypeTo && !transformRules.renumberStart) {
      // Validar si el usuario intenta cambiar tipos sin renumerar (riesgoso)
      // Pero permitimos continuar si está seguro (aquí forzamos la alerta visual)
    }

    try {
      let documentosAProcesar = JSON.parse(JSON.stringify(transformData.documentos));

      // 1. Filtro por Fechas
      if (transformRules.dateRangeFrom && transformRules.dateRangeTo) {
        const startDate = new Date(transformRules.dateRangeFrom);
        const endDate = new Date(transformRules.dateRangeTo);
        startDate.setUTCHours(0, 0, 0, 0);
        endDate.setUTCHours(23, 59, 59, 999);
        documentosAProcesar = documentosAProcesar.filter(doc => {
          const docDate = new Date(doc.fecha);
          return docDate >= startDate && docDate <= endDate;
        });
      }

      // 2. Filtro por Tipo de Documento (CORREGIDO: Usar Código, no ID)
      if (transformRules.changeTypeFrom) {
        // Buscamos el código del tipo seleccionado (ej. "CC")
        const tipoOrigen = tiposDocumento.find(t => t.id == transformRules.changeTypeFrom);
        
        if (tipoOrigen) {
          // Filtramos el JSON comparando códigos
          documentosAProcesar = documentosAProcesar.filter(doc => 
            doc.tipo_doc_codigo === tipoOrigen.codigo
          );
        }
      }
      
      if (documentosAProcesar.length === 0) {
        setLocalMessage("Ningún documento coincidió con los criterios de filtrado. No se realizó ninguna transformación.");
        setIsTransforming(false);
        return;
      }

      // 3. Ordenar cronológicamente
      documentosAProcesar.sort((a, b) => new Date(a.fecha) - new Date(b.fecha));
      
      let renumberCounter = transformRules.renumberStart ? parseInt(transformRules.renumberStart, 10) : null;

      // Buscamos el código del tipo destino si se seleccionó cambio
      let codigoDestino = null;
      if (transformRules.changeTypeTo) {
        const tipoDestino = tiposDocumento.find(t => t.id == transformRules.changeTypeTo);
        if (tipoDestino) codigoDestino = tipoDestino.codigo;
      }

      const documentosTransformados = documentosAProcesar.map(doc => {
        const newDoc = { ...doc };
        
        // Transformar Fecha
        const hasDateRule = transformRules.changeDayTo || transformRules.changeMonthTo || transformRules.changeYearTo;
        if (hasDateRule) {
          const dateToModify = new Date(newDoc.fecha);
          if (transformRules.changeYearTo) { dateToModify.setUTCFullYear(parseInt(transformRules.changeYearTo, 10)); }
          if (transformRules.changeMonthTo) { dateToModify.setUTCMonth(parseInt(transformRules.changeMonthTo, 10) - 1); }
          if (transformRules.changeDayTo) { dateToModify.setUTCDate(parseInt(transformRules.changeDayTo, 10)); }
          newDoc.fecha = dateToModify.toISOString();
        }

        // Transformar Tipo (Cambiar el CÓDIGO en el JSON)
        if (codigoDestino) {
          newDoc.tipo_doc_codigo = codigoDestino;
        }

        // Transformar Consecutivo
        if (renumberCounter !== null) {
          newDoc.numero = renumberCounter;
          renumberCounter++;
        }
        return newDoc;
      });
      
      // Filtrar movimientos contables asociados (solo los de los docs procesados)
      // Nota: En el JSON nuevo, los movimientos vienen DENTRO del documento ("transacciones" -> "movimientos_contables")
      // Pero si usamos el formato antiguo plano, filtramos aquí.
      // Como tu JSON nuevo es anidado, 'documentosTransformados' YA CONTIENE sus movimientos dentro.
      // Simplemente retornamos la estructura limpia.

      const newBackupData = {
        ...transformData,
        // Sobrescribimos con los documentos YA transformados
        transacciones: documentosTransformados,
        documentos: documentosTransformados
      };

      // Limpiamos propiedades viejas si existen para no confundir
      if (newBackupData.movimientos_contables) delete newBackupData.movimientos_contables;
      if (newBackupData.movimientos_inventario) delete newBackupData.movimientos_inventario;

      setTransformedJson(JSON.stringify(newBackupData, null, 2));
      setLocalMessage(`¡Éxito! Se transformaron ${documentosTransformados.length} documentos. Listo para descargar.`);

    } catch (err) {
      setLocalError(`Error durante la transformación: ${err.message}`);
    } finally {
      setIsTransforming(false);
    }
  };

  const handleDownloadTransformedJson = () => {
    if (!transformedJson) return;
    const blob = new Blob([transformedJson], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    const fechaHoy = new Date().toISOString().split('T')[0];
    link.download = `backup_transformado_${fechaHoy}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <>
      {/* CARD PRINCIPAL */}
      <div className="bg-white p-8 rounded-xl shadow-lg border border-gray-100 mt-8 animate-fadeIn">
        
        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-gray-100">
            <div className="p-3 bg-purple-100 rounded-full text-purple-600">
                <FaMagic className="text-xl" />
            </div>
            <div>
                <h2 className="text-xl font-bold text-gray-800">Transformación de Datos (ETL)</h2>
                <p className="text-gray-500 text-sm">Modificar fechas, tipos o consecutivos de un backup antes de restaurar.</p>
            </div>
        </div>
        
        {/* Paso A: Cargar Archivo */}
        <div className="bg-purple-50 p-6 rounded-xl border border-purple-100 mb-8">
            <label htmlFor="transformFile" className="block text-sm font-bold text-purple-900 mb-2 flex items-center gap-2">
                <FaUpload /> A. Cargar Archivo JSON Fuente
            </label>
            <input 
                id="transformFile" 
                type="file" 
                accept=".json" 
                onChange={handleTransformFileLoad}
                className={fileInputClass}
            />
            {transformData && (
                <div className="mt-3 flex items-center text-green-700 text-sm font-medium animate-fadeIn">
                    <FaCheckCircle className="mr-2" /> 
                    Archivo cargado: {transformData.documentos?.length || 0} documentos encontrados.
                </div>
            )}
        </div>

        {/* Paso B: Reglas (Deshabilitado si no hay archivo) */}
        <div className={`transition-opacity duration-300 ${!transformData ? 'opacity-50 pointer-events-none grayscale' : 'opacity-100'}`}>
            <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2">
                <FaCogs className="text-purple-500" /> B. Definir Reglas de Transformación
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                
                {/* Panel 1: Recodificación */}
                <div className="border border-gray-200 p-5 rounded-xl bg-white shadow-sm">
                    <h4 className="text-sm font-bold text-purple-700 uppercase mb-4 border-b border-gray-100 pb-2">Recodificación General</h4>
                    
                    <div className="space-y-4">
                        <div>
                            <label className={labelClass}>Nuevo N° Inicial Consecutivo</label>
                            <div className="relative">
                                <input type="number" name="renumberStart" value={transformRules.renumberStart} onChange={handleRuleChange} placeholder="Ej: 1001" className={inputClass} />
                                <FaSortNumericUp className="absolute right-3 top-3 text-gray-400 pointer-events-none" />
                            </div>
                        </div>
                        
                        <div className="grid grid-cols-3 gap-2">
                            <div>
                                <label className={labelClass}>Día</label>
                                <input type="number" name="changeDayTo" value={transformRules.changeDayTo} onChange={handleRuleChange} min="1" max="31" placeholder="DD" className={inputClass} />
                            </div>
                            <div>
                                <label className={labelClass}>Mes</label>
                                <select name="changeMonthTo" value={transformRules.changeMonthTo} onChange={handleRuleChange} className={selectClass}>
                                    <option value="">--</option>
                                    {[...Array(12).keys()].map(i => <option key={i+1} value={i+1}>{i+1}</option>)}
                                </select>
                            </div>
                            <div>
                                <label className={labelClass}>Año</label>
                                <input type="number" name="changeYearTo" value={transformRules.changeYearTo} onChange={handleRuleChange} min="2000" max="2099" placeholder="AAAA" className={inputClass} />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Panel 2: Cambio de Tipo */}
                <div className="border border-gray-200 p-5 rounded-xl bg-white shadow-sm">
                    <h4 className="text-sm font-bold text-purple-700 uppercase mb-4 border-b border-gray-100 pb-2">Cambio de Tipo de Documento</h4>
                    
                    <div className="space-y-4">
                        <div>
                            <label className={labelClass}>Rango de Fechas (Filtro)</label>
                            <div className="flex gap-2">
                                <div className="relative w-full">
                                    <input type="date" name="dateRangeFrom" value={transformRules.dateRangeFrom} onChange={handleRuleChange} className={inputClass} />
                                </div>
                                <div className="relative w-full">
                                    <input type="date" name="dateRangeTo" value={transformRules.dateRangeTo} onChange={handleRuleChange} className={inputClass} />
                                </div>
                            </div>
                        </div>

                        <div className="flex items-center gap-2 bg-gray-50 p-3 rounded-lg border border-gray-200">
                            <div className="w-1/2">
                                <label className={labelClass}>De Tipo (Origen)</label>
                                <select name="changeTypeFrom" value={transformRules.changeTypeFrom} onChange={handleRuleChange} className={selectClass}>
                                    <option value="">-- Seleccione --</option>
                                    {tiposDocumento.map(t=><option key={t.id} value={t.id}>{t.nombre}</option>)}
                                </select>
                            </div>
                            <FaExchangeAlt className="text-gray-400 mt-4" />
                            <div className="w-1/2">
                                <label className={labelClass}>A Tipo (Destino)</label>
                                <select name="changeTypeTo" value={transformRules.changeTypeTo} onChange={handleRuleChange} className={selectClass}>
                                    <option value="">-- Seleccione --</option>
                                    {tiposDocumento.map(t=><option key={t.id} value={t.id}>{t.nombre}</option>)}
                                </select>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        {/* Botón Acción */}
        <div className="flex justify-end mt-8 pt-6 border-t border-gray-100">
            <button 
                onClick={handleApplyTransformations} 
                disabled={!transformData || isTransforming} 
                className={`
                    px-8 py-3 rounded-lg shadow-lg font-bold text-white text-lg transition-all transform hover:-translate-y-0.5 flex items-center gap-2
                    ${!transformData || isTransforming ? 'bg-gray-400 cursor-not-allowed' : 'bg-purple-600 hover:bg-purple-700 hover:shadow-purple-200'}
                `}
            >
                {isTransforming ? 'Procesando...' : <><FaCogs /> Aplicar y Generar JSON</>}
            </button>
        </div>
        
        {/* Mensajes */}
        {localError && (
            <div className="mt-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded-r-lg flex items-center gap-3 animate-pulse">
                <FaExclamationTriangle className="text-xl" />
                <p>{localError}</p>
            </div>
        )}
        {localMessage && (
            <div className="mt-6 p-4 bg-green-50 border-l-4 border-green-500 text-green-700 rounded-r-lg flex items-center gap-3 animate-fadeIn">
                <FaCheckCircle className="text-xl" />
                <p>{localMessage}</p>
            </div>
        )}
      </div>

      {/* ZONA DE RESULTADO (TERMINAL) */}
      {transformedJson && (
          <div className="bg-slate-900 p-6 rounded-xl shadow-2xl mt-8 border border-slate-700 animate-slideDown">
              <div className="flex justify-between items-center mb-4">
                  <h3 className="text-green-400 font-mono font-bold flex items-center gap-2">
                      <FaCode /> Resultado de Transformación
                  </h3>
                  <button 
                    onClick={handleDownloadTransformedJson} 
                    className="px-4 py-2 bg-green-600 hover:bg-green-500 text-white font-bold rounded-lg text-sm flex items-center gap-2 transition-colors"
                  >
                      <FaDownload /> Descargar Archivo .JSON
                  </button>
              </div>
              <textarea 
                readOnly 
                value={transformedJson} 
                className="w-full h-64 bg-slate-950 text-green-500 font-mono text-xs p-4 rounded-lg border border-slate-800 focus:outline-none resize-none"
              ></textarea>
          </div>
      )}
    </>
  );
}