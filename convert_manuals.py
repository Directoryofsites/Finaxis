import os
import markdown
import glob

# Configuration
SOURCE_DIR = r"c:\ContaPY2\Manual"
OUTPUT_DIR = r"c:\ContaPY2\Manual\html"

# CSS Template (The "Portable" Design)
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        :root {{
            --primary-color: #2563eb;
            --secondary-color: #1e40af;
            --bg-color: #f8fafc;
            --text-color: #1e293b;
            --card-bg: #ffffff;
            --code-bg: #1e293b;
            --code-text: #e2e8f0;
            --border-color: #e2e8f0;
        }}
        body {{
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background-color: var(--bg-color);
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: var(--card-bg);
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        h1, h2, h3 {{
            color: var(--secondary-color);
            margin-top: 1.5em;
        }}
        h1 {{
            border-bottom: 2px solid var(--primary-color);
            padding-bottom: 10px;
            margin-top: 0;
        }}
        code {{
            font-family: 'Consolas', 'Monaco', monospace;
            background-color: #f1f5f9;
            padding: 2px 5px;
            border-radius: 4px;
            color: #d63384;
        }}
        pre {{
            background-color: var(--code-bg);
            color: var(--code-text);
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
        }}
        pre code {{
            background-color: transparent;
            color: inherit;
            padding: 0;
        }}
        blockquote {{
            border-left: 4px solid var(--primary-color);
            margin: 0;
            padding-left: 20px;
            color: #475569;
            background-color: #f1f5f9;
            padding: 10px 20px;
            border-radius: 0 4px 4px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid var(--border-color);
            padding: 10px;
            text-align: left;
        }}
        th {{
            background-color: #f1f5f9;
            font-weight: bold;
        }}
        img {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
            border: 1px solid var(--border-color);
        }}
        .back-link {{
            display: inline-block;
            margin-bottom: 20px;
            color: var(--primary-color);
            text-decoration: none;
            font-weight: bold;
        }}
        .back-link:hover {{
            text-decoration: underline;
        }}
        footer {{
            text-align: center;
            margin-top: 50px;
            font-size: 0.9em;
            color: #64748b;
            border-top: 1px solid var(--border-color);
            padding-top: 20px;
        }}
    </style>
</head>
<body>

<div class="container">
    <a href="javascript:history.back()" class="back-link">← Volver</a>
    
    <div class="content">
        {content}
    </div>

    <footer>
        Sistema Finaxis - Manual de Usuario
    </footer>
</div>

</body>
</html>
"""

def extract_title(md_content):
    """Extracts the first h1 header, or returns specific default."""
    for line in md_content.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return "Manual de Usuario"

def convert_manuals():
    # Ensure output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created directory: {OUTPUT_DIR}")

    # Find all MD files
    md_files = glob.glob(os.path.join(SOURCE_DIR, "*.md"))
    print(f"Found {len(md_files)} markdown files.")

    for md_file in md_files:
        filename = os.path.basename(md_file)
        name_only = os.path.splitext(filename)[0]
        
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                md_content = f.read()

            # Convert to HTML
            html_body = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
            
            # Extract title
            page_title = extract_title(md_content)

            # Fill template
            full_html = HTML_TEMPLATE.format(
                title=page_title,
                content=html_body
            )

            # Write HTML file
            output_path = os.path.join(OUTPUT_DIR, f"{name_only}.html")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(full_html)
            
            print(f"Converted: {filename} -> {name_only}.html")

        except Exception as e:
            print(f"ERROR converting {filename}: {e}")

    print("Conversion complete!")

if __name__ == "__main__":
    convert_manuals()
