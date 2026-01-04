from sqlalchemy.orm import Session
from app.models import PlanCuenta, Tercero, TipoDocumento, Empresa

class ImportUtils:

    @staticmethod
    def get_clase(code: str) -> int:
        if not code or not code[0].isdigit(): return 0
        return int(code[0])

    @staticmethod
    def get_puc_level(code: str) -> int:
        """
        Calcula el nivel de la cuenta según estándar PUC Colombia.
        1 dígito = Nivel 1 (Clase)
        2 dígitos = Nivel 2 (Grupo)
        4 dígitos = Nivel 3 (Cuenta)
        6 dígitos = Nivel 4 (Subcuenta)
        8+ dígitos = Nivel 5 (Auxiliar)
        """
        l = len(code)
        if l == 1: return 1
        if l == 2: return 2
        if l == 4: return 3
        if l == 6: return 4
        if l >= 8: return 5
        return l

    @staticmethod
    def get_parent_code(code: str) -> str | None:
        if len(code) > 8: return code[:-2] # 10 -> 8
        if len(code) == 8: return code[:-2] # 8 -> 6
        if len(code) == 6: return code[:-2] # 6 -> 4
        if len(code) == 4: return code[:-2] # 4 -> 2
        if len(code) == 2: return code[0]   # 2 -> 1
        return None

    @staticmethod
    def ensure_account_hierarchy(db: Session, empresa_id: int, code: str, name: str) -> int | None:
        """
        Asegura que la cuenta y TODOS sus padres existan en la base de datos.
        Retorna el ID de la cuenta solicitada.
        """
        # 1. Identificar toda la cadena de ancestros
        chain = []
        curr = code
        while curr:
            chain.append(curr)
            curr = ImportUtils.get_parent_code(curr)
        chain.reverse() # Ordenar: 1, 11, 1105...

        parent_id = None
        target_id = None

        num_created = 0
        for c in chain:
            existing = db.query(PlanCuenta).filter_by(empresa_id=empresa_id, codigo=c).first()
            
            if not existing:
                try:
                    with db.begin_nested(): # Savepoint para evitar rollback de toda la transaccion
                        # Determinar nombre (Genérico si es un padre autogenerado)
                        current_name = name if c == code else f"CUENTA GENERADA {c}"
                        
                        level = ImportUtils.get_puc_level(c)
                        
                        new_acc = PlanCuenta(
                            empresa_id=empresa_id,
                            codigo=c,
                            nombre=current_name,
                            nivel=level,
                            permite_movimiento=(len(c) >= 6),
                            clase=ImportUtils.get_clase(c),
                            cuenta_padre_id=parent_id
                        )
                        db.add(new_acc)
                        db.flush()
                        parent_id = new_acc.id
                        num_created += 1
                except Exception:
                    # Si falla, el nested rollback ya ocurrió.
                    # Intentamos recuperar buscando la cuenta (pudo ser creada por otro proceso)
                    rec = db.query(PlanCuenta).filter_by(empresa_id=empresa_id, codigo=c).first()
                    if rec:
                        parent_id = rec.id
            else:
                # Si existe, actualizamos su padre si falta (reparación de jerarquía)
                if parent_id and existing.cuenta_padre_id != parent_id:
                    existing.cuenta_padre_id = parent_id
                    db.add(existing)
                    db.flush()
                parent_id = existing.id
            
            if c == code:
                target_id = parent_id

        return target_id, num_created

    @staticmethod
    def ensure_tercero_exists(db: Session, empresa_id: int, nit: str, nombre: str, default_id: int = None) -> int:
        """
        Busca o crea un Tercero. Retorna su ID.
        Si falla y se provee default_id, retorna eso.
        """
        nit_clean = nit.strip() if nit else ""
        nombre_clean = nombre.strip().upper() if nombre else ""

        if not nit_clean: 
            # Si no hay NIT, intentar buscar por Nombre
            if nombre_clean:
                by_name = db.query(Tercero).filter_by(empresa_id=empresa_id, razon_social=nombre_clean).first()
                if by_name: return by_name.id, False
                # Si no existe por nombre, generamos un NIT ficticio basado en el nombre para poder crearlo
                # Ej: "GEN-JAIME MUNOZ"
                import re
                safe_name = re.sub(r'[^A-Z0-9]', '', nombre_clean)[:15]
                nit_clean = f"GEN-{safe_name}"
            else:
                return default_id, False
        
        existing = db.query(Tercero).filter_by(empresa_id=empresa_id, nit=nit_clean).first()
        if existing:
             return existing.id, False
             
        # Crear
        try:
            with db.begin_nested():
                new_tp = Tercero(
                    empresa_id=empresa_id,
                    nit=nit_clean,
                    razon_social=nombre.strip(),
                    es_cliente=True,
                    es_proveedor=True
                )
                db.add(new_tp)
                db.flush()
                return new_tp.id, True
        except:
             # Nested rollback autocalled
             rec = db.query(Tercero).filter_by(empresa_id=empresa_id, nit=nit_clean).first()
             return (rec.id, False) if rec else (default_id, False)

    @staticmethod
    def ensure_tipo_documento_exists(db: Session, empresa_id: int, codigo: str = None, nombre: str = None) -> int:
        """
        Busca o crea un Tipo de Documento usando Código y/o Nombre.
        Prioriza búsqueda por Nombre exacto para evitar duplicados semánticos.
        Prioriza búsqueda por Código si se provee.
        Si no existe, crea uno nuevo generando código si es necesario.
        """
        if not codigo and not nombre:
            return None
            
        codigo = codigo.strip().upper() if codigo else None
        nombre = nombre.strip() if nombre else None

        # 1. Buscar por NOMBRE (Prioridad Semántica)
        # Esto conecta "Recibo de Caja" (Excel) con "RC" (Sistema) si "Recibo de Caja" es el nombre en sistema.
        if nombre:
            existing_by_name = db.query(TipoDocumento).filter(
                TipoDocumento.empresa_id == empresa_id,
                TipoDocumento.nombre.ilike(nombre) 
            ).first()
            if existing_by_name:
                return existing_by_name.id

        # 2. Buscar por CÓDIGO (Prioridad de Identificador)
        if codigo:
            # Validacion anti-basura: Si el codigo es muy largo (>5) y NO hay nombre,
            # asumimos que el usuario mapeo "Nombre" en "Codigo" por error.
            # En ese caso, tratamos 'codigo' como 'nombre' para la generacion, pero no buscamos por codigo.
            if len(codigo) > 5 and not nombre:
                # Recursión tratando el codigo como nombre
                return ImportUtils.ensure_tipo_documento_exists(db, empresa_id, codigo=None, nombre=codigo)
            
            existing_by_code = db.query(TipoDocumento).filter_by(empresa_id=empresa_id, codigo=codigo[:5]).first()
            if existing_by_code:
                # Si encontramos por código pero traía nombre, actualizamos el nombre si era genérico
                if nombre and existing_by_code.nombre.startswith("TIPO IMPORTADO"):
                    existing_by_code.nombre = nombre
                    db.add(existing_by_code)
                    db.flush()
                return existing_by_code.id

        # 3. CREACIÓN (Si no se encontró)
        # Definir Código y Nombre Finales
        final_code = codigo
        final_name = nombre

        # Caso A: Solo tengo Nombre -> Generar Código
        if not final_code and final_name:
            # Generar código: Ej: "Recibo de Caja" -> "RC", "Comprobante" -> "CO"
            words = final_name.split()
            if len(words) >= 2:
                final_code = (words[0][0] + words[1][0]).upper()
            else:
                final_code = final_name[:2].upper()
            
            # Verificar colisión de código generado
            collision = db.query(TipoDocumento).filter_by(empresa_id=empresa_id, codigo=final_code).first()
            if collision:
                final_code = final_name[:3].upper() # Intentar con 3 letras
        
        # Caso B: Solo tengo Código -> Usar como Nombre
        if not final_name and final_code:
             final_name = f"DOCUMENTO {final_code}"

        # Truncar código final a 5 chars (limite DB típico)
        final_code = final_code[:5] if final_code else "GEN"

        try:
            with db.begin_nested():
                new_td = TipoDocumento(
                    empresa_id=empresa_id,
                    codigo=final_code,
                    nombre=final_name,
                    consecutivo_actual=0
                )
                db.add(new_td)
                db.flush()
                return new_td.id
        except Exception as e:
            # Posible carrera o error DB
            rec = db.query(TipoDocumento).filter_by(empresa_id=empresa_id, codigo=final_code).first()
            return rec.id if rec else None
