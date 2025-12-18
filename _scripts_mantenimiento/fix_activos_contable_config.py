#!/usr/bin/env python3
# Script para configurar automáticamente las cuentas contables de activos fijos

from app.core.database import SessionLocal
from app.models.activo_categoria import ActivoCategoria
from app.models.plan_cuenta import PlanCuenta

def configurar_cuentas_activos_automatico():
    """
    Configura automáticamente las cuentas contables para las categorías de activos
    basándose en el plan de cuentas existente
    """
    db = SessionLocal()
    try:
        print("🔧 CONFIGURANDO CUENTAS CONTABLES PARA ACTIVOS FIJOS")
        
        # 1. Buscar cuentas típicas de activos fijos en el PUC
        cuentas_activo = db.query(PlanCuenta).filter(
            PlanCuenta.codigo.like('15%')  # Activos fijos
        ).all()
        
        cuentas_gasto_deprec = db.query(PlanCuenta).filter(
            PlanCuenta.codigo.like('51%')  # Gastos de depreciación
        ).all()
        
        cuentas_deprec_acum = db.query(PlanCuenta).filter(
            PlanCuenta.codigo.like('1592%')  # Depreciación acumulada
        ).all()
        
        print(f"📊 Cuentas encontradas:")
        print(f"   - Activos (15xx): {len(cuentas_activo)}")
        print(f"   - Gastos deprec (51xx): {len(cuentas_gasto_deprec)}")
        print(f"   - Deprec acumulada (1592xx): {len(cuentas_deprec_acum)}")
        
        # 2. Obtener categorías sin configurar
        categorias = db.query(ActivoCategoria).filter(
            ActivoCategoria.cuenta_activo_id.is_(None)
        ).all()
        
        print(f"\n🏷️  Categorías a configurar: {len(categorias)}")
        
        # 3. Configurar automáticamente
        for categoria in categorias:
            print(f"\n⚙️  Configurando: {categoria.nombre}")
            
            # Buscar cuentas más apropiadas por nombre
            if "equipo" in categoria.nombre.lower() or "oficina" in categoria.nombre.lower():
                # Equipos de oficina
                cuenta_activo = next((c for c in cuentas_activo if "equipo" in c.nombre.lower() or "oficina" in c.nombre.lower()), None)
                cuenta_gasto = next((c for c in cuentas_gasto_deprec if "equipo" in c.nombre.lower() or "oficina" in c.nombre.lower()), None)
                cuenta_acum = next((c for c in cuentas_deprec_acum if "equipo" in c.nombre.lower() or "oficina" in c.nombre.lower()), None)
            elif "vehiculo" in categoria.nombre.lower() or "auto" in categoria.nombre.lower():
                # Vehículos
                cuenta_activo = next((c for c in cuentas_activo if "vehiculo" in c.nombre.lower() or "transporte" in c.nombre.lower()), None)
                cuenta_gasto = next((c for c in cuentas_gasto_deprec if "vehiculo" in c.nombre.lower() or "transporte" in c.nombre.lower()), None)
                cuenta_acum = next((c for c in cuentas_deprec_acum if "vehiculo" in c.nombre.lower() or "transporte" in c.nombre.lower()), None)
            else:
                # Genérico - usar las primeras disponibles
                cuenta_activo = cuentas_activo[0] if cuentas_activo else None
                cuenta_gasto = cuentas_gasto_deprec[0] if cuentas_gasto_deprec else None
                cuenta_acum = cuentas_deprec_acum[0] if cuentas_deprec_acum else None
            
            # Asignar cuentas encontradas
            if cuenta_activo:
                categoria.cuenta_activo_id = cuenta_activo.id
                print(f"   ✅ Cuenta activo: {cuenta_activo.codigo} - {cuenta_activo.nombre}")
            
            if cuenta_gasto:
                categoria.cuenta_gasto_depreciacion_id = cuenta_gasto.id
                print(f"   ✅ Cuenta gasto: {cuenta_gasto.codigo} - {cuenta_gasto.nombre}")
            
            if cuenta_acum:
                categoria.cuenta_depreciacion_acumulada_id = cuenta_acum.id
                print(f"   ✅ Cuenta acumulada: {cuenta_acum.codigo} - {cuenta_acum.nombre}")
            
            if not (cuenta_activo and cuenta_gasto and cuenta_acum):
                print(f"   ⚠️  Configuración incompleta - faltan cuentas en el PUC")
        
        db.commit()
        print(f"\n✅ Configuración completada!")
        
        # 4. Verificar resultado
        categorias_configuradas = db.query(ActivoCategoria).filter(
            ActivoCategoria.cuenta_activo_id.isnot(None),
            ActivoCategoria.cuenta_gasto_depreciacion_id.isnot(None),
            ActivoCategoria.cuenta_depreciacion_acumulada_id.isnot(None)
        ).count()
        
        total_categorias = db.query(ActivoCategoria).count()
        
        print(f"📊 RESULTADO:")
        print(f"   - Categorías totales: {total_categorias}")
        print(f"   - Categorías configuradas: {categorias_configuradas}")
        print(f"   - Pendientes: {total_categorias - categorias_configuradas}")
        
        if categorias_configuradas == total_categorias:
            print("🎉 ¡Todas las categorías están configuradas!")
        else:
            print("⚠️  Algunas categorías necesitan configuración manual")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    configurar_cuentas_activos_automatico()