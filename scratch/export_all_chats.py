import json
import os
import re

base_brain_path = r"C:\Users\lenovo\.gemini\antigravity\brain"
output_dir = r"C:\ContaPY2\artifacts\historiales_completos"

conversations = {
    "8c3d5919-66bb-4e88-9894-125789f68bfc": "Chat Actual - Seguridad y Empaquetado Finaxis",
    "bbab8f8d-da8b-464f-9296-20f4d44c734f": "Auditoría de Seguridad y Mejoras",
    "deb16871-0d35-4a50-a779-90134b7ac905": "Sistema de Reservas Concurrentes",
    "0f366a7d-3cef-4ad0-83cc-ef87dd5fb9df": "Optimización de Reportes PH",
    "00f54a2d-5668-45fa-b4b6-3075f9c5e61d": "Localización de Historial de Chats",
    "4abd07da-5571-40d7-b4f0-e067b54a1cc0": "Estabilización Lógica Pagos",
    "15811a1a-45d3-484e-abaf-732489f132c6": "Profesionalización Documentación Finaxis",
    "7f457332-1b5c-48db-9da8-8d9d1ebf2a7e": "Optimización Módulo Contable"
}

def clean_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def clean_content(text):
    if not text: return ""
    # Quitar metadatos y etiquetas de sistema
    text = re.sub(r'<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>', '', text, flags=re.DOTALL)
    text = re.sub(r'<USER_SETTINGS_CHANGE>.*?</USER_SETTINGS_CHANGE>', '', text, flags=re.DOTALL)
    text = text.replace("<USER_REQUEST>", "").replace("</USER_REQUEST>", "")
    return text.strip()

def export_conversation(conv_id, title):
    log_path = os.path.join(base_brain_path, conv_id, ".system_generated", "logs", "overview.txt")
    if not os.path.exists(log_path): return

    clean_title = clean_filename(title)
    output_path = os.path.join(output_dir, f"{clean_title}.md")
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        with open(output_path, 'w', encoding='utf-8') as out:
            out.write(f"# {title.upper()}\n\n")
            out.write(f"ID: {conv_id}\n\n---\n\n")

            for line in lines:
                try:
                    data = json.loads(line.strip())
                    source = data.get("source")
                    type_ = data.get("type")
                    content = clean_content(data.get("content", ""))
                    tool_calls = data.get("tool_calls", [])

                    if source == "USER_EXPLICIT":
                        if content:
                            out.write(f"### 👤 USUARIO\n\n{content}\n\n---\n\n")
                    
                    elif source == "MODEL":
                        if content:
                            out.write(f"### 🤖 ANTIGRAVITY\n\n{content}\n\n")
                        
                        # EXPORTAR LOS "CUADRITOS" (Tool Calls)
                        for tool in tool_calls:
                            name = tool.get("name")
                            args = tool.get("args", {})
                            
                            out.write(f"#### 🛠️ ACCIÓN: {name}\n")
                            
                            if name == "run_command":
                                cmd = args.get("CommandLine", "").strip('"')
                                out.write(f"```powershell\n{cmd}\n```\n")
                            elif name == "write_to_file":
                                code = args.get("CodeContent", "").replace("\\n", "\n").replace("\\t", "\t").strip('"')
                                file = args.get("TargetFile", "").strip('"')
                                out.write(f"Archivo: `{file}`\n```\n{code}\n```\n")
                            elif name == "replace_file_content" or name == "multi_replace_file_content":
                                out.write(f"*Modificación de archivo: {args.get('TargetFile')}*\n")
                            
                        if content or tool_calls:
                            out.write("\n---\n\n")
                except: continue
        print(f"Exportado: {clean_title}.md")
    except Exception as e:
        print(f"Error en {conv_id}: {str(e)}")

os.makedirs(output_dir, exist_ok=True)
for cid, ctitle in conversations.items():
    export_conversation(cid, ctitle)

all_dirs = [d for d in os.listdir(base_brain_path) if os.path.isdir(os.path.join(base_brain_path, d))]
for d in all_dirs:
    if d not in conversations and d != "tempmediaStorage":
        export_conversation(d, f"Chat_Extra_{d[:8]}")

print(f"\n¡Listo! Revisa la carpeta: {output_dir}")
