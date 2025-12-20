"use client";
import React from 'react';

/**
 * CleanHomePage - "Lienzo en Blanco" con Logo Real
 * 
 * Muestra el logo oficial de Finaxis como marca de agua.
 */
export default function CleanHomePage() {
    return (
        <div className="h-full w-full flex flex-col items-center justify-center bg-gray-50 select-none overflow-hidden relative">

            {/* Branding Central (Marca de Agua) */}
            <div className="flex flex-col items-center justify-center opacity-30 transform scale-125 pointer-events-none filter saturate-0">

                {/* LOGO REAL: Cargado desde public/logo_finaxis_real.png */}
                <img
                    src="/logo_finaxis_real.png"
                    alt="Finaxis ERP"
                    className="w-auto h-48 object-contain mb-8"
                />

                {/* Texto opcional si el logo no tiene texto, pero como sí tiene, esto podría sobrar.
                    Lo dejo comentado por si acaso el logo es solo isotipo.
                */}
                {/* 
                <h1 className="text-5xl font-bold text-slate-800 tracking-tight mt-4">FINAXIS</h1>
                <p className="text-xl font-light text-slate-500 tracking-widest mt-2 uppercase">Enterprise ERP</p> 
                */}
            </div>

            {/* Pista de Uso (Sutil, abajo) */}
            <div className="absolute bottom-10 text-slate-400 text-sm font-medium animate-pulse flex items-center">
                <span className="mr-2">Presione</span>
                <kbd className="px-2 py-0.5 bg-white border border-gray-300 rounded shadow-[0_2px_0_rgba(0,0,0,0.1)] text-slate-600 font-bold font-mono text-xs">Alt</kbd>
                <span className="ml-2">para Menú Principal</span>
            </div>

            {/* Decoración de Fondo (Patrón de Puntos) */}
            <div className="absolute inset-0 z-[-1] opacity-[0.03]"
                style={{
                    backgroundImage: 'radial-gradient(#000000 1px, transparent 1px)',
                    backgroundSize: '24px 24px'
                }}
            ></div>
        </div>
    );
}
