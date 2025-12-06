'use client';

import React from 'react';
import { 
  FaExclamationTriangle, 
  FaTrash, 
  FaTimes, 
  FaInfoCircle, 
  FaSpinner,
  FaListUl
} from 'react-icons/fa';

export default function ConfirmacionDepuracionModal({
  isOpen,
  onClose,
  onConfirm,
  analysisData,
  isLoading
}) {
  if (!isOpen || !analysisData) return null;

  const { cuentas_a_eliminar, cuentas_a_conservar_conteo, mensaje } = analysisData;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex justify-center items-center p-4 animate-fadeIn">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg border border-gray-100 overflow-hidden transform transition-all scale-100">
        
        {/* HEADER DE PELIGRO */}
        <div className="bg-red-50 p-6 border-b border-red-100 flex justify-between items-center">
            <h2 className="text-xl font-bold text-red-700 flex items-center gap-2">
                <FaExclamationTriangle className="text-2xl" />
                Confirmar Depuración
            </h2>
            <button 
                onClick={onClose} 
                className="text-red-400 hover:text-red-600 transition-colors text-xl p-1 rounded-full hover:bg-red-100"
            >
                <FaTimes />
            </button>
        </div>

        <div className="p-6 space-y-6">
            
            {/* RESUMEN DE ANÁLISIS */}
            <div className="bg-amber-50 border border-amber-200 p-4 rounded-lg flex gap-3 items-start">
                <FaInfoCircle className="text-amber-500 text-xl mt-1 flex-shrink-0" />
                <div>
                    <p className="font-bold text-amber-800 text-sm uppercase mb-1">Resultado del Análisis</p>
                    <p className="text-sm text-amber-700 leading-relaxed">{mensaje}</p>
                </div>
            </div>

            {/* LISTA DE CUENTAS A ELIMINAR */}
            {cuentas_a_eliminar.length > 0 && (
              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <div className="bg-gray-50 px-4 py-2 border-b border-gray-200 flex justify-between items-center">
                    <span className="text-xs font-bold text-gray-500 uppercase flex items-center gap-2">
                        <FaListUl /> Se eliminarán {cuentas_a_eliminar.length} cuentas
                    </span>
                </div>
                <div className="max-h-48 overflow-y-auto bg-white">
                  <ul className="divide-y divide-gray-100">
                    {cuentas_a_eliminar.map(cuenta => (
                      <li key={cuenta.id} className="px-4 py-2 text-sm hover:bg-red-50 transition-colors flex items-center gap-2">
                        <span className="font-mono font-bold text-gray-600 bg-gray-100 px-1.5 rounded text-xs">
                            {cuenta.codigo}
                        </span> 
                        <span className="text-gray-700 truncate">
                            {cuenta.nombre}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
            
            {/* ADVERTENCIA FINAL */}
            <div className="text-center">
                <p className="text-xs text-gray-500 mb-1">Cuentas seguras que se conservarán:</p>
                <p className="text-2xl font-bold text-green-600">{cuentas_a_conservar_conteo}</p>
            </div>
            
            <div className="p-4 rounded-lg bg-red-50 border border-red-100 text-center">
                <p className="text-xs font-bold text-red-800 uppercase mb-1">⚠️ Acción Irreversible</p>
                <p className="text-sm text-red-600">
                    Las cuentas listadas arriba desaparecerán permanentemente. No podrá deshacer esta acción.
                </p>
            </div>
        </div>

        {/* FOOTER ACCIONES */}
        <div className="p-6 bg-gray-50 border-t border-gray-200 flex justify-end gap-3">
          <button 
            type="button" 
            onClick={onClose} 
            disabled={isLoading} 
            className="px-5 py-2 text-gray-600 hover:bg-gray-200 rounded-lg font-medium transition-colors"
          >
            Cancelar
          </button>
          <button 
            type="button" 
            onClick={onConfirm} 
            disabled={isLoading || cuentas_a_eliminar.length === 0} 
            className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg shadow-md font-bold flex items-center gap-2 transition-transform transform hover:-translate-y-0.5 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {isLoading ? (
                <> <FaSpinner className="animate-spin" /> Eliminando... </>
            ) : (
                <> <FaTrash /> Confirmar y Eliminar </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}