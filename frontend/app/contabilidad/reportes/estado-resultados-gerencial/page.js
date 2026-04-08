'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Head from 'next/head';
import {
    FaSearch,
    FaFilePdf,
} from 'react-icons/fa';

import { toast } from 'react-toastify';
import { useAuth } from '../../../context/AuthContext';
import { apiService } from '../../../../lib/apiService';

const labelClass = "block text-[10px] font-bold text-slate-400 uppercase mb-1.5 tracking-widest";
const inputClass = "w-full px-4 py-2 bg-white border border-slate-200 rounded-xl shadow-sm focus:ring-2 focus:ring-slate-500 focus:border-slate-500 text-sm transition-all outline-none hover:border-slate-300";

export default function EstadoResultadosGerencialPage() {
    const { user, loading: authLoading } = useAuth();
    const router = useRouter();

    const [reporte, setReporte] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [fechaInicio, setFechaInicio] = useState(new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0]);
    const [fechaFin, setFechaFin] = useState(new Date().toISOString().split('T')[0]);
    const [isPageReady, setPageReady] = useState(false);

    useEffect(() => {
        if (!authLoading) {
            if (user && user.empresaId) {
                setPageReady(true);
            } else {
                router.push('/login');
            }
        }
    }, [user, authLoading, router]);

    const handleGenerateReport = async () => {
        if (!fechaInicio || !fechaFin) {
            toast.error("Por favor, seleccione una fecha de inicio y una fecha de fin.");
            return;
        }
        setIsLoading(true);
        setReporte(null);

        const params = {
            fecha_inicio: fechaInicio,
            fecha_fin: fechaFin,
        };

        try {
            const res = await apiService.get('/reports/income-statement-gerencial', { params: params });
            setReporte(res.data);
            toast.success("Reporte gerencial cargado exitosamente");
        } catch (err) {
            console.error(err);
            toast.error("Error al cargar el reporte");
        } finally {
            setIsLoading(false);
        }
    };

    const handleExportPDF = async () => {
        if (!fechaInicio || !fechaFin) return;
        toast.info("Generando PDF Gerencial...", { autoClose: 2000 });
        
        try {
            const response = await apiService.get('/reports/income-statement-gerencial/get-signed-url', {
                params: { fecha_inicio: fechaInicio, fecha_fin: fechaFin }
            });

            if (response.data && response.data.signed_url_token) {
                const token = response.data.signed_url_token;
                const pdfUrl = `${apiService.defaults.baseURL}/reports/income-statement-gerencial/imprimir?signed_token=${token}`;
                window.open(pdfUrl, '_blank');
            } else {
                toast.error("No se pudo obtener el enlace seguro para el PDF.");
            }
        } catch (error) {
            console.error("Error al exportar PDF:", error);
            const msg = error.response?.data?.detail || "Error al generar el PDF.";
            toast.error(msg);
        }
    };

    if (!isPageReady) {
        return <div className="p-8 text-center text-slate-500 animate-pulse">Cargando módulo gerencial...</div>;
    }

    return (
        <div className="bg-slate-50 min-h-screen pb-20 font-sans">
            {/* INJECT EDITED CSS STYLES DIRECTLY IN THE COMPONENT OR VIA A STYLE TAG SO IT MATCHES */}
            <style jsx global>{`
                .gerencial-theme {
                    /* Paleta: Verdes, Azules, Dorados (Sincronizado) */
                    --green-inst:   #2D6A26;
                    --green-light:  #6BAD5E;
                    --blue-slate:   #4A6FA5;
                    --gold-soft:    #C9A84C;
                    
                    /* Fondos y Texto */
                    --white:        #ffffff;
                    --bg-page:      #FAFAF7;
                    --text-main:    #1a1a1a;
                    --text-muted:   #888888;
                    --text-labels:  #444444;
                    --red-contable: #c0392b;
                    
                    /* Sombras y Bordes */
                    --shadow:       0 10px 40px -10px rgba(45, 106, 38, 0.12);
                    --border:       1px solid rgba(0,0,0,0.08);
                }

                .gerencial-theme .page-report {
                    max-width: 900px;
                    margin: 0 auto;
                    padding: 80px 60px;
                    background: var(--white);
                    box-shadow: var(--shadow);
                    color: var(--text-main);
                    border-radius: 4px;
                    position: relative;
                }

                .gerencial-theme .page-report::before {
                    content: '';
                    position: absolute;
                    top: 0; left: 0; right: 0;
                    height: 4px;
                    background: linear-gradient(90deg, var(--green-inst), var(--green-light), var(--gold-soft), var(--green-light), var(--green-inst));
                }

                /* ─── HEADER ─── */
                .gerencial-theme .header-report {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 50px;
                    padding-bottom: 30px;
                    border-bottom: 1px solid #f0f0f0;
                }
                .gerencial-theme .org-info {
                    text-align: left;
                }
                .gerencial-theme .org-name {
                    font-family: 'Cormorant Garamond', serif;
                    font-size: 38px;
                    font-weight: 700;
                    line-height: 1;
                    color: var(--text-main);
                }
                .gerencial-theme .org-name span { color: var(--green-inst); }
                .gerencial-theme .org-meta {
                    font-size: 11px;
                    color: var(--text-muted);
                    letter-spacing: 1.5px;
                    margin-top: 4px;
                    text-transform: uppercase;
                }
                .gerencial-theme .doc-info {
                    text-align: right;
                }
                .gerencial-theme .doc-title {
                    font-family: 'Cormorant Garamond', serif;
                    font-size: 18px;
                    font-style: italic;
                    color: #555555;
                    margin-bottom: 8px;
                }
                .gerencial-theme .doc-period {
                    display: inline-block;
                    border: 1.5px solid var(--green-inst);
                    border-radius: 4px;
                    padding: 6px 14px;
                    font-size: 14px;
                    font-weight: 700;
                    color: var(--text-main);
                }

                /* ─── KPI STRIP ─── */
                .gerencial-theme .kpi-strip {
                    display: flex;
                    gap: 20px;
                    margin-bottom: 40px;
                }
                .gerencial-theme .kpi-cell {
                    flex: 1;
                    background: var(--white);
                    padding: 20px;
                    border: 1.5px solid #e4e4e4;
                    border-radius: 8px;
                    position: relative;
                }
                .gerencial-theme .kpi-cell::before {
                    content: "";
                    position: absolute;
                    left: 0; top: 15%; bottom: 15%;
                    width: 4px;
                    border-radius: 0 2px 2px 0;
                }
                .gerencial-theme .kpi-cell.ing::before { background: var(--green-inst); }
                .gerencial-theme .kpi-cell.exp::before { background: var(--red-contable); }
                .gerencial-theme .kpi-cell.res::before { background: var(--gold-soft); }

                .gerencial-theme .kpi-label {
                    font-size: 9px;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 2px;
                    color: var(--text-muted);
                    margin-bottom: 5px;
                }
                .gerencial-theme .kpi-value {
                    font-size: 18px;
                    font-weight: 700;
                    color: var(--text-main);
                }
                .gerencial-theme .kpi-value.green { color: var(--green-inst); }
                .gerencial-theme .kpi-value.red   { color: var(--red-contable); }
                .gerencial-theme .kpi-value.gold  { color: var(--gold-soft); }

                /* ─── SECTION TITLE ─── */
                .gerencial-theme .section-head {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    margin-bottom: 15px;
                }
                .gerencial-theme .section-head .stripe {
                    width: 3px; height: 16px; border-radius: 2px;
                }
                .gerencial-theme .section-head .stripe.ing { background: var(--green-inst); }
                .gerencial-theme .section-head .stripe.exp { background: var(--red-contable); }

                .gerencial-theme .section-head h2 {
                    font-size: 10px;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 2px;
                    color: var(--text-labels);
                }

                /* ─── TABLE ─── */
                .gerencial-theme .tbl-wrap { margin-bottom: 36px; }

                .gerencial-theme table {
                    width: 100%;
                    border-collapse: collapse;
                }

                .gerencial-theme thead tr {
                    border-bottom: 2px solid var(--rule);
                }
                .gerencial-theme thead th {
                    font-size: 10px;
                    letter-spacing: .1em;
                    text-transform: uppercase;
                    font-family: 'IBM Plex Mono', monospace;
                    color: var(--muted);
                    font-weight: 500;
                    padding: 8px 10px 10px;
                }
                .gerencial-theme thead th:first-child { text-align: left; padding-left: 0; }
                .gerencial-theme thead th:not(:first-child) { text-align: right; }

                .gerencial-theme tbody tr {
                    border-bottom: 1px solid var(--warm1);
                    transition: background .12s;
                }
                .gerencial-theme tbody tr:hover { background: var(--warm1); }

                .gerencial-theme td {
                    padding: 11px 10px;
                    font-size: 14px;
                    vertical-align: middle;
                }
                .gerencial-theme td:first-child {
                    padding-left: 0;
                    color: var(--ink2);
                    font-weight: 400;
                }
                .gerencial-theme td:not(:first-child) {
                    text-align: right;
                    font-family: 'IBM Plex Mono', monospace;
                    font-size: 13px;
                    color: var(--ink);
                }

                .gerencial-theme .code-cell {
                    font-family: 'IBM Plex Mono', monospace;
                    font-size: 11px;
                    color: var(--muted);
                    padding-right: 16px;
                }

                /* pct bar */
                .gerencial-theme .bar-wrap { display: flex; align-items: center; gap: 8px; justify-content: flex-end; }
                .gerencial-theme .bar-track {
                    width: 80px; height: 5px;
                    background: var(--warm2);
                    border-radius: 3px;
                    overflow: hidden;
                }
                .gerencial-theme .bar-fill { height: 100%; border-radius: 3px; }

                /* subtotal */
                .gerencial-theme tr.subtotal td {
                    border-top: 1.5px solid var(--rule);
                    border-bottom: 1.5px solid var(--rule);
                    font-weight: 700;
                    font-size: 14px;
                    background: var(--warm1);
                }
                .gerencial-theme tr.subtotal td:first-child { font-family: 'Lato', sans-serif; }
                .gerencial-theme tr.subtotal td:not(:first-child) { font-family: 'IBM Plex Mono', monospace; }

                .gerencial-theme .loss { color: var(--red) !important; }
                .gerencial-theme .profit { color: var(--green) !important; }

                /* badge */
                .gerencial-theme .badge {
                    display: inline-block;
                    padding: 2px 8px;
                    border-radius: 20px;
                    font-size: 10px;
                    font-weight: 700;
                    font-family: 'IBM Plex Mono', monospace;
                    letter-spacing: .05em;
                    margin-left: 6px;
                    vertical-align: middle;
                }
                .gerencial-theme .badge.ing { background: var(--green-lt); color: var(--green); }
                .gerencial-theme .badge.gasto { background: var(--red-lt); color: var(--red); }
                .gerencial-theme .badge.info { background: var(--blue-lt); color: var(--blue); }

                /* group header */
                .gerencial-theme tr.group-row td {
                    font-size: 11px;
                    letter-spacing: .09em;
                    text-transform: uppercase;
                    color: var(--muted);
                    font-family: 'IBM Plex Mono', monospace;
                    padding: 14px 0 4px;
                    border-bottom: none;
                    background: transparent;
                }
                .gerencial-theme tr.group-row:hover { background: transparent; }

                /* ─── UTILIDAD BLOCK ─── */
                .gerencial-theme .result-block {
                    background: var(--bg-grand-total);
                    border: 2px solid var(--green-inst);
                    border-radius: 8px;
                    padding: 20px 30px;
                    margin-top: 30px;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    color: white;
                }
                .gerencial-theme .result-label {
                    font-family: 'Cormorant Garamond', serif;
                    font-size: 20px;
                    font-style: italic;
                    font-weight: 600;
                }
                .gerencial-theme .result-value {
                    font-size: 28px;
                    font-weight: 700;
                    color: var(--gold-soft);
                }

                /* ─── CHARTS ─── */
                .gerencial-theme .charts-row {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 24px;
                    margin: 44px 0;
                }
                @media (max-width: 640px) {
                    .gerencial-theme .charts-row { grid-template-columns: 1fr; }
                    .gerencial-theme .kpi-strip { grid-template-columns: 1fr; }
                }
                .gerencial-theme .chart-card {
                    border: 1px solid var(--rule);
                    border-radius: 10px;
                    padding: 22px;
                    background: var(--white);
                }
                .gerencial-theme .chart-title {
                    font-family: 'Playfair Display', serif;
                    font-size: 13px;
                    font-weight: 700;
                    color: var(--ink);
                    margin-bottom: 16px;
                    text-transform: uppercase;
                    letter-spacing: .06em;
                }
                .gerencial-theme .donut-wrap { display: flex; align-items: center; gap: 16px; }
                .gerencial-theme svg.donut { flex-shrink: 0; }
                .gerencial-theme .legend-list { font-size: 12px; color: var(--ink2); }
                .gerencial-theme .legend-list li {
                    display: flex; align-items: center; gap: 7px;
                    margin-bottom: 7px; list-style: none;
                }
                .gerencial-theme .leg-swatch { width: 10px; height: 10px; border-radius: 2px; flex-shrink:0; }
                .gerencial-theme .leg-name { flex: 1; }
                .gerencial-theme .leg-pct { font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: var(--muted); }

                .gerencial-theme .hbar-list { list-style: none; }
                .gerencial-theme .hbar-item { margin-bottom: 10px; }
                .gerencial-theme .hbar-meta { display: flex; justify-content: space-between; font-size: 11px; color: var(--muted); margin-bottom: 3px; }
                .gerencial-theme .hbar-name { font-family: 'Lato', sans-serif; color: var(--ink2); }
                .gerencial-theme .hbar-val  { font-family: 'IBM Plex Mono', monospace; font-size: 11px; }
                .gerencial-theme .hbar-track { height: 8px; background: var(--warm2); border-radius: 4px; overflow: hidden; }
                .gerencial-theme .hbar-fill  { height: 100%; border-radius: 4px; }
                
                .gerencial-theme .footer {
                    margin-top: 60px;
                    padding-top: 20px;
                    border-top: 1px solid var(--rule);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    font-size: 11px;
                    color: var(--muted);
                    font-family: 'IBM Plex Mono', monospace;
                    flex-wrap: wrap;
                    gap: 8px;
                }
                
                @keyframes fadeUp {
                    from { opacity: 0; transform: translateY(18px); }
                    to   { opacity: 1; transform: translateY(0); }
                }
                .gerencial-theme .fade-in { animation: fadeUp .5s ease both; }
                
                @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;700&family=Lato:ital,wght@0,300;0,400;0,700;1,400&family=Playfair+Display:ital,wght@0,400;0,700;1,400&display=swap');
            `}</style>

            <Head>
                <title>Estado de Resultados Gerencial</title>
            </Head>

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pt-24">
                
                {/* Panel Superior de Control */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
                    <div>
                        <h1 className="text-3xl font-black text-slate-900 tracking-tight">Estado de Resultados Gerencial</h1>
                        <p className="text-slate-500 mt-1">Visión estratégica y análisis visual financiero</p>
                    </div>

                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => router.push('/contabilidad/reportes/estado-resultados-clasificado')}
                            className="text-sm font-medium text-slate-500 hover:text-slate-800 transition-colors"
                        >
                            Ver Clasificado
                        </button>
                        <span className="text-slate-300">|</span>
                        <button
                            onClick={() => router.push('/contabilidad/reportes/estado-resultados')}
                            className="text-sm font-medium text-slate-500 hover:text-slate-800 transition-colors"
                        >
                            Ver Analítico
                        </button>
                    </div>
                </div>

                {/* Filtros */}
                <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 mb-8 relative z-10">
                    <div className="flex flex-col md:flex-row items-end gap-4">
                        <div className="w-full md:w-1/4">
                            <label className={labelClass}>Fecha Inicio</label>
                            <div className="relative">
                                <input
                                    type="date"
                                    value={fechaInicio}
                                    onChange={(e) => setFechaInicio(e.target.value)}
                                    className={inputClass}
                                />
                            </div>
                        </div>
                        <div className="w-full md:w-1/4">
                            <label className={labelClass}>Fecha Fin</label>
                            <div className="relative">
                                <input
                                    type="date"
                                    value={fechaFin}
                                    onChange={(e) => setFechaFin(e.target.value)}
                                    className={inputClass}
                                />
                            </div>
                        </div>

                        <div className="w-full md:w-auto flex-1 flex justify-end">
                            <button
                                onClick={handleGenerateReport}
                                disabled={isLoading}
                                className="w-full md:w-auto px-8 py-3 bg-slate-900 hover:bg-slate-800 disabled:bg-slate-300 text-white font-bold rounded-xl shadow-lg shadow-slate-900/20 transition-all flex items-center justify-center gap-2 hover:-translate-y-0.5"
                            >
                                {isLoading ? (
                                    <>
                                        <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                        </svg>
                                        Calculando...
                                    </>
                                ) : (
                                    <>
                                        <FaSearch />
                                        <span>Generar Vista Gerencial</span>
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
                
                {/* Export Bar */}
                {reporte && (
                    <div className="flex justify-end mb-6">
                         <button
                            onClick={handleExportPDF}
                            className="px-5 py-2.5 bg-white border border-slate-200 hover:border-red-200 hover:bg-red-50 text-slate-700 hover:text-red-700 font-bold rounded-xl transition-all shadow-sm flex items-center gap-2 group"
                        >
                            <FaFilePdf className="text-red-500 group-hover:scale-110 transition-transform" size={16} />
                            <span>Descargar PDF Premium</span>
                        </button>
                    </div>
                )}

                {/* EL REPORTE EN SU TEMA GERENCIAL (INYECTADO) */}
                {reporte && (
                    <div className="gerencial-theme">
                        <div className="page-report fade-in">
                            <header className="header-report">
                                <div className="org-info">
                                    <span className="badge">Informe Financiero Oficial</span>
                                    <div className="org-name">{user?.empresaNombre?.split(' ')[0] || 'Verduras'} <span>{user?.empresaNombre?.split(' ').slice(1).join(' ') || 'La 21'}</span></div>
                                    <div className="org-meta">NIT: {user?.empresaNit || 'Cargando...'}</div>
                                </div>
                                <div className="doc-info">
                                    <div className="doc-title">Estado de Resultados Gerencial</div>
                                    <div className="doc-period">{fechaInicio} — {fechaFin}</div>
                                </div>
                            </header>

                            <div className="kpi-strip">
                                <div className="kpi-cell ing">
                                    <div className="kpi-label">Margen Bruto</div>
                                    <div className="kpi-value green">{reporte.totales.porcentaje_margen_bruto.toFixed(1).replace('.', ',')}%</div>
                                </div>
                                <div className="kpi-cell exp">
                                    <div className="kpi-label">Margen Neto</div>
                                    <div className="kpi-value red">{reporte.totales.porcentaje_margen_neto.toFixed(1).replace('.', ',')}%</div>
                                </div>
                                <div className="kpi-cell res">
                                    <div className="kpi-label">Utilidad Neta</div>
                                    <div className={`kpi-value ${reporte.totales.utilidad_neta < 0 ? 'red' : 'gold'}`}>
                                        {`${reporte.totales.utilidad_neta < 0 ? '-' : ''}$${new Intl.NumberFormat('es-CO').format(Math.abs(reporte.totales.utilidad_neta))}`}
                                    </div>
                                </div>
                            </div>

                            {/* INGRESOS */}
                            <div className="section-card">
                                <div className="card-header ingresos">
                                    <div className="header-stripe"></div>
                                    <h2 className="card-title">Ingresos Operacionales</h2>
                                </div>
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Cuenta</th>
                                            <th>Descripción</th>
                                            <th>Valor</th>
                                            <th>%</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {reporte.ingresos.map((ing, idx) => (
                                            <tr key={ing.codigo}>
                                                <td className="code-cell">{ing.codigo}</td>
                                                <td>{ing.nombre} {ing.is_ingreso_principal && <span className="badge ing">Principal</span>}</td>
                                                <td>${new Intl.NumberFormat('es-CO').format(ing.saldo)}</td>
                                                <td>
                                                    <div className="bar-wrap">
                                                        <div className="bar-track"><div className="bar-fill" style={{ width: `${ing.porcentaje}%`, background: '#2e7d52' }}></div></div>
                                                        <span>{ing.porcentaje.toFixed(1).replace('.', ',')}%</span>
                                                    </div>
                                                </td>
                                            </tr>
                                        ))}
                                        <tr className="subtotal">
                                            <td colSpan="2"><strong>TOTAL INGRESOS OPERACIONALES</strong></td>
                                            <td><strong>${new Intl.NumberFormat('es-CO').format(reporte.totales.total_ingresos)}</strong></td>
                                            <td></td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>

                            {/* COSTOS DE VENTA */}
                            <div className="section-card border-l-4 border-l-amber-500">
                                <div className="card-header gastos !bg-amber-50">
                                    <div className="header-stripe !bg-amber-500"></div>
                                    <h2 className="card-title text-amber-900">Costo de Ventas y Mercancía</h2>
                                </div>
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Cuenta</th>
                                            <th>Descripción</th>
                                            <th>Valor</th>
                                            <th>% Ventas</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {reporte.costos.map((costo) => (
                                            <tr key={costo.codigo}>
                                                <td className="code-cell">{costo.codigo}</td>
                                                <td>{costo.nombre}</td>
                                                <td>${new Intl.NumberFormat('es-CO').format(costo.saldo)}</td>
                                                <td>
                                                    <div className="bar-wrap">
                                                        <div className="bar-track"><div className="bar-fill" style={{ width: `${costo.porcentaje}%`, background: '#f59e0b' }}></div></div>
                                                        <span>{costo.porcentaje.toFixed(1).replace('.', ',')}%</span>
                                                    </div>
                                                </td>
                                            </tr>
                                        ))}
                                        <tr className="subtotal !bg-amber-100/50">
                                            <td colSpan="2" className="!text-amber-900"><strong>TOTAL COSTO DE VENTAS</strong></td>
                                            <td className="!text-amber-900"><strong>${new Intl.NumberFormat('es-CO').format(reporte.totales.total_costos)}</strong></td>
                                            <td></td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>

                            {/* UTILIDAD BRUTA BLOCK */}
                            <div className="result-block !bg-emerald-900 !border-emerald-600 !mt-6 !mb-10">
                                <div className="result-label text-emerald-100 italic">Utilidad Bruta Operacional</div>
                                <div className="flex flex-col items-end">
                                    <div className="result-value !text-emerald-400">
                                        ${new Intl.NumberFormat('es-CO').format(reporte.totales.utilidad_bruta)}
                                    </div>
                                    <div className="text-[10px] uppercase tracking-widest text-emerald-300 font-bold">
                                        Margen Bruto: {reporte.totales.porcentaje_margen_bruto.toFixed(1).replace('.', ',')}%
                                    </div>
                                </div>
                            </div>

                            {/* GASTOS */}
                            <div className="section-card">
                                <div className="card-header gastos">
                                    <div className="header-stripe"></div>
                                    <h2 className="card-title">Gastos de Administración y Ventas</h2>
                                </div>
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Cuenta</th>
                                            <th>Descripción</th>
                                            <th>Valor</th>
                                            <th>%</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {/* NÓMINA */}
                                        {reporte.gastos_nomina && reporte.gastos_nomina.length > 0 && (
                                            <>
                                                <tr className="group-row"><td colSpan="4">▸ Nómina y Carga Prestacional</td></tr>
                                                {reporte.gastos_nomina.map(g => (
                                                    <tr key={g.codigo}>
                                                        <td className="code-cell">{g.codigo}</td>
                                                        <td>{g.nombre} {g.is_mayor_gasto && <span className="badge gasto">Mayor gasto</span>}</td>
                                                        <td>${new Intl.NumberFormat('es-CO').format(g.saldo)}</td>
                                                        <td>
                                                            <div className="bar-wrap">
                                                                <div className="bar-track"><div className="bar-fill" style={{ width: `${g.porcentaje}%`, background: '#b53a2a' }}></div></div>
                                                                <span>{g.porcentaje.toFixed(1).replace('.', ',')}%</span>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </>
                                        )}

                                        {/* OPERATIVOS */}
                                        {reporte.gastos_operativos && reporte.gastos_operativos.length > 0 && (
                                            <>
                                                <tr className="group-row"><td colSpan="4">▸ Gastos Operativos</td></tr>
                                                {reporte.gastos_operativos.map(g => (
                                                    <tr key={g.codigo}>
                                                        <td className="code-cell">{g.codigo}</td>
                                                        <td>{g.nombre} {g.is_mayor_gasto && <span className="badge gasto">Mayor gasto</span>}</td>
                                                        <td>${new Intl.NumberFormat('es-CO').format(g.saldo)}</td>
                                                        <td>
                                                            <div className="bar-wrap">
                                                                <div className="bar-track"><div className="bar-fill" style={{ width: `${g.porcentaje}%`, background: '#c05a45' }}></div></div>
                                                                <span>{g.porcentaje.toFixed(1).replace('.', ',')}%</span>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </>
                                        )}

                                        {/* GENERALES */}
                                        {reporte.gastos_generales && reporte.gastos_generales.length > 0 && (
                                            <>
                                                <tr className="group-row"><td colSpan="4">▸ Gastos Generales y Tributarios</td></tr>
                                                {reporte.gastos_generales.map(g => (
                                                    <tr key={g.codigo}>
                                                        <td className="code-cell">{g.codigo}</td>
                                                        <td>{g.nombre} {g.is_mayor_gasto && <span className="badge gasto">Mayor gasto</span>}</td>
                                                        <td>${new Intl.NumberFormat('es-CO').format(g.saldo)}</td>
                                                        <td>
                                                            <div className="bar-wrap">
                                                                <div className="bar-track"><div className="bar-fill" style={{ width: `${g.porcentaje}%`, background: '#d8958a' }}></div></div>
                                                                <span>{g.porcentaje.toFixed(1).replace('.', ',')}%</span>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </>
                                        )}

                                        <tr className="subtotal">
                                            <td colSpan="2"><strong>TOTAL GASTOS ADMINISTRATIVOS Y VENTAS</strong></td>
                                            <td><strong>${new Intl.NumberFormat('es-CO').format(reporte.totales.total_gastos)}</strong></td>
                                            <td></td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>

                            {/* RESULTADO */}
                            <div className="result-block">
                                <div className="result-label">Resultado Final del Período</div>
                                <div className="result-value">
                                    {reporte.totales.utilidad_neta < 0 ? '−' : ''}${new Intl.NumberFormat('es-CO').format(Math.abs(reporte.totales.utilidad_neta))}
                                </div>
                            </div>

                            {/* GRÁFICAS */}
                            <div className="charts-row">
                                <div className="chart-card">
                                    <div className="chart-title">Composición de Ingresos</div>
                                    <div className="donut-wrap">
                                        <svg className="donut" width="90" height="90" viewBox="0 0 36 36">
                                            <circle r="15.9155" cx="18" cy="18" fill="none" stroke="#e8dfd0" strokeWidth="3.8"/>
                                            {(() => {
                                                let offset = 25;
                                                const colors = ['#2e7d52', '#5aab82', '#9ecfb5', '#c8e6d6', '#e0f0e6'];
                                                return reporte.ingresos.slice(0, 5).map((ing, i) => {
                                                    const pct = ing.porcentaje;
                                                    if (pct <= 0) return null;
                                                    const strokeDasharray = `${pct} ${100 - pct}`;
                                                    const el = (
                                                        <circle 
                                                            key={i} 
                                                            r="15.9155" cx="18" cy="18" fill="none" 
                                                            stroke={colors[i]} strokeWidth="3.8"
                                                            strokeDasharray={strokeDasharray} 
                                                            strokeDashoffset={offset} 
                                                            strokeLinecap="round"
                                                        />
                                                    );
                                                    offset -= pct;
                                                    return el;
                                                });
                                            })()}
                                        </svg>
                                        <ul className="legend-list">
                                            {reporte.ingresos.slice(0, 5).map((ing, i) => {
                                                const colors = ['#2e7d52', '#5aab82', '#9ecfb5', '#c8e6d6', '#e0f0e6'];
                                                return (
                                                    <li key={i}>
                                                        <div className="leg-swatch" style={{ background: colors[i] }}></div>
                                                        <span className="leg-name truncate">{ing.nombre}</span>
                                                        <span className="leg-pct">{ing.porcentaje.toFixed(1).replace('.', ',')}%</span>
                                                    </li>
                                                );
                                            })}
                                        </ul>
                                    </div>
                                </div>

                                <div className="chart-card">
                                    <div className="chart-title">Top 5 Rubros de Mayor Impacto</div>
                                    <ul className="hbar-list">
                                        {reporte.top_10_impactos && reporte.top_10_impactos.slice(0, 5).map((impacto, i) => {
                                            const colors = ['#b53a2a', '#c05a45', '#f59e0b', '#d97060', '#1e4f87'];
                                            return (
                                                <li className="hbar-item" key={i}>
                                                    <div className="hbar-meta">
                                                        <span className="hbar-name truncate max-w-[60%]">{impacto.nombre}</span>
                                                        <span className="hbar-val">${new Intl.NumberFormat('es-CO').format(impacto.saldo)} · {impacto.porcentaje.toFixed(1).replace('.', ',')}%</span>
                                                    </div>
                                                    <div className="hbar-track">
                                                        <div className="hbar-fill" style={{ width: `${impacto.porcentaje}%`, background: colors[i] || '#cbd5e1' }}></div>
                                                    </div>
                                                </li>
                                            );
                                        })}
                                    </ul>
                                </div>
                            </div>
                            
                            <footer className="footer">
                                <span>Estado de Resultados Gerencial · {fechaInicio} – {fechaFin} · {user?.empresaNombre} · NIT {user?.empresaNit}</span>
                                <span>Generado automáticamente</span>
                            </footer>

                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
