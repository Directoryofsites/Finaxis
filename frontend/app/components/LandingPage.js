"use client";

import React from 'react';
import Link from 'next/link';
import {
    FaCalculator, FaChartBar, FaUsers, FaFileInvoiceDollar,
    FaBoxes, FaCog, FaCheckCircle, FaRocket, FaArrowRight,
    FaShieldAlt, FaLightbulb, FaPlug
} from 'react-icons/fa';

/**
 * LandingPage - Página comercial de Finaxis
 */
const LandingPage = () => {
    const [isMenuOpen, setIsMenuOpen] = React.useState(false);

    return (
        <div className="min-h-screen bg-white font-sans text-slate-900">
            {/* 1. NAVBAR (v9: Responsive con Menú Móvil) */}
            <nav className="fixed top-0 w-full z-50 bg-white/90 backdrop-blur-md border-b border-slate-100 h-20 flex items-center px-6 lg:px-12 justify-between">
                <div className="flex items-center gap-2">
                    <span className="text-2xl font-black tracking-tighter text-blue-800">FINAXIS</span>
                </div>

                {/* Desktop Menu */}
                <div className="hidden md:flex items-center gap-10">
                    <a href="#soluciones" className="text-base font-bold text-slate-600 hover:text-blue-600 transition-colors">Soluciones</a>
                    <a href="#planes" className="text-base font-bold text-slate-600 hover:text-blue-600 transition-colors">Planes</a>
                    <a href="#nosotros" className="text-base font-bold text-slate-600 hover:text-blue-600 transition-colors">Nosotros</a>
                    <Link href="/login" className="bg-blue-700 text-white px-8 py-3 rounded-full font-black text-base shadow-lg hover:bg-blue-800 hover:scale-105 transition-all">
                        Acceso Clientes
                    </Link>
                </div>

                {/* Mobile Menu Button */}
                <button
                    className="md:hidden text-2xl text-slate-900 p-2 focus:outline-none"
                    onClick={() => setIsMenuOpen(!isMenuOpen)}
                >
                    {isMenuOpen ? '✕' : '☰'}
                </button>

                {/* Mobile Menu Overlay */}
                {isMenuOpen && (
                    <div className="absolute top-20 left-0 w-full bg-white border-b border-slate-100 p-6 flex flex-col gap-6 md:hidden shadow-xl animate-in slide-in-from-top duration-300">
                        <a href="#soluciones" onClick={() => setIsMenuOpen(false)} className="text-lg font-bold text-slate-600">Soluciones</a>
                        <a href="#planes" onClick={() => setIsMenuOpen(false)} className="text-lg font-bold text-slate-600">Planes</a>
                        <a href="#nosotros" onClick={() => setIsMenuOpen(false)} className="text-lg font-bold text-slate-600">Nosotros</a>
                        <Link href="/login" onClick={() => setIsMenuOpen(false)} className="bg-blue-700 text-white px-6 py-4 rounded-xl font-black text-center text-lg shadow-lg hover:bg-blue-800 transition-all">
                            Acceso Clientes
                        </Link>
                    </div>
                )}
            </nav>

            {/* 2. HERO SECTION (v9: Optimizado para Móvil) */}
            <section className="pt-32 lg:pt-40 pb-20 px-6 lg:px-12 bg-gradient-to-b from-slate-50 to-white overflow-hidden">
                <div className="max-w-7xl mx-auto flex flex-col lg:flex-row items-center gap-12 lg:gap-8">
                    <div className="flex-1 text-center lg:text-left">
                        <span className="inline-block px-6 py-2 bg-blue-100 text-blue-800 rounded-full text-xs sm:text-sm font-black uppercase tracking-widest mb-6 lg:mb-8">
                            Potenciando tu Crecimiento Empresarial
                        </span>
                        <h1 className="text-4xl sm:text-6xl lg:text-8xl font-black leading-tight mb-8 tracking-tighter">
                            Impulsa tu éxito financiero con <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-700 to-cyan-500">Finaxis</span>
                        </h1>
                        <p className="text-xl lg:text-2xl text-slate-600 mb-12 max-w-2xl mx-auto lg:mx-0 leading-relaxed font-medium">
                            La plataforma líder en gestión contable y empresarial diseñada para el crecimiento tecnológico y la automatización inteligente.
                        </p>
                        <div className="flex flex-col sm:flex-row justify-center lg:justify-start gap-6">
                            <button className="bg-blue-700 text-white px-10 py-5 rounded-2xl font-black text-xl shadow-2xl shadow-blue-200 hover:bg-blue-800 transition-all hover:-translate-y-1">
                                Empieza Ahora
                            </button>
                            <button className="bg-white border-4 border-slate-100 px-10 py-5 rounded-2xl font-black text-xl hover:border-blue-600 hover:text-blue-600 transition-all shadow-lg">
                                Ver Demo
                            </button>
                        </div>
                    </div>
                    <div className="flex-1 relative mt-12 lg:mt-0">
                        <div className="absolute -inset-10 bg-gradient-to-tr from-cyan-400 to-blue-600 rounded-3xl blur-3xl opacity-20 animate-pulse"></div>
                        <img
                            src="https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&q=80&w=800"
                            alt="Dashboard Preview"
                            className="relative rounded-3xl shadow-2xl border-8 border-white"
                        />
                    </div>
                </div>
            </section>

            {/* 3. SOLUCIONES (EJES TEMÁTICOS) */}
            <section id="soluciones" className="py-32 px-6 lg:px-12">
                <div className="max-w-7xl mx-auto">
                    <div className="text-center mb-20">
                        <h2 className="text-5xl font-black mb-6 tracking-tight">Soluciones Integrales para tu Empresa</h2>
                        <p className="text-slate-500 text-xl font-medium max-w-3xl mx-auto leading-relaxed">Un ecosistema completo de herramientas diseñadas para optimizar cada proceso de tu negocio con la mayor potencia del mercado.</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10 text-left">
                        {/* Eje 1: Core Contable */}
                        <div className="p-12 rounded-[2.5rem] border-2 border-slate-50 bg-white hover:border-blue-100 hover:shadow-[0_30px_60px_-15px_rgba(30,58,138,0.1)] transition-all group">
                            <div className="w-20 h-20 bg-blue-50 rounded-3xl flex items-center justify-center text-blue-700 text-4xl mb-10 group-hover:bg-blue-700 group-hover:text-white transition-all transform group-hover:rotate-3">
                                <FaCalculator />
                            </div>
                            <h3 className="text-3xl font-black mb-8 leading-tight">Core Contable y Tributario</h3>
                            <ul className="space-y-6 text-slate-600">
                                <li className="flex items-center gap-4 text-xl font-bold">
                                    <FaCheckCircle className="text-cyan-500 shrink-0 text-2xl" /> Contabilidad Automatizada
                                </li>
                                <li className="flex items-center gap-4 text-xl font-bold">
                                    <FaCheckCircle className="text-cyan-500 shrink-0 text-2xl" /> Libros y Estados Financieros
                                </li>
                                <li className="flex items-center gap-4 text-xl font-bold">
                                    <FaCheckCircle className="text-cyan-500 shrink-0 text-2xl" /> Buzón Tributario (IA)
                                </li>
                            </ul>
                        </div>

                        {/* Eje 2: Operación Comercial */}
                        <div className="p-12 rounded-[2.5rem] border-2 border-slate-50 bg-white hover:border-cyan-100 hover:shadow-[0_30px_60px_-15px_rgba(8,145,178,0.1)] transition-all group">
                            <div className="w-20 h-20 bg-cyan-50 rounded-3xl flex items-center justify-center text-cyan-700 text-4xl mb-10 group-hover:bg-cyan-600 group-hover:text-white transition-all transform group-hover:-rotate-3">
                                <FaFileInvoiceDollar />
                            </div>
                            <h3 className="text-3xl font-black mb-8 leading-tight">Operación Comercial</h3>
                            <ul className="space-y-6 text-slate-600">
                                <li className="flex items-center gap-4 text-xl font-bold">
                                    <FaCheckCircle className="text-cyan-500 shrink-0 text-2xl" /> Facturación Electrónica DIAN
                                </li>
                                <li className="flex items-center gap-4 text-xl font-bold">
                                    <FaCheckCircle className="text-cyan-500 shrink-0 text-2xl" /> Control de Inventarios (Kardex)
                                </li>
                                <li className="flex items-center gap-4 text-xl font-bold">
                                    <FaCheckCircle className="text-cyan-500 shrink-0 text-2xl" /> Gestión de Compras y Gastos
                                </li>
                            </ul>
                        </div>

                        {/* Eje 3: Gestión Especializada */}
                        <div className="p-12 rounded-[2.5rem] border-2 border-slate-50 bg-white hover:border-indigo-100 hover:shadow-[0_30px_60px_-15px_rgba(67,56,202,0.1)] transition-all group">
                            <div className="w-20 h-20 bg-indigo-50 rounded-3xl flex items-center justify-center text-indigo-700 text-4xl mb-10 group-hover:bg-indigo-700 group-hover:text-white transition-all transform group-hover:rotate-3">
                                <FaUsers />
                            </div>
                            <h3 className="text-3xl font-black mb-8 leading-tight">Gestión Especializada</h3>
                            <ul className="space-y-6 text-slate-600">
                                <li className="flex items-center gap-4 text-xl font-bold">
                                    <FaCheckCircle className="text-cyan-500 shrink-0 text-2xl" /> Nómina Electrónica
                                </li>
                                <li className="flex items-center gap-4 text-xl font-bold">
                                    <FaCheckCircle className="text-cyan-500 shrink-0 text-2xl" /> Gestión de Recaudos (PH)
                                </li>
                                <li className="flex items-center gap-4 text-xl font-bold">
                                    <FaCheckCircle className="text-cyan-500 shrink-0 text-2xl" /> Producción e Industria
                                </li>
                            </ul>
                        </div>

                        {/* Eje 4: Inteligencia Financiera */}
                        <div className="p-12 rounded-[2.5rem] border-2 border-slate-50 bg-white hover:border-emerald-100 hover:shadow-[0_30px_60px_-15px_rgba(5,150,105,0.1)] transition-all group">
                            <div className="w-20 h-20 bg-emerald-50 rounded-3xl flex items-center justify-center text-emerald-700 text-4xl mb-10 group-hover:bg-emerald-600 group-hover:text-white transition-all transform group-hover:-rotate-3">
                                <FaChartBar />
                            </div>
                            <h3 className="text-3xl font-black mb-8 leading-tight">Inteligencia Financiera</h3>
                            <ul className="space-y-6 text-slate-600">
                                <li className="flex items-center gap-4 text-xl font-bold">
                                    <FaCheckCircle className="text-cyan-500 shrink-0 text-2xl" /> Dashboards Avanzados (ARAF)
                                </li>
                                <li className="flex items-center gap-4 text-xl font-bold">
                                    <FaCheckCircle className="text-cyan-500 shrink-0 text-2xl" /> Centros de Costo Detallados
                                </li>
                                <li className="flex items-center gap-4 text-xl font-bold">
                                    <FaCheckCircle className="text-cyan-500 shrink-0 text-2xl" /> Conciliación Bancaria
                                </li>
                            </ul>
                        </div>

                        {/* Eje 5: Administración y Seguridad */}
                        <div className="p-12 rounded-[2.5rem] border-2 border-slate-50 bg-white hover:border-slate-300 hover:shadow-2xl transition-all group">
                            <div className="w-20 h-20 bg-slate-100 rounded-3xl flex items-center justify-center text-slate-700 text-4xl mb-10 group-hover:bg-slate-800 group-hover:text-white transition-all transform group-hover:scale-110">
                                <FaCog />
                            </div>
                            <h3 className="text-3xl font-black mb-8 leading-tight">Seguridad y Administración</h3>
                            <ul className="space-y-6 text-slate-600">
                                <li className="flex items-center gap-4 text-xl font-bold">
                                    <FaCheckCircle className="text-cyan-500 shrink-0 text-2xl" /> Auditoría y Control de Log
                                </li>
                                <li className="flex items-center gap-4 text-xl font-bold">
                                    <FaCheckCircle className="text-cyan-500 shrink-0 text-2xl" /> Permisos Granulares
                                </li>
                                <li className="flex items-center gap-4 text-xl font-bold">
                                    <FaCheckCircle className="text-cyan-500 shrink-0 text-2xl" /> Backups en la Nube
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </section>

            {/* 4. PLANES DE PRECIOS */}
            <section id="planes" className="py-32 px-6 lg:px-12 bg-slate-50">
                <div className="max-w-7xl mx-auto">
                    <div className="text-center mb-24">
                        <h2 className="text-5xl font-black mb-6 tracking-tight">Planes diseñados para crecer</h2>
                        <p className="text-slate-500 text-xl font-medium max-w-3xl mx-auto">Elige la solución que mejor se adapte a tu etapa empresarial.</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
                        {/* Plan Emprendedor */}
                        <div className="bg-white p-12 rounded-[3rem] border-2 border-slate-100 flex flex-col h-full hover:border-blue-300 transition-all shadow-xl">
                            <h3 className="text-3xl font-black mb-2">Emprendedor</h3>
                            <p className="text-slate-400 font-bold text-lg mb-8 italic">Ideal para independientes</p>
                            <div className="mb-10 items-baseline flex">
                                <span className="text-5xl font-black text-slate-900">$99.000</span>
                                <span className="text-slate-400 text-xl font-bold ml-2">/ mes</span>
                            </div>
                            <ul className="space-y-5 mb-12 flex-1">
                                <li className="flex items-center gap-4 text-lg text-slate-600 font-bold">
                                    <FaCheckCircle className="text-cyan-500 shrink-0 text-xl" /> Facturación Electrónica
                                </li>
                                <li className="flex items-center gap-4 text-lg text-slate-600 font-bold">
                                    <FaCheckCircle className="text-cyan-500 shrink-0 text-xl" /> Contabilidad Básica
                                </li>
                                <li className="flex items-center gap-4 text-lg text-slate-600 font-bold">
                                    <FaCheckCircle className="text-cyan-500 shrink-0 text-xl" /> 1 Usuario
                                </li>
                            </ul>
                            <button className="w-full py-5 rounded-2xl border-4 border-slate-50 font-black text-lg hover:bg-slate-50 transition-colors">Elegir Emprendedor</button>
                        </div>

                        {/* Plan Pyme */}
                        <div className="bg-white p-12 rounded-[3rem] border-4 border-blue-600 shadow-[0_40px_80px_-15px_rgba(30,58,138,0.2)] flex flex-col h-full relative transform scale-105 z-10">
                            <div className="absolute top-0 right-12 -translate-y-1/2 bg-blue-600 text-white px-6 py-2 rounded-full text-sm font-black uppercase tracking-widest shadow-xl">Recomendado</div>
                            <h3 className="text-3xl font-black mb-2">Pyme</h3>
                            <p className="text-slate-400 font-bold text-lg mb-8 italic">Para empresas en expansión</p>
                            <div className="mb-10 items-baseline flex">
                                <span className="text-5xl font-black text-slate-900">$189.000</span>
                                <span className="text-slate-400 text-xl font-bold ml-2">/ mes</span>
                            </div>
                            <ul className="space-y-5 mb-12 flex-1">
                                <li className="flex items-center gap-4 text-lg text-slate-600 font-bold">
                                    <FaCheckCircle className="text-cyan-500 shrink-0 text-xl" /> Facturación Ilimitada
                                </li>
                                <li className="flex items-center gap-4 text-lg text-slate-600 font-bold">
                                    <FaCheckCircle className="text-cyan-500 shrink-0 text-xl" /> Inventarios y Compras
                                </li>
                                <li className="flex items-center gap-4 text-lg text-slate-600 font-bold">
                                    <FaCheckCircle className="text-cyan-500 shrink-0 text-xl" /> Nómina Electrónica
                                </li>
                                <li className="flex items-center gap-4 text-lg text-slate-600 font-bold">
                                    <FaCheckCircle className="text-cyan-500 shrink-0 text-xl" /> 5 Usuarios
                                </li>
                            </ul>
                            <button className="w-full py-5 rounded-2xl bg-blue-700 text-white font-black text-lg hover:bg-blue-800 transition-all shadow-xl hover:scale-[1.02]">Elegir Pyme</button>
                        </div>

                        {/* Plan Corporativo */}
                        <div className="bg-white p-12 rounded-[3rem] border-2 border-slate-100 flex flex-col h-full hover:border-blue-300 transition-all shadow-xl">
                            <h3 className="text-3xl font-black mb-2">Corporativo</h3>
                            <p className="text-slate-400 font-bold text-lg mb-8 italic">Control total sin límites</p>
                            <div className="mb-10 items-baseline flex">
                                <span className="text-5xl font-black text-slate-900">$299.000</span>
                                <span className="text-slate-400 text-xl font-bold ml-2">/ mes</span>
                            </div>
                            <ul className="space-y-5 mb-12 flex-1">
                                <li className="flex items-center gap-4 text-lg text-slate-600 font-bold">
                                    <FaCheckCircle className="text-cyan-500 shrink-0 text-xl" /> Todo lo de Pyme
                                </li>
                                <li className="flex items-center gap-4 text-lg text-slate-600 font-bold">
                                    <FaCheckCircle className="text-cyan-500 shrink-0 text-xl" /> Producción e Industria
                                </li>
                                <li className="flex items-center gap-4 text-lg text-slate-600 font-bold">
                                    <FaCheckCircle className="text-cyan-500 shrink-0 text-xl" /> Inteligencia Avanzada
                                </li>
                            </ul>
                            <button className="w-full py-5 rounded-2xl border-4 border-slate-50 font-black text-lg hover:bg-slate-50 transition-colors">Contactar Ventas</button>
                        </div>
                    </div>
                </div>
            </section>

            {/* 5. FOOTER (REDESIGN: LIGHT MODE FOR BRAND COHERENCE) */}
            <footer className="bg-slate-50 py-24 px-6 lg:px-12 border-t border-slate-200">
                <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-20">
                    <div className="lg:col-span-5">
                        {/* Logo Footer v6 - Usando multiply para eliminar el recuadro blanco sobre el fondo slate-50 */}
                        <img
                            src="/logo.png"
                            alt="Finaxis Logo"
                            className="h-48 w-auto mb-10 object-contain mix-blend-multiply"
                        />
                        <p className="text-slate-600 text-xl leading-relaxed font-medium mb-12">
                            Empoderamos el crecimiento de las empresas latinas a través de tecnología de vanguardia y automatización de procesos financieros inteligentes.
                        </p>
                        <div className="flex gap-6">
                            <div className="w-12 h-12 bg-white rounded-full shadow-md flex items-center justify-center text-blue-600 hover:bg-blue-600 hover:text-white transition-all cursor-pointer"><FaRocket /></div>
                            <div className="w-12 h-12 bg-white rounded-full shadow-md flex items-center justify-center text-blue-600 hover:bg-blue-600 hover:text-white transition-all cursor-pointer"><FaShieldAlt /></div>
                            <div className="w-12 h-12 bg-white rounded-full shadow-md flex items-center justify-center text-blue-600 hover:bg-blue-600 hover:text-white transition-all cursor-pointer"><FaLightbulb /></div>
                        </div>
                    </div>

                    <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-3 gap-12">
                        <div>
                            <h4 className="font-black text-lg uppercase tracking-widest text-slate-900 mb-8 border-l-4 border-blue-600 pl-4 uppercase">Producto</h4>
                            <ul className="space-y-6 text-slate-500 text-lg font-bold">
                                <li><a href="#" className="hover:text-blue-600 transition-colors">Características</a></li>
                                <li><a href="#" className="hover:text-blue-600 transition-colors">Módulos ERP</a></li>
                                <li><a href="#" className="hover:text-blue-600 transition-colors">Seguridad</a></li>
                            </ul>
                        </div>
                        <div>
                            <h4 className="font-black text-lg uppercase tracking-widest text-slate-900 mb-8 border-l-4 border-blue-600 pl-4 uppercase">Compañía</h4>
                            <ul className="space-y-6 text-slate-500 text-lg font-bold">
                                <li><a href="#" className="hover:text-blue-600 transition-colors">Sobre Nosotros</a></li>
                                <li><a href="#" className="hover:text-blue-600 transition-colors">Clientes</a></li>
                                <li><a href="#" className="hover:text-blue-600 transition-colors">Contacto</a></li>
                            </ul>
                        </div>
                        <div>
                            <h4 className="font-black text-lg uppercase tracking-widest text-slate-900 mb-8 border-l-4 border-blue-600 pl-4 uppercase">Plataforma</h4>
                            <Link href="/login" className="inline-flex items-center gap-3 bg-blue-700 text-white px-6 py-4 rounded-2xl font-black text-base shadow-lg hover:bg-blue-800 transition-all">
                                <FaPlug className="text-xl" /> Acceder <FaArrowRight />
                            </Link>
                        </div>
                    </div>
                </div>

                <div className="max-w-7xl mx-auto mt-24 pt-12 border-t border-slate-200 flex flex-col sm:flex-row justify-between items-center gap-10">
                    <p className="text-slate-400 text-base font-black tracking-tight">© 2026 FINAXIS.  INNOVACIÓN CONTABLE.</p>
                    <div className="flex gap-12 text-base text-slate-500 font-black">
                        <a href="#" className="hover:text-blue-600 transition-colors">PRIVACIDAD</a>
                        <a href="#" className="hover:text-blue-600 transition-colors">TÉRMINOS</a>
                        <a href="#" className="hover:text-blue-600 transition-colors">COOKIES</a>
                    </div>
                </div>
            </footer>
        </div>
    );
};

export default LandingPage;
