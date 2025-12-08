from sqlalchemy.orm import Session
from app.models.plan_cuenta import PlanCuenta
from app.models.empresa import Empresa

def seed_puc_simplificado(db: Session, empresa_id: int):
    """
    Crea las cuentas del PUC simplificado para pruebas de IVA si no existen.
    
    Estructura Simplificada:
    1. ACTIVO -> 13. CXC -> 1355 (Anticipo Imptos) -> 135505 (IVA Desc 19), 135510 (IVA Desc 5)
    2. PASIVO -> 24. Imptos x Pagar -> 2408 (IVA) -> 240801 (Gen 19), 240802 (Gen 5)
    4. INGRESOS -> 41. Operacionales -> 4135 (Comercio) -> 413501 (Vta 19), 413502 (Vta 5)
    6. COSTOS -> 61. Costo Ventas -> 6135 (Comercio) -> 613501 (Cumpra 19), 613502 (Cumpra 5)
    """
    
    # Lista de cuentas a asegurar
    cuentas = [
        # --- ACTIVO (IVA Descontable) ---
        {"codigo": "135515", "nombre": "IVA Descontable", "nivel": 4, "padre": "1355"}, # Padre asume que existe o se crea
        {"codigo": "13551501", "nombre": "IVA Descontable 19%", "nivel": 5, "padre": "135515", "permite_movimiento": True},
        {"codigo": "13551502", "nombre": "IVA Descontable 5%", "nivel": 5, "padre": "135515", "permite_movimiento": True},
        
        # --- PASIVO (IVA Generado) ---
        {"codigo": "2408", "nombre": "Impuesto sobre las ventas por pagar", "nivel": 4, "padre": "24"},
        {"codigo": "240801", "nombre": "IVA Generado 19%", "nivel": 5, "padre": "2408", "permite_movimiento": True},
        {"codigo": "240802", "nombre": "IVA Generado 5%", "nivel": 5, "padre": "2408", "permite_movimiento": True},
        
        # --- INGRESOS (Ventas) ---
        {"codigo": "4135", "nombre": "Comercio al por mayor y menor", "nivel": 4, "padre": "41"},
        {"codigo": "413501", "nombre": "Ventas Gravadas 19%", "nivel": 5, "padre": "4135", "permite_movimiento": True, "es_cuenta_de_ingresos": True},
        {"codigo": "413502", "nombre": "Ventas Gravadas 5%", "nivel": 5, "padre": "4135", "permite_movimiento": True, "es_cuenta_de_ingresos": True},
        {"codigo": "413503", "nombre": "Ventas Exentas", "nivel": 5, "padre": "4135", "permite_movimiento": True, "es_cuenta_de_ingresos": True},
        {"codigo": "413504", "nombre": "Ventas Excluidas", "nivel": 5, "padre": "4135", "permite_movimiento": True, "es_cuenta_de_ingresos": True},

        # --- COSTOS (Compras) ---
        {"codigo": "6135", "nombre": "Costo de Ventas - Comercio", "nivel": 4, "padre": "61"},
        {"codigo": "613501", "nombre": "Compras Gravadas 19%", "nivel": 5, "padre": "6135", "permite_movimiento": True},
        {"codigo": "613502", "nombre": "Compras Gravadas 5%", "nivel": 5, "padre": "6135", "permite_movimiento": True},
        
        # --- PASIVO (Retención en la Fuente) ---
        {"codigo": "2365", "nombre": "Retención en la fuente", "nivel": 4, "padre": "23"},
        {"codigo": "236505", "nombre": "ReteFuente Salarios", "nivel": 5, "padre": "2365", "permite_movimiento": True},
        {"codigo": "236515", "nombre": "ReteFuente Honorarios", "nivel": 5, "padre": "2365", "permite_movimiento": True},
        {"codigo": "236525", "nombre": "ReteFuente Servicios", "nivel": 5, "padre": "2365", "permite_movimiento": True},
        {"codigo": "236530", "nombre": "ReteFuente Arrendamientos", "nivel": 5, "padre": "2365", "permite_movimiento": True},
        {"codigo": "236540", "nombre": "ReteFuente Compras", "nivel": 5, "padre": "2365", "permite_movimiento": True},
    ]

    print("--- SEMBRANDO PUC SIMPLIFICADO ---")
    
    # 1. Asegurar padres de alto nivel (Simplificación: Asumimos que 1, 2, 4, 6, 13, 24, 41, 61 existen o los creamos rápido)
    # En un sistema real esto es más complejo, aqui hacemos un 'best effort'
    padres_basicos = [
        {"codigo": "1", "nombre": "ACTIVO", "nivel": 1, "padre": None},
        {"codigo": "2", "nombre": "PASIVO", "nivel": 1, "padre": None},
        {"codigo": "4", "nombre": "INGRESOS", "nivel": 1, "padre": None},
        {"codigo": "6", "nombre": "COSTOS", "nivel": 1, "padre": None},
        {"codigo": "13", "nombre": "DEUDORES", "nivel": 2, "padre": "1"},       # Corregido nivel padre
        {"codigo": "1355", "nombre": "ANTICIPO IMPUESTOS", "nivel": 3, "padre": "13"},  # Corregido nivel padre
        {"codigo": "23", "nombre": "CUENTAS POR PAGAR", "nivel": 2, "padre": "2"}, # Nuevo Padre
        {"codigo": "24", "nombre": "IMPUESTOS POR PAGAR", "nivel": 2, "padre": "2"},
        {"codigo": "41", "nombre": "OPERACIONALES", "nivel": 2, "padre": "4"},
        {"codigo": "61", "nombre": "COSTO VENTAS", "nivel": 2, "padre": "6"},
    ]
    
    # Combinar listas
    todos = padres_basicos + cuentas
    
    # Diccionario para buscar IDs de padres rápidamente
    # Primero cargamos lo que ya existe
    cuentas_existentes = db.query(PlanCuenta).filter(PlanCuenta.empresa_id == empresa_id).all()
    mapa_ids = {c.codigo: c.id for c in cuentas_existentes}

    count = 0
    for c_data in todos:
        codigo = c_data["codigo"]
        if codigo not in mapa_ids:
            # Buscar ID del padre
            padre_id = None
            if c_data["padre"]:
                 # El padre debería estar en mapa_ids porque ordenamos por nivel implícitamente al definir la lista
                 # (Padres primero). Si no está, hay un error de orden, pero aqui lo pusimos en orden.
                 padre_id = mapa_ids.get(c_data["padre"])
            
            nueva_cuenta = PlanCuenta(
                empresa_id=empresa_id,
                codigo=codigo,
                nombre=c_data["nombre"],
                nivel=c_data["nivel"],
                permite_movimiento=c_data.get("permite_movimiento", False),
                es_cuenta_de_ingresos=c_data.get("es_cuenta_de_ingresos", False),
                cuenta_padre_id=padre_id
            )
            db.add(nueva_cuenta)
            db.flush() # Para obtener ID
            mapa_ids[codigo] = nueva_cuenta.id
            count += 1
            print(f"Creada: {codigo} - {c_data['nombre']}")
    
    if count > 0:
        db.commit()
        print(f"Se crearon {count} cuentas nuevas.")
    else:
        print("El PUC simplificado ya estaba cargado.")

