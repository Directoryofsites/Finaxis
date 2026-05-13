'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Rocket, Store, User, CheckCircle, Server } from 'lucide-react';
import toast, { Toaster } from 'react-hot-toast';
import { API_URL } from '@/lib/apiService';

export default function SetupPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  // step: 0=elegir modo, 1=config PostgreSQL (solo multi), 2=datos empresa
  const [step, setStep] = useState(0);
  const [dbMode, setDbMode] = useState(null); // 'mono' | 'multi'

  const [dbConfig, setDbConfig] = useState({
    host: 'localhost',
    port: '5432',
    user: 'postgres',
    password: '',
    dbname: 'finaxis_network',
    migrate: false,
  });

  const [formData, setFormData] = useState({
    razon_social: '',
    nit: '',
    fecha_inicio: new Date().toISOString().split('T')[0],
    admin_email: '',
    admin_password: '',
  });

  const handleDbChange = (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setDbConfig((prev) => ({ ...prev, [e.target.name]: value }));
  };

  const handleChange = (e) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  // PASO 0 → elige modo
  const handleSelectMode = (mode) => {
    setDbMode(mode);
    if (mode === 'mono') {
      setStep(2); // Mono salta directo a datos de empresa
    } else {
      setStep(1); // Multi DEBE pasar por PostgreSQL
    }
  };

  // PASO 1: Conectar a PostgreSQL y preparar DB
  const handleConfigDb = async () => {
    if (!dbConfig.password) {
      toast.error('Ingrese la contraseña de PostgreSQL');
      return;
    }
    setLoading(true);
    const dbUrl = `postgresql://${dbConfig.user}:${dbConfig.password}@${dbConfig.host}:${dbConfig.port}/${dbConfig.dbname}`;

    try {
      const res = await fetch(`${API_URL}/api/setup/config-db`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ database_url: dbUrl }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Error al conectar con PostgreSQL');

      if (dbConfig.migrate) {
        toast.loading('Migrando datos locales...', { id: 'mig' });
        const migRes = await fetch(`${API_URL}/api/setup/migrate-data`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ database_url: dbUrl }),
        });
        if (migRes.ok) toast.success('Datos migrados correctamente.', { id: 'mig' });
        else toast.error('Migración con errores, pero la conexión fue guardada.', { id: 'mig' });
      }

      toast.success('PostgreSQL conectado y configurado correctamente.');
      setStep(2);
    } catch (err) {
      toast.error(err.message || 'No se pudo conectar a PostgreSQL');
    } finally {
      setLoading(false);
    }
  };

  // PASO 2: Crear empresa y admin
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.razon_social || !formData.nit || !formData.admin_email || !formData.admin_password) {
      toast.error('Complete todos los campos obligatorios');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/setup/initialize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      const data = await res.json();
      if (res.ok) {
        toast.success('¡Sistema inicializado! Ingresando...');
        setTimeout(() => router.push('/login'), 2000);
      } else {
        toast.error(data.detail || 'Error al inicializar el sistema');
      }
    } catch {
      toast.error('Error de conexión con el servidor');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #064e3b 100%)',
      padding: '1rem',
      fontFamily: 'Inter, system-ui, sans-serif'
    }}>
      <Toaster position="top-right" />

      <div style={{
        maxWidth: '900px',
        width: '100%',
        background: 'white',
        borderRadius: '24px',
        boxShadow: '0 25px 50px rgba(0,0,0,0.4)',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'row',
      }}>
        {/* Panel izquierdo */}
        <div style={{
          width: '38%',
          background: 'linear-gradient(180deg, #059669 0%, #0d9488 100%)',
          padding: '2.5rem 2rem',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'space-between',
          color: 'white',
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{
              background: 'rgba(255,255,255,0.2)',
              borderRadius: '20px',
              padding: '1.2rem',
              display: 'inline-block',
              marginBottom: '1rem',
            }}>
              <Rocket size={52} color="white" />
            </div>
            <h1 style={{ fontSize: '2rem', fontWeight: 900, margin: 0 }}>Finaxis</h1>
            <p style={{ fontSize: '0.8rem', opacity: 0.85, marginTop: '0.3rem' }}>
              Asistente de Configuración
            </p>
          </div>

          {/* Pasos */}
          <div style={{ width: '100%', marginTop: '2rem' }}>
            {[
              { num: 0, label: 'Tipo de Instalación' },
              { num: 1, label: 'Configuración de Red', skip: dbMode === 'mono' },
              { num: 2, label: 'Registro de Empresa' },
            ].map(({ num, label, skip }) => (
              <div key={num} style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                marginBottom: '0.75rem',
                opacity: (step >= num || skip) ? 1 : 0.35,
              }}>
                <div style={{
                  width: '28px', height: '28px',
                  borderRadius: '50%',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '0.75rem', fontWeight: 700,
                  background: step > num ? 'white' : 'rgba(255,255,255,0.2)',
                  color: step > num ? '#059669' : 'white',
                  border: step === num ? '2px solid white' : '2px solid transparent',
                  flexShrink: 0,
                }}>
                  {step > num ? '✓' : num + 1}
                </div>
                <span style={{ fontSize: '0.85rem', fontWeight: step === num ? 700 : 400 }}>
                  {label}
                  {skip && <span style={{ fontSize: '0.7rem', opacity: 0.6, marginLeft: '4px' }}>(omitido)</span>}
                </span>
              </div>
            ))}
          </div>

          <p style={{ fontSize: '0.72rem', opacity: 0.7, textAlign: 'center', marginTop: '1.5rem' }}>
            {step === 0 && 'Elija cómo funcionará Finaxis en su negocio.'}
            {step === 1 && 'Configure el servidor PostgreSQL para acceso en red.'}
            {step === 2 && 'Registre su empresa y el usuario administrador.'}
          </p>
        </div>

        {/* Panel derecho */}
        <div style={{ flex: 1, padding: '2.5rem', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>

          {/* ══════ PASO 0: Elegir modo ══════ */}
          {step === 0 && (
            <div>
              <h2 style={{ fontSize: '1.6rem', fontWeight: 900, color: '#1e293b', margin: '0 0 0.25rem 0' }}>
                Bienvenido a Finaxis
              </h2>
              <p style={{ color: '#64748b', fontSize: '0.9rem', marginBottom: '1.75rem' }}>
                Seleccione la arquitectura que corresponde a su negocio.
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {/* Opción MONO */}
                <button onClick={() => handleSelectMode('mono')}
                  style={{
                    display: 'flex', alignItems: 'flex-start', gap: '1rem',
                    padding: '1.25rem', border: '2px solid #e2e8f0', borderRadius: '16px',
                    background: 'white', cursor: 'pointer', textAlign: 'left',
                    transition: 'all 0.2s',
                  }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = '#059669'; e.currentTarget.style.background = '#f0fdf4'; }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = '#e2e8f0'; e.currentTarget.style.background = 'white'; }}
                >
                  <div style={{ background: '#f1f5f9', borderRadius: '12px', padding: '0.6rem', flexShrink: 0 }}>
                    <User size={22} color="#475569" />
                  </div>
                  <div>
                    <div style={{ fontWeight: 700, color: '#1e293b', fontSize: '0.95rem' }}>
                      Monousuario — Local
                    </div>
                    <div style={{ fontSize: '0.82rem', color: '#64748b', marginTop: '0.2rem' }}>
                      Para usar solo en este equipo. Sin servidor externo. Configuración automática (SQLite).
                    </div>
                  </div>
                </button>

                {/* Opción MULTI */}
                <button onClick={() => handleSelectMode('multi')}
                  style={{
                    display: 'flex', alignItems: 'flex-start', gap: '1rem',
                    padding: '1.25rem', border: '2px solid #e2e8f0', borderRadius: '16px',
                    background: 'white', cursor: 'pointer', textAlign: 'left',
                    transition: 'all 0.2s',
                  }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = '#059669'; e.currentTarget.style.background = '#f0fdf4'; }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = '#e2e8f0'; e.currentTarget.style.background = 'white'; }}
                >
                  <div style={{ background: '#f1f5f9', borderRadius: '12px', padding: '0.6rem', flexShrink: 0 }}>
                    <Store size={22} color="#475569" />
                  </div>
                  <div>
                    <div style={{ fontWeight: 700, color: '#1e293b', fontSize: '0.95rem' }}>
                      Multiusuario — Red Local
                    </div>
                    <div style={{ fontSize: '0.82rem', color: '#64748b', marginTop: '0.2rem' }}>
                      Varios equipos se conectan desde el navegador. Requiere PostgreSQL instalado en este PC.
                    </div>
                  </div>
                </button>
              </div>
            </div>
          )}

          {/* ══════ PASO 1: Config PostgreSQL ══════ */}
          {step === 1 && (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.25rem' }}>
                <Server size={20} color="#059669" />
                <h2 style={{ fontSize: '1.5rem', fontWeight: 900, color: '#059669', margin: 0 }}>
                  Servidor de Red (PostgreSQL)
                </h2>
              </div>
              <p style={{ color: '#64748b', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
                Ingrese los datos de conexión. Las otras PC entrarán escribiendo la IP de este equipo en su navegador.
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  <div>
                    <label style={labelStyle}>Host / IP</label>
                    <input name="host" value={dbConfig.host} onChange={handleDbChange} style={inputStyle} />
                  </div>
                  <div>
                    <label style={labelStyle}>Puerto</label>
                    <input name="port" value={dbConfig.port} onChange={handleDbChange} style={inputStyle} />
                  </div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  <div>
                    <label style={labelStyle}>Usuario de PostgreSQL</label>
                    <input name="user" value={dbConfig.user} onChange={handleDbChange} style={inputStyle} />
                  </div>
                  <div>
                    <label style={labelStyle}>Contraseña de PostgreSQL</label>
                    <input type="password" name="password" value={dbConfig.password}
                      onChange={handleDbChange} placeholder="Requerido" style={inputStyle} />
                  </div>
                </div>
                <div>
                  <label style={labelStyle}>Nombre de la Base de Datos</label>
                  <input name="dbname" value={dbConfig.dbname} onChange={handleDbChange} style={inputStyle} />
                </div>

                {/* Info estaciones */}
                <div style={{
                  background: '#eff6ff', border: '1px solid #bfdbfe',
                  borderRadius: '12px', padding: '0.75rem 1rem', fontSize: '0.78rem', color: '#1d4ed8',
                }}>
                  <strong>📡 Estaciones (otros equipos):</strong> No necesitan instalación. Solo abren el navegador y escriben{' '}
                  <code style={{ background: '#dbeafe', padding: '1px 4px', borderRadius: '4px' }}>
                    http://&lt;IP-de-este-PC&gt;:3000
                  </code>
                </div>

                {/* Migrar */}
                <label style={{
                  display: 'flex', alignItems: 'center', gap: '0.6rem', cursor: 'pointer',
                  background: '#fffbeb', border: '1px solid #fde68a',
                  borderRadius: '12px', padding: '0.75rem 1rem',
                }}>
                  <input type="checkbox" name="migrate" checked={dbConfig.migrate}
                    onChange={handleDbChange} style={{ width: '16px', height: '16px' }} />
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.85rem', color: '#92400e' }}>
                      Migrar datos de SQLite local
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#b45309' }}>
                      Importar empresas y documentos de una instalación anterior.
                    </div>
                  </div>
                </label>

                <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
                  <button onClick={() => setStep(0)} style={btnSecondaryStyle}>← Atrás</button>
                  <button onClick={handleConfigDb} disabled={loading} style={{
                    ...btnPrimaryStyle, flex: 2, opacity: loading ? 0.6 : 1,
                  }}>
                    {loading ? '⏳ Conectando...' : '🔌 Conectar y Continuar'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ══════ PASO 2: Datos empresa ══════ */}
          {step === 2 && (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.25rem' }}>
                <CheckCircle size={20} color="#059669" />
                <h2 style={{ fontSize: '1.5rem', fontWeight: 900, color: '#1e293b', margin: 0 }}>
                  Registro de Empresa
                </h2>
              </div>
              <p style={{ color: '#64748b', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
                {dbMode === 'multi'
                  ? '✅ PostgreSQL configurado. Ahora registre su primera empresa.'
                  : 'Configure su empresa y el usuario administrador.'}
              </p>

              <form onSubmit={handleSubmit}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                    <div>
                      <label style={labelStyle}>Razón Social *</label>
                      <input required name="razon_social" value={formData.razon_social}
                        onChange={handleChange} placeholder="Mi Empresa S.A.S." style={inputStyle} />
                    </div>
                    <div>
                      <label style={labelStyle}>NIT / Identificación *</label>
                      <input required name="nit" value={formData.nit}
                        onChange={handleChange} placeholder="900.123.456-7" style={inputStyle} />
                    </div>
                  </div>

                  <div style={{
                    borderTop: '1px solid #f1f5f9', paddingTop: '0.75rem', marginTop: '0.25rem',
                  }}>
                    <p style={{ fontSize: '0.75rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                      Usuario Administrador
                    </p>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                      <div>
                        <label style={labelStyle}>Correo Electrónico *</label>
                        <input required type="email" name="admin_email" value={formData.admin_email}
                          onChange={handleChange} placeholder="admin@miempresa.com" style={inputStyle} />
                      </div>
                      <div>
                        <label style={labelStyle}>Contraseña *</label>
                        <input required type="password" name="admin_password" value={formData.admin_password}
                          onChange={handleChange} placeholder="Mínimo 8 caracteres" style={inputStyle} />
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
                    <button type="button" onClick={() => setStep(dbMode === 'mono' ? 0 : 1)}
                      style={btnSecondaryStyle}>
                      ← Atrás
                    </button>
                    <button type="submit" disabled={loading} style={{
                      ...btnPrimaryStyle, flex: 2, opacity: loading ? 0.6 : 1,
                    }}>
                      {loading ? '⏳ Inicializando...' : '🚀 Finalizar y Entrar'}
                    </button>
                  </div>
                </div>
              </form>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}

// Estilos reutilizables
const labelStyle = {
  display: 'block',
  fontSize: '0.72rem',
  fontWeight: 700,
  color: '#475569',
  textTransform: 'uppercase',
  marginBottom: '0.3rem',
  letterSpacing: '0.05em',
};

const inputStyle = {
  width: '100%',
  padding: '0.5rem 0.75rem',
  border: '1.5px solid #e2e8f0',
  borderRadius: '10px',
  fontSize: '0.88rem',
  outline: 'none',
  boxSizing: 'border-box',
  fontFamily: 'inherit',
  color: '#1e293b',
};

const btnPrimaryStyle = {
  flex: 1,
  padding: '0.65rem 1rem',
  background: '#059669',
  color: 'white',
  border: 'none',
  borderRadius: '12px',
  fontWeight: 700,
  fontSize: '0.9rem',
  cursor: 'pointer',
  fontFamily: 'inherit',
  boxShadow: '0 4px 12px rgba(5,150,105,0.3)',
};

const btnSecondaryStyle = {
  flex: 1,
  padding: '0.65rem 1rem',
  background: 'white',
  color: '#475569',
  border: '1.5px solid #e2e8f0',
  borderRadius: '12px',
  fontWeight: 700,
  fontSize: '0.9rem',
  cursor: 'pointer',
  fontFamily: 'inherit',
};
