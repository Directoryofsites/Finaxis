from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case
from decimal import Decimal
from datetime import datetime
from typing import List, Optional, Dict, Any

from app.models.presupuesto import PresupuestoCabecera, PresupuestoDetalle, PresupuestoBitacora
from app.models.plan_cuenta import PlanCuenta
from app.models.movimiento_contable import MovimientoContable
from app.models.documento import Documento
from app.schemas.presupuesto import BudgetEntryRequest, IndividualMonthEdit

class PresupuestoService:
    @staticmethod
    def distribute_annual_budget(total_anual: Decimal) -> List[Decimal]:
        """Distribute an annual amount into 12 monthly installments with smart rounding."""
        base_mensual = (total_anual / Decimal('12')).quantize(Decimal('0.01'))
        distribucion = [base_mensual] * 12
        
        # Adjust for rounding difference in the last month
        suma_actual = sum(distribucion)
        diferencia = total_anual - suma_actual
        distribucion[11] += diferencia
        
        return distribucion

    @staticmethod
    def get_or_create_cabecera(db: Session, empresa_id: int, anio: int) -> PresupuestoCabecera:
        cabecera = db.query(PresupuestoCabecera).filter(
            PresupuestoCabecera.empresa_id == empresa_id,
            PresupuestoCabecera.anio == anio
        ).first()
        
        if not cabecera:
            cabecera = PresupuestoCabecera(empresa_id=empresa_id, anio=anio, estado='borrador')
            db.add(cabecera)
            db.commit()
            db.refresh(cabecera)
        return cabecera

    @staticmethod
    def register_account_budget(db: Session, empresa_id: int, request: BudgetEntryRequest):
        print(f"DEBUG BUDGET: Registering/Updating annual budget for {request.codigo_cuenta}, year {request.anio}, value {request.valor_anual}")
        cabecera = PresupuestoService.get_or_create_cabecera(db, empresa_id, request.anio)
        
        # 1. Distribute monthly
        cuotas = PresupuestoService.distribute_annual_budget(request.valor_anual)
        
        # 2. Get existing details to perform upsert (avoids IntegrityError with bitácora)
        existing_details = db.query(PresupuestoDetalle).filter(
            PresupuestoDetalle.cabecera_id == cabecera.id,
            PresupuestoDetalle.codigo_cuenta == request.codigo_cuenta
        ).all()
        
        detail_map = {d.mes: d for d in existing_details}
        
        try:
            for i, valor in enumerate(cuotas):
                mes = i + 1
                if mes in detail_map:
                    detalle = detail_map[mes]
                    detalle.valor_automatico = valor
                    # Update valor_vigente ONLY if there's no manual edit
                    if detalle.valor_editado is None:
                        detalle.valor_vigente = valor
                    print(f"DEBUG BUDGET: Updated month {mes} for {request.codigo_cuenta}")
                else:
                    detalle = PresupuestoDetalle(
                        cabecera_id=cabecera.id,
                        codigo_cuenta=request.codigo_cuenta,
                        mes=mes,
                        valor_automatico=valor,
                        valor_vigente=valor
                    )
                    db.add(detalle)
                    print(f"DEBUG BUDGET: Created month {mes} for {request.codigo_cuenta}")
            
            db.commit()
            print(f"DEBUG BUDGET: Success registering budget for {request.codigo_cuenta}")
        except Exception as e:
            db.rollback()
            print(f"DEBUG BUDGET: CRITICAL ERROR in register_account_budget: {str(e)}")
            raise e
            
        return {"status": "success", "message": f"Presupuesto registrado para cuenta {request.codigo_cuenta}"}

    @staticmethod
    def edit_monthly_budget(db: Session, detalle_id: int, usuario_id: int, nuevo_valor: Decimal, motivo: str = None):
        print(f"DEBUG BUDGET: Start edit_monthly_budget - detail_id: {detalle_id}, user_id: {usuario_id}, value: {nuevo_valor}")
        detalle = db.query(PresupuestoDetalle).filter(PresupuestoDetalle.id == detalle_id).first()
        if not detalle:
            print(f"DEBUG BUDGET: ERROR - Detail {detalle_id} not found")
            raise ValueError("Detalle de presupuesto no encontrado")
        
        valor_anterior = detalle.valor_vigente
        
        try:
            # 1. Update Detail first (Critical)
            detalle.valor_editado = nuevo_valor
            detalle.valor_vigente = nuevo_valor
            detalle.fecha_edicion = datetime.utcnow()
            print(f"DEBUG BUDGET: Detail {detalle_id} updated in session")

            # 2. Record in bitácora (Optional step, don't break if it fails)
            try:
                log = PresupuestoBitacora(
                    detalle_id=detalle.id,
                    usuario_id=usuario_id,
                    valor_anterior=valor_anterior,
                    valor_nuevo=nuevo_valor,
                    motivo=motivo or "Edición manual"
                )
                db.add(log)
                print(f"DEBUG BUDGET: Bitácora log prepared for detail {detalle_id}")
            except Exception as log_err:
                print(f"DEBUG BUDGET: WARNING - Could not create bitácora log: {str(log_err)}")
            
            # 3. Final Commit
            db.commit()
            db.refresh(detalle)
            print(f"DEBUG BUDGET: Transaction committed successfully for detail {detalle_id}")
            return detalle
        except Exception as e:
            db.rollback()
            print(f"DEBUG BUDGET: CRITICAL ERROR in transaction: {str(e)}")
            raise e

    @staticmethod
    def get_puc_for_budget(db: Session, empresa_id: int, anio: int):
        """
        Returns the PUC (classes 4-7) hierarchy that has movement in the previous or current year.
        Integrated with existing budgets.
        """
        # 1. Identity accounts with movement (Simplified for now, can be optimized with common table expressions)
        # We look for result accounts: codes starting with 4, 5, 6, 7
        result_accounts = db.query(PlanCuenta).filter(
            PlanCuenta.empresa_id == empresa_id,
            or_(
                PlanCuenta.codigo.like('4%'),
                PlanCuenta.codigo.like('5%'),
                PlanCuenta.codigo.like('6%'),
                PlanCuenta.codigo.like('7%')
            )
        ).order_by(PlanCuenta.codigo).all()
        
        # 2. Get current budget for this year
        cabecera = db.query(PresupuestoCabecera).filter(
            PresupuestoCabecera.empresa_id == empresa_id,
            PresupuestoCabecera.anio == anio
        ).first()
        
        budget_map = {}
        if cabecera:
            detalles = db.query(
                PresupuestoDetalle.codigo_cuenta,
                func.sum(PresupuestoDetalle.valor_vigente).label('total')
            ).filter(PresupuestoDetalle.cabecera_id == cabecera.id).group_by(PresupuestoDetalle.codigo_cuenta).all()
            
            for d in detalles:
                budget_map[d.codigo_cuenta] = d.total

        # 3. Build Tree (recursive helper or iterative)
        # For brevity, let's return a flat list first and handle tree building in frontend or a helper
        return [{
            "id": acc.id,
            "codigo": acc.codigo,
            "nombre": acc.nombre,
            "nivel": acc.nivel,
            "permite_movimiento": acc.permite_movimiento,
            "presupuesto_anual": budget_map.get(acc.codigo, 0),
            "tiene_presupuesto": acc.codigo in budget_map
        } for acc in result_accounts]

    @staticmethod
    def get_comparative_report(db: Session, empresa_id: int, anio: int, meses: List[int], codigos_puc: Optional[List[str]] = None):
        """
        Calculates Budgeted vs Executed for selected months.
        """
        # 1. Budgeted
        # Sum of valor_vigente for selected months and accounts
        budget_query = db.query(
            PresupuestoDetalle.codigo_cuenta,
            func.sum(PresupuestoDetalle.valor_vigente).label('presupuestado')
        ).join(PresupuestoCabecera).filter(
            PresupuestoCabecera.empresa_id == empresa_id,
            PresupuestoCabecera.anio == anio,
            PresupuestoDetalle.mes.in_(meses)
        )
        
        if codigos_puc:
            budget_query = budget_query.filter(PresupuestoDetalle.codigo_cuenta.in_(codigos_puc))
            
        budgets = budget_query.group_by(PresupuestoDetalle.codigo_cuenta).all()
        
        # 2. Executed (Movements)
        # This requires matching the accounts. We need to handle hierarchy rollups too.
        # For now, let's focus on auxiliar level.
        
        start_date = datetime(anio, min(meses), 1).date()
        # Last day of max month
        max_month = max(meses)
        from datetime import date, timedelta
        if max_month == 12:
            end_date = date(anio, 12, 31)
        else:
            # First day of next month minus 1 day
            end_date = (datetime(anio, max_month + 1, 1) - timedelta(days=1)).date()

        executed_query = db.query(
            PlanCuenta.codigo,
            func.sum(MovimientoContable.debito - MovimientoContable.credito).label('ejecutado')
        ).join(MovimientoContable, MovimientoContable.cuenta_id == PlanCuenta.id)\
         .join(Documento, MovimientoContable.documento_id == Documento.id)\
         .filter(
             Documento.empresa_id == empresa_id,
             Documento.fecha >= start_date,
             Documento.fecha <= end_date,
             Documento.anulado == False,
             or_(
                PlanCuenta.codigo.like('4%'),
                PlanCuenta.codigo.like('5%'),
                PlanCuenta.codigo.like('6%'),
                PlanCuenta.codigo.like('7%')
            )
         ).group_by(PlanCuenta.codigo)

        executed_data = executed_query.all()
        
        # Merge data and get names
        # Map for names
        name_map = {acc.codigo: acc.nombre for acc in db.query(PlanCuenta).filter(
            PlanCuenta.empresa_id == empresa_id,
            or_(
                *[PlanCuenta.codigo.like(f'{c}%') for c in ['4', '5', '6', '7']]
            )
        ).all()}

        results = []
        exec_map = {e.codigo: e.ejecutado for e in executed_data}
        budget_map = {b.codigo_cuenta: b.presupuestado for b in budgets}
        
        # Get all relevant account codes
        all_codes = sorted(list(set(exec_map.keys()) | set(budget_map.keys())))
        
        for code in all_codes:
            pres = budget_map.get(code, Decimal('0.00'))
            # For accounts 4 (Ingresos), executed is usually Net Credit. 
            # For 5, 6, 7 (Costs/Expenses), it's Net Debit.
            raw_exec = exec_map.get(code, Decimal('0.00'))
            
            # Sign adjustment based on account type
            if code.startswith('4'):
                ejec = -raw_exec # Credits are positive for income
            else:
                ejec = raw_exec # Debits are positive for expenses
                
            variacion_abs = ejec - pres
            variacion_pct = (variacion_abs / pres * 100) if pres != 0 else 0
            ejecucion_pct = (ejec / pres * 100) if pres != 0 else 0
            saldo = pres - ejec
            
            results.append({
                "codigo": code,
                "nombre": name_map.get(code, "Cuenta desconocida"),
                "presupuestado": pres,
                "ejecutado": ejec,
                "variacion_abs": variacion_abs,
                "variacion_pct": variacion_pct,
                "ejecucion_pct": ejecucion_pct,
                "saldo_por_ejecutar": saldo
            })
            
        return results

    @staticmethod
    def generate_comparative_csv(db: Session, empresa_id: int, anio: int, meses: List[int]):
        """Generates a CSV string of the comparative report."""
        report_data = PresupuestoService.get_comparative_report(db, empresa_id, anio, meses)
        
        import io
        import csv
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        
        # Header
        writer.writerow(["Codigo", "Nombre", "Presupuestado", "Ejecutado", "Variacion Abs", "Variacion %", "Ejecucion %", "Saldo por Ejecutar"])
        
        # Data
        for row in report_data:
            writer.writerow([
                row["codigo"],
                row["nombre"],
                f"{row['presupuestado']:.0f}",
                f"{row['ejecutado']:.0f}",
                f"{row['variacion_abs']:.0f}",
                f"{row['variacion_pct']:.0f}",
                f"{row['ejecucion_pct']:.0f}",
                f"{row['saldo_por_ejecutar']:.0f}"
            ])
            
        # Summary Row
        total_pres = sum(r['presupuestado'] for r in report_data)
        total_ejec = sum(r['ejecutado'] for r in report_data)
        total_var = sum(r['variacion_abs'] for r in report_data)
        total_pct = (total_ejec / total_pres * 100) if total_pres > 0 else 0
        
        writer.writerow([])
        writer.writerow([
            "TOTALES",
            "",
            f"{total_pres:.0f}",
            f"{total_ejec:.0f}",
            f"{total_var:.0f}",
            "",
            f"{total_pct:.1f}",
            ""
        ])
            
        return output.getvalue()

    @staticmethod
    def generate_comparative_pdf(db: Session, empresa_id: int, anio: int, meses: List[int]):
        """Generates a PDF using the standard reporting system."""
        report_data = PresupuestoService.get_comparative_report(db, empresa_id, anio, meses)
        
        from app.models.empresa import Empresa as models_empresa
        empresa_info = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
        
        from app.services.reports import GLOBAL_JINJA_ENV
        from weasyprint import HTML
        from fastapi import Response
        
        meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        periodo_str = f"{anio} - Meses: " + ", ".join([meses_nombres[m-1] for m in sorted(meses)])
        
        context = {
            'filas': report_data,
            'empresa': empresa_info,
            'periodo': periodo_str,
            'titulo_reporte': "Reporte Comparativo de Presupuesto",
            'totales': {
                'presupuestado': sum(r['presupuestado'] for r in report_data),
                'ejecutado': sum(r['ejecutado'] for r in report_data),
                'variacion': sum(r['variacion_abs'] for r in report_data)
            }
        }
        
        # Calculate global percentage
        pres = context['totales']['presupuestado']
        ejec = context['totales']['ejecutado']
        context['totales']['ejecucion_pct'] = (ejec / pres * 100) if pres > 0 else 0
        
        html_template = """
        <html>
        <head>
            <style>
                body { font-family: sans-serif; padding: 30px; }
                .company-name { font-size: 20px; font-bold: true; color: #1e40af; }
                table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                th, td { border: 1px solid #ccc; padding: 6px; text-align: left; font-size: 9px; }
                th { background-color: #f3f4f6; }
                .text-right { text-align: right; }
                .total-row { background-color: #e5e7eb; font-weight: bold; }
            </style>
        </head>
        <body>
            <div style="text-align: center;">
                <div class="company-name">{{ empresa.razon_social }}</div>
                <div>NIT: {{ empresa.nit }}</div>
                <h2 style="margin: 10px 0;">{{ titulo_reporte }}</h2>
                <div style="font-size: 11px;">{{ periodo }}</div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>C&oacute;digo</th>
                        <th>Nombre Cuenta</th>
                        <th class="text-right">Presupuestado</th>
                        <th class="text-right">Ejecutado</th>
                        <th class="text-right">Variaci&oacute;n $</th>
                        <th class="text-right">Ejecucion %</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in filas %}
                    <tr>
                        <td>{{ row.codigo }}</td>
                        <td>{{ row.nombre }}</td>
                        <td class="text-right">{{ "{:,.0f}".format(row.presupuestado) }}</td>
                        <td class="text-right">{{ "{:,.0f}".format(row.ejecutado) }}</td>
                        <td class="text-right">{{ "{:,.0f}".format(row.variacion_abs) }}</td>
                        <td class="text-right">{{ "{:,.1f}".format(row.ejecucion_pct) }}%</td>
                    </tr>
                    {% endfor %}
                    <tr class="total-row">
                        <td colspan="2">TOTALES</td>
                        <td class="text-right">{{ "{:,.0f}".format(totales.presupuestado) }}</td>
                        <td class="text-right">{{ "{:,.0f}".format(totales.ejecutado) }}</td>
                        <td class="text-right">{{ "{:,.0f}".format(totales.variacion) }}</td>
                        <td class="text-right">{{ "{:,.1f}".format(totales.ejecucion_pct) }}%</td>
                    </tr>
                </tbody>
            </table>
        </body>
        </html>
        """
        
        template = GLOBAL_JINJA_ENV.from_string(html_template)
        html_string = template.render(context)
        pdf_content = HTML(string=html_string).write_pdf()
        return Response(content=pdf_content, media_type="application/pdf")
    @staticmethod
    def bulk_import_budget(db: Session, empresa_id: int, anio: int, file_content: bytes, filename: str):
        """
        Imports budget from a CSV or Excel file.
        Expects columns: 'codigo' and 'valor_anual'.
        """
        import pandas as pd
        import io
        
        try:
            if filename.endswith('.csv'):
                # Try with different delimiters common in Excel/CSV
                try:
                    df = pd.read_csv(io.BytesIO(file_content), sep=';')
                except:
                    df = pd.read_csv(io.BytesIO(file_content), sep=',')
            else:
                df = pd.read_excel(io.BytesIO(file_content))
            
            # Normalize column names
            df.columns = [c.lower().strip() for c in df.columns]
            
            # Alias mapping
            rename_map = {
                'presupuestado': 'valor_anual',
                'monto': 'valor_anual',
                'total': 'valor_anual',
                'presupuesto': 'valor_anual'
            }
            df = df.rename(columns=rename_map)
            
            # Validation: check for required columns
            required = ['codigo', 'valor_anual']
            for col in required:
                if col not in df.columns:
                    raise ValueError(f"El archivo debe contener la columna '{col}'")
            
            results = {"success": 0, "errors": []}
            
            for index, row in df.iterrows():
                codigo = str(row['codigo']).strip()
                try:
                    raw_valor = str(row['valor_anual']).strip().lower()
                    
                    # Handle common empty/null representations in pandas/excel
                    if not raw_valor or raw_valor in ['nan', 'none', 'null', '']:
                        valor_anual = Decimal('0')
                    else:
                        # Clean currency symbols and spaces
                        clean_valor = raw_valor.replace('$', '').replace(' ', '').replace('\xa0', '').replace('usd', '')
                        
                        # Logic to handle international number formats
                        if '.' in clean_valor and ',' in clean_valor:
                            clean_valor = clean_valor.replace('.', '').replace(',', '.')
                        elif clean_valor.count('.') > 1:
                            clean_valor = clean_valor.replace('.', '')
                        elif '.' in clean_valor:
                            parts = clean_valor.split('.')
                            if len(parts[-1]) == 3:
                                clean_valor = clean_valor.replace('.', '')
                        elif ',' in clean_valor:
                            clean_valor = clean_valor.replace(',', '.')

                        # If cleaning resulted in empty string (e.g. only '$' was present)
                        if not clean_valor:
                            valor_anual = Decimal('0')
                        else:
                            try:
                                valor_anual = Decimal(clean_valor)
                                # Check for non-finite values (NaN, Inf) which Pydantic rejects
                                if not valor_anual.is_finite():
                                    valor_anual = Decimal('0')
                            except:
                                # Fallback if cleaning failed to produce a valid decimal
                                results["errors"].append(f"Fila {index+2}: Valor inválido '{raw_valor}'")
                                continue
                    
                    # Validate account exists
                    acc = db.query(PlanCuenta).filter(
                        PlanCuenta.empresa_id == empresa_id,
                        PlanCuenta.codigo == codigo
                    ).first()
                    
                    if not acc:
                        results["errors"].append(f"Fila {index+2}: La cuenta {codigo} no existe.")
                        continue
                    
                    if not acc.permite_movimiento:
                        results["errors"].append(f"Fila {index+2}: La cuenta {codigo} no es auxiliar.")
                        continue
                    
                    # Use existing registration logic
                    from app.schemas.presupuesto import BudgetEntryRequest
                    request = BudgetEntryRequest(anio=anio, codigo_cuenta=codigo, valor_anual=valor_anual)
                    PresupuestoService.register_account_budget(db, empresa_id, request)
                    results["success"] += 1
                    
                except Exception as e:
                    results["errors"].append(f"Fila {index+2}: Error procesando - {str(e)}")
            
            return results
        except Exception as e:
            raise ValueError(f"Error al procesar el archivo: {str(e)}")

    @staticmethod
    def generate_graphical_pdf(db: Session, empresa_id: int, anio: int, meses: List[int]):
        """Generates a PDF with progress bars for budget execution."""
        report_data = PresupuestoService.get_comparative_report(db, empresa_id, anio, meses)
        
        from app.models.empresa import Empresa as models_empresa
        empresa_info = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
        
        from app.services.reports import GLOBAL_JINJA_ENV
        from weasyprint import HTML
        from fastapi import Response
        
        meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        periodo_str = f"{anio} - Meses: " + ", ".join([meses_nombres[m-1] for m in sorted(meses)])
        
        context = {
            'filas': report_data,
            'empresa': empresa_info,
            'periodo': periodo_str,
            'titulo_reporte': "Visualización de Ejecución Presupuestal",
            'totales': {
                'presupuestado': sum(r['presupuestado'] for r in report_data),
                'ejecutado': sum(r['ejecutado'] for r in report_data)
            }
        }
        
        # Calculate global percentage
        pres = context['totales']['presupuestado']
        ejec = context['totales']['ejecutado']
        context['totales']['ejecucion_pct'] = (ejec / pres * 100) if pres > 0 else 0
        
        html_template = """
        <html>
        <head>
            <style>
                @page { size: A4; margin: 20mm; }
                body { font-family: 'Helvetica', 'Arial', sans-serif; color: #334155; }
                .header { text-align: center; margin-bottom: 30px; border-bottom: 2px solid #e2e8f0; padding-bottom: 20px; }
                .company-name { font-size: 24px; font-weight: bold; color: #1e40af; }
                .report-title { font-size: 18px; margin: 10px 0; color: #64748b; text-transform: uppercase; letter-spacing: 1px; }
                
                .row { margin-bottom: 25px; page-break-inside: avoid; }
                .row-header { display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 10px; font-weight: bold; }
                .account-info { color: #1e293b; }
                .execution-label { color: #64748b; text-align: right; }
                
                .progress-container { height: 12px; background-color: #f1f5f9; border-radius: 6px; overflow: hidden; display: flex; margin: 8px 0; border: 1px solid #e2e8f0; }
                .progress-bar { height: 100%; }
                .bar-main { background-color: #3b82f6; }
                .bar-warning { background-color: #ef4444; }
                .bar-over { background-color: #991b1b; opacity: 0.5; display: flex; align-items: center; justify-content: center; color: white; font-size: 8px; font-weight: bold; }
                
                .row-footer { display: flex; justify-content: space-between; font-size: 9px; color: #94a3b8; margin-top: 4px; }
                .data-box { width: 100%; display: table; }
                .data-cell { display: table-cell; }
                .text-right { text-align: right; }
            </style>
        </head>
        <body>
            <div class="header">
                <div class="company-name">{{ empresa.razon_social }}</div>
                <div style="font-size: 12px; color: #64748b;">NIT: {{ empresa.nit }}</div>
                <div class="report-title">{{ titulo_reporte }}</div>
                <div style="font-size: 11px;">Per&iacute;odo: {{ periodo }}</div>
            </div>

            {% for row in filas %}
            <div class="row">
                <table style="width: 100%;">
                    <tr>
                        <td style="font-size: 11px; font-weight: bold; color: #1e293b;">
                            <span style="color: #3b82f6;">{{ row.codigo }}</span><br>
                            {{ row.nombre }}
                        </td>
                        <td style="text-align: right; font-size: 10px; font-weight: bold; color: #64748b; vertical-align: bottom;">
                            EJECUCI&Oacute;N: {{ "{:,.1f}".format(row.ejecucion_pct) }}%
                        </td>
                    </tr>
                </table>
                <div class="progress-container">
                    {% if row.ejecucion_pct > 100 %}
                        <div class="progress-bar bar-warning" style="width: {{ (100 / row.ejecucion_pct * 100)|round(2) if row.ejecucion_pct > 0 else 100 }}%;"></div>
                        <div class="progress-bar bar-over" style="width: {{ ( (row.ejecucion_pct - 100) / row.ejecucion_pct * 100)|round(2) }}%;">!</div>
                    {% else %}
                        <div class="progress-bar bar-main" style="width: {{ [row.ejecucion_pct, 100]|min }}%;"></div>
                    {% endif %}
                </div>
                <table style="width: 100%; font-size: 9px; color: #64748b;">
                    <tr>
                        <td>Pres: ${{ "{:,.0f}".format(row.presupuestado) }}</td>
                        <td style="text-align: right;">Ejec: ${{ "{:,.0f}".format(row.ejecutado) }}</td>
                    </tr>
                </table>
            </div>
            {% endfor %}

            <!-- GRAND TOTAL SECTION -->
            <div style="margin-top: 40px; padding: 20px; background-color: #f8fafc; border: 2px solid #e2e8f0; border-radius: 12px; page-break-inside: avoid;">
                <table style="width: 100%; margin-bottom: 10px;">
                    <tr>
                        <td style="font-size: 16px; font-weight: bold; color: #1e293b; text-transform: uppercase; letter-spacing: 1px;">
                            TOTAL GENERAL DE EJECUCI&Oacute;N
                        </td>
                        <td style="text-align: right; font-size: 14px; font-weight: bold; color: #1e40af;">
                            {{ "{:,.1f}".format(totales.ejecucion_pct) }}%
                        </td>
                    </tr>
                </table>
                
                <div class="progress-container" style="height: 20px; border-radius: 10px; margin: 15px 0; border-width: 2px;">
                    {% if totales.ejecucion_pct > 100 %}
                        <div class="progress-bar bar-warning" style="width: {{ (100 / totales.ejecucion_pct * 100)|round(2) if totales.ejecucion_pct > 0 else 100 }}%;"></div>
                        <div class="progress-bar bar-over" style="width: {{ ( (totales.ejecucion_pct - 100) / totales.ejecucion_pct * 100)|round(2) }}%; font-size: 10px;">!</div>
                    {% else %}
                        <div class="progress-bar bar-main" style="width: {{ [totales.ejecucion_pct, 100]|min }}%; background: linear-gradient(to right, #3b82f6, #1d4ed8);"></div>
                    {% endif %}
                </div>

                <table style="width: 100%; font-size: 12px; font-weight: bold; color: #475569;">
                    <tr>
                        <td>TOTAL PRES: ${{ "{:,.0f}".format(totales.presupuestado) }}</td>
                        <td style="text-align: right;">TOTAL EJEC: ${{ "{:,.0f}".format(totales.ejecutado) }}</td>
                    </tr>
                </table>
            </div>
        </body>
        </html>
        """
        
        template = GLOBAL_JINJA_ENV.from_string(html_template)
        html_string = template.render(context)
        pdf_content = HTML(string=html_string).write_pdf()
        return Response(content=pdf_content, media_type="application/pdf")
