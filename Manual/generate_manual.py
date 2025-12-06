import os
import re
import base64
import glob

# Configuration
MANUAL_DIR = r"c:\ContaPY2\Manual"
OUTPUT_FILE = os.path.join(MANUAL_DIR, "manual_completo.html")

# Thematic Groups
GROUPS = {
    "Configuración y Maestros": [
        "capitulo_5_empresas.md",
        "capitulo_1_puc.md", "capitulo_2_tipos_documento.md", "capitulo_3_plantillas.md",
        "capitulo_4_conceptos.md", "capitulo_34_gestion_terceros.md", "capitulo_50_centros_de_costo.md"
    ],
    "Operación Diaria": [
        "capitulo_24_nuevo_documento.md", "capitulo_25_captura_rapida.md",
        "capitulo_26_explorador.md", "capitulo_40_compras.md", "capitulo_41_facturacion.md"
    ],
    "Reportes Contables": [
        "capitulo_27_libro_diario.md", "capitulo_28_balance_general.md", "capitulo_29_estado_resultados.md",
        "capitulo_30_balance_prueba.md", "capitulo_31_auxiliar_cuenta.md", "capitulo_32_libros_oficiales.md",
        "capitulo_33_super_informe.md", "capitulo_51_auxiliar_cc_cuenta.md", "capitulo_52_balance_general_cc.md",
        "capitulo_53_estado_resultados_cc_detallado.md", "capitulo_54_balance_prueba_cc.md", "capitulo_55_analisis_financiero.md"
    ],
    "Terceros y Cartera": [
        "capitulo_35_tercero_cuenta.md", "capitulo_36_estado_cuenta_cliente.md", "capitulo_37_auxiliar_cartera.md",
        "virtual_estado_cuenta_proveedor.md", "virtual_auxiliar_proveedor.md"
    ],
    "Inventario y Logística": [
        "capitulo_38_gestion_inventario.md", "capitulo_39_parametros_inventario.md",
        "capitulo_42_traslados.md", "capitulo_43_ajuste_inventario.md",
        "capitulo_44_rentabilidad_producto.md", "capitulo_45_movimiento_analitico.md", "capitulo_46_kardex_detallado.md",
        "capitulo_47_super_informe_inventarios.md", "capitulo_48_gestion_topes.md", "capitulo_49_gestion_ventas.md"
    ],
    "Utilidades": [
        "capitulo_60_edicion_documentos.md",
        "capitulo_61_recodificacion_masiva.md",
        "capitulo_62_papelera_reciclaje.md",
        "capitulo_63_control_cierre.md"
    ]
}

# Virtual Files Configuration
VIRTUAL_FILES = {
    "virtual_estado_cuenta_proveedor.md": {
        "source": "capitulo_36_estado_cuenta_cliente.md",
        "title": "Estado Cuenta Proveedor",
        "replacements": [
            ("Cliente", "Proveedor"),
            ("cliente", "proveedor"),
            ("Cartera", "Cuentas por Pagar"),
            ("cartera", "cuentas por pagar"),
            ("Cobrar", "Pagar")
        ]
    },
    "virtual_auxiliar_proveedor.md": {
        "source": "capitulo_37_auxiliar_cartera.md",
        "title": "Auxiliar Proveedores",
        "replacements": [
            ("Cliente", "Proveedor"),
            ("cliente", "proveedor"),
            ("Cartera", "Proveedores"),
            ("cartera", "proveedores")
        ]
    }
}

def md_to_html(text):
    # Basic MD to HTML conversion
    html = text
    
    # 1. Remove Chapter Numbers from Content (e.g., "Capítulo 53: ...")
    html = re.sub(r'Capítulo \d+[:\s-]*', '', html, flags=re.IGNORECASE)
    html = re.sub(r'Manual de Usuario - ', '', html, flags=re.IGNORECASE)
    
    # Escape HTML characters to prevent issues
    html = html.replace("<", "&lt;").replace(">", "&gt;")
    
    # --- TABLE PARSING ---
    def parse_tables(text):
        lines = text.split('\n')
        new_lines = []
        in_table = False
        table_buffer = []
        
        for line in lines:
            if line.strip().startswith('|'):
                in_table = True
                table_buffer.append(line)
            else:
                if in_table:
                    # Process the buffered table
                    if len(table_buffer) >= 2:
                        new_lines.append('<div class="table-container"><table>')
                        # Header
                        header_row = table_buffer[0].strip().strip('|').split('|')
                        new_lines.append('<thead><tr>')
                        for cell in header_row:
                            new_lines.append(f'<th>{cell.strip()}</th>')
                        new_lines.append('</tr></thead>')
                        
                        # Body
                        new_lines.append('<tbody>')
                        # Skip separator line (index 1)
                        for row in table_buffer[2:]:
                            cols = row.strip().strip('|').split('|')
                            new_lines.append('<tr>')
                            for cell in cols:
                                new_lines.append(f'<td>{cell.strip()}</td>')
                            new_lines.append('</tr>')
                        new_lines.append('</tbody></table></div>')
                    else:
                        # Not a valid table, just append lines
                        new_lines.extend(table_buffer)
                    
                    in_table = False
                    table_buffer = []
                    new_lines.append(line)
                else:
                    new_lines.append(line)
        
        if in_table:
             # Process remaining table at end of file
            if len(table_buffer) >= 2:
                new_lines.append('<div class="table-container"><table>')
                header_row = table_buffer[0].strip().strip('|').split('|')
                new_lines.append('<thead><tr>')
                for cell in header_row:
                    new_lines.append(f'<th>{cell.strip()}</th>')
                new_lines.append('</tr></thead>')
                new_lines.append('<tbody>')
                for row in table_buffer[2:]:
                    cols = row.strip().strip('|').split('|')
                    new_lines.append('<tr>')
                    for cell in cols:
                        new_lines.append(f'<td>{cell.strip()}</td>')
                    new_lines.append('</tr>')
                new_lines.append('</tbody></table></div>')
            else:
                new_lines.extend(table_buffer)
                
        return '\n'.join(new_lines)

    html = parse_tables(html)
    # ---------------------
    
    # Headers
    html = re.sub(r'^# (.*)', r'<h1 class="chapter-title">\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.*)', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.*)', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^#### (.*)', r'<h4>\1</h4>', html, flags=re.MULTILINE)
    
    # Bold
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    
    # Italic
    html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
    
    # Blockquotes / Alerts
    def blockquote_replacer(match):
        content = match.group(1)
        # Check for alert types
        alert_type = "info"
        if "[!TIP]" in content: alert_type = "success"; content = content.replace("[!TIP]", "").strip()
        elif "[!WARNING]" in content: alert_type = "warning"; content = content.replace("[!WARNING]", "").strip()
        elif "[!CAUTION]" in content: alert_type = "danger"; content = content.replace("[!CAUTION]", "").strip()
        elif "[!NOTE]" in content: alert_type = "info"; content = content.replace("[!NOTE]", "").strip()
        elif "[!IMPORTANT]" in content: alert_type = "warning"; content = content.replace("[!IMPORTANT]", "").strip()
        
        return f'<div class="alert alert-{alert_type}">{content}</div>'

    html = re.sub(r'^> (.*)', blockquote_replacer, html, flags=re.MULTILINE)
    
    # Lists
    lines = html.split('\n')
    new_lines = []
    in_list = False
    for line in lines:
        # Check if line is inside a table or html tag we just added
        if line.strip().startswith('<'):
             if in_list:
                new_lines.append('</ul>')
                in_list = False
             new_lines.append(line)
             continue

        if line.strip().startswith('* ') or line.strip().startswith('- '):
            if not in_list:
                new_lines.append('<ul>')
                in_list = True
            content = line.strip()[2:]
            content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
            new_lines.append(f'<li>{content}</li>')
        else:
            if in_list:
                new_lines.append('</ul>')
                in_list = False
            new_lines.append(line)
    if in_list:
        new_lines.append('</ul>')
    html = '\n'.join(new_lines)
    
    # Images
    def img_replacer(match):
        alt = match.group(1)
        path = match.group(2)
        try:
            if path.startswith("file:///"): path = path.replace("file:///", "")
            if not os.path.isabs(path):
                path = os.path.join(MANUAL_DIR, path)
            if os.path.exists(path):
                with open(path, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode('utf-8')
                    ext = os.path.splitext(path)[1].replace('.', '')
                    if ext == 'jpg': ext = 'jpeg'
                    return f'<div class="img-container"><img src="data:image/{ext};base64,{encoded}" alt="{alt}" class="manual-img"><p class="img-caption">{alt}</p></div>'
        except Exception as e:
            print(f"Error embedding image {path}: {e}")
        return f'<div class="img-container"><img src="{path}" alt="{alt}" class="manual-img"><p class="img-caption">{alt}</p></div>'
    
    html = re.sub(r'!\[(.*?)\]\((.*?)\)', img_replacer, html)
    
    # Horizontal Rules
    html = re.sub(r'^---', r'<hr>', html, flags=re.MULTILINE)
    
    return html

def generate_html():
    css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        
        :root {
            --primary: #2563eb;
            --secondary: #1e40af;
            --bg: #f1f5f9;
            --text: #334155;
            --sidebar-width: 320px;
            --sidebar-bg: #1e293b;
            --sidebar-text: #e2e8f0;
        }
        body {
            font-family: 'Inter', 'Segoe UI', sans-serif;
            margin: 0;
            padding: 0;
            background-color: var(--bg);
            color: var(--text);
            display: flex;
            height: 100vh;
            overflow: hidden;
        }
        /* Sidebar */
        .sidebar {
            width: var(--sidebar-width);
            background: var(--sidebar-bg);
            color: var(--sidebar-text);
            overflow-y: auto;
            padding: 2rem 1.5rem;
            flex-shrink: 0;
            box-shadow: 4px 0 10px rgba(0,0,0,0.1);
        }
        .sidebar h1 {
            font-size: 1.8rem;
            color: white;
            margin-bottom: 2.5rem;
            padding-left: 0.5rem;
            border-bottom: 1px solid #334155;
            padding-bottom: 1rem;
            font-weight: 700;
            letter-spacing: -0.02em;
        }
        .nav-group {
            margin-bottom: 2rem;
        }
        .nav-group-title {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #94a3b8;
            font-weight: 700;
            margin-bottom: 0.75rem;
            padding-left: 0.75rem;
        }
        .nav-link {
            display: flex;
            align-items: center;
            padding: 0.6rem 0.75rem;
            color: #cbd5e1;
            text-decoration: none;
            border-radius: 0.5rem;
            transition: all 0.2s ease;
            font-size: 0.95rem;
            font-weight: 400;
            margin-bottom: 0.25rem;
        }
        .nav-link::before {
            content: "•";
            margin-right: 0.75rem;
            color: #64748b;
            font-size: 1.2rem;
            line-height: 0;
        }
        .nav-link:hover {
            background-color: #334155;
            color: white;
            transform: translateX(4px);
        }
        .nav-link:hover::before {
            color: var(--primary);
        }
        .nav-link.active {
            background-color: var(--primary);
            color: white;
            font-weight: 600;
        }
        .nav-link.active::before {
            color: white;
        }
        
        /* Main Content */
        .main {
            flex: 1;
            overflow-y: auto;
            padding: 4rem 6rem;
            scroll-behavior: smooth;
        }
        .content-container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 5rem;
            border-radius: 1.5rem;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
        }
        
        /* Typography */
        h1.chapter-title {
            font-size: 2.8rem;
            color: #0f172a;
            margin-top: 5rem;
            margin-bottom: 2rem;
            border-bottom: 3px solid #e2e8f0;
            padding-bottom: 1rem;
            font-weight: 800;
            letter-spacing: -0.03em;
        }
        h2 {
            font-size: 2rem;
            color: var(--primary);
            margin-top: 3rem;
            margin-bottom: 1.25rem;
            font-weight: 700;
        }
        h3 {
            font-size: 1.5rem;
            color: #334155;
            margin-top: 2.5rem;
            margin-bottom: 1rem;
            font-weight: 600;
        }
        h4 {
            font-size: 1.2rem;
            color: #475569;
            margin-top: 2rem;
            margin-bottom: 0.75rem;
            font-weight: 600;
        }
        p, li {
            line-height: 1.8;
            font-size: 1.05rem;
            color: #475569;
            margin-bottom: 1.25rem;
        }
        ul {
            padding-left: 1.5rem;
            margin-bottom: 1.5rem;
        }
        li {
            margin-bottom: 0.5rem;
        }
        strong {
            color: #0f172a;
            font-weight: 700;
        }
        hr {
            border: 0;
            height: 1px;
            background: #e2e8f0;
            margin: 4rem 0;
        }
        
        /* Images */
        .img-container {
            margin: 3rem 0;
            text-align: center;
            background: #f8fafc;
            padding: 1rem;
            border-radius: 1rem;
        }
        .manual-img {
            max-width: 100%;
            border-radius: 0.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            border: 1px solid #e2e8f0;
        }
        .img-caption {
            font-size: 0.9rem;
            color: #64748b;
            margin-top: 1rem;
            font-style: italic;
            font-weight: 500;
        }
        
        /* Note Badge */
        .system-note {
            display: inline-block;
            background: #eff6ff;
            color: var(--primary);
            padding: 0.35rem 1rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 700;
            margin-bottom: 1.5rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border: 1px solid #bfdbfe;
        }
        
        /* Tables */
        .table-container {
            overflow-x: auto;
            margin: 2.5rem 0;
            border-radius: 0.75rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            border: 1px solid #e2e8f0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            font-size: 0.95rem;
        }
        th {
            background-color: #f1f5f9;
            color: #0f172a;
            font-weight: 700;
            text-align: left;
            padding: 1rem 1.25rem;
            border-bottom: 2px solid #e2e8f0;
            text-transform: uppercase;
            font-size: 0.85rem;
            letter-spacing: 0.05em;
        }
        td {
            padding: 1rem 1.25rem;
            border-bottom: 1px solid #e2e8f0;
            color: #334155;
        }
        tr:last-child td {
            border-bottom: none;
        }
        tr:hover td {
            background-color: #f8fafc;
        }
        
        /* Alerts */
        .alert {
            padding: 1.25rem;
            margin-bottom: 1.5rem;
            border-radius: 0.75rem;
            border-left: 5px solid;
            font-size: 1rem;
            display: flex;
            align-items: start;
        }
        .alert-info {
            background-color: #eff6ff;
            border-color: #3b82f6;
            color: #1e40af;
        }
        .alert-success {
            background-color: #f0fdf4;
            border-color: #22c55e;
            color: #15803d;
        }
        .alert-warning {
            background-color: #fefce8;
            border-color: #eab308;
            color: #854d0e;
        }
        .alert-danger {
            background-color: #fef2f2;
            border-color: #ef4444;
            color: #991b1b;
        }
    </style>
    """
    
    html_content = [f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Manual de Usuario - ContaPY</title>
        {css}
    </head>
    <body>
        <nav class="sidebar">
            <h1>ContaPY Manual</h1>
    """]
    
    # Build Sidebar
    for group_name, files in GROUPS.items():
        html_content.append(f'<div class="nav-group"><div class="nav-group-title">{group_name}</div>')
        for filename in files:
            # Create a readable ID
            file_id = filename.replace('.md', '')
            
            # Title Generation
            if filename in VIRTUAL_FILES:
                title = VIRTUAL_FILES[filename]["title"]
            else:
                # Remove 'capitulo_', extension, underscores, and then leading numbers
                title = filename.replace('capitulo_', '').replace('.md', '').replace('_', ' ')
                title = re.sub(r'^\d+\s*', '', title).title()
                
            html_content.append(f'<a href="#{file_id}" class="nav-link">{title}</a>')
        html_content.append('</div>')
    
    html_content.append("""
        </nav>
        <main class="main">
            <div class="content-container">
                <div style="text-align: center; margin-bottom: 8rem;">
                    <h1 style="font-size: 5rem; color: var(--primary); margin-bottom: 1.5rem; letter-spacing: -0.05em;">Manual de Usuario</h1>
                    <p style="font-size: 1.8rem; color: #64748b; font-weight: 300;">Sistema Contable ContaPY v1.0</p>
                    <div style="margin-top: 4rem; display: inline-block; padding: 1rem 2rem; background: #f1f5f9; border-radius: 2rem; color: #475569; font-weight: 600;">
                        Documentación Oficial Unificada
                    </div>
                </div>
    """)
    
    # Build Content
    for group_name, files in GROUPS.items():
        html_content.append(f'<div class="group-section"><h1 style="font-size: 3.5rem; color: #0f172a; margin: 8rem 0 4rem 0; border-bottom: 5px solid var(--primary); display: inline-block; letter-spacing: -0.03em;">{group_name}</h1></div>')
        
        for filename in files:
            file_id = filename.replace('.md', '')
            content = ""
            
            # Handle Virtual Files
            if filename in VIRTUAL_FILES:
                v_config = VIRTUAL_FILES[filename]
                source_path = os.path.join(MANUAL_DIR, v_config["source"])
                if os.path.exists(source_path):
                    with open(source_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Apply Replacements
                    for old, new in v_config["replacements"]:
                        content = content.replace(old, new)
                else:
                    print(f"Warning: Source file {v_config['source']} for virtual file {filename} not found.")
                    continue
            else:
                # Handle Regular Files
                file_path = os.path.join(MANUAL_DIR, filename)
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                else:
                    print(f"Warning: File {filename} not found.")
                    continue
            
            converted_html = md_to_html(content)
            
            html_content.append(f'<div id="{file_id}" class="chapter-container">')
            html_content.append(f'<div class="system-note">Módulo: {group_name}</div>')
            html_content.append(converted_html)
            html_content.append('</div><hr>')
                
    html_content.append("""
            </div>
        </main>
    </body>
    </html>
    """)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(''.join(html_content))
        
    print(f"Successfully generated {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_html()
