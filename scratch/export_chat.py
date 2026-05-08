import json
import os
import re

# CONFIGURACIÓN DINÁMICA
base_brain_path = rf"C:\Users\lenovo\.gemini\antigravity\brain"

def get_latest_conv_id():
    try:
        # Buscamos la carpeta con la fecha de modificación más reciente
        dirs = [d for d in os.listdir(base_brain_path) if os.path.isdir(os.path.join(base_brain_path, d)) and d != "tempmediaStorage"]
        if not dirs: return None
        latest_dir = max(dirs, key=lambda d: os.path.getmtime(os.path.join(base_brain_path, d)))
        return latest_dir
    except:
        return "b77a9c85-d5f5-4e1c-8323-ff3c43549a61" # Fallback al ID actual si algo falla

current_conv_id = get_latest_conv_id()
log_path = os.path.join(base_brain_path, current_conv_id, ".system_generated", "logs", "overview.txt")
output_path = r"C:\ContaPY2\artifacts\historial_chat_ACTUAL.md"


def clean_content(text):
    if not text: return ""
    text = re.sub(r'<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>', '', text, flags=re.DOTALL)
    text = re.sub(r'<USER_SETTINGS_CHANGE>.*?</USER_SETTINGS_CHANGE>', '', text, flags=re.DOTALL)
    text = text.replace("<USER_REQUEST>", "").replace("</USER_REQUEST>", "")
    # Si detectamos que el log está truncado, lo marcamos para que el usuario lo sepa
    if "truncated" in text.lower():
        text = text + "\n\n⚠️ [NOTA: Este mensaje fue recortado por el sistema de logs original]"
    return text.strip()

try:
    if not os.path.exists(log_path):
        print(f"Error: No se encontró el log en {log_path}")
        exit(1)

    with open(log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    with open(output_path, 'w', encoding='utf-8') as out:
        out.write("# HISTORIAL DE CONVERSACIÓN (VERSIÓN RECUPERADA)\n\n---\n\n")

        for line in lines:
            try:
                data = json.loads(line.strip())
                source = data.get("source")
                content = clean_content(data.get("content", ""))
                tool_calls = data.get("tool_calls", [])

                if source == "USER_EXPLICIT" and content:
                    out.write(f"### 👤 USUARIO\n\n{content}\n\n---\n\n")
                
                elif source == "MODEL":
                    important_tools = [t for t in tool_calls if t.get("name") in ["run_command", "write_to_file"]]
                    
                    if content or important_tools:
                        if content:
                            out.write(f"### 🤖 ANTIGRAVITY\n\n{content}\n\n")
                        
                        for tool in important_tools:
                            name = tool.get("name")
                            args = tool.get("args", {})
                            if name == "run_command":
                                cmd = args.get("CommandLine", "").strip('"')
                                out.write(f"**🛠️ COMANDO:**\n```powershell\n{cmd}\n```\n")
                            elif name == "write_to_file":
                                code = args.get("CodeContent", "").replace("\\n", "\n").replace("\\t", "\t").strip('"')
                                out.write(f"**📄 CÓDIGO GENERADO:**\n```\n{code}\n```\n")

                        out.write("\n---\n\n")
            except: continue

    print(f"Éxito: Historial exportado. Si algo salió truncado, es por el límite del log del sistema.")

except Exception as e:
    print(f"Error: {str(e)}")
