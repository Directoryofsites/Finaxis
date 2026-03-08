import CustomerPortalFull from '../../components/CustomerPortalFull';
import React from 'react';

// Esta página será accesible públicamente en /portal/[empresa_id]
export default async function PortalEmpresaPage({ params }) {
    // Obtenemos el slug/ID de la empresa de la URL
    const { empresa_id } = await params;

    return (
        <div className="portal-publico-wrapper min-h-screen bg-gray-50 flex flex-col items-center justify-center">
            <CustomerPortalFull empresaSlug={empresa_id} />
        </div>
    );
}

// Opcional: Para evitar que el layout principal del ERP inyecte sus Sidebars
// podríamos requerir un archivo layout.js en esta carpeta `portal`,
// pero en Next.js app router si el layout raíz tiene el SmartLayout,
// afectará todo. Para evadir SmartLayout, la mejor forma es revisar `layout.js` o `SmartLayout.js`.
