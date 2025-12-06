'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { FaBook, FaPrint, FaTimes } from 'react-icons/fa';

// --- Componentes Personalizados para Markdown (Diseño Estricto) ---
const MarkdownComponents = {
    // Títulos: Mayor peso y espacio superior. Color #1E1E1E.
    h1: ({ node, ...props }) => (
        <h1 className="text-4xl font-extrabold text-[#1E1E1E] mt-12 mb-8 border-b border-gray-200 pb-4 tracking-tight" {...props} />
    ),
    h2: ({ node, ...props }) => (
        <h2 className="text-2xl font-bold text-[#2B2B2B] mt-16 mb-6" {...props} />
    ),
    h3: ({ node, ...props }) => (
        <h3 className="text-xl font-semibold text-[#2B2B2B] mt-10 mb-4" {...props} />
    ),
    // Párrafos: Interlineado generoso (1.6), texto 18px (lg) para legibilidad.
    p: ({ node, ...props }) => (
        <p className="text-lg text-[#2B2B2B] leading-relaxed mb-6" {...props} />
    ),
    // Listas: Espaciadas y claras.
    ul: ({ node, ...props }) => (
        <ul className="list-disc list-outside ml-6 mb-8 space-y-3 text-lg text-[#2B2B2B]" {...props} />
    ),
    ol: ({ node, ...props }) => (
        <ol className="list-decimal list-outside ml-6 mb-8 space-y-3 text-lg text-[#2B2B2B]" {...props} />
    ),
    li: ({ node, ...props }) => (
        <li className="pl-2" {...props} />
    ),
    // Citas/Notas/Ejemplos: Cajas suaves.
    blockquote: ({ node, ...props }) => (
        <div className="bg-gray-50 border-l-4 border-indigo-400 rounded-r-lg p-6 my-8 shadow-sm">
            <blockquote className="italic text-gray-700 text-lg" {...props} />
        </div>
    ),
    // Tablas: Bordes ligeros.
    table: ({ node, ...props }) => (
        <div className="overflow-x-auto my-8 rounded-lg border border-gray-200 shadow-sm">
            <table className="min-w-full divide-y divide-gray-200" {...props} />
        </div>
    ),
    thead: ({ node, ...props }) => (
        <thead className="bg-gray-50" {...props} />
    ),
    th: ({ node, ...props }) => (
        <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider" {...props} />
    ),
    td: ({ node, ...props }) => (
        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 border-t border-gray-100" {...props} />
    ),
    // Enlaces
    a: ({ node, ...props }) => (
        <a className="text-indigo-600 hover:text-indigo-800 font-medium underline decoration-indigo-300 underline-offset-2 transition-colors" {...props} />
    ),
    // Imágenes
    img: ({ node, ...props }) => (
        <img className="rounded-xl shadow-md border border-gray-100 my-8 mx-auto" {...props} />
    ),
};

function ManualContent() {
    const searchParams = useSearchParams();
    const file = searchParams.get('file') || 'capitulo_1_puc.md';

    const [content, setContent] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchManual = async () => {
            setLoading(true);
            try {
                const res = await fetch(`http://localhost:8000/api/manual/${file}`);
                if (!res.ok) throw new Error(`Error: ${res.statusText}`);
                const data = await res.json();
                setContent(data.content);
            } catch (err) {
                console.error(err);
                setError("No se pudo cargar el manual.");
            } finally {
                setLoading(false);
            }
        };
        if (file) fetchManual();
    }, [file]);

    if (loading) {
        return (
            <div className="min-h-screen bg-white flex flex-col items-center justify-center">
                <span className="loading loading-spinner loading-lg text-indigo-600"></span>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-white flex items-center justify-center p-6">
                <div className="text-center">
                    <p className="text-red-600 text-xl font-medium mb-4">{error}</p>
                    <button onClick={() => window.location.reload()} className="btn btn-outline btn-error">Reintentar</button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#F9FAFB] font-sans text-[#1E1E1E]">
            {/* Header Minimalista */}
            <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-sm border-b border-gray-200 px-8 py-4 flex justify-between items-center shadow-sm">
                <div className="flex items-center gap-3">
                    <div className="bg-indigo-50 p-2 rounded-lg text-indigo-600">
                        <FaBook size={20} />
                    </div>
                    <span className="font-bold text-gray-700 tracking-tight">Manual de Usuario</span>
                </div>
                <div className="flex gap-3">
                    <button onClick={() => window.print()} className="p-2 text-gray-400 hover:text-indigo-600 transition-colors" title="Imprimir">
                        <FaPrint size={18} />
                    </button>
                    <button onClick={() => window.close()} className="p-2 text-gray-400 hover:text-red-600 transition-colors" title="Cerrar">
                        <FaTimes size={18} />
                    </button>
                </div>
            </header>

            {/* Contenedor de Lectura Optimizado */}
            <main className="max-w-4xl mx-auto px-6 py-12 md:py-16">
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-10 md:p-16">
                    <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={MarkdownComponents}
                    >
                        {content}
                    </ReactMarkdown>
                </div>
            </main>

            <footer className="max-w-4xl mx-auto pb-12 text-center text-gray-400 text-sm">
                &copy; {new Date().getFullYear()} ContaPY
            </footer>
        </div>
    );
}

export default function ManualPage() {
    return (
        <Suspense fallback={<div>Cargando...</div>}>
            <ManualContent />
        </Suspense>
    );
}
