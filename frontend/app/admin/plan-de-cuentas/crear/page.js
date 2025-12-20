'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

import { useAuth } from '../../../context/AuthContext';
import { apiService } from '../../../../lib/apiService';

// Lista de funciones especiales para el dropdown
const funcionesEspeciales = [
    { value: '', label: 'Ninguna (Cuenta estándar)' },
    { value: 'CUENTA_CARTERA', label: 'Cuenta de Cartera (Clientes)' },
    { value: 'CUENTA_PROVEEDORES', label: 'Cuenta de Proveedores' },
    { value: 'CUENTA_BANCARIA', label: 'Cuenta Bancaria (Tesorería)' },
    { value: 'CUENTA_IVA_GENERADO', label: 'IVA Generado' },
    { value: 'CUENTA_IVA_DESCONTABLE', label: 'IVA Descontable' },
    { value: 'CUENTA_RETENCION_FUENTE', label: 'Retención en la Fuente' },
    { value: 'CIERRE_EJERCICIO', label: 'Cierre del Ejercicio' },
    { value: 'CUENTA_INVENTARIO', label: 'Cuenta de Inventario' },
    { value: 'CUENTA_COSTO_VENTA', label: 'Costo de Venta' },
];

export default function CrearCuentaPage() {
    const router = useRouter();
    const { user, authLoading } = useAuth();
    const [formData, setFormData] = useState({
        codigo: '',
        nombre: '',
        permite_movimiento: false,
        funcion_especial: ''
    });
    const [error, setError] = useState(null);
    const [isLoading, setIsLoading] = useState(false);

    // Redirigir si el usuario no está autenticado
    useEffect(() => {
        if (!authLoading && !user) {
            router.push('/login');
        }
    }, [user, authLoading, router]);

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prevState => ({
            ...prevState,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        if (!user || !user.empresaId) {
            setError("No se pudo identificar al usuario o la empresa. Por favor, inicie sesión de nuevo.");
            setIsLoading(false);
            return;
        }

        try {
            let cuentaPadreId = null;
            let nivelCalculado = 1;
            const codigo = formData.codigo;
            let codigoPadre = '';

            // Lógica robusta para determinar el código del padre y el nivel
            if (codigo.length === 2) { // Grupo, ej: 23
                codigoPadre = codigo.substring(0, 1); // Padre es 2
            } else if (codigo.length === 4) { // Cuenta, ej: 1105
                codigoPadre = codigo.substring(0, 2); // Padre es 11
            } else if (codigo.length >= 6) { // Subcuenta, ej: 110505
                codigoPadre = codigo.substring(0, codigo.length - 2);
            }

            // Si hemos determinado un código padre, lo buscamos para obtener su ID y nivel
            if (codigoPadre) {
                try {
                    const res = await apiService.get(`/plan-cuentas/codigo/${codigoPadre}`);
                    cuentaPadreId = res.data.id;
                    nivelCalculado = res.data.nivel + 1;
                } catch (parentError) {
                    setError(`Error: La cuenta padre con código '${codigoPadre}' no existe. No se puede crear la cuenta hija.`);
                    setIsLoading(false);
                    return;
                }
            }

            // Construcción del payload final y completo para enviar al backend
            const payload = {
                codigo: formData.codigo,
                nombre: formData.nombre,
                permite_movimiento: formData.permite_movimiento,
                empresa_id: user.empresaId, // Usando la variable estandarizada
                nivel: nivelCalculado, // Usando el nivel calculado automáticamente
                funcion_especial: formData.funcion_especial || null,
                cuenta_padre_id: cuentaPadreId,
            };

            await apiService.post('/plan-cuentas/', payload);
            router.push('/admin/plan-de-cuentas');

        } catch (err) {
            let errorMessage = 'Ocurrió un error inesperado al crear la cuenta.';
            if (err.response?.data?.detail) {
                const detail = err.response.data.detail;
                if (Array.isArray(detail) && detail.length > 0 && detail[0].msg) {
                    errorMessage = detail[0].msg;
                } else {
                    errorMessage = String(detail);
                }
            }
            setError(errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

    if (authLoading) {
        return <div className="text-center p-4">Cargando...</div>;
    }

    return (
        <div className="container mx-auto p-4 max-w-2xl">
            <h1 className="text-2xl font-bold mb-4">Crear Nueva Cuenta Contable</h1>
            <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow-md space-y-4">
                <div>
                    <label htmlFor="codigo" className="block text-sm font-medium text-gray-700">Código de la Cuenta</label>
                    <input type="text" name="codigo" id="codigo" required value={formData.codigo} onChange={handleChange} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" />
                </div>
                <div>
                    <label htmlFor="nombre" className="block text-sm font-medium text-gray-700">Nombre de la Cuenta</label>
                    <input type="text" name="nombre" id="nombre" required value={formData.nombre} onChange={handleChange} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" />
                </div>
                {/* El campo de nivel manual ha sido eliminado */}
                <div>
                    <label htmlFor="funcion_especial" className="block text-sm font-medium text-gray-700">Función Especial</label>
                    <select name="funcion_especial" id="funcion_especial" value={formData.funcion_especial} onChange={handleChange} className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md" >
                        {funcionesEspeciales.map(func => (
                            <option key={func.value} value={func.value}>{func.label}</option>
                        ))}
                    </select>
                </div>
                <div className="flex items-center">
                    <input type="checkbox" name="permite_movimiento" id="permite_movimiento" checked={formData.permite_movimiento} onChange={handleChange} className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded" />
                    <label htmlFor="permite_movimiento" className="ml-2 block text-sm text-gray-900">Permite Movimiento (Cuenta Auxiliar)</label>
                </div>

                {error && <p className="text-red-500 text-sm">{error}</p>}

                <div className="text-right">
                    <button type="submit" disabled={isLoading} className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-indigo-300" >
                        {isLoading ? 'Guardando...' : 'Guardar Cuenta'}
                    </button>
                </div>
            </form>
        </div>
    );
}
