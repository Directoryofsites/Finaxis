"use client";
import React from 'react';

export default function SmartSearchSection() {
    return (
        <div className="flex flex-col items-center justify-center min-h-[85vh] w-full px-4 animate-in fade-in zoom-in duration-500 bg-gray-50/30">
            {/* Logo Section Only */}
            <div className="text-center relative group select-none">
                <div className="absolute -inset-8 bg-gradient-to-r from-blue-400 via-indigo-500 to-purple-500 rounded-full blur-[60px] opacity-10 group-hover:opacity-30 transition duration-1000 group-hover:duration-500"></div>
                <img
                    src="/logo_finaxis_real.png"
                    alt="Finaxis ERP"
                    className="relative h-28 object-contain drop-shadow-[0_10px_25px_rgba(0,0,0,0.15)] transform transition-transform duration-700 hover:scale-105"
                />
            </div>
        </div>
    );
}
