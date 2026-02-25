import json

# Esquema oficial de Tools para OpenAI Function Calling
# Esto sustituye todas las explicaciones de texto de "cómo debe responder"

AI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "generar_auxiliar_cuenta",
            "description": "Genera el reporte auxiliar de una cuenta contable específica.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cuenta": {
                        "type": "string",
                        "description": "Nombre o código de la cuenta contable (Ej: 1105, Caja, Bancos)"
                    },
                    "fecha_inicio": {
                        "type": "string",
                        "description": "Fecha de inicio en formato YYYY-MM-DD. Dejar nulo si se quiere desde el inicio de la empresa."
                    },
                    "fecha_fin": {
                        "type": "string",
                        "description": "Fecha de fin en formato YYYY-MM-DD. Dejar nulo para usar la fecha actual de ser necesario."
                    },
                    "formato": {
                        "type": "string",
                        "enum": ["PDF", "Excel"],
                        "description": "Formato deseado del reporte. Por defecto PDF si no se especifica."
                    }
                },
                "required": ["cuenta"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generar_balance_prueba",
            "description": "Genera un balance de prueba general. Si no se especifica, asume nivel 7 de detalle. Esta función es para el balance general de comprobación.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nivel": {
                        "type": "integer",
                        "description": "Nivel de detalle del balance. Por defecto 7 (máximo).",
                        "default": 7
                    },
                    "fecha_inicio": {
                        "type": "string",
                        "description": "Fecha de inicio en formato YYYY-MM-DD."
                    },
                    "fecha_fin": {
                        "type": "string",
                        "description": "Fecha de fin en formato YYYY-MM-DD."
                    },
                    "formato": {
                        "type": "string",
                        "enum": ["PDF", "Excel"]
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generar_estado_situacion_financiera",
            "description": "Genera un balance general / estado de situación financiera cortado a una fecha.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fecha_corte": {
                        "type": "string",
                        "description": "Fecha de corte en formato YYYY-MM-DD. Dejar nulo para cierre de hoy."
                    },
                    "formato": {
                        "type": "string",
                        "enum": ["PDF", "Excel"]
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generar_estado_resultados",
            "description": "Genera un PyG / estado de resultados en un período de tiempo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fecha_inicio": {
                        "type": "string",
                        "description": "Fecha de inicio en formato YYYY-MM-DD."
                    },
                    "fecha_fin": {
                        "type": "string",
                        "description": "Fecha de fin en formato YYYY-MM-DD."
                    },
                    "formato": {
                        "type": "string",
                        "enum": ["PDF", "Excel"]
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generar_relacion_saldos",
            "description": "FUNCIÓN MAESTRA DE AUXILIARES Y SALDOS: Úsala siempre que el usuario pida 'Movimientos', 'Auxiliares', 'Saldos' o 'Relación de' cuentas, terceros, donaciones, ingresos, etc. Extrae cuidadosamente la cuenta principal mencionada (Ej: Donaciones, Servicios, Honorarios).",
            "parameters": {
                "type": "object",
                "properties": {
                    "vista": {
                        "type": "string",
                        "enum": ["por_cuenta", "por_tercero", "general"],
                        "description": "Si pide 'movimiento de donaciones y sus terceros' o 'terceros de la cuenta X', la vista es 'por_cuenta'. Si pide 'movimientos del tercero Juan por todas las cuentas', la vista es 'por_tercero'. 'general' por defecto."
                    },
                    "cuenta": {
                        "type": "string",
                        "description": "Nombre de la cuenta o concepto a buscar (Ej: Donaciones, Caja, Bancos, Ingresos por servicio). OMITIR la palabra 'cuenta', solo el nombre base."
                    },
                    "tercero": {
                        "type": "string",
                        "description": "Nombre o identificación del tercero (opcional)."
                    },
                    "fecha_inicio": {
                        "type": "string",
                        "description": "Fecha de inicio YYYY-MM-DD."
                    },
                    "fecha_fin": {
                        "type": "string",
                        "description": "Fecha de fin YYYY-MM-DD."
                    },
                    "formato": {
                        "type": "string",
                        "enum": ["PDF", "Excel"]
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_recurso_o_reporte",
            "description": "USAR SOLO SI NO ES NINGUNO DE LOS OTROS: Busca un nombre de reporte abstracto en la plataforma web.",
            "parameters": {
                "type": "object",
                "properties": {
                    "termino_busqueda": {
                        "type": "string",
                        "description": "Nombre coloquial del reporte. (Ej: Ventas por cliente, Kardex, Rentabilidad)"
                    },
                    "fecha_inicio": {
                        "type": "string"
                    },
                    "fecha_fin": {
                        "type": "string"
                    },
                    "fecha_corte": {
                        "type": "string"
                    },
                    "filtros": {
                        "type": "object",
                        "description": "Filtros adicionales extraídos (Ej: producto, centro de costo)",
                        "additionalProperties": {
                            "type": "string"
                        }
                    }
                },
                "required": ["termino_busqueda"]
            }
        }
    },
    {
         "type": "function",
         "function": {
             "name": "generar_auditoria_avanzada",
             "description": "Busca documentos o movimientos contables muy específicos mediante múltiples filtros (por mayor, menor, conceptos, tipos de documento, montos).",
             "parameters": {
                 "type": "object",
                 "properties": {
                    "tercero": {"type": "string"},
                    "valor_monto": {"type": "string"},
                    "valor_operador": {"type": "string", "enum": ["mayor", "menor", "igual"]},
                    "concepto": {"type": "string"},
                    "cuenta": {"type": "string"},
                    "centro_costo": {"type": "string"},
                    "producto": {"type": "string"},
                    "filtro_tipo_doc": {"type": "string"},
                    "numero": {"type": "string"},
                    "fecha_inicio": {"type": "string"},
                    "fecha_fin": {"type": "string"}
                 },
                 "required": []
             }
         }
    },
    {
         "type": "function",
         "function": {
             "name": "generar_auxiliar_cartera",
             "description": "Genera un auxiliar de cartera (Cuentas por cobrar) filtrado por cliente/tercero.",
             "parameters": {
                 "type": "object",
                 "properties": {
                     "tercero": {"type": "string"},
                     "vista": {"type": "string", "enum": ["facturas", "recibos"]},
                     "fecha_inicio": {"type": "string"},
                     "fecha_fin": {"type": "string"}
                 },
                 "required": []
             }
         }
    },
    {
         "type": "function",
         "function": {
             "name": "generar_auxiliar_proveedores",
             "description": "Genera un auxiliar de proveedores (Cuentas por pagar) filtrado por proveedor/tercero.",
             "parameters": {
                 "type": "object",
                 "properties": {
                     "tercero": {"type": "string"},
                     "vista": {"type": "string", "enum": ["facturas", "recibos"]},
                     "fecha_inicio": {"type": "string"},
                     "fecha_fin": {"type": "string"}
                 },
                 "required": []
             }
         }
    }
]
