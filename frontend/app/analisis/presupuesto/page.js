"use client";

import React, { useState, useEffect } from 'react';
import { 
  Plus, 
  Search, 
  ChevronRight, 
  ChevronDown, 
  Save, 
  RefreshCcw, 
  Calendar,
  DollarSign,
  FileText,
  TrendingUp,
  Upload
} from 'lucide-react';
import { toast } from 'react-toastify';
import { apiService } from '../../../lib/apiService';
import ReporteEjecucion from './ReporteEjecucion';
import './style.css';

const BudgetPage = () => {
    const [anio, setAnio] = useState(new Date().getFullYear());
    const [activeTab, setActiveTab] = useState('gestion'); // 'gestion' or 'comparativo'
    const [pucData, setPucData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedAccount, setSelectedAccount] = useState(null);
    const [monthlyDetails, setMonthlyDetails] = useState([]);
    const [expandedRows, setExpandedRows] = useState(new Set());
    const [annualInput, setAnnualInput] = useState('');

    useEffect(() => {
        if (activeTab === 'gestion') fetchPuc();
    }, [anio, activeTab]);

    const fetchPuc = async () => {
        setLoading(true);
        try {
            const res = await apiService.get(`/presupuesto/puc?anio=${anio}`);
            setPucData(res.data);
        } catch (error) {
            toast.error("Error al cargar el PUC");
        } finally {
            setLoading(false);
        }
    };

    const toggleRow = (codigo) => {
        const newExpanded = new Set(expandedRows);
        if (newExpanded.has(codigo)) {
            newExpanded.delete(codigo);
        } else {
            newExpanded.add(codigo);
        }
        setExpandedRows(newExpanded);
    };

    const handleSelectAccount = async (account) => {
        if (!account.permite_movimiento) {
            toast.info("Selecciona una cuenta auxiliar (último nivel) para gestionar su presupuesto.");
            return;
        }
        
        setSelectedAccount(account);
        setAnnualInput(account.presupuesto_anual?.toString() || '');
        
        try {
            const res = await apiService.get(`/presupuesto/detalle/${account.codigo}/${anio}`);
            setMonthlyDetails(res.data);
        } catch (error) {
            toast.error("Error al cargar detalles mensuales");
        }
    };

    const cleanNumericString = (val) => {
        if (typeof val === 'number') return val;
        if (!val) return 0;
        // Remove all dots (thousands) and replace comma with dot (decimals)
        const cleaned = val.toString().replace(/\./g, '').replace(',', '.');
        return parseFloat(cleaned) || 0;
    };

    const handleSaveAnnual = async () => {
        if (!selectedAccount || !annualInput) return;
        
        const numericValue = cleanNumericString(annualInput);
        if (isNaN(numericValue)) {
            toast.error("Valor anual inválido");
            return;
        }

        try {
            await apiService.post(`/presupuesto/registrar`, {
                anio: anio,
                codigo_cuenta: selectedAccount.codigo,
                valor_anual: numericValue
            });
            toast.success("Presupuesto anual registrado y distribuido");
            fetchPuc();
            handleSelectAccount(selectedAccount); // Refresh monthly details
        } catch (error) {
            toast.error("Error al guardar el presupuesto");
        }
    };

    const handleEditMonth = async (detalleId, nuevoValor) => {
        const numericValue = cleanNumericString(nuevoValor);
        if (isNaN(numericValue)) return;
        
        try {
            await apiService.patch(`/presupuesto/editar-mes/${detalleId}`, { 
                nuevo_valor: numericValue
            });
            toast.success("Mes actualizado");
            // Local update to avoid full reload
            setMonthlyDetails(prev => prev.map(d => d.id === detalleId ? { ...d, valor_vigente: numericValue, valor_editado: numericValue } : d));
        } catch (error) {
            console.error("Error updating month:", error);
            toast.error("Error al actualizar mes");
        }
    };

    const handleImportExcel = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('archivo', file);
        formData.append('anio', anio);

        setLoading(true);
        try {
            const res = await apiService.post('/presupuesto/importar', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            
            const { success, errors } = res.data;
            if (success > 0) {
                toast.success(`Se importaron ${success} cuentas correctamente.`);
                fetchPuc();
            }
            if (errors && errors.length > 0) {
                // Show first few errors
                errors.slice(0, 3).forEach(err => toast.warning(err));
                if (errors.length > 3) toast.info(`Y ${errors.length - 3} errores más...`);
            }
        } catch (error) {
            toast.error(error.response?.data?.detail || "Error al importar el archivo");
        } finally {
            setLoading(false);
            e.target.value = null; // Reset input
        }
    };

    const visiblePuc = pucData.filter(acc => {
        // Si hay búsqueda, mostrar todo lo que coincida
        if (searchTerm) {
            return acc.codigo.includes(searchTerm) || acc.nombre.toLowerCase().includes(searchTerm.toLowerCase());
        }
        
        // Si no hay búsqueda, aplicar lógica de expansión
        if (acc.nivel === 1) return true;
        
        // Para niveles superiores, verificar si todos los padres están expandidos
        // Buscamos el ancestro inmediato
        const parent = pucData.find(p => 
            acc.codigo.startsWith(p.codigo) && 
            p.codigo !== acc.codigo && 
            p.nivel === acc.nivel - 1
        );
        
        if (!parent) return true; // No debería pasar si el PUC es coherente
        
        // Una cuenta es visible si su padre está expandido Y es visible
        // (La visibilidad del padre se valida recursivamente o por el hecho de que iteramos sobre todo el array)
        // Pero en un flat array filter, necesitamos una forma eficiente.
        // Como el array está ordenado (gracias al backend), podemos asumir que los padres vienen antes.
        
        return expandedRows.has(parent.codigo);
        // Nota: Para soporte multinivel profundo (3+ niveles), necesitamos verificar recursivamente 
        // o asegurarnos de que si el abuelo está cerrado, el padre no esté en expandedRows.
        // Por simplicidad y rendimiento, checkeamos solo el padre inmediato. 
        // Si el usuario colapsa el abuelo, el padre sigue "expandido" en el set pero oculto, 
        // así que el hijo también debe ocultarse.
    }).filter(acc => {
        // Segunda pasada para asegurar jerarquía profunda (abuelo colapsado -> hijo oculto)
        if (!searchTerm && acc.nivel > 1) {
            let currentLevel = acc.nivel;
            let currentCode = acc.codigo;
            
            while (currentLevel > 1) {
                const p = pucData.find(x => currentCode.startsWith(x.codigo) && x.codigo !== currentCode && x.nivel === currentLevel - 1);
                if (!p || !expandedRows.has(p.codigo)) return false;
                currentCode = p.codigo;
                currentLevel = p.nivel;
            }
        }
        return true;
    });

    const renderPucRow = (acc) => {
        const isExpanded = expandedRows.has(acc.codigo);
        const hasChildren = pucData.some(child => child.codigo.startsWith(acc.codigo) && child.codigo !== acc.codigo && child.nivel === acc.nivel + 1);
        
        return (
            <div 
                key={acc.codigo} 
                className={`flex items-center p-2 hover:bg-gray-50 cursor-pointer border-b text-sm 
                    ${selectedAccount?.codigo === acc.codigo ? 'bg-blue-50 ring-1 ring-blue-200 ring-inset' : ''}
                    ${!acc.permite_movimiento ? 'text-gray-400 bg-gray-50/20' : 'text-slate-700 font-semibold'}
                `}
                style={{ paddingLeft: `${(acc.nivel - 1) * 20}px` }}
                onClick={() => handleSelectAccount(acc)}
            >
                <div onClick={(e) => { e.stopPropagation(); toggleRow(acc.codigo); }} className="w-6 h-6 flex items-center justify-center mr-2">
                    {hasChildren && (isExpanded ? <ChevronDown size={14} className="text-gray-400" /> : <ChevronRight size={14} className="text-gray-400" />)}
                </div>
                <span className="font-mono w-24 shrink-0">{acc.codigo}</span>
                <span className="flex-grow truncate mr-2">{acc.nombre}</span>
                
                <div className="flex items-center space-x-2">
                    {acc.permite_movimiento ? (
                        <span className="text-[10px] bg-indigo-100 text-indigo-700 px-1.5 py-0.5 rounded font-bold uppercase shrink-0">Auxiliar</span>
                    ) : (
                        <span className="text-[10px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded font-medium uppercase shrink-0">Grupo</span>
                    )}
                    
                    {acc.tiene_presupuesto && (
                        <span className="text-[10px] bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full font-bold shrink-0">
                            ${parseFloat(acc.presupuesto_anual).toLocaleString()}
                        </span>
                    )}
                </div>
            </div>
        );
    };

    return (
        <div className="flex flex-col h-full bg-slate-50 p-6 space-y-6">
            <header className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-gray-800">Módulo de Presupuesto</h1>
                    <p className="text-gray-500">Gestión anual integrada al PUC</p>
                </div>
                <div className="flex items-center space-x-4">
                    <div className="bg-white rounded-lg shadow-sm border p-1 flex items-center">
                        <Calendar size={18} className="text-gray-400 mx-2" />
                        <select 
                            value={anio} 
                            onChange={(e) => setAnio(parseInt(e.target.value))}
                            className="bg-transparent border-none focus:ring-0 text-gray-700 font-medium"
                        >
                            {[2024, 2025, 2026].map(y => <option key={y} value={y}>{y}</option>)}
                        </select>
                    </div>
                    <div className="flex bg-white rounded-lg shadow-sm border p-1">
                        <button 
                            onClick={() => document.getElementById('budget-import-input').click()}
                            className="p-1 px-3 flex items-center gap-2 text-sm font-medium text-blue-600 hover:bg-blue-50 transition rounded-md border-r"
                            title="Importar desde Excel/CSV"
                        >
                            <Upload size={16} />
                            <span className="hidden sm:inline">Importar</span>
                        </button>
                        <input 
                            id="budget-import-input"
                            type="file" 
                            hidden 
                            accept=".csv, .xlsx, .xls"
                            onChange={handleImportExcel}
                        />
                        <button 
                            onClick={() => setActiveTab('gestion')}
                            className={`px-4 py-1.5 rounded-md text-sm font-medium transition ${activeTab === 'gestion' ? 'bg-blue-600 text-white' : 'text-gray-500 hover:text-gray-700'}`}
                        >
                            Gestión
                        </button>
                        <button 
                            onClick={() => setActiveTab('comparativo')}
                            className={`px-4 py-1.5 rounded-md text-sm font-medium transition ${activeTab === 'comparativo' ? 'bg-blue-600 text-white' : 'text-gray-500 hover:text-gray-700'}`}
                        >
                            Comparativo
                        </button>
                    </div>
                </div>
            </header>

            {activeTab === 'gestion' ? (
                <div className="grid grid-cols-12 gap-6 flex-grow overflow-hidden">
                    {/* Left Panel: PUC Tree */}
                    <div className="col-span-12 lg:col-span-5 bg-white rounded-xl shadow-sm border flex flex-col overflow-hidden">
                        <div className="p-4 border-b bg-gray-50/50 flex items-center space-x-2">
                            <Search size={18} className="text-gray-400" />
                            <input 
                                type="text" 
                                placeholder="Buscar cuenta por código o nombre..."
                                className="flex-grow bg-transparent border-none focus:ring-0 text-sm"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                            />
                        </div>
                        <div className="flex-grow overflow-y-auto">
                            {loading ? (
                                <div className="flex items-center justify-center p-12 text-gray-400">
                                    <RefreshCcw className="animate-spin mr-2" /> Cargando PUC...
                                </div>
                            ) : visiblePuc.map(acc => renderPucRow(acc))}
                        </div>
                    </div>

                    {/* Right Panel: Account details & Monthly Distribution */}
                    <div className="col-span-12 lg:col-span-7 bg-white rounded-xl shadow-sm border flex flex-col overflow-hidden">
                        {selectedAccount ? (
                            <>
                                <div className="p-6 border-b bg-slate-50/50">
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <h2 className="text-xl font-bold text-gray-800">{selectedAccount.nombre}</h2>
                                            <p className="font-mono text-gray-500">{selectedAccount.codigo}</p>
                                        </div>
                                        <div className="bg-blue-100 text-blue-700 px-3 py-1 rounded-lg font-bold text-lg">
                                            Total: ${monthlyDetails.reduce((acc, curr) => acc + parseFloat(curr.valor_vigente), 0).toLocaleString()}
                                        </div>
                                    </div>
                                    
                                    <div className="mt-6 flex items-end space-x-4">
                                        <div className="flex-grow">
                                            <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Presupuesto Anual Total</label>
                                            <div className="relative">
                                                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18}/>
                                                <input 
                                                    type="number"
                                                    className="w-full pl-10 pr-4 py-3 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                                                    placeholder="0.00"
                                                    value={annualInput}
                                                    onChange={(e) => setAnnualInput(e.target.value)}
                                                />
                                            </div>
                                        </div>
                                        <button 
                                            onClick={handleSaveAnnual}
                                            className="bg-gray-800 text-white px-6 py-3 rounded-xl hover:bg-black transition flex items-center space-x-2 shadow-lg"
                                        >
                                            <Save size={18} />
                                            <span>Distribuir Lineal</span>
                                        </button>
                                    </div>
                                    <p className="mt-2 text-xs text-gray-400 italic">Se dividirá en 12 cuotas iguales con ajuste por redondeo.</p>
                                </div>

                                <div className="flex-grow p-6 overflow-y-auto">
                                    <h3 className="text-sm font-bold text-gray-600 mb-4 flex items-center">
                                        <FileText size={16} className="mr-2" />
                                        Desglose Mensual
                                    </h3>
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                        {monthlyDetails.map((mes, idx) => (
                                            <div key={mes.id} className={`p-4 rounded-xl border transition-all ${mes.valor_editado ? 'border-amber-200 bg-amber-50/30' : 'border-gray-100 bg-white'}`}>
                                                <div className="flex justify-between mb-2">
                                                    <span className="text-xs font-bold text-gray-400 uppercase">{
                                                        ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"][idx]
                                                    }</span>
                                                    {mes.valor_editado && (
                                                        <span className="text-[10px] bg-amber-200 text-amber-800 px-1.5 rounded uppercase font-bold">Editado</span>
                                                    )}
                                                </div>
                                                 <div className="flex items-center space-x-2">
                                                    <DollarSign size={14} className="text-gray-400" />
                                                    <input 
                                                        type="number"
                                                        className="w-full bg-transparent border-none focus:ring-0 text-right font-bold text-gray-800"
                                                        value={mes.valor_vigente}
                                                        onChange={(e) => {
                                                            const val = e.target.value;
                                                            setMonthlyDetails(prev => prev.map(d => d.id === mes.id ? { ...d, valor_vigente: val } : d));
                                                        }}
                                                        onBlur={(e) => handleEditMonth(mes.id, e.target.value)}
                                                    />
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </>
                        ) : (
                            <div className="flex-grow flex flex-col items-center justify-center p-12 text-center">
                                <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mb-4 text-slate-300">
                                    <Plus size={40} />
                                </div>
                                <h3 className="text-lg font-bold text-gray-800">Selecciona una cuenta</h3>
                                <p className="text-gray-500 max-w-xs mx-auto">Elige una cuenta auxiliar del PUC a la izquierda para gestionar su presupuesto.</p>
                            </div>
                        )}
                    </div>
                </div>
            ) : (
                <div className="flex-grow overflow-auto">
                    <ReporteEjecucion anio={anio} />
                </div>
            )}
        </div>
    );
};

export default BudgetPage;
