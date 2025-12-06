import os
import sys
import re

# Add current directory to path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from generate_manual import GROUPS, VIRTUAL_FILES, md_to_html
    from generate_faq import FAQ_DATA
except ImportError as e:
    print(f"Error importing modules: {e}")
    # Fallback or exit
    sys.exit(1)

MANUAL_DIR = r"c:\ContaPY2\Manual"
OUTPUT_FILE = os.path.join(MANUAL_DIR, "manual_movil.html")

def generate_mobile_html():
    css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        
        :root {
            --primary: #2563eb;
            --bg: #ffffff;
            --text: #1e293b;
            --gray-100: #f1f5f9;
            --gray-200: #e2e8f0;
        }
        
        * {
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', sans-serif;
            margin: 0;
            padding: 0;
            background-color: var(--bg);
            color: var(--text);
            font-size: 18px; /* Larger base font for mobile */
            line-height: 1.6;
        }

        /* Mobile Header */
        .mobile-header {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 60px;
            background: var(--primary);
            color: white;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 1rem;
            z-index: 1000;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .header-title {
            font-weight: 700;
            font-size: 1.2rem;
        }

        .menu-toggle {
            background: none;
            border: none;
            color: white;
            font-size: 1.5rem;
            cursor: pointer;
        }

        /* Navigation Menu (Overlay) */
        .nav-overlay {
            position: fixed;
            top: 60px;
            left: 0;
            right: 0;
            bottom: 0;
            background: white;
            z-index: 999;
            overflow-y: auto;
            display: none; /* Hidden by default */
            padding: 1rem;
        }

        .nav-overlay.active {
            display: block;
        }

        .nav-group-title {
            font-size: 0.9rem;
            text-transform: uppercase;
            color: #94a3b8;
            font-weight: 700;
            margin-top: 1.5rem;
            margin-bottom: 0.5rem;
            border-bottom: 1px solid var(--gray-200);
            padding-bottom: 0.25rem;
        }

        .nav-link {
            display: block;
            padding: 0.75rem 0;
            color: var(--text);
            text-decoration: none;
            font-weight: 500;
            border-bottom: 1px solid var(--gray-100);
        }

        .nav-link:active {
            background-color: var(--gray-100);
        }

        /* Main Content */
        .main-content {
            margin-top: 60px; /* Space for header */
            padding: 1.5rem;
        }

        h1 { font-size: 2rem; color: var(--primary); margin-top: 2rem; line-height: 1.2; }
        h2 { font-size: 1.5rem; margin-top: 1.5rem; color: #334155; }
        h3 { font-size: 1.25rem; color: #475569; }
        
        p, li { margin-bottom: 1rem; }
        
        img { max-width: 100%; height: auto; border-radius: 0.5rem; }

        /* Tables responsive */
        .table-container {
            overflow-x: auto;
            margin-bottom: 1.5rem;
            border: 1px solid var(--gray-200);
            border-radius: 0.5rem;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            min-width: 500px; /* Force scroll on small screens */
        }
        
        th, td {
            padding: 0.75rem;
            border-bottom: 1px solid var(--gray-200);
            text-align: left;
            font-size: 0.9rem;
        }
        
        th { background: var(--gray-100); font-weight: 600; }

        /* FAQ Section */
        .faq-section {
            background-color: #f8fafc;
            border-radius: 1rem;
            padding: 1.5rem;
            margin-top: 2rem;
            border: 1px solid #e2e8f0;
        }

        .faq-header {
            font-size: 1.5rem;
            color: var(--primary);
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .faq-item {
            margin-bottom: 1.5rem;
            background: white;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }

        .faq-question {
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 0.5rem;
        }

        .faq-answer {
            color: #475569;
            font-size: 0.95rem;
        }

        /* Utility */
        .divider {
            height: 1px;
            background: var(--gray-200);
            margin: 3rem 0;
            border: none;
        }
        
        .back-to-top {
            display: block;
            text-align: center;
            margin: 2rem 0;
            padding: 1rem;
            background: var(--gray-100);
            color: var(--text);
            text-decoration: none;
            border-radius: 0.5rem;
            font-weight: 600;
        }
    </style>
    <script>
        function toggleMenu() {
            document.getElementById('navOverlay').classList.toggle('active');
        }
        function closeMenu() {
            document.getElementById('navOverlay').classList.remove('active');
        }
    </script>
    """

    html_content = [f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Manual ContaPY Móvil</title>
        {css}
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    </head>
    <body>
        <header class="mobile-header">
            <div class="header-title">ContaPY Manual</div>
            <button class="menu-toggle" onclick="toggleMenu()">
                <i class="fas fa-bars"></i>
            </button>
        </header>

        <nav id="navOverlay" class="nav-overlay">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
                <span style="font-weight:bold; font-size:1.2rem;">Índice</span>
                <button onclick="toggleMenu()" style="background:none; border:none; font-size:1.5rem; color:#64748b;"><i class="fas fa-times"></i></button>
            </div>
    """]

    # Build Navigation
    for group_name, files in GROUPS.items():
        html_content.append(f'<div class="nav-group-title">{group_name}</div>')
        for filename in files:
            file_id = filename.replace('.md', '')
            
            # Title Logic
            if filename in VIRTUAL_FILES:
                title = VIRTUAL_FILES[filename]["title"]
            else:
                title = filename.replace('capitulo_', '').replace('.md', '').replace('_', ' ')
                title = re.sub(r'^\d+\s*', '', title).title()
            
            html_content.append(f'<a href="#{file_id}" class="nav-link" onclick="closeMenu()">{title}</a>')

    html_content.append("""
        </nav>
        <main class="main-content">
    """)

    # Build Content
    for group_name, files in GROUPS.items():
        html_content.append(f'<div style="padding: 2rem 0 1rem 0; border-bottom: 2px solid var(--primary); margin-bottom: 2rem;"><h2 style="margin:0; color:var(--primary);">{group_name}</h2></div>')
        
        for filename in files:
            file_id = filename.replace('.md', '')
            
            # Determine Content Source
            if filename in VIRTUAL_FILES:
                vf = VIRTUAL_FILES[filename]
                source_path = os.path.join(MANUAL_DIR, vf["source"])
                title = vf["title"]
                replacements = vf["replacements"]
            else:
                source_path = os.path.join(MANUAL_DIR, filename)
                title = filename.replace('capitulo_', '').replace('.md', '').replace('_', ' ')
                title = re.sub(r'^\d+\s*', '', title).title()
                replacements = []

            # Read and Process Content
            if os.path.exists(source_path):
                with open(source_path, 'r', encoding='utf-8') as f:
                    md_text = f.read()
                
                # Apply Replacements
                for old, new in replacements:
                    md_text = md_text.replace(old, new)
                
                # Convert to HTML
                html_body = md_to_html(md_text)
                
                # Container
                html_content.append(f'<div id="{file_id}" class="chapter-container">')
                html_content.append(html_body)
                
                # Append FAQs
                faqs = FAQ_DATA.get(filename, [])
                if faqs:
                    html_content.append(f"""
                    <div class="faq-section">
                        <div class="faq-header"><i class="fas fa-question-circle"></i> Preguntas Frecuentes</div>
                    """)
                    for question, answer in faqs:
                        html_content.append(f"""
                        <div class="faq-item">
                            <div class="faq-question">{question}</div>
                            <div class="faq-answer">{answer}</div>
                        </div>
                        """)
                    html_content.append('</div>')
                
                html_content.append('<a href="#" class="back-to-top">↑ Volver al Inicio</a>')
                html_content.append('<hr class="divider">')
                html_content.append('</div>')
            else:
                print(f"Warning: File not found {source_path}")

    html_content.append("""
        </main>
    </body>
    </html>
    """)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(''.join(html_content))
    
    print(f"Successfully generated {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_mobile_html()
