#!/usr/bin/env python3
# Script para crear las cuentas contables necesarias para activos fijos

from app.core.database import SessionLocal
from app.models.plan_cuenta import PlanCuenta
from app.models.activo_categoria import ActivoCategoria

def crear_cuentas_activos_fijos():
    """
    Crea las cuentas contables necesarias para el módulo de activos fijos
    """
    db = SessionLocal()
    try:
        print("🏗️  CREANDO CUENTAS CONTABLES PARA ACTIVOS FIJOS")
        
        # Obtener empresa_id (asumiendo que hay al menos una empresa)
        empresa_id = 1  # Ajustar según tu configuración
        
        # Cuentas a crear
        cuentas_nuevas = [
            # ACTIVOS FIJOS (Clase 1)
            {"codigo": "1504", "nombre": "EQUIPOS DE OFICINA", "nivel": 3, "permite_movimiento": False},
            {"codigo": "150405", "nombre": "Muebles y Enseres", "nivel": 4, "permite_movimiento": True},
            {"codigo": "150410", "nombre": "Equipos de Oficina", "nivel": 4, "permite_movimiento": True},
            {"codigo": "150415", "nombre": "Equipos de Computación", "nivel": 4, "permite_movimiento": True},
            
            {"codigo": "1540", "nombre": "FLOTA Y EQUIPO DE TRANSPORTE", "nivel": 3, "permite_movimiento": False},
            {"codigo": "154005", "nombre": "Autos, Camionetas", "nivel": 4, "permite_movimiento": True},
            {"codigo": "154010", "nombre": "Camiones", "nivel": 4, "permite_movimiento": True},
            {"codigo": "154015", "nombre": "Motocicletas", "nivel": 4, "permite_movimiento": True},
            
            # DEPRECIACIÓN ACUMULADA (Clase 1)
            {"codigo": "1592", "nombre": "DEPRECIACIÓN ACUMULADA", "nivel": 3, "permite_movimiento": False},
            {"codigo": "159205", "nombre": "Dep. Acum. Equipos de Oficina", "nivel": 4, "permite_movimiento": True},
            {"codigo": "159210", "nombre": "Dep. Acum. Equipos de Computación", "nivel": 4, "permite_movimiento": True},
            {"codigo": "159215", "nombre": "Dep. Acum. Flota y Equipo Transporte", "nivel": 4, "permite_movimiento": True},
            
            # GASTOS DE DEPRECIACIÓN (Clase 5)
            {"codigo": "5160", "nombre": "DEPRECIACIONES", "nivel": 3, "permite_movimiento": False},
            {"codigo": "516005", "nombre": "Depreciación Equipos de Oficina", "nivel": 4, "permite_movimiento": True},
            {"codigo": "516010", "nombre": "Depreciación Equipos de Computación", "nivel": 4, "permite_movimiento": True},
            {"codigo": "516015", "nombre": "Depreciación Flota y Equipo Transporte", "nivel": 4, "permite_movimiento": True},
        ]
        
        cuentas_creadas = 0
        
        for cuenta_data in cuentas_nuevas:
            # Verificar si ya existe
            existe = db.query(PlanCuenta).filter(
                PlanCuenta.codigo == cuenta_data["codigo"],
                PlanCuenta.empresa_id == empresa_id
            ).first()
            
            if not existe:
                nueva_cuenta = PlanCuenta(
                    empresa_id=empresa_id,
                    codigo=cuenta_data["codigo"],
                    nombre=cuenta_data["nombre"],
                    nivel=cuenta_data["nivel"],
                    permite_movimiento=cuenta_data["permite_movimiento"]
                )
                db.add(nueva_cuenta)
                cuentas_creadas += 1
                print(f"✅ Creada: {cuenta_data['codigo']} - {cuenta_data['nombre']}")
            else:
                print(f"⏭️  Ya existe: {cuenta_data['codigo']} - {cuenta_data['nombre']}")
        
        db.commit()
        print(f"\n🎉 Proceso completado: {cuentas_creadas} cuentas nuevas creadas")
        
        # Ahora configurar las categorías automáticamente
        print("\n🔧 CONFIGURANDO CATEGORÍAS AUTOMÁTICAMENTE...")
        
        configuraciones = [
            {
                "nombre": "Equ Oficina",
                "cuenta_activo": "150410",
                "cuenta_gasto": "516005", 
                "cuenta_acumulada": "159205"
            },
            {
                "nombre": "Autos",
                "cuenta_activo": "154005",
                "cuenta_gasto": "516015",
                "cuenta_acumulada": "159215"
            }
        ]
        
        for config in configuraciones:
            categoria = db.query(ActivoCategoria).filter(
                ActivoCategoria.nombre == config["nombre"]
            ).first()
            
            if categoria:
                # Buscar cuentas
                cuenta_activo = db.query(PlanCuenta).filter(
                    PlanCuenta.codigo == config["cuenta_activo"],
                    PlanCuenta.empresa_id == empresa_id
                ).first()
                
                cuenta_gasto = db.query(PlanCuenta).filter(
                    PlanCuenta.codigo == config["cuenta_gasto"],
                    PlanCuenta.empresa_id == empresa_id
                ).first()
                
                cuenta_acumulada = db.query(PlanCuenta).filter(
                    PlanCuenta.codigo == config["cuenta_acumulada"],
                    PlanCuenta.empresa_id == empresa_id
                ).first()
                
                # Asignar
                if cuenta_activo:
                    categoria.cuenta_activo_id = cuenta_activo.id
                if cuenta_gasto:
                    categoria.cuenta_gasto_depreciacion_id = cuenta_gasto.id
                if cuenta_acumulada:
                    categoria.cuenta_depreciacion_acumulada_id = cuenta_acumulada.id
                
                print(f"✅ Configurada categoría: {categoria.nombre}")
        
        db.commit()
        print("🎯 ¡Configuración de activos fijos completada!")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    crear_cuentas_activos_fijos()