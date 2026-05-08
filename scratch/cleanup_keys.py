import os
import glob
from dotenv import load_dotenv

# Cargamos el .env para estar seguros de que tenemos acceso a las llaves
load_dotenv()

BAD_TOKEN = "a4afb1e20e856e8fb031b487efbfd239"
GOOD_REPLACEMENT = 'os.getenv("DATAICO_AUTH_TOKEN")'

files_to_fix = glob.glob("*.py") + glob.glob("app/**/*.py", recursive=True)

for file_path in files_to_fix:
    if "scratch" in file_path or ".venv" in file_path:
        continue
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        if BAD_TOKEN in content:
            print(f"Fixing: {file_path}")
            new_content = content.replace(f'"{BAD_TOKEN}"', GOOD_REPLACEMENT)
            new_content = content.replace(f"'{BAD_TOKEN}'", GOOD_REPLACEMENT)
            
            # Aseguramos que 'import os' esté presente
            if "import os" not in new_content and "import os" not in content:
                new_content = "import os\n" + new_content
                
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

print("Limpieza completada.")
