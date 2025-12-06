// frontend/app/components/ui/Paginacion.js
'use client';
import React from 'react';
import { FaChevronLeft, FaChevronRight } from 'react-icons/fa';

export default function Paginacion({ paginaActual, totalPaginas, onPageChange }) {
  if (totalPaginas <= 1) {
    return null; // No mostrar paginación si solo hay una página o menos
  }

  const handlePageClick = (page) => {
    if (page < 1 || page > totalPaginas || page === paginaActual) {
      return;
    }
    onPageChange(page);
  };

  const renderPageNumbers = () => {
    const pageNumbers = [];
    const maxPagesToShow = 5; // Cantidad de números de página a mostrar
    const halfPagesToShow = Math.floor(maxPagesToShow / 2);

    let startPage = Math.max(1, paginaActual - halfPagesToShow);
    let endPage = Math.min(totalPaginas, paginaActual + halfPagesToShow);

    if (paginaActual - halfPagesToShow <= 1) {
      endPage = Math.min(totalPaginas, maxPagesToShow);
    }

    if (paginaActual + halfPagesToShow >= totalPaginas) {
      startPage = Math.max(1, totalPaginas - maxPagesToShow + 1);
    }
    
    // Estilos base para botones de número
    const baseClass = "px-3 py-1 mx-1 rounded-lg text-sm font-bold transition-all duration-200 border shadow-sm min-w-[2.5rem]";
    const activeClass = "bg-indigo-600 text-white border-indigo-600 transform scale-105";
    const inactiveClass = "bg-white text-gray-600 hover:bg-indigo-50 border-gray-200 hover:border-indigo-300 hover:text-indigo-600";

    // Botón para ir a la primera página
    if (startPage > 1) {
      pageNumbers.push(
        <button 
            key="first" 
            onClick={() => handlePageClick(1)} 
            className={`${baseClass} ${inactiveClass}`}
        >
            1
        </button>
      );
      if (startPage > 2) {
        pageNumbers.push(<span key="start-ellipsis" className="px-1 text-gray-400 flex items-end">...</span>);
      }
    }

    // Números de página intermedios
    for (let i = startPage; i <= endPage; i++) {
      pageNumbers.push(
        <button
          key={i}
          onClick={() => handlePageClick(i)}
          className={`${baseClass} ${i === paginaActual ? activeClass : inactiveClass}`}
        >
          {i}
        </button>
      );
    }

    // Botón para ir a la última página
    if (endPage < totalPaginas) {
      if (endPage < totalPaginas - 1) {
        pageNumbers.push(<span key="end-ellipsis" className="px-1 text-gray-400 flex items-end">...</span>);
      }
      pageNumbers.push(
        <button 
            key="last" 
            onClick={() => handlePageClick(totalPaginas)} 
            className={`${baseClass} ${inactiveClass}`}
        >
            {totalPaginas}
        </button>
      );
    }

    return pageNumbers;
  };

  return (
    <div className="flex justify-center items-center mt-8 gap-2 animate-fadeIn">
      {/* Botón Anterior */}
      <button
        onClick={() => handlePageClick(paginaActual - 1)}
        disabled={paginaActual === 1}
        className="p-2 rounded-lg bg-white border border-gray-200 text-gray-500 hover:text-indigo-600 hover:bg-indigo-50 hover:border-indigo-300 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm"
        title="Página Anterior"
      >
        <FaChevronLeft />
      </button>

      {/* Números (Desktop) */}
      <div className="hidden md:flex items-center">
        {renderPageNumbers()}
      </div>

      {/* Texto (Móvil) */}
       <div className="md:hidden flex items-center bg-white px-4 py-1 rounded-lg border border-gray-200 shadow-sm">
        <span className="text-sm font-medium text-gray-600">
            Página <span className="text-indigo-600 font-bold">{paginaActual}</span> de {totalPaginas}
        </span>
      </div>

      {/* Botón Siguiente */}
      <button
        onClick={() => handlePageClick(paginaActual + 1)}
        disabled={paginaActual === totalPaginas}
        className="p-2 rounded-lg bg-white border border-gray-200 text-gray-500 hover:text-indigo-600 hover:bg-indigo-50 hover:border-indigo-300 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm"
        title="Página Siguiente"
      >
        <FaChevronRight />
      </button>
    </div>
  );
}