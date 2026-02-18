# scripts/init_lite_company.py
import sys
import os

# Añadir directorio raíz al path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from app.models.producto import Producto
from app.models.grupo_inventario import GrupoInventario
from app.models.plan_cuenta import PlanCuenta
from app.models.impuesto import TasaImpuesto
from app.services import empresa as empresa_service
from app.core import security

def init_lite_company(nit_empresa, saldo_inicial=10):
    db = SessionLocal()
    try:
        print(f"--- INICIALIZANDO EMPRESA EXPRESS (NIT: {nit_empresa}) ---")
        
        # 1. Buscar o Crear Empresa
        empresa = db.query(Empresa).filter(Empresa.nit == nit_empresa).first()
        if not empresa:
            print("Empresa no encontrada, creando nueva empresa de prueba...")
            empresa = Empresa(
                nit=nit_empresa,
                razon_social="EMPRESA LITE TEST",
                direccion="Calle Falsa 123",
                telefono="3001234567",
                email="lite@test.com",
                modo_operacion="LITE",
                is_lite_mode=True,
                saldo_facturas_venta=saldo_inicial,
                saldo_documentos_soporte=saldo_inicial,
                tipo_persona="1", # 1: Jurídica, 2: Natural
                regimen_fiscal="48", # 48: Impuesto sobre las ventas - IVA
                responsabilidad_fiscal="R-99-PN"
            )
            db.add(empresa)
            db.commit()
            print(f"Empresa creada con ID: {empresa.id}")
            
        else:
            # 2. Activar Modo Lite y Saldo (Solo si ya existía)
            print(f"Activando Modo Lite y asignando {saldo_inicial} facturas...")
            empresa.is_lite_mode = True
            empresa.saldo_facturas_venta = saldo_inicial
            empresa.saldo_documentos_soporte = saldo_inicial
            db.commit()
        
        # 3. Verificar/Crear "Shadow Configuration" (Cuentas y Grupos por Defecto)
        # Buscar cuenta de ingresos genérica (4135 o similar)
        cta_ingreso = db.query(PlanCuenta).filter(PlanCuenta.empresa_id == empresa.id, PlanCuenta.codigo.like('4135%')).first()
        if not cta_ingreso:
             print("Creando cuenta de ingreso genérica...")
             cta_ingreso = PlanCuenta(
                 empresa_id=empresa.id, 
                 codigo='41359501', 
                 nombre='INGRESOS SERVICIOS LITE', 
                 nivel=5, # Auxiliar
                 permite_movimiento=True,
                 es_cuenta_de_ingresos=True
             )
             db.add(cta_ingreso)
             db.commit()

        # Buscar grupo inventario por defecto
        grupo_defecto = db.query(GrupoInventario).filter(GrupoInventario.empresa_id == empresa.id, GrupoInventario.nombre == "GENERAL LITE").first()
        if not grupo_defecto:
            print("Creando Grupo de Inventario 'GENERAL LITE'...")
            # Necesitamos otras cuentas (Caja/Bancos para contrapartida se definen en TipoDoc, aqui grupo define Ingreso/Costo)
            # Para Lite de Servicios/Bienes sin inv, solo Ingreso es crítico, pero llenamos los demás con dummy o los mismos
            grupo_defecto = GrupoInventario(
                empresa_id=empresa.id, 
                nombre="GENERAL LITE",
                cuenta_ingreso_id=cta_ingreso.id,
                cuenta_inventario_id=cta_ingreso.id, # Hack: Apuntar a mismo si no se usa
                cuenta_costo_venta_id=cta_ingreso.id # Hack
            )
            db.add(grupo_defecto)
            db.commit()
            
        # 4. Crear Producto de Prueba (Bypass Inventario)
        prod_codigo = "EXPRESS-01"
        producto = db.query(Producto).filter(Producto.empresa_id == empresa.id, Producto.codigo == prod_codigo).first()
        if not producto:
            print(f"Creando Producto '{prod_codigo}' (Sin Control de Stock)...")
            
            # Buscar Impuesto 0% o 19%
            iva = db.query(TasaImpuesto).filter(TasaImpuesto.empresa_id == empresa.id).first()
            
            producto = Producto(
                empresa_id=empresa.id,
                codigo=prod_codigo,
                nombre="SERVICIO / PRODUCTO EXPRESS",
                es_servicio=False, # Es bien físico pero sin stock
                controlar_inventario=False, # <--- LA CLAVE
                grupo_id=grupo_defecto.id,
                impuesto_iva_id=iva.id if iva else None,
                precio_base_manual=10000,
                costo_promedio=5000
            )
            db.add(producto)
            db.commit()
        else:
            print(f"Actualizando producto '{prod_codigo}' a controlar_inventario=False...")
            producto.controlar_inventario = False
            db.commit()
            
        print("--- FINALIZADO CON ÉXITO ---")
        print(f"Empresa {empresa.razon_social} ahora es LITE.")
        print(f"Saldo Facturas: {empresa.saldo_facturas_venta}")
        print(f"Producto Prueba: {producto.nombre} (Control Inv: {producto.controlar_inventario})")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/init_lite_company.py [NIT_EMPRESA]")
    else:
        init_lite_company(sys.argv[1])
