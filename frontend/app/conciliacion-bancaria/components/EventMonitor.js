'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Activity, X } from 'lucide-react';

export default function EventMonitor() {
  const [isVisible, setIsVisible] = useState(false);
  const [events, setEvents] = useState([]);

  useEffect(() => {
    if (!isVisible) return;

    const addEvent = (type, details) => {
      setEvents(prev => [...prev.slice(-9), {
        timestamp: new Date().toLocaleTimeString(),
        type,
        details
      }]);
    };

    // Monitorear eventos de input
    const handleInput = (e) => {
      addEvent('input', {
        target: e.target.tagName,
        id: e.target.id,
        value: e.target.value,
        type: e.target.type
      });
    };

    // Monitorear eventos de change
    const handleChange = (e) => {
      addEvent('change', {
        target: e.target.tagName,
        id: e.target.id,
        value: e.target.value,
        type: e.target.type
      });
    };

    // Monitorear eventos de focus
    const handleFocus = (e) => {
      addEvent('focus', {
        target: e.target.tagName,
        id: e.target.id,
        type: e.target.type
      });
    };

    // Monitorear eventos de blur
    const handleBlur = (e) => {
      addEvent('blur', {
        target: e.target.tagName,
        id: e.target.id,
        type: e.target.type
      });
    };

    // Monitorear eventos de click
    const handleClick = (e) => {
      addEvent('click', {
        target: e.target.tagName,
        id: e.target.id,
        className: e.target.className,
        text: e.target.textContent?.substring(0, 20)
      });
    };

    // Monitorear eventos de teclado
    const handleKeyDown = (e) => {
      addEvent('keydown', {
        key: e.key,
        code: e.code,
        target: e.target.tagName,
        id: e.target.id
      });
    };

    // Agregar event listeners
    document.addEventListener('input', handleInput, true);
    document.addEventListener('change', handleChange, true);
    document.addEventListener('focus', handleFocus, true);
    document.addEventListener('blur', handleBlur, true);
    document.addEventListener('click', handleClick, true);
    document.addEventListener('keydown', handleKeyDown, true);

    return () => {
      document.removeEventListener('input', handleInput, true);
      document.removeEventListener('change', handleChange, true);
      document.removeEventListener('focus', handleFocus, true);
      document.removeEventListener('blur', handleBlur, true);
      document.removeEventListener('click', handleClick, true);
      document.removeEventListener('keydown', handleKeyDown, true);
    };
  }, [isVisible]);

  if (!isVisible) {
    return (
      <div className="fixed bottom-4 left-4 z-50">
        <Button
          onClick={() => setIsVisible(true)}
          variant="outline"
          size="sm"
          className="bg-blue-50 border-blue-200 text-blue-800 hover:bg-blue-100"
        >
          <Activity className="h-4 w-4 mr-2" />
          Monitor
        </Button>
      </div>
    );
  }

  return (
    <div className="fixed bottom-4 left-4 z-50 w-80 max-h-96 overflow-auto">
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-2">
              <Activity className="h-4 w-4 text-blue-600" />
              <span>Monitor de Eventos</span>
            </div>
            <Button
              onClick={() => setIsVisible(false)}
              variant="ghost"
              size="sm"
            >
              <X className="h-4 w-4" />
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-xs font-semibold text-blue-800">
                Eventos Recientes ({events.length})
              </span>
              <Button
                onClick={() => setEvents([])}
                variant="ghost"
                size="sm"
                className="text-xs"
              >
                Limpiar
              </Button>
            </div>
            
            <div className="text-xs bg-white p-2 rounded border max-h-64 overflow-auto font-mono">
              {events.length === 0 ? (
                <div className="text-gray-500">No hay eventos registrados</div>
              ) : (
                events.map((event, index) => (
                  <div key={index} className="mb-1 pb-1 border-b border-gray-100 last:border-b-0">
                    <div className="flex justify-between">
                      <span className={`font-semibold ${
                        event.type === 'input' ? 'text-green-600' :
                        event.type === 'change' ? 'text-blue-600' :
                        event.type === 'focus' ? 'text-purple-600' :
                        event.type === 'blur' ? 'text-orange-600' :
                        event.type === 'click' ? 'text-red-600' :
                        event.type === 'keydown' ? 'text-indigo-600' :
                        'text-gray-600'
                      }`}>
                        {event.type.toUpperCase()}
                      </span>
                      <span className="text-gray-500">{event.timestamp}</span>
                    </div>
                    <div className="text-gray-700">
                      {event.type === 'input' || event.type === 'change' ? (
                        <>
                          <div>Target: {event.details.target}#{event.details.id}</div>
                          <div>Value: "{event.details.value}"</div>
                        </>
                      ) : event.type === 'focus' || event.type === 'blur' ? (
                        <div>Target: {event.details.target}#{event.details.id}</div>
                      ) : event.type === 'click' ? (
                        <>
                          <div>Target: {event.details.target}#{event.details.id}</div>
                          {event.details.text && <div>Text: "{event.details.text}"</div>}
                        </>
                      ) : event.type === 'keydown' ? (
                        <>
                          <div>Key: {event.details.key} ({event.details.code})</div>
                          <div>Target: {event.details.target}#{event.details.id}</div>
                        </>
                      ) : (
                        <pre>{JSON.stringify(event.details, null, 2)}</pre>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}