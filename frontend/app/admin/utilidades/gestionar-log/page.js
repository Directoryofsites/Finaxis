'use client';

import React, { useState, useEffect } from 'react';
import BotonRegresar from '../../../components/BotonRegresar';
import { useAuth } from '../../../context/AuthContext'; // Importa el hook useAuth

export default function GestionarLogPage() {
  const { user } = useAuth(); // Obtiene el objeto user del contexto de autenticación
  const [empresas, setEmpresas] = useState([]);
  const [tiposDocumento, setTiposDocumento] = useState([]);
  const [mapTiposDocumento, setMapTiposDocumento] = useState(new Map());

  const [filtros, setFiltros] = useState({
    empresaId: '',
    tipoDocId: '',
    numero: ''
  });
  
  const [fechas, setFechas] = useState({
    inicio: '',
    fin: ''
  });

  const [selectedItems, setSelectedItems] = useState(new Set());
  const [searchResult, setSearchResult] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  // --- NUEVO: Estados para el modal del último documento ---
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [ultimoDocumentoInfo, setUltimoDocumentoInfo] = useState(null);
  const [isLoadingModal, setIsLoadingModal] = useState(false);


  const isDateRangeMode = filtros.numero.trim() === '*.*';

  useEffect(() => {
    const fetchEmpresas = async () => {
      try {

        const resEmpresas = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/empresas`);
        const dataEmpresas = await resEmpresas.json();
        if (!resEmpresas.ok) throw new Error(`Error al cargar empresas: ${dataEmpresas.message || resEmpresas.statusText}`);
        setEmpresas(dataEmpresas);
      } catch (err) {
        setError(`Error al cargar la lista de empresas: ${err.message}`);
      }
    };

    const fetchTiposDocumentoByEmpresa = async (currentEmpresaId) => {
      if (!currentEmpresaId) { // No cargar si no hay empresa seleccionada
        setTiposDocumento([]);
        setMapTiposDocumento(new Map());
        return;
      }
      try {
        const resTipos = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/tipos-documento?empresa_id=${currentEmpresaId}`);
        const dataTipos = await resTipos.json();
        if (!resTipos.ok) throw new Error(`Error al cargar tipos de documento: ${dataTipos.message || resTipos.statusText}`);
        setTiposDocumento(dataTipos);
        setMapTiposDocumento(new Map(dataTipos.map(t => [t.id, t])));
      } catch (err) {
        setError(`Error al cargar los tipos de documento para la empresa ${currentEmpresaId}: ${err.message}`);
      }
    };

    fetchEmpresas(); // Cargar la lista de empresas una sola vez

    // Este efecto se dispara cuando filtros.empresaId cambia
    fetchTiposDocumentoByEmpresa(filtros.empresaId);

  }, [filtros.empresaId]); // <-- Ahora depende de filtros.empresaId

  // Opcional: useEffect para establecer la empresaId por defecto si user.empresaId está disponible
  useEffect(() => {
    if (user && user.empresaId && !filtros.empresaId) {
      setFiltros(prev => ({ ...prev, empresaId: user.empresaId }));
    }
  }, [user, filtros.empresaId]); // Depende de user y filtros.empresaId para evitar bucles

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFiltros(prev => ({ ...prev, [name]: value }));
  };

  const handleDateChange = (e) => {
    const { name, value } = e.target;
    setFechas(prev => ({ ...prev, [name]: value }));
  };

  const handleBuscar = async () => {
    let hasError = false;
    // Aseguramos que user.empresaId esté disponible para la búsqueda
    if (!user || !user.empresaId) {
      setError('No se pudo obtener el ID de la empresa del usuario para realizar la búsqueda.');
      return;
    }
    
    if (!filtros.empresaId || !filtros.tipoDocId || !filtros.numero) {
      setError('Por favor, complete los filtros principales (Empresa, Tipo de Doc., Número).');
      hasError = true;
    }
    if (isDateRangeMode && (!fechas.inicio || !fechas.fin)) {
      setError('En modo rango (*.*), debe seleccionar Fecha Desde y Fecha Hasta.');
      hasError = true;
    }
    if (hasError) return;

    setIsLoading(true);
    setError('');
    setMessage('');
    setSearchResult([]);
    setSelectedItems(new Set());
    try {
      // El payload debe usar filtros.empresaId (seleccionado en el dropdown), NO user.empresaId de la sesión
      const payload = { ...filtros }; 
      if (isDateRangeMode) {
        payload.fechaInicio = fechas.inicio;

        payload.fechaFin = fechas.fin;
      }

      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/utilidades/buscar-documento-universal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message);
      
      setSearchResult(data);
      if (data.length === 0) {
        setMessage('No se encontraron resultados para los criterios de búsqueda.');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleSelectItem = (itemId) => {
    setSelectedItems(prevSelected => {
      const newSelected = new Set(prevSelected);
      if (newSelected.has(itemId)) {
        newSelected.delete(itemId);
      } else {
        newSelected.add(itemId);
      }
      return newSelected;
    });
  };

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      const allItemIds = new Set(searchResult.map(item => item.id));
      setSelectedItems(allItemIds);
    } else {
      setSelectedItems(new Set());
    }
  };
  
  const handleErradicar = async () => {
    if (selectedItems.size === 0) {
      setError("No hay items seleccionados para erradicar.");
      return;
    }
    
    const confirmation = window.prompt(`ALTO: Esta acción es irreversible y eliminará permanentemente ${selectedItems.size} registros del sistema.\n\nEscriba "ERRADICAR" para confirmar:`);
    if (confirmation !== 'ERRADICAR') {
      setMessage("Operación de erradicación cancelada por el usuario.");
      return;
    }

    setIsLoading(true);
    setError('');
    setMessage('');

    try {
        const documentoIds = [];
        const logIds = [];

        searchResult.forEach(item => {
            if (selectedItems.has(item.id)) {
                // Asumo que 'Activo' y 'Anulado' son documentos en la tabla 'documentos'
                // mientras que 'ANULACION' y 'ELIMINACION' son logs
                if (item.estado === 'Activo' || item.estado === 'Anulado') {
                    documentoIds.push(item.id);
                } else { // Estados como 'ANULACION' o 'ELIMINACION' vienen del log_eliminaciones
                    logIds.push(item.id);
                }
            }
        });

        const payload = { documentoIds, logIds, empresaId: filtros.empresaId }; // Aseguramos que la empresaId vaya en el payload para la erradicación

        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/utilidades/erradicar-documento`, {  
          method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.message);
        
        setMessage(data.message);
        alert(data.message);
        handleBuscar(); // Volver a buscar para actualizar la lista

    } catch (err) {
        setError(err.message);
    } finally {
        setIsLoading(false);
    }
  };
  
  // --- NUEVO: Handler para mostrar el último documento ---
  const handleShowLastDoc = async () => {
    setIsLoadingModal(true);
    setError('');
    // Aseguramos que user.empresaId esté disponible para la llamada
    if (!user || !user.empresaId) {
        setError('No se pudo obtener el ID de la empresa del usuario para ver el último documento.');
        setIsLoadingModal(false);
        return;
    }
    try {
        // Pasamos empresa_id como query param para el último documento
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/reports/ultimo-documento?empresa_id=${user.empresaId}`);
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.message || 'Error al obtener el último documento.');
        }
        setUltimoDocumentoInfo(data);
        setIsModalOpen(true);
    } catch (err) {
        setError(err.message);
    } finally {
        setIsLoadingModal(false);
    }
  };

  const getStatusClass = (estado) => {
    if (estado === 'Activo') return 'bg-green-100 text-green-800';
    if (estado === 'Anulado') return 'bg-yellow-100 text-yellow-800';
    if (estado === 'ANULACION') return 'bg-orange-100 text-orange-800'; // Tipo de operación de log
    if (estado === 'ELIMINACION') return 'bg-red-100 text-red-800'; // Tipo de operación de log
    return 'bg-gray-100 text-gray-800';
  };

  let isButtonDisabled = isLoading || !filtros.empresaId || !filtros.tipoDocId || !filtros.numero;
  if(isDateRangeMode && (!fechas.inicio || !fechas.fin)) {
      isButtonDisabled = true;
  }

  return (
    <div className="container mx-auto p-4 max-w-6xl space-y-6 bg-gray-50 min-h-screen">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">Inspector y Erradicador Universal</h1>
        <div className='flex items-center space-x-2'>
            <button onClick={handleShowLastDoc} disabled={isLoadingModal} className="px-4 py-2 text-sm font-medium text-white bg-teal-600 rounded-md hover:bg-teal-700 disabled:bg-gray-400">
                {isLoadingModal ? 'Buscando...' : 'Ver Último Documento'}
            </button>
            <BotonRegresar />
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
        <h2 className="text-xl font-semibold mb-4 border-b pb-2 text-gray-700">Panel de Búsqueda</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className='space-y-4'>
                <div>
                    <label htmlFor="empresaId" className="block text-sm font-medium text-gray-700">1. Seleccione Empresa</label>
                    <select id="empresaId" name="empresaId" value={filtros.empresaId} onChange={handleInputChange} className="mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                        <option value="">-- Seleccionar --</option>
                        {empresas.map(e => <option key={e.id} value={e.id}>{e.razon_social}</option>)}
                    </select>
                </div>
                <div>
                    <label htmlFor="tipoDocId" className="block text-sm font-medium text-gray-700">2. Seleccione Tipo de Doc.</label>
                    <select id="tipoDocId" name="tipoDocId" value={filtros.tipoDocId} onChange={handleInputChange} className="mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                        <option value="">-- Seleccionar --</option>
                        {tiposDocumento.map(t => <option key={t.id} value={t.id}>{`${t.codigo} - ${t.nombre}`}</option>)}
                    </select>
                </div>
            </div>
            <div className='space-y-4'>
                 <div>
                    <label htmlFor="numero" className="block text-sm font-medium text-gray-700">3. Ingrese Número o Comodín (*.*)</label>
                    <input type="text" id="numero" name="numero" value={filtros.numero} onChange={handleInputChange} className="mt-1 block w-full py-2 px-3 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" placeholder="Ej: 246 o *.*"/>
                </div>
                <div className='flex items-center space-x-4'>
                    <div className='flex-1'>
                        <label htmlFor="inicio" className="block text-sm font-medium text-gray-700">4. Fecha Desde</label>
                        <input type="date" id="inicio" name="inicio" value={fechas.inicio} onChange={handleDateChange} disabled={!isDateRangeMode} className="mt-1 block w-full py-2 px-3 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100"/>
                    </div>
                    <div className='flex-1'>
                        <label htmlFor="fin" className="block text-sm font-medium text-gray-700">5. Fecha Hasta</label>
                        <input type="date" id="fin" name="fin" value={fechas.fin} onChange={handleDateChange} disabled={!isDateRangeMode} className="mt-1 block w-full py-2 px-3 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100"/>
                    </div>
                </div>
            </div>
        </div>
        <div className="text-center mt-6">
            <button onClick={handleBuscar} disabled={isButtonDisabled} className="w-full md:w-auto flex-grow justify-center py-2 px-8 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed">
              {isLoading ? 'Buscando...' : 'Buscar Documentos'}
            </button>
        </div>
      </div>

      <div className="mt-6">
        {error && <div className="p-4 mb-4 text-sm text-red-700 bg-red-100 rounded-lg" role="alert">{error}</div>}
        {message && <div className="p-4 mb-4 text-sm text-blue-700 bg-blue-100 rounded-lg" role="alert">{message}</div>}

        {searchResult.length > 0 && (
          <div className="mt-4 bg-white p-4 rounded-lg shadow-md border border-gray-200">
             <div className="flex justify-between items-center mb-4">
                <h3 className="font-bold text-gray-700">Resultados Encontrados: {searchResult.length} ({selectedItems.size} seleccionados)</h3>
                <button onClick={handleErradicar} disabled={selectedItems.size === 0 || isLoading} className="text-white bg-red-600 hover:bg-red-700 font-medium rounded-lg text-sm px-4 py-2 disabled:bg-gray-400 disabled:cursor-not-allowed">
                    Erradicar Seleccionados
                </button>
             </div>
             <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="p-4 text-left">
                                <input type="checkbox"
                                  className="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                                  onChange={handleSelectAll}
                                  checked={searchResult.length > 0 && selectedItems.size === searchResult.length}
                                />
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo Doc</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Número</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Detalle</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {searchResult.map(item => {
                            const tipoDoc = mapTiposDocumento.get(item.tipo_documento_id);
                            return (
                                <tr key={`${item.estado}-${item.id}`} className="hover:bg-gray-50">
                                    <td className="p-4">
                                        <input type="checkbox"
                                          className="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                                          checked={selectedItems.has(item.id)}
                                          onChange={() => handleSelectItem(item.id)}
                                        />
                                    </td>
                                    <td className="px-4 py-4 whitespace-nowrap text-sm font-mono text-gray-600">{item.id}</td>
                                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-800">{tipoDoc ? `${tipoDoc.codigo} - ${tipoDoc.nombre}` : `ID: ${item.tipo_documento_id}`}</td>
                                    <td className="px-4 py-4 whitespace-nowrap text-sm font-bold text-gray-800">{item.numero}</td>
                                    <td className="px-4 py-4 whitespace-nowrap text-sm">
                                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusClass(item.estado)}`}>
                                            {item.estado}
                                        </span>
                                    </td>
                                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-600">{item.fecha ? new Date(item.fecha).toLocaleDateString('es-CO') : 'N/A'}</td>
                                    <td className="px-4 py-4 text-sm text-gray-800">{item.detalle}</td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
             </div>
          </div>
        )}
      </div>

        {/* --- NUEVO: Modal para mostrar el último documento --- */}
        {isModalOpen && ultimoDocumentoInfo && (
            <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center" id="my-modal">
                <div className="relative mx-auto p-5 border w-full max-w-md shadow-lg rounded-md bg-white">
                    <div className="text-center">
                        <h3 className="text-lg leading-6 font-medium text-gray-900">Último Documento Registrado</h3>
                        <div className="mt-4 text-left space-y-3">
                            <p><strong className="font-semibold text-gray-700">ID:</strong> {ultimoDocumentoInfo.id}</p>
                            <p><strong className="font-semibold text-gray-700">Tipo:</strong> {ultimoDocumentoInfo.tipo_doc_codigo} - {ultimoDocumentoInfo.tipo_doc_nombre}</p>
                            <p><strong className="font-semibold text-gray-700">Número:</strong> {ultimoDocumentoInfo.numero}</p>
                            <p><strong className="font-semibold text-gray-700">Fecha:</strong> {new Date(ultimoDocumentoInfo.fecha).toLocaleDateString('es-CO')}</p>
                            <p><strong className="font-semibold text-gray-700">Beneficiario:</strong> {ultimoDocumentoInfo.beneficiario}</p>
                            <p><strong className="font-semibold text-gray-700">Total Débitos:</strong> {new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(ultimoDocumentoInfo.total_debitos)}</p>
                        </div>
                        <div className="items-center px-4 py-3 mt-4">
                            <button
                                id="ok-btn"
                                onClick={() => setIsModalOpen(false)}
                                className="px-4 py-2 bg-indigo-500 text-white text-base font-medium rounded-md w-full shadow-sm hover:bg-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                            >
                                Cerrar
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        )}

    </div>
  );
}