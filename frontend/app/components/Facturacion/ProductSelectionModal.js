'use client';

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { 
  FaSearch, 
  FaBoxOpen, 
  FaTimes, 
  FaCheckCircle, 
  FaExclamationTriangle,
  FaCartPlus
} from 'react-icons/fa';
import debounce from 'lodash/debounce';
import * as productosService from '../../../lib/productosService'; 

// Estilos Reusables (Manual v2.0)
const inputClass = "w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm transition-all outline-none pl-10";

export default function ProductSelectionModal({
  isOpen,
  onClose,
  onAddProducts,
  mode = 'venta',
  bodegaIdSeleccionada
}) {
  const [products, setProducts] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedItems, setSelectedItems] = useState({});

  const fetchProducts = useCallback(async (currentSearchTerm) => {
    setIsLoading(true);
    setError('');
    try {
      const filtros = {
        search_term: currentSearchTerm || null,
        grupo_id: null,
        bodega_ids: bodegaIdSeleccionada ? [bodegaIdSeleccionada] : null
      };
      const response = await productosService.buscarProductos(filtros); 
      setProducts(response);
    } catch (err) {
      console.error("Error en fetchProducts:", err);
      setError('No se pudieron cargar los productos.');
    } finally {
      setIsLoading(false);
    }
  }, [bodegaIdSeleccionada]);

  const debouncedFetchProducts = useMemo(
      () => debounce(fetchProducts, 300)
  , [fetchProducts]);

  useEffect(() => {
    if (isOpen) {
      fetchProducts(searchTerm);
      setSelectedItems({});
    }
    return () => {
      debouncedFetchProducts.cancel();
    };
  }, [isOpen, fetchProducts, searchTerm, debouncedFetchProducts]);

  useEffect(() => {
    if (isOpen) {
       debouncedFetchProducts(searchTerm);
    }
  }, [searchTerm, isOpen, debouncedFetchProducts]);

  const handleQuantityChange = (product, quantity) => {
    const qty = parseFloat(quantity);
    
    if (qty < 0) return; 

    if (isNaN(qty) || qty <= 0) {
      const newSelected = { ...selectedItems };
      delete newSelected[product.id];
      setSelectedItems(newSelected);
    } else {
      setSelectedItems(prev => ({
        ...prev,
        [product.id]: { product, quantity: qty }
      }));
    }
  };

  const handleAddClick = () => {
    const itemsToAdd = Object.values(selectedItems).map(item => ({
        producto_id: item.product.id,
        codigo: item.product.codigo,
        nombre: item.product.nombre,
        cantidad: item.quantity,
        precio_unitario: item.product.precio_base_manual || item.product.precio_venta || 0, 
        costo_unitario: item.product.costo_promedio || 0
    }));
    onAddProducts(itemsToAdd);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex justify-center items-center p-4 animate-fadeIn">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col border border-gray-100">
        
        {/* HEADER */}
        <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50 rounded-t-xl">
          <div>
            <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                <FaBoxOpen className="text-indigo-500"/> Seleccionar Productos
            </h2>
            <p className="text-sm text-gray-500 mt-1">Busque y seleccione los items para añadir al documento.</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors text-2xl p-2 hover:bg-gray-200 rounded-full">
            <FaTimes />
          </button>
        </div>

        {/* BUSCADOR */}
        <div className="p-6 border-b border-gray-100 bg-white">
          <div className="relative">
            <input
                type="text"
                placeholder="Buscar por código, nombre o referencia..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className={inputClass}
                autoFocus
            />
            <FaSearch className="absolute left-4 top-4 text-gray-400 text-lg pointer-events-none" />
          </div>
          {error && (
              <div className="mt-3 flex items-center gap-2 text-red-600 text-sm bg-red-50 p-2 rounded border border-red-100">
                  <FaExclamationTriangle /> {error}
              </div>
          )}
        </div>

        {/* TABLA DE RESULTADOS */}
        <div className="flex-grow overflow-y-auto p-0 bg-gray-50">
          {isLoading && products.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-indigo-500">
                <span className="loading loading-spinner loading-lg mb-4"></span> 
                <p className="font-medium">Cargando catálogo...</p>
            </div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-white sticky top-0 shadow-sm z-10">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Código</th>
                  <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider w-1/3">Producto</th>
                  <th className="px-6 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider">Stock {bodegaIdSeleccionada ? '(Bodega)' : '(Global)'}</th>
                  <th className="px-6 py-3 text-right text-xs font-bold text-gray-500 uppercase tracking-wider">{mode === 'compra' ? 'Costo Prom.' : 'Precio Venta'}</th>
                  <th className="px-6 py-3 text-center text-xs font-bold text-indigo-600 uppercase tracking-wider w-32 bg-indigo-50">Cantidad</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100">
                {products.length === 0 && !isLoading ? (
                     <tr><td colSpan="5" className="text-center text-gray-400 py-12 italic">No se encontraron productos con ese criterio.</td></tr>
                ) : (
                    products.map(product => {
                        const isSelected = !!selectedItems[product.id];
                        const stockValue = product.stock_actual ?? 0;
                        const hasStock = stockValue > 0;

                        return (
                          <tr key={product.id} className={`transition-colors ${isSelected ? 'bg-indigo-50' : 'hover:bg-gray-50'}`}>
                            <td className="px-6 py-3 font-mono text-sm text-gray-600 font-semibold">{product.codigo}</td>
                            <td className="px-6 py-3 text-sm font-medium text-gray-800">{product.nombre}</td>
                            
                            <td className="px-6 py-3 text-right font-mono text-sm">
                                {product.es_servicio ? (
                                    <span className="text-gray-400 text-xs italic">Servicio</span>
                                ) : (
                                    <span className={`font-bold ${!hasStock ? 'text-red-500' : 'text-gray-700'}`}>
                                        {stockValue.toLocaleString('es-CO')}
                                    </span>
                                )}
                            </td>
                            
                            <td className="px-6 py-3 text-right font-mono text-sm text-gray-600">
                                ${(mode === 'compra' ? product.costo_promedio : product.precio_venta || 0).toLocaleString('es-CO')}
                            </td>
                            
                            <td className={`px-4 py-2 text-center border-l ${isSelected ? 'border-indigo-200 bg-indigo-100/50' : 'border-gray-100'}`}>
                                <input
                                    type="number"
                                    min="0"
                                    value={selectedItems[product.id]?.quantity || ''}
                                    onChange={(e) => handleQuantityChange(product, e.target.value)}
                                    className={`w-20 p-1.5 border rounded-lg text-center text-sm font-bold outline-none transition-all ${isSelected ? 'border-indigo-500 ring-2 ring-indigo-200 text-indigo-700 bg-white' : 'border-gray-300 text-gray-700 focus:border-indigo-400'}`}
                                    placeholder="0"
                                />
                            </td>
                          </tr>
                        );
                    })
                )}
              </tbody>
            </table>
          )}
        </div>

        {/* FOOTER ACCIONES */}
        <div className="p-6 border-t border-gray-100 bg-white rounded-b-xl flex justify-between items-center">
            <div className="text-sm text-gray-500">
                {Object.keys(selectedItems).length > 0 ? (
                    <span className="text-indigo-600 font-bold flex items-center gap-2">
                        <FaCheckCircle /> {Object.keys(selectedItems).length} producto(s) seleccionado(s)
                    </span>
                ) : (
                    <span>Seleccione cantidades para añadir.</span>
                )}
            </div>
            <div className="flex gap-3">
                <button onClick={onClose} className="px-5 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors font-medium">
                    Cancelar
                </button>
                <button
                    onClick={handleAddClick}
                    disabled={Object.keys(selectedItems).length === 0}
                    className="px-8 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 shadow-md font-bold flex items-center gap-2 disabled:bg-gray-300 disabled:cursor-not-allowed transform transition-transform active:scale-95"
                >
                    <FaCartPlus /> Añadir al Documento
                </button>
            </div>
        </div>
      </div>
    </div>
  );
}