"""
Sistema de monitoreo y métricas para el módulo de Conciliación Bancaria
"""

import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from functools import wraps
from collections import defaultdict, deque
import threading
from dataclasses import dataclass, asdict

@dataclass
class PerformanceMetric:
    """Métrica de rendimiento"""
    operation: str
    duration_ms: float
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class PerformanceMonitor:
    """Monitor de rendimiento para operaciones críticas"""
    
    def __init__(self, max_metrics: int = 10000):
        self.metrics: deque = deque(maxlen=max_metrics)
        self.operation_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'count': 0,
            'total_duration': 0,
            'success_count': 0,
            'error_count': 0,
            'avg_duration': 0,
            'min_duration': float('inf'),
            'max_duration': 0,
            'last_execution': None
        })
        self._lock = threading.Lock()
    
    def record_metric(self, metric: PerformanceMetric):
        """Registrar una métrica de rendimiento"""
        with self._lock:
            self.metrics.append(metric)
            
            # Actualizar estadísticas de la operación
            stats = self.operation_stats[metric.operation]
            stats['count'] += 1
            stats['total_duration'] += metric.duration_ms
            stats['last_execution'] = metric.timestamp
            
            if metric.success:
                stats['success_count'] += 1
            else:
                stats['error_count'] += 1
            
            # Actualizar min/max/avg
            stats['min_duration'] = min(stats['min_duration'], metric.duration_ms)
            stats['max_duration'] = max(stats['max_duration'], metric.duration_ms)
            stats['avg_duration'] = stats['total_duration'] / stats['count']
    
    def get_operation_stats(self, operation: str = None) -> Dict[str, Any]:
        """Obtener estadísticas de una operación específica o todas"""
        with self._lock:
            if operation:
                return dict(self.operation_stats.get(operation, {}))
            return {op: dict(stats) for op, stats in self.operation_stats.items()}
    
    def get_recent_metrics(self, minutes: int = 60) -> List[PerformanceMetric]:
        """Obtener métricas recientes"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        with self._lock:
            return [
                metric for metric in self.metrics 
                if metric.timestamp >= cutoff_time
            ]
    
    def get_slow_operations(self, threshold_ms: float = 1000) -> List[PerformanceMetric]:
        """Obtener operaciones lentas"""
        with self._lock:
            return [
                metric for metric in self.metrics 
                if metric.duration_ms > threshold_ms
            ]
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Obtener resumen de errores"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        errors = [
            metric for metric in self.metrics 
            if not metric.success and metric.timestamp >= cutoff_time
        ]
        
        error_by_operation = defaultdict(list)
        for error in errors:
            error_by_operation[error.operation].append(error)
        
        return {
            'total_errors': len(errors),
            'errors_by_operation': {
                op: {
                    'count': len(errs),
                    'latest_error': max(errs, key=lambda x: x.timestamp).error_message if errs else None,
                    'error_rate': len(errs) / max(1, self.operation_stats[op]['count']) * 100
                }
                for op, errs in error_by_operation.items()
            }
        }

# Instancia global del monitor
performance_monitor = PerformanceMonitor()

def monitor_performance(operation_name: str = None):
    """Decorador para monitorear el rendimiento de funciones"""
    def decorator(func):
        op_name = operation_name or f"{func.__module__}.{func.__name__}"
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error_message = None
            result = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                
                # Extraer metadata útil de los argumentos
                metadata = {}
                if args and hasattr(args[0], '__class__'):
                    metadata['class'] = args[0].__class__.__name__
                if len(args) > 1:
                    metadata['args_count'] = len(args) - 1
                if kwargs:
                    metadata['kwargs_keys'] = list(kwargs.keys())
                
                metric = PerformanceMetric(
                    operation=op_name,
                    duration_ms=duration_ms,
                    timestamp=datetime.now(),
                    success=success,
                    error_message=error_message,
                    metadata=metadata
                )
                
                performance_monitor.record_metric(metric)
        
        return wrapper
    return decorator

class AlertManager:
    """Gestor de alertas para condiciones críticas"""
    
    def __init__(self):
        self.alert_thresholds = {
            'slow_operation_ms': 5000,  # 5 segundos
            'error_rate_percent': 10,   # 10% de errores
            'memory_usage_mb': 500,     # 500MB de memoria
            'cache_hit_rate_percent': 50  # Menos del 50% de hit rate
        }
        self.active_alerts: List[Dict[str, Any]] = []
    
    def check_performance_alerts(self) -> List[Dict[str, Any]]:
        """Verificar alertas de rendimiento"""
        alerts = []
        
        # Verificar operaciones lentas
        slow_ops = performance_monitor.get_slow_operations(
            self.alert_thresholds['slow_operation_ms']
        )
        if slow_ops:
            recent_slow = [op for op in slow_ops if 
                          (datetime.now() - op.timestamp).seconds < 300]  # Últimos 5 minutos
            if recent_slow:
                alerts.append({
                    'type': 'slow_operations',
                    'severity': 'warning',
                    'message': f"{len(recent_slow)} operaciones lentas en los últimos 5 minutos",
                    'details': [
                        f"{op.operation}: {op.duration_ms:.0f}ms" 
                        for op in recent_slow[:5]
                    ]
                })
        
        # Verificar tasa de errores
        error_summary = performance_monitor.get_error_summary(hours=1)
        for operation, error_info in error_summary['errors_by_operation'].items():
            if error_info['error_rate'] > self.alert_thresholds['error_rate_percent']:
                alerts.append({
                    'type': 'high_error_rate',
                    'severity': 'critical',
                    'message': f"Alta tasa de errores en {operation}: {error_info['error_rate']:.1f}%",
                    'details': {
                        'operation': operation,
                        'error_count': error_info['count'],
                        'latest_error': error_info['latest_error']
                    }
                })
        
        return alerts
    
    def get_system_health(self) -> Dict[str, Any]:
        """Obtener estado general de salud del sistema"""
        from .cache import get_cache_health
        
        # Estadísticas de rendimiento
        recent_metrics = performance_monitor.get_recent_metrics(minutes=30)
        total_operations = len(recent_metrics)
        successful_operations = sum(1 for m in recent_metrics if m.success)
        
        success_rate = (successful_operations / max(1, total_operations)) * 100
        
        # Operaciones por minuto
        operations_per_minute = total_operations / 30 if total_operations > 0 else 0
        
        # Tiempo promedio de respuesta
        avg_response_time = (
            sum(m.duration_ms for m in recent_metrics) / max(1, total_operations)
        )
        
        # Estado del cache
        cache_health = get_cache_health()
        
        # Determinar estado general
        health_status = "healthy"
        if success_rate < 95 or avg_response_time > 2000:
            health_status = "warning"
        if success_rate < 90 or avg_response_time > 5000:
            health_status = "critical"
        
        return {
            'status': health_status,
            'performance': {
                'success_rate_percent': round(success_rate, 2),
                'avg_response_time_ms': round(avg_response_time, 2),
                'operations_per_minute': round(operations_per_minute, 2),
                'total_operations_30min': total_operations
            },
            'cache': cache_health,
            'alerts': self.check_performance_alerts(),
            'timestamp': datetime.now().isoformat()
        }

# Instancia global del gestor de alertas
alert_manager = AlertManager()

# Funciones específicas para conciliación bancaria
class BankReconciliationMonitor:
    """Monitor especializado para operaciones de conciliación bancaria"""
    
    @staticmethod
    @monitor_performance("bank_reconciliation.file_import")
    def monitor_file_import(func):
        """Monitor para importación de archivos"""
        return func
    
    @staticmethod
    @monitor_performance("bank_reconciliation.auto_matching")
    def monitor_auto_matching(func):
        """Monitor para matching automático"""
        return func
    
    @staticmethod
    @monitor_performance("bank_reconciliation.manual_reconciliation")
    def monitor_manual_reconciliation(func):
        """Monitor para conciliación manual"""
        return func
    
    @staticmethod
    @monitor_performance("bank_reconciliation.adjustment_generation")
    def monitor_adjustment_generation(func):
        """Monitor para generación de ajustes"""
        return func
    
    @staticmethod
    def get_reconciliation_metrics() -> Dict[str, Any]:
        """Obtener métricas específicas de conciliación"""
        stats = performance_monitor.get_operation_stats()
        
        reconciliation_ops = {
            key: value for key, value in stats.items()
            if 'bank_reconciliation' in key
        }
        
        return {
            'operations': reconciliation_ops,
            'summary': {
                'total_reconciliation_operations': sum(
                    op['count'] for op in reconciliation_ops.values()
                ),
                'avg_reconciliation_time': sum(
                    op['avg_duration'] for op in reconciliation_ops.values()
                ) / max(1, len(reconciliation_ops)),
                'reconciliation_success_rate': (
                    sum(op['success_count'] for op in reconciliation_ops.values()) /
                    max(1, sum(op['count'] for op in reconciliation_ops.values()))
                ) * 100
            }
        }

# Funciones de utilidad para logging de rendimiento
def log_performance_warning(operation: str, duration_ms: float, threshold_ms: float = 1000):
    """Registrar advertencia de rendimiento"""
    if duration_ms > threshold_ms:
        print(f"⚠️  Operación lenta detectada: {operation} tomó {duration_ms:.0f}ms")

def log_error_with_context(operation: str, error: Exception, context: Dict[str, Any] = None):
    """Registrar error con contexto adicional"""
    error_info = {
        'operation': operation,
        'error': str(error),
        'error_type': type(error).__name__,
        'timestamp': datetime.now().isoformat()
    }
    
    if context:
        error_info['context'] = context
    
    print(f"❌ Error en {operation}: {error}")
    if context:
        print(f"   Contexto: {context}")

# Middleware para monitoreo automático
class PerformanceMiddleware:
    """Middleware para monitoreo automático de requests"""
    
    def __init__(self):
        self.request_count = 0
        self.start_time = time.time()
    
    def __call__(self, request, call_next):
        """Procesar request y registrar métricas"""
        start_time = time.time()
        self.request_count += 1
        
        try:
            response = call_next(request)
            success = True
            error_message = None
        except Exception as e:
            success = False
            error_message = str(e)
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            
            # Registrar métrica si es una operación de conciliación bancaria
            if '/conciliacion-bancaria' in str(request.url):
                metric = PerformanceMetric(
                    operation=f"api.{request.method}.{request.url.path}",
                    duration_ms=duration_ms,
                    timestamp=datetime.now(),
                    success=success,
                    error_message=error_message,
                    metadata={
                        'method': request.method,
                        'path': request.url.path,
                        'request_count': self.request_count
                    }
                )
                performance_monitor.record_metric(metric)
        
        return response