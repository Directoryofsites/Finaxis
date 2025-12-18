import sys
import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

# Mock Setup
Base = declarative_base()

class PlanCuenta(Base):
    __tablename__ = 'plan_cuentas'
    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer)
    codigo = Column(String)
    nombre = Column(String)
    cuenta_padre_id = Column(Integer, ForeignKey('plan_cuentas.id'), nullable=True)
    permite_movimiento = Column(Boolean, default=False)
    nivel = Column(Integer)

class MovimientoContable(Base):
    __tablename__ = 'movimientos_contables'
    id = Column(Integer, primary_key=True)
    cuenta_id = Column(Integer)
    documento_id = Column(Integer)

class Documento(Base):
    __tablename__ = 'documentos'
    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer)

class TasaImpuesto(Base):
    __tablename__ = 'tasas_impuesto'
    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer)
    cuenta_id = Column(Integer) # Venta
    cuenta_iva_descontable_id = Column(Integer) # Compra

class TipoDocumento(Base):
    __tablename__ = 'tipos_documento'
    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer)
    cuenta_debito_cxc_id = Column(Integer)
    cuenta_credito_cxc_id = Column(Integer)
    cuenta_debito_cxp_id = Column(Integer)
    cuenta_credito_cxp_id = Column(Integer)

# In-memory DB
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db = Session()

# Create Hierarchy
# 1 (Root) -> 11 -> 1110 -> 111001 (Mov), 111002 (No Mov, but Configured)
c1 = PlanCuenta(id=1, empresa_id=1, codigo="1", nombre="ACTIVO", nivel=1, cuenta_padre_id=None)
c11 = PlanCuenta(id=2, empresa_id=1, codigo="11", nombre="DISPONIBLE", nivel=2, cuenta_padre_id=1)
c1110 = PlanCuenta(id=3, empresa_id=1, codigo="1110", nombre="BANCOS", nivel=3, cuenta_padre_id=2)
c111001 = PlanCuenta(id=4, empresa_id=1, codigo="111001", nombre="BANCO 1", nivel=4, cuenta_padre_id=3, permite_movimiento=True)
c111002 = PlanCuenta(id=5, empresa_id=1, codigo="111002", nombre="BANCO 2", nivel=4, cuenta_padre_id=3, permite_movimiento=True)

db.add_all([c1, c11, c1110, c111001, c111002])
db.commit()

# Add Movement to 111001
doc = Documento(id=1, empresa_id=1)
mov = MovimientoContable(id=1, cuenta_id=4, documento_id=1)
db.add_all([doc, mov])

# Add Configuration for 111002 (TasaImpuesto)
impuesto = TasaImpuesto(id=1, empresa_id=1, cuenta_id=5, cuenta_iva_descontable_id=5)
db.add(impuesto)
db.commit()

def _identificar_cuentas_borrables(db, cuenta_id, empresa_id):
    todas_las_cuentas_empresa = db.query(PlanCuenta).filter(PlanCuenta.empresa_id == empresa_id).all()
    cuentas_map = {c.id: c for c in todas_las_cuentas_empresa}
    
    # Mapa inverso: Código -> ID (para buscar ancestros por código)
    codigo_to_id = {c.codigo: c.id for c in todas_las_cuentas_empresa}
    
    if cuenta_id not in cuentas_map:
        return set(), set() # Cuenta no encontrada
        
    cuenta_raiz = cuentas_map[cuenta_id]
    codigo_raiz = str(cuenta_raiz.codigo)
    
    # 1. Identificar todos los descendientes (incluyendo la cuenta misma) usando PREFIJO DE CÓDIGO
    descendientes_ids = set()
    for c in todas_las_cuentas_empresa:
        if str(c.codigo).startswith(codigo_raiz):
            descendientes_ids.add(c.id)
            
    # --- PROTECCIÓN DE CONFIGURACIÓN (FKs) ---
    ids_protegidos = set()
    
    # A. Cuentas con Movimientos
    cuentas_con_movimiento_q = db.query(MovimientoContable.cuenta_id).join(
        Documento, MovimientoContable.documento_id == Documento.id
    ).filter(
        Documento.empresa_id == empresa_id,
        MovimientoContable.cuenta_id.in_(list(descendientes_ids))
    ).distinct().all()
    ids_protegidos.update({item[0] for item in cuentas_con_movimiento_q})
    
    # B. Cuentas usadas en Impuestos (TasaImpuesto)
    impuestos_q = db.query(TasaImpuesto.cuenta_id, TasaImpuesto.cuenta_iva_descontable_id).filter(
        TasaImpuesto.empresa_id == empresa_id
    ).all()
    for t in impuestos_q:
        if t.cuenta_id in descendientes_ids: ids_protegidos.add(t.cuenta_id)
        if t.cuenta_iva_descontable_id in descendientes_ids: ids_protegidos.add(t.cuenta_iva_descontable_id)
        
    # C. Cuentas usadas en Tipos de Documento
    tipos_doc_q = db.query(
        TipoDocumento.cuenta_debito_cxc_id, TipoDocumento.cuenta_credito_cxc_id,
        TipoDocumento.cuenta_debito_cxp_id, TipoDocumento.cuenta_credito_cxp_id
    ).filter(TipoDocumento.empresa_id == empresa_id).all()
    
    for td in tipos_doc_q:
        if td.cuenta_debito_cxc_id in descendientes_ids: ids_protegidos.add(td.cuenta_debito_cxc_id)
        if td.cuenta_credito_cxc_id in descendientes_ids: ids_protegidos.add(td.cuenta_credito_cxc_id)
        if td.cuenta_debito_cxp_id in descendientes_ids: ids_protegidos.add(td.cuenta_debito_cxp_id)
        if td.cuenta_credito_cxp_id in descendientes_ids: ids_protegidos.add(td.cuenta_credito_cxp_id)

    # 3. Identificar cuentas a conservar (las protegidas + sus ancestros)
    cuentas_a_conservar_ids = set(ids_protegidos)
    
    # Para cada cuenta protegida, salvamos a todos sus "padres lógicos" (por código)
    for id_protegido in ids_protegidos:
        cuenta_prot = cuentas_map.get(id_protegido)
        if not cuenta_prot: continue
        
        codigo_actual = str(cuenta_prot.codigo)
        
        # Subimos quitando caracteres hasta llegar a la longitud del código raíz
        while len(codigo_actual) >= len(codigo_raiz):
            if codigo_actual in codigo_to_id:
                ancestor_id = codigo_to_id[codigo_actual]
                if ancestor_id in descendientes_ids: 
                    cuentas_a_conservar_ids.add(ancestor_id)
            codigo_actual = codigo_actual[:-1]
                
    # 4. Las que se pueden borrar son: Todos los descendientes - Las que se deben conservar
    cuentas_a_eliminar_ids = descendientes_ids - cuentas_a_conservar_ids
    
    return cuentas_a_eliminar_ids, cuentas_a_conservar_ids

# Run Test
eliminar, conservar = _identificar_cuentas_borrables(db, 1, 1)

print(f"Eliminar IDs: {eliminar}")
print(f"Conservar IDs: {conservar}")

# Expected: Eliminar {} (None). Conservar {1, 2, 3, 4, 5} (All)
# 4 preserved by Movement. 5 preserved by TasaImpuesto.
expected_conservar = {1, 2, 3, 4, 5}
if conservar == expected_conservar:
    print("SUCCESS: Logic works with Movements AND Configuration.")
else:
    print(f"FAILURE: Expected to preserve {expected_conservar}, but got {conservar}")

