"use client";
import React from 'react';
import { useTheme } from '../context/ThemeContext';

export default function SmartSearchSection() {
    const { isDarkMode } = useTheme();

    return (
        <div className="flex flex-col items-center justify-center min-h-[85vh] w-full px-4 animate-in fade-in zoom-in duration-500 bg-transparent">
            {/* Logo Section Only */}
            <div className="text-center relative group select-none">
                <div className="absolute -inset-8 bg-gradient-to-r from-blue-400 via-indigo-500 to-purple-500 rounded-full blur-[60px] opacity-10 group-hover:opacity-30 transition duration-1000 group-hover:duration-500"></div>
                <img
                    src="/logo.png?v=7"
                    alt="Finaxis ERP"
                    className={`relative w-auto object-contain transform transition-all duration-700 hover:scale-105 ${isDarkMode ? 'invert brightness-[2] contrast-[1.2]' : 'mix-blend-multiply'}`}
                    style={{
                        height: 'clamp(400px, 75vh, 900px)'
                    }}
                />
            </div>
        </div>
    );
}
