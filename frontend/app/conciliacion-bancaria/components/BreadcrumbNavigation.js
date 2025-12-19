'use client';

import { ChevronRight, Home } from 'lucide-react';
import Link from 'next/link';

const BreadcrumbNavigation = ({ activeTab, selectedBankAccount }) => {
  const getTabName = (tab) => {
    const tabNames = {
      dashboard: 'Dashboard',
      import: 'Importar Extractos',
      manual: 'Conciliación Manual',
      adjustments: 'Ajustes Automáticos',
      reports: 'Reportes',
      config: 'Configuración'
    };
    return tabNames[tab] || 'Dashboard';
  };

  return (
    <nav className="flex items-center space-x-2 text-sm text-gray-600 mb-4">
      <Link href="/" className="flex items-center hover:text-blue-600 transition-colors">
        <Home className="h-4 w-4" />
      </Link>
      
      <ChevronRight className="h-4 w-4" />
      
      <Link href="/conciliacion-bancaria" className="hover:text-blue-600 transition-colors">
        Conciliación Bancaria
      </Link>
      
      {activeTab !== 'dashboard' && (
        <>
          <ChevronRight className="h-4 w-4" />
          <span className="text-gray-900 font-medium">
            {getTabName(activeTab)}
          </span>
        </>
      )}
      
      {selectedBankAccount && (
        <>
          <ChevronRight className="h-4 w-4" />
          <span className="text-blue-600 font-medium">
            {selectedBankAccount.nombre}
          </span>
        </>
      )}
    </nav>
  );
};

export default BreadcrumbNavigation;