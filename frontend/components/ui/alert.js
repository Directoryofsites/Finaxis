import React from 'react';
import { AlertTriangle, CheckCircle, Info, XCircle } from 'lucide-react';

const Alert = ({ children, variant = 'default', className = '' }) => {
  const baseClasses = 'relative w-full rounded-lg border p-4';
  
  const variantClasses = {
    default: 'bg-background text-foreground border-border',
    destructive: 'border-red-200 bg-red-50 text-red-900',
    success: 'border-green-200 bg-green-50 text-green-900',
    warning: 'border-yellow-200 bg-yellow-50 text-yellow-900',
    info: 'border-blue-200 bg-blue-50 text-blue-900'
  };

  const iconMap = {
    default: Info,
    destructive: XCircle,
    success: CheckCircle,
    warning: AlertTriangle,
    info: Info
  };

  const Icon = iconMap[variant];

  return (
    <div className={`${baseClasses} ${variantClasses[variant]} ${className}`} role="alert">
      <div className="flex items-start gap-3">
        <Icon className="h-4 w-4 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          {children}
        </div>
      </div>
    </div>
  );
};

const AlertDescription = ({ children, className = '' }) => {
  return (
    <div className={`text-sm ${className}`}>
      {children}
    </div>
  );
};

const AlertTitle = ({ children, className = '' }) => {
  return (
    <h5 className={`mb-1 font-medium leading-none tracking-tight ${className}`}>
      {children}
    </h5>
  );
};

export { Alert, AlertDescription, AlertTitle };