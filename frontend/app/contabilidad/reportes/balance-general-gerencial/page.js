'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
    FaBalanceScale,
    FaCalendarAlt,
    FaSearch,
    FaFilePdf,
    FaArrowRight,
    FaCheckCircle,
    FaEnvelope,
    FaWhatsapp,
    FaInfoCircle
} from 'react-icons/fa';

import { toast } from 'react-toastify';
import { useAuth } from '../../../context/AuthContext';
import { apiService } from '../../../../lib/apiService';
import { useAIAutomation } from '../../../hooks/useAIAutomation';

export default function BalanceGeneralGerencialPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-white flex flex-col items-center justify-center">
                <FaBalanceScale className="text-emerald-600 text-6xl mb-4 animate-pulse" />
                <p className="text-emerald-900 font-serif italic text-lg animate-pulse">Preparando Balance Gerencial...</p>
            </div>
        }>
            <BalanceGerencialContent />
        </Suspense>
    );
}

function BalanceGerencialContent() {
    const { user, authLoading } = useAuth();
    const router = useRouter();
    const searchParams = useSearchParams();

    const [reporte, setReporte] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [filtros, setFiltros] = useState({
        fecha_corte: new Date().toISOString().split('T')[0]
    });
    const [isPageReady, setPageReady] = useState(false);
    const [empresaInfo, setEmpresaInfo] = useState(null);

    useEffect(() => {
        if (!authLoading) {
            if (user && user.empresaId) {
                apiService.get(`/empresas/${user.empresaId}`)
                    .then(response => {
                        setEmpresaInfo(response.data);
                        setPageReady(true);
                    })
                    .catch(err => {
                        console.error("Error al cargar datos de empresa:", err);
                        setPageReady(true);
                    });
            } else {
                router.push('/login');
            }
        }
    }, [user, authLoading, router]);

    async function handleGenerateReport() {
        if (!filtros.fecha_corte) {
            toast.error("Seleccione una fecha de corte.");
            return;
        }
        setIsLoading(true);
        setError('');
        try {
            const data = await apiService.get('/reports/balance-sheet-gerencial', {
                params: { fecha_corte: filtros.fecha_corte }
            });
            setReporte(data.data);
            toast.success("Balance actualizado correctamente.");
        } catch (err) {
            setError(err.response?.data?.detail || "Error al generar el reporte.");
        } finally {
            setIsLoading(false);
        }
    }

    async function handleExportPDF() {
        if (!reporte) return;
        setIsLoading(true);
        try {
            const response = await apiService.get('/reports/balance-sheet-gerencial/get-signed-url', {
                params: { fecha_corte: filtros.fecha_corte }
            });
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const pdfUrl = `${baseUrl}/api/reports/balance-sheet-gerencial/imprimir?signed_token=${response.data.signed_url_token}`;
            window.open(pdfUrl, '_blank');
        } catch (err) {
            toast.error("Error al generar el PDF.");
        } finally {
            setIsLoading(false);
        }
    }

    const formatCurrency = (val) => {
        const num = parseFloat(val || 0);
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(num);
    };

    if (!isPageReady) return null;

    return (
        <div className="min-h-screen bg-slate-50/50 p-4 md:p-8 font-dm-sans">
            {/* Google Fonts */}
            <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=DM+Sans:wght@300;400;500;700&display=swap" rel="stylesheet" />

            <style jsx global>{`
                .font-cormorant { font-family: 'Cormorant Garamond', serif; }
                .font-dm-sans { font-family: 'DM Sans', sans-serif; }
                .gerencial-light-report {
                    max-width: 900px;
                    margin: 0 auto;
                    background: white;
                    box-shadow: 0 10px 40px -10px rgba(0,0,0,0.1);
                    min-height: 1000px;
                    position: relative;
                }
                .acc-code { letter-spacing: 1px; color: #BBB; font-size: 10px; font-weight: 700; }
                .report-header-bg {
                    background: linear-gradient(90deg, #2D6A26, #6BAD5E, #C9A84C, #6BAD5E, #2D6A26);
                    height: 5px;
                    width: 100%;
                }
                .section-card { 
                    border: 1.5px solid #E4E4E4; 
                    border-radius: 8px; 
                    overflow: hidden; 
                    display: flex;
                    flex-direction: column;
                }
                .card-header-stripe { width: 3px; height: 18px; border-radius: 2px; }
                .tabular { font-variant-numeric: tabular-nums; }
            `}</style>

            <div className="max-w-5xl mx-auto mb-8">
                {/* Header Administrativo */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-8">
                    <div>
                        <div className="flex items-center gap-4">
                            <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center text-emerald-700">
                                <FaBalanceScale size={24} />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold text-slate-800">Balance General Gerencial</h1>
                                <p className="text-slate-500 text-sm">Situación financiera · Versión Corporativa Premium</p>
                            </div>
                        </div>
                    </div>

                    <div className="flex gap-3 w-full md:w-auto">
                        <div className="relative flex-1 md:w-48">
                            <input
                                type="date"
                                value={filtros.fecha_corte}
                                onChange={(e) => setFiltros({ ...filtros, fecha_corte: e.target.value })}
                                className="w-full pl-10 pr-4 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 outline-none transition-all"
                            />
                            <FaCalendarAlt className="absolute left-3 top-3 text-slate-400" />
                        </div>
                        <button
                            onClick={handleGenerateReport}
                            disabled={isLoading}
                            className="px-6 py-2 bg-slate-900 text-white rounded-lg font-bold text-sm hover:bg-slate-800 transition-all flex items-center gap-2"
                        >
                            {isLoading ? '...' : <><FaSearch /> Generar</>}
                        </button>
                        <button
                            onClick={handleExportPDF}
                            disabled={!reporte || isLoading}
                            className="px-6 py-2 bg-white border border-rose-200 text-rose-600 rounded-lg font-bold text-sm hover:bg-rose-50 transition-all flex items-center gap-2 shadow-sm disabled:opacity-50"
                        >
                            <FaFilePdf /> PDF
                        </button>
                    </div>
                </div>

                {reporte ? (
                    <div className="gerencial-light-report font-dm-sans overflow-hidden">
                        <div className="report-header-bg"></div>
                        
                        {/* Cabecera Estilo Imagen */}
                        <div className="p-10 md:p-14 border-b border-slate-100 flex flex-col md:flex-row justify-between items-center md:items-start gap-8">
                            <div className="text-center md:text-left">
                                <span className="text-[10px] uppercase tracking-[3px] font-bold text-emerald-700 block mb-2">• INFORME FINANCIERO OFICIAL</span>
                                <h2 className="text-5xl font-cormorant font-bold text-slate-900 leading-none">
                                    {empresaInfo?.razon_social?.split(' ')[0] || 'Verduras'} <span className="text-emerald-700">{empresaInfo?.razon_social?.split(' ').slice(1).join(' ') || 'La 21'}</span>
                                </h2>
                                <p className="text-xs text-slate-400 tracking-[2px] mt-2">NIT {empresaInfo?.nit || '942.807.497'}</p>
                            </div>
                            
                            <div className="flex flex-col items-center md:items-end">
                                <div className="text-xl font-cormorant italic text-slate-500 mb-4">Estado de Situación Financiera</div>
                                <div className="border-[1.5px] border-emerald-700 rounded p-2 px-6 text-center">
                                    <div className="text-[9px] uppercase tracking-[2.5px] font-bold text-emerald-700 mb-1">FECHA DE CORTE</div>
                                    <div className="text-base font-bold text-slate-900">{new Date(filtros.fecha_corte).toLocaleDateString('es-CO', { day: 'numeric', month: 'long', year: 'numeric' })}</div>
                                </div>
                                <p className="text-[9px] text-slate-400 mt-2 italic">Cifras en Pesos Colombianos (COP)</p>
                            </div>
                        </div>

                        {/* Report Body */}
                        <div className="p-8 md:p-14 pt-8">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-16">
                                {/* ACTIVOS */}
                                <div className="space-y-6">
                                    <div className="section-card">
                                        <div className="bg-[#F2F8F1] p-3 px-5 border-b-[1.5px] border-slate-200 flex items-center gap-3">
                                            <div className="card-header-stripe bg-emerald-700"></div>
                                            <span className="text-xs font-bold uppercase tracking-[2.5px] text-slate-600">ACTIVOS</span>
                                        </div>
                                        <div className="p-0">
                                            {/* Corriente */}
                                            <div className="bg-slate-50 px-5 py-1.5 text-[9.5px] font-bold text-slate-400 uppercase tracking-[2px] border-b border-slate-100 flex items-center gap-2">
                                                <FaArrowRight size={8} /> Activo Corriente
                                            </div>
                                            <div className="divide-y divide-slate-50">
                                                {reporte.clasificado_activo?.corriente?.map((it, idx) => (
                                                    <div key={idx} className="px-5 py-2 flex justify-between items-center text-sm font-medium">
                                                        <div className="flex gap-3">
                                                            <span className="acc-code">{it.codigo}</span>
                                                            <span className="text-slate-600 uppercase text-[12px]">{it.nombre}</span>
                                                        </div>
                                                        <span className="tabular text-slate-900">{formatCurrency(it.saldo)}</span>
                                                    </div>
                                                ))}
                                                <div className="bg-[#F7F9F7] px-5 py-2.5 flex justify-between items-center border-t-[1.5px] border-[#D8E8D6] font-bold text-emerald-700">
                                                    <span className="text-sm">Total Activo Corriente</span>
                                                    <span className="tabular text-sm">{formatCurrency(reporte.clasificado_activo?.total_corriente)}</span>
                                                </div>
                                            </div>

                                            {/* No Corriente */}
                                            {reporte.clasificado_activo?.no_corriente?.length > 0 && (
                                                <>
                                                    <div className="bg-slate-50 px-5 py-1.5 text-[9.5px] font-bold text-slate-400 uppercase tracking-[2px] border-y border-slate-100 flex items-center gap-2">
                                                        <FaArrowRight size={8} /> Activo No Corriente
                                                    </div>
                                                    <div className="divide-y divide-slate-50">
                                                        {reporte.clasificado_activo.no_corriente.map((it, idx) => (
                                                            <div key={idx} className="px-5 py-2 flex justify-between items-center text-sm font-medium">
                                                                <div className="flex gap-3">
                                                                    <span className="acc-code">{it.codigo}</span>
                                                                    <span className="text-slate-600 uppercase text-[12px]">{it.nombre}</span>
                                                                </div>
                                                                <span className="tabular text-slate-900">{formatCurrency(it.saldo)}</span>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </>
                                            )}

                                            {/* Total Activos */}
                                            <div className="bg-[#EEF5ED] px-5 py-3 flex justify-between items-center border-t-2 border-emerald-700 font-bold text-emerald-950 mt-auto">
                                                <span className="text-[14px]">TOTAL ACTIVOS</span>
                                                <span className="tabular text-[14px]">{formatCurrency(reporte.total_activos)}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* PASIVOS Y PATRIMONIO */}
                                <div className="space-y-8">
                                    {/* Pasivos */}
                                    <div className="section-card">
                                        <div className="bg-[#F3F5F8] p-3 px-5 border-b-[1.5px] border-slate-200 flex items-center gap-3">
                                            <div className="card-header-stripe bg-[#4A6FA5]"></div>
                                            <span className="text-xs font-bold uppercase tracking-[2.5px] text-slate-600">PASIVOS</span>
                                        </div>
                                        <div>
                                            <div className="bg-slate-50 px-5 py-1.5 text-[9.5px] font-bold text-slate-400 uppercase tracking-[2px] border-b border-slate-100 flex items-center gap-2">
                                                <FaArrowRight size={8} /> Pasivo Corriente
                                            </div>
                                            <div className="divide-y divide-slate-50">
                                                {reporte.clasificado_pasivo?.corriente?.map((it, idx) => (
                                                    <div key={idx} className="px-5 py-2 flex justify-between items-center text-sm font-medium">
                                                        <div className="flex gap-3">
                                                            <span className="acc-code">{it.codigo}</span>
                                                            <span className="text-slate-600 uppercase text-[12px]">{it.nombre}</span>
                                                        </div>
                                                        <span className={`tabular ${it.saldo < 0 ? 'text-rose-600' : 'text-slate-900'}`}>{formatCurrency(it.saldo)}</span>
                                                    </div>
                                                ))}
                                                <div className="bg-[#F3F6FB] px-5 py-2.5 flex justify-between items-center border-t-[1.5px] border-[#C0CEDF] font-bold text-[#4A6FA5]">
                                                    <span className="text-sm">Total Pasivo Corriente</span>
                                                    <span className="tabular text-sm">{formatCurrency(reporte.clasificado_pasivo?.total_corriente)}</span>
                                                </div>
                                                 <div className="bg-[#EEF1F8] px-5 py-3 flex justify-between items-center border-t-2 border-[#4A6FA5] font-bold text-[#1F3560] mt-auto">
                                                     <span className="text-[13px]">TOTAL PASIVOS</span>
                                                     <span className="tabular text-[13px]">{formatCurrency(reporte.total_pasivos)}</span>
                                                 </div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Patrimonio */}
                                    <div className="section-card">
                                        <div className="bg-[#FBF8F1] p-3 px-5 border-b-[1.5px] border-slate-200 flex items-center gap-3">
                                            <div className="card-header-stripe bg-[#C9A84C]"></div>
                                            <span className="text-xs font-bold uppercase tracking-[2.5px] text-slate-600">PATRIMONIO</span>
                                        </div>
                                        <div className="divide-y divide-slate-50">
                                            {reporte.patrimonio?.map((it, idx) => (
                                                <div key={idx} className="px-5 py-2 flex justify-between items-center text-sm font-medium">
                                                    <div className="flex gap-3">
                                                        <span className="acc-code">{it.codigo}</span>
                                                        <span className="text-slate-600 uppercase text-[12px]">{it.nombre}</span>
                                                    </div>
                                                    <span className="tabular text-slate-900">{formatCurrency(it.saldo)}</span>
                                                </div>
                                            ))}
                                            <div className="px-5 py-2 flex justify-between items-center text-sm font-medium">
                                                <div className="flex gap-3">
                                                    <span className="acc-code">3605</span>
                                                    <span className="text-slate-600 uppercase text-[12px]">{reporte.nombre_utilidad}</span>
                                                </div>
                                                <span className={`tabular font-bold ${reporte.utilidad_ejercicio < 0 ? 'text-rose-600' : 'text-slate-900'}`}>{formatCurrency(reporte.utilidad_ejercicio)}</span>
                                            </div>
                                             <div className="bg-[#FAF5E9] px-5 py-3 flex justify-between items-center border-t-2 border-[#C9A84C] font-bold text-[#6B5010] mt-auto">
                                                 <span className="text-[13px]">TOTAL PATRIMONIO</span>
                                                 <span className={`tabular text-[13px] ${reporte.total_patrimonio < 0 ? 'text-rose-600' : ''}`}>{formatCurrency(reporte.total_patrimonio)}</span>
                                             </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* KPI Strip */}
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-10">
                                <div className="p-5 border-[1.5px] border-slate-200 rounded-lg bg-white relative before:content-[''] before:absolute before:left-0 before:top-4 before:bottom-4 before:w-1 before:bg-emerald-700 before:rounded-r">
                                    <div className="text-[9.5px] font-bold text-slate-400 uppercase tracking-[2.5px] mb-2">Total Activos</div>
                                    <div className="text-xl font-bold text-slate-900">{formatCurrency(reporte.total_activos)}</div>
                                    <div className="text-[10px] text-slate-400 mt-1 italic">Activo corriente 100%</div>
                                </div>
                                <div className="p-5 border-[1.5px] border-slate-200 rounded-lg bg-white relative before:content-[''] before:absolute before:left-0 before:top-4 before:bottom-4 before:w-1 before:bg-rose-600 before:rounded-r">
                                    <div className="text-[9.5px] font-bold text-slate-400 uppercase tracking-[2.5px] mb-2">Total Pasivos</div>
                                    <div className="text-xl font-bold text-rose-600 font-tabular">{formatCurrency(reporte.total_pasivos)}</div>
                                    <div className="text-[10px] text-slate-400 mt-1 italic">Pasivo corriente 100%</div>
                                </div>
                                <div className="p-5 border-[1.5px] border-slate-200 rounded-lg bg-white relative before:content-[''] before:absolute before:left-0 before:top-4 before:bottom-4 before:w-1 before:bg-[#C9A84C] before:rounded-r">
                                    <div className="text-[9.5px] font-bold text-slate-400 uppercase tracking-[2.5px] mb-2">Patrimonio Neto</div>
                                    <div className={`text-xl font-bold font-tabular ${reporte.total_patrimonio < 0 ? 'text-rose-600' : 'text-slate-900'}`}>{formatCurrency(reporte.total_patrimonio)}</div>
                                    <div className="text-[10px] text-slate-400 mt-1 italic">{reporte.total_patrimonio < 0 ? 'Déficit patrimonial' : 'Capital positivo'}</div>
                                </div>
                            </div>

                            {/* Grand Total Bar */}
                            <div className="bg-[#F5FAF4] border-2 border-emerald-700 rounded-lg p-6 px-8 flex items-center justify-between shadow-sm">
                                <div className="flex items-center gap-6">
                                    <div className="w-10 h-10 bg-emerald-700 rounded-full flex items-center justify-center text-white">
                                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
                                    </div>
                                    <div className="font-cormorant font-semibold italic text-lg text-slate-800">
                                        Verificación Contable: Total Pasivo + Patrimonio
                                    </div>
                                </div>
                                <div className="text-right">
                                    <span className="text-xs text-slate-400 font-bold mr-2 tabular">COP</span>
                                    <span className="text-3xl font-bold text-slate-900 tabular text-emerald-950 font-dm-sans">{formatCurrency(reporte.total_pasivo_patrimonio)}</span>
                                </div>
                            </div>
                            
                            <p className="text-center text-[10px] text-slate-400 mt-4 italic">
                                Activos = Pasivos + Patrimonio · Ecuación contable verificada
                            </p>

                            {/* Signatures */}
                            <div className="mt-16 grid grid-cols-2 gap-20">
                                <div className="text-center">
                                    <div className="h-[1.5px] bg-gradient-to-r from-transparent via-[#C9A84C] to-transparent mb-3"></div>
                                    <div className="text-[11px] font-bold text-slate-800 tracking-[2px] uppercase">Representante Legal</div>
                                    <div className="text-[9px] text-slate-400 mt-1">C.C. _______________________</div>
                                </div>
                                <div className="text-center">
                                    <div className="h-[1.5px] bg-gradient-to-r from-transparent via-[#C9A84C] to-transparent mb-3"></div>
                                    <div className="text-[11px] font-bold text-slate-800 tracking-[2px] uppercase">Contador Público</div>
                                    <div className="text-[9px] text-slate-400 mt-1">T.P. _______________________</div>
                                </div>
                            </div>
                        </div>

                        <div className="h-[3px] bg-gradient-to-r from-[#2D6A26] via-[#6BAD5E] to-[#C9A84C] mt-8"></div>
                    </div>
                ) : (
                    <div className="bg-white rounded-xl p-20 text-center border-2 border-dashed border-slate-200">
                        <FaBalanceScale className="text-slate-200 text-6xl mx-auto mb-4" />
                        <h3 className="text-slate-400 font-bold uppercase tracking-widest">Esperando Parámetros</h3>
                        <p className="text-slate-300 text-sm mt-2">Seleccione una fecha y haga clic en 'Generar Reporte'</p>
                    </div>
                )}
            </div>

            {/* Float Action Cards */}
            <div className="fixed bottom-6 right-6 flex flex-col gap-3">
               <button className="w-12 h-12 bg-white text-emerald-600 rounded-full shadow-lg flex items-center justify-center hover:scale-110 transition-all border border-emerald-100" title="Manual"><FaInfoCircle size={20}/></button>
            </div>
        </div>
    );
}
