'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Script from 'next/script';


export default function ImportarPucPage() {
  const [file, setFile] = useState(null);
  const [parsedData, setParsedData] = useState([]);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleFileChange = (e) => {
    setError(null);
    setSuccessMessage(null);
    setParsedData([]);
    const selectedFile = e.target.files[0];

    if (selectedFile && selectedFile.name.toLowerCase().endsWith('.csv')) {
      setFile(selectedFile);
    } else {
      setError("Por favor, selecciona un archivo con formato .csv");
      setFile(null);
    }
  };

  const handleParse = () => {
    if (!file) {
      setError("Primero debes seleccionar un archivo.");
      return;
    }
    setIsLoading(true);
    setSuccessMessage(null);

    // --- INICIO DEL BLOQUE CORREGIDO ---
    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      delimiter: ";", // Acepta punto y coma como separador
      bom: true,      // Ignora el "BOM" invisible de Excel

      // Función que transforma los encabezados para que coincidan con lo esperado
      transformHeader: function (header) {
        let lowerCaseHeader = header.toLowerCase();
        let snakeCaseHeader = lowerCaseHeader.replace(/ /g, '_');
        return snakeCaseHeader.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
      },

      complete: (results) => {
        const requiredHeaders = ['codigo', 'nombre', 'nivel', 'permite_movimiento'];
        const fileHeaders = results.meta.fields;
        const missingHeaders = requiredHeaders.filter(h => !fileHeaders.includes(h));

        if (missingHeaders.length > 0) {
          setError(`El archivo CSV no es válido. Faltan las siguientes columnas requeridas: ${missingHeaders.join(', ')}`);
          setParsedData([]);
        } else {
          setParsedData(results.data);
          setError(null);
        }
        setIsLoading(false);
      },
      error: (err) => {
        setError("Ocurrió un error al procesar el archivo: " + err.message);
        setIsLoading(false);
      }
    });
    // --- FIN DEL BLOQUE CORREGIDO ---
  };

  const handleImport = async () => {
    if (parsedData.length === 0) {
      setError("No hay datos para importar. Por favor, procesa un archivo primero.");
      return;
    }

    setIsLoading(true);
    setError(null);
    setSuccessMessage(null);

    try {

      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/plan-cuentas/importar-masivo`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ cuentas: parsedData }),
      });

      const result = await res.json();

      if (!res.ok) {
        throw new Error(result.details || result.message || 'Ocurrió un error en el servidor.');
      }

      setSuccessMessage(result.message);
      setParsedData([]);
      setFile(null);

      if (document.querySelector('input[type="file"]')) {
        document.querySelector('input[type="file"]').value = '';
      }

    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <Script
        src="https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js"
        strategy="lazyOnload"
      />

      <div className="container mx-auto p-4 max-w-4xl">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">Importar Plan de Cuentas (PUC)</h1>
            <p className="text-gray-600">Importación masiva desde archivo CSV.</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-lg font-semibold mb-2">Paso 1: Seleccionar Archivo</h2>
          <div className="bg-blue-50 border-l-4 border-blue-500 text-blue-700 p-4 mb-4" role="alert">
            <p className="font-bold">Formato Requerido</p>
            <p>El archivo CSV debe contener obligatoriamente las siguientes columnas: <strong>codigo, nombre, nivel, permite_movimiento</strong>. La columna <strong>funcion_especial</strong> es opcional.</p>
          </div>
          <input
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
          />
          {file && <p className="text-sm text-gray-500 mt-2">Archivo seleccionado: <strong>{file.name}</strong></p>}
          <button
            onClick={handleParse}
            disabled={!file || isLoading}
            className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:bg-indigo-300"
          >
            {isLoading && parsedData.length === 0 ? 'Procesando...' : 'Procesar y Ver Vista Previa'}
          </button>
        </div>

        {error && <p className="text-red-500 text-center font-semibold my-4 p-3 bg-red-100 rounded-md">{error}</p>}
        {successMessage && <p className="text-green-700 text-center font-semibold my-4 p-3 bg-green-100 rounded-md">{successMessage}</p>}

        {parsedData.length > 0 && (
          <div className="mt-6 bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-lg font-semibold mb-2">Paso 2: Vista Previa y Confirmación</h2>
            <p className="text-gray-600 mb-4">Revisa que los datos se hayan leído correctamente. Se han encontrado <strong>{parsedData.length}</strong> cuentas para importar.</p>
            <div className="overflow-x-auto max-h-96">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Código</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nombre</th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Nivel</th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Permite Mov.</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Función Especial</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {parsedData.map((cuenta, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">{cuenta.codigo}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">{cuenta.nombre}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-center">{cuenta.nivel}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-center">{String(cuenta.permite_movimiento).toLowerCase() === 'true' ? 'Sí' : 'No'}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">{cuenta.funcion_especial || 'N/A'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="text-right mt-4">
              <button
                onClick={handleImport}
                disabled={isLoading}
                className="px-6 py-3 bg-green-600 text-white font-bold rounded-md hover:bg-green-700 disabled:bg-green-300"
              >
                {isLoading ? 'Importando...' : 'Confirmar e Importar Cuentas'}
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  );
}