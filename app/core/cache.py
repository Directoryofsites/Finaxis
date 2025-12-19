"""
Sistema de caché para el módulo de Conciliación Bancaria
"""

import json
import time
from typing import Any, Optional, Dict
from functools import wraps
import hashlib

class SimpleCache:
    """Cache simple en memoria para configuraciones y datos frecuentemente accedidos"""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutos por defecto
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generar clave única para el cache"""
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Obtener valor del cache"""
        if key in self._cache:
            entry = self._cache[key]
            if time.time() < entry['expires_at']:
                entry['hits'] += 1
                entry['last_accessed'] = time.time()
                return entry['value']
            else:
                # Expirado, eliminar
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Establecer valor en el cache"""
        if ttl is None:
            ttl = self.default_ttl
        
        self._cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl,
            'created_at': time.time(),
            'last_accessed': time.time(),
            'hits': 0
        }
    
    def delete(self, key: str) -> bool:
        """Eliminar valor del cache"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Limpiar todo el cache"""
        self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cache"""
        total_entries = len(self._cache)
        total_hits = sum(entry['hits'] for entry in self._cache.values())
        
        return {
            'total_entries': total_entries,
            'total_hits': total_hits,
            'memory_usage_mb': len(str(self._cache)) / (1024 * 1024),
            'entries': [
                {
                    'key': key[:50] + '...' if len(key) > 50 else key,
                    'hits': entry['hits'],
                    'age_seconds': time.time() - entry['created_at'],
                    'ttl_remaining': max(0, entry['expires_at'] - time.time())
                }
                for key, entry in self._cache.items()
            ]
        }
    
    def cleanup_expired(self) -> int:
        """Limpiar entradas expiradas"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time >= entry['expires_at']
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        return len(expired_keys)

# Instancia global del cache
cache = SimpleCache()

def cached(ttl: int = 300, key_prefix: str = ""):
    """Decorador para cachear resultados de funciones"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clave del cache
            cache_key = cache._generate_key(
                f"{key_prefix}:{func.__name__}", 
                *args, 
                **kwargs
            )
            
            # Intentar obtener del cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Ejecutar función y cachear resultado
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        
        # Agregar método para limpiar cache de esta función
        wrapper.clear_cache = lambda: cache.clear()
        wrapper.cache_key = lambda *args, **kwargs: cache._generate_key(
            f"{key_prefix}:{func.__name__}", *args, **kwargs
        )
        
        return wrapper
    return decorator

def invalidate_cache_pattern(pattern: str) -> int:
    """Invalidar entradas del cache que coincidan con un patrón"""
    keys_to_delete = [
        key for key in cache._cache.keys()
        if pattern in key
    ]
    
    for key in keys_to_delete:
        cache.delete(key)
    
    return len(keys_to_delete)

# Funciones específicas para conciliación bancaria
class BankReconciliationCache:
    """Cache especializado para conciliación bancaria"""
    
    @staticmethod
    @cached(ttl=600, key_prefix="import_config")  # 10 minutos
    def get_import_config(config_id: int, empresa_id: int):
        """Cache para configuraciones de importación"""
        # Esta función será implementada en el servicio
        pass
    
    @staticmethod
    @cached(ttl=300, key_prefix="accounting_config")  # 5 minutos
    def get_accounting_config(bank_account_id: int, empresa_id: int):
        """Cache para configuraciones contables"""
        # Esta función será implementada en el servicio
        pass
    
    @staticmethod
    @cached(ttl=180, key_prefix="reconciliation_summary")  # 3 minutos
    def get_reconciliation_summary(bank_account_id: int, empresa_id: int):
        """Cache para resúmenes de conciliación"""
        # Esta función será implementada en el servicio
        pass
    
    @staticmethod
    def invalidate_config_cache(empresa_id: int, config_type: str = None):
        """Invalidar cache de configuraciones"""
        if config_type:
            pattern = f"{config_type}:*:{empresa_id}"
        else:
            pattern = f"*:{empresa_id}"
        
        return invalidate_cache_pattern(pattern)
    
    @staticmethod
    def invalidate_reconciliation_cache(bank_account_id: int, empresa_id: int):
        """Invalidar cache de conciliación para una cuenta específica"""
        patterns = [
            f"reconciliation_summary:*:{bank_account_id}:{empresa_id}",
            f"unmatched_movements:*:{bank_account_id}:{empresa_id}"
        ]
        
        total_invalidated = 0
        for pattern in patterns:
            total_invalidated += invalidate_cache_pattern(pattern)
        
        return total_invalidated

# Middleware para limpieza automática del cache
class CacheCleanupMiddleware:
    """Middleware para limpiar automáticamente el cache"""
    
    def __init__(self, cleanup_interval: int = 300):  # 5 minutos
        self.cleanup_interval = cleanup_interval
        self.last_cleanup = time.time()
    
    def __call__(self, request, call_next):
        """Procesar request y limpiar cache si es necesario"""
        current_time = time.time()
        
        # Limpiar cache expirado si ha pasado el intervalo
        if current_time - self.last_cleanup > self.cleanup_interval:
            expired_count = cache.cleanup_expired()
            if expired_count > 0:
                print(f"🧹 Cache cleanup: {expired_count} entradas expiradas eliminadas")
            self.last_cleanup = current_time
        
        return call_next(request)

# Funciones de utilidad para monitoreo
def get_cache_health() -> Dict[str, Any]:
    """Obtener estado de salud del cache"""
    stats = cache.get_stats()
    
    # Calcular métricas de salud
    hit_rate = 0
    if stats['total_entries'] > 0:
        total_accesses = sum(entry['hits'] for entry in stats['entries'])
        hit_rate = (total_accesses / max(1, stats['total_entries'])) * 100
    
    memory_usage_mb = stats['memory_usage_mb']
    
    # Determinar estado de salud
    health_status = "healthy"
    if memory_usage_mb > 100:  # Más de 100MB
        health_status = "warning"
    if memory_usage_mb > 500:  # Más de 500MB
        health_status = "critical"
    
    return {
        'status': health_status,
        'hit_rate_percent': round(hit_rate, 2),
        'memory_usage_mb': round(memory_usage_mb, 2),
        'total_entries': stats['total_entries'],
        'recommendations': _get_cache_recommendations(stats)
    }

def _get_cache_recommendations(stats: Dict[str, Any]) -> list:
    """Generar recomendaciones basadas en estadísticas del cache"""
    recommendations = []
    
    if stats['memory_usage_mb'] > 100:
        recommendations.append("Considerar reducir TTL de entradas para liberar memoria")
    
    low_hit_entries = [
        entry for entry in stats['entries'] 
        if entry['hits'] < 2 and entry['age_seconds'] > 300
    ]
    
    if len(low_hit_entries) > 10:
        recommendations.append("Muchas entradas con pocos hits, revisar patrones de cache")
    
    if stats['total_entries'] > 1000:
        recommendations.append("Cache muy grande, considerar implementar LRU eviction")
    
    return recommendations