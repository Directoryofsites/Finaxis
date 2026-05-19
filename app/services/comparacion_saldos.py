import calendar
from datetime import date, datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from fastapi import Response
from fastapi.responses import StreamingResponse
import io

from app.models.plan_cuenta import PlanCuenta
from app.models.movimiento_contable import MovimientoContable
from app.models.documento import Documento
from app.models.empresa import Empresa
from app.schemas.reporte_comparacion_saldos import FiltrosComparacionSaldos, FilaComparacionSaldos

from weasyprint import HTML

NOMBRES_MESES = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre"
}

def generate_comparacion_saldos_report(db: Session, empresa_id: int, filtros: FiltrosComparacionSaldos) -> Dict[str, Any]:
    """
    Calcula los saldos mensuales acumulados de fin de mes para las cuentas PUC solicitadas.
    Es 100% dialect-agnostic (funciona perfectamente en SQLite y PostgreSQL) al realizar
    consultas por rangos de fecha nativas y estructurar la jerarquía en memoria.
    """
    mes_inicio = filtros.mes_inicio or 1
    mes_fin = filtros.mes_fin or 12
    if mes_inicio > mes_fin:
        mes_inicio, mes_fin = mes_fin, mes_inicio
        
    meses = list(range(mes_inicio, mes_fin + 1))
    
    # 1. Consultar cuentas que cumplan los filtros base
    q_cuentas = db.query(PlanCuenta).filter(PlanCuenta.empresa_id == empresa_id)
    
    if filtros.cuenta_codigo:
        q_cuentas = q_cuentas.filter(PlanCuenta.codigo.startswith(filtros.cuenta_codigo))
        
    if filtros.tipo_filtro == "BALANCE":
        q_cuentas = q_cuentas.filter(or_(*[PlanCuenta.codigo.startswith(str(i)) for i in [1, 2, 3]]))
    elif filtros.tipo_filtro == "RESULTADOS":
        q_cuentas = q_cuentas.filter(or_(*[PlanCuenta.codigo.startswith(str(i)) for i in [4, 5, 6, 7]]))
        
    cuentas = q_cuentas.order_by(PlanCuenta.codigo).all()
    
    if not cuentas:
        return {"filas": [], "meses": meses}
        
    # 2. Inicializar mapa de cuentas en memoria
    cuentas_map = {c.id: {
        "data": {
            "codigo": c.codigo,
            "nombre": c.nombre,
            "nivel": c.nivel,
            "saldo_inicial": 0.0,
            "saldos_mensuales": {m: 0.0 for m in meses}
        },
        "children": [],
        "parent_id": c.cuenta_padre_id,
        "id": c.id
    } for c in cuentas}
    
    # Construir relaciones jerárquicas
    root_cuentas = []
    for c_id, c_node in cuentas_map.items():
        if c_node['parent_id'] and c_node['parent_id'] in cuentas_map:
            cuentas_map[c_node['parent_id']]['children'].append(c_id)
        else:
            root_cuentas.append(c_id)
            
    # 3. Obtener el saldo inicial (acumulado histórico de movimientos antes del 1 de enero del año de consulta)
    saldos_iniciales_q = db.query(
        MovimientoContable.cuenta_id,
        func.sum(MovimientoContable.debito - MovimientoContable.credito).label("saldo_inicial")
    ).join(Documento).filter(
        Documento.empresa_id == empresa_id,
        Documento.fecha < date(filtros.anio, 1, 1),
        Documento.anulado == False
    ).group_by(MovimientoContable.cuenta_id).all()
    
    for row in saldos_iniciales_q:
        if row.cuenta_id in cuentas_map:
            codigo = cuentas_map[row.cuenta_id]['data']['codigo']
            if codigo and codigo[0] in ('4', '5', '6', '7'):
                cuentas_map[row.cuenta_id]['data']['saldo_inicial'] = 0.0
            else:
                cuentas_map[row.cuenta_id]['data']['saldo_inicial'] = float(row.saldo_inicial or 0.0)
            
    # 4. Obtener movimientos mensuales agrupados por cuenta para cada mes del rango
    # movimientos_mensuales[cuenta_id][mes] = (debito, credito)
    movimientos_mensuales = {}
    
    for m in meses:
        _, ultimo_dia = calendar.monthrange(filtros.anio, m)
        f_ini = date(filtros.anio, m, 1)
        f_fin = date(filtros.anio, m, ultimo_dia)
        
        movs_mes = db.query(
            MovimientoContable.cuenta_id,
            func.sum(MovimientoContable.debito).label("debito"),
            func.sum(MovimientoContable.credito).label("credito")
        ).join(Documento).filter(
            Documento.empresa_id == empresa_id,
            Documento.fecha.between(f_ini, f_fin),
            Documento.anulado == False
        ).group_by(MovimientoContable.cuenta_id).all()
        
        for row in movs_mes:
            c_id = row.cuenta_id
            if c_id not in movimientos_mensuales:
                movimientos_mensuales[c_id] = {}
            movimientos_mensuales[c_id][m] = (float(row.debito or 0.0), float(row.credito or 0.0))
            
    # 5. Calcular saldos mensuales en las cuentas auxiliares (hojas)
    for c_id, c_node in cuentas_map.items():
        if not c_node['children']:
            codigo = c_node['data']['codigo']
            es_balance = codigo and codigo[0] in ('1', '2', '3')
            
            if es_balance:
                saldo_acumulado = c_node['data']['saldo_inicial']
                for m in meses:
                    deb, cred = 0.0, 0.0
                    if c_id in movimientos_mensuales and m in movimientos_mensuales[c_id]:
                        deb, cred = movimientos_mensuales[c_id][m]
                    saldo_acumulado += (deb - cred)
                    c_node['data']['saldos_mensuales'][m] = saldo_acumulado
            else:
                c_node['data']['saldo_inicial'] = 0.0
                for m in meses:
                    deb, cred = 0.0, 0.0
                    if c_id in movimientos_mensuales and m in movimientos_mensuales[c_id]:
                        deb, cred = movimientos_mensuales[c_id][m]
                    c_node['data']['saldos_mensuales'][m] = deb - cred
                
    # 6. Agregación recursiva hacia las cuentas padre (desde hojas hacia arriba)
    def acumular_padre(cuenta_id):
        c_node = cuentas_map[cuenta_id]
        if not c_node['children']:
            return
            
        # Procesar primero todos los hijos de forma recursiva
        for child_id in c_node['children']:
            acumular_padre(child_id)
            
        # Inicializar sumas del padre a cero
        c_node['data']['saldo_inicial'] = 0.0
        for m in meses:
            c_node['data']['saldos_mensuales'][m] = 0.0
            
        # Sumar los valores correspondientes de todos los hijos en este sub-árbol
        for child_id in c_node['children']:
            child_node = cuentas_map[child_id]
            c_node['data']['saldo_inicial'] += child_node['data']['saldo_inicial']
            for m in meses:
                c_node['data']['saldos_mensuales'][m] += child_node['data']['saldos_mensuales'][m]
                
    for root_id in root_cuentas:
        acumular_padre(root_id)
        
    # 7. Aplanar el árbol y formatear según el nivel máximo solicitado
    filas_reporte = []
    def aplanar(cuenta_id):
        c_node = cuentas_map[cuenta_id]
        
        if c_node['data']['nivel'] <= (filtros.nivel_maximo or 9):
            filas_reporte.append(FilaComparacionSaldos(
                codigo=c_node['data']['codigo'],
                nombre=c_node['data']['nombre'],
                nivel=c_node['data']['nivel'],
                saldo_inicial=c_node['data']['saldo_inicial'],
                saldos_mensuales=c_node['data']['saldos_mensuales']
            ))
            
        for child_id in sorted(c_node['children'], key=lambda x: cuentas_map[x]['data']['codigo']):
            aplanar(child_id)
            
    for root_id in sorted(root_cuentas, key=lambda x: cuentas_map[x]['data']['codigo']):
        aplanar(root_id)
        
    return {"filas": filas_reporte, "meses": meses}

def generate_comparacion_saldos_csv(data: Dict[str, Any]) -> Response:
    """
    Genera un archivo CSV con la comparación de saldos mensuales,
    diseñado específicamente para compatibilidad impecable con Microsoft Excel.
    """
    filas: List[FilaComparacionSaldos] = data["filas"]
    meses: List[int] = data["meses"]
    
    # BOM UTF-8 para garantizar acentos en Excel
    output = io.StringIO()
    output.write('\ufeff')
    
    # Construir cabeceras
    headers = ["Código", "Nombre", "Nivel", "Saldo Inicial"]
    for m in meses:
        headers.append(NOMBRES_MESES.get(m, f"Mes {m}"))
        
    output.write(";".join(headers) + "\n")
    
    for f in filas:
        row_data = [
            f.codigo,
            f.nombre,
            str(f.nivel),
            f"{f.saldo_inicial:.2f}".replace(".", ",")  # Formato numérico para Excel hispano
        ]
        for m in meses:
            val = f.saldos_mensuales.get(m, 0.0)
            row_data.append(f"{val:.2f}".replace(".", ","))
            
        output.write(";".join(row_data) + "\n")
        
    csv_data = output.getvalue()
    output.close()
    
    return Response(
        content=csv_data.encode('utf-8-sig'),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=comparacion_saldos_mensuales.csv"
        }
    )

def generate_comparacion_saldos_pdf(db: Session, empresa_id: int, filtros: FiltrosComparacionSaldos) -> Response:
    """
    Genera el archivo PDF premium utilizando WeasyPrint con una plantilla estructurada
    para visualización horizontal A4 landscape y alta densidad de columnas.
    """
    # 1. Obtener datos y empresa
    report_data = generate_comparacion_saldos_report(db, empresa_id, filtros)
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    
    meses: List[int] = report_data["meses"]
    filas: List[FilaComparacionSaldos] = report_data["filas"]
    
    mes_inicio = meses[0] if meses else 1
    mes_fin = meses[-1] if meses else 12
    
    fecha_generacion = datetime.now().strftime("%d/%m/%Y %I:%M %p")
    
    # 2. Formateador numérico
    def format_money(val: float) -> str:
        if val is None:
            val = 0.0
        return f"${val:,.2f}"
        
    # Calcular el número de columnas para ajustar dinámicamente el tamaño de fuente
    num_columnas = len(meses)
    tam_fuente = "8px"
    if num_columnas > 8:
        tam_fuente = "7px"
    elif num_columnas <= 4:
        tam_fuente = "9px"
        
    # 3. Construir la plantilla HTML premium para WeasyPrint
    html_template = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: A4 landscape;
                margin: 8mm 8mm 12mm 8mm;
                @bottom-right {{
                    content: "Página " counter(page) " de " counter(pages);
                    font-family: 'DM Sans', sans-serif;
                    font-size: 7px;
                    color: #64748b;
                }}
                @bottom-left {{
                    content: "Finaxis Cloud ERP - Generado el {fecha_generacion}";
                    font-family: 'DM Sans', sans-serif;
                    font-size: 7px;
                    color: #64748b;
                }}
            }}
            
            body {{
                font-family: 'DM Sans', 'Helvetica Neue', Arial, sans-serif;
                margin: 0;
                padding: 0;
                color: #0f172a;
                background: #ffffff;
                font-size: {tam_fuente};
                line-height: 1.2;
            }}
            
            /* Encabezado Principal */
            .header-container {{
                border-bottom: 2px solid #e2e8f0;
                padding-bottom: 5px;
                margin-bottom: 10px;
                display: block;
                width: 100%;
            }}
            
            .header-table {{
                width: 100%;
                border-collapse: collapse;
            }}
            
            .header-table td {{
                border: none;
                padding: 0;
            }}
            
            .empresa-title {{
                font-size: 13px;
                font-weight: 700;
                color: #1e293b;
                text-transform: uppercase;
                margin: 0;
            }}
            
            .empresa-nit {{
                font-size: 8px;
                color: #64748b;
                margin: 2px 0 0 0;
            }}
            
            .report-title {{
                font-size: 12px;
                font-weight: 700;
                color: #0f172a;
                text-align: right;
                margin: 0;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            .report-subtitle {{
                font-size: 8px;
                color: #0284c7;
                text-align: right;
                font-weight: 600;
                margin: 2px 0 0 0;
            }}
            
            /* Filtros Aplicados */
            .filters-badge {{
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                padding: 4px 8px;
                margin-bottom: 10px;
                font-size: 7px;
                color: #475569;
                display: block;
            }}
            
            /* Tabla del Reporte */
            .report-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 5px;
            }}
            
            .report-table th {{
                background-color: #0f172a;
                color: #ffffff;
                font-weight: 700;
                text-transform: uppercase;
                font-size: 7.5px;
                padding: 5px 4px;
                border: 1px solid #1e293b;
                text-align: left;
            }}
            
            .report-table th.num-col {{
                text-align: right;
            }}
            
            .report-table td {{
                padding: 4px 4px;
                border-bottom: 1px solid #f1f5f9;
                border-left: 1px solid #f1f5f9;
                border-right: 1px solid #f1f5f9;
            }}
            
            .report-table td.num-col {{
                text-align: right;
            }}
            
            /* Estilos Jerárquicos */
            .nivel-1 {{
                font-weight: 700;
                background-color: #f8fafc;
                color: #0f172a;
            }}
            
            .nivel-1 td {{
                border-top: 1px solid #cbd5e1;
                border-bottom: 1px solid #cbd5e1;
                padding-top: 6px;
                padding-bottom: 6px;
            }}
            
            .nivel-2 {{
                font-weight: 600;
                background-color: #ffffff;
                color: #1e293b;
            }}
            
            .nivel-3 {{
                font-weight: 600;
                color: #334155;
            }}
            
            .nivel-auxiliar {{
                color: #475569;
                font-weight: 400;
            }}
            
            .codigo-col {{
                font-family: monospace;
                font-size: 7.5px;
                letter-spacing: -0.2px;
            }}
            
            .nombre-col {{
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                max-width: 180px;
            }}
            
            .zebra-row {{
                background-color: #f8fafc;
            }}
        </style>
    </head>
    <body>
        <div class="header-container">
            <table class="header-table">
                <tr>
                    <td>
                        <h1 class="empresa-title">{empresa.razon_social if empresa else "EMPRESA LOCAL SAS"}</h1>
                        <p class="empresa-nit">NIT: {empresa.nit if empresa else "900.000.000-0"}</p>
                    </td>
                    <td>
                        <h2 class="report-title">Comparación Mensual de Saldos</h2>
                        <p class="report-subtitle">Año {filtros.anio} • Meses {NOMBRES_MESES.get(mes_inicio)} a {NOMBRES_MESES.get(mes_fin)}</p>
                    </td>
                </tr>
            </table>
        </div>
        
        <div class="filters-badge">
            <strong>Filtros activos:</strong> Nivel Máximo: {filtros.nivel_maximo or 9} | 
            Cuenta Base: {filtros.cuenta_codigo or 'Todas'} | 
            Tipo Cuentas: {filtros.tipo_filtro or 'Todas'}
        </div>
        
        <table class="report-table">
            <thead>
                <tr>
                    <th style="width: 50px;">Código</th>
                    <th style="width: 180px;">Nombre Cuenta</th>
                    <th class="num-col" style="width: 70px;">Saldo Inicial</th>
                    {"".join(f'<th class="num-col">{NOMBRES_MESES.get(m, f"Mes {m}")}</th>' for m in meses)}
                </tr>
            </thead>
            <tbody>
    """
    
    # Rellenar filas
    for i, f in enumerate(filas):
        # Determinar clase de estilo de nivel
        if f.nivel == 1:
            row_class = "nivel-1"
        elif f.nivel == 2:
            row_class = "nivel-2"
        elif f.nivel == 3:
            row_class = "nivel-3"
        else:
            row_class = "nivel-auxiliar"
            if i % 2 == 0:
                row_class += " zebra-row"
                
        # Sangrado visual para el nombre
        indent = "&nbsp;" * (f.nivel - 1) * 2
        
        html_template += f"""
                <tr class="{row_class}">
                    <td class="codigo-col">{f.codigo}</td>
                    <td class="nombre-col">{indent}{f.nombre}</td>
                    <td class="num-col">{format_money(f.saldo_inicial)}</td>
        """
        for m in meses:
            val = f.saldos_mensuales.get(m, 0.0)
            html_template += f'<td class="num-col">{format_money(val)}</td>'
            
        html_template += "</tr>"
        
    html_template += """
            </tbody>
        </table>
    </body>
    </html>
    """
    
    # 4. Compilar a PDF con WeasyPrint
    pdf_bytes = HTML(string=html_template).write_pdf()
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "inline; filename=comparacion_saldos_mensuales.pdf"
        }
    )
