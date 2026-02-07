'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { getPeriodosCerrados, cerrarPeriodo, reabrirPeriodo } from '../../../../lib/periodosService';
import { apiService } from '../../../../lib/apiService';
import { FaBook } from 'react-icons/fa';

export default function GestionPeriodosPage() {
  const { user } = useAuth();
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [fechaInicioOp, setFechaInicioOp] = useState(null);
  const [periodos, setPeriodos] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [operacionEnCurso, setOperacionEnCurso] = useState(null);

  const fetchData = useCallback(async () => {
    // Guardián: No hacer nada hasta que el usuario y su empresaId estén listos.
    if (!user || !user.empresaId) {
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError('');
    try {
      // --- CORRECCIÓN CLAVE ---
      // Se obtienen los datos de forma secuencial para evitar condiciones de carrera.
      // 1. Obtener primero los datos de la empresa.
      const empresaResponse = await apiService.get(`/empresas/${user.empresaId}`);
      // Asumimos formato YYYY-MM-DD
      const fechaParts = empresaResponse.data.fecha_inicio_operaciones.split('-');
      const fechaInicio = new Date(fechaParts[0], fechaParts[1] - 1, fechaParts[2]);
      setFechaInicioOp(fechaInicio);

      // 2. Luego, obtener los períodos cerrados.
      const periodosData = await getPeriodosCerrados();

      // 3. Generar la vista basada en el AÑO SELECCIONADO
      const mesesDelAno = Array.from({ length: 12 }, (_, i) => {
        const mes = i + 1;
        const cerrado = periodosData.some(p => p.ano === selectedYear && p.mes === mes);
        return { ano: selectedYear, mes, estado: cerrado ? 'Cerrado' : 'Abierto' };
      });
      setPeriodos(mesesDelAno);

    } catch (err) {
      setError('Error al cargar la configuración de los períodos.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, [user, selectedYear]); // Dependencia clave: selectedYear

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Generar lista de años disponibles (Mínimo desde 2019 o Inicio Operaciones)
  const availableYears = [];
  const currentYear = new Date().getFullYear();
  const endYear = 2050; // Extend range to 2050 per user request

  let startYear = 2019; // Piso histórico solicitado
  if (fechaInicioOp) {
    const opYear = fechaInicioOp.getFullYear();
    if (opYear < startYear) startYear = opYear;
  }

  for (let y = startYear; y <= endYear; y++) {
    availableYears.push(y);
  }

  const handleCerrarPeriodo = async (ano, mes) => {
    if (!window.confirm(`¿Está seguro de que desea cerrar el período ${mes}/${ano}?`)) return;
    setOperacionEnCurso({ ano, mes });
    setError('');
    try {
      await cerrarPeriodo(ano, mes);
      alert('Período cerrado exitosamente.');
      fetchData(); // Refrescar la lista
    } catch (err) {
      setError(err.response?.data?.detail || 'Ocurrió un error al cerrar el período.');
    } finally {
      setOperacionEnCurso(null);
    }
  };

  const handleReabrirPeriodo = async (ano, mes) => {
    if (!window.confirm(`ADVERTENCIA: ¿Está seguro de que desea reabrir el período ${mes}/${ano}?`)) return;
    setOperacionEnCurso({ ano, mes });
    setError('');
    try {
      await reabrirPeriodo(ano, mes);
      alert('Período reabierto exitosamente.');
      fetchData(); // Refrescar la lista
    } catch (err) {
      setError(err.response?.data?.detail || 'Ocurrió un error al reabrir el período.');
    } finally {
      setOperacionEnCurso(null);
    }
  };

  const esCerrable = (periodo, index) => {
    if (!fechaInicioOp || periodo.estado !== 'Abierto') return false;

    const fechaPeriodoActual = new Date(periodo.ano, periodo.mes - 1, 1);
    const fechaInicioNormalizada = new Date(fechaInicioOp.getFullYear(), fechaInicioOp.getMonth(), 1);

    // No permitir cerrar periodos anteriores al inicio de operaciones
    if (fechaPeriodoActual < fechaInicioNormalizada) {
      return false;
    }

    const esPrimerMesOperativo = periodo.ano === fechaInicioOp.getFullYear() && periodo.mes === fechaInicioOp.getMonth() + 1;

    // Si es el primer mes del año, necesitamos ver el diciembre ANTERIOR
    if (index === 0) {
      // Excepción: Si es el primer mes de operaciones absoluta, se puede cerrar
      if (esPrimerMesOperativo) return true;
      // TO-DO: Idealmente consultaríamos el estado de Diciembre del año anterior.
      // Por ahora, para simplificar lógica visual en frontend y dado que el backend valida:
      return true;
    }

    if (esPrimerMesOperativo) return true;

    return periodos[index - 1].estado === 'Cerrado';
  };

  const esReabrible = (periodo, index) => {
    if (periodo.estado !== 'Cerrado') return false;

    // El último período del año siempre es reabrible si está cerrado
    if (index === 11) return true;

    // Un período es reabrible si el siguiente está abierto
    return periodos[index + 1].estado === 'Abierto';
  };

  // RENDER MODIFICADO
  return (
    <div className="container mx-auto p-4">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <h1 className="text-3xl font-bold text-gray-800">Gestión de Períodos</h1>
          <button
            onClick={() => window.open('/manual/capitulo_7_cierre.html', '_blank')}
            className="btn btn-ghost text-indigo-600 hover:bg-indigo-50 gap-2 flex items-center px-2"
            title="Ver Manual de Usuario"
          >
            <FaBook className="text-lg" /> <span className="font-bold hidden md:inline">Manual</span>
          </button>
        </div>

        {/* SELECTOR DE AÑO */}
        <div className="flex items-center gap-2">
          <span className="font-semibold text-gray-600">Año:</span>
          <select
            value={selectedYear}
            onChange={(e) => setSelectedYear(parseInt(e.target.value))}
            className="select select-bordered select-sm w-32"
          >
            {availableYears.map(y => <option key={y} value={y}>{y}</option>)}
          </select>
        </div>
      </div>

      {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">{error}</div>}

      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4 text-indigo-700 border-b pb-2">Periodos del {selectedYear}</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white">
            <thead className="bg-gray-800 text-white">
              <tr>
                <th className="py-3 px-4 uppercase font-semibold text-sm">Mes</th>
                <th className="py-3 px-4 uppercase font-semibold text-sm">Estado</th>
                <th className="py-3 px-4 uppercase font-semibold text-sm text-center">Acciones</th>
              </tr>
            </thead>
            <tbody className="text-gray-700">
              {periodos.map((periodo, index) => {
                const nombreMes = new Date(periodo.ano, periodo.mes - 1).toLocaleString('es-CO', { month: 'long' });
                const enOperacion = operacionEnCurso?.ano === periodo.ano && operacionEnCurso?.mes === periodo.mes;

                return (
                  <tr key={`${periodo.ano}-${periodo.mes}`} className="border-b">
                    <td className="py-3 px-4 capitalize">{nombreMes}</td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${periodo.estado === 'Cerrado' ? 'bg-red-200 text-red-800' : 'bg-green-200 text-green-800'}`}>
                        {periodo.estado}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      {esCerrable(periodo, index) && (
                        <button
                          onClick={() => handleCerrarPeriodo(periodo.ano, periodo.mes)}
                          disabled={enOperacion}
                          className="bg-blue-500 text-white font-bold py-1 px-3 rounded hover:bg-blue-700 disabled:bg-gray-400"
                        >
                          {enOperacion ? 'Cerrando...' : 'Cerrar Período'}
                        </button>
                      )}
                      {esReabrible(periodo, index) && (
                        <button
                          onClick={() => handleReabrirPeriodo(periodo.ano, periodo.mes)}
                          disabled={enOperacion}
                          className="bg-yellow-500 text-white font-bold py-1 px-3 rounded hover:bg-yellow-700 disabled:bg-gray-400"
                        >
                          {enOperacion ? 'Abriendo...' : 'Reabrir Período'}
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}