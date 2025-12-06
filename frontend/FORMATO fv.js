<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <style>
        /* RESET Y BASE */
        body { font-family: 'Helvetica', sans-serif; font-size: 12px; color: #333; margin: 0; padding: 30px; }
        
        /* HEADER EMPRESA (Lado Izquierdo) */
        .header-table { width: 100%; border-collapse: collapse; margin-bottom: 30px; }
        .company-name { font-size: 18px; font-weight: bold; color: #000; margin-top: 10px; text-transform: uppercase; }
        .company-data { font-size: 11px; color: #555; line-height: 1.3; }

        /* CAJA FACTURA (Lado Derecho) */
        .invoice-box { 
            border: 1px solid #ccc; 
            border-radius: 8px; 
            overflow: hidden; 
            text-align: center; 
            width: 200px; 
            float: right; 
        }
        .invoice-title { 
            background: #eee; 
            color: #000; 
            padding: 8px; 
            font-weight: bold; 
            font-size: 14px; 
            border-bottom: 1px solid #ccc;
            text-transform: uppercase;
        }
        .invoice-data { padding: 10px; }
        .invoice-number { font-size: 20px; color: #d32f2f; font-weight: bold; margin-bottom: 5px; }
        .invoice-date { font-size: 11px; color: #666; }

        /* INFO CLIENTE */
        .client-section { 
            clear: both; 
            margin-top: 20px; 
            border-top: 2px solid #000; 
            border-bottom: 1px solid #ddd; 
            padding: 15px 0; 
            display: flex; 
            justify-content: space-between;
        }
        .label { font-weight: bold; color: #666; width: 70px; display: inline-block; }

        /* TABLA PRODUCTOS */
        .items-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        .items-table th { 
            background: #000; 
            color: #fff; 
            padding: 8px; 
            font-size: 11px; 
            text-align: left; 
            text-transform: uppercase;
        }
        .items-table td { 
            padding: 8px; 
            border-bottom: 1px solid #eee; 
            font-size: 11px; 
        }
        .text-right { text-align: right; }
        .font-mono { font-family: 'Courier New', monospace; }

        /* TOTALES Y PIE */
        .footer-section { margin-top: 20px; width: 100%; display: table; }
        .footer-left { display: table-cell; width: 60%; vertical-align: top; padding-right: 20px; }
        .footer-right { display: table-cell; width: 40%; vertical-align: top; }

        .amount-text { 
            font-weight: bold; 
            font-style: italic; 
            background: #f9f9f9; 
            padding: 10px; 
            border-left: 4px solid #000; 
            margin-bottom: 15px;
            font-size: 11px;
        }

        .totals-table { width: 100%; border-collapse: collapse; }
        .totals-table td { padding: 5px; text-align: right; font-size: 12px; }
        .total-label { font-weight: bold; color: #555; }
        .total-value { font-family: 'Courier New', monospace; font-weight: bold; }
        
        .grand-total { 
            background: #eee; 
            border-top: 2px solid #000; 
            font-size: 14px; 
            color: #000; 
            padding: 10px 5px;
        }

        .legal-text { 
            margin-top: 40px; 
            font-size: 9px; 
            color: #777; 
            text-align: center; 
            border-top: 1px solid #ddd; 
            padding-top: 10px; 
        }
    </style>
</head>
<body>

    <table class="header-table">
        <tr>
            <td width="60%" valign="top">
                {% if empresa.logo_url %}
                    <img src="{{empresa.logo_url}}" style="height: 70px; margin-bottom: 10px;">
                {% endif %}
                <div class="company-name">{{empresa.razon_social}}</div>
                <div class="company-data">
                    NIT: {{empresa.nit}}<br>
                    {{empresa.direccion}}<br>
                    Tel: {{empresa.telefono}}<br>
                    {{empresa.email}}
                </div>
            </td>
            <td width="40%" valign="top" align="right">
                <div class="invoice-box">
                    <div class="invoice-title">{{documento.tipo_nombre}}</div>
                    <div class="invoice-data">
                        <div class="invoice-number">N° {{documento.consecutivo}}</div>
                        <div class="invoice-date">Fecha: <strong>{{documento.fecha_emision}}</strong></div>
                        {% if documento.fecha_vencimiento %}
                        <div class="invoice-date">Vence: {{documento.fecha_vencimiento}}</div>
                        {% endif %}
                    </div>
                </div>
            </td>
        </tr>
    </table>

    <div class="client-section">
        <table width="100%">
            <tr>
                <td width="55%">
                    <div><span class="label">Cliente:</span> <strong>{{tercero.razon_social}}</strong></div>
                    <div><span class="label">NIT/CC:</span> {{tercero.nit}}</div>
                    <div><span class="label">Dirección:</span> {{tercero.direccion}}</div>
                </td>
                <td width="45%" valign="top">
                    <div><span class="label">Teléfono:</span> {{tercero.telefono}}</div>
                    </td>
            </tr>
        </table>
    </div>

    <table class="items-table">
        <thead>
            <tr>
                <th width="15%">Código</th>
                <th width="45%">Descripción del Producto / Servicio</th>
                <th width="10%" class="text-right">Cant</th>
                <th width="15%" class="text-right">Vr. Unitario</th>
                <th width="15%" class="text-right">Total</th>
            </tr>
        </thead>
        <tbody>
            {% for item in items %}
            <tr>
                <td>{{item.producto_codigo}}</td>
                <td>{{item.producto_nombre}}</td>
                <td class="text-right font-mono">{{item.cantidad}}</td>
                <td class="text-right font-mono">{{item.precio_unitario}}</td>
                <td class="text-right font-mono">{{item.subtotal}}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <div class="footer-section">
        <div class="footer-left">
            <div class="amount-text">
                SON: {{totales.valor_letras}}
            </div>
            {% if documento.observaciones %}
            <div style="font-size: 10px; border: 1px dashed #ccc; padding: 5px;">
                <strong>Notas / Observaciones:</strong><br>
                {{documento.observaciones}}
            </div>
            {% endif %}
        </div>
        
        <div class="footer-right">
            <table class="totals-table">
                <tr>
                    <td class="total-label">Subtotal:</td>
                    <td class="total-value">{{totales.subtotal}}</td>
                </tr>
                <tr>
                    <td class="total-label">IVA / Impuestos:</td>
                    <td class="total-value">{{totales.impuestos}}</td>
                </tr>
                <tr>
                    <td class="total-label grand-total">TOTAL A PAGAR:</td>
                    <td class="total-value grand-total">{{totales.total}}</td>
                </tr>
            </table>
        </div>
    </div>

    <div class="legal-text">
        Autorización de Facturación DIAN No. 18760000001. Rango Autorizado del 1 al 5000.<br>
        Esta factura de venta se asimila en todos sus efectos a una letra de cambio según el Art. 774 del Código de Comercio.<br>
        Impreso por Software ContaPY
    </div>

</body>
</html>