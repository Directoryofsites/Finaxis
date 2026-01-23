
def generar_pdf_cartera_detallada(db: Session, empresa_id: int, unidad_id: int):
    from weasyprint import HTML
    from app.models.empresa import Empresa
    from datetime import date
    import locale
    
    # Obtener datos
    try:
        detalle = get_cartera_ph_pendientes_detallada(db, empresa_id, unidad_id)
        unidad = db.query(PHUnidad).filter(PHUnidad.id == unidad_id).first()
        empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
        
        propietario_nombre = "Desconocido"
        if unidad and unidad.propietario_principal:
            propietario_nombre = unidad.propietario_principal.razon_social
            
        total = sum(d['saldo'] for d in detalle)
        fecha_impresion = date.today().strftime('%Y-%m-%d')
        
    except Exception as e:
        print(f"Error obteniendo datos para PDF: {e}")
        return HTML(string=f"<h1>Error generando reporte</h1><p>{str(e)}</p>").write_pdf()

    # Plantilla HTML Inline
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            @page {{ size: letter; margin: 2cm; }}
            body {{ font-family: sans-serif; font-size: 12px; color: #333; }}
            .header {{ text-align: center; margin-bottom: 30px; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
            .header h1 {{ margin: 0; font-size: 18px; color: #2c3e50; }}
            .header h2 {{ margin: 5px 0; font-size: 14px; font-weight: normal; }}
            .info-box {{ margin-bottom: 20px; background: #f9f9f9; padding: 15px; border-radius: 5px; }}
            .info-row {{ display: flex; justify-content: space-between; margin-bottom: 5px; }}
            .label {{ font-weight: bold; color: #666; }}
            
            table {{ w-width: 100%; border-collapse: collapse; margin-top: 20px; width: 100%; }}
            th {{ background: #2c3e50; color: white; padding: 10px; text-align: left; font-size: 11px; text-transform: uppercase; }}
            td {{ padding: 10px; border-bottom: 1px solid #eee; }}
            tr:last-child td {{ border-bottom: 2px solid #333; }}
            
            .amount {{ text-align: right; font-family: monospace; font-size: 13px; }}
            .total-row {{ background: #eee; font-weight: bold; }}
            .total-row td {{ border-top: 2px solid #333; }}
            
            .badge {{ padding: 2px 6px; border-radius: 4px; font-size: 10px; color: white; display: inline-block; width: 60px; text-align: center; }}
            .bg-INTERES {{ background: #dc3545; }} 
            .bg-MULTA {{ background: #fd7e14; }}
            .bg-CAPITAL {{ background: #0d6efd; }}
            
            .footer {{ margin-top: 40px; font-size: 10px; color: #999; text-align: center; border-top: 1px solid #eee; padding-top: 10px; }}
            .disclaimer {{ background: #fff3cd; color: #856404; padding: 10px; border-radius: 5px; font-size: 10px; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{empresa.razon_social if empresa else 'Empresa'}</h1>
            <h2>NIT: {empresa.nit if empresa else ''}</h2>
            <h3>Relación Detallada de Cartera por Concepto</h3>
        </div>
        
        <div class="info-box">
            <div class="info-row">
                <div><span class="label">Unidad:</span> {unidad.codigo if unidad else 'N/A'}</div>
                <div><span class="label">Fecha:</span> {fecha_impresion}</div>
            </div>
            <div class="info-row">
                <div><span class="label">Propietario:</span> {propietario_nombre}</div>
            </div>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Concepto</th>
                    <th width="100">Tipo</th>
                    <th width="150" style="text-align: right">Saldo Pendiente</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for item in detalle:
        badge_class = f"bg-{item['tipo']}"
        html_template += f"""
                <tr>
                    <td>{item['concepto']}</td>
                    <td><span class="badge {badge_class}">{item['tipo']}</span></td>
                    <td class="amount">${item['saldo']:,.0f}</td>
                </tr>
        """
        
    html_template += f"""
                <tr class="total-row">
                    <td colspan="2" style="text-align: right; padding-right: 20px;">TOTAL GENERAL</td>
                    <td class="amount">${total:,.0f}</td>
                </tr>
            </tbody>
        </table>
        
        <div class="disclaimer">
            <strong>Nota Explicativa:</strong> Este reporte presenta la composición del saldo pendiente aplicando virtualmente los pagos realizados en el siguiente orden de prelación: 
            1. Intereses de Mora, 2. Multas y Sanciones, 3. Capital y Expensas Comunes.
        </div>
        
        <div class="footer">
            Generado automáticamente por el sistema contable
        </div>
    </body>
    </html>
    """
    
    return HTML(string=html_template).write_pdf()
