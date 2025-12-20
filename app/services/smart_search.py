from typing import Dict, Any, List

class SmartSearchDispatcher:
    """
    Servicio de reconocimiento de intenciones para 'Smart Search'.
    Analiza una consulta en lenguaje natural y determina la acción a realizar.
    """

    @staticmethod
    def process_query(query: str) -> Dict[str, Any]:
        """
        Procesa la consulta y retorna una acción estructurada.
        
        Args:
            query (str): La consulta del usuario (ej: "Ver facturas de venta").

        Returns:
            Dict: {
                "action": "NAVIGATE" | "TOAST" | "UNKNOWN",
                "target": "/ruta/destino" (si aplica),
                "message": "Mensaje para el usuario" (opcional)
            }
        """
        query_lower = query.lower().strip()

        # -----------------------------------------------
        # 1. REGLAS DE NAVEGACIÓN (INTENT RECOGNITION)
        # -----------------------------------------------

        # --- FACTURACIÓN Y VENTAS ---
        if any(w in query_lower for w in ['factura', 'venta', 'facturación']):
            if 'crear' in query_lower or 'nueva' in query_lower:
                 # TODO: Definir ruta de creación si existe, por ahora listado
                return {
                    "action": "NAVIGATE",
                    "target": "/contabilidad/documentos",
                    "message": "Abriendo gestión de facturas..."
                }
            return {
                "action": "NAVIGATE",
                "target": "/contabilidad/documentos",
                "message": "Navegando a Facturas de Venta..."
            }

        # --- CLIENTES / TERCEROS ---
        if any(w in query_lower for w in ['cliente', 'tercero', 'proveedor']):
            return {
                "action": "NAVIGATE",
                "target": "/admin/terceros",
                "message": "Abriendo directorio de Terceros..."
            }

        # --- ANÁLISIS FINANCIERO / DASHBOARD ---
        if any(w in query_lower for w in ['analisis', 'financiero', 'ratio', 'indicador', 'balance']):
            return {
                "action": "NAVIGATE",
                "target": "/?module=analisis_financiero",
                "message": "Accediendo al Módulo de Análisis Financiero..."
            }

        # --- CONTABILIDAD GENERAL ---
        if 'puc' in query_lower or 'cuentas' in query_lower:
            return {
                "action": "NAVIGATE",
                "target": "/contabilidad/puc",
                "message": "Abriendo Plan Único de Cuentas (PUC)..."
            }
        
        if 'comprobante' in query_lower:
             return {
                "action": "NAVIGATE",
                "target": "/contabilidad/asientos",
                "message": "Navegando a Comprobantes Contables..."
            }

        # --- NÓMINA ---
        if any(w in query_lower for w in ['nomina', 'empleado', 'liquidar']):
            return {
                "action": "NAVIGATE",
                "target": "/nomina/liquidar", # Asumiendo ruta
                "message": "Navegando al módulo de Nómina..."
            }

        # --- SALUDO / CONVERSACIONAL (Placeholder AI) ---
        if any(w in query_lower for w in ['hola', 'buenos dias', 'ayuda']):
            return {
                "action": "TOAST",
                "target": None,
                "message": "¡Hola! Soy Finaxis AI. Escribe qué deseas hacer, como 'Ver facturas' o 'Analizar finanzas'."
            }

        # -----------------------------------------------
        # DEFAULT: NO ENTENDIDO
        # -----------------------------------------------
        return {
            "action": "UNKNOWN",
            "target": None,
            "message": "No estoy seguro de qué hacer. Prueba con 'Ver Facturas' o 'Análisis Financiero'."
        }
