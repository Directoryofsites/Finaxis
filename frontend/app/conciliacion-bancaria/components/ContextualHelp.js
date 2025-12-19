'use client';

import { useState } from 'react';
import { HelpCircle, X, BookOpen, Video, FileText } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const ContextualHelp = ({ activeTab }) => {
  const [isOpen, setIsOpen] = useState(false);

  const getHelpContent = (tab) => {
    const helpContent = {
      dashboard: {
        title: 'Dashboard de Conciliación',
        description: 'Vista general del estado de conciliaciones bancarias',
        tips: [
          'Revisa las estadísticas de conciliación en tiempo real',
          'Usa los filtros por fecha para análisis específicos',
          'Los indicadores de color muestran el estado de cada cuenta'
        ],
        actions: [
          { icon: BookOpen, text: 'Ver Guía Completa', action: () => window.open('/manual/conciliacion-bancaria', '_blank') },
          { icon: Video, text: 'Ver Video Tutorial', action: () => console.log('Video tutorial') },
        ]
      },
      import: {
        title: 'Importación de Extractos',
        description: 'Carga y procesa archivos de extractos bancarios',
        tips: [
          'Configura primero el formato de tu banco en la pestaña Configuración',
          'Los archivos soportados son: CSV, TXT, Excel',
          'El sistema detecta automáticamente duplicados',
          'Siempre revisa la vista previa antes de confirmar'
        ],
        actions: [
          { icon: FileText, text: 'Formatos Soportados', action: () => console.log('Formatos') },
          { icon: BookOpen, text: 'Guía de Importación', action: () => console.log('Guía') },
        ]
      },
      manual: {
        title: 'Conciliación Manual',
        description: 'Revisa y concilia movimientos manualmente',
        tips: [
          'Los movimientos se ordenan por fecha automáticamente',
          'Usa los filtros para encontrar movimientos específicos',
          'Puedes conciliar uno a uno o uno a muchos',
          'Siempre agrega notas explicativas'
        ],
        actions: [
          { icon: BookOpen, text: 'Mejores Prácticas', action: () => console.log('Prácticas') },
          { icon: Video, text: 'Demo Conciliación', action: () => console.log('Demo') },
        ]
      },
      adjustments: {
        title: 'Ajustes Automáticos',
        description: 'Genera asientos contables automáticamente',
        tips: [
          'El sistema detecta comisiones, intereses y notas automáticamente',
          'Siempre revisa la vista previa antes de aplicar',
          'Configura las cuentas contables en la pestaña Configuración',
          'Los ajustes se integran directamente al sistema contable'
        ],
        actions: [
          { icon: BookOpen, text: 'Tipos de Ajustes', action: () => console.log('Tipos') },
          { icon: FileText, text: 'Configurar Cuentas', action: () => console.log('Cuentas') },
        ]
      },
      reports: {
        title: 'Reportes de Conciliación',
        description: 'Genera reportes detallados y exportaciones',
        tips: [
          'Los reportes incluyen movimientos conciliados y pendientes',
          'Puedes exportar en PDF y Excel',
          'Usa los filtros por fecha para reportes específicos',
          'Los reportes son útiles para auditorías'
        ],
        actions: [
          { icon: FileText, text: 'Plantillas de Reporte', action: () => console.log('Plantillas') },
          { icon: BookOpen, text: 'Guía de Reportes', action: () => console.log('Reportes') },
        ]
      },
      config: {
        title: 'Configuración del Sistema',
        description: 'Configura formatos de banco y cuentas contables',
        tips: [
          'Crea una configuración por cada banco que uses',
          'Prueba siempre con un archivo de muestra',
          'Configura las cuentas contables para ajustes automáticos',
          'Las configuraciones se pueden duplicar y reutilizar'
        ],
        actions: [
          { icon: BookOpen, text: 'Guía de Configuración', action: () => console.log('Config') },
          { icon: FileText, text: 'Ejemplos de Formatos', action: () => console.log('Ejemplos') },
        ]
      }
    };

    return helpContent[tab] || helpContent.dashboard;
  };

  const content = getHelpContent(activeTab);

  if (!isOpen) {
    return (
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-50 shadow-lg"
      >
        <HelpCircle className="h-4 w-4 mr-2" />
        Ayuda
      </Button>
    );
  }

  return (
    <Card className="fixed bottom-6 right-6 z-50 w-80 shadow-xl">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center">
            <HelpCircle className="h-5 w-5 mr-2 text-blue-600" />
            {content.title}
          </CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsOpen(false)}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-gray-600">
          {content.description}
        </p>
        
        <div>
          <h4 className="font-medium text-sm mb-2">Consejos útiles:</h4>
          <ul className="text-sm text-gray-600 space-y-1">
            {content.tips.map((tip, index) => (
              <li key={index} className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                {tip}
              </li>
            ))}
          </ul>
        </div>
        
        <div className="space-y-2">
          {content.actions.map((action, index) => (
            <Button
              key={index}
              variant="outline"
              size="sm"
              onClick={action.action}
              className="w-full justify-start"
            >
              <action.icon className="h-4 w-4 mr-2" />
              {action.text}
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default ContextualHelp;