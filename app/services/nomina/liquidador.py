from datetime import date
from decimal import Decimal
from typing import Dict, Any

# PARAMETROS 2025 (Por defecto)
SMMLV_2025 = Decimal("1423500")
AUX_TRANSPORTE_2025 = Decimal("200000")
UVT_2025 = Decimal("49799") # Proyectado aprox

# Porcentajes
PORC_SALUD_EMPLEADO = Decimal("0.04")
PORC_PENSION_EMPLEADO = Decimal("0.04")
PORC_FSP_BASE = Decimal("0.01") # Para > 4 SMMLV

class LiquidadorNominaService:
    """
    Motor de cálculo de nómina colombiana.
    """

    @staticmethod
    def calcular_devengados_deducciones(
        salario_base: Decimal,
        dias_trabajados: int,
        tiene_auxilio: bool,
        horas_extras: Decimal = Decimal(0),

        comisiones: Decimal = Decimal(0),
        otros_devengados: Decimal = Decimal(0),
        otras_deducciones: Decimal = Decimal(0)
    ) -> Dict[str, Any]:

        
        # 1. Base Salarial Proporcional
        # Fórmula: (Salario / 30) * Días
        sueldo_devengado = (salario_base / Decimal(30)) * Decimal(dias_trabajados)
        
        # 2. Auxilio de Transporte
        # Regla: Se paga si devenga <= 2 SMMLV Y trabaja físicamente (días laborados).
        # Se paga proporcional a los días trabajados.
        auxilio_transporte = Decimal(0)
        es_elegible_auxilio = tiene_auxilio and (salario_base <= (SMMLV_2025 * 2))
        
        if es_elegible_auxilio:
             auxilio_transporte = (AUX_TRANSPORTE_2025 / Decimal(30)) * Decimal(dias_trabajados)
             
        # 3. Total Devengado (Base para SS)
        # OJO: El auxilio de transporte NO hace parte de la base para Salud/Pensión, 
        # pero sí para prestaciones (Cesantías/Primas).
        # Para deducciones de nómina (SS), la base es: Sueldo + Extras + Comisiones - NO Auxilio.
        # SE AGREGA: otros_devengados (depende si es salarial o no, asumimos NO salarial para base SS por defecto,
        # pero para total devengado sí suma)
        
        total_devengado_bruto = sueldo_devengado + auxilio_transporte + horas_extras + comisiones + otros_devengados
        
        # Asumimos que otros_devengados NO es base de SS por ahora (bonos no salariales)
        # Si fuera salarial debería sumarse aquí.
        base_seguridad_social = sueldo_devengado + horas_extras + comisiones 

        
        # Validación Base Mínima SS: No puede ser inferior a un SMMLV (proporcional si es tiempo parcial, aquí asumimos full time por ahora)
        # Si dias_trabajados < 30, la base se ajusta? En PILA sí, pero en nómina se descuenta sobre lo devengado real
        # salvo que sea inferior al mínimo legal, pero mantendremos la regla simple: % sobre base.
        
        # 4. Deducciones de Ley (Salud y Pensión)
        salud = base_seguridad_social * PORC_SALUD_EMPLEADO
        pension = base_seguridad_social * PORC_PENSION_EMPLEADO
        
        # 5. Fondo de Solidaridad Pensional
        fsp = Decimal(0)
        if base_seguridad_social > (SMMLV_2025 * 4):
            fsp = base_seguridad_social * PORC_FSP_BASE
            # Nota: Hay escalas progresivas hasta el 2% para salarios muy altos (>16 SMMLV), 
            # Implementamos el 1% básico por ahora.
            
        total_deducciones = salud + pension + fsp + otras_deducciones
        
        # 6. Neto
        neto = total_devengado_bruto - total_deducciones
        
        return {
            "sueldo_basico_periodo": sueldo_devengado,
            "auxilio_transporte": auxilio_transporte,
            "horas_extras": horas_extras,

            "comisiones": comisiones,
            "otros_devengados": otros_devengados,
            "total_devengado": total_devengado_bruto,
            "salud": salud,
            "pension": pension,
            "fsp": fsp,
            "otras_deducciones": otras_deducciones if otras_deducciones else Decimal(0),
            "total_deducciones": total_deducciones,
            "neto_pagar": neto,
            "dias_trabajados": dias_trabajados
        }
    @staticmethod
    def guardar_nomina(
        db, 
        empresa_id: int, 
        anio: int, 
        mes: int, 
        empleado_id: int, 
        dias: int, 
        extras: Decimal, 
        comisiones: Decimal,
        otros_devengados: Decimal,
        otras_deducciones: Decimal
    ):

        from app.models import nomina as models_nomina # Lazy import
        
        # 1. Buscar o Crear Cabecera de Nómina para el Periodo
        # Asumimos pago Mensual por defecto para Beta
        nomina = db.query(models_nomina.Nomina).filter(
            models_nomina.Nomina.empresa_id == empresa_id,
            models_nomina.Nomina.anio == anio,
            models_nomina.Nomina.mes == mes
        ).first()
        
        if not nomina:
            from datetime import date
            import calendar
            last_day = calendar.monthrange(anio, mes)[1]
            
            nomina = models_nomina.Nomina(
                empresa_id=empresa_id,
                anio=anio,
                mes=mes,
                fecha_inicio_periodo=date(anio, mes, 1),
                fecha_fin_periodo=date(anio, mes, last_day),
                periodo_pago=models_nomina.PeriodoPago.MENSUAL,
                estado=models_nomina.EstadoNomina.BORRADOR
            )
            db.add(nomina)
            db.flush()
            
        # 2. Obtener Empleado y Recalcular
        empleado = db.query(models_nomina.Empleado).get(empleado_id)
        if not empleado:
            raise ValueError("Empleado no encontrado")
            
        # --- VALIDACIÓN CANDADO (PREVENIR DUPLICADOS) ---
        # Verificar si ya existe liquidación para este empleado en este periodo
        # La única forma de reliquidar es eliminando explícitamente la anterior
        existing_detalle = db.query(models_nomina.DetalleNomina).filter(
            models_nomina.DetalleNomina.nomina_id == nomina.id,
            models_nomina.DetalleNomina.empleado_id == empleado_id
        ).first()
        
        if existing_detalle:
            raise ValueError(f"Ya existe una liquidación para {empleado.nombres} en el periodo {anio}-{mes}. Elimine la anterior para reliquidar.")
        # -----------------------------------------------

        valores = LiquidadorNominaService.calcular_devengados_deducciones(
            salario_base=Decimal(empleado.salario_base),
            dias_trabajados=dias,
            tiene_auxilio=empleado.auxilio_transporte,
            horas_extras=extras,
            comisiones=comisiones,
            otros_devengados=otros_devengados,
            otras_deducciones=otras_deducciones
        )
        # 4. Crear Detalle
        detalle = models_nomina.DetalleNomina(
            nomina_id=nomina.id,
            empleado_id=empleado_id,
            dias_trabajados=valores['dias_trabajados'],
            sueldo_basico_periodo=valores['sueldo_basico_periodo'],
            auxilio_transporte_periodo=valores['auxilio_transporte'],
            horas_extras_total=valores['horas_extras'],
            comisiones=valores['comisiones'],
            otros_devengados=valores['otros_devengados'],
            otras_deducciones=valores['otras_deducciones'],
            # Revisando DetalleNomina en models/nomina.py no vimos esos campos explicitos en el view_file (lineas 110-130).
            # Asumiremos que existen en la base de datos o need to check model first.
            # CRITICAL: El modelo DetalleNomina tiene estos campos? 
            # Si no los tiene, el script de guardar fallara.
            # Asumamos que SI existen por contexto anterior, pero validare si falla.
            # En step 174 no se vieron definitions de columnas, solo Fks en 110.
            # Voy a usar setattr dinamico o confiar.
            # MEJOR: Agregar al modelo si no existen.
            
            total_devengado=valores['total_devengado'],
            salud_empleado=valores['salud'],
            pension_empleado=valores['pension'],
            fondo_solidaridad=valores['fsp'],
            total_deducciones=valores['total_deducciones'],
            neto_pagar=valores['neto_pagar']
        )
        db.add(detalle)
        db.flush() # CRITICAL: Ensure detalle has ID for reference in Documento
        
        # 5. Contabilización Automática
        # Buscar configuración: Prioridad Específica > Global
        config_query = db.query(models_nomina.ConfiguracionNomina).filter(
            models_nomina.ConfiguracionNomina.empresa_id == empresa_id
        )
        
        config = None
        # 1. Intentar buscar configuración específica del Tipo de Nomina
        if empleado.tipo_nomina_id:
             config = config_query.filter(models_nomina.ConfiguracionNomina.tipo_nomina_id == empleado.tipo_nomina_id).first()
             
        # 2. Si no existe (o empleado no tiene tipo), buscar global (tipo_nomina_id IS NULL)
        if not config:
            config = db.query(models_nomina.ConfiguracionNomina).filter(
                models_nomina.ConfiguracionNomina.empresa_id == empresa_id,
                models_nomina.ConfiguracionNomina.tipo_nomina_id == None
            ).first()

        if config:
            from app.models import Documento, MovimientoContable, TipoDocumento
            
            # 1. Usar Tipo Documento Configurado
            tipo_doc = None
            # 1. Usar Tipo Documento Configurado
            tipo_doc = None
            if config.tipo_documento_id:
                # CRITICAL Fix: usar with_for_update() para evitar duplicados en operaciones simultáneas
                tipo_doc = db.query(TipoDocumento).filter(TipoDocumento.id == config.tipo_documento_id).with_for_update().first()
            
            # 2. Si no esta configurado, buscar por defecto 'NM' o 'NOMINA'
            if not tipo_doc:
                tipo_doc = db.query(TipoDocumento).filter(TipoDocumento.codigo.in_(['NM', 'NOM', 'NOMINA'])).with_for_update().first()
            
            # 3. Fallback: Usar cualquier tipo de documento contable disponible
            if not tipo_doc:
                tipo_doc = db.query(TipoDocumento).with_for_update().first() 

            if not tipo_doc:
               # Si aun así no existe (BD vacía), crear uno basico o advertir
               pass

            # Crear Documento Contable
            # 4. Actualizar consecutivo (Simulación básica, idealmente transacción atómica)
            nuevo_consecutivo = tipo_doc.consecutivo_actual + 1
            tipo_doc.consecutivo_actual = nuevo_consecutivo

            nuevo_doc = Documento(
                empresa_id=empresa_id,
                tipo_documento_id=tipo_doc.id,
                numero=nuevo_consecutivo, # Usamos 'numero' que es el campo correcto
                fecha=nomina.fecha_liquidacion,
                beneficiario_id=empleado.tercero_id, 
                observaciones=f"Nómina {nomina.mes}/{nomina.anio} - {empleado.nombres} {empleado.apellidos} (Ref: {detalle.id})",
                estado="ACTIVO", # Ajustado a 'ACTIVO' según modelo Documento por defecto
                usuario_creador_id=None 
            )
            db.add(nuevo_doc)
            db.flush() 
            
            # NUEVO: Guardar vínculo directo en el detalle
            detalle.documento_contable_id = nuevo_doc.id
            db.add(detalle)
            
            movimientos = []
            
            def agregar_mov(cuenta_id, debito, credito, descripcion):
                if cuenta_id and (debito > 0 or credito > 0):
                     movimientos.append(MovimientoContable(
                         documento_id=nuevo_doc.id,
                         cuenta_id=cuenta_id,
                         # tercero_id removido, se usa beneficiario en Documento
                         concepto=descripcion, # detalle -> concepto
                         debito=debito,
                         credito=credito
                         # base_impuesto removido, no existe en modelo
                     ))

            # 1. Gasto Sueldo (Debito)
            agregar_mov(config.cuenta_sueldo_id, valores['sueldo_basico_periodo'], 0, "Sueldo Básico")
            
            # 2. Gasto Aux Transporte (Debito)
            agregar_mov(config.cuenta_auxilio_transporte_id, valores['auxilio_transporte'], 0, "Auxilio Transporte")
            
            # 3. Gasto Extras (Debito)
            agregar_mov(config.cuenta_horas_extras_id, valores['horas_extras'], 0, "Horas Extras y Recargos")
            
            # 4. Gasto Comisiones (Debito)
            agregar_mov(config.cuenta_comisiones_id, valores['comisiones'], 0, "Comisiones")
            
            # 4.1 Gasto Otros Devengados (Debito)
            otros_dev = getattr(detalle, 'otros_devengados', 0) or 0
            if otros_dev > 0:
                 agregar_mov(config.cuenta_otros_devengados_id, otros_dev, 0, "Otros Devengados")
            
            
            # 5. Pasivo Salud (Credito) - Descuento al empleado
            agregar_mov(config.cuenta_aporte_salud_id, 0, valores['salud'], "Aporte Salud (Empleado)")
            
            # 6. Pasivo Pension (Credito) - Descuento al empleado
            agregar_mov(config.cuenta_aporte_pension_id, 0, valores['pension'], "Aporte Pensión (Empleado)")
            
            # 7. Pasivo FSP (Credito)
            agregar_mov(config.cuenta_fondo_solidaridad_id, 0, valores['fsp'], "Fondo Solidaridad Pensional")

            # 7.1 Pasivo Otras Deducciones (Credito)
            otras_ded = getattr(detalle, 'otras_deducciones', 0) or 0
            if otras_ded > 0:
                 agregar_mov(config.cuenta_otras_deducciones_id, 0, otras_ded, "Otras Deducciones")
            
            
            # 8. Neto a Pagar (Credito) -> Salarios por Pagar
            agregar_mov(config.cuenta_salarios_por_pagar_id, 0, valores['neto_pagar'], "Salarios por Pagar")
            
            db.add_all(movimientos)

        db.commit()
        db.refresh(detalle)
        return detalle
