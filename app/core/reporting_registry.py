from typing import Any, Dict, Optional, Type, Tuple
from sqlalchemy.orm import Session
from pydantic import BaseModel

class BaseReport:
    """
    Clase base abstracta para todos los reportes del sistema.
    Define la interfaz estándar que deben cumplir los reportes para ser
    invocados automáticamente por la IA, Servicios de Correo, etc.
    """
    key: str = "base_report"
    description: str = "Descripción base"
    
    # El esquema Pydantic usado para validar los filtros de este reporte
    filter_schema: Type[BaseModel] = None 

    def get_data(self, db: Session, empresa_id: int, filtros: BaseModel) -> Dict[str, Any]:
        """
        Obtiene los datos crudos del reporte (para JSON/Frontend).
        """
        raise NotImplementedError("Este reporte no implementa get_data")

    def generate_pdf(self, db: Session, empresa_id: int, filtros: BaseModel) -> Tuple[bytes, str]:
        """
        Genera el PDF del reporte.
        Retorna: (pdf_bytes, filename)
        """
        raise NotImplementedError("Este reporte no implementa generate_pdf")

class ReportRegistry:
    """
    Registro central (Singleton) de todos los reportes disponibles.
    """
    _registry: Dict[str, BaseReport] = {}

    @classmethod
    def register(cls, report_cls: Type[BaseReport]):
        """
        Decorador para registrar un reporte.
        Uso:
        @ReportRegistry.register
        class MiReporte(BaseReport): ...
        """
        instance = report_cls()
        if not instance.key:
            raise ValueError(f"El reporte {report_cls.__name__} debe tener una 'key' definida.")
        
        cls._registry[instance.key] = instance
        return report_cls

    @classmethod
    def get(cls, key: str) -> Optional[BaseReport]:
        """Obtiene una instancia de reporte por su clave."""
        return cls._registry.get(key)

    @classmethod
    def get_all(cls) -> Dict[str, BaseReport]:
        return cls._registry
