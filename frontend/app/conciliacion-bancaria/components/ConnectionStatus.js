'use client';

import { useState, useEffect } from 'react';
import { Wifi, WifiOff, AlertCircle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

const ConnectionStatus = () => {
  const [status, setStatus] = useState('checking'); // 'online', 'offline', 'checking'
  const [lastCheck, setLastCheck] = useState(null);

  const checkConnection = async () => {
    try {
      const response = await fetch('/api/conciliacion-bancaria/health', {
        method: 'GET',
        headers: {
          'Cache-Control': 'no-cache'
        }
      });
      
      if (response.ok) {
        setStatus('online');
      } else {
        setStatus('offline');
      }
    } catch (error) {
      setStatus('offline');
    }
    
    setLastCheck(new Date());
  };

  useEffect(() => {
    // Verificar conexión inicial
    checkConnection();
    
    // Verificar cada 30 segundos
    const interval = setInterval(checkConnection, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const getStatusConfig = () => {
    switch (status) {
      case 'online':
        return {
          icon: Wifi,
          text: 'Conectado',
          variant: 'default',
          className: 'bg-green-100 text-green-800 border-green-200'
        };
      case 'offline':
        return {
          icon: WifiOff,
          text: 'Sin conexión',
          variant: 'destructive',
          className: 'bg-red-100 text-red-800 border-red-200'
        };
      case 'checking':
        return {
          icon: AlertCircle,
          text: 'Verificando...',
          variant: 'secondary',
          className: 'bg-yellow-100 text-yellow-800 border-yellow-200'
        };
      default:
        return {
          icon: AlertCircle,
          text: 'Desconocido',
          variant: 'secondary',
          className: 'bg-gray-100 text-gray-800 border-gray-200'
        };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  return (
    <div className="fixed bottom-6 left-6 z-50">
      <Badge 
        variant={config.variant}
        className={`${config.className} px-3 py-1 flex items-center space-x-2 shadow-lg cursor-pointer`}
        onClick={checkConnection}
        title={lastCheck ? `Última verificación: ${lastCheck.toLocaleTimeString()}` : 'Verificar conexión'}
      >
        <Icon className="h-3 w-3" />
        <span className="text-xs font-medium">{config.text}</span>
      </Badge>
    </div>
  );
};

export default ConnectionStatus;