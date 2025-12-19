"""
Procesador optimizado de archivos para importaciones grandes
"""

import os
import csv
import pandas as pd
from typing import Iterator, List, Dict, Any, Optional
from datetime import datetime
import tempfile
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import hashlib
import json
from dataclasses import dataclass

@dataclass
class ProcessingChunk:
    """Chunk de datos para procesamiento paralelo"""
    chunk_id: int
    data: List[Dict[str, Any]]
    start_row: int
    end_row: int

class OptimizedFileProcessor:
    """Procesador optimizado para archivos grandes"""
    
    def __init__(self, chunk_size: int = 1000, max_workers: int = None):
        self.chunk_size = chunk_size
        self.max_workers = max_workers or min(4, mp.cpu_count())
        self.temp_dir = tempfile.gettempdir()
    
    def process_large_csv(self, file_path: str, field_mapping: Dict[str, int], 
                         delimiter: str = ",", encoding: str = "utf-8") -> Iterator[List[Dict[str, Any]]]:
        """Procesar archivo CSV grande en chunks"""
        
        try:
            with open(file_path, 'r', encoding=encoding, newline='') as file:
                # Detectar dialecto CSV
                sample = file.read(1024)
                file.seek(0)
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample, delimiters=delimiter)
                
                reader = csv.reader(file, dialect)
                
                # Saltar headers si existen
                next(reader, None)
                
                chunk = []
                row_count = 0
                
                for row in reader:
                    if len(row) < max(field_mapping.values()) + 1:
                        continue  # Saltar filas incompletas
                    
                    # Mapear campos según configuración
                    mapped_row = {}
                    for field_name, column_index in field_mapping.items():
                        if column_index < len(row):
                            mapped_row[field_name] = row[column_index].strip()
                    
                    chunk.append(mapped_row)
                    row_count += 1
                    
                    # Yield chunk cuando alcance el tamaño
                    if len(chunk) >= self.chunk_size:
                        yield chunk
                        chunk = []
                
                # Yield último chunk si tiene datos
                if chunk:
                    yield chunk
                    
        except Exception as e:
            raise Exception(f"Error procesando archivo CSV: {str(e)}")
    
    def process_large_excel(self, file_path: str, field_mapping: Dict[str, int], 
                           sheet_name: str = 0) -> Iterator[List[Dict[str, Any]]]:
        """Procesar archivo Excel grande en chunks"""
        
        try:
            # Leer archivo en chunks usando pandas
            chunk_iter = pd.read_excel(
                file_path, 
                sheet_name=sheet_name,
                chunksize=self.chunk_size,
                header=0
            )
            
            for chunk_df in chunk_iter:
                chunk_data = []
                
                for _, row in chunk_df.iterrows():
                    # Mapear campos según configuración
                    mapped_row = {}
                    for field_name, column_index in field_mapping.items():
                        if column_index < len(row):
                            value = row.iloc[column_index]
                            # Manejar valores NaN
                            mapped_row[field_name] = str(value).strip() if pd.notna(value) else ""
                    
                    chunk_data.append(mapped_row)
                
                yield chunk_data
                
        except Exception as e:
            raise Exception(f"Error procesando archivo Excel: {str(e)}")
    
    def validate_chunk_parallel(self, chunks: List[ProcessingChunk], 
                               validation_rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validar chunks en paralelo"""
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(self._validate_single_chunk, chunk, validation_rules)
                for chunk in chunks
            ]
            
            results = []
            for future in futures:
                try:
                    result = future.result(timeout=30)  # 30 segundos timeout
                    results.append(result)
                except Exception as e:
                    results.append({
                        'success': False,
                        'error': str(e),
                        'chunk_id': getattr(future, 'chunk_id', 'unknown')
                    })
            
            return results
    
    def _validate_single_chunk(self, chunk: ProcessingChunk, 
                              validation_rules: Dict[str, Any]) -> Dict[str, Any]:
        """Validar un chunk individual"""
        
        errors = []
        valid_rows = []
        
        for i, row in enumerate(chunk.data):
            row_errors = []
            
            # Validar campos requeridos
            for required_field in validation_rules.get('required_fields', []):
                if not row.get(required_field) or row[required_field].strip() == "":
                    row_errors.append(f"Campo requerido '{required_field}' está vacío")
            
            # Validar formato de fecha
            date_fields = validation_rules.get('date_fields', {})
            for field_name, date_format in date_fields.items():
                if field_name in row and row[field_name]:
                    try:
                        datetime.strptime(row[field_name], date_format)
                    except ValueError:
                        row_errors.append(f"Formato de fecha inválido en '{field_name}': {row[field_name]}")
            
            # Validar campos numéricos
            numeric_fields = validation_rules.get('numeric_fields', [])
            for field_name in numeric_fields:
                if field_name in row and row[field_name]:
                    try:
                        float(row[field_name].replace(',', ''))
                    except ValueError:
                        row_errors.append(f"Valor numérico inválido en '{field_name}': {row[field_name]}")
            
            if row_errors:
                errors.append({
                    'row': chunk.start_row + i,
                    'errors': row_errors,
                    'data': row
                })
            else:
                valid_rows.append(row)
        
        return {
            'success': True,
            'chunk_id': chunk.chunk_id,
            'valid_rows': valid_rows,
            'errors': errors,
            'processed_count': len(chunk.data),
            'valid_count': len(valid_rows),
            'error_count': len(errors)
        }
    
    def detect_duplicates_optimized(self, data_chunks: List[List[Dict[str, Any]]], 
                                   duplicate_fields: List[str]) -> List[Dict[str, Any]]:
        """Detectar duplicados de manera optimizada usando hashing"""
        
        seen_hashes = set()
        duplicates = []
        
        for chunk_idx, chunk in enumerate(data_chunks):
            for row_idx, row in enumerate(chunk):
                # Crear hash basado en campos de duplicación
                hash_data = []
                for field in duplicate_fields:
                    value = row.get(field, "").strip().lower()
                    hash_data.append(value)
                
                row_hash = hashlib.md5("|".join(hash_data).encode()).hexdigest()
                
                if row_hash in seen_hashes:
                    duplicates.append({
                        'chunk_index': chunk_idx,
                        'row_index': row_idx,
                        'hash': row_hash,
                        'data': row,
                        'duplicate_fields': {field: row.get(field) for field in duplicate_fields}
                    })
                else:
                    seen_hashes.add(row_hash)
        
        return duplicates
    
    def create_processing_summary(self, file_path: str, processing_results: List[Dict[str, Any]], 
                                 duplicates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Crear resumen del procesamiento"""
        
        # Calcular estadísticas
        total_processed = sum(result.get('processed_count', 0) for result in processing_results)
        total_valid = sum(result.get('valid_count', 0) for result in processing_results)
        total_errors = sum(result.get('error_count', 0) for result in processing_results)
        
        # Obtener información del archivo
        file_stats = os.stat(file_path)
        file_size_mb = file_stats.st_size / (1024 * 1024)
        
        # Agrupar errores por tipo
        error_summary = {}
        for result in processing_results:
            for error in result.get('errors', []):
                for error_msg in error.get('errors', []):
                    error_type = error_msg.split(':')[0] if ':' in error_msg else error_msg
                    error_summary[error_type] = error_summary.get(error_type, 0) + 1
        
        return {
            'file_info': {
                'path': file_path,
                'size_mb': round(file_size_mb, 2),
                'modified_date': datetime.fromtimestamp(file_stats.st_mtime).isoformat()
            },
            'processing_stats': {
                'total_rows_processed': total_processed,
                'valid_rows': total_valid,
                'error_rows': total_errors,
                'duplicate_rows': len(duplicates),
                'success_rate': (total_valid / max(1, total_processed)) * 100,
                'chunks_processed': len(processing_results)
            },
            'error_summary': error_summary,
            'duplicate_summary': {
                'count': len(duplicates),
                'sample_duplicates': duplicates[:5] if duplicates else []
            },
            'performance_metrics': {
                'processing_time_estimate': total_processed / 1000,  # Estimación simple
                'rows_per_second': 1000,  # Estimación
                'memory_efficient': True
            }
        }

class StreamingCSVProcessor:
    """Procesador de CSV que usa streaming para archivos muy grandes"""
    
    def __init__(self, buffer_size: int = 8192):
        self.buffer_size = buffer_size
    
    def process_streaming(self, file_path: str, field_mapping: Dict[str, int], 
                         callback_func, delimiter: str = ",") -> Dict[str, Any]:
        """Procesar archivo CSV usando streaming"""
        
        processed_count = 0
        error_count = 0
        start_time = datetime.now()
        
        try:
            with open(file_path, 'r', encoding='utf-8', buffering=self.buffer_size) as file:
                reader = csv.reader(file, delimiter=delimiter)
                
                # Saltar header
                next(reader, None)
                
                batch = []
                batch_size = 100
                
                for row_num, row in enumerate(reader, 1):
                    try:
                        # Mapear campos
                        mapped_row = {}
                        for field_name, column_index in field_mapping.items():
                            if column_index < len(row):
                                mapped_row[field_name] = row[column_index].strip()
                        
                        batch.append(mapped_row)
                        processed_count += 1
                        
                        # Procesar batch cuando esté lleno
                        if len(batch) >= batch_size:
                            callback_func(batch)
                            batch = []
                        
                    except Exception as e:
                        error_count += 1
                        print(f"Error procesando fila {row_num}: {str(e)}")
                
                # Procesar último batch
                if batch:
                    callback_func(batch)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'success': True,
                'processed_count': processed_count,
                'error_count': error_count,
                'processing_time_seconds': processing_time,
                'rows_per_second': processed_count / max(1, processing_time)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processed_count': processed_count,
                'error_count': error_count
            }

# Funciones de utilidad para optimización
def estimate_processing_time(file_size_mb: float, rows_per_mb: int = 10000) -> Dict[str, Any]:
    """Estimar tiempo de procesamiento basado en el tamaño del archivo"""
    
    estimated_rows = file_size_mb * rows_per_mb
    
    # Estimaciones basadas en benchmarks
    processing_rates = {
        'small': {'max_mb': 10, 'rows_per_second': 5000},
        'medium': {'max_mb': 100, 'rows_per_second': 3000},
        'large': {'max_mb': 500, 'rows_per_second': 1500},
        'very_large': {'max_mb': float('inf'), 'rows_per_second': 800}
    }
    
    # Determinar categoría
    category = 'very_large'
    for cat, limits in processing_rates.items():
        if file_size_mb <= limits['max_mb']:
            category = cat
            break
    
    rate = processing_rates[category]['rows_per_second']
    estimated_time_seconds = estimated_rows / rate
    
    return {
        'file_size_mb': file_size_mb,
        'estimated_rows': int(estimated_rows),
        'category': category,
        'estimated_time_seconds': estimated_time_seconds,
        'estimated_time_minutes': estimated_time_seconds / 60,
        'processing_rate': rate,
        'recommendations': _get_processing_recommendations(category, file_size_mb)
    }

def _get_processing_recommendations(category: str, file_size_mb: float) -> List[str]:
    """Obtener recomendaciones de procesamiento"""
    
    recommendations = []
    
    if category == 'large' or category == 'very_large':
        recommendations.append("Usar procesamiento en chunks para optimizar memoria")
        recommendations.append("Considerar procesamiento en background")
    
    if file_size_mb > 100:
        recommendations.append("Validar archivo antes de importación completa")
        recommendations.append("Implementar progreso de importación para el usuario")
    
    if file_size_mb > 500:
        recommendations.append("Considerar dividir archivo en múltiples importaciones")
        recommendations.append("Usar procesamiento paralelo si es posible")
    
    return recommendations